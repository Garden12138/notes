"""Deterministic verification of the section 14.3 Agent system design."""

import json
from collections.abc import Callable, Sequence
from datetime import date

from src.agent import DeepResearchAgent
from src.models import SearchAPI, SearchResult, TodoItem
from src.services import PlanningService, ReportingService, SummarizationService
from src.tool_events import ToolCallRecorder


class ScriptedAgent:
    """Small stand-in exposing the ToolAwareSimpleAgent service interface."""

    def __init__(
        self,
        name: str,
        responses: Sequence[str],
        listener: Callable[[dict[str, object]], None],
    ) -> None:
        self.name = name
        self._responses = list(responses)
        self._listener = listener
        self.prompts: list[str] = []
        self.clear_count = 0

    def run(self, input_text: str, **kwargs: object) -> str:
        del kwargs
        self.prompts.append(input_text)
        if not self._responses:
            raise RuntimeError(f"{self.name} 没有剩余的离线响应")
        response = self._responses.pop(0)
        self._listener(
            {
                "agent_name": self.name,
                "tool_name": "fixture_tool",
                "parsed_parameters": {"prompt_index": len(self.prompts)},
                "result": "fixture result",
            }
        )
        return response

    def clear_history(self) -> None:
        self.clear_count += 1


class FixtureSearcher:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def search(
        self,
        query: str,
        *,
        backend: SearchAPI | None,
        max_results: int,
    ) -> list[SearchResult]:
        assert backend == SearchAPI.TAVILY
        assert max_results == 5
        self.calls.append(query)
        call_number = len(self.calls)
        return [
            SearchResult(
                title=f"资料 {call_number}-1",
                url=f"https://example.invalid/{call_number}/1",
                snippet="用于验证来源编号和 Prompt 交接的离线资料。",
            ),
            SearchResult(
                title=f"资料 {call_number}-2",
                url=f"https://example.invalid/{call_number}/2",
                snippet="这是第二条固定资料，不代表真实搜索结果。",
            ),
        ]


class FixtureNoteWriter:
    def __init__(self) -> None:
        self.task_ids: list[int] = []

    def record(self, task: TodoItem) -> str:
        self.task_ids.append(task.id)
        return f"fixture-note-{task.id}"


def main() -> None:
    recorder = ToolCallRecorder()
    planner_agent = ScriptedAgent(
        "TODO Planner",
        [
            json.dumps(
                {
                    "tasks": [
                        {
                            "title": "基础概念",
                            "intent": "界定研究对象与核心术语",
                            "query": "自动化深度研究 基础概念",
                        },
                        {
                            "title": "应用现状",
                            "intent": "梳理代表应用与当前进展",
                            "query": "自动化深度研究 应用 现状",
                        },
                        {
                            "title": "限制趋势",
                            "intent": "分析限制、风险与发展趋势",
                            "query": "自动化深度研究 限制 趋势",
                        },
                    ]
                },
                ensure_ascii=False,
            )
        ],
        recorder,
    )
    summarizer_agent = ScriptedAgent(
        "Task Summarizer",
        [
            "## 核心观点\n\n固定总结一。[1]",
            "## 核心观点\n\n固定总结二。[1]",
            "## 核心观点\n\n固定总结三。[1]",
        ],
        recorder,
    )
    reporter_agent = ScriptedAgent(
        "Report Writer",
        ["# 自动化深度研究\n\n## 概述\n\n离线报告。"],
        recorder,
    )

    planner = PlanningService(planner_agent)
    summarizer = SummarizationService(summarizer_agent)
    reporter = ReportingService(reporter_agent)
    searcher = FixtureSearcher()
    notes = FixtureNoteWriter()
    coordinator = DeepResearchAgent(
        planner=planner,
        searcher=searcher,
        summarizer=summarizer,
        note_writer=notes,
        reporter=reporter,
        clock=lambda: date(2026, 9, 12),
        tool_event_source=recorder,
    )

    events = list(
        coordinator.run_stream("自动化深度研究", SearchAPI.TAVILY)
    )
    tool_events = [event for event in events if event.type == "tool_call"]
    completed_tasks = [
        event.task
        for event in events
        if event.type == "task"
        and event.task is not None
        and event.task.status.value == "completed"
    ]

    assert len(events) == 22
    assert [task.id for task in completed_tasks] == [1, 2, 3]
    assert len(tool_events) == 5
    assert [event.detail["agent_name"] for event in tool_events] == [
        "TODO Planner",
        "Task Summarizer",
        "Task Summarizer",
        "Task Summarizer",
        "Report Writer",
    ]
    assert "2026-09-12" in planner_agent.prompts[0]
    assert "只返回 JSON" in planner_agent.prompts[0]
    assert all("[1]" in prompt and "URL:" in prompt for prompt in summarizer_agent.prompts)
    assert "## 任务 1：基础概念" in reporter_agent.prompts[0]
    assert "https://example.invalid/3/2" in reporter_agent.prompts[0]
    assert planner_agent.clear_count == 1
    assert summarizer_agent.clear_count == 3
    assert reporter_agent.clear_count == 1
    assert searcher.calls == [task.query for task in completed_tasks]
    assert notes.task_ids == [1, 2, 3]

    print("=== 14.3 智能体系统设计离线验证 ===")
    print("role_agents: 3")
    print("todo_tasks: 3")
    print("stream_events: 22")
    print("planner_json_contract: ready")
    print("summarizer_source_context: ready")
    print("reporter_task_handoff: ready")
    print("role_history_isolation: ready")
    print("tool_call_listener_bridge: ready")
    print("sequential_collaboration: ready")
    print("external_api_calls: 0")


if __name__ == "__main__":
    main()
