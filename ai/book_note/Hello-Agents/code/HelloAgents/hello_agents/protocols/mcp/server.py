"""FastMCP server wrapper and a dependency-free in-memory fallback."""

from __future__ import annotations

import platform
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

try:
    from fastmcp import FastMCP

    FASTMCP_AVAILABLE = True
except ImportError:  # pragma: no cover - depends on optional package
    FastMCP = None  # type: ignore[assignment]
    FASTMCP_AVAILABLE = False


Handler = Callable[..., Any]


@dataclass(frozen=True)
class MCPToolDefinition:
    """Serializable description of an executable MCP capability."""

    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass(frozen=True)
class MCPResourceDefinition:
    """Serializable description of a readable MCP resource."""

    uri: str
    name: str
    description: str
    mime_type: str = "text/plain"


@dataclass(frozen=True)
class MCPPromptDefinition:
    """Serializable description of a reusable MCP prompt."""

    name: str
    description: str
    arguments: tuple[Dict[str, Any], ...] = ()


class BuiltinMCPServer:
    """In-process MCP-shaped server for tests without optional dependencies.

    When FastMCP is installed, :func:`create_builtin_server` returns a real
    ``FastMCP`` server instead.  This class keeps the same discovery and call
    semantics so examples remain deterministic in a minimal environment.
    """

    def __init__(self, name: str = "HelloAgents-BuiltinServer") -> None:
        self.name = name
        self._tools: Dict[str, tuple[MCPToolDefinition, Handler]] = {}
        self._resources: Dict[
            str,
            tuple[MCPResourceDefinition, Handler],
        ] = {}
        self._prompts: Dict[str, tuple[MCPPromptDefinition, Handler]] = {}

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Handler,
    ) -> None:
        """Register a discoverable callable."""
        normalized = name.strip()
        if not normalized:
            raise ValueError("工具名称不能为空")
        if normalized in self._tools:
            raise ValueError(f"工具已存在: {normalized}")
        self._tools[normalized] = (
            MCPToolDefinition(
                name=normalized,
                description=description.strip(),
                input_schema=dict(input_schema),
            ),
            handler,
        )

    def register_resource(
        self,
        uri: str,
        name: str,
        description: str,
        handler: Handler,
        mime_type: str = "text/plain",
    ) -> None:
        """Register a lazily read resource."""
        normalized = uri.strip()
        if not normalized:
            raise ValueError("资源 URI 不能为空")
        if normalized in self._resources:
            raise ValueError(f"资源已存在: {normalized}")
        self._resources[normalized] = (
            MCPResourceDefinition(
                uri=normalized,
                name=name.strip() or normalized,
                description=description.strip(),
                mime_type=mime_type,
            ),
            handler,
        )

    def register_prompt(
        self,
        name: str,
        description: str,
        handler: Handler,
        arguments: List[Dict[str, Any]] | None = None,
    ) -> None:
        """Register a reusable prompt template."""
        normalized = name.strip()
        if not normalized:
            raise ValueError("提示词名称不能为空")
        if normalized in self._prompts:
            raise ValueError(f"提示词已存在: {normalized}")
        self._prompts[normalized] = (
            MCPPromptDefinition(
                name=normalized,
                description=description.strip(),
                arguments=tuple(arguments or ()),
            ),
            handler,
        )

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return tool metadata without exposing handlers."""
        return [
            {
                "name": definition.name,
                "description": definition.description,
                "input_schema": definition.input_schema,
                "inputSchema": definition.input_schema,
            }
            for definition, _ in self._tools.values()
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Invoke a registered tool."""
        if name not in self._tools:
            available = ", ".join(self._tools) or "无"
            raise ValueError(f"未知 MCP 工具: {name}；可用工具: {available}")
        _, handler = self._tools[name]
        try:
            return handler(**arguments)
        except TypeError as exc:
            raise ValueError(f"工具参数无效: {exc}") from exc

    def list_resources(self) -> List[Dict[str, Any]]:
        """Return resource descriptions."""
        return [
            {
                "uri": definition.uri,
                "name": definition.name,
                "description": definition.description,
                "mime_type": definition.mime_type,
            }
            for definition, _ in self._resources.values()
        ]

    def read_resource(self, uri: str) -> Any:
        """Read a resource on demand."""
        if uri not in self._resources:
            raise ValueError(f"未知 MCP 资源: {uri}")
        _, handler = self._resources[uri]
        return handler()

    def list_prompts(self) -> List[Dict[str, Any]]:
        """Return prompt descriptions."""
        return [
            {
                "name": definition.name,
                "description": definition.description,
                "arguments": list(definition.arguments),
            }
            for definition, _ in self._prompts.values()
        ]

    def get_prompt(
        self,
        name: str,
        arguments: Dict[str, Any] | None = None,
    ) -> List[Dict[str, str]]:
        """Render a prompt into the same role/content shape used by Agents."""
        if name not in self._prompts:
            raise ValueError(f"未知 MCP 提示词: {name}")
        _, handler = self._prompts[name]
        try:
            content = handler(**(arguments or {}))
        except TypeError as exc:
            raise ValueError(f"提示词参数无效: {exc}") from exc
        return [{"role": "user", "content": str(content)}]


class MCPServer:
    """Thin FastMCP server wrapper matching the chapter's public interface."""

    def __init__(self, name: str, description: str | None = None) -> None:
        if not FASTMCP_AVAILABLE:
            raise ImportError(
                "MCPServer 需要 FastMCP 2.x：pip install 'fastmcp>=2,<3'",
            )
        self.name = name
        self.description = description or f"{name} MCP Server"
        self.mcp = FastMCP(name=name, instructions=self.description)

    def add_tool(
        self,
        func: Handler,
        name: str | None = None,
        description: str | None = None,
    ) -> Handler:
        """Expose a Python callable as an MCP tool."""
        self.mcp.tool(name=name, description=description)(func)
        return func

    def add_resource(
        self,
        func: Handler,
        uri: str,
        name: str | None = None,
        description: str | None = None,
        mime_type: str | None = None,
    ) -> Handler:
        """Expose a lazily evaluated resource under a stable URI."""
        if not uri.strip():
            raise ValueError("资源 URI 不能为空")
        kwargs = {
            "name": name,
            "description": description,
            "mime_type": mime_type,
        }
        self.mcp.resource(
            uri,
            **{key: value for key, value in kwargs.items() if value is not None},
        )(func)
        return func

    def add_prompt(
        self,
        func: Handler,
        name: str | None = None,
        description: str | None = None,
    ) -> Handler:
        """Expose a callable as a reusable MCP prompt template."""
        self.mcp.prompt(name=name, description=description)(func)
        return func

    def run(self, transport: str = "stdio", **kwargs: Any) -> None:
        """Run the server with a FastMCP-supported transport."""
        self.mcp.run(transport=transport, **kwargs)

    def get_info(self) -> Dict[str, Any]:
        """Return non-secret server metadata."""
        return {
            "name": self.name,
            "description": self.description,
            "protocol": "MCP",
            "implementation": "FastMCP",
        }


def _number_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "a": {"type": "number", "description": "第一个数"},
            "b": {"type": "number", "description": "第二个数"},
        },
        "required": ["a", "b"],
    }


def _divide(a: float, b: float) -> float:
    denominator = float(b)
    if denominator == 0:
        raise ValueError("除数不能为零")
    return float(a) / denominator


def _system_info() -> Dict[str, str]:
    return {
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "server_name": "HelloAgents-BuiltinServer",
    }


def create_builtin_server(prefer_fastmcp: bool = True) -> Any:
    """Create the six-capability demo server used by ``MCPTool()``.

    A real FastMCP in-memory server is preferred.  The local fallback exists so
    the framework's deterministic examples can run before optional protocol
    dependencies are installed.
    """
    if prefer_fastmcp and FASTMCP_AVAILABLE:
        server = FastMCP(
            name="HelloAgents-BuiltinServer",
            instructions="HelloAgents 第十章 MCP 内存演示服务器",
        )

        @server.tool()
        def add(a: float, b: float) -> float:
            """计算两个数的和。"""
            return a + b

        @server.tool()
        def subtract(a: float, b: float) -> float:
            """计算两个数的差。"""
            return a - b

        @server.tool()
        def multiply(a: float, b: float) -> float:
            """计算两个数的积。"""
            return a * b

        @server.tool()
        def divide(a: float, b: float) -> float:
            """计算两个数的商。"""
            return _divide(a, b)

        @server.tool()
        def greet(name: str = "World") -> str:
            """生成友好问候。"""
            return f"Hello, {name}! 欢迎使用 HelloAgents MCP 工具！"

        @server.tool()
        def get_system_info() -> Dict[str, str]:
            """获取非敏感的运行环境信息。"""
            return _system_info()

        @server.resource("config://hello-agents")
        def framework_config() -> str:
            """提供演示框架的只读配置。"""
            return "name=HelloAgents\nprotocol=MCP\nmode=memory"

        @server.prompt()
        def explain_concept(topic: str) -> str:
            """生成概念解释任务模板。"""
            return f"请用一个定义和一个例子解释 {topic}。"

        return server

    server = BuiltinMCPServer()
    schema = _number_schema()
    server.register_tool(
        "add",
        "计算两个数的和",
        schema,
        lambda a, b: float(a) + float(b),
    )
    server.register_tool(
        "subtract",
        "计算两个数的差",
        schema,
        lambda a, b: float(a) - float(b),
    )
    server.register_tool(
        "multiply",
        "计算两个数的积",
        schema,
        lambda a, b: float(a) * float(b),
    )
    server.register_tool("divide", "计算两个数的商", schema, _divide)
    server.register_tool(
        "greet",
        "生成友好问候",
        {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "要问候的名字",
                    "default": "World",
                }
            },
        },
        lambda name="World": (
            f"Hello, {name}! 欢迎使用 HelloAgents MCP 工具！"
        ),
    )
    server.register_tool(
        "get_system_info",
        "获取非敏感的运行环境信息",
        {"type": "object", "properties": {}},
        _system_info,
    )
    server.register_resource(
        uri="config://hello-agents",
        name="framework_config",
        description="HelloAgents 演示配置",
        handler=lambda: "name=HelloAgents\nprotocol=MCP\nmode=memory",
    )
    server.register_prompt(
        name="explain_concept",
        description="生成概念解释任务模板",
        arguments=[
            {
                "name": "topic",
                "description": "需要解释的主题",
                "required": True,
            }
        ],
        handler=lambda topic: f"请用一个定义和一个例子解释 {topic}。",
    )
    return server


__all__ = [
    "BuiltinMCPServer",
    "FASTMCP_AVAILABLE",
    "MCPPromptDefinition",
    "MCPResourceDefinition",
    "MCPServer",
    "MCPToolDefinition",
    "create_builtin_server",
]
