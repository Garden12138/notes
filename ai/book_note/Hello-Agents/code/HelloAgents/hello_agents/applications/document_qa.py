"""Document Q&A learning assistant built from RAGTool and MemoryTool."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from time import perf_counter
from typing import Any, Callable, Dict, List
from uuid import uuid4

from ..memory import MemoryConfig
from ..tools import MemoryTool, RAGTool


class PDFLearningAssistant:
    """Combine document retrieval, learning memory, and session reporting.

    The class name and public methods follow chapter 8.4. The underlying
    ``RAGTool`` can also load Markdown and text files, which keeps the example
    testable without hiding the PDF/MarkItDown dependency.
    """

    def __init__(
        self,
        user_id: str = "default_user",
        data_dir: str | Path = "./document_qa_data",
        memory_config: MemoryConfig | None = None,
        memory_tool: MemoryTool | None = None,
        rag_tool: RAGTool | None = None,
        llm: Any | None = None,
    ) -> None:
        self.user_id = validate_user_id(user_id)
        self.data_dir = Path(data_dir).expanduser().resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir = self.data_dir / "reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.session_start = utc_now()
        self.session_id = (
            f"session_{self.session_start.strftime('%Y%m%d_%H%M%S')}"
            f"_{uuid4().hex[:8]}"
        )
        self.namespace = f"pdf_{self.user_id}"

        if memory_tool is not None and memory_config is not None:
            raise ValueError(
                "memory_tool and memory_config cannot both be provided",
            )
        selected_config = memory_config or MemoryConfig(
            storage_path=str(self.data_dir / "memory"),
        )
        self.memory_tool = memory_tool or MemoryTool(
            user_id=self.user_id,
            config=selected_config,
        )
        if self.memory_tool.user_id != self.user_id:
            raise ValueError("memory_tool user_id does not match assistant user_id")
        self.memory_tool.session_id = self.session_id

        self.rag_tool = rag_tool or RAGTool(
            knowledge_base_path=str(self.data_dir / "knowledge_base"),
            database_path=str(self.data_dir / "rag_index.db"),
            rag_namespace=self.namespace,
            llm=llm,
        )
        if self.rag_tool.rag_namespace != self.namespace:
            raise ValueError(
                "rag_tool namespace does not match assistant user namespace",
            )

        self.current_document: str | None = None
        self.current_document_path: str | None = None
        self.loaded_documents: List[Dict[str, str]] = []
        self.interactions: List[Dict[str, Any]] = []
        self.notes: List[Dict[str, Any]] = []
        self.memory_warnings: List[str] = []
        self.stats = {
            "documents_loaded": 0,
            "questions_asked": 0,
            "concepts_learned": 0,
        }
        self._lock = RLock()
        self._closed = False

    def load_document(
        self,
        document_path: str | Path,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> Dict[str, Any]:
        """Load one document and record the event in episodic memory."""
        path = Path(document_path).expanduser().resolve()
        if not path.is_file():
            return {"success": False, "message": f"文件不存在：{path}"}
        if chunk_size <= 0:
            return {"success": False, "message": "chunk_size 必须大于 0"}
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            return {
                "success": False,
                "message": "chunk_overlap 必须满足 0 <= overlap < chunk_size",
            }

        document_id = stable_document_id(path)
        started = perf_counter()
        rag_result = self.rag_tool.execute(
            "add_document",
            file_path=str(path),
            document_id=document_id,
            namespace=self.namespace,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        elapsed = perf_counter() - started
        if is_tool_error(rag_result):
            return {
                "success": False,
                "message": f"加载失败：{strip_error_prefix(rag_result)}",
                "rag_result": rag_result,
            }

        memory_result = self.memory_tool.execute(
            "add",
            content=f"加载了文档《{path.name}》",
            memory_type="episodic",
            importance=0.9,
            event_type="document_loaded",
            document_id=document_id,
            source_path=str(path),
            session_id=self.session_id,
        )
        warning = self._remember_warning(memory_result)
        loaded_at = utc_now().isoformat()
        with self._lock:
            self.current_document = path.name
            self.current_document_path = str(path)
            self.stats["documents_loaded"] += 1
            self.loaded_documents.append(
                {
                    "document_id": document_id,
                    "name": path.name,
                    "path": str(path),
                    "loaded_at": loaded_at,
                },
            )

        result: Dict[str, Any] = {
            "success": True,
            "message": f"加载成功（耗时：{elapsed:.2f} 秒）",
            "document": path.name,
            "document_id": document_id,
            "rag_result": rag_result,
        }
        if warning:
            result["memory_warning"] = warning
        return result

    def ask(self, question: str, use_advanced_search: bool = True) -> str:
        """Answer one question from the loaded knowledge base."""
        normalized = question.strip()
        if not normalized:
            return "错误：问题不能为空。"
        if not self.current_document:
            return "请先加载文档。"

        working_result = self.memory_tool.execute(
            "add",
            content=f"提问：{normalized}",
            memory_type="working",
            importance=0.6,
            event_type="question",
            document=self.current_document,
            session_id=self.session_id,
        )
        self._remember_warning(working_result)

        answer = self.rag_tool.execute(
            "ask",
            question=normalized,
            namespace=self.namespace,
            limit=5,
            enable_advanced_search=bool(use_advanced_search),
            enable_mqe=bool(use_advanced_search),
            enable_hyde=bool(use_advanced_search),
            include_citations=True,
        )
        if is_tool_error(answer):
            return answer

        episodic_result = self.memory_tool.execute(
            "add",
            content=(
                f"围绕《{self.current_document}》提问：{normalized}\n"
                f"回答：{answer[:1200]}"
            ),
            memory_type="episodic",
            importance=0.7,
            event_type="qa_interaction",
            document=self.current_document,
            session_id=self.session_id,
        )
        self._remember_warning(episodic_result)
        asked_at = utc_now().isoformat()
        with self._lock:
            self.stats["questions_asked"] += 1
            self.interactions.append(
                {
                    "question": normalized,
                    "answer": answer,
                    "document": self.current_document,
                    "advanced_search": bool(use_advanced_search),
                    "asked_at": asked_at,
                },
            )
        return answer

    def add_note(self, content: str, concept: str | None = None) -> str:
        """Persist one learning note as semantic memory."""
        normalized = content.strip()
        if not normalized:
            return "错误：笔记内容不能为空。"
        selected_concept = (concept or "general").strip() or "general"
        memory_result = self.memory_tool.execute(
            "add",
            content=normalized,
            memory_type="semantic",
            importance=0.8,
            concept=selected_concept,
            event_type="learning_note",
            session_id=self.session_id,
        )
        if is_tool_error(memory_result):
            return memory_result

        with self._lock:
            self.stats["concepts_learned"] += 1
            self.notes.append(
                {
                    "content": normalized,
                    "concept": selected_concept,
                    "created_at": utc_now().isoformat(),
                },
            )
        return memory_result

    def recall(self, query: str, limit: int = 5) -> str:
        """Retrieve the user's previous learning events and notes."""
        normalized = query.strip()
        if not normalized:
            return "错误：回顾查询不能为空。"
        return self.memory_tool.execute(
            "search",
            query=normalized,
            limit=int(limit),
        )

    def get_stats(self) -> Dict[str, Any]:
        """Return the chapter's session-level learning metrics."""
        duration = max(0.0, (utc_now() - self.session_start).total_seconds())
        with self._lock:
            return {
                "会话时长": f"{duration:.0f}秒",
                "加载文档": self.stats["documents_loaded"],
                "提问次数": self.stats["questions_asked"],
                "学习笔记": self.stats["concepts_learned"],
                "当前文档": self.current_document or "未加载",
            }

    def generate_report(
        self,
        save_to_file: bool = True,
        output_path: str | Path | None = None,
    ) -> Dict[str, Any]:
        """Build a serializable report and optionally write it atomically."""
        duration = max(0.0, (utc_now() - self.session_start).total_seconds())
        memory_summary = self.memory_tool.execute("summary", limit_per_type=10)
        rag_status = self.rag_tool.execute("stats", namespace=self.namespace)
        with self._lock:
            report: Dict[str, Any] = {
                "session_info": {
                    "session_id": self.session_id,
                    "user_id": self.user_id,
                    "start_time": self.session_start.isoformat(),
                    "generated_at": utc_now().isoformat(),
                    "duration_seconds": round(duration, 3),
                },
                "learning_metrics": dict(self.stats),
                "loaded_documents": list(self.loaded_documents),
                "interactions": list(self.interactions),
                "notes": list(self.notes),
                "memory_summary": memory_summary,
                "rag_status": rag_status,
                "memory_warnings": list(self.memory_warnings),
            }

        if save_to_file:
            target = (
                Path(output_path).expanduser().resolve()
                if output_path is not None
                else self.report_dir / f"learning_report_{self.session_id}.json"
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            report["report_file"] = str(target)
            temporary = target.with_suffix(target.suffix + ".tmp")
            temporary.write_text(
                json.dumps(report, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary.replace(target)
        return report

    def close(self) -> None:
        """Close persistent tool resources once."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self.rag_tool.close()
        self.memory_tool.close()

    def _remember_warning(self, result: str) -> str | None:
        if not is_tool_error(result):
            return None
        warning = strip_error_prefix(result)
        with self._lock:
            self.memory_warnings.append(warning)
        return warning


def create_gradio_app(
    assistant_factory: Callable[[str], PDFLearningAssistant] | None = None,
) -> Any:
    """Create the four-tab Gradio UI from chapter 8.4.

    Gradio is imported lazily so the core assistant and offline demo do not
    require the optional Web dependency.
    """
    try:
        import gradio as gr
    except ImportError as error:
        raise RuntimeError(
            "Gradio is required for the Web UI: pip install 'gradio>=6,<7'",
        ) from error

    factory = assistant_factory or (lambda user_id: PDFLearningAssistant(user_id))
    assistants: Dict[str, PDFLearningAssistant] = {}
    assistants_lock = RLock()

    def get_assistant(state_key: str | None) -> PDFLearningAssistant | None:
        if not state_key:
            return None
        with assistants_lock:
            return assistants.get(state_key)

    def init_assistant(
        user_id: str,
        state_key: str | None,
    ) -> tuple[str, str]:
        key = state_key or uuid4().hex
        with assistants_lock:
            previous = assistants.pop(key, None)
        if previous is not None:
            previous.close()
        try:
            assistant = factory(user_id.strip() or "web_user")
        except Exception as error:
            return f"初始化失败：{error}", key
        with assistants_lock:
            assistants[key] = assistant
        return f"助手已初始化（用户：{assistant.user_id}）", key

    def load_document(file_path: str | None, state_key: str | None) -> str:
        assistant = get_assistant(state_key)
        if assistant is None:
            return "请先初始化助手。"
        if not file_path:
            return "请上传 PDF 文件。"
        result = assistant.load_document(file_path)
        if not result["success"]:
            return result["message"]
        return f"{result['message']}\n文档：{result['document']}"

    def chat(
        message: str,
        history: List[Dict[str, str]] | None,
        state_key: str | None,
    ) -> tuple[str, List[Dict[str, str]]]:
        records = list(history or [])
        normalized = message.strip()
        if not normalized:
            return "", records
        assistant = get_assistant(state_key)
        records.append({"role": "user", "content": normalized})
        if assistant is None:
            records.append(
                {"role": "assistant", "content": "请先初始化助手并加载文档。"},
            )
            return "", records
        if should_recall(normalized):
            response = "**学习回顾**\n\n" + assistant.recall(normalized)
        else:
            response = "**回答**\n\n" + assistant.ask(normalized)
        records.append({"role": "assistant", "content": response})
        return "", records

    def add_note(
        note_content: str,
        concept: str,
        state_key: str | None,
    ) -> str:
        assistant = get_assistant(state_key)
        if assistant is None:
            return "请先初始化助手。"
        result = assistant.add_note(note_content, concept or None)
        return result if is_tool_error(result) else "笔记已保存。"

    def show_stats(state_key: str | None) -> str:
        assistant = get_assistant(state_key)
        if assistant is None:
            return "请先初始化助手。"
        return "\n".join(
            f"- **{key}**：{value}"
            for key, value in assistant.get_stats().items()
        )

    def generate_report(
        state_key: str | None,
    ) -> tuple[str, str | None]:
        assistant = get_assistant(state_key)
        if assistant is None:
            return "请先初始化助手。", None
        report = assistant.generate_report(save_to_file=True)
        metrics = report["learning_metrics"]
        message = (
            "学习报告已生成："
            f"文档 {metrics['documents_loaded']}，"
            f"提问 {metrics['questions_asked']}，"
            f"笔记 {metrics['concepts_learned']}。"
        )
        return message, report.get("report_file")

    with gr.Blocks(title="智能文档问答助手") as demo:
        state_key = gr.State(value=None)
        gr.Markdown(
            "# 智能文档问答助手\n"
            "使用 RAGTool 检索文档，使用 MemoryTool 记录学习历程。",
        )
        with gr.Tab("开始使用"):
            with gr.Row():
                user_id_input = gr.Textbox(label="用户 ID", value="web_user")
                init_button = gr.Button("初始化助手", variant="primary")
            init_output = gr.Textbox(label="初始化状态", interactive=False)
            pdf_upload = gr.File(
                label="上传 PDF 文件",
                file_types=[".pdf"],
                type="filepath",
            )
            load_button = gr.Button("加载文档", variant="primary")
            load_output = gr.Textbox(label="加载状态", interactive=False)
            init_button.click(
                init_assistant,
                inputs=[user_id_input, state_key],
                outputs=[init_output, state_key],
            )
            load_button.click(
                load_document,
                inputs=[pdf_upload, state_key],
                outputs=load_output,
            )

        with gr.Tab("智能问答"):
            chatbot = gr.Chatbot(
                label="对话历史",
                type="messages",
                height=420,
            )
            with gr.Row():
                message_input = gr.Textbox(
                    label="问题",
                    placeholder="例如：Transformer 的核心组件有哪些？",
                    scale=4,
                )
                send_button = gr.Button("发送", variant="primary", scale=1)
            message_input.submit(
                chat,
                inputs=[message_input, chatbot, state_key],
                outputs=[message_input, chatbot],
            )
            send_button.click(
                chat,
                inputs=[message_input, chatbot, state_key],
                outputs=[message_input, chatbot],
            )

        with gr.Tab("学习笔记"):
            note_content = gr.Textbox(label="笔记内容", lines=4)
            concept_input = gr.Textbox(label="相关概念（可选）")
            note_button = gr.Button("保存笔记", variant="primary")
            note_output = gr.Textbox(label="保存状态", interactive=False)
            note_button.click(
                add_note,
                inputs=[note_content, concept_input, state_key],
                outputs=note_output,
            )

        with gr.Tab("学习统计"):
            stats_button = gr.Button("刷新统计", variant="primary")
            stats_output = gr.Markdown()
            stats_button.click(show_stats, inputs=state_key, outputs=stats_output)
            report_button = gr.Button("生成报告", variant="primary")
            report_output = gr.Textbox(label="报告状态", interactive=False)
            report_file = gr.File(label="下载 JSON 报告")
            report_button.click(
                generate_report,
                inputs=state_key,
                outputs=[report_output, report_file],
            )
    return demo


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def validate_user_id(user_id: str) -> str:
    normalized = user_id.strip()
    if not normalized:
        raise ValueError("user_id must not be blank")
    if len(normalized) > 80:
        raise ValueError("user_id must be at most 80 characters")
    if any(ord(character) < 32 for character in normalized):
        raise ValueError("user_id must not contain control characters")
    return normalized


def stable_document_id(path: Path) -> str:
    digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:20]
    return f"document_{digest}"


def is_tool_error(result: Any) -> bool:
    value = str(result).lstrip()
    return value.startswith(("错误：", "错误:", "❌"))


def strip_error_prefix(result: Any) -> str:
    return re.sub(r"^(?:错误\s*[：:]|❌)\s*", "", str(result).strip())


def should_recall(message: str) -> bool:
    return any(
        keyword in message
        for keyword in ("之前", "学过", "回顾", "历史", "记得", "笔记")
    )
