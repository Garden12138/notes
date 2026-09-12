"""Offline verification for the section 13.2 travel data models."""

from __future__ import annotations

from pydantic import BaseModel, ValidationError

from app.models import (
    Attraction,
    Budget,
    DayPlan,
    ErrorResponse,
    Hotel,
    Location,
    Meal,
    POIInfo,
    POISearchRequest,
    POISearchResponse,
    RouteInfo,
    RouteRequest,
    RouteResponse,
    TripPlan,
    TripPlanResponse,
    TripRequest,
    WeatherInfo,
    WeatherResponse,
)


SCHEMA_MODELS = (
    TripRequest,
    POISearchRequest,
    RouteRequest,
    Location,
    Attraction,
    Meal,
    Hotel,
    DayPlan,
    WeatherInfo,
    Budget,
    TripPlan,
    TripPlanResponse,
    POIInfo,
    POISearchResponse,
    RouteInfo,
    RouteResponse,
    WeatherResponse,
    ErrorResponse,
)


def expect_validation_error(
    model: type[BaseModel],
    **values: object,
) -> bool:
    """Return True only when a model rejects the supplied values."""
    try:
        model.model_validate(values)
    except ValidationError:
        return True
    raise AssertionError("测试数据本应触发 ValidationError")


def main() -> None:
    request = TripRequest(
        city="北京",
        start_date="2026-09-20",
        end_date="2026-09-21",
        travel_days=2,
        transportation="公共交通",
        accommodation="经济型酒店",
        preferences=["历史文化", "美食", "历史文化", ""],
        free_text_input="希望行程节奏适中",
    )
    location = Location.model_validate("116.397128,39.916527")
    attraction = Attraction(
        name="故宫博物院",
        address="北京市东城区景山前街 4 号",
        location=location,
        visit_duration=180,
        description="明清皇家宫殿建筑群",
        category="历史文化",
        rating=4.9,
        ticket_price=60,
    )
    hotel = Hotel(
        name="示例酒店",
        address="北京市东城区",
        location={"lng": 116.407, "lat": 39.904},
        price_range="400-600 元",
        rating="4.6",
        distance="距地铁站约 500 米",
        type="经济型",
        estimated_cost=500,
    )
    days = [
        DayPlan(
            date="2026-09-20",
            day_index=0,
            description="参观故宫并品尝北京菜",
            transportation="地铁 + 步行",
            accommodation="示例酒店",
            hotel=hotel,
            attractions=[attraction],
            meals=[
                Meal(
                    type="lunch",
                    name="北京菜午餐",
                    estimated_cost=150,
                )
            ],
        ),
        DayPlan(
            date="2026-09-21",
            day_index=1,
            description="自由活动并返程",
            transportation="公共交通",
            accommodation="无",
        ),
    ]
    weather = WeatherInfo(
        date="2026-09-20",
        day_weather="晴",
        night_weather="多云",
        day_temp="16°C",
        night_temp="8℃",
        wind_direction="北风",
        wind_power="3 级",
    )
    budget = Budget(
        total_attractions=60,
        total_hotels=500,
        total_meals=300,
        total_transportation=100,
    )
    plan = TripPlan(
        city=request.city,
        start_date=request.start_date,
        end_date=request.end_date,
        days=days,
        weather_info=[weather],
        overall_suggestions="提前预约景点，并根据天气调整步行时间。",
        budget=budget,
    )
    restored = TripPlan.model_validate_json(plan.model_dump_json())
    poi_request = POISearchRequest(keywords="博物馆", city="北京")
    route_request = RouteRequest(
        origin_address="故宫博物院",
        destination_address="景山公园",
        origin_city="北京",
        destination_city="北京",
    )
    poi = POIInfo(
        id="demo-poi-1",
        name="故宫博物院",
        type="博物馆",
        address=attraction.address,
        location=location,
    )
    route = RouteInfo(
        distance=1_200,
        duration=1_080,
        route_type=route_request.route_type,
        description="步行前往景山公园",
    )
    responses = (
        TripPlanResponse(success=True, data=plan),
        POISearchResponse(success=True, data=[poi]),
        RouteResponse(success=True, data=route),
        WeatherResponse(success=True, data=[weather]),
        ErrorResponse(message="示例错误", error_code="DEMO_ERROR"),
    )
    assert poi_request.citylimit is True
    assert all(response.message == "" for response in responses[:-1])

    failures = [
        expect_validation_error(
            Location,
            longitude=181,
            latitude=39.9,
        ),
        expect_validation_error(
            TripRequest,
            city="北京",
            start_date="2026-09-20",
            end_date="2026-09-21",
            travel_days=3,
            transportation="公共交通",
            accommodation="经济型酒店",
        ),
        expect_validation_error(
            Budget,
            total_attractions=60,
            total_hotels=500,
            total_meals=300,
            total_transportation=100,
            total=900,
        ),
    ]

    print("=== 13.2 旅行助手数据模型实践 ===")
    print(f"schema_models: {len(SCHEMA_MODELS)}")
    print(f"travel_days: {request.travel_days}")
    print(f"preferences: {', '.join(request.preferences)}")
    print(f"location: {location.longitude},{location.latitude}")
    print(f"weather_temperature: {weather.day_temp}")
    print(f"budget_total: {budget.total}")
    print(f"trip_days: {len(plan.days)}")
    print(f"json_round_trip: {restored == plan}")
    print(f"validation_failures_caught: {sum(failures)}")
    print("external_api_calls: 0")


if __name__ == "__main__":
    main()
