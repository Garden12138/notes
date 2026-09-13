"""Persist task evidence and the final report for the research workflow."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from hello_agents.tools import NoteTool

try:
    from ..models import SearchResult, TodoItem
except ImportError:  # Support imports with ``backend/src`` on sys.path.
    from models import SearchResult, TodoItem  # type: ignore[no-redef]


class NotesService:
    """Adapt NoteTool to the coordinator's task and report contracts."""

    def __init__(
        self,
        workspace: str,
        *,
        note_tool: NoteTool | None = None,
    ) -> None:
        self.workspace = Path(workspace).expanduser().resolve()
        self.notes_directory = self.workspace / "notes"
        self.reports_directory = self.workspace / "reports"
        self.notes_directory.mkdir(parents=True, exist_ok=True)
        self.reports_directory.mkdir(parents=True, exist_ok=True)
        self.note_tool = note_tool or NoteTool(
            workspace=str(self.notes_directory),
        )

    def record(self, task: TodoItem) -> str:
        """Record one completed task and return its persistent note ID."""
        return self.save_task_summary(
            task,
            task.sources,
            task.summary or "",
        )

    def save_task_summary(
        self,
        task: TodoItem,
        search_results: Sequence[SearchResult],
        summary: str,
    ) -> str:
        """Create a task note, or update it when a note ID is already known."""
        normalized_summary = summary.strip()
        if not normalized_summary:
            raise ValueError("任务总结不能为空")
        content = self._format_note_content(
            task,
            search_results,
            normalized_summary,
        )
        common = {
            "title": f"任务{task.id}：{task.title}",
            "content": content,
            "note_type": "task_state",
            "tags": ["research", "summary", f"task-{task.id}"],
        }

        if task.note_id:
            result = self.note_tool.run(
                {
                    "action": "update",
                    "note_id": task.note_id,
                    **common,
                },
            )
            self._raise_for_tool_error(result)
            return task.note_id

        result = self.note_tool.run({"action": "create", **common})
        self._raise_for_tool_error(result)
        note_id = str(result).strip()
        if not note_id:
            raise RuntimeError("NoteTool 未返回笔记 ID")
        return note_id

    def save_report(self, topic: str, report_markdown: str) -> str:
        """Atomically replace the stable final report file."""
        normalized_topic = topic.strip()
        normalized_report = report_markdown.strip()
        if not normalized_topic:
            raise ValueError("研究主题不能为空")
        if not normalized_report:
            raise ValueError("研究报告不能为空")

        report_path = self.reports_directory / "final_report.md"
        temporary_path = report_path.with_name(".final_report.md.tmp")
        temporary_path.write_text(normalized_report + "\n", encoding="utf-8")
        temporary_path.replace(report_path)
        return str(report_path)

    @staticmethod
    def _format_note_content(
        task: TodoItem,
        search_results: Sequence[SearchResult],
        summary: str,
    ) -> str:
        lines = [
            f"# 任务{task.id}：{task.title}",
            "",
            "## 任务信息",
            "",
            f"- **意图**：{task.intent}",
            f"- **查询**：{task.query}",
            "",
            "## 搜索结果",
            "",
        ]
        if not search_results:
            lines.append("未检索到可用来源。")
        for index, result in enumerate(search_results, start=1):
            lines.extend(
                [
                    f"[{index}] {result.title}",
                    f"URL: {result.url}",
                    f"摘要: {result.snippet}",
                    "",
                ],
            )
        lines.extend(["", "## 总结", "", summary])
        return "\n".join(lines).strip()

    @staticmethod
    def _raise_for_tool_error(result: Any) -> None:
        if isinstance(result, str) and result.startswith("错误："):
            raise RuntimeError(result.removeprefix("错误：").strip())

