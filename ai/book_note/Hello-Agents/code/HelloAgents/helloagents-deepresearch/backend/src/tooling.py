"""Create the chapter 14 search, note and service-layer toolset."""

from __future__ import annotations

from dataclasses import dataclass

from hello_agents.tools import NoteTool, SearchTool, ToolRegistry

try:
    from .config import Settings
    from .services.notes import NotesService
    from .services.search import SearchService
except ImportError:  # Support direct imports with ``backend/src`` on sys.path.
    from config import Settings  # type: ignore[no-redef]
    from services.notes import NotesService  # type: ignore[no-redef]
    from services.search import SearchService  # type: ignore[no-redef]


@dataclass(frozen=True)
class ResearchToolset:
    """Objects created together at the tool-system composition boundary."""

    registry: ToolRegistry
    search_tool: SearchTool
    note_tool: NoteTool
    searcher: SearchService
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
        searcher=SearchService(
            settings,
            search_tool=selected_search_tool,
            max_tokens_per_source=max_tokens_per_source,
        ),
        notes=notes,
    )
