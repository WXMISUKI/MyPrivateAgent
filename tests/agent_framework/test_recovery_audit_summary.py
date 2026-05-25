import unittest

from backend.agent_framework.recovery_operations import build_recovery_operation_contract
from backend.services.runtime_surface_builders import RuntimeRecoveryContractBuilder


class RecoveryAuditSummaryTests(unittest.TestCase):
    def test_recovery_operation_contract_exposes_audit_production_readiness(self):
        contract = build_recovery_operation_contract()

        readiness = contract["recovery_audit_production_readiness"]
        self.assertEqual(
            readiness["contract_version"],
            "phase-ii-recovery-audit-production-gate-v1",
        )
        self.assertTrue(readiness["ready"])
        self.assertTrue(readiness["operation_history_supported"])
        self.assertTrue(readiness["audit_summary_supported"])
        self.assertTrue(readiness["timeline_writer_available"])
        self.assertTrue(readiness["idempotent_trace_dedupe"])
        self.assertFalse(readiness["authorization_source"])

    def test_empty_operation_history_returns_stable_empty_summary(self):
        summary = RuntimeRecoveryContractBuilder.build_recovery_audit_summary([])

        self.assertEqual(summary["contract_version"], "phase-ii-recovery-audit-summary-v1")
        self.assertEqual(summary["operation_count"], 0)
        self.assertEqual(summary["latest_status"], "")
        self.assertEqual(summary["status_counts"], {})
        self.assertEqual(summary["retry_count"], 0)
        self.assertEqual(summary["latest_retry_status"], "")
        self.assertEqual(summary["latest_retry_terminal_reason"], "")
        self.assertFalse(summary["terminal"])
        self.assertFalse(summary["authorization_source"])

    def test_recovered_operation_summary_reports_latest_status_and_counts(self):
        operation = {
            "contract_version": "phase-ii-durable-recovery-operation-v1",
            "operation_id": "recovery_operation:run-1:submit:first",
            "run_id": "run-1",
            "entrypoint": "submit_approval.approved",
            "operation_status": "recovered",
            "recovery_reason": "ready_via_registry",
            "worker_ownership": {"implemented": False, "blocked_reason": "worker_ownership_not_implemented"},
            "recorded_at": "2026-05-23T09:00:00+00:00",
        }

        summary = RuntimeRecoveryContractBuilder.build_recovery_audit_summary([operation])

        self.assertEqual(summary["operation_count"], 1)
        self.assertEqual(summary["latest_status"], "recovered")
        self.assertEqual(summary["latest_entrypoint"], "submit_approval.approved")
        self.assertEqual(summary["latest_reason"], "ready_via_registry")
        self.assertEqual(summary["status_counts"], {"recovered": 1})
        self.assertEqual(summary["entrypoint_counts"], {"submit_approval.approved": 1})
        self.assertEqual(summary["reason_counts"], {"ready_via_registry": 1})
        self.assertFalse(summary["ownership_implemented"])
        self.assertFalse(summary["terminal"])

    def test_retry_and_terminal_distribution_is_reported(self):
        operations = [
            {
                "operation_id": "recovery_operation:run-1:submit:first",
                "run_id": "run-1",
                "entrypoint": "submit_approval.approved",
                "operation_status": "attempted",
                "recovery_reason": "transient_workspace_unavailable",
                "retry": {
                    "attempt_number": 1,
                    "max_attempts": 3,
                    "previous_operation_id": "",
                    "idempotency_key": "recovery:run-1:submit",
                    "status": "retryable",
                    "retryable": True,
                    "terminal": False,
                },
            },
            {
                "operation_id": "recovery_operation:run-1:submit:second",
                "run_id": "run-1",
                "entrypoint": "submit_approval.approved",
                "operation_status": "failed",
                "recovery_reason": "transient_workspace_unavailable",
                "retry": {
                    "attempt_number": 3,
                    "max_attempts": 3,
                    "previous_operation_id": "recovery_operation:run-1:submit:first",
                    "idempotency_key": "recovery:run-1:submit",
                    "status": "exhausted",
                    "retryable": True,
                    "terminal": True,
                },
            },
        ]

        summary = RuntimeRecoveryContractBuilder.build_recovery_audit_summary(operations)

        self.assertEqual(summary["operation_count"], 2)
        self.assertEqual(summary["status_counts"], {"attempted": 1, "failed": 1})
        self.assertEqual(summary["retry_count"], 2)
        self.assertEqual(summary["retry_status_counts"], {"retryable": 1, "exhausted": 1})
        self.assertEqual(summary["latest_retry_status"], "exhausted")
        self.assertEqual(summary["latest_retry_terminal_reason"], "transient_workspace_unavailable")
        self.assertTrue(summary["terminal"])
        self.assertEqual(summary["latest_terminal_reason"], "transient_workspace_unavailable")

    def test_ownership_evidence_is_summary_only_not_authorization(self):
        summary = RuntimeRecoveryContractBuilder.build_recovery_audit_summary([
            {
                "operation_id": "recovery_operation:run-1:submit:first",
                "run_id": "run-1",
                "entrypoint": "submit_approval.approved",
                "operation_status": "recovered",
                "recovery_reason": "ready_via_registry",
                "worker_ownership": {
                    "implemented": True,
                    "worker_id": "worker-a",
                    "lease_id": "lease-1",
                    "fencing_token": 2,
                    "lease_status": "validated",
                    "handler": lambda: None,
                },
            }
        ])

        self.assertTrue(summary["ownership_implemented"])
        self.assertEqual(summary["latest_ownership_status"], "validated")
        self.assertFalse(summary["authorization_source"])
        self.assertNotIn("handler", summary)

    def test_run_recovery_contract_includes_audit_summary(self):
        run_recovery = RuntimeRecoveryContractBuilder.build_run_recovery_contract({
            "run_id": "run-1",
            "recoverable": True,
            "tool_continuation": {"recovery_reason": "ready_via_registry"},
            "loop_continuation": {},
            "recovery_operations": [
                {
                    "operation_id": "recovery_operation:run-1:submit:first",
                    "run_id": "run-1",
                    "entrypoint": "submit_approval.approved",
                    "operation_status": "recovered",
                    "recovery_reason": "ready_via_registry",
                    "recorded_at": "2026-05-23T09:00:00+00:00",
                }
            ],
        })

        self.assertIn("recovery_audit_summary", run_recovery)
        self.assertEqual(run_recovery["recovery_audit_summary"]["operation_count"], 1)
        self.assertEqual(run_recovery["recovery_audit_summary"]["latest_status"], "recovered")
        self.assertEqual(run_recovery["recovery_operation_count"], 1)

    def test_run_recovery_contract_preserves_retry_terminal_summary(self):
        run_recovery = RuntimeRecoveryContractBuilder.build_run_recovery_contract({
            "run_id": "run-1",
            "recoverable": False,
            "tool_continuation": {"recovery_reason": "workspace_backend_unavailable"},
            "loop_continuation": {},
            "recovery_operations": [
                {
                    "operation_id": "recovery_operation:run-1:submit:retry",
                    "run_id": "run-1",
                    "entrypoint": "submit_approval.approved",
                    "operation_status": "failed",
                    "recovery_reason": "transient_workspace_unavailable",
                    "retry": {
                        "attempt_number": 3,
                        "max_attempts": 3,
                        "previous_operation_id": "recovery_operation:run-1:submit:first",
                        "idempotency_key": "recovery:run-1:submit",
                        "status": "exhausted",
                        "retryable": True,
                        "terminal": True,
                        "handler": lambda: None,
                    },
                    "recorded_at": "2026-05-24T09:00:00+00:00",
                }
            ],
        })

        summary = run_recovery["recovery_audit_summary"]
        self.assertEqual(summary["latest_retry_status"], "exhausted")
        self.assertEqual(summary["latest_retry_terminal_reason"], "transient_workspace_unavailable")
        self.assertEqual(summary["retry_status_counts"], {"exhausted": 1})
        self.assertNotIn("handler", run_recovery["recovery_operation_history"][0]["retry"])


if __name__ == "__main__":
    unittest.main()
