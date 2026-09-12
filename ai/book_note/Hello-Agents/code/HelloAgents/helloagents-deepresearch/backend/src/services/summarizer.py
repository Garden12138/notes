"""Task summarization service backed by the Task Summarizer agent."""

from __future__ import annotations

from collections.abc import Sequence

try:
    from ..models import SearchResult, TodoItem
    from ..prompts import TASK_SUMMARIZER_INSTRUCTIONS
    from .common import AgentRunner
except ImportError:  # Support imports when ``src`` is placed on sys.path.
    from models import SearchResult, TodoItem  # type: ignore[no-redef]
    from prompts import TASK_SUMMARIZER_INSTRUCTIONS  # type: ignore[no-redef]
    from services.common import AgentRunner  # type: ignore[no-redef]


class SummarizationService:
    """Format retrieved evidence and ask one Agent for a cited summary."""

    def __init__(self, agent: AgentRunner) -> None:
        self._agent = agent

    def summarize(
        self,
        task: TodoItem,
        search_results: Sequence[SearchResult],
    ) -> str:
        prompt = TASK_SUMMARIZER_INSTRUCTIONS.format(
            task_title=task.title,
            task_intent=task.intent,
            task_query=task.query,
            search_results=self.format_sources(search_results),
        )
        try:
            response = self._agent.run(prompt).strip()
        finally:
            self._agent.clear_history()
        if not response:
            raise ValueError(f"任务“{task.title}”没有生成总结")
        return response

    @staticmethod
    def format_sources(search_results: Sequence[SearchResult]) -> str:
        """Number sources once so the Agent can emit stable local citations."""
        if not search_results:
            return "暂无搜索结果"
        return "\n\n".join(
            (
                f"[{index}] {result.title}\n"
                f"URL: {result.url}\n"
                f"摘要: {result.snippet}"
            )
            for index, result in enumerate(search_results, start=1)
        )
