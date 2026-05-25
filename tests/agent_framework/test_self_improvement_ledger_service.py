import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import (
    Error,
    FeatureRequest,
    Learning,
    LearningCategory,
    LearningReviewRecord,
    LearningReviewStatus,
    LearningStatus,
    Priority,
)
from backend.services.self_improvement_ledger_service import SelfImprovementLedgerService


class SelfImprovementLedgerServiceTests(unittest.TestCase):
    def test_build_runtime_contract_exposes_self_improvement_boundaries(self):
        contract = SelfImprovementLedgerService().build_runtime_contract()

        self.assertEqual(contract["contract_version"], "phase-g-self-improvement-ledger-v1")
        self.assertEqual(contract["overall_status"], "ready")
        self.assertEqual(contract["record_types"], ["learning", "error", "feature_request"])
        self.assertIn("quality_gate", contract["tracked_sources"])
        self.assertIn("runtime_contract", contract["tracked_sources"])
        self.assertIn("AGENTS.md", contract["promotion_targets"])
        self.assertIn("promoted_to_skill", contract["governance_states"])
        self.assertIn("duplicate_merge", contract["quality_controls"])
        self.assertTrue(contract["runtime_surface_enabled"])
        self.assertEqual(contract["health_summary"]["pending_learning_count"], 0)
        self.assertEqual(contract["health_summary"]["attention_items"], [])

    def test_build_runtime_contract_includes_health_summary_when_db_is_available(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            db.add_all([
                Learning(
                    learning_id="LRN-1",
                    category=LearningCategory.CORRECTION,
                    priority=Priority.HIGH,
                    status=LearningStatus.PENDING,
                    summary="User corrected tool behavior",
                    source="user_feedback",
                    pattern_key="tool:correction",
                ),
                Learning(
                    learning_id="LRN-2",
                    category=LearningCategory.BEST_PRACTICE,
                    priority=Priority.MEDIUM,
                    status=LearningStatus.PROMOTED,
                    summary="Promoted best practice",
                    source="quality_gate",
                    pattern_key="quality:best-practice",
                ),
                Error(
                    error_id="ERR-1",
                    priority=Priority.CRITICAL,
                    status="pending",
                    summary="Runtime contract smoke failed",
                    error_message="contract check failed",
                ),
                FeatureRequest(
                    feature_id="FEAT-1",
                    priority=Priority.MEDIUM,
                    status="pending",
                    requested_capability="Expose query control plane",
                ),
                LearningReviewRecord(
                    review_id="LRV-1",
                    learning_id="LRN-1",
                    review_status=LearningReviewStatus.APPROVED,
                    quality_score=4,
                ),
            ])
            db.commit()

            contract = SelfImprovementLedgerService().build_runtime_contract(db=db)

            self.assertEqual(contract["overall_status"], "attention_required")
            self.assertEqual(contract["health_summary"]["pending_learning_count"], 1)
            self.assertEqual(contract["health_summary"]["pending_error_count"], 1)
            self.assertEqual(contract["health_summary"]["pending_feature_request_count"], 1)
            self.assertEqual(contract["health_summary"]["promoted_learning_count"], 1)
            self.assertEqual(contract["health_summary"]["reviewed_learning_count"], 1)
            self.assertEqual(contract["health_summary"]["average_learning_quality_score"], 4.0)
            self.assertEqual(
                contract["health_summary"]["attention_items"],
                ["pending_errors", "pending_learnings", "pending_feature_requests"],
            )
        finally:
            db.close()
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
