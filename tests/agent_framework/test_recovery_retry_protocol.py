import unittest

from backend.agent_framework.recovery_operations import (
    build_recovery_operation_contract,
    build_recovery_operation_record,
    build_recovery_retry_evidence,
    build_recovery_retry_policy_contract,
    is_recovery_reason_retryable,
    is_recovery_reason_terminal,
)


class RecoveryRetryProtocolTests(unittest.TestCase):
    def test_retry_policy_contract_declares_evidence_without_execution(self):
        policy = build_recovery_retry_policy_contract()

        self.assertEqual(policy["contract_version"], "phase-ii-recovery-retry-protocol-v1")
        self.assertFalse(policy["implemented"])
        self.assertTrue(policy["evidence_supported"])
        self.assertEqual(policy["max_attempts"], 3)
        self.assertEqual(policy["backoff_strategy"], "bounded_exponential")
        self.assertIn("transient_workspace_unavailable", policy["retryable_reasons"])
        self.assertIn("worker_ownership_lost", policy["terminal_reasons"])
        self.assertTrue(policy["non_executable_payload"])

    def test_recovery_operation_contract_exposes_retry_policy(self):
        contract = build_recovery_operation_contract()

        self.assertIn("retry_policy", contract)
        self.assertFalse(contract["retry_policy"]["implemented"])
        self.assertTrue(contract["retry_policy"]["evidence_supported"])

    def test_reason_classification_separates_retryable_and_terminal(self):
        self.assertTrue(is_recovery_reason_retryable("transient_workspace_unavailable"))
        self.assertFalse(is_recovery_reason_retryable("missing_registered_binding"))
        self.assertTrue(is_recovery_reason_terminal("stale_worker_fencing_token"))
        self.assertTrue(is_recovery_reason_terminal("worker_ownership_lost"))
        self.assertFalse(is_recovery_reason_terminal("transient_workspace_unavailable"))

    def test_retry_evidence_marks_retryable_attempt(self):
        retry = build_recovery_retry_evidence(
            attempt_number=2,
            previous_operation_id="recovery_operation:run-1:first",
            idempotency_key="recovery:run-1:submit_approval.approved",
            recovery_reason="transient_workspace_unavailable",
        )

        self.assertEqual(retry["attempt_number"], 2)
        self.assertEqual(retry["max_attempts"], 3)
        self.assertTrue(retry["retryable"])
        self.assertFalse(retry["terminal"])
        self.assertEqual(retry["status"], "retryable")

    def test_retry_evidence_marks_terminal_reason(self):
        retry = build_recovery_retry_evidence(
            attempt_number=1,
            previous_operation_id="recovery_operation:run-1:first",
            idempotency_key="recovery:run-1:submit_approval.approved",
            recovery_reason="worker_ownership_lost",
        )

        self.assertFalse(retry["retryable"])
        self.assertTrue(retry["terminal"])
        self.assertEqual(retry["status"], "terminal")

    def test_retry_evidence_marks_exhausted_final_attempt(self):
        retry = build_recovery_retry_evidence(
            attempt_number=3,
            previous_operation_id="recovery_operation:run-1:first",
            idempotency_key="recovery:run-1:submit_approval.approved",
            recovery_reason="transient_workspace_unavailable",
            max_attempts=3,
        )

        self.assertTrue(retry["retryable"])
        self.assertTrue(retry["terminal"])
        self.assertEqual(retry["status"], "exhausted")

    def test_operation_record_omits_retry_by_default(self):
        record = build_recovery_operation_record(
            run_id="run-1",
            entrypoint="submit_approval.approved",
            operation_status="recovered",
            recovery_reason="ready_via_registry",
            continuation_kind="tool_approval",
            continuation_id="approval-1",
            workspace_backend={"backend_kind": "sqlalchemy", "backend_mode": "strict", "durable": True},
            recorded_at="2026-05-23T09:00:00+00:00",
        )

        self.assertNotIn("retry", record)

    def test_operation_record_compacts_retry_evidence(self):
        retry = build_recovery_retry_evidence(
            attempt_number=2,
            previous_operation_id="recovery_operation:run-1:first",
            idempotency_key="recovery:run-1:submit_approval.approved",
            recovery_reason="transient_workspace_unavailable",
        )
        retry["handler"] = lambda: None

        record = build_recovery_operation_record(
            run_id="run-1",
            entrypoint="submit_approval.approved",
            operation_status="attempted",
            recovery_reason="transient_workspace_unavailable",
            continuation_kind="tool_approval",
            continuation_id="approval-1",
            workspace_backend={"backend_kind": "sqlalchemy", "backend_mode": "strict", "durable": True},
            recorded_at="2026-05-23T09:00:00+00:00",
            retry=retry,
        )

        compact = record["retry"]
        self.assertEqual(compact["attempt_number"], 2)
        self.assertEqual(compact["max_attempts"], 3)
        self.assertEqual(compact["previous_operation_id"], "recovery_operation:run-1:first")
        self.assertEqual(compact["idempotency_key"], "recovery:run-1:submit_approval.approved")
        self.assertEqual(compact["status"], "retryable")
        self.assertTrue(compact["retryable"])
        self.assertNotIn("handler", compact)


if __name__ == "__main__":
    unittest.main()
