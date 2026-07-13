from __future__ import annotations

import unittest

from backend.runtime_plane import Agent, ExecutionRequest, SimpleAgentAdapter, ToolAgentAdapter, tool


class ToolAgentAdapterTests(unittest.TestCase):
    def setUp(self):
        @tool
        def get_weather(city: str) -> str:
            """获取城市天气。"""
            return f"{city}: sunny"

        self.get_weather = get_weather

        def model_call(messages, tools=None):
            tool_messages = [message for message in messages if isinstance(message, dict) and message.get("role") == "tool"]
            if tool_messages:
                return {
                    "role": "assistant",
                    "content": f"tool_result={tool_messages[-1].get('content', '')}",
                }

            return {
                "role": "assistant",
                "content": "calling tool",
                "tool_calls": [
                    {
                        "id": "call-1",
                        "name": "get_weather",
                        "args": {"city": "北京"},
                    }
                ],
            }

        self.agent = Agent(
            name="tool_agent",
            instructions="你是一个会调用工具的最小运行层测试智能体。",
            model="gpt-4o",
            tools=[get_weather],
            description="Stage 1 tool agent slice",
            metadata={
                "role": "tooling",
                "governance_boundaries": ["single-tool", "no-approval"],
            },
        )
        self.adapter = ToolAgentAdapter(
            agent=self.agent,
            model_call=model_call,
            runtime_name="local",
        )

    def test_can_execute_and_manifest(self):
        health = self.adapter.health_check()
        self.assertEqual(health["status"], "ready")
        self.assertEqual(health["tool_count"], 1)

        can_execute, reason = self.adapter.can_execute()
        self.assertTrue(can_execute)
        self.assertEqual(reason, "")

        manifest = self.adapter.manifest()
        self.assertEqual(manifest.agent_id, "tool_agent")
        self.assertIn("tool_call", manifest.capabilities)
        self.assertIn("tooling", manifest.role)

    def test_tool_agent_emits_tool_stages_and_result(self):
        request = ExecutionRequest(
            request_id="req-tool-001",
            agent_id="tool_agent",
            user_input="北京天气怎么样？",
            thread_id="thread-tool-1",
            runtime="local",
            context_refs=["conversation:tool"],
            metadata={"stage": "stage1-tool"},
        )

        envelope = self.adapter.execute(request)

        self.assertEqual(envelope["request"]["request_id"], "req-tool-001")
        self.assertEqual(envelope["manifest"]["agent_id"], "tool_agent")
        self.assertEqual(envelope["result"]["status"], "success")
        self.assertIn("tool_result=北京: sunny", envelope["result"]["final_answer"])
        self.assertEqual(len(envelope["result"]["tool_calls"]), 1)
        self.assertEqual(envelope["result"]["tool_calls"][0]["name"], "get_weather")

        stages = [event["stage"] for event in envelope["events"]]
        self.assertEqual(stages, ["planning", "tool_calling", "observing", "finalizing"])
        self.assertEqual(envelope["events"][1]["type"], "completed")
        self.assertGreaterEqual(envelope["events"][1]["metadata"]["tool_call_count"], 1)
        self.assertIn("北京: sunny", envelope["events"][2]["payload_summary"])


if __name__ == "__main__":
    unittest.main()
