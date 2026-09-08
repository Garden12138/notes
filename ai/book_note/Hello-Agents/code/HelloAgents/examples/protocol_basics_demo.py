"""Offline quick experience for chapter 10.1."""

from __future__ import annotations

from hello_agents.tools import A2ATool, ANPTool, MCPTool


def main() -> None:
    """Run the three protocol examples without external services."""
    print("=== MCP：统一发现与调用工具 ===")
    mcp_tool = MCPTool()
    print(mcp_tool.run({"action": "list_tools"}))
    result = mcp_tool.run(
        {
            "action": "call_tool",
            "tool_name": "add",
            "arguments": {"a": 10, "b": 20},
        }
    )
    print(f"MCP 计算结果: {result}")

    print("\n=== ANP：注册并发现服务 ===")
    anp_tool = ANPTool()
    print(
        anp_tool.run(
            {
                "action": "register_service",
                "service_id": "calculator",
                "service_type": "math",
                "endpoint": "http://localhost:8080",
                "capabilities": ["add", "subtract"],
                "metadata": {"region": "local"},
            }
        )
    )
    print(anp_tool.run({"action": "discover_services", "service_type": "math"}))

    print("\n=== A2A：配置对等 Agent 端点 ===")
    a2a_tool = A2ATool("http://localhost:5000")
    print(a2a_tool.run({"action": "describe"}))
    print("A2A 工具创建成功")


if __name__ == "__main__":
    main()
