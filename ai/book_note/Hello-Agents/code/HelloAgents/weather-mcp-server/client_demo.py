#!/usr/bin/env python3
"""Exercise the weather MCP server through a real stdio session."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

from hello_agents import MCPClient


SERVER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVER_DIR.parent
SERVER_FILE = SERVER_DIR / "server.py"
FIXTURE_FILE = SERVER_DIR / "fixtures" / "weather.json"


def _object(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
    raise TypeError(f"预期 MCP 工具返回 JSON 对象，实际为 {type(value).__name__}")


def _child_env(use_fixture: bool) -> Dict[str, str]:
    inherited_pythonpath = os.getenv("PYTHONPATH", "")
    pythonpath = os.pathsep.join(
        item for item in (str(PROJECT_ROOT), inherited_pythonpath) if item
    )
    env = {
        "PYTHONPATH": pythonpath,
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    if use_fixture:
        env["WEATHER_MCP_FIXTURE_FILE"] = str(FIXTURE_FILE)
    return env


async def run_demo(use_fixture: bool = True) -> None:
    client = MCPClient(
        [sys.executable, str(SERVER_FILE)],
        env=_child_env(use_fixture),
    )
    async with client:
        tools = await client.list_tools()
        print("Transport:", client.get_transport_info()["transport_type"])
        print("Tools:", ", ".join(tool["name"] for tool in tools))

        info = _object(await client.call_tool("get_server_info", {}))
        print(f"Server: {info['name']} v{info['version']}")

        cities = _object(await client.call_tool("list_supported_cities", {}))
        print(f"Supported cities: {cities['count']}")

        for city in ("北京", "深圳"):
            weather = _object(
                await client.call_tool("get_weather", {"city": city})
            )
            if "error" in weather:
                print(f"{city}: ERROR {weather['error']}")
                continue
            print(
                f"{city}: {weather['temperature']:.1f}°C, "
                f"{weather['condition']}, humidity={weather['humidity']}%"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="测试天气 MCP Server")
    parser.add_argument(
        "--live",
        action="store_true",
        help="访问 wttr.in；默认使用仓库内固定数据完成协议验收",
    )
    args = parser.parse_args()
    asyncio.run(run_demo(use_fixture=not args.live))


if __name__ == "__main__":
    main()
