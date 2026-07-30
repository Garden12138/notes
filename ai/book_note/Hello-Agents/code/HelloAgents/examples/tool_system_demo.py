"""Offline practice for the chapter 7.5 tool system."""

from __future__ import annotations

import asyncio
import os
from unittest.mock import patch

from hello_agents import (
    AsyncToolExecutor,
    CalculatorTool,
    SearchTool,
    ToolChain,
    ToolChainManager,
    ToolRegistry,
    create_calculator_registry,
)


class FailingTavilyClient:
    """Fake primary backend used to demonstrate fallback."""

    def search(self, **kwargs):
        raise RuntimeError("模拟 Tavily 超时")


class FakeGoogleSearch:
    """Offline replacement for ``serpapi.GoogleSearch``."""

    def __init__(self, parameters):
        self.parameters = parameters

    def get_dict(self):
        query = self.parameters["q"]
        return {
            "organic_results": [
                {
                    "title": "HelloAgents 工具系统",
                    "snippet": f"离线结果，查询词：{query}",
                    "link": "https://example.com/hello-agents",
                },
            ],
        }


def show_schema_and_registry() -> None:
    registry = create_calculator_registry()
    calculator = CalculatorTool()
    registry.register_tool(calculator)

    schema = calculator.to_openai_schema()["function"]
    assert schema["name"] == "python_calculator"
    assert schema["parameters"]["required"] == ["input"]
    assert registry.execute_tool("my_calculator", "sqrt(16) + 2 * 3") == (
        "10.0"
    )
    assert registry.execute_tool(
        "my_calculator",
        "__import__('os').system('whoami')",
    ).startswith("计算失败")

    print(
        "Schema："
        f"{schema['name']}，必填参数 "
        f"{schema['parameters']['required']}",
    )
    print(
        "计算器：sqrt(16) + 2 * 3 = "
        f"{registry.execute_tool('my_calculator', 'sqrt(16) + 2 * 3')}",
    )
    print("危险表达式：已拒绝")


def show_search_fallback() -> None:
    search = SearchTool(
        backend="hybrid",
        tavily_client=FailingTavilyClient(),
        serpapi_factory=FakeGoogleSearch,
    )
    registry = ToolRegistry()
    registry.register_tool(search)
    result = registry.execute_tool("search", "HelloAgents 工具系统")
    assert result.startswith("SerpApi Google 搜索结果")
    assert "离线结果" in result
    print("混合搜索：Tavily 失败后切换到 SerpApi Fake 客户端")

    with patch.dict(os.environ, {}, clear=True):
        unconfigured = SearchTool().search("测试")
    assert "没有可用的搜索源" in unconfigured
    print("无密钥搜索：返回配置提示，未发起网络请求")


def show_tool_chain() -> None:
    registry = create_calculator_registry()
    registry.register_function(
        "normalize_expression",
        "移除输入中的计算指令",
        lambda text: text.removeprefix("请计算").strip(),
    )
    registry.register_function(
        "format_result",
        "把表达式与结果整理成一句话",
        lambda text: f"最终结果：{text}",
    )

    chain = ToolChain(
        name="calculate_and_format",
        description="规范表达式、计算并格式化结果",
    )
    chain.add_step(
        "normalize_expression",
        "{input}",
        "expression",
    )
    chain.add_step(
        "my_calculator",
        "{expression}",
        "calculation",
    )
    chain.add_step(
        "format_result",
        "{expression} = {calculation}",
        "answer",
    )

    manager = ToolChainManager(registry)
    manager.register_chain(chain)
    result = manager.execute_chain(
        "calculate_and_format",
        "请计算 sqrt(16) + 2 * 3",
    )
    assert result == "最终结果：sqrt(16) + 2 * 3 = 10.0"
    print(f"三步工具链：{result}")


async def show_parallel_execution() -> None:
    registry = ToolRegistry()
    registry.register_function("upper", "转为大写", str.upper)
    registry.register_function(
        "length",
        "统计文本长度",
        lambda text: str(len(text)),
    )

    with AsyncToolExecutor(registry, max_workers=2) as executor:
        results = await executor.execute_tools_parallel(
            [
                {"tool_name": "upper", "input_data": "agent"},
                {"tool_name": "length", "input_data": "HelloAgents"},
            ],
        )
    assert results == ["AGENT", "11"]
    print(f"并行执行：{results}")


def main() -> None:
    print("=== Tool、Schema 与注册表 ===")
    show_schema_and_registry()
    print("\n=== 多源搜索降级 ===")
    show_search_fallback()
    print("\n=== 工具链 ===")
    show_tool_chain()
    print("\n=== 异步执行器 ===")
    asyncio.run(show_parallel_execution())


if __name__ == "__main__":
    main()
