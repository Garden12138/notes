"""Communication-protocol interfaces introduced in chapter 10."""

from .a2a import A2AClient
from .anp import ANPDiscovery, ServiceInfo
from .base import Protocol, ProtocolType
from .mcp import (
    BuiltinMCPServer,
    MCPClient,
    MCPToolDefinition,
    create_builtin_server,
    create_context,
    parse_context,
)

__all__ = [
    "A2AClient",
    "ANPDiscovery",
    "BuiltinMCPServer",
    "MCPClient",
    "MCPToolDefinition",
    "Protocol",
    "ProtocolType",
    "ServiceInfo",
    "create_builtin_server",
    "create_context",
    "parse_context",
]
