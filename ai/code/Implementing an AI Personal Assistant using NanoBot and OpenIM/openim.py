"""
OpenIM channel implementation (Webhook inbound + REST outbound).

Features:
- Receive messages via OpenIM server webhook
- Reply via OpenIM REST /msg/send_msg
- Mark read to fix "always unread":
    * Prefer /msg/mark_msgs_as_read if webhook provides seq
    * Otherwise:
        - /msg/get_conversations_has_read_and_max_seq to fetch maxSeq
        - /msg/mark_conversation_as_read with hasReadSeq=maxSeq (hasReadSeq must be >=1)

Fixes:
- Scheme-B (bot in imAdminUserID): /auth/get_user_token(bot) fails with "don't get Admin token"
  -> auto fallback to /auth/get_admin_token(userID=bot_user_id) and cache "admin-only" users.
- Avoid spam "(当前只支持文本消息)" loop: ignore non-text events.
- Disable offline push to avoid openim-push "appid is invalid".
- Read receipt reliability: retry/backoff + lastReadSeq cache + mark-after-send second pass.
"""

from __future__ import annotations

import asyncio
import json
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from loguru import logger

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.schema import OpenIMConfig


def now_ms() -> int:
    return int(time.time() * 1000)


def _is_int_str(s: str) -> bool:
    try:
        int(s)
        return True
    except Exception:
        return False


def build_single_conversation_id(a: str, b: str) -> str:
    """
    OpenIM single conversationID commonly looks like: si_<min>_<max>.
    """
    if _is_int_str(a) and _is_int_str(b):
        x, y = int(a), int(b)
        lo, hi = (a, b) if x <= y else (b, a)
    else:
        lo, hi = (a, b) if a <= b else (b, a)
    return f"si_{lo}_{hi}"


def _to_int_or_none(v: Any) -> int | None:
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.isdigit():
        return int(v)
    return None


def _deep_get(d: Any, path: list[str]) -> Any:
    cur = d
    for k in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def extract_text_from_content(content: Any) -> str:
    """
    Webhook content may be:
      1) plain string: "hello"
      2) JSON string: '{"content":"hello"}'
      3) dict: {"content":"hello"}
    Normalize to plain text.
    """
    if content is None:
        return ""

    if isinstance(content, dict):
        return str(content.get("content") or "").strip()

    if isinstance(content, str):
        s = content.strip()
        if not s:
            return ""
        if s.startswith("{") and s.endswith("}"):
            try:
                obj = json.loads(s)
                if isinstance(obj, dict) and "content" in obj:
                    return str(obj.get("content") or "").strip()
            except Exception:
                pass
        return s

    return str(content).strip()


class OpenIMRestClient:
    """
    Minimal OpenIM REST client using stdlib (no extra deps).
    """

    def __init__(self, api_address: str, admin_user_id: str, admin_secret: str):
        self.api_address = api_address.rstrip("/")
        self.admin_user_id = admin_user_id
        self.admin_secret = admin_secret

        self._token_lock = threading.Lock()

        # admin token for admin_user_id (usually imAdmin)
        self._admin_token: str | None = None
        self._admin_token_expire_at = 0

        # admin token cache for "any admin user" (e.g. bot_user_id in scheme-B)
        self._admin_token_cache_by_user: dict[str, tuple[str, int]] = {}
        # user_id -> (token, expire_at)

        # user token cache
        self._user_token_cache: dict[tuple[str, int], tuple[str, int]] = {}
        # (user_id, platform_id) -> (token, expire_at)

        # once a user is known "admin-only" (can't get user token), store here
        self._admin_only_users: set[str] = set()

    def _post_json(
        self,
        path: str,
        body: dict[str, Any],
        headers: dict[str, str] | None = None,
        timeout: int = 10,
    ) -> dict[str, Any]:
        url = f"{self.api_address}{path}"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw) if raw else {}

    def get_admin_token(self) -> str:
        """
        POST /auth/get_admin_token for admin_user_id (usually imAdmin)
        """
        with self._token_lock:
            if self._admin_token and time.time() < self._admin_token_expire_at - 60:
                return self._admin_token

            body = {"secret": self.admin_secret, "userID": self.admin_user_id}
            resp = self._post_json("/auth/get_admin_token", body, headers={"operationID": str(now_ms())})
            if resp.get("errCode") != 0:
                raise RuntimeError(f"get_admin_token failed: {resp}")

            data = resp.get("data") or {}
            token = data.get("token")
            if not token:
                raise RuntimeError(f"get_admin_token missing token: {resp}")

            expire_seconds = int(data.get("expireTimeSeconds", 3600))
            self._admin_token = token
            self._admin_token_expire_at = int(time.time()) + expire_seconds
            return token

    def get_admin_token_for_user(self, user_id: str) -> str:
        """
        POST /auth/get_admin_token for a specific admin user (scheme-B bot).
        """
        with self._token_lock:
            cached = self._admin_token_cache_by_user.get(user_id)
            if cached and time.time() < cached[1] - 60:
                return cached[0]

            body = {"secret": self.admin_secret, "userID": user_id}
            resp = self._post_json("/auth/get_admin_token", body, headers={"operationID": str(now_ms())})
            if resp.get("errCode") != 0:
                raise RuntimeError(f"get_admin_token({user_id}) failed: {resp}")

            data = resp.get("data") or {}
            token = data.get("token")
            if not token:
                raise RuntimeError(f"get_admin_token({user_id}) missing token: {resp}")

            expire_seconds = int(data.get("expireTimeSeconds", 3600))
            expire_at = int(time.time()) + expire_seconds
            self._admin_token_cache_by_user[user_id] = (token, expire_at)
            return token

    def get_user_token(self, user_id: str, platform_id: int) -> str:
        """
        POST /auth/get_user_token
        NOTE: if user_id is admin (in imAdminUserID), server returns errDlt "don't get Admin token".
        """
        key = (user_id, platform_id)
        with self._token_lock:
            cached = self._user_token_cache.get(key)
            if cached and time.time() < cached[1] - 60:
                return cached[0]

        admin_token = self.get_admin_token()
        headers = {"operationID": str(now_ms()), "token": admin_token}
        body = {"platformID": int(platform_id), "userID": user_id}

        resp = self._post_json("/auth/get_user_token", body, headers=headers)
        if resp.get("errCode") != 0:
            raise RuntimeError(f"get_user_token failed: {resp}")

        data = resp.get("data") or {}
        token = data.get("token")
        if not token:
            raise RuntimeError(f"get_user_token missing token: {resp}")

        expire_seconds = int(data.get("expireTimeSeconds", 3600))
        expire_at = int(time.time()) + expire_seconds
        with self._token_lock:
            self._user_token_cache[key] = (token, expire_at)
        return token

    def get_sender_token(self, user_id: str, platform_id: int) -> str:
        """
        - Normal user: user token
        - Admin-only user (scheme-B bot): admin token
        Cache admin-only to avoid repeated server WARN.
        """
        if user_id in self._admin_only_users:
            return self.get_admin_token_for_user(user_id)

        try:
            return self.get_user_token(user_id, platform_id)
        except RuntimeError as e:
            msg = str(e)
            if "don't get Admin token" in msg:
                self._admin_only_users.add(user_id)
                return self.get_admin_token_for_user(user_id)
            raise

    def send_text(self, bot_user_id: str, bot_platform_id: int, bot_nickname: str, recv_user_id: str, text: str) -> None:
        token = self.get_sender_token(bot_user_id, bot_platform_id)
        headers = {"operationID": str(now_ms()), "token": token}

        body = {
            "sendID": bot_user_id,
            "recvID": recv_user_id,
            "groupID": "",
            "senderNickname": bot_nickname,
            "senderFaceURL": "",
            "senderPlatformID": int(bot_platform_id),
            "content": {"content": text},
            "contentType": 101,
            "sessionType": 1,
            "isOnlineOnly": False,
            # Disable offline push to avoid openim-push appid invalid
            "notOfflinePush": True,
            "sendTime": now_ms(),
            "ex": "",
        }

        resp = self._post_json("/msg/send_msg", body, headers=headers)
        if resp.get("errCode") != 0:
            raise RuntimeError(f"send_msg failed: {resp}")

    def mark_msgs_as_read(self, bot_user_id: str, bot_platform_id: int, conversation_id: str, seqs: list[int]) -> None:
        if not seqs or any((not isinstance(x, int) or x < 1) for x in seqs):
            raise RuntimeError(f"mark_msgs_as_read: invalid seqs={seqs}")

        token = self.get_sender_token(bot_user_id, bot_platform_id)
        headers = {"operationID": str(now_ms()), "token": token}
        body = {"conversationID": conversation_id, "userID": bot_user_id, "seqs": seqs}

        resp = self._post_json("/msg/mark_msgs_as_read", body, headers=headers)
        if resp.get("errCode") != 0:
            raise RuntimeError(f"mark_msgs_as_read failed: {resp}")

    def mark_conversation_as_read(
        self,
        bot_user_id: str,
        bot_platform_id: int,
        conversation_id: str,
        has_read_seq: int,
        seqs: list[int] | None = None,
    ) -> None:
        if not isinstance(has_read_seq, int) or has_read_seq < 1:
            raise RuntimeError(f"mark_conversation_as_read: has_read_seq invalid: {has_read_seq}")

        token = self.get_sender_token(bot_user_id, bot_platform_id)
        headers = {"operationID": str(now_ms()), "token": token}
        body = {
            "conversationID": conversation_id,
            "userID": bot_user_id,
            "hasReadSeq": int(has_read_seq),
            "seqs": seqs or [],
        }

        resp = self._post_json("/msg/mark_conversation_as_read", body, headers=headers)
        if resp.get("errCode") != 0:
            raise RuntimeError(f"mark_conversation_as_read failed: {resp}")

    def get_conversations_has_read_and_max_seq(self, bot_user_id: str, bot_platform_id: int, conversation_ids: list[str]) -> dict[str, dict[str, Any]]:
        token = self.get_sender_token(bot_user_id, bot_platform_id)
        headers = {"operationID": str(now_ms()), "token": token}
        body = {"userID": bot_user_id, "conversationIDs": conversation_ids}

        resp = self._post_json("/msg/get_conversations_has_read_and_max_seq", body, headers=headers)
        if resp.get("errCode") != 0:
            raise RuntimeError(f"get_conversations_has_read_and_max_seq failed: {resp}")

        data = resp.get("data") or {}
        seqs_map = data.get("seqs")
        if isinstance(seqs_map, dict):
            return seqs_map
        if isinstance(data, dict) and any(k in conversation_ids for k in data.keys()):
            return data
        return {}


class OpenIMChannel(BaseChannel):
    """
    OpenIM channel based on webhook inbound (HTTP server) and REST outbound.
    """

    name = "openim"

    def __init__(self, config: OpenIMConfig, bus: MessageBus):
        super().__init__(config, bus)
        self.config: OpenIMConfig = config
        self._client = OpenIMRestClient(
            api_address=config.api_address,
            admin_user_id=config.admin_user_id,
            admin_secret=config.admin_secret,
        )

        self._httpd: ThreadingHTTPServer | None = None
        self._http_thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

        # read receipt state
        self._read_state_lock = threading.Lock()
        self._last_read_seq: dict[str, int] = {}  # conversation_id -> last marked seq

    def _get_last_read_seq(self, conversation_id: str) -> int:
        with self._read_state_lock:
            return int(self._last_read_seq.get(conversation_id, 0))

    def _set_last_read_seq(self, conversation_id: str, seq: int) -> None:
        with self._read_state_lock:
            if seq > int(self._last_read_seq.get(conversation_id, 0)):
                self._last_read_seq[conversation_id] = int(seq)

    async def start(self) -> None:
        if not self.config.bot_user_id:
            logger.error("OpenIM bot_user_id not configured")
            return

        self._running = True
        self._loop = asyncio.get_running_loop()

        channel = self

        class Handler(BaseHTTPRequestHandler):
            def _reply_ok(self):
                payload = {"actionCode": 0, "errCode": 0, "errMsg": "", "errDlt": "", "nextCode": 0}
                data = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_POST(self):
                # allow query like ?contenttype=json
                if urlparse(self.path).path != channel.config.webhook_path:
                    self.send_response(404)
                    self.end_headers()
                    return

                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length) if length > 0 else b"{}"

                try:
                    event = json.loads(raw.decode("utf-8", errors="replace"))
                except Exception:
                    self._reply_ok()
                    return

                # Fast ACK
                self._reply_ok()

                # async processing
                threading.Thread(target=channel._handle_webhook_event, args=(event,), daemon=True).start()

            def log_message(self, format: str, *args: Any) -> None:
                return

        self._httpd = ThreadingHTTPServer((self.config.listen_host, self.config.listen_port), Handler)
        self._http_thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._http_thread.start()

        logger.info(
            "OpenIM channel webhook listening on http://{}:{}{}",
            self.config.listen_host,
            self.config.listen_port,
            self.config.webhook_path,
        )

        while self._running:
            await asyncio.sleep(1)

    async def stop(self) -> None:
        self._running = False
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
        if self._http_thread and self._http_thread.is_alive():
            self._http_thread.join(timeout=2)
        self._http_thread = None
        logger.info("OpenIM channel stopped")

    async def send(self, msg: OutboundMessage) -> None:
        """
        Reply to the user. For our single-chat MVP:
        - outbound recvID == msg.chat_id
        Also do a second-pass mark-read after sending (more reliable for maxSeq update).
        """
        try:
            await asyncio.to_thread(
                self._client.send_text,
                bot_user_id=self.config.bot_user_id,
                bot_platform_id=self.config.bot_platform_id,
                bot_nickname=self.config.bot_nickname,
                recv_user_id=msg.chat_id,
                text=(msg.content or "").strip(),
            )

            # second-pass read marking (helps when maxSeq lags right after inbound webhook)
            if self.config.enable_read_receipt:
                fake_event = {"conversationID": build_single_conversation_id(msg.chat_id, self.config.bot_user_id)}
                await asyncio.to_thread(self._try_mark_read, fake_event, msg.chat_id)

        except Exception as e:
            logger.error("OpenIM send failed: {}", e)

    def _extract_seq_from_event(self, event: dict[str, Any]) -> int | None:
        """
        Webhook payload differs across versions/configs.
        Try common locations for seq.
        """
        candidates = [
            event.get("seq"),
            _deep_get(event, ["msgData", "seq"]),
            _deep_get(event, ["data", "seq"]),
            _deep_get(event, ["msgData", "msgData", "seq"]),
        ]
        for c in candidates:
            seq = _to_int_or_none(c)
            if seq and seq >= 1:
                return seq
        return None

    def _handle_webhook_event(self, event: dict[str, Any]) -> None:
        """
        Runs in background thread.
        """
        try:
            send_id = str(event.get("sendID", ""))
            recv_id = str(event.get("recvID", ""))
            content_type = int(event.get("contentType", 0) or 0)

            # Only handle messages sent TO this bot, and avoid self-loop
            if recv_id != self.config.bot_user_id:
                return
            if send_id == self.config.bot_user_id:
                return

            # IMPORTANT: ignore non-text events to avoid spam loop (read receipts/system signals/etc.)
            if content_type != 101:
                return

            text = extract_text_from_content(event.get("content", ""))
            if not text:
                return

            # Mark read ASAP
            if self.config.enable_read_receipt:
                self._try_mark_read(event=event, peer_user_id=send_id)

            # Forward to bus (thread -> event loop)
            if not self._loop:
                return

            fut = asyncio.run_coroutine_threadsafe(
                self._handle_message(
                    sender_id=send_id,
                    chat_id=send_id,
                    content=text,
                    metadata={
                        "openim": {
                            "raw": event,
                            "conversation_id": event.get("conversationID"),
                            "seq": event.get("seq"),
                        }
                    },
                ),
                self._loop,
            )
            try:
                fut.result(timeout=0.1)
            except Exception:
                pass

        except Exception as e:
            logger.error("OpenIM webhook handle error: {}", e)

    def _try_mark_read(self, event: dict[str, Any], peer_user_id: str) -> None:
        """
        Prefer mark_msgs_as_read (needs seq).
        Fallback to mark_conversation_as_read using maxSeq with retry/backoff and lastReadSeq cache.
        """
        try:
            conversation_id = event.get("conversationID")
            if not conversation_id:
                conversation_id = build_single_conversation_id(peer_user_id, self.config.bot_user_id)
            conversation_id = str(conversation_id)

            # 1) Try per-message seq
            seq = self._extract_seq_from_event(event)
            if seq and seq >= 1:
                try:
                    self._client.mark_msgs_as_read(
                        bot_user_id=self.config.bot_user_id,
                        bot_platform_id=self.config.bot_platform_id,
                        conversation_id=conversation_id,
                        seqs=[seq],
                    )
                    self._set_last_read_seq(conversation_id, seq)
                    return
                except Exception:
                    pass  # fallback

            # 2) Fallback: query maxSeq and mark conversation as read
            last = self._get_last_read_seq(conversation_id)

            # retry 4 times: 0ms / 200ms / 400ms / 800ms
            for d in (0.0, 0.2, 0.4, 0.8):
                if d > 0:
                    time.sleep(d)

                seqs_map = self._client.get_conversations_has_read_and_max_seq(
                    bot_user_id=self.config.bot_user_id,
                    bot_platform_id=self.config.bot_platform_id,
                    conversation_ids=[conversation_id],
                )
                info = seqs_map.get(conversation_id) or {}
                max_seq = _to_int_or_none(info.get("maxSeq")) or 0
                has_read = _to_int_or_none(info.get("hasReadSeq")) or 0
                target = max(max_seq, has_read)

                if target <= 0:
                    continue
                if target <= last:
                    continue

                self._client.mark_conversation_as_read(
                    bot_user_id=self.config.bot_user_id,
                    bot_platform_id=self.config.bot_platform_id,
                    conversation_id=conversation_id,
                    has_read_seq=target,
                    seqs=[],
                )
                self._set_last_read_seq(conversation_id, target)
                return

        except Exception as e:
            logger.debug("OpenIM mark-read failed (ignored): {}", e)