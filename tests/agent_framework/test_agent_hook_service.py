import unittest

from backend.services.agent_hook_service import AgentHookService


class AgentHookServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = AgentHookService()

    def test_pre_tool_use_blocks_high_risk_keyword(self):
        decision = self.service.pre_tool_use(
            tool_name="mcp_filesystem_write",
            tool_args={"path": "/tmp/a.txt"},
            context={},
        )
        self.assertFalse(decision.allowed)
        self.assertIn("高风险工具", decision.reason)

    def test_pre_tool_use_allows_normal_tool(self):
        decision = self.service.pre_tool_use(
            tool_name="search",
            tool_args={"query": "舟山天气"},
            context={},
        )
        self.assertTrue(decision.allowed)

    def test_runtime_contract_contains_hook_catalog(self):
        contract = self.service.build_runtime_contract()
        self.assertIn("pre_tool_use", contract["enabled_hooks"])
        self.assertIn("high_risk_tool_keywords", contract)


if __name__ == "__main__":
    unittest.main()

