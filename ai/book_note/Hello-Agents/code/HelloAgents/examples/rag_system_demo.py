"""Offline practice for chapter 8.3's complete RAG pipeline."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from hello_agents import RAGTool, ToolRegistry


class DemoLLM:
    """Deterministic substitute for MQE, HyDE, and grounded generation."""

    def invoke(
        self,
        messages: list[dict[str, str]],
        **_: Any,
    ) -> str:
        system = messages[0]["content"]
        if "检索查询扩展助手" in system:
            return "1. Python 创建者\n2. Python 首次发布时间"
        if "可能的答案性文档" in system:
            return "Python 由 Guido van Rossum 创建，并于 1991 年首次发布。"
        return "Python 由 Guido van Rossum 创建，1991 年首次发布。[1][2]"


def main() -> None:
    with TemporaryDirectory(prefix="hello_agents_rag_") as temporary:
        root = Path(temporary)
        knowledge_base = root / "knowledge_base"
        guide = root / "python_guide.md"
        guide.write_text(
            """# Python 指南

## 起源

Python 由 Guido van Rossum 创建，并在 1991 年首次发布。

## 设计特点

Python 强调代码可读性，使用缩进组织代码块。
""",
            encoding="utf-8",
        )

        tool = RAGTool(
            knowledge_base_path=str(knowledge_base),
            rag_namespace="study",
            llm=DemoLLM(),
        )
        registry = ToolRegistry()
        registry.register_tool(tool)
        print("已注册工具：", registry.list_tools())

        print(
            tool.run(
                "add_document",
                file_path=str(guide),
                document_id="python_guide",
                chunk_size=24,
                chunk_overlap=5,
            ),
        )
        print(
            tool.run(
                {
                    "action": "add_text",
                    "text": (
                        "# RAG\n\nRAG 将外部知识检索结果注入提示词，"
                        "再由大语言模型生成答案。"
                    ),
                    "document_id": "rag_concept",
                },
            ),
        )

        basic = tool.search_results(
            "Python 发布时间",
            namespace="study",
            limit=2,
            min_score=0.01,
            enable_advanced_search=False,
        )
        print("基础检索：", headings(basic))

        advanced = tool.search_results(
            "Python 的作者和发布时间",
            namespace="study",
            limit=2,
            min_score=0.01,
            enable_advanced_search=True,
        )
        pipeline = tool._get_pipeline("study")["pipeline"]
        print("扩展查询数：", len(pipeline.last_expansions))
        print("高级检索：", headings(advanced))
        print(
            "问答：",
            tool.ask(
                "Python 是谁创建的，何时发布？",
                namespace="study",
                limit=2,
                min_score=0.01,
            ).split("\n\n参考来源：", maxsplit=1)[0],
        )

        tool.add_text(
            "# 私有项目\n\n这条资料只属于 private 命名空间。",
            namespace="private",
            document_id="private_note",
        )
        print("命名空间计数：", namespace_counts(tool))
        tool.close()

        restarted = RAGTool(
            knowledge_base_path=str(knowledge_base),
            rag_namespace="study",
            llm=DemoLLM(),
        )
        print(
            "重启后召回：",
            headings(
                restarted.search_results(
                    "Guido Python",
                    namespace="study",
                    limit=1,
                    min_score=0.01,
                    enable_advanced_search=False,
                ),
            ),
        )
        print(restarted.run("clear", namespace="study", confirm=True))
        print("清理后计数：", namespace_counts(restarted))
        restarted.run("clear", namespace="private", confirm=True)
        restarted.close()


def headings(results: list[dict[str, Any]]) -> list[str]:
    return [
        str(result.get("metadata", {}).get("heading_path"))
        for result in results
    ]


def namespace_counts(tool: RAGTool) -> dict[str, int]:
    return {
        namespace: tool._get_pipeline(namespace)["get_stats"]()[
            "chunks_count"
        ]
        for namespace in ("study", "private")
    }


if __name__ == "__main__":
    main()

