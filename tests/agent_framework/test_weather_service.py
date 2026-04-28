import unittest

from backend.services.weather_service import weather_service


class WeatherServiceTests(unittest.TestCase):
    def test_extract_city_prefers_destination_for_travel_context(self):
        query = "最近舟山天气怎么样，我明天从福州出发去舟山玩，你可以帮我规划一下吗"
        self.assertEqual(weather_service.extract_city(query), "舟山")

    def test_extract_city_keeps_single_city_for_simple_weather_query(self):
        query = "最近福州天气怎么样"
        self.assertEqual(weather_service.extract_city(query), "福州")


if __name__ == "__main__":
    unittest.main()
