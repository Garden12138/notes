"""Exceptions raised by the HelloAgents learning framework."""


class HelloAgentsException(Exception):
    """Base exception for errors raised inside HelloAgents."""


class LLMException(HelloAgentsException):
    """Error raised by an LLM client."""


class AgentException(HelloAgentsException):
    """Error raised while an Agent is running."""


class ConfigException(HelloAgentsException):
    """Error raised while loading or validating configuration."""


class ToolException(HelloAgentsException):
    """Error raised while registering or executing a tool."""
