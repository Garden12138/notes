"""Offline practice for chapter 9.4's NoteTool and ContextBuilder integration."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from hello_agents import (
    ContextBuilder,
    ContextConfig,
    ContextPacket,
    Message,
    NoteTool,
    SimpleAgent,
    ToolRegistry,
)


NOTE_RELEVANCE = {
    "blocker": 0.95,
    "action": 0.85,
    "task_state": 0.80,
    "conclusion": 0.75,
    "reference": 0.70,
    "general": 0.65,
}


class DemoLLM:
    """Deterministic response generator; no model API is called."""

    provider = "mock"

    def invoke(
        self,
        messages: list[dict[str, str]],
        **_: Any,
    ) -> str:
        context = messages[0]["content"]
        if "依赖冲突" not in context or "[笔记:" not in context:
            raise RuntimeError("相关 blocker 笔记没有进入上下文")
        return (
            "先用 pipdeptree 定位冲突链，再在独立分支统一约束版本"
            "并更新锁文件；完成后运行单元测试和集成测试，确认依赖"
            "调整没有引入回归。"
        )


class ProjectAssistant(SimpleAgent):
    """Long-running project assistant following section 9.4.4."""

    def __init__(
        self,
        project_name: str,
        llm: Any,
        note_tool: NoteTool,
    ) -> None:
        super().__init__(
            name="项目助手",
            llm=llm,
            system_prompt="",
            enable_tool_calling=False,
        )
        self.project_name = project_name
        self.note_tool = note_tool
        self.context_builder = ContextBuilder(
            config=ContextConfig(max_tokens=1200),
        )

    def run(
        self,
        input_text: str,
        note_as_action: bool = False,
        **kwargs: Any,
    ) -> str:
        relevant_notes = self._retrieve_relevant_notes(input_text)
        note_packets = self._notes_to_packets(relevant_notes)
        context = self.context_builder.build(
            user_query=input_text,
            conversation_history=self.get_history(),
            system_instructions=self._build_system_instructions(),
            custom_packets=note_packets,
        )
        response = self.llm.invoke(
            [
                {"role": "system", "content": context},
                {"role": "user", "content": input_text},
            ],
            **kwargs,
        )
        if note_as_action:
            self._save_as_note(input_text, response)
        self.add_message(Message(content=input_text, role="user"))
        self.add_message(Message(content=response, role="assistant"))
        return response

    def _retrieve_relevant_notes(
        self,
        query: str,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """Hydrate blocker metadata, merge search hits, and remove duplicates."""
        blocker_metadata = self.note_tool.run(
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
        if not isinstance(blocker_metadata, list):
            blocker_metadata = []
        if not isinstance(search_results, list):
            search_results = []

        hydrated = []
        for metadata in blocker_metadata:
            note = self.note_tool.run(
                {"action": "read", "note_id": metadata["note_id"]},
            )
            if isinstance(note, dict):
                hydrated.append(
                    {
                        **note["metadata"],
                        "note_id": metadata["note_id"],
                        "content": note["content"],
                    },
                )

        merged: dict[str, dict[str, Any]] = {}
        for note in [*hydrated, *search_results]:
            note_id = str(note.get("note_id") or note.get("id") or "")
            if note_id:
                merged[note_id] = note
        return list(merged.values())[:limit]

    def _notes_to_packets(
        self,
        notes: list[dict[str, Any]],
    ) -> list[ContextPacket]:
        packets = []
        for note in notes:
            note_type = str(note.get("type", "general"))
            content = f"[笔记:{note['title']}]\n{note['content']}"
            packets.append(
                ContextPacket(
                    content=content,
                    timestamp=datetime.fromisoformat(note["updated_at"]),
                    token_count=0,
                    relevance_score=NOTE_RELEVANCE.get(note_type, 0.65),
                    metadata={
                        "type": "note",
                        "note_type": note_type,
                        "note_id": note["note_id"],
                    },
                ),
            )
        return packets

    def _save_as_note(self, user_input: str, response: str) -> str:
        if "问题" in user_input or "阻塞" in user_input:
            note_type = "blocker"
        elif "计划" in user_input or "下一步" in user_input:
            note_type = "action"
        else:
            note_type = "conclusion"
        return str(
            self.note_tool.run(
                {
                    "action": "create",
                    "title": user_input[:30],
                    "content": f"## 问题\n\n{user_input}\n\n## 分析\n\n{response}",
                    "note_type": note_type,
                    "tags": [self.project_name, "auto_generated"],
                },
            ),
        )

    def _build_system_instructions(self) -> str:
        return (
            f"你是 {self.project_name} 项目的长期助手。"
            "请优先处理 blocker，并根据历史笔记给出可执行建议。"
        )


def main() -> None:
    """Exercise all seven actions and one note-aware Agent turn."""
    with TemporaryDirectory(prefix="hello_agents_notes_") as temporary:
        workspace = Path(temporary) / "project_notes"
        notes = NoteTool(workspace=str(workspace))
        registry = ToolRegistry()
        registry.register_tool(notes)
        print("已注册工具：", registry.list_tools())

        progress_id = notes.run(
            {
                "action": "create",
                "title": "数据管道重构 - 第一阶段",
                "content": (
                    "## 完成情况\n\n"
                    "数据模型层重构完成，测试覆盖率达到 85%。"
                    "\n\n## 下一步\n\n重构业务逻辑层。"
                ),
                "note_type": "task_state",
                "tags": ["refactoring", "phase1"],
            },
        )
        blocker_id = notes.run(
            {
                "action": "create",
                "title": "业务逻辑层依赖冲突",
                "content": (
                    "第三方库版本不兼容，影响业务逻辑层的三个模块。"
                ),
                "note_type": "blocker",
                "tags": ["dependency", "urgent"],
            },
        )
        reference_id = notes.run(
            {
                "action": "create",
                "title": "重构参考资料",
                "content": "项目依赖约束记录在 requirements.txt。",
                "note_type": "reference",
                "tags": ["dependency"],
            },
        )
        print("创建笔记：", progress_id, blocker_id, reference_id)

        progress = notes.run({"action": "read", "note_id": progress_id})
        print("读取标题：", progress["metadata"]["title"])
        print(
            notes.run(
                {
                    "action": "update",
                    "note_id": progress_id,
                    "tags": ["refactoring", "phase1", "completed"],
                },
            ),
        )

        search_results = notes.run(
            {"action": "search", "query": "依赖冲突", "limit": 5},
        )
        blockers = notes.run(
            {"action": "list", "note_type": "blocker", "limit": 5},
        )
        print("搜索结果：", [item["title"] for item in search_results])
        print("Blocker 列表：", [item["title"] for item in blockers])
        print(
            "笔记摘要：",
            json.dumps(notes.run({"action": "summary"}), ensure_ascii=False),
        )
        print(notes.run({"action": "delete", "note_id": reference_id}))

        restarted = NoteTool(workspace=str(workspace))
        restarted_summary = restarted.run({"action": "summary"})
        print("重启后笔记数：", restarted_summary["total_notes"])

        assistant = ProjectAssistant(
            project_name="data_pipeline_refactoring",
            llm=DemoLLM(),
            note_tool=restarted,
        )
        answer = assistant.run(
            "业务逻辑层的依赖冲突问题怎么处理？",
            note_as_action=True,
        )
        print("项目助手回答：", answer)
        print(
            "交互后摘要：",
            json.dumps(
                restarted.run({"action": "summary"}),
                ensure_ascii=False,
            ),
        )


if __name__ == "__main__":
    main()
