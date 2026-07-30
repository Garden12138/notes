"""Sequential composition for registered tools."""

from __future__ import annotations

from typing import Any

from .registry import ToolRegistry


class ToolChain:
    """Execute registered tools in a fixed sequence."""

    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description
        self.steps: list[dict[str, str]] = []

    def add_step(
        self,
        tool_name: str,
        input_template: str,
        output_key: str | None = None,
    ) -> None:
        """Add one step whose input can reference previous outputs."""
        self.steps.append(
            {
                "tool_name": tool_name,
                "input_template": input_template,
                "output_key": (
                    output_key or f"step_{len(self.steps)}_result"
                ),
            },
        )

    def execute(
        self,
        registry: ToolRegistry,
        initial_input: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Run the chain and return the final step's output."""
        if not self.steps:
            return f"错误：工具链 '{self.name}' 没有可执行步骤。"

        execution_context = dict(context or {})
        execution_context["input"] = initial_input

        for step in self.steps:
            try:
                tool_input = step["input_template"].format(
                    **execution_context,
                )
            except KeyError as error:
                missing_name = error.args[0]
                return (
                    "错误：工具链模板引用了不存在的变量 "
                    f"'{missing_name}'。"
                )
            except ValueError as error:
                return f"错误：工具链模板格式无效：{error}"

            result = registry.execute_tool(
                step["tool_name"],
                tool_input,
            )
            execution_context[step["output_key"]] = result

        last_key = self.steps[-1]["output_key"]
        return str(execution_context[last_key])


class ToolChainManager:
    """Register and execute named ToolChain objects."""

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry
        self.chains: dict[str, ToolChain] = {}

    def register_chain(self, chain: ToolChain) -> None:
        self.chains[chain.name] = chain

    def execute_chain(
        self,
        chain_name: str,
        input_data: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        chain = self.chains.get(chain_name)
        if chain is None:
            return f"错误：工具链 '{chain_name}' 不存在。"
        return chain.execute(self.registry, input_data, context)

    def list_chains(self) -> list[str]:
        return list(self.chains)


def create_research_chain() -> ToolChain:
    """Build the search-to-calculation example from the chapter."""
    chain = ToolChain(
        name="research_and_calculate",
        description="搜索信息并将结果交给计算工具",
    )
    chain.add_step(
        tool_name="search",
        input_template="{input}",
        output_key="search_result",
    )
    chain.add_step(
        tool_name="my_calculator",
        input_template="{search_result}",
        output_key="calculation_result",
    )
    return chain
