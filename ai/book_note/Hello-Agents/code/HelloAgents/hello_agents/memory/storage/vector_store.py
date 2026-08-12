"""A small SQLite-backed vector-search adapter for local practice."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List

from ..embedding import EmbeddingModel


@dataclass(frozen=True)
class VectorSearchResult:
    memory_id: str
    score: float
    metadata: Dict[str, Any]


class SQLiteVectorStore:
    """Persist vector-source text and calculate TF-IDF search locally.

    It follows the vector-store boundary used by the chapter while avoiding a
    mandatory Qdrant service for the runnable example. A production adapter can
    replace this class without changing the four memory types.
    """

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
                CREATE TABLE IF NOT EXISTS memory_vectors (
                    memory_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    namespace TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
                """,
            )
            self._connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_vectors_scope
                ON memory_vectors(user_id, memory_type, namespace)
                """,
            )

    def upsert(
        self,
        memory_id: str,
        user_id: str,
        memory_type: str,
        content: str,
        namespace: str = "text",
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO memory_vectors(
                    memory_id, user_id, memory_type,
                    namespace, content, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(memory_id) DO UPDATE SET
                    user_id = excluded.user_id,
                    memory_type = excluded.memory_type,
                    namespace = excluded.namespace,
                    content = excluded.content,
                    metadata_json = excluded.metadata_json
                """,
                (
                    memory_id,
                    user_id,
                    memory_type,
                    namespace,
                    content,
                    json.dumps(metadata or {}, ensure_ascii=False, default=str),
                ),
            )

    def search(
        self,
        query: str,
        embedder: EmbeddingModel,
        user_id: str,
        memory_type: str,
        namespace: str | None = None,
        limit: int | None = None,
    ) -> List[VectorSearchResult]:
        clauses = ["user_id = ?", "memory_type = ?"]
        values: List[Any] = [user_id, memory_type]
        if namespace:
            clauses.append("namespace = ?")
            values.append(namespace)
        sql = (
            "SELECT * FROM memory_vectors WHERE "
            + " AND ".join(clauses)
            + " ORDER BY memory_id"
        )
        with self._lock:
            rows = self._connection.execute(sql, values).fetchall()

        if not rows:
            return []
        scores = (
            embedder.similarities(query, [row["content"] for row in rows])
            if query.strip()
            else [1.0] * len(rows)
        )
        results = [
            VectorSearchResult(
                memory_id=row["memory_id"],
                score=score,
                metadata=json.loads(row["metadata_json"]),
            )
            for row, score in zip(rows, scores)
        ]
        results.sort(key=lambda result: result.score, reverse=True)
        return results[:limit] if limit is not None else results

    def remove(self, memory_id: str) -> bool:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "DELETE FROM memory_vectors WHERE memory_id = ?",
                (memory_id,),
            )
        return cursor.rowcount > 0

    def clear(self, user_id: str, memory_type: str) -> int:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                """
                DELETE FROM memory_vectors
                WHERE user_id = ? AND memory_type = ?
                """,
                (user_id, memory_type),
            )
        return cursor.rowcount

    def close(self) -> None:
        with self._lock:
            self._connection.close()

