import unittest

from backend.services.weather_service import weather_service


class WeatherCardTests(unittest.TestCase):
    def test_build_weather_card_from_text(self):
        text = "\n".join(
            [
                "天气查询结果（舟山）",
                "当前天气：小雨",
                "当前气温：15.7°C",
                "当前风速：22.6 km/h",
                "当前风向：西北",
                "未来三天预报：",
                "2026/04/22：中雨，气温 14.9°C 至 18.6°C，降水 38.9mm",
                "2026/04/23：阵雨，气温 14.1°C 至 15.6°C，降水 0.2mm",
            ]
        )

        card = weather_service.build_weather_card_from_text(text)
        self.assertIsNotNone(card)
        self.assertEqual(card["kind"], "weather")
        self.assertEqual(card["schema"], "weather.v1")
        self.assertEqual(card["city"], "舟山")
        self.assertEqual(card["current"]["weather"], "小雨")
        self.assertEqual(len(card["forecast"]), 2)
        self.assertEqual(card["forecast"][0]["date"], "2026/04/22")


if __name__ == "__main__":
    unittest.main()
