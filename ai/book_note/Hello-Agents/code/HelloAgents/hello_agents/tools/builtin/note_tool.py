"""Markdown + YAML note storage for long-horizon Agent tasks."""

from __future__ import annotations

import json
import warnings
from datetime import date, datetime
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List

import yaml

from ..base import Tool, ToolParameter


NOTE_TYPES = {
    "task_state",
    "conclusion",
    "blocker",
    "action",
    "reference",
    "general",
}


class NoteTool(Tool):
    """Persist structured project notes as human-readable Markdown files."""

    ACTIONS = {
        "create",
        "read",
        "update",
        "search",
        "list",
        "summary",
        "delete",
    }

    def __init__(self, workspace: str = "./notes") -> None:
        super().__init__(
            name="note",
            description=(
                "以 Markdown + YAML 保存和检索长期任务笔记；"
                "action 支持 create/read/update/search/list/summary/delete。"
            ),
        )
        self.workspace = Path(workspace).expanduser().resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.index_path = self.workspace / "notes_index.json"
        self._lock = RLock()
        self.index: Dict[str, Dict[str, Any]] = self._load_index()

    def run(
        self,
        parameters: Dict[str, Any] | str,
        **kwargs: Any,
    ) -> Any:
        """Support both ToolRegistry dictionaries and direct action calls."""
        if isinstance(parameters, str):
            return self.execute(parameters, **kwargs)
        values = dict(parameters)
        action = str(values.pop("action", "")).strip()
        return self.execute(action, **values)

    def execute(self, action: str, **parameters: Any) -> Any:
        normalized = action.lower().strip()
        if normalized not in self.ACTIONS:
            return (
                f"错误：未知 action '{action}'，可选值为 "
                + ", ".join(sorted(self.ACTIONS))
            )
        handlers = {
            "create": self._create_note,
            "read": self._read_note,
            "update": self._update_note,
            "search": self._search_notes,
            "list": self._list_notes,
            "summary": self._summary,
            "delete": self._delete_note,
        }
        try:
            return handlers[normalized](**parameters)
        except Exception as error:
            return f"错误：{error}"

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type="string",
                description="create/read/update/search/list/summary/delete",
            ),
            ToolParameter(
                name="note_id",
                type="string",
                description="read/update/delete 使用的笔记 ID",
                required=False,
            ),
            ToolParameter(
                name="title",
                type="string",
                description="create/update 使用的标题",
                required=False,
            ),
            ToolParameter(
                name="content",
                type="string",
                description="create/update 使用的 Markdown 正文",
                required=False,
            ),
            ToolParameter(
                name="note_type",
                type="string",
                description=(
                    "task_state/conclusion/blocker/action/reference/general"
                ),
                required=False,
                default="general",
            ),
            ToolParameter(
                name="tags",
                type="array",
                description="用于分类和过滤的标签",
                required=False,
            ),
            ToolParameter(
                name="query",
                type="string",
                description="search 使用的关键词",
                required=False,
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="search/list 返回数量上限",
                required=False,
                default=10,
            ),
        ]

    def _create_note(
        self,
        title: str,
        content: str,
        note_type: str = "general",
        tags: List[str] | str | None = None,
        **_: Any,
    ) -> str:
        """Create one note and return its stable file-based ID."""
        clean_title = self._validate_text(title, "title")
        clean_content = self._validate_text(content, "content")
        selected_type = self._validate_note_type(note_type)
        clean_tags = self._normalize_tags(tags)

        with self._lock:
            note_id = self._new_note_id()
            timestamp = self._now_iso()
            metadata = {
                "id": note_id,
                "title": clean_title,
                "type": selected_type,
                "tags": clean_tags,
                "created_at": timestamp,
                "updated_at": timestamp,
            }
            path = self._note_path(note_id)
            self._write_note(path, metadata, clean_content)
            self.index[note_id] = self._index_entry(metadata, path)
            self._save_index()
        return note_id

    def _read_note(self, note_id: str, **_: Any) -> Dict[str, Any]:
        """Read and parse a note while checking its index entry."""
        selected_id = self._validate_note_id(note_id)
        with self._lock:
            if selected_id not in self.index:
                raise ValueError(f"笔记不存在：{selected_id}")
            path = self._indexed_path(selected_id)
            if not path.is_file():
                raise FileNotFoundError(f"笔记文件缺失：{path.name}")
            metadata, content = self._parse_markdown(
                path.read_text(encoding="utf-8"),
            )
            metadata = self._normalize_metadata(metadata)
            if metadata.get("id") != selected_id:
                raise ValueError(
                    f"笔记 ID 与文件不一致：{path.name}",
                )
            metadata["file_path"] = str(path)
            return {
                "metadata": metadata,
                "content": content,
            }

    def _update_note(
        self,
        note_id: str,
        title: str | None = None,
        content: str | None = None,
        note_type: str | None = None,
        tags: List[str] | str | None = None,
        **_: Any,
    ) -> str:
        """Update supplied fields without changing the note ID or creation time."""
        selected_id = self._validate_note_id(note_id)
        if all(value is None for value in (title, content, note_type, tags)):
            raise ValueError("update 至少需要一个待更新字段")

        with self._lock:
            note = self._read_note(selected_id)
            metadata = dict(note["metadata"])
            old_content = note["content"]
            path = self._indexed_path(selected_id)

            if title is not None:
                metadata["title"] = self._validate_text(title, "title")
            if content is not None:
                old_content = self._validate_text(content, "content")
            if note_type is not None:
                metadata["type"] = self._validate_note_type(note_type)
            if tags is not None:
                metadata["tags"] = self._normalize_tags(tags)
            metadata["updated_at"] = self._now_iso()
            metadata.pop("file_path", None)

            self._write_note(path, metadata, old_content)
            self.index[selected_id] = self._index_entry(metadata, path)
            self._save_index()
        return f"✅ 笔记已更新：{metadata['title']}"

    def _search_notes(
        self,
        query: str,
        limit: int = 10,
        note_type: str | None = None,
        tags: List[str] | str | None = None,
        **_: Any,
    ) -> List[Dict[str, Any]]:
        """Search title and body, then order matches by update time."""
        keyword = self._validate_text(query, "query").casefold()
        selected_type = (
            self._validate_note_type(note_type)
            if note_type is not None
            else None
        )
        selected_tags = set(self._normalize_tags(tags))
        maximum = self._validate_limit(limit)
        results: List[Dict[str, Any]] = []

        for note_id, index_entry in list(self.index.items()):
            if not self._matches_filters(
                index_entry,
                selected_type,
                selected_tags,
            ):
                continue
            try:
                note = self._read_note(note_id)
            except Exception as error:
                warnings.warn(
                    f"读取笔记 {note_id} 失败：{error}",
                    RuntimeWarning,
                    stacklevel=2,
                )
                continue
            metadata = note["metadata"]
            searchable = "\n".join(
                [
                    str(metadata.get("title", "")),
                    note["content"],
                    " ".join(metadata.get("tags", [])),
                ],
            ).casefold()
            if keyword in searchable:
                results.append(self._note_result(metadata, note["content"]))

        results.sort(
            key=lambda item: item.get("updated_at", ""),
            reverse=True,
        )
        return results[:maximum]

    def _list_notes(
        self,
        note_type: str | None = None,
        tags: List[str] | str | None = None,
        limit: int = 20,
        **_: Any,
    ) -> List[Dict[str, Any]]:
        """List matching metadata without opening every Markdown file."""
        selected_type = (
            self._validate_note_type(note_type)
            if note_type is not None
            else None
        )
        selected_tags = set(self._normalize_tags(tags))
        maximum = self._validate_limit(limit)
        results = [
            self._public_metadata(metadata)
            for metadata in self.index.values()
            if self._matches_filters(
                metadata,
                selected_type,
                selected_tags,
            )
        ]
        results.sort(
            key=lambda item: item.get("updated_at", ""),
            reverse=True,
        )
        return results[:maximum]

    def _summary(self, **_: Any) -> Dict[str, Any]:
        """Return note counts and the five most recently updated entries."""
        type_counts: Dict[str, int] = {}
        for metadata in self.index.values():
            note_type = str(metadata.get("type", "general"))
            type_counts[note_type] = type_counts.get(note_type, 0) + 1
        recent = sorted(
            self.index.values(),
            key=lambda item: item.get("updated_at", ""),
            reverse=True,
        )[:5]
        return {
            "total_notes": len(self.index),
            "type_distribution": type_counts,
            "recent_notes": [
                {
                    "id": note["id"],
                    "title": note.get("title", ""),
                    "type": note.get("type", "general"),
                    "updated_at": note.get("updated_at", ""),
                }
                for note in recent
            ],
        }

    def _delete_note(self, note_id: str, **_: Any) -> str:
        """Delete the Markdown file and remove its index entry."""
        selected_id = self._validate_note_id(note_id)
        with self._lock:
            if selected_id not in self.index:
                raise ValueError(f"笔记不存在：{selected_id}")
            path = self._indexed_path(selected_id)
            title = self.index[selected_id].get("title", selected_id)
            if path.exists():
                path.unlink()
            del self.index[selected_id]
            self._save_index()
        return f"✅ 笔记已删除：{title}"

    def _build_markdown(
        self,
        metadata: Dict[str, Any],
        content: str,
    ) -> str:
        """Combine YAML front matter with the original Markdown body."""
        front_matter = {
            key: metadata[key]
            for key in (
                "id",
                "title",
                "type",
                "tags",
                "created_at",
                "updated_at",
            )
        }
        yaml_header = yaml.safe_dump(
            front_matter,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )
        return f"---\n{yaml_header}---\n\n{content.strip()}\n"

    @staticmethod
    def _parse_markdown(raw_content: str) -> tuple[Dict[str, Any], str]:
        """Split a Markdown document into YAML metadata and body."""
        if not raw_content.startswith("---\n"):
            return {}, raw_content.strip()
        delimiter = raw_content.find("\n---\n", 4)
        if delimiter < 0:
            raise ValueError("YAML 前置元数据缺少结束分隔符")
        yaml_text = raw_content[4:delimiter]
        content = raw_content[delimiter + 5 :].strip()
        metadata = yaml.safe_load(yaml_text) or {}
        if not isinstance(metadata, dict):
            raise ValueError("YAML 前置元数据必须是键值映射")
        return metadata, content

    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        if not self.index_path.exists():
            rebuilt = self._rebuild_index()
            if rebuilt:
                self.index = rebuilt
                self._save_index()
            return rebuilt
        try:
            data = json.loads(self.index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"无法读取笔记索引：{error}") from error
        if not isinstance(data, dict):
            raise ValueError("笔记索引必须是 JSON 对象")
        return {
            str(note_id): self._normalize_metadata(metadata)
            for note_id, metadata in data.items()
            if isinstance(metadata, dict)
        }

    def _rebuild_index(self) -> Dict[str, Dict[str, Any]]:
        """Recover the JSON index from valid Markdown files when absent."""
        rebuilt: Dict[str, Dict[str, Any]] = {}
        for path in sorted(self.workspace.glob("note_*.md")):
            try:
                metadata, _ = self._parse_markdown(
                    path.read_text(encoding="utf-8"),
                )
                metadata = self._normalize_metadata(metadata)
                note_id = str(metadata.get("id", ""))
                if note_id and path.name == f"{note_id}.md":
                    rebuilt[note_id] = self._index_entry(metadata, path)
            except Exception as error:
                warnings.warn(
                    f"跳过无法重建索引的文件 {path.name}：{error}",
                    RuntimeWarning,
                    stacklevel=2,
                )
        return rebuilt

    def _save_index(self) -> None:
        payload = json.dumps(
            self.index,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        self._atomic_write(self.index_path, payload + "\n")

    def _write_note(
        self,
        path: Path,
        metadata: Dict[str, Any],
        content: str,
    ) -> None:
        self._assert_in_workspace(path)
        self._atomic_write(path, self._build_markdown(metadata, content))

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(path)

    def _new_note_id(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        counter = len(self.index)
        while True:
            note_id = f"note_{timestamp}_{counter}"
            if note_id not in self.index and not self._note_path(note_id).exists():
                return note_id
            counter += 1

    def _note_path(self, note_id: str) -> Path:
        path = (self.workspace / f"{note_id}.md").resolve()
        self._assert_in_workspace(path)
        return path

    def _indexed_path(self, note_id: str) -> Path:
        metadata = self.index[note_id]
        raw_path = metadata.get("file_path")
        path = Path(raw_path).expanduser() if raw_path else self._note_path(note_id)
        if not path.is_absolute():
            path = self.workspace / path
        path = path.resolve()
        self._assert_in_workspace(path)
        if path.name != f"{note_id}.md":
            raise ValueError(f"索引文件名与笔记 ID 不一致：{note_id}")
        return path

    def _assert_in_workspace(self, path: Path) -> None:
        try:
            path.relative_to(self.workspace)
        except ValueError as error:
            raise ValueError("笔记路径超出工作目录") from error

    @staticmethod
    def _index_entry(
        metadata: Dict[str, Any],
        path: Path,
    ) -> Dict[str, Any]:
        return {
            "id": metadata["id"],
            "title": metadata["title"],
            "type": metadata["type"],
            "tags": list(metadata.get("tags", [])),
            "created_at": metadata["created_at"],
            "updated_at": metadata["updated_at"],
            "file_path": str(path),
        }

    @staticmethod
    def _public_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        result = dict(metadata)
        result["note_id"] = result["id"]
        return result

    def _note_result(
        self,
        metadata: Dict[str, Any],
        content: str,
    ) -> Dict[str, Any]:
        result = self._public_metadata(metadata)
        result["content"] = content
        return result

    @staticmethod
    def _matches_filters(
        metadata: Dict[str, Any],
        note_type: str | None,
        tags: set[str],
    ) -> bool:
        if note_type and metadata.get("type") != note_type:
            return False
        if tags and not tags.intersection(metadata.get("tags", [])):
            return False
        return True

    @staticmethod
    def _normalize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        result = dict(metadata)
        for key in ("created_at", "updated_at"):
            value = result.get(key)
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, date):
                result[key] = value.isoformat()
            elif value is not None:
                result[key] = str(value)
        result["tags"] = NoteTool._normalize_tags(result.get("tags"))
        return result

    @staticmethod
    def _normalize_tags(tags: List[str] | str | None) -> List[str]:
        if tags is None:
            return []
        values = tags.split(",") if isinstance(tags, str) else list(tags)
        normalized = []
        for value in values:
            tag = str(value).strip()
            if tag and tag not in normalized:
                normalized.append(tag)
        return normalized

    @staticmethod
    def _validate_note_type(note_type: str) -> str:
        selected = str(note_type).lower().strip()
        if selected not in NOTE_TYPES:
            choices = "、".join(sorted(NOTE_TYPES))
            raise ValueError(f"不支持的笔记类型，可选值：{choices}")
        return selected

    @staticmethod
    def _validate_text(value: str, name: str) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError(f"{name} 不能为空")
        return text

    @staticmethod
    def _validate_note_id(note_id: str) -> str:
        selected = str(note_id or "").strip()
        if not selected:
            raise ValueError("note_id 不能为空")
        allowed_characters = (
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789_"
        )
        if not selected.startswith("note_") or any(
            character not in allowed_characters
            for character in selected
        ):
            raise ValueError("note_id 格式不合法")
        return selected

    @staticmethod
    def _validate_limit(limit: int) -> int:
        value = int(limit)
        if value <= 0:
            raise ValueError("limit 必须大于 0")
        return value

    @staticmethod
    def _now_iso() -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")
