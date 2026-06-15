"""Weather assistant tool implementations.

Domain projects: replace these mock implementations with real API calls
(e.g., OpenWeatherMap, QWeather, wttr.in).
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict


# Mock weather data — replace with real API calls
_MOCK_WEATHER: Dict[str, Dict[str, Any]] = {
    "beijing": {"temp": 28, "condition": "晴", "humidity": 45, "wind": "北风3级"},
    "shanghai": {"temp": 32, "condition": "多云", "humidity": 65, "wind": "东南风2级"},
    "guangzhou": {"temp": 35, "condition": "雷阵雨", "humidity": 80, "wind": "南风4级"},
    "shenzhen": {"temp": 34, "condition": "阵雨", "humidity": 78, "wind": "西南风3级"},
    "hangzhou": {"temp": 30, "condition": "晴转多云", "humidity": 55, "wind": "东风2级"},
    "chengdu": {"temp": 26, "condition": "阴", "humidity": 70, "wind": "微风"},
}


def query_weather(args: Dict[str, Any]) -> str:
    """Query current weather for a city.

    Args:
        args: {"city": "城市名称"}

    Returns:
        JSON string with weather data.
    """
    city = str(args.get("city") or "unknown").strip()
    city_lower = city.lower()
    data = _MOCK_WEATHER.get(city_lower, {
        "temp": 25,
        "condition": "未知",
        "humidity": 50,
        "wind": "微风",
    })
    return json.dumps({
        "city": city,
        "temperature": f"{data['temp']}°C",
        "condition": data["condition"],
        "humidity": f"{data['humidity']}%",
        "wind": data["wind"],
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }, ensure_ascii=False)


def query_forecast(args: Dict[str, Any]) -> str:
    """Query weather forecast for a city.

    Args:
        args: {"city": "城市名称", "days": 3}

    Returns:
        JSON string with forecast data.
    """
    city = str(args.get("city") or "unknown").strip()
    days = int(args.get("days") or 3)
    days = max(1, min(days, 7))

    forecast = []
    base_temp = _MOCK_WEATHER.get(city.lower(), {}).get("temp", 25)
    conditions = ["晴", "多云", "阵雨", "雷阵雨", "阴", "小雨", "晴转多云"]
    for i in range(days):
        forecast.append({
            "date": f"2026-06-{15 + i}",
            "temp_high": base_temp + i,
            "temp_low": base_temp - 6 + i,
            "condition": conditions[i % len(conditions)],
        })

    return json.dumps({
        "city": city,
        "forecast": forecast,
    }, ensure_ascii=False)


# Tool spec definitions — used by DomainAgentExecutionService for registration
TOOL_SPECS: Dict[str, Dict[str, Any]] = {
    "query_weather": {
        "name": "query_weather",
        "description": "查询指定城市的当前天气信息。参数：city (城市名称)",
        "handler": query_weather,
    },
    "query_forecast": {
        "name": "query_forecast",
        "description": "查询指定城市的天气预报。参数：city (城市名称), days (预报天数，默认3天)",
        "handler": query_forecast,
    },
}
