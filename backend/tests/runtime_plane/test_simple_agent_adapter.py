from __future__ import annotations

import unittest

from backend.runtime_plane import (
    Agent,
    ExecutionRequest,
    SimpleAgentAdapter,
)


class SimpleAgentAdapterTests(unittest.TestCase):
    def setUp(self):
        def model_call(messages, tools=None):
            self.assertEqual(tools or [], [])
            self.assertGreaterEqual(len(messages), 1)
            return {
                "role": "assistant",
                "content": "simple_agent ready",
            }

        self.agent = Agent(
            name="simple_agent",
            instructions="你是一个最小运行层测试智能体。",
            model="gpt-4o",
            description="Stage 1 simple agent slice",
            metadata={
                "role": "simple",
                "governance_boundaries": ["no-tools", "no-approval"],
            },
        )
        self.adapter = SimpleAgentAdapter(
            agent=self.agent,
            model_call=model_call,
            runtime_name="local",
        )

    def test_contracts_are_normalized(self):
        request = ExecutionRequest(
            request_id="req-001",
            agent_id="simple_agent",
            user_input="hello",
            context_refs=["conversation:1", "source:manual"],
            metadata={"stage": "stage1"},
        )

        self.assertEqual(request.context_refs, ("conversation:1", "source:manual"))
        self.assertEqual(request.to_dict()["runtime"], "local")

        manifest = self.adapter.manifest()
        self.assertEqual(manifest.agent_id, "simple_agent")
        self.assertIn("chat", manifest.capabilities)
        self.assertIn("simple", manifest.role)

    def test_simple_agent_execution_emits_normalized_envelope(self):
        request = ExecutionRequest(
            request_id="req-002",
            agent_id="simple_agent",
            user_input="请打个招呼",
            thread_id="thread-1",
            runtime="local",
            context_refs=["conversation:2"],
            metadata={"stage": "stage1"},
        )

        envelope = self.adapter.execute(request)

        self.assertEqual(envelope["request"]["request_id"], "req-002")
        self.assertEqual(envelope["manifest"]["agent_id"], "simple_agent")
        self.assertEqual(envelope["result"]["status"], "success")
        self.assertEqual(envelope["result"]["final_answer"], "simple_agent ready")
        self.assertEqual(envelope["result"]["trace_ref"], "req-002")

        events = envelope["events"]
        self.assertEqual([event["stage"] for event in events], ["planning", "generating", "finalizing"])
        self.assertEqual(events[0]["type"], "started")
        self.assertEqual(events[-1]["type"], "completed")
        self.assertTrue(any("simple_agent ready" in event["payload_summary"] for event in events))

    def test_health_check_and_can_execute(self):
        health = self.adapter.health_check()
        self.assertEqual(health["status"], "ready")
        self.assertEqual(health["adapter_id"], "simple_agent")

        can_execute, reason = self.adapter.can_execute()
        self.assertTrue(can_execute)
        self.assertEqual(reason, "")


if __name__ == "__main__":
    unittest.main()
