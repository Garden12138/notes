"""Central configuration for the HelloAgents learning framework."""

from __future__ import annotations

import os
from typing import Any, Dict

from pydantic import BaseModel


class Config(BaseModel):
    """Store shared LLM, runtime, and history settings."""

    default_model: str = "gpt-3.5-turbo"
    default_provider: str = "openai"
    temperature: float = 0.7
    max_tokens: int | None = None

    debug: bool = False
    log_level: str = "INFO"

    max_history_length: int = 100

    @classmethod
    def from_env(cls) -> "Config":
        """Create a configuration from the chapter's environment variables."""
        max_tokens = os.getenv("MAX_TOKENS")
        return cls(
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            max_tokens=int(max_tokens) if max_tokens else None,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a plain dictionary on Pydantic v1 or v2."""
        if hasattr(self, "model_dump"):
            return self.model_dump()
        return self.dict()
