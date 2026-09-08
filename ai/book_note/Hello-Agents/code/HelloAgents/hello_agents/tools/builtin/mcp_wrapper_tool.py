"""Adapt one discovered MCP capability to a native HelloAgents Tool."""

from __future__ import annotations

from typing import Any, Dict, List, TYPE_CHECKING

from ..base import Tool, ToolParameter

if TYPE_CHECKING:
    from .protocol_tools import MCPTool


class MCPWrappedTool(Tool):
    """Proxy a single server tool through its parent ``MCPTool``."""

    def __init__(
        self,
        mcp_tool: "MCPTool",
        tool_info: Dict[str, Any],
        prefix: str = "",
    ) -> None:
        self.mcp_tool = mcp_tool
        self.tool_info = dict(tool_info)
        self.mcp_tool_name = str(tool_info.get("name", "")).strip()
        if not self.mcp_tool_name:
            raise ValueError("MCP 工具缺少名称")
        schema = tool_info.get("input_schema") or tool_info.get(
            "inputSchema",
            {},
        )
        self._parameters = self._parse_input_schema(schema)
        super().__init__(
            name=f"{prefix}{self.mcp_tool_name}",
            description=str(
                tool_info.get("description")
                or f"MCP 工具: {self.mcp_tool_name}",
            ),
        )

    @staticmethod
    def _parse_input_schema(
        input_schema: Dict[str, Any],
    ) -> List[ToolParameter]:
        """Convert top-level JSON Schema properties to ToolParameter objects."""
        if not isinstance(input_schema, dict):
            return []
        properties = input_schema.get("properties", {})
        required = set(input_schema.get("required", ()))
        if not isinstance(properties, dict):
            return []
        return [
            ToolParameter(
                name=name,
                type=str(info.get("type", "string")),
                description=str(info.get("description", "")),
                required=name in required,
                default=info.get("default"),
            )
            for name, info in properties.items()
            if isinstance(info, dict)
        ]

    def get_parameters(self) -> List[ToolParameter]:
        return list(self._parameters)

    def run(self, parameters: Dict[str, Any]) -> str:
        return self.mcp_tool.run(
            {
                "action": "call_tool",
                "tool_name": self.mcp_tool_name,
                "arguments": parameters,
            }
        )


__all__ = ["MCPWrappedTool"]
