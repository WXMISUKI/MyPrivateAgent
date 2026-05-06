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
                            },
                            {
                                "timestamp": "2026-04-25T18:00:02Z",
                                "source": "permission",
                                "event_type": "tool_permission_required",
                                "severity": "warning",
                                "summary": "工具等待授权",
                                "detail": "request_id=perm-p1-i11",
                                "payload": {
                                    "request_id": "perm-p1-i11",
                                    "tool_name": "filesystem.write",
                                    "permission_level": "ask",
                                    "tool_args": {"path": "README.md"},
                                },
                            },
                            {
                                "timestamp": "2026-04-25T18:00:03Z",
                                "run_id": "bg-run-p1-i11",
                                "parent_run_id": "sched-p1-i11",
                                "child_run_id": None,
                                "run_kind": "background",
                                "scheduler_run_id": "sched-p1-i11",
                                "source": "background",
                                "event_type": "background_started",
                                "severity": "info",
                                "summary": "后台任务已启动",
                                "detail": "background artifact generation",
                                "payload": {
                                    "background_run_id": "bg-run-p1-i11",
                                    "status": "running",
                                    "title": "后台任务",
                                },
                            },
                            {
                                "timestamp": "2026-04-25T18:00:04Z",
                                "run_id": "wt-run-p1-i11",
                                "parent_run_id": "sched-p1-i11",
                                "child_run_id": None,
                                "run_kind": "child",
                                "scheduler_run_id": "sched-p1-i11",
                                "source": "worktree",
                                "event_type": "worktree_prepared",
                                "severity": "info",
                                "summary": "工作区已准备",
                                "detail": "branch=feature/runtime-store",
                                "payload": {
                                    "worktree_run_id": "wt-run-p1-i11",
                                    "workspace_path": "D:/tmp/worktrees/p1-i11",
                                    "branch_name": "feature/runtime-store",
                                    "status": "running",
                                },
                            },
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
        self.assertEqual(serialized["items"][0]["scheduler_run"]["run_id"], "sched-p1-i11")
        self.assertEqual(serialized["items"][0]["scheduler_snapshot"]["child_count"], 1)
        self.assertEqual(serialized["items"][0]["scheduler_snapshot"]["child_status_counts"]["completed"], 1)
        self.assertEqual(serialized["items"][0]["child_executions"][0]["agent_role"], "backend")
        self.assertEqual(serialized["items"][0]["merge_summary"]["merge_status"], "completed")
        self.assertEqual(serialized["items"][0]["audit_trail"][0]["event_type"], "scheduler_fanout_prepared")
        self.assertEqual(serialized["items"][0]["run_trace"][0]["source"], "scheduler")
        self.assertEqual(serialized["items"][0]["runtime_summary"]["child_run_count"], 1)
        self.assertEqual(serialized["items"][0]["runtime_summary"]["approval_request_count"], 1)
        self.assertEqual(serialized["items"][0]["runtime_summary"]["background_run_count"], 1)
        self.assertEqual(serialized["items"][0]["runtime_summary"]["worktree_run_count"], 1)
        self.assertEqual(serialized["items"][0]["runtime_persistence"]["backend"], "metadata_adapter")

    def test_serialize_plan_item_runtime_and_trace_support_runtime_views(self):
        item = SimpleNamespace(
            id=11,
            plan_id=1,
            title="接入 filesystem.read",
            agent_role="backend",
            agent_id="backend-agent-p1-i11",
            handoff_status="executing",
            item_metadata={
                "required_capabilities": ["filesystem.read"],
                "audit_trail": [
                    {"timestamp": "2026-04-25T18:00:00Z", "event_type": "child_running", "content": "开始执行", "payload": {}}
                ],
                "run_trace": [
                    {
                        "timestamp": "2026-04-25T18:00:01Z",
                        "run_id": "sched-p1-i11",
                        "parent_run_id": None,
                        "child_run_id": None,
                        "run_kind": "scheduler",
                        "scheduler_run_id": "sched-p1-i11",
                        "plan_id": 1,
                        "plan_item_id": 11,
                        "agent_role": "backend",
                        "agent_id": "backend-agent-p1-i11",
                        "source": "scheduler",
                        "event_type": "scheduler_fanout_prepared",
                        "severity": "info",
                        "summary": "已准备 1 个子执行单元",
                        "detail": "调度器已完成 fan-out 拆分。",
                        "payload": {"child_count": 1},
                    },
                    {
                        "timestamp": "2026-04-25T18:00:02Z",
                        "run_id": "backend-child-p1-i11-c1",
                        "parent_run_id": "sched-p1-i11",
                        "child_run_id": "backend-child-p1-i11-c1",
                        "run_kind": "child",
                        "scheduler_run_id": "sched-p1-i11",
                        "plan_id": 1,
                        "plan_item_id": 11,
                        "agent_role": "backend",
                        "agent_id": "backend-agent-p1-i11-c1",
                        "source": "subagent",
                        "event_type": "child_completed",
                        "severity": "success",
                        "summary": "backend 子执行已完成",
                        "detail": "已完成后端接口",
                        "payload": {"child_execution_id": "backend-child-p1-i11-c1"},
                    },
                    {
                        "timestamp": "2026-04-25T18:00:03Z",
                        "run_id": "perm-p1-i11",
                        "parent_run_id": None,
                        "child_run_id": None,
                        "run_kind": "scheduler",
                        "scheduler_run_id": "sched-p1-i11",
                        "plan_id": 1,
                        "plan_item_id": 11,
                        "agent_role": "backend",
                        "agent_id": "backend-agent-p1-i11",
                        "source": "permission",
                        "event_type": "tool_permission_required",
                        "severity": "warning",
                        "summary": "工具等待授权",
                        "detail": "request_id=perm-p1-i11",
                        "payload": {
                            "request_id": "perm-p1-i11",
                            "tool_name": "filesystem.write",
                            "permission_level": "ask",
                            "tool_args": {"path": "README.md"},
                        },
                    },
                    {
                        "timestamp": "2026-04-25T18:00:04Z",
                        "run_id": "bg-run-p1-i11",
                        "parent_run_id": "sched-p1-i11",
                        "child_run_id": None,
                        "run_kind": "background",
                        "scheduler_run_id": "sched-p1-i11",
                        "plan_id": 1,
                        "plan_item_id": 11,
                        "agent_role": "background",
                        "agent_id": "background-agent-p1-i11",
                        "source": "background",
                        "event_type": "background_completed",
                        "severity": "success",
                        "summary": "后台任务已完成",
                        "detail": "artifact index refreshed",
                        "payload": {
                            "background_run_id": "bg-run-p1-i11",
                            "status": "completed",
                            "title": "后台任务",
                        },
                    },
                    {
                        "timestamp": "2026-04-25T18:00:05Z",
                        "run_id": "wt-run-p1-i11",
                        "parent_run_id": "sched-p1-i11",
                        "child_run_id": None,
                        "run_kind": "child",
                        "scheduler_run_id": "sched-p1-i11",
                        "plan_id": 1,
                        "plan_item_id": 11,
                        "agent_role": "backend",
                        "agent_id": "backend-agent-p1-i11",
                        "source": "worktree",
                        "event_type": "worktree_prepared",
                        "severity": "info",
                        "summary": "工作区已准备",
                        "detail": "branch=feature/runtime-store",
                        "payload": {
                            "worktree_run_id": "wt-run-p1-i11",
                            "workspace_path": "D:/tmp/worktrees/p1-i11",
                            "branch_name": "feature/runtime-store",
                            "status": "running",
                        },
                    },
                ],
                "child_execution_group": {
                    "run_id": "sched-p1-i11",
                    "merge_strategy": "role_sections",
                    "merge_status": "completed",
                    "merged_output": "[backend] 已完成后端接口",
                    "children": [
                        {
                            "child_execution_id": "backend-child-p1-i11-c1",
                            "child_run_id": "backend-child-p1-i11-c1",
                            "run_id": "backend-child-p1-i11-c1",
                            "parent_run_id": "sched-p1-i11",
                            "run_kind": "child",
                            "agent_role": "backend",
                            "agent_id": "backend-agent-p1-i11-c1",
                            "status": "completed",
                            "summary": "已完成后端接口",
                        }
                    ],
                },
            },
        )
        service = PlannerService(db=None)

        runtime_view = service.serialize_plan_item_runtime(item)
        trace_view = service.serialize_plan_item_trace(item, source="subagent", limit=10)

        self.assertEqual(runtime_view["scheduler_run"]["run_kind"], "scheduler")
        self.assertEqual(runtime_view["child_runs"][0]["run_kind"], "child")
        self.assertEqual(runtime_view["runtime_summary"]["run_trace_count"], 5)
        self.assertEqual(runtime_view["approval_requests"][0]["request_id"], "perm-p1-i11")
        self.assertEqual(runtime_view["background_runs"][0]["background_run_id"], "bg-run-p1-i11")
        self.assertEqual(runtime_view["worktree_runs"][0]["workspace_path"], "D:/tmp/worktrees/p1-i11")
        self.assertEqual(runtime_view["runtime_summary"]["approval_request_count"], 1)
        self.assertEqual(runtime_view["runtime_summary"]["background_run_count"], 1)
        self.assertEqual(runtime_view["runtime_summary"]["worktree_run_count"], 1)
        self.assertEqual(runtime_view["runtime_persistence"]["scope"], "plan_item_metadata")
        self.assertEqual(trace_view["summary"]["total"], 1)
        self.assertEqual(trace_view["events"][0]["event_type"], "child_completed")
        self.assertEqual(trace_view["runtime_persistence"]["backend"], "metadata_adapter")

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
