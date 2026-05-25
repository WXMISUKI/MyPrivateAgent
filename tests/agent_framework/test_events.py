import json
import unittest

from backend.agent_framework.events import AgentEvent, AgentEventFactory, AgentEventType
from backend.agent_framework.runtime import AgentRunContext, AgentRunKind, AgentState
from backend.agent_framework.tools import ArtifactRef, ToolExecutionEnvelope, ToolRenderMode, ToolSpec


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

    def test_event_factory_includes_parent_run_id(self):
        factory = AgentEventFactory("run_child_1", conversation_id=7, parent_run_id="run_parent_1")
        event = factory.build(AgentEventType.STATUS, {"status_kind": "subagent_spawned"})

        data = event.to_dict()
        self.assertEqual(data["parent_run_id"], "run_parent_1")
        self.assertTrue(data["event_id"].startswith("evt_"))

    def test_event_json_contains_unicode_content(self):
        factory = AgentEventFactory("run_abc", conversation_id=1)
        event = factory.build(AgentEventType.CONTENT, {"content": "天气查询结果（舟山）"}, iteration=1)
        parsed = json.loads(event.to_json())
        self.assertEqual(parsed["content"], "天气查询结果（舟山）")

    def test_event_factory_supports_runtime_core_metadata(self):
        factory = AgentEventFactory("run_123", conversation_id=42, parent_run_id="run_parent")
        event = factory.build(
            AgentEventType.STATUS,
            {"status_kind": "approval_created", "approval_request_id": "apr_001"},
            iteration=2,
        )
        enriched = AgentEvent(
            type=event.type,
            run_id=event.run_id,
            parent_run_id=event.parent_run_id,
            conversation_id=event.conversation_id,
            iteration=event.iteration,
            source="governance",
            severity="warning",
            summary="审批请求已创建",
            detail="等待人工确认",
            payload=event.payload,
        )

        data = enriched.to_dict()
        self.assertEqual(data["source"], "governance")
        self.assertEqual(data["severity"], "warning")
        self.assertEqual(data["summary"], "审批请求已创建")
        self.assertEqual(data["detail"], "等待人工确认")
        self.assertEqual(data["approval_request_id"], "apr_001")


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
        self.assertEqual(context.snapshot()["run_kind"], "chat")

    def test_run_context_snapshot_exposes_runtime_core_fields(self):
        context = AgentRunContext(
            conversation_id=7,
            user_id=9,
            model_name="doubao",
            parent_run_id="run_parent_1",
            run_kind=AgentRunKind.CHAT,
        )
        context.begin_iteration()
        context.transition_to(AgentState.WAITING_APPROVAL, stop_reason="approval_required")
        context.set_runtime_marker(error_category="tool_governance", approval_request_id="apr_001")

        snapshot = context.snapshot()

        self.assertTrue(snapshot["runtime_core"])
        self.assertEqual(snapshot["run_id"][:4], "run_")
        self.assertEqual(snapshot["parent_run_id"], "run_parent_1")
        self.assertEqual(snapshot["state"], "waiting_approval")
        self.assertEqual(snapshot["stop_reason"], "approval_required")
        self.assertEqual(snapshot["metadata"]["error_category"], "tool_governance")
        self.assertEqual(snapshot["metadata"]["approval_request_id"], "apr_001")

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

    def test_tool_execution_envelope_serializes_artifact_ref_and_execution_metadata(self):
        envelope = ToolExecutionEnvelope(
            tool_name="search",
            tool_call_id="call_1",
            status="ok",
            result_text="查询完成",
            render_mode=ToolRenderMode.STRUCTURED_CARD,
            card_schema="search_summary.v1",
            artifact_ref=ArtifactRef(
                artifact_id="art_001",
                kind="tool_result",
                uri="artifact://tool_result/art_001",
            ),
            execution_metadata={"duration_ms": 12.5, "result_source": "tool"},
            tool_spec={"name": "search"},
        )

        data = envelope.to_dict()

        self.assertEqual(data["tool_name"], "search")
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["render_mode"], "structured_card")
        self.assertEqual(data["artifact_ref"]["artifact_id"], "art_001")
        self.assertEqual(data["execution_metadata"]["result_source"], "tool")


if __name__ == "__main__":
    unittest.main()
