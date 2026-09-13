"""Create and adapt the chapter 14.4 search and note tools."""

from __future__ import annotations

from dataclasses import dataclass

from hello_agents.tools import NoteTool, SearchTool, ToolRegistry

try:
    from .config import Settings
    from .models import SearchAPI, SearchResult
    from .services.notes import NotesService
except ImportError:  # Support direct imports with ``backend/src`` on sys.path.
    from config import Settings  # type: ignore[no-redef]
    from models import SearchAPI, SearchResult  # type: ignore[no-redef]
    from services.notes import NotesService  # type: ignore[no-redef]


class SearchToolAdapter:
    """Expose SearchTool through the coordinator's structured Searcher API."""

    def __init__(
        self,
        search_tool: SearchTool,
        *,
        max_tokens_per_source: int = 2000,
    ) -> None:
        if max_tokens_per_source <= 0:
            raise ValueError("max_tokens_per_source 必须大于 0")
        self.search_tool = search_tool
        self.max_tokens_per_source = max_tokens_per_source
        self.last_notices: list[str] = []
        self.last_answer: str | None = None
        self.last_backend: str | None = None

    def search(
        self,
        query: str,
        *,
        backend: SearchAPI | None,
        max_results: int,
    ) -> list[SearchResult]:
        selected_backend = backend.value if backend else self.search_tool.backend
        response = self.search_tool.run(
            {
                "input": query,
                "backend": selected_backend,
                "mode": "structured",
                "max_results": max_results,
                "max_tokens_per_source": self.max_tokens_per_source,
            },
        )
        if not isinstance(response, dict):
            raise RuntimeError(str(response))

        self.last_backend = str(response.get("backend") or selected_backend)
        self.last_answer = (
            str(response["answer"]).strip()
            if response.get("answer")
            else None
        )
        self.last_notices = [
            str(notice) for notice in response.get("notices") or []
        ]
        results = response.get("results") or []
        return [SearchResult.model_validate(result) for result in results]


@dataclass(frozen=True)
class ResearchToolset:
    """Objects created together at the tool-system composition boundary."""

    registry: ToolRegistry
    search_tool: SearchTool
    note_tool: NoteTool
    searcher: SearchToolAdapter
    notes: NotesService


def build_tool_registry(
    search_tool: SearchTool,
    note_tool: NoteTool,
) -> ToolRegistry:
    """Register the two tools required by the deep-research agents."""
    registry = ToolRegistry()
    registry.register_tool(search_tool)
    registry.register_tool(note_tool)
    return registry


def build_research_toolset(
    settings: Settings,
    *,
    search_tool: SearchTool | None = None,
    note_tool: NoteTool | None = None,
    max_tokens_per_source: int = 2000,
) -> ResearchToolset:
    """Build SearchTool, NoteTool, their adapters, and one shared registry."""
    selected_search_tool = search_tool or SearchTool(
        backend=settings.search_api.value,
        tavily_key=settings.tavily_api_key,
        perplexity_key=settings.perplexity_api_key,
        searxng_url=settings.searxng_url,
    )
    notes = NotesService(
        settings.notes_workspace,
        note_tool=note_tool,
    )
    registry = build_tool_registry(selected_search_tool, notes.note_tool)
    return ResearchToolset(
        registry=registry,
        search_tool=selected_search_tool,
        note_tool=notes.note_tool,
        searcher=SearchToolAdapter(
            selected_search_tool,
            max_tokens_per_source=max_tokens_per_source,
        ),
        notes=notes,
    )
