# app_phishing.py
# pip install fastapi uvicorn httpx python-whois
# 启动：uvicorn app_phishing:app --host 0.0.0.0 --port 8002

from fastapi import FastAPI
from pydantic import BaseModel
from urllib.parse import urlparse, urljoin
import re
import ipaddress
import httpx
import whois
from datetime import datetime, timezone

app = FastAPI(title="Phishing URL Check Service", version="1.0.1")


class URLCheckRequest(BaseModel):
    url: str


# -----------------------
# 可配置项（按你业务改）
# -----------------------

# 用于仿冒检测（示例：常见平台/生态域名，可按广告业务补充）
TARGET_DOMAINS = [
    "google.com",
    "facebook.com",
    "tiktok.com",
    "bytedance.com",
    "jd.com",
    "taobao.com",
    "alipay.com",
    "wechat.com",
    "paypal.com",
    "apple.com",
    "microsoft.com",
]

WHOIS_YOUNG_DAYS = 30
DOMAIN_LEN_WARN = 25

SENSITIVE_WORDS = [
    # 英文
    "login", "sign in", "signin", "verify", "verification", "password",
    "account", "security", "suspended", "locked", "urgent", "confirm",
    "bank", "wallet", "payment", "billing", "invoice", "otp", "2fa",
    # 中文
    "登录", "验证", "认证", "密码", "账户", "账号", "安全", "异常", "冻结", "解封",
    "立即", "紧急", "确认", "支付", "银行卡", "钱包", "发票", "验证码"
]

# 抓取 HTML 限制（安全）
FETCH_TIMEOUT_S = 3.0
FETCH_MAX_BYTES = 200_000  # 200KB
UA = "url-phishing-check/1.0"


# -----------------------
# 通用工具
# -----------------------

def normalize_url(url: str) -> str:
    """
    URL 规范化：
    - 如果没有 scheme（如 https://），自动补 https://
    """
    url = (url or "").strip()
    if not url:
        return url

    p = urlparse(url)
    if not p.scheme:
        url = "https://" + url

    return url


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _to_utc_dt(x) -> datetime | None:
    if x is None:
        return None
    if isinstance(x, list):
        x = x[0] if x else None
    if isinstance(x, datetime):
        return x if x.tzinfo else x.replace(tzinfo=timezone.utc)
    return None


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            ins = cur[j - 1] + 1
            dele = prev[j] + 1
            sub = prev[j - 1] + (0 if ca == cb else 1)
            cur.append(min(ins, dele, sub))
        prev = cur
    return prev[-1]


def _idna_ascii(host: str) -> str:
    return host.encode("idna").decode("ascii").lower().strip(".")


def _is_ip_host(host: str) -> bool:
    host = host.strip("[]")
    try:
        ipaddress.ip_address(host)
        return True
    except Exception:
        return False


def _registrable_like(host: str) -> str:
    """
    简化版主域提取：取最后两段。
    注意：co.uk 这类会不准，但用于“提示/加权”足够。
    """
    parts = host.split(".")
    if len(parts) <= 2:
        return host
    return ".".join(parts[-2:])


def fetch_html_limited(url: str) -> tuple[str | None, str | None]:
    """
    安全抓取 HTML：
    - 不执行脚本（只是下载文本）
    - 不跟随跳转（follow_redirects=False）
    - 只分析 text/html
    - 限制最大下载字节
    """
    # ✅ 兜底：确保抓取时 URL 一定有 scheme
    url = normalize_url(url)

    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    }
    try:
        with httpx.Client(
            timeout=FETCH_TIMEOUT_S,
            verify=True,
            follow_redirects=False,
            headers=headers
        ) as client:
            resp = client.get(url)
    except Exception:
        return None, "落地页抓取失败（网络异常/超时）"

    ctype = (resp.headers.get("Content-Type") or "").lower()
    if ("text/html" not in ctype) and ("application/xhtml+xml" not in ctype):
        return None, "落地页非HTML内容（跳过内容特征检测）"

    content = resp.content[:FETCH_MAX_BYTES]
    try:
        html = content.decode(resp.encoding or "utf-8", errors="replace")
    except Exception:
        html = content.decode("utf-8", errors="replace")
    return html, None


# -----------------------
# 1) URL 特征
# -----------------------

def url_feature_check(url: str) -> tuple[list[str], list[str]]:
    block, warn = [], []

    # ✅ 先规范化（保证 urlparse 行为一致）
    url = normalize_url(url)

    p = urlparse(url)
    host = p.hostname
    if not host:
        warn.append("无法解析主机名（跳过URL特征）")
        return block, warn

    host_ascii = _idna_ascii(host)

    if len(host_ascii) >= DOMAIN_LEN_WARN:
        warn.append(f"域名长度较长({len(host_ascii)})")

    # @ 通常在 netloc userinfo 段出现
    if "@" in (p.netloc or ""):
        block.append("URL包含@用户信息段（常用于钓鱼混淆）")

    if "-" in host_ascii:
        warn.append("域名包含连字符-（常见于仿冒域名）")

    if _is_ip_host(host_ascii):
        block.append("使用IP地址作为主机名（高风险）")

    # Levenshtein：用“近似主域”去对比
    registrable = _registrable_like(host_ascii)
    for t in TARGET_DOMAINS:
        t_ascii = _idna_ascii(t)
        dist = levenshtein(registrable, t_ascii)
        if dist == 1:
            warn.append(f"疑似仿冒域名：{registrable} ~ {t_ascii} (distance=1)")
        elif dist == 2:
            warn.append(f"疑似仿冒域名：{registrable} ~ {t_ascii} (distance=2)")

    return block, warn


# -----------------------
# 2) WHOIS 信息
# -----------------------

def whois_age_check(url: str) -> tuple[list[str], list[str]]:
    block, warn = [], []

    # ✅ 先规范化（保证 urlparse 行为一致）
    url = normalize_url(url)

    p = urlparse(url)
    host = p.hostname
    if not host:
        warn.append("无法解析主机名（跳过WHOIS）")
        return block, warn

    host_ascii = _idna_ascii(host)
    registrable = _registrable_like(host_ascii)

    try:
        w = whois.whois(registrable)
    except Exception:
        warn.append("WHOIS查询失败（可能被限流/不支持该TLD）")
        return block, warn

    created = _to_utc_dt(getattr(w, "creation_date", None))
    if not created:
        warn.append("WHOIS缺少creation_date（无法判断注册时长）")
        return block, warn

    age_days = (_now_utc() - created).days
    if age_days < 0:
        warn.append("WHOIS注册时间异常（未来时间）")
        return block, warn

    if age_days < WHOIS_YOUNG_DAYS:
        warn.append(f"域名注册时间较短：{age_days}天（< {WHOIS_YOUNG_DAYS}天）")

    return block, warn


# -----------------------
# 3) 内容特征（按“最小修改方案”收敛误报）
# -----------------------

def content_feature_check(url: str) -> tuple[list[str], list[str]]:
    block, warn = [], []

    # ✅ 先规范化：避免 fetch 时因为缺 scheme 直接异常
    url = normalize_url(url)

    html, err = fetch_html_limited(url)
    if err:
        warn.append(err)
        return block, warn
    if not html:
        warn.append("落地页HTML为空（跳过内容特征检测）")
        return block, warn

    lower = html.lower()

    # 表单数量（保留：在广告业务里依然有参考价值）
    form_count = len(re.findall(r"<\s*form\b", lower))
    if form_count > 0:
        warn.append(f"落地页包含表单数量：{form_count}")

    # ✅ 最小修改 1：JS/Meta 重定向在大站很常见 —— 不单独输出 warn（避免 jd.com 误报）

    # ✅ 最小修改 2：敏感词不直接输出具体词；只打一个“存在敏感词”标记
    has_sensitive_words = any(w.lower() in lower for w in SENSITIVE_WORDS)
    if has_sensitive_words:
        warn.append("CONTENT_SENSITIVE_WORDS")

    # 硬拦截强特征：password + form action 跨域（保留）
    has_password = bool(re.search(r'type\s*=\s*["\']password["\']', lower))
    if has_password:
        actions = re.findall(r"<\s*form[^>]*\saction\s*=\s*['\"]([^'\"]+)", lower)
        if actions:
            final_host = (urlparse(url).hostname or "").lower()
            for act in actions[:5]:
                act_abs = urljoin(url, act)
                act_host = (urlparse(act_abs).hostname or "").lower()
                if act_host and final_host and act_host != final_host:
                    block.append("检测到密码表单且跨域提交（强疑似钓鱼）")
                    break
        else:
            # 有密码框但无明确 action：不足以硬拦截，仅提示
            warn.append("落地页包含密码输入框（可能是登录页）")

    return block, warn


# -----------------------
# 组合决策（能确定就拦截，否则提示）
# -----------------------

def phishing_check(url: str) -> str:
    # ✅ 统一入口规范化：短链/裸域名 自动补 https://
    url = normalize_url(url)

    block_reasons, warn_reasons = [], []

    b, w = url_feature_check(url)
    block_reasons += b
    warn_reasons += w

    b, w = whois_age_check(url)
    block_reasons += b
    warn_reasons += w

    b, w = content_feature_check(url)
    block_reasons += b
    warn_reasons += w

    # 组合信号
    mimic = any("distance=1" in r for r in warn_reasons)
    young = any("注册时间较短" in r for r in warn_reasons)
    has_form = any(r.startswith("落地页包含表单数量：") for r in warn_reasons)
    has_sensitive_flag = any(r == "CONTENT_SENSITIVE_WORDS" for r in warn_reasons)
    has_password_hint = any(("密码" in r) or ("password" in r.lower()) for r in warn_reasons) or any("密码表单" in r for r in block_reasons)

    # ✅ 最小修改 2 的落地：敏感词仅在“有上下文”时才提示
    # 上下文：表单 或 新注册 或 仿冒(distance=1)
    if has_sensitive_flag and (has_form or young or mimic):
        warn_reasons = [r for r in warn_reasons if r != "CONTENT_SENSITIVE_WORDS"]
        warn_reasons.append("落地页存在诱导性内容，结合上下文存在风险")
    else:
        # 否则直接移除标记，避免大站误报
        warn_reasons = [r for r in warn_reasons if r != "CONTENT_SENSITIVE_WORDS"]

    # 组合式高置信拦截：仿冒(distance=1) + 新注册 + 登录/密码相关
    if mimic and young and has_password_hint:
        block_reasons.append("仿冒域名 + 新注册 + 登录/密码特征组合命中（高置信钓鱼）")

    if block_reasons:
        reasons = "；".join(block_reasons[:3])
        return f"已拦截：{reasons}"

    if warn_reasons:
        reasons = "；".join(warn_reasons[:3])
        return f"检测通过，但存在钓鱼风险提示：{reasons}"

    return "检测通过"


@app.post("/check")
def check(req: URLCheckRequest):
    # ✅ 这里也可以先 normalize 一下（可选，但更稳）
    u = normalize_url(req.url)
    return {"result": phishing_check(u)}
