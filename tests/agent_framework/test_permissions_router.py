import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.routers.permissions import (
    PermissionApproveRequest,
    PermissionDenyRequest,
    approve_permission,
    deny_permission,
)


class _StubPermissionService:
    def __init__(self):
        self.request = SimpleNamespace(
            id="req-1",
            tool_name="mcp_filesystem_read",
            tool_args={"path": "/tmp/demo.txt"},
            user_id=1,
            conversation_id=99,
            plan_id=7,
            plan_item_id=13,
            run_id="child-run-13",
            parent_run_id="sched-run-7",
            child_run_id="child-run-13",
            scheduler_run_id="sched-run-7",
            run_kind="child",
        )
        self.approved = []
        self.denied = []

    def get_request(self, request_id):
        if request_id == self.request.id:
            return self.request
        return None

    def approve(self, request_id, result=None):
        self.approved.append((request_id, result))
        return request_id == self.request.id

    def deny(self, request_id):
        self.denied.append(request_id)
        return request_id == self.request.id


class _StubRunTraceService:
    calls = []
    audit_calls = []
    runtime_calls = []
    runtime_audit_calls = []

    def append_latest_active_item_trace(self, **kwargs):
        self.__class__.calls.append(kwargs)
        return True

    def append_latest_active_item_audit(self, **kwargs):
        self.__class__.audit_calls.append(kwargs)
        return True

    def append_runtime_trace(self, **kwargs):
        self.__class__.runtime_calls.append(kwargs)
        return True

    def append_runtime_audit(self, **kwargs):
        self.__class__.runtime_audit_calls.append(kwargs)
        return True

    def build_snapshot_ref(self, **kwargs):
        return {
            "snapshot_id": "PERM-REF-99",
            "generated_at": "2026-05-02T00:00:00Z",
            **kwargs,
        }


class PermissionsRouterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.permission_service = _StubPermissionService()
        _StubRunTraceService.calls = []
        _StubRunTraceService.audit_calls = []
        _StubRunTraceService.runtime_calls = []
        _StubRunTraceService.runtime_audit_calls = []

    @patch("backend.routers.permissions.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.permissions.get_permission_service")
    async def test_approve_permission_appends_success_trace(self, mock_permission_service, _mock_trace_service):
        mock_permission_service.return_value = self.permission_service

        payload = await approve_permission(
            PermissionApproveRequest(request_id="req-1", result="approved"),
            db=object(),
        )

        self.assertTrue(payload["success"])
        self.assertEqual(len(_StubRunTraceService.runtime_calls), 1)
        self.assertEqual(_StubRunTraceService.runtime_calls[0]["event_type"], "permission_approved")
        self.assertEqual(_StubRunTraceService.runtime_calls[0]["source"], "permission")
        self.assertEqual(_StubRunTraceService.runtime_calls[0]["run_id"], "child-run-13")
        self.assertEqual(_StubRunTraceService.runtime_calls[0]["payload"]["snapshot_ref"]["snapshot_id"], "PERM-REF-99")
        self.assertEqual(len(_StubRunTraceService.runtime_audit_calls), 1)
        self.assertEqual(_StubRunTraceService.runtime_audit_calls[0]["event_type"], "permission_approved")

    @patch("backend.routers.permissions.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.permissions.get_permission_service")
    async def test_deny_permission_appends_warning_trace(self, mock_permission_service, _mock_trace_service):
        mock_permission_service.return_value = self.permission_service

        payload = await deny_permission(
            PermissionDenyRequest(request_id="req-1"),
            db=object(),
        )

        self.assertTrue(payload["success"])
        self.assertEqual(len(_StubRunTraceService.runtime_calls), 1)
        self.assertEqual(_StubRunTraceService.runtime_calls[0]["event_type"], "permission_denied")
        self.assertEqual(_StubRunTraceService.runtime_calls[0]["severity"], "warning")
        self.assertEqual(_StubRunTraceService.runtime_calls[0]["payload"]["snapshot_ref"]["snapshot_id"], "PERM-REF-99")
        self.assertEqual(len(_StubRunTraceService.runtime_audit_calls), 1)
        self.assertEqual(_StubRunTraceService.runtime_audit_calls[0]["event_type"], "permission_denied")


if __name__ == "__main__":
    unittest.main()
