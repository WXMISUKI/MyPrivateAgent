import unittest
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend.models import PlanItemRecord, PlanRunRecord
from backend.models import PlanHandoffStatus, PlanStatus
from backend.services.scheduler_service import SchedulerService


class _StubDb:
    def commit(self):
        return None

    def refresh(self, _obj):
        return None


class SchedulerServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = SchedulerService(db=_StubDb())
        self.item = SimpleNamespace(
            id=11,
            plan_id=1,
            step_order=1,
            title="完成前后端联调并补测试文档",
            details="需要同时处理前端页面、后端接口、回归测试和说明文档。",
            status=PlanStatus.IN_PROGRESS,
            owner="主智能体",
            agent_role="planner",
            agent_id=None,
            handoff_status=PlanHandoffStatus.READY,
            item_metadata={"required_capabilities": ["filesystem.read"], "child_roles": ["backend", "frontend", "qa", "docs"]},
        )
        self.plan = SimpleNamespace(
            id=1,
            active_item_id=11,
            items=[self.item],
        )

    def test_prepare_execution_builds_fanout_context_and_child_records(self):
        state = self.service.prepare_execution(plan=self.plan, item=self.item)

        self.assertIsNotNone(state)
        self.assertEqual(state["child_count"], 4)
        self.assertEqual(state["execution_context"]["run_id"], "sched-p1-i11")
        self.assertEqual(state["execution_context"]["run_kind"], "scheduler")
        self.assertEqual(state["execution_context"]["scheduler_mode"], "fan_out")
        self.assertEqual(len(state["execution_context"]["child_contexts"]), 4)
        self.assertEqual(self.item.agent_id, "scheduler-p1-i11")
        self.assertEqual(self.item.handoff_status, PlanHandoffStatus.HANDED_OFF)
        children = self.item.item_metadata["child_execution_group"]["children"]
        self.assertEqual(children[0]["status"], "queued")
        self.assertEqual(children[0]["parent_run_id"], "sched-p1-i11")
        self.assertEqual(children[0]["run_kind"], "child")

    def test_merge_child_outputs_supports_partial_failure(self):
        state = self.service.prepare_execution(plan=self.plan, item=self.item)
        children = state["execution_context"]["child_contexts"]

        self.service.mark_child_running(plan=self.plan, item_id=11, child_execution_id=children[0]["child_execution_id"])
        self.service.mark_child_completed(
            plan=self.plan,
            item_id=11,
            child_execution_id=children[0]["child_execution_id"],
            output_text="后端接口已完成",
        )
        self.service.mark_child_failed(
            plan=self.plan,
            item_id=11,
            child_execution_id=children[1]["child_execution_id"],
            error_text="前端构建失败",
        )

        merged = self.service.merge_child_outputs(plan=self.plan, item_id=11)

        self.assertEqual(merged["merge_status"], "partial_failed")
        self.assertIn("[backend] 后端接口已完成", merged["merged_output"])
        self.assertIn("frontend=前端构建失败", merged["merged_output"])
        self.assertEqual(
            self.item.item_metadata["child_execution_group"]["merge_status"],
            "partial_failed",
        )

    def test_prepare_execution_includes_default_policy(self):
        state = self.service.prepare_execution(plan=self.plan, item=self.item)

        policy = state["execution_context"]["child_contexts"][0]["scheduler_policy"]

        self.assertEqual(policy["timeout_seconds"], 45)
        self.assertEqual(policy["max_retries"], 1)
        self.assertFalse(policy["cancel_on_failure"])

    def test_mark_child_cancelled_updates_child_status(self):
        state = self.service.prepare_execution(plan=self.plan, item=self.item)
        child_id = state["execution_context"]["child_contexts"][0]["child_execution_id"]

        self.service.mark_child_cancelled(
            plan=self.plan,
            item_id=11,
            child_execution_id=child_id,
            reason="检测到上游失败，已取消",
        )

        child = self.item.item_metadata["child_execution_group"]["children"][0]
        self.assertEqual(child["status"], "cancelled")
        self.assertEqual(child["error_kind"], "cancelled")

    def test_mark_child_policy_selected_updates_child_route_fields(self):
        state = self.service.prepare_execution(plan=self.plan, item=self.item)
        child_id = state["execution_context"]["child_contexts"][0]["child_execution_id"]
        self.service.mark_child_policy_selected(
            plan=self.plan,
            item_id=11,
            child_execution_id=child_id,
            model_name="llama3.1",
            provider_name="ollama",
            provider_order=["ollama", "volcengine-ark"],
            provider_switch_count=1,
            provider_history=[{"provider_name": "volcengine-ark", "model_name": "doubao", "reason": "initial"}],
        )
        child = self.item.item_metadata["child_execution_group"]["children"][0]
        self.assertEqual(child["model_name"], "llama3.1")
        self.assertEqual(child["provider_name"], "ollama")
        self.assertEqual(child["provider_order"], ["ollama", "volcengine-ark"])
        self.assertEqual(child["provider_switch_count"], 1)

    def test_build_execution_context_rehydrates_from_runtime_metadata(self):
        self.service.prepare_execution(plan=self.plan, item=self.item)

        execution_context = self.service.build_execution_context(
            plan=self.plan,
            item=self.item,
        )

        self.assertIsNotNone(execution_context)
        self.assertEqual(execution_context["scheduler_run_id"], "sched-p1-i11")
        self.assertEqual(execution_context["child_contexts"][0]["scheduler_policy"]["timeout_seconds"], 45)
        self.assertEqual(execution_context["child_contexts"][0]["required_capabilities"], ["filesystem.read"])

    def test_append_audit_event_records_timeline_entry(self):
        self.service.prepare_execution(plan=self.plan, item=self.item)

        self.service.append_audit_event(
            plan=self.plan,
            item_id=11,
            event_type="scheduler_retry",
            content="后端子执行开始重试",
            payload={"retry_count": 1},
        )

        trail = self.service.get_audit_trail(self.item)
        self.assertTrue(trail)
        self.assertEqual(trail[-1]["event_type"], "scheduler_retry")
        self.assertEqual(trail[-1]["payload"]["retry_count"], 1)

    def test_append_run_trace_event_records_unified_trace_entry(self):
        self.service.prepare_execution(plan=self.plan, item=self.item)

        self.service.append_run_trace_event(
            plan=self.plan,
            item_id=11,
            source="capability",
            event_type="capability_blocked",
            summary="能力依赖不足",
            detail="缺少 filesystem.read",
            severity="error",
            payload={"missing_capabilities": ["filesystem.read"]},
        )

        trace = self.service.get_run_trace(self.item)
        self.assertTrue(trace)
        self.assertEqual(trace[-1]["source"], "capability")
        self.assertEqual(trace[-1]["severity"], "error")
        self.assertEqual(trace[-1]["run_id"], "sched-p1-i11")
        self.assertEqual(trace[-1]["run_kind"], "scheduler")

    def test_resolve_child_roles_uses_subagent_registry_triggers(self):
        self.item.item_metadata = {"required_capabilities": ["filesystem.read"]}
        self.item.title = "做 research compare 并产出 planning 结论"
        self.item.details = "需要事实比对和方案拆解"

        roles = self.service._resolve_child_roles(self.item)

        self.assertIn("researcher", roles)
        self.assertIn("planner", roles)


class SchedulerServicePersistenceTests(unittest.TestCase):
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
            objective="验证 activity persistence",
            source="manual",
            status=PlanStatus.IN_PROGRESS,
            active_item_id=None,
            summary="执行中",
            plan_metadata={},
        )
        self.db.add(plan)
        self.db.flush()
        item = PlanItemRecord(
            plan_id=plan.id,
            step_order=1,
            title="落库 background/worktree",
            details="验证调度器 trace 钩子",
            status=PlanStatus.IN_PROGRESS,
            owner="planner",
            agent_role="planner",
            agent_id="scheduler-p1-i1",
            handoff_status=PlanHandoffStatus.EXECUTING,
            item_metadata={"required_capabilities": ["filesystem.read"]},
        )
        self.db.add(item)
        self.db.flush()
        plan.active_item_id = item.id
        self.db.commit()
        self.db.refresh(plan)
        self.db.refresh(item)
        self.plan = plan
        self.item = item
        self.service = SchedulerService(self.db)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def test_append_run_trace_event_persists_background_and_worktree_activities(self):
        self.service.append_run_trace_event(
            plan=self.plan,
            item_id=self.item.id,
            source="background",
            event_type="background_completed",
            summary="后台任务完成",
            detail="已整理运行时 artifact",
            payload={
                "background_run_id": "bg-persist-001",
                "status": "completed",
                "title": "后台任务",
                "artifact_id": "artifact-001",
                "artifact_kind": "runtime_skill_effect",
                "run_id": "bg-persist-001",
            },
        )
        self.service.append_run_trace_event(
            plan=self.plan,
            item_id=self.item.id,
            source="worktree",
            event_type="worktree_prepared",
            summary="工作区已准备",
            detail="branch=feature/runtime-activity",
            payload={
                "worktree_run_id": "wt-persist-001",
                "status": "running",
                "workspace_path": "D:/tmp/worktrees/persist",
                "branch_name": "feature/runtime-activity",
                "run_id": "wt-persist-001",
            },
        )

        background_runs = self.service.get_background_runs(self.item)
        worktree_runs = self.service.get_worktree_runs(self.item)

        self.assertEqual(background_runs[0]["background_run_id"], "bg-persist-001")
        self.assertEqual(background_runs[0]["artifact_id"], "artifact-001")
        self.assertEqual(worktree_runs[0]["worktree_run_id"], "wt-persist-001")
        self.assertEqual(worktree_runs[0]["workspace_path"], "D:/tmp/worktrees/persist")


if __name__ == "__main__":
    unittest.main()
