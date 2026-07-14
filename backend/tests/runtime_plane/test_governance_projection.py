from __future__ import annotations

import unittest

from backend.runtime_plane import (
    Agent,
    ApprovalAgentAdapter,
    ExecutionRequest,
    SimpleAgentAdapter,
    ToolAgentAdapter,
    tool,
)


class RuntimePlaneGovernanceProjectionTests(unittest.TestCase):
    def test_simple_agent_projection_is_read_only(self):
        adapter = SimpleAgentAdapter(
            agent=Agent(
                name="simple_projection_agent",
                instructions="Return a simple answer.",
                metadata={"role": "simple"},
            ),
            model_call=lambda messages, tools=None: {
                "role": "assistant",
                "content": "simple projection ready",
            },
        )

        envelope = adapter.execute(
            ExecutionRequest(
                request_id="req-projection-simple",
                agent_id="simple_projection_agent",
                user_input="hello",
            )
        )

        projection = envelope["governance_projection"]
        self.assertEqual(projection["read_model"], "runtime_plane_governance_projection")
        self.assertEqual(projection["contract_version"], "runtime-plane-governance-read-model-v1")
        self.assertEqual(projection["adapter_id"], "simple_agent")
        self.assertEqual(projection["result_status"], "success")
        self.assertEqual(projection["event_count"], 3)
        self.assertEqual(projection["stage_counts"], {"planning": 1, "generating": 1, "finalizing": 1})
        self.assertFalse(projection["approval_required"])
        self.assertEqual(projection["tool_call_count"], 0)
        self.assertTrue(projection["boundaries"]["read_model_only"])
        self.assertFalse(projection["boundaries"]["will_persist_trace"])
        self.assertFalse(projection["boundaries"]["will_submit_approval"])
        self.assertFalse(projection["boundaries"]["default_chat_changed"])

    def test_tool_agent_projection_preserves_tool_count(self):
        @tool
        def get_status(name: str) -> str:
            """Read status."""
            return f"{name}: ok"

        def model_call(messages, tools=None):
            if any(message.get("role") == "tool" for message in messages if isinstance(message, dict)):
                return {"role": "assistant", "content": "status observed"}
            return {
                "role": "assistant",
                "content": "calling tool",
                "tool_calls": [{"id": "call-1", "name": "get_status", "args": {"name": "runtime"}}],
            }

        adapter = ToolAgentAdapter(
            agent=Agent(name="tool_projection_agent", tools=[get_status], metadata={"role": "tool"}),
            model_call=model_call,
        )

        envelope = adapter.execute(
            ExecutionRequest(
                request_id="req-projection-tool",
                agent_id="tool_projection_agent",
                user_input="check runtime",
            )
        )

        projection = envelope["governance_projection"]
        self.assertEqual(projection["adapter_id"], "tool_agent")
        self.assertEqual(projection["tool_call_count"], 1)
        self.assertFalse(projection["approval_required"])
        self.assertEqual(projection["stage_counts"]["tool_calling"], 1)
        self.assertEqual(projection["stage_counts"]["observing"], 1)

    def test_approval_agent_projection_preserves_approval_indicator(self):
        @tool(permission_level="ask", risk_level="high")
        def delete_record(record_id: str) -> str:
            """Delete a record."""
            raise AssertionError("high-risk tool must not execute")

        adapter = ApprovalAgentAdapter(
            agent=Agent(name="approval_projection_agent", tools=[delete_record], metadata={"role": "approval"}),
            model_call=lambda messages, tools=None: {
                "role": "assistant",
                "content": "approval needed",
                "tool_calls": [{"id": "call-approval", "name": "delete_record", "args": {"record_id": "r1"}}],
            },
        )

        envelope = adapter.execute(
            ExecutionRequest(
                request_id="req-projection-approval",
                agent_id="approval_projection_agent",
                user_input="delete r1",
            )
        )

        projection = envelope["governance_projection"]
        self.assertEqual(projection["adapter_id"], "approval_agent")
        self.assertEqual(projection["result_status"], "approval_pending")
        self.assertTrue(projection["approval_required"])
        self.assertEqual(projection["approval_status"], "required")
        self.assertEqual(projection["approval_tool_name"], "delete_record")
        self.assertEqual(projection["tool_call_count"], 1)
        self.assertEqual(projection["stage_counts"], {"planning": 1, "approval": 1})
        self.assertTrue(projection["boundaries"]["read_model_only"])


if __name__ == "__main__":
    unittest.main()
