import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.services.run_trace_service import RunTraceService


class _StubPlannerService:
    def __init__(self, db):
        self.db = db
        self.active_item = SimpleNamespace(id=23, title="执行步骤")
        self.plan = SimpleNamespace(id=10, active_item_id=23, items=[self.active_item])

    def get_latest_plan_for_conversation(self, *, user_id, conversation_id):
        if user_id == 1 and conversation_id == 99:
            return self.plan
        return None

    def get_active_item(self, *, plan):
        return self.active_item


class _StubSchedulerService:
    calls = []
    audit_calls = []

    def __init__(self, db):
        self.db = db

    def append_run_trace_event(self, **kwargs):
        self.__class__.calls.append(kwargs)
        return kwargs.get("plan")

    def append_audit_event(self, **kwargs):
        self.__class__.audit_calls.append(kwargs)
        return kwargs.get("plan")


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


if __name__ == "__main__":
    unittest.main()
