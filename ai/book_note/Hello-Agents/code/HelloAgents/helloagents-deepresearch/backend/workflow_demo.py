"""Deterministic test double for the coordinator; it performs no real research."""

from collections.abc import Sequence

from src.agent import DeepResearchAgent
from src.models import SearchResult, TodoItem, TodoStatus
from src.streaming import encode_sse


class DemoPlanner:
    def plan(self, topic: str) -> list[TodoItem]:
        return [
            TodoItem(
                id=1,
                title="概念与范围",
                intent=f"界定“{topic}”的研究范围",
                query=f"{topic} 概念 范围",
            ),
            TodoItem(
                id=2,
                title="现状与案例",
                intent=f"了解“{topic}”的现状与案例",
                query=f"{topic} 现状 案例",
            ),
            TodoItem(
                id=3,
                title="限制与趋势",
                intent=f"整理“{topic}”的限制与趋势",
                query=f"{topic} 限制 趋势",
            ),
        ]


class DemoSearcher:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(self, query: str) -> list[SearchResult]:
        self.queries.append(query)
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


def main() -> None:
    searcher = DemoSearcher()
    notes = DemoNoteWriter()
    agent = DeepResearchAgent(
        planner=DemoPlanner(),
        searcher=searcher,
        summarizer=DemoSummarizer(),
        note_writer=notes,
        reporter=DemoReporter(),
    )

    events = list(agent.run_stream("自动化深度研究"))
    event_types = [event.type for event in events]
    assert event_types[0] == "status"
    assert event_types[-2:] == ["report", "done"]
    assert len(searcher.queries) == 3
    assert notes.recorded == [1, 2, 3]
    assert all(frame.endswith("\n\n") for frame in map(encode_sse, events))

    result = agent.run("自动化深度研究")
    assert len(result.todo_items) == 3
    assert result.report_markdown.startswith("# 自动化深度研究")

    print("=== 14.1 研究数据流离线验证 ===")
    print("todo_tasks: 3")
    print(f"stream_events: {len(events)}")
    print("search_summary_note_cycle: ready")
    print("sse_frames: ready")
    print("report_collection: ready")
    print("external_api_calls: 0")


if __name__ == "__main__":
    main()

