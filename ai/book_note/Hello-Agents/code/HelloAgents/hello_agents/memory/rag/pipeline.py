"""End-to-end RAG pipeline: load, chunk, index, retrieve, and augment."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

from ..embedding import EmbeddingModel, TFIDFEmbedding
from .document import DocumentProcessor
from .store import SQLiteRAGStore


class RAGPipeline:
    """The chapter's reusable RAG data and query pipeline."""

    def __init__(
        self,
        knowledge_base_path: str | Path = "./knowledge_base",
        collection_name: str = "rag_knowledge_base",
        rag_namespace: str = "default",
        database_path: str | Path | None = None,
        embedder: EmbeddingModel | None = None,
        llm: Any | None = None,
        store: SQLiteRAGStore | None = None,
    ) -> None:
        self.knowledge_base_path = Path(knowledge_base_path).expanduser()
        self.knowledge_base_path.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.namespace = rag_namespace
        self.embedder = embedder or TFIDFEmbedding()
        self.llm = llm
        self.store = store or SQLiteRAGStore(
            database_path or self.knowledge_base_path / "rag_index.db",
            collection_name=collection_name,
        )
        self.last_expansions: List[str] = []

    def add_documents(
        self,
        file_paths: Iterable[str | Path],
        chunk_size: int = 800,
        chunk_overlap: int = 100,
        document_ids: Dict[str, str] | None = None,
    ) -> int:
        processor = DocumentProcessor(chunk_size, chunk_overlap)
        total = 0
        for file_path in file_paths:
            path = Path(file_path).expanduser().resolve()
            document_id = None
            if document_ids:
                document_id = document_ids.get(str(file_path))
                document_id = document_id or document_ids.get(str(path))
            document = processor.load_file(path, document_id=document_id)
            chunks = processor.process_document(document)
            total += self.store.replace_document(
                self.namespace,
                str(document.doc_id),
                chunks,
            )
        return total

    def add_text(
        self,
        text: str,
        document_id: str | None = None,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
        **metadata: Any,
    ) -> int:
        processor = DocumentProcessor(chunk_size, chunk_overlap)
        document = processor.create_document(
            text,
            document_id=document_id,
            **metadata,
        )
        chunks = processor.process_document(document)
        return self.store.replace_document(
            self.namespace,
            str(document.doc_id),
            chunks,
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float | None = None,
    ) -> List[Dict[str, Any]]:
        return self.store.search(
            query=query,
            embedder=self.embedder,
            namespace=self.namespace,
            limit=top_k,
            score_threshold=score_threshold,
        )

    def search_advanced(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float | None = None,
        enable_mqe: bool = False,
        mqe_expansions: int = 2,
        enable_hyde: bool = False,
        candidate_pool_multiplier: int = 4,
    ) -> List[Dict[str, Any]]:
        if not query.strip() or top_k <= 0:
            return []

        expansions = [query.strip()]
        if enable_mqe and mqe_expansions > 0:
            expansions.extend(self.generate_mqe(query, mqe_expansions))
        if enable_hyde:
            hypothetical = self.generate_hyde(query)
            if hypothetical:
                expansions.append(hypothetical)
        self.last_expansions = unique_texts(expansions)

        pool_size = max(top_k * max(1, candidate_pool_multiplier), 20)
        per_query = max(1, pool_size // len(self.last_expansions))
        aggregated: Dict[str, Dict[str, Any]] = {}
        for expanded_query in self.last_expansions:
            hits = self.search(
                expanded_query,
                top_k=per_query,
                score_threshold=score_threshold,
            )
            for hit in hits:
                chunk_id = str(hit["id"])
                score = float(hit.get("score", 0.0))
                previous = aggregated.get(chunk_id)
                if previous is None or score > float(previous["score"]):
                    copy = {
                        **hit,
                        "metadata": {
                            **hit.get("metadata", {}),
                            "matched_query": expanded_query,
                        },
                    }
                    aggregated[chunk_id] = copy

        ranked = sorted(
            aggregated.values(),
            key=lambda result: float(result.get("score", 0.0)),
            reverse=True,
        )
        return ranked[:top_k]

    def generate_mqe(self, query: str, count: int) -> List[str]:
        if self.llm is None or count <= 0:
            return []
        messages = [
            {
                "role": "system",
                "content": (
                    "你是检索查询扩展助手。"
                    "生成语义等价或互补的多样化查询。"
                    "使用中文，简短，每行一个，不要解释。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"原始查询：{query}\n"
                    f"请给出 {count} 个不同表述。"
                ),
            },
        ]
        try:
            response = str(self.llm.invoke(messages) or "")
        except Exception:
            return []
        outputs = []
        for line in response.splitlines():
            cleaned = re.sub(r"^\s*(?:[-*•]|\d+[.)、])\s*", "", line).strip()
            if cleaned and cleaned != query:
                outputs.append(cleaned)
        return unique_texts(outputs)[:count]

    def generate_hyde(self, query: str) -> str | None:
        if self.llm is None:
            return None
        messages = [
            {
                "role": "system",
                "content": (
                    "根据问题写一段可能的答案性文档用于检索。"
                    "只写客观段落，不要分析过程。"
                ),
            },
            {"role": "user", "content": f"问题：{query}"},
        ]
        try:
            response = str(self.llm.invoke(messages) or "").strip()
        except Exception:
            return None
        return response or None

    def build_context(
        self,
        results: List[Dict[str, Any]],
        max_chars: int = 1200,
        include_citations: bool = True,
    ) -> tuple[str, List[Dict[str, Any]]]:
        if max_chars <= 0:
            return "", []
        blocks: List[str] = []
        citations: List[Dict[str, Any]] = []
        used = 0

        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata", {})
            content = clean_for_context(
                str(result.get("content") or metadata.get("content") or ""),
            )
            if not content:
                continue
            source = str(
                metadata.get("source_name")
                or metadata.get("source_path")
                or "unknown",
            )
            heading = metadata.get("heading_path")
            label = f"[{index}] {source}"
            if heading:
                label += f" > {heading}"
            block = f"{label}\n{content}" if include_citations else content
            separator_length = 2 if blocks else 0
            remaining = max_chars - used - separator_length
            if remaining <= 0:
                break
            if len(block) > remaining:
                block = truncate_at_boundary(block, remaining)
            if not block:
                break
            blocks.append(block)
            used += separator_length + len(block)
            citations.append(
                {
                    "index": index,
                    "source": source,
                    "heading": heading,
                    "score": float(result.get("score", 0.0)),
                    "doc_id": result.get("doc_id"),
                    "chunk_id": result.get("id"),
                },
            )
            if used >= max_chars:
                break
        return "\n\n".join(blocks), citations

    def answer_messages(self, question: str, context: str) -> List[Dict[str, str]]:
        return [
            {
                "role": "system",
                "content": (
                    "你是知识库问答助手。只能依据给定上下文回答；"
                    "上下文不足时明确说明，"
                    "不要用模型记忆补全事实。"
                    "回答中保留形如 [1] 的来源编号。"
                ),
            },
            {
                "role": "user",
                "content": f"问题：{question}\n\n相关上下文：\n{context}",
            },
        ]

    def get_stats(self) -> Dict[str, Any]:
        return self.store.get_stats(self.namespace)

    def clear(self) -> int:
        return self.store.clear_namespace(self.namespace)

    def close(self) -> None:
        self.store.close()

    def as_mapping(self) -> Dict[str, Any]:
        """Expose the function mapping used by the chapter's RAGTool code."""
        return {
            "pipeline": self,
            "store": self.store,
            "namespace": self.namespace,
            "add_documents": self.add_documents,
            "add_text": self.add_text,
            "search": self.search,
            "search_advanced": self.search_advanced,
            "build_context": self.build_context,
            "get_stats": self.get_stats,
            "clear": self.clear,
        }


def create_rag_pipeline(
    knowledge_base_path: str | Path = "./knowledge_base",
    collection_name: str = "rag_knowledge_base",
    rag_namespace: str = "default",
    database_path: str | Path | None = None,
    embedder: EmbeddingModel | None = None,
    llm: Any | None = None,
    qdrant_url: str | None = None,
    qdrant_api_key: str | None = None,
) -> Dict[str, Any]:
    """Create the chapter-compatible pipeline mapping.

    ``qdrant_url`` and ``qdrant_api_key`` remain in the signature so calls copied
    from the chapter fail with an explicit backend message instead of silently
    pretending to use Qdrant. The runnable learning backend is SQLite + TF-IDF;
    a Qdrant adapter can be added at the store boundary later.
    """
    if qdrant_url is not None or qdrant_api_key is not None:
        raise NotImplementedError(
            "This learning implementation uses SQLite + TF-IDF and does not "
            "connect to Qdrant. Leave qdrant_url/qdrant_api_key unset, or "
            "provide a Qdrant store adapter at the RAGPipeline boundary.",
        )
    return RAGPipeline(
        knowledge_base_path=knowledge_base_path,
        collection_name=collection_name,
        rag_namespace=rag_namespace,
        database_path=database_path,
        embedder=embedder,
        llm=llm,
    ).as_mapping()


def unique_texts(values: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    output: List[str] = []
    for value in values:
        normalized = value.strip()
        key = normalized.casefold()
        if normalized and key not in seen:
            seen.add(key)
            output.append(normalized)
    return output


def clean_for_context(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def truncate_at_boundary(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    if max_chars <= 1:
        return text[:max_chars]
    candidate = text[: max_chars - 1]
    boundary = max(
        candidate.rfind("。"),
        candidate.rfind("！"),
        candidate.rfind("？"),
        candidate.rfind(". "),
        candidate.rfind("\n"),
    )
    if boundary >= int(max_chars * 0.6):
        candidate = candidate[: boundary + 1]
    return candidate.rstrip() + "…"
