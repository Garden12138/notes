#!/usr/bin/env python3
"""Weather query MCP server from chapter 10.5."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from urllib.parse import quote

import requests

from hello_agents.protocols import MCPServer


SERVER_NAME = "weather-server"
SERVER_VERSION = "1.0.0"
DEFAULT_TIMEOUT = 10.0

CITY_MAP = {
    "北京": "Beijing",
    "上海": "Shanghai",
    "广州": "Guangzhou",
    "深圳": "Shenzhen",
    "杭州": "Hangzhou",
    "成都": "Chengdu",
    "重庆": "Chongqing",
    "武汉": "Wuhan",
    "西安": "Xi'an",
    "南京": "Nanjing",
    "天津": "Tianjin",
    "苏州": "Suzhou",
}


class WeatherServiceError(RuntimeError):
    """Represent a predictable upstream or response-shape failure."""


def _normalize_city(city: str) -> str:
    if not isinstance(city, str):
        raise WeatherServiceError("城市名称必须是字符串")
    normalized = city.strip()
    if not normalized:
        raise WeatherServiceError("城市名称不能为空")
    if len(normalized) > 80:
        raise WeatherServiceError("城市名称过长")
    return normalized


def _fixture_weather(city: str, fixture_file: str) -> Dict[str, Any]:
    """Read deterministic data used only by the local acceptance demo."""
    path = Path(fixture_file).expanduser().resolve()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WeatherServiceError(f"无法读取天气测试数据: {exc}") from exc

    record = payload.get(city) if isinstance(payload, dict) else None
    if not isinstance(record, dict):
        raise WeatherServiceError(f"测试数据中没有城市: {city}")
    return {**record, "city": city}


def _description(current: Dict[str, Any]) -> str:
    localized = current.get("lang_zh")
    if isinstance(localized, list) and localized:
        first = localized[0]
        if isinstance(first, dict) and first.get("value"):
            return str(first["value"])

    descriptions = current.get("weatherDesc")
    if isinstance(descriptions, list) and descriptions:
        first = descriptions[0]
        if isinstance(first, dict) and first.get("value"):
            return str(first["value"])
    return "未知"


def _number(current: Dict[str, Any], key: str, value_type: type) -> Any:
    try:
        return value_type(current[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise WeatherServiceError(f"天气响应缺少有效字段: {key}") from exc


def get_weather_data(city: str) -> Dict[str, Any]:
    """Get normalized current weather data from wttr.in."""
    normalized_city = _normalize_city(city)
    fixture_file = os.getenv("WEATHER_MCP_FIXTURE_FILE")
    if fixture_file:
        return _fixture_weather(normalized_city, fixture_file)

    timeout_text = os.getenv("WEATHER_MCP_TIMEOUT", str(DEFAULT_TIMEOUT))
    try:
        timeout = float(timeout_text)
    except ValueError as exc:
        raise WeatherServiceError("WEATHER_MCP_TIMEOUT 必须是数字") from exc
    if timeout <= 0:
        raise WeatherServiceError("WEATHER_MCP_TIMEOUT 必须大于 0")

    city_en = quote(CITY_MAP.get(normalized_city, normalized_city), safe="")
    try:
        response = requests.get(
            f"https://wttr.in/{city_en}",
            params={"format": "j1", "lang": "zh"},
            headers={
                "User-Agent": f"HelloAgents-{SERVER_NAME}/{SERVER_VERSION}"
            },
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise WeatherServiceError(f"天气服务请求失败: {exc}") from exc
    except ValueError as exc:
        raise WeatherServiceError("天气服务返回了无效 JSON") from exc

    # wttr.in has returned both the documented top-level shape and a
    # transient {"data": {...}} wrapper, so accept either without weakening
    # the field validation below.
    if not isinstance(payload, dict):
        raise WeatherServiceError("天气响应的 JSON 结构无效")
    weather_payload = payload.get("data", payload)
    if not isinstance(weather_payload, dict):
        raise WeatherServiceError("天气响应的 JSON 结构无效")
    conditions = weather_payload.get("current_condition")
    if not isinstance(conditions, list) or not conditions:
        raise WeatherServiceError("天气响应缺少 current_condition")
    current = conditions[0]
    if not isinstance(current, dict):
        raise WeatherServiceError("天气响应中的 current_condition 无效")

    return {
        "city": normalized_city,
        "temperature": _number(current, "temp_C", float),
        "feels_like": _number(current, "FeelsLikeC", float),
        "humidity": _number(current, "humidity", int),
        "condition": _description(current),
        "wind_speed": round(
            _number(current, "windspeedKmph", float) / 3.6,
            1,
        ),
        "visibility": _number(current, "visibility", float),
        "timestamp": (
            datetime.now().astimezone().isoformat(timespec="seconds")
        ),
    }


def _as_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def get_weather(city: str) -> str:
    """获取指定城市的当前天气。"""
    try:
        return _as_json(get_weather_data(city))
    except WeatherServiceError as exc:
        normalized = city.strip() if isinstance(city, str) else str(city)
        return _as_json({"error": str(exc), "city": normalized})


def list_supported_cities() -> str:
    """列出服务器内置中文名称映射的城市。"""
    return _as_json({"cities": list(CITY_MAP), "count": len(CITY_MAP)})


def get_server_info() -> str:
    """获取天气 MCP 服务器的名称、版本和工具列表。"""
    return _as_json(
        {
            "name": "Weather MCP Server",
            "version": SERVER_VERSION,
            "upstream": "wttr.in",
            "tools": [
                "get_weather",
                "list_supported_cities",
                "get_server_info",
            ],
        }
    )


weather_server = MCPServer(
    name=SERVER_NAME,
    description="基于 wttr.in 的天气查询服务",
)
weather_server.add_tool(get_weather)
weather_server.add_tool(list_supported_cities)
weather_server.add_tool(get_server_info)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行天气 MCP Server")
    parser.add_argument(
        "--transport",
        choices=("stdio", "http"),
        default=os.getenv("MCP_TRANSPORT", "stdio"),
    )
    parser.add_argument("--host", default=os.getenv("MCP_HOST", "127.0.0.1"))
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8081")),
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.transport == "stdio":
        weather_server.run(transport="stdio")
        return
    weather_server.run(transport="http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
