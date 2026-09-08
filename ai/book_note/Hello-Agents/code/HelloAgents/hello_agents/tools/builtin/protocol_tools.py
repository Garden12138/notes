"""Unified Tool wrappers for the communication-protocol chapter."""

from __future__ import annotations

from typing import Any, Dict, List

from ...protocols import (
    A2AClient,
    ANPDiscovery,
    MCPClient,
    ServiceInfo,
    create_builtin_server,
)
from ..base import Tool, ToolParameter


class MCPTool(Tool):
    """Expose section 10.1's MCP discovery/call experience as a Tool."""

    def __init__(
        self,
        name: str = "mcp",
        description: str = "通过 MCP 发现并调用外部能力",
        server_command: List[str] | None = None,
        client: MCPClient | None = None,
    ) -> None:
        super().__init__(name=name, description=description)
        self.server_command = list(server_command) if server_command else None
        if client is not None:
            self._client = client
        elif self.server_command is None:
            self._client = MCPClient(create_builtin_server())
        else:
            self._client = None

    def run(self, parameters: Dict[str, Any]) -> str:
        """List or call tools exposed by the configured MCP endpoint."""
        action = str(parameters.get("action", "")).strip().lower()
        if not action and parameters.get("tool_name"):
            action = "call_tool"
        if not action:
            return "错误：必须指定 action 参数"
        if self._client is None:
            command = " ".join(self.server_command or [])
            return (
                "错误：10.1 仅实现内存快速体验；外部 MCP 传输将在 10.2 接入。"
                f" 当前命令: {command}"
            )

        try:
            if action == "list_tools":
                tools = self._client.list_tools()
                if not tools:
                    return "没有找到可用工具"
                lines = [f"找到 {len(tools)} 个工具:"]
                lines.extend(
                    f"- {tool['name']}: {tool['description']}" for tool in tools
                )
                return "\n".join(lines)

            if action == "call_tool":
                tool_name = str(parameters.get("tool_name", "")).strip()
                arguments = parameters.get("arguments", {})
                if not tool_name:
                    return "错误：call_tool 必须指定 tool_name"
                result = self._client.call_tool(tool_name, arguments)
                return str(result)

            return f"错误：不支持的 MCP 操作 '{action}'"
        except (TypeError, ValueError) as exc:
            return f"MCP 操作失败: {exc}"

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type="string",
                description="操作类型：list_tools 或 call_tool",
                required=True,
            ),
            ToolParameter(
                name="tool_name",
                type="string",
                description="call_tool 要调用的工具名称",
                required=False,
            ),
            ToolParameter(
                name="arguments",
                type="object",
                description="call_tool 的结构化参数",
                required=False,
            ),
        ]


class A2ATool(Tool):
    """Hold a validated peer endpoint behind the same Tool interface."""

    def __init__(
        self,
        agent_url: str,
        name: str = "a2a",
        description: str = "连接远程 Agent 并与其协作",
    ) -> None:
        super().__init__(name=name, description=description)
        self.client = A2AClient(agent_url)
        self.agent_url = self.client.agent_url

    def run(self, parameters: Dict[str, Any]) -> str:
        """Describe the endpoint; task exchange is implemented in section 10.3."""
        action = str(parameters.get("action", "describe")).strip().lower()
        if action == "describe":
            return self.client.describe()
        return (
            f"错误：10.1 只完成 A2A 端点配置，不执行 '{action}'；"
            "真实任务通信将在 10.3 接入。"
        )

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type="string",
                description="当前支持 describe；后续扩展任务通信",
                required=False,
                default="describe",
            )
        ]


class ANPTool(Tool):
    """Expose the chapter's conceptual service registry as a Tool."""

    def __init__(
        self,
        name: str = "anp",
        description: str = "注册和发现 Agent 网络服务",
        discovery: ANPDiscovery | None = None,
    ) -> None:
        super().__init__(name=name, description=description)
        self.discovery = discovery or ANPDiscovery()

    def run(self, parameters: Dict[str, Any]) -> str:
        """Register, unregister or discover services."""
        action = str(parameters.get("action", "")).strip().lower()
        if not action:
            return "错误：必须指定 action 参数"

        try:
            if action == "register_service":
                missing = [
                    field
                    for field in ("service_id", "service_type", "endpoint")
                    if not parameters.get(field)
                ]
                if missing:
                    return f"错误：缺少参数 {', '.join(missing)}"
                service = ServiceInfo(
                    service_id=str(parameters["service_id"]),
                    service_type=str(parameters["service_type"]),
                    endpoint=str(parameters["endpoint"]),
                    service_name=parameters.get("service_name"),
                    capabilities=tuple(parameters.get("capabilities", ())),
                    metadata=dict(parameters.get("metadata", {})),
                )
                self.discovery.register_service(service)
                return f"已注册服务: {service.service_id}"

            if action == "unregister_service":
                service_id = str(parameters.get("service_id", "")).strip()
                if not service_id:
                    return "错误：缺少参数 service_id"
                if self.discovery.unregister_service(service_id):
                    return f"已注销服务: {service_id}"
                return f"错误：服务不存在: {service_id}"

            if action == "discover_services":
                services = self.discovery.discover_services(
                    service_type=parameters.get("service_type"),
                    filters=parameters.get("filters"),
                )
                if not services:
                    return "没有找到服务"
                lines = [f"找到 {len(services)} 个服务:"]
                lines.extend(
                    (
                        f"- {service.service_id} | {service.service_type} | "
                        f"{service.endpoint}"
                    )
                    for service in services
                )
                return "\n".join(lines)

            return f"错误：不支持的 ANP 操作 '{action}'"
        except (TypeError, ValueError) as exc:
            return f"ANP 操作失败: {exc}"

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type="string",
                description=(
                    "操作类型：register_service、unregister_service 或 "
                    "discover_services"
                ),
                required=True,
            ),
            ToolParameter(
                name="service_id",
                type="string",
                description="稳定的服务标识",
                required=False,
            ),
            ToolParameter(
                name="service_type",
                type="string",
                description="服务类型，也可用于发现过滤",
                required=False,
            ),
            ToolParameter(
                name="endpoint",
                type="string",
                description="服务访问地址",
                required=False,
            ),
            ToolParameter(
                name="service_name",
                type="string",
                description="可读服务名称",
                required=False,
            ),
            ToolParameter(
                name="capabilities",
                type="array",
                description="服务能力列表",
                required=False,
            ),
            ToolParameter(
                name="metadata",
                type="object",
                description="服务元数据",
                required=False,
            ),
            ToolParameter(
                name="filters",
                type="object",
                description="发现服务时使用的元数据精确过滤条件",
                required=False,
            ),
        ]
