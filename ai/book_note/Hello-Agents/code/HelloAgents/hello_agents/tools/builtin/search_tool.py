"""Tavily and SerpApi search with deterministic fallback order."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from typing import Any

from ..base import Tool, ToolParameter


SerpApiFactory = Callable[[dict[str, Any]], Any]
_SUPPORTED_BACKENDS = {"hybrid", "tavily", "serpapi"}


class SearchTool(Tool):
    """Multi-source search tool used in chapter 7.5."""

    def __init__(
        self,
        backend: str = "hybrid",
        tavily_key: str | None = None,
        serpapi_key: str | None = None,
        *,
        tavily_client: Any | None = None,
        serpapi_factory: SerpApiFactory | None = None,
    ) -> None:
        if backend not in _SUPPORTED_BACKENDS:
            supported = "、".join(sorted(_SUPPORTED_BACKENDS))
            raise ValueError(
                f"不支持搜索后端 '{backend}'，可选值：{supported}",
            )

        super().__init__(
            name="search",
            description=(
                "智能网页搜索工具；hybrid 模式优先使用 Tavily，"
                "失败时降级到 SerpApi。"
            ),
        )
        self.backend = backend
        self.tavily_key = tavily_key or os.getenv("TAVILY_API_KEY")
        self.serpapi_key = serpapi_key or os.getenv("SERPAPI_API_KEY")
        self.tavily_client = tavily_client
        self.serpapi_factory = serpapi_factory
        self.available_backends: list[str] = []
        self._setup_backends()

    def _setup_backends(self) -> None:
        """Initialize only the clients that can actually be used."""
        if self.tavily_client is not None:
            self.available_backends.append("tavily")
        elif self.tavily_key:
            try:
                from tavily import TavilyClient
            except ImportError:
                pass
            else:
                self.tavily_client = TavilyClient(
                    api_key=self.tavily_key,
                )
                self.available_backends.append("tavily")

        if self.serpapi_factory is not None:
            self.available_backends.append("serpapi")
        elif self.serpapi_key:
            try:
                from serpapi import GoogleSearch
            except ImportError:
                pass
            else:
                self.serpapi_factory = GoogleSearch
                self.available_backends.append("serpapi")

    def run(self, parameters: dict[str, Any]) -> str:
        query = str(
            parameters.get("input")
            or parameters.get("query")
            or "",
        ).strip()
        if not query:
            return "错误：搜索查询不能为空"

        if self.backend == "tavily":
            return self._run_single_backend("tavily", query)
        if self.backend == "serpapi":
            return self._run_single_backend("serpapi", query)
        return self._search_hybrid(query)

    def search(self, query: str) -> str:
        """Convenience entry point for lightweight function registration."""
        return self.run({"input": query})

    def get_parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="input",
                type="string",
                description="需要检索的关键词或问题",
                required=True,
            ),
        ]

    def _run_single_backend(self, backend: str, query: str) -> str:
        if backend not in self.available_backends:
            return self._configuration_error(backend)
        try:
            if backend == "tavily":
                return self._search_tavily(query)
            return self._search_serpapi(query)
        except Exception as error:
            return f"错误：{backend} 搜索失败：{error}"

    def _search_hybrid(self, query: str) -> str:
        errors: list[str] = []
        if "tavily" in self.available_backends:
            try:
                return self._search_tavily(query)
            except Exception as error:
                errors.append(f"Tavily：{error}")

        if "serpapi" in self.available_backends:
            try:
                return self._search_serpapi(query)
            except Exception as error:
                errors.append(f"SerpApi：{error}")

        if errors:
            return "错误：所有搜索源均失败（" + "；".join(errors) + "）"
        return self._configuration_error("hybrid")

    def _search_tavily(self, query: str) -> str:
        if self.tavily_client is None:
            raise RuntimeError("Tavily 客户端未初始化")
        response = self.tavily_client.search(
            query=query,
            search_depth="basic",
            include_answer=True,
            max_results=3,
        )
        if not isinstance(response, Mapping):
            raise TypeError("Tavily 返回值不是字典")

        lines = [
            "Tavily AI 搜索结果",
            f"直接答案：{response.get('answer') or '未找到直接答案'}",
        ]
        results = response.get("results") or []
        for index, item in enumerate(results[:3], start=1):
            lines.extend(self._format_result(index, item, "content"))
        return "\n".join(lines)

    def _search_serpapi(self, query: str) -> str:
        if self.serpapi_factory is None:
            raise RuntimeError("SerpApi 客户端未初始化")
        search = self.serpapi_factory(
            {
                "q": query,
                "api_key": self.serpapi_key,
                "num": 3,
            },
        )
        response = search.get_dict()
        if not isinstance(response, Mapping):
            raise TypeError("SerpApi 返回值不是字典")

        lines = ["SerpApi Google 搜索结果"]
        results = response.get("organic_results") or []
        if not results:
            lines.append("未找到相关结果")
        for index, item in enumerate(results[:3], start=1):
            lines.extend(self._format_result(index, item, "snippet"))
        return "\n".join(lines)

    @staticmethod
    def _format_result(
        index: int,
        item: Mapping[str, Any],
        summary_key: str,
    ) -> list[str]:
        title = str(item.get("title") or "无标题")
        summary = str(item.get(summary_key) or "").strip()
        link = str(item.get("url") or item.get("link") or "").strip()
        if len(summary) > 200:
            summary = summary[:200] + "..."
        lines = [f"[{index}] {title}"]
        if summary:
            lines.append(f"    {summary}")
        if link:
            lines.append(f"    来源：{link}")
        return lines

    @staticmethod
    def _configuration_error(backend: str) -> str:
        if backend == "tavily":
            return (
                "错误：Tavily 不可用，请安装 tavily-python 并配置 "
                "TAVILY_API_KEY"
            )
        if backend == "serpapi":
            return (
                "错误：SerpApi 不可用，请安装 google-search-results "
                "并配置 SERPAPI_API_KEY"
            )
        return (
            "错误：没有可用的搜索源，请配置 TAVILY_API_KEY 或 "
            "SERPAPI_API_KEY，并安装对应依赖"
        )
