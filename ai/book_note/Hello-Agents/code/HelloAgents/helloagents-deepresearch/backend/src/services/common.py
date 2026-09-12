"""Small runtime protocol shared by role services."""

from __future__ import annotations

from typing import Protocol


class AgentRunner(Protocol):
    """Subset implemented by ToolAwareSimpleAgent and deterministic fixtures."""

    def run(self, input_text: str, **kwargs: object) -> str: ...

    def clear_history(self) -> None: ...
