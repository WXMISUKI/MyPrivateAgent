import unittest

from backend.harness.agent_harness import AgentHarness


class CapabilityGapFeedbackTests(unittest.TestCase):
    def test_travel_completion_fallback_uses_structured_gap_sections(self):
        harness = AgentHarness(model=None, tools=[], model_name="doubao")
        result = harness._build_completion_fallback_response(
            user_goal="最近舟山天气怎么样，我明天从福州出发去舟山玩，你可以帮我规划一下吗",
            tool_call_history=[
                {
                    "name": "search",
                    "result": "天气查询结果（舟山）\n当前天气：晴\n当前气温：22.0C",
                    "args": {"query": "舟山天气"},
                }
            ],
            completeness_check={"missing_parts": ["transport", "play"]},
        )

        self.assertIn("已完成", result)
        self.assertIn("当前缺口", result)
        self.assertIn("建议补强能力", result)
        self.assertIn("交通路线检索工具", result)
        self.assertIn("POI / 景点检索工具", result)


if __name__ == "__main__":
    unittest.main()
