import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.services.chat_service import (
    _build_run_trace_from_runtime_event,
    collect_orchestrator_response,
    extract_event_field,
    maybe_mark_plan_handoff_executing,
    maybe_start_plan_for_chat,
    stream_scheduled_orchestrator_events,
    stream_orchestrator_events,
)


class _StubOrchestrator:
    def __init__(self, chunks):
        self._chunks = chunks
        self.calls = []

    async def process_message(self, user_message: str, selected_model: str, execution_context=None):
        self.calls.append({
            "user_message": user_message,
            "selected_model": selected_model,
            "execution_context": execution_context,
        })
        for chunk in self._chunks:
            yield chunk


class _NamedOrchestrator(_StubOrchestrator):
    def __init__(self, label):
        super().__init__([
            json_for_content(f"{label}完成"),
            json_for_done(f"{label}完成"),
        ])
        self.label = label


def json_for_content(content):
    return f'{{"type":"content","content":"{content}"}}'


def json_for_done(content):
    return f'{{"type":"done","content":"{content}"}}'


class ChatServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_collect_orchestrator_response_prefers_done_content(self):
        orchestrator = _StubOrchestrator([
            '{"type":"content","content":"舟山"}',
            '{"type":"content","payload":{"content":"天气"}}',
            '{"type":"done","payload":{"content":"舟山天气晴"}}',
        ])

        result = await collect_orchestrator_response(
            orchestrator=orchestrator,
            user_message="今天舟山什么天气",
            model_name="doubao",
        )

        self.assertEqual(result, "舟山天气晴")

    async def test_collect_orchestrator_response_falls_back_to_accumulated_content(self):
        orchestrator = _StubOrchestrator([
            '{"type":"content","content":"hello"}',
            '{"type":"done","content":""}',
        ])

        result = await collect_orchestrator_response(
            orchestrator=orchestrator,
            user_message="hi",
            model_name="doubao",
        )

        self.assertEqual(result, "hello")

    async def test_stream_orchestrator_events_passes_execution_context(self):
        orchestrator = _StubOrchestrator([
            '{"type":"content","content":"hello"}',
            '{"type":"done","content":"hello"}',
        ])

        events = []
        async for chunk, content in stream_orchestrator_events(
            orchestrator=orchestrator,
            user_message="hi",
            model_name="doubao",
            execution_context={"agent_role": "frontend", "agent_id": "frontend-agent-p1-i2"},
        ):
            events.append((chunk, content))

        self.assertEqual(len(events), 2)
        self.assertEqual(orchestrator.calls[0]["execution_context"]["agent_role"], "frontend")

    async def test_runtime_skills_status_maps_to_run_trace(self):
        trace_event = _build_run_trace_from_runtime_event(
            {
                "type": "status",
                "status_kind": "runtime_skills",
                "selected_count": 2,
                "selected_items": [
                    {"type": "skill", "id": 1, "name": "Frontend UI Review"},
                    {"type": "skill", "id": 2, "name": "Planner Skill"},
                ],
                "agent_role": "frontend",
            }
        )

        self.assertIsNotNone(trace_event)
        self.assertEqual(trace_event["source"], "skill")
        self.assertEqual(trace_event["event_type"], "runtime_skills_selected")
        self.assertIn("Frontend UI Review", trace_event["summary"])

    async def test_boundary_fallback_status_maps_to_capability_gap_trace(self):
        trace_event = _build_run_trace_from_runtime_event(
            {
                "type": "status",
                "status_kind": "execution_progress",
                "phase": "boundary_fallback",
                "content": "当前缺少可靠交通建议。",
                "completion_check": {
                    "missing_parts": ["transport", "play"],
                    "profile": "travel_planning",
                    "stage": "boundary_fallback",
                },
            }
        )

        self.assertIsNotNone(trace_event)
        self.assertEqual(trace_event["source"], "agent")
        self.assertEqual(trace_event["event_type"], "capability_gap_fallback")
        self.assertEqual(trace_event["payload"]["missing_parts"], ["transport", "play"])
        self.assertEqual(trace_event["payload"]["profile"], "travel_planning")
        self.assertEqual(trace_event["payload"]["completion_stage"], "boundary_fallback")

    async def test_completion_retry_status_maps_to_run_trace(self):
        trace_event = _build_run_trace_from_runtime_event(
            {
                "type": "status",
                "status_kind": "execution_progress",
                "phase": "completion_retry",
                "content": "已拿到天气结果，正在补查交通与游玩建议。",
                "completion_check": {
                    "missing_parts": ["transport", "play"],
                    "profile": "travel_planning",
                    "stage": "retry",
                },
            }
        )

        self.assertIsNotNone(trace_event)
        self.assertEqual(trace_event["event_type"], "completion_retry")
        self.assertEqual(trace_event["payload"]["missing_parts"], ["transport", "play"])
        self.assertEqual(trace_event["payload"]["profile"], "travel_planning")
        self.assertEqual(trace_event["payload"]["completion_stage"], "retry")

    async def test_hook_tool_denied_maps_to_hook_run_trace(self):
        trace_event = _build_run_trace_from_runtime_event(
            {
                "type": "tool_denied",
                "name": "mcp_filesystem_write",
                "reason": "工具治理策略阻断：命中高风险工具治理策略",
                "hook_decision": {"policy": "high_risk_tool_block"},
            }
        )

        self.assertIsNotNone(trace_event)
        self.assertEqual(trace_event["source"], "hook")
        self.assertEqual(trace_event["event_type"], "pre_tool_use_blocked")

    async def test_tool_result_includes_hook_post_payload(self):
        trace_event = _build_run_trace_from_runtime_event(
            {
                "type": "tool_result",
                "name": "search",
                "status": "ok",
                "result": "天气查询结果（舟山）",
                "tool_execution": {
                    "status": "ok",
                    "hook_post": {"policy": "post_observation_recorded", "result_length": 12},
                },
            }
        )

        self.assertIsNotNone(trace_event)
        self.assertEqual(trace_event["source"], "tool")
        self.assertEqual(trace_event["payload"]["hook_post"]["policy"], "post_observation_recorded")

    async def test_content_with_completion_check_maps_to_completion_finalized_trace(self):
        trace_event = _build_run_trace_from_runtime_event(
            {
                "type": "content",
                "content": "我先根据当前已确认的信息给你一个阶段性建议。",
                "framework_notice": True,
                "completion_check": {
                    "should_finalize": True,
                    "stop_reason": "tool_result_incomplete",
                    "missing_parts": ["transport"],
                    "profile": "travel_planning",
                    "stage": "boundary_fallback",
                },
            }
        )

        self.assertIsNotNone(trace_event)
        self.assertEqual(trace_event["event_type"], "completion_finalized")
        self.assertTrue(trace_event["payload"]["framework_notice"])
        self.assertEqual(trace_event["payload"]["profile"], "travel_planning")
        self.assertEqual(trace_event["payload"]["completion_stage"], "boundary_fallback")


class _StubPlannerService:
    def __init__(self, db):
        self.db = db
        self.active_item = SimpleNamespace(
            id=23,
            title="实现前端交互",
            details="实现前端交互细节",
            status="in_progress",
            agent_role="frontend",
            agent_id="frontend-agent-p10-i23",
            handoff_status=SimpleNamespace(value="handed_off"),
            item_metadata={"required_capabilities": ["filesystem.read", "search.query"]},
        )
        self.plan = SimpleNamespace(id=10, active_item_id=23, items=[self.active_item])
        self.blocked = False

    def get_latest_plan_for_conversation(self, *, user_id, conversation_id):
        return self.plan

    def begin_execution(self, *, plan):
        return plan

    def prepare_handoff(self, *, plan):
        return plan

    def mark_handoff_executing(self, *, plan):
        self.active_item.handoff_status = SimpleNamespace(value="executing")
        return plan

    def block_active_item(self, *, plan, reason, missing_capabilities=None, unavailable_capabilities=None):
        self.blocked = True
        self.active_item.status = SimpleNamespace(value="blocked")
        self.active_item.block_reason = reason
        self.active_item.missing_capabilities = list(missing_capabilities or [])
        self.active_item.unavailable_capabilities = list(unavailable_capabilities or [])
        return plan

    def get_active_item(self, *, plan):
        return self.active_item

    def serialize_plan(self, plan):
        return {"id": plan.id, "items": [{"id": self.active_item.id}], "blocked": self.blocked}


class _StubPlannerServiceFanout(_StubPlannerService):
    def __init__(self, db):
        super().__init__(db)
        self.active_item.title = "完成前后端联调并补测试文档"
        self.active_item.agent_role = "planner"
        self.active_item.agent_id = None
        self.active_item.item_metadata = {
            "required_capabilities": ["filesystem.read", "search.query"],
            "child_roles": ["backend", "frontend", "qa"],
        }


class _StubCapabilityAdapterReady:
    def validate_capabilities(self, capabilities):
        return {
            "ready": True,
            "missing_capabilities": [],
            "unavailable_capabilities": [],
            "resolved_capabilities": [],
        }


class _StubCapabilityAdapterBlocked:
    def validate_capabilities(self, capabilities):
        return {
            "ready": False,
            "missing_capabilities": ["filesystem.read"],
            "unavailable_capabilities": ["search.query"],
            "resolved_capabilities": [],
        }


class PlannerChatLifecycleTests(unittest.TestCase):
    @patch("backend.services.chat_service._get_mcp_adapter_service", return_value=_StubCapabilityAdapterReady())
    @patch("backend.services.chat_service._get_planner_service_cls", return_value=_StubPlannerService)
    def test_maybe_start_plan_for_chat_builds_handoff_context_and_events(self, _mock_planner_cls, _mock_capability_service):
        state = maybe_start_plan_for_chat(
            db=object(),
            user_id=1,
            conversation_id=99,
        )

        self.assertIsNotNone(state)
        self.assertEqual(len(state["events"]), 3)
        self.assertEqual(state["events"][0]["type"], "plan_updated")
        self.assertEqual(state["events"][1]["type"], "plan_updated")
        self.assertEqual(state["events"][2]["status_kind"], "agent_handoff")
        self.assertEqual(state["execution_context"]["agent_role"], "frontend")
        self.assertEqual(state["execution_context"]["agent_id"], "frontend-agent-p10-i23")
        self.assertEqual(state["execution_context"]["required_capabilities"], ["filesystem.read", "search.query"])

    @patch("backend.services.chat_service._get_mcp_adapter_service", return_value=_StubCapabilityAdapterReady())
    @patch("backend.services.chat_service._get_planner_service_cls", return_value=_StubPlannerService)
    def test_maybe_mark_plan_handoff_executing_returns_execution_event(self, _mock_planner_cls, _mock_capability_service):
        state = maybe_mark_plan_handoff_executing(
            db=object(),
            user_id=1,
            conversation_id=99,
        )

        self.assertIsNotNone(state)
        self.assertEqual(len(state["events"]), 2)
        self.assertEqual(state["events"][1]["status_kind"], "agent_execution")
        self.assertEqual(state["execution_context"]["handoff_status"], "executing")

    @patch("backend.services.chat_service._get_mcp_adapter_service", return_value=_StubCapabilityAdapterReady())
    @patch("backend.services.chat_service._get_planner_service_cls", return_value=_StubPlannerServiceFanout)
    def test_maybe_start_plan_for_chat_builds_scheduler_fanout_context(self, _mock_planner_cls, _mock_capability_service):
        state = maybe_start_plan_for_chat(
            db=object(),
            user_id=1,
            conversation_id=99,
        )

        self.assertIsNotNone(state)
        self.assertEqual(state["events"][-1]["status_kind"], "scheduler_fanout_prepared")
        self.assertEqual(state["execution_context"]["scheduler_mode"], "fan_out")
        self.assertEqual(len(state["execution_context"]["child_contexts"]), 3)


class _StubPlannerServiceForStream:
    def __init__(self, db):
        self.db = db
        self.plan = SimpleNamespace(
            id=10,
            active_item_id=23,
            items=[
                SimpleNamespace(
                    id=23,
                    title="联调",
                    details="并发执行",
                    status="in_progress",
                    item_metadata={},
                    handoff_status=SimpleNamespace(value="executing"),
                )
            ],
        )

    def get_latest_plan_for_conversation(self, *, user_id, conversation_id):
        return self.plan

    def get_active_item(self, *, plan):
        return plan.items[0]

    def serialize_plan(self, plan):
        return {"id": plan.id, "active_item_id": plan.active_item_id}


class _StubSchedulerServiceForStream:
    trace_events = []

    def __init__(self, db):
        self.db = db
        self.completed = []
        self.failed = []
        self.cancelled = []
        self.retried = []

    def mark_child_running(self, *, plan, item_id, child_execution_id):
        return plan

    def mark_child_completed(self, *, plan, item_id, child_execution_id, output_text):
        self.completed.append((child_execution_id, output_text))
        return plan

    def mark_child_failed(self, *, plan, item_id, child_execution_id, error_text, error_kind="failed", retry_count=None):
        self.failed.append((child_execution_id, error_text, error_kind, retry_count))
        return plan

    def mark_child_retrying(self, *, plan, item_id, child_execution_id, retry_count, error_text):
        self.retried.append((child_execution_id, retry_count, error_text))
        return plan

    def mark_child_cancelled(self, *, plan, item_id, child_execution_id, reason):
        self.cancelled.append((child_execution_id, reason))
        return plan

    def get_execution_policy(self, item):
        return {
            "timeout_seconds": 1,
            "max_retries": 1,
            "cancel_on_failure": True,
        }

    def append_audit_event(self, **kwargs):
        return kwargs.get("plan")

    def append_run_trace_event(self, **kwargs):
        self.__class__.trace_events.append(kwargs)
        return kwargs.get("plan")

    def merge_child_outputs(self, *, plan, item_id):
        outputs = [text for _child_id, text in self.completed]
        return {
            "merge_status": "partial_failed" if self.failed or self.cancelled else "completed",
            "merged_output": "\n".join(outputs),
            "completed_children": len(self.completed),
            "failed_children": len(self.failed) + len(self.cancelled),
            "pending_children": 0,
        }


class ScheduledStreamTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        _StubSchedulerServiceForStream.trace_events = []

    @patch("backend.services.chat_service._get_scheduler_service_cls", return_value=_StubSchedulerServiceForStream)
    @patch("backend.services.chat_service._get_planner_service_cls", return_value=_StubPlannerServiceForStream)
    async def test_stream_scheduled_orchestrator_events_runs_children_and_merges_results(self, _mock_planner_cls, _mock_scheduler_cls):
        def orchestrator_factory(*, conversation_id, show_reasoning):
            return _NamedOrchestrator(label=f"child-{conversation_id}-{show_reasoning}")

        with patch("backend.services.chat_service._get_orchestrator_factory", return_value=orchestrator_factory):
            events = []
            async for chunk, actual_content in stream_scheduled_orchestrator_events(
                orchestrator=SimpleNamespace(show_reasoning=False),
                db=object(),
                user_id=1,
                conversation_id=99,
                user_message="执行任务",
                model_name="doubao",
                execution_context={
                    "scheduler_mode": "fan_out",
                    "scheduler_run_id": "sched-p10-i23",
                    "plan_id": 10,
                    "plan_item_id": 23,
                    "child_contexts": [
                        {
                            "plan_id": 10,
                            "plan_item_id": 23,
                            "plan_item_title": "联调",
                            "agent_role": "backend",
                            "agent_id": "backend-agent-p10-i23-c1",
                            "child_execution_id": "backend-child-p10-i23-c1",
                        },
                        {
                            "plan_id": 10,
                            "plan_item_id": 23,
                            "plan_item_title": "联调",
                            "agent_role": "frontend",
                            "agent_id": "frontend-agent-p10-i23-c2",
                            "child_execution_id": "frontend-child-p10-i23-c2",
                        },
                    ],
                },
            ):
                events.append((chunk, actual_content))

        joined = "\n".join(chunk for chunk, _content in events)
        self.assertIn("scheduler_fanout_started", joined)
        self.assertIn("scheduler_merged", joined)
        self.assertIn("subagent_spawned", joined)
        self.assertIn("subagent_collected", joined)
        self.assertTrue(events[-1][1])

    @patch("backend.services.chat_service._get_scheduler_service_cls", return_value=_StubSchedulerServiceForStream)
    @patch("backend.services.chat_service._get_planner_service_cls", return_value=_StubPlannerServiceForStream)
    async def test_stream_scheduled_orchestrator_events_retries_then_fails_and_cancels_pending(self, _mock_planner_cls, _mock_scheduler_cls):
        attempts = {}

        async def fake_collect_orchestrator_response(
            *,
            orchestrator,
            user_message,
            model_name,
            execution_context=None,
            db=None,
            user_id=None,
            conversation_id=None,
        ):
            child_id = execution_context["child_execution_id"]
            attempts[child_id] = attempts.get(child_id, 0) + 1
            if child_id.endswith("c1"):
                raise TimeoutError("timeout")
            await asyncio.sleep(0.05)
            return "frontend完成"

        def orchestrator_factory(*, conversation_id, show_reasoning):
            return SimpleNamespace()

        with (
            patch("backend.services.chat_service._get_orchestrator_factory", return_value=orchestrator_factory),
            patch("backend.services.chat_service.collect_orchestrator_response", side_effect=fake_collect_orchestrator_response),
        ):
            events = []
            async for chunk, actual_content in stream_scheduled_orchestrator_events(
                orchestrator=SimpleNamespace(show_reasoning=False),
                db=object(),
                user_id=1,
                conversation_id=99,
                user_message="执行任务",
                model_name="doubao",
                execution_context={
                    "scheduler_mode": "fan_out",
                    "scheduler_run_id": "sched-p10-i23",
                    "plan_id": 10,
                    "plan_item_id": 23,
                    "child_contexts": [
                        {
                            "plan_id": 10,
                            "plan_item_id": 23,
                            "plan_item_title": "联调",
                            "agent_role": "backend",
                            "agent_id": "backend-agent-p10-i23-c1",
                            "child_execution_id": "backend-child-p10-i23-c1",
                            "scheduler_policy": {"timeout_seconds": 1, "max_retries": 1, "cancel_on_failure": True},
                        },
                        {
                            "plan_id": 10,
                            "plan_item_id": 23,
                            "plan_item_title": "联调",
                            "agent_role": "frontend",
                            "agent_id": "frontend-agent-p10-i23-c2",
                            "child_execution_id": "frontend-child-p10-i23-c2",
                            "scheduler_policy": {"timeout_seconds": 1, "max_retries": 1, "cancel_on_failure": True},
                        },
                    ],
                },
            ):
                events.append((chunk, actual_content))

        joined = "\n".join(chunk for chunk, _content in events)
        self.assertIn("scheduler_retry", joined)
        self.assertIn("subagent_failed", joined)
        self.assertIn("scheduler_cancelled", joined)
        self.assertGreaterEqual(attempts["backend-child-p10-i23-c1"], 2)

    @patch("backend.services.chat_service._get_mcp_adapter_service", return_value=_StubCapabilityAdapterBlocked())
    @patch("backend.services.chat_service._get_planner_service_cls", return_value=_StubPlannerService)
    def test_maybe_start_plan_for_chat_blocks_when_required_capability_unavailable(self, _mock_planner_cls, _mock_capability_service):
        state = maybe_start_plan_for_chat(
            db=object(),
            user_id=1,
            conversation_id=99,
        )

        self.assertTrue(state["blocked"])
        self.assertIsNone(state["execution_context"])
        self.assertEqual(state["events"][-1]["status_kind"], "capability_blocked")
        self.assertIn("filesystem.read", state["blocked_message"])
        self.assertIn("search.query", state["blocked_message"])


class EventFieldTests(unittest.TestCase):
    def test_extract_event_field_supports_payload(self):
        event = {"payload": {"content": "来自 payload"}}
        self.assertEqual(extract_event_field(event, "content"), "来自 payload")

    def test_extract_event_field_prefers_top_level(self):
        event = {"content": "顶层", "payload": {"content": "payload"}}
        self.assertEqual(extract_event_field(event, "content"), "顶层")


class RuntimeTraceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        _StubSchedulerServiceForStream.trace_events = []

    @patch("backend.services.chat_service._get_scheduler_service_cls", return_value=_StubSchedulerServiceForStream)
    @patch("backend.services.chat_service._get_planner_service_cls", return_value=_StubPlannerServiceForStream)
    async def test_stream_orchestrator_events_records_permission_and_mcp_tool_trace(self, _mock_planner_cls, _mock_scheduler_cls):
        orchestrator = _StubOrchestrator([
            '{"type":"tool_permission_required","name":"mcp_filesystem_read","request_id":"perm-1","permission_level":"ask"}',
            '{"type":"tool_result","name":"mcp_filesystem_read","result":"读取完成","tool_call_id":"call-1","status":"ok","result_source":"tool","tool_execution":{"status":"ok","result_source":"tool","duration_ms":12.5}}',
            '{"type":"tool_denied","name":"delete_file","reason":"权限被拒绝"}',
            '{"type":"done","content":"完成"}',
        ])

        events = []
        async for chunk, content in stream_orchestrator_events(
            orchestrator=orchestrator,
            user_message="执行任务",
            model_name="doubao",
            execution_context={"plan_item_id": 23, "agent_role": "frontend"},
            db=object(),
            user_id=1,
            conversation_id=99,
        ):
            events.append((chunk, content))

        self.assertEqual(len(events), 4)
        self.assertEqual(len(_StubSchedulerServiceForStream.trace_events), 3)

        permission_event, mcp_event, denied_event = _StubSchedulerServiceForStream.trace_events
        self.assertEqual(permission_event["source"], "permission")
        self.assertEqual(permission_event["event_type"], "tool_permission_required")
        self.assertEqual(mcp_event["source"], "mcp")
        self.assertEqual(mcp_event["event_type"], "mcp_tool_called")
        self.assertEqual(denied_event["event_type"], "tool_denied")

    @patch("backend.services.chat_service._get_scheduler_service_cls", return_value=_StubSchedulerServiceForStream)
    @patch("backend.services.chat_service._get_planner_service_cls", return_value=_StubPlannerServiceForStream)
    async def test_collect_orchestrator_response_records_tool_error_trace(self, _mock_planner_cls, _mock_scheduler_cls):
        orchestrator = _StubOrchestrator([
            '{"type":"tool_result","name":"search","result":"执行错误: network timeout","tool_call_id":"call-2","status":"error","result_source":"tool_error","tool_execution":{"status":"error","result_source":"tool_error","duration_ms":20.0}}',
            '{"type":"done","content":"最终回答"}',
        ])

        result = await collect_orchestrator_response(
            orchestrator=orchestrator,
            user_message="查询一下",
            model_name="doubao",
            execution_context={"plan_item_id": 23, "agent_role": "frontend"},
            db=object(),
            user_id=1,
            conversation_id=99,
        )

        self.assertEqual(result, "最终回答")
        self.assertEqual(len(_StubSchedulerServiceForStream.trace_events), 1)
        self.assertEqual(_StubSchedulerServiceForStream.trace_events[0]["source"], "tool")
        self.assertEqual(_StubSchedulerServiceForStream.trace_events[0]["event_type"], "tool_failed")
        self.assertEqual(_StubSchedulerServiceForStream.trace_events[0]["payload"]["error_category"], "provider_timeout")


if __name__ == "__main__":
    unittest.main()
