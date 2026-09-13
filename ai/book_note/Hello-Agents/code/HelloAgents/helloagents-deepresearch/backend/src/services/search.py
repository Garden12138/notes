"""Search scheduling, normalization and caching for deep research."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

from hello_agents.tools import SearchTool

try:
    from ..config import Settings
    from ..models import SearchAPI, SearchResult
except ImportError:  # Support direct imports with ``backend/src`` on sys.path.
    from config import Settings  # type: ignore[no-redef]
    from models import SearchAPI, SearchResult  # type: ignore[no-redef]


logger = logging.getLogger(__name__)


class SearchService:
    """Call SearchTool through the coordinator's structured search contract."""

    def __init__(
        self,
        settings: Settings,
        *,
        search_tool: SearchTool | None = None,
        cache_dir: str | Path | None = None,
        max_tokens_per_source: int = 2000,
    ) -> None:
        if max_tokens_per_source <= 0:
            raise ValueError("max_tokens_per_source 必须大于 0")

        self.settings = settings
        self.search_tool = search_tool or SearchTool(
            backend=settings.search_api.value,
            tavily_key=settings.tavily_api_key,
            perplexity_key=settings.perplexity_api_key,
            searxng_url=settings.searxng_url,
        )
        self.cache_dir = Path(
            cache_dir or settings.search_cache_dir,
        ).expanduser().resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_tokens_per_source = max_tokens_per_source

        self.last_notices: list[str] = []
        self.last_answer: str | None = None
        self.last_backend: str | None = None
        self.last_cache_hit = False
        self.last_error: str | None = None

    def search(
        self,
        query: str,
        *,
        backend: SearchAPI | None = None,
        max_results: int = 5,
        use_cache: bool = True,
    ) -> list[SearchResult]:
        """Search once, returning validated and optionally cached sources."""
        normalized_query = " ".join(query.split())
        if not normalized_query:
            raise ValueError("搜索查询不能为空")
        if not 1 <= max_results <= 20:
            raise ValueError("max_results 必须在 1–20 之间")

        selected_backend = (backend or self.settings.search_api).value
        cache_file = self.cache_dir / (
            self._generate_cache_key(
                normalized_query,
                selected_backend,
                max_results,
            )
            + ".json"
        )
        self._reset_diagnostics(selected_backend)

        if use_cache:
            cached_results = self._read_cache(cache_file)
            if cached_results is not None:
                self.last_cache_hit = True
                self.last_notices = ["命中搜索缓存"]
                logger.info("从缓存读取搜索结果：%s", normalized_query)
                return cached_results

        try:
            raw_response = self.search_tool.run(
                {
                    "input": normalized_query,
                    "backend": selected_backend,
                    "mode": "structured",
                    "max_results": max_results,
                    "max_tokens_per_source": self.max_tokens_per_source,
                }
            )
            if not isinstance(raw_response, dict):
                raise RuntimeError(str(raw_response))

            self.last_backend = str(
                raw_response.get("backend") or selected_backend,
            )
            self.last_answer = (
                str(raw_response["answer"]).strip()
                if raw_response.get("answer")
                else None
            )
            self.last_notices = [
                str(notice) for notice in raw_response.get("notices") or []
            ]
            results = self._process_results(
                raw_response.get("results") or [],
                max_results=max_results,
            )

            error_notices = [
                notice
                for notice in self.last_notices
                if notice.startswith("错误：")
            ]
            if not results and error_notices:
                self.last_error = "；".join(error_notices)
                logger.error(
                    "搜索失败：%s，错误：%s",
                    normalized_query,
                    self.last_error,
                )
            else:
                logger.info(
                    "搜索成功：%s，返回 %d 个结果",
                    normalized_query,
                    len(results),
                )

            if use_cache and results:
                self._write_cache(cache_file, results)
            return results
        except Exception as error:
            self.last_error = str(error)
            logger.error(
                "搜索失败：%s，错误：%s",
                normalized_query,
                error,
            )
            return []

    def _process_results(
        self,
        raw_results: Any,
        *,
        max_results: int,
    ) -> list[SearchResult]:
        if not isinstance(raw_results, list):
            raise ValueError("SearchTool 的 results 必须是列表")

        validated = [SearchResult.model_validate(item) for item in raw_results]
        unique = self._deduplicate_sources(validated)
        return [self._limit_source_tokens(item) for item in unique][
            :max_results
        ]

    @staticmethod
    def _deduplicate_sources(
        sources: list[SearchResult],
    ) -> list[SearchResult]:
        """Keep the first occurrence of each non-empty URL."""
        seen_urls: set[str] = set()
        unique_sources: list[SearchResult] = []
        for source in sources:
            if source.url in seen_urls:
                continue
            seen_urls.add(source.url)
            unique_sources.append(source)
        return unique_sources

    def _limit_source_tokens(self, source: SearchResult) -> SearchResult:
        """Apply the chapter's four-characters-per-token approximation."""
        max_characters = self.max_tokens_per_source * 4
        if len(source.snippet) <= max_characters:
            return source
        return source.model_copy(
            update={"snippet": source.snippet[:max_characters] + "..."},
        )

    def _generate_cache_key(
        self,
        query: str,
        backend: str,
        max_results: int,
    ) -> str:
        """Identify the inputs that can change a cached result payload."""
        content = json.dumps(
            {
                "query": query,
                "backend": backend,
                "max_results": max_results,
                "max_tokens_per_source": self.max_tokens_per_source,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _read_cache(self, cache_file: Path) -> list[SearchResult] | None:
        if not cache_file.is_file():
            return None
        try:
            payload = json.loads(cache_file.read_text(encoding="utf-8"))
            if not isinstance(payload, list):
                raise ValueError("缓存根节点必须是列表")
            return [SearchResult.model_validate(item) for item in payload]
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
            logger.warning("忽略损坏的搜索缓存 %s：%s", cache_file, error)
            return None

    @staticmethod
    def _write_cache(
        cache_file: Path,
        results: list[SearchResult],
    ) -> None:
        payload = [result.model_dump(mode="json") for result in results]
        temporary_file = cache_file.with_name(
            f".{cache_file.name}.{uuid4().hex}.tmp",
        )
        try:
            temporary_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            temporary_file.replace(cache_file)
        finally:
            temporary_file.unlink(missing_ok=True)

    def _reset_diagnostics(self, selected_backend: str) -> None:
        self.last_notices = []
        self.last_answer = None
        self.last_backend = selected_backend
        self.last_cache_hit = False
        self.last_error = None
