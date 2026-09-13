"""Composition root for the chapter 14.5 service layer."""

from __future__ import annotations

from collections.abc import Callable

from hello_agents import HelloAgentsLLM

try:
    from ..agent import DeepResearchAgent
    from ..config import Settings
    from ..models import ResearchRequest
    from ..tool_events import ToolCallRecorder
    from ..tooling import build_research_toolset
    from .factory import build_role_services
except ImportError:  # Support direct imports with ``backend/src`` on sys.path.
    from agent import DeepResearchAgent  # type: ignore[no-redef]
    from config import Settings  # type: ignore[no-redef]
    from models import ResearchRequest  # type: ignore[no-redef]
    from tool_events import ToolCallRecorder  # type: ignore[no-redef]
    from tooling import build_research_toolset  # type: ignore[no-redef]
    from services.factory import build_role_services  # type: ignore[no-redef]


RunnerFactory = Callable[[ResearchRequest], DeepResearchAgent]


def build_runner_factory(settings: Settings) -> RunnerFactory:
    """Create the configured LLM once and request-scoped workflow services."""
    missing = [
        name
        for name, ready in settings.integration_status().items()
        if not ready
    ]
    if missing:
        raise ValueError("缺少可用集成配置：" + "、".join(missing))

    llm = HelloAgentsLLM(
        model=settings.llm_model_id,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url or None,
        provider=settings.llm_provider or None,
    )

    def create_runner(request: ResearchRequest) -> DeepResearchAgent:
        del request  # Backend selection is forwarded by run_stream, not construction.
        recorder = ToolCallRecorder()
        toolset = build_research_toolset(settings)
        roles = build_role_services(
            llm,
            tool_call_listener=recorder,
        )
        return DeepResearchAgent(
            planner=roles.planner,
            searcher=toolset.searcher,
            summarizer=roles.summarizer,
            note_writer=toolset.notes,
            reporter=roles.reporter,
            tool_event_source=recorder,
            report_store=toolset.notes,
        )

    return create_runner


def build_runner_factory_if_ready(
    settings: Settings,
) -> RunnerFactory | None:
    """Leave the API inspectable when required external config is absent."""
    if not all(settings.integration_status().values()):
        return None
    return build_runner_factory(settings)
