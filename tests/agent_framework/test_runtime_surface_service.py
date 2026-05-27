import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.agent_framework.adapters import SQLAlchemyEmbeddedRunWorkspaceStore
from backend.agent_framework.continuation_registry import InMemoryEmbeddedContinuationRegistry
from backend.agent_framework.persistence import (
    InMemoryEmbeddedRunWorkspaceStore,
    build_embedded_workspace_state_contract,
)
from backend.agent_framework.sdk import EmbeddedAgentRuntimeSDK
import backend.services.runtime_surface_service as runtime_surface_service_module
from backend.models import Base
from backend.services.governance_overview_run_state_builder import GovernanceOverviewRunStateBuilder
from backend.services.runtime_core_contract_builder import RuntimeCoreContractBuilder
from backend.services.runtime_surface_builders import ProviderCatalogBuilder, RuntimeRecoveryContractBuilder
from backend.services.runtime_surface_profile_context import RuntimeSurfaceProfileContextAssembler
from backend.services.runtime_surface_profile_assembler import RuntimeSurfaceProfileAssembler
from backend.services.runtime_surface_service import RuntimeSurfaceService


class RuntimeSurfaceServiceTests(unittest.TestCase):
    def test_runtime_surface_service_uses_dedicated_profile_assembler(self):
        self.assertIs(
            runtime_surface_service_module.RuntimeSurfaceProfileAssembler,
            RuntimeSurfaceProfileAssembler,
        )

    def test_runtime_surface_profile_context_prefers_parent_run_for_recovery_target(self):
        self.assertEqual(
            RuntimeSurfaceProfileContextAssembler.resolve_recovery_target_run_id(
                parent_run_id=" parent-run-1 ",
                runtime_scope={"scheduler_run_id": "scheduler-run-1", "run_id": "run-1"},
            ),
            "parent-run-1",
        )

    def test_runtime_surface_profile_context_falls_back_to_scheduler_then_run(self):
        self.assertEqual(
            RuntimeSurfaceProfileContextAssembler.resolve_recovery_target_run_id(
                runtime_scope={"scheduler_run_id": " scheduler-run-1 ", "run_id": "run-1"},
            ),
            "scheduler-run-1",
        )
        self.assertEqual(
            RuntimeSurfaceProfileContextAssembler.resolve_recovery_target_run_id(
                runtime_scope={"scheduler_run_id": " ", "run_id": " run-1 "},
            ),
            "run-1",
        )

    def test_runtime_surface_profile_context_delegates_runtime_scope_to_service(self):
        class StubService:
            def __init__(self):
                self.calls = []

            def _build_runtime_scope_contract(self, **kwargs):
                self.calls.append(kwargs)
                return {"run_id": kwargs["run_id"], "scheduler_run_id": kwargs["scheduler_run_id"]}

        service = StubService()
        context = RuntimeSurfaceProfileContextAssembler.assemble(
            service,
            db="db",
            conversation_id=11,
            plan_id=22,
            item_id=33,
            query_id="query-1",
            run_id="run-1",
            child_run_id="child-run-1",
            scheduler_run_id="scheduler-run-1",
        )

        self.assertEqual(context.query_id, "query-1")
        self.assertEqual(context.runtime_scope["run_id"], "run-1")
        self.assertEqual(context.recovery_target_run_id, "scheduler-run-1")
        self.assertEqual(
            service.calls,
            [
                {
                    "db": "db",
                    "conversation_id": 11,
                    "plan_id": 22,
                    "item_id": 33,
                    "run_id": "run-1",
                    "parent_run_id": None,
                    "child_run_id": "child-run-1",
                    "scheduler_run_id": "scheduler-run-1",
                }
            ],
        )

    def test_runtime_surface_profile_assembler_uses_context_assembler(self):
        self.assertIs(
            RuntimeSurfaceProfileAssembler.__dict__["assemble"].__func__.__globals__[
                "RuntimeSurfaceProfileContextAssembler"
            ],
            RuntimeSurfaceProfileContextAssembler,
        )

    def test_runtime_core_contract_builder_builds_default_contract(self):
        contract = RuntimeCoreContractBuilder.build_contract()

        self.assertTrue(contract["runtime_core"])
        self.assertEqual(contract["contract_version"], "phase-a-runtime-core-v1")
        self.assertEqual(contract["run_id"], "")
        self.assertEqual(contract["run_kind"], "contract")
        self.assertEqual(contract["status"], "not_started")
        self.assertEqual(contract["trace_count"], 0)
        self.assertIsNone(contract["latest_trace_event"])
        self.assertEqual(contract["child_merge_entities"], [])
        self.assertEqual(contract["child_merge_section_counts"], {})

    def test_runtime_core_contract_builder_applies_scope_and_child_display_fallback(self):
        contract = RuntimeCoreContractBuilder.build_contract(
            runtime_scope={
                "run_id": " run-1 ",
                "parent_run_id": " parent-run-1 ",
                "child_run_id": " child-run-1 ",
                "scheduler_run_id": " scheduler-run-1 ",
                "run_kind": " scheduler ",
                "status": " running ",
                "trace_count": 2,
                "latest_trace_event": {"summary": "调度执行中"},
            }
        )

        self.assertEqual(contract["run_id"], "run-1")
        self.assertEqual(contract["parent_run_id"], "parent-run-1")
        self.assertEqual(contract["child_run_id"], "child-run-1")
        self.assertEqual(contract["child_display_id"], "child-run-1")
        self.assertEqual(contract["scheduler_run_id"], "scheduler-run-1")
        self.assertEqual(contract["run_kind"], "scheduler")
        self.assertEqual(contract["status"], "running")
        self.assertEqual(contract["trace_count"], 2)
        self.assertEqual(contract["latest_trace_event"], {"summary": "调度执行中"})

    def test_runtime_core_contract_builder_preserves_child_merge_evidence(self):
        contract = RuntimeCoreContractBuilder.build_contract(
            runtime_scope={
                "child_merge_intent": " risk_review ",
                "child_merge_entities": ["交易", "风险"],
                "child_merge_entity_count": 2,
                "child_merge_focus_count": 3,
                "child_merge_action_count": 1,
                "child_merge_primary_entities": ["交易"],
                "child_merge_conclusion": " 建议复核 ",
                "child_merge_section_source": " merged_sections ",
                "child_merge_section_ids": ["merged_entities"],
                "child_merge_section_counts": {"merged_entities": 2},
            }
        )

        self.assertEqual(contract["child_merge_intent"], "risk_review")
        self.assertEqual(contract["child_merge_entities"], ["交易", "风险"])
        self.assertEqual(contract["child_merge_entity_count"], 2)
        self.assertEqual(contract["child_merge_focus_count"], 3)
        self.assertEqual(contract["child_merge_action_count"], 1)
        self.assertEqual(contract["child_merge_primary_entities"], ["交易"])
        self.assertEqual(contract["child_merge_conclusion"], "建议复核")
        self.assertEqual(contract["child_merge_section_source"], "merged_sections")
        self.assertEqual(contract["child_merge_section_ids"], ["merged_entities"])
        self.assertEqual(contract["child_merge_section_counts"], {"merged_entities": 2})

    def test_runtime_surface_service_runtime_core_wrapper_uses_builder(self):
        self.assertIs(
            RuntimeSurfaceService._build_runtime_core_contract.__globals__["RuntimeCoreContractBuilder"],
            RuntimeCoreContractBuilder,
        )
        self.assertEqual(
            RuntimeSurfaceService()._build_runtime_core_contract(runtime_scope={"run_id": "run-1"})["run_id"],
            "run-1",
        )

    def test_governance_overview_run_state_builder_builds_default_run(self):
        run = GovernanceOverviewRunStateBuilder.build_run_state()

        self.assertTrue(run["runtime_core"])
        self.assertEqual(run["run_id"], "")
        self.assertEqual(run["run_kind"], "contract")
        self.assertEqual(run["status"], "not_started")
        self.assertEqual(run["trace_count"], 0)
        self.assertIsNone(run["latest_trace_event"])
        self.assertEqual(run["child_merge_entities"], [])
        self.assertEqual(run["child_merge_section_counts"], {})

    def test_governance_overview_run_state_builder_preserves_scope_and_child_merge(self):
        run = GovernanceOverviewRunStateBuilder.build_run_state(
            runtime_scope={
                "run_id": " run-1 ",
                "parent_run_id": " parent-run-1 ",
                "child_run_id": " child-run-1 ",
                "scheduler_run_id": " scheduler-run-1 ",
                "run_kind": " scheduler ",
                "status": " running ",
                "trace_count": 2,
                "latest_trace_event": {"summary": "调度执行中"},
                "child_merge_intent": " risk_review ",
                "child_merge_entities": ["交易", "风险"],
                "child_merge_entity_count": 2,
                "child_merge_focus_count": 3,
                "child_merge_action_count": 1,
                "child_merge_primary_entities": ["交易"],
                "child_merge_conclusion": " 建议复核 ",
                "child_merge_section_source": " merged_sections ",
                "child_merge_section_ids": ["merged_entities"],
                "child_merge_section_counts": {"merged_entities": 2},
            }
        )

        self.assertEqual(run["run_id"], "run-1")
        self.assertEqual(run["parent_run_id"], "parent-run-1")
        self.assertEqual(run["child_run_id"], "child-run-1")
        self.assertEqual(run["child_display_id"], "child-run-1")
        self.assertEqual(run["scheduler_run_id"], "scheduler-run-1")
        self.assertEqual(run["run_kind"], "scheduler")
        self.assertEqual(run["status"], "running")
        self.assertEqual(run["trace_count"], 2)
        self.assertEqual(run["latest_trace_event"], {"summary": "调度执行中"})
        self.assertEqual(run["child_merge_intent"], "risk_review")
        self.assertEqual(run["child_merge_entities"], ["交易", "风险"])
        self.assertEqual(run["child_merge_entity_count"], 2)
        self.assertEqual(run["child_merge_focus_count"], 3)
        self.assertEqual(run["child_merge_action_count"], 1)
        self.assertEqual(run["child_merge_primary_entities"], ["交易"])
        self.assertEqual(run["child_merge_conclusion"], "建议复核")
        self.assertEqual(run["child_merge_section_source"], "merged_sections")
        self.assertEqual(run["child_merge_section_ids"], ["merged_entities"])
        self.assertEqual(run["child_merge_section_counts"], {"merged_entities": 2})

    def test_governance_overview_contract_uses_run_state_builder(self):
        self.assertIs(
            RuntimeSurfaceService._build_governance_overview_contract.__globals__[
                "GovernanceOverviewRunStateBuilder"
            ],
            GovernanceOverviewRunStateBuilder,
        )

    def test_provider_catalog_builder_keeps_model_provider_resolution_isolated(self):
        catalog = ProviderCatalogBuilder.build_catalog(
            all_models=[
                {
                    "name": "doubao",
                    "provider": "volcengine-ark",
                    "provider_label": "火山引擎 Ark",
                    "type": "cloud",
                    "configured": True,
                    "available": True,
                    "source": "env",
                    "actual_model": "doubao-seed-2-0-mini-260215",
                },
                {
                    "name": "llama3.1",
                    "provider": "ollama",
                    "provider_label": "Ollama",
                    "type": "local",
                    "configured": False,
                    "available": False,
                    "source": "builtin",
                },
            ],
            effective_config={"enabled_providers": ["volcengine-ark"]},
            override_config={"enabled_providers": ["volcengine-ark"]},
            config_layers={"editable_keys": ["enabled_providers"]},
        )

        self.assertEqual([item["name"] for item in catalog["models"]], ["doubao"])
        self.assertEqual({item["provider_id"] for item in catalog["providers"]}, {"volcengine-ark", "ollama"})
        self.assertEqual(catalog["providers"][0]["enabled_source"], "override")
        self.assertEqual(catalog["providers"][0]["model_sources"], ["env"])
        self.assertEqual(catalog["providers"][0]["actual_models"], ["doubao-seed-2-0-mini-260215"])
        self.assertEqual(catalog["providers"][1]["enabled"], False)
        self.assertEqual(
            catalog["config_layers"]["provider_resolution"],
            {
                "available_provider_ids": ["ollama", "volcengine-ark"],
                "enabled_provider_ids": ["volcengine-ark"],
                "disabled_provider_ids": ["ollama"],
                "default_behavior": "override_selected",
            },
        )

    def test_recovery_alignment_treats_resolved_approval_as_state_gated(self):
        summary = RuntimeRecoveryContractBuilder.build_recovery_alignment_summary(
            expected_entrypoints=[
                {
                    "method": "submit_approval",
                    "mode": "approved",
                    "available": True,
                    "recovery_reason": "ready_via_registry",
                }
            ],
            current_entrypoints=[
                {
                    "method": "submit_approval",
                    "mode": "approved",
                    "available": False,
                    "blocked_reason": "approval_already_resolved",
                    "approval_status": "denied",
                }
            ],
        )

        entry = summary["entries"][0]
        self.assertEqual(summary["current_alignment_status"], "aligned")
        self.assertEqual(entry["current_alignment"], "state_gated")
        self.assertEqual(entry["current_blocked_reason"], "approval_already_resolved")

    @patch("backend.services.runtime_surface_service.get_model_router")
    @patch("backend.services.runtime_surface_service.get_runtime_surface_config_service")
    @patch("backend.services.runtime_surface_service.get_capability_profile_service")
    @patch("backend.services.runtime_surface_service.get_agent_memory_service")
    @patch("backend.services.runtime_surface_service.get_subagent_runtime_service")
    @patch("backend.services.runtime_surface_service.get_agent_hook_service")
    @patch("backend.services.runtime_surface_service.get_mcp_runtime_service")
    @patch("backend.services.runtime_surface_service.get_skill_runtime_service")
    @patch("backend.services.runtime_surface_service.get_tool_runtime_service")
    @patch("backend.services.runtime_surface_service.get_runtime_contract_gate_service")
    @patch("backend.services.runtime_surface_service.get_self_improvement_ledger_service")
    @patch("backend.services.runtime_surface_service.get_query_control_plane_service")
    @patch("backend.services.runtime_surface_service.get_embedded_workspace_store")
    @patch("backend.services.runtime_surface_service.get_default_embedded_runtime_factory")
    def test_runtime_surface_binds_worker_ownership_enablement_config_to_factory(
        self,
        mock_runtime_factory_getter,
        mock_workspace_store_factory,
        mock_query_control_factory,
        mock_self_improvement_factory,
        mock_contract_gate_factory,
        mock_tool_runtime_factory,
        mock_skill_runtime_factory,
        mock_mcp_runtime_factory,
        mock_hook_factory,
        mock_subagent_factory,
        mock_memory_factory,
        mock_capability_factory,
        mock_config_factory,
        mock_router_factory,
    ):
        effective_config = {
            "auth_mode": "demo_guest",
            "default_model": "doubao",
            "enabled_providers": [],
            "failover_thresholds": {"medium": 0.2, "high": 0.4},
            "worker_ownership_production_enablement_config": {
                "source_kind": "runtime_config",
                "config_id": "runtime-surface-prod-enable-001",
            },
        }
        mock_config_factory.return_value.get_effective_config.return_value = effective_config
        mock_config_factory.return_value.load_overrides.return_value = {
            "worker_ownership_production_enablement_config": dict(
                effective_config["worker_ownership_production_enablement_config"]
            )
        }
        mock_config_factory.return_value.get_config_layers.return_value = {
            "defaults": {},
            "overrides": mock_config_factory.return_value.load_overrides.return_value,
            "effective": effective_config,
            "editable_keys": ["worker_ownership_production_enablement_config"],
        }
        mock_router_factory.return_value.list_available_models.return_value = {}
        mock_workspace_store_factory.return_value.describe_backend.return_value = {}
        mock_runtime_factory = unittest.mock.Mock()
        mock_runtime_factory.configure_worker_ownership_production_enablement_config.return_value = (
            mock_runtime_factory
        )
        mock_runtime_factory.build_runtime_contract.return_value = {
            "contract_version": "phase-ii-embedded-runtime-factory-v1",
            "default_runtime_profile": {},
            "default_recovery_capabilities": {},
            "workspace_backend": {},
            "persistence_interface": {},
            "production_recovery_gate": {},
            "worker_ownership": {
                "production_enablement_runtime_config_consumer": {
                    "overall_status": "blocked",
                    "config_id": "runtime-surface-prod-enable-001",
                    "will_enable_production_default": False,
                    "executes_lock": False,
                    "starts_background_worker": False,
                    "runs_recovery_auto_claim": False,
                }
            },
        }
        mock_runtime_factory_getter.return_value = mock_runtime_factory
        mock_mcp_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_skill_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_tool_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_tool_runtime_factory.return_value.build_adapter_health_contract.return_value = {}
        mock_capability_factory.return_value.build_runtime_contract.return_value = {}
        mock_memory_factory.return_value.build_runtime_contract.return_value = {}
        mock_subagent_factory.return_value.build_runtime_contract.return_value = {}
        mock_hook_factory.return_value.build_runtime_contract.return_value = {}
        mock_contract_gate_factory.return_value.build_runtime_contract.return_value = {}
        mock_self_improvement_factory.return_value.build_runtime_contract.return_value = {}
        mock_query_control_factory.return_value.build_runtime_contract.return_value = {}

        service = RuntimeSurfaceService()
        profile = service.get_runtime_profile()

        mock_runtime_factory.configure_worker_ownership_production_enablement_config.assert_called_once_with(
            effective_config["worker_ownership_production_enablement_config"]
        )
        consumer = profile["embedded_runtime_factory"]["worker_ownership"][
            "production_enablement_runtime_config_consumer"
        ]
        self.assertEqual(consumer["config_id"], "runtime-surface-prod-enable-001")
        self.assertFalse(consumer["will_enable_production_default"])

    @patch("backend.services.runtime_surface_service.get_model_router")
    @patch("backend.services.runtime_surface_service.get_runtime_surface_config_service")
    @patch("backend.services.runtime_surface_service.get_capability_profile_service")
    @patch("backend.services.runtime_surface_service.get_agent_memory_service")
    @patch("backend.services.runtime_surface_service.get_subagent_runtime_service")
    @patch("backend.services.runtime_surface_service.get_agent_hook_service")
    @patch("backend.services.runtime_surface_service.get_mcp_runtime_service")
    @patch("backend.services.runtime_surface_service.get_skill_runtime_service")
    @patch("backend.services.runtime_surface_service.get_tool_runtime_service")
    @patch("backend.services.runtime_surface_service.get_runtime_contract_gate_service")
    @patch("backend.services.runtime_surface_service.get_self_improvement_ledger_service")
    @patch("backend.services.runtime_surface_service.get_query_control_plane_service")
    @patch("backend.services.runtime_surface_service.get_embedded_workspace_store")
    def test_runtime_profile_includes_models_and_providers(self, mock_workspace_store_factory, mock_query_control_factory, mock_self_improvement_factory, mock_contract_gate_factory, mock_tool_runtime_factory, mock_skill_runtime_factory, mock_mcp_runtime_factory, mock_hook_factory, mock_subagent_factory, mock_memory_factory, mock_capability_factory, mock_config_factory, mock_router_factory):
        mock_router = mock_router_factory.return_value
        mock_workspace_store_factory.return_value.describe_backend.return_value = {
            "backend_kind": "sqlalchemy",
            "durable": True,
            "backend_mode": "strict_sql",
            "operation_fallback_allowed": False,
            "fallback_active": False,
            "fallback_reason": "",
            "last_error": "",
        }
        mock_config_factory.return_value.get_effective_config.return_value = {
            "auth_mode": "demo_guest",
            "default_model": "doubao",
            "enabled_providers": ["volcengine-ark"],
            "failover_thresholds": {"medium": 0.2, "high": 0.4},
        }
        mock_config_factory.return_value.get_config_layers.return_value = {
            "defaults": {"auth_mode": "demo_guest", "default_model": "doubao", "enabled_providers": [], "failover_thresholds": {"medium": 0.2, "high": 0.4}},
            "overrides": {"enabled_providers": ["volcengine-ark"]},
            "effective": {"auth_mode": "demo_guest", "default_model": "doubao", "enabled_providers": ["volcengine-ark"], "failover_thresholds": {"medium": 0.2, "high": 0.4}},
            "override_path": ".myagent/runtime_surface.json",
            "editable_keys": ["auth_mode", "default_model", "enabled_providers", "failover_thresholds"],
        }
        mock_capability_factory.return_value.build_runtime_contract.return_value = {
            "identity_summary": "主协调智能体",
            "operating_principles": ["规则1"],
            "available_capabilities": ["天气查询"],
            "limited_capabilities": ["交通路线检索"],
            "enabled_mcp_capabilities": [],
            "registered_tools": [],
        }
        mock_memory_factory.return_value.build_runtime_contract.return_value = {
            "contract_version": "phase-b-memory-entry-v1",
            "loaded_layers": [{"name": "global", "path": "GLOBAL_AGENT.md"}],
            "missing_layers": [{"name": "local", "path": "PROJECT_AGENT.local.md"}],
            "memory_entries": [{"memory_id": "memory:global", "retrieval_reason": "loaded_layer:global"}],
            "layer_order": ["global", "project", "local", "org_policy"],
            "active": True,
        }
        mock_skill_runtime_factory.return_value.build_runtime_contract.return_value = {
            "contract_version": "phase-b-skill-definition-v1",
            "total_definitions": 1,
            "definitions": [{"skill_id": 1, "name": "Frontend UI Review"}],
        }
        mock_subagent_factory.return_value.build_runtime_contract.return_value = {
            "total_profiles": 1,
            "profiles": [{"name": "planner"}],
        }
        mock_hook_factory.return_value.build_runtime_contract.return_value = {
            "enabled_hooks": ["pre_tool_use", "post_tool_use"],
            "governance_model": "minimal",
        }
        mock_tool_runtime_factory.return_value.build_runtime_contract.return_value = {
            "contract_version": "phase-b-tool-runtime-v1",
            "total_tools": 2,
            "base_tool_count": 1,
            "langchain_tool_count": 1,
            "tool_spec_count": 1,
            "doubao_definition_count": 1,
            "mcp_capability_count": 1,
            "high_risk_tool_count": 1,
            "tools": [],
        }
        mock_tool_runtime_factory.return_value.build_adapter_health_contract.return_value = {
            "contract_version": "phase-b-adapter-health-v1",
            "overall_status": "healthy",
            "adapter_count": 3,
            "unavailable_count": 0,
            "adapters": [],
        }
        mock_contract_gate_factory.return_value.build_runtime_contract.return_value = {
            "contract_version": "phase-f-runtime-contract-gate-v1",
            "available": True,
            "overall_status": "healthy",
            "check_count": 3,
            "failed_check_count": 0,
            "checks": [{"name": "embedded_sdk_event_payloads", "ok": True}],
        }
        mock_self_improvement_factory.return_value.build_runtime_contract.return_value = {
            "contract_version": "phase-g-self-improvement-ledger-v1",
            "overall_status": "ready",
            "record_types": ["learning", "error", "feature_request"],
            "tracked_sources": ["conversation", "error", "user_feedback", "quality_gate", "runtime_contract"],
            "promotion_targets": ["AGENTS.md", "docs", "system_prompt", "best_practice", "skill"],
            "governance_states": ["pending", "in_progress", "resolved", "promoted", "disabled", "rolled_back"],
            "quality_controls": ["review", "version_history", "duplicate_merge", "rollback", "restore"],
            "runtime_surface_enabled": True,
            "health_summary": {
                "total_learning_count": 0,
                "pending_learning_count": 0,
                "resolved_learning_count": 0,
                "promoted_learning_count": 0,
                "disabled_learning_count": 0,
                "rolled_back_learning_count": 0,
                "reviewed_learning_count": 0,
                "average_learning_quality_score": None,
                "total_error_count": 0,
                "pending_error_count": 0,
                "total_feature_request_count": 0,
                "pending_feature_request_count": 0,
                "attention_items": [],
            },
        }
        mock_query_control_factory.return_value.build_runtime_contract.return_value = {
            "contract_version": "phase-g-query-control-plane-v1",
            "overall_status": "design_ready",
            "lifecycle_stages": ["input_received", "context_assembly", "planning", "model_stream", "tool_decision", "tool_execution", "observation", "review", "final_output"],
            "execution_channels": ["main_chat", "embedded_sdk", "external_adapter", "subagent_lane"],
            "required_trace_events": ["input_received", "context_assembly", "planning", "model_stream", "tool_decision", "tool_execution", "observation", "review", "final_output"],
            "adapter_boundaries": {"provider_adapter": "normalizes model streams into runtime events"},
            "governance_requirements": ["traceable_lifecycle_stage"],
            "runtime_surface_enabled": True,
        }
        mock_mcp_runtime_factory.return_value.build_runtime_contract.return_value = {
            "contract_version": "phase-b-mcp-runtime-v1",
            "overall_status": "healthy",
            "capability_count": 2,
            "components": [
                {"component_id": "mcp_registry", "status": "healthy"},
                {"component_id": "mcp_session_manager", "status": "healthy"},
                {"component_id": "mcp_capability_router", "status": "healthy"},
                {"component_id": "mcp_audit", "status": "healthy"},
            ],
        }
        mock_router.list_available_models.return_value = {
            "doubao": {
                "name": "doubao",
                "display_name": "豆包",
                "provider": "volcengine-ark",
                "provider_label": "火山引擎 Ark",
                "type": "cloud",
                "configured": True,
                "available": True,
                "is_default": True,
                "base_url": "https://ark.example.com",
                "actual_model": "doubao-seed-2-0-mini-260215",
                "source": "env",
            },
            "llama3.1": {
                "name": "llama3.1",
                "display_name": "Llama 3.1",
                "provider": "ollama",
                "provider_label": "Ollama",
                "type": "local",
                "configured": False,
                "available": False,
                "is_default": False,
                "base_url": "http://localhost:11434",
                "source": "builtin",
            },
        }

        service = RuntimeSurfaceService()
        profile = service.get_runtime_profile()

        self.assertEqual(profile["agent_mode"], "general_demo")
        self.assertEqual(len(profile["models"]), 1)
        self.assertEqual({item["provider_id"] for item in profile["providers"]}, {"volcengine-ark", "ollama"})
        self.assertEqual(profile["providers"][0]["models"], ["doubao"])
        self.assertEqual(profile["capability_contract"]["identity_summary"], "主协调智能体")
        self.assertEqual(profile["config_layers"]["editable_keys"], ["auth_mode", "default_model", "enabled_providers", "failover_thresholds"])
        self.assertEqual(profile["failover_thresholds"]["medium"], 0.2)
        self.assertEqual(profile["failover_thresholds"]["high"], 0.4)
        self.assertIn("configured_model_count", profile["providers"][0])
        self.assertEqual(profile["config_layers"]["provider_resolution"]["enabled_provider_ids"], ["volcengine-ark"])
        self.assertEqual(profile["providers"][1]["enabled"], False)
        self.assertEqual(profile["providers"][0]["model_sources"], ["env"])
        self.assertEqual(profile["providers"][0]["actual_models"], ["doubao-seed-2-0-mini-260215"])
        self.assertIn("business_auth_description", profile["auth_mode_contract"])
        self.assertTrue(profile["memory_contract"]["active"])
        self.assertEqual(profile["memory_contract"]["contract_version"], "phase-b-memory-entry-v1")
        self.assertEqual(profile["memory_contract"]["loaded_layers"][0]["name"], "global")
        self.assertEqual(profile["skill_contract"]["contract_version"], "phase-b-skill-definition-v1")
        self.assertEqual(profile["skill_contract"]["total_definitions"], 1)
        self.assertEqual(profile["subagent_contract"]["total_profiles"], 1)
        self.assertIn("pre_tool_use", profile["hook_contract"]["enabled_hooks"])
        self.assertIn("command_contract", profile)
        self.assertGreaterEqual(profile["command_contract"]["total_commands"], 10)
        self.assertEqual(profile["embedded_runtime_boundaries"]["contract_version"], "phase-ii-embedded-runtime-boundaries-v1")
        self.assertTrue(profile["embedded_runtime_boundaries"]["connected"])
        self.assertIn("_runs", profile["embedded_runtime_boundaries"]["volatile_runtime_state"])
        self.assertIn("run_workspace_snapshot", profile["embedded_runtime_boundaries"]["persistence_seams"])
        self.assertEqual(profile["embedded_runtime_boundaries"]["delegate_preflight_status"], "relationship_only")
        self.assertFalse(profile["embedded_runtime_boundaries"]["real_child_executor_ready"])
        self.assertFalse(profile["embedded_runtime_boundaries"]["delegate_promotion_ready"])
        self.assertEqual(profile["embedded_runtime_boundaries"]["delegate_executor_binding_status"], "blocked")
        self.assertIn("child_context_budget_defined", profile["embedded_runtime_boundaries"]["delegate_executor_binding_blockers"])
        self.assertEqual(profile["embedded_runtime_boundaries"]["delegate_recommended_next_step"], "keep_relationship_only")
        self.assertEqual(profile["embedded_runtime_boundaries"]["delegate_gate_status"], "blocked")
        self.assertFalse(profile["embedded_runtime_boundaries"]["delegate_gate_allowed"])
        self.assertEqual(
            profile["embedded_runtime_boundaries"]["child_executor_backend_registry"]["contract_version"],
            "phase-ii-child-executor-backend-registry-v1",
        )
        self.assertEqual(
            profile["child_executor_backend_registry"]["overall_status"],
            "relationship_only",
        )
        self.assertEqual(
            profile["child_executor_backend_registry"]["ready_backend_count"],
            0,
        )
        self.assertEqual(profile["child_executor_promotion_gate"]["gate_status"], "blocked")
        self.assertFalse(profile["child_executor_promotion_gate"]["allowed"])
        self.assertEqual(
            profile["child_executor_promotion_gate"]["child_executor_execution_prerequisites"]["overall_status"],
            "blocked",
        )
        self.assertFalse(
            profile["child_executor_promotion_gate"]["child_executor_execution_prerequisites"]["ready"]
        )
        self.assertEqual(
            profile["child_executor_dispatch_contract"]["contract_version"],
            "phase-ii-child-executor-dispatch-v1",
        )
        self.assertEqual(profile["child_executor_dispatch_contract"]["overall_status"], "blocked")
        self.assertFalse(profile["child_executor_dispatch_contract"]["dispatch_ready"])
        self.assertFalse(profile["child_executor_dispatch_contract"]["will_dispatch"])
        self.assertIn("worker_backend_dispatch_ready", profile["child_executor_dispatch_contract"]["blockers"])
        self.assertEqual(
            profile["embedded_runtime_boundaries"]["child_executor_dispatch_contract"]["overall_status"],
            "blocked",
        )
        self.assertFalse(profile["embedded_runtime_boundaries"]["delegate_dispatch_ready"])
        self.assertEqual(
            profile["governance_overview"]["child_executor_dispatch_contract"]["overall_status"],
            "blocked",
        )
        self.assertFalse(profile["governance_overview"]["child_executor_dispatch_contract"]["dispatch_ready"])
        self.assertEqual(profile["embedded_runtime_boundaries"]["delegate_route_status"], "blocked")
        self.assertEqual(profile["embedded_runtime_boundaries"]["delegate_route_executor_path"], "")
        self.assertEqual(profile["embedded_runtime_boundaries"]["delegate_binding_status"], "blocked")
        self.assertEqual(profile["embedded_runtime_boundaries"]["delegate_binding_id"], "")
        self.assertEqual(profile["embedded_runtime_boundaries"]["delegate_stub_status"], "blocked")
        self.assertEqual(profile["embedded_runtime_boundaries"]["delegate_stub_binding_id"], "")
        self.assertEqual(profile["embedded_runtime_boundaries"]["delegate_execution_status"], "blocked")
        self.assertEqual(profile["embedded_runtime_boundaries"]["delegate_execution_binding_id"], "")
        self.assertEqual(profile["embedded_runtime_boundaries"]["delegate_execution_output_summary"], "")
        self.assertEqual(profile["embedded_runtime_boundaries"]["delegate_execution_output_envelope"], {})
        self.assertEqual(profile["embedded_runtime_boundaries"]["delegate_merge_status"], "blocked")
        self.assertEqual(profile["embedded_runtime_boundaries"]["delegate_merge_section_count"], 0)
        self.assertEqual(profile["embedded_runtime_boundaries"]["delegate_replay_record_count"], 0)
        self.assertEqual(profile["embedded_runtime_boundaries"]["delegate_replay_records"], [])
        self.assertEqual(profile["embedded_runtime_boundaries"]["delegate_artifact_summary"]["record_count"], 0)
        self.assertIn("child_context_budget_defined", profile["embedded_runtime_boundaries"]["delegate_missing_requirements"])
        self.assertEqual(profile["embedded_runtime_boundaries"]["workspace_backend"]["backend_kind"], "sqlalchemy")
        self.assertTrue(profile["embedded_runtime_boundaries"]["workspace_backend"]["durable"])
        self.assertEqual(profile["embedded_runtime_boundaries"]["workspace_backend"]["backend_mode"], "strict_sql")
        self.assertFalse(profile["embedded_runtime_boundaries"]["workspace_backend"]["operation_fallback_allowed"])
        self.assertEqual(
            profile["embedded_runtime_boundaries"]["persistence_interface"]["contract_version"],
            "phase-ii-embedded-sdk-persistence-interface-v1",
        )
        self.assertEqual(
            profile["embedded_runtime_boundaries"]["persistence_interface"]["persistence_posture"],
            "durable_ready",
        )
        self.assertEqual(profile["embedded_runtime_factory"]["contract_version"], "phase-ii-embedded-runtime-factory-v1")
        self.assertTrue(profile["embedded_runtime_factory"]["shared_default_runtime"])
        self.assertEqual(profile["embedded_runtime_factory"]["default_runtime_profile"]["db_mode"], "sqlite")
        self.assertEqual(profile["embedded_runtime_factory"]["default_runtime_profile"]["db_mode_source"], "default")
        self.assertEqual(profile["embedded_runtime_factory"]["default_runtime_profile"]["embedded_workspace_store_mode"], "strict_sql")
        self.assertEqual(profile["embedded_runtime_factory"]["default_runtime_profile"]["embedded_workspace_store_mode_source"], "derived_from_db_mode")
        self.assertEqual(profile["embedded_runtime_factory"]["default_runtime_profile"]["default_runtime_mode"], "durable_default")
        self.assertEqual(profile["embedded_runtime_factory"]["default_runtime_profile"]["persistence_posture"], "durable_ready")
        self.assertEqual(profile["embedded_runtime_factory"]["default_runtime_profile"]["workspace_strategy_rule"], "memory_only_if_db_mode_memory_else_strict_sql")
        self.assertTrue(profile["embedded_runtime_factory"]["default_runtime_profile"]["durable_by_default"])
        self.assertEqual(profile["embedded_runtime_factory"]["default_runtime_profile"]["recommended_bootstrap"], "EmbeddedRuntimeFactory")
        self.assertEqual(profile["embedded_runtime_factory"]["default_recovery_capabilities"]["recovery_mode"], "registry_backed")
        self.assertTrue(profile["embedded_runtime_factory"]["default_recovery_capabilities"]["requires_durable_workspace"])
        self.assertEqual(profile["default_runtime_recovery"]["contract_version"], "phase-ii-default-runtime-recovery-v1")
        self.assertEqual(profile["default_runtime_recovery"]["recovery_mode"], "registry_backed")
        self.assertEqual(profile["default_runtime_recovery"]["recovery_posture"], "cross_process_candidate")
        self.assertEqual(profile["default_runtime_recovery"]["persistence_posture"], "durable_ready")
        self.assertEqual(
            profile["default_runtime_recovery"]["persistence_interface"]["contract_version"],
            "phase-ii-embedded-sdk-persistence-interface-v1",
        )
        self.assertTrue(profile["default_runtime_recovery"]["expected_cross_process_candidate"])
        default_recovery_entrypoints = {
            (item["method"], item.get("mode") or ""): item
            for item in profile["default_runtime_recovery"]["recovery_entrypoints"]
        }
        self.assertTrue(default_recovery_entrypoints[("submit_approval", "approved")]["available"])
        self.assertEqual(
            default_recovery_entrypoints[("submit_approval", "approved")]["recovery_reason"],
            "ready_via_registry",
        )
        self.assertTrue(default_recovery_entrypoints[("resume_run", "continue_loop")]["available"])
        self.assertEqual(
            default_recovery_entrypoints[("resume_run", "continue_loop")]["recovery_reason"],
            "ready_via_registry",
        )
        self.assertEqual(
            profile["embedded_runtime_factory"]["default_runtime_profile"]["configurable_bootstrap_knobs"],
            ["DB_MODE", "EMBEDDED_WORKSPACE_STORE_MODE", "WORKER_OWNERSHIP_STORE_MODE"],
        )
        self.assertEqual(
            profile["embedded_runtime_factory"]["default_runtime_profile"]["hot_reloadable_bootstrap_knobs"],
            ["EMBEDDED_WORKSPACE_STORE_MODE", "WORKER_OWNERSHIP_STORE_MODE"],
        )
        self.assertEqual(
            profile["embedded_runtime_factory"]["default_runtime_profile"]["restart_required_bootstrap_knobs"],
            ["DB_MODE"],
        )
        self.assertEqual(profile["embedded_runtime_bootstrap"]["contract_version"], "phase-ii-embedded-runtime-factory-v1")
        self.assertEqual(
            profile["embedded_runtime_bootstrap"]["default_runtime_profile"]["default_runtime_mode"],
            "durable_default",
        )

    @patch("backend.services.runtime_surface_service.get_default_embedded_runtime_factory")
    @patch("backend.services.runtime_surface_service.get_model_router")
    @patch("backend.services.runtime_surface_service.get_runtime_surface_config_service")
    @patch("backend.services.runtime_surface_service.get_capability_profile_service")
    @patch("backend.services.runtime_surface_service.get_agent_memory_service")
    @patch("backend.services.runtime_surface_service.get_subagent_runtime_service")
    @patch("backend.services.runtime_surface_service.get_agent_hook_service")
    @patch("backend.services.runtime_surface_service.get_mcp_runtime_service")
    @patch("backend.services.runtime_surface_service.get_skill_runtime_service")
    @patch("backend.services.runtime_surface_service.get_tool_runtime_service")
    @patch("backend.services.runtime_surface_service.get_runtime_contract_gate_service")
    @patch("backend.services.runtime_surface_service.get_self_improvement_ledger_service")
    @patch("backend.services.runtime_surface_service.get_query_control_plane_service")
    @patch("backend.services.runtime_surface_service.get_embedded_workspace_store")
    def test_runtime_surface_uses_default_runtime_factory_for_sdk_reader(
        self,
        mock_workspace_store_factory,
        mock_query_control_factory,
        mock_self_improvement_factory,
        mock_contract_gate_factory,
        mock_tool_runtime_factory,
        mock_skill_runtime_factory,
        mock_mcp_runtime_factory,
        mock_hook_factory,
        mock_subagent_factory,
        mock_memory_factory,
        mock_capability_factory,
        mock_config_factory,
        mock_router_factory,
        mock_factory,
    ):
        stub_factory = unittest.mock.Mock()
        stub_reader = unittest.mock.Mock()
        stub_reader.list_child_executor_outputs.return_value = {"contract_version": "phase-ii-child-executor-replay-v1", "record_count": 0, "records": []}
        stub_factory.create_sdk.return_value = stub_reader
        mock_factory.return_value = stub_factory
        mock_workspace_store_factory.return_value.describe_backend.return_value = {
            "backend_kind": "sqlalchemy",
            "durable": True,
            "backend_mode": "strict_sql",
            "operation_fallback_allowed": False,
            "fallback_active": False,
            "fallback_reason": "",
            "last_error": "",
        }
        mock_router_factory.return_value.list_available_models.return_value = {}
        mock_config_factory.return_value.get_effective_config.return_value = {
            "auth_mode": "demo_guest",
            "default_model": "doubao",
            "enabled_providers": [],
            "failover_thresholds": {"medium": 0.2, "high": 0.4},
        }
        mock_config_factory.return_value.get_config_layers.return_value = {
            "defaults": {},
            "overrides": {},
            "effective": {},
            "editable_keys": [],
        }
        mock_capability_factory.return_value.build_runtime_contract.return_value = {}
        mock_memory_factory.return_value.build_runtime_contract.return_value = {"active": False, "loaded_layers": [], "missing_layers": [], "memory_entries": [], "layer_order": []}
        mock_subagent_factory.return_value.build_runtime_contract.return_value = {}
        mock_hook_factory.return_value.build_runtime_contract.return_value = {}
        mock_mcp_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_skill_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_tool_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_tool_runtime_factory.return_value.build_adapter_health_contract.return_value = {}
        mock_contract_gate_factory.return_value.build_runtime_contract.return_value = {}
        mock_self_improvement_factory.return_value.build_runtime_contract.return_value = {}
        mock_query_control_factory.return_value.build_runtime_contract.return_value = {}

        service = RuntimeSurfaceService()
        service.get_child_executor_output_replay(parent_run_id="run-main-01")

        mock_factory.assert_called()
        stub_factory.create_sdk.assert_called()
        stub_reader.list_child_executor_outputs.assert_called_once_with("run-main-01")

    @patch("backend.services.runtime_surface_service.get_model_router")
    @patch("backend.services.runtime_surface_service.get_runtime_surface_config_service")
    @patch("backend.services.runtime_surface_service.get_capability_profile_service")
    @patch("backend.services.runtime_surface_service.get_agent_memory_service")
    @patch("backend.services.runtime_surface_service.get_subagent_runtime_service")
    @patch("backend.services.runtime_surface_service.get_agent_hook_service")
    @patch("backend.services.runtime_surface_service.get_mcp_runtime_service")
    @patch("backend.services.runtime_surface_service.get_skill_runtime_service")
    @patch("backend.services.runtime_surface_service.get_tool_runtime_service")
    @patch("backend.services.runtime_surface_service.get_runtime_contract_gate_service")
    @patch("backend.services.runtime_surface_service.get_self_improvement_ledger_service")
    @patch("backend.services.runtime_surface_service.get_query_control_plane_service")
    def test_update_runtime_profile_validates_default_model(self, mock_query_control_factory, mock_self_improvement_factory, mock_contract_gate_factory, mock_tool_runtime_factory, mock_skill_runtime_factory, mock_mcp_runtime_factory, mock_hook_factory, mock_subagent_factory, mock_memory_factory, mock_capability_factory, mock_config_factory, mock_router_factory):
        mock_router = mock_router_factory.return_value
        mock_config = mock_config_factory.return_value
        mock_capability_factory.return_value.build_runtime_contract.return_value = {}
        mock_memory_factory.return_value.build_runtime_contract.return_value = {
            "loaded_layers": [],
            "missing_layers": [],
            "layer_order": [],
            "active": False,
        }
        mock_subagent_factory.return_value.build_runtime_contract.return_value = {
            "total_profiles": 0,
            "profiles": [],
        }
        mock_hook_factory.return_value.build_runtime_contract.return_value = {
            "enabled_hooks": [],
            "governance_model": "minimal",
        }
        mock_tool_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_tool_runtime_factory.return_value.build_adapter_health_contract.return_value = {}
        mock_contract_gate_factory.return_value.build_runtime_contract.return_value = {}
        mock_self_improvement_factory.return_value.build_runtime_contract.return_value = {}
        mock_query_control_factory.return_value.build_runtime_contract.return_value = {}
        mock_skill_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_mcp_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_config.get_effective_config.return_value = {
            "auth_mode": "demo_guest",
            "default_model": "doubao",
            "enabled_providers": [],
            "failover_thresholds": {"medium": 0.2, "high": 0.4},
        }
        mock_config.get_config_layers.return_value = {
            "defaults": {"auth_mode": "demo_guest", "default_model": "doubao", "enabled_providers": [], "failover_thresholds": {"medium": 0.2, "high": 0.4}},
            "overrides": {},
            "effective": {"auth_mode": "demo_guest", "default_model": "doubao", "enabled_providers": [], "failover_thresholds": {"medium": 0.2, "high": 0.4}},
            "override_path": ".myagent/runtime_surface.json",
            "editable_keys": ["auth_mode", "default_model", "enabled_providers", "failover_thresholds"],
        }
        mock_router.list_available_models.return_value = {
            "doubao": {
                "name": "doubao",
                "display_name": "豆包",
                "provider": "volcengine-ark",
                "provider_label": "火山引擎 Ark",
                "type": "cloud",
                "configured": True,
                "available": True,
                "is_default": True,
            },
            "llama3.1": {
                "name": "llama3.1",
                "display_name": "Llama 3.1",
                "provider": "ollama",
                "provider_label": "Ollama",
                "type": "local",
                "configured": True,
                "available": True,
                "is_default": False,
            },
        }

        service = RuntimeSurfaceService()
        with self.assertRaises(ValueError):
            service.update_runtime_profile({"default_model": "not-found"})

        with self.assertRaises(ValueError):
            service.update_runtime_profile({"enabled_providers": ["ollama"]})

        with self.assertRaises(ValueError):
            service.update_runtime_profile({"enabled_providers": ["unknown-provider"]})

        service.update_runtime_profile({"default_model": "doubao"})
        mock_config.update_overrides.assert_called_once_with({"default_model": "doubao"})

    @patch("backend.services.runtime_surface_service.set_embedded_workspace_store_mode")
    @patch("backend.services.runtime_surface_service.get_embedded_workspace_store")
    @patch("backend.services.runtime_surface_service.get_default_embedded_runtime_factory")
    @patch("backend.services.runtime_surface_service.get_model_router")
    @patch("backend.services.runtime_surface_service.get_runtime_surface_config_service")
    @patch("backend.services.runtime_surface_service.get_capability_profile_service")
    @patch("backend.services.runtime_surface_service.get_agent_memory_service")
    @patch("backend.services.runtime_surface_service.get_subagent_runtime_service")
    @patch("backend.services.runtime_surface_service.get_agent_hook_service")
    @patch("backend.services.runtime_surface_service.get_mcp_runtime_service")
    @patch("backend.services.runtime_surface_service.get_skill_runtime_service")
    @patch("backend.services.runtime_surface_service.get_tool_runtime_service")
    @patch("backend.services.runtime_surface_service.get_runtime_contract_gate_service")
    @patch("backend.services.runtime_surface_service.get_self_improvement_ledger_service")
    @patch("backend.services.runtime_surface_service.get_query_control_plane_service")
    def test_update_runtime_profile_can_apply_embedded_workspace_store_mode(
        self,
        mock_query_control_factory,
        mock_self_improvement_factory,
        mock_contract_gate_factory,
        mock_tool_runtime_factory,
        mock_skill_runtime_factory,
        mock_mcp_runtime_factory,
        mock_hook_factory,
        mock_subagent_factory,
        mock_memory_factory,
        mock_capability_factory,
        mock_config_factory,
        mock_router_factory,
        mock_runtime_factory_getter,
        mock_workspace_store_getter,
        mock_set_mode,
    ):
        mock_router_factory.return_value.list_available_models.return_value = {}
        mock_config = mock_config_factory.return_value
        mock_config.get_effective_config.side_effect = [
            {
                "auth_mode": "demo_guest",
                "default_model": "doubao",
                "enabled_providers": [],
                "embedded_workspace_store_mode": "strict_sql",
                "failover_thresholds": {"medium": 0.2, "high": 0.4},
            },
            {
                "auth_mode": "demo_guest",
                "default_model": "doubao",
                "enabled_providers": [],
                "embedded_workspace_store_mode": "memory_only",
                "failover_thresholds": {"medium": 0.2, "high": 0.4},
            },
            {
                "auth_mode": "demo_guest",
                "default_model": "doubao",
                "enabled_providers": [],
                "embedded_workspace_store_mode": "memory_only",
                "failover_thresholds": {"medium": 0.2, "high": 0.4},
            },
            {
                "auth_mode": "demo_guest",
                "default_model": "doubao",
                "enabled_providers": [],
                "embedded_workspace_store_mode": "memory_only",
                "failover_thresholds": {"medium": 0.2, "high": 0.4},
            },
        ]
        mock_config.get_config_layers.return_value = {
            "defaults": {},
            "overrides": {},
            "effective": {},
            "editable_keys": [],
        }
        mock_capability_factory.return_value.build_runtime_contract.return_value = {}
        mock_memory_factory.return_value.build_runtime_contract.return_value = {"active": False, "loaded_layers": [], "missing_layers": [], "memory_entries": [], "layer_order": []}
        mock_subagent_factory.return_value.build_runtime_contract.return_value = {}
        mock_hook_factory.return_value.build_runtime_contract.return_value = {}
        mock_mcp_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_skill_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_tool_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_tool_runtime_factory.return_value.build_adapter_health_contract.return_value = {}
        mock_contract_gate_factory.return_value.build_runtime_contract.return_value = {}
        mock_self_improvement_factory.return_value.build_runtime_contract.return_value = {}
        mock_query_control_factory.return_value.build_runtime_contract.return_value = {}
        mock_workspace_store_getter.return_value.describe_backend.return_value = {
            "backend_kind": "sqlalchemy",
            "durable": True,
            "backend_mode": "memory_only",
            "operation_fallback_allowed": False,
            "fallback_active": False,
            "fallback_reason": "",
            "last_error": "",
        }
        mock_runtime_factory = unittest.mock.Mock()
        mock_runtime_factory.build_runtime_contract.return_value = {
            "contract_version": "phase-ii-embedded-runtime-factory-v1",
            "default_runtime_profile": {"embedded_workspace_store_mode": "memory_only"},
        }
        mock_runtime_factory_getter.return_value = mock_runtime_factory

        service = RuntimeSurfaceService()
        service.update_runtime_profile({"embedded_workspace_store_mode": "memory_only"})

        mock_config.update_overrides.assert_called_once_with({"embedded_workspace_store_mode": "memory_only"})
        self.assertEqual(mock_set_mode.call_args_list[-1].args, ("memory_only",))
        self.assertIs(service.runtime_factory, mock_runtime_factory)

    @patch("backend.services.runtime_surface_service.set_embedded_workspace_store_mode")
    @patch("backend.services.runtime_surface_service.get_embedded_workspace_store")
    @patch("backend.services.runtime_surface_service.get_default_embedded_runtime_factory")
    @patch("backend.services.runtime_surface_service.get_model_router")
    @patch("backend.services.runtime_surface_service.get_runtime_surface_config_service")
    @patch("backend.services.runtime_surface_service.get_capability_profile_service")
    @patch("backend.services.runtime_surface_service.get_agent_memory_service")
    @patch("backend.services.runtime_surface_service.get_subagent_runtime_service")
    @patch("backend.services.runtime_surface_service.get_agent_hook_service")
    @patch("backend.services.runtime_surface_service.get_mcp_runtime_service")
    @patch("backend.services.runtime_surface_service.get_skill_runtime_service")
    @patch("backend.services.runtime_surface_service.get_tool_runtime_service")
    @patch("backend.services.runtime_surface_service.get_runtime_contract_gate_service")
    @patch("backend.services.runtime_surface_service.get_self_improvement_ledger_service")
    @patch("backend.services.runtime_surface_service.get_query_control_plane_service")
    def test_update_embedded_runtime_bootstrap_can_apply_workspace_store_mode(
        self,
        mock_query_control_factory,
        mock_self_improvement_factory,
        mock_contract_gate_factory,
        mock_tool_runtime_factory,
        mock_skill_runtime_factory,
        mock_mcp_runtime_factory,
        mock_hook_factory,
        mock_subagent_factory,
        mock_memory_factory,
        mock_capability_factory,
        mock_config_factory,
        mock_router_factory,
        mock_runtime_factory_getter,
        mock_workspace_store_getter,
        mock_set_mode,
    ):
        mock_router_factory.return_value.list_available_models.return_value = {}
        mock_config = mock_config_factory.return_value
        mock_config.get_effective_config.side_effect = [
            {
                "auth_mode": "demo_guest",
                "default_model": "doubao",
                "enabled_providers": [],
                "embedded_workspace_store_mode": "strict_sql",
                "failover_thresholds": {"medium": 0.2, "high": 0.4},
            },
            {
                "auth_mode": "demo_guest",
                "default_model": "doubao",
                "enabled_providers": [],
                "embedded_workspace_store_mode": "memory_only",
                "failover_thresholds": {"medium": 0.2, "high": 0.4},
            },
        ]
        mock_config.get_config_layers.return_value = {
            "defaults": {},
            "overrides": {},
            "effective": {},
            "editable_keys": [],
        }
        mock_capability_factory.return_value.build_runtime_contract.return_value = {}
        mock_memory_factory.return_value.build_runtime_contract.return_value = {"active": False, "loaded_layers": [], "missing_layers": [], "memory_entries": [], "layer_order": []}
        mock_subagent_factory.return_value.build_runtime_contract.return_value = {}
        mock_hook_factory.return_value.build_runtime_contract.return_value = {}
        mock_mcp_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_skill_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_tool_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_tool_runtime_factory.return_value.build_adapter_health_contract.return_value = {}
        mock_contract_gate_factory.return_value.build_runtime_contract.return_value = {}
        mock_self_improvement_factory.return_value.build_runtime_contract.return_value = {}
        mock_query_control_factory.return_value.build_runtime_contract.return_value = {}
        mock_workspace_store_getter.return_value.describe_backend.return_value = {
            "backend_kind": "in_memory",
            "durable": False,
            "backend_mode": "memory_only",
            "operation_fallback_allowed": False,
            "fallback_active": False,
            "fallback_reason": "",
            "last_error": "",
        }
        initial_runtime_factory = unittest.mock.Mock()
        initial_runtime_factory.build_runtime_contract.return_value = {
            "contract_version": "phase-ii-embedded-runtime-factory-v1",
            "default_runtime_profile": {
                "embedded_workspace_store_mode": "strict_sql",
                "default_runtime_mode": "durable_default",
                "recovery_posture": "cross_process_candidate",
            },
            "default_recovery_expectation": {
                "cross_process_candidate": True,
                "cross_process_block_reason": "",
            },
            "workspace_backend": {
                "backend_kind": "sqlalchemy",
                "backend_mode": "strict_sql",
                "durable": True,
            },
        }
        updated_runtime_factory = unittest.mock.Mock()
        updated_runtime_factory.build_runtime_contract.return_value = {
            "contract_version": "phase-ii-embedded-runtime-factory-v1",
            "default_runtime_profile": {
                "embedded_workspace_store_mode": "memory_only",
                "default_runtime_mode": "memory_preview",
                "recovery_posture": "in_process_only",
            },
            "default_recovery_expectation": {
                "cross_process_candidate": False,
                "cross_process_block_reason": "workspace_backend_not_durable",
            },
            "workspace_backend": {
                "backend_kind": "in_memory",
                "backend_mode": "memory_only",
            },
        }
        mock_runtime_factory_getter.side_effect = [initial_runtime_factory, updated_runtime_factory]

        service = RuntimeSurfaceService()
        contract = service.update_embedded_runtime_bootstrap({"embedded_workspace_store_mode": "memory_only"})

        mock_config.update_overrides.assert_called_once_with({"embedded_workspace_store_mode": "memory_only"})
        self.assertEqual(mock_set_mode.call_args_list[-1].args, ("memory_only",))
        self.assertEqual(contract["default_runtime_profile"]["embedded_workspace_store_mode"], "memory_only")
        self.assertEqual(contract["update_status"], "applied")
        self.assertEqual(contract["applied_changes"], ["embedded_workspace_store_mode"])
        self.assertTrue(contract["hot_reload_applied"])
        self.assertFalse(contract["restart_required"])
        self.assertTrue(contract["post_update_verification"]["effective_change"])
        self.assertEqual(contract["post_update_verification"]["previous_runtime_mode"], "durable_default")
        self.assertEqual(contract["post_update_verification"]["current_runtime_mode"], "memory_preview")
        self.assertEqual(contract["post_update_verification"]["previous_recovery_posture"], "cross_process_candidate")
        self.assertEqual(contract["post_update_verification"]["current_recovery_posture"], "in_process_only")
        self.assertTrue(contract["post_update_verification"]["runtime_mode_changed"])
        self.assertTrue(contract["post_update_verification"]["recovery_posture_changed"])
        self.assertTrue(contract["post_update_verification"]["workspace_backend_changed"])
        self.assertTrue(contract["post_update_verification"]["durable_capability_changed"])
        self.assertTrue(contract["post_update_verification"]["previous_cross_process_candidate"])
        self.assertFalse(contract["post_update_verification"]["current_cross_process_candidate"])
        self.assertTrue(contract["post_update_verification"]["cross_process_candidate_changed"])
        self.assertEqual(contract["post_update_verification"]["current_cross_process_block_reason"], "workspace_backend_not_durable")
        self.assertTrue(contract["post_update_verification"]["previous_default_recovery_expectation"]["cross_process_candidate"])
        self.assertFalse(contract["post_update_verification"]["current_default_recovery_expectation"]["cross_process_candidate"])
        self.assertEqual(contract["post_update_verification"]["applied_workspace_store_mode"], "memory_only")
        self.assertTrue(contract["post_update_verification"]["workspace_mode_applied"])
        self.assertTrue(contract["post_update_verification"]["recovery_contract_aligned"])
        self.assertEqual(contract["post_update_verification"]["current_workspace_backend_kind"], "in_memory")

    @patch("backend.services.runtime_surface_service.get_model_router")
    @patch("backend.services.runtime_surface_service.get_runtime_surface_config_service")
    @patch("backend.services.runtime_surface_service.get_capability_profile_service")
    @patch("backend.services.runtime_surface_service.get_agent_memory_service")
    @patch("backend.services.runtime_surface_service.get_subagent_runtime_service")
    @patch("backend.services.runtime_surface_service.get_agent_hook_service")
    @patch("backend.services.runtime_surface_service.get_mcp_runtime_service")
    @patch("backend.services.runtime_surface_service.get_skill_runtime_service")
    @patch("backend.services.runtime_surface_service.get_tool_runtime_service")
    @patch("backend.services.runtime_surface_service.get_runtime_contract_gate_service")
    @patch("backend.services.runtime_surface_service.get_self_improvement_ledger_service")
    @patch("backend.services.runtime_surface_service.get_query_control_plane_service")
    def test_runtime_profile_passes_db_to_self_improvement_ledger(self, mock_query_control_factory, mock_self_improvement_factory, mock_contract_gate_factory, mock_tool_runtime_factory, mock_skill_runtime_factory, mock_mcp_runtime_factory, mock_hook_factory, mock_subagent_factory, mock_memory_factory, mock_capability_factory, mock_config_factory, mock_router_factory):
        db = object()
        mock_router_factory.return_value.list_available_models.return_value = {}
        mock_config_factory.return_value.get_effective_config.return_value = {
            "auth_mode": "demo_guest",
            "default_model": "doubao",
            "enabled_providers": [],
            "failover_thresholds": {"medium": 0.2, "high": 0.4},
        }
        mock_config_factory.return_value.get_config_layers.return_value = {
            "defaults": {},
            "overrides": {},
            "effective": {},
            "editable_keys": [],
        }
        mock_capability_factory.return_value.build_runtime_contract.return_value = {}
        mock_memory_factory.return_value.build_runtime_contract.return_value = {
            "contract_version": "phase-b-memory-entry-v1",
            "active": False,
            "loaded_layers": [],
            "missing_layers": [],
            "memory_entries": [],
            "layer_order": [],
        }
        mock_subagent_factory.return_value.build_runtime_contract.return_value = {}
        mock_hook_factory.return_value.build_runtime_contract.return_value = {}
        mock_mcp_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_skill_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_tool_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_tool_runtime_factory.return_value.build_adapter_health_contract.return_value = {}
        mock_contract_gate_factory.return_value.build_runtime_contract.return_value = {}
        mock_self_improvement_factory.return_value.build_runtime_contract.return_value = {
            "contract_version": "phase-g-self-improvement-ledger-v1",
            "overall_status": "attention_required",
            "health_summary": {"pending_learning_count": 1},
        }
        mock_query_control_factory.return_value.build_runtime_contract.return_value = {}

        profile = RuntimeSurfaceService().get_runtime_profile(db=db)

        mock_self_improvement_factory.return_value.build_runtime_contract.assert_called_once_with(db=db)
        self.assertEqual(profile["self_improvement_ledger"]["health_summary"]["pending_learning_count"], 1)

    @patch("backend.services.runtime_surface_service.SchedulerService")
    @patch("backend.services.runtime_surface_service.get_model_router")
    @patch("backend.services.runtime_surface_service.get_runtime_surface_config_service")
    @patch("backend.services.runtime_surface_service.get_capability_profile_service")
    @patch("backend.services.runtime_surface_service.get_agent_memory_service")
    @patch("backend.services.runtime_surface_service.get_subagent_runtime_service")
    @patch("backend.services.runtime_surface_service.get_agent_hook_service")
    @patch("backend.services.runtime_surface_service.get_mcp_runtime_service")
    @patch("backend.services.runtime_surface_service.get_skill_runtime_service")
    @patch("backend.services.runtime_surface_service.get_tool_runtime_service")
    @patch("backend.services.runtime_surface_service.get_runtime_contract_gate_service")
    @patch("backend.services.runtime_surface_service.get_self_improvement_ledger_service")
    @patch("backend.services.runtime_surface_service.get_query_control_plane_service")
    def test_runtime_profile_surfaces_latest_main_chat_query_control_trace(
        self,
        mock_query_control_factory,
        mock_self_improvement_factory,
        mock_contract_gate_factory,
        mock_tool_runtime_factory,
        mock_skill_runtime_factory,
        mock_mcp_runtime_factory,
        mock_hook_factory,
        mock_subagent_factory,
        mock_memory_factory,
        mock_capability_factory,
        mock_config_factory,
        mock_router_factory,
        mock_scheduler_cls,
    ):
        mock_router_factory.return_value.list_available_models.return_value = {}
        mock_config_factory.return_value.get_effective_config.return_value = {
            "auth_mode": "demo_guest",
            "default_model": "doubao",
            "enabled_providers": [],
            "failover_thresholds": {"medium": 0.2, "high": 0.4},
        }
        mock_config_factory.return_value.get_config_layers.return_value = {
            "defaults": {},
            "overrides": {},
            "effective": {},
            "editable_keys": [],
        }
        mock_capability_factory.return_value.build_runtime_contract.return_value = {}
        mock_memory_factory.return_value.build_runtime_contract.return_value = {"active": False, "loaded_layers": [], "missing_layers": [], "memory_entries": [], "layer_order": []}
        mock_subagent_factory.return_value.build_runtime_contract.return_value = {}
        mock_hook_factory.return_value.build_runtime_contract.return_value = {}
        mock_mcp_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_skill_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_tool_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_tool_runtime_factory.return_value.build_adapter_health_contract.return_value = {}
        mock_contract_gate_factory.return_value.build_runtime_contract.return_value = {}
        mock_self_improvement_factory.return_value.build_runtime_contract.return_value = {}
        mock_query_control_factory.return_value.build_runtime_contract.return_value = {}
        mock_scheduler_cls.return_value.filter_run_trace.return_value = [
            {
                "timestamp": "2026-05-16T10:00:00Z",
                "summary": "Main chat planning",
                "detail": "phase=planning",
                "payload": {
                    "channel": "main_chat",
                    "stage": "planning",
                    "query_id": "manual-chat-1",
                    "snapshot_ref": {"snapshot_id": "QUER-PLAN-321-20260516100000"},
                    "dedupe_key": "query_control:main_chat:planning:321:manual-chat-1",
                },
            }
        ]

        class _FakeItem:
            id = 23
            plan_id = 10
            status = "in_progress"

        class _FakePlan:
            id = 10
            active_item_id = 23
            items = [_FakeItem()]

        class _FakeQuery:
            def filter(self, *_args, **_kwargs):
                return self

            def order_by(self, *_args, **_kwargs):
                return self

            def first(self):
                return _FakePlan()

        class _FakeDb:
            def query(self, *_args, **_kwargs):
                return _FakeQuery()

        service = RuntimeSurfaceService()
        profile = service.get_runtime_profile(db=_FakeDb(), conversation_id=321)

        self.assertIn("contract_snapshot", profile)
        self.assertEqual(profile["contract_snapshot"]["contract_version"], "phase-c-runtime-contract-snapshot-v1")
        self.assertIn("channel_promotion_gate", profile)
        self.assertEqual(profile["channel_promotion_gate"]["contract_version"], "phase-h-channel-promotion-gate-v1")
        self.assertIn("runtime_core", profile)
        self.assertIn("governance_overview", profile)
        self.assertIn("main_chat_trace_overview", profile)
        self.assertIn("run_recovery", profile)
        self.assertIn("child_executor_promotion_gate", profile)
        self.assertEqual(profile["runtime_core"]["run_id"], "")
        self.assertEqual(profile["governance_overview"]["run"]["run_id"], "")
        self.assertEqual(profile["main_chat_trace_overview"]["recording_state"], "recorded")
        self.assertEqual(profile["main_chat_trace_overview"]["trace_event_count"], 1)
        self.assertEqual(profile["main_chat_trace_overview"]["stage_counts"]["planning"], 1)
        self.assertEqual(profile["main_chat_trace_overview"]["last_success_stage"], "planning")
        self.assertEqual(profile["main_chat_trace_overview"]["last_warning_stage"], "")
        self.assertEqual(profile["main_chat_trace_overview"]["recent_queries"][0]["query_id"], "manual-chat-1")
        self.assertEqual(profile["main_chat_trace_overview"]["latest_stage"], "planning")
        self.assertEqual(profile["main_chat_trace_overview"]["latest_query_id"], "manual-chat-1")
        self.assertEqual(profile["main_chat_trace_overview"]["latest_snapshot_id"], "QUER-PLAN-321-20260516100000")
        self.assertEqual(profile["governance_overview"]["main_chat"]["recording_state"], "recorded")
        self.assertEqual(profile["governance_overview"]["main_chat"]["stage_counts"]["planning"], 1)
        self.assertEqual(profile["governance_overview"]["main_chat"]["last_success_stage"], "planning")
        self.assertEqual(profile["governance_overview"]["main_chat"]["recent_queries"][0]["query_id"], "manual-chat-1")
        self.assertEqual(profile["governance_overview"]["main_chat"]["latest_stage"], "planning")
        self.assertEqual(profile["channel_promotion_gate"]["channels_by_id"]["main_chat"]["current_layer"], "query_workspace")
        self.assertEqual(profile["channel_promotion_gate"]["channels_by_id"]["subagent_lane"]["current_layer"], "recent_summary")
        self.assertIn("query_detail", profile["channel_promotion_gate"]["channels_by_id"]["external_adapter"]["blocked_layers"])
        unavailable_profile = RuntimeSurfaceService().get_runtime_profile(db=None, conversation_id=321)
        self.assertEqual(unavailable_profile["main_chat_trace_overview"]["recording_state"], "unavailable")
        self.assertEqual(unavailable_profile["main_chat_trace_overview"]["reason"], "db_unavailable")
        self.assertEqual(unavailable_profile["governance_overview"]["main_chat"]["recording_state"], "unavailable")
        self.assertEqual(unavailable_profile["governance_overview"]["main_chat"]["reason"], "db_unavailable")

        detail_profile = RuntimeSurfaceService().get_runtime_profile(
            db=_FakeDb(),
            conversation_id=321,
            query_id="manual-chat-1",
        )
        self.assertEqual(detail_profile["main_chat_query_detail"]["recording_state"], "recorded")
        self.assertEqual(detail_profile["main_chat_query_detail"]["read_model_layer"], "query_detail")
        self.assertEqual(detail_profile["main_chat_query_detail"]["source_channel"], "main_chat")
        self.assertEqual(detail_profile["main_chat_query_detail"]["identity_kind"], "query_id")
        self.assertEqual(detail_profile["main_chat_query_detail"]["query_id"], "manual-chat-1")
        self.assertEqual(detail_profile["main_chat_query_detail"]["stage_chain"], ["planning"])
        self.assertEqual(detail_profile["main_chat_query_detail"]["latest_summary"], "Main chat planning")
        self.assertEqual(detail_profile["main_chat_query_detail"]["stage_count"], 1)
        self.assertEqual(detail_profile["main_chat_query_detail"]["warning_count"], 0)
        self.assertEqual(detail_profile["main_chat_query_detail"]["dedupe_keys"], ["query_control:main_chat:planning:321:manual-chat-1"])
        self.assertEqual(detail_profile["main_chat_query_detail"]["dedupe_key_count"], 1)
        self.assertEqual(detail_profile["main_chat_query_detail"]["recent_event_count"], 1)
        self.assertEqual(detail_profile["main_chat_query_detail"]["recent_events"][0]["stage"], "planning")
        self.assertEqual(detail_profile["main_chat_query_detail"]["query_id"], "manual-chat-1")
        self.assertEqual(detail_profile["runtime_core"]["run_id"], "")
        self.assertEqual(detail_profile["governance_overview"]["run"]["run_id"], "")
        dedicated_detail = RuntimeSurfaceService().get_main_chat_query_detail(
            db=_FakeDb(),
            conversation_id=321,
            query_id="manual-chat-1",
        )
        self.assertEqual(dedicated_detail["query_id"], "manual-chat-1")
        self.assertEqual(dedicated_detail["latest_summary"], "Main chat planning")
        self.assertEqual(dedicated_detail["stage_count"], 1)
        self.assertEqual(dedicated_detail["recent_event_count"], 1)
        missing_query_detail = RuntimeSurfaceService().get_main_chat_query_detail(
            db=_FakeDb(),
            conversation_id=321,
            query_id="",
        )
        self.assertEqual(missing_query_detail["recording_state"], "unavailable")
        self.assertEqual(missing_query_detail["reason"], "query_id_missing")
        self.assertEqual(missing_query_detail["recent_event_count"], 0)
        unavailable_history = RuntimeSurfaceService().get_main_chat_query_history(
            db=None,
            conversation_id=321,
            page=1,
            page_size=2,
        )
        self.assertEqual(unavailable_history["recording_state"], "unavailable")
        self.assertEqual(unavailable_history["reason"], "db_unavailable")
        self.assertEqual(unavailable_history["items"], [])
        mock_scheduler_cls.return_value.filter_run_trace.return_value = [
            {
                "timestamp": "2026-05-16T10:00:00Z",
                "summary": "Main chat planning 1",
                "detail": "phase=planning",
                "payload": {
                    "channel": "main_chat",
                    "stage": "planning",
                    "query_id": "manual-chat-1",
                    "snapshot_ref": {"snapshot_id": "QUER-PLAN-1"},
                },
            },
            {
                "timestamp": "2026-05-16T10:05:00Z",
                "summary": "Main chat final output 2",
                "detail": "phase=final_output",
                "payload": {
                    "channel": "main_chat",
                    "stage": "final_output",
                    "query_id": "manual-chat-2",
                    "snapshot_ref": {"snapshot_id": "QUER-FINAL-2"},
                },
            },
            {
                "timestamp": "2026-05-16T10:10:00Z",
                "summary": "Main chat review 3",
                "detail": "phase=review",
                "payload": {
                    "channel": "main_chat",
                    "stage": "review",
                    "query_id": "manual-chat-3",
                    "snapshot_ref": {"snapshot_id": "QUER-REVIEW-3"},
                },
            },
        ]
        history = RuntimeSurfaceService().get_main_chat_query_history(
            db=_FakeDb(),
            conversation_id=321,
            page=1,
            page_size=2,
        )
        self.assertEqual(history["recording_state"], "recorded")
        self.assertEqual(history["total_items"], 3)
        self.assertEqual(len(history["items"]), 2)
        self.assertEqual(history["items"][0]["query_id"], "manual-chat-3")
        self.assertEqual(history["items"][1]["query_id"], "manual-chat-2")
        self.assertTrue(history["has_more"])
        self.assertIn("manual-chat-2", history["next_cursor"])
        single_page_history = RuntimeSurfaceService().get_main_chat_query_history(
            db=_FakeDb(),
            conversation_id=321,
            page=1,
            page_size=10,
        )
        self.assertEqual(single_page_history["recording_state"], "recorded")
        self.assertEqual(single_page_history["read_model_layer"], "query_history")
        self.assertEqual(single_page_history["source_channel"], "main_chat")
        self.assertEqual(single_page_history["identity_kind"], "query_id")
        self.assertEqual(single_page_history["pagination_mode"], "page_plus_cursor")
        self.assertFalse(single_page_history["has_more"])
        self.assertEqual(single_page_history["next_cursor"], "")
        mock_scheduler_cls.return_value.filter_run_trace.return_value = [
            {
                "timestamp": "2026-05-16T10:00:00Z",
                "summary": "已创建 frontend 子智能体执行单元",
                "detail": "",
                "payload": {
                    "channel": "subagent_lane",
                    "stage": "planning",
                    "query_id": "frontend-child-p10-i23-c1",
                },
            },
            {
                "timestamp": "2026-05-16T10:10:00Z",
                "summary": "已合并 frontend 子智能体结果到主响应",
                "detail": "",
                "payload": {
                    "channel": "subagent_lane",
                    "stage": "final_output",
                    "query_id": "frontend-child-p10-i23-c1",
                },
            },
        ]
        subagent_summary = RuntimeSurfaceService().get_subagent_lane_recent_summary(
            db=_FakeDb(),
            conversation_id=321,
        )
        self.assertEqual(subagent_summary["recording_state"], "recorded")
        self.assertEqual(subagent_summary["total_items"], 1)
        self.assertEqual(subagent_summary["latest_query_id"], "frontend-child-p10-i23-c1")
        self.assertEqual(subagent_summary["latest_stage"], "final_output")
        self.assertEqual(subagent_summary["items"][0]["latest_summary"], "已合并 frontend 子智能体结果到主响应")
        subagent_readiness = RuntimeSurfaceService().get_subagent_lane_query_detail_readiness(
            db=_FakeDb(),
            conversation_id=321,
        )
        self.assertEqual(subagent_readiness["contract_version"], "phase-h-subagent-lane-query-detail-readiness-v1")
        self.assertEqual(subagent_readiness["channel"], "subagent_lane")
        self.assertEqual(subagent_readiness["readiness_status"], "ready")
        self.assertTrue(subagent_readiness["ready_for_detail"])
        self.assertEqual(subagent_readiness["recent_summary_status"], "recorded")
        self.assertTrue(subagent_readiness["required_capabilities"]["stable_query_id"])
        self.assertTrue(subagent_readiness["required_capabilities"]["stage_chain_candidate"])
        self.assertTrue(subagent_readiness["required_capabilities"]["recent_summary_recorded"])
        self.assertTrue(subagent_readiness["required_capabilities"]["separates_child_run_events"])
        self.assertEqual(subagent_readiness["blocking_reasons"], [])
        self.assertEqual(
            subagent_readiness["recommended_next_change"],
            "subagent-lane-query-detail-contract",
        )
        subagent_detail = RuntimeSurfaceService().get_subagent_lane_query_detail(
            db=_FakeDb(),
            conversation_id=321,
            query_id="frontend-child-p10-i23-c1",
        )
        self.assertEqual(subagent_detail["contract_version"], "phase-h-subagent-lane-query-detail-v1")
        self.assertEqual(subagent_detail["channel"], "subagent_lane")
        self.assertEqual(subagent_detail["recording_state"], "recorded")
        self.assertEqual(subagent_detail["query_id"], "frontend-child-p10-i23-c1")
        self.assertEqual(subagent_detail["stage_chain"], ["planning", "final_output"])
        self.assertEqual(subagent_detail["latest_stage"], "final_output")
        self.assertEqual(subagent_detail["latest_summary"], "已合并 frontend 子智能体结果到主响应")
        self.assertEqual(subagent_detail["stage_count"], 2)
        self.assertEqual(subagent_detail["recent_event_count"], 2)
        self.assertNotIn("history_items", subagent_detail)
        self.assertNotIn("next_cursor", subagent_detail)
        missing_subagent_detail = RuntimeSurfaceService().get_subagent_lane_query_detail(
            db=_FakeDb(),
            conversation_id=321,
            query_id="",
        )
        self.assertEqual(missing_subagent_detail["recording_state"], "unavailable")
        self.assertEqual(missing_subagent_detail["reason"], "query_id_missing")
        unavailable_subagent_summary = RuntimeSurfaceService().get_subagent_lane_recent_summary(
            db=None,
            conversation_id=321,
        )
        self.assertEqual(unavailable_subagent_summary["recording_state"], "unavailable")
        self.assertEqual(unavailable_subagent_summary["reason"], "db_unavailable")
        unavailable_readiness = RuntimeSurfaceService().get_subagent_lane_query_detail_readiness(
            db=None,
            conversation_id=321,
        )
        self.assertFalse(unavailable_readiness["ready_for_detail"])
        self.assertEqual(unavailable_readiness["readiness_status"], "blocked")
        self.assertIn("recent_summary_not_recorded", unavailable_readiness["blocking_reasons"])

    @patch("backend.services.runtime_surface_service.SchedulerService")
    @patch("backend.services.runtime_surface_service.get_embedded_workspace_store")
    @patch("backend.services.runtime_surface_service.get_model_router")
    @patch("backend.services.runtime_surface_service.get_runtime_surface_config_service")
    @patch("backend.services.runtime_surface_service.get_capability_profile_service")
    @patch("backend.services.runtime_surface_service.get_agent_memory_service")
    @patch("backend.services.runtime_surface_service.get_subagent_runtime_service")
    @patch("backend.services.runtime_surface_service.get_agent_hook_service")
    @patch("backend.services.runtime_surface_service.get_mcp_runtime_service")
    @patch("backend.services.runtime_surface_service.get_skill_runtime_service")
    @patch("backend.services.runtime_surface_service.get_tool_runtime_service")
    @patch("backend.services.runtime_surface_service.get_runtime_contract_gate_service")
    @patch("backend.services.runtime_surface_service.get_self_improvement_ledger_service")
    def test_external_adapter_recent_summary_feeds_promotion_gate(
        self,
        _mock_ledger,
        _mock_contract_gate,
        _mock_tool_runtime,
        _mock_skill_runtime,
        _mock_mcp_runtime,
        _mock_agent_hook,
        _mock_subagent_runtime,
        _mock_agent_memory,
        _mock_capability,
        mock_config_service,
        _mock_model_router,
        _mock_workspace_store,
        mock_scheduler_cls,
    ):
        mock_config_service.return_value.get_effective_config.return_value = {
            "auth_mode": "demo_guest",
            "default_model": "doubao",
            "enabled_providers": [],
            "failover_thresholds": {"medium": 0.2, "high": 0.4},
        }
        mock_config_service.return_value.load_overrides.return_value = {}
        mock_config_service.return_value.get_config_layers.return_value = {
            "defaults": {},
            "overrides": {},
            "effective": mock_config_service.return_value.get_effective_config.return_value,
            "editable_keys": [],
        }
        mock_scheduler_cls.return_value.filter_run_trace.return_value = [
            {
                "timestamp": "2026-05-18T10:00:00Z",
                "summary": "External adapter assembled request",
                "detail": "",
                "payload": {
                    "channel": "external_adapter",
                    "stage": "context_assembly",
                    "query_id": "external-run-1",
                },
            },
            {
                "timestamp": "2026-05-18T10:01:00Z",
                "summary": "External adapter returned output",
                "detail": "",
                "payload": {
                    "channel": "external_adapter",
                    "stage": "final_output",
                    "query_id": "external-run-1",
                },
            },
        ]

        class _FakeItem:
            id = 23
            plan_id = 10
            status = "in_progress"

        class _FakePlan:
            id = 10
            active_item_id = 23
            items = [_FakeItem()]

        class _FakeQuery:
            def filter(self, *_args, **_kwargs):
                return self

            def order_by(self, *_args, **_kwargs):
                return self

            def first(self):
                return _FakePlan()

        class _FakeDb:
            def query(self, *_args, **_kwargs):
                return _FakeQuery()

        service = RuntimeSurfaceService()
        summary = service.get_external_adapter_recent_summary(
            db=_FakeDb(),
            conversation_id=321,
        )

        self.assertEqual(summary["contract_version"], "phase-i-external-adapter-recent-summary-v1")
        self.assertEqual(summary["recording_state"], "recorded")
        self.assertEqual(summary["total_items"], 1)
        self.assertEqual(summary["latest_query_id"], "external-run-1")
        self.assertEqual(summary["latest_stage"], "final_output")
        self.assertEqual(summary["latest_summary"], "External adapter returned output")
        self.assertEqual(summary["items"][0]["recording_state"], "recorded")
        self.assertNotIn("history_items", summary)
        self.assertNotIn("recent_events", summary)

        gate = service.get_channel_promotion_gate(db=_FakeDb(), conversation_id=321)
        external = gate["channels_by_id"]["external_adapter"]
        self.assertEqual(external["evidence"]["recent_summary_status"], "recorded")
        self.assertFalse(external["evidence"]["ready_for_detail"])
        self.assertIn("query_detail", external["blocked_layers"])

        unavailable = service.get_external_adapter_recent_summary(db=None, conversation_id=321)
        self.assertEqual(unavailable["recording_state"], "unavailable")
        self.assertEqual(unavailable["reason"], "db_unavailable")

    @patch("backend.services.runtime_surface_service.SchedulerService")
    @patch("backend.services.runtime_surface_service.get_embedded_workspace_store")
    @patch("backend.services.runtime_surface_service.get_model_router")
    @patch("backend.services.runtime_surface_service.get_runtime_surface_config_service")
    @patch("backend.services.runtime_surface_service.get_capability_profile_service")
    @patch("backend.services.runtime_surface_service.get_agent_memory_service")
    @patch("backend.services.runtime_surface_service.get_subagent_runtime_service")
    @patch("backend.services.runtime_surface_service.get_agent_hook_service")
    @patch("backend.services.runtime_surface_service.get_mcp_runtime_service")
    @patch("backend.services.runtime_surface_service.get_skill_runtime_service")
    @patch("backend.services.runtime_surface_service.get_tool_runtime_service")
    @patch("backend.services.runtime_surface_service.get_runtime_contract_gate_service")
    @patch("backend.services.runtime_surface_service.get_self_improvement_ledger_service")
    @patch("backend.services.runtime_surface_service.get_query_control_plane_service")
    def test_runtime_profile_surfaces_backend_governance_run_state(
        self,
        mock_query_control_factory,
        mock_self_improvement_factory,
        mock_contract_gate_factory,
        mock_tool_runtime_factory,
        mock_skill_runtime_factory,
        mock_mcp_runtime_factory,
        mock_hook_factory,
        mock_subagent_factory,
        mock_memory_factory,
        mock_capability_factory,
        mock_config_factory,
        mock_router_factory,
        mock_workspace_store_factory,
        mock_scheduler_cls,
    ):
        store = InMemoryEmbeddedRunWorkspaceStore()
        sdk = EmbeddedAgentRuntimeSDK(workspace_store=store)
        parent = sdk.create_run(
            {
                "conversation_id": 42,
                "user_id": 7,
                "model_name": "doubao",
                "run_kind": "chat",
                "metadata": {"agent_name": "fraud_assistant"},
            }
        )
        sdk.merge_child_executor_output(
            sdk.execute_bound_child_executor(
                sdk.bind_child_executor_routing(
                    {
                        "input": "复核交易风险",
                        "merge_strategy": "append_summary",
                        "metadata": {
                            "agent_name": "risk_reviewer",
                            "scheduler_policy": {"timeout_seconds": 45},
                            "worker_runtime_backend": "embedded_sdk_worker",
                            "explicit_executor_binding_opt_in": True,
                        },
                    },
                    parent_run_id=parent["run"]["run_id"],
                ),
                parent_run_id=parent["run"]["run_id"],
            ),
            parent_run_id=parent["run"]["run_id"],
        )

        mock_workspace_store_factory.return_value = store
        mock_scheduler = mock_scheduler_cls.return_value
        mock_scheduler.serialize_scheduler_run.return_value = {
            "run_id": parent["run"]["run_id"],
            "parent_run_id": "root-run-00",
            "child_run_id": "",
            "scheduler_run_id": parent["run"]["run_id"],
            "run_kind": "scheduler",
            "state": "running",
            "merge_strategy": "append_summary",
            "merge_status": "running",
            "child_count": 1,
            "active_children": 1,
            "child_status_counts": {"running": 1},
            "policy": {},
        }
        mock_scheduler.get_run_trace.return_value = [
            {
                "timestamp": "2026-05-16T10:00:00Z",
                "run_id": parent["run"]["run_id"],
                "parent_run_id": "root-run-00",
                "child_run_id": "",
                "run_kind": "scheduler",
                "scheduler_run_id": parent["run"]["run_id"],
                "source": "scheduler",
                "event_type": "scheduler_execution_started",
                "severity": "info",
                "summary": "调度执行中",
                "detail": "child_count=1",
                "payload": {
                    "run_id": parent["run"]["run_id"],
                    "scheduler_run_id": parent["run"]["run_id"],
                },
            }
        ]
        mock_scheduler.filter_run_trace.return_value = mock_scheduler.get_run_trace.return_value
        mock_router_factory.return_value.list_available_models.return_value = {}
        mock_config_factory.return_value.get_effective_config.return_value = {
            "auth_mode": "demo_guest",
            "default_model": "doubao",
            "enabled_providers": [],
            "failover_thresholds": {"medium": 0.2, "high": 0.4},
        }
        mock_config_factory.return_value.get_config_layers.return_value = {
            "defaults": {},
            "overrides": {},
            "effective": {},
            "editable_keys": [],
        }
        mock_capability_factory.return_value.build_runtime_contract.return_value = {}
        mock_memory_factory.return_value.build_runtime_contract.return_value = {
            "contract_version": "phase-b-memory-entry-v1",
            "active": False,
            "loaded_layers": [],
            "missing_layers": [],
            "memory_entries": [],
            "layer_order": [],
        }
        mock_subagent_factory.return_value.build_runtime_contract.return_value = {}
        mock_hook_factory.return_value.build_runtime_contract.return_value = {}
        mock_mcp_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_skill_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_tool_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_tool_runtime_factory.return_value.build_adapter_health_contract.return_value = {}
        mock_contract_gate_factory.return_value.build_runtime_contract.return_value = {}
        mock_self_improvement_factory.return_value.build_runtime_contract.return_value = {}
        mock_query_control_factory.return_value.build_runtime_contract.return_value = {}

        class _FakeItem:
            id = 23
            plan_id = 10
            status = "in_progress"

        class _FakePlan:
            id = 10
            active_item_id = 23
            items = [_FakeItem()]

        class _FakeQuery:
            def filter(self, *_args, **_kwargs):
                return self

            def order_by(self, *_args, **_kwargs):
                return self

            def first(self):
                return _FakePlan()

        class _FakeDb:
            def query(self, *_args, **_kwargs):
                return _FakeQuery()

        profile = RuntimeSurfaceService().get_runtime_profile(db=_FakeDb(), conversation_id=321)

        self.assertEqual(profile["runtime_core"]["run_id"], parent["run"]["run_id"])
        self.assertEqual(profile["runtime_core"]["parent_run_id"], "root-run-00")
        self.assertEqual(profile["runtime_core"]["child_display_id"], profile["runtime_core"]["child_run_id"])
        self.assertEqual(profile["runtime_core"]["scheduler_run_id"], parent["run"]["run_id"])
        self.assertEqual(profile["runtime_core"]["status"], "running")
        self.assertEqual(profile["runtime_core"]["trace_count"], 1)
        self.assertEqual(profile["runtime_core"]["latest_trace_event"]["summary"], "调度执行中")
        self.assertEqual(profile["runtime_core"]["child_merge_intent"], "risk_review")
        self.assertEqual(profile["runtime_core"]["child_merge_entities"], ["交易", "风险"])
        self.assertEqual(profile["runtime_core"]["child_merge_entity_count"], 2)
        self.assertEqual(profile["runtime_core"]["child_merge_focus_count"], 3)
        self.assertEqual(profile["runtime_core"]["child_merge_action_count"], 3)
        self.assertEqual(profile["runtime_core"]["child_merge_primary_entities"], ["交易", "风险"])
        self.assertEqual(profile["runtime_core"]["child_merge_conclusion"], "建议人工复核关键风险点后继续主流程")
        self.assertEqual(profile["runtime_core"]["child_merge_section_source"], "merged_sections")
        self.assertEqual(
            profile["runtime_core"]["child_merge_section_ids"],
            ["merged_entities", "merged_focus", "merged_actions", "latest_conclusion"],
        )
        self.assertEqual(profile["runtime_core"]["child_merge_section_counts"]["merged_entities"], 2)
        self.assertEqual(profile["runtime_core"]["child_merge_section_counts"]["merged_focus"], 3)
        self.assertTrue(profile["run_recovery"]["available"])
        self.assertEqual(profile["run_recovery"]["contract_version"], "phase-ii-run-recovery-v1")
        self.assertFalse(profile["run_recovery"]["recoverable"])
        self.assertEqual(profile["run_recovery"]["loop_continuation"]["recovery_reason"], "descriptor_missing")
        self.assertEqual(profile["run_recovery"]["recovery_capabilities"]["recovery_mode"], "unavailable")
        self.assertFalse(profile["run_recovery"]["recovery_capabilities"]["requires_durable_workspace"])
        profile_recovery_entrypoints = {
            (item["method"], item.get("mode") or ""): item
            for item in profile["run_recovery"]["recovery_entrypoints"]
        }
        self.assertTrue(profile_recovery_entrypoints[("probe_run_recovery", "")]["available"])
        self.assertFalse(profile_recovery_entrypoints[("submit_approval", "approved")]["available"])
        self.assertEqual(
            profile_recovery_entrypoints[("submit_approval", "approved")]["blocked_reason"],
            "run_not_waiting_approval",
        )
        self.assertFalse(profile_recovery_entrypoints[("resume_run", "default")]["available"])
        self.assertEqual(
            profile_recovery_entrypoints[("resume_run", "default")]["blocked_reason"],
            "run_not_observing",
        )
        self.assertEqual(profile["governance_overview"]["run"]["run_id"], parent["run"]["run_id"])
        self.assertEqual(profile["governance_overview"]["run"]["parent_run_id"], "root-run-00")
        self.assertEqual(profile["governance_overview"]["run"]["child_display_id"], profile["governance_overview"]["run"]["child_run_id"])
        self.assertEqual(profile["governance_overview"]["run"]["scheduler_run_id"], parent["run"]["run_id"])
        self.assertEqual(profile["governance_overview"]["run"]["child_merge_intent"], "risk_review")
        self.assertEqual(profile["governance_overview"]["run"]["child_merge_entities"], ["交易", "风险"])
        self.assertEqual(profile["governance_overview"]["run"]["child_merge_entity_count"], 2)
        self.assertEqual(profile["governance_overview"]["run"]["child_merge_focus_count"], 3)
        self.assertEqual(profile["governance_overview"]["run"]["child_merge_action_count"], 3)
        self.assertEqual(profile["governance_overview"]["run"]["child_merge_primary_entities"], ["交易", "风险"])
        self.assertEqual(profile["governance_overview"]["run"]["child_merge_conclusion"], "建议人工复核关键风险点后继续主流程")
        self.assertEqual(profile["governance_overview"]["run"]["child_merge_section_source"], "merged_sections")
        self.assertEqual(
            profile["governance_overview"]["run"]["child_merge_section_ids"],
            ["merged_entities", "merged_focus", "merged_actions", "latest_conclusion"],
        )
        self.assertEqual(profile["governance_overview"]["run"]["child_merge_section_counts"]["merged_entities"], 2)
        self.assertEqual(profile["governance_overview"]["run"]["latest_trace_event"]["summary"], "调度执行中")
        self.assertEqual(
            profile["governance_overview"]["default_runtime_recovery"]["recovery_mode"],
            "registry_backed",
        )
        governance_default_entrypoints = {
            (item["method"], item.get("mode") or ""): item
            for item in profile["governance_overview"]["default_runtime_recovery"]["recovery_entrypoints"]
        }
        self.assertTrue(governance_default_entrypoints[("submit_approval", "approved")]["available"])
        governance_alignment_entries = {
            (item["method"], item.get("mode") or ""): item
            for item in profile["governance_overview"]["recovery_alignment_summary"]["entries"]
        }
        self.assertEqual(
            profile["governance_overview"]["recovery_alignment_summary"]["current_alignment_status"],
            "aligned",
        )
        self.assertEqual(
            governance_alignment_entries[("submit_approval", "approved")]["current_alignment"],
            "state_gated",
        )
        self.assertEqual(profile["child_executor_preflight"]["status"], "relationship_only")
        self.assertFalse(profile["child_executor_preflight"]["promotion_ready"])
        self.assertEqual(profile["child_executor_preflight"]["executor_binding_status"], "blocked")
        self.assertEqual(profile["governance_overview"]["child_executor_preflight"]["status"], "relationship_only")

    @patch("backend.services.runtime_surface_service.get_command_registry_service")
    @patch("backend.services.runtime_surface_service.get_model_router")
    @patch("backend.services.runtime_surface_service.get_runtime_surface_config_service")
    @patch("backend.services.runtime_surface_service.get_capability_profile_service")
    @patch("backend.services.runtime_surface_service.get_agent_memory_service")
    @patch("backend.services.runtime_surface_service.get_subagent_runtime_service")
    @patch("backend.services.runtime_surface_service.get_agent_hook_service")
    @patch("backend.services.runtime_surface_service.get_mcp_runtime_service")
    @patch("backend.services.runtime_surface_service.get_skill_runtime_service")
    @patch("backend.services.runtime_surface_service.get_tool_runtime_service")
    @patch("backend.services.runtime_surface_service.get_runtime_contract_gate_service")
    @patch("backend.services.runtime_surface_service.get_self_improvement_ledger_service")
    @patch("backend.services.runtime_surface_service.get_query_control_plane_service")
    @patch("backend.services.runtime_surface_service.get_embedded_workspace_store")
    @patch("backend.services.runtime_surface_service.SchedulerService")
    def test_runtime_profile_surfaces_ready_child_executor_preflight(
        self,
        mock_scheduler_cls,
        mock_workspace_store_factory,
        mock_query_control_factory,
        mock_self_improvement_factory,
        mock_contract_gate_factory,
        mock_tool_runtime_factory,
        mock_skill_runtime_factory,
        mock_mcp_runtime_factory,
        mock_hook_factory,
        mock_subagent_factory,
        mock_memory_factory,
        mock_capability_factory,
        mock_config_factory,
        mock_router_factory,
        mock_command_registry_factory,
    ):
        store = InMemoryEmbeddedRunWorkspaceStore()
        sdk = EmbeddedAgentRuntimeSDK(workspace_store=store)
        parent = sdk.create_run(
            {
                "conversation_id": 42,
                "user_id": 7,
                "model_name": "doubao",
                "run_kind": "chat",
                "metadata": {"agent_name": "fraud_assistant"},
            }
        )
        sdk.merge_child_executor_output(
            sdk.execute_bound_child_executor(
                sdk.bind_child_executor_routing(
                    {
                        "input": "复核交易风险",
                        "merge_strategy": "append_summary",
                        "metadata": {
                            "agent_name": "risk_reviewer",
                            "scheduler_policy": {"timeout_seconds": 45},
                            "worker_runtime_backend": "embedded_sdk_worker",
                        },
                    },
                    parent_run_id=parent["run"]["run_id"],
                ),
                parent_run_id=parent["run"]["run_id"],
            ),
            parent_run_id=parent["run"]["run_id"],
        )

        mock_workspace_store_factory.return_value = store
        store.describe_backend = lambda: {
            "backend_kind": "sqlalchemy",
            "durable": True,
            "backend_mode": "strict_sql",
            "operation_fallback_allowed": False,
            "fallback_active": False,
            "fallback_reason": "",
            "last_error": "",
            "state_contract": build_embedded_workspace_state_contract(),
        }
        mock_scheduler = mock_scheduler_cls.return_value
        mock_scheduler.serialize_scheduler_run.return_value = {
            "run_id": parent["run"]["run_id"],
            "parent_run_id": "root-run-00",
            "child_run_id": "",
            "scheduler_run_id": parent["run"]["run_id"],
            "run_kind": "scheduler",
            "state": "running",
            "merge_strategy": "append_summary",
            "merge_status": "running",
            "child_count": 1,
            "active_children": 1,
            "child_status_counts": {"running": 1},
            "policy": {},
        }
        mock_scheduler.get_run_trace.return_value = [
            {
                "timestamp": "2026-05-16T10:00:00Z",
                "run_id": parent["run"]["run_id"],
                "parent_run_id": "root-run-00",
                "child_run_id": "",
                "run_kind": "scheduler",
                "scheduler_run_id": parent["run"]["run_id"],
                "source": "scheduler",
                "event_type": "scheduler_execution_started",
                "severity": "info",
                "summary": "调度执行中",
                "detail": "child_count=1",
                "payload": {
                    "run_id": parent["run"]["run_id"],
                    "scheduler_run_id": parent["run"]["run_id"],
                },
            }
        ]
        mock_scheduler.filter_run_trace.return_value = mock_scheduler.get_run_trace.return_value
        mock_router_factory.return_value.list_available_models.return_value = {}
        mock_config_factory.return_value.get_effective_config.return_value = {
            "auth_mode": "demo_guest",
            "default_model": "doubao",
            "enabled_providers": [],
            "failover_thresholds": {"medium": 0.2, "high": 0.4},
        }
        mock_config_factory.return_value.get_config_layers.return_value = {
            "defaults": {},
            "overrides": {},
            "effective": {},
            "editable_keys": [],
        }
        mock_capability_factory.return_value.build_runtime_contract.return_value = {}
        mock_memory_factory.return_value.build_runtime_contract.return_value = {
            "contract_version": "phase-b-memory-entry-v1",
            "active": False,
            "loaded_layers": [],
            "missing_layers": [],
            "memory_entries": [],
            "layer_order": [],
        }
        mock_subagent_factory.return_value.build_runtime_contract.return_value = {}
        mock_hook_factory.return_value.build_runtime_contract.return_value = {}
        mock_mcp_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_skill_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_tool_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_tool_runtime_factory.return_value.build_adapter_health_contract.return_value = {}
        mock_contract_gate_factory.return_value.build_runtime_contract.return_value = {}
        mock_self_improvement_factory.return_value.build_runtime_contract.return_value = {}
        mock_query_control_factory.return_value.build_runtime_contract.return_value = {}
        mock_command_registry = mock_command_registry_factory.return_value
        mock_command_registry.build_runtime_contract.return_value = {
            "contract_version": "phase-b-command-runtime-v1",
            "total_commands": 1,
            "command_definitions": [],
            "embedded_sdk": {
                "contract_version": "phase-b-embedded-sdk-v1",
                "delegate_preflight": {
                    "contract_version": "phase-ii-child-executor-preflight-v1",
                    "status": "promotion_candidate",
                    "promotion_ready": True,
                    "real_child_executor_ready": True,
                    "executor_binding_status": "ready",
                    "executor_binding_blockers": [],
                    "recommended_next_step": "wire_executor_backend",
                    "promotion_requirements": [
                        "child_run_recovery_boundary_defined",
                        "child_context_budget_defined",
                        "child_result_merge_semantics_defined",
                        "worker_runtime_backend_selected",
                    ],
                    "missing_requirements": [],
                    "non_goals": ["real_child_executor_dispatch"],
                    "current_scope": ["create_child_run_relationship"],
                },
                "delegate_gate": {
                    "gate_status": "passed",
                    "allowed": True,
                    "failure_reason": "",
                },
            },
            "agent_harness_facade": {
                "contract_version": "phase-b-agent-harness-facade-v1",
                "delegate_preflight": {
                    "contract_version": "phase-ii-child-executor-preflight-v1",
                    "status": "promotion_candidate",
                    "promotion_ready": True,
                    "real_child_executor_ready": True,
                    "executor_binding_status": "ready",
                    "executor_binding_blockers": [],
                    "recommended_next_step": "wire_executor_backend",
                    "promotion_requirements": [
                        "child_run_recovery_boundary_defined",
                        "child_context_budget_defined",
                        "child_result_merge_semantics_defined",
                        "worker_runtime_backend_selected",
                    ],
                    "missing_requirements": [],
                    "non_goals": ["real_child_executor_dispatch"],
                    "current_scope": ["create_child_run_relationship"],
                },
            },
        }

        class _FakeItem:
            id = 23
            plan_id = 10
            status = "in_progress"

        class _FakePlan:
            id = 10
            active_item_id = 23
            items = [_FakeItem()]

        class _FakeQuery:
            def filter(self, *_args, **_kwargs):
                return self

            def order_by(self, *_args, **_kwargs):
                return self

            def first(self):
                return _FakePlan()

        class _FakeDb:
            def query(self, *_args, **_kwargs):
                return _FakeQuery()

        profile = RuntimeSurfaceService().get_runtime_profile(db=_FakeDb(), conversation_id=321)

        self.assertEqual(profile["child_executor_preflight"]["status"], "promotion_candidate")
        self.assertTrue(profile["child_executor_preflight"]["promotion_ready"])
        self.assertEqual(profile["child_executor_preflight"]["executor_binding_status"], "ready")
        self.assertTrue(profile["child_executor_preflight"]["delegate_gate_allowed"])
        self.assertEqual(profile["governance_overview"]["child_executor_preflight"]["status"], "promotion_candidate")
        workspace_backend = profile["governance_overview"]["child_executor_preflight"]["workspace_backend"]
        self.assertEqual(workspace_backend["backend_kind"], "sqlalchemy")
        state_contract = workspace_backend["state_contract"]
        self.assertEqual(
            state_contract["contract_version"],
            "phase-ii-durable-workspace-state-contract-v1",
        )
        self.assertIn("run_snapshot", state_contract["durable_state_kinds"])
        self.assertIn("executable_continuation_callable", state_contract["runtime_only_state_kinds"])

    @patch("backend.services.runtime_surface_service.get_model_router")
    @patch("backend.services.runtime_surface_service.get_runtime_surface_config_service")
    @patch("backend.services.runtime_surface_service.get_capability_profile_service")
    @patch("backend.services.runtime_surface_service.get_agent_memory_service")
    @patch("backend.services.runtime_surface_service.get_subagent_runtime_service")
    @patch("backend.services.runtime_surface_service.get_agent_hook_service")
    @patch("backend.services.runtime_surface_service.get_mcp_runtime_service")
    @patch("backend.services.runtime_surface_service.get_skill_runtime_service")
    @patch("backend.services.runtime_surface_service.get_tool_runtime_service")
    @patch("backend.services.runtime_surface_service.get_runtime_contract_gate_service")
    @patch("backend.services.runtime_surface_service.get_self_improvement_ledger_service")
    @patch("backend.services.runtime_surface_service.get_query_control_plane_service")
    @patch("backend.services.runtime_surface_service.get_embedded_workspace_store")
    def test_runtime_surface_can_return_child_executor_replay_and_summary(
        self,
        mock_workspace_store_factory,
        mock_query_control_factory,
        mock_self_improvement_factory,
        mock_contract_gate_factory,
        mock_tool_runtime_factory,
        mock_skill_runtime_factory,
        mock_mcp_runtime_factory,
        mock_hook_factory,
        mock_subagent_factory,
        mock_memory_factory,
        mock_capability_factory,
        mock_config_factory,
        mock_router_factory,
    ):
        store = InMemoryEmbeddedRunWorkspaceStore()
        sdk = EmbeddedAgentRuntimeSDK(workspace_store=store)
        parent = sdk.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
            "metadata": {"agent_name": "fraud_assistant"},
        })
        merged = sdk.merge_child_executor_output(
            sdk.execute_bound_child_executor(
                sdk.bind_child_executor_routing(
                    {
                        "input": "复核交易风险",
                        "merge_strategy": "append_summary",
                        "metadata": {
                            "agent_name": "risk_reviewer",
                            "scheduler_policy": {"timeout_seconds": 45},
                            "worker_runtime_backend": "embedded_sdk_worker",
                        },
                    },
                    parent_run_id=parent["run"]["run_id"],
                ),
                parent_run_id=parent["run"]["run_id"],
            ),
            parent_run_id=parent["run"]["run_id"],
        )
        mock_workspace_store_factory.return_value = store
        mock_router_factory.return_value.list_available_models.return_value = {}
        mock_config_factory.return_value.get_effective_config.return_value = {
            "auth_mode": "demo_guest",
            "default_model": "doubao",
            "enabled_providers": [],
            "failover_thresholds": {"medium": 0.2, "high": 0.4},
        }
        mock_config_factory.return_value.get_config_layers.return_value = {
            "defaults": {},
            "overrides": {},
            "effective": {},
            "editable_keys": [],
        }
        mock_capability_factory.return_value.build_runtime_contract.return_value = {}
        mock_memory_factory.return_value.build_runtime_contract.return_value = {"active": False, "loaded_layers": [], "missing_layers": [], "memory_entries": [], "layer_order": []}
        mock_subagent_factory.return_value.build_runtime_contract.return_value = {}
        mock_hook_factory.return_value.build_runtime_contract.return_value = {}
        mock_mcp_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_skill_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_tool_runtime_factory.return_value.build_runtime_contract.return_value = {}
        mock_tool_runtime_factory.return_value.build_adapter_health_contract.return_value = {}
        mock_contract_gate_factory.return_value.build_runtime_contract.return_value = {}
        mock_self_improvement_factory.return_value.build_runtime_contract.return_value = {}
        mock_query_control_factory.return_value.build_runtime_contract.return_value = {}

        service = RuntimeSurfaceService()
        replay = service.get_child_executor_output_replay(parent_run_id=parent["run"]["run_id"])
        summary = service.get_child_executor_output_summary(parent_run_id=parent["run"]["run_id"])
        merged_semantics = service.get_child_executor_merged_semantics(parent_run_id=parent["run"]["run_id"])
        run_recovery = service.get_run_recovery(run_id=parent["run"]["run_id"])

        self.assertEqual(replay["record_count"], 1)
        self.assertEqual(replay["records"][0]["execution_status"], "executed")
        self.assertEqual(replay["records"][0]["merge_status"], "merged")
        self.assertEqual(summary["record_count"], 1)
        self.assertEqual(summary["latest_merge_strategy"], "append_summary")
        self.assertEqual(summary["latest_merged_output"], merged["merged_output"])
        self.assertTrue(merged_semantics["available"])
        self.assertEqual(merged_semantics["intent_catalog_version"], "phase-ii-child-intent-catalog-v1")
        self.assertEqual(merged_semantics["intent_label"], "risk_review")
        self.assertEqual(merged_semantics["merge_behavior"]["focus_points"], "append_dedup")
        self.assertEqual(merged_semantics["merged_sections"]["merged_entities"]["section_id"], "merged_entities")
        self.assertEqual(merged_semantics["merged_sections"]["merged_entities"]["section_kind"], "list")
        self.assertEqual(merged_semantics["merged_sections"]["merged_entities"]["item_count"], 2)
        self.assertIn("交易", merged_semantics["merged_sections"]["merged_entities"]["items"])
        self.assertEqual(merged_semantics["parent_state_surface"]["section_source"], "merged_sections")
        self.assertEqual(
            merged_semantics["parent_state_surface"]["section_counts"]["merged_entities"],
            merged_semantics["parent_state_surface"]["entity_count"],
        )
        self.assertTrue(run_recovery["available"])
        self.assertEqual(run_recovery["contract_version"], "phase-ii-run-recovery-v1")
        self.assertFalse(run_recovery["recoverable"])
        self.assertEqual(run_recovery["loop_continuation"]["recovery_reason"], "descriptor_missing")
        self.assertEqual(run_recovery["recovery_capabilities"]["recovery_mode"], "unavailable")
        run_recovery_entrypoints = {
            (item["method"], item.get("mode") or ""): item
            for item in run_recovery["recovery_entrypoints"]
        }
        self.assertFalse(run_recovery_entrypoints[("submit_approval", "approved")]["available"])
        self.assertEqual(run_recovery_entrypoints[("submit_approval", "approved")]["blocked_reason"], "run_not_waiting_approval")

    def test_run_recovery_can_report_ready_via_registry_with_durable_workspace(self):
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        try:
            store = SQLAlchemyEmbeddedRunWorkspaceStore(
                TestingSessionLocal,
                allow_operation_fallback=False,
                backend_mode="strict_sql",
            )
            registry = InMemoryEmbeddedContinuationRegistry()

            def _tool_executor(_run):
                return {
                    "tool_name": "filesystem_write",
                    "args": {"path": "case.md"},
                    "result": "写入成功",
                }

            def _reviewer(_run):
                return {
                    "reviewer": "quality_gate",
                    "status": "approved",
                    "summary": "工具结果可接受",
                }

            registry.register("tool_executor.filesystem_write", _tool_executor)
            registry.register("reviewer.quality_gate", _reviewer)

            writer = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
            result = writer.create_run({
                "conversation_id": 42,
                "user_id": 7,
                "model_name": "doubao",
                "run_kind": "chat",
            })
            executed = writer.execute_run(
                result["run"]["run_id"],
                tool_policy=lambda _run: {
                    "status": "approval_required",
                    "tool_name": "filesystem_write",
                    "tool_args": {"path": "case.md"},
                    "reason": "高风险写文件工具需要人工审批",
                },
                tool_executor=_tool_executor,
                reviewer=_reviewer,
            )

            service = RuntimeSurfaceService()
            service.embedded_workspace_store = store
            service.continuation_registry = registry

            recovery = service.get_run_recovery(run_id=result["run"]["run_id"])

            self.assertTrue(recovery["available"])
            self.assertTrue(recovery["recoverable"])
            self.assertEqual(recovery["checkpoint"]["status"], "ready")
            self.assertEqual(recovery["checkpoint"]["checkpoint_kind"], "approval_waiting")
            self.assertEqual(recovery["resume_cursor"]["cursor_status"], "ready")
            self.assertEqual(recovery["resume_cursor"]["entrypoint"], "submit_approval.approved")
            self.assertEqual(recovery["resume_cursor"]["recovery_reason"], "ready_via_registry")
            self.assertEqual(recovery["tool_continuation"]["recovery_reason"], "ready_via_registry")
            self.assertEqual(recovery["loop_continuation"]["recovery_reason"], "ready_via_registry")
            self.assertEqual(recovery["workspace_backend"]["backend_kind"], "sqlalchemy")
            self.assertTrue(recovery["workspace_backend"]["durable"])
            self.assertEqual(
                recovery["workspace_backend"]["state_contract"]["contract_version"],
                "phase-ii-durable-workspace-state-contract-v1",
            )
            self.assertEqual(recovery["recovery_capabilities"]["recovery_mode"], "registry_backed")
            self.assertTrue(recovery["recovery_capabilities"]["requires_durable_workspace"])
            self.assertTrue(recovery["recovery_capabilities"]["requires_registry_bindings"])
            recovery_entrypoints = {
                (item["method"], item.get("mode") or ""): item
                for item in recovery["recovery_entrypoints"]
            }
            self.assertTrue(recovery_entrypoints[("submit_approval", "approved")]["available"])
            self.assertEqual(
                recovery_entrypoints[("submit_approval", "approved")]["recovery_reason"],
                "ready_via_registry",
            )
            self.assertFalse(recovery_entrypoints[("resume_run", "continue_loop")]["available"])
            self.assertEqual(
                recovery_entrypoints[("resume_run", "continue_loop")]["blocked_reason"],
                "run_not_observing",
            )

            reader = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
            reader.submit_approval(executed["approval_request"]["request_id"], "approved")
            reader.resume_run(result["run"]["run_id"], continue_loop=True)
            recovered_surface = service.get_run_recovery(run_id=result["run"]["run_id"])

            self.assertEqual(
                recovered_surface["recovery_operation_boundary"]["contract_version"],
                "phase-ii-durable-recovery-operation-v1",
            )
            self.assertFalse(
                recovered_surface["recovery_operation_boundary"]["worker_ownership"]["implemented"]
            )
            self.assertEqual(
                recovered_surface["latest_recovery_operation"]["operation_status"],
                "recovered",
            )
            self.assertEqual(
                recovered_surface["latest_recovery_operation"]["entrypoint"],
                "resume_run.continue_loop",
            )
            self.assertEqual(
                recovered_surface["latest_recovery_operation"]["persistence_posture"],
                "durable_ready",
            )
            self.assertEqual(recovered_surface["recovery_operation_count"], 2)
            self.assertNotIn("handler", recovered_surface["latest_recovery_operation"])
            self.assertNotIn("callable", recovered_surface["latest_recovery_operation"])
        finally:
            Base.metadata.drop_all(bind=engine)
            engine.dispose()

    def test_run_recovery_exposes_resolved_approval_gate(self):
        store = InMemoryEmbeddedRunWorkspaceStore()
        registry = InMemoryEmbeddedContinuationRegistry()
        writer = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
        result = writer.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
        })
        executed = writer.execute_run(
            result["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "approval_required",
                "tool_name": "filesystem_write",
                "tool_args": {"path": "case.md"},
                "reason": "高风险写文件工具需要人工审批",
            },
            tool_executor=lambda _run: {
                "tool_name": "filesystem_write",
                "args": {"path": "case.md"},
                "result": "不应该执行",
            },
        )
        writer.submit_approval(executed["approval_request"]["request_id"], "denied")

        service = RuntimeSurfaceService()
        service.embedded_workspace_store = store
        service.continuation_registry = registry
        recovery = service.get_run_recovery(run_id=result["run"]["run_id"])

        self.assertEqual(recovery["approval_request"]["status"], "denied")
        self.assertEqual(recovery["checkpoint"]["status"], "stale")
        self.assertEqual(recovery["checkpoint"]["recovery_reason"], "denied")
        self.assertEqual(recovery["resume_cursor"]["cursor_status"], "stale")
        self.assertEqual(recovery["resume_cursor"]["recovery_reason"], "denied")
        recovery_entrypoints = {
            (item["method"], item.get("mode") or ""): item
            for item in recovery["recovery_entrypoints"]
        }
        self.assertFalse(recovery_entrypoints[("submit_approval", "approved")]["available"])
        self.assertEqual(
            recovery_entrypoints[("submit_approval", "approved")]["blocked_reason"],
            "approval_already_resolved",
        )
        self.assertEqual(
            recovery_entrypoints[("submit_approval", "approved")]["recovery_reason"],
            "already_resolved",
        )
        self.assertEqual(recovery_entrypoints[("submit_approval", "approved")]["approval_status"], "denied")

    def test_runtime_surface_can_return_embedded_runtime_bootstrap_contract(self):
        service = RuntimeSurfaceService()

        contract = service.get_embedded_runtime_bootstrap()

        self.assertEqual(contract["contract_version"], "phase-ii-embedded-runtime-factory-v1")
        self.assertEqual(contract["runtime_backend"], "EmbeddedAgentRuntimeSDK")
        self.assertIn("default_runtime_profile", contract)
        self.assertIn("recommended_bootstrap", contract["default_runtime_profile"])
        self.assertIn("default_recovery_capabilities", contract)
        self.assertEqual(contract["bootstrap_recovery_validation"]["contract_version"], "phase-ii-embedded-runtime-bootstrap-validation-v1")
        self.assertEqual(contract["bootstrap_recovery_validation"]["validation_status"], "passed")
        self.assertIn("recovery_capabilities", contract["bootstrap_recovery_validation"])
        bootstrap_recovery_entrypoints = {
            (item["method"], item.get("mode") or ""): item
            for item in contract["bootstrap_recovery_validation"]["recovery_entrypoints"]
        }
        self.assertTrue(bootstrap_recovery_entrypoints[("submit_approval", "approved")]["available"])
        self.assertEqual(
            bootstrap_recovery_entrypoints[("submit_approval", "approved")]["recovery_reason"],
            "ready_via_registry",
        )
        bootstrap_alignment_entries = {
            (item["method"], item.get("mode") or ""): item
            for item in contract["recovery_alignment_summary"]["entries"]
        }
        self.assertEqual(contract["recovery_alignment_summary"]["actual_alignment_status"], "aligned")
        self.assertEqual(
            bootstrap_alignment_entries[("submit_approval", "approved")]["actual_alignment"],
            "aligned",
        )

    def test_embedded_runtime_bootstrap_recovery_validation_matches_memory_mode_contract(self):
        service = RuntimeSurfaceService()

        validation = service._validate_embedded_runtime_bootstrap_recovery({
            "default_runtime_profile": {
                "embedded_workspace_store_mode": "memory_only",
            },
            "default_recovery_expectation": {
                "cross_process_candidate": False,
                "cross_process_block_reason": "workspace_backend_not_durable",
            },
        })

        self.assertEqual(validation["contract_version"], "phase-ii-embedded-runtime-bootstrap-validation-v1")
        self.assertFalse(validation["expected_recoverable"])
        self.assertFalse(validation["actual_recoverable"])
        self.assertEqual(validation["workspace_backend_kind"], "in_memory")
        self.assertEqual(validation["workspace_backend_mode"], "memory_only")
        self.assertEqual(validation["tool_recovery_reason"], "workspace_backend_not_durable")
        self.assertEqual(validation["loop_recovery_reason"], "workspace_backend_not_durable")
        self.assertEqual(validation["recovery_capabilities"]["recovery_mode"], "unavailable")
        self.assertFalse(validation["recovery_capabilities"]["requires_durable_workspace"])
        memory_recovery_entrypoints = {
            (item["method"], item.get("mode") or ""): item
            for item in validation["recovery_entrypoints"]
        }
        self.assertFalse(memory_recovery_entrypoints[("submit_approval", "approved")]["available"])
        self.assertEqual(
            memory_recovery_entrypoints[("submit_approval", "approved")]["blocked_reason"],
            "workspace_backend_not_durable",
        )
        self.assertEqual(validation["validation_status"], "passed")

    def test_embedded_runtime_bootstrap_recovery_validation_matches_strict_sql_mode_contract(self):
        service = RuntimeSurfaceService()

        validation = service._validate_embedded_runtime_bootstrap_recovery({
            "default_runtime_profile": {
                "embedded_workspace_store_mode": "strict_sql",
            },
            "default_recovery_expectation": {
                "cross_process_candidate": True,
                "cross_process_block_reason": "",
            },
        })

        self.assertEqual(validation["contract_version"], "phase-ii-embedded-runtime-bootstrap-validation-v1")
        self.assertTrue(validation["expected_recoverable"])
        self.assertTrue(validation["actual_recoverable"])
        self.assertEqual(validation["workspace_backend_kind"], "sqlalchemy")
        self.assertEqual(validation["workspace_backend_mode"], "strict_sql")
        self.assertEqual(validation["tool_recovery_reason"], "ready_via_registry")
        self.assertEqual(validation["loop_recovery_reason"], "ready_via_registry")
        self.assertEqual(validation["recovery_capabilities"]["recovery_mode"], "registry_backed")
        self.assertTrue(validation["recovery_capabilities"]["requires_durable_workspace"])
        self.assertTrue(validation["recovery_capabilities"]["requires_registry_bindings"])
        strict_sql_recovery_entrypoints = {
            (item["method"], item.get("mode") or ""): item
            for item in validation["recovery_entrypoints"]
        }
        self.assertTrue(strict_sql_recovery_entrypoints[("submit_approval", "approved")]["available"])
        self.assertEqual(
            strict_sql_recovery_entrypoints[("submit_approval", "approved")]["recovery_reason"],
            "ready_via_registry",
        )
        self.assertEqual(validation["validation_status"], "passed")


if __name__ == "__main__":
    unittest.main()
