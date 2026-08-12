"""Capacity- and TTL-bounded working memory."""

from __future__ import annotations

import math
from collections import OrderedDict
from datetime import timedelta
from statistics import mean
from typing import Any, Dict, List

from ..base import BaseMemory, MemoryConfig, MemoryItem, TimeRange, utc_now
from ..embedding import EmbeddingModel, keyword_overlap
from .common import importance_weight, metadata_matches, with_retrieval_score


class WorkingMemory(BaseMemory):
    """Keep current-task information in process memory only."""

    memory_type = "working"

    def __init__(
        self,
        user_id: str,
        config: MemoryConfig,
        embedder: EmbeddingModel,
    ) -> None:
        super().__init__(user_id, config)
        self.embedder = embedder
        self._items: "OrderedDict[str, MemoryItem]" = OrderedDict()

    def add(self, item: MemoryItem) -> str:
        self._remove_expired()
        normalized = item.clone(
            user_id=self.user_id,
            memory_type=self.memory_type,
        )
        self._items[normalized.id] = normalized
        while len(self._items) > self.config.working_memory_capacity:
            victim = min(
                self._items.values(),
                key=lambda memory: (memory.importance, memory.timestamp),
            )
            self._items.pop(victim.id, None)
        return normalized.id

    def retrieve(
        self,
        query: str,
        limit: int = 5,
        min_importance: float = 0.0,
        time_range: TimeRange | None = None,
        **filters: Any,
    ) -> List[MemoryItem]:
        self._remove_expired()
        items = [
            item
            for item in self._items.values()
            if item.importance >= min_importance
            and metadata_matches(item, filters)
            and (
                time_range is None
                or time_range[0] <= item.timestamp <= time_range[1]
            )
        ]
        if not items:
            return []

        semantic_scores = (
            self.embedder.similarities(query, [item.content for item in items])
            if query.strip()
            else [1.0] * len(items)
        )
        ttl = self.config.working_memory_ttl_minutes
        ranked = []
        for item, semantic_score in zip(items, semantic_scores):
            keyword_score = (
                keyword_overlap(query, item.content)
                if query.strip()
                else 1.0
            )
            relevance = semantic_score * 0.7 + keyword_score * 0.3
            if query.strip() and relevance <= 0.0:
                continue
            age_minutes = max(
                0.0,
                (utc_now() - item.timestamp).total_seconds() / 60.0,
            )
            time_decay = math.exp(-age_minutes / ttl)
            score = relevance * time_decay * importance_weight(item)
            ranked.append(with_retrieval_score(item, score))

        ranked.sort(
            key=lambda item: item.metadata["_retrieval_score"],
            reverse=True,
        )
        return ranked[: max(0, limit)]

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
        self._items[memory_id] = updated
        return True

    def remove(self, memory_id: str) -> bool:
        return self._items.pop(memory_id, None) is not None

    def get(self, memory_id: str) -> MemoryItem | None:
        self._remove_expired()
        return self._items.get(memory_id)

    def get_all(self) -> List[MemoryItem]:
        self._remove_expired()
        return list(self._items.values())

    def clear(self) -> int:
        count = len(self._items)
        self._items.clear()
        return count

    def forget(self, strategy: str = "importance", **kwargs: Any) -> int:
        self._remove_expired()
        items = self.get_all()
        normalized = strategy.lower().strip().removesuffix("_based")
        if normalized == "importance":
            threshold = float(
                kwargs.get("threshold", self.config.importance_threshold),
            )
            ids = [item.id for item in items if item.importance < threshold]
        elif normalized == "time":
            max_age_days = float(kwargs.get("max_age_days", 1))
            cutoff = utc_now() - timedelta(days=max_age_days)
            ids = [item.id for item in items if item.timestamp < cutoff]
        elif normalized == "capacity":
            capacity = int(
                kwargs.get(
                    "max_capacity",
                    self.config.working_memory_capacity,
                ),
            )
            overflow = max(0, len(items) - capacity)
            ids = [
                item.id
                for item in sorted(
                    items,
                    key=lambda memory: (memory.importance, memory.timestamp),
                )[:overflow]
            ]
        else:
            raise ValueError(
                "strategy must be one of: importance, time, capacity",
            )
        return sum(1 for memory_id in ids if self.remove(memory_id))

    def get_stats(self) -> Dict[str, Any]:
        items = self.get_all()
        return {
            "memory_type": self.memory_type,
            "count": len(items),
            "capacity": self.config.working_memory_capacity,
            "ttl_minutes": self.config.working_memory_ttl_minutes,
            "average_importance": round(
                mean(item.importance for item in items),
                4,
            )
            if items
            else 0.0,
        }

    def _remove_expired(self) -> int:
        cutoff = utc_now() - timedelta(
            minutes=self.config.working_memory_ttl_minutes,
        )
        expired = [
            memory_id
            for memory_id, item in self._items.items()
            if item.timestamp < cutoff
        ]
        for memory_id in expired:
            self._items.pop(memory_id, None)
        return len(expired)
