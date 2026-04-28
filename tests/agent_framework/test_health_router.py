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

    @patch("backend.routers.health.get_runtime_surface_service")
    def test_runtime_profile_endpoint_returns_runtime_surface(self, mock_factory):
        mock_factory.return_value.get_runtime_profile.return_value = {
            "agent_mode": "general_demo",
            "auth_mode": "demo_guest",
            "default_model": "doubao",
            "models": [{"name": "doubao", "display_name": "豆包"}],
            "providers": [{"provider_id": "volcengine-ark", "display_name": "火山引擎 Ark"}],
            "capability_contract": {"identity_summary": "主协调智能体"},
            "config_layers": {
                "defaults": {"auth_mode": "demo_guest", "default_model": "doubao"},
                "overrides": {},
                "effective": {"auth_mode": "demo_guest", "default_model": "doubao"},
                "override_path": ".myagent/runtime_surface.json",
                "editable_keys": ["auth_mode", "default_model"],
            },
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/runtime-profile")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["auth_mode"], "demo_guest")
        self.assertEqual(response.json()["capability_contract"]["identity_summary"], "主协调智能体")
        self.assertEqual(response.json()["config_layers"]["defaults"]["auth_mode"], "demo_guest")

    @patch("backend.routers.health.get_runtime_surface_service")
    def test_runtime_profile_patch_updates_surface(self, mock_factory):
        mock_factory.return_value.update_runtime_profile.return_value = {
            "agent_mode": "general_demo",
            "auth_mode": "business_auth",
            "default_model": "doubao",
            "models": [],
            "providers": [],
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.patch("/api/runtime-profile", json={"auth_mode": "business_auth"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["auth_mode"], "business_auth")

    @patch("backend.routers.health.get_capability_gap_service")
    def test_capability_gaps_endpoint_returns_summary(self, mock_factory):
        mock_factory.return_value.get_summary.return_value = {
            "total_gap_events": 3,
            "top_missing_parts": [{"name": "transport", "count": 2}],
            "suggested_investments": ["增加交通路线检索工具，或接入地图 / 出行类 MCP。"],
            "recent_examples": [],
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/capability-gaps")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_gap_events"], 3)
        mock_factory.return_value.get_summary.assert_called_once_with(
            limit=100,
            missing_part=None,
            keyword=None,
            profile=None,
            completion_stage=None,
            error_category=None,
        )

    @patch("backend.routers.health.get_capability_gap_service")
    def test_capability_gaps_endpoint_forwards_filters(self, mock_factory):
        mock_factory.return_value.get_summary.return_value = {
            "total_gap_events": 1,
            "top_missing_parts": [{"name": "transport", "count": 1}],
            "suggested_investments": [],
            "recent_examples": [],
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get(
            "/api/capability-gaps?limit=20&missing_part=transport&keyword=舟山&profile=travel_planning&completion_stage=boundary_fallback&error_category=provider_timeout"
        )
        self.assertEqual(response.status_code, 200)
        mock_factory.return_value.get_summary.assert_called_once_with(
            limit=20,
            missing_part="transport",
            keyword="舟山",
            profile="travel_planning",
            completion_stage="boundary_fallback",
            error_category="provider_timeout",
        )


if __name__ == "__main__":
    unittest.main()
