import unittest
from types import SimpleNamespace

from backend.services.runtime_learning_service import RuntimeKnowledgeLevel, RuntimeLearningService


class RuntimeLearningServiceTests(unittest.TestCase):
    def test_build_runtime_context_merges_prompts_and_best_practices(self):
        prompts = [
            SimpleNamespace(
                prompt_key="weather_tool_policy",
                prompt_type="tool_usage",
                content="天气查询优先使用 search 工具，不要额外调用时间工具。",
            )
        ]
        practices = [
            SimpleNamespace(
                practice_id="BP-001",
                title="确定性结果直出",
                description="天气和时间类结果优先原样返回，避免二次模型改写。",
            )
        ]

        context = RuntimeLearningService.build_runtime_context(
            prompts=prompts,
            practices=practices,
        )

        self.assertFalse(context.is_empty)
        self.assertIn("weather_tool_policy", context.system_prompt)
        self.assertIn("BP-001", context.system_prompt)
        self.assertEqual(context.prompt_count, 1)
        self.assertEqual(context.practice_count, 1)

    def test_build_runtime_context_is_empty_when_no_knowledge(self):
        context = RuntimeLearningService.build_runtime_context(prompts=[], practices=[])
        self.assertTrue(context.is_empty)
        self.assertEqual(context.prompt_count, 0)
        self.assertEqual(context.practice_count, 0)

    def test_runtime_governance_excludes_diagnostic_entries_from_prompt(self):
        prompts = [
            SimpleNamespace(
                prompt_key="diag_only",
                prompt_type="behavior",
                content="仅用于诊断，不应该注入模型。",
                priority=1,
                tags=["diagnostic"],
            ),
            SimpleNamespace(
                prompt_key="enforced_tool_policy",
                prompt_type="tool_usage",
                content="天气查询只调用一次 search。",
                priority=5,
                tags=["runtime"],
            ),
        ]
        practices = [
            SimpleNamespace(
                practice_id="BP-DIAG",
                title="诊断观察",
                description="仅记录，不注入。",
                priority="medium",
                tags=["diagnostic"],
            ),
            SimpleNamespace(
                practice_id="BP-ENF",
                title="确定性结果直出",
                description="避免二次模型改写。",
                priority="high",
                tags=[],
            ),
        ]

        context = RuntimeLearningService.build_runtime_context(prompts=prompts, practices=practices)

        self.assertIn("enforced_tool_policy", context.system_prompt)
        self.assertIn("BP-ENF", context.system_prompt)
        self.assertNotIn("diag_only", context.system_prompt)
        self.assertNotIn("BP-DIAG", context.system_prompt)
        self.assertEqual(context.metadata["enforced_count"], 2)
        self.assertEqual(context.metadata["diagnostic_count"], 2)
        self.assertIn("prompt:diag_only", context.metadata["governance"][RuntimeKnowledgeLevel.DIAGNOSTIC.value])

    def test_runtime_governance_filters_scope_disabled_and_rollback(self):
        prompts = [
            SimpleNamespace(
                prompt_key="chat_only",
                prompt_type="workflow",
                content="仅用于聊天场景。",
                priority=5,
                tags=["scope:chat"],
                is_active=True,
            ),
            SimpleNamespace(
                prompt_key="search_only",
                prompt_type="workflow",
                content="仅用于搜索场景。",
                priority=5,
                tags=["scope:search"],
                is_active=True,
            ),
            SimpleNamespace(
                prompt_key="disabled_prompt",
                prompt_type="behavior",
                content="已禁用。",
                priority=1,
                tags=["disabled"],
                is_active=True,
            ),
        ]
        practices = [
            SimpleNamespace(
                practice_id="BP-ROLLBACK",
                title="已回滚规则",
                description="不应再注入。",
                priority="high",
                tags=[],
                trade_offs={"runtime": {"rollback": True, "rollback_reason": "regression"}},
            ),
            SimpleNamespace(
                practice_id="BP-CHAT",
                title="聊天规则",
                description="适用于 chat scope。",
                priority="high",
                tags=["scope:chat"],
                trade_offs={},
            ),
        ]

        context = RuntimeLearningService.build_runtime_context(
            prompts=prompts,
            practices=practices,
            scope="chat",
        )

        self.assertIn("chat_only", context.system_prompt)
        self.assertIn("BP-CHAT", context.system_prompt)
        self.assertNotIn("search_only", context.system_prompt)
        self.assertNotIn("disabled_prompt", context.system_prompt)
        self.assertNotIn("BP-ROLLBACK", context.system_prompt)
        skipped_reasons = {item["id"]: item["reason"] for item in context.metadata["skipped_items"]}
        self.assertEqual(skipped_reasons["search_only"], "scope_mismatch")
        self.assertEqual(skipped_reasons["disabled_prompt"], "disabled")
        self.assertEqual(skipped_reasons["BP-ROLLBACK"], "rollback")


if __name__ == "__main__":
    unittest.main()
