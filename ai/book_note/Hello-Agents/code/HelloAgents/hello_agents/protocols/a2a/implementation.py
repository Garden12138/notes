"""Endpoint configuration used by section 10.1's A2A quick experience."""

from __future__ import annotations

from urllib.parse import urlparse


class A2AClient:
    """Validate and hold the address of a peer Agent.

    Section 10.1 only creates an A2A tool; it does not start a peer server or
    exchange a task.  Keeping endpoint validation here makes that setup code
    executable without pretending that a local stub is the official A2A wire
    protocol.
    """

    def __init__(self, agent_url: str) -> None:
        normalized = agent_url.strip().rstrip("/")
        parsed = urlparse(normalized)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("agent_url 必须是有效的 HTTP(S) 地址")
        self.agent_url = normalized

    def describe(self) -> str:
        """Return local endpoint configuration without making a request."""
        return f"A2A endpoint: {self.agent_url}"
