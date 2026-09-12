"""Deterministic verification of the section 14.2 TODO research workflow."""

import json
import warnings
from collections.abc import Sequence
from datetime import date

warnings.filterwarnings(
    "ignore",
    message="Using `httpx` with `starlette.testclient` is deprecated.*",
)

from fastapi.testclient import TestClient

from src.agent import DeepResearchAgent
from src.config import Settings
from src.main import create_app
from src.models import SearchAPI, SearchResult, TodoDraft, TodoItem, TodoStatus
from src.streaming import encode_sse


class DemoPlanner:
    def __init__(self) -> None:
        self.received_date = ""

    def plan(self, topic: str, current_date: str) -> list[TodoDraft]:
        self.received_date = current_date
        return [
            TodoDraft(
                title="概念与范围",
                intent=f"界定“{topic}”的研究范围",
                query=f"{topic} 概念 范围",
            ),
            TodoDraft(
                title="现状与案例",
                intent=f"了解“{topic}”的现状与案例",
                query=f"{topic} 现状 案例",
            ),
            TodoDraft(
                title="限制与趋势",
                intent=f"整理“{topic}”的限制与趋势",
                query=f"{topic} 限制 趋势",
            ),
        ]


class DemoSearcher:
    def __init__(self) -> None:
        self.calls: list[tuple[str, SearchAPI | None, int]] = []

    def search(
        self,
        query: str,
        *,
        backend: SearchAPI | None,
        max_results: int,
    ) -> list[SearchResult]:
        self.calls.append((query, backend, max_results))
        return [
            SearchResult(
                title="离线测试资料",
                url="https://example.invalid/offline-fixture",
                snippet="这是验证数据流的固定夹具，不代表真实搜索结果。",
            )
        ]


class DemoSummarizer:
    def summarize(
        self,
        task: TodoItem,
        search_results: Sequence[SearchResult],
    ) -> str:
        assert search_results
        return f"## {task.title}\n\n离线流程验证摘要。[1]"


class DemoNoteWriter:
    def __init__(self) -> None:
        self.recorded: list[int] = []

    def record(self, task: TodoItem) -> str:
        self.recorded.append(task.id)
        return f"demo-note-{task.id}"


class DemoReporter:
    def write(self, topic: str, tasks: Sequence[TodoItem]) -> str:
        assert all(task.status == TodoStatus.COMPLETED for task in tasks)
        sections = "\n\n".join(task.summary or "" for task in tasks)
        return f"# {topic}\n\n{sections}\n\n## 参考资料\n\n[1] 离线测试夹具"


class FailingSearcher(DemoSearcher):
    def search(
        self,
        query: str,
        *,
        backend: SearchAPI | None,
        max_results: int,
    ) -> list[SearchResult]:
        super().search(query, backend=backend, max_results=max_results)
        raise RuntimeError("离线失败夹具")


def build_agent(
    *,
    planner: DemoPlanner | None = None,
    searcher: DemoSearcher | None = None,
    notes: DemoNoteWriter | None = None,
) -> DeepResearchAgent:
    return DeepResearchAgent(
        planner=planner or DemoPlanner(),
        searcher=searcher or DemoSearcher(),
        summarizer=DemoSummarizer(),
        note_writer=notes or DemoNoteWriter(),
        reporter=DemoReporter(),
        clock=lambda: date(2026, 9, 12),
        max_results=5,
    )


def main() -> None:
    planner = DemoPlanner()
    searcher = DemoSearcher()
    notes = DemoNoteWriter()
    agent = build_agent(planner=planner, searcher=searcher, notes=notes)

    events = list(
        agent.run_stream("自动化深度研究", SearchAPI.DUCKDUCKGO)
    )
    event_types = [event.type for event in events]
    assert event_types[0] == "status"
    assert event_types[-2:] == ["report", "done"]
    assert planner.received_date == "2026-09-12"
    assert len(searcher.calls) == 3
    assert all(
        backend == SearchAPI.DUCKDUCKGO and limit == 5
        for _, backend, limit in searcher.calls
    )
    assert notes.recorded == [1, 2, 3]
    completed = [
        event.task
        for event in events
        if event.type == "task"
        and event.task is not None
        and event.task.status == TodoStatus.COMPLETED
    ]
    assert [task.id for task in completed] == [1, 2, 3]
    assert all(task.sources for task in completed)
    assert all(frame.endswith("\n\n") for frame in map(encode_sse, events))

    result = build_agent().run(
        "自动化深度研究",
        SearchAPI.DUCKDUCKGO,
    )
    assert len(result.todo_items) == 3
    assert result.report_markdown.startswith("# 自动化深度研究")

    failure_events = []
    try:
        failure_events.extend(
            build_agent(searcher=FailingSearcher()).run_stream(
                "失败状态验证",
                SearchAPI.DUCKDUCKGO,
            )
        )
    except RuntimeError as exc:
        assert str(exc) == "离线失败夹具"
    assert failure_events[-1].task is not None
    assert failure_events[-1].task.status == TodoStatus.FAILED

    api_searcher = DemoSearcher()
    app = create_app(
        settings=Settings(_env_file=None),
        runner_factory=lambda request: build_agent(searcher=api_searcher),
    )
    response = TestClient(app).post(
        "/research/stream",
        json={
            "topic": "自动化深度研究",
            "search_api": "perplexity",
        },
    )
    assert response.status_code == 200
    api_events = [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    assert api_events[-1]["type"] == "done"
    assert all(
        backend == SearchAPI.PERPLEXITY
        for _, backend, _ in api_searcher.calls
    )
    unavailable = TestClient(
        create_app(settings=Settings(_env_file=None))
    ).post(
        "/research/stream",
        json={"topic": "自动化深度研究"},
    )
    assert unavailable.status_code == 503

    print("=== 14.2 TODO 驱动研究离线验证 ===")
    print("todo_tasks: 3")
    print(f"stream_events: {len(events)}")
    print("todo_drafts_numbered: ready")
    print("planning_date_forwarded: ready")
    print("selected_search_backend: ready")
    print("task_state_transitions: ready")
    print("source_preservation: ready")
    print("failure_state: ready")
    print("sse_frames: ready")
    print("fastapi_stream_route: ready")
    print("report_collection: ready")
    print("external_api_calls: 0")


if __name__ == "__main__":
    main()
