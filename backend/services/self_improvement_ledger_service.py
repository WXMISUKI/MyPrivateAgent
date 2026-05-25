"""Runtime contract for the self-improvement ledger."""

from __future__ import annotations

from typing import Any, Dict

try:
    from models import Error, FeatureRequest, Learning, LearningReviewRecord, LearningStatus
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.models import Error, FeatureRequest, Learning, LearningReviewRecord, LearningStatus


class SelfImprovementLedgerService:
    """Describe the learning/error/feature-request loop as a runtime capability."""

    CONTRACT_VERSION = "phase-g-self-improvement-ledger-v1"

    def build_runtime_contract(self, db: Any = None) -> Dict[str, Any]:
        contract = {
            "contract_version": self.CONTRACT_VERSION,
            "overall_status": "ready",
            "record_types": ["learning", "error", "feature_request"],
            "tracked_sources": [
                "conversation",
                "error",
                "user_feedback",
                "quality_gate",
                "runtime_contract",
            ],
            "promotion_targets": [
                "AGENTS.md",
                "docs",
                "system_prompt",
                "best_practice",
                "skill",
            ],
            "governance_states": [
                "pending",
                "in_progress",
                "resolved",
                "promoted",
                "promoted_to_skill",
                "disabled",
                "rolled_back",
            ],
            "quality_controls": [
                "review",
                "version_history",
                "duplicate_merge",
                "rollback",
                "restore",
            ],
            "runtime_surface_enabled": True,
            "health_summary": self._empty_health_summary(),
        }
        if db is not None:
            health_summary = self._build_health_summary(db)
            contract["health_summary"] = health_summary
            if health_summary["attention_items"]:
                contract["overall_status"] = "attention_required"
        return contract

    def _empty_health_summary(self) -> Dict[str, Any]:
        return {
            "total_learning_count": 0,
            "pending_learning_count": 0,
            "resolved_learning_count": 0,
            "promoted_learning_count": 0,
            "disabled_learning_count": 0,
            "rolled_back_learning_count": 0,
            "reviewed_learning_count": 0,
            "average_learning_quality_score": None,
            "total_error_count": 0,
            "pending_error_count": 0,
            "total_feature_request_count": 0,
            "pending_feature_request_count": 0,
            "attention_items": [],
        }

    def _build_health_summary(self, db: Any) -> Dict[str, Any]:
        latest_reviews = db.query(LearningReviewRecord).order_by(
            LearningReviewRecord.learning_id.asc(),
            LearningReviewRecord.created_at.desc(),
            LearningReviewRecord.id.desc(),
        ).all()
        latest_review_map = {}
        for review in latest_reviews:
            latest_review_map.setdefault(review.learning_id, review)
        quality_scores = [
            int(review.quality_score)
            for review in latest_review_map.values()
            if review.quality_score is not None
        ]

        pending_learning_count = db.query(Learning).filter(
            Learning.status == LearningStatus.PENDING
        ).count()
        pending_error_count = db.query(Error).filter(Error.status == "pending").count()
        pending_feature_request_count = db.query(FeatureRequest).filter(
            FeatureRequest.status == "pending"
        ).count()

        attention_items = []
        if pending_error_count:
            attention_items.append("pending_errors")
        if pending_learning_count:
            attention_items.append("pending_learnings")
        if pending_feature_request_count:
            attention_items.append("pending_feature_requests")

        return {
            "total_learning_count": db.query(Learning).count(),
            "pending_learning_count": pending_learning_count,
            "resolved_learning_count": db.query(Learning).filter(
                Learning.status == LearningStatus.RESOLVED
            ).count(),
            "promoted_learning_count": db.query(Learning).filter(
                Learning.status.in_([LearningStatus.PROMOTED, LearningStatus.PROMOTED_TO_SKILL])
            ).count(),
            "disabled_learning_count": db.query(Learning).filter(
                Learning.status == LearningStatus.DISABLED
            ).count(),
            "rolled_back_learning_count": db.query(Learning).filter(
                Learning.status == LearningStatus.ROLLED_BACK
            ).count(),
            "reviewed_learning_count": len(latest_review_map),
            "average_learning_quality_score": round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else None,
            "total_error_count": db.query(Error).count(),
            "pending_error_count": pending_error_count,
            "total_feature_request_count": db.query(FeatureRequest).count(),
            "pending_feature_request_count": pending_feature_request_count,
            "attention_items": attention_items,
        }


_self_improvement_ledger_service: SelfImprovementLedgerService | None = None


def get_self_improvement_ledger_service() -> SelfImprovementLedgerService:
    global _self_improvement_ledger_service
    if _self_improvement_ledger_service is None:
        _self_improvement_ledger_service = SelfImprovementLedgerService()
    return _self_improvement_ledger_service
