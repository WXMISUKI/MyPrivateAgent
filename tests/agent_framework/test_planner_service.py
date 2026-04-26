import unittest
from types import SimpleNamespace

from backend.models import PlanStatus
from backend.services.planner_service import PlannerService


class PlannerServiceTests(unittest.TestCase):
    def test_serialize_plan_includes_required_capabilities(self):
        plan = SimpleNamespace(
            id=1,
            user_id=2,
            conversation_id=3,
            objective="完善 MCP 执行链路",
            source="manual",
            status="pending",
            active_item_id=None,
            summary="待执行",
            created_at="2026-04-25T00:00:00",
            updated_at="2026-04-25T00:00:01",
            items=[
                SimpleNamespace(
                    id=11,
                    plan_id=1,
                    step_order=1,
                    title="接入 filesystem.read",
                    details="需要读取仓库内容",
                    status="pending",
                    owner="后端子智能体",
                    agent_role="backend",
                    agent_id="backend-agent-p1-i11",
                    handoff_status="ready",
                    item_metadata={
                        "required_capabilities": ["filesystem.read", "search.query"],
                        "audit_trail": [
                            {
                                "timestamp": "2026-04-25T18:00:00Z",
                                "event_type": "scheduler_fanout_prepared",
                                "content": "已准备 1 个子执行单元",
                                "payload": {"child_count": 1},
                            }
                        ],
                        "run_trace": [
                            {
                                "timestamp": "2026-04-25T18:00:01Z",
                                "source": "scheduler",
                                "event_type": "scheduler_fanout_prepared",
                                "severity": "info",
                                "summary": "已准备 1 个子执行单元",
                                "detail": "调度器已完成 fan-out 拆分。",
                                "payload": {"child_count": 1},
                            }
                        ],
                        "child_execution_group": {
                            "run_id": "sched-p1-i11",
                            "merge_strategy": "role_sections",
                            "merge_status": "completed",
                            "merged_output": "[backend] 已完成后端接口",
                            "children": [
                                {
                                    "child_execution_id": "backend-child-p1-i11-c1",
                                    "agent_role": "backend",
                                    "agent_id": "backend-agent-p1-i11-c1",
                                    "status": "completed",
                                    "summary": "已完成后端接口",
                                }
                            ],
                        },
                    },
                    created_at="2026-04-25T00:00:00",
                    updated_at="2026-04-25T00:00:01",
                )
            ],
        )
        service = PlannerService(db=None)

        serialized = service.serialize_plan(plan)

        self.assertEqual(serialized["items"][0]["required_capabilities"], ["filesystem.read", "search.query"])
        self.assertEqual(serialized["items"][0]["child_executions"][0]["agent_role"], "backend")
        self.assertEqual(serialized["items"][0]["merge_summary"]["merge_status"], "completed")
        self.assertEqual(serialized["items"][0]["audit_trail"][0]["event_type"], "scheduler_fanout_prepared")
        self.assertEqual(serialized["items"][0]["run_trace"][0]["source"], "scheduler")

    def test_suggest_assignment_adds_capabilities_for_filesystem_and_search(self):
        service = PlannerService(db=None)

        assignment = service._suggest_assignment("分析代码库并搜索相关文档")

        self.assertIn("filesystem.read", assignment["required_capabilities"])
        self.assertIn("search.query", assignment["required_capabilities"])

    def test_block_active_item_marks_plan_as_blocked_and_records_guard_metadata(self):
        service = PlannerService(db=SimpleNamespace(commit=lambda: None, refresh=lambda _obj: None))
        active_item = SimpleNamespace(
            id=11,
            status=PlanStatus.IN_PROGRESS,
            details="原始描述",
            item_metadata={"required_capabilities": ["filesystem.read"]},
            agent_role="backend",
            agent_id="backend-agent-p1-i11",
            handoff_status="executing",
        )
        plan = SimpleNamespace(
            id=1,
            user_id=2,
            conversation_id=3,
            objective="完善 MCP 执行链路",
            source="manual",
            status=PlanStatus.IN_PROGRESS,
            active_item_id=11,
            summary="执行中",
            items=[active_item],
        )

        updated = service.block_active_item(
            plan=plan,
            reason="缺少能力依赖",
            missing_capabilities=["filesystem.read"],
            unavailable_capabilities=["search.query"],
        )

        self.assertIs(updated, plan)
        self.assertEqual(active_item.status, PlanStatus.BLOCKED)
        self.assertEqual(plan.status, PlanStatus.BLOCKED)
        self.assertIsNone(plan.active_item_id)
        self.assertEqual(
            active_item.item_metadata["capability_guard"]["missing_capabilities"],
            ["filesystem.read"],
        )
        self.assertIn("阻塞原因", active_item.details)


if __name__ == "__main__":
    unittest.main()
