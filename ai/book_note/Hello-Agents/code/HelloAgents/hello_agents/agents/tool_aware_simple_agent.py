"""SimpleAgent extension that reports completed tool calls to a listener."""

from __future__ import annotations

import json
from typing import Any, Callable, TypedDict

from ..core.config import Config
from ..core.llm import HelloAgentsLLM
from ..tools.registry import ToolRegistry
from .simple_agent import SimpleAgent


class ToolCallInfo(TypedDict):
    """Information exposed after one tool call finishes."""

    agent_name: str
    tool_name: str
    parsed_parameters: dict[str, Any]
    result: str


ToolCallListener = Callable[[ToolCallInfo], None]


class ToolAwareSimpleAgent(SimpleAgent):
    """Keep SimpleAgent behavior while making tool calls observable."""

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: str | None = None,
        config: Config | None = None,
        tool_registry: ToolRegistry | None = None,
        enable_tool_calling: bool = True,
        tool_call_listener: ToolCallListener | None = None,
    ) -> None:
        super().__init__(
            name=name,
            llm=llm,
            system_prompt=system_prompt,
            config=config,
            tool_registry=tool_registry,
            enable_tool_calling=enable_tool_calling,
        )
        self._tool_call_listener = tool_call_listener

    def _execute_tool_call(self, tool_name: str, parameters: str) -> str:
        """Execute through SimpleAgent, then notify the optional listener."""
        parsed_parameters = self._parse_listener_parameters(
            tool_name,
            parameters,
        )
        result = super()._execute_tool_call(tool_name, parameters)
        if self._tool_call_listener is not None:
            self._tool_call_listener(
                ToolCallInfo(
                    agent_name=self.name,
                    tool_name=tool_name,
                    parsed_parameters=parsed_parameters,
                    result=result,
                )
            )
        return result

    def _parse_listener_parameters(
        self,
        tool_name: str,
        parameters: str,
    ) -> dict[str, Any]:
        """Reuse Tool metadata when possible and support lightweight functions."""
        tool = self.tool_registry.get_tool(tool_name) if self.tool_registry else None
        if tool is not None:
            return self._parse_tool_parameters(tool, parameters)

        raw = parameters.strip()
        if raw.startswith("{"):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, dict):
                return parsed

        if "=" in raw:
            parsed_pairs: dict[str, Any] = {}
            for pair in raw.split(","):
                if "=" not in pair:
                    continue
                key, value = pair.split("=", 1)
                parsed_pairs[key.strip()] = value.strip()
            if parsed_pairs:
                return parsed_pairs
        return {"input": raw}
