"""Async MCP client supporting the transport forms used in chapter 10.2."""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .server import BuiltinMCPServer, FASTMCP_AVAILABLE

if FASTMCP_AVAILABLE:  # pragma: no branch - depends on optional package
    from fastmcp import Client, FastMCP
    from fastmcp.client.transports import (
        PythonStdioTransport,
        SSETransport,
        StdioTransport,
        StreamableHttpTransport,
    )
else:  # pragma: no cover - names are only used after dependency checks
    Client = None  # type: ignore[assignment]
    FastMCP = None  # type: ignore[assignment]
    PythonStdioTransport = None  # type: ignore[assignment]
    SSETransport = None  # type: ignore[assignment]
    StdioTransport = None  # type: ignore[assignment]
    StreamableHttpTransport = None  # type: ignore[assignment]


class MCPClient:
    """Connect to an MCP server and normalize Tools, Resources and Prompts.

    Supported source forms follow the chapter examples: an in-memory server,
    a Python script, a command list, an HTTP URL, or a transport dictionary.
    All protocol operations are asynchronous and require ``async with``.
    """

    def __init__(
        self,
        server_source: Any,
        server_args: Sequence[str] | None = None,
        transport_type: str | None = None,
        env: Dict[str, str] | None = None,
        **transport_kwargs: Any,
    ) -> None:
        self.server_source = server_source
        self.server_args = list(server_args or ())
        self.transport_type = (
            transport_type.strip().lower() if transport_type else None
        )
        self.env = dict(env or {})
        self.transport_kwargs = dict(transport_kwargs)
        self.transport_kind = self._infer_transport_kind(server_source)
        self._local_server = (
            server_source
            if isinstance(server_source, BuiltinMCPServer)
            else None
        )
        self._client: Any = None
        self._context_manager: Any = None
        self._connected = False

    def _infer_transport_kind(self, source: Any) -> str:
        if isinstance(source, BuiltinMCPServer):
            return "memory"
        if FASTMCP_AVAILABLE and isinstance(source, FastMCP):
            return "memory"
        if isinstance(source, dict):
            return str(source.get("transport", "config")).lower()
        if isinstance(source, (list, tuple)):
            return "stdio"
        if isinstance(source, str):
            if source.startswith(("http://", "https://")):
                return self.transport_type or "streamable_http"
            if source.endswith(".py"):
                return "stdio"
        return self.transport_type or "auto"

    @staticmethod
    def _require_fastmcp() -> None:
        if not FASTMCP_AVAILABLE:
            raise ImportError(
                "外部 MCP 连接需要 FastMCP 2.x："
                "pip install 'fastmcp>=2,<3'",
            )

    def _prepare_fastmcp_source(self) -> Any:
        self._require_fastmcp()
        source = self.server_source

        if isinstance(source, FastMCP):
            return source

        if isinstance(source, dict):
            if "mcpServers" in source:
                return source
            return self._transport_from_config(source)

        if isinstance(source, str) and source.startswith(
            ("http://", "https://"),
        ):
            if self.transport_type == "sse":
                return SSETransport(url=source, **self.transport_kwargs)
            if self.transport_type in {"http", "streamable_http"}:
                return StreamableHttpTransport(
                    url=source,
                    **self.transport_kwargs,
                )
            return source

        if isinstance(source, str) and source.endswith(".py"):
            return PythonStdioTransport(
                script_path=source,
                args=self.server_args,
                env=self.env or None,
                **self.transport_kwargs,
            )

        if isinstance(source, (list, tuple)) and source:
            command = [str(part) for part in source]
            return StdioTransport(
                command=command[0],
                args=command[1:] + self.server_args,
                env=self.env or None,
                **self.transport_kwargs,
            )

        return source

    def _transport_from_config(self, config: Dict[str, Any]) -> Any:
        transport = str(config.get("transport", "stdio")).lower()
        common = dict(self.transport_kwargs)

        if transport == "stdio":
            command = str(config.get("command", "python"))
            args = [str(value) for value in config.get("args", ())]
            env = config.get("env") or self.env or None
            cwd = config.get("cwd")
            if command in {"python", "python3"} and args and args[0].endswith(
                ".py",
            ):
                return PythonStdioTransport(
                    script_path=args[0],
                    args=args[1:] + self.server_args,
                    env=env,
                    cwd=cwd,
                    **common,
                )
            return StdioTransport(
                command=command,
                args=args + self.server_args,
                env=env,
                cwd=cwd,
                **common,
            )

        if transport == "sse":
            return SSETransport(
                url=config["url"],
                headers=config.get("headers"),
                auth=config.get("auth"),
                **common,
            )

        if transport in {"http", "streamable_http"}:
            return StreamableHttpTransport(
                url=config["url"],
                headers=config.get("headers"),
                auth=config.get("auth"),
                **common,
            )

        raise ValueError(f"不支持的 MCP 传输类型: {transport}")

    async def __aenter__(self) -> "MCPClient":
        if self._connected:
            raise RuntimeError("MCPClient 已经连接")
        if self._local_server is not None:
            self._connected = True
            return self

        source = self._prepare_fastmcp_source()
        self._client = Client(source)
        self._context_manager = self._client
        try:
            await self._context_manager.__aenter__()
        except Exception:
            self._client = None
            self._context_manager = None
            raise
        self._connected = True
        return self

    async def __aexit__(
        self,
        exc_type: Any,
        exc_value: Any,
        traceback: Any,
    ) -> None:
        try:
            if self._context_manager is not None:
                await self._context_manager.__aexit__(
                    exc_type,
                    exc_value,
                    traceback,
                )
        finally:
            self._client = None
            self._context_manager = None
            self._connected = False

    def _require_connection(self) -> None:
        if not self._connected:
            raise RuntimeError(
                "MCPClient 尚未连接，请使用 'async with client:'",
            )

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Discover tools and normalize their input schema key."""
        self._require_connection()
        if self._local_server is not None:
            return self._local_server.list_tools()
        result = await self._client.list_tools()
        tools = self._unwrap_sequence(result, "tools")
        normalized = []
        for tool in tools:
            schema = self._value(tool, "inputSchema", "input_schema") or {}
            normalized.append(
                {
                    "name": str(self._value(tool, "name") or ""),
                    "description": str(
                        self._value(tool, "description") or "",
                    ),
                    "input_schema": schema,
                    "inputSchema": schema,
                }
            )
        return normalized

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Any:
        """Call an MCP tool and unwrap structured or text content."""
        self._require_connection()
        if not isinstance(arguments, dict):
            raise TypeError("arguments 必须是字典")
        if self._local_server is not None:
            return self._local_server.call_tool(tool_name, arguments)

        result = await self._client.call_tool(tool_name, arguments)
        if bool(self._value(result, "isError", "is_error")):
            raise RuntimeError(self._content_text(result) or "MCP 工具调用失败")
        data = self._value(result, "data")
        if data is not None:
            return data
        structured = self._value(
            result,
            "structuredContent",
            "structured_content",
        )
        if structured is not None:
            return structured
        return self._content_value(result)

    async def list_resources(self) -> List[Dict[str, Any]]:
        """List static resources exposed by the server."""
        self._require_connection()
        if self._local_server is not None:
            return self._local_server.list_resources()
        result = await self._client.list_resources()
        resources = self._unwrap_sequence(result, "resources")
        return [
            {
                "uri": str(self._value(resource, "uri") or ""),
                "name": str(self._value(resource, "name") or ""),
                "description": str(
                    self._value(resource, "description") or "",
                ),
                "mime_type": self._value(
                    resource,
                    "mimeType",
                    "mime_type",
                ),
            }
            for resource in resources
        ]

    async def read_resource(self, uri: str) -> Any:
        """Read one resource and unwrap text or binary blocks."""
        self._require_connection()
        if self._local_server is not None:
            return self._local_server.read_resource(uri)
        result = await self._client.read_resource(uri)
        return self._content_value(result, sequence_keys=("contents",))

    async def list_prompts(self) -> List[Dict[str, Any]]:
        """List reusable prompt templates."""
        self._require_connection()
        if self._local_server is not None:
            return self._local_server.list_prompts()
        result = await self._client.list_prompts()
        prompts = self._unwrap_sequence(result, "prompts")
        return [
            {
                "name": str(self._value(prompt, "name") or ""),
                "description": str(
                    self._value(prompt, "description") or "",
                ),
                "arguments": self._value(prompt, "arguments") or [],
            }
            for prompt in prompts
        ]

    async def get_prompt(
        self,
        prompt_name: str,
        arguments: Dict[str, Any] | None = None,
    ) -> List[Dict[str, str]]:
        """Render a prompt and normalize it to role/content messages."""
        self._require_connection()
        if self._local_server is not None:
            return self._local_server.get_prompt(prompt_name, arguments)
        result = await self._client.get_prompt(prompt_name, arguments or {})
        messages = self._unwrap_sequence(result, "messages")
        normalized = []
        for message in messages:
            role = self._value(message, "role") or "user"
            if hasattr(role, "value"):
                role = role.value
            content = self._value(message, "content")
            normalized.append(
                {
                    "role": str(role),
                    "content": self._block_value(content),
                }
            )
        return normalized

    async def ping(self) -> bool:
        """Check whether the current server session responds."""
        self._require_connection()
        if self._local_server is not None:
            return True
        try:
            await self._client.ping()
            return True
        except Exception:
            return False

    def get_transport_info(self) -> Dict[str, Any]:
        """Describe the selected transport without exposing credentials."""
        return {
            "status": "connected" if self._connected else "not_connected",
            "transport_type": self.transport_kind,
        }

    @staticmethod
    def _value(value: Any, *keys: str) -> Any:
        for key in keys:
            if isinstance(value, dict) and key in value:
                return value[key]
            if hasattr(value, key):
                return getattr(value, key)
        return None

    @classmethod
    def _unwrap_sequence(cls, result: Any, key: str) -> List[Any]:
        if isinstance(result, (list, tuple)):
            return list(result)
        value = cls._value(result, key)
        if isinstance(value, (list, tuple)):
            return list(value)
        return []

    @classmethod
    def _block_value(cls, block: Any) -> str:
        if block is None:
            return ""
        if isinstance(block, str):
            return block
        if isinstance(block, bytes):
            return block.decode("utf-8", errors="replace")
        if isinstance(block, (list, tuple)):
            return "\n".join(cls._block_value(item) for item in block)
        for key in ("text", "data", "blob"):
            value = cls._value(block, key)
            if value is not None:
                if isinstance(value, bytes):
                    return value.decode("utf-8", errors="replace")
                return str(value)
        return str(block)

    @classmethod
    def _content_value(
        cls,
        result: Any,
        sequence_keys: tuple[str, ...] = ("content", "contents"),
    ) -> Any:
        blocks: Any = result if isinstance(result, (list, tuple)) else None
        if blocks is None:
            for key in sequence_keys:
                candidate = cls._value(result, key)
                if candidate is not None:
                    blocks = candidate
                    break
        if blocks is None:
            return result
        if not isinstance(blocks, (list, tuple)):
            return cls._block_value(blocks)
        values = [cls._block_value(block) for block in blocks]
        if len(values) == 1:
            return values[0]
        return values

    @classmethod
    def _content_text(cls, result: Any) -> str:
        value = cls._content_value(result)
        if isinstance(value, list):
            return "\n".join(str(item) for item in value)
        return str(value) if value is not None else ""


__all__ = ["MCPClient"]
