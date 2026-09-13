"""FastAPI backend implemented through section 15.4 of Cyber Town."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from agents import NPCAgentManager, NPCNotFoundError, create_npc_manager
from architecture import NPC_CATALOG, build_architecture_snapshot
from batch_generator import NPCBatchGenerator
from config import Settings, get_settings
from logger import DialogueLogger
from models import (
    AffinityInfoResponse,
    AffinityListResponse,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    NPCListResponse,
    NPCStateInfo,
    NPCStateRefreshResponse,
    NPCStatusResponse,
)
from relationship_manager import AffinitySnapshot
from state_manager import NPCStateManager


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
                relationship_database_path=settings.sqlite_path,
            ),
            None,
        )
    except Exception as error:
        return None, f"NPC Agent 初始化失败：{error}"


def _affinity_response(snapshot: AffinitySnapshot) -> AffinityInfoResponse:
    return AffinityInfoResponse(
        npc_name=snapshot.npc_name,
        player_id=snapshot.player_id,
        score=snapshot.score,
        level=snapshot.level,
        modifier=snapshot.modifier,
        interaction_count=snapshot.interaction_count,
        updated_at=snapshot.updated_at,
    )


def create_app(
    settings: Settings | None = None,
    npc_manager: NPCAgentManager | None = None,
    state_manager: NPCStateManager | None = None,
    dialogue_logger: DialogueLogger | None = None,
    start_background_tasks: bool = True,
) -> FastAPI:
    current_settings = settings or get_settings()
    owns_manager = npc_manager is None
    owns_logger = dialogue_logger is None
    manager = npc_manager
    initialization_error: str | None = None
    if manager is None:
        manager, initialization_error = _initialize_manager(current_settings)

    logger = dialogue_logger or DialogueLogger(current_settings.log_path)
    state = state_manager or NPCStateManager(
        batch_generator=(
            NPCBatchGenerator(manager.llm) if manager is not None else None
        ),
        update_interval=current_settings.npc_update_interval,
        error_reporter=logger.log_error,
        refresh_reporter=logger.log_state_refresh,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if start_background_tasks:
            await state.start(refresh_immediately=True)
        try:
            yield
        finally:
            await state.stop()
            if owns_manager and manager is not None:
                manager.close()
            if owns_logger:
                logger.close()

    app = FastAPI(
        title="赛博小镇 API",
        version="0.4.0",
        description="HelloAgents 第十五章 15.1～15.6 实践",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=current_settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    def require_manager() -> NPCAgentManager:
        if manager is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=initialization_error or "NPC 对话服务未初始化",
            )
        return manager

    def resolve_profile(npc_name: str):
        try:
            return require_manager().get_profile(npc_name)
        except NPCNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            ) from error

    @app.get("/")
    def root() -> dict[str, object]:
        return {
            "project": "helloagents-ai-town",
            "scope": "chapter_15_1_to_15_4_backend_service",
            "version": "0.4.0",
            "npcs": state.get_npc_count(),
            "docs": "/docs",
            "implemented": [
                "health",
                "architecture",
                "npc_catalog",
                "npc_chat",
                "npc_memory",
                "npc_player_affinity",
                "npc_busy_state",
                "scheduled_background_dialogues",
                "daily_dialogue_logs",
            ],
        }

    @app.get("/healthz", response_model=HealthResponse)
    def health() -> HealthResponse:
        ready = manager is not None and manager.ready
        return HealthResponse(
            scope="chapter_15_1_to_15_4_backend_service",
            conversation_ready=ready,
            state_scheduler_running=state.running,
            integrations=current_settings.integration_status(),
            detail=None if ready else initialization_error,
        )

    @app.get("/architecture")
    def architecture():
        return build_architecture_snapshot()

    @app.get("/npcs", response_model=NPCListResponse)
    def list_npcs() -> NPCListResponse:
        npcs = [
            profile.model_copy(
                update={"available": not state.is_npc_busy(profile.name)},
            )
            for profile in NPC_CATALOG
        ]
        return NPCListResponse(npcs=npcs, total=len(npcs))

    @app.get("/npcs/status", response_model=NPCStatusResponse)
    def get_npc_status() -> NPCStatusResponse:
        return NPCStatusResponse(**state.get_current_state())

    @app.post("/npcs/status/refresh", response_model=NPCStateRefreshResponse)
    async def refresh_npc_status() -> NPCStateRefreshResponse:
        try:
            dialogues = await state.force_update()
        except RuntimeError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(error),
            ) from error
        except Exception as error:
            logger.log_error(f"NPC 状态刷新失败：{error}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"NPC 状态刷新失败：{error}",
            ) from error
        snapshot = state.get_current_state()
        return NPCStateRefreshResponse(
            message="NPC 状态已刷新",
            dialogues=dialogues,
            last_update=snapshot["last_update"],
        )

    @app.get("/npcs/{npc_name}/status", response_model=NPCStateInfo)
    def get_single_npc_status(npc_name: str) -> NPCStateInfo:
        snapshot = state.get_npc_state(npc_name)
        if snapshot is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"NPC {npc_name!r} 不存在",
            )
        return NPCStateInfo(**snapshot)

    @app.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> ChatResponse:
        npc_manager_instance = require_manager()
        profile = resolve_profile(request.npc_name)
        if not state.try_begin_dialogue(profile.name, request.player_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"NPC {profile.name} 正在与其他玩家对话",
            )
        try:
            result = npc_manager_instance.chat_with_affinity(
                npc_name=profile.name,
                message=request.message,
                player_id=request.player_id,
            )
            logger.log_dialogue(
                npc_name=profile.name,
                player_id=request.player_id,
                player_message=request.message,
                npc_reply=result.response,
                affinity=result.affinity,
                recent_memory_count=result.recent_memory_count,
                relevant_memory_count=result.relevant_memory_count,
            )
        except Exception as error:
            logger.log_error(
                f"对话处理失败：npc={profile.name}, "
                f"player={request.player_id}, error={error}",
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"NPC 回复生成失败：{error}",
            ) from error
        finally:
            state.finish_dialogue(profile.name, request.player_id)
        return ChatResponse(
            npc_name=profile.name,
            npc_title=profile.title,
            message=result.response,
            affinity_score=result.affinity.new_affinity,
            affinity_level=result.affinity.new_level,
            affinity_change=result.affinity.change_amount,
            affinity_reason=result.affinity.reason,
            affinity_sentiment=result.affinity.sentiment,
            affinity_analysis_valid=result.affinity.analysis_valid,
            interaction_count=result.affinity.interaction_count,
        )

    @app.get(
        "/npcs/{npc_name}/affinity",
        response_model=AffinityInfoResponse,
    )
    def get_npc_affinity(
        npc_name: str,
        player_id: str = Query(default="player", min_length=1, max_length=80),
    ) -> AffinityInfoResponse:
        profile = resolve_profile(npc_name)
        snapshot = require_manager().get_affinity(profile.name, player_id)
        return _affinity_response(snapshot)

    @app.get(
        "/affinity/{npc_name}/{player_id}",
        response_model=AffinityInfoResponse,
    )
    def get_affinity_compatibility(
        npc_name: str,
        player_id: str,
    ) -> AffinityInfoResponse:
        return get_npc_affinity(npc_name, player_id)

    @app.get("/affinities", response_model=AffinityListResponse)
    def get_all_affinities(
        player_id: str = Query(default="player", min_length=1, max_length=80),
    ) -> AffinityListResponse:
        snapshots = require_manager().get_all_affinities(player_id)
        return AffinityListResponse(
            player_id=player_id,
            affinities={
                name: _affinity_response(snapshot)
                for name, snapshot in snapshots.items()
            },
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
