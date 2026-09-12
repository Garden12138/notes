"""Amap MCP assembly used by the travel-planning agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


REQUIRED_AMAP_TOOLS = (
    "amap_maps_text_search",
    "amap_maps_weather",
)


class MCPIntegrationError(RuntimeError):
    """Raised when the configured MCP server cannot provide required tools."""


@dataclass(frozen=True)
class AmapMCPConfig:
    """Configuration needed to launch the chapter's Amap MCP server."""

    api_key: str = field(repr=False)
    server_command: tuple[str, ...] = ("uvx", "amap-mcp-server")

    def __post_init__(self) -> None:
        normalized_key = self.api_key.strip()
        normalized_command = tuple(
            part.strip() for part in self.server_command if part.strip()
        )
        if not normalized_key:
            raise MCPIntegrationError("未配置 AMAP_MAPS_API_KEY")
        if not normalized_command:
            raise MCPIntegrationError("高德 MCP Server 启动命令不能为空")
        object.__setattr__(self, "api_key", normalized_key)
        object.__setattr__(self, "server_command", normalized_command)


@dataclass(frozen=True)
class AmapMCPRuntime:
    """One discovered MCP facade shared by the three retrieval agents."""

    tool: Any
    expanded_tool_names: tuple[str, ...]

    def has_tool(self, name: str) -> bool:
        return name in self.expanded_tool_names


def create_amap_mcp_runtime(
    config: AmapMCPConfig,
    mcp_tool_class: Any | None = None,
) -> AmapMCPRuntime:
    """Create one MCPTool, discover sub-tools and verify the required pair.

    ``mcp_tool_class`` is injectable so discovery and configuration can be
    checked offline without launching ``uvx`` or contacting Amap.
    """
    if mcp_tool_class is None:
        try:
            from hello_agents.tools import MCPTool
        except ImportError as exc:
            raise MCPIntegrationError(
                "未找到 hello_agents，请使用 README 中的 PYTHONPATH 启动方式",
            ) from exc
        mcp_tool_class = MCPTool

    try:
        tool = mcp_tool_class(
            name="amap",
            description="高德地图 MCP 服务",
            server_command=list(config.server_command),
            env={"AMAP_MAPS_API_KEY": config.api_key},
            auto_expand=True,
        )
        expanded_tools = tool.get_expanded_tools()
    except Exception as exc:
        raise MCPIntegrationError(f"高德 MCP 工具初始化失败：{exc}") from exc

    names = tuple(
        name
        for expanded_tool in expanded_tools
        if (name := str(getattr(expanded_tool, "name", "")).strip())
    )
    missing = [name for name in REQUIRED_AMAP_TOOLS if name not in names]
    if missing:
        missing_text = "、".join(missing)
        discovered_text = "、".join(names) or "无"
        raise MCPIntegrationError(
            f"高德 MCP Server 缺少必要工具：{missing_text}；"
            f"实际发现：{discovered_text}",
        )

    return AmapMCPRuntime(tool=tool, expanded_tool_names=names)


__all__ = [
    "AmapMCPConfig",
    "AmapMCPRuntime",
    "MCPIntegrationError",
    "REQUIRED_AMAP_TOOLS",
    "create_amap_mcp_runtime",
]
