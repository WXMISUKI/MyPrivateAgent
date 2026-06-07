import unittest
from pathlib import Path

from backend.services.domain_agent_registry_service import DomainAgentRegistryService


class CompanyProfileDomainAgentManifestTests(unittest.TestCase):
    def test_company_profile_manifest_declares_trial_source_and_grounding_policy(self):
        service = DomainAgentRegistryService(Path("backend/domain_agents"))

        contract = service.build_runtime_contract()
        agents = {agent["id"]: agent for agent in contract["agents"]}
        agent = agents["company_profile"]

        self.assertEqual(agent["status"], "ready")
        self.assertEqual(agent["capabilities"]["rag_sources"], ["company_profile_2025_trial"])
        self.assertEqual(agent["capabilities"]["graph_sources"], [])
        self.assertEqual(agent["grounding_policy"]["must_use_knowledge_for_domains"], ["company.profile"])
        self.assertTrue(agent["grounding_policy"]["require_citations"])
        self.assertFalse(agent["grounding_policy"]["allow_ungrounded"])
        self.assertEqual(agent["grounding_policy"]["source_acl_mode"], "agent_manifest")

    def test_company_profile_source_is_visible_in_rag_source_registry(self):
        service = DomainAgentRegistryService(Path("backend/domain_agents"))

        registry = service.build_rag_source_registry_contract()

        entries = {
            (entry["agent_id"], entry["source_id"])
            for entry in registry["entries"]
        }
        self.assertIn(("company_profile", "company_profile_2025_trial"), entries)


if __name__ == "__main__":
    unittest.main()
