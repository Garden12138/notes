"""A2A server and client adapters used by chapter 10.3.

The public API follows the chapter's ``A2AServer.skill`` and
``A2AClient.execute_skill`` examples. Network communication is implemented
with the official ``a2a-sdk`` when installed; registered skills can also be
invoked locally so the collaboration flow remains testable without a service.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import re
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Iterable
from urllib.parse import urlparse


SkillHandler = Callable[[str], Any]

try:  # Optional dependency: local skill execution does not require the SDK.
    import httpx
    from google.protobuf.json_format import MessageToDict

    from a2a.client import ClientConfig, create_client
    from a2a.client.card_resolver import A2ACardResolver
    from a2a.helpers import (
        get_artifact_text,
        get_message_text,
        new_task_from_user_message,
        new_text_message,
        new_text_part,
    )
    from a2a.server.agent_execution import AgentExecutor, RequestContext
    from a2a.server.events import EventQueue
    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.routes import (
        create_agent_card_routes,
        create_jsonrpc_routes,
    )
    from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
    from a2a.types import (
        AgentCapabilities,
        AgentCard,
        AgentInterface,
        AgentSkill,
        CancelTaskRequest,
        GetTaskRequest,
        Role,
        SendMessageConfiguration,
        SendMessageRequest,
        StreamResponse,
        Task,
        TaskState,
    )

    A2A_AVAILABLE = True
except ImportError:  # pragma: no cover - dependency-free mode.
    A2A_AVAILABLE = False
    AgentExecutor = object  # type: ignore[assignment,misc]
    RequestContext = Any  # type: ignore[assignment,misc]
    EventQueue = Any  # type: ignore[assignment,misc]


def _run_async(factory: Callable[[], Awaitable[Any]]) -> Any:
    """Run a coroutine from synchronous code, including inside an event loop."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(factory())

    def run_in_thread() -> Any:
        return asyncio.run(factory())

    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(run_in_thread).result()


def _serialize_result(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _state_name(value: int) -> str:
    if not A2A_AVAILABLE:
        return str(value)
    name = TaskState.Name(value)
    return name.removeprefix("TASK_STATE_").lower().replace("_", "-")


@dataclass(frozen=True)
class A2ASkillDefinition:
    """Serializable metadata advertised in an Agent Card."""

    id: str
    name: str
    description: str
    tags: tuple[str, ...] = ()
    examples: tuple[str, ...] = ()
    input_modes: tuple[str, ...] = ("text/plain",)
    output_modes: tuple[str, ...] = ("text/plain",)


class A2AServer:
    """Register Agent skills and expose them through an A2A JSON-RPC server."""

    def __init__(
        self,
        name: str,
        description: str,
        version: str = "1.0.0",
        capabilities: Dict[str, Any] | None = None,
    ) -> None:
        self.name = name.strip()
        self.description = description.strip()
        self.version = version.strip()
        self.capabilities = dict(capabilities or {})
        if not self.name or not self.description or not self.version:
            raise ValueError("name、description 和 version 不能为空")
        self.skills: Dict[str, SkillHandler] = {}
        self._skill_definitions: Dict[str, A2ASkillDefinition] = {}

    def skill(
        self,
        name: str,
        description: str | None = None,
        *,
        tags: Iterable[str] | None = None,
        examples: Iterable[str] | None = None,
        input_modes: Iterable[str] | None = None,
        output_modes: Iterable[str] | None = None,
    ) -> Callable[[SkillHandler], SkillHandler]:
        """Register a function and its public Agent Card metadata."""
        skill_id = name.strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", skill_id):
            raise ValueError("skill 名称只能包含字母、数字、点、下划线和连字符")
        if skill_id in self.skills:
            raise ValueError(f"skill 已存在: {skill_id}")

        def decorator(handler: SkillHandler) -> SkillHandler:
            skill_description = (
                description
                or inspect.getdoc(handler)
                or f"执行 {skill_id} 任务"
            )
            self.skills[skill_id] = handler
            self._skill_definitions[skill_id] = A2ASkillDefinition(
                id=skill_id,
                name=skill_id,
                description=skill_description,
                tags=tuple(tags or self.capabilities.keys() or (skill_id,)),
                examples=tuple(examples or ()),
                input_modes=tuple(input_modes or ("text/plain",)),
                output_modes=tuple(output_modes or ("text/plain",)),
            )
            return handler

        return decorator

    def list_skills(self) -> list[Dict[str, Any]]:
        """Return metadata that will be advertised by the Agent Card."""
        return [
            {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "tags": list(item.tags),
                "examples": list(item.examples),
                "input_modes": list(item.input_modes),
                "output_modes": list(item.output_modes),
            }
            for item in self._skill_definitions.values()
        ]

    async def execute_skill_async(self, skill_name: str, text: str) -> str:
        """Invoke one registered skill without crossing the network."""
        skill_id = skill_name.strip()
        if skill_id not in self.skills:
            raise ValueError(f"未知 A2A skill: {skill_id}")
        result = self.skills[skill_id](text)
        if inspect.isawaitable(result):
            result = await result
        return _serialize_result(result)

    def execute_skill(self, skill_name: str, text: str) -> Dict[str, Any]:
        """Return a task-like result for deterministic local practice."""
        try:
            result = _run_async(
                lambda: self.execute_skill_async(skill_name, text),
            )
            return {
                "status": "completed",
                "skill": skill_name,
                "result": result,
                "artifacts": [{"name": "result", "text": result}],
            }
        except Exception as exc:
            return {
                "status": "failed",
                "skill": skill_name,
                "result": "",
                "error": str(exc),
                "artifacts": [],
            }

    def _decode_skill_request(self, text: str) -> tuple[str, str]:
        """Decode the compatibility envelope used by ``execute_skill``."""
        stripped = text.strip()
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            data = None
        if isinstance(data, dict) and "helloagents_skill" in data:
            return str(data["helloagents_skill"]), str(data.get("input", ""))

        header = re.match(
            r"^skill\s*:\s*([A-Za-z0-9_.-]+)\s*\n(.*)$",
            stripped,
            re.DOTALL | re.IGNORECASE,
        )
        if header:
            return header.group(1), header.group(2)

        first_word = stripped.split(maxsplit=1)
        if first_word and first_word[0].lower() in self.skills:
            payload = first_word[1] if len(first_word) == 2 else ""
            return first_word[0].lower(), payload
        if len(self.skills) == 1:
            return next(iter(self.skills)), stripped
        raise ValueError(
            "无法确定目标 skill；请使用 execute_skill() 或在消息中指定 skill",
        )

    def get_agent_card(self, base_url: str) -> Dict[str, Any]:
        """Return an Agent Card as a normal dictionary."""
        normalized = base_url.rstrip("/")
        if A2A_AVAILABLE:
            return MessageToDict(
                self.build_agent_card(normalized),
                preserving_proto_field_name=True,
            )
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "supported_interfaces": [
                {
                    "url": normalized,
                    "protocol_binding": "JSONRPC",
                    "protocol_version": "1.0",
                },
            ],
            "capabilities": {"streaming": True},
            "default_input_modes": ["text/plain"],
            "default_output_modes": ["text/plain"],
            "skills": self.list_skills(),
        }

    def build_agent_card(self, base_url: str) -> Any:
        """Build the official SDK's protobuf Agent Card."""
        self._require_sdk("构建 Agent Card")
        return AgentCard(
            name=self.name,
            description=self.description,
            version=self.version,
            supported_interfaces=[
                AgentInterface(
                    url=base_url.rstrip("/"),
                    protocol_binding="JSONRPC",
                    protocol_version="1.0",
                ),
            ],
            capabilities=AgentCapabilities(streaming=True),
            default_input_modes=["text/plain"],
            default_output_modes=["text/plain"],
            skills=[
                AgentSkill(
                    id=item.id,
                    name=item.name,
                    description=item.description,
                    tags=list(item.tags),
                    examples=list(item.examples),
                    input_modes=list(item.input_modes),
                    output_modes=list(item.output_modes),
                )
                for item in self._skill_definitions.values()
            ],
        )

    def build_app(
        self,
        host: str = "127.0.0.1",
        port: int = 5000,
        public_url: str | None = None,
    ) -> Any:
        """Create a Starlette application backed by the official A2A SDK."""
        self._require_sdk("启动 A2A HTTP 服务")
        try:
            from starlette.applications import Starlette
        except ImportError as exc:  # pragma: no cover - optional extra.
            raise RuntimeError(
                '缺少 HTTP Server 依赖，请安装 "a2a-sdk[http-server]"',
            ) from exc

        advertised_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
        endpoint = public_url or f"http://{advertised_host}:{port}"
        card = self.build_agent_card(endpoint)
        request_handler = DefaultRequestHandler(
            agent_executor=_SkillExecutor(self),
            task_store=InMemoryTaskStore(),
            agent_card=card,
        )
        routes = [
            *create_agent_card_routes(card),
            *create_jsonrpc_routes(request_handler, rpc_url="/"),
        ]

        @asynccontextmanager
        async def lifespan(_: Any):
            try:
                yield
            finally:
                await request_handler.aclose()

        return Starlette(routes=routes, lifespan=lifespan)

    def run(
        self,
        host: str = "127.0.0.1",
        port: int = 5000,
        public_url: str | None = None,
        log_level: str = "warning",
    ) -> None:
        """Run the A2A service with Uvicorn."""
        self._require_sdk("启动 A2A HTTP 服务")
        try:
            import uvicorn
        except ImportError as exc:  # pragma: no cover - optional extra.
            raise RuntimeError(
                '缺少 HTTP Server 依赖，请安装 "a2a-sdk[http-server]"',
            ) from exc
        uvicorn.run(
            self.build_app(host=host, port=port, public_url=public_url),
            host=host,
            port=port,
            log_level=log_level,
        )

    @staticmethod
    def _require_sdk(action: str) -> None:
        if not A2A_AVAILABLE:
            raise RuntimeError(
                f"{action}需要 A2A SDK，请安装 a2a-sdk[http-server]",
            )


class _SkillExecutor(AgentExecutor):
    """Translate an A2A Message into task events and a result Artifact."""

    def __init__(self, server: A2AServer) -> None:
        self.server = server

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        if context.message is None:
            raise ValueError("A2A 请求缺少 Message")

        task = context.current_task
        if task is None:
            task = new_task_from_user_message(context.message)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.context_id)
        await updater.start_work(
            new_text_message(
                "正在执行 Agent skill",
                task_id=task.id,
                context_id=task.context_id,
            ),
        )

        try:
            skill_name, payload = self.server._decode_skill_request(
                get_message_text(context.message),
            )
            result = await self.server.execute_skill_async(skill_name, payload)
            await updater.add_artifact(
                parts=[new_text_part(result)],
                name=f"{skill_name}-result",
                last_chunk=True,
            )
            await updater.complete(
                new_text_message(
                    f"skill {skill_name} 执行完成",
                    task_id=task.id,
                    context_id=task.context_id,
                ),
            )
        except Exception as exc:
            await updater.failed(
                new_text_message(
                    f"执行失败: {exc}",
                    task_id=task.id,
                    context_id=task.context_id,
                ),
            )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        if not context.task_id or not context.context_id:
            raise ValueError("取消任务需要 task_id 和 context_id")
        updater = TaskUpdater(
            event_queue,
            context.task_id,
            context.context_id,
        )
        await updater.cancel(
            new_text_message(
                "任务已取消",
                task_id=context.task_id,
                context_id=context.context_id,
            ),
        )


class A2AClient:
    """Discover an Agent and exchange A2A messages and task operations."""

    def __init__(
        self,
        agent_url: str,
        *,
        timeout: float = 30.0,
        local_server: A2AServer | None = None,
    ) -> None:
        normalized = agent_url.strip().rstrip("/")
        if local_server is None:
            parsed = urlparse(normalized)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("agent_url 必须是有效的 HTTP(S) 地址")
        if timeout <= 0:
            raise ValueError("timeout 必须大于 0")
        self.agent_url = normalized
        self.timeout = timeout
        self._local_server = local_server

    @classmethod
    def from_server(cls, server: A2AServer) -> "A2AClient":
        """Create a dependency-free client for local collaboration tests."""
        return cls(
            f"local://{server.name}",
            local_server=server,
        )

    def describe(self) -> str:
        """Return endpoint configuration without making a request."""
        return f"A2A endpoint: {self.agent_url}"

    def get_agent_card(self) -> Dict[str, Any]:
        return _run_async(self.get_agent_card_async)

    async def get_agent_card_async(self) -> Dict[str, Any]:
        if self._local_server is not None:
            return self._local_server.get_agent_card(self.agent_url)
        self._require_sdk()
        async with httpx.AsyncClient(timeout=self.timeout) as http_client:
            resolver = A2ACardResolver(http_client, self.agent_url)
            card = await resolver.get_agent_card()
        return MessageToDict(card, preserving_proto_field_name=True)

    def send_message(
        self,
        text: str,
        *,
        task_id: str | None = None,
        context_id: str | None = None,
        streaming: bool = True,
    ) -> Dict[str, Any]:
        return _run_async(
            lambda: self.send_message_async(
                text,
                task_id=task_id,
                context_id=context_id,
                streaming=streaming,
            ),
        )

    async def send_message_async(
        self,
        text: str,
        *,
        task_id: str | None = None,
        context_id: str | None = None,
        streaming: bool = True,
    ) -> Dict[str, Any]:
        if not text.strip():
            raise ValueError("A2A Message 不能为空")
        if self._local_server is not None:
            skill_name, payload = self._local_server._decode_skill_request(text)
            return self._local_server.execute_skill(skill_name, payload)

        self._require_sdk()
        request = SendMessageRequest(
            message=new_text_message(
                text,
                role=Role.ROLE_USER,
                task_id=task_id,
                context_id=context_id,
            ),
            configuration=SendMessageConfiguration(
                accepted_output_modes=["text/plain"],
                history_length=10,
                return_immediately=False,
            ),
        )
        async with httpx.AsyncClient(timeout=self.timeout) as http_client:
            config = ClientConfig(
                streaming=streaming,
                httpx_client=http_client,
                accepted_output_modes=["text/plain"],
            )
            client = await create_client(
                self.agent_url,
                client_config=config,
                resolver_http_kwargs={"timeout": self.timeout},
            )
            async with client:
                responses = [
                    response async for response in client.send_message(request)
                ]
        return self._normalize_stream(responses)

    def execute_skill(self, skill_name: str, text: str) -> Dict[str, Any]:
        """Compatibility helper layered on top of a normal A2A Message."""
        if self._local_server is not None:
            return self._local_server.execute_skill(skill_name, text)
        envelope = json.dumps(
            {"helloagents_skill": skill_name, "input": text},
            ensure_ascii=False,
        )
        response = self.send_message(envelope)
        response["skill"] = skill_name
        return response

    def get_task(self, task_id: str) -> Dict[str, Any]:
        return _run_async(lambda: self.get_task_async(task_id))

    async def get_task_async(self, task_id: str) -> Dict[str, Any]:
        if self._local_server is not None:
            raise RuntimeError("本地直调不保存远程 Task；请使用 HTTP 服务")
        self._require_sdk()
        if not task_id.strip():
            raise ValueError("task_id 不能为空")
        async with httpx.AsyncClient(timeout=self.timeout) as http_client:
            client = await create_client(
                self.agent_url,
                client_config=ClientConfig(httpx_client=http_client),
            )
            async with client:
                task = await client.get_task(GetTaskRequest(id=task_id))
        return self._normalize_task(task)

    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        return _run_async(lambda: self.cancel_task_async(task_id))

    async def cancel_task_async(self, task_id: str) -> Dict[str, Any]:
        if self._local_server is not None:
            raise RuntimeError("本地直调没有可取消的远程 Task")
        self._require_sdk()
        if not task_id.strip():
            raise ValueError("task_id 不能为空")
        async with httpx.AsyncClient(timeout=self.timeout) as http_client:
            client = await create_client(
                self.agent_url,
                client_config=ClientConfig(httpx_client=http_client),
            )
            async with client:
                task = await client.cancel_task(CancelTaskRequest(id=task_id))
        return self._normalize_task(task)

    @staticmethod
    def _normalize_task(task: Task) -> Dict[str, Any]:
        artifacts = [
            {
                "id": artifact.artifact_id,
                "name": artifact.name,
                "text": get_artifact_text(artifact),
            }
            for artifact in task.artifacts
        ]
        return {
            "task_id": task.id,
            "context_id": task.context_id,
            "status": _state_name(task.status.state),
            "result": artifacts[-1]["text"] if artifacts else "",
            "artifacts": artifacts,
        }

    @classmethod
    def _normalize_stream(
        cls,
        responses: Iterable[StreamResponse],
    ) -> Dict[str, Any]:
        task_id = ""
        context_id = ""
        status = "unknown"
        artifacts: list[Dict[str, str]] = []
        messages: list[str] = []
        events: list[Dict[str, str]] = []
        error = ""

        for response in responses:
            kind = response.WhichOneof("payload")
            if kind == "task":
                task = response.task
                task_id = task.id
                context_id = task.context_id
                status = _state_name(task.status.state)
                artifacts = cls._normalize_task(task)["artifacts"]
                events.append({"type": "task", "status": status})
            elif kind == "message":
                message = response.message
                task_id = message.task_id or task_id
                context_id = message.context_id or context_id
                text = get_message_text(message)
                messages.append(text)
                status = "completed"
                events.append({"type": "message", "text": text})
            elif kind == "status_update":
                update = response.status_update
                task_id = update.task_id or task_id
                context_id = update.context_id or context_id
                status = _state_name(update.status.state)
                text = (
                    get_message_text(update.status.message)
                    if update.status.HasField("message")
                    else ""
                )
                events.append(
                    {"type": "status", "status": status, "text": text},
                )
                if status in {"failed", "rejected", "canceled"}:
                    error = text
            elif kind == "artifact_update":
                update = response.artifact_update
                task_id = update.task_id or task_id
                context_id = update.context_id or context_id
                artifact = {
                    "id": update.artifact.artifact_id,
                    "name": update.artifact.name,
                    "text": get_artifact_text(update.artifact),
                }
                artifacts.append(artifact)
                events.append(
                    {"type": "artifact", "name": artifact["name"]},
                )

        result = artifacts[-1]["text"] if artifacts else "\n".join(messages)
        return {
            "task_id": task_id,
            "context_id": context_id,
            "status": status,
            "result": result,
            "error": error,
            "artifacts": artifacts,
            "events": events,
        }

    @staticmethod
    def _require_sdk() -> None:
        if not A2A_AVAILABLE:
            raise RuntimeError(
                "A2A 网络通信需要 a2a-sdk，请先安装 a2a-sdk[http-server]",
            )
