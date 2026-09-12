"""Offline verification for section 13.4 MCP and image integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.agent_runtime import (
    build_shared_agent_resources,
    create_trip_planner,
)
from app.services.mcp_integration import (
    AmapMCPConfig,
    MCPIntegrationError,
    create_amap_mcp_runtime,
)
from app.services.unsplash import UnsplashService, enrich_trip_plan_images


@dataclass(frozen=True)
class FakeExpandedTool:
    name: str


class FakeMCPTool:
    """Record MCP construction without starting a child process."""

    advertised_names = (
        "amap_maps_text_search",
        "amap_maps_weather",
        "amap_maps_geo",
    )
    latest_config: dict[str, Any] = {}

    def __init__(self, **kwargs: Any) -> None:
        type(self).latest_config = kwargs

    def get_expanded_tools(self) -> list[FakeExpandedTool]:
        return [FakeExpandedTool(name) for name in self.advertised_names]


class IncompleteFakeMCPTool(FakeMCPTool):
    advertised_names = ("amap_maps_text_search",)


class FakeAgent:
    """Minimal constructor surface used by build_simple_agent_team."""

    def __init__(
        self,
        name: str,
        llm: Any,
        system_prompt: str,
        enable_tool_calling: bool = True,
    ) -> None:
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        self.enable_tool_calling = enable_tool_calling
        self.tools: list[Any] = []

    def add_tool(self, tool: Any) -> None:
        self.tools.append(tool)

    def run(self, input_text: str, **kwargs: Any) -> str:
        raise AssertionError("装配验证不应执行 Agent")


class FakeLLM:
    latest_config: dict[str, str] = {}

    def __init__(self, **kwargs: str) -> None:
        type(self).latest_config = kwargs


@dataclass(frozen=True)
class FakeSettings:
    llm_api_key: str = "offline-llm-key"
    llm_model_id: str = "offline-model"
    llm_base_url: str = "https://llm.example/v1"
    amap_maps_api_key: str = "offline-amap-key"


class FakeHTTPResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return {
            "results": [
                {
                    "id": "offline-photo",
                    "urls": {
                        "regular": "https://images.example/offline.jpg",
                        "thumb": "https://images.example/offline-thumb.jpg",
                    },
                    "alt_description": "offline verification image",
                    "user": {"name": "Test Photographer"},
                }
            ]
        }


@dataclass
class FakeAttraction:
    name: str
    image_url: str | None = None


@dataclass
class FakeDayPlan:
    attractions: list[FakeAttraction]


@dataclass
class FakeTripPlan:
    city: str
    days: list[FakeDayPlan]


def main() -> None:
    config = AmapMCPConfig(api_key="offline-amap-key")
    resources = build_shared_agent_resources(
        FakeSettings(),
        llm_class=FakeLLM,
        mcp_tool_class=FakeMCPTool,
    )
    runtime = resources.amap
    recorded = FakeMCPTool.latest_config
    assert recorded["server_command"] == ["uvx", "amap-mcp-server"]
    assert recorded["env"] == {"AMAP_MAPS_API_KEY": "offline-amap-key"}
    assert recorded["auto_expand"] is True
    assert "offline-amap-key" not in repr(config)

    planner = create_trip_planner(
        resources=resources,
        agent_class=FakeAgent,
    )
    retrieval_agents = (
        planner.attraction_agent,
        planner.weather_agent,
        planner.hotel_agent,
    )
    shared_tool = all(
        agent.tools == [runtime.tool] for agent in retrieval_agents
    )
    planner_without_tools = planner.planner_agent.tools == []
    assert shared_tool
    assert planner_without_tools

    http_calls: list[dict[str, Any]] = []

    def fake_get(url: str, **kwargs: Any) -> FakeHTTPResponse:
        http_calls.append({"url": url, **kwargs})
        return FakeHTTPResponse()

    image_service = UnsplashService(
        access_key="offline-unsplash-key",
        http_get=fake_get,
    )
    trip_plan = FakeTripPlan(
        city="北京",
        days=[FakeDayPlan(attractions=[FakeAttraction(name="故宫")])],
    )
    enrich_trip_plan_images(trip_plan, image_service)  # type: ignore[arg-type]
    assert len(http_calls) == 1
    assert http_calls[0]["params"]["query"] == "故宫 北京"
    assert http_calls[0]["params"]["per_page"] == 1
    assert trip_plan.days[0].attractions[0].image_url is not None

    missing_tools_rejected = False
    try:
        create_amap_mcp_runtime(
            config,
            mcp_tool_class=IncompleteFakeMCPTool,
        )
    except MCPIntegrationError:
        missing_tools_rejected = True
    assert missing_tools_rejected

    print("=== 13.4 MCP 工具集成实践 ===")
    print(f"server_command: {' '.join(config.server_command)}")
    print(f"api_key_forwarded: {bool(recorded['env'])}")
    print(f"secret_redacted: {'offline-amap-key' not in repr(config)}")
    print(f"auto_expand: {recorded['auto_expand']}")
    print(f"expanded_tools: {', '.join(runtime.expanded_tool_names)}")
    print("required_tools_ready: True")
    print(f"shared_amap_tool: {shared_tool}")
    print(f"planner_without_tools: {planner_without_tools}")
    print(f"unsplash_query: {http_calls[0]['params']['query']}")
    print("unsplash_image_attached: True")
    print(f"missing_tools_rejected: {missing_tools_rejected}")
    print("mcp_server_processes_started: 0")
    print("external_api_calls: 0")


if __name__ == "__main__":
    main()
