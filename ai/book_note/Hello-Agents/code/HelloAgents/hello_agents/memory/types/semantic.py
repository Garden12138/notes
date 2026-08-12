"""Hybrid vector-and-graph semantic memory."""

from __future__ import annotations

import re
from typing import Any, List, Set, Tuple

from ..base import MemoryConfig, MemoryItem, TimeRange
from ..embedding import EmbeddingModel
from ..storage import SQLiteDocumentStore, SQLiteGraphStore, SQLiteVectorStore
from .common import PersistentMemory, importance_weight, with_retrieval_score


class SemanticMemory(PersistentMemory):
    """Store stable facts and combine vector with entity-graph retrieval."""

    memory_type = "semantic"

    def __init__(
        self,
        user_id: str,
        config: MemoryConfig,
        document_store: SQLiteDocumentStore,
        vector_store: SQLiteVectorStore,
        graph_store: SQLiteGraphStore,
        embedder: EmbeddingModel,
    ) -> None:
        super().__init__(
            user_id,
            config,
            document_store,
            vector_store,
            embedder,
        )
        self.graph_store = graph_store

    def _index(self, item: MemoryItem) -> None:
        super()._index(item)
        entities, relations = extract_entities_and_relations(item.content)
        self.graph_store.upsert(
            item.id,
            item.user_id,
            entities,
            relations,
        )

    def _deindex(self, memory_id: str) -> None:
        super()._deindex(memory_id)
        self.graph_store.remove(memory_id)

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
        graph_scores = self.graph_store.search(query, self.user_id)

        ranked = []
        for item in candidates:
            vector = vector_scores.get(item.id, 0.0)
            graph = graph_scores.get(item.id, 0.0)
            if not query.strip():
                vector = 1.0
            elif vector <= 0.0 and graph <= 0.0:
                continue
            score = (vector * 0.7 + graph * 0.3) * importance_weight(item)
            ranked.append(with_retrieval_score(item, score))
        ranked.sort(
            key=lambda item: item.metadata["_retrieval_score"],
            reverse=True,
        )
        return ranked[: max(0, limit)]

    def remove(self, memory_id: str) -> bool:
        return super().remove(memory_id)

    def clear(self) -> int:
        count = super().clear()
        self.graph_store.clear(self.user_id)
        return count


def extract_entities_and_relations(
    content: str,
) -> Tuple[Set[str], List[Tuple[str, str, str]]]:
    """Provide a deterministic rule fallback for the chapter's graph layer.

    This is deliberately small: production code can replace it with spaCy or
    an LLM extractor without altering ``SemanticMemory`` or ``MemoryManager``.
    """
    entities: Set[str] = set(
        token
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_+#.-]{1,31}", content)
    )
    relations: List[Tuple[str, str, str]] = []
    relation_words = ["是", "喜欢", "擅长", "使用", "负责", "学习"]
    for relation in relation_words:
        pattern = rf"([^，。；,;]{{1,24}}?){relation}([^，。；,;]{{1,24}})"
        for match in re.finditer(pattern, content):
            source = match.group(1).strip(" ：:的")
            target = match.group(2).strip(" ：:的")
            if source and target:
                relations.append((source, relation, target))
                entities.update({source, target})

    for segment in re.findall(r"[\u4e00-\u9fff]{2,16}", content):
        entities.add(segment)
    return entities, relations
