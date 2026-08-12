"""Time-aware episodic memory."""

from __future__ import annotations

from typing import Any, List

from ..base import MemoryItem, TimeRange
from .common import (
    PersistentMemory,
    importance_weight,
    recency_score,
    with_retrieval_score,
)


class EpisodicMemory(PersistentMemory):
    """Recall concrete events using vector relevance and recency."""

    memory_type = "episodic"

    def retrieve(
        self,
        query: str,
        limit: int = 5,
        min_importance: float = 0.0,
        time_range: TimeRange | None = None,
        **filters: Any,
    ) -> List[MemoryItem]:
        candidates = self._candidates(min_importance, time_range, filters)
        if not candidates:
            return []
        vector_scores = {
            result.memory_id: result.score
            for result in self.vector_store.search(
                query,
                self.embedder,
                self.user_id,
                self.memory_type,
            )
        }
        ranked = []
        for item in candidates:
            vector = vector_scores.get(item.id, 0.0)
            if query.strip() and vector <= 0.0:
                continue
            score = (
                vector * 0.8
                + recency_score(item, self.config.recency_half_life_days) * 0.2
            ) * importance_weight(item)
            ranked.append(with_retrieval_score(item, score))
        ranked.sort(
            key=lambda item: item.metadata["_retrieval_score"],
            reverse=True,
        )
        return ranked[: max(0, limit)]
