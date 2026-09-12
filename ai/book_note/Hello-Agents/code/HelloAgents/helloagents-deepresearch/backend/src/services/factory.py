"""Composition helper for the three ToolAwareSimpleAgent role services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

try:
    from ..prompts import (
        REPORT_WRITER_SYSTEM_PROMPT,
        TASK_SUMMARIZER_SYSTEM_PROMPT,
        TODO_PLANNER_SYSTEM_PROMPT,
    )
    from .planner import PlanningService
    from .reporter import ReportingService
    from .summarizer import SummarizationService
except ImportError:  # Support imports when ``src`` is placed on sys.path.
    from prompts import (  # type: ignore[no-redef]
        REPORT_WRITER_SYSTEM_PROMPT,
        TASK_SUMMARIZER_SYSTEM_PROMPT,
        TODO_PLANNER_SYSTEM_PROMPT,
    )
    from services.planner import PlanningService  # type: ignore[no-redef]
    from services.reporter import ReportingService  # type: ignore[no-redef]
    from services.summarizer import SummarizationService  # type: ignore[no-redef]


@dataclass(frozen=True)
class RoleServices:
    planner: PlanningService
    summarizer: SummarizationService
    reporter: ReportingService


def build_role_services(
    llm: Any,
    *,
    tool_registry: Any = None,
    tool_call_listener: Callable[[dict[str, Any]], None] | None = None,
) -> RoleServices:
    """Create three isolated role agents sharing one LLM and optional tools."""
    from hello_agents import ToolAwareSimpleAgent

    def create_agent(name: str, system_prompt: str) -> ToolAwareSimpleAgent:
        return ToolAwareSimpleAgent(
            name=name,
            system_prompt=system_prompt,
            llm=llm,
            tool_registry=tool_registry,
            enable_tool_calling=tool_registry is not None,
            tool_call_listener=tool_call_listener,
        )

    return RoleServices(
        planner=PlanningService(
            create_agent("TODO Planner", TODO_PLANNER_SYSTEM_PROMPT)
        ),
        summarizer=SummarizationService(
            create_agent("Task Summarizer", TASK_SUMMARIZER_SYSTEM_PROMPT)
        ),
        reporter=ReportingService(
            create_agent("Report Writer", REPORT_WRITER_SYSTEM_PROMPT)
        ),
    )
