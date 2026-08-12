"""SQLite entity and relation index used by semantic memory."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import RLock
from typing import Dict, Iterable, List, Tuple

from ..embedding import keyword_overlap


class SQLiteGraphStore:
    """Store the small entity graph required by the chapter's local demo."""

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
                CREATE TABLE IF NOT EXISTS memory_entities (
                    memory_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    entity TEXT NOT NULL,
                    PRIMARY KEY(memory_id, entity)
                )
                """,
            )
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_relations (
                    memory_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    target TEXT NOT NULL,
                    PRIMARY KEY(memory_id, source, relation, target)
                )
                """,
            )

    def upsert(
        self,
        memory_id: str,
        user_id: str,
        entities: Iterable[str],
        relations: Iterable[Tuple[str, str, str]],
    ) -> None:
        with self._lock, self._connection:
            self._remove_without_commit(memory_id)
            self._connection.executemany(
                """
                INSERT OR IGNORE INTO memory_entities(memory_id, user_id, entity)
                VALUES (?, ?, ?)
                """,
                [
                    (memory_id, user_id, entity)
                    for entity in entities
                    if entity.strip()
                ],
            )
            self._connection.executemany(
                """
                INSERT OR IGNORE INTO memory_relations(
                    memory_id, user_id, source, relation, target
                ) VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (memory_id, user_id, source, relation, target)
                    for source, relation, target in relations
                    if source.strip() and target.strip()
                ],
            )

    def search(
        self,
        query: str,
        user_id: str,
        limit: int | None = None,
    ) -> Dict[str, float]:
        if not query.strip():
            return {}
        with self._lock:
            entity_rows = self._connection.execute(
                "SELECT memory_id, entity FROM memory_entities WHERE user_id = ?",
                (user_id,),
            ).fetchall()
            relation_rows = self._connection.execute(
                """
                SELECT memory_id, source, relation, target
                FROM memory_relations WHERE user_id = ?
                """,
                (user_id,),
            ).fetchall()

        scores: Dict[str, float] = {}
        normalized_query = query.lower()
        for row in entity_rows:
            entity = row["entity"]
            score = (
                1.0
                if entity.lower() in normalized_query
                else keyword_overlap(query, entity)
            )
            scores[row["memory_id"]] = max(scores.get(row["memory_id"], 0.0), score)
        for row in relation_rows:
            statement = f"{row['source']} {row['relation']} {row['target']}"
            score = keyword_overlap(query, statement)
            scores[row["memory_id"]] = max(scores.get(row["memory_id"], 0.0), score)

        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        if limit is not None:
            ranked = ranked[:limit]
        return dict(ranked)

    def remove(self, memory_id: str) -> bool:
        with self._lock, self._connection:
            removed = self._remove_without_commit(memory_id)
        return removed > 0

    def _remove_without_commit(self, memory_id: str) -> int:
        entity_cursor = self._connection.execute(
            "DELETE FROM memory_entities WHERE memory_id = ?",
            (memory_id,),
        )
        relation_cursor = self._connection.execute(
            "DELETE FROM memory_relations WHERE memory_id = ?",
            (memory_id,),
        )
        return entity_cursor.rowcount + relation_cursor.rowcount

    def clear(self, user_id: str) -> int:
        with self._lock, self._connection:
            entity_cursor = self._connection.execute(
                "DELETE FROM memory_entities WHERE user_id = ?",
                (user_id,),
            )
            relation_cursor = self._connection.execute(
                "DELETE FROM memory_relations WHERE user_id = ?",
                (user_id,),
            )
        return entity_cursor.rowcount + relation_cursor.rowcount

    def close(self) -> None:
        with self._lock:
            self._connection.close()
