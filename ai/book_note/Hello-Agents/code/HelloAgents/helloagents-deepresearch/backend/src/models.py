"""Data contracts for architecture inspection and research streaming."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class APIModel(BaseModel):
    """Base model with strict input and predictable serialization."""

    model_config = ConfigDict(extra="forbid")


class ArchitectureLayer(APIModel):
    name: str
    technology: str
    responsibilities: list[str]


class AgentSpec(APIModel):
    name: str
    responsibility: str
    input: str
    output: str


class ToolSpec(APIModel):
    name: str
    responsibility: str


class DataFlowStep(APIModel):
    order: int = Field(ge=1)
    name: str
    description: str


class ArchitectureSnapshot(APIModel):
    project: str
    scope: str
    layers: list[ArchitectureLayer]
    agents: list[AgentSpec]
    tools: list[ToolSpec]
    endpoint: str
    transport: str
    data_flow: list[DataFlowStep]
    implemented_capabilities: list[str]
    deferred_capabilities: list[str]


class HealthResponse(APIModel):
    status: Literal["ok"] = "ok"
    scope: str
    workflow_ready: bool
    integrations: dict[str, bool]


class SearchAPI(str, Enum):
    DUCKDUCKGO = "duckduckgo"
    TAVILY = "tavily"
    PERPLEXITY = "perplexity"
    SEARXNG = "searxng"


class ResearchRequest(APIModel):
    topic: str = Field(min_length=2, max_length=500)
    search_api: SearchAPI | None = None

    @field_validator("topic")
    @classmethod
    def normalize_topic(cls, value: str) -> str:
        topic = value.strip()
        if len(topic) < 2:
            raise ValueError("研究主题至少需要两个字符")
        return topic


class SearchResult(APIModel):
    title: str = Field(min_length=1)
    url: str = Field(min_length=1)
    snippet: str = Field(min_length=1)


class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchPhase(str, Enum):
    PLANNING = "planning"
    EXECUTION = "execution"
    REPORTING = "reporting"
    COMPLETED = "completed"
    FAILED = "failed"


class TodoDraft(APIModel):
    """Planner output before the coordinator assigns stable IDs and status."""

    title: str = Field(min_length=1, max_length=120)
    intent: str = Field(min_length=1, max_length=500)
    query: str = Field(min_length=1, max_length=500)

    @field_validator("title", "intent", "query")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("TODO 字段不能为空")
        return normalized


class TodoItem(TodoDraft):
    id: int = Field(ge=1)
    status: TodoStatus = TodoStatus.PENDING
    summary: str | None = None
    sources: list[SearchResult] = Field(default_factory=list)
    note_id: str | None = None


ResearchEventType = Literal[
    "status",
    "tasks",
    "task",
    "report",
    "done",
    "error",
]


class ResearchEvent(APIModel):
    type: ResearchEventType
    phase: ResearchPhase | None = None
    message: str | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    tasks: list[TodoItem] | None = None
    task: TodoItem | None = None
    report_markdown: str | None = None
    detail: dict[str, Any] | None = None


class ResearchResult(APIModel):
    topic: str
    todo_items: list[TodoItem]
    report_markdown: str
    phase: ResearchPhase = ResearchPhase.COMPLETED
