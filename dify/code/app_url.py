# app_url.py
# pip install fastapi pydantic httpx
# 启动：uvicorn app_url:app --host 0.0.0.0 --port 8001

from fastapi import FastAPI
from pydantic import BaseModel
from urllib.parse import urlparse, urljoin
import ipaddress
import socket
import re
import httpx

app = FastAPI(title="URL HTTPS Only Check Service", version="1.1.2")


class URLCheckRequest(BaseModel):
    url: str


# 按需增删短链域名
SHORTENER_DOMAINS = {
    "3.cn",
    "2pppp.cn",
    "0u10.cn",
    "1m2nn.cn",
    "6mms.cn"
}


def _strip_and_clean(url: str) -> str:
    url = url.strip()
    url = re.sub(r'[\u0000-\u001f\u007f]', '', url)
    return url


def _ensure_https_scheme(url: str) -> str:
    # 支持用户输入 "3.cn/xxx" 这种无 scheme 的形式：默认补 https://
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        return "https://" + url
    return url


def _dns_ip_safety_check(hostname_ascii: str) -> str | None:
    """
    返回 None 表示安全；否则返回原因字符串
    """
    try:
        ip_list = socket.getaddrinfo(hostname_ascii, None)
    except Exception:
        return "域名无法解析"

    for item in ip_list:
        ip_str = item[4][0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            return f"非法 IP 地址：{ip_str}"

        if (
            ip_obj.is_private or
            ip_obj.is_loopback or
            ip_obj.is_link_local or
            ip_obj.is_multicast or
            ip_obj.is_reserved
        ):
            return f"域名解析到不安全的 IP 地址：{ip_str}"

    return None


def check_url_https_only(url: str) -> str:
    if not url or not isinstance(url, str):
        return "URL 为空或格式非法"

    url = _strip_and_clean(url)
    url = _ensure_https_scheme(url)

    try:
        parsed = urlparse(url)
    except Exception:
        return "URL 解析失败"

    # 1. 必须是 https
    if parsed.scheme.lower() != "https":
        return "仅允许 HTTPS 链接"

    # 2. 必须有 hostname
    hostname = parsed.hostname
    if not hostname:
        return "URL 中缺少有效的主机名"

    # 3. 拒绝 user:pass@host 形式
    if parsed.username or parsed.password:
        return "URL 包含用户名或密码字段，存在钓鱼风险"

    # 4. 端口校验（仅允许 443）
    if parsed.port not in (None, 443):
        return f"不允许的端口号：{parsed.port}"

    # 5. IDN 规范化（Unicode 域名 → punycode）
    try:
        hostname_ascii = hostname.encode("idna").decode("ascii")
    except Exception:
        return "域名 IDN 解析失败"

    # 6. DNS 解析并校验 IP（防内网 / 本机 / 保留地址）
    reason = _dns_ip_safety_check(hostname_ascii)
    if reason:
        return reason

    return "检测通过"


def is_short_link(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return host in SHORTENER_DOMAINS


def expand_short_url(
    start_url: str,
    max_redirects: int = 5,
    timeout_s: float = 5.0
) -> tuple[str | None, str | None, list[str]]:
    """
    返回 (final_url, error_reason, http_urls)
    - final_url: 成功展开到的最终 URL
    - error_reason: 失败原因
    - http_urls: 跳转链中出现过的 http:// URL（仅记录为风险提示，不直接拦截）
    """
    http_urls: list[str] = []
    current = start_url

    with httpx.Client(
        follow_redirects=False,
        timeout=timeout_s,
        verify=True,
        headers={"User-Agent": "url-precheck/1.1.2"}
    ) as client:
        for _ in range(max_redirects):
            try:
                try:
                    resp = client.head(current)
                except httpx.HTTPError:
                    resp = client.get(current)
            except Exception:
                return None, "短链展开失败（网络请求异常）", http_urls

            # 非跳转：认为到达最终落地
            if resp.status_code not in (301, 302, 303, 307, 308):
                return current, None, http_urls

            location = resp.headers.get("Location")
            if not location:
                return None, "短链展开失败（跳转缺少 Location）", http_urls

            next_url = urljoin(current, location)
            next_url = _strip_and_clean(next_url)
            next_url = _ensure_https_scheme(next_url)

            p = urlparse(next_url)
            scheme = (p.scheme or "").lower()

            # 允许 http/https；其他协议拦截
            if scheme not in ("http", "https"):
                return None, "短链跳转到不支持的协议，已拦截", http_urls

            # 记录链路中的 http（仅记录，不拦截）
            if scheme == "http":
                http_urls.append(next_url)

            # 对下一跳做 DNS/IP 安全校验（防 SSRF）
            if not p.hostname:
                return None, "短链跳转到无效主机名，已拦截", http_urls
            try:
                hostname_ascii = p.hostname.encode("idna").decode("ascii")
            except Exception:
                return None, "短链跳转域名 IDN 解析失败", http_urls

            reason = _dns_ip_safety_check(hostname_ascii)
            if reason:
                return None, f"短链跳转目标不安全：{reason}", http_urls

            current = next_url

        return None, f"短链跳转次数超过上限（{max_redirects}）", http_urls


@app.post("/check")
def check_url(req: URLCheckRequest):
    raw = req.url
    if raw is None:
        return {"result": "URL 为空或格式非法"}

    # 先做基础规则校验（含 DNS/IP 安全）
    base_result = check_url_https_only(raw)
    if base_result != "检测通过":
        return {"result": base_result}

    normalized = _ensure_https_scheme(_strip_and_clean(raw))

    if is_short_link(normalized):
        final_url, err, http_urls = expand_short_url(normalized, max_redirects=5, timeout_s=5.0)
        if err:
            return {"result": err}

        # 最终落地再跑一遍你的基础校验（双保险）
        final_check = check_url_https_only(final_url)
        if final_check != "检测通过":
            return {"result": f"短链落地页未通过校验：{final_check}"}

        # 通过但链路出现 http：在 result 里提示（不直接拦截）
        if http_urls:
            # 去重保持顺序
            seen = set()
            http_urls_unique = []
            for u in http_urls:
                if u not in seen:
                    seen.add(u)
                    http_urls_unique.append(u)

            return {"result": "检测通过，但跳转链出现HTTP：" + " , ".join(http_urls_unique)}

        return {"result": "检测通过"}

    return {"result": "检测通过"}
