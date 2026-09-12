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

        prompt = REPORT_WRITER_INSTRUCTIONS.format(
            research_topic=topic,
            task_summaries=self.format_tasks(tasks),
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
        """Keep summaries and their source lists in the same task block."""
        blocks: list[str] = []
        for index, task in enumerate(tasks, start=1):
            summary = task.summary or "暂无可用信息"
            sources = "\n".join(
                f"  - [{source.title}]({source.url})"
                for source in task.sources
            ) or "  - 暂无来源"
            blocks.append(
                f"## 任务 {index}：{task.title}\n"
                f"意图：{task.intent}\n"
                f"查询：{task.query}\n\n"
                f"{summary}\n\n"
                f"来源：\n{sources}"
            )
        return "\n\n".join(blocks)
