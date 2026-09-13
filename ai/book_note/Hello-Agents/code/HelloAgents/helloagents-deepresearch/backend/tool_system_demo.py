"""Deterministic verification for chapter 14.4's integrated tool system."""

from __future__ import annotations

from datetime import date
from tempfile import TemporaryDirectory

from hello_agents.tools import SearchTool

from src.agent import DeepResearchAgent
from src.config import Settings
from src.models import SearchAPI, SearchResult, TodoDraft, TodoItem
from src.tooling import build_research_toolset


class FakeTavilyClient:
    def search(self, **parameters):
        query = parameters["query"]
        return {
            "answer": f"{query} 的固定测试答案",
            "results": [
                {
                    "title": "共同来源",
                    "url": "https://example.com/shared",
                    "content": "甲" * 40,
                },
                {
                    "title": "Tavily 来源",
                    "url": "https://example.com/tavily",
                    "content": "Tavily 摘要",
                },
            ],
        }


def fake_duckduckgo(query: str, max_results: int):
    del max_results
    return [
        {
            "title": "重复的共同来源",
            "href": "https://example.com/shared",
            "body": f"DuckDuckGo 重复结果：{query}",
        },
        {
            "title": "DuckDuckGo 来源",
            "href": "https://example.com/duckduckgo",
            "body": "DuckDuckGo 摘要",
        },
    ]


def fake_perplexity(query: str, max_results: int):
    del max_results
    return {
        "answer": f"Perplexity 对 {query} 的固定回答",
        "search_results": [
            {
                "title": "Perplexity 来源",
                "url": "https://example.com/perplexity",
                "snippet": "Perplexity 摘要",
            },
        ],
    }


def fake_searxng(query: str, max_results: int):
    del max_results
    return {
        "results": [
            {
                "title": "SearXNG 来源",
                "url": "https://example.com/searxng",
                "content": f"SearXNG 摘要：{query}",
            },
        ],
    }


class StaticPlanner:
    def plan(self, topic: str, current_date: str) -> list[TodoDraft]:
        assert topic == "工具系统集成"
        assert current_date == "2026-09-13"
        return [
            TodoDraft(
                title=f"子任务 {index}",
                intent=f"验证第 {index} 个研究切面",
                query=f"工具系统切面 {index}",
            )
            for index in range(1, 4)
        ]


class StaticSummarizer:
    def summarize(
        self,
        task: TodoItem,
        search_results: list[SearchResult],
    ) -> str:
        return f"{task.title} 共保留 {len(search_results)} 个去重来源。[1]"


class StaticReporter:
    def write(self, topic: str, tasks: list[TodoItem]) -> str:
        assert all(task.summary for task in tasks)
        return f"# {topic}\n\n已完成 {len(tasks)} 个子任务。"


def main() -> None:
    search_tool = SearchTool(
        backend="advanced",
        tavily_client=FakeTavilyClient(),
        duckduckgo_client=fake_duckduckgo,
        perplexity_client=fake_perplexity,
        searxng_client=fake_searxng,
    )
    with TemporaryDirectory(prefix="helloagents-deepresearch-") as temporary:
        toolset = build_research_toolset(
            Settings(search_api="advanced", notes_workspace=temporary),
            search_tool=search_tool,
            max_tokens_per_source=5,
        )
        searcher = toolset.searcher
        notes = toolset.notes
        registry = toolset.registry

        first_results = searcher.search(
            "工具系统集成",
            backend=SearchAPI.ADVANCED,
            max_results=5,
        )
        assert len(first_results) == 5
        assert len({result.url for result in first_results}) == 5
        assert first_results[0].snippet == "甲" * 20 + "..."
        assert searcher.last_backend == "advanced"
        assert searcher.last_answer

        assert registry.list_tools() == ["search", "note"]
        assert "Advanced 多源搜索结果" in registry.execute_tool(
            "search",
            "工具系统集成",
        )

        coordinator = DeepResearchAgent(
            planner=StaticPlanner(),
            searcher=searcher,
            summarizer=StaticSummarizer(),
            note_writer=notes,
            reporter=StaticReporter(),
            report_store=notes,
            clock=lambda: date(2026, 9, 13),
            max_results=5,
        )
        result = coordinator.run(
            "工具系统集成",
            SearchAPI.ADVANCED,
        )

        assert len(result.todo_items) == 3
        assert all(task.note_id for task in result.todo_items)
        assert len(notes.note_tool.index) == 3
        first_note = notes.note_tool.run(
            {
                "action": "read",
                "note_id": result.todo_items[0].note_id,
            },
        )
        assert "## 搜索结果" in first_note["content"]
        assert "## 总结" in first_note["content"]
        assert result.report_path
        assert notes.reports_directory.joinpath("final_report.md").is_file()

        print("=== 14.4 工具系统集成离线验证 ===")
        print(f"registered_tools: {', '.join(registry.list_tools())}")
        print("search_backends: tavily, duckduckgo, perplexity, searxng")
        print(f"advanced_results: {len(first_results)}")
        print("deduplicated_urls: ready")
        print("source_token_limit: ready")
        print(f"task_notes: {len(notes.note_tool.index)}")
        print("final_report: ready")
        print("coordinator_persistence: ready")
        print("external_api_calls: 0")


if __name__ == "__main__":
    main()
