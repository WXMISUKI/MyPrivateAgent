import unittest

from fastapi.testclient import TestClient

from backend.agent_server.app import create_app
from backend.agent_server.config import AgentServerBootstrapConfig, AgentServerConfig, AgentServerUIConfig


class ProviderOnboardingRouterTests(unittest.TestCase):
    def setUp(self):
        app = create_app(
            AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False),
                route_names=("provider_onboarding",),
            )
        )
        self.client = TestClient(app)

    def test_list_provider_onboarding(self):
        response = self.client.get("/api/provider-onboarding")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["contract_version"], "provider-onboarding-catalog-v1")
        self.assertGreaterEqual(len(payload["entries"]), 5)

    def test_get_provider_onboarding_detail(self):
        response = self.client.get("/api/provider-onboarding/knowledge-rag-provider")

        self.assertEqual(response.status_code, 200)
        entry = response.json()["entry"]
        self.assertEqual(entry["provider_id"], "unifiedKnowledgeProvider")
        self.assertIn("knowledge.rag.retrieve", entry["capability_ids"])
        self.assertIn("smoke_commands", entry)

    def test_get_provider_onboarding_readiness(self):
        response = self.client.get("/api/provider-onboarding/knowledge-rag-provider/readiness")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["onboarding_id"], "knowledge-rag-provider")
        self.assertIn("checks", payload)
        self.assertEqual(
            payload["live_probe_hints"]["service_provider_detail"],
            "/api/service-providers/unifiedKnowledgeProvider",
        )

    def test_unknown_onboarding_id_returns_structured_404(self):
        response = self.client.get("/api/provider-onboarding/missing-provider")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "PROVIDER_ONBOARDING_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
