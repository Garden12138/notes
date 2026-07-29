"""Tool registration and execution used by SimpleAgent and ReActAgent."""

from __future__ import annotations

from typing import Any, Callable

from .base import Tool


class ToolRegistry:
    """Store Tool objects and lightweight string-to-string functions."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self._functions: dict[str, dict[str, Any]] = {}

    def register_tool(self, tool: Tool, auto_expand: bool = True) -> None:
        """Register a Tool, expanding it when the Tool provides sub-tools."""
        if auto_expand and tool.expandable:
            expanded_tools = tool.get_expanded_tools()
            if expanded_tools:
                for sub_tool in expanded_tools:
                    self._tools[sub_tool.name] = sub_tool
                return
        self._tools[tool.name] = tool

    def register_function(
        self,
        name: str,
        description: str,
        func: Callable[[str], str],
    ) -> None:
        """Register a simple function as a tool."""
        self._functions[name] = {
            "description": description,
            "func": func,
        }

    def unregister(self, name: str) -> bool:
        """Remove a Tool or function by name."""
        if name in self._tools:
            del self._tools[name]
            return True
        if name in self._functions:
            del self._functions[name]
            return True
        return False

    def unregister_tool(self, name: str) -> bool:
        """Compatibility alias used by the learning-branch Agent code."""
        return self.unregister(name)

    def get_tool(self, name: str) -> Tool | None:
        """Return a registered Tool object."""
        return self._tools.get(name)

    def get_function(self, name: str) -> Callable[[str], str] | None:
        """Return a registered lightweight function."""
        info = self._functions.get(name)
        return info["func"] if info else None

    def execute_tool(self, name: str, input_text: str) -> str:
        """Execute a registered Tool or function with text input."""
        try:
            if name in self._tools:
                return str(self._tools[name].run({"input": input_text}))
            if name in self._functions:
                return str(self._functions[name]["func"](input_text))
        except Exception as error:
            return f"错误：执行工具 '{name}' 时发生异常：{error}"
        return f"错误：未找到名为 '{name}' 的工具。"

    def get_tools_description(self) -> str:
        """Return the prompt-facing list of available tools."""
        descriptions = [
            f"- {tool.name}: {tool.description}"
            for tool in self._tools.values()
        ]
        descriptions.extend(
            f"- {name}: {info['description']}"
            for name, info in self._functions.items()
        )
        return "\n".join(descriptions) if descriptions else "暂无可用工具"

    def list_tools(self) -> list[str]:
        """Return names in registration order."""
        return [*self._tools, *self._functions]

    def get_all_tools(self) -> list[Tool]:
        """Return all Tool objects, excluding lightweight functions."""
        return list(self._tools.values())

    def clear(self) -> None:
        """Remove all registered capabilities."""
        self._tools.clear()
        self._functions.clear()


global_registry = ToolRegistry()
