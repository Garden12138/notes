"""Final report service backed by the Report Writer agent."""

from __future__ import annotations

from collections.abc import Sequence

try:
    from ..models import TodoItem, TodoStatus
    from ..prompts import REPORT_WRITER_INSTRUCTIONS
    from .common import AgentRunner
except ImportError:  # Support imports when ``src`` is placed on sys.path.
    from models import TodoItem, TodoStatus  # type: ignore[no-redef]
    from prompts import REPORT_WRITER_INSTRUCTIONS  # type: ignore[no-redef]
    from services.common import AgentRunner  # type: ignore[no-redef]


class ReportingService:
    """Combine completed task summaries without reopening the research scope."""

    def __init__(self, agent: AgentRunner) -> None:
        self._agent = agent

    def write(self, topic: str, tasks: Sequence[TodoItem]) -> str:
        if not tasks:
            raise ValueError("没有可用于生成报告的任务")
        if any(task.status != TodoStatus.COMPLETED for task in tasks):
            raise ValueError("Report Writer 只能接收已完成任务")

        task_summaries = [
            (
                task,
                task.summary or "",
                [source.url for source in task.sources],
            )
            for task in tasks
        ]
        return self.generate_report(topic, task_summaries)

    def generate_report(
        self,
        research_topic: str,
        task_summaries: Sequence[tuple[TodoItem, str, Sequence[str]]],
    ) -> str:
        """Generate one report from the chapter's task-summary tuples."""
        normalized_topic = research_topic.strip()
        if not normalized_topic:
            raise ValueError("研究主题不能为空")
        if not task_summaries:
            raise ValueError("没有可用于生成报告的任务总结")
        if any(not summary.strip() for _, summary, _ in task_summaries):
            raise ValueError("Report Writer 只能接收非空任务总结")

        prompt = REPORT_WRITER_INSTRUCTIONS.format(
            research_topic=normalized_topic,
            task_summaries=self.format_summaries(task_summaries),
        )
        try:
            response = self._agent.run(prompt).strip()
        finally:
            self._agent.clear_history()
        if not response:
            raise ValueError("Report Writer 没有生成报告")
        return response

    @staticmethod
    def format_tasks(tasks: Sequence[TodoItem]) -> str:
        """Compatibility helper for callers that already hold TodoItem values."""
        task_summaries = [
            (
                task,
                task.summary or "暂无可用信息",
                [source.url for source in task.sources],
            )
            for task in tasks
        ]
        return ReportingService.format_summaries(task_summaries)

    @staticmethod
    def format_summaries(
        task_summaries: Sequence[tuple[TodoItem, str, Sequence[str]]],
    ) -> str:
        """Keep each summary and its source URLs in one numbered task block."""
        blocks: list[str] = []
        for index, (task, summary, source_urls) in enumerate(
            task_summaries,
            start=1,
        ):
            sources = "\n".join(f"  - {url}" for url in source_urls)
            sources = sources or "  - 暂无来源"
            blocks.append(
                f"## 任务 {index}：{task.title}\n"
                f"意图：{task.intent}\n"
                f"{summary.strip()}\n\n"
                f"来源：\n{sources}"
            )
        return "\n\n".join(blocks)
