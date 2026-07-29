"""Simple conversation Agent with the chapter's optional text-tool protocol."""

from __future__ import annotations

import json
import re
from typing import Any, Iterator

from ..core.agent import Agent
from ..core.config import Config
from ..core.llm import HelloAgentsLLM
from ..core.message import Message
from ..tools.base import Tool
from ..tools.registry import ToolRegistry


class SimpleAgent(Agent):
    """Build a normal chat request and optionally execute text tool calls."""

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: str | None = None,
        config: Config | None = None,
        tool_registry: ToolRegistry | None = None,
        enable_tool_calling: bool = True,
    ) -> None:
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry
        self.enable_tool_calling = (
            enable_tool_calling and tool_registry is not None
        )

    def _get_enhanced_system_prompt(self) -> str:
        """Append tool descriptions and the chapter's call protocol."""
        base_prompt = self.system_prompt or "你是一个有用的AI助手。"
        if not self.enable_tool_calling or not self.tool_registry:
            return base_prompt

        tools = self.tool_registry.get_tools_description()
        if tools == "暂无可用工具":
            return base_prompt
        return (
            f"{base_prompt}\n\n"
            "## 可用工具\n"
            f"{tools}\n\n"
            "## 工具调用格式\n"
            "需要工具时输出 `[TOOL_CALL:{tool_name}:{parameters}]`。\n"
            "多个参数使用 `key=value` 并以逗号分隔；"
            "工具结果返回后，再给出完整回答。"
        )

    def run(
        self,
        input_text: str,
        max_tool_iterations: int = 3,
        **kwargs: Any,
    ) -> str:
        """Run one conversation turn, including optional tool iterations."""
        messages = [
            {
                "role": "system",
                "content": self._get_enhanced_system_prompt(),
            },
            *(message.to_dict() for message in self._history),
            {"role": "user", "content": input_text},
        ]

        if self.enable_tool_calling:
            response = self._run_with_tools(
                messages,
                max_tool_iterations=max_tool_iterations,
                **kwargs,
            )
        else:
            response = self.llm.invoke(messages, **kwargs)

        self.add_message(Message(content=input_text, role="user"))
        self.add_message(Message(content=response, role="assistant"))
        return response

    def _run_with_tools(
        self,
        messages: list[dict[str, str]],
        max_tool_iterations: int,
        **kwargs: Any,
    ) -> str:
        """Repeat model → tool → model until no call marker remains."""
        for _ in range(max_tool_iterations):
            response = self.llm.invoke(messages, **kwargs)
            tool_calls = self._parse_tool_calls(response)
            if not tool_calls:
                return response

            clean_response = response
            results = []
            for call in tool_calls:
                clean_response = clean_response.replace(call["original"], "")
                results.append(
                    self._execute_tool_call(
                        call["tool_name"],
                        call["parameters"],
                    ),
                )
            messages.append(
                {"role": "assistant", "content": clean_response.strip()},
            )
            joined_results = "\n\n".join(results)
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "工具执行结果：\n"
                        f"{joined_results}\n\n"
                        "请基于这些结果给出完整的回答。"
                    ),
                },
            )

        return self.llm.invoke(messages, **kwargs)

    @staticmethod
    def _parse_tool_calls(text: str) -> list[dict[str, str]]:
        """Extract ``[TOOL_CALL:name:parameters]`` markers."""
        pattern = r"\[TOOL_CALL:([^:]+):([^\]]+)\]"
        return [
            {
                "tool_name": name.strip(),
                "parameters": parameters.strip(),
                "original": f"[TOOL_CALL:{name}:{parameters}]",
            }
            for name, parameters in re.findall(pattern, text)
        ]

    def _execute_tool_call(self, tool_name: str, parameters: str) -> str:
        """Dispatch to a Tool object or a registered lightweight function."""
        if not self.tool_registry:
            return "错误：未配置工具注册表。"

        tool = self.tool_registry.get_tool(tool_name)
        try:
            if tool:
                result = tool.run(
                    self._parse_tool_parameters(tool, parameters),
                )
            elif self.tool_registry.get_function(tool_name):
                result = self.tool_registry.execute_tool(
                    tool_name,
                    parameters,
                )
            else:
                return f"错误：未找到工具 '{tool_name}'。"
        except Exception as error:
            return f"错误：工具 '{tool_name}' 执行失败：{error}"
        return f"工具 {tool_name} 执行结果：\n{result}"

    def _parse_tool_parameters(
        self,
        tool: Tool,
        parameters: str,
    ) -> dict[str, Any]:
        """Parse JSON, key-value pairs, or one plain-text input."""
        raw = parameters.strip()
        values: dict[str, Any]
        if raw.startswith("{"):
            try:
                parsed = json.loads(raw)
                values = parsed if isinstance(parsed, dict) else {"input": raw}
            except json.JSONDecodeError:
                values = {"input": raw}
        elif "=" in raw:
            values = {}
            for pair in raw.split(","):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    values[key.strip()] = value.strip()
        else:
            definitions = tool.get_parameters()
            key = definitions[0].name if len(definitions) == 1 else "input"
            values = {key: raw}

        parameter_types = {
            parameter.name: parameter.type
            for parameter in tool.get_parameters()
        }
        for key, value in list(values.items()):
            if not isinstance(value, str):
                continue
            try:
                if parameter_types.get(key) == "integer":
                    values[key] = int(value)
                elif parameter_types.get(key) == "number":
                    values[key] = float(value)
                elif parameter_types.get(key) == "boolean":
                    values[key] = value.lower() in {"true", "1", "yes"}
            except ValueError:
                pass
        return values

    def add_tool(self, tool: Tool, auto_expand: bool = True) -> None:
        """Register a Tool and enable tool calling."""
        if self.tool_registry is None:
            self.tool_registry = ToolRegistry()
        self.tool_registry.register_tool(tool, auto_expand=auto_expand)
        self.enable_tool_calling = True

    def remove_tool(self, tool_name: str) -> bool:
        """Remove a registered Tool or function."""
        return bool(
            self.tool_registry
            and self.tool_registry.unregister(tool_name)
        )

    def list_tools(self) -> list[str]:
        """Return currently available tool names."""
        return self.tool_registry.list_tools() if self.tool_registry else []

    def has_tools(self) -> bool:
        """Report whether text tool calling is active."""
        return bool(
            self.enable_tool_calling
            and self.tool_registry
            and self.tool_registry.list_tools()
        )

    def stream_run(self, input_text: str, **kwargs: Any) -> Iterator[str]:
        """Stream a plain conversation response and then store it."""
        messages = []
        if self.system_prompt:
            messages.append(
                {"role": "system", "content": self.system_prompt},
            )
        messages.extend(message.to_dict() for message in self._history)
        messages.append({"role": "user", "content": input_text})

        full_response = ""
        for chunk in self.llm.stream_invoke(messages, **kwargs):
            full_response += chunk
            yield chunk

        self.add_message(Message(content=input_text, role="user"))
        self.add_message(
            Message(content=full_response, role="assistant"),
        )
