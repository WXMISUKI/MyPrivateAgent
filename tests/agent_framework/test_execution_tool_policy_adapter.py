import unittest

from backend.agent_framework.runtime import AgentRunContext
from backend.agent_framework.tool_policy import build_policy_engine_tool_policy


class ExecutionToolPolicyAdapterTests(unittest.TestCase):
    def test_policy_adapter_maps_high_risk_tool_to_approval_required_decision(self):
        run_context = AgentRunContext(conversation_id=42, user_id=7, model_name="doubao")

        policy = build_policy_engine_tool_policy(
            tool_name="mcp_filesystem_write",
            tool_args={"path": "case.md"},
        )

        decision = policy(run_context).to_dict()

        self.assertEqual(decision["status"], "approval_required")
        self.assertEqual(decision["tool_name"], "mcp_filesystem_write")
        self.assertEqual(decision["tool_args"], {"path": "case.md"})
        self.assertEqual(decision["metadata"]["reason_code"], "high_risk_tool_requires_approval")
        self.assertEqual(decision["metadata"]["policy"], "high_risk_tool_requires_approval")

    def test_policy_adapter_maps_allowlist_block_to_denied_decision(self):
        run_context = AgentRunContext(conversation_id=42, user_id=7, model_name="doubao")
        run_context.metadata["agent_role"] = "frontend"

        policy = build_policy_engine_tool_policy(
            tool_name="get_current_datetime",
            tool_args={},
        )

        decision = policy(run_context).to_dict()

        self.assertEqual(decision["status"], "denied")
        self.assertEqual(decision["tool_name"], "get_current_datetime")
        self.assertEqual(decision["metadata"]["reason_code"], "subagent_tool_allowlist_block")
        self.assertEqual(decision["metadata"]["policy"], "subagent_tool_allowlist_block")


if __name__ == "__main__":
    unittest.main()
