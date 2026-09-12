"""Pydantic request and response models for the travel assistant."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


MealType = Literal["breakfast", "lunch", "dinner", "snack"]
RouteType = Literal["walking", "driving", "transit"]


def _iso_date(value: Any, field_name: str) -> str:
    """Normalize a date-like value to ``YYYY-MM-DD`` or raise clearly."""
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError as exc:
        raise ValueError(f"{field_name} 必须是 YYYY-MM-DD 格式") from exc


class SchemaModel(BaseModel):
    """Shared strictness for the public HTTP data contract."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class TripRequest(SchemaModel):
    """Travel planning request submitted by the front end."""

    city: str = Field(..., min_length=1, description="目的地城市")
    start_date: str = Field(..., description="开始日期 YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期 YYYY-MM-DD")
    travel_days: int = Field(..., ge=1, le=30, description="旅行天数")
    transportation: str = Field(..., min_length=1, description="交通方式")
    accommodation: str = Field(..., min_length=1, description="住宿偏好")
    preferences: list[str] = Field(
        default_factory=list,
        description="旅行偏好标签",
    )
    free_text_input: str | None = Field(default="", description="额外要求")

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
        json_schema_extra={
            "example": {
                "city": "北京",
                "start_date": "2026-09-20",
                "end_date": "2026-09-22",
                "travel_days": 3,
                "transportation": "公共交通",
                "accommodation": "经济型酒店",
                "preferences": ["历史文化", "美食"],
                "free_text_input": "希望多安排博物馆",
            }
        },
    )

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def validate_dates(cls, value: Any, info: Any) -> str:
        return _iso_date(value, info.field_name)

    @field_validator("preferences")
    @classmethod
    def normalize_preferences(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in values:
            item = value.strip()
            if item and item not in normalized:
                normalized.append(item)
        return normalized

    @model_validator(mode="after")
    def validate_date_range(self) -> "TripRequest":
        start = date.fromisoformat(self.start_date)
        end = date.fromisoformat(self.end_date)
        if end < start:
            raise ValueError("end_date 不能早于 start_date")
        expected_days = (end - start).days + 1
        if self.travel_days != expected_days:
            raise ValueError(
                f"travel_days 应为 {expected_days}，"
                f"当前值为 {self.travel_days}"
            )
        return self


class POISearchRequest(SchemaModel):
    """Point-of-interest search request."""

    keywords: str = Field(..., min_length=1, description="搜索关键词")
    city: str = Field(..., min_length=1, description="城市")
    citylimit: bool = Field(default=True, description="是否限制在城市范围内")


class RouteRequest(SchemaModel):
    """Route planning request between two addresses."""

    origin_address: str = Field(..., min_length=1, description="起点地址")
    destination_address: str = Field(..., min_length=1, description="终点地址")
    origin_city: str | None = Field(default=None, description="起点城市")
    destination_city: str | None = Field(default=None, description="终点城市")
    route_type: RouteType = Field(default="walking", description="路线类型")


class Location(SchemaModel):
    """Geographic longitude and latitude."""

    longitude: float = Field(..., ge=-180, le=180, description="经度")
    latitude: float = Field(..., ge=-90, le=90, description="纬度")

    @model_validator(mode="before")
    @classmethod
    def normalize_external_location(cls, value: Any) -> Any:
        """Accept Amap strings and common longitude/latitude aliases."""
        if isinstance(value, str):
            parts = [
                part.strip()
                for part in value.replace("，", ",").split(",")
            ]
            if len(parts) != 2 or not all(parts):
                raise ValueError("位置字符串必须是 '经度,纬度'")
            return {"longitude": parts[0], "latitude": parts[1]}
        if isinstance(value, dict):
            normalized = dict(value)
            if "longitude" not in normalized:
                normalized["longitude"] = normalized.get(
                    "lng",
                    normalized.get("lon"),
                )
            if "latitude" not in normalized:
                normalized["latitude"] = normalized.get("lat")
            normalized.pop("lng", None)
            normalized.pop("lon", None)
            normalized.pop("lat", None)
            return normalized
        return value


class Attraction(SchemaModel):
    """Attraction information used in one day plan."""

    name: str = Field(..., min_length=1, description="景点名称")
    address: str = Field(..., min_length=1, description="地址")
    location: Location = Field(..., description="经纬度坐标")
    visit_duration: int = Field(..., gt=0, description="建议游览时间（分钟）")
    description: str = Field(..., min_length=1, description="景点描述")
    category: str | None = Field(default="景点", description="景点类别")
    rating: float | None = Field(default=None, ge=0, le=5, description="评分")
    photos: list[str] = Field(default_factory=list, description="图片 URL 列表")
    poi_id: str = Field(default="", description="POI ID")
    image_url: str | None = Field(default=None, description="主图片 URL")
    ticket_price: int = Field(default=0, ge=0, description="门票价格（元）")


class Meal(SchemaModel):
    """Meal information in a day plan."""

    type: MealType = Field(..., description="餐饮类型")
    name: str = Field(..., min_length=1, description="餐饮名称")
    address: str | None = Field(default=None, description="地址")
    location: Location | None = Field(default=None, description="经纬度坐标")
    description: str | None = Field(default=None, description="描述")
    estimated_cost: int = Field(default=0, ge=0, description="预估费用（元）")


class Hotel(SchemaModel):
    """Hotel recommendation for an overnight stay."""

    name: str = Field(..., min_length=1, description="酒店名称")
    address: str = Field(default="", description="酒店地址")
    location: Location | None = Field(default=None, description="酒店位置")
    price_range: str = Field(default="", description="价格范围")
    rating: str = Field(default="", description="评分")
    distance: str = Field(default="", description="距离景点距离")
    type: str = Field(default="", description="酒店类型")
    estimated_cost: int = Field(default=0, ge=0, description="每晚预估费用")


class DayPlan(SchemaModel):
    """One day's itinerary."""

    date: str = Field(..., description="日期 YYYY-MM-DD")
    day_index: int = Field(..., ge=0, description="第几天（从 0 开始）")
    description: str = Field(..., min_length=1, description="当日行程描述")
    transportation: str = Field(..., min_length=1, description="交通方式")
    accommodation: str = Field(..., min_length=1, description="住宿安排")
    hotel: Hotel | None = Field(default=None, description="推荐酒店")
    attractions: list[Attraction] = Field(
        default_factory=list,
        description="景点列表",
    )
    meals: list[Meal] = Field(default_factory=list, description="餐饮列表")

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, value: Any) -> str:
        return _iso_date(value, "date")


class WeatherInfo(SchemaModel):
    """Weather information normalized from an external service."""

    date: str = Field(..., description="日期 YYYY-MM-DD")
    day_weather: str = Field(default="", description="白天天气")
    night_weather: str = Field(default="", description="夜间天气")
    day_temp: int = Field(default=0, description="白天温度（摄氏度）")
    night_temp: int = Field(default=0, description="夜间温度（摄氏度）")
    wind_direction: str = Field(default="", description="风向")
    wind_power: str = Field(default="", description="风力")

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, value: Any) -> str:
        return _iso_date(value, "date")

    @field_validator("day_temp", "night_temp", mode="before")
    @classmethod
    def parse_temperature(cls, value: Any) -> int:
        """Strip temperature units; keep the chapter's invalid-to-zero fallback."""
        if isinstance(value, str):
            normalized = (
                value.replace("°C", "")
                .replace("℃", "")
                .replace("°", "")
                .strip()
            )
            try:
                return int(normalized)
            except ValueError:
                return 0
        return int(value)


class Budget(SchemaModel):
    """Travel cost breakdown with a checked total."""

    total_attractions: int = Field(default=0, ge=0, description="景点门票")
    total_hotels: int = Field(default=0, ge=0, description="酒店")
    total_meals: int = Field(default=0, ge=0, description="餐饮")
    total_transportation: int = Field(default=0, ge=0, description="交通")
    total: int = Field(default=0, ge=0, description="总费用")

    @model_validator(mode="after")
    def validate_total(self) -> "Budget":
        expected = (
            self.total_attractions
            + self.total_hotels
            + self.total_meals
            + self.total_transportation
        )
        if self.total == 0:
            object.__setattr__(self, "total", expected)
        elif self.total != expected:
            raise ValueError(f"total 应为各项之和 {expected}")
        return self


class TripPlan(SchemaModel):
    """Complete travel plan returned to the front end."""

    city: str = Field(..., min_length=1, description="目的地城市")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    days: list[DayPlan] = Field(..., min_length=1, description="每日行程")
    weather_info: list[WeatherInfo] = Field(
        default_factory=list,
        description="天气信息",
    )
    overall_suggestions: str = Field(..., min_length=1, description="总体建议")
    budget: Budget | None = Field(default=None, description="预算信息")

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def validate_dates(cls, value: Any, info: Any) -> str:
        return _iso_date(value, info.field_name)

    @model_validator(mode="after")
    def validate_schedule(self) -> "TripPlan":
        start = date.fromisoformat(self.start_date)
        end = date.fromisoformat(self.end_date)
        if end < start:
            raise ValueError("end_date 不能早于 start_date")

        expected_days = (end - start).days + 1
        if len(self.days) != expected_days:
            raise ValueError(f"days 应包含 {expected_days} 天的完整行程")

        seen_dates: set[str] = set()
        for day in self.days:
            current = date.fromisoformat(day.date)
            if current < start or current > end:
                raise ValueError(f"行程日期 {day.date} 超出旅行范围")
            if day.date in seen_dates:
                raise ValueError(f"行程日期 {day.date} 重复")
            expected_index = (current - start).days
            if day.day_index != expected_index:
                raise ValueError(
                    f"{day.date} 的 day_index 应为 {expected_index}"
                )
            seen_dates.add(day.date)

        weather_dates: set[str] = set()
        for weather in self.weather_info:
            current = date.fromisoformat(weather.date)
            if current < start or current > end:
                raise ValueError(f"天气日期 {weather.date} 超出旅行范围")
            if weather.date in weather_dates:
                raise ValueError(f"天气日期 {weather.date} 重复")
            weather_dates.add(weather.date)
        return self


class TripPlanResponse(SchemaModel):
    """Unified travel-planning API response."""

    success: bool = Field(..., description="是否成功")
    message: str = Field(default="", description="消息")
    data: TripPlan | None = Field(default=None, description="旅行计划")

    @model_validator(mode="after")
    def require_success_data(self) -> "TripPlanResponse":
        if self.success and self.data is None:
            raise ValueError("success=True 时必须提供 data")
        return self


class POIInfo(SchemaModel):
    """Normalized point-of-interest response."""

    id: str = Field(..., min_length=1, description="POI ID")
    name: str = Field(..., min_length=1, description="名称")
    type: str = Field(..., min_length=1, description="类型")
    address: str = Field(..., description="地址")
    location: Location = Field(..., description="经纬度坐标")
    tel: str | None = Field(default=None, description="电话")


class POISearchResponse(SchemaModel):
    """Unified POI search response."""

    success: bool = Field(..., description="是否成功")
    message: str = Field(default="", description="消息")
    data: list[POIInfo] = Field(default_factory=list, description="POI 列表")


class RouteInfo(SchemaModel):
    """Normalized route information."""

    distance: float = Field(..., ge=0, description="距离（米）")
    duration: int = Field(..., ge=0, description="时间（秒）")
    route_type: RouteType = Field(..., description="路线类型")
    description: str = Field(..., description="路线描述")


class RouteResponse(SchemaModel):
    """Unified route-planning response."""

    success: bool = Field(..., description="是否成功")
    message: str = Field(default="", description="消息")
    data: RouteInfo | None = Field(default=None, description="路线信息")


class WeatherResponse(SchemaModel):
    """Unified weather-query response."""

    success: bool = Field(..., description="是否成功")
    message: str = Field(default="", description="消息")
    data: list[WeatherInfo] = Field(
        default_factory=list,
        description="天气信息",
    )


class ErrorResponse(SchemaModel):
    """Common error payload."""

    success: Literal[False] = Field(default=False, description="是否成功")
    message: str = Field(..., min_length=1, description="错误消息")
    error_code: str | None = Field(default=None, description="错误代码")
