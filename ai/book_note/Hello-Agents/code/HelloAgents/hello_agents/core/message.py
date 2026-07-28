"""Message objects shared by HelloAgents components."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal

from pydantic import BaseModel, Field


MessageRole = Literal["user", "assistant", "system", "tool"]


class Message(BaseModel):
    """Represent one message inside the framework."""

    content: str
    role: MessageRole
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        """Convert to the message shape accepted by the OpenAI API."""
        return {
            "role": self.role,
            "content": self.content,
        }

    def __str__(self) -> str:
        """Return a compact representation for logs and debugging."""
        return f"[{self.role}] {self.content}"
