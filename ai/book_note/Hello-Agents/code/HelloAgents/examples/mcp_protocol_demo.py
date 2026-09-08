"""Deterministic MCP practice for chapter 10.2."""

from __future__ import annotations

import asyncio
from typing import Any

from hello_agents import MCPClient, SimpleAgent, create_builtin_server
from hello_agents.tools import MCPTool, ToolRegistry


class DeterministicLLM:
    """Drive one tool call without a paid model API."""

    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, messages: list[dict[str, str]], **_: Any) -> str:
        self.calls += 1
        if self.calls == 1:
            return "[TOOL_CALL:calculator_multiply:a=25,b=16]"
        if "400.0" not in messages[-1]["content"]:
            raise AssertionError("模型未收到 MCP 工具结果")
        return "25 × 16 = 400。"


async def inspect_protocol(server: Any) -> None:
    """Exercise Tools, Resources and Prompts through the async client."""
    client = MCPClient(server)
    print("=== MCPClient：发现与调用 ===")
    async with client:
        tools = await client.list_tools()
        print("Transport:", client.get_transport_info()["transport_type"])
        print("Tools:", ", ".join(tool["name"] for tool in tools))
        result = await client.call_tool(
            "multiply",
            {"a": 25, "b": 16},
        )
        print("multiply(25, 16):", result)

        resources = await client.list_resources()
        resource_uri = resources[0]["uri"]
        print("Resource:", await client.read_resource(resource_uri))

        prompts = await client.list_prompts()
        prompt = await client.get_prompt(
            prompts[0]["name"],
            {"topic": "MCP"},
        )
        print("Prompt:", prompt[0]["content"])


def inspect_agent_integration(server: Any) -> None:
    """Expand remote tools and let SimpleAgent consume one result."""
    print("\n=== MCPTool：自动展开与 Agent 集成 ===")
    mcp_tool = MCPTool(name="calculator", server=server)
    registry = ToolRegistry()
    registry.register_tool(mcp_tool)
    print("Expanded tools:", ", ".join(registry.list_tools()))

    agent = SimpleAgent(
        name="calculator-agent",
        llm=DeterministicLLM(),  # type: ignore[arg-type]
        system_prompt="必要时调用工具完成计算。",
        tool_registry=registry,
    )
    print("Agent:", agent.run("计算 25 乘以 16。"))


def main() -> None:
    """Run the complete example without FastMCP or an external service."""
    server = create_builtin_server(prefer_fastmcp=False)
    asyncio.run(inspect_protocol(server))
    inspect_agent_integration(server)


if __name__ == "__main__":
    main()
