from __future__ import annotations

import unittest

from backend.runtime_plane import (
    Agent,
    ApprovalAgentAdapter,
    ExecutionRequest,
    tool,
)


class ApprovalAgentAdapterTests(unittest.TestCase):
    def setUp(self):
        self.high_risk_called = False

        @tool(permission_level="ask", risk_level="high")
        def delete_customer_record(customer_id: str) -> str:
            """Delete a customer record."""
            self.high_risk_called = True
            return f"deleted:{customer_id}"

        self.delete_customer_record = delete_customer_record

        def model_call(messages, tools=None):
            return {
                "role": "assistant",
                "content": "requesting approval",
                "tool_calls": [
                    {
                        "id": "call-approval-1",
                        "name": "delete_customer_record",
                        "args": {"customer_id": "cust-001"},
                    }
                ],
            }

        self.agent = Agent(
            name="approval_agent",
            instructions="You request approval before high-risk actions.",
            model="gpt-4o",
            tools=[delete_customer_record],
            description="Stage 1 approval agent slice",
            metadata={
                "role": "approval",
                "governance_boundaries": ["approval-pending", "no-production-approval"],
            },
        )
        self.adapter = ApprovalAgentAdapter(
            agent=self.agent,
            model_call=model_call,
            runtime_name="local",
        )

    def test_can_execute_and_manifest(self):
        health = self.adapter.health_check()
        self.assertEqual(health["status"], "ready")
        self.assertEqual(health["approval_tool_count"], 1)

        can_execute, reason = self.adapter.can_execute()
        self.assertTrue(can_execute)
        self.assertEqual(reason, "")

        manifest = self.adapter.manifest()
        self.assertEqual(manifest.agent_id, "approval_agent")
        self.assertIn("approval", manifest.capabilities)
        self.assertIn("approval", manifest.role)

    def test_high_risk_tool_call_returns_approval_pending_without_execution(self):
        request = ExecutionRequest(
            request_id="req-approval-001",
            agent_id="approval_agent",
            user_input="Delete customer cust-001",
            thread_id="thread-approval-1",
            runtime="local",
            context_refs=["conversation:approval"],
            metadata={"stage": "stage1-approval"},
        )

        envelope = self.adapter.execute(request)

        self.assertFalse(self.high_risk_called)
        self.assertEqual(envelope["result"]["status"], "approval_pending")
        self.assertEqual(envelope["result"]["final_answer"], "")
        self.assertEqual(len(envelope["result"]["tool_calls"]), 1)

        stages = [event["stage"] for event in envelope["events"]]
        self.assertEqual(stages, ["planning", "approval"])
        approval_event = envelope["events"][1]
        self.assertEqual(approval_event["type"], "approval_required")
        self.assertEqual(approval_event["metadata"]["request_id"], "req-approval-001")
        self.assertEqual(approval_event["metadata"]["agent_id"], "approval_agent")
        self.assertEqual(approval_event["metadata"]["tool_name"], "delete_customer_record")
        self.assertEqual(approval_event["metadata"]["risk_level"], "high")
        self.assertEqual(approval_event["metadata"]["permission_level"], "ask")
        self.assertEqual(approval_event["metadata"]["approval_reason"], "high_risk_tool_intent")
        self.assertFalse(approval_event["metadata"]["will_execute"])
        self.assertFalse(approval_event["metadata"]["production_approval_submitted"])
        self.assertEqual(approval_event["metadata"]["args_summary"]["fields"], ["customer_id"])

        result_approval = envelope["result"]["metadata"]["approval_request"]
        self.assertEqual(result_approval["tool_name"], "delete_customer_record")
        self.assertFalse(result_approval["will_execute"])

    def test_adapter_blocks_without_approval_capable_tools(self):
        @tool
        def read_status(name: str) -> str:
            """Read status."""
            return f"{name}: ok"

        adapter = ApprovalAgentAdapter(
            agent=Agent(
                name="no_approval_agent",
                instructions="Read-only agent.",
                tools=[read_status],
            ),
            model_call=lambda messages, tools=None: {"role": "assistant", "content": "ok"},
        )

        health = adapter.health_check()
        self.assertEqual(health["status"], "blocked")
        can_execute, reason = adapter.can_execute()
        self.assertFalse(can_execute)
        self.assertEqual(reason, "approval_capable_tool_required")


if __name__ == "__main__":
    unittest.main()
