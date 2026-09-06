"""Long-running codebase maintainer assembled from chapter 9 components."""

from __future__ import annotations

import json
import re
import shlex
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Sequence

from ..context import ContextBuilder, ContextConfig, ContextPacket
from ..core.llm import HelloAgentsLLM
from ..core.message import Message
from ..memory import MemoryConfig
from ..tools import MemoryTool, NoteTool, TerminalTool


MAINTAINER_MODES = {"auto", "explore", "analyze", "plan"}
NOTE_RELEVANCE = {
    "blocker": 0.90,
    "action": 0.80,
    "task_state": 0.75,
    "conclusion": 0.70,
    "reference": 0.65,
    "general": 0.60,
}


class CodebaseMaintainer:
    """Coordinate JIT exploration, memory, notes, and context selection."""

    def __init__(
        self,
        project_name: str,
        codebase_path: str,
        llm: HelloAgentsLLM | Any | None = None,
        *,
        state_path: str | None = None,
        context_config: ContextConfig | None = None,
        terminal_timeout: float = 60,
        max_history_messages: int = 20,
        verbose: bool = True,
    ) -> None:
        project = project_name.strip()
        if not project:
            raise ValueError("project_name 不能为空")
        if max_history_messages <= 0:
            raise ValueError("max_history_messages 必须大于 0")

        codebase = Path(codebase_path).expanduser().resolve()
        if not codebase.is_dir():
            raise NotADirectoryError(f"代码库目录不存在：{codebase}")

        state_root = Path(
            state_path or f"./{self._safe_project_name(project)}_maintainer",
        ).expanduser().resolve()
        state_root.mkdir(parents=True, exist_ok=True)

        now = datetime.now().astimezone()
        self.project_name = project
        self.codebase_path = codebase
        self.state_path = state_root
        self.session_id = f"session_{now.strftime('%Y%m%d_%H%M%S_%f')}"
        self.llm = llm or HelloAgentsLLM()
        self.memory_tool = MemoryTool(
            user_id=project,
            config=MemoryConfig(
                storage_path=str(state_root / "memory"),
            ),
        )
        self.note_tool = NoteTool(workspace=str(state_root / "notes"))
        self.terminal_tool = TerminalTool(
            workspace=str(codebase),
            timeout=terminal_timeout,
        )
        self.context_builder = ContextBuilder(
            memory_tool=self.memory_tool,
            rag_tool=None,
            config=context_config
            or ContextConfig(
                max_tokens=4000,
                reserve_ratio=0.15,
                min_relevance=0.2,
                enable_compression=True,
            ),
        )
        self.conversation_history: List[Message] = []
        self.max_history_messages = int(max_history_messages)
        self.verbose = bool(verbose)
        self.stats: Dict[str, Any] = {
            "session_start": now,
            "commands_executed": 0,
            "notes_created": 0,
            "issues_found": 0,
        }
        self._closed = False

        self._log(f"✅ 代码库维护助手已初始化：{project}")
        self._log(f"📁 工作目录：{codebase}")
        self._log(f"🆔 会话 ID：{self.session_id}")

    def run(
        self,
        user_input: str,
        mode: str = "auto",
        **llm_kwargs: Any,
    ) -> str:
        """Run the chapter's six-stage maintenance loop."""
        self._ensure_open()
        query = user_input.strip()
        if not query:
            raise ValueError("user_input 不能为空")
        requested_mode = mode.lower().strip()
        if requested_mode not in MAINTAINER_MODES:
            choices = "、".join(sorted(MAINTAINER_MODES))
            raise ValueError(f"不支持 mode={mode!r}，可选值：{choices}")
        effective_mode = self._resolve_mode(query, requested_mode)

        self._log(f"\n👤 用户：{query}")
        if requested_mode == "auto":
            self._log(f"🧭 规则路由：auto → {effective_mode}")

        pre_context = self._preprocess_by_mode(query, effective_mode)
        relevant_notes = self._retrieve_relevant_notes(query)
        note_packets = self._notes_to_packets(relevant_notes)
        context = self.context_builder.build(
            user_query=query,
            conversation_history=self.conversation_history,
            system_instructions=self._build_system_instructions(
                effective_mode,
            ),
            custom_packets=[*note_packets, *pre_context],
        )

        self._log("🤖 正在思考...")
        response = self.llm.invoke(
            [
                {"role": "system", "content": context},
                {"role": "user", "content": query},
            ],
            **llm_kwargs,
        )
        answer = str(response).strip()
        if not answer:
            raise RuntimeError("LLM 返回了空响应")

        self._postprocess_response(query, answer, effective_mode)
        self._update_history(query, answer)
        self._record_interaction(query, answer)
        self._log(f"🤖 助手：{answer}\n")
        return answer

    def _resolve_mode(self, user_input: str, mode: str) -> str:
        """Resolve auto with explicit keyword rules, not an AI claim."""
        if mode != "auto":
            return mode
        lowered = user_input.lower()
        if any(
            keyword in lowered
            for keyword in ("计划", "下一步", "优先级", "任务")
        ):
            return "plan"
        if any(
            keyword in lowered
            for keyword in (
                "分析",
                "检查",
                "质量",
                "问题",
                "错误",
                "bug",
                "todo",
                "fixme",
                "复杂度",
                "重构建议",
            )
        ):
            return "analyze"
        return "explore"

    def _preprocess_by_mode(
        self,
        user_input: str,
        mode: str,
    ) -> List[ContextPacket]:
        """Collect mode-specific terminal or task-state packets."""
        packets: List[ContextPacket] = []
        now = datetime.now().astimezone()

        if mode == "explore":
            self._log("🔍 探索代码库结构...")
            structure = self._run_terminal(
                "find . -name '*.py' -type f | sort | head -n 20",
            )
            packets.append(
                self._packet(
                    f"[代码库结构]\n{structure}",
                    now,
                    0.60,
                    "code_structure",
                    "terminal",
                ),
            )

        elif mode == "analyze":
            self._log("📊 分析代码质量...")
            python_files = self._run_terminal(
                "find . -name '*.py' -type f | sort | head -n 100",
            )
            line_count = self._count_source_lines(python_files)
            todos = self._run_terminal(
                "grep -Ern 'TODO|FIXME' --include='*.py' . | head -n 10",
            )
            inspected = self._inspect_requested_files(user_input)
            content = (
                f"[代码统计]\n{line_count}\n\n"
                f"[待办事项]\n{todos}"
            )
            if inspected:
                content += f"\n\n[指定文件]\n{inspected}"
            packets.append(
                self._packet(
                    content,
                    now,
                    0.70,
                    "code_analysis",
                    "terminal",
                ),
            )

        elif mode == "plan":
            self._log("📋 加载任务规划...")
            task_notes = self.note_tool.run(
                {
                    "action": "list",
                    "note_type": "task_state",
                    "limit": 3,
                },
            )
            if isinstance(task_notes, list) and task_notes:
                content = "\n".join(
                    f"- {note['title']}"
                    for note in task_notes
                )
                packets.append(
                    self._packet(
                        f"[当前任务]\n{content}",
                        now,
                        0.80,
                        "task_plan",
                        "notes",
                    ),
                )
        return packets

    def _count_source_lines(self, file_listing: str) -> str:
        """Count listed files without using the unsafe find -exec action."""
        paths = [
            line.strip()
            for line in file_listing.splitlines()
            if line.strip().startswith("./")
        ]
        if not paths:
            return "未找到可统计的 Python 文件。"

        selected: List[str] = []
        command_length = len("wc -l ")
        for path in paths:
            quoted = shlex.quote(path)
            if len(selected) >= 50 or command_length + len(quoted) + 1 > 7000:
                break
            selected.append(quoted)
            command_length += len(quoted) + 1
        output = self._run_terminal("wc -l " + " ".join(selected))
        if len(selected) < len(paths):
            output += f"\n仅统计前 {len(selected)} 个文件。"
        return output

    def _inspect_requested_files(self, user_input: str) -> str:
        """Preview explicitly named Python files in analyze mode."""
        candidates = []
        for match in re.findall(
            r"(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.py",
            user_input,
        ):
            if match not in candidates:
                candidates.append(match)
        previews = []
        for path in candidates[:3]:
            result = self._run_terminal(
                f"head -n 120 {shlex.quote(path)}",
            )
            previews.append(f"[{path}]\n{result}")
        return "\n\n".join(previews)

    def _retrieve_relevant_notes(
        self,
        query: str,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """Load blocker bodies, merge keyword matches, and deduplicate."""
        blockers = self.note_tool.run(
            {
                "action": "list",
                "note_type": "blocker",
                "limit": 2,
            },
        )
        search_results = self.note_tool.run(
            {
                "action": "search",
                "query": query,
                "limit": limit,
            },
        )

        hydrated: List[Dict[str, Any]] = []
        if isinstance(blockers, list):
            for metadata in blockers:
                note_id = metadata.get("note_id") or metadata.get("id")
                if not note_id:
                    continue
                note = self.note_tool.run(
                    {"action": "read", "note_id": note_id},
                )
                if isinstance(note, dict):
                    hydrated.append(
                        {
                            **note["metadata"],
                            "note_id": note_id,
                            "content": note["content"],
                        },
                    )

        merged: Dict[str, Dict[str, Any]] = {}
        candidates: Sequence[Dict[str, Any]] = [
            *hydrated,
            *(search_results if isinstance(search_results, list) else []),
        ]
        for note in candidates:
            note_id = str(note.get("note_id") or note.get("id") or "")
            if note_id:
                merged[note_id] = note
        return list(merged.values())[:limit]

    def _notes_to_packets(
        self,
        notes: Sequence[Dict[str, Any]],
    ) -> List[ContextPacket]:
        packets = []
        for note in notes:
            content_text = str(note.get("content", "")).strip()
            if not content_text:
                continue
            note_type = str(note.get("type", "general"))
            title = str(note.get("title", "Untitled"))
            content = (
                f"[笔记:{title}]\n"
                f"类型：{note_type}\n\n{content_text}"
            )
            packets.append(
                ContextPacket(
                    content=content,
                    timestamp=self._parse_timestamp(note.get("updated_at")),
                    token_count=0,
                    relevance_score=NOTE_RELEVANCE.get(note_type, 0.60),
                    metadata={
                        "type": "note",
                        "note_type": note_type,
                        "note_id": note.get("note_id") or note.get("id"),
                    },
                ),
            )
        return packets

    def _build_system_instructions(self, mode: str) -> str:
        base = f"""你是 {self.project_name} 项目的代码库维护助手。

你的核心能力：
1. 根据 TerminalTool 的即时结果理解代码库
2. 使用 NoteTool 追踪发现、阻塞和计划
3. 基于记忆与历史笔记提供连贯建议

当前会话 ID：{self.session_id}
"""
        mode_specific = {
            "explore": """
当前模式：探索代码库
- 说明主要目录、模块和入口
- 区分已看到的事实与仍需读取的内容
- 给出下一步应查看的文件
""",
            "analyze": """
当前模式：分析代码质量
- 根据统计、TODO、FIXME 和文件片段指出具体问题
- 不要声称检查过未提供的文件
- 给出可验证的修改与测试建议
""",
            "plan": """
当前模式：任务规划
- 优先处理 blocker，再结合 task_state 排序行动项
- 每项写清依赖、风险和验收条件
- 不要把尚未执行的计划描述成已完成
""",
        }
        return base + mode_specific[mode]

    def _postprocess_response(
        self,
        user_input: str,
        response: str,
        mode: str,
    ) -> None:
        lowered_response = response.lower()
        if any(
            keyword in lowered_response
            for keyword in ("问题", "bug", "错误", "阻塞")
        ):
            note_id = self.note_tool.run(
                {
                    "action": "create",
                    "title": f"发现问题：{user_input[:30]}",
                    "content": (
                        f"## 用户输入\n\n{user_input}\n\n"
                        f"## 问题分析\n\n{response[:500]}"
                    ),
                    "note_type": "blocker",
                    "tags": [
                        self.project_name,
                        "auto_detected",
                        self.session_id,
                    ],
                },
            )
            if self._is_note_id(note_id):
                self.stats["notes_created"] += 1
                self.stats["issues_found"] += 1
                self._log("📝 已自动创建问题笔记")
            else:
                self._log(f"[WARNING] 问题笔记写入失败：{note_id}")
        elif mode == "plan" or any(
            keyword in user_input.lower()
            for keyword in ("计划", "下一步", "任务", "todo")
        ):
            note_id = self.note_tool.run(
                {
                    "action": "create",
                    "title": f"任务规划：{user_input[:30]}",
                    "content": (
                        f"## 讨论\n\n{user_input}\n\n"
                        f"## 行动计划\n\n{response[:500]}"
                    ),
                    "note_type": "action",
                    "tags": [
                        self.project_name,
                        "planning",
                        self.session_id,
                    ],
                },
            )
            if self._is_note_id(note_id):
                self.stats["notes_created"] += 1
                self._log("📝 已自动创建行动计划笔记")
            else:
                self._log(f"[WARNING] 行动笔记写入失败：{note_id}")

    def _update_history(self, user_input: str, response: str) -> None:
        now = datetime.now().astimezone()
        self.conversation_history.extend(
            [
                Message(content=user_input, role="user", timestamp=now),
                Message(content=response, role="assistant", timestamp=now),
            ],
        )
        if len(self.conversation_history) > self.max_history_messages:
            self.conversation_history = self.conversation_history[
                -self.max_history_messages :
            ]

    def _record_interaction(self, user_input: str, response: str) -> None:
        try:
            result = self.memory_tool.auto_record_conversation(
                user_message=user_input,
                assistant_message=response,
                conversation_id=self.session_id,
                importance=0.60,
            )
            if str(result).startswith("错误："):
                self._log(f"[WARNING] 交互记忆写入失败：{result}")
        except Exception as error:
            self._log(f"[WARNING] 交互记忆写入失败：{error}")

    def explore(self, target: str = ".") -> str:
        return self.run(f"请探索 {target} 的代码结构", mode="explore")

    def analyze(self, focus: str = "") -> str:
        query = "请分析代码质量"
        if focus.strip():
            query += f"，重点关注 {focus.strip()}"
        return self.run(query, mode="analyze")

    def plan_next_steps(self) -> str:
        return self.run("根据当前进度，规划下一步任务", mode="plan")

    def execute_command(self, command: str) -> str:
        self._ensure_open()
        return self._run_terminal(command)

    def create_note(
        self,
        title: str,
        content: str,
        note_type: str = "general",
        tags: List[str] | None = None,
    ) -> str:
        self._ensure_open()
        result = self.note_tool.run(
            {
                "action": "create",
                "title": title,
                "content": content,
                "note_type": note_type,
                "tags": tags or [self.project_name],
            },
        )
        if self._is_note_id(result):
            self.stats["notes_created"] += 1
        return str(result)

    def get_stats(self) -> Dict[str, Any]:
        self._ensure_open()
        duration = (
            datetime.now().astimezone() - self.stats["session_start"]
        ).total_seconds()
        note_summary = self.note_tool.run({"action": "summary"})
        return {
            "session_info": {
                "session_id": self.session_id,
                "project": self.project_name,
                "duration_seconds": round(duration, 3),
            },
            "activity": {
                "commands_executed": self.stats["commands_executed"],
                "notes_created": self.stats["notes_created"],
                "issues_found": self.stats["issues_found"],
            },
            "notes": note_summary if isinstance(note_summary, dict) else {},
        }

    def generate_report(
        self,
        save_to_file: bool = True,
        output_path: str | None = None,
    ) -> Dict[str, Any]:
        report = self.get_stats()
        if not save_to_file:
            return report

        path = Path(
            output_path
            or self.state_path
            / "reports"
            / f"maintainer_report_{self.session_id}.json",
        ).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
            + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        report["report_file"] = str(path)
        self._log(f"📄 报告已保存：{path}")
        return report

    def close(self) -> None:
        if not self._closed:
            self.memory_tool.close()
            self._closed = True

    def __enter__(self) -> "CodebaseMaintainer":
        self._ensure_open()
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _run_terminal(self, command: str) -> str:
        result = self.terminal_tool.run({"command": command})
        self.stats["commands_executed"] += 1
        return result

    @staticmethod
    def _packet(
        content: str,
        timestamp: datetime,
        relevance_score: float,
        packet_type: str,
        source: str,
    ) -> ContextPacket:
        return ContextPacket(
            content=content,
            timestamp=timestamp,
            token_count=0,
            relevance_score=relevance_score,
            metadata={"type": packet_type, "source": source},
        )

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value))
        except (TypeError, ValueError):
            return datetime.now().astimezone()

    @staticmethod
    def _is_note_id(value: Any) -> bool:
        return isinstance(value, str) and value.startswith("note_")

    @staticmethod
    def _safe_project_name(project_name: str) -> str:
        selected = re.sub(r"[^\w.-]+", "_", project_name).strip("._")
        return selected or "project"

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("CodebaseMaintainer 已关闭")

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message)
