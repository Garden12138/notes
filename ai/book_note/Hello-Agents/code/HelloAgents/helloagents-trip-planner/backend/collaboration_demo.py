"""Offline verification of the section 13.3 four-agent workflow."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from app.agents import (
    MultiAgentTripPlanner,
    TripPlanningError,
    build_simple_agent_team,
)
from app.models import TripRequest


@dataclass
class ScriptedAgent:
    """Deterministic stand-in that records every delivered query."""

    name: str
    response: str
    queries: list[str] = field(default_factory=list)

    def run(self, input_text: str, **kwargs: Any) -> str:
        del kwargs
        self.queries.append(input_text)
        return self.response


class WiringAgent:
    """Minimal SimpleAgent-compatible class for dependency wiring checks."""

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
        del input_text, kwargs
        return "not used"


def attraction(name: str, longitude: float, latitude: float) -> dict[str, Any]:
    return {
        "name": name,
        "address": "示例地址",
        "location": {"longitude": longitude, "latitude": latitude},
        "visit_duration": 120,
        "description": "由测试工具返回的示例景点",
        "category": "历史文化",
        "ticket_price": 25,
    }


def meals(day_index: int) -> list[dict[str, Any]]:
    return [
        {
            "type": meal_type,
            "name": f"第 {day_index + 1} 天{label}",
            "estimated_cost": 40,
        }
        for meal_type, label in (
            ("breakfast", "早餐"),
            ("lunch", "午餐"),
            ("dinner", "晚餐"),
        )
    ]


def build_plan_response() -> str:
    hotel = {
        "name": "示例酒店",
        "address": "示例酒店地址",
        "location": {"longitude": 116.40, "latitude": 39.90},
        "price_range": "200-300 元",
        "rating": "4.5",
        "distance": "距景点约 1 公里",
        "type": "经济型酒店",
        "estimated_cost": 250,
    }
    plan = {
        "city": "北京",
        "start_date": "2026-09-20",
        "end_date": "2026-09-21",
        "days": [
            {
                "date": "2026-09-20",
                "day_index": 0,
                "description": "游览示例景点 A 和 B",
                "transportation": "公共交通",
                "accommodation": "经济型酒店",
                "hotel": hotel,
                "attractions": [
                    attraction("示例景点 A", 116.39, 39.91),
                    attraction("示例景点 B", 116.40, 39.92),
                ],
                "meals": meals(0),
            },
            {
                "date": "2026-09-21",
                "day_index": 1,
                "description": "游览示例景点 C 和 D",
                "transportation": "公共交通",
                "accommodation": "经济型酒店",
                "hotel": hotel,
                "attractions": [
                    attraction("示例景点 C", 116.41, 39.93),
                    attraction("示例景点 D", 116.42, 39.94),
                ],
                "meals": meals(1),
            },
        ],
        "weather_info": [
            {
                "date": "2026-09-20",
                "day_weather": "晴",
                "night_weather": "多云",
                "day_temp": 26,
                "night_temp": 17,
                "wind_direction": "北风",
                "wind_power": "2 级",
            },
            {
                "date": "2026-09-21",
                "day_weather": "多云",
                "night_weather": "晴",
                "day_temp": 24,
                "night_temp": 16,
                "wind_direction": "东风",
                "wind_power": "2 级",
            },
        ],
        "overall_suggestions": "根据天气调整户外游览时间。",
        "budget": {
            "total_attractions": 100,
            "total_hotels": 500,
            "total_meals": 240,
            "total_transportation": 120,
            "total": 960,
        },
    }
    return f"```json\n{json.dumps(plan, ensure_ascii=False)}\n```"


def main() -> None:
    request = TripRequest(
        city="北京",
        start_date="2026-09-20",
        end_date="2026-09-21",
        travel_days=2,
        transportation="公共交通",
        accommodation="经济型酒店",
        preferences=["历史文化", "博物馆"],
        free_text_input="行程不要太赶",
    )
    attraction_agent = ScriptedAgent(
        "景点搜索专家",
        '[{"name":"示例景点 A"},{"name":"示例景点 B"},'
        '{"name":"示例景点 C"},{"name":"示例景点 D"}]',
    )
    weather_agent = ScriptedAgent(
        "天气查询专家",
        '[{"date":"2026-09-20","weather":"晴"},'
        '{"date":"2026-09-21","weather":"多云"}]',
    )
    hotel_agent = ScriptedAgent(
        "酒店推荐专家",
        '[{"name":"示例酒店","estimated_cost":250}]',
    )
    planner_agent = ScriptedAgent("行程规划专家", build_plan_response())
    planner = MultiAgentTripPlanner(
        attraction_agent,
        weather_agent,
        hotel_agent,
        planner_agent,
    )
    plan = planner.plan_trip(request)

    planner_query = planner_agent.queries[0]
    forwarded = {
        "attractions": "示例景点 A" in planner_query,
        "weather": '"weather":"晴"' in planner_query,
        "hotels": "示例酒店" in planner_query,
    }
    call_order = [trace.step for trace in planner.last_trace]
    assert call_order == [
        "attraction_search",
        "weather_query",
        "hotel_recommendation",
        "trip_planning",
    ]
    assert all(forwarded.values())

    shared_tool = object()
    wired_team = build_simple_agent_team(
        llm=object(),
        amap_tool=shared_tool,
        agent_class=WiringAgent,
    )
    search_agents = (
        wired_team.attraction_agent,
        wired_team.weather_agent,
        wired_team.hotel_agent,
    )
    shared_tool_reused = all(
        agent.tools == [shared_tool] for agent in search_agents
    )
    planner_without_tools = wired_team.planner_agent.tools == []

    invalid_planner = MultiAgentTripPlanner(
        attraction_agent,
        weather_agent,
        hotel_agent,
        ScriptedAgent("行程规划专家", "没有 JSON"),
    )
    try:
        invalid_planner.plan_trip(request)
    except TripPlanningError:
        invalid_plan_rejected = True
    else:
        invalid_plan_rejected = False

    print("=== 13.3 多智能体协作实践 ===")
    print(
        "workflow_steps: "
        + " -> ".join([*call_order, "response_parsing"])
    )
    print(f"agent_calls: {len(planner.last_trace)}")
    print(f"attraction_context_forwarded: {forwarded['attractions']}")
    print(f"weather_context_forwarded: {forwarded['weather']}")
    print(f"hotel_context_forwarded: {forwarded['hotels']}")
    print(f"shared_tool_reused: {shared_tool_reused}")
    print(f"planner_without_tools: {planner_without_tools}")
    print(f"trip_city: {plan.city}")
    print(f"trip_days: {len(plan.days)}")
    print(f"budget_total: {plan.budget.total if plan.budget else 0}")
    print(f"invalid_plan_rejected: {invalid_plan_rejected}")
    print("external_api_calls: 0")


if __name__ == "__main__":
    main()
