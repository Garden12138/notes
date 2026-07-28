"""Abstract Agent interface used by concrete HelloAgents paradigms."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .config import Config
from .llm import HelloAgentsLLM
from .message import Message


class Agent(ABC):
    """Define the common dependencies and behavior of an Agent."""

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: str | None = None,
        config: Config | None = None,
    ) -> None:
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        self.config = config or Config()
        self._history: list[Message] = []

    @abstractmethod
    def run(self, input_text: str, **kwargs: object) -> str:
        """Run the Agent and return its final text response."""
        raise NotImplementedError

    def add_message(self, message: Message) -> None:
        """Append one message to the conversation history."""
        self._history.append(message)

    def clear_history(self) -> None:
        """Remove all messages from the conversation history."""
        self._history.clear()

    def get_history(self) -> list[Message]:
        """Return a shallow copy so callers cannot replace the internal list."""
        return self._history.copy()

    def __str__(self) -> str:
        """Return a concise identity for logs and debugging."""
        return f"Agent(name={self.name}, provider={self.llm.provider})"

    def __repr__(self) -> str:
        return self.__str__()
