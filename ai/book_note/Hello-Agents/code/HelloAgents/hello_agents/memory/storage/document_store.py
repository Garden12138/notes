"""SQLite document storage for persistent memory records."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List

from ..base import MemoryItem, TimeRange, ensure_aware


class SQLiteDocumentStore:
    """Persist normalized ``MemoryItem`` objects in one local database."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._connection = sqlite3.connect(
            str(self.database_path),
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        self._initialize()

    def _initialize(self) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    importance REAL NOT NULL,
                    metadata_json TEXT NOT NULL
                )
                """,
            )
            self._connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memories_scope
                ON memories(user_id, memory_type, timestamp)
                """,
            )

    def save(self, item: MemoryItem) -> str:
        data = item.as_dict()
        timestamp = ensure_aware(data["timestamp"]).isoformat()
        metadata = json.dumps(
            data["metadata"],
            ensure_ascii=False,
            default=str,
        )
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO memories(
                    id, user_id, memory_type, content,
                    timestamp, importance, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_id = excluded.user_id,
                    memory_type = excluded.memory_type,
                    content = excluded.content,
                    timestamp = excluded.timestamp,
                    importance = excluded.importance,
                    metadata_json = excluded.metadata_json
                """,
                (
                    data["id"],
                    data["user_id"],
                    data["memory_type"],
                    data["content"],
                    timestamp,
                    data["importance"],
                    metadata,
                ),
            )
        return item.id

    def get(self, memory_id: str) -> MemoryItem | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM memories WHERE id = ?",
                (memory_id,),
            ).fetchone()
        return self._from_row(row) if row else None

    def list_items(
        self,
        user_id: str,
        memory_type: str,
        min_importance: float = 0.0,
        time_range: TimeRange | None = None,
        limit: int | None = None,
    ) -> List[MemoryItem]:
        clauses = [
            "user_id = ?",
            "memory_type = ?",
            "importance >= ?",
        ]
        values: List[Any] = [user_id, memory_type, min_importance]
        if time_range:
            start, end = time_range
            clauses.extend(["timestamp >= ?", "timestamp <= ?"])
            values.extend(
                [ensure_aware(start).isoformat(), ensure_aware(end).isoformat()],
            )

        sql = (
            "SELECT * FROM memories WHERE "
            + " AND ".join(clauses)
            + " ORDER BY timestamp DESC"
        )
        if limit is not None:
            sql += " LIMIT ?"
            values.append(max(0, limit))

        with self._lock:
            rows = self._connection.execute(sql, values).fetchall()
        return [self._from_row(row) for row in rows]

    def remove(self, memory_id: str) -> bool:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "DELETE FROM memories WHERE id = ?",
                (memory_id,),
            )
        return cursor.rowcount > 0

    def clear(self, user_id: str, memory_type: str) -> int:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "DELETE FROM memories WHERE user_id = ? AND memory_type = ?",
                (user_id, memory_type),
            )
        return cursor.rowcount

    def count(self, user_id: str, memory_type: str) -> int:
        with self._lock:
            row = self._connection.execute(
                """
                SELECT COUNT(*) AS count FROM memories
                WHERE user_id = ? AND memory_type = ?
                """,
                (user_id, memory_type),
            ).fetchone()
        return int(row["count"])

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    @staticmethod
    def _from_row(row: sqlite3.Row) -> MemoryItem:
        return MemoryItem(
            id=row["id"],
            user_id=row["user_id"],
            memory_type=row["memory_type"],
            content=row["content"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            importance=float(row["importance"]),
            metadata=json.loads(row["metadata_json"]),
        )

