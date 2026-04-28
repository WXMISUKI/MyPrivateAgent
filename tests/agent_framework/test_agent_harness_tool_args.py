import unittest

from backend.harness.agent_harness import AgentHarness, ErrorHandler
from backend.harness.tools.langchain_tools import normalize_search_query_payload


class AgentHarnessToolArgumentTests(unittest.TestCase):
    def test_normalize_search_query_payload_repairs_malformed_query_dict(self):
        payload = {
            '{"queryquery': ': " "舟山舟山最近最近天气天气情况情况 明天明天舟山舟山天气预报 福州福州到到舟山舟山的的交通交通方式方式 舟山舟山旅游旅游游玩游玩攻略攻略',
            'value': ''
        }

        normalized = normalize_search_query_payload(payload)

        self.assertTrue(normalized)
        self.assertIn("舟山", normalized)
        self.assertIn("天气", normalized)
        self.assertNotIn("queryquery", normalized)

    def test_sanitize_tool_arguments_recovers_search_query_field(self):
        harness = AgentHarness(model=object(), tools=[], use_bind_tools=False)

        arguments = harness._sanitize_tool_arguments(
            tool_name="search",
            arguments={
                '{"queryquery': ': " "舟山最近天气 明天舟山天气预报',
                'value': ''
            },
        )

        self.assertEqual(set(arguments.keys()), {"query"})
        self.assertIn("舟山", arguments["query"])

    def test_non_retryable_tool_validation_error_is_detected(self):
        harness = AgentHarness(model=object(), tools=[], use_bind_tools=False)

        self.assertTrue(
            harness._is_non_retryable_tool_validation_error(
                "执行错误: 1 validation error for SearchInput\nquery\n  Field required"
            )
        )
        self.assertFalse(harness._is_non_retryable_tool_validation_error("执行错误: network timeout"))

    def test_tool_repetition_budget_blocks_same_signature(self):
        harness = AgentHarness(model=object(), tools=[], use_bind_tools=False)

        result = harness._check_tool_repetition_budget(
            tool_name="search",
            tool_args={"query": "舟山天气"},
            tool_call_history=[
                {"name": "search", "args": {"query": "舟山天气"}, "result": "天气查询结果（舟山）..."}
            ],
        )

        self.assertIsNotNone(result)
        self.assertIn("去重保护", result["reason"])

    def test_travel_completeness_check_detects_missing_sections_after_budget(self):
        harness = AgentHarness(model=object(), tools=[], use_bind_tools=False)

        result = harness._evaluate_tool_result_completeness(
            user_goal="最近舟山天气怎么样，我明天从福州出发去舟山玩，你可以帮我规划一下吗",
            tool_results=[
                {"name": "search", "result": "天气查询结果（舟山） 当前天气：阴 未来三天预报：..."}
            ],
            tool_call_history=[
                {"name": "search", "args": {"query": "舟山天气"}, "result": "天气查询结果（舟山） 当前天气：阴 未来三天预报：..."},
                {"name": "search", "args": {"query": "舟山天气攻略"}, "result": "天气查询结果（舟山） 当前天气：阴 未来三天预报：..."},
            ],
        )

        self.assertIsNotNone(result)
        self.assertTrue(result["should_finalize"])
        self.assertIn("transport", result["missing_parts"])
        self.assertIn("play", result["missing_parts"])

    def test_travel_completeness_check_requests_single_retry_before_budget_exhausted(self):
        harness = AgentHarness(model=object(), tools=[], use_bind_tools=False)

        result = harness._evaluate_tool_result_completeness(
            user_goal="最近舟山天气怎么样，我明天从福州出发去舟山玩，你可以帮我规划一下吗",
            tool_results=[
                {"name": "search", "result": "天气查询结果（舟山） 当前天气：阴 未来三天预报：..."}
            ],
            tool_call_history=[
                {"name": "search", "args": {"query": "舟山天气"}, "result": "天气查询结果（舟山） 当前天气：阴 未来三天预报：..."},
            ],
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["action"], "retry")
        self.assertEqual(result["retry_tool_call"]["name"], "search")
        self.assertIn("交通方式", result["retry_tool_call"]["arguments"]["query"])

    def test_build_iteration_messages_adds_synthesis_instruction_for_travel_goal(self):
        harness = AgentHarness(model=object(), tools=[], use_bind_tools=False)

        messages = harness._build_iteration_messages(
            messages=[],
            user_goal="最近舟山天气怎么样，我明天从福州出发去舟山玩，你可以帮我规划一下吗",
            tool_call_history=[{"name": "search", "args": {"query": "舟山天气"}, "result": "天气查询结果（舟山）"}],
        )

        self.assertEqual(len(messages), 1)
        self.assertIn("最终答复至少覆盖", messages[0].content)

    def test_build_iteration_messages_adds_synthesis_instruction_for_research_compare_goal(self):
        harness = AgentHarness(model=object(), tools=[], use_bind_tools=False)

        messages = harness._build_iteration_messages(
            messages=[],
            user_goal="请帮我对比两种智能体框架方案，并说明为什么推荐其中一个",
            tool_call_history=[{"name": "search", "args": {"query": "智能体框架对比"}, "result": "一些零散结果"}],
        )

        self.assertEqual(len(messages), 1)
        self.assertIn("复合型研究/对比请求", messages[0].content)

    def test_build_completion_fallback_response_mentions_boundary_for_travel_goal(self):
        harness = AgentHarness(model=object(), tools=[], use_bind_tools=False)

        response = harness._build_completion_fallback_response(
            user_goal="最近舟山天气怎么样，我明天从福州出发去舟山玩，你可以帮我规划一下吗",
            tool_call_history=[
                {
                    "name": "search",
                    "args": {"query": "舟山天气"},
                    "result": "天气查询结果（舟山）\n当前天气：阴\n未来三天预报：2026/04/27：阴"
                }
            ],
            completeness_check={
                "missing_parts": ["transport", "play"]
            },
        )

        self.assertIn("阶段性建议", response)
        self.assertIn("交通建议", response)
        self.assertIn("游玩/行程建议", response)

    def test_should_use_final_synthesis_mode_for_travel_goal_after_tool_observation(self):
        harness = AgentHarness(model=object(), tools=[], use_bind_tools=False)

        self.assertTrue(
            harness._should_use_final_synthesis_mode(
                user_goal="最近舟山天气怎么样，我明天从福州出发去舟山玩，你可以帮我规划一下吗",
                tool_call_history=[{"name": "search", "args": {"query": "舟山天气"}, "result": "天气查询结果（舟山）"}],
            )
        )
        self.assertFalse(
            harness._should_use_final_synthesis_mode(
                user_goal="明天舟山天气怎么样",
                tool_call_history=[{"name": "search", "args": {"query": "舟山天气"}, "result": "天气查询结果（舟山）"}],
            )
        )
        self.assertTrue(
            harness._should_use_final_synthesis_mode(
                user_goal="请帮我对比两种智能体框架方案，并说明为什么推荐其中一个",
                tool_call_history=[{"name": "search", "args": {"query": "智能体框架对比"}, "result": "一些零散结果"}],
            )
        )
        self.assertTrue(
            harness._should_use_final_synthesis_mode(
                user_goal="请帮我规划这个通用智能体框架接下来的实施步骤，并说明怎么推进落地",
                tool_call_history=[{"name": "search", "args": {"query": "智能体框架实施步骤"}, "result": "一些零散结果"}],
            )
        )

    def test_error_handler_classifies_retryable_provider_errors(self):
        handler = ErrorHandler()

        result = handler.classify_error(RuntimeError("network timeout"))

        self.assertEqual(result["category"], "provider_timeout")
        self.assertTrue(result["retryable"])

    def test_error_handler_classifies_non_retryable_validation_errors(self):
        handler = ErrorHandler()

        result = handler.classify_error(RuntimeError("1 validation error for SearchInput"))

        self.assertEqual(result["category"], "tool_validation")
        self.assertFalse(result["retryable"])


if __name__ == "__main__":
    unittest.main()
