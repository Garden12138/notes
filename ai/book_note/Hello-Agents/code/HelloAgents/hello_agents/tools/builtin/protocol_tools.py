"""Unified Tool wrappers for the communication-protocol chapter."""

from __future__ import annotations

import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Awaitable, Callable, Dict, List

from ...protocols import (
    A2AClient,
    ANPDiscovery,
    MCPClient,
    ServiceInfo,
    create_builtin_server,
)
from ..base import Tool, ToolParameter


MCP_SERVER_ENV_MAP = {
    "server-github": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
    "server-slack": ["SLACK_BOT_TOKEN", "SLACK_TEAM_ID"],
    "server-gdrive": [
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_REFRESH_TOKEN",
    ],
    "server-google-drive": [
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_REFRESH_TOKEN",
    ],
    "server-postgres": ["POSTGRES_CONNECTION_STRING"],
    "server-filesystem": [],
    "server-sqlite": [],
}


def _run_async(factory: Callable[[], Awaitable[Any]]) -> Any:
    """Run an async MCP operation from normal or already-async code."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(factory())

    def run_in_thread() -> Any:
        return asyncio.run(factory())

    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(run_in_thread).result()


class MCPTool(Tool):
    """Expose MCP Tools, Resources and Prompts through HelloAgents Tool."""

    def __init__(
        self,
        name: str = "mcp",
        description: str | None = None,
        server_command: List[str] | None = None,
        server_args: List[str] | None = None,
        server: Any = None,
        auto_expand: bool = True,
        env: Dict[str, str] | None = None,
        env_keys: List[str] | None = None,
        transport_type: str | None = None,
        client: MCPClient | None = None,
    ) -> None:
        self.server_command = list(server_command) if server_command else None
        self.server_args = list(server_args or ())
        self.server = server
        self.transport_type = transport_type
        self.env = self._prepare_env(env, env_keys, self.server_command)
        self._provided_client = client
        self.auto_expand = auto_expand
        self.prefix = f"{name}_" if auto_expand else ""
        self._available_tools: List[Dict[str, Any]] = []
        self._discovery_error: str | None = None

        if self.server is None and self.server_command is None and client is None:
            self.server = create_builtin_server()
        self._discover_tools()

        if description is None:
            if self._available_tools:
                description = (
                    "MCP 能力服务器，提供 "
                    f"{len(self._available_tools)} 个工具"
                )
            else:
                description = (
                    "通过 MCP 发现工具、资源和提示词并执行调用"
                )
        super().__init__(
            name=name,
            description=description,
            expandable=auto_expand,
        )

    @staticmethod
    def _prepare_env(
        env: Dict[str, str] | None,
        env_keys: List[str] | None,
        server_command: List[str] | None,
    ) -> Dict[str, str]:
        """Resolve server variables with explicit values taking precedence."""
        resolved: Dict[str, str] = {}
        if server_command:
            server_name = next(
                (
                    part.rsplit("/", 1)[-1]
                    for part in server_command
                    if "server-" in part
                ),
                None,
            )
            for key in MCP_SERVER_ENV_MAP.get(server_name or "", ()):
                value = os.getenv(key)
                if value:
                    resolved[key] = value
        for key in env_keys or ():
            value = os.getenv(key)
            if value:
                resolved[key] = value
        if env:
            resolved.update(env)
        return resolved

    def _new_client(self) -> MCPClient:
        if self._provided_client is not None:
            return self._provided_client
        source = self.server if self.server is not None else self.server_command
        if source is None:
            raise RuntimeError("未配置 MCP Server")
        return MCPClient(
            source,
            server_args=self.server_args,
            transport_type=self.transport_type,
            env=self.env,
        )

    def _discover_tools(self) -> None:
        async def discover() -> List[Dict[str, Any]]:
            async with self._new_client() as client:
                return await client.list_tools()

        try:
            self._available_tools = _run_async(discover)
            self._discovery_error = None
        except Exception as exc:
            self._available_tools = []
            self._discovery_error = str(exc)

    def get_expanded_tools(self) -> List[Tool]:
        """Wrap every discovered server tool as an independent Tool."""
        if not self.auto_expand:
            return []
        from .mcp_wrapper_tool import MCPWrappedTool

        return [
            MCPWrappedTool(
                mcp_tool=self,
                tool_info=tool_info,
                prefix=self.prefix,
            )
            for tool_info in self._available_tools
        ]

    @staticmethod
    def _format_value(value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, (dict, list, tuple)):
            return json.dumps(value, ensure_ascii=False, indent=2)
        return str(value)

    def run(self, parameters: Dict[str, Any]) -> str:
        """Execute one synchronous facade operation against the MCP client."""
        action = str(parameters.get("action", "")).strip().lower()
        if not action and parameters.get("tool_name"):
            action = "call_tool"
        if not action:
            return "错误：必须指定 action 参数"

        async def execute() -> Any:
            async with self._new_client() as client:
                if action == "list_tools":
                    return await client.list_tools()
                if action == "call_tool":
                    tool_name = str(parameters.get("tool_name", "")).strip()
                    if not tool_name:
                        raise ValueError("call_tool 必须指定 tool_name")
                    arguments = parameters.get("arguments", {})
                    return await client.call_tool(tool_name, arguments)
                if action == "list_resources":
                    return await client.list_resources()
                if action == "read_resource":
                    uri = str(parameters.get("uri", "")).strip()
                    if not uri:
                        raise ValueError("read_resource 必须指定 uri")
                    return await client.read_resource(uri)
                if action == "list_prompts":
                    return await client.list_prompts()
                if action == "get_prompt":
                    prompt_name = str(
                        parameters.get("prompt_name", ""),
                    ).strip()
                    if not prompt_name:
                        raise ValueError("get_prompt 必须指定 prompt_name")
                    prompt_arguments = parameters.get(
                        "prompt_arguments",
                        {},
                    )
                    return await client.get_prompt(
                        prompt_name,
                        prompt_arguments,
                    )
                if action == "ping":
                    return await client.ping()
                raise ValueError(f"不支持的 MCP 操作 '{action}'")

        try:
            result = _run_async(execute)
            if action == "list_tools":
                if not result:
                    return "没有找到可用工具"
                lines = [f"找到 {len(result)} 个工具:"]
                lines.extend(
                    f"- {tool['name']}: {tool['description']}"
                    for tool in result
                )
                return "\n".join(lines)
            if action == "list_resources":
                if not result:
                    return "没有找到可用资源"
                return "\n".join(
                    [f"找到 {len(result)} 个资源:"]
                    + [
                        f"- {item['uri']}: {item['name']}"
                        for item in result
                    ]
                )
            if action == "list_prompts":
                if not result:
                    return "没有找到可用提示词"
                return "\n".join(
                    [f"找到 {len(result)} 个提示词:"]
                    + [
                        f"- {item['name']}: {item['description']}"
                        for item in result
                    ]
                )
            return self._format_value(result)
        except Exception as exc:
            return f"MCP 操作失败: {exc}"

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type="string",
                description=(
                    "操作类型：list_tools、call_tool、list_resources、"
                    "read_resource、list_prompts、get_prompt 或 ping"
                ),
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
            ToolParameter(
                name="uri",
                type="string",
                description="read_resource 要读取的资源 URI",
                required=False,
            ),
            ToolParameter(
                name="prompt_name",
                type="string",
                description="get_prompt 要渲染的提示词名称",
                required=False,
            ),
            ToolParameter(
                name="prompt_arguments",
                type="object",
                description="提示词模板参数",
                required=False,
            ),
        ]


class A2ATool(Tool):
    """Expose a peer Agent's card, messages and tasks as one Tool."""

    def __init__(
        self,
        agent_url: str | None = None,
        name: str = "a2a",
        description: str = "连接远程 Agent 并与其协作",
        client: A2AClient | None = None,
    ) -> None:
        super().__init__(name=name, description=description)
        if client is None:
            if not agent_url:
                raise ValueError("必须提供 agent_url 或 client")
            client = A2AClient(agent_url)
        self.client = client
        self.agent_url = self.client.agent_url

    def run(self, parameters: Dict[str, Any]) -> str:
        """Run one synchronous facade operation against the A2A client."""
        action = str(parameters.get("action", "")).strip().lower()
        if not action:
            action = "execute_skill" if parameters.get("skill_name") else (
                "send_message" if parameters.get("input") else "describe"
            )

        try:
            if action == "describe":
                return self.client.describe()
            if action == "get_agent_card":
                return json.dumps(
                    self.client.get_agent_card(),
                    ensure_ascii=False,
                    indent=2,
                )
            if action in {"send_message", "execute_skill"}:
                text = str(
                    parameters.get("input", parameters.get("text", "")),
                ).strip()
                if not text:
                    raise ValueError(f"{action} 必须提供 input")
                if action == "execute_skill":
                    skill_name = str(
                        parameters.get("skill_name", ""),
                    ).strip()
                    if not skill_name:
                        raise ValueError("execute_skill 必须提供 skill_name")
                    result = self.client.execute_skill(skill_name, text)
                else:
                    result = self.client.send_message(text)
                if result.get("status") == "failed":
                    return f"A2A 任务失败: {result.get('error', '未知错误')}"
                return str(result.get("result", result))
            if action == "get_task":
                task_id = str(parameters.get("task_id", "")).strip()
                if not task_id:
                    raise ValueError("get_task 必须提供 task_id")
                return json.dumps(
                    self.client.get_task(task_id),
                    ensure_ascii=False,
                    indent=2,
                )
            if action == "cancel_task":
                task_id = str(parameters.get("task_id", "")).strip()
                if not task_id:
                    raise ValueError("cancel_task 必须提供 task_id")
                return json.dumps(
                    self.client.cancel_task(task_id),
                    ensure_ascii=False,
                    indent=2,
                )
            raise ValueError(f"不支持的 A2A 操作 '{action}'")
        except Exception as exc:
            return f"A2A 操作失败: {exc}"

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type="string",
                description=(
                    "操作类型：describe、get_agent_card、send_message、"
                    "execute_skill、get_task 或 cancel_task"
                ),
                required=False,
            ),
            ToolParameter(
                name="skill_name",
                type="string",
                description="execute_skill 要调用的兼容层 skill 名称",
                required=False,
            ),
            ToolParameter(
                name="input",
                type="string",
                description="发送给远程 Agent 的任务内容",
                required=False,
            ),
            ToolParameter(
                name="task_id",
                type="string",
                description="get_task 或 cancel_task 使用的远程任务 ID",
                required=False,
            ),
        ]


class ANPTool(Tool):
    """Expose the chapter's service directory and routing metadata as a Tool."""

    def __init__(
        self,
        name: str = "anp",
        description: str = "注册、发现和选择 Agent 网络服务",
        discovery: ANPDiscovery | None = None,
    ) -> None:
        super().__init__(name=name, description=description)
        self.discovery = discovery or ANPDiscovery()

    @staticmethod
    def _capabilities(parameters: Dict[str, Any]) -> List[str]:
        capabilities = parameters.get("capabilities", ())
        if isinstance(capabilities, str):
            return [
                item.strip()
                for item in capabilities.split(",")
                if item.strip()
            ]
        if not isinstance(capabilities, (list, tuple, set)):
            raise TypeError("capabilities 必须是数组或逗号分隔字符串")
        return [str(item).strip() for item in capabilities if str(item).strip()]

    @staticmethod
    def _format(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, indent=2)

    def run(self, parameters: Dict[str, Any]) -> str:
        """Register, discover, select or update Agent services."""
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
                    capabilities=tuple(self._capabilities(parameters)),
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

            if action == "get_service":
                service_id = str(parameters.get("service_id", "")).strip()
                if not service_id:
                    raise ValueError("get_service 必须提供 service_id")
                service = self.discovery.get_service(service_id)
                if service is None:
                    return f"错误：服务不存在: {service_id}"
                return self._format(service.to_dict())

            if action == "update_metadata":
                service_id = str(parameters.get("service_id", "")).strip()
                if not service_id:
                    raise ValueError("update_metadata 必须提供 service_id")
                updates = parameters.get("metadata")
                if not isinstance(updates, dict):
                    raise ValueError("update_metadata 必须提供 metadata 对象")
                service = self.discovery.update_metadata(service_id, updates)
                return self._format(service.to_dict())

            if action in {"list_services", "discover_services"}:
                services = self.discovery.discover_services(
                    service_type=(
                        parameters.get("service_type")
                        if action == "discover_services"
                        else None
                    ),
                    filters=parameters.get("filters"),
                    required_capabilities=self._capabilities(parameters),
                )
                if not services:
                    return "没有找到服务"
                limit = parameters.get("limit")
                if limit is not None:
                    limit = int(limit)
                    if limit <= 0:
                        raise ValueError("limit 必须大于 0")
                    services = services[:limit]
                if action == "discover_services":
                    lines = [f"找到 {len(services)} 个服务:"]
                    lines.extend(
                        (
                            f"- {service.service_id} | "
                            f"{service.service_type} | {service.endpoint}"
                        )
                        for service in services
                    )
                    return "\n".join(lines)
                return self._format(
                    [service.to_dict() for service in services],
                )

            if action == "select_service":
                service_type = str(
                    parameters.get("service_type", ""),
                ).strip()
                if not service_type:
                    raise ValueError("select_service 必须提供 service_type")
                ascending = parameters.get("ascending", True)
                if isinstance(ascending, str):
                    ascending = ascending.strip().lower() in {
                        "true",
                        "1",
                        "yes",
                    }
                selected = self.discovery.select_service(
                    service_type,
                    filters=parameters.get("filters"),
                    required_capabilities=self._capabilities(parameters),
                    sort_by=str(parameters.get("sort_by", "load")),
                    ascending=bool(ascending),
                )
                if selected is None:
                    return "没有找到服务"
                return self._format(selected.to_dict())

            return f"错误：不支持的 ANP 操作 '{action}'"
        except (TypeError, ValueError) as exc:
            return f"ANP 操作失败: {exc}"

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type="string",
                description=(
                    "操作类型：register_service、unregister_service、"
                    "get_service、update_metadata、list_services、"
                    "discover_services 或 select_service"
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
                description="服务类型，也可用于发现和选择",
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
                description="服务能力列表或发现时的必要能力",
                required=False,
            ),
            ToolParameter(
                name="metadata",
                type="object",
                description="注册或更新服务时使用的元数据",
                required=False,
            ),
            ToolParameter(
                name="filters",
                type="object",
                description="发现服务时使用的元数据精确过滤条件",
                required=False,
            ),
            ToolParameter(
                name="sort_by",
                type="string",
                description="选择服务时排序的数值型 metadata 字段",
                required=False,
                default="load",
            ),
            ToolParameter(
                name="ascending",
                type="boolean",
                description="选择服务时是否按字段升序排列",
                required=False,
                default=True,
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="最多返回多少个服务",
                required=False,
            ),
        ]
