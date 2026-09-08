"""Client facade for section 10.1's in-memory MCP quick experience."""

from __future__ import annotations

from typing import Any, Dict, List

from .server import BuiltinMCPServer


class MCPClient:
    """Discover and invoke capabilities from an in-process MCP demo server."""

    def __init__(self, server: BuiltinMCPServer) -> None:
        if not isinstance(server, BuiltinMCPServer):
            raise TypeError("10.1 的 MCPClient 仅接收 BuiltinMCPServer")
        self.server = server

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return the server's current tool catalog."""
        return self.server.list_tools()

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a discovered tool with structured arguments."""
        if not isinstance(arguments, dict):
            raise TypeError("arguments 必须是字典")
        return self.server.call_tool(tool_name, arguments)
