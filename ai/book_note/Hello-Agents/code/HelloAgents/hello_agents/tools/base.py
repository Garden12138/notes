"""Core interfaces shared by the HelloAgents tool system."""

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

    def to_openai_schema(self) -> Dict[str, Any]:
        """Convert this Tool to a Chat Completions function schema."""
        supported_types = {
            "array",
            "boolean",
            "integer",
            "number",
            "object",
            "string",
        }
        properties: Dict[str, Any] = {}
        required: List[str] = []

        for parameter in self.get_parameters():
            parameter_type = parameter.type.lower()
            if parameter_type not in supported_types:
                parameter_type = "string"

            description = parameter.description
            if parameter.default is not None:
                description = (
                    f"{description}（默认值：{parameter.default}）"
                )

            property_schema: Dict[str, Any] = {
                "type": parameter_type,
                "description": description,
            }
            if parameter_type == "array":
                property_schema["items"] = {"type": "string"}

            properties[parameter.name] = property_schema
            if parameter.required:
                required.append(parameter.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def __str__(self) -> str:
        return f"Tool(name={self.name})"

    def __repr__(self) -> str:
        return self.__str__()
