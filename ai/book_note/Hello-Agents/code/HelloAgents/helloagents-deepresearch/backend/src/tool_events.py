"""Bridge ToolAwareSimpleAgent callbacks into coordinator events."""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from copy import deepcopy
from typing import Any


class ToolCallRecorder:
    """Collect tool-call metadata until the streaming coordinator drains it."""

    def __init__(self) -> None:
        self._pending: deque[dict[str, Any]] = deque()

    def __call__(self, call_info: Mapping[str, Any]) -> None:
        parameters = call_info.get("parsed_parameters", {})
        if not isinstance(parameters, dict):
            parameters = {"input": str(parameters)}
        self._pending.append(
            {
                "agent_name": str(call_info.get("agent_name", "unknown")),
                "tool_name": str(call_info.get("tool_name", "unknown")),
                "parsed_parameters": deepcopy(parameters),
            }
        )

    def drain(self) -> list[dict[str, Any]]:
        """Return pending records once, preserving call order."""
        records = list(self._pending)
        self._pending.clear()
        return records
