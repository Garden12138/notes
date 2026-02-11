# audio2text.py
# pip install transformers==4.57.3 modelscope==1.33.0 torch==2.9.1 torchaudio==2.9.1 torchcodec==0.9.1 funasr==1.2.9 fastapi uvicorn requests
# 启动：uvicorn audio2text:app --host 0.0.0.0 --port 8004

import os
import uuid
import shutil
import tempfile
import subprocess
import requests
import wave
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from funasr import AutoModel

# ----------------------------
# 配置项
# ----------------------------
MODEL_DIR = "FunAudioLLM/Fun-ASR-Nano-2512"
DEVICE = "cuda:2"  # 没 GPU 可改成 "cpu"
VAD_MODEL = "fsmn-vad"
VAD_KWARGS = {"max_single_segment_time": 30000}

# 你提取音频用的参数（建议保持一致）
AUDIO_SR = 44100
AUDIO_CH = 2

# requests 下载超时（连接超时, 读取超时）
DOWNLOAD_TIMEOUT = (10, 120)

# ----------------------------
# 全局模型（启动时加载）
# ----------------------------
ASR_MODEL: AutoModel | None = None


def is_http_url(s: str) -> bool:
    try:
        p = urlparse(s)
        return p.scheme in ("http", "https")
    except Exception:
        return False


def ensure_model_loaded():
    """只加载一次模型到全局变量"""
    global ASR_MODEL
    if ASR_MODEL is None:
        ASR_MODEL = AutoModel(
            model=MODEL_DIR,
            trust_remote_code=True,
            vad_model=VAD_MODEL,
            vad_kwargs=VAD_KWARGS,
            remote_code="./model.py",
            device=DEVICE,
        )


def warmup_model():
    """
    可选：启动时做一次短音频推理预热，减少首请求延迟。
    """
    ensure_model_loaded()
    assert ASR_MODEL is not None

    tmp_dir = tempfile.mkdtemp(prefix="asr_warmup_")
    wav_path = os.path.join(tmp_dir, "warmup.wav")

    # 生成 0.5 秒静音 wav（44100Hz, 2ch）
    duration_sec = 0.5
    nframes = int(AUDIO_SR * duration_sec)

    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(AUDIO_CH)
        wf.setsampwidth(2)  # pcm_s16le
        wf.setframerate(AUDIO_SR)
        wf.writeframes(b"\x00\x00" * AUDIO_CH * nframes)

    try:
        _ = ASR_MODEL.generate(input=[wav_path], cache={}, batch_size=1)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def download_video(video_url: str, dst_path: str):
    """下载视频到 dst_path"""
    try:
        with requests.get(video_url, stream=True, timeout=DOWNLOAD_TIMEOUT) as r:
            r.raise_for_status()
            with open(dst_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"下载视频失败: {e}")


def extract_audio_from_video(video_path: str, audio_path: str):
    """使用 ffmpeg 从视频提取音频 wav"""
    cmd = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-i",
        video_path,
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        str(AUDIO_SR),
        "-ac",
        str(AUDIO_CH),
        audio_path,
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"音频提取失败: {e}")


def asr_recognition(wav_path: str) -> str:
    """使用已加载的全局模型进行识别"""
    ensure_model_loaded()
    assert ASR_MODEL is not None

    res = ASR_MODEL.generate(input=[wav_path], cache={}, batch_size=1)
    if not res or "text" not in res[0]:
        return ""
    return res[0]["text"]


class VideoReq(BaseModel):
    url: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1) 启动即加载模型
    ensure_model_loaded()
    # 2) 可选：warm-up，进一步减少首请求耗时
    try:
        warmup_model()
        print("[startup] ASR model loaded + warmed up.")
    except Exception as e:
        # warmup 失败不影响服务启动（但会让首请求更慢）
        print(f"[startup] warmup failed: {e}")

    yield

    # 这里可以做资源释放（多数情况下无需显式释放）
    print("[shutdown] service stopping...")


app = FastAPI(title="Video ASR Service", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/ready")
def ready():
    return {"model_loaded": ASR_MODEL is not None, "device": DEVICE}


@app.post("/process_video/")
async def process_video(req: VideoReq):
    """
    req.url:
    - 如果是 http/https：下载后处理
    - 如果不是：http(s)，则视为本地文件名/路径，必须存在
    """
    # 每次请求一个独立临时目录，避免并发冲突
    workdir = tempfile.mkdtemp(prefix="asr_job_")
    job_id = uuid.uuid4().hex[:8]

    tmp_video_path = os.path.join(workdir, f"video_{job_id}.mp4")
    tmp_audio_path = os.path.join(workdir, f"audio_{job_id}.wav")

    # 是否使用临时下载视频（决定是否删除）
    using_temp_video = False

    try:
        if is_http_url(req.url):
            using_temp_video = True
            download_video(req.url, tmp_video_path)
            video_path = tmp_video_path
        else:
            # 本地文件：支持传文件名或相对/绝对路径
            video_path = req.url
            if not os.path.exists(video_path):
                raise HTTPException(status_code=400, detail=f"本地文件不存在: {video_path}")

        extract_audio_from_video(video_path, tmp_audio_path)
        text = asr_recognition(tmp_audio_path)

        return {"audio_content": text}

    finally:
        # 只清理临时目录（不会影响本地视频源文件）
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    import uvicorn
    # 注意：多 worker 会导致每个进程各加载一份模型，占用更多 GPU 显存
    uvicorn.run(app, host="0.0.0.0", port=8004)

