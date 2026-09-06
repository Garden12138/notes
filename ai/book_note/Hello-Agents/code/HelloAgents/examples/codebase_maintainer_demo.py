"""Offline end-to-end practice for chapter 9.6's codebase maintainer."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from hello_agents import CodebaseMaintainer


class DemoLLM:
    """Return deterministic answers and verify each context layer."""

    provider = "mock"

    def invoke(
        self,
        messages: list[dict[str, str]],
        **_: Any,
    ) -> str:
        context = messages[0]["content"]
        query = messages[-1]["content"]
        if "探索" in query:
            self._require(context, "[代码库结构]", "app/models/user.py")
            return (
                "当前代码库按 models、services 和 tests 分层；"
                "建议先查看用户模型和订单服务，再核对相应测试。"
            )
        if "分析" in query:
            self._require(
                context,
                "[代码统计]",
                "[待办事项]",
                "TODO",
                "FIXME",
            )
            return (
                "发现代码问题：user.py 尚未落实邮箱唯一约束，"
                "order_service.py 仍有订单校验 FIXME。应先补失败测试，"
                "再分别修改模型约束和服务校验。"
            )
        if "规划" in query:
            self._require(context, "[当前任务]", "[笔记:", "blocker")
            return (
                "下一步任务：第一，补充邮箱重复和非法订单测试；"
                "第二，修改模型与服务；第三，运行测试并把通过"
                "结果记录为 conclusion。"
            )
        if "回顾" in query:
            self._require(context, "[笔记:", "记忆：", "邮箱唯一约束")
            return (
                "已恢复上一会话状态：当前 blocker 是邮箱唯一约束和"
                "订单校验，已有行动计划要求先补测试再修改实现。"
            )
        raise RuntimeError(f"未覆盖的演示问题：{query}")

    @staticmethod
    def _require(context: str, *values: str) -> None:
        missing = [value for value in values if value not in context]
        if missing:
            raise RuntimeError(f"上下文缺少：{missing}")


def build_flask_fixture(root: Path) -> None:
    """Create a disposable Flask-like project for the walkthrough."""
    for directory in (
        root / "app" / "models",
        root / "app" / "services",
        root / "tests",
    ):
        directory.mkdir(parents=True, exist_ok=True)

    (root / "app" / "__init__.py").write_text(
        "from flask import Flask\n\ndef create_app():\n    return Flask(__name__)\n",
        encoding="utf-8",
    )
    (root / "app" / "models" / "user.py").write_text(
        """class User:
    # TODO: add a unique constraint for email
    email = None
""",
        encoding="utf-8",
    )
    (root / "app" / "services" / "order_service.py").write_text(
        """def process_order(order):
    # FIXME: validate stock and order status before processing
    return order
""",
        encoding="utf-8",
    )
    (root / "tests" / "test_user.py").write_text(
        """def test_user_email():
    assert True
""",
        encoding="utf-8",
    )
    (root / "requirements.txt").write_text(
        "Flask==3.1.2\n",
        encoding="utf-8",
    )


def main() -> None:
    """Run exploration, analysis, planning, and cross-session recovery."""
    with TemporaryDirectory(prefix="hello_agents_maintainer_") as temporary:
        root = Path(temporary)
        codebase = root / "my_flask_app"
        state = root / "maintainer_state"
        codebase.mkdir()
        build_flask_fixture(codebase)

        print("=== 第一次会话 ===")
        maintainer = CodebaseMaintainer(
            project_name="my_flask_app",
            codebase_path=str(codebase),
            state_path=str(state),
            llm=DemoLLM(),
        )
        maintainer.create_note(
            title="第一阶段：模型与服务校验",
            content=(
                "目标是补齐用户邮箱唯一约束和订单处理前置校验。"
            ),
            note_type="task_state",
            tags=["refactoring", "phase1"],
        )

        print("探索结论：", maintainer.explore())
        print("分析结论：", maintainer.analyze("TODO 和 FIXME"))
        print("规划结论：", maintainer.plan_next_steps())

        stats = maintainer.get_stats()
        print("命令执行数：", stats["activity"]["commands_executed"])
        print("本会话创建笔记数：", stats["activity"]["notes_created"])
        print("发现问题数：", stats["activity"]["issues_found"])
        print("持久笔记总数：", stats["notes"]["total_notes"])
        report = maintainer.generate_report()
        print("报告文件：", Path(report["report_file"]).name)
        maintainer.close()

        print("\n=== 第二次会话 ===")
        resumed = CodebaseMaintainer(
            project_name="my_flask_app",
            codebase_path=str(codebase),
            state_path=str(state),
            llm=DemoLLM(),
        )
        print(
            "恢复结论：",
            resumed.run("请回顾上一会话发现的代码问题"),
        )
        resumed_stats = resumed.get_stats()
        print("恢复后笔记总数：", resumed_stats["notes"]["total_notes"])
        print(
            "恢复后情景记忆数：",
            resumed.memory_tool.manager.get_memory_stats()["episodic"][
                "count"
            ],
        )
        resumed.close()


if __name__ == "__main__":
    main()
