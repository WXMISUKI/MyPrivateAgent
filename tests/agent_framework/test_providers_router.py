import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.agent_server.app import create_app
from backend.agent_server.config import AgentServerBootstrapConfig, AgentServerConfig, AgentServerUIConfig


class ProvidersRouterTests(unittest.TestCase):
    @staticmethod
    def _extract_error_text(payload):
        detail = payload.get("detail")
        if isinstance(detail, str):
            return detail
        error = payload.get("error") or {}
        message = error.get("message")
        if isinstance(message, str):
            return message
        return str(payload)

    @patch("backend.routers.providers.get_provider_failover_analytics_service")
    def test_failover_analytics_endpoint_returns_summary(self, mock_factory):
        mock_factory.return_value.get_summary.return_value = {
            "window_days": 7,
            "total_children": 10,
            "switched_children": 2,
            "total_switches": 3,
            "switch_rate": 0.2,
            "avg_switches_per_switched_child": 1.5,
            "top_provider_failover_pairs": [{"name": "volcengine-ark->ollama", "count": 2}],
            "top_final_models": [{"name": "llama3.1", "count": 4}],
            "top_final_providers": [{"name": "ollama", "count": 6}],
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/failover-analytics?window_days=7&limit=300")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["window_days"], 7)
        self.assertEqual(response.json()["switch_rate"], 0.2)
        mock_factory.return_value.get_summary.assert_called_once_with(window_days=7, limit=300)

    def test_failover_analytics_endpoint_rejects_invalid_window(self):
        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/failover-analytics?window_days=5&limit=100")
        self.assertEqual(response.status_code, 400)
        self.assertIn("7/14/30", self._extract_error_text(response.json()))

    def test_failover_analytics_endpoint_rejects_invalid_limit(self):
        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/failover-analytics?window_days=7&limit=0")
        self.assertEqual(response.status_code, 400)
        self.assertIn("1-5000", self._extract_error_text(response.json()))


if __name__ == "__main__":
    unittest.main()
