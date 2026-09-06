"""Offline practice for chapter 9.5's just-in-time filesystem access."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from hello_agents import (
    ContextBuilder,
    ContextConfig,
    ContextPacket,
    NoteTool,
    TerminalTool,
    ToolRegistry,
)


class DemoLLM:
    """Deterministic substitute that verifies terminal output is visible."""

    provider = "mock"

    def invoke(
        self,
        messages: list[dict[str, str]],
        **_: Any,
    ) -> str:
        context = messages[0]["content"]
        required = ("[Context]", "processor.py", "TODO", "[即时文件]")
        if not all(value in context for value in required):
            raise RuntimeError("TerminalTool 输出没有进入 ContextBuilder")
        return (
            "processor.py 中仍有缓存失效 TODO；先补充缓存更新测试，"
            "再实现失效逻辑，并把验证结果更新到 blocker 笔记。"
        )


def build_demo_project(root: Path) -> None:
    """Create a small disposable codebase for safe exploration."""
    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / "logs").mkdir()
    (root / "docs").mkdir()
    (root / "README.md").write_text(
        "# Data Pipeline\n\nA small refactoring project.\n",
        encoding="utf-8",
    )
    (root / "src" / "processor.py").write_text(
        """class Processor:
    def process(self, rows):
        # TODO: invalidate cache after updating rows
        return [row.strip() for row in rows]
""",
        encoding="utf-8",
    )
    (root / "tests" / "test_processor.py").write_text(
        """def test_process():
    assert True
""",
        encoding="utf-8",
    )
    (root / "logs" / "app.log").write_text(
        "\n".join(
            [
                "2026-09-06:ERROR:DatabaseConnectionError",
                "2026-09-06:INFO:RequestFinished",
                "2026-09-06:ERROR:TimeoutException",
                "2026-09-06:ERROR:DatabaseConnectionError",
            ],
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "docs" / "large.txt").write_text(
        "0123456789" * 40,
        encoding="utf-8",
    )


def main() -> None:
    """Exercise navigation, pipelines, limits, and context integration."""
    with TemporaryDirectory(prefix="hello_agents_terminal_") as temporary:
        root = Path(temporary) / "project"
        root.mkdir()
        build_demo_project(root)

        terminal = TerminalTool(
            workspace=str(root),
            timeout=5,
            max_output_size=160,
        )
        notes = NoteTool(workspace=str(Path(temporary) / "notes"))
        registry = ToolRegistry()
        registry.register_tool(terminal)
        registry.register_tool(notes)
        print("已注册工具：", registry.list_tools())

        python_files = terminal.run(
            {"command": "find . -name '*.py' -type f | sort"},
        )
        print("Python 文件：")
        print(python_files)

        todo_result = terminal.run(
            {"command": "grep -rn 'TODO' --include='*.py' ."},
        )
        print("TODO 搜索：")
        print(todo_result)

        print(terminal.run({"command": "cd src"}))
        print("当前目录：", terminal.run({"command": "pwd"}))
        print("文件预览：")
        print(terminal.run({"command": "head -n 4 processor.py"}))
        print(terminal.run({"command": "cd ~"}))

        print("错误类型统计：")
        print(
            terminal.run(
                {
                    "command": (
                        "grep ERROR logs/app.log | cut -d: -f3 | "
                        "sort | uniq -c"
                    ),
                },
            ),
        )

        note_id = notes.run(
            {
                "action": "create",
                "title": "processor.py 缓存失效待办",
                "content": f"## 即时检索结果\n\n```text\n{todo_result}\n```",
                "note_type": "blocker",
                "tags": ["processor", "cache"],
            },
        )
        note = notes.run({"action": "read", "note_id": note_id})
        print("已记录笔记：", note["metadata"]["title"])

        packet = ContextPacket(
            content=f"[即时文件]\n{todo_result}",
            timestamp=datetime.now().astimezone(),
            token_count=0,
            relevance_score=0.9,
            metadata={"type": "code_structure", "source": "terminal"},
        )
        context = ContextBuilder(
            config=ContextConfig(max_tokens=500),
        ).build(
            user_query="下一步应该怎样处理代码中的待办？",
            system_instructions="你是代码库维护助手。",
            custom_packets=[packet],
        )
        answer = DemoLLM().invoke(
            [
                {"role": "system", "content": context},
                {
                    "role": "user",
                    "content": "下一步应该怎样处理代码中的待办？",
                },
            ],
        )
        print("维护建议：", answer)

        print("越界访问：", terminal.run({"command": "cat /etc/passwd"}))
        print("非白名单：", terminal.run({"command": "rm -rf ."}))
        print(
            "控制符注入：",
            terminal.run({"command": "ls; cat /etc/passwd"}),
        )
        truncated = terminal.run({"command": "cat docs/large.txt"})
        print("大文件是否截断：", "输出被截断" in truncated)


if __name__ == "__main__":
    main()
