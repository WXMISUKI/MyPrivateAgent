import unittest
from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.agent_server.app import create_app
from backend.agent_server.config import AgentServerBootstrapConfig, AgentServerConfig, AgentServerUIConfig


class _StubRunTraceService:
    trace_calls = []
    audit_calls = []

    def append_latest_active_item_trace(self, **kwargs):
        self.__class__.trace_calls.append(kwargs)
        return True

    def append_latest_active_item_audit(self, **kwargs):
        self.__class__.audit_calls.append(kwargs)
        return True

    def build_snapshot_ref(self, **kwargs):
        return {
            "snapshot_id": "DOCT-REF-321",
            "generated_at": "2026-05-02T00:00:00Z",
            **kwargs,
        }


class HealthRouterTests(unittest.TestCase):
    def setUp(self):
        _StubRunTraceService.trace_calls = []
        _StubRunTraceService.audit_calls = []

    @patch("backend.routers.health.get_runtime_surface_service")
    @patch("backend.routers.health.get_provider_failover_analytics_service")
    @patch("backend.routers.health.get_startup_diagnostics_service")
    def test_health_endpoint_returns_diagnostics_report(self, mock_factory, mock_failover_factory, mock_runtime_factory):
        mock_factory.return_value.collect_report.return_value = {
            "status": "ok",
            "summary": {"ok": 1, "warn": 0, "fail": 0},
            "checks": {},
        }
        mock_failover_factory.return_value.get_summary.return_value = {
            "switch_rate": 0.35,
            "total_children": 10,
            "switched_children": 3,
            "total_switches": 4,
        }
        mock_runtime_factory.return_value.get_runtime_profile.return_value = {
            "failover_thresholds": {"medium": 0.2, "high": 0.4}
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
        self.assertEqual(response.json()["failover"]["alert_level"], "medium")
        self.assertEqual(response.json()["failover"]["alert_thresholds"]["medium"], 0.2)

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

    @patch("backend.routers.health.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.health.get_doctor_runtime_service")
    def test_doctor_endpoint_returns_startup_report(self, mock_factory, _mock_trace_service):
        mock_factory.return_value.run_startup_report.return_value = {
            "scope": "startup",
            "status": "ok",
            "exit_code": 0,
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/doctor?conversation_id=321")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["scope"], "startup")
        self.assertIn("timeline_recording", response.json())
        mock_factory.return_value.run_startup_report.assert_called_once_with()
        self.assertEqual(len(_StubRunTraceService.trace_calls), 2)
        self.assertEqual(_StubRunTraceService.trace_calls[0]["event_type"], "doctor_run_started")
        self.assertEqual(_StubRunTraceService.trace_calls[1]["event_type"], "doctor_run_completed")
        self.assertEqual(len(_StubRunTraceService.audit_calls), 2)
        self.assertEqual(response.json()["timeline_recording"]["snapshot_ref"]["snapshot_id"], "DOCT-REF-321")
        self.assertEqual(_StubRunTraceService.trace_calls[0]["payload"]["snapshot_ref"]["snapshot_id"], "DOCT-REF-321")

    @patch("backend.routers.health.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.health.get_doctor_runtime_service")
    def test_doctor_endpoint_returns_governance_report(self, mock_factory, _mock_trace_service):
        mock_factory.return_value.run_capability_gap_report.return_value = {
            "scope": "capability_gap",
            "status": "warn",
            "gate_passed": False,
            "exit_code": 2,
            "non_closed_action_count": 12,
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/doctor?capability_gaps=true&window_days=14&limit=200&max_open_actions=10&max_long_blocked_actions=0&conversation_id=321")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["scope"], "capability_gap")
        mock_factory.return_value.run_capability_gap_report.assert_called_once_with(
            limit=200,
            window_days=14,
            max_open_actions=10,
            max_long_blocked_actions=0,
        )
        self.assertEqual(len(_StubRunTraceService.trace_calls), 3)
        self.assertEqual(_StubRunTraceService.trace_calls[-1]["event_type"], "doctor_gate_failed")
        self.assertEqual(len(_StubRunTraceService.audit_calls), 3)
        self.assertEqual(response.json()["timeline_recording"]["snapshot_ref"]["snapshot_id"], "DOCT-REF-321")

    @patch("backend.routers.health.get_capability_gap_service")
    @patch("backend.routers.health.get_remediation_status_service")
    def test_capability_gaps_endpoint_returns_summary(self, mock_status_factory, mock_factory):
        mock_status_factory.return_value.status_map.return_value = {
            "fix_final_synthesis_chain": {
                "status": "in_progress",
                "updated_at": "2026-04-29T00:00:00Z",
                "updated_by": "tester",
            }
        }
        mock_factory.return_value.get_summary.return_value = {
            "total_gap_events": 3,
            "top_missing_parts": [{"name": "transport", "count": 2}],
            "suggested_investments": ["增加交通路线检索工具，或接入地图 / 出行类 MCP。"],
            "recent_examples": [],
            "remediation_targets": [{"action_id": "fix_final_synthesis_chain", "owner": "agent-core"}],
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
        self.assertEqual(response.json()["remediation_targets"][0]["status"], "in_progress")
        self.assertIn("remediation_status_counts", response.json())
        self.assertIn("remediation_progress", response.json())
        mock_factory.return_value.get_summary.assert_called_once_with(
            limit=100,
            missing_part=None,
            keyword=None,
            profile=None,
            completion_stage=None,
            error_category=None,
            hook_event_type=None,
            subagent_role=None,
            provider=None,
            model_name=None,
            window_days=None,
        )

    @patch("backend.routers.health.get_capability_gap_service")
    @patch("backend.routers.health.get_remediation_status_service")
    def test_capability_gaps_endpoint_forwards_filters(self, _mock_status_factory, mock_factory):
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
            "/api/capability-gaps?limit=20&missing_part=transport&keyword=舟山&profile=travel_planning&completion_stage=boundary_fallback&error_category=provider_timeout&hook_event_type=pre_tool_use_blocked&subagent_role=frontend&provider=volcengine-ark&model_name=doubao&window_days=14"
        )
        self.assertEqual(response.status_code, 200)
        mock_factory.return_value.get_summary.assert_called_once_with(
            limit=20,
            missing_part="transport",
            keyword="舟山",
            profile="travel_planning",
            completion_stage="boundary_fallback",
            error_category="provider_timeout",
            hook_event_type="pre_tool_use_blocked",
            subagent_role="frontend",
            provider="volcengine-ark",
            model_name="doubao",
            window_days=14,
        )

    def test_liveness_returns_ok(self):
        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)
        response = client.get("/api/health/live")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_readiness_returns_ready(self):
        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)
        response = client.get("/api/health/ready")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ready")

    @patch("backend.routers.health.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.health.get_remediation_status_service")
    def test_remediation_status_endpoints(self, mock_service_factory, _mock_trace_service):
        mock_service = mock_service_factory.return_value
        mock_service.list_statuses.return_value = [
            {"action_id": "fix_final_synthesis_chain", "status": "in_progress"}
        ]
        mock_service.upsert_status.return_value = {
            "action_id": "fix_final_synthesis_chain",
            "status": "done",
            "owner": "agent-core",
            "module": "planning",
            "updated_by": "tester",
            "note": "verified in governance panel",
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        list_response = client.get("/api/remediation-status")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()["items"][0]["action_id"], "fix_final_synthesis_chain")

        patch_response = client.patch(
            "/api/remediation-status/fix_final_synthesis_chain",
            json={"status": "done", "updated_by": "tester", "conversation_id": 321},
        )
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.json()["status"], "done")
        self.assertIn("timeline_recording", patch_response.json())
        self.assertEqual(len(_StubRunTraceService.trace_calls), 1)
        self.assertEqual(_StubRunTraceService.trace_calls[0]["event_type"], "remediation_status_updated")
        self.assertEqual(_StubRunTraceService.trace_calls[0]["source"], "governance")
        self.assertEqual(len(_StubRunTraceService.audit_calls), 1)
        self.assertEqual(_StubRunTraceService.audit_calls[0]["event_type"], "remediation_status_updated")
        self.assertEqual(patch_response.json()["timeline_recording"]["snapshot_ref"]["snapshot_id"], "DOCT-REF-321")


if __name__ == "__main__":
    unittest.main()
