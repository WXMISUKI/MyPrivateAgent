import json
import unittest

from backend.agent_framework.events import AgentEventFactory, AgentEventType
from backend.agent_framework.runtime import AgentRunContext, AgentState
from backend.agent_framework.tools import ToolRenderMode, ToolSpec


class AgentEventTests(unittest.TestCase):
    def test_state_event_type_serializes(self):
        factory = AgentEventFactory("run_999", conversation_id=8)
        event = factory.build_state_event(
            previous_state="generating",
            state="tool_calling",
            iteration=3,
        )

        data = event.to_dict()
        self.assertEqual(data["type"], "state")
        self.assertEqual(data["payload"]["previous_state"], "generating")
        self.assertEqual(data["payload"]["state"], "tool_calling")
        self.assertEqual(data["payload"]["status_kind"], "agent_state")

    def test_event_factory_flattens_payload(self):
        factory = AgentEventFactory("run_123", conversation_id=42)
        event = factory.build(
            AgentEventType.TOOL_RESULT,
            {
                "name": "search",
                "result": "ok",
                "tool_spec": {"render_mode": "plain_text"},
            },
            iteration=2,
        )

        data = event.to_dict()
        self.assertEqual(data["type"], "tool_result")
        self.assertEqual(data["run_id"], "run_123")
        self.assertEqual(data["conversation_id"], 42)
        self.assertEqual(data["iteration"], 2)
        self.assertEqual(data["payload"]["name"], "search")
        self.assertEqual(data["name"], "search")
        self.assertEqual(data["tool_spec"]["render_mode"], "plain_text")

    def test_event_json_contains_unicode_content(self):
        factory = AgentEventFactory("run_abc", conversation_id=1)
        event = factory.build(AgentEventType.CONTENT, {"content": "天气查询结果（舟山）"}, iteration=1)
        parsed = json.loads(event.to_json())
        self.assertEqual(parsed["content"], "天气查询结果（舟山）")


class AgentRuntimeTests(unittest.TestCase):
    def test_run_context_tracks_state_and_tool_history(self):
        context = AgentRunContext(conversation_id=7, user_id=9, model_name="doubao")
        iteration = context.begin_iteration()
        self.assertEqual(iteration, 1)
        self.assertEqual(context.state, AgentState.GENERATING)
        self.assertTrue(context.state_history)

        transition = context.set_state(AgentState.TOOL_CALLING)
        self.assertEqual(transition["previous_state"], "generating")
        self.assertEqual(transition["state"], "tool_calling")
        context.record_tool_result(
            "search",
            {"query": "舟山天气"},
            "ok",
            "call_1",
            execution={"cache_hit": True, "duration_ms": 1.25},
        )
        context.set_state(AgentState.FINALIZING, stop_reason="completed")
        context.set_state(AgentState.DONE)

        self.assertEqual(context.stop_reason, "completed")
        self.assertEqual(len(context.tool_history), 1)
        self.assertEqual(context.tool_history[0]["tool_name"], "search")
        self.assertEqual(context.tool_history[0]["iteration"], 1)
        self.assertTrue(context.tool_history[0]["execution"]["cache_hit"])

    def test_invalid_transition_raises(self):
        context = AgentRunContext(conversation_id=7, user_id=9, model_name="doubao")
        with self.assertRaises(ValueError):
            context.transition_to(AgentState.DONE)


class ToolSpecTests(unittest.TestCase):
    def test_tool_spec_serializes_render_mode(self):
        spec = ToolSpec(
            name="get_current_datetime",
            description="datetime",
            deterministic=True,
            safe_to_rephrase=False,
            render_mode=ToolRenderMode.PLAIN_TEXT,
            passthrough_strategy="always",
            cache_ttl_seconds=30,
            card_schema="datetime.v1",
        )
        data = spec.to_dict()
        self.assertEqual(data["render_mode"], "plain_text")
        self.assertTrue(data["deterministic"])
        self.assertEqual(data["card_schema"], "datetime.v1")
        self.assertEqual(data["cache_ttl_seconds"], 30)


if __name__ == "__main__":
    unittest.main()
