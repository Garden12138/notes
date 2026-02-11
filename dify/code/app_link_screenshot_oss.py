# app_link_screenshot_oss.py
# pip install fastapi uvicorn selenium oss2
# 启动：uvicorn app_link_screenshot_oss:app --host 0.0.0.0 --port 8003

from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl
import uuid
import time
import os
import shutil
import base64
from pathlib import Path
from typing import Optional

import oss2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


app = FastAPI(title="Link Screenshot Service (OSS)", version="1.1.2")


# -------------------------
# OSS 配置（你已脱敏）
# 建议：真实环境把 AK/SK 放环境变量，不要写死在代码
# -------------------------
OSS_ENDPOINT = "oss-cn-shanghai.aliyuncs.com"
OSS_ACCESS_KEY_ID = "xxxx"
OSS_SECRET_ACCESS_KEY = "xxxx"
OSS_BUCKET_NAME = "xxxx"
OSS_DOMAIN_MAPPING = "xxxx"
OSS_DIR = "xxxx"


class ScreenshotRequest(BaseModel):
    url: HttpUrl

    # 页面加载等待参数
    wait_sec: Optional[float] = 2.0          # 打开后先等一会儿（首屏资源）
    dom_ready_timeout: Optional[float] = 25  # 等 document.readyState=complete 超时

    # 截图策略
    full_page: Optional[bool] = True

    # 懒加载触发
    scroll: Optional[bool] = True
    scroll_step: Optional[int] = 900
    scroll_pause: Optional[float] = 0.35
    scroll_max_rounds: Optional[int] = 60

    # 滚动后等待图片加载（按完成比例）
    images_wait_timeout: Optional[float] = 12
    images_min_ratio: Optional[float] = 0.85

    # 上传后是否删除本地文件
    cleanup_local: Optional[bool] = True


DEFAULT_SAVE_PATH = Path("./screenshots")
DEFAULT_SAVE_PATH.mkdir(parents=True, exist_ok=True)


# -------------------------
# Chromium / Driver
# -------------------------
def detect_chromium_binary() -> str:
    candidates = [
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/snap/bin/chromium",
    ]
    for p in candidates:
        if Path(p).exists():
            return p

    for name in ["chromium-browser", "chromium", "google-chrome", "google-chrome-stable"]:
        p = shutil.which(name)
        if p:
            return p

    raise RuntimeError("No Chromium/Chrome executable found. Please install chromium or google-chrome.")


def patch_snap_libproxy_if_needed(chrome_binary: str) -> None:
    """
    snap chromium 常见报错：
      libpxbackend-1.0.so: cannot open shared object file
      Failed to load module: ... libgiolibproxy.so
    通过补 LD_LIBRARY_PATH 解决。
    """
    if "/snap/" not in chrome_binary:
        return

    snap_current = "/snap/chromium/current"
    libproxy_dirs = [
        f"{snap_current}/usr/lib/x86_64-linux-gnu/libproxy",
        f"{snap_current}/usr/lib/aarch64-linux-gnu/libproxy",
        f"{snap_current}/usr/lib/arm-linux-gnueabihf/libproxy",
    ]
    libproxy_dir = next((d for d in libproxy_dirs if Path(d).exists()), None)
    if not libproxy_dir:
        return

    old = os.environ.get("LD_LIBRARY_PATH", "")
    parts = [p for p in old.split(":") if p]
    if libproxy_dir not in parts:
        parts.append(libproxy_dir)
        os.environ["LD_LIBRARY_PATH"] = ":".join(parts)


def find_chromedriver() -> str:
    p = shutil.which("chromedriver")
    if p:
        return p

    candidates = [
        "/usr/bin/chromedriver",
        "/usr/lib/chromium-browser/chromedriver",
        "/usr/lib/chromium/chromedriver",
    ]
    for c in candidates:
        if Path(c).exists():
            return c

    raise RuntimeError(
        "chromedriver not found. Install via: sudo apt install -y chromium-chromedriver (or chromium-driver)"
    )


def build_driver() -> webdriver.Chrome:
    chrome_options = Options()

    chrome_binary = detect_chromium_binary()
    chrome_options.binary_location = chrome_binary
    patch_snap_libproxy_if_needed(chrome_binary)

    # 尽量降低被识别为自动化/降级页面的概率
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    # 固定桌面视窗（不要把高度 resize 到整页高度，避免触发响应式二次布局）
    chrome_options.add_argument("--window-size=1280,900")
    chrome_options.add_argument("--lang=zh-CN")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    )

    service = Service(find_chromedriver())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # 进一步隐藏 webdriver 痕迹（尽力而为）
    try:
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except Exception:
        pass

    return driver


# -------------------------
# Page helpers
# -------------------------
def wait_dom_ready(driver: webdriver.Chrome, timeout_sec: float = 25.0) -> None:
    end = time.time() + timeout_sec
    while time.time() < end:
        try:
            if driver.execute_script("return document.readyState") == "complete":
                return
        except Exception:
            pass
        time.sleep(0.2)


def scroll_to_bottom(driver: webdriver.Chrome, step: int = 900, pause: float = 0.35, max_rounds: int = 60) -> None:
    """
    向下滚动触发懒加载（图片、代码高亮、评论区、推荐模块等）
    最后回到顶部，保证截图从页面顶部开始。
    """
    last_h = driver.execute_script("return document.body.scrollHeight")
    y = 0
    for _ in range(max_rounds):
        y = min(y + step, last_h)
        driver.execute_script("window.scrollTo(0, arguments[0]);", y)
        time.sleep(pause)
        new_h = driver.execute_script("return document.body.scrollHeight")
        if new_h != last_h:
            last_h = new_h
        if y >= last_h - 5:
            break

    # 底部停留一下，让最后几屏的懒加载也触发
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.0)

    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.6)


def wait_images_loaded(driver: webdriver.Chrome, timeout_sec: float = 12.0, min_ratio: float = 0.85) -> None:
    """
    等待页面上大部分图片 complete（避免无限等，用比例阈值）
    """
    end = time.time() + timeout_sec
    while time.time() < end:
        try:
            ok = driver.execute_script(
                """
                const imgs = Array.from(document.images || []);
                if (imgs.length === 0) return true;

                let done = 0;
                for (const img of imgs) {
                  if (img.complete) done++;
                }
                return (done / imgs.length) >= arguments[0];
                """,
                float(min_ratio),
            )
            if ok:
                return
        except Exception:
            pass
        time.sleep(0.3)


def save_fullpage_screenshot_cdp(driver: webdriver.Chrome, filepath: Path) -> None:
    """
    使用 CDP 截整页（不把窗口高度 resize 到整页高度，减少布局变化）
    """
    driver.execute_cdp_cmd("Page.enable", {})
    result = driver.execute_cdp_cmd(
        "Page.captureScreenshot",
        {
            "format": "png",
            "captureBeyondViewport": True,
            "fromSurface": True,
        },
    )
    filepath.write_bytes(base64.b64decode(result["data"]))


# -------------------------
# OSS helpers
# -------------------------
def oss_bucket() -> oss2.Bucket:
    auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_SECRET_ACCESS_KEY)
    return oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)


def oss_key_for(filename: str) -> str:
    prefix = OSS_DIR.strip("/")
    return f"{prefix}/{filename}" if prefix else filename


def oss_public_url(object_key: str) -> str:
    base = OSS_DOMAIN_MAPPING.rstrip("/")
    key = object_key.lstrip("/")
    return f"{base}/{key}"


def upload_to_oss(local_path: Path, object_key: str) -> None:
    bucket = oss_bucket()
    bucket.put_object_from_file(object_key, str(local_path))


# -------------------------
# Main workflow
# -------------------------
def capture_and_upload(req: ScreenshotRequest) -> str:
    driver = build_driver()
    filename = f"{uuid.uuid4()}.png"
    local_path = DEFAULT_SAVE_PATH / filename
    object_key = oss_key_for(filename)

    try:
        driver.set_page_load_timeout(45)
        driver.get(str(req.url))

        # ① 等 DOM/脚本加载完成
        wait_dom_ready(driver, timeout_sec=req.dom_ready_timeout or 25)

        # ② 初始等待（给首屏资源一点时间）
        time.sleep(req.wait_sec or 2.0)

        # ③ 滚动触发懒加载
        if req.scroll:
            scroll_to_bottom(
                driver,
                step=req.scroll_step or 900,
                pause=req.scroll_pause or 0.35,
                max_rounds=req.scroll_max_rounds or 60,
            )

        # ④ 滚动后等图片资源完成
        wait_images_loaded(
            driver,
            timeout_sec=req.images_wait_timeout or 12,
            min_ratio=req.images_min_ratio or 0.85,
        )

        # ⑤ 截图
        if req.full_page:
            save_fullpage_screenshot_cdp(driver, local_path)
        else:
            driver.save_screenshot(str(local_path))

        # ⑥ 上传 OSS
        upload_to_oss(local_path, object_key)

        # ⑦ 返回下载地址
        return oss_public_url(object_key)

    finally:
        try:
            driver.quit()
        except Exception:
            pass

        # ⑧ 清理本地文件（默认清理）
        if req.cleanup_local:
            try:
                if local_path.exists():
                    local_path.unlink()
            except Exception:
                pass


@app.post("/screenshot")
async def screenshot(req: ScreenshotRequest):
    try:
        url = capture_and_upload(req)
        return {"url": url}
    except Exception as e:
        return {"error": str(e)}
