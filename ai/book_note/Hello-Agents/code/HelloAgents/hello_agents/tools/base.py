"""Minimal tool interface required by the chapter's Agent paradigms."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from pydantic import BaseModel


class ToolParameter(BaseModel):
    """Describe one argument accepted by a tool."""

    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None


class Tool(ABC):
    """Base class for tools registered in ``ToolRegistry``."""

    def __init__(
        self,
        name: str,
        description: str,
        expandable: bool = False,
    ) -> None:
        self.name = name
        self.description = description
        self.expandable = expandable

    @abstractmethod
    def run(self, parameters: Dict[str, Any]) -> str:
        """Execute the tool with structured parameters."""
        raise NotImplementedError

    @abstractmethod
    def get_parameters(self) -> List[ToolParameter]:
        """Return the tool's parameter definitions."""
        raise NotImplementedError

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Check that all required parameters are present."""
        required = [
            parameter.name
            for parameter in self.get_parameters()
            if parameter.required
        ]
        return all(name in parameters for name in required)

    def get_expanded_tools(self) -> List["Tool"] | None:
        """Extension point reserved for later expandable-tool chapters."""
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the tool definition to a serializable dictionary."""
        parameters = []
        for parameter in self.get_parameters():
            if hasattr(parameter, "model_dump"):
                parameters.append(parameter.model_dump())
            else:
                parameters.append(parameter.dict())
        return {
            "name": self.name,
            "description": self.description,
            "parameters": parameters,
        }

    def __str__(self) -> str:
        return f"Tool(name={self.name})"

    def __repr__(self) -> str:
        return self.__str__()
