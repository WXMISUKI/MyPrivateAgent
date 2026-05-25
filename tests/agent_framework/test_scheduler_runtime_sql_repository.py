import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend.models import PlanHandoffStatus, PlanItemRecord, PlanRunRecord, PlanStatus, ChildRunRecord, SchedulerRunRecord
from backend.services.scheduler_runtime_sql_repository import SchedulerRuntimeSqlRepository
from backend.services.scheduler_runtime_store import SchedulerRuntimeStore


class SchedulerRuntimeSqlRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = TestingSessionLocal()
        self.plan = PlanRunRecord(
            user_id=1,
            conversation_id=2,
            objective="验证 scheduler runtime relational repository",
            source="manual",
            status=PlanStatus.PENDING,
            summary="待执行",
            plan_metadata={},
        )
        self.db.add(self.plan)
        self.db.flush()
        self.item = PlanItemRecord(
            plan_id=self.plan.id,
            step_order=1,
            title="并发执行验证",
            details="测试运行时独立持久化",
            status=PlanStatus.IN_PROGRESS,
            owner="主智能体",
            agent_role="planner",
            agent_id="scheduler-p1-i1",
            handoff_status=PlanHandoffStatus.EXECUTING,
            item_metadata={
                "required_capabilities": ["filesystem.read"],
                "child_roles": ["backend", "frontend"],
            },
        )
        self.db.add(self.item)
        self.db.flush()
        self.repository = SchedulerRuntimeSqlRepository(self.db)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def test_save_child_group_persists_runtime_rows(self):
        group = {
            "run_id": "sched-p1-i1",
            "merge_strategy": "role_sections",
            "merge_status": "pending",
            "policy": {"timeout_seconds": 45, "max_retries": 1, "cancel_on_failure": False},
            "children": [
                {
                    "child_execution_id": "backend-child-p1-i1-c1",
                    "child_run_id": "backend-run-1",
                    "run_id": "backend-run-1",
                    "parent_run_id": "sched-p1-i1",
                    "run_kind": "child",
                    "agent_role": "backend",
                    "agent_id": "backend-agent-p1-i1-c1",
                    "status": "queued",
                }
            ],
        }

        saved = self.repository.save_child_group(self.item, group)

        self.assertEqual(saved["run_id"], "sched-p1-i1")
        self.assertEqual(saved["children"][0]["agent_role"], "backend")
        self.assertEqual(saved["children"][0]["child_display_id"], "backend-run-1")
        self.assertEqual(self.db.query(SchedulerRunRecord).count(), 1)
        self.assertEqual(self.db.query(ChildRunRecord).count(), 1)

    def test_store_uses_relational_repository_when_injected(self):
        self.repository.save_child_group(
            self.item,
            {
                "run_id": "sched-p1-i1",
                "merge_strategy": "role_sections",
                "merge_status": "completed",
                "policy": {"timeout_seconds": 60},
                "children": [
                    {
                        "child_execution_id": "frontend-child-p1-i1-c2",
                        "child_run_id": "frontend-run-2",
                        "run_id": "frontend-run-2",
                        "parent_run_id": "sched-p1-i1",
                        "run_kind": "child",
                        "agent_role": "frontend",
                        "agent_id": "frontend-agent-p1-i1-c2",
                        "status": "completed",
                        "summary": "前端已完成",
                    }
                ],
            },
        )

        store = SchedulerRuntimeStore(repository=self.repository)
        runtime = store.load_runtime(self.item)

        self.assertEqual(runtime["persistence"]["backend"], "relational_tables")
        self.assertEqual(runtime["scheduler_run"]["merge_status"], "completed")
        self.assertEqual(runtime["child_runs"][0]["summary"], "前端已完成")
        self.assertEqual(runtime["child_runs"][0]["child_display_id"], "frontend-run-2")

    def test_repository_backfills_relational_rows_from_metadata_group(self):
        self.item.item_metadata = {
            "required_capabilities": ["filesystem.read"],
            "child_roles": ["backend"],
            "child_execution_group": {
                "run_id": "sched-p1-i1",
                "merge_strategy": "role_sections",
                "merge_status": "pending",
                "policy": {"timeout_seconds": 45},
                "children": [
                    {
                        "child_execution_id": "backend-child-p1-i1-c1",
                        "child_run_id": "backend-run-1",
                        "run_id": "backend-run-1",
                        "parent_run_id": "sched-p1-i1",
                        "run_kind": "child",
                        "agent_role": "backend",
                        "agent_id": "backend-agent-p1-i1-c1",
                        "status": "queued",
                    }
                ],
            },
        }

        group = self.repository.get_child_group(self.item)

        self.assertIsNotNone(group)
        self.assertEqual(group["run_id"], "sched-p1-i1")
        self.assertEqual(self.db.query(SchedulerRunRecord).count(), 1)
        self.assertEqual(self.db.query(ChildRunRecord).count(), 1)


if __name__ == "__main__":
    unittest.main()
