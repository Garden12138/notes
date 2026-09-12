"""Travel validation and MCP-backed planning routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ...agents import MultiAgentTripPlanner, TripPlanningError
from ...models import TripPlanResponse, TripRequest
from ...services.agent_runtime import AgentRuntimeError, create_trip_planner
from ...services.mcp_integration import MCPIntegrationError
from ...services.unsplash import (
    UnsplashService,
    enrich_trip_plan_images,
    get_unsplash_service,
)


router = APIRouter(prefix="/trip", tags=["trip"])


@router.post("/validate", response_model=TripRequest)
def validate_trip_request(request: TripRequest) -> TripRequest:
    """Return a normalized request without invoking agents or external APIs."""
    return request


def get_trip_planner() -> MultiAgentTripPlanner:
    """Assemble request-local Agents around one shared MCP facade."""
    try:
        return create_trip_planner()
    except (AgentRuntimeError, MCPIntegrationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.post(
    "/plan",
    response_model=TripPlanResponse,
    responses={
        status.HTTP_502_BAD_GATEWAY: {"description": "Agent 输出无效"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "LLM 或 MCP 运行时不可用",
        },
    },
)
def create_trip_plan(
    request: TripRequest,
    planner: Annotated[MultiAgentTripPlanner, Depends(get_trip_planner)],
    image_service: Annotated[
        UnsplashService,
        Depends(get_unsplash_service),
    ],
) -> TripPlanResponse:
    """Run the fixed Agent workflow, then enrich attractions with photos."""
    try:
        plan = planner.plan_trip(request)
    except TripPlanningError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    enrich_trip_plan_images(plan, image_service)
    return TripPlanResponse(success=True, message="旅行计划生成成功", data=plan)
