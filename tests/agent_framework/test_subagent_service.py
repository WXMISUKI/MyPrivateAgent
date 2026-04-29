import unittest

from backend.services.subagent_service import (
    SubagentContext,
    SubagentRuntimeService,
    get_subagent_runtime_service,
)


class SubagentRuntimeServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = SubagentRuntimeService()
        self.context = SubagentContext(
            agent_role="frontend",
            agent_id="frontend-agent-p10-i23",
            plan_id=10,
            plan_item_id=23,
            plan_item_title="实现聊天页交互",
            handoff_status="executing",
        )

    def test_normalize_context_returns_none_for_general_role(self):
        context = self.service.normalize_context({
            "agent_role": "general",
            "agent_id": "general-agent-p1-i1",
        })
        self.assertIsNone(context)

    def test_normalize_context_builds_subagent_context(self):
        context = self.service.normalize_context({
            "agent_role": "backend",
            "agent_id": "backend-agent-p9-i2",
            "plan_id": 9,
            "plan_item_id": 2,
            "plan_item_title": "实现 plans API",
            "handoff_status": "handed_off",
        })

        self.assertIsNotNone(context)
        self.assertEqual(context.agent_role, "backend")
        self.assertEqual(context.plan_item_title, "实现 plans API")

    def test_build_role_system_prompt_mentions_role_and_scope(self):
        prompt = self.service.build_role_system_prompt(self.context)

        self.assertIn("frontend", prompt)
        self.assertIn("agent_id=frontend-agent-p10-i23", prompt)
        self.assertIn("实现聊天页交互", prompt)

    def test_build_spawn_collect_merge_events_include_runtime_fields(self):
        spawn_event = self.service.build_spawn_event(self.context)
        collect_event = self.service.build_collect_event(self.context, output_text="已完成页面交互和按钮态整理")
        merge_event = self.service.build_merge_event(self.context)

        self.assertEqual(spawn_event["status_kind"], "subagent_spawned")
        self.assertEqual(collect_event["status_kind"], "subagent_collected")
        self.assertEqual(merge_event["status_kind"], "subagent_merged")
        self.assertEqual(spawn_event["agent_id"], "frontend-agent-p10-i23")
        self.assertIn("页面交互", collect_event["subagent_output_excerpt"])

    def test_runtime_contract_exposes_registered_profiles(self):
        contract = self.service.build_runtime_contract()
        self.assertGreaterEqual(contract["total_profiles"], 3)
        names = {item["name"] for item in contract["profiles"]}
        self.assertIn("planner", names)
        self.assertIn("researcher", names)
        self.assertIn("executor", names)

    def test_role_prompt_includes_profile_governance(self):
        planner_context = SubagentContext(
            agent_role="planner",
            agent_id="planner-agent-p1-i2",
            plan_id=1,
            plan_item_id=2,
            plan_item_title="拆解执行路线",
            handoff_status="executing",
        )
        prompt = self.service.build_role_system_prompt(planner_context)
        self.assertIn("可用工具范围", prompt)
        self.assertIn("上下文策略", prompt)

    def test_get_subagent_runtime_service_returns_singleton(self):
        first = get_subagent_runtime_service()
        second = get_subagent_runtime_service()
        self.assertIs(first, second)


if __name__ == "__main__":
    unittest.main()
