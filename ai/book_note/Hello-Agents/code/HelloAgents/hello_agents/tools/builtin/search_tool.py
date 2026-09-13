"""Unified web search backends used by the learning framework."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterable, Mapping
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..base import Tool, ToolParameter


SerpApiFactory = Callable[[dict[str, Any]], Any]
SearchAdapter = Callable[[str, int], Any]
_SUPPORTED_BACKENDS = {
    "advanced",
    "duckduckgo",
    "hybrid",
    "perplexity",
    "searxng",
    "serpapi",
    "tavily",
}
_ADVANCED_BACKENDS = (
    "tavily",
    "duckduckgo",
    "perplexity",
    "searxng",
    "serpapi",
)


class SearchTool(Tool):
    """Search several engines through one input and output contract.

    ``hybrid`` keeps the chapter 7 fallback behavior (Tavily, then SerpApi).
    ``advanced`` queries every configured backend and merges the results.
    Callers may inject adapters for deterministic tests or private services.
    """

    def __init__(
        self,
        backend: str = "hybrid",
        tavily_key: str | None = None,
        serpapi_key: str | None = None,
        perplexity_key: str | None = None,
        searxng_url: str | None = None,
        *,
        tavily_client: Any | None = None,
        serpapi_factory: SerpApiFactory | None = None,
        duckduckgo_client: Any | None = None,
        perplexity_client: SearchAdapter | None = None,
        searxng_client: SearchAdapter | None = None,
        request_timeout: float = 30.0,
    ) -> None:
        selected_backend = self._validate_backend(backend)
        if request_timeout <= 0:
            raise ValueError("request_timeout 必须大于 0")

        super().__init__(
            name="search",
            description=(
                "统一网页搜索工具，支持 Tavily、SerpApi、DuckDuckGo、"
                "Perplexity、SearXNG，以及组合多个来源的 advanced 模式。"
            ),
        )
        self.backend = selected_backend
        self.tavily_key = tavily_key or os.getenv("TAVILY_API_KEY")
        self.serpapi_key = serpapi_key or os.getenv("SERPAPI_API_KEY")
        self.perplexity_key = perplexity_key or os.getenv(
            "PERPLEXITY_API_KEY",
        )
        self.searxng_url = (
            searxng_url or os.getenv("SEARXNG_URL") or ""
        ).rstrip("/")
        self.tavily_client = tavily_client
        self.serpapi_factory = serpapi_factory
        self.duckduckgo_client = duckduckgo_client
        self.perplexity_client = perplexity_client
        self.searxng_client = searxng_client
        self.request_timeout = float(request_timeout)
        self.available_backends: list[str] = []
        self._setup_backends()

    def _setup_backends(self) -> None:
        """Initialize optional SDK clients without making network requests."""
        if self.tavily_client is not None:
            self._mark_available("tavily")
        elif self.tavily_key:
            try:
                from tavily import TavilyClient
            except ImportError:
                pass
            else:
                self.tavily_client = TavilyClient(api_key=self.tavily_key)
                self._mark_available("tavily")

        if self.serpapi_factory is not None:
            self._mark_available("serpapi")
        elif self.serpapi_key:
            try:
                from serpapi import GoogleSearch
            except ImportError:
                pass
            else:
                self.serpapi_factory = GoogleSearch
                self._mark_available("serpapi")

        if self.duckduckgo_client is not None:
            self._mark_available("duckduckgo")
        else:
            try:
                from ddgs import DDGS
            except ImportError:
                pass
            else:
                self.duckduckgo_client = DDGS()
                self._mark_available("duckduckgo")

        if self.perplexity_client is not None or self.perplexity_key:
            self._mark_available("perplexity")

        if self.searxng_client is not None or self.searxng_url:
            self._mark_available("searxng")

    def run(self, parameters: dict[str, Any]) -> str | dict[str, Any]:
        """Execute a search in text or structured mode."""
        query = str(
            parameters.get("input") or parameters.get("query") or "",
        ).strip()
        if not query:
            return "错误：搜索查询不能为空"

        try:
            backend = self._validate_backend(
                str(parameters.get("backend") or self.backend),
            )
            mode = str(parameters.get("mode") or "text").lower().strip()
            if mode not in {"text", "structured"}:
                raise ValueError("mode 仅支持 text 或 structured")
            max_results = self._positive_integer(
                parameters.get("max_results", 5),
                "max_results",
                maximum=20,
            )
            max_tokens = self._positive_integer(
                parameters.get(
                    "max_tokens_per_source",
                    parameters.get("max_source_tokens", 2000),
                ),
                "max_tokens_per_source",
            )
        except ValueError as error:
            return f"错误：{error}"

        payload = self._dispatch(query, backend, max_results)
        payload["results"] = self.deduplicate_sources(
            [
                self.limit_source_tokens(item, max_tokens)
                for item in payload.get("results", [])
            ],
        )[:max_results]
        return payload if mode == "structured" else self._format_text(payload)

    def search(
        self,
        query: str,
        *,
        backend: str | None = None,
        max_results: int = 5,
        mode: str = "text",
    ) -> str | dict[str, Any]:
        """Convenience entry point for direct use and function registration."""
        return self.run(
            {
                "input": query,
                "backend": backend or self.backend,
                "max_results": max_results,
                "mode": mode,
            },
        )

    def get_parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="input",
                type="string",
                description="需要检索的关键词或问题",
                required=True,
            ),
            ToolParameter(
                name="backend",
                type="string",
                description=(
                    "tavily/serpapi/duckduckgo/perplexity/searxng/"
                    "hybrid/advanced"
                ),
                required=False,
                default=self.backend,
            ),
            ToolParameter(
                name="mode",
                type="string",
                description="text 返回可读文本，structured 返回统一字典",
                required=False,
                default="text",
            ),
            ToolParameter(
                name="max_results",
                type="integer",
                description="最多返回的去重结果数",
                required=False,
                default=5,
            ),
            ToolParameter(
                name="max_tokens_per_source",
                type="integer",
                description="每条摘要的近似 Token 上限",
                required=False,
                default=2000,
            ),
        ]

    def _dispatch(
        self,
        query: str,
        backend: str,
        max_results: int,
    ) -> dict[str, Any]:
        if backend == "hybrid":
            return self._search_hybrid(query, max_results)
        if backend == "advanced":
            return self._search_advanced(query, max_results)
        return self._safe_search_backend(backend, query, max_results)

    def _search_hybrid(
        self,
        query: str,
        max_results: int,
    ) -> dict[str, Any]:
        notices: list[str] = []
        for backend in ("tavily", "serpapi"):
            if backend not in self.available_backends:
                continue
            payload = self._safe_search_backend(backend, query, max_results)
            if payload["results"]:
                payload["notices"] = [*notices, *payload["notices"]]
                return payload
            notices.extend(payload["notices"])

        if not notices:
            notices.append(self._configuration_error("hybrid"))
        return self._payload("hybrid", notices=notices)

    def _search_advanced(
        self,
        query: str,
        max_results: int,
    ) -> dict[str, Any]:
        responses: list[dict[str, Any]] = []
        notices: list[str] = []
        answer: str | None = None

        for backend in _ADVANCED_BACKENDS:
            if backend not in self.available_backends:
                continue
            payload = self._safe_search_backend(backend, query, max_results)
            responses.append(payload)
            notices.extend(payload["notices"])
            if answer is None and payload.get("answer"):
                answer = str(payload["answer"])

        if not responses:
            return self._payload(
                "advanced",
                notices=[self._configuration_error("advanced")],
            )

        result_groups = [list(item["results"]) for item in responses]
        merged: list[dict[str, str]] = []
        for index in range(
            max((len(group) for group in result_groups), default=0),
        ):
            for group in result_groups:
                if index < len(group):
                    merged.append(group[index])

        used = [
            str(payload["backend"])
            for payload in responses
            if payload["results"] or payload.get("answer")
        ]
        if used:
            notices.insert(0, "组合来源：" + "、".join(used))
        return self._payload(
            "advanced",
            results=merged,
            answer=answer,
            notices=notices,
        )

    def _safe_search_backend(
        self,
        backend: str,
        query: str,
        max_results: int,
    ) -> dict[str, Any]:
        if backend not in self.available_backends:
            return self._payload(
                backend,
                notices=[self._configuration_error(backend)],
            )
        try:
            handlers = {
                "tavily": self._search_tavily,
                "serpapi": self._search_serpapi,
                "duckduckgo": self._search_duckduckgo,
                "perplexity": self._search_perplexity,
                "searxng": self._search_searxng,
            }
            return handlers[backend](query, max_results)
        except Exception as error:
            return self._payload(
                backend,
                notices=[f"错误：{backend} 搜索失败：{error}"],
            )

    def _search_tavily(
        self,
        query: str,
        max_results: int,
    ) -> dict[str, Any]:
        if self.tavily_client is None:
            raise RuntimeError("Tavily 客户端未初始化")
        response = self.tavily_client.search(
            query=query,
            search_depth="basic",
            include_answer=True,
            max_results=max_results,
        )
        data = self._as_mapping(response, "Tavily")
        results = [
            self._normalize_result(item, "content")
            for item in self._mapping_items(data.get("results"))
        ]
        return self._payload(
            "tavily",
            results=results,
        )

    def _search_serpapi(
        self,
        query: str,
        max_results: int,
    ) -> dict[str, Any]:
        if self.serpapi_factory is None:
            raise RuntimeError("SerpApi 客户端未初始化")
        search = self.serpapi_factory(
            {
                "q": query,
                "api_key": self.serpapi_key,
                "num": max_results,
            },
        )
        data = self._as_mapping(search.get_dict(), "SerpApi")
        results = [
            self._normalize_result(item, "snippet")
            for item in self._mapping_items(data.get("organic_results"))
        ]
        return self._payload("serpapi", results=results)

    def _search_duckduckgo(
        self,
        query: str,
        max_results: int,
    ) -> dict[str, Any]:
        if self.duckduckgo_client is None:
            raise RuntimeError("DuckDuckGo 客户端未初始化")
        if callable(self.duckduckgo_client):
            raw_results = self.duckduckgo_client(query, max_results)
        else:
            raw_results = self.duckduckgo_client.text(
                query,
                max_results=max_results,
            )
        results = [
            self._normalize_result(item, "body")
            for item in self._mapping_items(raw_results)
        ]
        return self._payload("duckduckgo", results=results)

    def _search_perplexity(
        self,
        query: str,
        max_results: int,
    ) -> dict[str, Any]:
        if self.perplexity_client is not None:
            response = self.perplexity_client(query, max_results)
        else:
            body = {
                "model": os.getenv("PERPLEXITY_MODEL", "sonar"),
                "messages": [{"role": "user", "content": query}],
            }
            response = self._request_json(
                "https://api.perplexity.ai/chat/completions",
                method="POST",
                body=body,
                headers={
                    "Authorization": f"Bearer {self.perplexity_key}",
                    "Content-Type": "application/json",
                },
            )
        data = self._as_mapping(response, "Perplexity")
        answer = self._extract_perplexity_answer(data)
        raw_results = data.get("search_results") or data.get("results") or []
        results = [
            self._normalize_result(
                item,
                "snippet",
                fallback_summary=answer,
            )
            for item in self._mapping_items(raw_results)
        ]
        if not results:
            for index, citation in enumerate(
                data.get("citations") or [],
                start=1,
            ):
                url = str(citation).strip()
                if url:
                    results.append(
                        {
                            "title": f"Perplexity 来源 {index}",
                            "url": url,
                            "snippet": answer or "Perplexity 未提供来源摘要",
                        },
                    )
        return self._payload(
            "perplexity",
            results=results[:max_results],
            answer=answer,
        )

    def _search_searxng(
        self,
        query: str,
        max_results: int,
    ) -> dict[str, Any]:
        if self.searxng_client is not None:
            response = self.searxng_client(query, max_results)
        else:
            query_string = urlencode(
                {"q": query, "format": "json", "language": "zh-CN"},
            )
            response = self._request_json(
                f"{self.searxng_url}/search?{query_string}",
            )
        data = self._as_mapping(response, "SearXNG")
        results = [
            self._normalize_result(item, "content")
            for item in self._mapping_items(data.get("results"))
        ]
        return self._payload("searxng", results=results[:max_results])

    def _request_json(
        self,
        url: str,
        *,
        method: str = "GET",
        body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Mapping[str, Any]:
        request = Request(
            url,
            method=method,
            data=(json.dumps(body).encode("utf-8") if body else None),
            headers=dict(headers or {}),
        )
        with urlopen(request, timeout=self.request_timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        return self._as_mapping(data, url)

    @staticmethod
    def deduplicate_sources(
        sources: Iterable[Mapping[str, Any]],
    ) -> list[dict[str, str]]:
        """Keep the first occurrence of each non-empty URL."""
        seen_urls: set[str] = set()
        unique_sources: list[dict[str, str]] = []
        for source in sources:
            url = str(source.get("url") or "").strip()
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            unique_sources.append(
                {
                    "title": str(source.get("title") or url).strip(),
                    "url": url,
                    "snippet": str(
                        source.get("snippet") or "未提供摘要",
                    ).strip(),
                },
            )
        return unique_sources

    @staticmethod
    def limit_source_tokens(
        source: Mapping[str, Any],
        max_tokens: int = 2000,
    ) -> dict[str, Any]:
        """Apply the chapter's rough estimate of four characters per token."""
        if max_tokens <= 0:
            raise ValueError("max_tokens 必须大于 0")
        result = dict(source)
        snippet = str(result.get("snippet") or "")
        max_characters = max_tokens * 4
        if len(snippet) > max_characters:
            snippet = snippet[:max_characters] + "..."
        result["snippet"] = snippet
        return result

    @staticmethod
    def _normalize_result(
        item: Mapping[str, Any],
        summary_key: str,
        *,
        fallback_summary: str | None = None,
    ) -> dict[str, str]:
        url = str(
            item.get("url") or item.get("link") or item.get("href") or "",
        ).strip()
        return {
            "title": str(item.get("title") or url or "无标题").strip(),
            "url": url,
            "snippet": str(
                item.get(summary_key)
                or item.get("content")
                or item.get("body")
                or fallback_summary
                or "未提供摘要",
            ).strip(),
        }

    @staticmethod
    def _mapping_items(value: Any) -> list[Mapping[str, Any]]:
        if not isinstance(value, Iterable) or isinstance(
            value,
            (str, bytes, Mapping),
        ):
            return []
        return [item for item in value if isinstance(item, Mapping)]

    @staticmethod
    def _as_mapping(value: Any, backend: str) -> Mapping[str, Any]:
        if isinstance(value, Mapping):
            return value
        if hasattr(value, "model_dump"):
            dumped = value.model_dump()
            if isinstance(dumped, Mapping):
                return dumped
        raise TypeError(f"{backend} 返回值不是字典")

    @staticmethod
    def _extract_perplexity_answer(data: Mapping[str, Any]) -> str | None:
        direct_answer = SearchTool._optional_text(data.get("answer"))
        if direct_answer:
            return direct_answer
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            return None
        first = choices[0]
        if not isinstance(first, Mapping):
            return None
        message = first.get("message")
        if not isinstance(message, Mapping):
            return None
        return SearchTool._optional_text(message.get("content"))

    @staticmethod
    def _optional_text(value: Any) -> str | None:
        text = str(value or "").strip()
        return text or None

    @staticmethod
    def _payload(
        backend: str,
        *,
        results: Iterable[Mapping[str, Any]] = (),
        answer: str | None = None,
        notices: Iterable[str] = (),
    ) -> dict[str, Any]:
        return {
            "results": [dict(item) for item in results],
            "backend": backend,
            "answer": answer,
            "notices": [str(notice) for notice in notices if str(notice)],
        }

    @staticmethod
    def _format_text(payload: Mapping[str, Any]) -> str:
        results = list(payload.get("results") or [])
        notices = [str(item) for item in payload.get("notices") or []]
        if not results and notices:
            return "\n".join(notices)

        backend = str(payload.get("backend") or "search")
        labels = {
            "advanced": "Advanced 多源搜索结果",
            "duckduckgo": "DuckDuckGo 搜索结果",
            "perplexity": "Perplexity 搜索结果",
            "searxng": "SearXNG 搜索结果",
            "serpapi": "SerpApi Google 搜索结果",
            "tavily": "Tavily AI 搜索结果",
        }
        lines = [labels.get(backend, f"{backend} 搜索结果")]
        answer = SearchTool._optional_text(payload.get("answer"))
        if answer:
            lines.append(f"直接答案：{answer}")
        if not results:
            lines.append("未找到相关结果")
        for index, item in enumerate(results, start=1):
            lines.append(f"[{index}] {item.get('title') or '无标题'}")
            snippet = str(item.get("snippet") or "").strip()
            url = str(item.get("url") or "").strip()
            if snippet:
                lines.append(f"    {snippet}")
            if url:
                lines.append(f"    来源：{url}")
        lines.extend(f"通知：{notice}" for notice in notices)
        return "\n".join(lines)

    def _mark_available(self, backend: str) -> None:
        if backend not in self.available_backends:
            self.available_backends.append(backend)

    @staticmethod
    def _validate_backend(backend: str) -> str:
        selected = backend.lower().strip()
        if selected not in _SUPPORTED_BACKENDS:
            supported = "、".join(sorted(_SUPPORTED_BACKENDS))
            raise ValueError(
                f"不支持搜索后端 '{backend}'，可选值：{supported}",
            )
        return selected

    @staticmethod
    def _positive_integer(
        value: Any,
        name: str,
        *,
        maximum: int | None = None,
    ) -> int:
        try:
            number = int(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{name} 必须是整数") from error
        if number <= 0:
            raise ValueError(f"{name} 必须大于 0")
        if maximum is not None and number > maximum:
            raise ValueError(f"{name} 不能大于 {maximum}")
        return number

    @staticmethod
    def _configuration_error(backend: str) -> str:
        messages = {
            "tavily": (
                "错误：Tavily 不可用，请安装 tavily-python 并配置 "
                "TAVILY_API_KEY"
            ),
            "serpapi": (
                "错误：SerpApi 不可用，请安装 google-search-results 并配置 "
                "SERPAPI_API_KEY"
            ),
            "duckduckgo": "错误：DuckDuckGo 不可用，请安装 ddgs",
            "perplexity": "错误：Perplexity 不可用，请配置 PERPLEXITY_API_KEY",
            "searxng": "错误：SearXNG 不可用，请配置 SEARXNG_URL",
            "advanced": "错误：Advanced 模式没有可用的搜索源",
        }
        if backend == "hybrid":
            return (
                "错误：没有可用的搜索源，请配置 TAVILY_API_KEY 或 "
                "SERPAPI_API_KEY，并安装对应依赖"
            )
        return messages[backend]
