import unittest
from types import SimpleNamespace

from backend.services.promptops_contract_service import PromptOpsContractService


class PromptOpsContractServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = PromptOpsContractService()

    def test_legacy_prompt_defaults_to_active_version_one(self):
        prompt = SimpleNamespace(
            prompt_key="refund_policy",
            prompt_type="behavior",
            content="Use the refund policy.",
            priority=3,
            is_active=True,
            area=None,
            tags=[],
        )

        contract = self.service.normalize_prompt(prompt)

        self.assertEqual(contract["prompt_key"], "refund_policy")
        self.assertEqual(contract["version"], "1")
        self.assertEqual(contract["status"], "active")
        self.assertEqual(contract["runtime_binding"]["injection_behavior"], "unchanged")

    def test_tags_preserve_governance_metadata(self):
        prompt = SimpleNamespace(
            prompt_key="refund_policy",
            prompt_type="workflow",
            content="Handle refund for {{order_id}}.",
            priority=5,
            is_active=True,
            area="commerce",
            tags=[
                "version:2",
                "status:review",
                "owner:agent-team",
                "grounding_policy:ecommerce",
                "eval_set:refund-eval",
                "approval:pending",
                "rollout:manual",
                "rollback_target:1",
                "freeform",
            ],
        )

        contract = self.service.normalize_prompt(prompt)

        self.assertEqual(contract["version"], "2")
        self.assertEqual(contract["status"], "review")
        self.assertEqual(contract["owner"], "agent-team")
        self.assertEqual(contract["grounding_policy_ref"], "ecommerce")
        self.assertEqual(contract["eval_set_ref"], "refund-eval")
        self.assertEqual(contract["approval_state"], "pending")
        self.assertEqual(contract["rollout_strategy"], "manual")
        self.assertEqual(contract["rollback_target"], "1")
        self.assertIn("freeform", contract["tags"])

    def test_template_variables_are_extracted_into_schema(self):
        prompt = SimpleNamespace(
            prompt_key="order_lookup",
            prompt_type="tool_usage",
            content="Find {{customer_id}} order {{order_id}} and reuse {{order_id}}.",
            priority=5,
            is_active=True,
            area=None,
            tags=[],
        )

        contract = self.service.normalize_prompt(prompt)

        self.assertEqual(contract["variables_schema"]["required"], ["customer_id", "order_id"])
        self.assertEqual(contract["variables_schema"]["properties"]["customer_id"]["type"], "string")
        self.assertEqual(contract["variables_schema"]["properties"]["order_id"]["type"], "string")

    def test_inactive_prompt_defaults_to_archived(self):
        prompt = SimpleNamespace(
            prompt_key="old_prompt",
            prompt_type="behavior",
            content="Old behavior.",
            priority=1,
            is_active=False,
            area=None,
            tags=[],
        )

        contract = self.service.normalize_prompt(prompt)

        self.assertEqual(contract["status"], "archived")
        self.assertFalse(contract["runtime_binding"]["is_active"])

    def test_registry_is_visibility_only(self):
        prompts = [
            SimpleNamespace(
                prompt_key="active_prompt",
                prompt_type="behavior",
                content="Active.",
                priority=1,
                is_active=True,
                area=None,
                tags=[],
            ),
            SimpleNamespace(
                prompt_key="inactive_prompt",
                prompt_type="behavior",
                content="Inactive.",
                priority=1,
                is_active=False,
                area=None,
                tags=[],
            ),
        ]

        registry = self.service.build_registry(prompts)

        self.assertEqual(registry["prompt_count"], 2)
        self.assertEqual(registry["active_prompt_count"], 1)
        self.assertEqual(registry["behavior_boundary"]["mode"], "visibility_only")
        self.assertFalse(registry["behavior_boundary"]["chat_prompt_injection_changed"])


if __name__ == "__main__":
    unittest.main()
