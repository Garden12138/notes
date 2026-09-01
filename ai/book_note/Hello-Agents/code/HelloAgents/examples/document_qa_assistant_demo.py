"""Offline end-to-end practice for chapter 8.4's learning assistant."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List

from hello_agents import (
    MemoryConfig,
    MemoryTool,
    PDFLearningAssistant,
    RAGTool,
)


class DemoLLM:
    """Deterministic replacement for MQE, HyDE, and grounded generation."""

    def invoke(self, messages: List[Dict[str, Any]]) -> str:
        system = str(messages[0].get("content", ""))
        if "查询扩展" in system:
            return "注意力机制的作用\n自注意力为什么重要"
        if "答案性文档" in system:
            return "注意力机制根据相关性动态聚合上下文信息。"
        return (
            "注意力机制会计算词元之间的相关性，并按权重聚合上下文；"
            "多头注意力还能并行关注不同关系。[1][2]"
        )


def main() -> None:
    with TemporaryDirectory(prefix="hello_agents_document_qa_") as directory:
        root = Path(directory)
        document = root / "happy_llm_excerpt.md"
        document.write_text(
            """# Transformer 学习摘录

## 注意力机制

注意力机制计算查询与键的相关性，再使用得到的权重聚合值向量，使模型能够动态选择上下文信息。

## 多头注意力

多头注意力在多个表示子空间并行计算注意力，让不同头关注语法、位置或语义等不同关系。

## 学习建议

理解注意力时，应区分查询、键和值，并结合缩放点积公式观察张量形状。
""",
            encoding="utf-8",
        )

        config = MemoryConfig(storage_path=str(root / "memory"))
        memory_tool = MemoryTool(user_id="garden", config=config)
        rag_tool = RAGTool(
            knowledge_base_path=str(root / "knowledge_base"),
            database_path=str(root / "rag.db"),
            rag_namespace="pdf_garden",
            llm=DemoLLM(),
        )
        assistant = PDFLearningAssistant(
            user_id="garden",
            data_dir=root,
            memory_tool=memory_tool,
            rag_tool=rag_tool,
        )

        loaded = assistant.load_document(
            document,
            chunk_size=70,
            chunk_overlap=10,
        )
        print("加载结果：", loaded["success"], loaded.get("document"))

        answer = assistant.ask("注意力机制如何利用上下文？")
        print("问答结果：", answer.split("\n\n参考来源：", 1)[0])

        note_result = assistant.add_note(
            "查询决定关注目标，键用于匹配，值承载被聚合的信息。",
            concept="attention",
        )
        print("笔记写入：", not note_result.startswith("错误"))

        recalled = assistant.recall("注意力机制")
        print("学习回顾：", "找到" in recalled)
        print("学习统计：", assistant.get_stats())

        report = assistant.generate_report(save_to_file=True)
        print("报告指标：", report["learning_metrics"])
        print("报告已生成：", Path(report["report_file"]).is_file())
        assistant.close()

        restarted = PDFLearningAssistant(
            user_id="garden",
            data_dir=root,
            memory_tool=MemoryTool(user_id="garden", config=config),
            rag_tool=RAGTool(
                knowledge_base_path=str(root / "knowledge_base"),
                database_path=str(root / "rag.db"),
                rag_namespace="pdf_garden",
                llm=DemoLLM(),
            ),
        )
        print("跨会话回顾：", "找到" in restarted.recall("注意力机制"))
        restarted.close()


if __name__ == "__main__":
    main()
