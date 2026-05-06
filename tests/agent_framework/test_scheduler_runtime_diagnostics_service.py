import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend.models import PermissionRequestRecord, PlanHandoffStatus, PlanItemRecord, PlanRunRecord, PlanStatus
from backend.services.scheduler_runtime_diagnostics_service import SchedulerRuntimeDiagnosticsService
from backend.services.scheduler_runtime_store import SchedulerRuntimeStore


class SchedulerRuntimeDiagnosticsServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = TestingSessionLocal()
        plan = PlanRunRecord(
            user_id=1,
            conversation_id=2,
            objective="验证 runtime backend diagnostics",
            source="manual",
            status=PlanStatus.IN_PROGRESS,
            summary="执行中",
            plan_metadata={},
        )
        self.db.add(plan)
        self.db.flush()
        item = PlanItemRecord(
            plan_id=plan.id,
            step_order=1,
            title="调度执行",
            details="诊断测试",
            status=PlanStatus.IN_PROGRESS,
            owner="主智能体",
            agent_role="planner",
            agent_id="scheduler-p1-i1",
            handoff_status=PlanHandoffStatus.EXECUTING,
            item_metadata={
                "required_capabilities": ["filesystem.read"],
                "child_roles": ["backend"],
                "run_trace": [
                    {
                        "timestamp": "2026-05-05T11:00:00Z",
                        "run_id": "sched-p1-i1",
                        "source": "permission",
                        "event_type": "tool_permission_required",
                        "payload": {
                            "request_id": "perm-diag-001",
                            "tool_name": "filesystem.write",
                            "permission_level": "ask",
                        },
                    },
                    {
                        "timestamp": "2026-05-05T11:00:02Z",
                        "run_id": "bg-diag-001",
                        "parent_run_id": "sched-p1-i1",
                        "run_kind": "background",
                        "source": "background",
                        "event_type": "background_started",
                        "payload": {"background_run_id": "bg-diag-001", "status": "running"},
                    },
                    {
                        "timestamp": "2026-05-05T11:00:03Z",
                        "run_id": "wt-diag-001",
                        "parent_run_id": "sched-p1-i1",
                        "source": "worktree",
                        "event_type": "worktree_prepared",
                        "payload": {
                            "worktree_run_id": "wt-diag-001",
                            "workspace_path": "D:/tmp/worktrees/diag",
                            "branch_name": "feature/diag",
                            "status": "running",
                        },
                    },
                ],
                "child_execution_group": {
                    "run_id": "sched-p1-i1",
                    "merge_strategy": "role_sections",
                    "merge_status": "pending",
                    "children": [
                        {
                            "child_execution_id": "backend-child-p1-i1-c1",
                            "child_run_id": "backend-run-1",
                            "run_id": "backend-run-1",
                            "agent_role": "backend",
                            "status": "queued",
                        }
                    ],
                },
            },
        )
        self.db.add(item)
        self.db.add(
            PermissionRequestRecord(
                request_id="perm-diag-001",
                tool_name="filesystem.write",
                tool_args={"path": "README.md"},
                permission_level="ask",
                status="approved",
                user_id=1,
                conversation_id=2,
                result="approved",
            )
        )
        self.db.commit()
        store = SchedulerRuntimeStore(db=self.db)
        store.record_background_run(
            item,
            {
                "background_run_id": "bg-diag-001",
                "run_id": "bg-diag-001",
                "parent_run_id": "sched-p1-i1",
                "scheduler_run_id": "sched-p1-i1",
                "status": "running",
                "source": "background",
                "event_type": "background_started",
                "title": "后台任务",
                "detail": "后台运行中",
                "metadata": {"selected_count": 1},
            },
        )
        store.record_worktree_run(
            item,
            {
                "worktree_run_id": "wt-diag-001",
                "run_id": "wt-diag-001",
                "parent_run_id": "sched-p1-i1",
                "scheduler_run_id": "sched-p1-i1",
                "status": "running",
                "source": "worktree",
                "event_type": "worktree_prepared",
                "workspace_path": "D:/tmp/worktrees/diag",
                "branch_name": "feature/diag",
                "detail": "工作区运行中",
                "metadata": {"owner": "backend"},
            },
        )
        self.db.commit()
        self.item = item
        self.service = SchedulerRuntimeDiagnosticsService(self.db)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def test_collect_status_returns_runtime_backend_summary(self):
        status = self.service.collect_status(limit=10)

        self.assertEqual(status["status"], "ok")
        self.assertIn("requested_backend", status)
        self.assertIn("table_status", status)
        self.assertEqual(status["metadata_runtime_summary"]["runtime_item_count"], 1)
        self.assertEqual(status["record_counts"]["background_runs"], 1)
        self.assertEqual(status["record_counts"]["worktree_runs"], 1)
        self.assertEqual(status["runtime_attachment_summary"]["approval_request_count"], 1)
        self.assertEqual(status["runtime_attachment_summary"]["background_run_count"], 1)
        self.assertEqual(status["runtime_attachment_summary"]["worktree_run_count"], 1)

    def test_reconcile_to_relational_backfills_runtime_tables(self):
        result = self.service.reconcile_to_relational(plan_id=self.item.plan_id, item_id=self.item.id, limit=10)

        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["table_ready"])
        self.assertEqual(result["reconciled_items"], 1)
        self.assertEqual(result["items"][0]["status"], "reconciled")


if __name__ == "__main__":
    unittest.main()
