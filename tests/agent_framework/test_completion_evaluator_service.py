import unittest

from backend.services.completion_evaluator_service import CompletionEvaluatorService


class CompletionEvaluatorServiceTests(unittest.TestCase):
    def test_first_weather_only_result_triggers_single_retry_for_travel_goal(self):
        service = CompletionEvaluatorService()

        result = service.evaluate(
            user_goal="最近舟山天气怎么样，我明天从福州出发去舟山玩，你可以帮我规划一下吗",
            tool_results=[{"name": "search", "result": "天气查询结果（舟山） 当前天气：阴"}],
            tool_call_history=[
                {
                    "name": "search",
                    "args": {"query": "舟山明天天气 福州到舟山交通方式 舟山景点"},
                    "result": "天气查询结果（舟山） 当前天气：阴",
                }
            ],
            max_similar_tool_calls=2,
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["action"], "retry")
        self.assertIn("transport", result["missing_parts"])
        self.assertIn("play", result["missing_parts"])
        self.assertIn("交通方式", result["retry_tool_call"]["arguments"]["query"])

    def test_second_incomplete_result_finalizes_after_budget(self):
        service = CompletionEvaluatorService()

        result = service.evaluate(
            user_goal="最近舟山天气怎么样，我明天从福州出发去舟山玩，你可以帮我规划一下吗",
            tool_results=[{"name": "search", "result": "天气查询结果（舟山） 当前天气：阴"}],
            tool_call_history=[
                {"name": "search", "args": {"query": "舟山天气"}, "result": "天气查询结果（舟山） 当前天气：阴"},
                {"name": "search", "args": {"query": "福州到舟山交通方式；舟山景点"}, "result": "天气查询结果（舟山） 当前天气：阴"},
            ],
            max_similar_tool_calls=2,
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["action"], "finalize")
        self.assertTrue(result["should_finalize"])
        self.assertIn("transport", result["missing_parts"])

    def test_research_compare_goal_uses_generic_composite_profile(self):
        service = CompletionEvaluatorService()

        result = service.evaluate(
            user_goal="请帮我对比两种智能体框架方案，并说明为什么推荐其中一个",
            tool_results=[{"name": "search", "result": "只返回了一些零散信息"}],
            tool_call_history=[
                {
                    "name": "search",
                    "args": {"query": "智能体框架对比 推荐 原因"},
                    "result": "只返回了一些零散信息",
                },
                {
                    "name": "search",
                    "args": {"query": "智能体框架对比 推荐 原因"},
                    "result": "只返回了一些零散信息",
                },
            ],
            max_similar_tool_calls=2,
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["profile"], "research_compare")
        self.assertEqual(result["action"], "finalize")
        self.assertIn("options", result["missing_parts"])
        self.assertIn("recommendation", result["missing_parts"])

    def test_build_synthesis_instruction_supports_research_compare_profile(self):
        service = CompletionEvaluatorService()

        prompt = service.build_synthesis_instruction("请帮我对比两种智能体框架方案，并说明为什么推荐其中一个")

        self.assertIn("复合型研究/对比请求", prompt)
        self.assertIn("候选方案或关键选项", prompt)

    def test_task_planning_goal_uses_planning_profile(self):
        service = CompletionEvaluatorService()

        result = service.evaluate(
            user_goal="请帮我规划这个通用智能体框架接下来的实施步骤，并说明怎么推进落地",
            tool_results=[{"name": "search", "result": "只找到一些背景信息"}],
            tool_call_history=[
                {
                    "name": "search",
                    "args": {"query": "智能体框架 实施步骤 风险 计划"},
                    "result": "只找到一些背景信息",
                },
                {
                    "name": "search",
                    "args": {"query": "智能体框架 实施步骤 风险 计划"},
                    "result": "只找到一些背景信息",
                },
            ],
            max_similar_tool_calls=2,
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["profile"], "planning")
        self.assertEqual(result["action"], "finalize")
        self.assertIn("steps", result["missing_parts"])
        self.assertIn("risks", result["missing_parts"])

    def test_build_synthesis_instruction_supports_planning_profile(self):
        service = CompletionEvaluatorService()

        prompt = service.build_synthesis_instruction("请帮我规划这个通用智能体框架接下来的实施步骤，并说明怎么推进落地")

        self.assertIn("复合型规划请求", prompt)
        self.assertIn("分步骤执行计划", prompt)


if __name__ == "__main__":
    unittest.main()
