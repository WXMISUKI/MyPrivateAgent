"""Shared runtime dependency seam for embedded harness defaults."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import TYPE_CHECKING, Any

try:
    from .adapters import get_embedded_workspace_store, get_embedded_workspace_store_mode
    from .continuation_registry import EmbeddedContinuationRegistry, get_embedded_continuation_registry
    from .persistence import EmbeddedRunWorkspaceStore, build_embedded_sdk_persistence_interface
    from .worker_ownership import (
        build_worker_ownership_contract,
        build_worker_ownership_operational_readiness_contract,
        build_worker_ownership_production_enablement_runtime_config_consumer_contract,
        get_runtime_worker_ownership_store,
        get_worker_ownership_store_mode,
    )
    from ..config import DB_MODE
except ImportError:  # pragma: no cover - package import compatibility
    from backend.agent_framework.adapters import get_embedded_workspace_store, get_embedded_workspace_store_mode
    from backend.agent_framework.continuation_registry import (
        EmbeddedContinuationRegistry,
        get_embedded_continuation_registry,
    )
    from backend.agent_framework.persistence import EmbeddedRunWorkspaceStore, build_embedded_sdk_persistence_interface
    from backend.agent_framework.worker_ownership import (
        build_worker_ownership_contract,
        build_worker_ownership_operational_readiness_contract,
        build_worker_ownership_production_enablement_runtime_config_consumer_contract,
        get_runtime_worker_ownership_store,
        get_worker_ownership_store_mode,
    )
    from backend.config import DB_MODE

if TYPE_CHECKING:  # pragma: no cover - import only for typing
    from .harness import AgentHarnessFacade
    from .sdk import EmbeddedAgentRuntimeSDK


@dataclass(frozen=True)
class EmbeddedRuntimeDependencies:
    workspace_store: EmbeddedRunWorkspaceStore
    continuation_registry: EmbeddedContinuationRegistry
    worker_ownership_store: Any | None = None


@dataclass(frozen=True)
class EmbeddedRuntimeFactory:
    dependencies: EmbeddedRuntimeDependencies
    worker_ownership_production_enablement_config: dict[str, Any] | None = None

    def configure_worker_ownership_production_enablement_config(
        self,
        config: dict[str, Any] | None,
    ) -> "EmbeddedRuntimeFactory":
        return EmbeddedRuntimeFactory(
            dependencies=self.dependencies,
            worker_ownership_production_enablement_config=(
                dict(config) if isinstance(config, dict) else None
            ),
        )

    def create_sdk(self, **kwargs: Any) -> "EmbeddedAgentRuntimeSDK":
        if kwargs.get("runtime_dependencies") is None:
            kwargs["runtime_dependencies"] = self.dependencies
        try:
            from .sdk import EmbeddedAgentRuntimeSDK
        except ImportError:  # pragma: no cover - package import compatibility
            from backend.agent_framework.sdk import EmbeddedAgentRuntimeSDK
        return EmbeddedAgentRuntimeSDK(**kwargs)

    def create_agent(self, **kwargs: Any) -> "AgentHarnessFacade":
        if kwargs.get("runtime_dependencies") is None:
            kwargs["runtime_dependencies"] = self.dependencies
        try:
            from .harness import create_agent
        except ImportError:  # pragma: no cover - package import compatibility
            from backend.agent_framework.harness import create_agent
        return create_agent(**kwargs)

    def build_runtime_contract(self) -> dict[str, Any]:
        workspace_store = self.dependencies.workspace_store
        continuation_registry = self.dependencies.continuation_registry
        worker_ownership_store = self.dependencies.worker_ownership_store
        describe_backend = getattr(workspace_store, "describe_backend", None)
        workspace_backend = dict(describe_backend() or {}) if callable(describe_backend) else {}
        build_catalog = getattr(continuation_registry, "build_catalog", None)
        registry_catalog = dict(build_catalog() or {}) if callable(build_catalog) else {}
        build_ownership_contract = getattr(worker_ownership_store, "build_contract", None)
        ownership_contract = (
            dict(build_ownership_contract() or {})
            if callable(build_ownership_contract)
            else build_worker_ownership_contract()
        ) if worker_ownership_store is not None else {
            "contract_version": "phase-ii-runtime-worker-ownership-v1",
            "adapter_kind": "",
            "operations": [],
            "fail_closed_reasons": [],
            "durable": False,
            "non_executable_payload": True,
        }
        db_mode_source = "env" if os.getenv("DB_MODE") is not None else "default"
        current_workspace_store_mode = get_embedded_workspace_store_mode()
        embedded_workspace_store_mode_source = (
            "env" if os.getenv("EMBEDDED_WORKSPACE_STORE_MODE") is not None else "derived_from_db_mode"
        )
        worker_ownership_store_mode = get_worker_ownership_store_mode()
        worker_ownership_store_mode_source = (
            "env" if os.getenv("WORKER_OWNERSHIP_STORE_MODE") is not None else "default"
        )
        worker_ownership_operational_readiness = build_worker_ownership_operational_readiness_contract(
            ownership_contract=ownership_contract,
            store_mode=worker_ownership_store_mode,
            auto_claim_enabled=False,
        )
        production_enablement_config = dict(
            self.worker_ownership_production_enablement_config or {}
        )
        production_enablement_dry_run = production_enablement_config.pop(
            "composition_dry_run", None
        )
        production_enablement_runtime_config_consumer = (
            build_worker_ownership_production_enablement_runtime_config_consumer_contract(
                config=production_enablement_config,
                composition_dry_run_contract=(
                    dict(production_enablement_dry_run)
                    if isinstance(production_enablement_dry_run, dict)
                    else None
                ),
            )
        )
        persistence_interface = build_embedded_sdk_persistence_interface(
            workspace_backend,
            worker_ownership_production_gate=dict(
                worker_ownership_operational_readiness.get("production_gate") or {}
            ),
            worker_ownership_production_enablement_runtime_config_consumer=(
                production_enablement_runtime_config_consumer
            ),
        )
        durable = bool(persistence_interface.get("durable"))
        fallback_active = bool(persistence_interface.get("fallback_active"))
        persistence_posture = str(persistence_interface.get("persistence_posture") or "").strip()
        default_runtime_mode = "memory_preview" if persistence_posture == "memory_preview" else "durable_default"
        if persistence_posture == "durable_degraded":
            default_runtime_mode = "durable_degraded"
        recovery_posture = (
            "cross_process_candidate"
            if bool(persistence_interface.get("cross_process_candidate"))
            else ("degraded_fallback" if fallback_active else "in_process_only")
        )
        default_recovery_mode = (
            "registry_backed"
            if durable and not fallback_active
            else ("unavailable" if fallback_active or not durable else "in_process")
        )
        default_probe_reason = "descriptor_missing"
        cross_process_block_reason = (
            ""
            if durable and not fallback_active
            else ("workspace_backend_fallback_active" if fallback_active else "workspace_backend_not_durable")
        )
        return {
            "contract_version": "phase-ii-embedded-runtime-factory-v1",
            "runtime_backend": "EmbeddedAgentRuntimeSDK",
            "shared_default_runtime": True,
            "dependency_sources": ["workspace_store", "continuation_registry", "worker_ownership_store"],
            "default_recovery_capabilities": {
                "recovery_mode": default_recovery_mode,
                "requires_durable_workspace": default_recovery_mode == "registry_backed",
                "requires_registry_bindings": default_recovery_mode == "registry_backed",
            },
            "default_runtime_profile": {
                "db_mode": DB_MODE,
                "db_mode_source": db_mode_source,
                "embedded_workspace_store_mode": current_workspace_store_mode,
                "embedded_workspace_store_mode_source": embedded_workspace_store_mode_source,
                "worker_ownership_store_mode": worker_ownership_store_mode,
                "worker_ownership_store_mode_source": worker_ownership_store_mode_source,
                "default_runtime_mode": default_runtime_mode,
                "recovery_posture": recovery_posture,
                "persistence_posture": persistence_posture,
                "workspace_strategy_rule": "memory_only_if_db_mode_memory_else_strict_sql",
                "durable_by_default": durable and not fallback_active,
                "recommended_bootstrap": "EmbeddedRuntimeFactory",
                "configurable_bootstrap_knobs": [
                    "DB_MODE",
                    "EMBEDDED_WORKSPACE_STORE_MODE",
                    "WORKER_OWNERSHIP_STORE_MODE",
                ],
                "hot_reloadable_bootstrap_knobs": [
                    "EMBEDDED_WORKSPACE_STORE_MODE",
                    "WORKER_OWNERSHIP_STORE_MODE",
                ],
                "restart_required_bootstrap_knobs": [
                    "DB_MODE",
                ],
            },
            "workspace_backend": {
                "backend_kind": str(workspace_backend.get("backend_kind") or "").strip(),
                "backend_mode": str(workspace_backend.get("backend_mode") or "").strip(),
                "durable": bool(workspace_backend.get("durable")),
                "operation_fallback_allowed": bool(workspace_backend.get("operation_fallback_allowed")),
                "fallback_active": bool(workspace_backend.get("fallback_active")),
                "fallback_reason": str(workspace_backend.get("fallback_reason") or "").strip(),
                "last_error": str(workspace_backend.get("last_error") or "").strip(),
            },
            "persistence_interface": persistence_interface,
            "production_recovery_gate": dict(persistence_interface.get("production_recovery_gate") or {}),
            "continuation_registry": {
                "registry_type": str(registry_catalog.get("registry_type") or "").strip(),
                "total_bindings": int(registry_catalog.get("total_bindings") or 0),
            },
            "worker_ownership": {
                "contract_version": str(ownership_contract.get("contract_version") or "").strip(),
                "available": worker_ownership_store is not None,
                "adapter_kind": str(ownership_contract.get("adapter_kind") or "").strip(),
                "durable": bool(ownership_contract.get("durable")),
                "enforcement_mode": "opt_in_descriptor_evidence",
                "operations": list(ownership_contract.get("operations") or []),
                "fail_closed_reasons": list(ownership_contract.get("fail_closed_reasons") or []),
                "operational_readiness": worker_ownership_operational_readiness,
                "production_gate": dict(worker_ownership_operational_readiness.get("production_gate") or {}),
                "production_enablement_runtime_config_consumer": (
                    production_enablement_runtime_config_consumer
                ),
            },
            "default_recovery_expectation": {
                "contract_version": "phase-ii-default-recovery-expectation-v1",
                "probe_contract_version": "phase-ii-run-recovery-v1",
                "descriptor_required": True,
                "default_probe_recoverable": False,
                "default_probe_reason": default_probe_reason,
                "cross_process_candidate": durable and not fallback_active,
                "cross_process_block_reason": cross_process_block_reason,
                "workspace_backend_kind": str(workspace_backend.get("backend_kind") or "").strip(),
                "workspace_backend_mode": str(workspace_backend.get("backend_mode") or "").strip(),
            },
            "recovery_capabilities": [
                "runtime.continuation_binding_catalog",
                "runtime.run_recovery_probe",
                "runtime.run_resume",
            ],
            "factory_methods": ["create_sdk", "create_agent"],
        }


def get_default_embedded_runtime_dependencies() -> EmbeddedRuntimeDependencies:
    return EmbeddedRuntimeDependencies(
        workspace_store=get_embedded_workspace_store(),
        continuation_registry=get_embedded_continuation_registry(),
        worker_ownership_store=get_runtime_worker_ownership_store(),
    )


def get_default_embedded_runtime_factory() -> EmbeddedRuntimeFactory:
    return EmbeddedRuntimeFactory(
        dependencies=get_default_embedded_runtime_dependencies(),
    )


def create_default_embedded_runtime_sdk(**kwargs: Any) -> "EmbeddedAgentRuntimeSDK":
    return get_default_embedded_runtime_factory().create_sdk(**kwargs)
