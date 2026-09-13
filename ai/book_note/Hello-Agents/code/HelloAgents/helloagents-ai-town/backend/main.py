"""FastAPI entry point for sections 15.1 and 15.2 of Cyber Town."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from agents import (
    NPCAgentManager,
    NPCNotFoundError,
    create_npc_manager,
)
from architecture import NPC_CATALOG, build_architecture_snapshot
from config import Settings, get_settings
from models import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    NPCListResponse,
)


def _initialize_manager(
    settings: Settings,
) -> tuple[NPCAgentManager | None, str | None]:
    if not settings.llm_configured:
        return None, "请配置 LLM_MODEL_ID、LLM_API_KEY 和 LLM_BASE_URL"
    try:
        return (
            create_npc_manager(
                model=settings.llm_model_id,
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                memory_root=settings.memory_path,
            ),
            None,
        )
    except Exception as error:
        return None, f"NPC Agent 初始化失败：{error}"


def create_app(
    settings: Settings | None = None,
    npc_manager: NPCAgentManager | None = None,
) -> FastAPI:
    current_settings = settings or get_settings()
    owns_manager = npc_manager is None
    manager = npc_manager
    initialization_error: str | None = None
    if manager is None:
        manager, initialization_error = _initialize_manager(current_settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        if owns_manager and manager is not None:
            manager.close()

    app = FastAPI(
        title="赛博小镇 API",
        version="0.2.0",
        description="HelloAgents 第十五章 15.1～15.2 实践",
        lifespan=lifespan,
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
            "scope": "chapter_15_1_to_15_2_npc_agents",
            "docs": "/docs",
            "implemented": [
                "health",
                "architecture",
                "npc_catalog",
                "npc_chat",
                "npc_memory",
                "batch_background_dialogue_generator",
            ],
        }

    @app.get("/healthz", response_model=HealthResponse)
    def health() -> HealthResponse:
        ready = manager is not None and manager.ready
        return HealthResponse(
            scope="chapter_15_1_to_15_2_npc_agents",
            conversation_ready=ready,
            integrations=current_settings.integration_status(),
            detail=None if ready else initialization_error,
        )

    @app.get("/architecture")
    def architecture():
        return build_architecture_snapshot()

    @app.get("/npcs", response_model=NPCListResponse)
    def list_npcs() -> NPCListResponse:
        return NPCListResponse(npcs=NPC_CATALOG, total=len(NPC_CATALOG))

    @app.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> ChatResponse:
        if manager is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=initialization_error or "NPC 对话服务未初始化",
            )
        try:
            profile = manager.get_profile(request.npc_name)
            reply = manager.chat(
                npc_name=request.npc_name,
                message=request.message,
                player_id=request.player_id,
            )
        except NPCNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            ) from error
        except Exception as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"NPC 回复生成失败：{error}",
            ) from error
        return ChatResponse(
            npc_name=profile.name,
            npc_title=profile.title,
            message=reply,
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
