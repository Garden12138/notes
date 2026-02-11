# qwen3_omni_flash_api.py.py
# pip install fastapi uvicorn openai
# 启动：uvicorn qwen3_omni_flash_api.py:app --host 0.0.0.0 --port 8005

import os
import json
import re
from typing import Any, Dict, Optional
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from openai import OpenAI


# -------------------------
# Config
# -------------------------
DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"  # Beijing by default


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    #api_key = os.getenv("DASHSCOPE_API_KEY")
    #if not api_key:
        #raise RuntimeError("DASHSCOPE_API_KEY is not set")
    api_key = "sk-xxxx"
    base_url = os.getenv("DASHSCOPE_BASE_URL", DEFAULT_BASE_URL)
    return OpenAI(api_key=api_key, base_url=base_url)


# -------------------------
# Request/Response Models
# -------------------------
class VideoAnalyzeRequest(BaseModel):
    video_url: HttpUrl


class VideoAnalyzeResponse(BaseModel):
    screen_content: str
    subtitle_content: str


# -------------------------
# Helpers
# -------------------------
PROMPT = (
    "你是视频内容分析助手。请严格按以下要求输出一个 JSON 对象（不要输出 Markdown，不要解释）：\n"
    "1、按照画面的出现时间顺序梳理并提取画面内容（screen_content）。可用编号；如能给出大致时间点更好（mm:ss）。\n"
    "2、提取视频中的字幕内容/屏幕文字内容（subtitle_content）。如果没有字幕或屏幕文字，请返回空字符串。\n"
    "3、必须只输出如下 JSON（字符串内如需换行请用 \\n 表示，不要出现真实换行符）：\n"
    "{\"screen_content\":\"\", \"subtitle_content\":\"\"}\n"
)


def _strip_code_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z0-9]*\n?", "", s)
        s = re.sub(r"\n?```$", "", s)
    return s.strip()


def _extract_json_candidate(text: str) -> str:
    text = _strip_code_fences(text)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1].strip()
    return text.strip()


def _fallback_extract_fields(text: str) -> Dict[str, str]:
    # best-effort extraction even if JSON is malformed
    def pick(name: str) -> str:
        m = re.search(rf'"{name}"\s*:\s*"(.*?)"\s*(,|\}})', text, flags=re.S)
        if not m:
            m = re.search(rf"'{name}'\s*:\s*'(.*?)'\s*(,|\}})", text, flags=re.S)
        return (m.group(1) if m else "").replace("\\n", "\n")

    return {
        "screen_content": pick("screen_content"),
        "subtitle_content": pick("subtitle_content"),
    }


def parse_model_output(raw_text: str) -> Dict[str, str]:
    candidate = _extract_json_candidate(raw_text)
    # normalize some common quote issues
    candidate = candidate.replace("“", '"').replace("”", '"').replace("’", "'")

    try:
        obj = json.loads(candidate)
        return {
            "screen_content": str(obj.get("screen_content", "")),
            "subtitle_content": str(obj.get("subtitle_content", "")),
        }
    except Exception:
        return _fallback_extract_fields(raw_text)


def call_qwen3_omni_flash(video_url: str) -> str:
    """
    Calls qwen3-omni-flash with streaming=True and returns the aggregated text output.
    """
    client = get_client()

    # Qwen-Omni video URL input format (OpenAI-compatible)
    # See official doc examples: type=video_url, video_url.url is mp4 URL. stream must be True. :contentReference[oaicite:3]{index=3}
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "video_url", "video_url": {"url": video_url}},
                {"type": "text", "text": PROMPT},
            ],
        }
    ]

    completion = client.chat.completions.create(
        model="qwen3-omni-flash",
        messages=messages,
        modalities=["text"],  # only need text output
        stream=True,          # mandatory for Qwen-Omni models :contentReference[oaicite:4]{index=4}
        stream_options={"include_usage": True},
        # optional: keep non-thinking mode for more direct/short output
        extra_body={"enable_thinking": False},
    )

    parts = []
    for chunk in completion:
        try:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                parts.append(chunk.choices[0].delta.content)
        except Exception:
            # ignore any unexpected chunk shapes
            pass

    return "".join(parts).strip()


# -------------------------
# FastAPI App
# -------------------------
app = FastAPI(title="Video Analyzer (Qwen3-Omni-Flash)", version="1.0.0")


@app.post("/analyze", response_model=VideoAnalyzeResponse)
def analyze(req: VideoAnalyzeRequest) -> Any:
    try:
        raw_text = call_qwen3_omni_flash(str(req.video_url))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Model call failed: {e}")

    result = parse_model_output(raw_text)
    # Ensure keys exist
    return VideoAnalyzeResponse(
        screen_content=result.get("screen_content", ""),
        subtitle_content=result.get("subtitle_content", ""),
    )

