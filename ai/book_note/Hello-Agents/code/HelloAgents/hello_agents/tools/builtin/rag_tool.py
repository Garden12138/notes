"""Agent-facing retrieval-augmented generation tool."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from ...memory.embedding import EmbeddingModel
from ...memory.rag import create_rag_pipeline
from ..base import Tool, ToolParameter


class RAGTool(Tool):
    """Load documents, retrieve chunks, and answer from grounded context."""

    ACTIONS = {
        "add_document",
        "add_text",
        "ask",
        "search",
        "stats",
        "clear",
    }

    def __init__(
        self,
        knowledge_base_path: str = "./knowledge_base",
        qdrant_url: str | None = None,
        qdrant_api_key: str | None = None,
        collection_name: str = "rag_knowledge_base",
        rag_namespace: str = "default",
        database_path: str | None = None,
        embedder: EmbeddingModel | None = None,
        llm: Any | None = None,
    ) -> None:
        super().__init__(
            name="rag",
            description=(
                "向知识库添加文档或文本，检索相关片段，"
                "并基于检索上下文问答。"
                "action 支持 add_document/add_text/search/ask/stats/clear。"
            ),
        )
        self.knowledge_base_path = Path(knowledge_base_path).expanduser()
        self.knowledge_base_path.mkdir(parents=True, exist_ok=True)
        self.qdrant_url = qdrant_url
        self.qdrant_api_key = qdrant_api_key
        self.collection_name = collection_name
        self.rag_namespace = rag_namespace
        self.database_path = database_path or str(
            self.knowledge_base_path / "rag_index.db",
        )
        self.embedder = embedder
        self.llm = llm
        self._pipelines: Dict[str, Dict[str, Any]] = {}
        self._pipelines[rag_namespace] = self._create_pipeline(rag_namespace)

    def run(
        self,
        parameters: Dict[str, Any] | str,
        **kwargs: Any,
    ) -> str:
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
            return getattr(self, f"_{normalized}")(**parameters)
        except Exception as error:
            return f"错误：{error}"

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type="string",
                description=(
                    "add_document/add_text/search/ask/stats/clear"
                ),
            ),
            ToolParameter(
                name="file_path",
                type="string",
                description="add_document 使用的文件路径",
                required=False,
            ),
            ToolParameter(
                name="text",
                type="string",
                description="add_text 使用的 Markdown 或纯文本",
                required=False,
            ),
            ToolParameter(
                name="document_id",
                type="string",
                description="稳定文档 ID；再次写入会替换旧分块",
                required=False,
            ),
            ToolParameter(
                name="query",
                type="string",
                description="search 使用的查询",
                required=False,
            ),
            ToolParameter(
                name="question",
                type="string",
                description="ask 使用的问题",
                required=False,
            ),
            ToolParameter(
                name="namespace",
                type="string",
                description="隔离不同知识库的命名空间",
                required=False,
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="最大召回数量",
                required=False,
                default=5,
            ),
            ToolParameter(
                name="min_score",
                type="number",
                description="最低检索分数",
                required=False,
                default=0.1,
            ),
            ToolParameter(
                name="include_citations",
                type="boolean",
                description="是否在结果中保留来源",
                required=False,
                default=True,
            ),
            ToolParameter(
                name="enable_advanced_search",
                type="boolean",
                description="是否启用 MQE 与 HyDE 扩展检索",
                required=False,
                default=True,
            ),
            ToolParameter(
                name="confirm",
                type="boolean",
                description="clear 操作的显式确认",
                required=False,
                default=False,
            ),
        ]

    def _create_pipeline(self, namespace: str) -> Dict[str, Any]:
        return create_rag_pipeline(
            knowledge_base_path=self.knowledge_base_path,
            qdrant_url=self.qdrant_url,
            qdrant_api_key=self.qdrant_api_key,
            collection_name=self.collection_name,
            rag_namespace=namespace,
            database_path=self.database_path,
            embedder=self.embedder,
            llm=self.llm,
        )

    def _get_pipeline(self, namespace: str | None = None) -> Dict[str, Any]:
        selected = (namespace or self.rag_namespace).strip()
        if not selected:
            raise ValueError("namespace must not be blank")
        if selected not in self._pipelines:
            self._pipelines[selected] = self._create_pipeline(selected)
        return self._pipelines[selected]

    def _add_document(
        self,
        file_path: str,
        document_id: str | None = None,
        namespace: str | None = None,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
        **_: Any,
    ) -> str:
        if not file_path:
            raise ValueError("file_path 不能为空")
        path = Path(file_path).expanduser().resolve()
        pipeline = self._get_pipeline(namespace)
        document_ids = {str(path): document_id} if document_id else None
        count = pipeline["add_documents"](
            [path],
            chunk_size=int(chunk_size),
            chunk_overlap=int(chunk_overlap),
            document_ids=document_ids,
        )
        return (
            f"已添加文档：{path.name}\n"
            f"分块数量：{count}\n"
            f"命名空间：{pipeline['namespace']}"
        )

    def _add_text(
        self,
        text: str,
        document_id: str | None = None,
        namespace: str | None = None,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
        **metadata: Any,
    ) -> str:
        if not text or not text.strip():
            raise ValueError("text 不能为空")
        pipeline = self._get_pipeline(namespace)
        count = pipeline["add_text"](
            text=text,
            document_id=document_id,
            chunk_size=int(chunk_size),
            chunk_overlap=int(chunk_overlap),
            **metadata,
        )
        resolved_id = document_id or "content-hash"
        return (
            f"已添加文本：{resolved_id}\n"
            f"分块数量：{count}\n"
            f"命名空间：{pipeline['namespace']}"
        )

    def _search(
        self,
        query: str | None = None,
        question: str | None = None,
        limit: int = 5,
        min_score: float = 0.1,
        enable_advanced_search: bool = True,
        enable_mqe: bool = True,
        enable_hyde: bool = True,
        include_citations: bool = True,
        namespace: str | None = None,
        **_: Any,
    ) -> str:
        search_query = (query or question or "").strip()
        if not search_query:
            raise ValueError("query 不能为空")
        results = self.search_results(
            search_query,
            namespace=namespace,
            limit=int(limit),
            min_score=float(min_score),
            enable_advanced_search=as_bool(enable_advanced_search),
            enable_mqe=as_bool(enable_mqe),
            enable_hyde=as_bool(enable_hyde),
        )
        if not results:
            return f"未找到与“{search_query}”相关的内容。"

        lines = [f"找到 {len(results)} 个相关片段："]
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata", {})
            content = str(result.get("content", "")).replace("\n", " ")
            if len(content) > 240:
                content = content[:239].rstrip() + "…"
            score = float(result.get("score", 0.0))
            lines.append(f"{index}. {content}（相关度={score:.3f}）")
            if as_bool(include_citations):
                source = metadata.get("source_name") or metadata.get(
                    "source_path",
                    "unknown",
                )
                heading = metadata.get("heading_path")
                suffix = f" > {heading}" if heading else ""
                lines.append(f"   来源：{source}{suffix}")
        return "\n".join(lines)

    def _ask(
        self,
        question: str | None = None,
        query: str | None = None,
        limit: int = 5,
        min_score: float = 0.1,
        enable_advanced_search: bool = True,
        enable_mqe: bool = True,
        enable_hyde: bool = True,
        include_citations: bool = True,
        max_chars: int = 1200,
        namespace: str | None = None,
        **_: Any,
    ) -> str:
        user_question = (question or query or "").strip()
        if not user_question:
            raise ValueError("question 不能为空")
        pipeline = self._get_pipeline(namespace)
        llm = self._get_llm()
        results = self.search_results(
            user_question,
            namespace=namespace,
            limit=int(limit),
            min_score=float(min_score),
            enable_advanced_search=as_bool(enable_advanced_search),
            enable_mqe=as_bool(enable_mqe),
            enable_hyde=as_bool(enable_hyde),
        )
        if not results:
            return f"知识库中没有找到与“{user_question}”相关的信息。"
        context, citations = pipeline["build_context"](
            results,
            max_chars=int(max_chars),
            include_citations=as_bool(include_citations),
        )
        if not context:
            return "检索到了候选片段，但未能构建有效上下文。"

        messages = pipeline["pipeline"].answer_messages(
            user_question,
            context,
        )
        answer = str(llm.invoke(messages) or "").strip()
        if not answer:
            return "模型未生成有效回答。"
        if as_bool(include_citations) and citations:
            answer += "\n\n参考来源："
            for citation in citations:
                heading = (
                    f" > {citation['heading']}"
                    if citation.get("heading")
                    else ""
                )
                answer += (
                    f"\n[{citation['index']}] {citation['source']}"
                    f"{heading}（相关度={citation['score']:.3f}）"
                )
        return answer

    def _stats(
        self,
        namespace: str | None = None,
        **_: Any,
    ) -> str:
        pipeline = self._get_pipeline(namespace)
        stats = pipeline["get_stats"]()
        sources = stats.get("sources", [])
        return "\n".join(
            [
                "RAG 知识库统计：",
                f"- 集合：{stats['collection_name']}",
                f"- 命名空间：{stats['namespace']}",
                f"- 文档数：{stats['documents_count']}",
                f"- 分块数：{stats['chunks_count']}",
                f"- 存储：{stats['store_type']}",
                f"- 来源数：{len(sources)}",
            ],
        )

    def _clear(
        self,
        confirm: bool = False,
        namespace: str | None = None,
        **_: Any,
    ) -> str:
        if not as_bool(confirm):
            return "清空知识库需要显式设置 confirm=true。"
        pipeline = self._get_pipeline(namespace)
        count = pipeline["clear"]()
        return (
            f"已清空命名空间 {pipeline['namespace']}，"
            f"删除 {count} 个分块。"
        )

    def search_results(
        self,
        query: str,
        namespace: str | None = None,
        limit: int = 5,
        min_score: float = 0.1,
        enable_advanced_search: bool = True,
        enable_mqe: bool = True,
        enable_hyde: bool = True,
    ) -> List[Dict[str, Any]]:
        pipeline = self._get_pipeline(namespace)
        threshold = min_score if min_score > 0 else None
        if enable_advanced_search:
            return pipeline["search_advanced"](
                query=query,
                top_k=limit,
                score_threshold=threshold,
                enable_mqe=enable_mqe,
                enable_hyde=enable_hyde,
            )
        return pipeline["search"](
            query=query,
            top_k=limit,
            score_threshold=threshold,
        )

    def get_relevant_context(
        self,
        query: str,
        limit: int = 3,
        max_chars: int = 1200,
        namespace: str | None = None,
    ) -> str:
        pipeline = self._get_pipeline(namespace)
        results = self.search_results(
            query,
            namespace=namespace,
            limit=limit,
            enable_advanced_search=False,
        )
        context, _ = pipeline["build_context"](
            results,
            max_chars=max_chars,
            include_citations=True,
        )
        return context

    def add_document(
        self,
        file_path: str,
        namespace: str | None = None,
        **kwargs: Any,
    ) -> str:
        return self._add_document(file_path, namespace=namespace, **kwargs)

    def add_text(
        self,
        text: str,
        namespace: str | None = None,
        **kwargs: Any,
    ) -> str:
        return self._add_text(text, namespace=namespace, **kwargs)

    def search(
        self,
        query: str,
        namespace: str | None = None,
        **kwargs: Any,
    ) -> str:
        return self._search(query=query, namespace=namespace, **kwargs)

    def ask(
        self,
        question: str,
        namespace: str | None = None,
        **kwargs: Any,
    ) -> str:
        return self._ask(question=question, namespace=namespace, **kwargs)

    def close(self) -> None:
        closed: set[int] = set()
        for pipeline in self._pipelines.values():
            store = pipeline["store"]
            if id(store) not in closed:
                store.close()
                closed.add(id(store))

    def _get_llm(self) -> Any:
        if self.llm is None:
            from ...core.llm import HelloAgentsLLM

            self.llm = HelloAgentsLLM()
            for pipeline in self._pipelines.values():
                pipeline["pipeline"].llm = self.llm
        return self.llm


def as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.lower().strip() in {"1", "true", "yes", "on"}
    return bool(value)
