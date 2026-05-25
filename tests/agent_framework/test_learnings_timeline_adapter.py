import unittest
from unittest.mock import patch

from backend.routers.learnings import _record_learning_timeline


class _StubSelfImprovementTimelineService:
    def __init__(self):
        self.calls = []

    def record_learning_event(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "trace_written": True,
            "audit_written": True,
            "conversation_id": kwargs["conversation_id"],
            "snapshot_ref": {"snapshot_id": "LEARNING-SNAPSHOT-1"},
            "dedupe_key": f"learning:{kwargs['event_type']}:{kwargs['conversation_id']}:{kwargs['learning_id']}",
        }


class LearningsTimelineAdapterTests(unittest.TestCase):
    def test_record_learning_timeline_delegates_to_self_improvement_timeline_service(self):
        service = _StubSelfImprovementTimelineService()

        with patch("backend.routers.learnings.get_self_improvement_timeline_service", return_value=service):
            recording = _record_learning_timeline(
                db=object(),
                conversation_id=321,
                learning_id="LRN-1",
                event_type="learning_promoted",
                summary="Learning `LRN-1` 已提升",
                detail="target_type=best_practice",
                severity="success",
                payload={"action": "promote"},
            )

        self.assertTrue(recording["trace_written"])
        self.assertEqual(recording["dedupe_key"], "learning:learning_promoted:321:LRN-1")
        self.assertEqual(service.calls[0]["learning_id"], "LRN-1")
        self.assertEqual(service.calls[0]["event_type"], "learning_promoted")
        self.assertEqual(service.calls[0]["payload"], {"action": "promote"})


if __name__ == "__main__":
    unittest.main()
