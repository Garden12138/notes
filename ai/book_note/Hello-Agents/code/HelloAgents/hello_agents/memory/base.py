"""Shared data models and interfaces for the HelloAgents memory system."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field, validator


MEMORY_TYPES = {"working", "episodic", "semantic", "perceptual"}
TimeRange = Tuple[datetime, datetime]


def utc_now() -> datetime:
    """Return an RFC 3339-friendly, timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def ensure_aware(value: datetime) -> datetime:
    """Treat naive timestamps as UTC and normalize aware ones to UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class MemoryItem(BaseModel):
    """The normalized record shared by all four memory types."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    memory_type: str = "semantic"
    user_id: str = "default"
    timestamp: datetime = Field(default_factory=utc_now)
    importance: float = 0.5
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("content")
    def content_must_not_be_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("memory content must not be blank")
        return value.strip()

    @validator("memory_type")
    def memory_type_must_be_supported(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized not in MEMORY_TYPES:
            raise ValueError(f"unsupported memory type: {value}")
        return normalized

    @validator("timestamp")
    def timestamp_must_be_timezone_aware(cls, value: datetime) -> datetime:
        return ensure_aware(value)

    @validator("importance")
    def importance_must_be_in_range(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("importance must be between 0 and 1")
        return float(value)

    class Config:
        validate_assignment = True

    def clone(self, **changes: Any) -> "MemoryItem":
        """Return a deep copy that works with Pydantic 1 and 2."""
        if hasattr(self, "model_copy"):
            return self.model_copy(deep=True, update=changes)
        return self.copy(deep=True, update=changes)

    def as_dict(self) -> Dict[str, Any]:
        """Return a regular dictionary for persistence."""
        if hasattr(self, "model_dump"):
            return self.model_dump()
        return self.dict()


class MemoryConfig(BaseModel):
    """Configuration shared by the manager and storage backends."""

    storage_path: str = "./memory_data"
    database_filename: str = "memory.db"
    max_capacity: int = 100
    importance_threshold: float = 0.1
    working_memory_capacity: int = 50
    working_memory_ttl_minutes: int = 60
    recency_half_life_days: float = 30.0
    perceptual_modalities: List[str] = Field(
        default_factory=lambda: ["text", "image", "audio", "video"],
    )

    @validator(
        "max_capacity",
        "working_memory_capacity",
        "working_memory_ttl_minutes",
    )
    def positive_integer(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("capacity and TTL values must be positive")
        return value

    @validator("importance_threshold")
    def threshold_in_range(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("importance_threshold must be between 0 and 1")
        return float(value)

    @validator("recency_half_life_days")
    def half_life_must_be_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("recency_half_life_days must be positive")
        return float(value)

    @property
    def database_path(self) -> Path:
        return Path(self.storage_path).expanduser() / self.database_filename


class BaseMemory(ABC):
    """Common contract implemented by every memory type."""

    def __init__(
        self,
        user_id: str,
        config: MemoryConfig | None = None,
    ) -> None:
        self.user_id = user_id
        self.config = config or MemoryConfig()

    @abstractmethod
    def add(self, item: MemoryItem) -> str:
        """Store one memory and return its ID."""

    @abstractmethod
    def retrieve(
        self,
        query: str,
        limit: int = 5,
        min_importance: float = 0.0,
        time_range: TimeRange | None = None,
        **filters: Any,
    ) -> List[MemoryItem]:
        """Retrieve ranked memories."""

    @abstractmethod
    def update(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update mutable fields of one memory."""

    @abstractmethod
    def remove(self, memory_id: str) -> bool:
        """Remove one memory and all of its indexes."""

    @abstractmethod
    def get(self, memory_id: str) -> MemoryItem | None:
        """Return one memory when it belongs to this user and type."""

    @abstractmethod
    def get_all(self) -> List[MemoryItem]:
        """Return all memories for this user and type."""

    @abstractmethod
    def clear(self) -> int:
        """Remove all memories for this user and return the count."""

    @abstractmethod
    def forget(self, strategy: str = "importance", **kwargs: Any) -> int:
        """Apply a forgetting strategy and return the removed count."""

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Return type-level statistics."""

    def has_memory(self, memory_id: str) -> bool:
        return self.get(memory_id) is not None
