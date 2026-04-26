"""Shared weather service backed by Open-Meteo."""

from __future__ import annotations

import asyncio
import copy
import logging
import re
import threading
import time
from typing import Any, Dict, Optional

import httpx
try:
    from agent_framework.card_schemas import WEATHER_CARD_SCHEMA
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_framework.card_schemas import WEATHER_CARD_SCHEMA

logger = logging.getLogger(__name__)


CITY_COORDS = {
    "北京": {"lat": 39.90, "lon": 116.41},
    "上海": {"lat": 31.23, "lon": 121.47},
    "广州": {"lat": 23.13, "lon": 113.26},
    "深圳": {"lat": 22.54, "lon": 114.06},
    "成都": {"lat": 30.67, "lon": 104.07},
    "杭州": {"lat": 30.27, "lon": 120.15},
    "西安": {"lat": 34.34, "lon": 108.94},
    "重庆": {"lat": 29.56, "lon": 106.55},
    "南京": {"lat": 32.06, "lon": 118.79},
    "武汉": {"lat": 30.59, "lon": 114.31},
    "天津": {"lat": 39.13, "lon": 117.20},
    "苏州": {"lat": 31.30, "lon": 120.58},
    "郑州": {"lat": 34.76, "lon": 113.75},
    "长沙": {"lat": 28.23, "lon": 112.94},
    "青岛": {"lat": 36.07, "lon": 120.38},
    "沈阳": {"lat": 41.81, "lon": 123.43},
    "大连": {"lat": 38.92, "lon": 121.63},
    "厦门": {"lat": 24.48, "lon": 118.09},
    "昆明": {"lat": 25.04, "lon": 102.71},
    "哈尔滨": {"lat": 45.80, "lon": 126.53},
    "长春": {"lat": 43.88, "lon": 125.32},
    "福州": {"lat": 26.08, "lon": 119.30},
    "南昌": {"lat": 28.68, "lon": 115.86},
    "贵阳": {"lat": 26.65, "lon": 106.63},
    "太原": {"lat": 37.87, "lon": 112.55},
    "济南": {"lat": 36.65, "lon": 117.12},
    "南宁": {"lat": 22.82, "lon": 108.37},
    "合肥": {"lat": 31.82, "lon": 117.23},
    "石家庄": {"lat": 38.04, "lon": 114.51},
    "兰州": {"lat": 36.06, "lon": 103.75},
    "乌鲁木齐": {"lat": 43.83, "lon": 87.62},
    "银川": {"lat": 38.47, "lon": 106.23},
    "西宁": {"lat": 36.62, "lon": 101.78},
    "拉萨": {"lat": 29.65, "lon": 91.10},
    "呼和浩特": {"lat": 40.84, "lon": 111.75},
    "海口": {"lat": 20.04, "lon": 110.35},
    "三亚": {"lat": 18.25, "lon": 109.51},
    "东莞": {"lat": 23.04, "lon": 113.75},
    "佛山": {"lat": 23.02, "lon": 113.12},
    "宁波": {"lat": 29.87, "lon": 121.55},
    "温州": {"lat": 28.00, "lon": 120.69},
    "无锡": {"lat": 31.49, "lon": 120.30},
    "常州": {"lat": 31.81, "lon": 119.97},
    "徐州": {"lat": 34.20, "lon": 117.29},
    "扬州": {"lat": 32.39, "lon": 119.43},
    "镇江": {"lat": 32.20, "lon": 119.45},
    "绍兴": {"lat": 30.00, "lon": 120.58},
    "嘉兴": {"lat": 30.75, "lon": 120.76},
    "湖州": {"lat": 30.87, "lon": 120.09},
    "金华": {"lat": 29.08, "lon": 119.65},
    "台州": {"lat": 28.65, "lon": 121.43},
    "丽水": {"lat": 28.46, "lon": 119.92},
    "舟山": {"lat": 29.98, "lon": 122.11},
    "衢州": {"lat": 28.97, "lon": 118.87},
    "芜湖": {"lat": 31.33, "lon": 118.38},
    "蚌埠": {"lat": 32.92, "lon": 117.39},
    "淮南": {"lat": 32.63, "lon": 117.00},
    "马鞍山": {"lat": 31.67, "lon": 118.51},
    "安庆": {"lat": 30.54, "lon": 117.05},
    "宿州": {"lat": 33.65, "lon": 116.96},
    "阜阳": {"lat": 32.89, "lon": 115.81},
    "黄山": {"lat": 29.72, "lon": 118.34},
    "滁州": {"lat": 32.30, "lon": 118.32},
    "池州": {"lat": 30.66, "lon": 117.49},
    "宣城": {"lat": 30.94, "lon": 118.87},
}

CITY_ALIASES = {
    "beijing": "北京",
    "shanghai": "上海",
    "guangzhou": "广州",
    "shenzhen": "深圳",
    "hangzhou": "杭州",
    "ningbo": "宁波",
    "zhoushan": "舟山",
}


class WeatherService:
    """Open-Meteo weather service with simple city extraction."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    WEATHER_CODES = {
        0: "晴",
        1: "晴间多云",
        2: "多云",
        3: "阴",
        45: "雾",
        48: "霜雾",
        51: "小毛毛雨",
        53: "中毛毛雨",
        55: "大毛毛雨",
        61: "小雨",
        63: "中雨",
        65: "大雨",
        71: "小雪",
        73: "中雪",
        75: "大雪",
        80: "阵雨",
        81: "强阵雨",
        82: "暴雨",
        95: "雷暴",
        96: "雷暴伴小冰雹",
        99: "雷暴伴大冰雹",
    }

    def __init__(self, timeout_seconds: float = 10.0, cache_ttl_seconds: float = 300.0):
        self.timeout_seconds = timeout_seconds
        self.cache_ttl_seconds = cache_ttl_seconds
        self._weather_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = threading.Lock()

    def is_weather_query(self, query: str) -> bool:
        lowered = query.lower()
        weather_keywords = ("天气", "气温", "温度", "下雨", "降雨", "weather", "forecast")
        return any(keyword in query or keyword in lowered for keyword in weather_keywords)

    def extract_city(self, query: str) -> Optional[str]:
        normalized = query.strip()
        lowered = normalized.lower()

        for alias, city in CITY_ALIASES.items():
            if alias in lowered:
                return city

        for city in sorted(CITY_COORDS.keys(), key=len, reverse=True):
            if city in normalized or f"{city}市" in normalized:
                return city

        return None

    async def get_weather_by_city(self, city: str) -> Dict[str, Any]:
        coords = CITY_COORDS.get(city)
        if not coords:
            raise ValueError(f"暂不支持查询城市: {city}")

        cached_weather = self._get_cached_weather(city)
        if cached_weather is not None:
            return cached_weather

        payload = await self._fetch_weather_payload(city, coords)
        weather = self._parse_weather(payload, city)
        self._store_cached_weather(city, weather)
        return copy.deepcopy(weather)

    async def _fetch_weather_payload(self, city: str, coords: Dict[str, float]) -> Dict[str, Any]:
        """Fetch raw weather payload from the upstream API."""
        params = {
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "current_weather": "true",
            "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "Asia/Shanghai",
            "forecast_days": 3,
        }

        timeout = httpx.Timeout(self.timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()

    async def get_weather_text_for_query(self, query: str) -> str:
        city = self.extract_city(query)
        if not city:
            return f"关于'{query}'的天气信息：未识别到明确城市，请直接提供城市名，例如“舟山天气”。"

        try:
            weather = await self.get_weather_by_city(city)
            return self.format_weather(weather)
        except ValueError as exc:
            return f"关于'{query}'的天气信息：{exc}"
        except httpx.HTTPError as exc:
            logger.warning("[WeatherService] 天气 API 请求失败 city=%s error=%s", city, exc)
            return f"关于'{query}'的天气信息：天气服务暂时不可用，请稍后重试。"
        except Exception as exc:
            logger.exception("[WeatherService] 未预期错误 city=%s", city)
            return f"关于'{query}'的天气信息：查询失败（{exc}）。"

    def get_weather_text_for_query_sync(self, query: str) -> str:
        return self._run_async_sync(self.get_weather_text_for_query(query))

    def clear_cache(self) -> None:
        """Clear the in-memory weather cache."""
        with self._cache_lock:
            self._weather_cache.clear()

    def format_weather(self, data: Dict[str, Any]) -> str:
        current = data["current"]
        forecast = data.get("forecast", [])
        lines = [
            f"天气查询结果（{data['city']}）",
            f"当前天气：{current['weather']}",
            f"当前气温：{current['temperature']}",
            f"当前风速：{current['wind_speed']}",
            f"当前风向：{current['wind_direction']}",
            "未来三天预报：",
        ]

        for day in forecast[:3]:
            display_date = day["date"].replace("-", "/")
            lines.append(
                f"{display_date}：{day['weather']}，气温 {day['min_temp']} 至 {day['max_temp']}，降水 {day['precipitation']}"
            )

        if not forecast:
            lines.append("暂无未来天气数据。")

        return "\n".join(lines)

    def build_weather_card(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build structured card payload from parsed weather data."""
        return {
            "kind": "weather",
            "schema": WEATHER_CARD_SCHEMA,
            "city": data["city"],
            "current": {
                "weather": data["current"]["weather"],
                "temperature": data["current"]["temperature"],
                "wind_speed": data["current"]["wind_speed"],
                "wind_direction": data["current"]["wind_direction"],
            },
            "forecast": [
                {
                    "date": str(day["date"]).replace("-", "/"),
                    "weather": day["weather"],
                    "min_temp": day["min_temp"],
                    "max_temp": day["max_temp"],
                    "precipitation": day["precipitation"],
                }
                for day in data.get("forecast", [])[:3]
            ],
        }

    def build_weather_card_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse a formatted weather text block back into structured card data."""
        if not text or not text.startswith("天气查询结果（"):
            return None

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) < 2:
            return None

        title_match = re.match(r"^天气查询结果（(.+?)）$", lines[0])
        if not title_match:
            return None

        card: Dict[str, Any] = {
            "kind": "weather",
            "schema": WEATHER_CARD_SCHEMA,
            "city": title_match.group(1),
            "current": {},
            "forecast": [],
        }

        for line in lines[1:]:
            if line.startswith("当前天气："):
                card["current"]["weather"] = line.split("：", 1)[1]
            elif line.startswith("当前气温："):
                card["current"]["temperature"] = line.split("：", 1)[1]
            elif line.startswith("当前风速："):
                card["current"]["wind_speed"] = line.split("：", 1)[1]
            elif line.startswith("当前风向："):
                card["current"]["wind_direction"] = line.split("：", 1)[1]
            elif line.startswith("未来三天预报："):
                continue
            else:
                forecast_match = re.match(
                    r"^(\d{4}/\d{2}/\d{2})：(.+?)，气温\s+(.+?)\s+至\s+(.+?)，降水\s+(.+)$",
                    line,
                )
                if forecast_match:
                    date_value, weather, min_temp, max_temp, precipitation = forecast_match.groups()
                    card["forecast"].append(
                        {
                            "date": date_value,
                            "weather": weather,
                            "min_temp": min_temp,
                            "max_temp": max_temp,
                            "precipitation": precipitation,
                        }
                    )

        if not card["current"]:
            return None

        return card

    def _parse_weather(self, payload: Dict[str, Any], city: str) -> Dict[str, Any]:
        current_weather = payload.get("current_weather") or {}
        daily = payload.get("daily") or {}

        forecast = []
        dates = daily.get("time", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        precipitation = daily.get("precipitation_sum", [])
        weather_codes = daily.get("weathercode", [])

        for index, date_value in enumerate(dates):
            forecast.append({
                "date": date_value,
                "max_temp": f"{max_temps[index]}°C" if index < len(max_temps) else "N/A",
                "min_temp": f"{min_temps[index]}°C" if index < len(min_temps) else "N/A",
                "precipitation": f"{precipitation[index]}mm" if index < len(precipitation) else "N/A",
                "weather": self.WEATHER_CODES.get(weather_codes[index], "未知") if index < len(weather_codes) else "未知",
            })

        return {
            "city": city,
            "current": {
                "temperature": f"{current_weather.get('temperature', 'N/A')}°C",
                "weather": self.WEATHER_CODES.get(current_weather.get("weathercode"), "未知"),
                "wind_speed": f"{current_weather.get('windspeed', 'N/A')} km/h",
                "wind_direction": self._wind_direction(current_weather.get("winddirection", 0)),
            },
            "forecast": forecast,
        }

    def _get_cached_weather(self, city: str) -> Optional[Dict[str, Any]]:
        """Return cached weather data when it is still fresh."""
        if self.cache_ttl_seconds <= 0:
            return None

        now = time.monotonic()
        with self._cache_lock:
            cached = self._weather_cache.get(city)
            if not cached:
                return None
            if cached["expires_at"] <= now:
                self._weather_cache.pop(city, None)
                return None
            logger.info("[WeatherService] 命中天气缓存 city=%s", city)
            return copy.deepcopy(cached["value"])

    def _store_cached_weather(self, city: str, weather: Dict[str, Any]) -> None:
        """Store parsed weather data in the short-lived in-memory cache."""
        if self.cache_ttl_seconds <= 0:
            return

        with self._cache_lock:
            self._weather_cache[city] = {
                "value": copy.deepcopy(weather),
                "expires_at": time.monotonic() + self.cache_ttl_seconds,
            }

    def _wind_direction(self, degrees: float) -> str:
        directions = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]
        index = int((degrees + 22.5) // 45) % 8
        return directions[index]

    def _run_async_sync(self, coro):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)

        result: Dict[str, Any] = {}
        error: Dict[str, BaseException] = {}

        def runner():
            try:
                result["value"] = asyncio.run(coro)
            except BaseException as exc:  # pragma: no cover - defensive bridge
                error["value"] = exc

        thread = threading.Thread(target=runner, daemon=True)
        thread.start()
        thread.join()

        if "value" in error:
            raise error["value"]
        return result["value"]


weather_service = WeatherService()
