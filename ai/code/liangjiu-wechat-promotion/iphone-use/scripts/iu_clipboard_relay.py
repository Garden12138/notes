#!/usr/bin/env python3
"""
iPhone Shortcuts -> Mac local relay -> iphone-use /agent/inbox

Usage:
    python3 iu_clipboard_relay.py

The iPhone Shortcut should POST JSON to:
    http://<MAC_LAN_IP>:18080/clipboard

No Authorization header is required on the iPhone side. This relay reads:
    ~/.iphone-use/agent-token
and forwards the JSON to:
    http://127.0.0.1:44321/agent/inbox
with the correct Bearer token.
"""

from __future__ import annotations

import ipaddress
import json
import os
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

LISTEN_HOST = os.environ.get("IU_RELAY_HOST", "0.0.0.0")
LISTEN_PORT = int(os.environ.get("IU_RELAY_PORT", "18080"))
UPSTREAM_URL = os.environ.get(
    "IU_INBOX_URL",
    "http://127.0.0.1:44321/agent/inbox",
)
TOKEN_FILE = Path(
    os.environ.get(
        "IU_AGENT_TOKEN_FILE",
        str(Path.home() / ".iphone-use" / "agent-token"),
    )
)


def read_token() -> str:
    if not TOKEN_FILE.exists():
        raise RuntimeError(f"agent token file not found: {TOKEN_FILE}")
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    if not token:
        raise RuntimeError(f"agent token is empty: {TOKEN_FILE}")
    return token


def is_private_or_loopback(address: str) -> bool:
    """Only accept requests from private LAN or loopback addresses."""
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local


def forward_to_inbox(payload: dict[str, Any]) -> tuple[int, str]:
    token = read_token()
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        UPSTREAM_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            text = response.read().decode("utf-8", errors="replace")
            return response.status, text
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        return exc.code, text


class Handler(BaseHTTPRequestHandler):
    server_version = "IUClipboardRelay/1.0"

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path.rstrip("/") in ("", "/health"):
            self.send_json(
                200,
                {
                    "ok": True,
                    "service": "iu-clipboard-relay",
                    "upstream": UPSTREAM_URL,
                },
            )
            return
        self.send_json(404, {"ok": False, "error": "NOT_FOUND"})

    def do_POST(self) -> None:
        client_ip = self.client_address[0]
        if not is_private_or_loopback(client_ip):
            self.send_json(
                403,
                {
                    "ok": False,
                    "error": "NON_LAN_CLIENT_REJECTED",
                    "client_ip": client_ip,
                },
            )
            return

        if self.path.rstrip("/") != "/clipboard":
            self.send_json(404, {"ok": False, "error": "NOT_FOUND"})
            return

        raw_length = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_length)
        except ValueError:
            self.send_json(400, {"ok": False, "error": "INVALID_CONTENT_LENGTH"})
            return

        raw = self.rfile.read(length)
        text = raw.decode("utf-8", errors="replace")

        print("\n========== iPhone Shortcut request ==========", flush=True)
        print(f"client: {client_ip}", flush=True)
        print(f"path: {self.path}", flush=True)
        print(f"content-type: {self.headers.get('Content-Type', '')}", flush=True)
        print(f"body: {text if text else '<empty>'}", flush=True)

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            self.send_json(
                400,
                {
                    "ok": False,
                    "error": "INVALID_JSON",
                    "message": str(exc),
                    "raw": text,
                },
            )
            return

        if not isinstance(payload, dict):
            self.send_json(
                400,
                {
                    "ok": False,
                    "error": "JSON_BODY_MUST_BE_OBJECT",
                },
            )
            return

        payload.setdefault("verb", "clipboard_export")
        payload.setdefault("ok", True)

        try:
            upstream_status, upstream_body = forward_to_inbox(payload)
        except Exception as exc:
            self.send_json(
                502,
                {
                    "ok": False,
                    "error": "UPSTREAM_REQUEST_FAILED",
                    "message": str(exc),
                },
            )
            return

        forwarded = 200 <= upstream_status < 300
        print(
            f"forwarded: {forwarded}, upstream_status: {upstream_status}, "
            f"upstream_body: {upstream_body!r}",
            flush=True,
        )

        self.send_json(
            200 if forwarded else 502,
            {
                "ok": forwarded,
                "forwarded": forwarded,
                "upstream_status": upstream_status,
                "upstream_body": upstream_body,
                "received": payload,
            },
        )

    def log_message(self, fmt: str, *args: Any) -> None:
        return


def main() -> None:
    try:
        read_token()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)

    server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), Handler)
    print(f"IU Clipboard Relay listening on http://{LISTEN_HOST}:{LISTEN_PORT}")
    print("Shortcut POST URL: http://<MAC_LAN_IP>:18080/clipboard")
    print(f"Forwarding to: {UPSTREAM_URL}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
