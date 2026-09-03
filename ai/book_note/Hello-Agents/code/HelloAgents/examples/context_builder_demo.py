"""Offline practice for chapter 9.3's ContextBuilder and Agent integration."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from hello_agents import (
    ContextBuilder,
    ContextConfig,
    ContextPacket,
    MemoryConfig,
    MemoryTool,
    Message,
    RAGTool,
    SimpleAgent,
)


class DemoLLM:
    """Deterministic substitute that verifies the assembled prompt."""

    provider = "mock"

    def invoke(
        self,
        messages: list[dict[str, str]],
        **_: Any,
    ) -> str:
        context = messages[0]["content"]
        required = ("[Role & Policies]", "[Task]", "[Output]")
        if not all(section in context for section in required):
            raise RuntimeError("ContextBuilder 未生成完整的固定骨架")
        return (
            "可以先将低基数字符串列转换为 category，"
            "再通过 downcast 缩小数值列类型；大文件使用 chunksize 分块读取。"
        )


class ContextAwareAgent(SimpleAgent):
    """SimpleAgent variant following the integration shown in section 9.3."""

    def __init__(
        self,
        name: str,
        llm: Any,
        context_builder: ContextBuilder,
        memory_tool: MemoryTool,
        system_prompt: str = "",
    ) -> None:
        super().__init__(
            name=name,
            llm=llm,
            system_prompt=system_prompt,
            enable_tool_calling=False,
        )
        self.context_builder = context_builder
        self.memory_tool = memory_tool

    def run(
        self,
        input_text: str,
        custom_packets: list[ContextPacket] | None = None,
        **kwargs: Any,
    ) -> str:
        """Build context, call the model, then update history and memory."""
        optimized_context = self.context_builder.build(
            user_query=input_text,
            conversation_history=self.get_history(),
            system_instructions=self.system_prompt,
            custom_packets=custom_packets,
        )
        response = self.llm.invoke(
            [
                {"role": "system", "content": optimized_context},
                {"role": "user", "content": input_text},
            ],
            **kwargs,
        )
        self.add_message(Message(content=input_text, role="user"))
        self.add_message(Message(content=response, role="assistant"))
        self.memory_tool.run(
            {
                "action": "add",
                "content": f"Q: {input_text}\nA: {response[:200]}",
                "memory_type": "episodic",
                "importance": 0.6,
            },
        )
        return response


def main() -> None:
    """Build a Pandas context and complete one deterministic Agent turn."""
    with TemporaryDirectory(prefix="hello_agents_context_") as temporary:
        root = Path(temporary)
        memory_tool = MemoryTool(
            user_id="garden",
            config=MemoryConfig(storage_path=str(root / "memory")),
        )
        rag_tool = RAGTool(
            knowledge_base_path=str(root / "knowledge_base"),
        )

        memory_tool.run(
            {
                "action": "add",
                "content": "用户正在使用 Python 和 Pandas 开发数据分析工具。",
                "memory_type": "semantic",
                "importance": 0.9,
            },
        )
        rag_tool.add_text(
            (
                "如何优化 Pandas 的内存占用？可以使用 category 类型、"
                "数值 downcast、"
                "chunksize 分块读取，并及时删除不再使用的中间 DataFrame。"
            ),
            document_id="pandas-memory-guide",
            source_name="Pandas 内存优化指南",
        )

        builder = ContextBuilder(
            memory_tool=memory_tool,
            rag_tool=rag_tool,
            config=ContextConfig(
                max_tokens=500,
                reserve_ratio=0.2,
                min_relevance=0.1,
                enable_compression=True,
            ),
        )
        history = [
            Message(
                content="我已经完成 CSV 读取模块。",
                role="user",
                timestamp=datetime.now(),
            ),
            Message(
                content="接下来可以处理数据类型和大文件读取。",
                role="assistant",
                timestamp=datetime.now(),
            ),
        ]
        state = ContextPacket(
            content="当前状态：CSV 读取已完成，尚未处理内存优化。",
            timestamp=datetime.now(),
            token_count=0,
            relevance_score=0.9,
            metadata={"type": "task_state"},
        )

        context = builder.build(
            user_query="如何优化 Pandas 的内存占用？",
            conversation_history=history,
            system_instructions=(
                "你是一位资深 Python 数据工程顾问，请给出可执行建议。"
            ),
            custom_packets=[state],
        )
        print("构建的上下文：")
        print(context)

        agent = ContextAwareAgent(
            name="数据分析顾问",
            llm=DemoLLM(),
            context_builder=builder,
            memory_tool=memory_tool,
            system_prompt="你是一位资深 Python 数据工程顾问。",
        )
        for message in history:
            agent.add_message(message)
        print("\nAgent 回答：")
        print(agent.run("如何优化 Pandas 的内存占用？", [state]))

        rag_tool.close()
        memory_tool.close()


if __name__ == "__main__":
    main()
