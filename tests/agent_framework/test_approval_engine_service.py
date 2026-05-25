import unittest

from backend.services.approval_engine_service import get_approval_engine_service
from backend.services.scheduler_runtime_entities import ApprovalRequestState


class ApprovalEngineServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = get_approval_engine_service()

    def test_create_tool_approval_request_returns_formal_runtime_state(self):
        approval = self.service.create_tool_approval_request(
            request_id="perm-approval-001",
            tool_name="mcp_filesystem_write",
            tool_args={"path": "README.md"},
            context={
                "user_id": 7,
                "conversation_id": 11,
                "plan_id": 13,
                "plan_item_id": 17,
                "run_id": "child-run-001",
                "parent_run_id": "sched-run-001",
                "child_run_id": "child-run-001",
                "child_display_id": "child-run-001",
                "scheduler_run_id": "sched-run-001",
                "run_kind": "child",
                "source_event_type": "tool_permission_required",
                "agent_role": "backend",
                "agent_id": "backend-agent-001",
            },
            permission_level="ask",
            reason="命中高风险工具治理策略，需要人工审批。",
            reason_code="high_risk_tool_requires_approval",
            requested_at="2026-05-11T09:00:00Z",
            request_metadata={"tool_call_id": "call-001"},
        )

        self.assertIsInstance(approval, ApprovalRequestState)
        serialized = approval.to_dict()

        self.assertEqual(serialized["request_id"], "perm-approval-001")
        self.assertTrue(serialized["requires_approval"])
        self.assertEqual(serialized["request_kind"], "tool_permission")
        self.assertEqual(serialized["reason_code"], "high_risk_tool_requires_approval")
        self.assertEqual(serialized["requested_by_role"], "backend")
        self.assertEqual(serialized["requested_by_agent_id"], "backend-agent-001")
        self.assertEqual(serialized["child_run_id"], "child-run-001")
        self.assertEqual(serialized["child_display_id"], "child-run-001")
        self.assertEqual(serialized["tool_args"]["path"], "README.md")
        self.assertEqual(serialized["request_metadata"]["tool_call_id"], "call-001")

    def test_create_tool_approval_request_normalizes_defaults(self):
        approval = self.service.create_tool_approval_request(
            request_id=" perm-approval-002 ",
            tool_name=" mcp_filesystem_write ",
            tool_args=None,
            context=None,
            reason_code="",
            reason="",
        )

        serialized = approval.to_dict()

        self.assertEqual(serialized["request_id"], "perm-approval-002")
        self.assertEqual(serialized["tool_name"], "mcp_filesystem_write")
        self.assertEqual(serialized["permission_level"], "ask")
        self.assertEqual(serialized["source_event_type"], "tool_permission_required")
        self.assertTrue(serialized["requires_approval"])
        self.assertIsNone(serialized["reason_code"])
        self.assertEqual(serialized["tool_args"], {})
        self.assertEqual(serialized["request_metadata"], {})

    def test_submit_pending_approval_accepts_decision_and_updates_state(self):
        approval = self.service.create_tool_approval_request(
            request_id="perm-approval-003",
            tool_name="filesystem_write",
            tool_args={"path": "case.md"},
            context={"run_id": "run-003"},
        )

        submission = self.service.submit_approval_decision(
            approval,
            "approved",
            completed_at="2026-05-21T08:00:00Z",
        )

        self.assertEqual(submission["status"], "accepted")
        self.assertEqual(submission["reason"], "approval_resolved")
        self.assertEqual(submission["event_status_kind"], "approval_resolved")
        self.assertEqual(submission["original_decision"], "pending")
        self.assertEqual(submission["attempted_decision"], "approved")
        self.assertEqual(approval.status, "approved")
        self.assertEqual(approval.result, "approved")
        self.assertEqual(approval.completed_at, "2026-05-21T08:00:00Z")
        self.assertFalse(approval.requires_approval)

    def test_submit_resolved_approval_replays_same_decision_without_mutating_state(self):
        approval = self.service.create_tool_approval_request(
            request_id="perm-approval-004",
            tool_name="filesystem_write",
            tool_args={"path": "case.md"},
            context={"run_id": "run-004"},
        )
        self.service.submit_approval_decision(
            approval,
            "approved",
            completed_at="2026-05-21T08:00:00Z",
        )

        submission = self.service.submit_approval_decision(
            approval,
            "approved",
            completed_at="2026-05-21T09:00:00Z",
        )

        self.assertEqual(submission["status"], "replayed")
        self.assertEqual(submission["reason"], "approval_already_resolved")
        self.assertEqual(submission["event_status_kind"], "approval_replayed")
        self.assertEqual(submission["original_decision"], "approved")
        self.assertEqual(submission["attempted_decision"], "approved")
        self.assertEqual(approval.status, "approved")
        self.assertEqual(approval.completed_at, "2026-05-21T08:00:00Z")

    def test_submit_resolved_approval_ignores_reversal_without_mutating_state(self):
        approval = self.service.create_tool_approval_request(
            request_id="perm-approval-005",
            tool_name="filesystem_write",
            tool_args={"path": "case.md"},
            context={"run_id": "run-005"},
        )
        self.service.submit_approval_decision(
            approval,
            "denied",
            completed_at="2026-05-21T08:00:00Z",
        )

        submission = self.service.submit_approval_decision(
            approval,
            "approved",
            completed_at="2026-05-21T09:00:00Z",
        )

        self.assertEqual(submission["status"], "ignored")
        self.assertEqual(submission["reason"], "approval_already_resolved")
        self.assertEqual(submission["event_status_kind"], "approval_ignored")
        self.assertEqual(submission["original_decision"], "denied")
        self.assertEqual(submission["attempted_decision"], "approved")
        self.assertEqual(approval.status, "denied")
        self.assertEqual(approval.completed_at, "2026-05-21T08:00:00Z")


if __name__ == "__main__":
    unittest.main()
