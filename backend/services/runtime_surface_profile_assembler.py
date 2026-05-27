"""Top-level runtime profile assembler for RuntimeSurfaceService."""

from __future__ import annotations

from typing import Any, Dict

try:
    from services.runtime_surface_builders import EmbeddedRuntimeContractBundleBuilder, ProviderCatalogBuilder
    from services.runtime_surface_profile_context import RuntimeSurfaceProfileContextAssembler
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.runtime_surface_builders import EmbeddedRuntimeContractBundleBuilder, ProviderCatalogBuilder
    from backend.services.runtime_surface_profile_context import RuntimeSurfaceProfileContextAssembler


class RuntimeSurfaceProfileAssembler:
    """Assemble the top-level runtime profile contract for RuntimeSurfaceService."""

    @classmethod
    def assemble(
        cls,
        service: Any,
        *,
        db: Any = None,
        conversation_id: int | None = None,
        plan_id: int | None = None,
        item_id: int | None = None,
        query_id: str | None = None,
        run_id: str | None = None,
        parent_run_id: str | None = None,
        child_run_id: str | None = None,
        scheduler_run_id: str | None = None,
        auth_mode_default: str = "",
        default_model_default: str = "",
    ) -> Dict[str, Any]:
        effective_config = service.config_service.get_effective_config()
        all_models = service._list_all_models()
        provider_catalog = ProviderCatalogBuilder.build_catalog(
            all_models=all_models,
            effective_config=effective_config,
            config_layers=service.config_service.get_config_layers(),
            override_config=service.config_service.load_overrides(),
        )
        models = provider_catalog["models"]
        providers = provider_catalog["providers"]
        config_layers = provider_catalog["config_layers"]

        profile_context = RuntimeSurfaceProfileContextAssembler.assemble(
            service,
            db=db,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
            query_id=query_id,
            run_id=run_id,
            parent_run_id=parent_run_id,
            child_run_id=child_run_id,
            scheduler_run_id=scheduler_run_id,
        )
        runtime_scope = profile_context.runtime_scope or {}

        main_chat_trace_overview = service._build_main_chat_trace_overview_contract(
            db=db,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
        )
        main_chat_query_detail = service._build_main_chat_query_detail_contract(
            db=db,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
            query_id=query_id,
        )
        external_adapter_recent_summary = service._build_external_adapter_recent_summary_contract(
            db=db,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
        )
        channel_promotion_gate = service.get_channel_promotion_gate(
            db=db,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
        )
        recovery_target_run_id = profile_context.recovery_target_run_id
        run_recovery = (
            service.get_run_recovery(run_id=recovery_target_run_id)
            if recovery_target_run_id
            else service._build_run_recovery_contract()
        )
        command_contract = service.command_registry_service.build_runtime_contract()
        child_executor_preflight = service._build_child_executor_preflight_contract(command_contract)
        child_executor_promotion_gate = service._build_child_executor_promotion_gate_contract(
            command_contract,
            child_executor_preflight,
        )
        child_executor_dispatch_contract = service._build_child_executor_dispatch_contract(
            command_contract,
            child_executor_promotion_gate,
        )
        embedded_runtime_factory = service.runtime_factory.build_runtime_contract()
        embedded_runtime_bundle = EmbeddedRuntimeContractBundleBuilder.build_profile_bundle(embedded_runtime_factory)

        profile = {
            "agent_mode": "general_demo",
            "auth_mode": effective_config.get("auth_mode", auth_mode_default),
            "default_model": effective_config.get("default_model", default_model_default),
            "failover_thresholds": effective_config.get("failover_thresholds") or {"medium": 0.2, "high": 0.4},
            "runtime_core": service._build_runtime_core_contract(runtime_scope=runtime_scope),
            "child_executor_preflight": child_executor_preflight,
            "child_executor_backend_registry": child_executor_preflight.get("backend_registry") or {},
            "child_executor_promotion_gate": child_executor_promotion_gate,
            "child_executor_dispatch_contract": child_executor_dispatch_contract,
            "default_runtime_recovery": embedded_runtime_bundle["default_runtime_recovery"],
            "governance_overview": service._build_governance_overview_contract(
                main_chat_trace_overview=main_chat_trace_overview,
                runtime_scope=runtime_scope,
                run_recovery=run_recovery,
                default_runtime_recovery=embedded_runtime_bundle["default_runtime_recovery"],
                child_executor_preflight=child_executor_preflight,
                child_executor_promotion_gate=child_executor_promotion_gate,
                child_executor_dispatch_contract=child_executor_dispatch_contract,
            ),
            "run_recovery": run_recovery,
            "main_chat_trace_overview": main_chat_trace_overview,
            "main_chat_query_detail": main_chat_query_detail,
            "external_adapter_recent_summary": external_adapter_recent_summary,
            "channel_promotion_gate": channel_promotion_gate,
            "tool_runtime": service.tool_runtime_service.build_runtime_contract(),
            "mcp_runtime": service.mcp_runtime_service.build_runtime_contract(),
            "adapter_health": service.tool_runtime_service.build_adapter_health_contract(),
            "models": models,
            "providers": providers,
            "capability_contract": service.capability_profile_service.build_runtime_contract(),
            "skill_contract": service.skill_runtime_service.build_runtime_contract(),
            "memory_contract": service.agent_memory_service.build_runtime_contract(),
            "subagent_contract": service.subagent_runtime_service.build_runtime_contract(),
            "hook_contract": service.agent_hook_service.build_runtime_contract(),
            "command_contract": command_contract,
            "embedded_runtime_factory": embedded_runtime_bundle["embedded_runtime_factory"],
            "embedded_runtime_bootstrap": embedded_runtime_bundle["embedded_runtime_bootstrap"],
            "embedded_runtime_boundaries": service._build_embedded_runtime_boundaries_contract(command_contract),
            "runtime_contract_gate": service.contract_gate_service.build_runtime_contract(),
            "self_improvement_ledger": service.self_improvement_ledger_service.build_runtime_contract(db=db),
            "query_control_plane": service.query_control_plane_service.build_runtime_contract(),
            "config_layers": config_layers,
            "auth_mode_contract": {
                "current_mode": effective_config.get("auth_mode", auth_mode_default),
                "demo_guest_description": "免登录直达，适合通用框架演示、能力盘点与本地调试。",
                "business_auth_description": "登录页作为正式入口，适合后续接入真实鉴权、组织和权限体系。",
            },
        }
        profile["contract_snapshot"] = service.contract_snapshot_service.build_snapshot(profile)
        return profile
