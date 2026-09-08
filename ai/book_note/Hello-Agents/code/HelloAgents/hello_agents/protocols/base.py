"""Shared concepts for the communication-protocol chapter."""

from __future__ import annotations

from enum import Enum


class ProtocolType(str, Enum):
    """Protocol families introduced in chapter 10."""

    MCP = "mcp"
    A2A = "a2a"
    ANP = "anp"


class Protocol:
    """Describe a protocol implementation without forcing one inheritance model.

    MCP, A2A and ANP have different responsibilities and dependencies.  This
    class therefore records common identity only; concrete implementations do
    not have to inherit it.
    """

    def __init__(
        self,
        protocol_type: ProtocolType,
        version: str = "1.0.0",
    ) -> None:
        if not version.strip():
            raise ValueError("version 不能为空")
        self._protocol_type = protocol_type
        self._version = version.strip()

    @property
    def protocol_name(self) -> str:
        """Return the lowercase protocol identifier."""
        return self._protocol_type.value

    @property
    def version(self) -> str:
        """Return the declared implementation version."""
        return self._version

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(protocol={self.protocol_name}, "
            f"version={self.version})"
        )

    def __repr__(self) -> str:
        return str(self)
