import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.schemas_runtime_surface import RuntimeSurfaceGovernanceOverviewResponse
from backend.services.chat_service import (
    _attach_main_chat_query_control_mapping,
    _build_main_chat_input_received_event,
    _build_run_trace_from_runtime_event,
    _extract_execution_run_scope,
    collect_orchestrator_response,
    collect_scheduled_orchestrator_response,
    extract_event_field,
    merge_chat_execution_context,
    maybe_mark_plan_handoff_executing,
    maybe_start_plan_for_chat,
    RuntimeApprovalRequired,
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


class _StubMainChatQueryControlService:
    calls = []

    @classmethod
    def record_query_control_events(cls, **kwargs):
        cls.calls.append(kwargs)
        return {"recordings": [{"trace_written": True}], "failures": []}


class _NamedOrchestrator(_StubOrchestrator):
    def __init__(self, label):
        super().__init__([
            json_for_content(f"{label}完成"),
            json_for_done(f"{label}完成"),
        ])
        self.label = label


class _StubProviderAwareOrchestrator(_StubOrchestrator):
    def __init__(self):
        super().__init__([
            json_for_content("provider aware content"),
            json_for_done("provider aware done"),
        ])
        self.show_reasoning = False
        self.model_provider = SimpleNamespace(
            list_available_models=lambda: {
                "doubao": {
                    "name": "doubao",
                    "provider": "volcengine-ark",
                    "available": True,
                    "is_default": True,
                },
                "llama3.1": {
                    "name": "llama3.1",
                    "provider": "ollama",
                    "available": True,
                    "is_default": True,
                },
            }
        )


def json_for_content(content):
    return f'{{"type":"content","content":"{content}"}}'


def json_for_done(content):
    return f'{{"type":"done","content":"{content}"}}'


class ChatServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        _StubMainChatQueryControlService.calls = []

    async def test_build_main_chat_input_received_event_preserves_main_chat_seed_fields(self):
        event = _build_main_chat_input_received_event(
            user_message="请总结今天进度",
            model_name="doubao",
            execution_context={"run_id": "run-1", "agent_role": "planner"},
        )

        self.assertEqual(event["type"], "status")
        self.assertEqual(event["status_kind"], "main_chat_input_received")
        self.assertEqual(event["content"], "请总结今天进度")
        self.assertEqual(event["model_name"], "doubao")
        self.assertEqual(event["run_id"], "run-1")
        self.assertEqual(event["agent_role"], "planner")

    async def test_merge_chat_execution_context_prefers_runtime_keys(self):
        merged = merge_chat_execution_context(
            {"run_id": "manual-chat-1", "enable_main_chat_query_control_timeline": True, "agent_role": "manual"},
            {"run_id": "handoff-p10-i23", "agent_role": "frontend"},
        )

        self.assertEqual(merged["run_id"], "handoff-p10-i23")
        self.assertEqual(merged["agent_role"], "frontend")
        self.assertTrue(merged["enable_main_chat_query_control_timeline"])

    async def test_attach_main_chat_query_control_mapping_marks_main_chat_lifecycle_stage(self):
        mapped = _attach_main_chat_query_control_mapping({
            "type": "content",
            "content": "阶段性输出",
        })

        self.assertEqual(mapped["_query_control"]["channel"], "main_chat")
        self.assertEqual(mapped["_query_control"]["stage"], "model_stream")

    async def test_attach_main_chat_query_control_mapping_skips_waiting_approval_done(self):
        mapped = _attach_main_chat_query_control_mapping({
            "type": "done",
            "content": "等待审批",
            "state": "waiting_approval",
            "stop_reason": "approval_required",
        })

        self.assertNotIn("_query_control", mapped)

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

    async def test_collect_orchestrator_response_raises_when_waiting_approval(self):
        orchestrator = _StubOrchestrator([
            '{"type":"done","content":"等待审批","state":"waiting_approval","stop_reason":"approval_required"}',
        ])

        with self.assertRaises(RuntimeApprovalRequired) as caught:
            await collect_orchestrator_response(
                orchestrator=orchestrator,
                user_message="hi",
                model_name="doubao",
            )

        self.assertEqual(caught.exception.message, "等待审批")
        self.assertEqual(caught.exception.event["state"], "waiting_approval")

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

    @patch("backend.services.chat_service._get_main_chat_query_control_service", return_value=_StubMainChatQueryControlService())
    async def test_collect_orchestrator_response_records_main_chat_query_control_events_when_opted_in(self, _mock_main_chat_service):
        orchestrator = _StubOrchestrator([
            '{"type":"reasoning","content":"先拆解任务"}',
            '{"type":"content","content":"hello"}',
            '{"type":"done","content":"hello"}',
        ])

        result = await collect_orchestrator_response(
            orchestrator=orchestrator,
            user_message="hi",
            model_name="doubao",
            db=object(),
            conversation_id=42,
            execution_context={
                "run_id": "handoff-p1-i2",
                "enable_main_chat_query_control_timeline": True,
            },
        )

        self.assertEqual(result, "hello")
        self.assertEqual(len(_StubMainChatQueryControlService.calls), 4)
        self.assertEqual(_StubMainChatQueryControlService.calls[0]["query_id"], "handoff-p1-i2")

    @patch("backend.services.chat_service._get_main_chat_query_control_service", return_value=_StubMainChatQueryControlService())
    async def test_collect_orchestrator_response_skips_main_chat_query_control_events_without_opt_in(self, _mock_main_chat_service):
        orchestrator = _StubOrchestrator([
            '{"type":"content","content":"hello"}',
            '{"type":"done","content":"hello"}',
        ])

        result = await collect_orchestrator_response(
            orchestrator=orchestrator,
            user_message="hi",
            model_name="doubao",
            db=object(),
            conversation_id=42,
            execution_context={"run_id": "handoff-p1-i2"},
        )

        self.assertEqual(result, "hello")
        self.assertEqual(_StubMainChatQueryControlService.calls, [])

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

    async def test_framework_adapter_status_maps_to_run_trace(self):
        trace_event = _build_run_trace_from_runtime_event(
            {
                "type": "status",
                "source": "framework_adapter",
                "adapter_id": "local_fake_framework",
                "framework_name": "LocalFakeFramework",
                "status": "stream_started",
                "summary": "LocalFakeFramework adapter stream started",
                "detail": "received 1 messages",
            }
        )

        self.assertIsNotNone(trace_event)
        self.assertEqual(trace_event["source"], "framework_adapter")
        self.assertEqual(trace_event["event_type"], "framework_adapter_status")
        self.assertEqual(trace_event["payload"]["adapter_id"], "local_fake_framework")

    async def test_framework_adapter_reasoning_maps_to_run_trace(self):
        trace_event = _build_run_trace_from_runtime_event(
            {
                "type": "reasoning",
                "source": "framework_adapter",
                "adapter_id": "local_fake_framework",
                "framework_name": "LocalFakeFramework",
                "summary": "local fake adapter is planning next action",
                "detail": "phase_c2_local_pilot",
            }
        )

        self.assertIsNotNone(trace_event)
        self.assertEqual(trace_event["source"], "framework_adapter")
        self.assertEqual(trace_event["event_type"], "framework_adapter_reasoning")

    async def test_framework_adapter_content_maps_to_run_trace(self):
        trace_event = _build_run_trace_from_runtime_event(
            {
                "type": "content",
                "source": "framework_adapter",
                "adapter_id": "local_fake_framework",
                "framework_name": "LocalFakeFramework",
                "content": "Local fake adapter processed: 巡检计划",
            }
        )

        self.assertIsNotNone(trace_event)
        self.assertEqual(trace_event["source"], "framework_adapter")
        self.assertEqual(trace_event["event_type"], "framework_adapter_output")
        self.assertIn("巡检计划", trace_event["payload"]["content"])

    async def test_approval_created_status_maps_to_pending_permission_trace(self):
        trace_event = _build_run_trace_from_runtime_event(
            {
                "type": "status",
                "status_kind": "approval_created",
                "approval_request_id": "apr_001",
                "tool_name": "mcp_filesystem_write",
                "permission_level": "high_risk",
                "reason_code": "high_risk_tool_requires_approval",
                "reason": "高风险工具需要人工审批",
                "requested_by_role": "planner",
                "requested_by_agent_id": "planner-agent-p1",
                "tool_args": {"path": "README.md"},
            }
        )

        self.assertIsNotNone(trace_event)
        self.assertEqual(trace_event["source"], "governance")
        self.assertEqual(trace_event["event_type"], "tool_permission_required")
        self.assertEqual(trace_event["payload"]["request_id"], "apr_001")
        self.assertEqual(trace_event["payload"]["approval_request_id"], "apr_001")
        self.assertEqual(trace_event["payload"]["reason_code"], "high_risk_tool_requires_approval")
        self.assertEqual(trace_event["payload"]["requested_by_role"], "planner")
        self.assertEqual(trace_event["payload"]["tool_args"]["path"], "README.md")

    async def test_approval_resolved_status_maps_to_permission_approved_trace(self):
        trace_event = _build_run_trace_from_runtime_event(
            {
                "type": "status",
                "status_kind": "approval_resolved",
                "approval_request_id": "apr_001",
                "status": "approved",
                "result": "approved",
                "tool_name": "mcp_filesystem_write",
                "permission_level": "high_risk",
                "completed_at": "2026-05-11T10:00:00Z",
            }
        )

        self.assertIsNotNone(trace_event)
        self.assertEqual(trace_event["source"], "governance")
        self.assertEqual(trace_event["event_type"], "permission_approved")
        self.assertEqual(trace_event["severity"], "success")
        self.assertEqual(trace_event["payload"]["request_id"], "apr_001")
        self.assertEqual(trace_event["payload"]["status"], "approved")

    async def test_approval_resolved_status_normalizes_approve_and_deny_synonyms(self):
        approved_trace = _build_run_trace_from_runtime_event(
            {
                "type": "status",
                "status_kind": "approval_resolved",
                "approval_request_id": "apr_approve",
                "status": "approve",
                "tool_name": "mcp_filesystem_write",
            }
        )
        denied_trace = _build_run_trace_from_runtime_event(
            {
                "type": "status",
                "status_kind": "approval_resolved",
                "approval_request_id": "apr_deny",
                "result": "deny",
                "tool_name": "mcp_filesystem_write",
            }
        )

        self.assertEqual(approved_trace["event_type"], "permission_approved")
        self.assertEqual(approved_trace["payload"]["status"], "approved")
        self.assertEqual(denied_trace["event_type"], "permission_denied")
        self.assertEqual(denied_trace["payload"]["status"], "denied")

    async def test_tool_permission_required_and_approval_created_share_canonical_shape(self):
        direct_trace = _build_run_trace_from_runtime_event(
            {
                "type": "tool_permission_required",
                "name": "mcp_filesystem_read",
                "request_id": "perm-001",
                "permission_level": "ask",
                "args": {"path": "README.md"},
            }
        )
        approval_trace = _build_run_trace_from_runtime_event(
            {
                "type": "status",
                "status_kind": "approval_created",
                "tool_name": "mcp_filesystem_read",
                "approval_request_id": "perm-001",
                "permission_level": "ask",
                "tool_args": {"path": "README.md"},
            }
        )

        self.assertEqual(direct_trace["source"], approval_trace["source"])
        self.assertEqual(direct_trace["event_type"], approval_trace["event_type"])
        self.assertEqual(direct_trace["payload"]["request_id"], approval_trace["payload"]["request_id"])
        self.assertEqual(direct_trace["payload"]["approval_request_id"], approval_trace["payload"]["approval_request_id"])
        self.assertEqual(direct_trace["payload"]["tool_name"], approval_trace["payload"]["tool_name"])
        self.assertEqual(direct_trace["payload"]["permission_level"], approval_trace["payload"]["permission_level"])
        self.assertEqual(direct_trace["payload"]["tool_args"], approval_trace["payload"]["tool_args"])

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

    def test_runtime_surface_governance_overview_schema_supports_run_approval_and_audit(self):
        overview = RuntimeSurfaceGovernanceOverviewResponse(
            run={
                "run_id": "run-001",
                "status": "waiting_approval",
                "trace_count": 4,
                "child_merge_entity_count": 2,
                "child_merge_focus_count": 3,
                "child_merge_action_count": 1,
                "child_merge_section_source": "merged_sections",
                "child_merge_section_ids": ["merged_entities", "merged_focus"],
                "child_merge_section_counts": {"merged_entities": 2, "merged_focus": 3},
                "latest_trace_event": {
                    "event_type": "tool_permission_required",
                    "source": "governance",
                    "summary": "等待审批",
                },
            },
            approval={
                "request_count": 1,
                "pending_count": 1,
                "latest_request": {
                    "request_id": "apr_001",
                    "status": "pending",
                    "tool_name": "mcp_filesystem_write",
                    "permission_level": "high_risk",
                },
            },
            audit={
                "event_count": 2,
                "latest_event": {
                    "event_type": "permission_approved",
                    "source": "governance",
                    "summary": "审批已通过",
                },
            },
        )

        self.assertEqual(overview.run.run_id, "run-001")
        self.assertEqual(overview.run.child_merge_entity_count, 2)
        self.assertEqual(overview.run.child_merge_focus_count, 3)
        self.assertEqual(overview.run.child_merge_section_source, "merged_sections")
        self.assertEqual(overview.run.child_merge_section_ids, ["merged_entities", "merged_focus"])
        self.assertEqual(overview.run.child_merge_section_counts["merged_entities"], 2)
        self.assertEqual(overview.run.latest_trace_event.event_type, "tool_permission_required")
        self.assertEqual(overview.run.latest_trace_event.source, "governance")
        self.assertEqual(overview.approval.pending_count, 1)
        self.assertEqual(overview.approval.latest_request.request_id, "apr_001")
        self.assertEqual(overview.approval.latest_request.permission_level, "high_risk")
        self.assertEqual(overview.audit.event_count, 2)
        self.assertEqual(overview.audit.latest_event.event_type, "permission_approved")
        self.assertEqual(overview.audit.latest_event.summary, "审批已通过")

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

    async def test_state_event_maps_to_runtime_trace(self):
        trace_event = _build_run_trace_from_runtime_event(
            {
                "type": "state",
                "previous_state": "generating",
                "state": "tool_calling",
                "stop_reason": "",
            }
        )

        self.assertIsNotNone(trace_event)
        self.assertEqual(trace_event["source"], "runtime")
        self.assertEqual(trace_event["event_type"], "agent_state_changed")
        self.assertEqual(trace_event["payload"]["previous_state"], "generating")
        self.assertEqual(trace_event["payload"]["state"], "tool_calling")

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
        self.assertEqual(state["execution_context"]["run_id"], "handoff-p10-i23")
        self.assertEqual(state["execution_context"]["run_kind"], "subagent")
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
        self.assertEqual(state["execution_context"]["run_id"], "handoff-p10-i23")
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
        self.assertEqual(state["execution_context"]["run_id"], "sched-p10-i23")
        self.assertEqual(state["execution_context"]["run_kind"], "scheduler")
        self.assertEqual(state["execution_context"]["scheduler_mode"], "fan_out")
        self.assertEqual(len(state["execution_context"]["child_contexts"]), 3)
        self.assertEqual(state["execution_context"]["child_contexts"][0]["parent_run_id"], "sched-p10-i23")


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
        self.waiting_approval = []

    def mark_child_running(self, *, plan, item_id, child_execution_id):
        return plan

    def mark_child_policy_selected(
        self,
        *,
        plan,
        item_id,
        child_execution_id,
        model_name,
        provider_name,
        provider_order=None,
        provider_switch_count=None,
        provider_history=None,
    ):
        return plan

    def mark_child_completed(self, *, plan, item_id, child_execution_id, output_text):
        self.completed.append((child_execution_id, output_text))
        return plan

    def mark_child_failed(self, *, plan, item_id, child_execution_id, error_text, error_kind="failed", retry_count=None):
        self.failed.append((child_execution_id, error_text, error_kind, retry_count))
        return plan

    def mark_child_waiting_approval(self, *, plan, item_id, child_execution_id, reason, approval_event=None, retry_count=None):
        self.waiting_approval.append((child_execution_id, reason, approval_event, retry_count))
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


class _StubSubagentRuntimeServiceForQueryControl:
    query_control_calls = []

    @classmethod
    def normalize_context(cls, payload):
        return SimpleNamespace(
            agent_role=payload.get("agent_role"),
            agent_id=payload.get("agent_id"),
            plan_id=payload.get("plan_id"),
            plan_item_id=payload.get("plan_item_id"),
            plan_item_title=payload.get("plan_item_title", ""),
            handoff_status=payload.get("handoff_status", ""),
            execution_mode=payload.get("execution_mode", ""),
            required_capabilities=tuple(payload.get("required_capabilities") or []),
            run_id=payload.get("run_id") or payload.get("child_execution_id"),
            parent_run_id=payload.get("parent_run_id") or payload.get("scheduler_run_id", ""),
        )

    @staticmethod
    def build_spawn_event(context):
        return {
            "type": "status",
            "status_kind": "subagent_spawned",
            "run_id": context.run_id,
            "parent_run_id": context.parent_run_id,
            "agent_role": context.agent_role,
            "agent_id": context.agent_id,
            "content": f"{context.agent_role} spawned",
        }

    @staticmethod
    def build_collect_event(context, *, output_text):
        return {
            "type": "status",
            "status_kind": "subagent_collected",
            "run_id": context.run_id,
            "parent_run_id": context.parent_run_id,
            "agent_role": context.agent_role,
            "agent_id": context.agent_id,
            "subagent_output_excerpt": output_text,
            "content": f"{context.agent_role} collected",
        }

    @classmethod
    def record_query_control_events(cls, **kwargs):
        cls.query_control_calls.append(kwargs)
        return {"recordings": [{"trace_written": True}], "failures": []}


class ScheduledStreamTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        _StubSchedulerServiceForStream.trace_events = []
        _StubSubagentRuntimeServiceForQueryControl.query_control_calls = []

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

    @patch("backend.services.chat_service._get_subagent_runtime_service", return_value=_StubSubagentRuntimeServiceForQueryControl())
    @patch("backend.services.chat_service._get_scheduler_service_cls", return_value=_StubSchedulerServiceForStream)
    @patch("backend.services.chat_service._get_planner_service_cls", return_value=_StubPlannerServiceForStream)
    async def test_stream_scheduled_orchestrator_events_records_subagent_query_control_events(self, _mock_planner_cls, _mock_scheduler_cls, _mock_subagent_service):
        def orchestrator_factory(*, conversation_id, show_reasoning):
            return _NamedOrchestrator(label=f"child-{conversation_id}-{show_reasoning}")

        with patch("backend.services.chat_service._get_orchestrator_factory", return_value=orchestrator_factory):
            async for _chunk, _actual_content in stream_scheduled_orchestrator_events(
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
                            "parent_run_id": "sched-p10-i23",
                        },
                    ],
                },
            ):
                pass

        status_kinds = [
            call["events"][0]["status_kind"]
            for call in _StubSubagentRuntimeServiceForQueryControl.query_control_calls
        ]
        self.assertIn("subagent_spawned", status_kinds)
        self.assertIn("subagent_collected", status_kinds)
        self.assertIn("subagent_merged", status_kinds)
        self.assertEqual(_StubSubagentRuntimeServiceForQueryControl.query_control_calls[0]["conversation_id"], 99)

    @patch("backend.services.chat_service._get_scheduler_service_cls", return_value=_StubSchedulerServiceForStream)
    @patch("backend.services.chat_service._get_planner_service_cls", return_value=_StubPlannerServiceForStream)
    async def test_stream_scheduled_orchestrator_events_pauses_when_child_waits_for_approval(self, _mock_planner_cls, _mock_scheduler_cls):
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
            raise RuntimeApprovalRequired(
                "等待审批",
                {
                    "type": "done",
                    "state": "waiting_approval",
                    "stop_reason": "approval_required",
                    "approval_request_id": "apr_child_001",
                    "approval_request": {"request_id": "apr_child_001", "status": "pending"},
                    "error_category": "tool_governance",
                },
            )

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
                            "child_run_id": "backend-run-1",
                            "child_display_id": "backend-run-1",
                            "scheduler_policy": {"timeout_seconds": 1, "max_retries": 0, "cancel_on_failure": True},
                        },
                    ],
                },
            ):
                events.append((chunk, actual_content))

        joined = "\n".join(chunk for chunk, _content in events)
        self.assertIn("subagent_waiting_approval", joined)
        self.assertNotIn("subagent_collected", joined)
        self.assertNotIn("scheduler_merged", joined)
        self.assertIn('"state": "waiting_approval"', joined)
        waiting_approval_event = next(
            json.loads(chunk)
            for chunk, _content in events
            if '"status_kind": "subagent_waiting_approval"' in chunk
        )
        self.assertEqual(waiting_approval_event["child_run_id"], "backend-run-1")
        self.assertEqual(waiting_approval_event["child_display_id"], "backend-run-1")
        done_event = json.loads(events[-1][0])
        self.assertEqual(done_event["approval_request_id"], "apr_child_001")
        self.assertEqual(done_event["error_category"], "tool_governance")
        self.assertEqual(done_event["approval_event"]["approval_request_id"], "apr_child_001")
        self.assertEqual(events[-1][1], "等待审批")

    async def test_collect_scheduled_orchestrator_response_raises_when_waiting_approval(self):
        async def fake_stream_scheduled_orchestrator_events(**_kwargs):
            yield (
                '{"type":"done","content":"等待审批","state":"waiting_approval","stop_reason":"approval_required"}',
                "等待审批",
            )

        with patch(
            "backend.services.chat_service.stream_scheduled_orchestrator_events",
            side_effect=fake_stream_scheduled_orchestrator_events,
        ):
            with self.assertRaises(RuntimeApprovalRequired) as caught:
                await collect_scheduled_orchestrator_response(
                    orchestrator=SimpleNamespace(),
                    db=object(),
                    user_id=1,
                    conversation_id=99,
                    user_message="执行任务",
                    model_name="doubao",
                    execution_context={"scheduler_mode": "fan_out"},
                )

        self.assertEqual(caught.exception.message, "等待审批")
        self.assertEqual(caught.exception.event["state"], "waiting_approval")

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

    @patch("backend.services.chat_service._get_scheduler_service_cls", return_value=_StubSchedulerServiceForStream)
    @patch("backend.services.chat_service._get_planner_service_cls", return_value=_StubPlannerServiceForStream)
    async def test_stream_scheduled_orchestrator_events_routes_model_by_provider_policy(self, _mock_planner_cls, _mock_scheduler_cls):
        class _StubPolicyEngine:
            @staticmethod
            def select_provider_hint(*, requested_model, context):
                role = (context or {}).get("agent_role")
                return {
                    "selected_provider": "ollama" if role == "backend" else "volcengine-ark",
                    "provider_order": ["ollama", "volcengine-ark"],
                    "reason": "default_provider_order",
                    "model_name": requested_model,
                    "agent_role": role,
                }

            @staticmethod
            def select_model_for_provider(*, requested_model, selected_provider, available_models):
                if selected_provider == "ollama":
                    return {
                        "resolved_model": "llama3.1",
                        "resolved_provider": "ollama",
                        "reason": "provider_fallback_model_selected",
                    }
                return {
                    "resolved_model": requested_model,
                    "resolved_provider": selected_provider,
                    "reason": "requested_model_matches_provider",
                }

        def orchestrator_factory(*, conversation_id, show_reasoning):
            return _StubOrchestrator([
                json_for_content("ok"),
                json_for_done("ok"),
            ])

        with (
            patch("backend.services.chat_service._get_orchestrator_factory", return_value=orchestrator_factory),
            patch("backend.services.chat_service._get_policy_engine_service", return_value=_StubPolicyEngine()),
        ):
            events = []
            async for chunk, actual_content in stream_scheduled_orchestrator_events(
                orchestrator=_StubProviderAwareOrchestrator(),
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
                            "child_run_id": "backend-run-1",
                            "child_display_id": "backend-run-1",
                            "run_id": "backend-run-1",
                        },
                    ],
                },
            ):
                events.append((chunk, actual_content))

        joined = "\n".join(chunk for chunk, _content in events)
        self.assertIn("subagent_policy_selected", joined)
        self.assertIn("\"model_name\": \"llama3.1\"", joined)
        self.assertIn("\"provider_name\": \"ollama\"", joined)
        policy_event = next(
            json.loads(chunk)
            for chunk, _content in events
            if '"status_kind": "subagent_policy_selected"' in chunk
        )
        self.assertEqual(policy_event["child_run_id"], "backend-run-1")
        self.assertEqual(policy_event["child_display_id"], "backend-run-1")

    async def test_run_parallel_child_execution_switches_provider_on_failure(self):
        class _FailThenPassOrchestrator:
            def __init__(self):
                self.calls = []

            async def process_message(self, user_message: str, selected_model: str, execution_context=None):
                self.calls.append(selected_model)
                if selected_model == "doubao":
                    raise RuntimeError("provider failure")
                yield json_for_content("ok")
                yield json_for_done("ok")

        class _PolicyEngine:
            @staticmethod
            def select_model_for_provider(*, requested_model, selected_provider, available_models):
                if selected_provider == "ollama":
                    return {"resolved_model": "llama3.1", "resolved_provider": "ollama", "reason": "fallback"}
                return {"resolved_model": requested_model, "resolved_provider": selected_provider, "reason": "keep"}

        orchestrator_instance = _FailThenPassOrchestrator()

        def _factory(*, conversation_id, show_reasoning):
            return orchestrator_instance

        child_payload = {
            "child_execution_id": "backend-child-p10-i23-c1",
            "agent_role": "backend",
            "agent_id": "backend-agent-p10-i23-c1",
            "model_name": "doubao",
            "provider_name": "volcengine-ark",
            "provider_order": ["volcengine-ark", "ollama"],
        }

        from backend.services.chat_service import _run_parallel_child_execution
        result = await _run_parallel_child_execution(
            orchestrator_factory=_factory,
            db=None,
            user_id=1,
            conversation_id=99,
            show_reasoning=False,
            user_message="执行任务",
            model_name="doubao",
            child_payload=child_payload,
            child_context=SimpleNamespace(agent_role="backend", agent_id="backend-agent-p10-i23-c1"),
            scheduler_policy={"timeout_seconds": 2, "max_retries": 1},
            policy_engine=_PolicyEngine(),
            model_catalog=[
                {"name": "doubao", "provider": "volcengine-ark"},
                {"name": "llama3.1", "provider": "ollama"},
            ],
        )
        _payload, _ctx, output_text, outcome = result
        self.assertEqual(outcome["status"], "completed")
        self.assertEqual(output_text, "ok")
        self.assertEqual(child_payload["provider_name"], "ollama")
        self.assertEqual(child_payload["model_name"], "llama3.1")
        self.assertEqual(outcome["provider_switch_count"], 1)


class RuntimeRunScopeTests(unittest.TestCase):
    def test_extract_execution_run_scope_prefers_child_display_id(self):
        scope = _extract_execution_run_scope({
            "run_id": "run-main-01",
            "parent_run_id": "sched-p10-i23",
            "child_execution_id": "backend-child-p10-i23-c1",
            "child_run_id": "backend-run-1",
            "child_display_id": "backend-run-1",
            "scheduler_run_id": "sched-p10-i23",
            "plan_id": 10,
            "plan_item_id": 23,
            "agent_role": "backend",
            "agent_id": "backend-agent-p10-i23-c1",
        })

        self.assertEqual(scope["child_run_id"], "backend-run-1")
        self.assertEqual(scope["child_display_id"], "backend-run-1")

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
        self.assertEqual(permission_event["source"], "governance")
        self.assertEqual(permission_event["event_type"], "tool_permission_required")
        self.assertEqual(permission_event["execution_context"]["agent_role"], "frontend")
        self.assertEqual(permission_event["payload"]["approval_request_id"], "perm-1")
        self.assertEqual(permission_event["payload"]["tool_args"], {})
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
