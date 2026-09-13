"""Data contracts for the Cyber Town architecture and NPC dialogue API."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


AffinityLevelName = Literal["陌生", "熟悉", "友好", "亲密", "挚友"]
AffinitySentimentName = Literal["positive", "neutral", "negative"]


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ArchitectureLayer(APIModel):
    name: str
    technology: str
    responsibilities: list[str]
    boundary: str


class SystemComponent(APIModel):
    name: str
    layer: str
    status: Literal["implemented", "deferred"]
    responsibility: str


class DataFlowStep(APIModel):
    order: int = Field(ge=1)
    actor: str
    action: str
    status: Literal["implemented", "deferred"]


class ArchitectureSnapshot(APIModel):
    project: str
    scope: str
    layers: list[ArchitectureLayer]
    components: list[SystemComponent]
    data_flow: list[DataFlowStep]
    implemented_capabilities: list[str]
    deferred_capabilities: list[str]


class NPCProfile(APIModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=1, max_length=40)
    role: str = Field(min_length=1, max_length=80)
    location: str = Field(min_length=1, max_length=80)
    activity: str = Field(min_length=1, max_length=120)
    personality: str = Field(min_length=1, max_length=240)
    available: bool = True


class NPCListResponse(APIModel):
    npcs: list[NPCProfile]
    total: int = Field(ge=0)


class HealthResponse(APIModel):
    status: Literal["ok"] = "ok"
    scope: str
    conversation_ready: bool
    integrations: dict[str, bool]
    detail: str | None = None


class ChatRequest(APIModel):
    npc_name: str = Field(min_length=1, max_length=40)
    player_id: str = Field(default="player", min_length=1, max_length=80)
    message: str = Field(min_length=1, max_length=1000)

    @field_validator("npc_name", "player_id", "message")
    @classmethod
    def strip_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("字段不能为空")
        return normalized


class ChatResponse(APIModel):
    npc_name: str
    npc_title: str
    message: str
    affinity_score: float = Field(ge=0, le=100)
    affinity_level: AffinityLevelName
    affinity_change: int = Field(ge=-15, le=10)
    affinity_reason: str
    affinity_sentiment: AffinitySentimentName
    affinity_analysis_valid: bool
    interaction_count: int = Field(ge=1)
    success: Literal[True] = True
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
