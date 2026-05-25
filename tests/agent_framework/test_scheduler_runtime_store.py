import unittest
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend.models import PermissionRequestRecord, PlanHandoffStatus, PlanItemRecord, PlanRunRecord, PlanStatus
from backend.services.scheduler_runtime_store import SchedulerRuntimeStore


class _FailingRuntimeRepository:
    @staticmethod
    def get_persistence_descriptor():
        return {
            "backend": "relational_tables",
            "scope": "scheduler_runs+child_runs",
            "durable": True,
            "migration_ready": True,
        }

    @staticmethod
    def get_required_capabilities(_item):
        return ["filesystem.read"]

    @staticmethod
    def get_metadata(item):
        return dict(item.item_metadata or {})

    @staticmethod
    def get_child_roles(_item):
        return ["backend"]

    @staticmethod
    def save_child_roles(_item, roles):
        return list(roles or [])

    @staticmethod
    def get_child_group(_item):
        raise RuntimeError("relational repository unavailable")

    @staticmethod
    def save_child_group(_item, _group):
        raise RuntimeError("relational repository unavailable")

    @staticmethod
    def list_children(_item):
        raise RuntimeError("relational repository unavailable")

    @staticmethod
    def find_child_group_entry(_item, _child_execution_id):
        raise RuntimeError("relational repository unavailable")

    @staticmethod
    def get_audit_trail(_item):
        return []

    @staticmethod
    def append_audit_trail(_item, entry, *, limit=50):
        return [dict(entry or {})][-limit:]

    @staticmethod
    def get_run_trace(_item):
        return []

    @staticmethod
    def append_run_trace(_item, entry, *, limit=100):
        return [dict(entry or {})][-limit:]


class SchedulerRuntimeStoreTests(unittest.TestCase):
    def setUp(self):
        self.store = SchedulerRuntimeStore()
        self.item = SimpleNamespace(
            item_metadata={
                "required_capabilities": ["filesystem.read", "search.query"],
                "child_roles": ["backend", "frontend"],
            }
        )

    def test_save_runtime_and_load_runtime_round_trip(self):
        self.store.save_runtime(
            self.item,
            scheduler_run={
                "run_id": "sched-p8-i3",
                "merge_strategy": "role_sections",
                "merge_status": "pending",
                "policy": {"timeout_seconds": 60, "max_retries": 2, "cancel_on_failure": True},
            },
            child_runs=[
                {
                    "child_execution_id": "backend-child-p8-i3-c1",
                    "run_id": "backend-run-1",
                    "agent_role": "backend",
                    "status": "queued",
                },
                {
                    "child_execution_id": "frontend-child-p8-i3-c2",
                    "run_id": "frontend-run-2",
                    "agent_role": "frontend",
                    "status": "running",
                },
            ],
        )

        runtime = self.store.load_runtime(self.item)

        self.assertEqual(runtime["scheduler_run"]["run_id"], "sched-p8-i3")
        self.assertEqual(runtime["scheduler_run"]["policy"]["timeout_seconds"], 60)
        self.assertEqual(len(runtime["child_runs"]), 2)
        self.assertEqual(runtime["child_runs"][0]["parent_run_id"], "sched-p8-i3")
        self.assertEqual(runtime["child_runs"][1]["status"], "running")
        self.assertEqual(runtime["child_runs"][0]["child_display_id"], runtime["child_runs"][0]["child_run_id"])
        self.assertEqual(runtime["persistence"]["backend"], "metadata_adapter")

        runtime_state = self.store.load_runtime_state(self.item)
        self.assertEqual(runtime_state.scheduler_run.child_count, 2)
        self.assertEqual(runtime_state.scheduler_run.active_children, 2)
        self.assertEqual(
            runtime_state.child_runs[0].to_dict()["child_display_id"],
            runtime_state.child_runs[0].child_run_id,
        )

    def test_update_child_run_persists_changes(self):
        self.store.save_runtime(
            self.item,
            scheduler_run={"run_id": "sched-p8-i3", "merge_strategy": "role_sections", "merge_status": "pending"},
            child_runs=[
                {
                    "child_execution_id": "backend-child-p8-i3-c1",
                    "agent_role": "backend",
                    "status": "queued",
                }
            ],
        )

        updated = self.store.update_child_run(
            self.item,
            "backend-child-p8-i3-c1",
            {
                "status": "completed",
                "summary": "后端已完成",
                "provider_name": "ollama",
            },
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated["status"], "completed")
        self.assertEqual(updated["summary"], "后端已完成")
        self.assertEqual(self.store.get_child_run(self.item, "backend-child-p8-i3-c1")["provider_name"], "ollama")

    def test_store_exposes_required_capabilities_and_child_roles(self):
        self.assertEqual(self.store.get_required_capabilities(self.item), ["filesystem.read", "search.query"])
        self.assertEqual(self.store.get_child_roles(self.item), ["backend", "frontend"])
        self.assertEqual(self.store.get_persistence_descriptor()["scope"], "plan_item_metadata")

    def test_store_falls_back_to_metadata_when_repository_operation_fails(self):
        item = SimpleNamespace(
            item_metadata={
                "child_execution_group": {
                    "run_id": "sched-p9-i4",
                    "merge_strategy": "role_sections",
                    "merge_status": "completed",
                    "children": [
                        {
                            "child_execution_id": "backend-child-p9-i4-c1",
                            "run_id": "backend-run-1",
                            "agent_role": "backend",
                            "status": "completed",
                            "summary": "后端已完成",
                        }
                    ],
                }
            }
        )

        store = SchedulerRuntimeStore(repository=_FailingRuntimeRepository())
        runtime = store.load_runtime(item)

        self.assertEqual(runtime["scheduler_run"]["run_id"], "sched-p9-i4")
        self.assertEqual(runtime["child_runs"][0]["summary"], "后端已完成")
        self.assertEqual(store.get_persistence_descriptor()["backend"], "metadata_adapter")
        self.assertEqual(store.get_persistence_descriptor()["effective_backend"], "metadata")
        self.assertEqual(
            store.get_persistence_descriptor()["fallback_reason"],
            "runtime_operation_failed:get_child_group",
        )

    def test_store_projects_approval_background_and_worktree_views_from_trace(self):
        item = SimpleNamespace(
            plan_id=1,
            item_metadata={
                "run_trace": [
                    {
                        "timestamp": "2026-05-05T10:00:00Z",
                        "run_id": "sched-p1-i1",
                        "parent_run_id": None,
                        "child_run_id": None,
                        "run_kind": "scheduler",
                        "scheduler_run_id": "sched-p1-i1",
                        "source": "permission",
                        "event_type": "tool_permission_required",
                        "summary": "工具等待授权",
                        "detail": "request_id=perm-001",
                        "payload": {
                            "request_id": "perm-001",
                            "tool_name": "filesystem.write",
                            "permission_level": "ask",
                            "tool_args": {"path": "README.md"},
                        },
                    },
                    {
                        "timestamp": "2026-05-05T10:00:05Z",
                        "run_id": "bg-run-1",
                        "parent_run_id": "sched-p1-i1",
                        "child_run_id": None,
                        "run_kind": "background",
                        "scheduler_run_id": "sched-p1-i1",
                        "source": "background",
                        "event_type": "background_started",
                        "summary": "后台任务已启动",
                        "detail": "后台整理 artifacts",
                        "payload": {"title": "后台整理 artifacts", "status": "running"},
                    },
                    {
                        "timestamp": "2026-05-05T10:00:08Z",
                        "run_id": "wt-run-1",
                        "parent_run_id": "sched-p1-i1",
                        "child_run_id": None,
                        "run_kind": "child",
                        "scheduler_run_id": "sched-p1-i1",
                        "source": "worktree",
                        "event_type": "worktree_prepared",
                        "summary": "工作区已准备",
                        "detail": "branch=feature/runtime-store",
                        "payload": {
                            "worktree_run_id": "wt-run-1",
                            "workspace_path": "D:/tmp/worktrees/p1-i1",
                            "branch_name": "feature/runtime-store",
                            "status": "running",
                        },
                    },
                ]
            },
        )

        runtime = self.store.load_runtime(item)

        self.assertEqual(runtime["approval_requests"][0]["request_id"], "perm-001")
        self.assertEqual(runtime["approval_requests"][0]["status"], "pending")
        self.assertEqual(runtime["background_runs"][0]["background_run_id"], "bg-run-1")
        self.assertEqual(runtime["worktree_runs"][0]["workspace_path"], "D:/tmp/worktrees/p1-i1")


class SchedulerRuntimeStoreDatabaseProjectionTests(unittest.TestCase):
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
            conversation_id=21,
            objective="验证 runtime store 审批投影",
            source="manual",
            status=PlanStatus.IN_PROGRESS,
            summary="执行中",
            plan_metadata={},
        )
        self.db.add(plan)
        self.db.flush()
        self.item = PlanItemRecord(
            plan_id=plan.id,
            step_order=1,
            title="等待权限批准",
            details="验证审批状态合并",
            status=PlanStatus.IN_PROGRESS,
            owner="planner",
            agent_role="backend",
            agent_id="backend-agent-p1-i1",
            handoff_status=PlanHandoffStatus.EXECUTING,
            item_metadata={
                "run_trace": [
                    {
                        "timestamp": "2026-05-05T10:00:00Z",
                        "run_id": "sched-p1-i1",
                        "source": "permission",
                        "event_type": "tool_permission_required",
                        "payload": {
                            "request_id": "perm-db-001",
                            "tool_name": "filesystem.write",
                            "permission_level": "ask",
                        },
                    }
                ]
            },
        )
        self.db.add(self.item)
        self.db.add(
            PermissionRequestRecord(
                request_id="perm-db-001",
                tool_name="filesystem.write",
                tool_args={"path": "README.md"},
                permission_level="ask",
                status="approved",
                user_id=1,
                conversation_id=21,
                plan_id=plan.id,
                plan_item_id=self.item.id,
                run_id="child-run-db-001",
                parent_run_id="sched-run-db-001",
                child_run_id="child-run-db-001",
                scheduler_run_id="sched-run-db-001",
                run_kind="child",
                request_metadata={"tool_call_id": "call-db-001"},
                result="approved",
            )
        )
        self.db.commit()
        store = SchedulerRuntimeStore(db=self.db)
        store.record_background_run(
            self.item,
            {
                "background_run_id": "bg-db-001",
                "run_id": "bg-db-001",
                "parent_run_id": "sched-run-db-001",
                "scheduler_run_id": "sched-run-db-001",
                "status": "completed",
                "source": "background",
                "event_type": "background_completed",
                "title": "后台整理 artifacts",
                "detail": "后台任务完成",
                "artifact_id": "artifact_bg_001",
                "artifact_kind": "runtime_skill_effect",
                "metadata": {"selected_count": 2},
            },
        )
        store.record_worktree_run(
            self.item,
            {
                "worktree_run_id": "wt-db-001",
                "run_id": "wt-db-001",
                "parent_run_id": "sched-run-db-001",
                "scheduler_run_id": "sched-run-db-001",
                "status": "running",
                "source": "worktree",
                "event_type": "worktree_prepared",
                "workspace_path": "D:/tmp/worktrees/db",
                "branch_name": "feature/runtime-activity",
                "detail": "工作区已创建",
                "metadata": {"owner": "backend"},
            },
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def test_store_merges_permission_records_into_runtime_projection(self):
        store = SchedulerRuntimeStore(db=self.db)

        runtime = store.load_runtime(self.item)

        self.assertEqual(runtime["approval_requests"][0]["request_id"], "perm-db-001")
        self.assertEqual(runtime["approval_requests"][0]["status"], "approved")
        self.assertEqual(runtime["approval_requests"][0]["conversation_id"], 21)
        self.assertEqual(runtime["approval_requests"][0]["plan_item_id"], self.item.id)
        self.assertEqual(runtime["approval_requests"][0]["run_id"], "child-run-db-001")
        self.assertEqual(runtime["approval_requests"][0]["request_metadata"]["tool_call_id"], "call-db-001")
        self.assertEqual(runtime["approval_requests"][0]["tool_args"]["path"], "README.md")
        self.assertEqual(runtime["background_runs"][0]["background_run_id"], "bg-db-001")
        self.assertEqual(runtime["background_runs"][0]["artifact_id"], "artifact_bg_001")
        self.assertEqual(runtime["worktree_runs"][0]["worktree_run_id"], "wt-db-001")
        self.assertEqual(runtime["worktree_runs"][0]["branch_name"], "feature/runtime-activity")


if __name__ == "__main__":
    unittest.main()
