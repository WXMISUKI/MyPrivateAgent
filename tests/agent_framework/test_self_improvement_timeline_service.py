import unittest

from backend.services.self_improvement_timeline_service import SelfImprovementTimelineService


class _StubRunTraceService:
    def __init__(self):
        self.trace_calls = []
        self.audit_calls = []
        self.existing_dedupe_keys = set()
        self.dedupe_checks = []

    def build_snapshot_ref(self, **kwargs):
        return {
            "snapshot_id": "LEARNING-SNAPSHOT-1",
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


class _StubRunTraceServiceWithoutDedupeLookup:
    def __init__(self):
        self.trace_calls = []
        self.audit_calls = []

    def build_snapshot_ref(self, **kwargs):
        return {
            "snapshot_id": "LEARNING-SNAPSHOT-1",
            **kwargs,
        }

    def append_latest_active_item_trace(self, **kwargs):
        self.trace_calls.append(kwargs)
        return True

    def append_latest_active_item_audit(self, **kwargs):
        self.audit_calls.append(kwargs)
        return True


class SelfImprovementTimelineServiceTests(unittest.TestCase):
    def test_record_learning_event_writes_trace_and_audit_with_snapshot_ref(self):
        trace_service = _StubRunTraceService()
        service = SelfImprovementTimelineService(trace_service_factory=lambda db: trace_service)

        recording = service.record_learning_event(
            db=object(),
            conversation_id=321,
            learning_id="LRN-1",
            event_type="learning_review_approved",
            summary="Learning `LRN-1` 已提交审核",
            detail="review_status=approved quality_score=4",
            severity="success",
            payload={"review_id": "LRV-1"},
        )

        self.assertTrue(recording["trace_written"])
        self.assertTrue(recording["audit_written"])
        self.assertEqual(recording["conversation_id"], 321)
        self.assertEqual(recording["snapshot_ref"]["snapshot_id"], "LEARNING-SNAPSHOT-1")
        self.assertEqual(trace_service.trace_calls[0]["source"], "learning")
        self.assertEqual(trace_service.trace_calls[0]["event_type"], "learning_review_approved")
        self.assertEqual(trace_service.trace_calls[0]["payload"]["learning_id"], "LRN-1")
        self.assertEqual(trace_service.trace_calls[0]["payload"]["conversation_id"], 321)
        self.assertEqual(trace_service.trace_calls[0]["payload"]["snapshot_ref"]["snapshot_id"], "LEARNING-SNAPSHOT-1")
        self.assertEqual(trace_service.audit_calls[0]["event_type"], "learning_review_approved")
        self.assertEqual(trace_service.audit_calls[0]["content"], "Learning `LRN-1` 已提交审核")
        self.assertEqual(
            trace_service.trace_calls[0]["payload"]["dedupe_key"],
            "learning:learning_review_approved:321:LRN-1",
        )

    def test_record_learning_event_returns_snapshot_without_writing_when_conversation_is_missing(self):
        trace_service = _StubRunTraceService()
        service = SelfImprovementTimelineService(trace_service_factory=lambda db: trace_service)

        recording = service.record_learning_event(
            db=object(),
            conversation_id=None,
            learning_id="LRN-2",
            event_type="learning_created",
            summary="Learning `LRN-2` 已创建",
        )

        self.assertFalse(recording["trace_written"])
        self.assertFalse(recording["audit_written"])
        self.assertIsNone(recording["conversation_id"])
        self.assertEqual(recording["snapshot_ref"]["event_type"], "learning_created")
        self.assertEqual(trace_service.trace_calls, [])
        self.assertEqual(trace_service.audit_calls, [])

    def test_record_error_event_writes_error_payload_to_trace_and_audit(self):
        trace_service = _StubRunTraceService()
        service = SelfImprovementTimelineService(trace_service_factory=lambda db: trace_service)

        recording = service.record_error_event(
            db=object(),
            conversation_id=321,
            error_id="ERR-1",
            event_type="error_recorded",
            summary="Error `ERR-1` 已记录",
            detail="status=pending",
            severity="error",
            payload={"status": "pending"},
        )

        self.assertTrue(recording["trace_written"])
        self.assertEqual(recording["snapshot_ref"]["source"], "error")
        self.assertEqual(trace_service.trace_calls[0]["source"], "error")
        self.assertEqual(trace_service.trace_calls[0]["payload"]["error_id"], "ERR-1")
        self.assertEqual(trace_service.trace_calls[0]["payload"]["conversation_id"], 321)
        self.assertEqual(
            trace_service.trace_calls[0]["payload"]["dedupe_key"],
            "error:error_recorded:321:ERR-1",
        )
        self.assertEqual(trace_service.audit_calls[0]["event_type"], "error_recorded")

    def test_record_feature_request_event_writes_feature_payload_to_trace_and_audit(self):
        trace_service = _StubRunTraceService()
        service = SelfImprovementTimelineService(trace_service_factory=lambda db: trace_service)

        recording = service.record_feature_request_event(
            db=object(),
            conversation_id=321,
            feature_id="FEAT-1",
            event_type="feature_request_recorded",
            summary="Feature request `FEAT-1` 已记录",
            detail="status=pending",
            severity="info",
            payload={"status": "pending"},
        )

        self.assertTrue(recording["audit_written"])
        self.assertEqual(recording["snapshot_ref"]["source"], "feature_request")
        self.assertEqual(trace_service.trace_calls[0]["source"], "feature_request")
        self.assertEqual(trace_service.trace_calls[0]["payload"]["feature_id"], "FEAT-1")
        self.assertEqual(trace_service.trace_calls[0]["payload"]["conversation_id"], 321)
        self.assertEqual(
            trace_service.trace_calls[0]["payload"]["dedupe_key"],
            "feature_request:feature_request_recorded:321:FEAT-1",
        )
        self.assertEqual(trace_service.audit_calls[0]["content"], "Feature request `FEAT-1` 已记录")

    def test_record_event_preserves_explicit_dedupe_key(self):
        trace_service = _StubRunTraceService()
        service = SelfImprovementTimelineService(trace_service_factory=lambda db: trace_service)

        recording = service.record_error_event(
            db=object(),
            conversation_id=321,
            error_id="ERR-1",
            event_type="error_recorded",
            summary="Error `ERR-1` 已记录",
            payload={"dedupe_key": "custom:error:key"},
        )

        self.assertEqual(recording["dedupe_key"], "custom:error:key")
        self.assertEqual(trace_service.trace_calls[0]["payload"]["dedupe_key"], "custom:error:key")

    def test_record_event_skips_trace_and_audit_when_dedupe_key_already_exists(self):
        trace_service = _StubRunTraceService()
        trace_service.existing_dedupe_keys = {"error:error_recorded:321:ERR-1"}
        service = SelfImprovementTimelineService(trace_service_factory=lambda db: trace_service)

        recording = service.record_error_event(
            db=object(),
            conversation_id=321,
            error_id="ERR-1",
            event_type="error_recorded",
            summary="Error `ERR-1` 已记录",
        )

        self.assertFalse(recording["trace_written"])
        self.assertFalse(recording["audit_written"])
        self.assertEqual(recording["dedupe_source"], "persisted_trace")
        self.assertEqual(recording["dedupe_key"], "error:error_recorded:321:ERR-1")
        self.assertEqual(trace_service.trace_calls, [])
        self.assertEqual(trace_service.audit_calls, [])
        self.assertEqual(trace_service.dedupe_checks[0]["source"], "error")
        self.assertEqual(trace_service.dedupe_checks[0]["event_type"], "error_recorded")

    def test_record_event_writes_when_trace_service_does_not_support_dedupe_lookup(self):
        trace_service = _StubRunTraceServiceWithoutDedupeLookup()
        service = SelfImprovementTimelineService(trace_service_factory=lambda db: trace_service)

        recording = service.record_feature_request_event(
            db=object(),
            conversation_id=321,
            feature_id="FEAT-1",
            event_type="feature_request_recorded",
            summary="Feature request `FEAT-1` 已记录",
        )

        self.assertTrue(recording["trace_written"])
        self.assertTrue(recording["audit_written"])
        self.assertEqual(len(trace_service.trace_calls), 1)


if __name__ == "__main__":
    unittest.main()
