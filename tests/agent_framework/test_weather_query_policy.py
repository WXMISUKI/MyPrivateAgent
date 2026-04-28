import unittest

from backend.agent_framework.tools import ToolSpec
from backend.harness.agent_harness import AgentHarness
from backend.harness.tool_registry import get_registry
from backend.services.weather_service import weather_service


class WeatherQueryPolicyTests(unittest.TestCase):
    def test_pure_weather_query_is_detected(self):
        self.assertTrue(weather_service.is_weather_query("明天舟山天气怎么样"))
        self.assertTrue(weather_service.is_pure_weather_query("明天舟山天气怎么样"))

    def test_composite_travel_query_is_not_treated_as_pure_weather(self):
        query = "最近舟山天气怎么样，我明天从福州出发去舟山玩，你可以帮我规划一下吗"
        self.assertTrue(weather_service.is_weather_query(query))
        self.assertFalse(weather_service.is_pure_weather_query(query))

    def test_weather_passthrough_only_for_pure_weather_queries(self):
        harness = AgentHarness(model=object(), tools=[], use_bind_tools=False)
        get_registry().register_tool_spec(
            ToolSpec(
                name="search",
                description="search",
                passthrough_strategy="weather_query",
                safe_to_rephrase=False,
            )
        )
        weather_result = (
            "天气查询结果（舟山）\n"
            "当前天气：多云\n"
            "当前气温：23°C\n"
            "当前风速：3 km/h\n"
            "当前风向：南\n"
            "未来三天预报：\n"
            "2026/04/27：阴，气温 16°C 至 27°C，降水 0.0mm"
        )

        pure_query_result = harness._maybe_use_direct_tool_result(
            [{"name": "search", "result": weather_result}],
            [{"name": "search", "arguments": {"query": "明天舟山天气怎么样"}}],
        )
        composite_query_result = harness._maybe_use_direct_tool_result(
            [{"name": "search", "result": weather_result}],
            [{"name": "search", "arguments": {"query": "最近舟山天气怎么样，我明天从福州出发去舟山玩，你可以帮我规划一下吗"}}],
        )

        self.assertEqual(pure_query_result, weather_result)
        self.assertIsNone(composite_query_result)


if __name__ == "__main__":
    unittest.main()
