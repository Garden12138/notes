"""Communication-protocol interfaces introduced in chapter 10."""

from .a2a import A2A_AVAILABLE, A2AClient, A2AServer, A2ASkillDefinition
from .anp import (
    ANPDiscovery,
    ANPNetwork,
    ServiceInfo,
    discover_service,
    register_service,
)
from .base import Protocol, ProtocolType
from .mcp import (
    BuiltinMCPServer,
    FASTMCP_AVAILABLE,
    MCPClient,
    MCPPromptDefinition,
    MCPResourceDefinition,
    MCPServer,
    MCPToolDefinition,
    create_builtin_server,
    create_context,
    create_error_response,
    create_success_response,
    parse_context,
)

__all__ = [
    "A2A_AVAILABLE",
    "A2AClient",
    "A2AServer",
    "A2ASkillDefinition",
    "ANPDiscovery",
    "ANPNetwork",
    "BuiltinMCPServer",
    "FASTMCP_AVAILABLE",
    "MCPClient",
    "MCPPromptDefinition",
    "MCPResourceDefinition",
    "MCPServer",
    "MCPToolDefinition",
    "Protocol",
    "ProtocolType",
    "ServiceInfo",
    "create_builtin_server",
    "create_context",
    "create_error_response",
    "create_success_response",
    "discover_service",
    "parse_context",
    "register_service",
]
