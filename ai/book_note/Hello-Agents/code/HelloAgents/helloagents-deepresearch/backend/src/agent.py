"""Coordinator contract for the TODO-driven research data flow."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Protocol

try:
    from .models import (
        ResearchEvent,
        ResearchResult,
        SearchResult,
        TodoItem,
        TodoStatus,
    )
except ImportError:  # Support direct execution through ``src/main.py``.
    from models import (  # type: ignore[no-redef]
        ResearchEvent,
        ResearchResult,
        SearchResult,
        TodoItem,
        TodoStatus,
    )


class Planner(Protocol):
    def plan(self, topic: str) -> list[TodoItem]: ...


class Searcher(Protocol):
    def search(self, query: str) -> list[SearchResult]: ...


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
    ) -> None:
        self._planner = planner
        self._searcher = searcher
        self._summarizer = summarizer
        self._note_writer = note_writer
        self._reporter = reporter

    @staticmethod
    def _snapshot(task: TodoItem) -> TodoItem:
        return task.model_copy(deep=True)

    def run_stream(self, topic: str) -> Iterator[ResearchEvent]:
        """Yield observable events while executing planning, research and report stages."""
        normalized_topic = topic.strip()
        if len(normalized_topic) < 2:
            raise ValueError("研究主题至少需要两个字符")

        yield ResearchEvent(type="status", message="正在规划研究任务", progress=0)
        tasks = self._planner.plan(normalized_topic)
        if not 3 <= len(tasks) <= 5:
            raise ValueError("TODO Planner 必须生成 3–5 个子任务")
        if len({task.id for task in tasks}) != len(tasks):
            raise ValueError("子任务 ID 不能重复")

        yield ResearchEvent(
            type="tasks",
            message=f"已生成 {len(tasks)} 个研究任务",
            progress=10,
            tasks=[self._snapshot(task) for task in tasks],
        )

        for index, task in enumerate(tasks, start=1):
            task.status = TodoStatus.IN_PROGRESS
            yield ResearchEvent(
                type="task",
                message=f"正在研究：{task.title}",
                progress=10 + int((index - 1) / len(tasks) * 75),
                task=self._snapshot(task),
            )

            results = self._searcher.search(task.query)
            task.sources = list(results)
            task.summary = self._summarizer.summarize(task, results).strip()
            if not task.summary:
                raise ValueError(f"任务“{task.title}”没有生成总结")
            task.note_id = self._note_writer.record(self._snapshot(task))
            task.status = TodoStatus.COMPLETED

            yield ResearchEvent(
                type="task",
                message=f"已完成：{task.title}",
                progress=10 + int(index / len(tasks) * 75),
                task=self._snapshot(task),
            )

        yield ResearchEvent(type="status", message="正在生成最终报告", progress=90)
        report = self._reporter.write(
            normalized_topic,
            [self._snapshot(task) for task in tasks],
        ).strip()
        if not report:
            raise ValueError("Report Writer 没有生成报告")
        yield ResearchEvent(type="report", report_markdown=report, progress=98)
        yield ResearchEvent(type="done", message="研究完成", progress=100)

    def run(self, topic: str) -> ResearchResult:
        """Collect the streaming workflow into one result object."""
        tasks: list[TodoItem] = []
        report = ""
        for event in self.run_stream(topic):
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
