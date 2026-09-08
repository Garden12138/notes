"""Connect to ``mcp_example_server.py`` through the MCP stdio transport."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from hello_agents import MCPClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVER_FILE = Path(__file__).with_name("mcp_example_server.py")


async def main() -> None:
    """Start the child server, discover capabilities and consume each kind."""
    inherited_pythonpath = os.getenv("PYTHONPATH", "")
    pythonpath = os.pathsep.join(
        value
        for value in (str(PROJECT_ROOT), inherited_pythonpath)
        if value
    )
    client = MCPClient(
        str(SERVER_FILE),
        env={
            "PYTHONPATH": pythonpath,
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )

    async with client:
        tools = await client.list_tools()
        print("Transport:", client.get_transport_info()["transport_type"])
        print("Tools:", ", ".join(item["name"] for item in tools))
        print("add(4, 6):", await client.call_tool("add", {"a": 4, "b": 6}))
        print(
            "Resource:",
            await client.read_resource("guide://client-usage"),
        )
        prompt = await client.get_prompt(
            "explain_concept",
            {"topic": "MCP"},
        )
        print("Prompt:", prompt[0]["content"])


if __name__ == "__main__":
    asyncio.run(main())
