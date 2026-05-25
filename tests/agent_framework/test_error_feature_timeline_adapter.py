import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import Error, FeatureRequest, Priority
from backend.routers.learnings import (
    ErrorCreate,
    ErrorUpdate,
    FeatureRequestCreate,
    FeatureRequestUpdate,
    create_error,
    create_feature_request,
    update_error,
    update_feature_request,
)


class _StubSelfImprovementTimelineService:
    def __init__(self):
        self.error_calls = []
        self.feature_calls = []

    def record_error_event(self, **kwargs):
        self.error_calls.append(kwargs)
        return {
            "trace_written": True,
            "audit_written": True,
            "conversation_id": kwargs["conversation_id"],
            "snapshot_ref": {"snapshot_id": "ERROR-SNAPSHOT-1"},
            "dedupe_key": f"error:{kwargs['event_type']}:{kwargs['conversation_id']}:{kwargs['error_id']}",
        }

    def record_feature_request_event(self, **kwargs):
        self.feature_calls.append(kwargs)
        return {
            "trace_written": True,
            "audit_written": True,
            "conversation_id": kwargs["conversation_id"],
            "snapshot_ref": {"snapshot_id": "FEATURE-SNAPSHOT-1"},
            "dedupe_key": f"feature_request:{kwargs['event_type']}:{kwargs['conversation_id']}:{kwargs['feature_id']}",
        }


class ErrorFeatureTimelineAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.SessionLocal()

    async def asyncTearDown(self):
        self.db.close()
        self.engine.dispose()

    async def test_create_error_records_self_improvement_timeline(self):
        service = _StubSelfImprovementTimelineService()

        with patch("backend.routers.learnings.get_self_improvement_timeline_service", return_value=service):
            response = await create_error(
                ErrorCreate(
                    summary="Runtime contract smoke failed",
                    error_message="contract check failed",
                    conversation_id=321,
                ),
                db=self.db,
            )

        self.assertEqual(response.timeline_recording["snapshot_ref"]["snapshot_id"], "ERROR-SNAPSHOT-1")
        self.assertEqual(response.timeline_recording["dedupe_key"], f"error:error_recorded:321:{response.error_id}")
        self.assertEqual(response.snapshot_ref["snapshot_id"], "ERROR-SNAPSHOT-1")
        self.assertEqual(service.error_calls[0]["event_type"], "error_recorded")
        self.assertEqual(service.error_calls[0]["conversation_id"], 321)
        self.assertEqual(service.error_calls[0]["payload"]["status"], "pending")

    async def test_update_error_records_status_change_timeline(self):
        self.db.add(Error(
            error_id="ERR-1",
            priority=Priority.HIGH,
            status="pending",
            summary="Runtime contract smoke failed",
        ))
        self.db.commit()
        service = _StubSelfImprovementTimelineService()

        with patch("backend.routers.learnings.get_self_improvement_timeline_service", return_value=service):
            response = await update_error(
                "ERR-1",
                ErrorUpdate(status="resolved", suggested_fix="Fixed contract payload", conversation_id=321),
                db=self.db,
            )

        self.assertEqual(response.status, "resolved")
        self.assertEqual(response.timeline_recording["snapshot_ref"]["snapshot_id"], "ERROR-SNAPSHOT-1")
        self.assertEqual(response.timeline_recording["dedupe_key"], "error:error_updated:321:ERR-1")
        self.assertEqual(service.error_calls[0]["event_type"], "error_updated")
        self.assertEqual(service.error_calls[0]["payload"]["status"], "resolved")

    async def test_create_feature_request_records_self_improvement_timeline(self):
        service = _StubSelfImprovementTimelineService()

        with patch("backend.routers.learnings.get_self_improvement_timeline_service", return_value=service):
            response = await create_feature_request(
                FeatureRequestCreate(
                    requested_capability="Expose query control plane",
                    conversation_id=321,
                ),
                db=self.db,
            )

        self.assertEqual(response.timeline_recording["snapshot_ref"]["snapshot_id"], "FEATURE-SNAPSHOT-1")
        self.assertEqual(response.timeline_recording["dedupe_key"], f"feature_request:feature_request_recorded:321:{response.feature_id}")
        self.assertEqual(response.snapshot_ref["snapshot_id"], "FEATURE-SNAPSHOT-1")
        self.assertEqual(service.feature_calls[0]["event_type"], "feature_request_recorded")
        self.assertEqual(service.feature_calls[0]["payload"]["status"], "pending")

    async def test_update_feature_request_records_status_change_timeline(self):
        self.db.add(FeatureRequest(
            feature_id="FEAT-1",
            priority=Priority.MEDIUM,
            status="pending",
            requested_capability="Expose query control plane",
            complexity_estimate="medium",
        ))
        self.db.commit()
        service = _StubSelfImprovementTimelineService()

        with patch("backend.routers.learnings.get_self_improvement_timeline_service", return_value=service):
            response = await update_feature_request(
                "FEAT-1",
                FeatureRequestUpdate(status="resolved", suggested_implementation="Added runtime contract", conversation_id=321),
                db=self.db,
            )

        self.assertEqual(response.status, "resolved")
        self.assertEqual(response.timeline_recording["snapshot_ref"]["snapshot_id"], "FEATURE-SNAPSHOT-1")
        self.assertEqual(response.timeline_recording["dedupe_key"], "feature_request:feature_request_updated:321:FEAT-1")
        self.assertEqual(service.feature_calls[0]["event_type"], "feature_request_updated")
        self.assertEqual(service.feature_calls[0]["payload"]["status"], "resolved")


if __name__ == "__main__":
    unittest.main()
