"""Deterministic verification for chapter 14.5's four core services."""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import date
from tempfile import TemporaryDirectory

from src.agent import DeepResearchAgent
from src.config import Settings
from src.models import ResearchRequest, SearchAPI, SearchResult, TodoDraft
from src.services import (
    NotesService,
    PlanningService,
    ReportingService,
    SummarizationService,
)
from src.services.search import SearchService
from src.services.composition import build_runner_factory


class ScriptedAgent:
    """Return fixed model responses while retaining prompts for assertions."""

    def __init__(self, responses: Sequence[str]) -> None:
        self._responses = list(responses)
        self.prompts: list[str] = []
        self.clear_count = 0

    def run(self, input_text: str, **kwargs: object) -> str:
        del kwargs
        self.prompts.append(input_text)
        if not self._responses:
            raise RuntimeError("没有剩余的脚本化响应")
        return self._responses.pop(0)

    def clear_history(self) -> None:
        self.clear_count += 1


class CountingSearchTool:
    """Expose duplicate and long results without calling a search service."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def run(self, parameters: dict[str, object]) -> dict[str, object]:
        self.calls.append(dict(parameters))
        query = str(parameters["input"])
        return {
            "backend": parameters["backend"],
            "answer": f"{query} 的固定答案",
            "notices": [],
            "results": [
                {
                    "title": "首个来源",
                    "url": f"https://example.invalid/{query}/shared",
                    "snippet": "甲" * 40,
                },
                {
                    "title": "重复来源",
                    "url": f"https://example.invalid/{query}/shared",
                    "snippet": "重复内容",
                },
                {
                    "title": "补充来源",
                    "url": f"https://example.invalid/{query}/second",
                    "snippet": "补充内容",
                },
            ],
        }


def main() -> None:
    planner_agent = ScriptedAgent(
        [
            "规划如下：\n"
            + json.dumps(
                {
                    "tasks": [
                        {
                            "title": "服务职责",
                            "intent": "梳理服务层边界",
                            "query": "服务层 测试",
                        },
                        {
                            "title": "数据交接",
                            "intent": "检查结构化输入输出",
                            "query": "数据 交接",
                        },
                        {
                            "title": "错误边界",
                            "intent": "检查异常和缓存行为",
                            "query": "错误 缓存",
                        },
                    ]
                },
                ensure_ascii=False,
            )
            + "\n规划结束。"
        ]
    )
    summarizer_agent = ScriptedAgent(
        [
            "## 服务职责\n\n服务封装模型与工具调用。[1]",
            "## 数据交接\n\n任务总结同时保留来源。[1]",
            "## 错误边界\n\n缓存只保存有效结果。[1]",
        ]
    )
    reporter_agent = ScriptedAgent(
        ["# 服务层实现\n\n## 概述\n\n四个服务完成线性研究流程。"]
    )
    planner = PlanningService(planner_agent)
    summarizer = SummarizationService(summarizer_agent)
    reporter = ReportingService(reporter_agent)
    search_tool = CountingSearchTool()

    weak_plan = [
        TodoDraft(title="概念", intent="了解概念", query="服务层"),
        TodoDraft(title="实现", intent="了解实现", query="缓存"),
    ]
    evaluation = planner.evaluate_plan(weak_plan)
    assert evaluation == {
        "score": 60,
        "suggestions": [
            "子任务数量过少，可能遗漏重要信息",
            "任务「概念」的查询过于简单",
            "任务「实现」的查询过于简单",
        ],
    }

    with TemporaryDirectory(prefix="helloagents-service-layer-") as temporary:
        settings = Settings(
            search_api="tavily",
            notes_workspace=f"{temporary}/workspace",
            search_cache_dir=f"{temporary}/cache/search",
        )
        searcher = SearchService(
            settings,
            search_tool=search_tool,  # type: ignore[arg-type]
            max_tokens_per_source=2,
        )
        notes = NotesService(settings.notes_workspace)

        first_results = searcher.search(
            "服务层 测试",
            backend=SearchAPI.TAVILY,
            max_results=5,
        )
        cached_results = searcher.search(
            "  服务层   测试  ",
            backend=SearchAPI.TAVILY,
            max_results=5,
        )
        assert first_results == cached_results
        assert len(first_results) == 2
        assert first_results[0].snippet == "甲" * 8 + "..."
        assert len(search_tool.calls) == 1
        assert searcher.last_cache_hit is True

        coordinator = DeepResearchAgent(
            planner=planner,
            searcher=searcher,
            summarizer=summarizer,
            note_writer=notes,
            reporter=reporter,
            report_store=notes,
            clock=lambda: date(2026, 9, 13),
        )
        result = coordinator.run("服务层实现", SearchAPI.TAVILY)

        assert len(result.todo_items) == 3
        assert all(task.summary and task.note_id for task in result.todo_items)
        assert result.report_path
        assert len(search_tool.calls) == 3
        assert planner_agent.clear_count == 1
        assert summarizer_agent.clear_count == 3
        assert reporter_agent.clear_count == 1
        assert "规划如下" not in result.report_markdown
        assert "https://example.invalid" in reporter_agent.prompts[0]

        first_summary, first_urls = (
            result.todo_items[0].summary,
            [source.url for source in result.todo_items[0].sources],
        )
        assert first_summary
        assert len(first_urls) == 2
        assert notes.reports_directory.joinpath("final_report.md").is_file()

        configured_settings = Settings(
            llm_provider="custom",
            llm_model_id="fixture-model",
            llm_api_key="fixture-key",
            llm_base_url="https://example.invalid/v1",
            search_api="duckduckgo",
            notes_workspace=f"{temporary}/configured-workspace",
            search_cache_dir=f"{temporary}/configured-cache/search",
        )
        runner_factory = build_runner_factory(configured_settings)
        first_runner = runner_factory(ResearchRequest(topic="服务层实现"))
        second_runner = runner_factory(ResearchRequest(topic="服务层实现"))
        assert first_runner is not second_runner
        assert first_runner._planner is not second_runner._planner

        print("=== 14.5 服务层实现离线验证 ===")
        print("core_services: 4")
        print(f"plan_quality_score: {evaluation['score']}")
        print("planner_robust_json: ready")
        print("summary_source_urls: ready")
        print("report_context: ready")
        print("search_deduplication: ready")
        print("search_token_limit: ready")
        print("search_cache_hit: ready")
        print("request_scoped_workflow: ready")
        print("external_api_calls: 0")


if __name__ == "__main__":
    main()
