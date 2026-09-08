"""Small FastMCP stdio server used by the chapter 10.2 client examples."""

from __future__ import annotations

from hello_agents import MCPServer


server = MCPServer(
    name="HelloAgents-PracticeServer",
    description="第十章 MCP 客户端连接练习",
)


def add(a: float, b: float) -> float:
    """计算两个数的和。"""
    return a + b


def greet(name: str = "World") -> str:
    """向指定用户问好。"""
    return f"Hello, {name}!"


def guide() -> str:
    """返回客户端调用提示。"""
    return "先 list_tools 发现能力，再 call_tool 传入结构化参数。"


def explain(topic: str) -> str:
    """生成一个概念解释任务。"""
    return f"请用定义、一个例子和一条边界解释 {topic}。"


server.add_tool(add)
server.add_tool(greet)
server.add_resource(
    guide,
    uri="guide://client-usage",
    name="client_usage",
    description="MCP 客户端调用指南",
)
server.add_prompt(explain, name="explain_concept")


if __name__ == "__main__":
    server.run(transport="stdio")
