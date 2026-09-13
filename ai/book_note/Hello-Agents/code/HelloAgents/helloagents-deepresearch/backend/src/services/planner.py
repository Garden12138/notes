"""Research planning service backed by the TODO Planner agent."""

from __future__ import annotations

import json
from collections.abc import Sequence
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
        normalized_topic = topic.strip()
        normalized_date = current_date.strip()
        if not normalized_topic:
            raise ValueError("研究主题不能为空")
        if not normalized_date:
            raise ValueError("当前日期不能为空")

        prompt = TODO_PLANNER_INSTRUCTIONS.format(
            current_date=normalized_date,
            research_topic=normalized_topic,
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
    def evaluate_plan(todo_items: Sequence[TodoDraft]) -> dict[str, Any]:
        """Apply the chapter's deterministic plan-quality heuristic."""
        score = 100
        suggestions: list[str] = []

        if len(todo_items) < 3:
            score -= 20
            suggestions.append("子任务数量过少，可能遗漏重要信息")
        elif len(todo_items) > 5:
            score -= 10
            suggestions.append("子任务数量过多，可能存在冗余")

        for task in todo_items:
            if len(task.query.split()) < 2:
                score -= 10
                suggestions.append(f"任务「{task.title}」的查询过于简单")

        return {
            "score": max(0, min(100, score)),
            "suggestions": suggestions,
        }

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
