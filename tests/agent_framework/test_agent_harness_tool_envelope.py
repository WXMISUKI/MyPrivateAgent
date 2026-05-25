import unittest
from unittest.mock import patch

from backend.harness.agent_harness import AgentHarness


class AgentHarnessToolEnvelopeTests(unittest.TestCase):
    def test_build_tool_event_payload_includes_tool_execution_envelope(self):
        harness = AgentHarness.__new__(AgentHarness)

        with patch.object(
            harness,
            "_get_tool_event_metadata",
            return_value={
                "name": "search",
                "render_mode": "structured_card",
                "card_schema": "search_summary.v1",
            },
        ):
            payload = harness._build_tool_event_payload(
                tool_name="search",
                tool_result="查询完成",
                tool_args={"query": "OpenAI"},
                tool_call_id="call_1",
                execution_metadata={
                    "cache_hit": False,
                    "duration_ms": 21.0,
                    "result_source": "tool",
                    "status": "ok",
                },
            )

        envelope = payload["tool_execution_envelope"]
        self.assertEqual(envelope["tool_name"], "search")
        self.assertEqual(envelope["tool_call_id"], "call_1")
        self.assertEqual(envelope["status"], "ok")
        self.assertEqual(envelope["result_text"], "查询完成")
        self.assertEqual(envelope["render_mode"], "structured_card")
        self.assertEqual(envelope["card_schema"], "search_summary.v1")
        self.assertEqual(envelope["execution_metadata"]["result_source"], "tool")
        self.assertEqual(envelope["tool_spec"]["name"], "search")


if __name__ == "__main__":
    unittest.main()
