"""Runtime surface helpers for demo mode and dynamic model/provider catalogs."""

from __future__ import annotations

import tempfile
from typing import Any, Dict, List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

try:
    from agent_framework.adapters import InMemoryEmbeddedRunWorkspaceStore, SQLAlchemyEmbeddedRunWorkspaceStore, get_embedded_workspace_store, set_embedded_workspace_store_mode
    from agent_framework.continuation_registry import InMemoryEmbeddedContinuationRegistry, get_embedded_continuation_registry
    from agent_framework.persistence import build_embedded_sdk_persistence_interface
    from agent_framework.runtime_dependencies import get_default_embedded_runtime_factory
    from agent_framework.sdk import EmbeddedAgentRuntimeSDK, build_child_executor_dispatch_contract, build_child_executor_execution_prerequisites_contract
    from agent_framework.child_executor_backends import build_child_executor_backend_registry_contract
    from config import AUTH_MODE, DEFAULT_MODEL
    from database import Base
    from model_router import get_model_router
    from services.agent_memory_service import get_agent_memory_service
    from services.agent_hook_service import get_agent_hook_service
    from services.capability_profile_service import get_capability_profile_service
    from services.command_registry_service import get_command_registry_service
    from services.mcp_runtime_service import get_mcp_runtime_service
    from services.query_control_plane_service import get_query_control_plane_service
    from services.runtime_contract_snapshot_service import get_runtime_contract_snapshot_service
    from services.runtime_contract_gate_service import get_runtime_contract_gate_service
    from services.self_improvement_ledger_service import get_self_improvement_ledger_service
    from services.runtime_core_contract_builder import RuntimeCoreContractBuilder
    from services.runtime_surface_config_service import get_runtime_surface_config_service
    from services.runtime_surface_builders import (
        EmbeddedRuntimeContractBundleBuilder,
        ChannelPromotionGateBuilder,
        ExternalAdapterRecentSummaryBuilder,
        MainChatGovernanceOverviewBuilder,
        MainChatQueryReadModelBuilder,
        RuntimeRecoveryContractBuilder,
        SubagentLaneQueryDetailBuilder,
        SubagentLaneQueryDetailReadinessBuilder,
        SubagentLaneRecentSummaryBuilder,
    )
    from services.runtime_surface_profile_assembler import RuntimeSurfaceProfileAssembler
    from services.skill_runtime_service import get_skill_runtime_service
    from services.subagent_service import get_subagent_runtime_service
    from services.tool_runtime_service import get_tool_runtime_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_framework.adapters import InMemoryEmbeddedRunWorkspaceStore, SQLAlchemyEmbeddedRunWorkspaceStore, get_embedded_workspace_store, set_embedded_workspace_store_mode
    from backend.agent_framework.continuation_registry import InMemoryEmbeddedContinuationRegistry, get_embedded_continuation_registry
    from backend.agent_framework.persistence import build_embedded_sdk_persistence_interface
    from backend.agent_framework.runtime_dependencies import get_default_embedded_runtime_factory
    from backend.agent_framework.sdk import EmbeddedAgentRuntimeSDK, build_child_executor_dispatch_contract, build_child_executor_execution_prerequisites_contract
    from backend.agent_framework.child_executor_backends import build_child_executor_backend_registry_contract
    from backend.config import AUTH_MODE, DEFAULT_MODEL
    from backend.database import Base
    from backend.model_router import get_model_router
    from backend.services.agent_memory_service import get_agent_memory_service
    from backend.services.agent_hook_service import get_agent_hook_service
    from backend.services.capability_profile_service import get_capability_profile_service
    from backend.services.command_registry_service import get_command_registry_service
    from backend.services.mcp_runtime_service import get_mcp_runtime_service
    from backend.services.query_control_plane_service import get_query_control_plane_service
    from backend.services.runtime_contract_snapshot_service import get_runtime_contract_snapshot_service
    from backend.services.runtime_contract_gate_service import get_runtime_contract_gate_service
    from backend.services.self_improvement_ledger_service import get_self_improvement_ledger_service
    from backend.services.runtime_core_contract_builder import RuntimeCoreContractBuilder
    from backend.services.runtime_surface_config_service import get_runtime_surface_config_service
    from backend.services.runtime_surface_builders import (
        EmbeddedRuntimeContractBundleBuilder,
        ChannelPromotionGateBuilder,
        ExternalAdapterRecentSummaryBuilder,
        MainChatGovernanceOverviewBuilder,
        MainChatQueryReadModelBuilder,
        RuntimeRecoveryContractBuilder,
        SubagentLaneQueryDetailBuilder,
        SubagentLaneQueryDetailReadinessBuilder,
        SubagentLaneRecentSummaryBuilder,
    )
    from backend.services.runtime_surface_profile_assembler import RuntimeSurfaceProfileAssembler
    from backend.services.skill_runtime_service import get_skill_runtime_service
    from backend.services.subagent_service import get_subagent_runtime_service
    from backend.services.tool_runtime_service import get_tool_runtime_service
try:
    from models import PlanRunRecord
    from services.scheduler_service import SchedulerService
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.models import PlanRunRecord
    from backend.services.scheduler_service import SchedulerService


class RuntimeSurfaceService:
    """Expose model/provider/auth surface to clients."""

    def __init__(self):
        self.model_router = get_model_router()
        self.config_service = get_runtime_surface_config_service()
        self.capability_profile_service = get_capability_profile_service()
        self.agent_memory_service = get_agent_memory_service()
        self.agent_hook_service = get_agent_hook_service()
        self.subagent_runtime_service = get_subagent_runtime_service()
        self.command_registry_service = get_command_registry_service()
        self.tool_runtime_service = get_tool_runtime_service()
        self.mcp_runtime_service = get_mcp_runtime_service()
        self.query_control_plane_service = get_query_control_plane_service()
        self.skill_runtime_service = get_skill_runtime_service()
        self.contract_snapshot_service = get_runtime_contract_snapshot_service()
        self.contract_gate_service = get_runtime_contract_gate_service()
        self.self_improvement_ledger_service = get_self_improvement_ledger_service()
        self._sync_embedded_runtime_bootstrap_config()
        self.embedded_workspace_store = get_embedded_workspace_store()
        self.continuation_registry = get_embedded_continuation_registry()
        self.runtime_factory = self._configure_embedded_runtime_factory(
            get_default_embedded_runtime_factory()
        )

    def _list_all_models(self) -> List[Dict[str, Any]]:
        models = list(self.model_router.list_available_models().values())
        models.sort(key=lambda item: (not bool(item.get("is_default")), item.get("provider", ""), item.get("display_name", item.get("name", ""))))
        return models

    def _sync_embedded_runtime_bootstrap_config(self) -> None:
        effective = self.config_service.get_effective_config()
        requested_mode = str(effective.get("embedded_workspace_store_mode") or "").strip().lower()
        if requested_mode:
            set_embedded_workspace_store_mode(requested_mode)

    def _configure_embedded_runtime_factory(self, runtime_factory: Any) -> Any:
        effective = self.config_service.get_effective_config()
        config = effective.get("worker_ownership_production_enablement_config")
        configure = getattr(
            runtime_factory,
            "configure_worker_ownership_production_enablement_config",
            None,
        )
        if callable(configure):
            configured = configure(config if isinstance(config, dict) else None)
            if configured is not None:
                return configured
        return runtime_factory

    def _resolve_enabled_provider_ids(self, provider_ids: List[str], effective_config: Dict[str, Any]) -> set[str]:
        configured = [
            str(item or "").strip()
            for item in (effective_config.get("enabled_providers") or [])
            if str(item or "").strip()
        ]
        if not configured:
            return set(provider_ids)
        return {provider_id for provider_id in configured if provider_id in provider_ids}

    def list_models(self) -> List[Dict[str, Any]]:
        effective_config = self.config_service.get_effective_config()
        models = self._list_all_models()
        provider_ids = sorted({str(item.get("provider") or "unknown") for item in models})
        enabled_provider_ids = self._resolve_enabled_provider_ids(provider_ids, effective_config)
        return [item for item in models if str(item.get("provider") or "unknown") in enabled_provider_ids]

    def get_runtime_profile(
        self,
        db: Any = None,
        *,
        conversation_id: int | None = None,
        plan_id: int | None = None,
        item_id: int | None = None,
        query_id: str | None = None,
        run_id: str | None = None,
        parent_run_id: str | None = None,
        child_run_id: str | None = None,
        scheduler_run_id: str | None = None,
    ) -> Dict[str, Any]:
        return RuntimeSurfaceProfileAssembler.assemble(
            self,
            db=db,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
            query_id=query_id,
            run_id=run_id,
            parent_run_id=parent_run_id,
            child_run_id=child_run_id,
            scheduler_run_id=scheduler_run_id,
            auth_mode_default=AUTH_MODE,
            default_model_default=DEFAULT_MODEL,
        )

    def get_main_chat_query_detail(
        self,
        *,
        db: Any = None,
        conversation_id: int | None = None,
        plan_id: int | None = None,
        item_id: int | None = None,
        query_id: str | None = None,
    ) -> Dict[str, Any]:
        """Return the dedicated query-level read model for main_chat governance drill-down."""
        return self._build_main_chat_query_detail_contract(
            db=db,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
            query_id=query_id,
        )

    def get_main_chat_query_history(
        self,
        *,
        db: Any = None,
        conversation_id: int | None = None,
        plan_id: int | None = None,
        item_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        return self._build_main_chat_query_history_contract(
            db=db,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
            page=page,
            page_size=page_size,
        )

    def get_subagent_lane_recent_summary(
        self,
        *,
        db: Any = None,
        conversation_id: int | None = None,
        plan_id: int | None = None,
        item_id: int | None = None,
    ) -> Dict[str, Any]:
        return self._build_subagent_lane_recent_summary_contract(
            db=db,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
        )

    def get_external_adapter_recent_summary(
        self,
        *,
        db: Any = None,
        conversation_id: int | None = None,
        plan_id: int | None = None,
        item_id: int | None = None,
    ) -> Dict[str, Any]:
        return self._build_external_adapter_recent_summary_contract(
            db=db,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
        )

    def get_subagent_lane_query_detail_readiness(
        self,
        *,
        db: Any = None,
        conversation_id: int | None = None,
        plan_id: int | None = None,
        item_id: int | None = None,
    ) -> Dict[str, Any]:
        summary = self._build_subagent_lane_recent_summary_contract(
            db=db,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
        )
        return SubagentLaneQueryDetailReadinessBuilder.build_readiness_from_summary(summary)

    def get_subagent_lane_query_detail(
        self,
        *,
        db: Any = None,
        conversation_id: int | None = None,
        plan_id: int | None = None,
        item_id: int | None = None,
        query_id: str | None = None,
    ) -> Dict[str, Any]:
        return self._build_subagent_lane_query_detail_contract(
            db=db,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
            query_id=query_id,
        )

    def get_channel_promotion_gate(
        self,
        *,
        db: Any = None,
        conversation_id: int | None = None,
        plan_id: int | None = None,
        item_id: int | None = None,
    ) -> Dict[str, Any]:
        subagent_summary = self._build_subagent_lane_recent_summary_contract(
            db=db,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
        )
        external_summary = self._build_external_adapter_recent_summary_contract(
            db=db,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
        )
        subagent_readiness = SubagentLaneQueryDetailReadinessBuilder.build_readiness_from_summary(subagent_summary)
        return ChannelPromotionGateBuilder.build_contract(
            subagent_lane_readiness=subagent_readiness,
            external_adapter_readiness={
                "readiness_status": "candidate",
                "recent_summary_status": str(external_summary.get("recording_state") or "unavailable"),
                "ready_for_detail": False,
                "blocking_reasons": ["detail_not_generalized"],
            },
        )

    def get_child_executor_output_replay(self, *, parent_run_id: str) -> Dict[str, Any]:
        return self._build_child_executor_sdk_reader().list_child_executor_outputs(parent_run_id)

    def get_child_executor_output_summary(self, *, parent_run_id: str) -> Dict[str, Any]:
        return self._build_child_executor_sdk_reader().summarize_child_executor_outputs(parent_run_id)

    def get_child_executor_merged_semantics(self, *, parent_run_id: str) -> Dict[str, Any]:
        return self._build_child_executor_sdk_reader().summarize_child_executor_merged_semantics(parent_run_id)

    def get_embedded_runtime_bootstrap(self) -> Dict[str, Any]:
        factory_contract = self.runtime_factory.build_runtime_contract()
        bootstrap_recovery_validation = self._validate_embedded_runtime_bootstrap_recovery(factory_contract)
        return EmbeddedRuntimeContractBundleBuilder.build_bootstrap_contract(
            factory_contract,
            bootstrap_recovery_validation=bootstrap_recovery_validation,
        )

    def update_embedded_runtime_bootstrap(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(payload or {})
        allowed_keys = {"embedded_workspace_store_mode"}
        update_payload = {
            key: value
            for key, value in payload.items()
            if key in allowed_keys and value is not None
        }
        if not update_payload:
            raise ValueError("embedded runtime bootstrap 更新至少需要提供 embedded_workspace_store_mode")
        previous_contract = self.get_embedded_runtime_bootstrap()
        self.config_service.update_overrides(update_payload)
        self._sync_embedded_runtime_bootstrap_config()
        self.embedded_workspace_store = get_embedded_workspace_store()
        self.continuation_registry = get_embedded_continuation_registry()
        self.runtime_factory = self._configure_embedded_runtime_factory(
            get_default_embedded_runtime_factory()
        )
        contract = self.get_embedded_runtime_bootstrap()
        requested_workspace_mode = str(update_payload.get("embedded_workspace_store_mode") or "").strip()
        contract["update_status"] = "applied"
        contract["applied_changes"] = sorted(update_payload.keys())
        contract["hot_reload_applied"] = "embedded_workspace_store_mode" in update_payload
        contract["restart_required"] = False
        contract["restart_required_changes"] = []
        contract["post_update_verification"] = EmbeddedRuntimeContractBundleBuilder.build_post_update_verification(
            previous_contract=previous_contract,
            current_contract=contract,
            requested_workspace_mode=requested_workspace_mode,
        )
        return contract

    def _validate_embedded_runtime_bootstrap_recovery(self, contract: Dict[str, Any] | None = None) -> Dict[str, Any]:
        normalized_contract = dict(contract or self.runtime_factory.build_runtime_contract())
        profile = dict(normalized_contract.get("default_runtime_profile") or {})
        requested_mode = str(profile.get("embedded_workspace_store_mode") or "").strip().lower() or "memory_only"
        expected = dict(normalized_contract.get("default_recovery_expectation") or {})

        registry = InMemoryEmbeddedContinuationRegistry()

        def _tool_executor(_run):
            return {
                "tool_name": "filesystem_write",
                "args": {"path": "bootstrap-validation.md"},
                "result": "ok",
            }

        def _reviewer(_run):
            return {
                "reviewer": "quality_gate",
                "status": "approved",
                "summary": "bootstrap validation ok",
            }

        registry.register("tool_executor.filesystem_write", _tool_executor)
        registry.register("reviewer.quality_gate", _reviewer)

        engine = None
        store = None
        try:
            if requested_mode == "memory_only":
                store = InMemoryEmbeddedRunWorkspaceStore()
            else:
                with tempfile.TemporaryDirectory() as tmp_dir:
                    sqlite_path = f"{tmp_dir}/bootstrap_validation.db"
                    engine = create_engine(
                        f"sqlite:///{sqlite_path}",
                        connect_args={"check_same_thread": False},
                        poolclass=StaticPool,
                    )
                    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                    Base.metadata.create_all(bind=engine)
                    store = SQLAlchemyEmbeddedRunWorkspaceStore(
                        TestingSessionLocal,
                        allow_operation_fallback=requested_mode == "prefer_sql_with_fallback",
                        backend_mode=requested_mode,
                    )
                    validation = self._run_embedded_runtime_bootstrap_validation(
                        store=store,
                        registry=registry,
                        expected=expected,
                        requested_mode=requested_mode,
                    )
                    Base.metadata.drop_all(bind=engine)
                    engine.dispose()
                    engine = None
                    return validation

            return self._run_embedded_runtime_bootstrap_validation(
                store=store,
                registry=registry,
                expected=expected,
                requested_mode=requested_mode,
            )
        finally:
            if engine is not None:
                Base.metadata.drop_all(bind=engine)
                engine.dispose()

    def _run_embedded_runtime_bootstrap_validation(
        self,
        *,
        store: Any,
        registry: InMemoryEmbeddedContinuationRegistry,
        expected: Dict[str, Any],
        requested_mode: str,
    ) -> Dict[str, Any]:
        writer = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
        result = writer.create_run({
            "conversation_id": 42,
            "user_id": 7,
            "model_name": "doubao",
            "run_kind": "chat",
        })
        writer.execute_run(
            result["run"]["run_id"],
            tool_policy=lambda _run: {
                "status": "approval_required",
                "tool_name": "filesystem_write",
                "tool_args": {"path": "bootstrap-validation.md"},
                "reason": "Validate embedded runtime bootstrap recovery behavior.",
            },
            tool_executor=lambda _run: {
                "tool_name": "filesystem_write",
                "args": {"path": "bootstrap-validation.md"},
                "result": "ok",
            },
            reviewer=lambda _run: {
                "reviewer": "quality_gate",
                "status": "approved",
                "summary": "bootstrap validation ok",
            },
        )
        reader = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
        probe = reader.probe_run_recovery(result["run"]["run_id"])
        return RuntimeRecoveryContractBuilder.build_bootstrap_validation_contract(
            expected=expected,
            requested_mode=requested_mode,
            probe=probe,
        )

    def get_run_recovery(self, *, run_id: str) -> Dict[str, Any]:
        normalized_run_id = str(run_id or "").strip()
        if not normalized_run_id:
            return self._build_run_recovery_contract()
        try:
            probe = self._build_child_executor_sdk_reader().probe_run_recovery(normalized_run_id)
        except Exception as exc:
            return self._build_run_recovery_contract({
                "run_id": normalized_run_id,
                "recoverable": False,
                "error": str(exc),
            })
        return self._build_run_recovery_contract(probe)

    def _build_run_recovery_contract(self, probe: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return RuntimeRecoveryContractBuilder.build_run_recovery_contract(probe)

    def _build_default_runtime_recovery_contract(self, factory_contract: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return RuntimeRecoveryContractBuilder.build_default_runtime_recovery_contract(factory_contract)

    def _build_child_merge_state_contract(self, runtime_scope: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return RuntimeCoreContractBuilder.build_child_merge_state_contract(runtime_scope)

    def _build_runtime_core_contract(self, *, runtime_scope: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return RuntimeCoreContractBuilder.build_contract(runtime_scope=runtime_scope)

    def _build_child_executor_sdk_reader(self) -> EmbeddedAgentRuntimeSDK:
        return self.runtime_factory.create_sdk(
            workspace_store=self.embedded_workspace_store,
            continuation_registry=self.continuation_registry,
        )

    def _build_embedded_runtime_boundaries_contract(self, command_contract: Dict[str, Any] | None) -> Dict[str, Any]:
        contract = dict(command_contract or {})
        embedded_sdk = dict(contract.get("embedded_sdk") or {})
        agent_harness_facade = dict(contract.get("agent_harness_facade") or {})
        delegate_preflight = dict(embedded_sdk.get("delegate_preflight") or {})
        delegate_gate = dict(embedded_sdk.get("delegate_gate") or {})
        delegate_routing = dict(embedded_sdk.get("delegate_routing") or {})
        delegate_binding = dict(embedded_sdk.get("delegate_binding") or {})
        delegate_stub = dict(embedded_sdk.get("delegate_stub") or {})
        delegate_execution = dict(embedded_sdk.get("delegate_execution") or {})
        delegate_merge = dict(embedded_sdk.get("delegate_merge") or {})
        delegate_replay = dict(embedded_sdk.get("delegate_replay") or {})
        delegate_artifact_summary = dict(embedded_sdk.get("delegate_artifact_summary") or {})
        child_executor_dispatch_contract = dict(embedded_sdk.get("child_executor_dispatch_contract") or {})
        facade_delegate_preflight = dict(agent_harness_facade.get("delegate_preflight") or {})
        connected = bool(embedded_sdk) or bool(agent_harness_facade)
        return {
            "contract_version": "phase-ii-embedded-runtime-boundaries-v1",
            "connected": connected,
            "sdk_contract_version": str(embedded_sdk.get("contract_version") or "").strip(),
            "facade_contract_version": str(agent_harness_facade.get("contract_version") or "").strip(),
            "volatile_runtime_state": list(embedded_sdk.get("volatile_runtime_state") or []),
            "persistence_seams": list(embedded_sdk.get("persistence_seams") or []),
            "recovery_entrypoints": [dict(item) for item in (embedded_sdk.get("recovery_entrypoints") or [])],
            "delegate_preflight_status": str(delegate_preflight.get("status") or "").strip(),
            "real_child_executor_ready": bool(delegate_preflight.get("real_child_executor_ready")),
            "delegate_promotion_ready": bool(delegate_preflight.get("promotion_ready")),
            "delegate_executor_binding_status": str(delegate_preflight.get("executor_binding_status") or "").strip(),
            "delegate_executor_binding_blockers": list(delegate_preflight.get("executor_binding_blockers") or []),
            "delegate_recommended_next_step": str(delegate_preflight.get("recommended_next_step") or "").strip(),
            "delegate_gate_status": str(delegate_gate.get("gate_status") or "").strip(),
            "delegate_gate_allowed": bool(delegate_gate.get("allowed")),
            "delegate_gate_failure_reason": str(delegate_gate.get("failure_reason") or "").strip(),
            "delegate_route_status": str(delegate_routing.get("route_status") or "").strip(),
            "delegate_route_executor_path": str(delegate_routing.get("executor_path") or "").strip(),
            "delegate_route_reason": str(delegate_routing.get("route_reason") or "").strip(),
            "delegate_route_recommended_action": str(delegate_routing.get("recommended_action") or "").strip(),
            "delegate_binding_status": str(delegate_binding.get("binding_status") or "").strip(),
            "delegate_binding_id": str(delegate_binding.get("binding_id") or "").strip(),
            "delegate_binding_reason": str(delegate_binding.get("binding_reason") or "").strip(),
            "delegate_binding_recommended_action": str(delegate_binding.get("recommended_action") or "").strip(),
            "delegate_stub_status": str(delegate_stub.get("stub_status") or "").strip(),
            "delegate_stub_binding_id": str(delegate_stub.get("binding_id") or "").strip(),
            "delegate_stub_executor_path": str(delegate_stub.get("executor_path") or "").strip(),
            "delegate_stub_reason": str(delegate_stub.get("stub_reason") or "").strip(),
            "delegate_stub_recommended_action": str(delegate_stub.get("recommended_action") or "").strip(),
            "delegate_execution_status": str(delegate_execution.get("execution_status") or "").strip(),
            "delegate_execution_binding_id": str(delegate_execution.get("binding_id") or "").strip(),
            "delegate_execution_executor_path": str(delegate_execution.get("executor_path") or "").strip(),
            "delegate_execution_mode": str(delegate_execution.get("execution_mode") or "").strip(),
            "delegate_execution_output_summary": str(delegate_execution.get("output_summary") or "").strip(),
            "delegate_execution_reason": str(delegate_execution.get("execution_reason") or "").strip(),
            "delegate_execution_output_text": str(delegate_execution.get("output_text") or "").strip(),
            "delegate_execution_output_envelope": dict(delegate_execution.get("output_envelope") or {}),
            "delegate_execution_recommended_action": str(delegate_execution.get("recommended_action") or "").strip(),
            "delegate_merge_status": str(delegate_merge.get("merge_status") or "").strip(),
            "delegate_merge_ready": bool(delegate_merge.get("merge_ready")),
            "delegate_merge_reason": str(delegate_merge.get("merge_reason") or "").strip(),
            "delegate_merge_strategy": str(delegate_merge.get("merge_strategy") or "").strip(),
            "delegate_merged_summary": str(delegate_merge.get("merged_summary") or "").strip(),
            "delegate_merged_output": str(delegate_merge.get("merged_output") or "").strip(),
            "delegate_merge_artifact_ref": dict(delegate_merge.get("artifact_ref") or {}),
            "delegate_merge_section_count": int(delegate_merge.get("section_count") or 0),
            "delegate_replay_record_count": int(delegate_replay.get("record_count") or 0),
            "delegate_replay_records": list(delegate_replay.get("records") or []),
            "delegate_artifact_summary": dict(delegate_artifact_summary),
            "delegate_promotion_requirements": list(delegate_preflight.get("promotion_requirements") or []),
            "delegate_missing_requirements": list(delegate_preflight.get("missing_requirements") or []),
            "delegate_non_goals": list(delegate_preflight.get("non_goals") or []),
            "delegate_current_scope": list(delegate_preflight.get("current_scope") or []),
            "child_executor_backend_registry": dict(
                embedded_sdk.get("child_executor_backend_registry")
                or build_child_executor_backend_registry_contract()
            ),
            "child_executor_dispatch_contract": child_executor_dispatch_contract,
            "delegate_dispatch_status": str(child_executor_dispatch_contract.get("overall_status") or "").strip(),
            "delegate_dispatch_ready": bool(child_executor_dispatch_contract.get("dispatch_ready")),
            "delegate_dispatch_will_dispatch": bool(child_executor_dispatch_contract.get("will_dispatch")),
            "delegate_dispatch_mode": str(child_executor_dispatch_contract.get("dispatch_mode") or "").strip(),
            "delegate_dispatch_backend_id": str(child_executor_dispatch_contract.get("backend_id") or "").strip(),
            "delegate_dispatch_blockers": list(child_executor_dispatch_contract.get("blockers") or []),
            "approved_reference_slices": [dict(item) for item in (delegate_preflight.get("approved_reference_slices") or [])],
            "facade_delegate_preflight_status": str(facade_delegate_preflight.get("status") or "").strip(),
            "workspace_backend": self._describe_embedded_workspace_backend(),
            "persistence_interface": build_embedded_sdk_persistence_interface(self._describe_embedded_workspace_backend()),
            "reason": "" if connected else "command_contract_unavailable",
        }

    def _describe_embedded_workspace_backend(self) -> Dict[str, Any]:
        describe_backend = getattr(self.embedded_workspace_store, "describe_backend", None)
        if not callable(describe_backend):
            return {
                "backend_kind": "",
                "durable": False,
                "fallback_active": False,
                "fallback_reason": "",
                "last_error": "",
            }
        description = dict(describe_backend() or {})
        return {
            "backend_kind": str(description.get("backend_kind") or "").strip(),
            "durable": bool(description.get("durable")),
            "backend_mode": str(description.get("backend_mode") or "").strip(),
            "operation_fallback_allowed": bool(description.get("operation_fallback_allowed")),
            "fallback_active": bool(description.get("fallback_active")),
            "fallback_reason": str(description.get("fallback_reason") or "").strip(),
            "last_error": str(description.get("last_error") or "").strip(),
            "state_contract": dict(description.get("state_contract") or {}),
        }

    def _build_child_executor_preflight_contract(self, command_contract: Dict[str, Any] | None) -> Dict[str, Any]:
        contract = dict(command_contract or {})
        embedded_sdk = dict(contract.get("embedded_sdk") or {})
        agent_harness_facade = dict(contract.get("agent_harness_facade") or {})
        delegate_preflight = dict(embedded_sdk.get("delegate_preflight") or {})
        facade_delegate_preflight = dict(agent_harness_facade.get("delegate_preflight") or {})
        delegate_gate = dict(embedded_sdk.get("delegate_gate") or {})
        workspace_backend = self._describe_embedded_workspace_backend()
        return {
            "contract_version": str(delegate_preflight.get("contract_version") or facade_delegate_preflight.get("contract_version") or "phase-ii-child-executor-preflight-v1").strip(),
            "status": str(delegate_preflight.get("status") or facade_delegate_preflight.get("status") or "").strip(),
            "promotion_ready": bool(delegate_preflight.get("promotion_ready")),
            "real_child_executor_ready": bool(delegate_preflight.get("real_child_executor_ready")),
            "executor_binding_status": str(delegate_preflight.get("executor_binding_status") or "").strip(),
            "executor_binding_blockers": list(delegate_preflight.get("executor_binding_blockers") or []),
            "recommended_next_step": str(delegate_preflight.get("recommended_next_step") or "").strip(),
            "delegate_gate_status": str(delegate_gate.get("gate_status") or "").strip(),
            "delegate_gate_allowed": bool(delegate_gate.get("allowed")),
            "delegate_gate_failure_reason": str(delegate_gate.get("failure_reason") or "").strip(),
            "delegate_promotion_requirements": list(delegate_preflight.get("promotion_requirements") or []),
            "delegate_missing_requirements": list(delegate_preflight.get("missing_requirements") or []),
            "delegate_non_goals": list(delegate_preflight.get("non_goals") or []),
            "delegate_current_scope": list(delegate_preflight.get("current_scope") or []),
            "backend_registry": dict(
                delegate_preflight.get("backend_registry")
                or embedded_sdk.get("child_executor_backend_registry")
                or build_child_executor_backend_registry_contract()
            ),
            "workspace_backend": workspace_backend,
        }

    def _build_child_executor_promotion_gate_contract(
        self,
        command_contract: Dict[str, Any] | None,
        child_executor_preflight: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        contract = dict(command_contract or {})
        embedded_sdk = dict(contract.get("embedded_sdk") or {})
        gate = dict(embedded_sdk.get("delegate_gate") or {})
        normalized_preflight = dict(child_executor_preflight or self._build_child_executor_preflight_contract(command_contract))
        blockers = [str(item).strip() for item in (gate.get("blockers") or normalized_preflight.get("executor_binding_blockers") or []) if str(item).strip()]
        gate_contract = {
            "contract_version": str(gate.get("contract_version") or "phase-ii-child-executor-gate-v1").strip(),
            "gate_status": str(gate.get("gate_status") or ("passed" if bool(gate.get("allowed")) else "blocked")).strip(),
            "allowed": bool(gate.get("allowed")),
            "failure_reason": str(gate.get("failure_reason") or ("child_executor_preflight_blocked" if not bool(gate.get("allowed")) else "")).strip(),
            "executor_path": str(gate.get("executor_path") or "").strip(),
            "recommended_next_step": str(gate.get("recommended_next_step") or normalized_preflight.get("recommended_next_step") or "keep_relationship_only").strip(),
            "blockers": blockers,
            "checked_at": str(gate.get("checked_at") or "").strip(),
            "preflight": normalized_preflight,
        }
        prerequisites = gate.get("child_executor_execution_prerequisites")
        if not isinstance(prerequisites, dict):
            prerequisites = build_child_executor_execution_prerequisites_contract(
                preflight=normalized_preflight,
                gate=gate_contract,
            )
        gate_contract["child_executor_execution_prerequisites"] = dict(prerequisites)
        return gate_contract

    def _build_child_executor_dispatch_contract(
        self,
        command_contract: Dict[str, Any] | None,
        child_executor_promotion_gate: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        contract = dict(command_contract or {})
        embedded_sdk = dict(contract.get("embedded_sdk") or {})
        dispatch_contract = embedded_sdk.get("child_executor_dispatch_contract")
        if isinstance(dispatch_contract, dict) and dispatch_contract:
            return dict(dispatch_contract)
        gate = dict(child_executor_promotion_gate or embedded_sdk.get("delegate_gate") or {})
        return build_child_executor_dispatch_contract(
            gate=gate,
            backend_registry=dict(
                embedded_sdk.get("child_executor_backend_registry")
                or build_child_executor_backend_registry_contract()
            ),
        )

    def _build_governance_overview_contract(
        self,
        *,
        main_chat_trace_overview: Dict[str, Any] | None = None,
        runtime_scope: Dict[str, Any] | None = None,
        run_recovery: Dict[str, Any] | None = None,
        default_runtime_recovery: Dict[str, Any] | None = None,
        child_executor_preflight: Dict[str, Any] | None = None,
        child_executor_promotion_gate: Dict[str, Any] | None = None,
        child_executor_dispatch_contract: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        trace_overview = dict(main_chat_trace_overview or {})
        scope = dict(runtime_scope or {})
        recovery = dict(run_recovery or {})
        default_recovery = dict(default_runtime_recovery or {})
        preflight = dict(child_executor_preflight or {})
        gate = dict(child_executor_promotion_gate or {})
        dispatch = dict(child_executor_dispatch_contract or {})
        recovery_alignment_summary = RuntimeRecoveryContractBuilder.build_recovery_alignment_summary(
            expected_entrypoints=list(default_recovery.get("recovery_entrypoints") or []),
            current_entrypoints=list(recovery.get("recovery_entrypoints") or []),
        )
        return {
            "contract_version": "phase-a-governance-overview-v1",
            "run": {
                "runtime_core": True,
                "run_id": str(scope.get("run_id") or "").strip(),
                "parent_run_id": str(scope.get("parent_run_id") or "").strip(),
                "child_run_id": str(scope.get("child_run_id") or "").strip(),
                "child_display_id": str(scope.get("child_display_id") or scope.get("child_run_id") or "").strip(),
                "scheduler_run_id": str(scope.get("scheduler_run_id") or "").strip(),
                "run_kind": str(scope.get("run_kind") or "contract").strip() or "contract",
                "status": str(scope.get("status") or "not_started").strip() or "not_started",
                "trace_count": int(scope.get("trace_count") or 0),
                "latest_trace_event": dict(scope.get("latest_trace_event") or {}) or None,
                **self._build_child_merge_state_contract(scope),
            },
            "run_recovery": {
                "contract_version": str(recovery.get("contract_version") or "").strip(),
                "available": bool(recovery.get("available")),
                "run_id": str(recovery.get("run_id") or "").strip(),
                "run_state": str(recovery.get("run_state") or "").strip(),
                "recoverable": bool(recovery.get("recoverable")),
                "tool_continuation": dict(recovery.get("tool_continuation") or {}),
                "loop_continuation": dict(recovery.get("loop_continuation") or {}),
                "checkpoint": dict(recovery.get("checkpoint") or {}),
                "resume_cursor": dict(recovery.get("resume_cursor") or {}),
                "recovery_entrypoints": [dict(item) for item in (recovery.get("recovery_entrypoints") or [])],
                "workspace_backend": dict(recovery.get("workspace_backend") or {}),
                "reason": str(recovery.get("reason") or "").strip(),
            },
            "default_runtime_recovery": {
                "contract_version": str(default_recovery.get("contract_version") or "").strip(),
                "recovery_mode": str(default_recovery.get("recovery_mode") or "").strip(),
                "recovery_posture": str(default_recovery.get("recovery_posture") or "").strip(),
                "requires_durable_workspace": bool(default_recovery.get("requires_durable_workspace")),
                "requires_registry_bindings": bool(default_recovery.get("requires_registry_bindings")),
                "expected_cross_process_candidate": bool(default_recovery.get("expected_cross_process_candidate")),
                "cross_process_block_reason": str(default_recovery.get("cross_process_block_reason") or "").strip(),
                "workspace_backend_kind": str(default_recovery.get("workspace_backend_kind") or "").strip(),
                "workspace_backend_mode": str(default_recovery.get("workspace_backend_mode") or "").strip(),
                "recovery_entrypoints": [dict(item) for item in (default_recovery.get("recovery_entrypoints") or [])],
            },
            "recovery_alignment_summary": recovery_alignment_summary,
            "child_executor_preflight": {
                "contract_version": str(preflight.get("contract_version") or "").strip(),
                "status": str(preflight.get("status") or "").strip(),
                "promotion_ready": bool(preflight.get("promotion_ready")),
                "real_child_executor_ready": bool(preflight.get("real_child_executor_ready")),
                "executor_binding_status": str(preflight.get("executor_binding_status") or "").strip(),
                "executor_binding_blockers": list(preflight.get("executor_binding_blockers") or []),
                "recommended_next_step": str(preflight.get("recommended_next_step") or "").strip(),
                "delegate_gate_status": str(preflight.get("delegate_gate_status") or "").strip(),
                "delegate_gate_allowed": bool(preflight.get("delegate_gate_allowed")),
                "delegate_gate_failure_reason": str(preflight.get("delegate_gate_failure_reason") or "").strip(),
                "delegate_promotion_requirements": list(preflight.get("delegate_promotion_requirements") or []),
                "delegate_missing_requirements": list(preflight.get("delegate_missing_requirements") or []),
                "delegate_non_goals": list(preflight.get("delegate_non_goals") or []),
                "delegate_current_scope": list(preflight.get("delegate_current_scope") or []),
                "workspace_backend": dict(preflight.get("workspace_backend") or {}),
            },
            "child_executor_promotion_gate": {
                "contract_version": str(gate.get("contract_version") or "").strip(),
                "gate_status": str(gate.get("gate_status") or "").strip(),
                "allowed": bool(gate.get("allowed")),
                "failure_reason": str(gate.get("failure_reason") or "").strip(),
                "executor_path": str(gate.get("executor_path") or "").strip(),
                "recommended_next_step": str(gate.get("recommended_next_step") or "").strip(),
                "blockers": list(gate.get("blockers") or []),
                "checked_at": str(gate.get("checked_at") or "").strip(),
                "child_executor_execution_prerequisites": dict(
                    gate.get("child_executor_execution_prerequisites") or {}
                ),
            },
            "child_executor_dispatch_contract": {
                "contract_version": str(dispatch.get("contract_version") or "").strip(),
                "overall_status": str(dispatch.get("overall_status") or "").strip(),
                "dispatch_ready": bool(dispatch.get("dispatch_ready")),
                "will_dispatch": bool(dispatch.get("will_dispatch")),
                "dispatch_mode": str(dispatch.get("dispatch_mode") or "").strip(),
                "backend_id": str(dispatch.get("backend_id") or "").strip(),
                "backend_status": str(dispatch.get("backend_status") or "").strip(),
                "backend_dispatch_ready": bool(dispatch.get("backend_dispatch_ready")),
                "gate_allowed": bool(dispatch.get("gate_allowed")),
                "prerequisites_ready": bool(dispatch.get("prerequisites_ready")),
                "relationship_seam_preserved": bool(dispatch.get("relationship_seam_preserved")),
                "blockers": list(dispatch.get("blockers") or []),
                "child_executor_dispatch_attempt_handoff": dict(
                    dispatch.get("child_executor_dispatch_attempt_handoff") or {}
                ),
                "dispatch_attempt_handoff": dict(
                    dispatch.get("dispatch_attempt_handoff") or {}
                ),
                "recommended_next_step": str(dispatch.get("recommended_next_step") or "").strip(),
            },
            "approval": {
                "request_count": 0,
                "pending_count": 0,
                "latest_request": None,
            },
            "audit": {
                "event_count": 0,
                "latest_event": None,
            },
            "main_chat": MainChatGovernanceOverviewBuilder.build_governance_main_chat_contract(trace_overview),
        }

    def _build_runtime_scope_contract(
        self,
        *,
        db: Any,
        conversation_id: int | None,
        plan_id: int | None,
        item_id: int | None,
        run_id: str | None = None,
        parent_run_id: str | None = None,
        child_run_id: str | None = None,
        scheduler_run_id: str | None = None,
    ) -> Dict[str, Any]:
        scope = {
            "runtime_core": True,
            "run_id": "",
            "parent_run_id": "",
            "child_run_id": "",
            "scheduler_run_id": "",
            "run_kind": "contract",
            "status": "not_started",
            "trace_count": 0,
            "latest_trace_event": None,
            "child_merge_intent": "",
            "child_merge_entities": [],
            "child_merge_entity_count": 0,
            "child_merge_focus_count": 0,
            "child_merge_action_count": 0,
            "child_merge_primary_entities": [],
            "child_merge_conclusion": "",
        }
        explicit_run_id = str(run_id or "").strip()
        explicit_parent_run_id = str(parent_run_id or "").strip()
        explicit_child_run_id = str(child_run_id or "").strip()
        explicit_scheduler_run_id = str(scheduler_run_id or "").strip()
        target = None
        if db is not None:
            target = self._resolve_runtime_target(db=db, conversation_id=conversation_id, plan_id=plan_id, item_id=item_id)
        scheduler_run = {}
        scheduler_service = None
        if target is not None:
            scheduler_service = SchedulerService(db)
            scheduler_run = dict(scheduler_service.serialize_scheduler_run(target) or {})
        resolved_run_id = explicit_run_id or str(scheduler_run.get("run_id") or "").strip()
        resolved_parent_run_id = explicit_parent_run_id or str(scheduler_run.get("parent_run_id") or "").strip()
        resolved_child_run_id = explicit_child_run_id or str(scheduler_run.get("child_run_id") or "").strip()
        resolved_scheduler_run_id = (
            explicit_scheduler_run_id
            or str(scheduler_run.get("scheduler_run_id") or "").strip()
            or str(scheduler_run.get("run_id") or "").strip()
        )

        if not any([resolved_run_id, resolved_parent_run_id, resolved_child_run_id, resolved_scheduler_run_id]):
            return scope

        scope["run_id"] = resolved_run_id
        scope["parent_run_id"] = resolved_parent_run_id
        scope["child_run_id"] = resolved_child_run_id
        scope["child_display_id"] = resolved_child_run_id
        scope["scheduler_run_id"] = resolved_scheduler_run_id
        scope["run_kind"] = str(scheduler_run.get("run_kind") or ("child" if resolved_child_run_id else "scheduler")).strip() or ("child" if resolved_child_run_id else "scheduler")
        scope["status"] = str(scheduler_run.get("state") or "not_started").strip() or "not_started"

        trace_events: list[dict[str, Any]] = []
        if scheduler_service is not None:
            try:
                trace_events = list(scheduler_service.get_run_trace(target) or [])
            except Exception:
                trace_events = []
            if resolved_run_id or resolved_child_run_id:
                try:
                    filtered_trace_events = scheduler_service.filter_run_trace(
                        target,
                        run_id=resolved_run_id or None,
                        child_run_id=resolved_child_run_id or None,
                        limit=100,
                    )
                    if filtered_trace_events:
                        trace_events = list(filtered_trace_events)
                except Exception:
                    pass

        scope["trace_count"] = len(trace_events)
        if trace_events:
            latest = dict(trace_events[-1])
            scope["latest_trace_event"] = {
                "event_type": str(latest.get("event_type") or "").strip(),
                "source": str(latest.get("source") or "").strip(),
                "severity": str(latest.get("severity") or "").strip(),
                "summary": str(latest.get("summary") or "").strip(),
                "detail": str(latest.get("detail") or "").strip(),
            }

        merge_parent_run_id = explicit_parent_run_id or resolved_scheduler_run_id or resolved_run_id
        if merge_parent_run_id:
            try:
                merged_semantics = self._build_child_executor_sdk_reader().summarize_child_executor_merged_semantics(merge_parent_run_id)
            except Exception:
                merged_semantics = {}
            parent_state = dict((merged_semantics or {}).get("parent_state_surface") or {})
            scope["child_merge_intent"] = str(parent_state.get("intent_label") or "").strip()
            scope["child_merge_entities"] = [
                str(item or "").strip()
                for item in (parent_state.get("primary_entities") or [])
                if str(item or "").strip()
            ]
            scope["child_merge_entity_count"] = int(parent_state.get("entity_count") or 0)
            scope["child_merge_focus_count"] = int(parent_state.get("focus_count") or 0)
            scope["child_merge_action_count"] = int(parent_state.get("action_count") or 0)
            scope["child_merge_primary_entities"] = [
                str(item or "").strip()
                for item in (parent_state.get("primary_entities") or [])
                if str(item or "").strip()
            ]
            scope["child_merge_conclusion"] = str(parent_state.get("latest_conclusion") or "").strip()
            scope["child_merge_section_source"] = str(parent_state.get("section_source") or "").strip()
            scope["child_merge_section_ids"] = [
                str(item or "").strip()
                for item in (parent_state.get("section_ids") or [])
                if str(item or "").strip()
            ]
            scope["child_merge_section_counts"] = dict(parent_state.get("section_counts") or {})
        return scope

    def _build_main_chat_trace_overview_contract(
        self,
        *,
        db: Any,
        conversation_id: int | None,
        plan_id: int | None,
        item_id: int | None,
    ) -> Dict[str, Any]:
        overview = MainChatGovernanceOverviewBuilder.build_trace_overview_contract()
        if db is None:
            overview["reason"] = "db_unavailable"
            return overview

        target = self._resolve_runtime_target(db=db, conversation_id=conversation_id, plan_id=plan_id, item_id=item_id)
        if target is None:
            overview["reason"] = "runtime_target_unresolved"
            return overview

        scheduler_service = SchedulerService(db)
        events = scheduler_service.filter_run_trace(target, source="query_control", limit=100)
        return MainChatGovernanceOverviewBuilder.build_trace_overview_from_events(
            events=events,
        )

    def _build_main_chat_query_detail_contract(
        self,
        *,
        db: Any,
        conversation_id: int | None,
        plan_id: int | None,
        item_id: int | None,
        query_id: str | None,
    ) -> Dict[str, Any]:
        detail = MainChatQueryReadModelBuilder.build_detail_contract(query_id)
        normalized_query_id = str(query_id or "").strip()
        if not normalized_query_id:
            detail["reason"] = "query_id_missing"
            return detail
        if db is None:
            detail["reason"] = "db_unavailable"
            return detail

        target = self._resolve_runtime_target(db=db, conversation_id=conversation_id, plan_id=plan_id, item_id=item_id)
        if target is None:
            detail["reason"] = "runtime_target_unresolved"
            return detail

        scheduler_service = SchedulerService(db)
        events = scheduler_service.filter_run_trace(target, source="query_control", limit=200)
        return MainChatQueryReadModelBuilder.build_detail_from_events(
            query_id=normalized_query_id,
            events=events,
        )

    def _build_main_chat_query_history_contract(
        self,
        *,
        db: Any,
        conversation_id: int | None,
        plan_id: int | None,
        item_id: int | None,
        page: int,
        page_size: int,
    ) -> Dict[str, Any]:
        history = MainChatQueryReadModelBuilder.build_history_contract(page, page_size)
        if db is None:
            history["reason"] = "db_unavailable"
            return history

        target = self._resolve_runtime_target(db=db, conversation_id=conversation_id, plan_id=plan_id, item_id=item_id)
        if target is None:
            history["reason"] = "runtime_target_unresolved"
            return history

        scheduler_service = SchedulerService(db)
        events = scheduler_service.filter_run_trace(target, source="query_control", limit=500)
        return MainChatQueryReadModelBuilder.build_history_from_events(
            events=events,
            page=page,
            page_size=page_size,
        )

    def _build_subagent_lane_recent_summary_contract(
        self,
        *,
        db: Any,
        conversation_id: int | None,
        plan_id: int | None,
        item_id: int | None,
    ) -> Dict[str, Any]:
        summary = SubagentLaneRecentSummaryBuilder.build_summary_contract()
        if db is None:
            summary["reason"] = "db_unavailable"
            return summary

        target = self._resolve_runtime_target(db=db, conversation_id=conversation_id, plan_id=plan_id, item_id=item_id)
        if target is None:
            summary["reason"] = "runtime_target_unresolved"
            return summary

        scheduler_service = SchedulerService(db)
        events = scheduler_service.filter_run_trace(target, source="query_control", limit=200)
        return SubagentLaneRecentSummaryBuilder.build_summary_from_events(
            events=events,
        )

    def _build_external_adapter_recent_summary_contract(
        self,
        *,
        db: Any,
        conversation_id: int | None,
        plan_id: int | None,
        item_id: int | None,
    ) -> Dict[str, Any]:
        summary = ExternalAdapterRecentSummaryBuilder.build_summary_contract()
        if db is None:
            summary["reason"] = "db_unavailable"
            return summary

        target = self._resolve_runtime_target(db=db, conversation_id=conversation_id, plan_id=plan_id, item_id=item_id)
        if target is None:
            summary["reason"] = "runtime_target_unresolved"
            return summary

        scheduler_service = SchedulerService(db)
        events = scheduler_service.filter_run_trace(target, source="query_control", limit=200)
        return ExternalAdapterRecentSummaryBuilder.build_summary_from_events(
            events=events,
        )

    def _build_subagent_lane_query_detail_contract(
        self,
        *,
        db: Any,
        conversation_id: int | None,
        plan_id: int | None,
        item_id: int | None,
        query_id: str | None,
    ) -> Dict[str, Any]:
        detail = SubagentLaneQueryDetailBuilder.build_detail_contract(query_id)
        normalized_query_id = str(query_id or "").strip()
        if not normalized_query_id:
            detail["reason"] = "query_id_missing"
            return detail
        if db is None:
            detail["reason"] = "db_unavailable"
            return detail

        target = self._resolve_runtime_target(db=db, conversation_id=conversation_id, plan_id=plan_id, item_id=item_id)
        if target is None:
            detail["reason"] = "runtime_target_unresolved"
            return detail

        scheduler_service = SchedulerService(db)
        events = scheduler_service.filter_run_trace(target, source="query_control", limit=200)
        return SubagentLaneQueryDetailBuilder.build_detail_from_events(
            query_id=normalized_query_id,
            events=events,
        )

    def _resolve_runtime_target(
        self,
        *,
        db: Any,
        conversation_id: int | None,
        plan_id: int | None,
        item_id: int | None,
    ) -> Any:
        plan = None
        if plan_id is not None:
            plan = (
                db.query(PlanRunRecord)
                .filter(PlanRunRecord.id == plan_id)
                .first()
            )
        elif conversation_id is not None:
            plan = (
                db.query(PlanRunRecord)
                .filter(PlanRunRecord.conversation_id == conversation_id)
                .order_by(PlanRunRecord.updated_at.desc())
                .first()
            )
        if plan is None:
            return None
        if item_id is not None:
            return next((item for item in plan.items if item.id == item_id), None)
        active_item = next(
            (
                item for item in plan.items
                if str(getattr(item.status, "value", item.status)) == "in_progress"
            ),
            None,
        )
        if active_item is not None:
            return active_item
        if getattr(plan, "active_item_id", None) is not None:
            return next((item for item in plan.items if item.id == plan.active_item_id), None)
        return next(iter(plan.items or []), None)

    def update_runtime_profile(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(payload or {})
        all_models = self._list_all_models()
        available_model_names = {item["name"] for item in all_models}
        provider_by_model = {
            item["name"]: str(item.get("provider") or "unknown")
            for item in all_models
        }
        available_provider_ids = sorted({provider_by_model[item["name"]] for item in all_models})
        current_effective = self.config_service.get_effective_config()

        requested_enabled = payload.get("enabled_providers")
        if requested_enabled is None:
            enabled_provider_ids = self._resolve_enabled_provider_ids(available_provider_ids, current_effective)
        else:
            if not isinstance(requested_enabled, list):
                raise ValueError("enabled_providers 必须是 provider_id 字符串列表")
            unknown_provider_ids = sorted(
                {
                    str(item or "").strip()
                    for item in requested_enabled
                    if str(item or "").strip() and str(item or "").strip() not in available_provider_ids
                }
            )
            if unknown_provider_ids:
                raise ValueError(f"enabled_providers 包含未知 provider: {', '.join(unknown_provider_ids)}")
            enabled_provider_ids = self._resolve_enabled_provider_ids(
                available_provider_ids,
                {"enabled_providers": requested_enabled},
            )

        candidate_default_model = str(
            payload.get("default_model")
            or current_effective.get("default_model", DEFAULT_MODEL)
        ).strip()
        if "default_model" in payload:
            if payload["default_model"] not in available_model_names:
                raise ValueError(f"default_model `{payload['default_model']}` 不在当前运行时模型目录中")
        if candidate_default_model:
            model_provider = provider_by_model.get(candidate_default_model)
            if model_provider and model_provider not in enabled_provider_ids:
                raise ValueError(f"default_model `{candidate_default_model}` 所属 provider 当前未启用，请先启用对应 provider 或切换默认模型")

        bootstrap_payload = {}
        if "embedded_workspace_store_mode" in payload:
            bootstrap_payload["embedded_workspace_store_mode"] = payload["embedded_workspace_store_mode"]
        profile_payload = {
            key: value
            for key, value in payload.items()
            if key != "embedded_workspace_store_mode"
        }
        if profile_payload:
            self.config_service.update_overrides(profile_payload)
        if bootstrap_payload:
            self.update_embedded_runtime_bootstrap(
                bootstrap_payload
            )
        return self.get_runtime_profile()


_runtime_surface_service: RuntimeSurfaceService | None = None


def get_runtime_surface_service() -> RuntimeSurfaceService:
    global _runtime_surface_service
    if _runtime_surface_service is None:
        _runtime_surface_service = RuntimeSurfaceService()
    return _runtime_surface_service
