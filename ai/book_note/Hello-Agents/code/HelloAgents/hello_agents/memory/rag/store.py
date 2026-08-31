"""Persistent local vector-store boundary for the RAG learning example."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Iterable, List

from ..embedding import EmbeddingModel
from .document import (
    DocumentChunk,
    preprocess_markdown_for_embedding,
    utc_iso,
)


@dataclass(frozen=True)
class RAGSearchResult:
    chunk_id: str
    doc_id: str
    content: str
    score: float
    metadata: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        metadata = {**self.metadata, "content": self.content}
        return {
            "id": self.chunk_id,
            "memory_id": self.chunk_id,
            "doc_id": self.doc_id,
            "content": self.content,
            "score": self.score,
            "metadata": metadata,
        }


class SQLiteRAGStore:
    """Persist chunks and perform local TF-IDF search within one namespace."""

    def __init__(
        self,
        database_path: str | Path,
        collection_name: str = "rag_knowledge_base",
    ) -> None:
        if not collection_name.strip():
            raise ValueError("collection_name must not be blank")
        self.database_path = Path(database_path).expanduser()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
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
                CREATE TABLE IF NOT EXISTS rag_chunks (
                    collection_name TEXT NOT NULL,
                    namespace TEXT NOT NULL,
                    chunk_id TEXT NOT NULL,
                    doc_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding_content TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    heading_path TEXT,
                    chunk_index INTEGER NOT NULL,
                    total_chunks INTEGER NOT NULL,
                    start_offset INTEGER NOT NULL,
                    end_offset INTEGER NOT NULL,
                    metadata_json TEXT NOT NULL,
                    indexed_at TEXT NOT NULL,
                    PRIMARY KEY(collection_name, namespace, chunk_id)
                )
                """,
            )
            self._connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_rag_chunks_scope
                ON rag_chunks(collection_name, namespace, doc_id, chunk_index)
                """,
            )

    def replace_document(
        self,
        namespace: str,
        doc_id: str,
        chunks: Iterable[DocumentChunk],
    ) -> int:
        normalized_namespace = validate_namespace(namespace)
        values = []
        for chunk in chunks:
            heading = chunk.metadata.get("heading_path")
            embedding_content = (
                f"{heading}\n{chunk.content}" if heading else chunk.content
            )
            embedding_content = preprocess_markdown_for_embedding(
                embedding_content,
            )
            values.append(
                (
                    self.collection_name,
                    normalized_namespace,
                    chunk.chunk_id,
                    doc_id,
                    chunk.content,
                    embedding_content,
                    str(chunk.metadata.get("source_path", "unknown")),
                    heading,
                    chunk.chunk_index,
                    int(chunk.metadata.get("total_chunks", len(values) + 1)),
                    int(chunk.metadata.get("start", 0)),
                    int(chunk.metadata.get("end", len(chunk.content))),
                    json.dumps(
                        chunk.metadata,
                        ensure_ascii=False,
                        default=str,
                    ),
                    utc_iso(),
                ),
            )

        with self._lock, self._connection:
            self._connection.execute(
                """
                DELETE FROM rag_chunks
                WHERE collection_name = ? AND namespace = ? AND doc_id = ?
                """,
                (self.collection_name, normalized_namespace, doc_id),
            )
            self._connection.executemany(
                """
                INSERT INTO rag_chunks(
                    collection_name, namespace, chunk_id, doc_id,
                    content, embedding_content, source_path, heading_path,
                    chunk_index, total_chunks, start_offset, end_offset,
                    metadata_json, indexed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )
        return len(values)

    def search(
        self,
        query: str,
        embedder: EmbeddingModel,
        namespace: str = "default",
        limit: int = 5,
        score_threshold: float | None = None,
    ) -> List[Dict[str, Any]]:
        if not query.strip() or limit <= 0:
            return []
        rows = self.list_rows(namespace)
        if not rows:
            return []
        scores = embedder.similarities(
            query,
            [row["embedding_content"] for row in rows],
        )
        threshold = 0.0 if score_threshold is None else float(score_threshold)
        results: List[RAGSearchResult] = []
        for row, score in zip(rows, scores):
            if score < threshold or score <= 0.0:
                continue
            results.append(
                RAGSearchResult(
                    chunk_id=row["chunk_id"],
                    doc_id=row["doc_id"],
                    content=row["content"],
                    score=round(float(score), 6),
                    metadata=json.loads(row["metadata_json"]),
                ),
            )
        results.sort(
            key=lambda result: (
                result.score,
                -int(result.metadata.get("chunk_index", 0)),
            ),
            reverse=True,
        )
        return [result.as_dict() for result in results[:limit]]

    def list_rows(self, namespace: str) -> List[sqlite3.Row]:
        normalized_namespace = validate_namespace(namespace)
        with self._lock:
            return self._connection.execute(
                """
                SELECT * FROM rag_chunks
                WHERE collection_name = ? AND namespace = ?
                ORDER BY doc_id, chunk_index
                """,
                (self.collection_name, normalized_namespace),
            ).fetchall()

    def delete_document(self, namespace: str, doc_id: str) -> int:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                """
                DELETE FROM rag_chunks
                WHERE collection_name = ? AND namespace = ? AND doc_id = ?
                """,
                (self.collection_name, validate_namespace(namespace), doc_id),
            )
        return cursor.rowcount

    def clear_namespace(self, namespace: str) -> int:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                """
                DELETE FROM rag_chunks
                WHERE collection_name = ? AND namespace = ?
                """,
                (self.collection_name, validate_namespace(namespace)),
            )
        return cursor.rowcount

    def get_stats(self, namespace: str) -> Dict[str, Any]:
        rows = self.list_rows(namespace)
        documents = {row["doc_id"] for row in rows}
        sources = sorted({row["source_path"] for row in rows})
        return {
            "store_type": "sqlite_tfidf",
            "collection_name": self.collection_name,
            "namespace": validate_namespace(namespace),
            "chunks_count": len(rows),
            "documents_count": len(documents),
            "sources": sources,
            "database_path": str(self.database_path),
        }

    def close(self) -> None:
        with self._lock:
            self._connection.close()


def validate_namespace(namespace: str) -> str:
    normalized = namespace.strip()
    if not normalized:
        raise ValueError("namespace must not be blank")
    if len(normalized) > 128:
        raise ValueError("namespace must be at most 128 characters")
    return normalized
