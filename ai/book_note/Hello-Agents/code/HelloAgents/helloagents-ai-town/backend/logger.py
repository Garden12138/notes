"""Daily dialogue logs written to both console and file."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4


class DialogueLogger:
    """Record dialogue, relationship changes, refreshes, and errors."""

    def __init__(self, log_dir: str | Path = "./logs", console: bool = True) -> None:
        self.log_dir = Path(log_dir)
        self._lock = RLock()
        self._file_date: str | None = None
        self._file_handler: logging.FileHandler | None = None
        self.logger = logging.getLogger(
            f"cyber_town.dialogue.{uuid4().hex}",
        )
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        if console:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(levelname)s - %(message)s",
                    datefmt="%H:%M:%S",
                ),
            )
            self.logger.addHandler(handler)

    @property
    def current_log_path(self) -> Path:
        today = datetime.now().astimezone().strftime("%Y-%m-%d")
        return self.log_dir / f"dialogue_{today}.log"

    def log_dialogue(
        self,
        *,
        npc_name: str,
        player_id: str,
        player_message: str,
        npc_reply: str,
        affinity: Any,
        recent_memory_count: int,
        relevant_memory_count: int,
    ) -> None:
        change = f"{affinity.change_amount:+d}"
        lines = [
            "=" * 60,
            f"NPC: {npc_name}",
            f"玩家: {player_id}",
            f"玩家消息: {player_message}",
            f"记忆: 近期 {recent_memory_count} 条，相关 {relevant_memory_count} 条",
            f"NPC 回复: {npc_reply}",
            (
                f"好感度: {affinity.old_affinity:.0f} -> "
                f"{affinity.new_affinity:.0f} ({change})，{affinity.new_level}"
            ),
            f"原因: {affinity.reason}；情感: {affinity.sentiment}",
            f"分析有效: {affinity.analysis_valid}",
            "=" * 60,
        ]
        self._emit(logging.INFO, "\n".join(lines))

    def log_state_refresh(self, dialogues: dict[str, str]) -> None:
        summary = "；".join(
            f"{name}: {dialogue}" for name, dialogue in dialogues.items()
        )
        self._emit(logging.INFO, f"NPC 背景对白已更新：{summary}")

    def log_error(self, message: str) -> None:
        self._emit(logging.ERROR, message)

    def _emit(self, level: int, message: str) -> None:
        with self._lock:
            self._ensure_file_handler()
            self.logger.log(level, message)

    def _ensure_file_handler(self) -> None:
        today = datetime.now().astimezone().strftime("%Y-%m-%d")
        if self._file_handler is not None and self._file_date == today:
            return
        self.log_dir.mkdir(parents=True, exist_ok=True)
        if self._file_handler is not None:
            self.logger.removeHandler(self._file_handler)
            self._file_handler.close()
        handler = logging.FileHandler(
            self.log_dir / f"dialogue_{today}.log",
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            ),
        )
        self.logger.addHandler(handler)
        self._file_handler = handler
        self._file_date = today

    def close(self) -> None:
        with self._lock:
            for handler in list(self.logger.handlers):
                self.logger.removeHandler(handler)
                handler.close()
            self._file_handler = None

