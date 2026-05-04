import os
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.agent_server.app import create_app
from backend.agent_server.config import AgentServerBootstrapConfig, AgentServerConfig, AgentServerUIConfig
from backend.agent_server.dependencies import get_db as dependency_get_db
from backend.database import Base, get_db as database_get_db
from backend.models import Learning, LearningCategory, LearningReviewRecord, LearningStatus, LearningVersionRecord, Priority


class LearningsRouterTests(unittest.TestCase):
    def setUp(self):
        temp_root = Path(__file__).resolve().parent / ".tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        self.db_path = temp_root / f"learnings-{uuid.uuid4().hex}.db"
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            connect_args={"check_same_thread": False},
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )

        def override_get_db():
            db = self.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[dependency_get_db] = override_get_db
        app.dependency_overrides[database_get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        self.engine.dispose()
        if self.db_path.exists():
            os.remove(self.db_path)

    def _seed_learning(
        self,
        learning_id: str,
        *,
        status: LearningStatus = LearningStatus.PENDING,
        tags=None,
        promoted_to=None,
        category=LearningCategory.CORRECTION,
        pattern_key=None,
    ):
        db = self.SessionLocal()
        try:
            learning = Learning(
                learning_id=learning_id,
                category=category,
                priority=Priority.MEDIUM,
                status=status,
                summary=f"Learning {learning_id}",
                details="original details",
                source="user_feedback",
                tags=list(tags or []),
                pattern_key=pattern_key or f"user_feedback:{learning_id}",
                recurrence_count=1,
                promoted_to=promoted_to,
            )
            db.add(learning)
            db.commit()
        finally:
            db.close()

    def test_learning_governance_actions_update_status_and_tags(self):
        self._seed_learning("LRN-1")
        self._seed_learning("LRN-2", status=LearningStatus.PROMOTED, promoted_to="CLAUDE.md")

        disable_response = self.client.post("/api/learnings/LRN-1/disable", json={"note": "不再推荐", "conversation_id": 321})
        self.assertEqual(disable_response.status_code, 200)
        self.assertEqual(disable_response.json()["status"], "disabled")
        self.assertIn("disabled", disable_response.json()["tags"])
        self.assertIsNotNone(disable_response.json()["snapshot_ref"])
        self.assertEqual(disable_response.json()["timeline_recording"]["conversation_id"], 321)

        class _StubTransformer:
            async def transform_learning(self, learning_id, target_type, db):
                learning = db.query(Learning).filter(Learning.learning_id == learning_id).first()
                learning.status = LearningStatus.PROMOTED_TO_SKILL if target_type == "best_practice" else LearningStatus.PROMOTED
                learning.promoted_to = "BP-001" if target_type == "best_practice" else "PROMPT-001"
                db.commit()
                return {
                    "success": True,
                    "type": target_type,
                    "id": learning.promoted_to,
                }

        with patch("backend.routers.learnings._get_knowledge_transformer", return_value=_StubTransformer()):
            promote_response = self.client.post("/api/learnings/LRN-1/promote", json={"note": "确认可用", "conversation_id": 321})

        self.assertEqual(promote_response.status_code, 200)
        self.assertEqual(promote_response.json()["status"], "promoted_to_skill")
        self.assertEqual(promote_response.json()["promoted_to"], "BP-001")
        self.assertIn("governance", promote_response.json()["details"])
        self.assertEqual(promote_response.json()["history_count"], 2)
        self.assertIn("promotion_without_approved_review", promote_response.json()["conflict_flags"])
        self.assertIsNotNone(promote_response.json()["snapshot_ref"])

        self._seed_learning("LRN-3", category=LearningCategory.INSIGHT)
        with patch("backend.routers.learnings._get_knowledge_transformer", return_value=_StubTransformer()):
            prompt_response = self.client.post("/api/learnings/LRN-3/promote", json={"note": "生成系统提示", "conversation_id": 321})

        self.assertEqual(prompt_response.status_code, 200)
        self.assertEqual(prompt_response.json()["status"], "promoted")
        self.assertEqual(prompt_response.json()["promoted_to"], "PROMPT-001")
        self.assertIsNotNone(prompt_response.json()["snapshot_ref"])

        rollback_response = self.client.post("/api/learnings/LRN-2/rollback", json={"note": "回退错误提升", "conversation_id": 321})
        self.assertEqual(rollback_response.status_code, 200)
        self.assertEqual(rollback_response.json()["status"], "rolled_back")
        self.assertIn("rollback", rollback_response.json()["tags"])
        self.assertEqual(rollback_response.json()["history_count"], 1)
        self.assertIsNotNone(rollback_response.json()["snapshot_ref"])

        restore_response = self.client.post("/api/learnings/LRN-2/restore", json={"note": "恢复原状态", "conversation_id": 321})
        self.assertEqual(restore_response.status_code, 200)
        self.assertEqual(restore_response.json()["status"], "promoted")
        self.assertEqual(restore_response.json()["promoted_to"], "CLAUDE.md")
        self.assertEqual(restore_response.json()["history_count"], 2)
        self.assertIn("promotion_without_approved_review", restore_response.json()["conflict_flags"])
        self.assertIsNotNone(restore_response.json()["snapshot_ref"])

    def test_learning_stats_include_governance_states(self):
        self._seed_learning("LRN-1", status=LearningStatus.DISABLED)
        self._seed_learning("LRN-2", status=LearningStatus.ROLLED_BACK)
        self._seed_learning("LRN-3", status=LearningStatus.PENDING)

        response = self.client.get("/api/learnings/stats")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["disabled_learnings"], 1)
        self.assertEqual(response.json()["rolled_back_learnings"], 1)

    def test_learning_review_endpoint_records_history_and_latest_review(self):
        self._seed_learning("LRN-4", pattern_key="user_feedback:shared")
        self._seed_learning("LRN-5", pattern_key="user_feedback:shared")

        first_response = self.client.post(
            "/api/learnings/LRN-4/review",
            json={
                "review_status": "approved",
                "quality_score": 4,
                "reviewer": "tester",
                "review_note": "first review",
                "conversation_id": 321,
            },
        )
        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(first_response.json()["review_status"], "approved")
        self.assertIsNotNone(first_response.json()["snapshot_ref"])
        self.assertEqual(first_response.json()["timeline_recording"]["conversation_id"], 321)

        second_response = self.client.post(
            "/api/learnings/LRN-4/review",
            json={
                "review_status": "needs_changes",
                "quality_score": 2,
                "reviewer": "tester-2",
                "review_note": "second review",
                "conversation_id": 321,
            },
        )
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(second_response.json()["review_status"], "needs_changes")
        self.assertIsNotNone(second_response.json()["snapshot_ref"])

        detail_response = self.client.get("/api/learnings/LRN-4")
        self.assertEqual(detail_response.status_code, 200)
        self.assertIsNotNone(detail_response.json()["latest_review"])
        self.assertEqual(detail_response.json()["latest_review"]["review_status"], "needs_changes")
        self.assertEqual(detail_response.json()["latest_review"]["quality_score"], 2)
        self.assertEqual(detail_response.json()["history_count"], 2)
        self.assertIn("review_needs_changes", detail_response.json()["conflict_flags"])
        self.assertIn("duplicate_pattern_key", detail_response.json()["conflict_flags"])
        self.assertIn("duplicate_learning_group", detail_response.json()["conflict_flags"])
        self.assertEqual(detail_response.json()["conflict_context"]["duplicate_learning_ids"], ["LRN-5"])

        latest_review_response = self.client.get("/api/learnings/LRN-4/review")
        self.assertEqual(latest_review_response.status_code, 200)
        self.assertEqual(latest_review_response.json()["review_status"], "needs_changes")

        history_response = self.client.get("/api/learnings/LRN-4/history")
        self.assertEqual(history_response.status_code, 200)
        self.assertEqual(len(history_response.json()), 2)
        self.assertEqual(history_response.json()[0]["event_type"], "review:needs_changes")
        self.assertEqual(history_response.json()[1]["event_type"], "review:approved")

        stats_response = self.client.get("/api/learnings/stats")
        self.assertEqual(stats_response.status_code, 200)
        self.assertEqual(stats_response.json()["reviewed_learnings"], 1)
        self.assertEqual(stats_response.json()["average_quality_score"], 2.0)

        db = self.SessionLocal()
        try:
            self.assertEqual(db.query(LearningReviewRecord).filter(LearningReviewRecord.learning_id == "LRN-4").count(), 2)
            self.assertEqual(db.query(LearningVersionRecord).filter(LearningVersionRecord.learning_id == "LRN-4").count(), 2)
        finally:
            db.close()

    def test_learning_history_compare_and_duplicate_merge(self):
        self._seed_learning("LRN-6", pattern_key="user_feedback:mergeable")
        self._seed_learning("LRN-7", pattern_key="user_feedback:mergeable")

        self.client.post(
            "/api/learnings/LRN-6/review",
            json={
                "review_status": "approved",
                "quality_score": 5,
                "reviewer": "tester",
                "review_note": "snapshot A",
                "conversation_id": 321,
            },
        )
        self.client.post(
            "/api/learnings/LRN-6/review",
            json={
                "review_status": "needs_changes",
                "quality_score": 2,
                "reviewer": "tester",
                "review_note": "snapshot B",
                "conversation_id": 321,
            },
        )

        history_response = self.client.get("/api/learnings/LRN-6/history")
        self.assertEqual(history_response.status_code, 200)
        latest_version_id = history_response.json()[0]["version_id"]
        previous_version_id = history_response.json()[1]["version_id"]

        compare_response = self.client.get(
            f"/api/learnings/LRN-6/compare?base_version_id={previous_version_id}&target_version_id={latest_version_id}"
        )
        self.assertEqual(compare_response.status_code, 200)
        self.assertTrue(compare_response.json()["has_changes"])
        changed_fields = {item["field"] for item in compare_response.json()["changed_fields"]}
        self.assertIn("review_status", changed_fields)
        self.assertIn("quality_score", changed_fields)

        merge_response = self.client.post(
            "/api/learnings/LRN-6/merge-duplicate",
            json={"source_learning_id": "LRN-7", "note": "合并重复学习", "conversation_id": 321},
        )
        self.assertEqual(merge_response.status_code, 200)
        self.assertEqual(merge_response.json()["recurrence_count"], 2)
        self.assertEqual(merge_response.json()["conflict_context"]["duplicate_learning_ids"], [])
        self.assertNotIn("duplicate_pattern_key", merge_response.json()["conflict_flags"])
        self.assertIsNotNone(merge_response.json()["snapshot_ref"])

        db = self.SessionLocal()
        try:
            source = db.query(Learning).filter(Learning.learning_id == "LRN-7").first()
            target = db.query(Learning).filter(Learning.learning_id == "LRN-6").first()
            self.assertEqual(source.status, LearningStatus.DISABLED)
            self.assertIn("merged_into:LRN-6", source.tags)
            self.assertIn("LRN-7", target.see_also)
            self.assertEqual(
                db.query(LearningVersionRecord).filter(LearningVersionRecord.learning_id == "LRN-6").count(),
                3,
            )
        finally:
            db.close()

    def test_apply_learning_version_restores_snapshot_into_current_learning(self):
        create_response = self.client.post(
            "/api/learnings",
            json={
                "category": "correction",
                "priority": "medium",
                "summary": "Original summary",
                "details": "Original details",
                "suggested_action": "Original action",
                "source": "user_feedback",
                "tags": ["prompt:original"],
                "pattern_key": "apply-version:test",
            },
        )
        self.assertEqual(create_response.status_code, 200)
        learning_id = create_response.json()["learning_id"]

        update_response = self.client.put(
            f"/api/learnings/{learning_id}",
            json={
                "summary": "Updated summary",
                "details": "Updated details",
                "suggested_action": "Updated action",
                "status": "resolved",
            },
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["summary"], "Updated summary")

        history_response = self.client.get(f"/api/learnings/{learning_id}/history")
        self.assertEqual(history_response.status_code, 200)
        created_version_id = history_response.json()[1]["version_id"]

        apply_response = self.client.post(
            f"/api/learnings/{learning_id}/apply-version",
            json={"version_id": created_version_id, "note": "恢复到原始版本", "fields": ["summary"]},
        )
        self.assertEqual(apply_response.status_code, 200)
        self.assertEqual(apply_response.json()["applied_version_id"], created_version_id)
        self.assertEqual(apply_response.json()["applied_fields"], ["summary"])
        self.assertIsNotNone(apply_response.json()["snapshot_ref"])
        self.assertEqual(apply_response.json()["timeline_recording"]["trace_written"], False)
        self.assertEqual(apply_response.json()["learning"]["summary"], "Original summary")
        self.assertTrue(apply_response.json()["learning"]["details"].startswith("Updated details"))
        self.assertEqual(apply_response.json()["learning"]["suggested_action"], "Updated action")
        self.assertEqual(apply_response.json()["learning"]["status"], "resolved")

        db = self.SessionLocal()
        try:
            learning = db.query(Learning).filter(Learning.learning_id == learning_id).first()
            self.assertEqual(learning.summary, "Original summary")
            self.assertTrue(str(learning.details or "").startswith("Updated details"))
            self.assertEqual(
                db.query(LearningVersionRecord).filter(LearningVersionRecord.learning_id == learning_id).count(),
                3,
            )
            latest_version = db.query(LearningVersionRecord).filter(
                LearningVersionRecord.learning_id == learning_id
            ).order_by(LearningVersionRecord.id.desc()).first()
            self.assertIsNotNone((latest_version.version_metadata or {}).get("snapshot_ref"))
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
