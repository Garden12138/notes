"""Research planning service backed by the TODO Planner agent."""

from __future__ import annotations

import json
from typing import Any

try:
    from ..models import TodoDraft
    from ..prompts import TODO_PLANNER_INSTRUCTIONS
    from .common import AgentRunner
except ImportError:  # Support imports when ``src`` is placed on sys.path.
    from models import TodoDraft  # type: ignore[no-redef]
    from prompts import TODO_PLANNER_INSTRUCTIONS  # type: ignore[no-redef]
    from services.common import AgentRunner  # type: ignore[no-redef]


class PlanningService:
    """Convert one research topic into validated TODO drafts."""

    def __init__(self, agent: AgentRunner) -> None:
        self._agent = agent

    def plan(self, topic: str, current_date: str) -> list[TodoDraft]:
        prompt = TODO_PLANNER_INSTRUCTIONS.format(
            current_date=current_date,
            research_topic=topic,
        )
        try:
            response = self._agent.run(prompt)
        finally:
            self._agent.clear_history()

        payload = self._extract_json(response)
        raw_tasks = payload.get("tasks") if isinstance(payload, dict) else payload
        if not isinstance(raw_tasks, list):
            raise ValueError("TODO Planner 必须返回 JSON 任务列表")

        tasks: list[TodoDraft] = []
        for raw_task in raw_tasks:
            if not isinstance(raw_task, dict):
                raise ValueError("TODO Planner 的每项任务都必须是 JSON 对象")
            tasks.append(TodoDraft.model_validate(raw_task))
        return tasks

    @staticmethod
    def _extract_json(response: str) -> dict[str, Any] | list[Any]:
        """Decode the first valid JSON object or array in the model response."""
        text = response.strip()
        decoder = json.JSONDecoder()
        for index, character in enumerate(text):
            if character not in "[{":
                continue
            try:
                payload, _ = decoder.raw_decode(text[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(payload, (dict, list)):
                return payload
        raise ValueError("无法从 TODO Planner 响应中解析 JSON")
