#!/usr/bin/env python3
"""Use the custom weather MCP server from a HelloAgents Agent."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from hello_agents import HelloAgentsLLM, SimpleAgent
from hello_agents.tools import MCPTool


SERVER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVER_DIR.parent
SERVER_FILE = SERVER_DIR / "server.py"


def _server_env() -> dict[str, str]:
    inherited_pythonpath = os.getenv("PYTHONPATH", "")
    pythonpath = os.pathsep.join(
        item for item in (str(PROJECT_ROOT), inherited_pythonpath) if item
    )
    env = {
        "PYTHONPATH": pythonpath,
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    for key in ("WEATHER_MCP_TIMEOUT", "WEATHER_MCP_FIXTURE_FILE"):
        value = os.getenv(key)
        if value:
            env[key] = value
    return env


def create_weather_assistant() -> SimpleAgent:
    """Create an Agent and explicitly register discovered MCP child tools."""
    load_dotenv()
    assistant = SimpleAgent(
        name="天气助手",
        llm=HelloAgentsLLM(),
        system_prompt=(
            "你是天气助手。查询实时天气时必须调用 "
            "mcp_get_weather，并根据工具返回的数据回答；"
            "如果工具返回 error，应说明查询失败，不要编造天气。"
        ),
    )
    weather_tool = MCPTool(
        name="mcp",
        server_command=[sys.executable, str(SERVER_FILE)],
        env=_server_env(),
    )
    expanded_tools = weather_tool.get_expanded_tools()
    if not expanded_tools:
        raise RuntimeError(
            "未发现天气 MCP 工具，请检查 FastMCP、服务脚本和启动日志"
        )
    for tool in expanded_tools:
        assistant.add_tool(tool)
    return assistant


def main() -> None:
    parser = argparse.ArgumentParser(description="HelloAgents 天气助手")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="执行一次北京天气查询后退出",
    )
    args = parser.parse_args()
    assistant = create_weather_assistant()

    if args.demo:
        print(assistant.run("北京今天天气怎么样？"))
        return

    while True:
        user_input = input("\n你: ").strip()
        if user_input.lower() in {"quit", "q", "exit", "退出"}:
            break
        if user_input:
            print("助手:", assistant.run(user_input))


if __name__ == "__main__":
    main()
