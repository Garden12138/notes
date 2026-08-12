"""Agent-facing tool for the complete memory lifecycle."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List
from uuid import uuid4

from ...memory import MemoryConfig, MemoryManager
from ...memory.base import MEMORY_TYPES, utc_now
from ..base import Tool, ToolParameter


class MemoryTool(Tool):
    """Expose memory CRUD, retrieval, consolidation, and forgetting."""

    ACTIONS = {
        "add",
        "search",
        "summary",
        "stats",
        "update",
        "remove",
        "forget",
        "consolidate",
        "clear_all",
    }

    def __init__(
        self,
        user_id: str = "default",
        config: MemoryConfig | None = None,
        memory_config: MemoryConfig | None = None,
        memory_types: Iterable[str] | None = None,
        memory_manager: MemoryManager | None = None,
    ) -> None:
        super().__init__(
            name="memory",
            description=(
                "保存、检索、更新、删除、整合和遗忘用户记忆；"
                "action 支持 add/search/summary/stats/update/remove/forget/"
                "consolidate/clear_all。"
            ),
        )
        if config is not None and memory_config is not None:
            raise ValueError("config and memory_config cannot both be provided")
        selected = {
            value.lower().strip()
            for value in (memory_types or ["working", "episodic", "semantic"])
        }
        unknown = selected - MEMORY_TYPES
        if unknown:
            raise ValueError(f"unsupported memory types: {sorted(unknown)}")
        self.memory_manager = memory_manager or MemoryManager(
            user_id,
            config or memory_config,
            enable_working="working" in selected,
            enable_episodic="episodic" in selected,
            enable_semantic="semantic" in selected,
            enable_perceptual="perceptual" in selected,
        )
        self.manager = self.memory_manager
        self.user_id = self.manager.user_id
        self.session_id = str(uuid4())

    def run(
        self,
        parameters: Dict[str, Any] | str,
        **kwargs: Any,
    ) -> str:
        """Support both ToolRegistry dictionaries and chapter-style calls."""
        if isinstance(parameters, str):
            return self.execute(parameters, **kwargs)
        values = dict(parameters)
        action = str(values.pop("action", "")).strip()
        return self.execute(action, **values)

    def execute(self, action: str, **parameters: Any) -> str:
        normalized = action.lower().strip()
        if normalized not in self.ACTIONS:
            return (
                f"错误：未知 action '{action}'，可选值为 "
                + ", ".join(sorted(self.ACTIONS))
            )
        try:
            handler = getattr(self, f"_{normalized}")
            return handler(**parameters)
        except Exception as error:
            return f"错误：{error}"

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type="string",
                description="要执行的记忆操作",
            ),
            ToolParameter(
                name="content",
                type="string",
                description="add/update 使用的记忆内容",
                required=False,
            ),
            ToolParameter(
                name="query",
                type="string",
                description="search 使用的查询文本",
                required=False,
            ),
            ToolParameter(
                name="memory_type",
                type="string",
                description="working/episodic/semantic/perceptual",
                required=False,
                default="working",
            ),
            ToolParameter(
                name="memory_types",
                type="array",
                description="search/forget 限定的记忆类型",
                required=False,
            ),
            ToolParameter(
                name="importance",
                type="number",
                description="0 到 1 的重要性",
                required=False,
                default=0.5,
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="最大召回数量",
                required=False,
                default=5,
            ),
            ToolParameter(
                name="memory_id",
                type="string",
                description="update/remove 使用的记忆 ID",
                required=False,
            ),
            ToolParameter(
                name="strategy",
                type="string",
                description="importance/time/capacity 遗忘策略",
                required=False,
                default="importance",
            ),
            ToolParameter(
                name="from_type",
                type="string",
                description="整合来源类型",
                required=False,
                default="working",
            ),
            ToolParameter(
                name="to_type",
                type="string",
                description="整合目标类型",
                required=False,
                default="episodic",
            ),
            ToolParameter(
                name="modality",
                type="string",
                description="感知记忆的 text/image/audio/video 模态",
                required=False,
            ),
            ToolParameter(
                name="file_path",
                type="string",
                description="感知记忆对应的媒体路径",
                required=False,
            ),
        ]

    def _add(
        self,
        content: str,
        memory_type: str = "working",
        importance: float = 0.5,
        auto_classify: bool = False,
        modality: str | None = None,
        file_path: str | None = None,
        **metadata: Any,
    ) -> str:
        record_metadata = {
            **metadata,
            "session_id": self.session_id,
            "recorded_at": utc_now().isoformat(),
        }
        if modality:
            record_metadata["modality"] = modality
        if file_path:
            record_metadata["raw_data"] = file_path
            record_metadata.setdefault("modality", infer_modality(file_path))

        memory_id = self.manager.add_memory(
            content=content,
            memory_type=memory_type,
            importance=float(importance),
            metadata=record_metadata,
            auto_classify=as_bool(auto_classify),
        )
        selected_type = (
            self.manager.classify_memory(content, record_metadata)
            if as_bool(auto_classify)
            else memory_type
        )
        return f"已添加 {selected_type} 记忆，ID：{memory_id}"

    def _search(
        self,
        query: str,
        memory_type: str | None = None,
        memory_types: Iterable[str] | str | None = None,
        limit: int = 5,
        min_importance: float = 0.1,
        modality: str | None = None,
        **filters: Any,
    ) -> str:
        selected = normalize_memory_types(memory_types, memory_type)
        if modality:
            filters["modality"] = modality
        items = self.manager.retrieve_memories(
            query=query,
            memory_types=selected,
            limit=int(limit),
            min_importance=float(min_importance),
            **filters,
        )
        if not items:
            return "未找到相关记忆。"
        lines = [f"找到 {len(items)} 条相关记忆："]
        for index, item in enumerate(items, start=1):
            score = item.metadata.get("_retrieval_score", 0.0)
            lines.append(
                f"{index}. [{item.memory_type}] {item.content} "
                f"(重要性={item.importance:.2f}, "
                f"相关分={score:.3f}, ID={item.id})",
            )
        return "\n".join(lines)

    def _summary(self, limit_per_type: int = 3, **_: Any) -> str:
        lines = ["记忆摘要："]
        for memory_type, memory in self.manager.memory_types.items():
            items = memory.retrieve("", limit=int(limit_per_type))
            lines.append(f"- {memory_type}: {len(memory.get_all())} 条")
            lines.extend(f"  · {item.content}" for item in items)
        return "\n".join(lines)

    def _stats(self, **_: Any) -> str:
        return json.dumps(
            self.manager.get_memory_stats(),
            ensure_ascii=False,
            indent=2,
            default=serialize_value,
        )

    def _update(
        self,
        memory_id: str,
        content: str | None = None,
        importance: float | None = None,
        metadata: Dict[str, Any] | None = None,
        **_: Any,
    ) -> str:
        updates: Dict[str, Any] = {}
        if content is not None:
            updates["content"] = content
        if importance is not None:
            updates["importance"] = float(importance)
        if metadata is not None:
            updates["metadata"] = metadata
        if not updates:
            raise ValueError("update 至少需要 content、importance 或 metadata")
        return (
            f"已更新记忆：{memory_id}"
            if self.manager.update_memory(memory_id, **updates)
            else f"未找到记忆：{memory_id}"
        )

    def _remove(self, memory_id: str, **_: Any) -> str:
        return (
            f"已删除记忆：{memory_id}"
            if self.manager.remove_memory(memory_id)
            else f"未找到记忆：{memory_id}"
        )

    def _forget(
        self,
        strategy: str = "importance",
        memory_type: str | None = None,
        memory_types: Iterable[str] | str | None = None,
        threshold: float | None = None,
        max_age_days: float | None = None,
        max_capacity: int | None = None,
        **_: Any,
    ) -> str:
        kwargs = {
            key: value
            for key, value in {
                "threshold": threshold,
                "max_age_days": max_age_days,
                "max_capacity": max_capacity,
            }.items()
            if value is not None
        }
        counts = self.manager.forget_memories(
            strategy=strategy,
            memory_types=normalize_memory_types(memory_types, memory_type),
            **kwargs,
        )
        return "遗忘完成：" + ", ".join(
            f"{memory_type}={count}"
            for memory_type, count in counts.items()
        )

    def _consolidate(
        self,
        from_type: str = "working",
        to_type: str = "episodic",
        importance_threshold: float = 0.7,
        **_: Any,
    ) -> str:
        count = self.manager.consolidate_memories(
            from_type=from_type,
            to_type=to_type,
            importance_threshold=float(importance_threshold),
        )
        return f"整合完成：{from_type} → {to_type}，迁移 {count} 条记忆。"

    def _clear_all(self, **_: Any) -> str:
        counts = self.manager.clear_all()
        return "清理完成：" + ", ".join(
            f"{memory_type}={count}"
            for memory_type, count in counts.items()
        )

    def auto_record_conversation(
        self,
        user_message: str,
        assistant_message: str,
        conversation_id: str | None = None,
        importance: float = 0.5,
    ) -> str:
        """Record one interaction as episodic memory with valid metadata."""
        return self._add(
            content=f"用户：{user_message}\n助手：{assistant_message}",
            memory_type="episodic",
            importance=importance,
            conversation_id=conversation_id or self.session_id,
        )

    def add_knowledge(
        self,
        content: str,
        importance: float = 0.8,
        **metadata: Any,
    ) -> str:
        return self._add(
            content=content,
            memory_type="semantic",
            importance=importance,
            **metadata,
        )

    def get_context_for_query(self, query: str, limit: int = 5) -> str:
        items = self.manager.retrieve_memories(query, limit=limit)
        return "\n".join(f"- {item.content}" for item in items)

    def start_new_session(self, clear_working: bool = True) -> str:
        if clear_working and "working" in self.manager.memory_types:
            self.manager.memory_types["working"].clear()
        self.session_id = str(uuid4())
        return self.session_id

    def close(self) -> None:
        self.manager.close()


def normalize_memory_types(
    memory_types: Iterable[str] | str | None,
    memory_type: str | None,
) -> List[str] | None:
    if memory_types is None:
        return [memory_type] if memory_type else None
    if isinstance(memory_types, str):
        return [value.strip() for value in memory_types.split(",") if value.strip()]
    return list(memory_types)


def infer_modality(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        return "image"
    if suffix in {".mp3", ".wav", ".m4a", ".flac"}:
        return "audio"
    if suffix in {".mp4", ".mov", ".avi", ".mkv"}:
        return "video"
    return "text"


def as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.lower().strip() in {"1", "true", "yes", "on"}
    return bool(value)


def serialize_value(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)
