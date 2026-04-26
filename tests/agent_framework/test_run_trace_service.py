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

    def __init__(self, db):
        self.db = db

    def append_run_trace_event(self, **kwargs):
        self.__class__.calls.append(kwargs)
        return kwargs.get("plan")


class RunTraceServiceTests(unittest.TestCase):
    def setUp(self):
        _StubSchedulerService.calls = []
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


if __name__ == "__main__":
    unittest.main()
