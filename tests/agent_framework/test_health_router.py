import unittest
from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.agent_server.app import create_app
from backend.agent_server.config import AgentServerBootstrapConfig, AgentServerConfig, AgentServerUIConfig


class HealthRouterTests(unittest.TestCase):
    @patch("backend.routers.health.get_startup_diagnostics_service")
    def test_health_endpoint_returns_diagnostics_report(self, mock_factory):
        mock_factory.return_value.collect_report.return_value = {
            "status": "ok",
            "summary": {"ok": 1, "warn": 0, "fail": 0},
            "checks": {},
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")


if __name__ == "__main__":
    unittest.main()
