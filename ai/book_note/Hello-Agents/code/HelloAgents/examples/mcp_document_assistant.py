"""Two-Agent document assistant following chapter 10.2's MCP workflow."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from hello_agents import HelloAgentsLLM, SimpleAgent
from hello_agents.tools import MCPTool


def build_searcher(llm: HelloAgentsLLM) -> SimpleAgent:
    """Create the GitHub research Agent and expand server capabilities."""
    searcher = SimpleAgent(
        name="GitHub搜索专家",
        llm=llm,
        system_prompt=(
            "你负责搜索 GitHub 仓库。优先使用搜索工具，"
            "返回仓库名称、链接、简介和主要特点。"
        ),
    )
    searcher.add_tool(
        MCPTool(
            name="gh",
            description="搜索 GitHub 仓库",
            server_command=[
                "npx",
                "-y",
                "@modelcontextprotocol/server-github",
            ],
            env_keys=["GITHUB_PERSONAL_ACCESS_TOKEN"],
        )
    )
    return searcher


def build_writer(llm: HelloAgentsLLM) -> SimpleAgent:
    """Create the Agent that turns research material into Markdown."""
    return SimpleAgent(
        name="文档生成专家",
        llm=llm,
        system_prompt=(
            "你负责把调研结果整理为 Markdown 报告。"
            "报告包含标题、简介、项目列表和总结；"
            "只返回完整报告，不使用代码围栏。"
        ),
        enable_tool_calling=False,
    )


def main() -> None:
    """Research repositories, generate a report and save it through MCP."""
    load_dotenv()
    if not os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN"):
        raise RuntimeError("请先配置 GITHUB_PERSONAL_ACCESS_TOKEN")

    output_dir = Path("mcp_output").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    llm = HelloAgentsLLM()
    searcher = build_searcher(llm)
    writer = build_writer(llm)
    filesystem = MCPTool(
        name="fs",
        description="将报告写入指定输出目录",
        server_command=[
            "npx",
            "-y",
            "@modelcontextprotocol/server-filesystem",
            str(output_dir),
        ],
    )

    print("步骤 1/3：搜索 AI Agent 仓库")
    research = searcher.run(
        "搜索 5 个有代表性的 Python AI Agent 仓库。"
    )

    print("步骤 2/3：整理 Markdown 报告")
    report = writer.run(
        "请将以下搜索结果整理为《AI Agent 框架调研》：\n\n"
        f"{research}"
    )

    print("步骤 3/3：通过文件系统 MCP Server 保存")
    save_result = filesystem.run(
        {
            "action": "call_tool",
            "tool_name": "write_file",
            "arguments": {
                "path": str(output_dir / "report.md"),
                "content": report,
            },
        }
    )
    print(save_result)
    print(f"报告位置：{output_dir / 'report.md'}")


if __name__ == "__main__":
    main()
