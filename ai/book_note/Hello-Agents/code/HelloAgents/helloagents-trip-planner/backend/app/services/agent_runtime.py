"""Production dependency assembly for the multi-agent travel planner."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Protocol

from ..agents import MultiAgentTripPlanner, build_simple_agent_team
from .mcp_integration import (
    AmapMCPConfig,
    AmapMCPRuntime,
    MCPIntegrationError,
    create_amap_mcp_runtime,
)


class AgentRuntimeError(RuntimeError):
    """Raised when LLM or MCP dependencies cannot be assembled."""


class RuntimeSettings(Protocol):
    """Configuration fields consumed by the production assembler."""

    llm_api_key: str
    llm_model_id: str
    llm_base_url: str
    amap_maps_api_key: str


@dataclass(frozen=True)
class SharedAgentResources:
    """Stateless resources shared by all request-scoped Agent teams."""

    llm: Any
    amap: AmapMCPRuntime


def build_shared_agent_resources(
    settings: RuntimeSettings,
    llm_class: Any | None = None,
    mcp_tool_class: Any | None = None,
) -> SharedAgentResources:
    """Build the LLM and one discovered Amap MCP facade."""
    missing = [
        name
        for name, value in (
            ("LLM_API_KEY", settings.llm_api_key),
            ("LLM_MODEL_ID", settings.llm_model_id),
            ("LLM_BASE_URL", settings.llm_base_url),
            ("AMAP_MAPS_API_KEY", settings.amap_maps_api_key),
        )
        if not value.strip()
    ]
    if missing:
        raise AgentRuntimeError(f"缺少运行配置：{'、'.join(missing)}")

    if llm_class is None:
        try:
            from hello_agents import HelloAgentsLLM
        except ImportError as exc:
            raise AgentRuntimeError(
                "未找到 hello_agents，请使用 README 中的 PYTHONPATH 启动方式",
            ) from exc
        llm_class = HelloAgentsLLM

    try:
        llm = llm_class(
            model=settings.llm_model_id,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )
        amap = create_amap_mcp_runtime(
            AmapMCPConfig(api_key=settings.amap_maps_api_key),
            mcp_tool_class=mcp_tool_class,
        )
    except MCPIntegrationError:
        raise
    except Exception as exc:
        raise AgentRuntimeError(f"旅行 Agent 运行时初始化失败：{exc}") from exc

    return SharedAgentResources(llm=llm, amap=amap)


@lru_cache(maxsize=1)
def get_shared_agent_resources() -> SharedAgentResources:
    """Discover MCP tools once and reuse the resulting facade."""
    from ..config import get_settings

    return build_shared_agent_resources(get_settings())


def create_trip_planner(
    resources: SharedAgentResources | None = None,
    agent_class: Any | None = None,
) -> MultiAgentTripPlanner:
    """Create request-local Agents around shared LLM and MCP resources."""
    shared = resources or get_shared_agent_resources()
    return build_simple_agent_team(
        llm=shared.llm,
        amap_tool=shared.amap.tool,
        agent_class=agent_class,
    )


def clear_shared_agent_resources() -> None:
    """Clear the lazy singleton, mainly for configuration reloads and tests."""
    get_shared_agent_resources.cache_clear()


__all__ = [
    "AgentRuntimeError",
    "RuntimeSettings",
    "SharedAgentResources",
    "build_shared_agent_resources",
    "clear_shared_agent_resources",
    "create_trip_planner",
    "get_shared_agent_resources",
]
