import unittest
import sys
import types
from fastapi.testclient import TestClient
from unittest.mock import patch

if "slowapi" not in sys.modules:
    slowapi_module = types.ModuleType("slowapi")
    slowapi_module.Limiter = lambda *args, **kwargs: object()
    slowapi_module._rate_limit_exceeded_handler = lambda *args, **kwargs: None
    sys.modules["slowapi"] = slowapi_module

    slowapi_util_module = types.ModuleType("slowapi.util")
    slowapi_util_module.get_remote_address = lambda request: "127.0.0.1"
    sys.modules["slowapi.util"] = slowapi_util_module

    slowapi_errors_module = types.ModuleType("slowapi.errors")
    slowapi_errors_module.RateLimitExceeded = type("RateLimitExceeded", (Exception,), {})
    sys.modules["slowapi.errors"] = slowapi_errors_module

from backend.agent_server.app import create_app
from backend.agent_server.config import AgentServerBootstrapConfig, AgentServerConfig, AgentServerUIConfig
from backend.routers import health as health_router


class _StubRunTraceService:
    trace_calls = []
    audit_calls = []
    existing_runtime_trace_fingerprints = set()
    existing_runtime_trace_dedupe_keys = set()

    def append_latest_active_item_trace(self, **kwargs):
        self.__class__.trace_calls.append(kwargs)
        payload = kwargs.get("payload") if isinstance(kwargs.get("payload"), dict) else {}
        if payload.get("dedupe_key"):
            self.__class__.existing_runtime_trace_dedupe_keys.add(payload["dedupe_key"])
        return True

    def append_runtime_trace(self, **kwargs):
        self.__class__.trace_calls.append(kwargs)
        payload = kwargs.get("payload") if isinstance(kwargs.get("payload"), dict) else {}
        if payload.get("dedupe_key"):
            self.__class__.existing_runtime_trace_dedupe_keys.add(payload["dedupe_key"])
        return True

    def has_runtime_trace_fingerprint(self, **kwargs):
        return (
            kwargs.get("fingerprint") in self.__class__.existing_runtime_trace_fingerprints
        )

    def has_runtime_trace_dedupe_key(self, **kwargs):
        return (
            kwargs.get("dedupe_key") in self.__class__.existing_runtime_trace_dedupe_keys
        )

    def append_latest_active_item_audit(self, **kwargs):
        self.__class__.audit_calls.append(kwargs)
        return True

    def build_snapshot_ref(self, **kwargs):
        return {
            "snapshot_id": "DOCT-REF-321",
            "generated_at": "2026-05-02T00:00:00Z",
            **kwargs,
        }


class _StubRuntimeSurfaceService:
    def __init__(self, profile):
        self.profile = profile

    def get_runtime_profile(self, **_kwargs):
        return dict(self.profile)

    def get_main_chat_query_detail(self, **_kwargs):
        return dict(self.profile.get("main_chat_query_detail") or {})

    def get_subagent_lane_recent_summary(self, **_kwargs):
        return dict(self.profile.get("subagent_lane_recent_summary") or {})

    def get_external_adapter_recent_summary(self, **_kwargs):
        return dict(self.profile.get("external_adapter_recent_summary") or {})

    def get_channel_promotion_gate(self, **_kwargs):
        return dict(self.profile.get("channel_promotion_gate") or {})

    def update_runtime_profile(self, _payload):
        return dict(self.profile)


class _CyclingRuntimeSurfaceService:
    def __init__(self, profiles):
        self.profiles = list(profiles)
        self.index = 0

    def get_runtime_profile(self, **_kwargs):
        profile = self.profiles[min(self.index, len(self.profiles) - 1)]
        self.index += 1
        return dict(profile)


class _StubSchedulerRuntimeDiagnosticsService:
    def collect_status(self, *, limit=50):
        return {
            "status": "ok",
            "requested_backend": "auto",
            "effective_backend": "metadata",
            "backend": "metadata_adapter",
            "backend_source": "metadata",
            "table_ready": False,
            "fallback_reason": "scheduler_runtime_tables_missing",
            "record_counts": {"scheduler_runs": 0, "child_runs": 0},
            "metadata_runtime_summary": {"scan_limit": limit, "runtime_item_count": 1, "items": []},
        }

    def reconcile_to_relational(self, *, plan_id=None, item_id=None, limit=100):
        return {
            "status": "ok",
            "table_ready": True,
            "requested_backend": "auto",
            "reconciled_items": 2,
            "skipped_items": 1,
            "items": [
                {"plan_id": plan_id or 1, "item_id": item_id or 11, "status": "reconciled", "child_count": 2}
            ],
            "limit": limit,
        }


class _StubFrameworkAdapterRuntimeService:
    calls = []

    def execute_adapter_run(self, **kwargs):
        self.__class__.calls.append(kwargs)
        return {
            "adapter_id": kwargs["adapter_id"],
            "run_id": kwargs["run_id"],
            "translated_input": {
                "adapter_id": kwargs["adapter_id"],
                "run_id": kwargs["run_id"],
                "message_count": len(kwargs["messages"]),
            },
            "events": [
                {"type": "status", "source": "framework_adapter"},
                {"type": "reasoning", "source": "framework_adapter"},
                {"type": "content", "source": "framework_adapter"},
            ],
            "final_output": "Local fake adapter processed: 生成巡检计划",
        }

    def execute_external_adapter_run(self, **kwargs):
        self.__class__.calls.append(kwargs)
        return {
            "adapter_id": kwargs["adapter_id"],
            "run_id": kwargs["run_id"],
            "translated_input": {
                "adapter_id": kwargs["adapter_id"],
                "run_id": kwargs["run_id"],
                "message_count": len(kwargs["messages"]),
            },
            "events": [
                {"type": "status", "source": "framework_adapter"},
                {"type": "content", "source": "framework_adapter"},
            ],
            "final_output": "LangGraph external pilot processed: test",
            "status": "ok",
            "snapshot_ref": {
                "snapshot_id": "FRAM-EXT-321-20260513000000",
                "generated_at": "2026-05-13T00:00:00Z",
            },
        }

    def precheck_adapter(
        self,
        *,
        adapter_id,
        db=None,
        user_id=None,
        conversation_id=None,
        execution_context=None,
    ):
        return {
            "adapter_id": adapter_id,
            "framework_name": "LangGraph" if adapter_id == "langgraph_draft" else "LocalFakeFramework",
            "ready": False,
            "status": "not_configured",
            "configuration_status": "missing_package",
            "execution_mode": "draft_external_runtime",
            "package_installed": False,
            "runtime_enabled": False,
            "required_packages": ["langgraph"],
            "missing_packages": ["langgraph"],
            "required_env": ["LANGGRAPH_RUNTIME_ENDPOINT", "LANGGRAPH_ASSISTANT_ID"],
            "missing_env": ["LANGGRAPH_RUNTIME_ENDPOINT", "LANGGRAPH_ASSISTANT_ID"],
            "execution_block_reason": "missing required package: langgraph",
            "detail": "LangGraph draft adapter is blocked: missing required package: langgraph",
            "timeline_recording": {
                "conversation_id": conversation_id or 321,
                "snapshot_ref": {
                    "snapshot_id": "FRAM-PRECHECK-321",
                    "generated_at": "2026-05-12T00:00:00Z",
                    "conversation_id": conversation_id or 321,
                    "source": "framework_adapter",
                    "event_type": "framework_adapter_precheck_completed",
                },
            },
        }


class HealthRouterTests(unittest.TestCase):
    def setUp(self):
        health_router._RUNTIME_CONTRACT_GATE_TRACE_FINGERPRINTS.clear()
        _StubRunTraceService.trace_calls = []
        _StubRunTraceService.audit_calls = []
        _StubRunTraceService.existing_runtime_trace_fingerprints = set()
        _StubRunTraceService.existing_runtime_trace_dedupe_keys = set()
        _StubFrameworkAdapterRuntimeService.calls = []

    @patch("backend.services.scheduler_service.SchedulerService")
    def test_collect_framework_adapter_external_error_counts_declares_window_scope(self, mock_scheduler_cls):
        from backend.routers.health import _collect_framework_adapter_external_error_counts

        class _Query:
            def order_by(self, *_args):
                return self

            def limit(self, value):
                self.limit_value = value
                return self

            def all(self):
                return ["item-1", "item-2"]

        class _Db:
            def query(self, *_args):
                return _Query()

        scheduler = mock_scheduler_cls.return_value
        scheduler.filter_run_trace.side_effect = [
            [{"payload": {"error_type": "protocol_error"}}],
            [{"payload": {"error_type": "connectivity_error"}}, {"payload": {"error_type": "protocol_error"}}],
        ]

        counts = _collect_framework_adapter_external_error_counts(db=_Db(), limit=7)

        self.assertEqual(counts["total"], 3)
        self.assertEqual(counts["window_scope"], "recent_plan_items")
        self.assertEqual(counts["sample_size"], 7)
        self.assertEqual(counts["by_error_type"]["protocol_error"], 2)

    @patch("backend.routers.health._collect_framework_adapter_external_error_counts")
    @patch("backend.routers.health._collect_latest_framework_adapter_external_error_summary")
    @patch("backend.routers.health.get_scheduler_runtime_diagnostics_service", return_value=_StubSchedulerRuntimeDiagnosticsService())
    @patch("backend.routers.health.get_runtime_surface_service")
    @patch("backend.routers.health.get_provider_failover_analytics_service")
    @patch("backend.routers.health.get_startup_diagnostics_service")
    def test_health_endpoint_returns_diagnostics_report(
        self,
        mock_factory,
        mock_failover_factory,
        mock_runtime_factory,
        _mock_runtime_backend_factory,
        mock_external_error_summary,
        mock_external_error_counts,
    ):
        mock_factory.return_value.collect_report.return_value = {
            "status": "ok",
            "summary": {"ok": 1, "warn": 0, "fail": 0},
            "checks": {
                "framework_adapters": {
                    "status": "warn",
                    "details": ["langgraph_draft: status=not_configured | config=missing_package"],
                    "remediation_actions": [],
                }
            },
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
        mock_external_error_summary.return_value = {
            "event_type": "framework_adapter_external_error",
            "error_type": "protocol_error",
            "adapter_id": "langgraph_draft",
            "framework_name": "LangGraph",
            "detail": "transport probe did not provide assistant identity evidence",
            "snapshot_ref": {"snapshot_id": "FRAM-EXT-ERR-321-20260513010000"},
        }
        mock_external_error_counts.return_value = {
            "total": 3,
            "window_scope": "recent_plan_items",
            "sample_size": 50,
            "by_error_type": {
                "protocol_error": 2,
                "connectivity_error": 1,
            },
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
        self.assertEqual(response.json()["runtime_backend"]["effective_backend"], "metadata")
        self.assertEqual(
            response.json()["checks"]["framework_adapters"]["latest_external_pilot_failure"]["error_type"],
            "protocol_error",
        )
        self.assertEqual(
            response.json()["checks"]["framework_adapters"]["latest_external_pilot_failure"]["framework_name"],
            "LangGraph",
        )
        self.assertEqual(
            response.json()["checks"]["framework_adapters"]["external_pilot_failure_counts"]["total"],
            3,
        )
        self.assertEqual(
            response.json()["checks"]["framework_adapters"]["external_pilot_failure_counts"]["by_error_type"]["protocol_error"],
            2,
        )
        self.assertEqual(
            response.json()["checks"]["framework_adapters"]["external_pilot_failure_counts"]["window_scope"],
            "recent_plan_items",
        )
        self.assertEqual(
            response.json()["checks"]["framework_adapters"]["external_pilot_failure_counts"]["sample_size"],
            50,
        )

    @patch("backend.routers.health.get_runtime_surface_service")
    def test_runtime_profile_endpoint_returns_runtime_surface(self, mock_factory):
        mock_factory.return_value.get_runtime_profile.return_value = {
            "agent_mode": "general_demo",
            "auth_mode": "demo_guest",
            "default_model": "doubao",
            "default_runtime_recovery": {
                "contract_version": "phase-ii-default-runtime-recovery-v1",
                "recovery_mode": "registry_backed",
                "recovery_posture": "cross_process_candidate",
                "requires_durable_workspace": True,
                "requires_registry_bindings": True,
                "expected_cross_process_candidate": True,
                "cross_process_block_reason": "",
                "workspace_backend_kind": "sqlalchemy",
                "workspace_backend_mode": "strict_sql",
                "recovery_entrypoints": [
                    {
                        "method": "submit_approval",
                        "mode": "approved",
                        "available": True,
                        "recovery_reason": "ready_via_registry",
                        "blocked_reason": "",
                    }
                ],
            },
            "governance_overview": {
                "default_runtime_recovery": {
                    "recovery_mode": "registry_backed",
                    "recovery_entrypoints": [
                        {
                            "method": "submit_approval",
                            "mode": "approved",
                            "available": True,
                        }
                    ],
                },
                "recovery_alignment_summary": {
                    "current_alignment_status": "aligned",
                    "entries": [
                        {
                            "method": "submit_approval",
                            "mode": "approved",
                            "current_alignment": "state_gated",
                        }
                    ],
                },
            },
            "models": [{"name": "doubao", "display_name": "豆包"}],
            "providers": [{"provider_id": "volcengine-ark", "display_name": "火山引擎 Ark"}],
            "capability_contract": {"identity_summary": "主协调智能体"},
            "embedded_runtime_factory": {
                "contract_version": "phase-ii-embedded-runtime-factory-v1",
                "runtime_backend": "EmbeddedAgentRuntimeSDK",
                "shared_default_runtime": True,
                "default_recovery_capabilities": {
                    "recovery_mode": "registry_backed",
                    "requires_durable_workspace": True,
                    "requires_registry_bindings": True,
                },
                "default_runtime_profile": {
                    "db_mode": "sqlite",
                    "embedded_workspace_store_mode": "strict_sql",
                    "default_runtime_mode": "durable_default",
                    "recovery_posture": "cross_process_candidate",
                },
            },
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
        self.assertEqual(response.json()["default_runtime_recovery"]["recovery_mode"], "registry_backed")
        self.assertEqual(response.json()["default_runtime_recovery"]["recovery_entrypoints"][0]["method"], "submit_approval")
        self.assertEqual(response.json()["governance_overview"]["recovery_alignment_summary"]["current_alignment_status"], "aligned")
        self.assertEqual(response.json()["embedded_runtime_factory"]["default_runtime_profile"]["default_runtime_mode"], "durable_default")
        self.assertEqual(
            response.json()["embedded_runtime_factory"]["default_recovery_capabilities"]["recovery_mode"],
            "registry_backed",
        )
        self.assertEqual(response.json()["config_layers"]["defaults"]["auth_mode"], "demo_guest")

    @patch("backend.routers.health.get_runtime_surface_service")
    def test_main_chat_query_detail_endpoint_returns_dedicated_read_model(self, mock_factory):
        mock_factory.return_value.get_main_chat_query_detail.return_value = {
            "contract_version": "phase-g-main-chat-query-detail-v1",
            "query_id": "manual-chat-7",
            "recording_state": "recorded",
            "latest_stage": "final_output",
            "latest_summary": "Main chat final output",
            "dedupe_key_count": 2,
            "stage_count": 2,
            "warning_count": 0,
            "event_count": 2,
            "recent_event_count": 2,
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/runtime-profile/main-chat-query-detail?conversation_id=321&query_id=manual-chat-7")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["query_id"], "manual-chat-7")
        self.assertEqual(response.json()["latest_stage"], "final_output")
        self.assertEqual(response.json()["dedupe_key_count"], 2)
        self.assertEqual(response.json()["recent_event_count"], 2)
        mock_factory.return_value.get_main_chat_query_detail.assert_called_once_with(
            db=unittest.mock.ANY,
            conversation_id=321,
            plan_id=None,
            item_id=None,
            query_id="manual-chat-7",
        )

    @patch("backend.routers.health.get_runtime_surface_service")
    def test_main_chat_query_history_endpoint_returns_paginated_read_model(self, mock_factory):
        mock_factory.return_value.get_main_chat_query_history.return_value = {
            "contract_version": "phase-h-main-chat-query-history-v1",
            "recording_state": "recorded",
            "items": [
                {
                    "query_id": "manual-chat-9",
                    "latest_stage": "final_output",
                    "latest_summary": "Main chat final output 9",
                    "latest_timestamp": "2026-05-17T10:00:00Z",
                }
            ],
            "page": 1,
            "page_size": 20,
            "total_items": 3,
            "has_more": False,
            "next_cursor": "",
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/runtime-profile/main-chat-query-history?conversation_id=321&page=1&page_size=20")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["recording_state"], "recorded")
        self.assertEqual(response.json()["items"][0]["query_id"], "manual-chat-9")
        mock_factory.return_value.get_main_chat_query_history.assert_called_once_with(
            db=unittest.mock.ANY,
            conversation_id=321,
            plan_id=None,
            item_id=None,
            page=1,
            page_size=20,
        )

    @patch("backend.routers.health.get_runtime_surface_service")
    def test_subagent_lane_recent_summary_endpoint_returns_trial_read_model(self, mock_factory):
        mock_factory.return_value.get_subagent_lane_recent_summary.return_value = {
            "contract_version": "phase-h-subagent-lane-recent-summary-v1",
            "recording_state": "recorded",
            "items": [
                {
                    "query_id": "frontend-child-p10-i23-c1",
                    "latest_stage": "final_output",
                    "latest_summary": "已合并 frontend 子智能体结果到主响应",
                    "latest_timestamp": "2026-05-17T10:00:00Z",
                }
            ],
            "latest_query_id": "frontend-child-p10-i23-c1",
            "latest_stage": "final_output",
            "latest_summary": "已合并 frontend 子智能体结果到主响应",
            "latest_timestamp": "2026-05-17T10:00:00Z",
            "total_items": 1,
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/runtime-profile/subagent-lane-recent-summary?conversation_id=321")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["recording_state"], "recorded")
        self.assertEqual(response.json()["items"][0]["query_id"], "frontend-child-p10-i23-c1")
        mock_factory.return_value.get_subagent_lane_recent_summary.assert_called_once_with(
            db=unittest.mock.ANY,
            conversation_id=321,
            plan_id=None,
            item_id=None,
        )

    @patch("backend.routers.health.get_runtime_surface_service")
    def test_subagent_lane_query_detail_readiness_endpoint_returns_dedicated_contract(self, mock_factory):
        mock_factory.return_value.get_subagent_lane_query_detail_readiness.return_value = {
            "contract_version": "phase-h-subagent-lane-query-detail-readiness-v1",
            "channel": "subagent_lane",
            "readiness_status": "ready",
            "recent_summary_status": "recorded",
            "ready_for_detail": True,
            "required_capabilities": {
                "stable_query_id": True,
                "stage_chain_candidate": True,
                "recent_summary_recorded": True,
                "separates_child_run_events": True,
            },
            "blocking_reasons": [],
            "recommended_next_change": "subagent-lane-query-detail-contract",
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/runtime-profile/subagent-lane-query-detail-readiness?conversation_id=321")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["readiness_status"], "ready")
        self.assertTrue(response.json()["ready_for_detail"])
        self.assertNotIn("recent_events", response.json())
        self.assertNotIn("history_items", response.json())
        mock_factory.return_value.get_subagent_lane_query_detail_readiness.assert_called_once_with(
            db=unittest.mock.ANY,
            conversation_id=321,
            plan_id=None,
            item_id=None,
        )

    @patch("backend.routers.health.get_runtime_surface_service")
    def test_external_adapter_recent_summary_endpoint_returns_trial_read_model(self, mock_factory):
        mock_factory.return_value.get_external_adapter_recent_summary.return_value = {
            "contract_version": "phase-i-external-adapter-recent-summary-v1",
            "recording_state": "recorded",
            "items": [
                {
                    "query_id": "external-run-1",
                    "latest_stage": "final_output",
                    "latest_summary": "External adapter returned output",
                    "latest_timestamp": "2026-05-18T10:01:00Z",
                    "recording_state": "recorded",
                }
            ],
            "latest_query_id": "external-run-1",
            "latest_stage": "final_output",
            "latest_summary": "External adapter returned output",
            "latest_timestamp": "2026-05-18T10:01:00Z",
            "total_items": 1,
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/runtime-profile/external-adapter-recent-summary?conversation_id=321")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["recording_state"], "recorded")
        self.assertEqual(response.json()["items"][0]["query_id"], "external-run-1")
        mock_factory.return_value.get_external_adapter_recent_summary.assert_called_once_with(
            db=unittest.mock.ANY,
            conversation_id=321,
            plan_id=None,
            item_id=None,
        )

    @patch("backend.routers.health.get_runtime_surface_service")
    def test_channel_promotion_gate_endpoint_returns_canonical_gate_contract(self, mock_factory):
        mock_factory.return_value.get_channel_promotion_gate.return_value = {
            "contract_version": "phase-h-channel-promotion-gate-v1",
            "overall_status": "guarded",
            "layer_order": ["readiness", "recent_summary", "query_detail", "query_history", "query_workspace"],
            "channels_by_id": {
                "main_chat": {"channel": "main_chat", "current_layer": "query_workspace"},
                "subagent_lane": {"channel": "subagent_lane", "current_layer": "recent_summary"},
                "external_adapter": {"channel": "external_adapter", "blocked_layers": ["query_detail"]},
            },
            "over_promotion_guard": {
                "blocked_channels": ["subagent_lane", "external_adapter"],
                "blocked_layers": {"query_detail": ["external_adapter"]},
                "reason": "promotion_must_follow_readiness_then_summary_then_detail_then_history_then_workspace",
            },
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/runtime-profile/channel-promotion-gate?conversation_id=321")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["contract_version"], "phase-h-channel-promotion-gate-v1")
        self.assertEqual(response.json()["overall_status"], "guarded")
        self.assertEqual(response.json()["channels_by_id"]["main_chat"]["current_layer"], "query_workspace")
        mock_factory.return_value.get_channel_promotion_gate.assert_called_once_with(
            db=unittest.mock.ANY,
            conversation_id=321,
            plan_id=None,
            item_id=None,
        )

    @patch("backend.routers.health.get_runtime_surface_service")
    def test_subagent_lane_query_detail_endpoint_returns_dedicated_contract(self, mock_factory):
        mock_factory.return_value.get_subagent_lane_query_detail.return_value = {
            "contract_version": "phase-h-subagent-lane-query-detail-v1",
            "channel": "subagent_lane",
            "query_id": "frontend-child-p10-i23-c1",
            "recording_state": "recorded",
            "stage_chain": ["planning", "final_output"],
            "recent_events": [
                {"stage": "planning", "summary": "spawned"},
                {"stage": "final_output", "summary": "merged"},
            ],
            "recent_event_count": 2,
            "latest_stage": "final_output",
            "latest_summary": "merged",
            "stage_count": 2,
            "warning_count": 0,
            "event_count": 2,
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get(
            "/api/runtime-profile/subagent-lane-query-detail"
            "?conversation_id=321&query_id=frontend-child-p10-i23-c1"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["contract_version"], "phase-h-subagent-lane-query-detail-v1")
        self.assertEqual(response.json()["channel"], "subagent_lane")
        self.assertEqual(response.json()["latest_stage"], "final_output")
        self.assertEqual(response.json()["recent_event_count"], 2)
        self.assertNotIn("history_items", response.json())
        self.assertNotIn("next_cursor", response.json())
        mock_factory.return_value.get_subagent_lane_query_detail.assert_called_once_with(
            db=unittest.mock.ANY,
            conversation_id=321,
            plan_id=None,
            item_id=None,
            query_id="frontend-child-p10-i23-c1",
        )

    @patch("backend.routers.health.get_runtime_surface_service")
    def test_child_executor_output_replay_endpoint_returns_dedicated_read_model(self, mock_factory):
        mock_factory.return_value.get_child_executor_output_replay.return_value = {
            "contract_version": "phase-ii-child-executor-replay-v1",
            "parent_run_id": "run-parent-1",
            "record_count": 1,
            "records": [
                {
                    "binding_id": "binding:embedded_sdk_worker_candidate:run-parent-1",
                    "execution_status": "executed",
                    "merge_status": "merged",
                }
            ],
            "latest_merged_summary": "risk_reviewer 已通过 embedded_sdk_worker_skeleton 执行最小路径",
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/runtime-profile/child-executor-output-replay?parent_run_id=run-parent-1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["record_count"], 1)
        self.assertEqual(response.json()["records"][0]["execution_status"], "executed")
        mock_factory.return_value.get_child_executor_output_replay.assert_called_once_with(
            parent_run_id="run-parent-1",
        )

    @patch("backend.routers.health.get_runtime_surface_service")
    def test_child_executor_output_summary_endpoint_returns_compact_summary(self, mock_factory):
        mock_factory.return_value.get_child_executor_output_summary.return_value = {
            "contract_version": "phase-ii-child-executor-artifact-summary-v1",
            "parent_run_id": "run-parent-1",
            "record_count": 1,
            "latest_artifact_id": "child-output:binding:embedded_sdk_worker_candidate:run-parent-1",
            "latest_merge_strategy": "append_summary",
            "latest_merged_summary": "risk_reviewer 已通过 embedded_sdk_worker_skeleton 执行最小路径",
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/runtime-profile/child-executor-output-summary?parent_run_id=run-parent-1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["record_count"], 1)
        self.assertEqual(response.json()["latest_merge_strategy"], "append_summary")
        mock_factory.return_value.get_child_executor_output_summary.assert_called_once_with(
            parent_run_id="run-parent-1",
        )

    @patch("backend.routers.health.get_runtime_surface_service")
    def test_child_executor_merged_semantics_endpoint_returns_dedicated_read_model(self, mock_factory):
        mock_factory.return_value.get_child_executor_merged_semantics.return_value = {
            "contract_version": "phase-ii-child-executor-merged-semantics-v2",
            "parent_run_id": "run-parent-1",
            "record_count": 1,
            "available": True,
            "intent_catalog_version": "phase-ii-child-intent-catalog-v1",
            "supported_intents": ["risk_review", "planning", "general_analysis"],
            "intent_label": "risk_review",
            "merge_behavior": {
                "entities": "append_dedup",
                "focus_points": "append_dedup",
                "action_items": "append_dedup",
            },
            "merged_sections": {
                "merged_entities": {"section_id": "merged_entities", "title": "Merged Entities", "merge_mode": "append_dedup", "items": ["交易", "风险"]},
                "merged_focus": {"section_id": "merged_focus", "title": "Merged Focus", "merge_mode": "append_dedup", "items": ["复核异常"]},
                "merged_actions": {"section_id": "merged_actions", "title": "Merged Actions", "merge_mode": "append_dedup", "items": ["人工复核"]},
                "latest_conclusion": {"section_id": "latest_conclusion", "title": "Latest Conclusion", "merge_mode": "replace_latest", "text": "建议人工复核"},
            },
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/runtime-profile/child-executor-merged-semantics?parent_run_id=run-parent-1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["intent_label"], "risk_review")
        self.assertEqual(response.json()["intent_catalog_version"], "phase-ii-child-intent-catalog-v1")
        self.assertEqual(response.json()["merge_behavior"]["entities"], "append_dedup")
        self.assertEqual(response.json()["merged_sections"]["merged_entities"]["section_id"], "merged_entities")
        mock_factory.return_value.get_child_executor_merged_semantics.assert_called_once_with(
            parent_run_id="run-parent-1",
        )

    @patch("backend.routers.health.get_runtime_surface_service")
    def test_run_recovery_endpoint_returns_dedicated_read_model(self, mock_factory):
        mock_factory.return_value.get_run_recovery.return_value = {
            "contract_version": "phase-ii-run-recovery-v1",
            "available": True,
            "run_id": "run-parent-1",
            "run_state": "observing",
            "recoverable": True,
            "tool_continuation": {
                "recovery_reason": "ready_via_registry",
                "workspace_backend": {"backend_kind": "sqlalchemy", "durable": True},
            },
            "loop_continuation": {
                "recovery_reason": "ready_via_registry",
                "workspace_backend": {"backend_kind": "sqlalchemy", "durable": True},
            },
            "recovery_capabilities": {
                "recovery_mode": "registry_backed",
                "requires_durable_workspace": True,
                "requires_registry_bindings": True,
            },
            "recovery_entrypoints": [
                {
                    "method": "submit_approval",
                    "mode": "approved",
                    "available": True,
                    "recovery_reason": "ready_via_registry",
                    "blocked_reason": "",
                }
            ],
            "workspace_backend": {"backend_kind": "sqlalchemy", "durable": True},
            "reason": "",
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/runtime-profile/run-recovery?run_id=run-parent-1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["contract_version"], "phase-ii-run-recovery-v1")
        self.assertTrue(response.json()["recoverable"])
        self.assertEqual(response.json()["tool_continuation"]["recovery_reason"], "ready_via_registry")
        self.assertEqual(response.json()["recovery_capabilities"]["recovery_mode"], "registry_backed")
        self.assertEqual(response.json()["recovery_entrypoints"][0]["method"], "submit_approval")
        self.assertTrue(response.json()["recovery_entrypoints"][0]["available"])
        mock_factory.return_value.get_run_recovery.assert_called_once_with(
            run_id="run-parent-1",
        )

    @patch("backend.routers.health.get_runtime_surface_service")
    def test_embedded_runtime_bootstrap_endpoint_returns_dedicated_contract(self, mock_factory):
        mock_factory.return_value.get_embedded_runtime_bootstrap.return_value = {
            "contract_version": "phase-ii-embedded-runtime-factory-v1",
            "runtime_backend": "EmbeddedAgentRuntimeSDK",
            "shared_default_runtime": True,
            "default_recovery_capabilities": {
                "recovery_mode": "registry_backed",
                "requires_durable_workspace": True,
                "requires_registry_bindings": True,
            },
            "default_runtime_profile": {
                "db_mode": "sqlite",
                "embedded_workspace_store_mode": "strict_sql",
                "default_runtime_mode": "durable_default",
                "recovery_posture": "cross_process_candidate",
                "recommended_bootstrap": "EmbeddedRuntimeFactory",
            },
            "bootstrap_recovery_validation": {
                "contract_version": "phase-ii-embedded-runtime-bootstrap-validation-v1",
                "validation_status": "passed",
                "recovery_capabilities": {
                    "recovery_mode": "registry_backed",
                    "requires_durable_workspace": True,
                    "requires_registry_bindings": True,
                },
                "recovery_entrypoints": [
                    {
                        "method": "submit_approval",
                        "mode": "approved",
                        "available": True,
                        "recovery_reason": "ready_via_registry",
                        "blocked_reason": "",
                    }
                ],
            },
            "recovery_alignment_summary": {
                "actual_alignment_status": "aligned",
                "entries": [
                    {
                        "method": "submit_approval",
                        "mode": "approved",
                        "actual_alignment": "aligned",
                    }
                ],
            },
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/runtime-profile/embedded-runtime-bootstrap")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["contract_version"], "phase-ii-embedded-runtime-factory-v1")
        self.assertEqual(response.json()["default_runtime_profile"]["recommended_bootstrap"], "EmbeddedRuntimeFactory")
        self.assertEqual(response.json()["default_recovery_capabilities"]["recovery_mode"], "registry_backed")
        self.assertEqual(response.json()["bootstrap_recovery_validation"]["validation_status"], "passed")
        self.assertEqual(
            response.json()["bootstrap_recovery_validation"]["recovery_capabilities"]["recovery_mode"],
            "registry_backed",
        )
        self.assertTrue(response.json()["bootstrap_recovery_validation"]["recovery_entrypoints"][0]["available"])
        self.assertEqual(response.json()["recovery_alignment_summary"]["actual_alignment_status"], "aligned")
        mock_factory.return_value.get_embedded_runtime_bootstrap.assert_called_once_with()

    @patch("backend.routers.health.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.health.get_runtime_surface_service")
    def test_embedded_runtime_bootstrap_patch_updates_dedicated_contract(self, mock_factory, _mock_trace):
        _StubRunTraceService.trace_calls.clear()
        _StubRunTraceService.audit_calls.clear()
        mock_factory.return_value.update_embedded_runtime_bootstrap.return_value = {
            "contract_version": "phase-ii-embedded-runtime-factory-v1",
            "runtime_backend": "EmbeddedAgentRuntimeSDK",
            "shared_default_runtime": True,
            "default_runtime_profile": {
                "db_mode": "sqlite",
                "embedded_workspace_store_mode": "memory_only",
                "default_runtime_mode": "memory_preview",
                "recovery_posture": "in_process_only",
                "recommended_bootstrap": "EmbeddedRuntimeFactory",
            },
            "update_status": "applied",
            "applied_changes": ["embedded_workspace_store_mode"],
            "hot_reload_applied": True,
            "restart_required": False,
            "restart_required_changes": [],
            "post_update_verification": {
                "effective_change": True,
                "previous_runtime_mode": "durable_default",
                "current_runtime_mode": "memory_preview",
                "previous_recovery_posture": "cross_process_candidate",
                "current_recovery_posture": "in_process_only",
                "current_workspace_backend_kind": "in_memory",
                "current_workspace_backend_mode": "memory_only",
                "runtime_mode_changed": True,
                "recovery_posture_changed": True,
                "workspace_backend_changed": True,
                "durable_capability_changed": True,
                "previous_cross_process_candidate": True,
                "current_cross_process_candidate": False,
                "cross_process_candidate_changed": True,
                "previous_cross_process_block_reason": "",
                "current_cross_process_block_reason": "workspace_backend_not_durable",
                "applied_workspace_store_mode": "memory_only",
                "workspace_mode_applied": True,
                "recovery_contract_aligned": True,
                "previous_default_recovery_expectation": {
                    "cross_process_candidate": True,
                },
                "current_default_recovery_expectation": {
                    "cross_process_candidate": False,
                },
            },
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.patch(
            "/api/runtime-profile/embedded-runtime-bootstrap",
            json={
                "embedded_workspace_store_mode": "memory_only",
                "conversation_id": 321,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["default_runtime_profile"]["embedded_workspace_store_mode"], "memory_only")
        self.assertEqual(response.json()["update_status"], "applied")
        self.assertTrue(response.json()["hot_reload_applied"])
        self.assertFalse(response.json()["restart_required"])
        self.assertTrue(response.json()["post_update_verification"]["effective_change"])
        self.assertEqual(response.json()["post_update_verification"]["current_runtime_mode"], "memory_preview")
        self.assertTrue(response.json()["post_update_verification"]["runtime_mode_changed"])
        self.assertTrue(response.json()["post_update_verification"]["recovery_posture_changed"])
        self.assertTrue(response.json()["post_update_verification"]["cross_process_candidate_changed"])
        self.assertEqual(response.json()["post_update_verification"]["applied_workspace_store_mode"], "memory_only")
        self.assertTrue(response.json()["post_update_verification"]["workspace_mode_applied"])
        self.assertTrue(response.json()["post_update_verification"]["recovery_contract_aligned"])
        self.assertEqual(response.json()["post_update_verification"]["current_cross_process_block_reason"], "workspace_backend_not_durable")
        self.assertFalse(
            response.json()["post_update_verification"]["current_default_recovery_expectation"]["cross_process_candidate"]
        )
        self.assertTrue(response.json()["timeline_recording"]["trace_written"])
        self.assertTrue(response.json()["timeline_recording"]["audit_written"])
        self.assertEqual(response.json()["timeline_recording"]["conversation_id"], 321)
        self.assertEqual(len(_StubRunTraceService.trace_calls), 1)
        self.assertEqual(len(_StubRunTraceService.audit_calls), 1)
        self.assertEqual(_StubRunTraceService.trace_calls[0]["source"], "runtime_control")
        self.assertEqual(_StubRunTraceService.trace_calls[0]["event_type"], "embedded_runtime_bootstrap_updated")
        self.assertEqual(
            _StubRunTraceService.trace_calls[0]["payload"]["requested_embedded_workspace_store_mode"],
            "memory_only",
        )
        self.assertEqual(
            _StubRunTraceService.trace_calls[0]["payload"]["current_runtime_mode"],
            "memory_preview",
        )
        self.assertEqual(
            _StubRunTraceService.audit_calls[0]["event_type"],
            "embedded_runtime_bootstrap_updated",
        )
        mock_factory.return_value.update_embedded_runtime_bootstrap.assert_called_once_with(
            {"embedded_workspace_store_mode": "memory_only"}
        )

    @patch("backend.routers.health.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.health.get_runtime_surface_service")
    def test_embedded_runtime_bootstrap_patch_skips_timeline_when_conversation_scope_missing(self, mock_factory, _mock_trace):
        _StubRunTraceService.trace_calls.clear()
        _StubRunTraceService.audit_calls.clear()
        mock_factory.return_value.update_embedded_runtime_bootstrap.return_value = {
            "contract_version": "phase-ii-embedded-runtime-factory-v1",
            "default_runtime_profile": {
                "embedded_workspace_store_mode": "memory_only",
            },
            "update_status": "applied",
            "applied_changes": ["embedded_workspace_store_mode"],
            "post_update_verification": {
                "current_runtime_mode": "memory_preview",
                "current_recovery_posture": "in_process_only",
            },
        }

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.patch(
            "/api/runtime-profile/embedded-runtime-bootstrap",
            json={"embedded_workspace_store_mode": "memory_only"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("timeline_recording", response.json())
        self.assertEqual(_StubRunTraceService.trace_calls, [])
        self.assertEqual(_StubRunTraceService.audit_calls, [])

    @patch("backend.routers.health.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.health.get_runtime_surface_service")
    def test_runtime_profile_records_contract_gate_degraded_trace_when_context_is_provided(self, mock_factory, _mock_trace):
        _StubRunTraceService.trace_calls.clear()
        mock_factory.return_value = _StubRuntimeSurfaceService({
            "agent_mode": "general_demo",
            "runtime_contract_gate": {
                "contract_version": "phase-f-runtime-contract-gate-v1",
                "available": True,
                "overall_status": "degraded",
                "generated_at": "2026-05-14T00:00:00Z",
                "report_path": "quality-gate-report.json",
                "check_count": 2,
                "failed_check_count": 1,
                "failure_reason": "contract_checks_failed",
                "runtime_contract_summary": {
                    "overall_status": "degraded",
                    "check_count": 2,
                    "failed_check_count": 1,
                    "missing_payload_count": 1,
                    "approval_replay_coverage": {
                        "event_payload_sample": False,
                        "observed_status_kinds": ["approval_created", "approval_resolved"],
                    },
                    "approval_lifecycle_recovery_coverage": {
                        "alignment_smoke": True,
                        "replayed_submission_status": "replayed",
                        "ignored_submission_status": "ignored",
                        "resolved_recovery_reason": "already_resolved",
                    },
                    "approved_tool_execution_coverage": {
                        "bridge_smoke": True,
                        "approved_tool_call_count": 1,
                        "approved_policy_original_status": "approval_required",
                        "approved_policy_override_status": "approved",
                        "deny_override_status": "policy_denied",
                        "deny_tool_call_count": 0,
                    },
                    "sdk_tool_runtime_execution_coverage": {
                        "bridge_smoke": True,
                        "auto_tool_call_count": 1,
                        "auto_tool_history_count": 1,
                        "approved_tool_call_count": 1,
                        "approved_policy_original_status": "approval_required",
                        "approved_policy_override_status": "approved",
                        "deny_override_status": "policy_denied",
                        "deny_tool_call_count": 0,
                    },
                    "embedded_sdk_persistence_coverage": {
                        "persistence_smoke": True,
                        "contract_version": "phase-ii-embedded-sdk-persistence-interface-v1",
                        "memory_posture": "memory_preview",
                        "durable_posture": "durable_ready",
                        "degraded_posture": "durable_degraded",
                        "memory_cross_process_block_reason": "workspace_backend_not_durable",
                        "degraded_cross_process_block_reason": "workspace_backend_fallback_active",
                        "durable_cross_process_candidate": True,
                        "production_recovery_gate_contract_version": "phase-ii-durable-workspace-production-recovery-gate-v1",
                        "production_recovery_gate_status": "blocked",
                        "production_recovery_gate_missing_sections": [
                            "durable_backend_migration_rollout",
                            "worker_ownership_production_gate",
                        ],
                        "production_recovery_default_enabled": False,
                        "production_recovery_worker_ownership_gate_contract_version": "phase-ii-worker-ownership-production-gate-v1",
                        "production_recovery_worker_ownership_gate_status": "blocked",
                        "production_recovery_worker_ownership_default_enabled": False,
                        "production_recovery_worker_ownership_missing_sections": [
                            "vendor_lock_semantics",
                            "heartbeat_renewal_supervisor",
                        ],
                    },
                    "worker_ownership_store_mode_coverage": {
                        "mode_smoke": True,
                        "default_mode": "memory_only",
                        "default_mode_source": "default",
                        "default_adapter_kind": "in_memory",
                        "default_durable": False,
                        "configurable_knob_present": True,
                        "hot_reloadable_knob_present": True,
                        "strict_mode_status": "sqlalchemy_durable",
                        "fallback_mode_status": "fallback_to_memory",
                    },
                    "child_executor_promotion_gate_coverage": {
                        "gate_smoke": True,
                        "contract_version": "phase-ii-child-executor-gate-v1",
                        "gate_status": "blocked",
                        "allowed": False,
                        "failure_reason": "child_executor_preflight_blocked",
                        "blocker_count": 2,
                        "recommended_next_step": "keep_relationship_only",
                    },
                    "child_executor_execution_prerequisites_coverage": {
                        "prerequisites_smoke": True,
                        "contract_version": "phase-ii-child-executor-execution-prerequisites-v1",
                        "overall_status": "blocked",
                        "ready": False,
                        "requirement_count": 3,
                        "missing_requirement_count": 2,
                        "missing_requirements": ["backend_dispatch_ready", "worker_budget"],
                    },
                    "child_executor_dispatch_coverage": {
                        "dispatch_smoke": True,
                        "contract_version": "phase-ii-child-executor-dispatch-v1",
                        "overall_status": "blocked",
                        "dispatch_ready": False,
                        "will_dispatch": False,
                        "backend_dispatch_ready": False,
                        "relationship_seam_preserved": True,
                        "blocker_count": 2,
                        "dispatch_attempt_handoff_status": "blocked",
                        "dispatch_attempt_handoff_ready": False,
                        "opt_in_dispatch_attempt_handoff_ready": True,
                        "opt_in_attempt_validation_ready": True,
                        "opt_in_ready_dispatch_status": "ready",
                        "opt_in_ready_dispatch_ready": True,
                        "opt_in_ready_handoff_ready": True,
                        "opt_in_ready_will_dispatch": False,
                        "recommended_next_step": "implement_child_executor_backend_dispatch",
                    },
                    "recovery_retry_evidence_coverage": {
                        "retry_smoke": True,
                        "contract_version": "phase-ii-recovery-retry-protocol-v1",
                        "attempt_number": 3,
                        "max_attempts": 3,
                        "retry_status": "exhausted",
                        "retryable": False,
                        "terminal": True,
                        "recovery_reason": "workspace_backend_not_durable",
                        "idempotency_key_present": True,
                    },
                    "recovery_retry_scheduler_coverage": {
                        "scheduler_smoke": True,
                        "contract_version": "phase-ii-recovery-retry-scheduler-v1",
                        "default_status": "disabled",
                        "default_eligible": True,
                        "default_will_execute": False,
                        "enabled_status": "executed",
                        "enabled_will_execute": True,
                        "latest_operation_status": "recovered",
                        "attempt_number": 1,
                        "retry_status": "retryable",
                        "recovery_reason": "transient_workspace_unavailable",
                        "previous_operation_id_present": True,
                        "idempotency_key_present": True,
                    },
                    "durable_recovery_loader_coverage": {
                        "loader_smoke": True,
                        "contract_version": "phase-ii-durable-recovery-loader-v1",
                        "loader_status": "ready",
                        "loader_ready": True,
                        "loader_recovery_reason": "ready_via_registry",
                        "all_bindings_resolved": True,
                        "missing_recovery_reason": "run_snapshot_missing",
                        "unsafe_recovery_reason": "descriptor_corrupted",
                        "executes_recovery": False,
                        "deserializes_callables": False,
                    },
                    "subagent_lane_query_detail_coverage": {
                        "detail_smoke": True,
                        "contract_version": "phase-h-subagent-lane-query-detail-v1",
                        "recording_state": "recorded",
                        "stage_count": 2,
                        "recent_event_count": 2,
                    },
                },
                "runtime_contract_artifact_schema": {
                    "contract_version": "phase-f-runtime-contract-artifact-schema-v1",
                    "overall_status": "degraded",
                    "summary_required_fields": [
                        "overall_status",
                        "subagent_lane_query_detail_coverage.detail_smoke",
                    ],
                    "summary_missing_fields": [
                        "subagent_lane_query_detail_coverage.detail_smoke",
                    ],
                },
                "checks": [
                    {"name": "runtime_profile_contract_snapshot", "ok": True},
                    {
                        "name": "embedded_sdk_event_payloads",
                        "ok": False,
                        "failure_reason": "sdk_event_payload_contract_incomplete",
                        "missing_payload_count": 1,
                        "observed_status_kinds": ["approval_created", "approval_resolved"],
                    },
                ],
            },
        })

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/runtime-profile?conversation_id=321&plan_id=10&item_id=23")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["runtime_contract_gate"]["overall_status"], "degraded")
        self.assertEqual(response.json()["runtime_contract_gate_timeline_recording"]["trace_written"], True)
        self.assertEqual(len(_StubRunTraceService.trace_calls), 1)
        trace_call = _StubRunTraceService.trace_calls[0]
        self.assertEqual(trace_call["conversation_id"], 321)
        self.assertEqual(trace_call["plan_id"], 10)
        self.assertEqual(trace_call["item_id"], 23)
        self.assertEqual(trace_call["source"], "runtime_contract")
        self.assertEqual(trace_call["event_type"], "runtime_contract_gate_degraded")
        self.assertEqual(trace_call["severity"], "warning")
        self.assertIn("approval_lifecycle=covered", trace_call["detail"])
        self.assertIn("approved_tool=covered", trace_call["detail"])
        self.assertIn("sdk_tool=covered", trace_call["detail"])
        self.assertIn("embedded_persistence=covered", trace_call["detail"])
        self.assertIn("worker_ownership=covered", trace_call["detail"])
        self.assertIn("child_executor_gate=covered", trace_call["detail"])
        self.assertIn("child_executor_prerequisites=covered", trace_call["detail"])
        self.assertIn("child_executor_dispatch=covered", trace_call["detail"])
        self.assertIn("subagent_detail=covered", trace_call["detail"])
        self.assertIn("recovery_retry=covered", trace_call["detail"])
        self.assertIn("recovery_retry_scheduler=covered", trace_call["detail"])
        self.assertIn("durable_loader=covered", trace_call["detail"])
        self.assertIn("child_executor_dispatcher=missing", trace_call["detail"])
        self.assertEqual(trace_call["payload"]["failed_check_count"], 1)
        self.assertEqual(trace_call["payload"]["failed_checks"][0]["name"], "embedded_sdk_event_payloads")
        self.assertEqual(trace_call["payload"]["runtime_contract_summary"]["missing_payload_count"], 1)
        self.assertFalse(
            trace_call["payload"]["runtime_contract_summary"]["approval_replay_coverage"]["event_payload_sample"]
        )
        lifecycle_coverage = trace_call["payload"]["runtime_contract_summary"]["approval_lifecycle_recovery_coverage"]
        self.assertTrue(lifecycle_coverage["alignment_smoke"])
        self.assertEqual(lifecycle_coverage["replayed_submission_status"], "replayed")
        self.assertEqual(lifecycle_coverage["ignored_submission_status"], "ignored")
        self.assertEqual(lifecycle_coverage["resolved_recovery_reason"], "already_resolved")
        approved_coverage = trace_call["payload"]["runtime_contract_summary"]["approved_tool_execution_coverage"]
        self.assertTrue(approved_coverage["bridge_smoke"])
        self.assertEqual(approved_coverage["approved_tool_call_count"], 1)
        self.assertEqual(approved_coverage["approved_policy_original_status"], "approval_required")
        self.assertEqual(approved_coverage["approved_policy_override_status"], "approved")
        self.assertEqual(approved_coverage["deny_override_status"], "policy_denied")
        self.assertEqual(approved_coverage["deny_tool_call_count"], 0)
        sdk_tool_coverage = trace_call["payload"]["runtime_contract_summary"]["sdk_tool_runtime_execution_coverage"]
        self.assertTrue(sdk_tool_coverage["bridge_smoke"])
        self.assertEqual(sdk_tool_coverage["auto_tool_call_count"], 1)
        self.assertEqual(sdk_tool_coverage["auto_tool_history_count"], 1)
        persistence_coverage = trace_call["payload"]["runtime_contract_summary"]["embedded_sdk_persistence_coverage"]
        self.assertTrue(persistence_coverage["persistence_smoke"])
        self.assertEqual(persistence_coverage["memory_posture"], "memory_preview")
        worker_ownership_coverage = trace_call["payload"]["runtime_contract_summary"]["worker_ownership_store_mode_coverage"]
        self.assertTrue(worker_ownership_coverage["mode_smoke"])
        self.assertEqual(worker_ownership_coverage["default_mode"], "memory_only")
        child_gate_coverage = trace_call["payload"]["runtime_contract_summary"]["child_executor_promotion_gate_coverage"]
        self.assertTrue(child_gate_coverage["gate_smoke"])
        self.assertEqual(child_gate_coverage["gate_status"], "blocked")
        prerequisites_coverage = trace_call["payload"]["runtime_contract_summary"]["child_executor_execution_prerequisites_coverage"]
        self.assertTrue(prerequisites_coverage["prerequisites_smoke"])
        self.assertEqual(prerequisites_coverage["missing_requirement_count"], 2)
        child_dispatch_coverage = trace_call["payload"]["runtime_contract_summary"]["child_executor_dispatch_coverage"]
        self.assertTrue(child_dispatch_coverage["dispatch_smoke"])
        self.assertFalse(child_dispatch_coverage["will_dispatch"])
        self.assertEqual(child_dispatch_coverage["opt_in_ready_dispatch_status"], "ready")
        self.assertTrue(child_dispatch_coverage["opt_in_ready_dispatch_ready"])
        retry_coverage = trace_call["payload"]["runtime_contract_summary"]["recovery_retry_evidence_coverage"]
        self.assertTrue(retry_coverage["retry_smoke"])
        self.assertEqual(retry_coverage["contract_version"], "phase-ii-recovery-retry-protocol-v1")
        self.assertEqual(retry_coverage["attempt_number"], 3)
        self.assertEqual(retry_coverage["max_attempts"], 3)
        self.assertEqual(retry_coverage["retry_status"], "exhausted")
        self.assertFalse(retry_coverage["retryable"])
        self.assertTrue(retry_coverage["terminal"])
        self.assertEqual(retry_coverage["recovery_reason"], "workspace_backend_not_durable")
        self.assertTrue(retry_coverage["idempotency_key_present"])
        scheduler_coverage = trace_call["payload"]["runtime_contract_summary"]["recovery_retry_scheduler_coverage"]
        self.assertTrue(scheduler_coverage["scheduler_smoke"])
        self.assertEqual(scheduler_coverage["enabled_status"], "executed")
        durable_loader_coverage = trace_call["payload"]["runtime_contract_summary"]["durable_recovery_loader_coverage"]
        self.assertTrue(durable_loader_coverage["loader_smoke"])
        self.assertEqual(durable_loader_coverage["loader_status"], "ready")
        self.assertEqual(durable_loader_coverage["unsafe_recovery_reason"], "descriptor_corrupted")
        dispatcher_coverage = trace_call["payload"]["runtime_contract_summary"]["child_executor_dispatcher_coverage"]
        self.assertFalse(dispatcher_coverage["dispatcher_smoke"])
        self.assertEqual(dispatcher_coverage["contract_version"], "")
        subagent_coverage = trace_call["payload"]["runtime_contract_summary"]["subagent_lane_query_detail_coverage"]
        self.assertTrue(subagent_coverage["detail_smoke"])
        self.assertEqual(subagent_coverage["contract_version"], "phase-h-subagent-lane-query-detail-v1")
        self.assertEqual(subagent_coverage["recording_state"], "recorded")
        self.assertEqual(subagent_coverage["stage_count"], 2)
        self.assertEqual(subagent_coverage["recent_event_count"], 2)
        artifact_schema = trace_call["payload"]["runtime_contract_artifact_schema"]
        self.assertEqual(artifact_schema["contract_version"], "phase-f-runtime-contract-artifact-schema-v1")
        self.assertEqual(artifact_schema["overall_status"], "degraded")
        self.assertIn(
            "subagent_lane_query_detail_coverage.detail_smoke",
            artifact_schema["summary_required_fields"],
        )
        self.assertEqual(
            artifact_schema["summary_missing_fields"],
            ["subagent_lane_query_detail_coverage.detail_smoke"],
        )
        self.assertIn("approval_resolved", trace_call["payload"]["failed_checks"][0]["observed_status_kinds"])
        self.assertEqual(
            trace_call["payload"]["fingerprint"],
            response.json()["runtime_contract_gate_timeline_recording"]["fingerprint"],
        )
        expected_dedupe_key = f"runtime_contract_gate_degraded:{trace_call['payload']['fingerprint']}"
        self.assertEqual(trace_call["payload"]["dedupe_key"], expected_dedupe_key)
        self.assertEqual(response.json()["runtime_contract_gate_timeline_recording"]["dedupe_key"], expected_dedupe_key)

    @patch("backend.routers.health.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.health.get_runtime_surface_service")
    def test_runtime_profile_dedupes_repeated_contract_gate_degraded_trace(self, mock_factory, _mock_trace):
        _StubRunTraceService.trace_calls.clear()
        mock_factory.return_value = _StubRuntimeSurfaceService({
            "agent_mode": "general_demo",
            "runtime_contract_gate": {
                "contract_version": "phase-f-runtime-contract-gate-v1",
                "available": True,
                "overall_status": "degraded",
                "generated_at": "2026-05-14T00:00:00Z",
                "report_path": "quality-gate-report.json",
                "check_count": 1,
                "failed_check_count": 1,
                "failure_reason": "contract_checks_failed",
                "checks": [
                    {"name": "adapter_health_status", "ok": False, "failure_reason": "adapter degraded"},
                ],
            },
        })

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        first_response = client.get("/api/runtime-profile?conversation_id=321&plan_id=10&item_id=23")
        second_response = client.get("/api/runtime-profile?conversation_id=321&plan_id=10&item_id=23")

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(first_response.json()["runtime_contract_gate_timeline_recording"]["trace_written"], True)
        self.assertEqual(second_response.json()["runtime_contract_gate_timeline_recording"]["trace_written"], False)
        self.assertEqual(
            second_response.json()["runtime_contract_gate_timeline_recording"]["reason"],
            "duplicate_runtime_contract_gate_trace",
        )
        self.assertEqual(len(_StubRunTraceService.trace_calls), 1)
        self.assertIn("approval_lifecycle=unknown", _StubRunTraceService.trace_calls[0]["detail"])

    @patch("backend.routers.health.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.health.get_runtime_surface_service")
    def test_runtime_profile_dedupes_contract_gate_degraded_trace_from_persisted_trace(
        self,
        mock_factory,
        _mock_trace,
    ):
        _StubRunTraceService.trace_calls.clear()
        runtime_contract_gate = {
            "contract_version": "phase-f-runtime-contract-gate-v1",
            "available": True,
            "overall_status": "degraded",
            "generated_at": "2026-05-14T00:00:00Z",
            "report_path": "quality-gate-report.json",
            "check_count": 1,
            "failed_check_count": 1,
            "failure_reason": "contract_checks_failed",
            "checks": [
                {"name": "adapter_health_status", "ok": False, "failure_reason": "adapter degraded"},
            ],
        }
        persisted_fingerprint = health_router._build_runtime_contract_gate_trace_fingerprint(
            conversation_id=321,
            plan_id=10,
            item_id=23,
            runtime_contract_gate=runtime_contract_gate,
        )
        _StubRunTraceService.existing_runtime_trace_dedupe_keys = {
            f"runtime_contract_gate_degraded:{persisted_fingerprint}"
        }
        mock_factory.return_value = _StubRuntimeSurfaceService({
            "agent_mode": "general_demo",
            "runtime_contract_gate": runtime_contract_gate,
        })

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/runtime-profile?conversation_id=321&plan_id=10&item_id=23")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["runtime_contract_gate_timeline_recording"]["trace_written"], False)
        self.assertEqual(
            response.json()["runtime_contract_gate_timeline_recording"]["reason"],
            "duplicate_runtime_contract_gate_trace",
        )
        self.assertEqual(response.json()["runtime_contract_gate_timeline_recording"]["dedupe_source"], "persisted_trace")
        self.assertEqual(len(_StubRunTraceService.trace_calls), 0)

    @patch("backend.routers.health.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.health.get_runtime_surface_service")
    def test_runtime_profile_records_contract_gate_trace_again_when_failure_signature_changes(self, mock_factory, _mock_trace):
        _StubRunTraceService.trace_calls.clear()
        base_profile = {
            "agent_mode": "general_demo",
            "runtime_contract_gate": {
                "contract_version": "phase-f-runtime-contract-gate-v1",
                "available": True,
                "overall_status": "degraded",
                "generated_at": "2026-05-14T00:00:00Z",
                "report_path": "quality-gate-report.json",
                "check_count": 1,
                "failed_check_count": 1,
                "failure_reason": "contract_checks_failed",
                "runtime_contract_summary": {
                    "overall_status": "degraded",
                    "check_count": 1,
                    "failed_check_count": 1,
                    "missing_payload_count": 1,
                    "approval_replay_coverage": {
                        "event_payload_sample": False,
                        "observed_status_kinds": ["approval_created"],
                    },
                },
                "checks": [
                    {
                        "name": "embedded_sdk_event_payloads",
                        "ok": False,
                        "failure_reason": "payload missing",
                        "missing_payload_count": 1,
                    },
                ],
            },
        }
        changed_profile = {
            **base_profile,
            "runtime_contract_gate": {
                **base_profile["runtime_contract_gate"],
                "runtime_contract_summary": {
                    "overall_status": "degraded",
                    "check_count": 1,
                    "failed_check_count": 1,
                    "missing_payload_count": 2,
                    "approval_replay_coverage": {
                        "event_payload_sample": False,
                        "observed_status_kinds": ["approval_created", "approval_resolved"],
                    },
                },
                "checks": [
                    {
                        "name": "embedded_sdk_event_payloads",
                        "ok": False,
                        "failure_reason": "payload missing",
                        "missing_payload_count": 1,
                    },
                ],
            },
        }
        mock_factory.return_value = _CyclingRuntimeSurfaceService([base_profile, changed_profile])

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        first_response = client.get("/api/runtime-profile?conversation_id=321&plan_id=10&item_id=23")
        second_response = client.get("/api/runtime-profile?conversation_id=321&plan_id=10&item_id=23")

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(first_response.json()["runtime_contract_gate_timeline_recording"]["trace_written"], True)
        self.assertEqual(second_response.json()["runtime_contract_gate_timeline_recording"]["trace_written"], True)
        self.assertEqual(len(_StubRunTraceService.trace_calls), 2)
        self.assertEqual(_StubRunTraceService.trace_calls[1]["payload"]["failed_check_count"], 1)
        self.assertEqual(
            _StubRunTraceService.trace_calls[1]["payload"]["runtime_contract_summary"]["missing_payload_count"],
            2,
        )
        self.assertFalse(
            _StubRunTraceService.trace_calls[0]["payload"]["runtime_contract_summary"]["subagent_lane_query_detail_coverage"]["detail_smoke"]
        )

    @patch("backend.routers.health.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.health.get_runtime_surface_service")
    def test_runtime_profile_records_contract_gate_trace_again_when_approved_tool_coverage_changes(
        self,
        mock_factory,
        _mock_trace,
    ):
        base_summary = {
            "overall_status": "degraded",
            "check_count": 2,
            "failed_check_count": 1,
            "missing_payload_count": 1,
            "approval_replay_coverage": {
                "event_payload_sample": False,
                "observed_status_kinds": ["approval_created"],
            },
            "approved_tool_execution_coverage": {
                "bridge_smoke": False,
                "approved_tool_call_count": 0,
                "approved_policy_original_status": "",
                "approved_policy_override_status": "",
                "deny_override_status": "",
                "deny_tool_call_count": 0,
            },
        }
        base_gate = {
            "contract_version": "phase-f-runtime-contract-gate-v1",
            "available": True,
            "overall_status": "degraded",
            "generated_at": "2026-05-22T00:00:00Z",
            "report_path": "quality-gate-report.json",
            "check_count": 2,
            "failed_check_count": 1,
            "failure_reason": "contract_checks_failed",
            "runtime_contract_summary": base_summary,
            "checks": [
                {"name": "runtime_profile_contract_snapshot", "ok": True},
                {
                    "name": "embedded_sdk_event_payloads",
                    "ok": False,
                    "failure_reason": "payload missing",
                    "missing_payload_count": 1,
                },
            ],
        }
        changed_gate = {
            **base_gate,
            "runtime_contract_summary": {
                **base_summary,
                "approved_tool_execution_coverage": {
                    "bridge_smoke": True,
                    "approved_tool_call_count": 1,
                    "approved_policy_original_status": "approval_required",
                    "approved_policy_override_status": "approved",
                    "deny_override_status": "policy_denied",
                    "deny_tool_call_count": 0,
                },
            },
        }
        mock_factory.return_value = _CyclingRuntimeSurfaceService([
            {"agent_mode": "general_demo", "runtime_contract_gate": base_gate},
            {"agent_mode": "general_demo", "runtime_contract_gate": changed_gate},
        ])

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        first_response = client.get("/api/runtime-profile?conversation_id=321&plan_id=10&item_id=23")
        second_response = client.get("/api/runtime-profile?conversation_id=321&plan_id=10&item_id=23")

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertTrue(first_response.json()["runtime_contract_gate_timeline_recording"]["trace_written"])
        self.assertTrue(second_response.json()["runtime_contract_gate_timeline_recording"]["trace_written"])
        self.assertEqual(len(_StubRunTraceService.trace_calls), 2)
        first_fingerprint = _StubRunTraceService.trace_calls[0]["payload"]["fingerprint"]
        second_fingerprint = _StubRunTraceService.trace_calls[1]["payload"]["fingerprint"]
        self.assertNotEqual(first_fingerprint, second_fingerprint)
        self.assertFalse(
            _StubRunTraceService.trace_calls[0]["payload"]["runtime_contract_summary"]["approved_tool_execution_coverage"]["bridge_smoke"]
        )
        self.assertTrue(
            _StubRunTraceService.trace_calls[1]["payload"]["runtime_contract_summary"]["approved_tool_execution_coverage"]["bridge_smoke"]
        )

    @patch("backend.routers.health.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.health.get_runtime_surface_service")
    def test_runtime_profile_contract_gate_trace_fails_closed_when_lifecycle_coverage_evidence_disagrees(
        self,
        mock_factory,
        _mock_trace,
    ):
        _StubRunTraceService.trace_calls.clear()
        mock_factory.return_value = _StubRuntimeSurfaceService({
            "agent_mode": "general_demo",
            "runtime_contract_gate": {
                "contract_version": "phase-f-runtime-contract-gate-v1",
                "available": True,
                "overall_status": "degraded",
                "generated_at": "2026-05-22T00:00:00Z",
                "report_path": "quality-gate-report.json",
                "check_count": 1,
                "failed_check_count": 1,
                "failure_reason": "contract_checks_failed",
                "runtime_contract_summary": {
                    "overall_status": "degraded",
                    "check_count": 1,
                    "failed_check_count": 1,
                    "missing_payload_count": 0,
                    "approval_lifecycle_recovery_coverage": {
                        "alignment_smoke": True,
                        "replayed_submission_status": "replayed",
                        "ignored_submission_status": "accepted",
                        "resolved_recovery_reason": "already_resolved",
                    },
                },
                "checks": [
                    {"name": "approval_lifecycle_recovery_alignment", "ok": False},
                ],
            },
        })
        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/runtime-profile?conversation_id=321&plan_id=10&item_id=23")

        self.assertEqual(response.status_code, 200)
        coverage = _StubRunTraceService.trace_calls[0]["payload"]["runtime_contract_summary"][
            "approval_lifecycle_recovery_coverage"
        ]
        self.assertFalse(coverage["alignment_smoke"])
        self.assertEqual(coverage["replayed_submission_status"], "replayed")
        self.assertEqual(coverage["ignored_submission_status"], "accepted")
        self.assertEqual(coverage["resolved_recovery_reason"], "already_resolved")

    @patch("backend.routers.health.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.health.get_runtime_surface_service")
    def test_runtime_profile_contract_gate_trace_fails_closed_when_recovery_retry_evidence_disagrees(
        self,
        mock_factory,
        _mock_trace,
    ):
        _StubRunTraceService.trace_calls.clear()
        mock_factory.return_value = _StubRuntimeSurfaceService({
            "agent_mode": "general_demo",
            "runtime_contract_gate": {
                "contract_version": "phase-f-runtime-contract-gate-v1",
                "available": True,
                "overall_status": "degraded",
                "generated_at": "2026-05-24T00:00:00Z",
                "report_path": "quality-gate-report.json",
                "check_count": 1,
                "failed_check_count": 1,
                "failure_reason": "contract_checks_failed",
                "runtime_contract_summary": {
                    "overall_status": "degraded",
                    "check_count": 1,
                    "failed_check_count": 1,
                    "missing_payload_count": 0,
                    "recovery_retry_evidence_coverage": {
                        "retry_smoke": True,
                        "contract_version": "phase-ii-recovery-retry-protocol-v1",
                        "attempt_number": 2,
                        "max_attempts": 3,
                        "retry_status": "attempted",
                        "retryable": True,
                        "terminal": False,
                        "recovery_reason": "workspace_backend_not_durable",
                        "idempotency_key_present": False,
                    },
                },
                "checks": [
                    {"name": "recovery_retry_evidence", "ok": False},
                ],
            },
        })
        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/runtime-profile?conversation_id=321&plan_id=10&item_id=23")

        self.assertEqual(response.status_code, 200)
        self.assertIn("recovery_retry=missing", _StubRunTraceService.trace_calls[0]["detail"])
        coverage = _StubRunTraceService.trace_calls[0]["payload"]["runtime_contract_summary"][
            "recovery_retry_evidence_coverage"
        ]
        self.assertFalse(coverage["retry_smoke"])
        self.assertEqual(coverage["attempt_number"], 2)
        self.assertEqual(coverage["retry_status"], "attempted")
        self.assertFalse(coverage["terminal"])
        self.assertFalse(coverage["idempotency_key_present"])

    @patch("backend.routers.health.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.health.get_runtime_surface_service")
    def test_runtime_profile_records_contract_gate_trace_again_when_subagent_detail_coverage_changes(
        self,
        mock_factory,
        _mock_trace,
    ):
        base_summary = {
            "overall_status": "degraded",
            "check_count": 2,
            "failed_check_count": 1,
            "missing_payload_count": 1,
            "approval_replay_coverage": {
                "event_payload_sample": False,
                "observed_status_kinds": ["approval_created"],
            },
            "approved_tool_execution_coverage": {
                "bridge_smoke": True,
                "approved_tool_call_count": 1,
                "approved_policy_original_status": "approval_required",
                "approved_policy_override_status": "approved",
                "deny_override_status": "policy_denied",
                "deny_tool_call_count": 0,
            },
            "subagent_lane_query_detail_coverage": {
                "detail_smoke": False,
                "contract_version": "",
                "recording_state": "",
                "stage_count": 0,
                "recent_event_count": 0,
            },
        }
        base_gate = {
            "contract_version": "phase-f-runtime-contract-gate-v1",
            "available": True,
            "overall_status": "degraded",
            "generated_at": "2026-05-22T00:00:00Z",
            "report_path": "quality-gate-report.json",
            "check_count": 2,
            "failed_check_count": 1,
            "failure_reason": "contract_checks_failed",
            "runtime_contract_summary": base_summary,
            "checks": [
                {"name": "runtime_profile_contract_snapshot", "ok": True},
                {
                    "name": "embedded_sdk_event_payloads",
                    "ok": False,
                    "failure_reason": "payload missing",
                    "missing_payload_count": 1,
                },
            ],
        }
        changed_gate = {
            **base_gate,
            "runtime_contract_summary": {
                **base_summary,
                "subagent_lane_query_detail_coverage": {
                    "detail_smoke": True,
                    "contract_version": "phase-h-subagent-lane-query-detail-v1",
                    "recording_state": "recorded",
                    "stage_count": 2,
                    "recent_event_count": 2,
                },
            },
        }
        mock_factory.return_value = _CyclingRuntimeSurfaceService([
            {"agent_mode": "general_demo", "runtime_contract_gate": base_gate},
            {"agent_mode": "general_demo", "runtime_contract_gate": changed_gate},
        ])

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        first_response = client.get("/api/runtime-profile?conversation_id=321&plan_id=10&item_id=23")
        second_response = client.get("/api/runtime-profile?conversation_id=321&plan_id=10&item_id=23")

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertTrue(first_response.json()["runtime_contract_gate_timeline_recording"]["trace_written"])
        self.assertTrue(second_response.json()["runtime_contract_gate_timeline_recording"]["trace_written"])
        self.assertEqual(len(_StubRunTraceService.trace_calls), 2)
        first_fingerprint = _StubRunTraceService.trace_calls[0]["payload"]["fingerprint"]
        second_fingerprint = _StubRunTraceService.trace_calls[1]["payload"]["fingerprint"]
        self.assertNotEqual(first_fingerprint, second_fingerprint)
        self.assertFalse(
            _StubRunTraceService.trace_calls[0]["payload"]["runtime_contract_summary"]["subagent_lane_query_detail_coverage"]["detail_smoke"]
        )
        changed_coverage = _StubRunTraceService.trace_calls[1]["payload"]["runtime_contract_summary"]["subagent_lane_query_detail_coverage"]
        self.assertTrue(changed_coverage["detail_smoke"])
        self.assertEqual(changed_coverage["contract_version"], "phase-h-subagent-lane-query-detail-v1")
        self.assertEqual(changed_coverage["stage_count"], 2)

    @patch("backend.routers.health.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.health.get_runtime_surface_service")
    def test_runtime_profile_records_contract_gate_trace_again_when_recovery_retry_coverage_changes(
        self,
        mock_factory,
        _mock_trace,
    ):
        _StubRunTraceService.trace_calls.clear()
        base_summary = {
            "overall_status": "degraded",
            "check_count": 2,
            "failed_check_count": 1,
            "missing_payload_count": 1,
            "approval_replay_coverage": {
                "event_payload_sample": False,
                "observed_status_kinds": ["approval_created"],
            },
            "recovery_retry_evidence_coverage": {
                "retry_smoke": False,
                "contract_version": "",
                "attempt_number": 0,
                "max_attempts": 0,
                "retry_status": "",
                "retryable": False,
                "terminal": False,
                "recovery_reason": "",
                "idempotency_key_present": False,
            },
        }
        base_gate = {
            "contract_version": "phase-f-runtime-contract-gate-v1",
            "available": True,
            "overall_status": "degraded",
            "generated_at": "2026-05-24T00:00:00Z",
            "report_path": "quality-gate-report.json",
            "check_count": 2,
            "failed_check_count": 1,
            "failure_reason": "contract_checks_failed",
            "runtime_contract_summary": base_summary,
            "checks": [
                {"name": "runtime_profile_contract_snapshot", "ok": True},
                {
                    "name": "embedded_sdk_event_payloads",
                    "ok": False,
                    "failure_reason": "payload missing",
                    "missing_payload_count": 1,
                },
            ],
        }
        changed_gate = {
            **base_gate,
            "runtime_contract_summary": {
                **base_summary,
                "recovery_retry_evidence_coverage": {
                    "retry_smoke": True,
                    "contract_version": "phase-ii-recovery-retry-protocol-v1",
                    "attempt_number": 3,
                    "max_attempts": 3,
                    "retry_status": "exhausted",
                    "retryable": True,
                    "terminal": True,
                    "recovery_reason": "workspace_backend_not_durable",
                    "idempotency_key_present": True,
                },
            },
        }
        mock_factory.return_value = _CyclingRuntimeSurfaceService([
            {"agent_mode": "general_demo", "runtime_contract_gate": base_gate},
            {"agent_mode": "general_demo", "runtime_contract_gate": changed_gate},
        ])

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        first_response = client.get("/api/runtime-profile?conversation_id=321&plan_id=10&item_id=23")
        second_response = client.get("/api/runtime-profile?conversation_id=321&plan_id=10&item_id=23")

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertTrue(first_response.json()["runtime_contract_gate_timeline_recording"]["trace_written"])
        self.assertTrue(second_response.json()["runtime_contract_gate_timeline_recording"]["trace_written"])
        self.assertEqual(len(_StubRunTraceService.trace_calls), 2)
        first_payload = _StubRunTraceService.trace_calls[0]["payload"]
        second_payload = _StubRunTraceService.trace_calls[1]["payload"]
        self.assertNotEqual(first_payload["fingerprint"], second_payload["fingerprint"])
        self.assertIn("recovery_retry=missing", _StubRunTraceService.trace_calls[0]["detail"])
        self.assertIn("recovery_retry=covered", _StubRunTraceService.trace_calls[1]["detail"])
        self.assertFalse(
            first_payload["runtime_contract_summary"]["recovery_retry_evidence_coverage"]["retry_smoke"]
        )
        changed_coverage = second_payload["runtime_contract_summary"]["recovery_retry_evidence_coverage"]
        self.assertTrue(changed_coverage["retry_smoke"])
        self.assertEqual(changed_coverage["contract_version"], "phase-ii-recovery-retry-protocol-v1")
        self.assertEqual(changed_coverage["attempt_number"], 3)
        self.assertEqual(changed_coverage["retry_status"], "exhausted")

    @patch("backend.routers.health.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.health.get_runtime_surface_service")
    def test_runtime_profile_records_contract_gate_trace_again_when_artifact_schema_changes(
        self,
        mock_factory,
        _mock_trace,
    ):
        _StubRunTraceService.trace_calls.clear()
        base_schema = {
            "contract_version": "phase-f-runtime-contract-artifact-schema-v1",
            "overall_status": "degraded",
            "summary_required_fields": ["subagent_lane_query_detail_coverage.detail_smoke"],
            "summary_missing_fields": ["subagent_lane_query_detail_coverage.detail_smoke"],
        }
        base_gate = {
            "contract_version": "phase-f-runtime-contract-gate-v1",
            "available": True,
            "overall_status": "degraded",
            "generated_at": "2026-05-22T00:00:00Z",
            "report_path": "quality-gate-report.json",
            "check_count": 1,
            "failed_check_count": 1,
            "failure_reason": "contract_checks_failed",
            "runtime_contract_summary": {
                "overall_status": "degraded",
                "check_count": 1,
                "failed_check_count": 1,
                "missing_payload_count": 1,
                "approval_replay_coverage": {
                    "event_payload_sample": False,
                    "observed_status_kinds": ["approval_created"],
                },
            },
            "runtime_contract_artifact_schema": base_schema,
            "checks": [
                {
                    "name": "embedded_sdk_event_payloads",
                    "ok": False,
                    "failure_reason": "payload missing",
                    "missing_payload_count": 1,
                },
            ],
        }
        changed_gate = {
            **base_gate,
            "runtime_contract_artifact_schema": {
                **base_schema,
                "overall_status": "healthy",
                "summary_missing_fields": [],
            },
        }
        mock_factory.return_value = _CyclingRuntimeSurfaceService([
            {"agent_mode": "general_demo", "runtime_contract_gate": base_gate},
            {"agent_mode": "general_demo", "runtime_contract_gate": changed_gate},
        ])

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        first_response = client.get("/api/runtime-profile?conversation_id=321&plan_id=10&item_id=23")
        second_response = client.get("/api/runtime-profile?conversation_id=321&plan_id=10&item_id=23")

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertTrue(first_response.json()["runtime_contract_gate_timeline_recording"]["trace_written"])
        self.assertTrue(second_response.json()["runtime_contract_gate_timeline_recording"]["trace_written"])
        self.assertEqual(len(_StubRunTraceService.trace_calls), 2)
        first_payload = _StubRunTraceService.trace_calls[0]["payload"]
        second_payload = _StubRunTraceService.trace_calls[1]["payload"]
        self.assertNotEqual(first_payload["fingerprint"], second_payload["fingerprint"])
        self.assertEqual(first_payload["runtime_contract_artifact_schema"]["overall_status"], "degraded")
        self.assertEqual(second_payload["runtime_contract_artifact_schema"]["overall_status"], "healthy")
        self.assertEqual(second_payload["runtime_contract_artifact_schema"]["summary_missing_fields"], [])

    @patch("backend.routers.health.get_scheduler_runtime_diagnostics_service", return_value=_StubSchedulerRuntimeDiagnosticsService())
    def test_runtime_backend_status_endpoint_returns_backend_diagnostics(self, _mock_factory):
        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get("/api/runtime-backend?limit=25")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["backend"], "metadata_adapter")
        self.assertEqual(response.json()["metadata_runtime_summary"]["scan_limit"], 25)

    @patch("backend.routers.health.get_scheduler_runtime_diagnostics_service", return_value=_StubSchedulerRuntimeDiagnosticsService())
    def test_runtime_backend_reconcile_endpoint_runs_reconciliation(self, _mock_factory):
        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.post("/api/runtime-backend/reconcile?plan_id=9&item_id=21&limit=10")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["reconciled_items"], 2)
        self.assertEqual(response.json()["items"][0]["plan_id"], 9)

    @patch("backend.routers.health.get_runtime_surface_service")
    def test_runtime_profile_patch_updates_surface(self, mock_factory):
        mock_factory.return_value.update_runtime_profile.return_value = {
            "agent_mode": "general_demo",
            "auth_mode": "business_auth",
            "default_model": "doubao",
            "embedded_runtime_bootstrap": {
                "contract_version": "phase-ii-embedded-runtime-factory-v1",
                "default_runtime_profile": {
                    "embedded_workspace_store_mode": "memory_only",
                },
            },
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

        response = client.patch(
            "/api/runtime-profile",
            json={"auth_mode": "business_auth", "embedded_workspace_store_mode": "memory_only"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["auth_mode"], "business_auth")
        self.assertEqual(
            response.json()["embedded_runtime_bootstrap"]["default_runtime_profile"]["embedded_workspace_store_mode"],
            "memory_only",
        )

    @patch("backend.routers.health.ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER", True)
    @patch("backend.routers.health.get_framework_adapter_runtime_service", return_value=_StubFrameworkAdapterRuntimeService())
    def test_framework_adapter_pilot_run_endpoint_executes_runtime_service(self, _mock_runtime_service):
        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.post(
            "/api/runtime-framework-adapters/pilot-run",
            json={
                "adapter_id": "local_fake_framework",
                "run_id": "run-c2-route-1",
                "conversation_id": 321,
                "user_id": 1,
                "messages": [{"role": "user", "content": "生成巡检计划"}],
                "execution_context": {"plan_id": 10, "plan_item_id": 24},
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["adapter_id"], "local_fake_framework")
        self.assertEqual(response.json()["run_id"], "run-c2-route-1")
        self.assertEqual(response.json()["final_output"], "Local fake adapter processed: 生成巡检计划")
        self.assertEqual(_StubFrameworkAdapterRuntimeService.calls[0]["conversation_id"], 321)
        self.assertEqual(_StubFrameworkAdapterRuntimeService.calls[0]["messages"][0]["content"], "生成巡检计划")

    @patch("backend.routers.health.ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER", False)
    def test_framework_adapter_pilot_run_endpoint_rejects_when_disabled(self):
        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.post(
            "/api/runtime-framework-adapters/pilot-run",
            json={
                "adapter_id": "local_fake_framework",
                "run_id": "run-c2-route-disabled",
                "messages": [{"role": "user", "content": "test"}],
            },
        )
        self.assertEqual(response.status_code, 409)
        self.assertIn("disabled", response.json()["error"]["message"])

    @patch("backend.routers.health.ENABLE_LANGGRAPH_EXTERNAL_PILOT", False)
    @patch("backend.routers.health.get_framework_adapter_runtime_service", return_value=_StubFrameworkAdapterRuntimeService())
    def test_framework_adapter_external_pilot_endpoint_rejects_when_disabled(self, _mock_runtime_service):
        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.post(
            "/api/runtime-framework-adapters/external-pilot",
            json={
                "adapter_id": "langgraph_draft",
                "run_id": "run-external-1",
                "messages": [{"role": "user", "content": "test"}],
            },
        )
        self.assertEqual(response.status_code, 409)
        self.assertIn("disabled", response.json()["error"]["message"])

    @patch("backend.routers.health.ENABLE_LANGGRAPH_EXTERNAL_PILOT", True)
    @patch("backend.routers.health.get_framework_adapter_runtime_service", return_value=_StubFrameworkAdapterRuntimeService())
    def test_framework_adapter_external_pilot_endpoint_returns_snapshot(self, _mock_runtime_service):
        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.post(
            "/api/runtime-framework-adapters/external-pilot",
            json={
                "adapter_id": "langgraph_draft",
                "run_id": "run-external-1",
                "conversation_id": 321,
                "user_id": 1,
                "messages": [{"role": "user", "content": "test"}],
                "execution_context": {
                    "plan_id": 10,
                    "plan_item_id": 24,
                    "run_kind": "framework_adapter_external_pilot",
                },
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["adapter_id"], "langgraph_draft")
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["snapshot_ref"]["snapshot_id"], "FRAM-EXT-321-20260513000000")
        self.assertEqual(_StubFrameworkAdapterRuntimeService.calls[0]["conversation_id"], 321)
        self.assertEqual(_StubFrameworkAdapterRuntimeService.calls[0]["messages"][0]["content"], "test")

    @patch("backend.routers.health.get_framework_adapter_runtime_service", return_value=_StubFrameworkAdapterRuntimeService())
    def test_framework_adapter_precheck_endpoint_returns_readiness(self, _mock_runtime_service):
        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.post(
            "/api/runtime-framework-adapters/precheck",
            json={
                "adapter_id": "langgraph_draft",
                "conversation_id": 321,
                "execution_context": {
                    "plan_id": 10,
                    "plan_item_id": 24,
                    "run_kind": "framework_adapter_precheck",
                },
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["adapter_id"], "langgraph_draft")
        self.assertEqual(response.json()["configuration_status"], "missing_package")
        self.assertEqual(response.json()["missing_packages"], ["langgraph"])
        self.assertEqual(response.json()["timeline_recording"]["snapshot_ref"]["snapshot_id"], "FRAM-PRECHECK-321")

    @patch("backend.routers.health.ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER", True)
    @patch("backend.routers.health.get_framework_adapter_runtime_service")
    def test_framework_adapter_pilot_run_endpoint_returns_diagnostic_error_for_registered_placeholder(self, mock_runtime_service_factory):
        mock_runtime_service_factory.return_value.execute_adapter_run.side_effect = ValueError(
            "LangGraph draft adapter is registered as a Phase D-0 placeholder; runtime execution is not enabled."
        )

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.post(
            "/api/runtime-framework-adapters/pilot-run",
            json={
                "adapter_id": "langgraph_draft",
                "run_id": "run-d0-route-disabled",
                "messages": [{"role": "user", "content": "test"}],
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("runtime execution is not enabled", response.json()["error"]["message"])

    @patch("backend.routers.health._collect_framework_adapter_external_error_counts")
    @patch("backend.routers.health._collect_latest_framework_adapter_external_error_summary")
    @patch("backend.routers.health.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.health.get_doctor_runtime_service")
    def test_doctor_endpoint_returns_startup_report(
        self,
        mock_factory,
        _mock_trace_service,
        mock_external_error_summary,
        mock_external_error_counts,
    ):
        mock_factory.return_value.run_startup_report.return_value = {
            "scope": "startup",
            "status": "ok",
            "exit_code": 0,
            "checks": {
                "framework_adapters": {
                    "status": "warn",
                    "details": ["langgraph_draft: status=not_configured | config=missing_package"],
                    "remediation_actions": [
                        {
                            "adapter_id": "langgraph_draft",
                            "framework_name": "LangGraph",
                            "type": "install_package",
                            "packages": ["langgraph"],
                        }
                    ],
                }
            },
        }
        mock_external_error_summary.return_value = {
            "event_type": "framework_adapter_external_error",
            "error_type": "configuration_error",
            "adapter_id": "langgraph_draft",
            "framework_name": "LangGraph",
            "detail": "assistant identity is not recognized by external runtime",
            "snapshot_ref": {"snapshot_id": "FRAM-EXT-ERR-321-20260513020000"},
        }
        mock_external_error_counts.return_value = {
            "total": 4,
            "by_error_type": {
                "configuration_error": 3,
                "protocol_error": 1,
            },
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
        self.assertEqual(response.json()["checks"]["framework_adapters"]["status"], "warn")
        self.assertEqual(
            response.json()["checks"]["framework_adapters"]["latest_external_pilot_failure"]["error_type"],
            "configuration_error",
        )
        self.assertEqual(
            response.json()["checks"]["framework_adapters"]["external_pilot_failure_counts"]["by_error_type"]["configuration_error"],
            3,
        )
        self.assertIn("timeline_recording", response.json())
        mock_factory.return_value.run_startup_report.assert_called_once_with()
        self.assertEqual(len(_StubRunTraceService.trace_calls), 2)
        self.assertEqual(_StubRunTraceService.trace_calls[0]["event_type"], "doctor_run_started")
        self.assertEqual(_StubRunTraceService.trace_calls[1]["event_type"], "doctor_run_completed")
        self.assertEqual(
            _StubRunTraceService.trace_calls[1]["payload"]["framework_adapters"]["status"],
            "warn",
        )
        self.assertEqual(
            _StubRunTraceService.trace_calls[1]["payload"]["framework_adapters"]["remediation_actions"][0]["type"],
            "install_package",
        )
        self.assertEqual(
            _StubRunTraceService.trace_calls[1]["payload"]["framework_adapters"]["remediation_actions"][0]["framework_name"],
            "LangGraph",
        )
        self.assertEqual(
            _StubRunTraceService.trace_calls[1]["payload"]["framework_adapters"]["latest_external_pilot_failure"]["error_type"],
            "configuration_error",
        )
        self.assertEqual(
            _StubRunTraceService.trace_calls[1]["payload"]["framework_adapters"]["external_pilot_failure_counts"]["total"],
            4,
        )
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

    @patch("backend.routers.health.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.health.get_doctor_runtime_service")
    def test_doctor_endpoint_dedupes_repeated_gate_failed_trace(self, mock_factory, _mock_trace_service):
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

        first_response = client.get(
            "/api/doctor?capability_gaps=true&window_days=14&limit=200&max_open_actions=10&max_long_blocked_actions=0&conversation_id=321"
        )
        second_response = client.get(
            "/api/doctor?capability_gaps=true&window_days=14&limit=200&max_open_actions=10&max_long_blocked_actions=0&conversation_id=321"
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(first_response.json()["timeline_recording"]["trace_gate_failed"], True)
        self.assertEqual(second_response.json()["timeline_recording"]["trace_gate_failed"], False)
        self.assertEqual(
            second_response.json()["timeline_recording"]["gate_failed_dedupe_source"],
            "persisted_trace",
        )
        gate_failed_traces = [
            call for call in _StubRunTraceService.trace_calls if call["event_type"] == "doctor_gate_failed"
        ]
        gate_failed_audits = [
            call for call in _StubRunTraceService.audit_calls if call["event_type"] == "doctor_gate_failed"
        ]
        self.assertEqual(len(gate_failed_traces), 1)
        self.assertEqual(len(gate_failed_audits), 1)

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
