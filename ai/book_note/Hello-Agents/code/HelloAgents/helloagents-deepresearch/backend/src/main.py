"""FastAPI entry point for the chapter 14 deep-research application."""

from __future__ import annotations

from collections.abc import Callable, Iterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

try:
    from .agent import DeepResearchAgent
    from .architecture import build_architecture_snapshot
    from .config import Settings, get_settings
    from .models import HealthResponse, ResearchEvent, ResearchPhase, ResearchRequest
    from .services.composition import build_runner_factory_if_ready
    from .streaming import encode_sse
except ImportError:  # Allow ``python src/main.py`` as shown in the chapter.
    from agent import DeepResearchAgent  # type: ignore[no-redef]
    from architecture import build_architecture_snapshot  # type: ignore[no-redef]
    from config import Settings, get_settings  # type: ignore[no-redef]
    from models import (  # type: ignore[no-redef]
        HealthResponse,
        ResearchEvent,
        ResearchPhase,
        ResearchRequest,
    )
    from services.composition import (  # type: ignore[no-redef]
        build_runner_factory_if_ready,
    )
    from streaming import encode_sse  # type: ignore[no-redef]


RunnerFactory = Callable[[ResearchRequest], DeepResearchAgent]


def create_app(
    *,
    settings: Settings | None = None,
    runner_factory: RunnerFactory | None = None,
) -> FastAPI:
    """Create an API whose real research services are supplied at composition time."""
    current_settings = settings or get_settings()
    app = FastAPI(
        title="HelloAgents Deep Research",
        version="0.1.0",
        description="Automated deep research assistant",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=current_settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "project": "helloagents-deepresearch",
            "scope": "chapter_14_1_to_14_6_frontend_interaction",
            "docs": "/docs",
        }

    @app.get("/healthz", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            scope="chapter_14_1_to_14_6_frontend_interaction",
            workflow_ready=runner_factory is not None,
            integrations=current_settings.integration_status(),
        )

    @app.get("/architecture")
    def architecture():
        return build_architecture_snapshot()

    @app.post("/research/stream")
    def stream_research(payload: ResearchRequest) -> StreamingResponse:
        if runner_factory is None:
            raise HTTPException(
                status_code=503,
                detail=(
                    "研究服务已实现，但 LLM、搜索或笔记配置尚未全部就绪；"
                    "请检查 /healthz 与 .env"
                ),
            )
        runner = runner_factory(payload)

        def event_iterator() -> Iterator[str]:
            try:
                for event in runner.run_stream(payload.topic, payload.search_api):
                    yield encode_sse(event)
            except Exception as exc:
                yield encode_sse(
                    ResearchEvent(
                        type="error",
                        phase=ResearchPhase.FAILED,
                        message="研究流程执行失败",
                        detail={"reason": str(exc)},
                    )
                )

        return StreamingResponse(
            event_iterator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    return app


_runtime_settings = get_settings()
app = create_app(
    settings=_runtime_settings,
    runner_factory=build_runner_factory_if_ready(_runtime_settings),
)


if __name__ == "__main__":
    import uvicorn

    runtime_settings = get_settings()
    uvicorn.run(
        app,
        host=runtime_settings.host,
        port=runtime_settings.port,
        log_level="info",
    )
