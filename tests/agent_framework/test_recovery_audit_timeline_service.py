import unittest

from backend.services.recovery_audit_timeline_service import (
    RECOVERY_AUDIT_TRACE_EVENT_TYPE,
    RECOVERY_AUDIT_TRACE_SOURCE,
    RecoveryAuditTimelineService,
)


class _StubRunTraceService:
    def __init__(self):
        self.trace_calls = []
        self.existing_dedupe_keys = set()
        self.dedupe_checks = []

    def append_runtime_trace(self, **kwargs):
        self.trace_calls.append(kwargs)
        return True

    def has_runtime_trace_dedupe_key(self, **kwargs):
        self.dedupe_checks.append(kwargs)
        return kwargs.get("dedupe_key") in self.existing_dedupe_keys


class _TraceServiceWithoutAppend:
    def has_runtime_trace_dedupe_key(self, **_kwargs):
        return False


class RecoveryAuditTimelineServiceTests(unittest.TestCase):
    def _operation(self):
        return {
            "operation_id": "recovery_operation:run-1:submit:first",
            "run_id": "run-1",
            "entrypoint": "submit_approval.approved",
            "operation_status": "recovered",
            "recovery_reason": "ready_via_registry",
            "blocked_reason": "",
            "retry": {
                "attempt_number": 1,
                "max_attempts": 3,
                "status": "attempted",
                "handler": lambda: None,
            },
            "worker_ownership": {
                "implemented": True,
                "lease_status": "validated",
                "handler": lambda: None,
            },
            "handler": lambda: None,
            "recorded_at": "2026-05-23T09:00:00+00:00",
        }

    def test_record_operation_writes_compact_runtime_trace(self):
        trace_service = _StubRunTraceService()
        service = RecoveryAuditTimelineService(trace_service_factory=lambda db: trace_service)

        result = service.record_operation(
            operation=self._operation(),
            user_id=7,
            conversation_id=42,
        )

        self.assertTrue(result["trace_written"])
        self.assertEqual(result["operation_id"], "recovery_operation:run-1:submit:first")
        self.assertEqual(
            result["dedupe_key"],
            "recovery_audit:run-1:recovery_operation_run-1_submit_first",
        )
        self.assertEqual(len(trace_service.trace_calls), 1)
        trace_call = trace_service.trace_calls[0]
        self.assertEqual(trace_call["source"], RECOVERY_AUDIT_TRACE_SOURCE)
        self.assertEqual(trace_call["event_type"], RECOVERY_AUDIT_TRACE_EVENT_TYPE)
        self.assertEqual(trace_call["run_id"], "run-1")
        self.assertEqual(trace_call["severity"], "info")
        payload = trace_call["payload"]
        self.assertEqual(payload["operation_status"], "recovered")
        self.assertEqual(payload["recovery_reason"], "ready_via_registry")
        self.assertEqual(payload["retry_status"], "attempted")
        self.assertEqual(payload["ownership_status"], "validated")
        self.assertNotIn("handler", payload)

    def test_record_operation_uses_warning_severity_for_blocked_operation(self):
        trace_service = _StubRunTraceService()
        service = RecoveryAuditTimelineService(trace_service_factory=lambda db: trace_service)
        operation = self._operation()
        operation["operation_status"] = "blocked"
        operation["recovery_reason"] = "missing_registered_binding"

        result = service.record_operation(operation=operation, user_id=7, conversation_id=42)

        self.assertTrue(result["trace_written"])
        self.assertEqual(trace_service.trace_calls[0]["severity"], "warning")

    def test_record_operation_skips_when_dedupe_key_already_exists(self):
        trace_service = _StubRunTraceService()
        trace_service.existing_dedupe_keys = {
            "recovery_audit:run-1:recovery_operation_run-1_submit_first"
        }
        service = RecoveryAuditTimelineService(trace_service_factory=lambda db: trace_service)

        result = service.record_operation(
            operation=self._operation(),
            user_id=7,
            conversation_id=42,
        )

        self.assertFalse(result["trace_written"])
        self.assertEqual(result["dedupe_source"], "persisted_trace")
        self.assertEqual(trace_service.trace_calls, [])
        self.assertEqual(trace_service.dedupe_checks[0]["source"], RECOVERY_AUDIT_TRACE_SOURCE)

    def test_record_operation_fails_open_when_trace_service_cannot_append(self):
        service = RecoveryAuditTimelineService(trace_service_factory=lambda db: _TraceServiceWithoutAppend())

        result = service.record_operation(operation=self._operation(), user_id=7, conversation_id=42)

        self.assertFalse(result["trace_written"])
        self.assertEqual(result["reason"], "trace_service_unavailable")
        self.assertEqual(
            result["dedupe_key"],
            "recovery_audit:run-1:recovery_operation_run-1_submit_first",
        )

    def test_record_operation_builds_fallback_dedupe_key_without_operation_id(self):
        trace_service = _StubRunTraceService()
        service = RecoveryAuditTimelineService(trace_service_factory=lambda db: trace_service)
        operation = self._operation()
        operation["operation_id"] = ""

        result = service.record_operation(operation=operation, user_id=7, conversation_id=42)

        self.assertTrue(result["trace_written"])
        self.assertEqual(
            result["dedupe_key"],
            "recovery_audit:run-1:submit_approval.approved:recovered:ready_via_registry",
        )


if __name__ == "__main__":
    unittest.main()
