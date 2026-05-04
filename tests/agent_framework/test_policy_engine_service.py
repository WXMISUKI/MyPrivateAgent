import unittest

from backend.services.policy_engine_service import get_policy_engine_service


class PolicyEngineServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = get_policy_engine_service()

    def test_blocks_high_risk_tool(self):
        decision = self.service.evaluate_tool_use(
            tool_name="mcp_filesystem_write",
            tool_args={"path": "a.txt"},
            context={"agent_role": "backend"},
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.metadata["policy"], "high_risk_tool_block")

    def test_blocks_tool_not_in_subagent_allowlist(self):
        decision = self.service.evaluate_tool_use(
            tool_name="get_current_datetime",
            tool_args={},
            context={"agent_role": "frontend"},
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.metadata["policy"], "subagent_tool_allowlist_block")

    def test_select_provider_hint_with_override(self):
        hint = self.service.select_provider_hint(
            requested_model="doubao",
            requested_provider="anthropic",
            context={"agent_role": "planner"},
        )
        self.assertEqual(hint["selected_provider"], "anthropic")
        self.assertEqual(hint["reason"], "request_provider_override")

    def test_select_model_for_provider_falls_back_to_provider_default(self):
        route = self.service.select_model_for_provider(
            requested_model="doubao",
            selected_provider="ollama",
            available_models=[
                {"name": "doubao", "provider": "volcengine-ark", "available": True, "is_default": True},
                {"name": "llama3.1", "provider": "ollama", "available": True, "is_default": True},
            ],
        )
        self.assertEqual(route["resolved_provider"], "ollama")
        self.assertEqual(route["resolved_model"], "llama3.1")
        self.assertEqual(route["reason"], "provider_fallback_model_selected")


if __name__ == "__main__":
    unittest.main()
