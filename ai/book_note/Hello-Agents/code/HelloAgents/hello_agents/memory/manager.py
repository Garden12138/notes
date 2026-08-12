"""Coordinator for working, episodic, semantic, and perceptual memory."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .base import MEMORY_TYPES, MemoryConfig, MemoryItem, TimeRange
from .embedding import EmbeddingModel, TFIDFEmbedding
from .storage import SQLiteDocumentStore, SQLiteGraphStore, SQLiteVectorStore
from .types import (
    EpisodicMemory,
    PerceptualMemory,
    SemanticMemory,
    WorkingMemory,
)


class MemoryManager:
    """Route lifecycle operations to the enabled memory implementations."""

    def __init__(
        self,
        user_id: str = "default",
        config: MemoryConfig | None = None,
        embedding_model: EmbeddingModel | None = None,
        enable_working: bool = True,
        enable_episodic: bool = True,
        enable_semantic: bool = True,
        enable_perceptual: bool = False,
    ) -> None:
        if not user_id.strip():
            raise ValueError("user_id must not be blank")
        self.user_id = user_id
        self.config = config or MemoryConfig()
        self.embedding_model = embedding_model or TFIDFEmbedding()

        self.document_store = SQLiteDocumentStore(self.config.database_path)
        self.vector_store = SQLiteVectorStore(self.config.database_path)
        self.graph_store = SQLiteGraphStore(self.config.database_path)

        self.memory_types: Dict[str, Any] = {}
        if enable_working:
            self.memory_types["working"] = WorkingMemory(
                user_id,
                self.config,
                self.embedding_model,
            )
        if enable_episodic:
            self.memory_types["episodic"] = EpisodicMemory(
                user_id,
                self.config,
                self.document_store,
                self.vector_store,
                self.embedding_model,
            )
        if enable_semantic:
            self.memory_types["semantic"] = SemanticMemory(
                user_id,
                self.config,
                self.document_store,
                self.vector_store,
                self.graph_store,
                self.embedding_model,
            )
        if enable_perceptual:
            self.memory_types["perceptual"] = PerceptualMemory(
                user_id,
                self.config,
                self.document_store,
                self.vector_store,
                self.embedding_model,
            )

    def add_memory(
        self,
        content: str,
        memory_type: str = "semantic",
        importance: float = 0.5,
        metadata: Dict[str, Any] | None = None,
        auto_classify: bool = False,
    ) -> str:
        selected = (
            self.classify_memory(content, metadata or {})
            if auto_classify
            else memory_type.lower().strip()
        )
        memory = self._get_memory(selected)
        item = MemoryItem(
            content=content,
            memory_type=selected,
            user_id=self.user_id,
            importance=importance,
            metadata=metadata or {},
        )
        return memory.add(item)

    def retrieve_memories(
        self,
        query: str,
        memory_types: Iterable[str] | None = None,
        limit: int = 5,
        min_importance: float = 0.0,
        time_range: TimeRange | None = None,
        **filters: Any,
    ) -> List[MemoryItem]:
        if limit <= 0:
            return []
        if memory_types is None:
            selected = list(self.memory_types)
        elif isinstance(memory_types, str):
            selected = [memory_types.lower().strip()]
        else:
            selected = [value.lower().strip() for value in memory_types]
        if not selected:
            return []

        results: Dict[str, MemoryItem] = {}
        for memory_type in selected:
            memory = self._get_memory(memory_type)
            for item in memory.retrieve(
                query,
                limit=limit,
                min_importance=min_importance,
                time_range=time_range,
                **filters,
            ):
                previous = results.get(item.id)
                if previous is None or self._score(item) > self._score(previous):
                    results[item.id] = item

        ranked = sorted(
            results.values(),
            key=lambda item: (self._score(item), item.importance, item.timestamp),
            reverse=True,
        )
        return ranked[:limit]

    def update_memory(self, memory_id: str, **updates: Any) -> bool:
        for memory in self.memory_types.values():
            if memory.has_memory(memory_id):
                return memory.update(memory_id, updates)
        return False

    def remove_memory(self, memory_id: str) -> bool:
        for memory in self.memory_types.values():
            if memory.has_memory(memory_id):
                return memory.remove(memory_id)
        return False

    def forget_memories(
        self,
        strategy: str = "importance",
        memory_types: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> Dict[str, int]:
        if memory_types is None:
            selected = list(self.memory_types)
        elif isinstance(memory_types, str):
            selected = [memory_types]
        else:
            selected = list(memory_types)
        return {
            memory_type: self._get_memory(memory_type).forget(strategy, **kwargs)
            for memory_type in selected
        }

    def consolidate_memories(
        self,
        from_type: str = "working",
        to_type: str = "episodic",
        importance_threshold: float = 0.7,
    ) -> int:
        if from_type == to_type:
            raise ValueError("source and target memory types must differ")
        source = self._get_memory(from_type)
        target = self._get_memory(to_type)
        candidates = [
            item
            for item in source.get_all()
            if item.importance >= importance_threshold
        ]
        moved = 0
        for item in candidates:
            metadata = {
                **item.metadata,
                "consolidated_from": from_type,
                "source_memory_id": item.id,
            }
            new_id = target.add(
                MemoryItem(
                    content=item.content,
                    memory_type=to_type,
                    user_id=self.user_id,
                    timestamp=item.timestamp,
                    importance=min(1.0, item.importance * 1.1),
                    metadata=metadata,
                ),
            )
            if source.remove(item.id):
                moved += 1
            else:
                target.remove(new_id)
        return moved

    def get_memory_stats(self) -> Dict[str, Dict[str, Any]]:
        return {
            memory_type: memory.get_stats()
            for memory_type, memory in self.memory_types.items()
        }

    def clear_all(self) -> Dict[str, int]:
        return {
            memory_type: memory.clear()
            for memory_type, memory in self.memory_types.items()
        }

    def classify_memory(
        self,
        content: str,
        metadata: Dict[str, Any] | None = None,
    ) -> str:
        """Use the chapter's lightweight rule routing, not an LLM claim."""
        metadata = metadata or {}
        if metadata.get("modality") or metadata.get("raw_data"):
            return "perceptual"
        lowered = content.lower()
        if any(word in lowered for word in ["刚才", "当前", "这一步", "待办"]):
            return "working"
        if any(
            word in lowered
            for word in ["昨天", "上次", "曾经", "完成了", "发生在"]
        ):
            return "episodic"
        return "semantic"

    def close(self) -> None:
        self.document_store.close()
        self.vector_store.close()
        self.graph_store.close()

    def _get_memory(self, memory_type: str) -> Any:
        normalized = memory_type.lower().strip()
        if normalized not in MEMORY_TYPES:
            raise ValueError(f"unsupported memory type: {memory_type}")
        if normalized not in self.memory_types:
            raise ValueError(f"memory type is disabled: {normalized}")
        return self.memory_types[normalized]

    @staticmethod
    def _score(item: MemoryItem) -> float:
        return float(item.metadata.get("_retrieval_score", 0.0))
