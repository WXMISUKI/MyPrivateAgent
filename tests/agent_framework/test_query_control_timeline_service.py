import unittest

from backend.services.query_control_timeline_service import QueryControlTimelineService


class _StubRunTraceService:
    def __init__(self):
        self.trace_calls = []
        self.audit_calls = []
        self.existing_dedupe_keys = set()
        self.dedupe_checks = []

    def build_snapshot_ref(self, **kwargs):
        return {
            "snapshot_id": "QUERY-SNAPSHOT-1",
            **kwargs,
        }

    def append_latest_active_item_trace(self, **kwargs):
        self.trace_calls.append(kwargs)
        return True

    def append_latest_active_item_audit(self, **kwargs):
        self.audit_calls.append(kwargs)
        return True

    def has_runtime_trace_dedupe_key(self, **kwargs):
        self.dedupe_checks.append(kwargs)
        return kwargs.get("dedupe_key") in self.existing_dedupe_keys


class QueryControlTimelineServiceTests(unittest.TestCase):
    def test_record_stage_writes_trace_and_audit_with_snapshot_and_dedupe_key(self):
        trace_service = _StubRunTraceService()
        service = QueryControlTimelineService(trace_service_factory=lambda db: trace_service)

        recording = service.record_stage(
            db=object(),
            conversation_id=321,
            channel="main_chat",
            stage="input_received",
            query_id="query-1",
            summary="Query input received",
            detail="message accepted",
            severity="info",
            payload={"message_id": 123},
        )

        self.assertTrue(recording["trace_written"])
        self.assertTrue(recording["audit_written"])
        self.assertEqual(recording["snapshot_ref"]["source"], "query_control")
        self.assertEqual(recording["dedupe_key"], "query_control:main_chat:input_received:321:query-1")
        self.assertEqual(trace_service.trace_calls[0]["source"], "query_control")
        self.assertEqual(trace_service.trace_calls[0]["event_type"], "query_control_input_received")
        self.assertEqual(trace_service.trace_calls[0]["payload"]["channel"], "main_chat")
        self.assertEqual(trace_service.trace_calls[0]["payload"]["stage"], "input_received")
        self.assertEqual(trace_service.trace_calls[0]["payload"]["query_id"], "query-1")
        self.assertEqual(trace_service.trace_calls[0]["payload"]["dedupe_key"], "query_control:main_chat:input_received:321:query-1")
        self.assertEqual(trace_service.audit_calls[0]["event_type"], "query_control_input_received")
        self.assertEqual(trace_service.audit_calls[0]["content"], "Query input received")

    def test_record_stage_skips_when_dedupe_key_already_exists(self):
        trace_service = _StubRunTraceService()
        trace_service.existing_dedupe_keys = {"query_control:embedded_sdk:planning:321:run-1"}
        service = QueryControlTimelineService(trace_service_factory=lambda db: trace_service)

        recording = service.record_stage(
            db=object(),
            conversation_id=321,
            channel="embedded_sdk",
            stage="planning",
            query_id="run-1",
            summary="Planning started",
        )

        self.assertFalse(recording["trace_written"])
        self.assertFalse(recording["audit_written"])
        self.assertEqual(recording["dedupe_source"], "persisted_trace")
        self.assertEqual(trace_service.trace_calls, [])
        self.assertEqual(trace_service.audit_calls, [])

    def test_record_stage_rejects_unknown_lifecycle_stage(self):
        service = QueryControlTimelineService(trace_service_factory=lambda db: _StubRunTraceService())

        with self.assertRaises(ValueError):
            service.record_stage(
                db=object(),
                conversation_id=321,
                channel="main_chat",
                stage="unknown_stage",
                query_id="query-1",
                summary="Bad stage",
            )

    def test_record_stage_returns_snapshot_without_writing_when_conversation_is_missing(self):
        trace_service = _StubRunTraceService()
        service = QueryControlTimelineService(trace_service_factory=lambda db: trace_service)

        recording = service.record_stage(
            db=object(),
            conversation_id=None,
            channel="external_adapter",
            stage="context_assembly",
            query_id="pilot-1",
            summary="Context assembled",
        )

        self.assertFalse(recording["trace_written"])
        self.assertFalse(recording["audit_written"])
        self.assertEqual(recording["dedupe_key"], "query_control:external_adapter:context_assembly:NA:pilot-1")
        self.assertEqual(trace_service.trace_calls, [])
        self.assertEqual(trace_service.audit_calls, [])


if __name__ == "__main__":
    unittest.main()
