"""NPC interaction state and periodic ambient-dialogue cache."""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Callable

from agents import NPC_ROLES
from batch_generator import NPCBatchGenerator


@dataclass(frozen=True)
class NPCPosition:
    x: float
    y: float


@dataclass(frozen=True)
class NPCState:
    npc_id: str
    npc_name: str
    npc_title: str
    position: NPCPosition
    is_busy: bool = False
    current_action: str = "idle"
    busy_player_id: str | None = None
    last_interaction: str | None = None
    background_dialogue: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


STATE_POSITIONS = {
    "张三": NPCPosition(x=300, y=200),
    "李四": NPCPosition(x=500, y=200),
    "王五": NPCPosition(x=700, y=200),
}


class NPCStateManager:
    """Track busy state and periodically refresh all ambient dialogue."""

    def __init__(
        self,
        batch_generator: NPCBatchGenerator | None = None,
        update_interval: int = 30,
        error_reporter: Callable[[str], None] | None = None,
        refresh_reporter: Callable[[dict[str, str]], None] | None = None,
    ) -> None:
        if update_interval < 1:
            raise ValueError("update_interval 必须大于 0")
        self.batch_generator = batch_generator
        self.update_interval = update_interval
        self._error_reporter = error_reporter
        self._refresh_reporter = refresh_reporter
        self._lock = RLock()
        self._refresh_lock = asyncio.Lock()
        self._update_task: asyncio.Task[None] | None = None
        self._running = False
        self._last_update: datetime | None = None
        self._next_update_at: datetime | None = None
        self._aliases = {
            role.npc_id: role.name for role in NPC_ROLES.values()
        }
        self._states = {
            role.name: NPCState(
                npc_id=role.npc_id,
                npc_name=role.name,
                npc_title=role.title,
                position=STATE_POSITIONS[role.name],
            )
            for role in NPC_ROLES.values()
        }

    @property
    def running(self) -> bool:
        return self._running

    def _resolve_name(self, npc_name_or_id: str) -> str | None:
        candidate = npc_name_or_id.strip()
        if candidate in self._states:
            return candidate
        return self._aliases.get(candidate)

    def get_npc_state(self, npc_name_or_id: str) -> dict[str, object] | None:
        name = self._resolve_name(npc_name_or_id)
        if name is None:
            return None
        with self._lock:
            return self._states[name].to_dict()

    def get_all_npc_states(self) -> list[dict[str, object]]:
        with self._lock:
            return [
                self._states[name].to_dict()
                for name in NPC_ROLES
            ]

    def get_npc_count(self) -> int:
        return len(self._states)

    def is_npc_busy(self, npc_name_or_id: str) -> bool:
        state = self.get_npc_state(npc_name_or_id)
        return bool(state and state["is_busy"])

    def try_begin_dialogue(
        self,
        npc_name_or_id: str,
        player_id: str,
    ) -> bool:
        """Atomically reserve an NPC so check and update cannot race."""
        name = self._resolve_name(npc_name_or_id)
        if name is None:
            return False
        normalized_player = player_id.strip()
        if not normalized_player:
            raise ValueError("player_id 不能为空")
        with self._lock:
            current = self._states[name]
            if current.is_busy:
                return False
            self._states[name] = replace(
                current,
                is_busy=True,
                busy_player_id=normalized_player,
                current_action=f"与 {normalized_player} 对话",
                last_interaction=datetime.now(timezone.utc).isoformat(),
            )
        return True

    def finish_dialogue(
        self,
        npc_name_or_id: str,
        player_id: str,
    ) -> None:
        name = self._resolve_name(npc_name_or_id)
        if name is None:
            return
        with self._lock:
            current = self._states[name]
            if current.busy_player_id not in {None, player_id}:
                return
            self._states[name] = replace(
                current,
                is_busy=False,
                busy_player_id=None,
                current_action="idle",
                last_interaction=datetime.now(timezone.utc).isoformat(),
            )

    async def start(self, refresh_immediately: bool = True) -> None:
        """Start one cancellable scheduler; optionally populate the cache now."""
        if self._running or self.batch_generator is None:
            return
        self._running = True
        if refresh_immediately:
            try:
                await self._refresh_once()
            except Exception as error:
                self._report_error(f"NPC 背景对白首次更新失败：{error}")
        self._schedule_next_update()
        self._update_task = asyncio.create_task(
            self._auto_update_loop(),
            name="cyber-town-npc-state-updater",
        )

    async def stop(self) -> None:
        self._running = False
        task = self._update_task
        self._update_task = None
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    async def force_update(self) -> dict[str, str]:
        if self.batch_generator is None:
            raise RuntimeError("未配置批量背景对白生成器")
        return await self._refresh_once()

    async def _auto_update_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self.update_interval)
                await self._refresh_once()
            except asyncio.CancelledError:
                break
            except Exception as error:
                self._report_error(f"NPC 背景对白自动更新失败：{error}")
            finally:
                if self._running:
                    self._schedule_next_update()

    async def _refresh_once(self) -> dict[str, str]:
        if self.batch_generator is None:
            raise RuntimeError("未配置批量背景对白生成器")
        async with self._refresh_lock:
            dialogues = await asyncio.to_thread(
                self.batch_generator.generate_batch_dialogues,
            )
            now = datetime.now(timezone.utc)
            with self._lock:
                for name, dialogue in dialogues.items():
                    current = self._states[name]
                    self._states[name] = replace(
                        current,
                        background_dialogue=dialogue,
                    )
                self._last_update = now
                self._next_update_at = now + timedelta(
                    seconds=self.update_interval,
                )
            if self._refresh_reporter is not None:
                self._refresh_reporter(dict(dialogues))
            return dict(dialogues)

    def get_current_state(self) -> dict[str, object]:
        with self._lock:
            dialogues = {
                name: state.background_dialogue
                for name, state in self._states.items()
                if state.background_dialogue is not None
            }
            last_update = self._last_update
            next_update_at = self._next_update_at
            states = [self._states[name].to_dict() for name in NPC_ROLES]
        now = datetime.now(timezone.utc)
        next_update_in = (
            max(0, int((next_update_at - now).total_seconds()))
            if next_update_at is not None
            else self.update_interval
        )
        return {
            "npcs": states,
            "dialogues": dialogues,
            "last_update": last_update.isoformat() if last_update else None,
            "next_update_in": next_update_in,
            "update_interval": self.update_interval,
            "scheduler_running": self._running,
        }

    def get_npc_dialogue(self, npc_name_or_id: str) -> str | None:
        state = self.get_npc_state(npc_name_or_id)
        if state is None:
            return None
        value = state["background_dialogue"]
        return str(value) if value is not None else None

    def _schedule_next_update(self) -> None:
        with self._lock:
            self._next_update_at = datetime.now(timezone.utc) + timedelta(
                seconds=self.update_interval,
            )

    def _report_error(self, message: str) -> None:
        if self._error_reporter is not None:
            self._error_reporter(message)


# The chapter uses StateManager while the official project uses NPCStateManager.
StateManager = NPCStateManager
