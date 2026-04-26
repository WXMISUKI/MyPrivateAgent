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

    def append_latest_active_item_trace(self, **kwargs):
        self.__class__.calls.append(kwargs)
        return True


class PermissionsRouterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.permission_service = _StubPermissionService()
        _StubRunTraceService.calls = []

    @patch("backend.routers.permissions.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.permissions.get_permission_service")
    async def test_approve_permission_appends_success_trace(self, mock_permission_service, _mock_trace_service):
        mock_permission_service.return_value = self.permission_service

        payload = await approve_permission(
            PermissionApproveRequest(request_id="req-1", result="approved"),
            db=object(),
        )

        self.assertTrue(payload["success"])
        self.assertEqual(len(_StubRunTraceService.calls), 1)
        self.assertEqual(_StubRunTraceService.calls[0]["event_type"], "permission_approved")
        self.assertEqual(_StubRunTraceService.calls[0]["source"], "permission")

    @patch("backend.routers.permissions.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.permissions.get_permission_service")
    async def test_deny_permission_appends_warning_trace(self, mock_permission_service, _mock_trace_service):
        mock_permission_service.return_value = self.permission_service

        payload = await deny_permission(
            PermissionDenyRequest(request_id="req-1"),
            db=object(),
        )

        self.assertTrue(payload["success"])
        self.assertEqual(len(_StubRunTraceService.calls), 1)
        self.assertEqual(_StubRunTraceService.calls[0]["event_type"], "permission_denied")
        self.assertEqual(_StubRunTraceService.calls[0]["severity"], "warning")


if __name__ == "__main__":
    unittest.main()
