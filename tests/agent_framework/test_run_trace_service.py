import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.services.run_trace_service import RunTraceService


class _StubPlannerService:
    def __init__(self, db):
        self.db = db
        self.active_item = SimpleNamespace(id=23, title="执行步骤")
        self.runtime_item = SimpleNamespace(id=24, title="子执行步骤")
        self.plan = SimpleNamespace(id=10, active_item_id=23, items=[self.active_item, self.runtime_item])

    def get_latest_plan_for_conversation(self, *, user_id, conversation_id):
        if user_id == 1 and conversation_id == 99:
            return self.plan
        return None

    def get_active_item(self, *, plan):
        return self.active_item

    def resolve_runtime_target(
        self,
        *,
        user_id,
        conversation_id=None,
        plan_id=None,
        item_id=None,
        run_id=None,
        child_run_id=None,
        search_limit=50,
    ):
        if user_id != 1:
            return None, None
        if plan_id == 10:
            return self.plan, self.active_item
        if plan_id is not None:
            return None, None
        if item_id == 24:
            return self.plan, self.runtime_item
        if run_id == "sched-p10-i24" or child_run_id == "backend-child-p10-i24-c1":
            return self.plan, self.runtime_item
        if item_id is not None or run_id or child_run_id:
            return None, None
        if conversation_id == 99:
            return self.plan, self.active_item
        return None, None


class _StubSchedulerService:
    calls = []
    audit_calls = []
    trace_events = []

    def __init__(self, db):
        self.db = db

    def append_run_trace_event(self, **kwargs):
        self.__class__.calls.append(kwargs)
        return kwargs.get("plan")

    def append_audit_event(self, **kwargs):
        self.__class__.audit_calls.append(kwargs)
        return kwargs.get("plan")

    def filter_run_trace(self, item, **kwargs):
        return [
            dict(event)
            for event in self.__class__.trace_events
            if not kwargs.get("source") or event.get("source") == kwargs.get("source")
        ]


class _StubConversation:
    id = 99
    user_id = 1


class _StubConversationQuery:
    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return _StubConversation()


class _StubDb:
    def query(self, _model):
        return _StubConversationQuery()


class RunTraceServiceTests(unittest.TestCase):
    def setUp(self):
        _StubSchedulerService.calls = []
        _StubSchedulerService.audit_calls = []
        _StubSchedulerService.trace_events = []
        self.service = RunTraceService(db=object())

    @patch.object(RunTraceService, "_get_planner_service", return_value=_StubPlannerService)
    @patch.object(RunTraceService, "_get_scheduler_service", return_value=_StubSchedulerService)
    def test_append_latest_active_item_trace_appends_to_active_plan_item(self, _mock_scheduler, _mock_planner):
        success = self.service.append_latest_active_item_trace(
            user_id=1,
            conversation_id=99,
            source="permission",
            event_type="permission_approved",
            summary="权限已批准",
            detail="允许执行",
            severity="success",
            payload={"request_id": "req-1"},
        )

        self.assertTrue(success)
        self.assertEqual(len(_StubSchedulerService.calls), 1)
        self.assertEqual(_StubSchedulerService.calls[0]["item_id"], 23)
        self.assertEqual(_StubSchedulerService.calls[0]["event_type"], "permission_approved")

    @patch.object(RunTraceService, "_get_planner_service", return_value=_StubPlannerService)
    @patch.object(RunTraceService, "_get_scheduler_service", return_value=_StubSchedulerService)
    def test_append_latest_active_item_trace_canonicalizes_payload_plan_scope(self, _mock_scheduler, _mock_planner):
        success = self.service.append_latest_active_item_trace(
            user_id=1,
            conversation_id=99,
            source="permission",
            event_type="permission_approved",
            summary="权限已批准",
            payload={"plan_id": 999, "plan_item_id": 998},
        )

        self.assertTrue(success)
        self.assertEqual(_StubSchedulerService.calls[-1]["item_id"], 23)
        self.assertEqual(_StubSchedulerService.calls[-1]["payload"]["plan_id"], 10)
        self.assertEqual(_StubSchedulerService.calls[-1]["payload"]["plan_item_id"], 23)

    @patch.object(RunTraceService, "_get_planner_service", return_value=_StubPlannerService)
    @patch.object(RunTraceService, "_get_scheduler_service", return_value=_StubSchedulerService)
    def test_append_latest_active_item_trace_returns_false_when_plan_missing(self, _mock_scheduler, _mock_planner):
        success = self.service.append_latest_active_item_trace(
            user_id=1,
            conversation_id=1000,
            source="permission",
            event_type="permission_denied",
            summary="权限已拒绝",
        )

        self.assertFalse(success)
        self.assertEqual(_StubSchedulerService.calls, [])

    @patch.object(RunTraceService, "_get_conversation_model", return_value=_StubConversation)
    @patch.object(RunTraceService, "_get_planner_service", return_value=_StubPlannerService)
    @patch.object(RunTraceService, "_get_scheduler_service", return_value=_StubSchedulerService)
    def test_append_latest_active_item_trace_resolves_user_id_from_conversation(self, _mock_scheduler, _mock_planner, _mock_conversation):
        self.service = RunTraceService(db=_StubDb())
        success = self.service.append_latest_active_item_trace(
            user_id=None,
            conversation_id=99,
            source="doctor",
            event_type="doctor_run_completed",
            summary="Doctor 已完成",
        )

        self.assertTrue(success)
        self.assertEqual(len(_StubSchedulerService.calls), 1)
        self.assertEqual(_StubSchedulerService.calls[0]["event_type"], "doctor_run_completed")

    @patch.object(RunTraceService, "_get_conversation_model", return_value=_StubConversation)
    @patch.object(RunTraceService, "_get_planner_service", return_value=_StubPlannerService)
    @patch.object(RunTraceService, "_get_scheduler_service", return_value=_StubSchedulerService)
    def test_append_latest_active_item_audit_appends_to_active_plan_item(self, _mock_scheduler, _mock_planner, _mock_conversation):
        self.service = RunTraceService(db=_StubDb())
        success = self.service.append_latest_active_item_audit(
            user_id=None,
            conversation_id=99,
            event_type="doctor_run_started",
            content="Doctor 启动",
            payload={"scope": "startup"},
        )

        self.assertTrue(success)
        self.assertEqual(len(_StubSchedulerService.audit_calls), 1)
        self.assertEqual(_StubSchedulerService.audit_calls[0]["event_type"], "doctor_run_started")

    @patch.object(RunTraceService, "_get_planner_service", return_value=_StubPlannerService)
    @patch.object(RunTraceService, "_get_scheduler_service", return_value=_StubSchedulerService)
    def test_append_latest_active_item_trace_returns_false_when_context_missing(self, _mock_scheduler, _mock_planner):
        success = self.service.append_latest_active_item_trace(
            user_id=None,
            conversation_id=None,
            source="runtime",
            event_type="agent_state_changed",
            summary="状态迁移",
        )

        self.assertFalse(success)
        self.assertEqual(_StubSchedulerService.calls, [])

    @patch.object(RunTraceService, "_get_planner_service", return_value=_StubPlannerService)
    @patch.object(RunTraceService, "_get_scheduler_service", return_value=_StubSchedulerService)
    def test_append_runtime_trace_supports_run_scope_lookup(self, _mock_scheduler, _mock_planner):
        success = self.service.append_runtime_trace(
            user_id=1,
            conversation_id=99,
            run_id="sched-p10-i24",
            source="scheduler",
            event_type="scheduler_merged",
            summary="调度器已合并",
        )

        self.assertTrue(success)
        self.assertEqual(_StubSchedulerService.calls[-1]["item_id"], 24)
        self.assertEqual(_StubSchedulerService.calls[-1]["payload"]["run_id"], "sched-p10-i24")

    @patch.object(RunTraceService, "_get_planner_service", return_value=_StubPlannerService)
    @patch.object(RunTraceService, "_get_scheduler_service", return_value=_StubSchedulerService)
    def test_append_runtime_trace_prefers_explicit_run_scope_over_payload_scope(self, _mock_scheduler, _mock_planner):
        success = self.service.append_runtime_trace(
            user_id=1,
            conversation_id=99,
            run_id="sched-p10-i24",
            child_run_id="backend-child-p10-i24-c1",
            source="scheduler",
            event_type="scheduler_merged",
            summary="调度器已合并",
            payload={"run_id": "stale-run", "child_run_id": "stale-child"},
        )

        self.assertTrue(success)
        self.assertEqual(_StubSchedulerService.calls[-1]["payload"]["run_id"], "sched-p10-i24")
        self.assertEqual(_StubSchedulerService.calls[-1]["payload"]["child_run_id"], "backend-child-p10-i24-c1")
        self.assertEqual(_StubSchedulerService.calls[-1]["payload"]["plan_id"], 10)
        self.assertEqual(_StubSchedulerService.calls[-1]["payload"]["plan_item_id"], 24)

    @patch.object(RunTraceService, "_get_planner_service", return_value=_StubPlannerService)
    @patch.object(RunTraceService, "_get_scheduler_service", return_value=_StubSchedulerService)
    def test_append_runtime_audit_prefers_explicit_child_run_scope_over_stale_plan_scope(self, _mock_scheduler, _mock_planner):
        success = self.service.append_runtime_audit(
            user_id=1,
            conversation_id=99,
            child_run_id="backend-child-p10-i24-c1",
            event_type="child_completed",
            content="子执行完成",
            payload={"plan_id": 999, "plan_item_id": 998},
        )

        self.assertTrue(success)
        self.assertEqual(_StubSchedulerService.audit_calls[-1]["item_id"], 24)
        self.assertEqual(_StubSchedulerService.audit_calls[-1]["payload"]["child_run_id"], "backend-child-p10-i24-c1")
        self.assertEqual(_StubSchedulerService.audit_calls[-1]["payload"]["plan_id"], 10)
        self.assertEqual(_StubSchedulerService.audit_calls[-1]["payload"]["plan_item_id"], 24)

    @patch.object(RunTraceService, "_get_planner_service", return_value=_StubPlannerService)
    @patch.object(RunTraceService, "_get_scheduler_service", return_value=_StubSchedulerService)
    def test_append_runtime_trace_prefers_explicit_plan_scope_over_payload_scope(self, _mock_scheduler, _mock_planner):
        success = self.service.append_runtime_trace(
            user_id=1,
            conversation_id=99,
            plan_id=10,
            source="scheduler",
            event_type="scheduler_merged",
            summary="调度器已合并",
            payload={"plan_id": 999, "plan_item_id": 998},
        )

        self.assertTrue(success)
        self.assertEqual(_StubSchedulerService.calls[-1]["item_id"], 23)
        self.assertEqual(_StubSchedulerService.calls[-1]["payload"]["plan_id"], 10)
        self.assertEqual(_StubSchedulerService.calls[-1]["payload"]["plan_item_id"], 23)

    @patch.object(RunTraceService, "_get_planner_service", return_value=_StubPlannerService)
    @patch.object(RunTraceService, "_get_scheduler_service", return_value=_StubSchedulerService)
    def test_append_runtime_audit_supports_child_run_scope_lookup(self, _mock_scheduler, _mock_planner):
        success = self.service.append_runtime_audit(
            user_id=1,
            conversation_id=99,
            child_run_id="backend-child-p10-i24-c1",
            event_type="child_completed",
            content="子执行完成",
        )

        self.assertTrue(success)
        self.assertEqual(_StubSchedulerService.audit_calls[-1]["item_id"], 24)

    @patch.object(RunTraceService, "_get_planner_service", return_value=_StubPlannerService)
    @patch.object(RunTraceService, "_get_scheduler_service", return_value=_StubSchedulerService)
    def test_append_runtime_trace_does_not_fallback_when_run_scope_is_explicit_but_missing(self, _mock_scheduler, _mock_planner):
        success = self.service.append_runtime_trace(
            user_id=1,
            conversation_id=99,
            run_id="sched-p10-i999",
            source="scheduler",
            event_type="scheduler_missing",
            summary="未找到目标运行",
        )

        self.assertFalse(success)
        self.assertEqual(_StubSchedulerService.calls, [])

    @patch.object(RunTraceService, "_get_planner_service", return_value=_StubPlannerService)
    @patch.object(RunTraceService, "_get_scheduler_service", return_value=_StubSchedulerService)
    def test_append_runtime_audit_does_not_fallback_when_item_scope_is_explicit_but_missing(self, _mock_scheduler, _mock_planner):
        success = self.service.append_runtime_audit(
            user_id=1,
            conversation_id=99,
            item_id=999,
            event_type="runtime_missing",
            content="未找到目标步骤",
        )

        self.assertFalse(success)
        self.assertEqual(_StubSchedulerService.audit_calls, [])

    @patch.object(RunTraceService, "_get_planner_service", return_value=_StubPlannerService)
    @patch.object(RunTraceService, "_get_scheduler_service", return_value=_StubSchedulerService)
    def test_append_runtime_audit_prefers_explicit_item_scope_over_payload_scope(self, _mock_scheduler, _mock_planner):
        success = self.service.append_runtime_audit(
            user_id=1,
            conversation_id=99,
            item_id=24,
            event_type="runtime_checked",
            content="目标步骤已校验",
            payload={"plan_id": 999, "plan_item_id": 998},
        )

        self.assertTrue(success)
        self.assertEqual(_StubSchedulerService.audit_calls[-1]["item_id"], 24)
        self.assertEqual(_StubSchedulerService.audit_calls[-1]["payload"]["plan_id"], 10)
        self.assertEqual(_StubSchedulerService.audit_calls[-1]["payload"]["plan_item_id"], 24)

    @patch.object(RunTraceService, "_get_planner_service", return_value=_StubPlannerService)
    @patch.object(RunTraceService, "_get_scheduler_service", return_value=_StubSchedulerService)
    def test_append_runtime_trace_does_not_fallback_when_plan_scope_is_explicit_but_missing(self, _mock_scheduler, _mock_planner):
        success = self.service.append_runtime_trace(
            user_id=1,
            conversation_id=99,
            plan_id=999,
            source="scheduler",
            event_type="scheduler_missing",
            summary="未找到目标计划",
        )

        self.assertFalse(success)
        self.assertEqual(_StubSchedulerService.calls, [])

    @patch.object(RunTraceService, "_get_planner_service", return_value=_StubPlannerService)
    @patch.object(RunTraceService, "_get_scheduler_service", return_value=_StubSchedulerService)
    def test_has_runtime_trace_fingerprint_prefers_dedupe_key(self, _mock_scheduler, _mock_planner):
        _StubSchedulerService.trace_events = [
            {
                "source": "runtime_contract",
                "event_type": "runtime_contract_gate_degraded",
                "payload": {
                    "fingerprint": "different-fingerprint",
                    "dedupe_key": "runtime_contract_gate_degraded:abc123",
                },
            }
        ]

        exists = self.service.has_runtime_trace_fingerprint(
            user_id=1,
            conversation_id=99,
            plan_id=10,
            source="runtime_contract",
            event_type="runtime_contract_gate_degraded",
            fingerprint="abc123",
            dedupe_key="runtime_contract_gate_degraded:abc123",
        )

        self.assertTrue(exists)

    @patch.object(RunTraceService, "_get_planner_service", return_value=_StubPlannerService)
    @patch.object(RunTraceService, "_get_scheduler_service", return_value=_StubSchedulerService)
    def test_has_runtime_trace_fingerprint_falls_back_to_fingerprint(self, _mock_scheduler, _mock_planner):
        _StubSchedulerService.trace_events = [
            {
                "source": "runtime_contract",
                "event_type": "runtime_contract_gate_degraded",
                "payload": {
                    "fingerprint": "legacy-fingerprint",
                },
            }
        ]

        exists = self.service.has_runtime_trace_fingerprint(
            user_id=1,
            conversation_id=99,
            plan_id=10,
            source="runtime_contract",
            event_type="runtime_contract_gate_degraded",
            fingerprint="legacy-fingerprint",
            dedupe_key="runtime_contract_gate_degraded:legacy-fingerprint",
        )

        self.assertTrue(exists)

    @patch.object(RunTraceService, "_get_planner_service", return_value=_StubPlannerService)
    @patch.object(RunTraceService, "_get_scheduler_service", return_value=_StubSchedulerService)
    def test_has_runtime_trace_dedupe_key_checks_payload_dedupe_key(self, _mock_scheduler, _mock_planner):
        _StubSchedulerService.trace_events = [
            {
                "source": "doctor",
                "event_type": "doctor_run_completed",
                "payload": {
                    "dedupe_key": "doctor_run_completed:conversation-99:startup",
                },
            }
        ]

        exists = self.service.has_runtime_trace_dedupe_key(
            user_id=1,
            conversation_id=99,
            source="doctor",
            event_type="doctor_run_completed",
            dedupe_key="doctor_run_completed:conversation-99:startup",
        )

        self.assertTrue(exists)


if __name__ == "__main__":
    unittest.main()
