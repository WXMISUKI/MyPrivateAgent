import unittest
from types import SimpleNamespace

from fastapi import HTTPException

from backend.services.server_service import (
    build_error_event,
    build_sse_event,
    ensure_exists,
    permission_request_to_dict,
    success_response,
)


class ServerServiceTests(unittest.TestCase):
    def test_build_sse_event_formats_payload(self):
        payload = build_sse_event({"type": "content", "content": "舟山天气"})
        self.assertTrue(payload.startswith("data: "))
        self.assertIn("舟山天气", payload)
        self.assertTrue(payload.endswith("\n\n"))

    def test_build_sse_event_accepts_raw_json_string(self):
        payload = build_sse_event('{"type":"content","content":"舟山天气"}')
        self.assertEqual(payload, 'data: {"type":"content","content":"舟山天气"}\n\n')

    def test_build_error_event_uses_standard_shape(self):
        payload = build_error_event("出错了")
        self.assertIn('"type": "error"', payload)
        self.assertIn('"error": "出错了"', payload)

    def test_ensure_exists_raises_404(self):
        with self.assertRaises(HTTPException) as context:
            ensure_exists(None, "不存在")
        self.assertEqual(context.exception.status_code, 404)

    def test_success_response_merges_extra_fields(self):
        payload = success_response("完成", conversation_id=7)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["conversation_id"], 7)

    def test_permission_request_to_dict_serializes_status_and_result(self):
        request = SimpleNamespace(
            id="req_1",
            tool_name="search",
            tool_args={"query": "舟山天气"},
            permission_level="ask",
            conversation_id=10,
            plan_id=13,
            plan_item_id=17,
            run_id="child-run-001",
            parent_run_id="sched-run-001",
            child_run_id="child-run-001",
            child_display_id="child-run-001",
            scheduler_run_id="sched-run-001",
            run_kind="child",
            status=SimpleNamespace(value="pending"),
            created_at=SimpleNamespace(isoformat=lambda: "2026-04-23T12:00:00"),
            result="approved",
        )
        payload = permission_request_to_dict(request, include_result=True)
        self.assertEqual(payload["id"], "req_1")
        self.assertEqual(payload["status"], "pending")
        self.assertEqual(payload["result"], "approved")
        self.assertEqual(payload["child_display_id"], "child-run-001")
        self.assertEqual(payload["runtime_scope"]["child_display_id"], "child-run-001")


if __name__ == "__main__":
    unittest.main()
