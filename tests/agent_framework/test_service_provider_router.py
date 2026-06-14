import unittest

from fastapi.testclient import TestClient

from backend.agent_server.app import create_app
from backend.agent_server.config import AgentServerBootstrapConfig, AgentServerConfig, AgentServerUIConfig


class ServiceProviderRouterTests(unittest.TestCase):
    def test_service_provider_list_route_is_registered(self):
        app = create_app(
            AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False),
                route_names=("service_providers",),
            )
        )
        client = TestClient(app)

        response = client.get("/api/service-providers")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["contract_version"], "provider-service-consumption-v1")
        self.assertIn("providers", payload)

    def test_service_provider_unknown_provider_returns_404(self):
        app = create_app(
            AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False),
                route_names=("service_providers",),
            )
        )
        client = TestClient(app)

        response = client.get("/api/service-providers/missing-provider")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "SERVICE_PROVIDER_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
