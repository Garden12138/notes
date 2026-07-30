"""Agent using the OpenAI-compatible structured tool-calling protocol."""

from __future__ import annotations

import json
from typing import Any, Iterator

from ..core.agent import Agent
from ..core.config import Config
from ..core.llm import HelloAgentsLLM
from ..core.message import Message
from ..tools.base import Tool
from ..tools.registry import ToolRegistry


ToolChoice = str | dict[str, Any]


class FunctionCallAgent(Agent):
    """Run a SimpleAgent-like loop with structured ``tool_calls``."""

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: str | None = None,
        config: Config | None = None,
        tool_registry: ToolRegistry | None = None,
        enable_tool_calling: bool = True,
        default_tool_choice: ToolChoice = "auto",
        max_tool_iterations: int = 3,
    ) -> None:
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry
        self.enable_tool_calling = (
            enable_tool_calling and tool_registry is not None
        )
        self.default_tool_choice = default_tool_choice
        self.max_tool_iterations = max_tool_iterations

    def _get_system_prompt(self) -> str:
        """Build the system prompt; schemas carry the formal definitions."""
        base_prompt = (
            self.system_prompt
            or "你是一个可靠的 AI 助手，可在需要时调用工具。"
        )
        if not self.enable_tool_calling or not self.tool_registry:
            return base_prompt

        descriptions = self.tool_registry.get_tools_description()
        if descriptions == "暂无可用工具":
            return base_prompt
        return (
            f"{base_prompt}\n\n"
            "## 可用工具\n"
            f"{descriptions}\n\n"
            "需要外部信息或执行动作时，请通过函数调用使用工具。"
        )

    def _build_tool_schemas(self) -> list[dict[str, Any]]:
        """Convert registered tools to Chat Completions tool schemas."""
        if not self.enable_tool_calling or not self.tool_registry:
            return []

        schemas: list[dict[str, Any]] = []
        for tool in self.tool_registry.get_all_tools():
            schemas.append(tool.to_openai_schema())

        function_map = getattr(self.tool_registry, "_functions", {})
        for name, info in function_map.items():
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": info.get("description", ""),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "input": {
                                    "type": "string",
                                    "description": "输入文本",
                                },
                            },
                            "required": ["input"],
                        },
                    },
                },
            )
        return schemas

    @staticmethod
    def _extract_message_content(raw_content: Any) -> str:
        """Read text from a string or a list-style content response."""
        if raw_content is None:
            return ""
        if isinstance(raw_content, str):
            return raw_content
        if isinstance(raw_content, list):
            parts = []
            for item in raw_content:
                text = (
                    item.get("text")
                    if isinstance(item, dict)
                    else getattr(item, "text", None)
                )
                if text:
                    parts.append(text)
            return "".join(parts)
        return str(raw_content)

    @staticmethod
    def _parse_function_call_arguments(
        arguments: str | None,
    ) -> dict[str, Any]:
        """Parse the JSON argument string returned by the model."""
        if not arguments:
            return {}
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _convert_parameter_types(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Use Tool metadata to recover simple Python scalar types."""
        if not self.tool_registry:
            return arguments
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            return arguments

        parameter_types = {
            parameter.name: parameter.type.lower()
            for parameter in tool.get_parameters()
        }
        converted: dict[str, Any] = {}
        for name, value in arguments.items():
            parameter_type = parameter_types.get(name)
            try:
                if parameter_type in {"number", "float"}:
                    converted[name] = float(value)
                elif parameter_type in {"integer", "int"}:
                    converted[name] = int(value)
                elif parameter_type in {"boolean", "bool"}:
                    if isinstance(value, str):
                        converted[name] = value.lower() in {
                            "true",
                            "1",
                            "yes",
                        }
                    else:
                        converted[name] = bool(value)
                else:
                    converted[name] = value
            except (TypeError, ValueError):
                converted[name] = value
        return converted

    def _execute_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> str:
        """Execute one Tool object or lightweight function."""
        if not self.tool_registry:
            return "错误：未配置工具注册表。"

        tool = self.tool_registry.get_tool(tool_name)
        try:
            if tool:
                typed_arguments = self._convert_parameter_types(
                    tool_name,
                    arguments,
                )
                if not tool.validate_parameters(typed_arguments):
                    required = [
                        parameter.name
                        for parameter in tool.get_parameters()
                        if parameter.required
                    ]
                    missing = [
                        name
                        for name in required
                        if name not in typed_arguments
                    ]
                    return (
                        f"错误：工具 '{tool_name}' 缺少必需参数："
                        f"{'、'.join(missing)}"
                    )
                return str(tool.run(typed_arguments))

            function = self.tool_registry.get_function(tool_name)
            if function:
                return str(function(arguments.get("input", "")))
        except Exception as error:
            return f"错误：工具 '{tool_name}' 执行失败：{error}"
        return f"错误：未找到工具 '{tool_name}'。"

    def _invoke_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_choice: ToolChoice,
        **kwargs: Any,
    ) -> Any:
        """Call the SDK directly so structured ``tool_calls`` are preserved."""
        client = getattr(self.llm, "_client", None)
        if client is None:
            raise RuntimeError(
                "HelloAgentsLLM 未正确初始化客户端，无法执行函数调用。",
            )

        request_options = dict(kwargs)
        request_options.setdefault("temperature", self.llm.temperature)
        if self.llm.max_tokens is not None:
            request_options.setdefault("max_tokens", self.llm.max_tokens)
        return client.chat.completions.create(
            model=self.llm.model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            **request_options,
        )

    def run(
        self,
        input_text: str,
        *,
        max_tool_iterations: int | None = None,
        tool_choice: ToolChoice | None = None,
        **kwargs: Any,
    ) -> str:
        """Run model → tool → model using native structured messages."""
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._get_system_prompt()},
            *(message.to_dict() for message in self._history),
            {"role": "user", "content": input_text},
        ]
        tool_schemas = self._build_tool_schemas()
        if not tool_schemas:
            response = self.llm.invoke(messages, **kwargs)
            self._save_turn(input_text, response)
            return response

        iteration_limit = (
            max_tool_iterations
            if max_tool_iterations is not None
            else self.max_tool_iterations
        )
        effective_tool_choice = (
            tool_choice
            if tool_choice is not None
            else self.default_tool_choice
        )
        final_response = ""

        for _ in range(iteration_limit):
            response = self._invoke_with_tools(
                messages,
                tools=tool_schemas,
                tool_choice=effective_tool_choice,
                **kwargs,
            )
            assistant_message = response.choices[0].message
            content = self._extract_message_content(
                assistant_message.content,
            )
            tool_calls = list(assistant_message.tool_calls or [])
            if not tool_calls:
                final_response = content
                break

            messages.append(
                {
                    "role": "assistant",
                    "content": content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": (
                                    tool_call.function.arguments
                                ),
                            },
                        }
                        for tool_call in tool_calls
                    ],
                },
            )
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                arguments = self._parse_function_call_arguments(
                    tool_call.function.arguments,
                )
                result = self._execute_tool_call(
                    tool_name,
                    arguments,
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    },
                )
        else:
            final_choice = self._invoke_with_tools(
                messages,
                tools=tool_schemas,
                tool_choice="none",
                **kwargs,
            )
            final_response = self._extract_message_content(
                final_choice.choices[0].message.content,
            )

        self._save_turn(input_text, final_response)
        return final_response

    def _save_turn(self, input_text: str, output_text: str) -> None:
        self.add_message(Message(content=input_text, role="user"))
        self.add_message(
            Message(content=output_text, role="assistant"),
        )

    def add_tool(self, tool: Tool) -> None:
        """Register a Tool and enable structured tool calling."""
        if self.tool_registry is None:
            self.tool_registry = ToolRegistry()
        self.tool_registry.register_tool(tool)
        self.enable_tool_calling = True

    def remove_tool(self, tool_name: str) -> bool:
        """Remove a registered Tool or function."""
        return bool(
            self.tool_registry
            and self.tool_registry.unregister(tool_name)
        )

    def list_tools(self) -> list[str]:
        """Return all available tool names."""
        return self.tool_registry.list_tools() if self.tool_registry else []

    def has_tools(self) -> bool:
        """Report whether structured tool calling is active."""
        return bool(
            self.enable_tool_calling
            and self.tool_registry
            and self.tool_registry.list_tools()
        )

    def stream_run(self, input_text: str, **kwargs: Any) -> Iterator[str]:
        """Fall back to one complete response, matching the chapter code."""
        yield self.run(input_text, **kwargs)
