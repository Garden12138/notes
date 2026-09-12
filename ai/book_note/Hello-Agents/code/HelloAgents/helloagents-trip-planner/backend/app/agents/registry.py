"""Role registry for the four-agent architecture introduced in section 13.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AgentRole:
    """Describe one Agent boundary without constructing an LLM client yet."""

    name: str
    display_name: str
    responsibility: str
    expected_inputs: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    external_capabilities: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_agent_registry() -> tuple[AgentRole, ...]:
    """Return the chapter's four specialized travel Agent roles."""
    return (
        AgentRole(
            name="attraction_search",
            display_name="景点搜索 Agent",
            responsibility="根据城市、日期和偏好检索候选景点",
            expected_inputs=("city", "preferences"),
            expected_outputs=("attractions",),
            external_capabilities=("amap_maps_text_search",),
        ),
        AgentRole(
            name="weather_query",
            display_name="天气查询 Agent",
            responsibility="查询旅行日期范围内的天气并给出出行提示",
            expected_inputs=("city", "start_date", "end_date"),
            expected_outputs=("weather_forecast",),
            external_capabilities=("amap_maps_weather",),
        ),
        AgentRole(
            name="hotel_recommendation",
            display_name="酒店推荐 Agent",
            responsibility="根据城市和住宿偏好筛选酒店",
            expected_inputs=("city", "accommodation"),
            expected_outputs=("hotels",),
            external_capabilities=("amap_maps_text_search",),
        ),
        AgentRole(
            name="trip_planning",
            display_name="行程规划 Agent",
            responsibility="整合景点、天气和酒店结果，生成每日行程与预算",
            expected_inputs=("request", "attractions", "weather", "hotels"),
            expected_outputs=("trip_plan", "budget", "map_points"),
            external_capabilities=(),
        ),
    )
