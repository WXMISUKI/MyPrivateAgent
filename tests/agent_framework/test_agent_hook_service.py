import unittest
import json

from langchain_core.messages import HumanMessage

from backend.harness.agent_harness import AgentHarness
from backend.services.agent_hook_service import AgentHookService


class _HighRiskToolModel:
    async def ainvoke(self, _messages):
        return type("ToolResponse", (), {
            "content": "",
            "tool_calls": [{
                "name": "mcp_filesystem_write",
                "args": {"path": "/tmp/a.txt"},
                "id": "call-high-risk-1",
            }],
        })()


class AgentHookServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = AgentHookService()

    def test_pre_tool_use_requires_approval_for_high_risk_keyword(self):
        decision = self.service.pre_tool_use(
            tool_name="mcp_filesystem_write",
            tool_args={"path": "/tmp/a.txt"},
            context={},
        )
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_approval)
        self.assertEqual(decision.reason_code, "high_risk_tool_requires_approval")
        self.assertIn("高风险工具", decision.reason)

    def test_pre_tool_use_allows_normal_tool(self):
        decision = self.service.pre_tool_use(
            tool_name="search",
            tool_args={"query": "舟山天气"},
            context={},
        )
        self.assertTrue(decision.allowed)
        self.assertFalse(decision.requires_approval)

    def test_runtime_contract_contains_hook_catalog(self):
        contract = self.service.build_runtime_contract()
        self.assertIn("pre_tool_use", contract["enabled_hooks"])
        self.assertIn("high_risk_tool_keywords", contract)


class AgentHarnessApprovalHookTests(unittest.IsolatedAsyncioTestCase):
    async def test_high_risk_hook_decision_pauses_run_with_approval_created(self):
        harness = AgentHarness(
            model=_HighRiskToolModel(),
            tools=[],
            use_bind_tools=False,
            user_id=7,
            conversation_id=11,
            model_name="test-model",
        )

        events = []
        async for chunk in harness.run([HumanMessage(content="写入一个文件")]):
            events.append(json.loads(chunk))

        approval_event = next(
            item for item in events
            if item.get("payload", {}).get("status_kind") == "approval_created"
        )
        state_values = [
            item.get("payload", {}).get("state")
            for item in events
            if item.get("type") == "state"
        ]
        done_event = events[-1]

        self.assertEqual(approval_event["type"], "status")
        self.assertEqual(approval_event["payload"]["status_kind"], "approval_created")
        self.assertEqual(approval_event["payload"]["tool_name"], "mcp_filesystem_write")
        self.assertEqual(approval_event["payload"]["reason_code"], "high_risk_tool_requires_approval")
        self.assertEqual(approval_event["payload"]["approval_request"]["status"], "pending")
        self.assertTrue(approval_event["payload"]["approval_request"]["requires_approval"])
        self.assertNotIn("tool_denied", [item["type"] for item in events])
        self.assertIn("waiting_approval", state_values)
        self.assertNotIn("observing", state_values)
        self.assertNotIn("done", state_values)
        self.assertEqual(done_event["type"], "done")
        self.assertEqual(done_event["payload"]["state"], "waiting_approval")
        self.assertEqual(done_event["payload"]["stop_reason"], "approval_required")
        self.assertEqual(done_event["payload"]["approval_request_id"], approval_event["payload"]["approval_request_id"])
        self.assertEqual(done_event["payload"]["error_category"], "tool_governance")


if __name__ == "__main__":
    unittest.main()
