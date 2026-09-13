"""FastAPI entry point for the section 15.1 Cyber Town baseline."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from architecture import NPC_CATALOG, build_architecture_snapshot
from config import Settings, get_settings
from models import ChatRequest, HealthResponse, NPCListResponse


def create_app(settings: Settings | None = None) -> FastAPI:
    current_settings = settings or get_settings()
    app = FastAPI(
        title="赛博小镇 API",
        version="0.1.0",
        description="HelloAgents 第十五章 15.1 架构基线",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=current_settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    @app.get("/")
    def root() -> dict[str, object]:
        return {
            "project": "helloagents-ai-town",
            "scope": "chapter_15_1_architecture_baseline",
            "docs": "/docs",
            "implemented": ["health", "architecture", "npc_catalog"],
        }

    @app.get("/healthz", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            scope="chapter_15_1_architecture_baseline",
            conversation_ready=False,
            integrations=current_settings.integration_status(),
        )

    @app.get("/architecture")
    def architecture():
        return build_architecture_snapshot()

    @app.get("/npcs", response_model=NPCListResponse)
    def list_npcs() -> NPCListResponse:
        return NPCListResponse(npcs=NPC_CATALOG, total=len(NPC_CATALOG))

    @app.post("/chat", status_code=status.HTTP_501_NOT_IMPLEMENTED)
    def chat(_: ChatRequest) -> None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="15.1 仅实现架构基线；NPC Agent 对话将在 15.2 接入",
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    runtime_settings = get_settings()
    uvicorn.run(
        "main:app",
        host=runtime_settings.api_host,
        port=runtime_settings.api_port,
        reload=False,
    )
