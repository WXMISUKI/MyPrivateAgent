import unittest

from backend.services.subagent_registry_service import get_subagent_registry_service


class SubagentRegistryServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = get_subagent_registry_service()

    def test_infer_roles_from_text(self):
        roles = self.service.infer_roles_from_text("请先做 research compare，再给 planning 方案")
        self.assertIn("researcher", roles)
        self.assertIn("planner", roles)

    def test_runtime_contract_contains_governance_fields(self):
        contract = self.service.build_runtime_contract()
        self.assertGreaterEqual(contract["total_profiles"], 3)
        first = contract["profiles"][0]
        self.assertIn("enabled", first)
        self.assertIn("max_turns", first)


if __name__ == "__main__":
    unittest.main()

