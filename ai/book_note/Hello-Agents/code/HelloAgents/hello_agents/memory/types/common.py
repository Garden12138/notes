"""Shared behavior for the three persistent memory types."""

from __future__ import annotations

import math
from datetime import timedelta
from statistics import mean
from typing import Any, Dict, List

from ..base import BaseMemory, MemoryConfig, MemoryItem, TimeRange, utc_now
from ..embedding import EmbeddingModel
from ..storage import SQLiteDocumentStore, SQLiteVectorStore


def metadata_matches(item: MemoryItem, filters: Dict[str, Any]) -> bool:
    """Apply exact metadata filters after storage-level filtering."""
    for key, expected in filters.items():
        if expected is None:
            continue
        if item.metadata.get(key) != expected:
            return False
    return True


def recency_score(item: MemoryItem, half_life_days: float) -> float:
    age_days = max(0.0, (utc_now() - item.timestamp).total_seconds() / 86400.0)
    return math.exp(-math.log(2.0) * age_days / half_life_days)


def importance_weight(item: MemoryItem) -> float:
    return 0.8 + item.importance * 0.4


def with_retrieval_score(item: MemoryItem, score: float) -> MemoryItem:
    copy = item.clone()
    copy.metadata = {**copy.metadata, "_retrieval_score": round(score, 6)}
    return copy


class PersistentMemory(BaseMemory):
    """CRUD, capacity, and forgetting shared by persistent memories."""

    memory_type: str

    def __init__(
        self,
        user_id: str,
        config: MemoryConfig,
        document_store: SQLiteDocumentStore,
        vector_store: SQLiteVectorStore,
        embedder: EmbeddingModel,
    ) -> None:
        super().__init__(user_id, config)
        self.document_store = document_store
        self.vector_store = vector_store
        self.embedder = embedder

    def add(self, item: MemoryItem) -> str:
        normalized = item.clone(
            user_id=self.user_id,
            memory_type=self.memory_type,
        )
        self.document_store.save(normalized)
        try:
            self._index(normalized)
        except Exception:
            self.document_store.remove(normalized.id)
            self._deindex(normalized.id)
            raise
        self.forget(strategy="capacity", max_capacity=self.config.max_capacity)
        return normalized.id

    def _index(self, item: MemoryItem) -> None:
        self.vector_store.upsert(
            memory_id=item.id,
            user_id=item.user_id,
            memory_type=item.memory_type,
            content=item.content,
            namespace=self._namespace(item),
            metadata={
                **item.metadata,
                "importance": item.importance,
                "timestamp": item.timestamp.isoformat(),
            },
        )

    def _namespace(self, item: MemoryItem) -> str:
        return "text"

    def _deindex(self, memory_id: str) -> None:
        self.vector_store.remove(memory_id)

    def update(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        item = self.get(memory_id)
        if item is None:
            return False
        allowed = {"content", "importance", "metadata", "timestamp"}
        unknown = set(updates) - allowed
        if unknown:
            raise ValueError(f"fields cannot be updated: {sorted(unknown)}")

        updated = item.clone()
        for key, value in updates.items():
            setattr(updated, key, value)
        self.document_store.save(updated)
        try:
            self._index(updated)
        except Exception:
            self.document_store.save(item)
            self._index(item)
            raise
        return True

    def remove(self, memory_id: str) -> bool:
        item = self.get(memory_id)
        if item is None:
            return False
        removed = self.document_store.remove(memory_id)
        self._deindex(memory_id)
        return removed

    def get(self, memory_id: str) -> MemoryItem | None:
        item = self.document_store.get(memory_id)
        if (
            item is None
            or item.user_id != self.user_id
            or item.memory_type != self.memory_type
        ):
            return None
        return item

    def get_all(self) -> List[MemoryItem]:
        return self.document_store.list_items(self.user_id, self.memory_type)

    def _candidates(
        self,
        min_importance: float,
        time_range: TimeRange | None,
        filters: Dict[str, Any],
    ) -> List[MemoryItem]:
        items = self.document_store.list_items(
            self.user_id,
            self.memory_type,
            min_importance=min_importance,
            time_range=time_range,
        )
        return [item for item in items if metadata_matches(item, filters)]

    def clear(self) -> int:
        count = self.document_store.clear(self.user_id, self.memory_type)
        self.vector_store.clear(self.user_id, self.memory_type)
        return count

    def forget(self, strategy: str = "importance", **kwargs: Any) -> int:
        items = self.get_all()
        normalized = strategy.lower().strip().removesuffix("_based")
        to_remove: List[MemoryItem]

        if normalized == "importance":
            threshold = float(
                kwargs.get("threshold", self.config.importance_threshold),
            )
            to_remove = [item for item in items if item.importance < threshold]
        elif normalized == "time":
            max_age_days = float(kwargs.get("max_age_days", 30))
            cutoff = utc_now() - timedelta(days=max_age_days)
            to_remove = [item for item in items if item.timestamp < cutoff]
        elif normalized == "capacity":
            capacity = int(kwargs.get("max_capacity", self.config.max_capacity))
            overflow = max(0, len(items) - capacity)
            to_remove = sorted(
                items,
                key=lambda item: (item.importance, item.timestamp),
            )[:overflow]
        else:
            raise ValueError(
                "strategy must be one of: importance, time, capacity",
            )

        return sum(1 for item in to_remove if self.remove(item.id))

    def get_stats(self) -> Dict[str, Any]:
        items = self.get_all()
        return {
            "memory_type": self.memory_type,
            "count": len(items),
            "average_importance": round(
                mean(item.importance for item in items),
                4,
            )
            if items
            else 0.0,
            "oldest": min((item.timestamp for item in items), default=None),
            "newest": max((item.timestamp for item in items), default=None),
        }
