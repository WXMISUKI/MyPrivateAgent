import asyncio
import unittest

from backend.services.weather_service import WeatherService


def _sample_payload():
    return {
        "current_weather": {
            "temperature": 15.7,
            "weathercode": 61,
            "windspeed": 22.6,
            "winddirection": 315,
        },
        "daily": {
            "time": ["2026-04-24", "2026-04-25"],
            "temperature_2m_max": [18.6, 15.6],
            "temperature_2m_min": [14.9, 14.1],
            "precipitation_sum": [38.9, 0.2],
            "weathercode": [63, 80],
        },
    }


class _StubWeatherService(WeatherService):
    def __init__(self, cache_ttl_seconds: float = 300.0):
        super().__init__(timeout_seconds=0.1, cache_ttl_seconds=cache_ttl_seconds)
        self.fetch_count = 0

    async def _fetch_weather_payload(self, city, coords):
        self.fetch_count += 1
        return _sample_payload()


class WeatherServiceCacheTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_weather_by_city_uses_short_term_cache(self):
        service = _StubWeatherService(cache_ttl_seconds=300)

        first = await service.get_weather_by_city("舟山")
        second = await service.get_weather_by_city("舟山")

        self.assertEqual(service.fetch_count, 1)
        self.assertEqual(first["city"], "舟山")
        self.assertEqual(second["current"]["weather"], "小雨")

    async def test_cached_weather_is_returned_as_copy(self):
        service = _StubWeatherService(cache_ttl_seconds=300)

        first = await service.get_weather_by_city("舟山")
        first["current"]["weather"] = "被污染"
        second = await service.get_weather_by_city("舟山")

        self.assertEqual(service.fetch_count, 1)
        self.assertEqual(second["current"]["weather"], "小雨")

    async def test_cache_expiry_refetches_weather(self):
        service = _StubWeatherService(cache_ttl_seconds=0.01)

        await service.get_weather_by_city("舟山")
        await asyncio.sleep(0.03)
        await service.get_weather_by_city("舟山")

        self.assertEqual(service.fetch_count, 2)


if __name__ == "__main__":
    unittest.main()
