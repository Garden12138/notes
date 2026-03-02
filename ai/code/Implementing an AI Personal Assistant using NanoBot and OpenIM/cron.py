"""Cron tool for scheduling reminders and tasks."""

from typing import Any

from nanobot.agent.tools.base import Tool
from nanobot.cron.service import CronService
from nanobot.cron.types import CronSchedule


class CronTool(Tool):
    """Tool to schedule reminders and recurring tasks."""

    def __init__(self, cron_service: CronService):
        self._cron = cron_service
        self._channel = ""
        self._chat_id = ""

    def set_context(self, channel: str, chat_id: str) -> None:
        """Set the current session context for delivery."""
        self._channel = channel
        self._chat_id = chat_id

    @property
    def name(self) -> str:
        return "cron"

    @property
    def description(self) -> str:
        return (
            "Schedule reminders and recurring tasks. Actions: add, list, remove.\n"
            "kind=system_event: deliver message directly (no agent).\n"
            "kind=agent_turn: execute message through agent (task mode)."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["add", "list", "remove"],
                    "description": "Action to perform",
                },
                "message": {
                    "type": "string",
                    "description": "Message for the job. For reminder: content to send. For task: instruction for agent.",
                },
                "every_seconds": {
                    "type": "integer",
                    "description": "Interval in seconds (for recurring tasks)",
                },
                "cron_expr": {
                    "type": "string",
                    "description": "Cron expression like '0 9 * * *' (for scheduled tasks)",
                },
                "at": {
                    "type": "string",
                    "description": "ISO datetime for one-time execution (e.g. '2026-02-12T10:30:00')",
                },
                "kind": {
                    "type": "string",
                    "enum": ["system_event", "agent_turn"],
                    "description": (
                        "system_event = deliver message directly (no agent). "
                        "agent_turn = run agent on message (can call tools, then reply)."
                    ),
                },
                "job_id": {
                    "type": "string",
                    "description": "Job ID (for remove)",
                },
                "after_seconds": {
                    "type": "integer",
                    "description": "One-time delay in seconds (e.g. 60 means run once after 60 seconds)"
                },
            },
            "required": ["action"],
        }

    async def execute(
        self,
        action: str,
        message: str = "",
        every_seconds: int | None = None,
        after_seconds: int | None = None,   # ✅ 新增
        cron_expr: str | None = None,
        at: str | None = None,
        kind: str | None = None,
        job_id: str | None = None,
        **kwargs: Any,
    ) -> str:
        if action == "add":
            return self._add_job(message, after_seconds, every_seconds, cron_expr, at, kind)
        elif action == "list":
            return self._list_jobs()
        elif action == "remove":
            return self._remove_job(job_id)
        return f"Unknown action: {action}"

    def _add_job(
        self,
        message: str,
        after_seconds: int | None,
        every_seconds: int | None,
        cron_expr: str | None,
        at: str | None,
        kind: str | None,
    ) -> str:
        if not message:
            return "Error: message is required for add"
        if not self._channel or not self._chat_id:
            return "Error: no session context (channel/chat_id)"

        payload_kind = (kind or "system_event").strip()
        if payload_kind not in ("system_event", "agent_turn"):
            return "Error: kind must be 'system_event' or 'agent_turn'"

        # Build schedule
        delete_after = False
        if after_seconds:
            from time import time
            at_ms = int((time() + int(after_seconds)) * 1000)
            schedule = CronSchedule(kind="at", at_ms=at_ms)
            delete_after = True
        elif every_seconds:
            schedule = CronSchedule(kind="every", every_ms=int(every_seconds) * 1000)
        elif cron_expr:
            schedule = CronSchedule(kind="cron", expr=cron_expr)
        elif at:
            from datetime import datetime

            dt = datetime.fromisoformat(at)
            at_ms = int(dt.timestamp() * 1000)
            schedule = CronSchedule(kind="at", at_ms=at_ms)
            delete_after = True
        else:
            return "Error: either every_seconds, cron_expr, or at is required"

        # deliver=True：无论是提醒(system_event)还是任务(agent_turn)，都默认投递到当前会话
        # - system_event：执行端应直接把 message 发给用户
        # - agent_turn：执行端应把 message 交给 agent，并把 agent 的 response 发给用户
        try:
            # ✅ 新签名（你按 Step2 改过 CronService.add_job 才会支持 payload_kind）
            job = self._cron.add_job(
                name=message[:30],
                schedule=schedule,
                message=message,
                deliver=True,
                channel=self._channel,
                to=self._chat_id,
                payload_kind=payload_kind,
                delete_after_run=delete_after,
            )
        except TypeError:
            # ✅ 兼容旧签名：不会报错，但也不会把 kind 写进 jobs.json
            job = self._cron.add_job(
                name=message[:30],
                schedule=schedule,
                message=message,
                deliver=True,
                channel=self._channel,
                to=self._chat_id,
                delete_after_run=delete_after,
            )

        return f"Created job '{job.name}' (id: {job.id}, kind: {payload_kind})"

    def _list_jobs(self) -> str:
        jobs = self._cron.list_jobs()
        if not jobs:
            return "No scheduled jobs."
        lines = []
        for j in jobs:
            # j.payload.kind 可能不存在（旧 jobs.json），用 getattr 安全读取
            k = getattr(getattr(j, "payload", None), "kind", None)
            if k:
                lines.append(f"- {j.name} (id: {j.id}, {j.schedule.kind}, kind={k})")
            else:
                lines.append(f"- {j.name} (id: {j.id}, {j.schedule.kind})")
        return "Scheduled jobs:\n" + "\n".join(lines)

    def _remove_job(self, job_id: str | None) -> str:
        if not job_id:
            return "Error: job_id is required for remove"
        if self._cron.remove_job(job_id):
            return f"Removed job {job_id}"
        return f"Job {job_id} not found"