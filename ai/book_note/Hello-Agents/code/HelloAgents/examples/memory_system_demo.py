"""Offline practice for chapter 8.2's complete memory lifecycle."""

from __future__ import annotations

import re
from tempfile import TemporaryDirectory

from hello_agents import MemoryConfig, MemoryTool, ToolRegistry


def memory_id(result: str) -> str:
    """Extract the ID returned by ``MemoryTool`` for later CRUD calls."""
    match = re.search(r"ID：([0-9a-f-]+)$", result)
    if not match:
        raise RuntimeError(result)
    return match.group(1)


def main() -> None:
    with TemporaryDirectory(prefix="hello_agents_memory_") as storage_path:
        config = MemoryConfig(
            storage_path=storage_path,
            working_memory_capacity=3,
            working_memory_ttl_minutes=30,
        )
        tool = MemoryTool(
            user_id="garden",
            config=config,
            memory_types=["working", "episodic", "semantic", "perceptual"],
        )
        registry = ToolRegistry()
        registry.register_tool(tool)
        print("已注册工具：", registry.list_tools())

        semantic_id = memory_id(
            tool.run(
                "add",
                content=(
                    "用户是一名前端工程师，喜欢 Python 和 TypeScript。"
                ),
                memory_type="semantic",
                importance=0.9,
            ),
        )
        tool.run(
            {
                "action": "add",
                "content": "刚才决定先完成第八章记忆系统实践。",
                "memory_type": "working",
                "importance": 0.8,
            },
        )
        perceptual_id = memory_id(
            tool.run(
                "add",
                content="架构图展示 MemoryTool 到四类记忆的调用关系。",
                memory_type="perceptual",
                importance=0.7,
                file_path="memory_architecture.png",
            ),
        )
        print("写入后数量：", counts(tool))

        hits = tool.manager.retrieve_memories("Python TypeScript")
        print("检索结果：", [item.content for item in hits])

        print(
            tool.run(
                "update",
                memory_id=semantic_id,
                content=(
                    "用户是一名前端工程师，主要使用 Python 和 TypeScript。"
                ),
                importance=0.95,
            ),
        )
        print(
            tool.run(
                "consolidate",
                from_type="working",
                to_type="episodic",
                importance_threshold=0.7,
            ),
        )
        print(tool.run("remove", memory_id=perceptual_id))

        tool.run(
            "add",
            content="临时且不重要的候选信息。",
            memory_type="semantic",
            importance=0.05,
        )
        print(
            tool.run(
                "forget",
                memory_types=["semantic"],
                strategy="importance",
                threshold=0.1,
            ),
        )
        print("维护后数量：", counts(tool))
        tool.close()

        restarted = MemoryTool(
            user_id="garden",
            config=config,
            memory_types=["working", "episodic", "semantic", "perceptual"],
        )
        persistent = restarted.manager.retrieve_memories(
            "Python TypeScript",
            memory_types=["semantic"],
        )
        print("重启后召回：", [item.content for item in persistent])
        print(
            "重启后工作记忆：",
            restarted.manager.get_memory_stats()["working"]["count"],
        )

        other_user = MemoryTool(
            user_id="visitor",
            config=config,
            memory_types=["working", "episodic", "semantic", "perceptual"],
        )
        print(
            "其他用户召回：",
            len(
                other_user.manager.retrieve_memories(
                    "Python TypeScript",
                    memory_types=["semantic"],
                ),
            ),
        )
        other_user.close()
        print(restarted.run("clear_all"))
        restarted.close()


def counts(tool: MemoryTool) -> dict[str, int]:
    return {
        name: stats["count"]
        for name, stats in tool.manager.get_memory_stats().items()
    }


if __name__ == "__main__":
    main()
