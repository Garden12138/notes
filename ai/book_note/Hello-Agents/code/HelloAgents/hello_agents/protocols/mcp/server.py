"""Small in-memory MCP-shaped server used by the section 10.1 demo.

This module implements discovery and invocation semantics for the chapter's
quick experience.  Network transports and full FastMCP integration belong to
the dedicated MCP section that follows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List


ToolHandler = Callable[..., Any]


@dataclass(frozen=True)
class MCPToolDefinition:
    """Describe one callable capability exposed by an MCP server."""

    name: str
    description: str
    input_schema: Dict[str, Any]


class BuiltinMCPServer:
    """In-process capability registry for the chapter's zero-config example."""

    def __init__(self, name: str = "HelloAgents-BuiltinServer") -> None:
        self.name = name
        self._tools: Dict[str, tuple[MCPToolDefinition, ToolHandler]] = {}

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: ToolHandler,
    ) -> None:
        """Register a discoverable callable and reject accidental duplicates."""
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("工具名称不能为空")
        if normalized_name in self._tools:
            raise ValueError(f"工具已存在: {normalized_name}")
        definition = MCPToolDefinition(
            name=normalized_name,
            description=description.strip(),
            input_schema=dict(input_schema),
        )
        self._tools[normalized_name] = (definition, handler)

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return serializable tool descriptions, excluding Python handlers."""
        return [
            {
                "name": definition.name,
                "description": definition.description,
                "input_schema": definition.input_schema,
            }
            for definition, _ in self._tools.values()
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Invoke one registered capability with structured arguments."""
        if name not in self._tools:
            available = ", ".join(self._tools) or "无"
            raise ValueError(f"未知 MCP 工具: {name}；可用工具: {available}")
        _, handler = self._tools[name]
        try:
            return handler(**arguments)
        except TypeError as exc:
            raise ValueError(f"工具参数无效: {exc}") from exc


def create_builtin_server() -> BuiltinMCPServer:
    """Create the arithmetic server used by ``MCPTool()``."""
    server = BuiltinMCPServer()
    number_schema = {
        "type": "object",
        "properties": {
            "a": {"type": "number"},
            "b": {"type": "number"},
        },
        "required": ["a", "b"],
    }
    server.register_tool(
        name="add",
        description="计算两个数的和",
        input_schema=number_schema,
        handler=lambda a, b: float(a) + float(b),
    )
    server.register_tool(
        name="subtract",
        description="计算两个数的差",
        input_schema=number_schema,
        handler=lambda a, b: float(a) - float(b),
    )
    server.register_tool(
        name="multiply",
        description="计算两个数的积",
        input_schema=number_schema,
        handler=lambda a, b: float(a) * float(b),
    )

    def divide(a: float, b: float) -> float:
        denominator = float(b)
        if denominator == 0:
            raise ValueError("除数不能为零")
        return float(a) / denominator

    server.register_tool(
        name="divide",
        description="计算两个数的商",
        input_schema=number_schema,
        handler=divide,
    )
    return server
