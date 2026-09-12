"""Coordinator contract for the TODO-driven research data flow."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from datetime import date
from typing import Any, Protocol

try:
    from .models import (
        ResearchEvent,
        ResearchPhase,
        ResearchResult,
        SearchAPI,
        SearchResult,
        TodoDraft,
        TodoItem,
        TodoStatus,
    )
except ImportError:  # Support direct execution through ``src/main.py``.
    from models import (  # type: ignore[no-redef]
        ResearchEvent,
        ResearchPhase,
        ResearchResult,
        SearchAPI,
        SearchResult,
        TodoDraft,
        TodoItem,
        TodoStatus,
    )


class Planner(Protocol):
    def plan(self, topic: str, current_date: str) -> list[TodoDraft]: ...


class Searcher(Protocol):
    def search(
        self,
        query: str,
        *,
        backend: SearchAPI | None,
        max_results: int,
    ) -> list[SearchResult]: ...


class Summarizer(Protocol):
    def summarize(
        self,
        task: TodoItem,
        search_results: Sequence[SearchResult],
    ) -> str: ...


class NoteWriter(Protocol):
    def record(self, task: TodoItem) -> str | None: ...


class Reporter(Protocol):
    def write(self, topic: str, tasks: Sequence[TodoItem]) -> str: ...


class ToolEventSource(Protocol):
    def drain(self) -> list[dict[str, Any]]: ...


class DeepResearchAgent:
    """Run the eight-step research flow against injected concrete services."""

    def __init__(
        self,
        *,
        planner: Planner,
        searcher: Searcher,
        summarizer: Summarizer,
        note_writer: NoteWriter,
        reporter: Reporter,
        clock: Callable[[], date] = date.today,
        max_results: int = 5,
        tool_event_source: ToolEventSource | None = None,
    ) -> None:
        self._planner = planner
        self._searcher = searcher
        self._summarizer = summarizer
        self._note_writer = note_writer
        self._reporter = reporter
        self._clock = clock
        self._tool_event_source = tool_event_source
        if max_results < 1:
            raise ValueError("max_results 必须大于 0")
        self._max_results = max_results

    @staticmethod
    def _snapshot(task: TodoItem) -> TodoItem:
        return task.model_copy(deep=True)

    def _drain_tool_call_events(
        self,
        *,
        phase: ResearchPhase,
        progress: int,
    ) -> list[ResearchEvent]:
        if self._tool_event_source is None:
            return []
        events: list[ResearchEvent] = []
        for call in self._tool_event_source.drain():
            agent_name = str(call.get("agent_name", "unknown"))
            tool_name = str(call.get("tool_name", "unknown"))
            events.append(
                ResearchEvent(
                    type="tool_call",
                    phase=phase,
                    message=f"{agent_name} 调用工具：{tool_name}",
                    progress=progress,
                    detail=call,
                )
            )
        return events

    def run_stream(
        self,
        topic: str,
        search_api: SearchAPI | None = None,
    ) -> Iterator[ResearchEvent]:
        """Yield observable events while executing planning, research and report stages."""
        normalized_topic = topic.strip()
        if len(normalized_topic) < 2:
            raise ValueError("研究主题至少需要两个字符")

        current_date = self._clock().isoformat()
        yield ResearchEvent(
            type="status",
            phase=ResearchPhase.PLANNING,
            message="正在规划研究任务",
            progress=0,
            detail={"current_date": current_date},
        )
        try:
            drafts = self._planner.plan(normalized_topic, current_date)
        except Exception:
            yield from self._drain_tool_call_events(
                phase=ResearchPhase.FAILED,
                progress=0,
            )
            raise
        yield from self._drain_tool_call_events(
            phase=ResearchPhase.PLANNING,
            progress=5,
        )
        if not 3 <= len(drafts) <= 5:
            raise ValueError("TODO Planner 必须生成 3–5 个子任务")
        normalized_queries = {draft.query.casefold() for draft in drafts}
        if len(normalized_queries) != len(drafts):
            raise ValueError("TODO Planner 生成了重复查询")
        tasks = [
            TodoItem(id=index, **draft.model_dump())
            for index, draft in enumerate(drafts, start=1)
        ]

        yield ResearchEvent(
            type="tasks",
            phase=ResearchPhase.PLANNING,
            message=f"已生成 {len(tasks)} 个研究任务",
            progress=10,
            tasks=[self._snapshot(task) for task in tasks],
        )

        for index, task in enumerate(tasks, start=1):
            task.status = TodoStatus.IN_PROGRESS
            yield ResearchEvent(
                type="task",
                phase=ResearchPhase.EXECUTION,
                message=f"正在研究：{task.title}",
                progress=10 + int((index - 1) / len(tasks) * 75),
                task=self._snapshot(task),
            )

            try:
                yield ResearchEvent(
                    type="status",
                    phase=ResearchPhase.EXECUTION,
                    message=f"正在搜索：{task.title}",
                    progress=10 + int((index - 1) / len(tasks) * 75),
                    detail={"task_id": task.id, "query": task.query},
                )
                results = self._searcher.search(
                    task.query,
                    backend=search_api,
                    max_results=self._max_results,
                )
                task.sources = list(results)
                yield ResearchEvent(
                    type="status",
                    phase=ResearchPhase.EXECUTION,
                    message=f"正在总结：{task.title}",
                    progress=10 + int((index - 0.5) / len(tasks) * 75),
                    detail={"task_id": task.id, "source_count": len(results)},
                )
                task.summary = self._summarizer.summarize(task, results).strip()
                yield from self._drain_tool_call_events(
                    phase=ResearchPhase.EXECUTION,
                    progress=10 + int((index - 0.5) / len(tasks) * 75),
                )
                if not task.summary:
                    raise ValueError(f"任务“{task.title}”没有生成总结")
                task.note_id = self._note_writer.record(self._snapshot(task))
                yield from self._drain_tool_call_events(
                    phase=ResearchPhase.EXECUTION,
                    progress=10 + int(index / len(tasks) * 75),
                )
                task.status = TodoStatus.COMPLETED
            except Exception:
                yield from self._drain_tool_call_events(
                    phase=ResearchPhase.FAILED,
                    progress=10 + int((index - 0.5) / len(tasks) * 75),
                )
                task.status = TodoStatus.FAILED
                yield ResearchEvent(
                    type="task",
                    phase=ResearchPhase.FAILED,
                    message=f"执行失败：{task.title}",
                    task=self._snapshot(task),
                )
                raise

            yield ResearchEvent(
                type="task",
                phase=ResearchPhase.EXECUTION,
                message=f"已完成：{task.title}",
                progress=10 + int(index / len(tasks) * 75),
                task=self._snapshot(task),
            )

        yield ResearchEvent(
            type="status",
            phase=ResearchPhase.REPORTING,
            message="正在生成最终报告",
            progress=90,
        )
        try:
            report = self._reporter.write(
                normalized_topic,
                [self._snapshot(task) for task in tasks],
            ).strip()
        except Exception:
            yield from self._drain_tool_call_events(
                phase=ResearchPhase.FAILED,
                progress=90,
            )
            raise
        yield from self._drain_tool_call_events(
            phase=ResearchPhase.REPORTING,
            progress=95,
        )
        if not report:
            raise ValueError("Report Writer 没有生成报告")
        yield ResearchEvent(
            type="report",
            phase=ResearchPhase.REPORTING,
            report_markdown=report,
            progress=98,
        )
        yield ResearchEvent(
            type="done",
            phase=ResearchPhase.COMPLETED,
            message="研究完成",
            progress=100,
        )

    def run(
        self,
        topic: str,
        search_api: SearchAPI | None = None,
    ) -> ResearchResult:
        """Collect the streaming workflow into one result object."""
        tasks: list[TodoItem] = []
        report = ""
        for event in self.run_stream(topic, search_api):
            if event.type == "task" and event.task is not None:
                current = event.task
                for index, task in enumerate(tasks):
                    if task.id == current.id:
                        tasks[index] = current
                        break
                else:
                    tasks.append(current)
            elif event.type == "report" and event.report_markdown:
                report = event.report_markdown
        return ResearchResult(
            topic=topic.strip(),
            todo_items=tasks,
            report_markdown=report,
        )
