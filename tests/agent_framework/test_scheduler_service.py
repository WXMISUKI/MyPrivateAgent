import unittest
from types import SimpleNamespace

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
        self.assertEqual(state["execution_context"]["scheduler_mode"], "fan_out")
        self.assertEqual(len(state["execution_context"]["child_contexts"]), 4)
        self.assertEqual(self.item.agent_id, "scheduler-p1-i11")
        self.assertEqual(self.item.handoff_status, PlanHandoffStatus.HANDED_OFF)
        children = self.item.item_metadata["child_execution_group"]["children"]
        self.assertEqual(children[0]["status"], "queued")

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


if __name__ == "__main__":
    unittest.main()
