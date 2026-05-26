"""Runtime contract smoke for Phase C quality gate."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


def _bootstrap_path() -> None:
    root = Path(__file__).resolve().parents[2]
    candidate = str(root)
    if candidate not in sys.path:
        sys.path.insert(0, candidate)


_bootstrap_path()

try:
    from agent_framework.adapters import SQLAlchemyEmbeddedRunWorkspaceStore
    from agent_framework.continuation_registry import InMemoryEmbeddedContinuationRegistry
    from agent_framework.durable_recovery_loader import DurableRecoveryLoader
    from agent_framework.loader_handoff import build_durable_loader_execution_handoff_decision
    from agent_framework.child_executor_dispatcher import ChildExecutorDispatcher
    from agent_framework.child_executor_dispatcher import (
        build_child_executor_dispatch_attempt_handoff_contract,
        build_child_executor_dispatch_result_handoff_contract,
        build_child_executor_dispatch_result_retry_audit_policy_contract,
    )
    from agent_framework.child_executor_backends import (
        build_child_executor_backend_registry_contract,
        build_child_executor_sandbox_worker_backend_entry,
    )
    from agent_framework.child_executor_sandbox_worker_backend import (
        build_sandbox_dispatch_attempt_envelope,
        build_sandbox_worker_backend_adapter_contract,
    )
    from agent_framework.harness import create_agent
    from agent_framework.persistence import InMemoryEmbeddedRunWorkspaceStore
    from agent_framework.production_recovery_policy import (
        build_production_recovery_registry_checkpoint_policy_contract,
    )
    from agent_framework.recovery_operations import build_recovery_operation_contract
    from agent_framework.runtime_dependencies import EmbeddedRuntimeDependencies, EmbeddedRuntimeFactory
    from agent_framework.sdk import (
        EmbeddedAgentRuntimeSDK,
        build_child_executor_dispatch_contract,
        validate_embedded_sdk_event_payloads,
    )
    from agent_framework.tools import ToolSpec
    from agent_framework.worker_ownership import (
        InMemoryRuntimeWorkerOwnershipStore,
        SQLAlchemyRuntimeWorkerOwnershipStore,
        WorkerOwnershipRenewalSupervisor,
        WorkerOwnershipStoreFallback,
    )
    from agent_framework import worker_ownership as worker_ownership_module
    from agent_server import create_app
    from agent_server.config import AgentServerBootstrapConfig, AgentServerConfig, AgentServerUIConfig
    from database import Base
    from harness.tool_registry import ToolRegistry
    from services.runtime_surface_builders import SubagentLaneQueryDetailBuilder
    from services.runtime_surface_service import RuntimeSurfaceService
    from services.tool_runtime_service import ToolRuntimeService
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_framework.adapters import SQLAlchemyEmbeddedRunWorkspaceStore
    from backend.agent_framework.continuation_registry import InMemoryEmbeddedContinuationRegistry
    from backend.agent_framework.durable_recovery_loader import DurableRecoveryLoader
    from backend.agent_framework.loader_handoff import build_durable_loader_execution_handoff_decision
    from backend.agent_framework.child_executor_dispatcher import ChildExecutorDispatcher
    from backend.agent_framework.child_executor_dispatcher import (
        build_child_executor_dispatch_attempt_handoff_contract,
        build_child_executor_dispatch_result_handoff_contract,
        build_child_executor_dispatch_result_retry_audit_policy_contract,
    )
    from backend.agent_framework.child_executor_backends import (
        build_child_executor_backend_registry_contract,
        build_child_executor_sandbox_worker_backend_entry,
    )
    from backend.agent_framework.child_executor_sandbox_worker_backend import (
        build_sandbox_dispatch_attempt_envelope,
        build_sandbox_worker_backend_adapter_contract,
    )
    from backend.agent_framework.harness import create_agent
    from backend.agent_framework.persistence import InMemoryEmbeddedRunWorkspaceStore
    from backend.agent_framework.production_recovery_policy import (
        build_production_recovery_registry_checkpoint_policy_contract,
    )
    from backend.agent_framework.recovery_operations import build_recovery_operation_contract
    from backend.agent_framework.runtime_dependencies import EmbeddedRuntimeDependencies, EmbeddedRuntimeFactory
    from backend.agent_framework.sdk import (
        EmbeddedAgentRuntimeSDK,
        build_child_executor_dispatch_contract,
        validate_embedded_sdk_event_payloads,
    )
    from backend.agent_framework.tools import ToolSpec
    from backend.agent_framework.worker_ownership import (
        InMemoryRuntimeWorkerOwnershipStore,
        SQLAlchemyRuntimeWorkerOwnershipStore,
        WorkerOwnershipRenewalSupervisor,
        WorkerOwnershipStoreFallback,
    )
    from backend.agent_framework import worker_ownership as worker_ownership_module
    from backend.agent_server import create_app
    from backend.agent_server.config import AgentServerBootstrapConfig, AgentServerConfig, AgentServerUIConfig
    from backend.database import Base
    from backend.harness.tool_registry import ToolRegistry
    from backend.services.runtime_surface_builders import SubagentLaneQueryDetailBuilder
    from backend.services.runtime_surface_service import RuntimeSurfaceService
    from backend.services.tool_runtime_service import ToolRuntimeService


def main() -> int:
    previous_fake_adapter_flag = os.environ.get("ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER")
    os.environ["ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER"] = "true"
    previous_fake_adapter_module_flags: dict[str, dict[str, object]] = {}
    _force_local_fake_adapter_for_smoke(previous_fake_adapter_module_flags)
    app = create_app(
        config=AgentServerConfig(
            bootstrap=AgentServerBootstrapConfig(load_environment=True, init_database=False),
            ui=AgentServerUIConfig(enabled=False, mode="disabled"),
        )
    )
    _force_local_fake_adapter_for_smoke(previous_fake_adapter_module_flags)
    checks = []
    with TestClient(app) as client:
        runtime_profile_response = client.get("/api/runtime-profile")
        runtime_profile_payload = runtime_profile_response.json()
        runtime_profile_ok = (
            runtime_profile_response.status_code == 200
            and str(((runtime_profile_payload.get("contract_snapshot") or {}).get("overall_status") or "")).strip() == "healthy"
        )
        artifact_schema = ((runtime_profile_payload.get("runtime_contract_gate") or {}).get("runtime_contract_artifact_schema") or {})
        if not isinstance(artifact_schema, dict):
            artifact_schema = {}
        artifact_schema_missing_fields = [
            str(field_name)
            for field_name in (artifact_schema.get("summary_missing_fields") or [])
            if str(field_name or "").strip()
        ]
        checks.append(
            {
                "name": "runtime_profile_contract_snapshot",
                "ok": runtime_profile_ok,
                "status_code": runtime_profile_response.status_code,
                "contract_snapshot_status": (runtime_profile_payload.get("contract_snapshot") or {}).get("overall_status"),
                "adapter_health_status": (runtime_profile_payload.get("adapter_health") or {}).get("overall_status"),
                "runtime_contract_artifact_schema_status": str(artifact_schema.get("overall_status") or "").strip(),
                "runtime_contract_artifact_schema_missing_field_count": len(artifact_schema_missing_fields),
                "runtime_contract_artifact_schema_missing_fields": artifact_schema_missing_fields,
                "failure_reason": "" if runtime_profile_ok else "contract_snapshot_not_healthy",
            }
        )

        pilot_run_response = client.post(
            "/api/runtime-framework-adapters/pilot-run",
            json={
                "adapter_id": "local_fake_framework",
                "run_id": "smoke-runtime-contract-pilot",
                "messages": [{"role": "user", "content": "生成巡检计划"}],
                "execution_context": {"run_kind": "framework_adapter"},
            },
        )
        pilot_run_payload = pilot_run_response.json()
        pilot_run_ok = (
            pilot_run_response.status_code == 200
            and str(pilot_run_payload.get("adapter_id") or "").strip() == "local_fake_framework"
            and len(pilot_run_payload.get("events") or []) >= 3
        )
        checks.append(
            {
                "name": "framework_adapter_pilot_run",
                "ok": pilot_run_ok,
                "status_code": pilot_run_response.status_code,
                "adapter_id": pilot_run_payload.get("adapter_id"),
                "event_count": len(pilot_run_payload.get("events") or []),
                "final_output": str(pilot_run_payload.get("final_output") or "")[:200],
                "failure_reason": "" if pilot_run_ok else "pilot_run_contract_incomplete",
            }
        )

        sdk_events = _build_embedded_sdk_event_sample()
        sdk_event_validation = validate_embedded_sdk_event_payloads(sdk_events)
        sdk_event_payloads_ok = bool(sdk_event_validation.get("valid"))
        observed_status_kinds = sorted(
            {
                str(event.get("status_kind") or "").strip()
                for event in sdk_events
                if str(event.get("status_kind") or "").strip()
            }
        )
        checks.append(
            {
                "name": "embedded_sdk_event_payloads",
                "ok": sdk_event_payloads_ok,
                "event_count": len(sdk_events),
                "observed_status_kinds": observed_status_kinds,
                "checked_event_count": sdk_event_validation.get("checked_event_count", 0),
                "missing_payload_count": sdk_event_validation.get("missing_payload_count", 0),
                "missing_payloads": sdk_event_validation.get("missing_payloads", []),
                "failure_reason": "" if sdk_event_payloads_ok else "sdk_event_payload_contract_incomplete",
            }
        )

        durable_recovery_result = _run_embedded_sdk_durable_recovery_check()
        checks.append(
            {
                "name": "embedded_sdk_durable_recovery",
                **durable_recovery_result,
            }
        )
        checkpoint_cursor_result = _run_durable_checkpoint_resume_cursor_check()
        checks.append(
            {
                "name": "durable_checkpoint_resume_cursor",
                **checkpoint_cursor_result,
            }
        )
        durable_loader_result = _run_durable_recovery_loader_contract_check()
        checks.append(
            {
                "name": "durable_recovery_loader",
                **durable_loader_result,
            }
        )
        persistence_posture_result = _run_embedded_sdk_persistence_posture_check()
        checks.append(
            {
                "name": "embedded_sdk_persistence_posture",
                **persistence_posture_result,
            }
        )
        ownership_store_mode_result = _run_worker_ownership_store_mode_contract_check()
        checks.append(
            {
                "name": "worker_ownership_store_mode",
                **ownership_store_mode_result,
            }
        )
        recovery_retry_result = _run_recovery_retry_evidence_contract_check()
        checks.append(
            {
                "name": "recovery_retry_evidence",
                **recovery_retry_result,
            }
        )
        recovery_retry_scheduler_result = _run_recovery_retry_scheduler_contract_check()
        checks.append(
            {
                "name": "recovery_retry_scheduler",
                **recovery_retry_scheduler_result,
            }
        )
        child_executor_gate_result = _run_child_executor_promotion_gate_contract_check(runtime_profile_payload)
        checks.append(
            {
                "name": "child_executor_promotion_gate",
                **child_executor_gate_result,
            }
        )
        child_executor_dispatch_result = _run_child_executor_dispatch_contract_check(runtime_profile_payload)
        checks.append(
            {
                "name": "child_executor_dispatch_contract",
                **child_executor_dispatch_result,
            }
        )
        child_executor_dispatcher_result = _run_child_executor_dispatcher_contract_check()
        checks.append(
            {
                "name": "child_executor_dispatcher",
                **child_executor_dispatcher_result,
            }
        )
        child_executor_dispatch_result_handoff_result = (
            _run_child_executor_dispatch_result_handoff_contract_check()
        )
        checks.append(
            {
                "name": "child_executor_dispatch_result_handoff",
                **child_executor_dispatch_result_handoff_result,
            }
        )
        child_executor_dispatch_result_retry_audit_result = (
            _run_child_executor_dispatch_result_retry_audit_policy_contract_check()
        )
        checks.append(
            {
                "name": "child_executor_dispatch_result_retry_audit_policy",
                **child_executor_dispatch_result_retry_audit_result,
            }
        )
        child_executor_sandbox_backend_result = _run_child_executor_sandbox_backend_contract_check()
        checks.append(
            {
                "name": "child_executor_sandbox_backend",
                **child_executor_sandbox_backend_result,
            }
        )
        run_recovery_result = _run_runtime_surface_run_recovery_contract_check()
        checks.append(
            {
                "name": "runtime_surface_run_recovery",
                **run_recovery_result,
            }
        )
        approval_lifecycle_result = _run_approval_lifecycle_recovery_alignment_check()
        checks.append(
            {
                "name": "approval_lifecycle_recovery_alignment",
                **approval_lifecycle_result,
            }
        )
        approved_tool_bridge_result = _run_runtime_approved_tool_execution_bridge_check()
        checks.append(
            {
                "name": "runtime_approved_tool_execution_bridge",
                **approved_tool_bridge_result,
            }
        )
        sdk_tool_bridge_result = _run_sdk_tool_runtime_execution_bridge_check()
        checks.append(
            {
                "name": "sdk_tool_runtime_execution_bridge",
                **sdk_tool_bridge_result,
            }
        )
        tool_timeout_retry_result = _run_tool_runtime_timeout_retry_contract_check()
        checks.append(
            {
                "name": "tool_runtime_timeout_retry",
                **tool_timeout_retry_result,
            }
        )
        subagent_lane_detail_result = _run_subagent_lane_query_detail_contract_check(client)
        checks.append(
            {
                "name": "subagent_lane_query_detail",
                **subagent_lane_detail_result,
            }
        )

    payload = {
        "status": "ok" if all(item["ok"] for item in checks) else "fail",
        "checks": checks,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    exit_code = 0 if payload["status"] == "ok" else 1
    if previous_fake_adapter_flag is None:
        os.environ.pop("ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER", None)
    else:
        os.environ["ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER"] = previous_fake_adapter_flag
    _restore_local_fake_adapter_module_flags(previous_fake_adapter_module_flags)
    return exit_code


def _force_local_fake_adapter_for_smoke(previous_flags: dict[str, dict[str, object]]) -> None:
    os.environ["ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER"] = "true"
    for module_name in (
        "config",
        "backend.config",
        "agent_framework.framework_adapters",
        "backend.agent_framework.framework_adapters",
        "routers.health",
        "backend.routers.health",
    ):
        module = sys.modules.get(module_name)
        if module is None:
            continue
        module_flags = previous_flags.setdefault(module_name, {})
        if hasattr(module, "ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER"):
            module_flags.setdefault(
                "ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER",
                getattr(module, "ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER"),
            )
            setattr(module, "ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER", True)
        if hasattr(module, "_framework_adapter_registry"):
            module_flags.setdefault("_framework_adapter_registry", getattr(module, "_framework_adapter_registry"))
            setattr(module, "_framework_adapter_registry", None)


class _SmokeDurableWorkspaceStore(InMemoryEmbeddedRunWorkspaceStore):
    def describe_backend(self) -> dict:
        return {
            "backend_kind": "smoke_durable",
            "backend_mode": "strict_smoke",
            "durable": True,
            "operation_fallback_allowed": False,
            "fallback_active": False,
            "fallback_reason": "",
            "last_error": "",
            "state_contract": super().describe_backend()["state_contract"],
        }


class _SmokeDegradedWorkspaceStore(InMemoryEmbeddedRunWorkspaceStore):
    def describe_backend(self) -> dict:
        return {
            "backend_kind": "smoke_durable",
            "backend_mode": "strict_smoke",
            "durable": True,
            "operation_fallback_allowed": True,
            "fallback_active": True,
            "fallback_reason": "save_run_snapshot",
            "last_error": "db unavailable",
            "state_contract": super().describe_backend()["state_contract"],
        }


def _build_smoke_factory_contract(
    workspace_store,
    worker_ownership_store=None,
    worker_ownership_production_enablement_config=None,
) -> dict:
    factory = EmbeddedRuntimeFactory(
        dependencies=EmbeddedRuntimeDependencies(
            workspace_store=workspace_store,
            continuation_registry=InMemoryEmbeddedContinuationRegistry(),
            worker_ownership_store=worker_ownership_store,
        ),
        worker_ownership_production_enablement_config=(
            worker_ownership_production_enablement_config
        ),
    )
    return factory.build_runtime_contract()


def _build_smoke_factory_contract_with_ownership(worker_ownership_store) -> dict:
    factory = EmbeddedRuntimeFactory(
        dependencies=EmbeddedRuntimeDependencies(
            workspace_store=InMemoryEmbeddedRunWorkspaceStore(),
            continuation_registry=InMemoryEmbeddedContinuationRegistry(),
            worker_ownership_store=worker_ownership_store,
        )
    )
    return factory.build_runtime_contract()


def _run_worker_ownership_store_mode_contract_check() -> dict:
    previous_mode = getattr(worker_ownership_module, "WORKER_OWNERSHIP_STORE_MODE", "memory_only")
    previous_env = os.environ.get("WORKER_OWNERSHIP_STORE_MODE")
    try:
        os.environ.pop("WORKER_OWNERSHIP_STORE_MODE", None)
        worker_ownership_module.WORKER_OWNERSHIP_STORE_MODE = "memory_only"
        memory_contract = _build_smoke_factory_contract_with_ownership(InMemoryRuntimeWorkerOwnershipStore())
        memory_profile = dict(memory_contract.get("default_runtime_profile") or {})
        memory_ownership = dict(memory_contract.get("worker_ownership") or {})
        memory_readiness = dict(memory_ownership.get("operational_readiness") or {})
        memory_production_gate = dict(memory_ownership.get("production_gate") or {})

        os.environ["WORKER_OWNERSHIP_STORE_MODE"] = "strict_sql"
        worker_ownership_module.WORKER_OWNERSHIP_STORE_MODE = "strict_sql"
        strict_contract = _build_smoke_factory_contract_with_ownership(
            SQLAlchemyRuntimeWorkerOwnershipStore(lambda: None)
        )
        strict_profile = dict(strict_contract.get("default_runtime_profile") or {})
        strict_ownership = dict(strict_contract.get("worker_ownership") or {})
        strict_readiness = dict(strict_ownership.get("operational_readiness") or {})
        strict_production_gate = dict(strict_ownership.get("production_gate") or {})
        strict_production_missing_sections = (
            strict_production_gate.get("missing_sections")
            if isinstance(strict_production_gate.get("missing_sections"), list)
            else []
        )
        strict_production_sections = [
            item for item in strict_production_gate.get("sections") or [] if isinstance(item, dict)
        ]
        vendor_lock_section = next(
            (
                item
                for item in strict_production_sections
                if str(item.get("name") or "").strip() == "vendor_lock_semantics"
            ),
            {},
        )
        vendor_lock_evidence = dict(vendor_lock_section.get("evidence") or {})
        vendor_lock_missing_sections = (
            vendor_lock_evidence.get("vendor_lock_missing_sections")
            if isinstance(vendor_lock_evidence.get("vendor_lock_missing_sections"), list)
            else []
        )
        vendor_lock_adapter_missing_sections = (
            vendor_lock_evidence.get("vendor_lock_adapter_missing_sections")
            if isinstance(vendor_lock_evidence.get("vendor_lock_adapter_missing_sections"), list)
            else []
        )
        renewal_section = next(
            (
                item
                for item in strict_production_sections
                if str(item.get("name") or "").strip() == "heartbeat_renewal_supervisor"
            ),
            {},
        )
        renewal_evidence = dict(renewal_section.get("evidence") or {})
        renewal_missing_sections = (
            renewal_evidence.get("renewal_supervisor_missing_sections")
            if isinstance(renewal_evidence.get("renewal_supervisor_missing_sections"), list)
            else []
        )
        rollout_section = next(
            (
                item
                for item in strict_production_sections
                if str(item.get("name") or "").strip() == "rollout_checklist"
            ),
            {},
        )
        rollout_evidence = dict(rollout_section.get("evidence") or {})
        rollout_missing_sections = (
            rollout_evidence.get("rollout_missing_sections")
            if isinstance(rollout_evidence.get("rollout_missing_sections"), list)
            else []
        )
        auto_claim_section = next(
            (
                item
                for item in strict_production_sections
                if str(item.get("name") or "").strip() == "recovery_entry_auto_claim_policy"
            ),
            {},
        )
        auto_claim_evidence = dict(auto_claim_section.get("evidence") or {})
        auto_claim_missing_sections = (
            auto_claim_evidence.get("auto_claim_missing_sections")
            if isinstance(auto_claim_evidence.get("auto_claim_missing_sections"), list)
            else []
        )
        audit_section = next(
            (
                item
                for item in strict_production_sections
                if str(item.get("name") or "").strip() == "ownership_audit_evidence"
            ),
            {},
        )
        audit_evidence = dict(audit_section.get("evidence") or {})
        audit_missing_sections = (
            audit_evidence.get("ownership_audit_missing_sections")
            if isinstance(audit_evidence.get("ownership_audit_missing_sections"), list)
            else []
        )
        enablement_section = next(
            (
                item
                for item in strict_production_sections
                if str(item.get("name") or "").strip() == "fail_closed_default_decision"
            ),
            {},
        )
        enablement_evidence = dict(enablement_section.get("evidence") or {})
        enablement_blocking_sections = (
            enablement_evidence.get("blocking_sections")
            if isinstance(enablement_evidence.get("blocking_sections"), list)
            else []
        )
        postgres_probe_default = (
            worker_ownership_module.build_worker_ownership_postgres_vendor_lock_probe_contract()
        )
        postgres_probe_ready = (
            worker_ownership_module.build_worker_ownership_postgres_vendor_lock_probe_contract(
                advisory_lock_family="pg_try_advisory_lock",
                lock_key_derivation="hash_run_id_to_bigint",
                lock_scope="session",
                fencing_token_binding="lease_fencing_token",
                ttl_renewal_strategy="heartbeat_validates_session_lock",
                failover_behavior="session_disconnect_releases_lock",
                stale_owner_cleanup_strategy="connection_pool_reaper",
                probe_safety="metadata_only",
            )
        )
        postgres_probe_missing_sections = (
            postgres_probe_default.get("missing_sections")
            if isinstance(postgres_probe_default.get("missing_sections"), list)
            else []
        )
        postgres_execution_default = worker_ownership_module.PostgresAdvisoryLockExecutionSeam()
        postgres_execution_default_contract = postgres_execution_default.contract()
        postgres_execution_default_probe = postgres_execution_default.probe_once()
        postgres_execution_envelopes: list[dict[str, object]] = []

        def _postgres_execution_executor(envelope: dict[str, object]) -> dict[str, object]:
            postgres_execution_envelopes.append(dict(envelope))
            operation = str(envelope.get("operation") or "")
            if operation == "probe":
                return {"ok": True}
            if operation == "acquire":
                return {"ok": True, "acquired": True}
            return {"ok": False}

        postgres_execution_opt_in = worker_ownership_module.PostgresAdvisoryLockExecutionSeam(
            executor=_postgres_execution_executor
        )
        postgres_execution_opt_in_contract = postgres_execution_opt_in.contract()
        postgres_execution_opt_in_probe = postgres_execution_opt_in.probe_once()
        postgres_execution_opt_in_acquire = postgres_execution_opt_in.acquire_once(
            run_id="postgres-lock-smoke-run",
            worker_id="postgres-lock-smoke-worker",
            lease_id="postgres-lock-smoke-lease",
            fencing_token=11,
        )
        postgres_rollout_consumer_default = (
            worker_ownership_module.build_worker_ownership_postgres_rollout_artifact_consumer_contract()
        )
        postgres_rollout_artifact_ready = {
            "source_kind": "rollout_artifact",
            "artifact_id": "pg-rollout-smoke-001",
            "approved_by": "runtime-ops",
            "approved_at": "2026-05-25T08:45:00Z",
            "target_store_mode": "strict_sql",
            "target_backend": "postgres",
            "lock_adapter_kind": "postgres_advisory_lock",
            "lock_scope": "run",
            "fencing_strategy": "fencing_token",
            "ttl_renewal_strategy": "session_ttl_renewal",
            "failover_strategy": "connection_loss_releases_lock",
            "stale_owner_cleanup_strategy": "ttl_cleanup",
            "rollout_artifact": "rollout/worker-ownership/pg-rollout-smoke-001",
            "vendor_lock_decision_id": "vendor-lock-postgres-smoke-001",
            "renewal_lifecycle_reference": "renewal-lifecycle-smoke-001",
            "auto_claim_decision_reference": "auto-claim-policy-smoke-001",
            "audit_evidence_reference": "ownership-audit-smoke-001",
            "rollback_plan_reference": "rollback-worker-ownership-smoke-001",
            "fallback_policy_reference": "fallback-worker-ownership-smoke-001",
        }
        postgres_rollout_consumer_ready = (
            worker_ownership_module.build_worker_ownership_postgres_rollout_artifact_consumer_contract(
                artifact=postgres_rollout_artifact_ready,
                postgres_execution_seam_contract=postgres_execution_opt_in_contract,
            )
        )
        postgres_rollout_consumer_default_missing = (
            postgres_rollout_consumer_default.get("missing_sections")
            if isinstance(postgres_rollout_consumer_default.get("missing_sections"), list)
            else []
        )
        postgres_rollout_consumer_ready_input = dict(
            postgres_rollout_consumer_ready.get("enablement_input_source") or {}
        )
        postgres_target_binding_default = (
            worker_ownership_module
            .build_worker_ownership_postgres_vendor_lock_target_artifact_binding_contract()
        )
        postgres_target_binding_ready = (
            worker_ownership_module
            .build_worker_ownership_postgres_vendor_lock_target_artifact_binding_contract(
                artifact=postgres_rollout_artifact_ready,
                postgres_rollout_consumer_contract=postgres_rollout_consumer_ready,
            )
        )
        postgres_target_binding_default_missing = (
            postgres_target_binding_default.get("missing_sections")
            if isinstance(postgres_target_binding_default.get("missing_sections"), list)
            else []
        )
        postgres_target_binding_ready_input = dict(
            postgres_target_binding_ready.get("target_decision_input") or {}
        )
        postgres_target_binding_ready_decision = dict(
            postgres_target_binding_ready.get("target_decision") or {}
        )
        postgres_semantics_binding_default = (
            worker_ownership_module
            .build_worker_ownership_postgres_vendor_lock_semantics_binding_contract()
        )
        postgres_semantics_binding_ready = (
            worker_ownership_module
            .build_worker_ownership_postgres_vendor_lock_semantics_binding_contract(
                target_artifact_binding_contract=postgres_target_binding_ready,
                postgres_execution_seam_contract=postgres_execution_opt_in_contract,
            )
        )
        postgres_semantics_binding_default_missing = (
            postgres_semantics_binding_default.get("missing_sections")
            if isinstance(postgres_semantics_binding_default.get("missing_sections"), list)
            else []
        )
        postgres_wiring_decision_default = (
            worker_ownership_module
            .build_worker_ownership_postgres_vendor_lock_production_gate_wiring_decision_contract()
        )
        postgres_wiring_decision_ready = (
            worker_ownership_module
            .build_worker_ownership_postgres_vendor_lock_production_gate_wiring_decision_contract(
                semantics_binding_contract=postgres_semantics_binding_ready,
                decision_recorded=True,
                decision_id="pg-wire-smoke-001",
                approved_by="runtime-ops",
                approved_at="2026-05-25T09:30:00Z",
                production_rollout_confirmed=True,
                rollback_plan_reference="rollback-worker-ownership-smoke-001",
                fallback_policy_reference="fallback-worker-ownership-smoke-001",
            )
        )
        postgres_wiring_decision_default_missing = (
            postgres_wiring_decision_default.get("missing_sections")
            if isinstance(postgres_wiring_decision_default.get("missing_sections"), list)
            else []
        )
        production_dry_run_default = (
            worker_ownership_module
            .build_worker_ownership_production_gate_composition_dry_run_contract()
        )
        production_dry_run_default_missing = (
            production_dry_run_default.get("missing_sections")
            if isinstance(production_dry_run_default.get("missing_sections"), list)
            else []
        )
        production_dry_run_ready = (
            worker_ownership_module
            .build_worker_ownership_production_gate_composition_dry_run_contract(
                vendor_lock_wiring_decision_contract=postgres_wiring_decision_ready,
                renewal_supervisor_contract=(
                    worker_ownership_module.build_worker_ownership_renewal_supervisor_contract(
                        heartbeat_operation_present=True,
                        renew_once_supported=True,
                        owner_identity_required=True,
                        controlled_lifecycle_supported=True,
                        starts_by_default=False,
                        active=False,
                        stop_supported=True,
                        failure_fail_closed=True,
                        background_supervisor_present=True,
                        renewal_owner_identity_present=True,
                        ttl_interval_policy_present=True,
                        lease_loss_fail_closed=True,
                        supervisor_enabled_by_default=True,
                    )
                ),
                rollout_confirmation_decision_contract=(
                    worker_ownership_module
                    .build_worker_ownership_rollout_confirmation_decision_contract(
                        decision_recorded=True,
                        decision_id="rollout-confirm-smoke-001",
                        approved_by="runtime-ops",
                        approved_at="2026-05-25T09:35:00Z",
                        target_store_mode="strict_sql",
                        rollback_plan_acknowledged=True,
                        fallback_policy_acknowledged=True,
                        renewal_lifecycle_verified=True,
                        auto_claim_decision_recorded=True,
                        production_rollout_confirmed=True,
                        input_source_contract=(
                            worker_ownership_module
                            .build_worker_ownership_rollout_confirmation_input_source_contract(
                                input_source_kind="deployment_artifact",
                                decision_id="rollout-confirm-smoke-001",
                                approved_by="runtime-ops",
                                approved_at="2026-05-25T09:35:00Z",
                                target_store_mode="strict_sql",
                                rollback_plan_reference="rollback-worker-ownership-smoke-001",
                                fallback_policy_reference="fallback-worker-ownership-smoke-001",
                                renewal_lifecycle_reference="renewal-lifecycle-smoke-001",
                                auto_claim_decision_reference="auto-claim-smoke-001",
                                deployment_artifact="worker-ownership-rollout-artifact-001",
                            )
                        ),
                    )
                ),
                auto_claim_enablement_gate_contract=(
                    worker_ownership_module
                    .build_worker_ownership_explicit_auto_claim_enablement_gate_contract(
                        explicit_runtime_configuration=True,
                        production_gate_ready=True,
                        durable_ownership_ready=True,
                        descriptor_evidence_fallback=True,
                        idempotency_evidence_ready=True,
                        audit_evidence_ready=True,
                        lease_validation_ready=True,
                        rollout_auto_claim_decision_recorded=True,
                    )
                ),
                ownership_audit_evidence_contract=(
                    worker_ownership_module.build_worker_ownership_audit_evidence_contract(
                        compact_ownership_evidence=True,
                        operation_history_ready=True,
                        recovery_operation_link_ready=True,
                        timeline_writer_ready=True,
                        idempotent_dedupe_ready=True,
                        authorization_source=False,
                    )
                ),
                production_default_enablement_input_source_contract=(
                    postgres_rollout_consumer_ready_input
                ),
            )
        )
        production_dry_run_ready_missing = (
            production_dry_run_ready.get("missing_sections")
            if isinstance(production_dry_run_ready.get("missing_sections"), list)
            else []
        )
        enablement_config_consumer_default = (
            worker_ownership_module
            .build_worker_ownership_production_enablement_runtime_config_consumer_contract()
        )
        enablement_config_consumer_default_missing = (
            enablement_config_consumer_default.get("missing_sections")
            if isinstance(
                enablement_config_consumer_default.get("missing_sections"), list
            )
            else []
        )
        enablement_config_consumer_ready = (
            worker_ownership_module
            .build_worker_ownership_production_enablement_runtime_config_consumer_contract(
                config={
                    "source_kind": "runtime_config",
                    "config_id": "prod-enable-config-smoke-001",
                    "approved_by": "runtime-ops",
                    "approved_at": "2026-05-25T09:40:00Z",
                    "target_store_mode": "strict_sql",
                    "target_backend": "postgres",
                    "lock_adapter_kind": "postgres_advisory_lock",
                    "rollout_artifact": "rollout/worker-ownership/pg-rollout-001",
                    "vendor_lock_decision_id": "pg-wire-smoke-001",
                    "renewal_lifecycle_reference": "renewal-lifecycle-smoke-001",
                    "auto_claim_decision_reference": "auto-claim-smoke-001",
                    "audit_evidence_reference": "ownership-audit-smoke-001",
                    "rollback_plan_reference": "rollback-worker-ownership-smoke-001",
                    "fallback_policy_reference": "fallback-worker-ownership-smoke-001",
                },
                composition_dry_run_contract=production_dry_run_ready,
            )
        )
        enablement_config_consumer_ready_missing = (
            enablement_config_consumer_ready.get("missing_sections")
            if isinstance(
                enablement_config_consumer_ready.get("missing_sections"), list
            )
            else []
        )
        factory_binding_default = dict(
            memory_ownership.get("production_enablement_runtime_config_consumer") or {}
        )
        factory_binding_ready_contract = _build_smoke_factory_contract(
            InMemoryEmbeddedRunWorkspaceStore(),
            InMemoryRuntimeWorkerOwnershipStore(),
            {
                "source_kind": "runtime_config",
                "config_id": "prod-enable-factory-smoke-001",
                "approved_by": "runtime-ops",
                "approved_at": "2026-05-25T09:45:00Z",
                "target_store_mode": "strict_sql",
                "target_backend": "postgres",
                "lock_adapter_kind": "postgres_advisory_lock",
                "rollout_artifact": "rollout/worker-ownership/pg-rollout-001",
                "vendor_lock_decision_id": "pg-wire-smoke-001",
                "renewal_lifecycle_reference": "renewal-lifecycle-smoke-001",
                "auto_claim_decision_reference": "auto-claim-smoke-001",
                "audit_evidence_reference": "ownership-audit-smoke-001",
                "rollback_plan_reference": "rollback-worker-ownership-smoke-001",
                "fallback_policy_reference": "fallback-worker-ownership-smoke-001",
                "composition_dry_run": production_dry_run_ready,
            },
        )
        factory_binding_ready = dict(
            dict(factory_binding_ready_contract.get("worker_ownership") or {}).get(
                "production_enablement_runtime_config_consumer"
            )
            or {}
        )

        renewal_smoke_store = InMemoryRuntimeWorkerOwnershipStore()
        renewal_smoke_claim = renewal_smoke_store.claim_run(
            "renewal-smoke-run",
            "renewal-smoke-worker",
            lease_ttl_seconds=30,
        )
        renewal_smoke_supervisor = WorkerOwnershipRenewalSupervisor(
            store=renewal_smoke_store,
            lease_ttl_seconds=45,
            renew_interval_seconds=15,
        )
        renewal_smoke_success = renewal_smoke_supervisor.renew_once(
            run_id="renewal-smoke-run",
            worker_id="renewal-smoke-worker",
            lease_id=str(renewal_smoke_claim.get("lease_id") or ""),
            fencing_token=int(renewal_smoke_claim.get("fencing_token") or 0),
        )
        renewal_smoke_stale = renewal_smoke_supervisor.renew_once(
            run_id="renewal-smoke-run",
            worker_id="renewal-smoke-worker",
            lease_id=str(renewal_smoke_claim.get("lease_id") or ""),
            fencing_token=int(renewal_smoke_claim.get("fencing_token") or 0) + 1,
        )
        renewal_lifecycle_store = InMemoryRuntimeWorkerOwnershipStore()
        renewal_lifecycle_claim = renewal_lifecycle_store.claim_run(
            "renewal-lifecycle-smoke-run",
            "renewal-lifecycle-worker",
            lease_ttl_seconds=30,
        )
        renewal_lifecycle_supervisor = WorkerOwnershipRenewalSupervisor(
            store=renewal_lifecycle_store,
            lease_ttl_seconds=45,
            renew_interval_seconds=30,
        )
        renewal_lifecycle_initial = renewal_lifecycle_supervisor.status()
        renewal_lifecycle_started = renewal_lifecycle_supervisor.start(
            run_id="renewal-lifecycle-smoke-run",
            worker_id="renewal-lifecycle-worker",
            lease_id=str(renewal_lifecycle_claim.get("lease_id") or ""),
            fencing_token=int(renewal_lifecycle_claim.get("fencing_token") or 0),
        )
        renewal_lifecycle_stopped = renewal_lifecycle_supervisor.stop()

        os.environ["WORKER_OWNERSHIP_STORE_MODE"] = "prefer_sql_with_fallback"
        worker_ownership_module.WORKER_OWNERSHIP_STORE_MODE = "prefer_sql_with_fallback"
        fallback_contract = _build_smoke_factory_contract_with_ownership(
            WorkerOwnershipStoreFallback(
                InMemoryRuntimeWorkerOwnershipStore(),
                configured_mode="prefer_sql_with_fallback",
                fallback_reason="smoke_sql_unavailable",
            )
        )
        fallback_profile = dict(fallback_contract.get("default_runtime_profile") or {})
        fallback_ownership = dict(fallback_contract.get("worker_ownership") or {})
        fallback_readiness = dict(fallback_ownership.get("operational_readiness") or {})
        fallback_knobs = set(memory_profile.get("configurable_bootstrap_knobs") or [])
        fallback_hot_reload = set(memory_profile.get("hot_reloadable_bootstrap_knobs") or [])
        ok = (
            memory_profile.get("worker_ownership_store_mode") == "memory_only"
            and memory_profile.get("worker_ownership_store_mode_source") == "default"
            and memory_ownership.get("adapter_kind") == "in_memory"
            and memory_ownership.get("durable") is False
            and memory_readiness.get("readiness_status") == "preview_or_degraded"
            and memory_readiness.get("production_ready") is False
            and memory_readiness.get("recovery_entry_claim_mode") == "descriptor_evidence_only"
            and "WORKER_OWNERSHIP_STORE_MODE" in fallback_knobs
            and "WORKER_OWNERSHIP_STORE_MODE" in fallback_hot_reload
            and strict_profile.get("worker_ownership_store_mode") == "strict_sql"
            and strict_profile.get("worker_ownership_store_mode_source") == "env"
            and strict_ownership.get("adapter_kind") == "sqlalchemy"
            and strict_ownership.get("durable") is True
            and strict_readiness.get("readiness_status") == "production_ready"
            and strict_readiness.get("vendor_lock_posture") == "sql_row_lease_fencing"
            and dict(strict_readiness.get("migration_checklist") or {}).get("migration_ready") is True
            and strict_production_gate.get("contract_version") == "phase-ii-worker-ownership-production-gate-v1"
            and strict_production_gate.get("overall_status") == "blocked"
            and "vendor_lock_semantics" in strict_production_missing_sections
            and "heartbeat_renewal_supervisor" in strict_production_missing_sections
            and strict_production_gate.get("production_default_enabled") is False
            and vendor_lock_evidence.get("vendor_lock_contract_version")
            == "phase-ii-worker-ownership-vendor-lock-semantics-v1"
            and vendor_lock_evidence.get("vendor_lock_status") == "blocked"
            and vendor_lock_evidence.get("current_posture") == "sql_row_lease_fencing"
            and vendor_lock_evidence.get("sql_row_lease_fencing") is True
            and vendor_lock_evidence.get("sql_row_lease_is_vendor_lock") is False
            and vendor_lock_evidence.get("vendor_lock_adapter_present") is False
            and vendor_lock_evidence.get("vendor_lock_adapter_contract_version")
            == "phase-ii-worker-ownership-vendor-lock-adapter-v1"
            and vendor_lock_evidence.get("vendor_lock_adapter_status") == "blocked"
            and vendor_lock_evidence.get("vendor_lock_adapter_kind") == ""
            and vendor_lock_evidence.get("vendor_lock_adapter_target_backend") == ""
            and vendor_lock_evidence.get("vendor_lock_adapter_scope") == ""
            and vendor_lock_evidence.get("vendor_lock_adapter_fencing_strategy") == ""
            and vendor_lock_evidence.get("vendor_lock_adapter_ttl_renewal_strategy") == ""
            and vendor_lock_evidence.get("vendor_lock_adapter_failover_strategy") == ""
            and vendor_lock_evidence.get("vendor_lock_adapter_stale_cleanup_strategy") == ""
            and vendor_lock_evidence.get("vendor_lock_adapter_acquire_supported") is False
            and vendor_lock_evidence.get("vendor_lock_adapter_renew_supported") is False
            and vendor_lock_evidence.get("vendor_lock_adapter_release_supported") is False
            and vendor_lock_evidence.get("vendor_lock_adapter_probe_supported") is False
            and vendor_lock_evidence.get("vendor_lock_adapter_production_allowed") is False
            and vendor_lock_evidence.get("vendor_lock_adapter_sql_row_lease_is_vendor_lock")
            is False
            and "adapter_kind" in vendor_lock_adapter_missing_sections
            and "target_backend" in vendor_lock_adapter_missing_sections
            and postgres_probe_default.get("contract_version")
            == "phase-ii-worker-ownership-postgres-vendor-lock-probe-v1"
            and postgres_probe_default.get("overall_status") == "blocked"
            and postgres_probe_default.get("executes_probe") is False
            and postgres_probe_default.get("sql_row_lease_is_vendor_lock") is False
            and "advisory_lock_family" in postgres_probe_missing_sections
            and "probe_safety" in postgres_probe_missing_sections
            and postgres_probe_ready.get("overall_status") == "ready"
            and postgres_probe_ready.get("executes_probe") is False
            and postgres_execution_default_contract.get("contract_version")
            == "phase-ii-worker-ownership-postgres-advisory-lock-execution-seam-v1"
            and postgres_execution_default_contract.get("overall_status") == "blocked"
            and postgres_execution_default_contract.get("executor_bound") is False
            and postgres_execution_default_contract.get("enabled_by_default") is False
            and postgres_execution_default_contract.get("production_lock_allowed") is False
            and "executor_binding"
            in (postgres_execution_default_contract.get("missing_sections") or [])
            and postgres_execution_default_probe.get("status") == "blocked"
            and postgres_execution_default_probe.get("executed") is False
            and postgres_execution_opt_in_contract.get("overall_status") == "ready"
            and postgres_execution_opt_in_contract.get("executor_bound") is True
            and postgres_execution_opt_in_contract.get("enabled_by_default") is False
            and postgres_execution_opt_in_contract.get("production_lock_allowed") is False
            and postgres_execution_opt_in_probe.get("status") == "ready"
            and postgres_execution_opt_in_probe.get("executed") is True
            and postgres_execution_opt_in_acquire.get("status") == "acquired"
            and postgres_execution_opt_in_acquire.get("acquired") is True
            and postgres_execution_opt_in_acquire.get("executed") is True
            and len(postgres_execution_envelopes) == 2
            and postgres_execution_envelopes[1].get("operation") == "acquire"
            and postgres_execution_envelopes[1].get("sql")
            == "SELECT pg_try_advisory_lock(:lock_key)"
            and postgres_rollout_consumer_default.get("contract_version")
            == "phase-ii-worker-ownership-postgres-rollout-artifact-consumer-v1"
            and postgres_rollout_consumer_default.get("overall_status") == "blocked"
            and postgres_rollout_consumer_default.get("will_enable_production_default")
            is False
            and postgres_rollout_consumer_default.get("executes_advisory_lock") is False
            and "source_kind" in postgres_rollout_consumer_default_missing
            and "postgres_execution_seam" in postgres_rollout_consumer_default_missing
            and postgres_rollout_consumer_ready.get("overall_status") == "ready"
            and postgres_rollout_consumer_ready.get("target_backend") == "postgres"
            and postgres_rollout_consumer_ready.get("lock_adapter_kind")
            == "postgres_advisory_lock"
            and postgres_rollout_consumer_ready.get("will_enable_production_default") is False
            and postgres_rollout_consumer_ready.get("executes_advisory_lock") is False
            and postgres_rollout_consumer_ready_input.get("overall_status") == "ready"
            and postgres_target_binding_default.get("contract_version")
            == (
                "phase-ii-worker-ownership-postgres-vendor-lock-target"
                "-artifact-binding-v1"
            )
            and postgres_target_binding_default.get("overall_status") == "blocked"
            and postgres_target_binding_default.get("will_enable_production_lock")
            is False
            and postgres_target_binding_default.get("executes_advisory_lock") is False
            and "source_kind" in postgres_target_binding_default_missing
            and "postgres_rollout_consumer" in postgres_target_binding_default_missing
            and postgres_target_binding_ready.get("overall_status") == "ready"
            and postgres_target_binding_ready.get("target_backend") == "postgres"
            and postgres_target_binding_ready.get("lock_adapter_kind")
            == "postgres_advisory_lock"
            and postgres_target_binding_ready.get("will_enable_production_lock") is False
            and postgres_target_binding_ready.get("executes_advisory_lock") is False
            and postgres_target_binding_ready.get("sql_row_lease_is_vendor_lock") is False
            and postgres_target_binding_ready_input.get("overall_status") == "ready"
            and postgres_target_binding_ready_decision.get("overall_status") == "ready"
            and postgres_target_binding_ready_decision.get("production_lock_allowed") is True
            and postgres_semantics_binding_default.get("contract_version")
            == "phase-ii-worker-ownership-postgres-vendor-lock-semantics-binding-v1"
            and postgres_semantics_binding_default.get("overall_status") == "blocked"
            and "target_artifact_binding" in postgres_semantics_binding_default_missing
            and "postgres_execution_seam" in postgres_semantics_binding_default_missing
            and "vendor_lock_semantics" in postgres_semantics_binding_default_missing
            and postgres_semantics_binding_default.get("will_enable_production_lock") is False
            and postgres_semantics_binding_default.get("will_update_production_gate") is False
            and postgres_semantics_binding_default.get("executes_advisory_lock") is False
            and postgres_semantics_binding_ready.get("overall_status") == "ready"
            and postgres_semantics_binding_ready.get("target_backend") == "postgres"
            and postgres_semantics_binding_ready.get("lock_adapter_kind")
            == "postgres_advisory_lock"
            and postgres_semantics_binding_ready.get("postgres_probe_status") == "ready"
            and postgres_semantics_binding_ready.get("vendor_lock_adapter_status") == "ready"
            and postgres_semantics_binding_ready.get("vendor_lock_semantics_status") == "ready"
            and postgres_semantics_binding_ready.get("will_enable_production_lock") is False
            and postgres_semantics_binding_ready.get("will_update_production_gate") is False
            and postgres_semantics_binding_ready.get("executes_advisory_lock") is False
            and postgres_semantics_binding_ready.get("sql_row_lease_is_vendor_lock") is False
            and postgres_wiring_decision_default.get("contract_version")
            == (
                "phase-ii-worker-ownership-postgres-vendor-lock-production-gate"
                "-wiring-decision-v1"
            )
            and postgres_wiring_decision_default.get("overall_status") == "blocked"
            and "semantics_binding" in postgres_wiring_decision_default_missing
            and "decision_recorded" in postgres_wiring_decision_default_missing
            and postgres_wiring_decision_default.get("wiring_allowed") is False
            and postgres_wiring_decision_default.get("will_update_production_gate") is False
            and postgres_wiring_decision_default.get("will_enable_production_lock") is False
            and postgres_wiring_decision_default.get("executes_advisory_lock") is False
            and postgres_wiring_decision_ready.get("overall_status") == "ready"
            and postgres_wiring_decision_ready.get("semantics_binding_status") == "ready"
            and postgres_wiring_decision_ready.get("candidate_semantics_status") == "ready"
            and postgres_wiring_decision_ready.get("wiring_allowed") is True
            and postgres_wiring_decision_ready.get("target_backend") == "postgres"
            and postgres_wiring_decision_ready.get("lock_adapter_kind")
            == "postgres_advisory_lock"
            and postgres_wiring_decision_ready.get("will_update_production_gate") is False
            and postgres_wiring_decision_ready.get("will_enable_production_lock") is False
            and postgres_wiring_decision_ready.get("executes_advisory_lock") is False
            and production_dry_run_default.get("contract_version")
            == "phase-ii-worker-ownership-production-gate-composition-dry-run-v1"
            and production_dry_run_default.get("overall_status") == "blocked"
            and "vendor_lock_wiring_decision" in production_dry_run_default_missing
            and "heartbeat_renewal_supervisor" in production_dry_run_default_missing
            and "rollout_confirmation" in production_dry_run_default_missing
            and "recovery_entry_auto_claim_enablement" in production_dry_run_default_missing
            and "ownership_audit_evidence" in production_dry_run_default_missing
            and "production_default_enablement_input_source"
            in production_dry_run_default_missing
            and production_dry_run_default.get("all_required_sections_ready") is False
            and production_dry_run_default.get("production_default_would_be_allowed")
            is False
            and production_dry_run_default.get("will_enable_production_default") is False
            and production_dry_run_default.get("executes_lock") is False
            and production_dry_run_default.get("starts_background_worker") is False
            and production_dry_run_default.get("runs_recovery_auto_claim") is False
            and production_dry_run_ready.get("overall_status") == "ready"
            and production_dry_run_ready.get("all_required_sections_ready") is True
            and production_dry_run_ready.get("production_default_would_be_allowed") is True
            and production_dry_run_ready_missing == []
            and production_dry_run_ready.get("will_enable_production_default") is False
            and production_dry_run_ready.get("executes_lock") is False
            and production_dry_run_ready.get("starts_background_worker") is False
            and production_dry_run_ready.get("runs_recovery_auto_claim") is False
            and enablement_config_consumer_default.get("contract_version")
            == (
                "phase-ii-worker-ownership-production-enablement-runtime-config"
                "-consumer-v1"
            )
            and enablement_config_consumer_default.get("overall_status") == "blocked"
            and "source_kind" in enablement_config_consumer_default_missing
            and "config_id" in enablement_config_consumer_default_missing
            and "enablement_input_source" in enablement_config_consumer_default_missing
            and "composition_dry_run" in enablement_config_consumer_default_missing
            and enablement_config_consumer_default.get("will_enable_production_default")
            is False
            and enablement_config_consumer_default.get("executes_lock") is False
            and enablement_config_consumer_default.get("starts_background_worker") is False
            and enablement_config_consumer_default.get("runs_recovery_auto_claim") is False
            and enablement_config_consumer_ready.get("overall_status") == "ready"
            and enablement_config_consumer_ready_missing == []
            and enablement_config_consumer_ready.get("target_backend") == "postgres"
            and enablement_config_consumer_ready.get("lock_adapter_kind")
            == "postgres_advisory_lock"
            and (
                enablement_config_consumer_ready.get("enablement_input_source") or {}
            ).get("overall_status")
            == "ready"
            and (
                enablement_config_consumer_ready.get("composition_dry_run") or {}
            ).get("overall_status")
            == "ready"
            and enablement_config_consumer_ready.get("composition_dry_run_would_allow")
            is True
            and enablement_config_consumer_ready.get("will_enable_production_default")
            is False
            and enablement_config_consumer_ready.get("executes_lock") is False
            and enablement_config_consumer_ready.get("starts_background_worker") is False
            and enablement_config_consumer_ready.get("runs_recovery_auto_claim") is False
            and vendor_lock_evidence.get("production_lock_allowed") is False
            and "vendor_lock_adapter" in vendor_lock_missing_sections
            and "target_decision" in vendor_lock_missing_sections
            and vendor_lock_evidence.get("vendor_lock_target_decision_contract_version")
            == "phase-ii-worker-ownership-vendor-lock-target-decision-v1"
            and vendor_lock_evidence.get("vendor_lock_target_decision_status") == "blocked"
            and vendor_lock_evidence.get("vendor_lock_target_decision_recorded") is False
            and vendor_lock_evidence.get("vendor_lock_target_backend") == ""
            and vendor_lock_evidence.get("vendor_lock_target_adapter_kind") == ""
            and vendor_lock_evidence.get("vendor_lock_target_scope") == ""
            and vendor_lock_evidence.get("vendor_lock_target_input_contract_version")
            == "phase-ii-worker-ownership-vendor-lock-target-decision-input-v1"
            and vendor_lock_evidence.get("vendor_lock_target_input_source_status") == "blocked"
            and vendor_lock_evidence.get("vendor_lock_target_input_source_kind") == ""
            and vendor_lock_evidence.get("vendor_lock_target_input_decision_id") == ""
            and vendor_lock_evidence.get("vendor_lock_target_input_backend") == ""
            and vendor_lock_evidence.get("vendor_lock_target_input_adapter_kind") == ""
            and vendor_lock_evidence.get("vendor_lock_target_input_sql_row_lease_is_vendor_lock")
            is False
            and "input_source_kind"
            in (vendor_lock_evidence.get("vendor_lock_target_input_missing_sections") or [])
            and vendor_lock_evidence.get("vendor_lock_target_sql_row_lease_is_vendor_lock")
            is False
            and vendor_lock_evidence.get("vendor_lock_target_production_allowed") is False
            and "decision_recorded"
            in (vendor_lock_evidence.get("vendor_lock_target_missing_sections") or [])
            and renewal_evidence.get("renewal_supervisor_contract_version")
            == "phase-ii-worker-ownership-renewal-supervisor-v1"
            and renewal_evidence.get("renewal_supervisor_status") == "blocked"
            and renewal_evidence.get("supervisor_enabled_by_default") is False
            and renewal_evidence.get("renew_once_supported") is True
            and renewal_evidence.get("owner_identity_required") is True
            and renewal_evidence.get("ttl_interval_policy_ready") is True
            and renewal_evidence.get("controlled_lifecycle_supported") is True
            and renewal_evidence.get("starts_by_default") is False
            and renewal_evidence.get("active") is False
            and renewal_evidence.get("stop_supported") is True
            and renewal_evidence.get("failure_fail_closed") is True
            and renewal_evidence.get("lease_loss_fail_closed") is True
            and "background_supervisor" in renewal_missing_sections
            and renewal_smoke_success.get("renewal_status") == "renewed"
            and renewal_smoke_success.get("renewed") is True
            and renewal_smoke_success.get("background_supervisor_started") is False
            and renewal_smoke_stale.get("renewal_status") == "blocked"
            and renewal_smoke_stale.get("reason") == "stale_worker_fencing_token"
            and renewal_lifecycle_initial.get("active") is False
            and renewal_lifecycle_initial.get("starts_by_default") is False
            and renewal_lifecycle_started.get("active") is True
            and renewal_lifecycle_started.get("last_renewal_status") == "renewed"
            and renewal_lifecycle_started.get("renewal_count") == 1
            and renewal_lifecycle_stopped.get("active") is False
            and renewal_lifecycle_stopped.get("renewal_count") == 1
            and rollout_evidence.get("rollout_readiness_contract_version")
            == "phase-ii-worker-ownership-rollout-readiness-v1"
            and rollout_evidence.get("rollout_readiness_status") == "blocked"
            and rollout_evidence.get("production_rollout_confirmed") is False
            and rollout_evidence.get("migration_ready") is True
            and rollout_evidence.get("stale_fencing_verified") is True
            and rollout_evidence.get("rollback_plan_ready") is False
            and rollout_evidence.get("rollout_operationalization_status") == "blocked"
            and rollout_evidence.get("rollout_mode") == "readiness_only"
            and "rollback_plan" in (rollout_evidence.get("rollout_missing_artifacts") or [])
            and "rollout_confirmation_decision"
            in (rollout_evidence.get("rollout_missing_artifacts") or [])
            and rollout_evidence.get("rollback_plan_status") == "missing"
            and rollout_evidence.get("fallback_policy_status") == "missing"
            and rollout_evidence.get("renewal_lifecycle_verification_status") == "missing"
            and rollout_evidence.get("auto_claim_decision_status") == "missing"
            and rollout_evidence.get("rollout_confirmation_decision_contract_version")
            == "phase-ii-worker-ownership-rollout-confirmation-decision-v1"
            and rollout_evidence.get("rollout_confirmation_decision_status") == "blocked"
            and rollout_evidence.get("rollout_decision_recorded") is False
            and rollout_evidence.get("rollout_target_store_mode") == ""
            and "decision_recorded"
            in (rollout_evidence.get("rollout_confirmation_missing_sections") or [])
            and rollout_evidence.get("rollout_confirmation_production_rollout_confirmed")
            is False
            and rollout_evidence.get("rollout_confirmation_input_contract_version")
            == "phase-ii-worker-ownership-rollout-confirmation-input-source-v1"
            and rollout_evidence.get("rollout_confirmation_input_source_status") == "blocked"
            and rollout_evidence.get("rollout_confirmation_input_source_kind") == ""
            and rollout_evidence.get("rollout_confirmation_input_decision_id") == ""
            and "input_source_kind"
            in (rollout_evidence.get("rollout_confirmation_input_missing_sections") or [])
            and "decision_id"
            in (rollout_evidence.get("rollout_confirmation_input_missing_sections") or [])
            and rollout_evidence.get("rollout_confirmation_input_sql_row_lease_is_authority")
            is False
            and "strict_mode_rollout" in rollout_missing_sections
            and auto_claim_evidence.get("auto_claim_policy_contract_version")
            == "phase-ii-worker-ownership-auto-claim-policy-v1"
            and auto_claim_evidence.get("auto_claim_policy_status") == "blocked"
            and auto_claim_evidence.get("auto_claim_enabled_by_default") is False
            and auto_claim_evidence.get("descriptor_evidence_fallback") is True
            and auto_claim_evidence.get("lease_validation_required") is True
            and auto_claim_evidence.get("entrypoint_allowlist_ready") is True
            and auto_claim_evidence.get("auto_claim_entrypoint_allowlist_contract_version")
            == "phase-ii-worker-ownership-auto-claim-entrypoint-allowlist-v1"
            and auto_claim_evidence.get("auto_claim_entrypoint_allowlist_status") == "ready"
            and "submit_approval.approved"
            in (auto_claim_evidence.get("auto_claim_allowed_entrypoints") or [])
            and "resume_run.continue_loop"
            in (auto_claim_evidence.get("auto_claim_allowed_entrypoints") or [])
            and auto_claim_evidence.get("auto_claim_missing_entrypoints") == []
            and auto_claim_evidence.get("auto_claim_default_auto_claim_enabled") is False
            and auto_claim_evidence.get("auto_claim_requires_production_gate_ready") is True
            and auto_claim_evidence.get("auto_claim_enablement_gate_contract_version")
            == "phase-ii-worker-ownership-explicit-auto-claim-enablement-gate-v1"
            and auto_claim_evidence.get("auto_claim_enablement_gate_status") == "blocked"
            and auto_claim_evidence.get("auto_claim_will_auto_claim") is False
            and auto_claim_evidence.get("auto_claim_requested_entrypoint")
            == "submit_approval.approved"
            and "explicit_runtime_configuration"
            in (auto_claim_evidence.get("auto_claim_enablement_missing_sections") or [])
            and auto_claim_evidence.get("auto_claim_enablement_blocked_reason")
            == "explicit_runtime_configuration_missing"
            and "explicit_runtime_configuration" in auto_claim_missing_sections
            and audit_evidence.get("ownership_audit_contract_version")
            == "phase-ii-worker-ownership-audit-evidence-v1"
            and audit_evidence.get("ownership_audit_status") == "blocked"
            and audit_evidence.get("compact_ownership_evidence") is True
            and audit_evidence.get("operation_history_ready") is False
            and audit_evidence.get("timeline_writer_ready") is False
            and audit_evidence.get("idempotent_dedupe_ready") is False
            and audit_evidence.get("authorization_source") is False
            and "operation_history" in audit_missing_sections
            and enablement_evidence.get("enablement_strategy_contract_version")
            == "phase-ii-worker-ownership-production-enablement-strategy-v1"
            and enablement_evidence.get("enablement_strategy_status") == "blocked"
            and enablement_evidence.get("production_default_enabled_requested") is False
            and enablement_evidence.get("production_default_allowed") is False
            and enablement_evidence.get("enablement_input_source_contract_version")
            == "phase-ii-worker-ownership-production-default-enablement-input-source-v1"
            and enablement_evidence.get("enablement_input_source_status") == "blocked"
            and enablement_evidence.get("enablement_input_source_kind") == ""
            and enablement_evidence.get("enablement_input_source_ready") is False
            and "input_source_kind"
            in (enablement_evidence.get("enablement_input_source_missing_sections") or [])
            and enablement_evidence.get("explicit_enablement_required") is True
            and enablement_evidence.get("fail_closed_when_blocked") is True
            and enablement_evidence.get("sql_row_lease_is_not_default_authority") is True
            and factory_binding_default.get("overall_status") == "blocked"
            and factory_binding_ready.get("overall_status") == "ready"
            and factory_binding_ready.get("config_id") == "prod-enable-factory-smoke-001"
            and factory_binding_ready.get("will_enable_production_default") is False
            and factory_binding_ready.get("executes_lock") is False
            and factory_binding_ready.get("starts_background_worker") is False
            and factory_binding_ready.get("runs_recovery_auto_claim") is False
            and "vendor_lock_semantics" in enablement_blocking_sections
            and fallback_profile.get("worker_ownership_store_mode") == "prefer_sql_with_fallback"
            and fallback_profile.get("worker_ownership_store_mode_source") == "env"
            and fallback_ownership.get("adapter_kind") == "in_memory"
            and fallback_ownership.get("durable") is False
            and fallback_readiness.get("readiness_status") == "preview_or_degraded"
            and fallback_readiness.get("fallback_active") is True
        )
        return {
            "ok": ok,
            "default_mode": str(memory_profile.get("worker_ownership_store_mode") or ""),
            "default_mode_source": str(memory_profile.get("worker_ownership_store_mode_source") or ""),
            "default_adapter_kind": str(memory_ownership.get("adapter_kind") or ""),
            "default_durable": bool(memory_ownership.get("durable")),
            "operational_readiness_contract_version": str(memory_readiness.get("contract_version") or ""),
            "default_operational_readiness_status": str(memory_readiness.get("readiness_status") or ""),
            "default_operational_production_ready": bool(memory_readiness.get("production_ready")),
            "auto_claim_mode_default": str(memory_readiness.get("recovery_entry_claim_mode") or ""),
            "production_gate_contract_version": str(strict_production_gate.get("contract_version") or ""),
            "production_gate_status": str(strict_production_gate.get("overall_status") or ""),
            "production_gate_missing_sections": list(strict_production_missing_sections),
            "production_default_enabled": bool(strict_production_gate.get("production_default_enabled")),
            "vendor_lock_contract_version": str(
                vendor_lock_evidence.get("vendor_lock_contract_version") or ""
            ),
            "vendor_lock_status": str(vendor_lock_evidence.get("vendor_lock_status") or ""),
            "vendor_lock_missing_sections": list(vendor_lock_missing_sections),
            "vendor_lock_current_posture": str(vendor_lock_evidence.get("current_posture") or ""),
            "vendor_lock_sql_row_lease_fencing": bool(
                vendor_lock_evidence.get("sql_row_lease_fencing")
            ),
            "vendor_lock_sql_row_lease_is_vendor_lock": bool(
                vendor_lock_evidence.get("sql_row_lease_is_vendor_lock")
            ),
            "vendor_lock_adapter_present": bool(
                vendor_lock_evidence.get("vendor_lock_adapter_present")
            ),
            "vendor_lock_adapter_contract_version": str(
                vendor_lock_evidence.get("vendor_lock_adapter_contract_version") or ""
            ),
            "vendor_lock_adapter_status": str(
                vendor_lock_evidence.get("vendor_lock_adapter_status") or ""
            ),
            "vendor_lock_adapter_target_backend": str(
                vendor_lock_evidence.get("vendor_lock_adapter_target_backend") or ""
            ),
            "vendor_lock_adapter_scope": str(
                vendor_lock_evidence.get("vendor_lock_adapter_scope") or ""
            ),
            "vendor_lock_adapter_fencing_strategy": str(
                vendor_lock_evidence.get("vendor_lock_adapter_fencing_strategy") or ""
            ),
            "vendor_lock_adapter_ttl_renewal_strategy": str(
                vendor_lock_evidence.get("vendor_lock_adapter_ttl_renewal_strategy") or ""
            ),
            "vendor_lock_adapter_failover_strategy": str(
                vendor_lock_evidence.get("vendor_lock_adapter_failover_strategy") or ""
            ),
            "vendor_lock_adapter_stale_cleanup_strategy": str(
                vendor_lock_evidence.get("vendor_lock_adapter_stale_cleanup_strategy") or ""
            ),
            "vendor_lock_adapter_acquire_supported": bool(
                vendor_lock_evidence.get("vendor_lock_adapter_acquire_supported")
            ),
            "vendor_lock_adapter_renew_supported": bool(
                vendor_lock_evidence.get("vendor_lock_adapter_renew_supported")
            ),
            "vendor_lock_adapter_release_supported": bool(
                vendor_lock_evidence.get("vendor_lock_adapter_release_supported")
            ),
            "vendor_lock_adapter_probe_supported": bool(
                vendor_lock_evidence.get("vendor_lock_adapter_probe_supported")
            ),
            "vendor_lock_adapter_production_allowed": bool(
                vendor_lock_evidence.get("vendor_lock_adapter_production_allowed")
            ),
            "vendor_lock_adapter_sql_row_lease_is_vendor_lock": bool(
                vendor_lock_evidence.get("vendor_lock_adapter_sql_row_lease_is_vendor_lock")
            ),
            "vendor_lock_adapter_missing_sections": list(vendor_lock_adapter_missing_sections),
            "vendor_lock_adapter_kind": str(vendor_lock_evidence.get("lock_adapter_kind") or ""),
            "postgres_probe_contract_version": str(
                postgres_probe_default.get("contract_version") or ""
            ),
            "postgres_probe_status": str(postgres_probe_default.get("overall_status") or ""),
            "postgres_probe_missing_sections": list(postgres_probe_missing_sections),
            "postgres_probe_executes": bool(postgres_probe_default.get("executes_probe")),
            "postgres_probe_sql_row_lease_is_vendor_lock": bool(
                postgres_probe_default.get("sql_row_lease_is_vendor_lock")
            ),
            "postgres_probe_ready_status": str(postgres_probe_ready.get("overall_status") or ""),
            "postgres_probe_ready_executes": bool(postgres_probe_ready.get("executes_probe")),
            "postgres_execution_seam_contract_version": str(
                postgres_execution_default_contract.get("contract_version") or ""
            ),
            "postgres_execution_default_status": str(
                postgres_execution_default_contract.get("overall_status") or ""
            ),
            "postgres_execution_default_executor_bound": bool(
                postgres_execution_default_contract.get("executor_bound")
            ),
            "postgres_execution_default_enabled_by_default": bool(
                postgres_execution_default_contract.get("enabled_by_default")
            ),
            "postgres_execution_default_production_allowed": bool(
                postgres_execution_default_contract.get("production_lock_allowed")
            ),
            "postgres_execution_default_missing_sections": list(
                postgres_execution_default_contract.get("missing_sections")
                if isinstance(postgres_execution_default_contract.get("missing_sections"), list)
                else []
            ),
            "postgres_execution_default_probe_status": str(
                postgres_execution_default_probe.get("status") or ""
            ),
            "postgres_execution_default_probe_executed": bool(
                postgres_execution_default_probe.get("executed")
            ),
            "postgres_execution_opt_in_status": str(
                postgres_execution_opt_in_contract.get("overall_status") or ""
            ),
            "postgres_execution_opt_in_executor_bound": bool(
                postgres_execution_opt_in_contract.get("executor_bound")
            ),
            "postgres_execution_opt_in_enabled_by_default": bool(
                postgres_execution_opt_in_contract.get("enabled_by_default")
            ),
            "postgres_execution_opt_in_production_allowed": bool(
                postgres_execution_opt_in_contract.get("production_lock_allowed")
            ),
            "postgres_execution_opt_in_probe_status": str(
                postgres_execution_opt_in_probe.get("status") or ""
            ),
            "postgres_execution_opt_in_probe_executed": bool(
                postgres_execution_opt_in_probe.get("executed")
            ),
            "postgres_execution_opt_in_acquire_status": str(
                postgres_execution_opt_in_acquire.get("status") or ""
            ),
            "postgres_execution_opt_in_acquire_executed": bool(
                postgres_execution_opt_in_acquire.get("executed")
            ),
            "postgres_execution_opt_in_acquired": bool(
                postgres_execution_opt_in_acquire.get("acquired")
            ),
            "postgres_execution_opt_in_envelope_count": len(postgres_execution_envelopes),
            "postgres_rollout_consumer_contract_version": str(
                postgres_rollout_consumer_default.get("contract_version") or ""
            ),
            "postgres_rollout_consumer_default_status": str(
                postgres_rollout_consumer_default.get("overall_status") or ""
            ),
            "postgres_rollout_consumer_default_missing_sections": list(
                postgres_rollout_consumer_default_missing
            ),
            "postgres_rollout_consumer_default_will_enable_default": bool(
                postgres_rollout_consumer_default.get("will_enable_production_default")
            ),
            "postgres_rollout_consumer_default_executes_lock": bool(
                postgres_rollout_consumer_default.get("executes_advisory_lock")
            ),
            "postgres_rollout_consumer_ready_status": str(
                postgres_rollout_consumer_ready.get("overall_status") or ""
            ),
            "postgres_rollout_consumer_ready_target_backend": str(
                postgres_rollout_consumer_ready.get("target_backend") or ""
            ),
            "postgres_rollout_consumer_ready_lock_adapter_kind": str(
                postgres_rollout_consumer_ready.get("lock_adapter_kind") or ""
            ),
            "postgres_rollout_consumer_ready_will_enable_default": bool(
                postgres_rollout_consumer_ready.get("will_enable_production_default")
            ),
            "postgres_rollout_consumer_ready_executes_lock": bool(
                postgres_rollout_consumer_ready.get("executes_advisory_lock")
            ),
            "postgres_rollout_consumer_input_source_status": str(
                postgres_rollout_consumer_ready_input.get("overall_status") or ""
            ),
            "postgres_rollout_consumer_input_source_ready": bool(
                postgres_rollout_consumer_ready_input.get("ready")
            ),
            "postgres_rollout_consumer_input_source_kind": str(
                postgres_rollout_consumer_ready_input.get("input_source_kind") or ""
            ),
            "postgres_target_binding_contract_version": str(
                postgres_target_binding_default.get("contract_version") or ""
            ),
            "postgres_target_binding_default_status": str(
                postgres_target_binding_default.get("overall_status") or ""
            ),
            "postgres_target_binding_default_missing_sections": list(
                postgres_target_binding_default_missing
            ),
            "postgres_target_binding_default_will_enable_lock": bool(
                postgres_target_binding_default.get("will_enable_production_lock")
            ),
            "postgres_target_binding_default_executes_lock": bool(
                postgres_target_binding_default.get("executes_advisory_lock")
            ),
            "postgres_target_binding_ready_status": str(
                postgres_target_binding_ready.get("overall_status") or ""
            ),
            "postgres_target_binding_ready_target_backend": str(
                postgres_target_binding_ready.get("target_backend") or ""
            ),
            "postgres_target_binding_ready_lock_adapter_kind": str(
                postgres_target_binding_ready.get("lock_adapter_kind") or ""
            ),
            "postgres_target_binding_ready_will_enable_lock": bool(
                postgres_target_binding_ready.get("will_enable_production_lock")
            ),
            "postgres_target_binding_ready_executes_lock": bool(
                postgres_target_binding_ready.get("executes_advisory_lock")
            ),
            "postgres_target_binding_target_input_status": str(
                postgres_target_binding_ready_input.get("overall_status") or ""
            ),
            "postgres_target_binding_target_decision_status": str(
                postgres_target_binding_ready_decision.get("overall_status") or ""
            ),
            "postgres_target_binding_target_decision_production_allowed": bool(
                postgres_target_binding_ready_decision.get("production_lock_allowed")
            ),
            "postgres_semantics_binding_contract_version": str(
                postgres_semantics_binding_default.get("contract_version") or ""
            ),
            "postgres_semantics_binding_default_status": str(
                postgres_semantics_binding_default.get("overall_status") or ""
            ),
            "postgres_semantics_binding_default_missing_sections": list(
                postgres_semantics_binding_default_missing
            ),
            "postgres_semantics_binding_default_will_enable_lock": bool(
                postgres_semantics_binding_default.get("will_enable_production_lock")
            ),
            "postgres_semantics_binding_default_will_update_gate": bool(
                postgres_semantics_binding_default.get("will_update_production_gate")
            ),
            "postgres_semantics_binding_default_executes_lock": bool(
                postgres_semantics_binding_default.get("executes_advisory_lock")
            ),
            "postgres_semantics_binding_ready_status": str(
                postgres_semantics_binding_ready.get("overall_status") or ""
            ),
            "postgres_semantics_binding_ready_target_backend": str(
                postgres_semantics_binding_ready.get("target_backend") or ""
            ),
            "postgres_semantics_binding_ready_lock_adapter_kind": str(
                postgres_semantics_binding_ready.get("lock_adapter_kind") or ""
            ),
            "postgres_semantics_binding_ready_probe_status": str(
                postgres_semantics_binding_ready.get("postgres_probe_status") or ""
            ),
            "postgres_semantics_binding_ready_adapter_status": str(
                postgres_semantics_binding_ready.get("vendor_lock_adapter_status") or ""
            ),
            "postgres_semantics_binding_ready_semantics_status": str(
                postgres_semantics_binding_ready.get("vendor_lock_semantics_status") or ""
            ),
            "postgres_semantics_binding_ready_will_enable_lock": bool(
                postgres_semantics_binding_ready.get("will_enable_production_lock")
            ),
            "postgres_semantics_binding_ready_will_update_gate": bool(
                postgres_semantics_binding_ready.get("will_update_production_gate")
            ),
            "postgres_semantics_binding_ready_executes_lock": bool(
                postgres_semantics_binding_ready.get("executes_advisory_lock")
            ),
            "postgres_wiring_decision_contract_version": str(
                postgres_wiring_decision_default.get("contract_version") or ""
            ),
            "postgres_wiring_decision_default_status": str(
                postgres_wiring_decision_default.get("overall_status") or ""
            ),
            "postgres_wiring_decision_default_missing_sections": list(
                postgres_wiring_decision_default_missing
            ),
            "postgres_wiring_decision_default_wiring_allowed": bool(
                postgres_wiring_decision_default.get("wiring_allowed")
            ),
            "postgres_wiring_decision_default_will_update_gate": bool(
                postgres_wiring_decision_default.get("will_update_production_gate")
            ),
            "postgres_wiring_decision_default_will_enable_lock": bool(
                postgres_wiring_decision_default.get("will_enable_production_lock")
            ),
            "postgres_wiring_decision_default_executes_lock": bool(
                postgres_wiring_decision_default.get("executes_advisory_lock")
            ),
            "postgres_wiring_decision_ready_status": str(
                postgres_wiring_decision_ready.get("overall_status") or ""
            ),
            "postgres_wiring_decision_ready_semantics_binding_status": str(
                postgres_wiring_decision_ready.get("semantics_binding_status") or ""
            ),
            "postgres_wiring_decision_ready_candidate_status": str(
                postgres_wiring_decision_ready.get("candidate_semantics_status") or ""
            ),
            "postgres_wiring_decision_ready_wiring_allowed": bool(
                postgres_wiring_decision_ready.get("wiring_allowed")
            ),
            "postgres_wiring_decision_ready_target_backend": str(
                postgres_wiring_decision_ready.get("target_backend") or ""
            ),
            "postgres_wiring_decision_ready_lock_adapter_kind": str(
                postgres_wiring_decision_ready.get("lock_adapter_kind") or ""
            ),
            "postgres_wiring_decision_ready_will_update_gate": bool(
                postgres_wiring_decision_ready.get("will_update_production_gate")
            ),
            "postgres_wiring_decision_ready_will_enable_lock": bool(
                postgres_wiring_decision_ready.get("will_enable_production_lock")
            ),
            "postgres_wiring_decision_ready_executes_lock": bool(
                postgres_wiring_decision_ready.get("executes_advisory_lock")
            ),
            "production_dry_run_contract_version": str(
                production_dry_run_default.get("contract_version") or ""
            ),
            "production_dry_run_default_status": str(
                production_dry_run_default.get("overall_status") or ""
            ),
            "production_dry_run_default_missing_sections": list(
                production_dry_run_default_missing
            ),
            "production_dry_run_default_all_required_ready": bool(
                production_dry_run_default.get("all_required_sections_ready")
            ),
            "production_dry_run_default_would_allow": bool(
                production_dry_run_default.get("production_default_would_be_allowed")
            ),
            "production_dry_run_default_will_enable": bool(
                production_dry_run_default.get("will_enable_production_default")
            ),
            "production_dry_run_default_executes_lock": bool(
                production_dry_run_default.get("executes_lock")
            ),
            "production_dry_run_default_starts_worker": bool(
                production_dry_run_default.get("starts_background_worker")
            ),
            "production_dry_run_default_runs_auto_claim": bool(
                production_dry_run_default.get("runs_recovery_auto_claim")
            ),
            "production_dry_run_ready_status": str(
                production_dry_run_ready.get("overall_status") or ""
            ),
            "production_dry_run_ready_missing_sections": list(
                production_dry_run_ready_missing
            ),
            "production_dry_run_ready_all_required_ready": bool(
                production_dry_run_ready.get("all_required_sections_ready")
            ),
            "production_dry_run_ready_would_allow": bool(
                production_dry_run_ready.get("production_default_would_be_allowed")
            ),
            "production_dry_run_ready_will_enable": bool(
                production_dry_run_ready.get("will_enable_production_default")
            ),
            "production_dry_run_ready_executes_lock": bool(
                production_dry_run_ready.get("executes_lock")
            ),
            "production_dry_run_ready_starts_worker": bool(
                production_dry_run_ready.get("starts_background_worker")
            ),
            "production_dry_run_ready_runs_auto_claim": bool(
                production_dry_run_ready.get("runs_recovery_auto_claim")
            ),
            "enablement_config_consumer_contract_version": str(
                enablement_config_consumer_default.get("contract_version") or ""
            ),
            "enablement_config_consumer_default_status": str(
                enablement_config_consumer_default.get("overall_status") or ""
            ),
            "enablement_config_consumer_default_missing_sections": list(
                enablement_config_consumer_default_missing
            ),
            "enablement_config_consumer_default_will_enable": bool(
                enablement_config_consumer_default.get(
                    "will_enable_production_default"
                )
            ),
            "enablement_config_consumer_default_executes_lock": bool(
                enablement_config_consumer_default.get("executes_lock")
            ),
            "enablement_config_consumer_default_starts_worker": bool(
                enablement_config_consumer_default.get("starts_background_worker")
            ),
            "enablement_config_consumer_default_runs_auto_claim": bool(
                enablement_config_consumer_default.get("runs_recovery_auto_claim")
            ),
            "enablement_config_consumer_ready_status": str(
                enablement_config_consumer_ready.get("overall_status") or ""
            ),
            "enablement_config_consumer_ready_missing_sections": list(
                enablement_config_consumer_ready_missing
            ),
            "enablement_config_consumer_ready_target_backend": str(
                enablement_config_consumer_ready.get("target_backend") or ""
            ),
            "enablement_config_consumer_ready_lock_adapter_kind": str(
                enablement_config_consumer_ready.get("lock_adapter_kind") or ""
            ),
            "enablement_config_consumer_ready_input_source_status": str(
                (
                    enablement_config_consumer_ready.get("enablement_input_source")
                    or {}
                ).get("overall_status")
                or ""
            ),
            "enablement_config_consumer_ready_dry_run_status": str(
                (
                    enablement_config_consumer_ready.get("composition_dry_run")
                    or {}
                ).get("overall_status")
                or ""
            ),
            "enablement_config_consumer_ready_dry_run_would_allow": bool(
                enablement_config_consumer_ready.get(
                    "composition_dry_run_would_allow"
                )
            ),
            "enablement_config_consumer_ready_will_enable": bool(
                enablement_config_consumer_ready.get("will_enable_production_default")
            ),
            "enablement_config_consumer_ready_executes_lock": bool(
                enablement_config_consumer_ready.get("executes_lock")
            ),
            "enablement_config_consumer_ready_starts_worker": bool(
                enablement_config_consumer_ready.get("starts_background_worker")
            ),
            "enablement_config_consumer_ready_runs_auto_claim": bool(
                enablement_config_consumer_ready.get("runs_recovery_auto_claim")
            ),
            "enablement_config_factory_binding_default_status": str(
                factory_binding_default.get("overall_status") or ""
            ),
            "enablement_config_factory_binding_ready_status": str(
                factory_binding_ready.get("overall_status") or ""
            ),
            "enablement_config_factory_binding_ready_config_id": str(
                factory_binding_ready.get("config_id") or ""
            ),
            "enablement_config_factory_binding_will_enable": bool(
                factory_binding_ready.get("will_enable_production_default")
            ),
            "enablement_config_factory_binding_executes_lock": bool(
                factory_binding_ready.get("executes_lock")
            ),
            "enablement_config_factory_binding_starts_worker": bool(
                factory_binding_ready.get("starts_background_worker")
            ),
            "enablement_config_factory_binding_runs_auto_claim": bool(
                factory_binding_ready.get("runs_recovery_auto_claim")
            ),
            "vendor_lock_scope_defined": bool(vendor_lock_evidence.get("lock_scope_defined")),
            "vendor_lock_fencing_guarantee_defined": bool(
                vendor_lock_evidence.get("fencing_guarantee_defined")
            ),
            "vendor_lock_failover_semantics_defined": bool(
                vendor_lock_evidence.get("failover_semantics_defined")
            ),
            "vendor_lock_ttl_renewal_semantics_defined": bool(
                vendor_lock_evidence.get("ttl_renewal_semantics_defined")
            ),
            "vendor_lock_stale_owner_cleanup_defined": bool(
                vendor_lock_evidence.get("stale_owner_cleanup_defined")
            ),
            "vendor_lock_production_allowed": bool(
                vendor_lock_evidence.get("production_lock_allowed")
            ),
            "vendor_lock_target_decision_contract_version": str(
                vendor_lock_evidence.get("vendor_lock_target_decision_contract_version") or ""
            ),
            "vendor_lock_target_decision_status": str(
                vendor_lock_evidence.get("vendor_lock_target_decision_status") or ""
            ),
            "vendor_lock_target_decision_recorded": bool(
                vendor_lock_evidence.get("vendor_lock_target_decision_recorded")
            ),
            "vendor_lock_target_backend": str(
                vendor_lock_evidence.get("vendor_lock_target_backend") or ""
            ),
            "vendor_lock_target_adapter_kind": str(
                vendor_lock_evidence.get("vendor_lock_target_adapter_kind") or ""
            ),
            "vendor_lock_target_scope": str(
                vendor_lock_evidence.get("vendor_lock_target_scope") or ""
            ),
            "vendor_lock_target_fencing_strategy": str(
                vendor_lock_evidence.get("vendor_lock_target_fencing_strategy") or ""
            ),
            "vendor_lock_target_ttl_renewal_strategy": str(
                vendor_lock_evidence.get("vendor_lock_target_ttl_renewal_strategy") or ""
            ),
            "vendor_lock_target_failover_strategy": str(
                vendor_lock_evidence.get("vendor_lock_target_failover_strategy") or ""
            ),
            "vendor_lock_target_stale_cleanup_strategy": str(
                vendor_lock_evidence.get("vendor_lock_target_stale_cleanup_strategy") or ""
            ),
            "vendor_lock_target_missing_sections": list(
                vendor_lock_evidence.get("vendor_lock_target_missing_sections")
                if isinstance(vendor_lock_evidence.get("vendor_lock_target_missing_sections"), list)
                else []
            ),
            "vendor_lock_target_sql_row_lease_is_vendor_lock": bool(
                vendor_lock_evidence.get("vendor_lock_target_sql_row_lease_is_vendor_lock")
            ),
            "vendor_lock_target_production_allowed": bool(
                vendor_lock_evidence.get("vendor_lock_target_production_allowed")
            ),
            "vendor_lock_target_input_contract_version": str(
                vendor_lock_evidence.get("vendor_lock_target_input_contract_version") or ""
            ),
            "vendor_lock_target_input_source_status": str(
                vendor_lock_evidence.get("vendor_lock_target_input_source_status") or ""
            ),
            "vendor_lock_target_input_source_kind": str(
                vendor_lock_evidence.get("vendor_lock_target_input_source_kind") or ""
            ),
            "vendor_lock_target_input_decision_id": str(
                vendor_lock_evidence.get("vendor_lock_target_input_decision_id") or ""
            ),
            "vendor_lock_target_input_approved_by": str(
                vendor_lock_evidence.get("vendor_lock_target_input_approved_by") or ""
            ),
            "vendor_lock_target_input_approved_at": str(
                vendor_lock_evidence.get("vendor_lock_target_input_approved_at") or ""
            ),
            "vendor_lock_target_input_backend": str(
                vendor_lock_evidence.get("vendor_lock_target_input_backend") or ""
            ),
            "vendor_lock_target_input_adapter_kind": str(
                vendor_lock_evidence.get("vendor_lock_target_input_adapter_kind") or ""
            ),
            "vendor_lock_target_input_rollout_artifact": str(
                vendor_lock_evidence.get("vendor_lock_target_input_rollout_artifact") or ""
            ),
            "vendor_lock_target_input_config_key": str(
                vendor_lock_evidence.get("vendor_lock_target_input_config_key") or ""
            ),
            "vendor_lock_target_input_manual_approval_reference": str(
                vendor_lock_evidence.get("vendor_lock_target_input_manual_approval_reference") or ""
            ),
            "vendor_lock_target_input_missing_sections": list(
                vendor_lock_evidence.get("vendor_lock_target_input_missing_sections")
                if isinstance(vendor_lock_evidence.get("vendor_lock_target_input_missing_sections"), list)
                else []
            ),
            "vendor_lock_target_input_sql_row_lease_is_vendor_lock": bool(
                vendor_lock_evidence.get("vendor_lock_target_input_sql_row_lease_is_vendor_lock")
            ),
            "renewal_supervisor_contract_version": str(
                renewal_evidence.get("renewal_supervisor_contract_version") or ""
            ),
            "renewal_supervisor_status": str(renewal_evidence.get("renewal_supervisor_status") or ""),
            "renewal_supervisor_missing_sections": list(renewal_missing_sections),
            "renewal_supervisor_enabled_by_default": bool(
                renewal_evidence.get("supervisor_enabled_by_default")
            ),
            "renewal_supervisor_renew_once_supported": bool(
                renewal_evidence.get("renew_once_supported")
            ),
            "renewal_supervisor_owner_identity_required": bool(
                renewal_evidence.get("owner_identity_required")
            ),
            "renewal_supervisor_ttl_interval_policy_ready": bool(
                renewal_evidence.get("ttl_interval_policy_ready")
            ),
            "renewal_supervisor_controlled_lifecycle_supported": bool(
                renewal_evidence.get("controlled_lifecycle_supported")
            ),
            "renewal_supervisor_starts_by_default": bool(
                renewal_evidence.get("starts_by_default")
            ),
            "renewal_supervisor_active": bool(renewal_evidence.get("active")),
            "renewal_supervisor_last_renewal_status": str(
                renewal_evidence.get("last_renewal_status") or ""
            ),
            "renewal_supervisor_stop_supported": bool(renewal_evidence.get("stop_supported")),
            "renewal_supervisor_failure_fail_closed": bool(
                renewal_evidence.get("failure_fail_closed")
            ),
            "renewal_supervisor_lease_loss_fail_closed": bool(
                renewal_evidence.get("lease_loss_fail_closed")
            ),
            "renewal_supervisor_renew_once_status": str(
                renewal_smoke_success.get("renewal_status") or ""
            ),
            "renewal_supervisor_renew_once_background_started": bool(
                renewal_smoke_success.get("background_supervisor_started")
            ),
            "renewal_supervisor_stale_fencing_status": str(
                renewal_smoke_stale.get("renewal_status") or ""
            ),
            "renewal_supervisor_stale_fencing_reason": str(
                renewal_smoke_stale.get("reason") or ""
            ),
            "renewal_supervisor_lifecycle_initial_active": bool(
                renewal_lifecycle_initial.get("active")
            ),
            "renewal_supervisor_lifecycle_started_active": bool(
                renewal_lifecycle_started.get("active")
            ),
            "renewal_supervisor_lifecycle_started_status": str(
                renewal_lifecycle_started.get("last_renewal_status") or ""
            ),
            "renewal_supervisor_lifecycle_started_count": int(
                renewal_lifecycle_started.get("renewal_count") or 0
            ),
            "renewal_supervisor_lifecycle_stopped_active": bool(
                renewal_lifecycle_stopped.get("active")
            ),
            "renewal_supervisor_lifecycle_stopped_count": int(
                renewal_lifecycle_stopped.get("renewal_count") or 0
            ),
            "rollout_readiness_contract_version": str(
                rollout_evidence.get("rollout_readiness_contract_version") or ""
            ),
            "rollout_readiness_status": str(rollout_evidence.get("rollout_readiness_status") or ""),
            "rollout_missing_sections": list(rollout_missing_sections),
            "production_rollout_confirmed": bool(rollout_evidence.get("production_rollout_confirmed")),
            "rollout_migration_ready": bool(rollout_evidence.get("migration_ready")),
            "rollout_stale_fencing_verified": bool(rollout_evidence.get("stale_fencing_verified")),
            "rollout_rollback_plan_ready": bool(rollout_evidence.get("rollback_plan_ready")),
            "rollout_operationalization_status": str(
                rollout_evidence.get("rollout_operationalization_status") or ""
            ),
            "rollout_mode": str(rollout_evidence.get("rollout_mode") or ""),
            "rollout_missing_artifacts": list(
                rollout_evidence.get("rollout_missing_artifacts")
                if isinstance(rollout_evidence.get("rollout_missing_artifacts"), list)
                else []
            ),
            "rollout_rollback_plan_status": str(
                rollout_evidence.get("rollback_plan_status") or ""
            ),
            "rollout_fallback_policy_status": str(
                rollout_evidence.get("fallback_policy_status") or ""
            ),
            "rollout_renewal_lifecycle_verification_status": str(
                rollout_evidence.get("renewal_lifecycle_verification_status") or ""
            ),
            "rollout_auto_claim_decision_status": str(
                rollout_evidence.get("auto_claim_decision_status") or ""
            ),
            "rollout_confirmation_decision_contract_version": str(
                rollout_evidence.get("rollout_confirmation_decision_contract_version") or ""
            ),
            "rollout_confirmation_decision_status": str(
                rollout_evidence.get("rollout_confirmation_decision_status") or ""
            ),
            "rollout_decision_recorded": bool(
                rollout_evidence.get("rollout_decision_recorded")
            ),
            "rollout_decision_id": str(rollout_evidence.get("rollout_decision_id") or ""),
            "rollout_approved_by": str(rollout_evidence.get("rollout_approved_by") or ""),
            "rollout_approved_at": str(rollout_evidence.get("rollout_approved_at") or ""),
            "rollout_target_store_mode": str(
                rollout_evidence.get("rollout_target_store_mode") or ""
            ),
            "rollout_confirmation_missing_sections": list(
                rollout_evidence.get("rollout_confirmation_missing_sections")
                if isinstance(
                    rollout_evidence.get("rollout_confirmation_missing_sections"), list
                )
                else []
            ),
            "rollout_confirmation_production_rollout_confirmed": bool(
                rollout_evidence.get("rollout_confirmation_production_rollout_confirmed")
            ),
            "rollout_confirmation_input_contract_version": str(
                rollout_evidence.get("rollout_confirmation_input_contract_version") or ""
            ),
            "rollout_confirmation_input_source_status": str(
                rollout_evidence.get("rollout_confirmation_input_source_status") or ""
            ),
            "rollout_confirmation_input_source_kind": str(
                rollout_evidence.get("rollout_confirmation_input_source_kind") or ""
            ),
            "rollout_confirmation_input_decision_id": str(
                rollout_evidence.get("rollout_confirmation_input_decision_id") or ""
            ),
            "rollout_confirmation_input_approved_by": str(
                rollout_evidence.get("rollout_confirmation_input_approved_by") or ""
            ),
            "rollout_confirmation_input_approved_at": str(
                rollout_evidence.get("rollout_confirmation_input_approved_at") or ""
            ),
            "rollout_confirmation_input_target_store_mode": str(
                rollout_evidence.get("rollout_confirmation_input_target_store_mode") or ""
            ),
            "rollout_confirmation_input_rollback_plan_reference": str(
                rollout_evidence.get("rollout_confirmation_input_rollback_plan_reference") or ""
            ),
            "rollout_confirmation_input_fallback_policy_reference": str(
                rollout_evidence.get("rollout_confirmation_input_fallback_policy_reference") or ""
            ),
            "rollout_confirmation_input_renewal_lifecycle_reference": str(
                rollout_evidence.get("rollout_confirmation_input_renewal_lifecycle_reference")
                or ""
            ),
            "rollout_confirmation_input_auto_claim_decision_reference": str(
                rollout_evidence.get("rollout_confirmation_input_auto_claim_decision_reference")
                or ""
            ),
            "rollout_confirmation_input_missing_sections": list(
                rollout_evidence.get("rollout_confirmation_input_missing_sections")
                if isinstance(
                    rollout_evidence.get("rollout_confirmation_input_missing_sections"), list
                )
                else []
            ),
            "rollout_confirmation_input_sql_row_lease_is_authority": bool(
                rollout_evidence.get("rollout_confirmation_input_sql_row_lease_is_authority")
            ),
            "auto_claim_policy_contract_version": str(
                auto_claim_evidence.get("auto_claim_policy_contract_version") or ""
            ),
            "auto_claim_policy_status": str(auto_claim_evidence.get("auto_claim_policy_status") or ""),
            "auto_claim_missing_sections": list(auto_claim_missing_sections),
            "auto_claim_enabled_by_default": bool(
                auto_claim_evidence.get("auto_claim_enabled_by_default")
            ),
            "auto_claim_descriptor_evidence_fallback": bool(
                auto_claim_evidence.get("descriptor_evidence_fallback")
            ),
            "auto_claim_lease_validation_required": bool(
                auto_claim_evidence.get("lease_validation_required")
            ),
            "auto_claim_entrypoint_allowlist_ready": bool(
                auto_claim_evidence.get("entrypoint_allowlist_ready")
            ),
            "auto_claim_entrypoint_allowlist_contract_version": str(
                auto_claim_evidence.get("auto_claim_entrypoint_allowlist_contract_version") or ""
            ),
            "auto_claim_entrypoint_allowlist_status": str(
                auto_claim_evidence.get("auto_claim_entrypoint_allowlist_status") or ""
            ),
            "auto_claim_allowed_entrypoints": list(
                auto_claim_evidence.get("auto_claim_allowed_entrypoints")
                if isinstance(auto_claim_evidence.get("auto_claim_allowed_entrypoints"), list)
                else []
            ),
            "auto_claim_missing_entrypoints": list(
                auto_claim_evidence.get("auto_claim_missing_entrypoints")
                if isinstance(auto_claim_evidence.get("auto_claim_missing_entrypoints"), list)
                else []
            ),
            "auto_claim_default_auto_claim_enabled": bool(
                auto_claim_evidence.get("auto_claim_default_auto_claim_enabled")
            ),
            "auto_claim_requires_production_gate_ready": bool(
                auto_claim_evidence.get("auto_claim_requires_production_gate_ready")
            ),
            "auto_claim_enablement_gate_contract_version": str(
                auto_claim_evidence.get("auto_claim_enablement_gate_contract_version") or ""
            ),
            "auto_claim_enablement_gate_status": str(
                auto_claim_evidence.get("auto_claim_enablement_gate_status") or ""
            ),
            "auto_claim_will_auto_claim": bool(
                auto_claim_evidence.get("auto_claim_will_auto_claim")
            ),
            "auto_claim_requested_entrypoint": str(
                auto_claim_evidence.get("auto_claim_requested_entrypoint") or ""
            ),
            "auto_claim_enablement_missing_sections": list(
                auto_claim_evidence.get("auto_claim_enablement_missing_sections")
                if isinstance(
                    auto_claim_evidence.get("auto_claim_enablement_missing_sections"), list
                )
                else []
            ),
            "auto_claim_enablement_blocked_reason": str(
                auto_claim_evidence.get("auto_claim_enablement_blocked_reason") or ""
            ),
            "ownership_audit_contract_version": str(
                audit_evidence.get("ownership_audit_contract_version") or ""
            ),
            "ownership_audit_status": str(audit_evidence.get("ownership_audit_status") or ""),
            "ownership_audit_missing_sections": list(audit_missing_sections),
            "ownership_audit_compact_evidence": bool(
                audit_evidence.get("compact_ownership_evidence")
            ),
            "ownership_audit_operation_history_ready": bool(
                audit_evidence.get("operation_history_ready")
            ),
            "ownership_audit_recovery_operation_link_ready": bool(
                audit_evidence.get("recovery_operation_link_ready")
            ),
            "ownership_audit_timeline_writer_ready": bool(
                audit_evidence.get("timeline_writer_ready")
            ),
            "ownership_audit_idempotent_dedupe_ready": bool(
                audit_evidence.get("idempotent_dedupe_ready")
            ),
            "ownership_audit_authorization_source": bool(
                audit_evidence.get("authorization_source")
            ),
            "enablement_strategy_contract_version": str(
                enablement_evidence.get("enablement_strategy_contract_version") or ""
            ),
            "enablement_strategy_status": str(
                enablement_evidence.get("enablement_strategy_status") or ""
            ),
            "enablement_strategy_blocking_sections": list(enablement_blocking_sections),
            "production_default_enabled_requested": bool(
                enablement_evidence.get("production_default_enabled_requested")
            ),
            "production_default_allowed": bool(
                enablement_evidence.get("production_default_allowed")
            ),
            "enablement_input_source_contract_version": str(
                enablement_evidence.get("enablement_input_source_contract_version") or ""
            ),
            "enablement_input_source_status": str(
                enablement_evidence.get("enablement_input_source_status") or ""
            ),
            "enablement_input_source_kind": str(
                enablement_evidence.get("enablement_input_source_kind") or ""
            ),
            "enablement_request_id": str(enablement_evidence.get("enablement_request_id") or ""),
            "enablement_requested_by": str(
                enablement_evidence.get("enablement_requested_by") or ""
            ),
            "enablement_requested_at": str(
                enablement_evidence.get("enablement_requested_at") or ""
            ),
            "enablement_target_store_mode": str(
                enablement_evidence.get("enablement_target_store_mode") or ""
            ),
            "enablement_rollout_artifact": str(
                enablement_evidence.get("enablement_rollout_artifact") or ""
            ),
            "enablement_vendor_lock_decision_id": str(
                enablement_evidence.get("enablement_vendor_lock_decision_id") or ""
            ),
            "enablement_renewal_lifecycle_reference": str(
                enablement_evidence.get("enablement_renewal_lifecycle_reference") or ""
            ),
            "enablement_auto_claim_decision_reference": str(
                enablement_evidence.get("enablement_auto_claim_decision_reference") or ""
            ),
            "enablement_audit_evidence_reference": str(
                enablement_evidence.get("enablement_audit_evidence_reference") or ""
            ),
            "enablement_rollback_plan_reference": str(
                enablement_evidence.get("enablement_rollback_plan_reference") or ""
            ),
            "enablement_fallback_policy_reference": str(
                enablement_evidence.get("enablement_fallback_policy_reference") or ""
            ),
            "enablement_input_source_ready": bool(
                enablement_evidence.get("enablement_input_source_ready")
            ),
            "enablement_input_source_missing_sections": list(
                enablement_evidence.get("enablement_input_source_missing_sections")
                if isinstance(enablement_evidence.get("enablement_input_source_missing_sections"), list)
                else []
            ),
            "enablement_explicit_required": bool(
                enablement_evidence.get("explicit_enablement_required")
            ),
            "enablement_all_required_sections_ready": bool(
                enablement_evidence.get("all_required_sections_ready")
            ),
            "enablement_fail_closed_when_blocked": bool(
                enablement_evidence.get("fail_closed_when_blocked")
            ),
            "enablement_sql_row_lease_not_default_authority": bool(
                enablement_evidence.get("sql_row_lease_is_not_default_authority")
            ),
            "default_production_gate_status": str(memory_production_gate.get("overall_status") or ""),
            "configurable_knob_present": "WORKER_OWNERSHIP_STORE_MODE" in fallback_knobs,
            "hot_reloadable_knob_present": "WORKER_OWNERSHIP_STORE_MODE" in fallback_hot_reload,
            "strict_mode_status": "sqlalchemy_durable"
            if strict_ownership.get("adapter_kind") == "sqlalchemy" and bool(strict_ownership.get("durable"))
            else "unavailable",
            "strict_operational_readiness_status": str(strict_readiness.get("readiness_status") or ""),
            "strict_vendor_lock_posture": str(strict_readiness.get("vendor_lock_posture") or ""),
            "strict_migration_ready": bool(dict(strict_readiness.get("migration_checklist") or {}).get("migration_ready")),
            "fallback_mode_status": "fallback_to_memory"
            if fallback_ownership.get("adapter_kind") == "in_memory" and not bool(fallback_ownership.get("durable"))
            else "unavailable",
            "fallback_operational_readiness_status": str(fallback_readiness.get("readiness_status") or ""),
            "fallback_active": bool(fallback_readiness.get("fallback_active")),
            "failure_reason": "" if ok else "worker_ownership_store_mode_contract_incomplete",
        }
    finally:
        worker_ownership_module.WORKER_OWNERSHIP_STORE_MODE = previous_mode
        if previous_env is None:
            os.environ.pop("WORKER_OWNERSHIP_STORE_MODE", None)
        else:
            os.environ["WORKER_OWNERSHIP_STORE_MODE"] = previous_env


def _run_embedded_sdk_persistence_posture_check() -> dict:
    memory_contract = _build_smoke_factory_contract(InMemoryEmbeddedRunWorkspaceStore())
    durable_contract = _build_smoke_factory_contract(
        _SmokeDurableWorkspaceStore(),
        SQLAlchemyRuntimeWorkerOwnershipStore(lambda: None),
    )
    degraded_contract = _build_smoke_factory_contract(_SmokeDegradedWorkspaceStore())
    memory_interface = dict(memory_contract.get("persistence_interface") or {})
    durable_interface = dict(durable_contract.get("persistence_interface") or {})
    degraded_interface = dict(degraded_contract.get("persistence_interface") or {})
    durable_production_gate = dict(durable_interface.get("production_recovery_gate") or {})
    durable_missing_sections = (
        durable_production_gate.get("missing_sections")
        if isinstance(durable_production_gate.get("missing_sections"), list)
        else []
    )
    durable_sections = [
        item for item in durable_production_gate.get("sections") or [] if isinstance(item, dict)
    ]
    durable_worker_ownership_section = next(
        (
            item
            for item in durable_sections
            if str(item.get("name") or "").strip() == "worker_ownership_production_gate"
        ),
        {},
    )
    durable_worker_ownership_evidence = dict(durable_worker_ownership_section.get("evidence") or {})
    durable_worker_ownership_missing_sections = (
        durable_worker_ownership_evidence.get("worker_ownership_missing_sections")
        if isinstance(durable_worker_ownership_evidence.get("worker_ownership_missing_sections"), list)
        else []
    )
    recovery_operation_contract = build_recovery_operation_contract()
    audit_readiness = dict(recovery_operation_contract.get("recovery_audit_production_readiness") or {})
    registry_checkpoint_policy = build_production_recovery_registry_checkpoint_policy_contract()
    ok = (
        memory_interface.get("persistence_posture") == "memory_preview"
        and memory_interface.get("cross_process_block_reason") == "workspace_backend_not_durable"
        and durable_interface.get("persistence_posture") == "durable_ready"
        and bool(durable_interface.get("cross_process_candidate"))
        and durable_production_gate.get("contract_version")
        == "phase-ii-durable-workspace-production-recovery-gate-v1"
        and durable_production_gate.get("overall_status") == "blocked"
        and "descriptor_lifecycle_governance" not in durable_missing_sections
        and "loader_execution_handoff_policy" not in durable_missing_sections
        and "recovery_audit_operation_history" not in durable_missing_sections
        and "registry_binding_resolution" not in durable_missing_sections
        and "checkpoint_resume_cursor_gate" not in durable_missing_sections
        and "durable_backend_migration_rollout" in durable_missing_sections
        and "worker_ownership_production_gate" in durable_missing_sections
        and durable_worker_ownership_evidence.get("worker_ownership_gate_contract_version")
        == "phase-ii-worker-ownership-production-gate-v1"
        and durable_worker_ownership_evidence.get("worker_ownership_gate_status") == "blocked"
        and durable_worker_ownership_evidence.get("worker_ownership_production_default_enabled") is False
        and "vendor_lock_semantics" in durable_worker_ownership_missing_sections
        and "heartbeat_renewal_supervisor" in durable_worker_ownership_missing_sections
        and audit_readiness.get("contract_version") == "phase-ii-recovery-audit-production-gate-v1"
        and audit_readiness.get("ready") is True
        and audit_readiness.get("operation_history_supported") is True
        and audit_readiness.get("audit_summary_supported") is True
        and audit_readiness.get("timeline_writer_available") is True
        and audit_readiness.get("idempotent_trace_dedupe") is True
        and audit_readiness.get("authorization_source") is False
        and registry_checkpoint_policy.get("contract_version")
        == "phase-ii-production-recovery-registry-checkpoint-policy-v1"
        and registry_checkpoint_policy.get("ready") is True
        and registry_checkpoint_policy.get("registry_binding_policy_ready") is True
        and registry_checkpoint_policy.get("checkpoint_resume_cursor_policy_ready") is True
        and registry_checkpoint_policy.get("authorization_source") is False
        and durable_production_gate.get("production_default_enabled") is False
        and degraded_interface.get("persistence_posture") == "durable_degraded"
        and degraded_interface.get("cross_process_block_reason") == "workspace_backend_fallback_active"
    )
    return {
        "ok": ok,
        "contract_version": str(durable_interface.get("contract_version") or ""),
        "memory_posture": str(memory_interface.get("persistence_posture") or ""),
        "durable_posture": str(durable_interface.get("persistence_posture") or ""),
        "degraded_posture": str(degraded_interface.get("persistence_posture") or ""),
        "memory_cross_process_block_reason": str(memory_interface.get("cross_process_block_reason") or ""),
        "degraded_cross_process_block_reason": str(degraded_interface.get("cross_process_block_reason") or ""),
        "durable_cross_process_candidate": bool(durable_interface.get("cross_process_candidate")),
        "production_recovery_gate_contract_version": str(durable_production_gate.get("contract_version") or ""),
        "production_recovery_gate_status": str(durable_production_gate.get("overall_status") or ""),
        "production_recovery_gate_missing_sections": list(durable_missing_sections),
        "production_recovery_default_enabled": bool(durable_production_gate.get("production_default_enabled")),
        "production_recovery_worker_ownership_gate_contract_version": str(
            durable_worker_ownership_evidence.get("worker_ownership_gate_contract_version") or ""
        ),
        "production_recovery_worker_ownership_gate_status": str(
            durable_worker_ownership_evidence.get("worker_ownership_gate_status") or ""
        ),
        "production_recovery_worker_ownership_default_enabled": bool(
            durable_worker_ownership_evidence.get("worker_ownership_production_default_enabled")
        ),
        "production_recovery_worker_ownership_missing_sections": list(
            durable_worker_ownership_missing_sections
        ),
        "recovery_audit_contract_version": str(audit_readiness.get("contract_version") or ""),
        "recovery_audit_ready": bool(audit_readiness.get("ready")),
        "recovery_audit_operation_history_supported": bool(audit_readiness.get("operation_history_supported")),
        "recovery_audit_summary_supported": bool(audit_readiness.get("audit_summary_supported")),
        "recovery_audit_timeline_writer_available": bool(audit_readiness.get("timeline_writer_available")),
        "recovery_audit_idempotent_trace_dedupe": bool(audit_readiness.get("idempotent_trace_dedupe")),
        "recovery_audit_authorization_source": bool(audit_readiness.get("authorization_source")),
        "registry_checkpoint_policy_contract_version": str(
            registry_checkpoint_policy.get("contract_version") or ""
        ),
        "registry_checkpoint_policy_ready": bool(registry_checkpoint_policy.get("ready")),
        "registry_binding_policy_ready": bool(registry_checkpoint_policy.get("registry_binding_policy_ready")),
        "checkpoint_resume_cursor_policy_ready": bool(
            registry_checkpoint_policy.get("checkpoint_resume_cursor_policy_ready")
        ),
        "registry_checkpoint_policy_authorization_source": bool(
            registry_checkpoint_policy.get("authorization_source")
        ),
        "failure_reason": "" if ok else "embedded_sdk_persistence_posture_incomplete",
    }


def _run_recovery_retry_evidence_contract_check() -> dict:
    store = InMemoryEmbeddedRunWorkspaceStore()
    writer = EmbeddedAgentRuntimeSDK(workspace_store=store)
    result = writer.create_run({"conversation_id": 42, "user_id": 7, "run_kind": "chat"})
    executed = writer.execute_run(
        result["run"]["run_id"],
        tool_policy=lambda _run: {
            "status": "approval_required",
            "tool_name": "filesystem_write",
            "tool_args": {"path": "retry-smoke.md"},
            "reason": "Smoke validates explicit recovery retry evidence.",
        },
        tool_executor=lambda _run: {
            "tool_name": "filesystem_write",
            "args": {"path": "retry-smoke.md"},
            "result": "ok",
        },
    )

    reader = EmbeddedAgentRuntimeSDK(workspace_store=store)
    try:
        reader.submit_approval(
            executed["approval_request"]["request_id"],
            "approved",
            retry_attempt={
                "attempt_number": 3,
                "max_attempts": 3,
                "previous_operation_id": "recovery_operation:smoke:submit:first",
                "idempotency_key": "recovery:smoke:submit_approval.approved",
            },
        )
    except ValueError as exc:
        failure_message = str(exc)
    else:
        failure_message = ""

    failed_event = next(
        (
            event
            for event in reader.stream_events(result["run"]["run_id"])
            if event.get("status_kind") == "recovery_failed_closed"
        ),
        {},
    )
    retry = dict((failed_event.get("recovery_operation") or {}).get("retry") or {})
    recovery_reason = str(retry.get("recovery_reason") or "").strip()
    retry_status = str(retry.get("status") or "").strip()
    attempt_number = int(retry.get("attempt_number") or 0)
    max_attempts = int(retry.get("max_attempts") or 0)
    idempotency_key = str(retry.get("idempotency_key") or "").strip()
    ok = (
        "workspace_backend_not_durable" in failure_message
        and str(failed_event.get("status_kind") or "").strip() == "recovery_failed_closed"
        and str(retry.get("contract_version") or "").strip() == "phase-ii-recovery-retry-protocol-v1"
        and attempt_number == 3
        and max_attempts == 3
        and retry_status == "exhausted"
        and not bool(retry.get("retryable"))
        and bool(retry.get("terminal"))
        and recovery_reason == "workspace_backend_not_durable"
        and bool(idempotency_key)
    )
    return {
        "ok": ok,
        "contract_version": str(retry.get("contract_version") or ""),
        "attempt_number": attempt_number,
        "max_attempts": max_attempts,
        "retry_status": retry_status,
        "retryable": bool(retry.get("retryable")),
        "terminal": bool(retry.get("terminal")),
        "recovery_reason": recovery_reason,
        "idempotency_key_present": bool(idempotency_key),
        "failure_reason": "" if ok else "recovery_retry_evidence_incomplete",
    }


def _run_recovery_retry_scheduler_contract_check() -> dict:
    store = _SmokeDurableWorkspaceStore()
    registry = InMemoryEmbeddedContinuationRegistry()

    def _tool_executor(_run):
        return {
            "tool_name": "filesystem_write",
            "args": {"path": "retry-scheduler.md"},
            "result": "ok",
        }

    def _reviewer(_run):
        return {
            "reviewer": "quality_gate",
            "status": "approved",
            "summary": "retry scheduler ok",
        }

    registry.register("tool_executor.filesystem_write", _tool_executor)
    registry.register("reviewer.quality_gate", _reviewer)
    writer = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
    result = writer.create_run({"conversation_id": 42, "user_id": 7, "run_kind": "chat"})
    executed = writer.execute_run(
        result["run"]["run_id"],
        tool_policy=lambda _run: {
            "status": "approval_required",
            "tool_name": "filesystem_write",
            "tool_args": {"path": "retry-scheduler.md"},
            "reason": "Smoke validates recovery retry scheduler.",
        },
        tool_executor=_tool_executor,
        reviewer=_reviewer,
    )
    run_id = result["run"]["run_id"]
    request_id = executed["approval_request"]["request_id"]
    previous_operation_id = f"recovery_operation:{run_id}:submit_approval.approved:previous"
    previous_operation = {
        "contract_version": "phase-ii-durable-recovery-operation-v1",
        "operation_id": previous_operation_id,
        "run_id": run_id,
        "entrypoint": "submit_approval.approved",
        "operation_status": "blocked",
        "recovery_reason": "transient_workspace_unavailable",
        "blocked_reason": "transient_workspace_unavailable",
        "continuation_ref": {
            "continuation_kind": "tool_approval",
            "continuation_id": request_id,
            "descriptor_present": True,
            "binding_ids": {"tool_executor_binding_id": "tool_executor.filesystem_write"},
            "missing_binding_ids": [],
        },
        "workspace_backend": {
            "backend_kind": "smoke_durable",
            "backend_mode": "strict_smoke",
            "durable": True,
            "fallback_active": False,
        },
        "persistence_posture": "durable_ready",
        "worker_ownership": {
            "implemented": False,
            "boundary": "worker_lease_not_implemented",
        },
        "recorded_at": "2026-05-24T00:00:00+00:00",
    }
    snapshot = store.get_run_snapshot(run_id)
    metadata = dict(snapshot.get("metadata") or {})
    metadata["latest_recovery_operation"] = dict(previous_operation)
    metadata["recovery_operations"] = [dict(previous_operation)]
    snapshot["metadata"] = metadata
    store.save_run_snapshot(snapshot)

    disabled_reader = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
    disabled_decision = disabled_reader.schedule_recovery_retry(run_id)
    automatic_reader = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
    automatic_decision = automatic_reader.schedule_recovery_retry(
        run_id,
        enabled=True,
        production_automatic_retry=True,
    )
    enabled_reader = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
    executed_decision = enabled_reader.schedule_recovery_retry(run_id, enabled=True)
    latest_operation = dict(executed_decision.get("latest_operation") or {})
    retry = dict(latest_operation.get("retry") or {})
    production_gate = dict(automatic_decision.get("production_scheduler_gate") or {})
    missing_sections = (
        production_gate.get("missing_sections")
        if isinstance(production_gate.get("missing_sections"), list)
        else []
    )
    ok = (
        str(disabled_decision.get("contract_version") or "").strip() == "phase-ii-recovery-retry-scheduler-v1"
        and str(disabled_decision.get("status") or "").strip() == "disabled"
        and bool(disabled_decision.get("eligible"))
        and not bool(disabled_decision.get("will_execute"))
        and str(automatic_decision.get("status") or "").strip() == "blocked"
        and str(automatic_decision.get("blocked_reason") or "").strip() == "production_scheduler_gate_blocked"
        and not bool(automatic_decision.get("will_execute"))
        and str(production_gate.get("contract_version") or "").strip()
        == "phase-ii-recovery-retry-production-scheduler-gate-v1"
        and str(production_gate.get("overall_status") or "").strip() == "blocked"
        and "durable_scheduling_state" in missing_sections
        and not bool(production_gate.get("automatic_retry_enabled_by_default"))
        and str(executed_decision.get("status") or "").strip() == "executed"
        and bool(executed_decision.get("will_execute"))
        and str(latest_operation.get("operation_status") or "").strip() == "recovered"
        and int(retry.get("attempt_number") or 0) == 1
        and str(retry.get("previous_operation_id") or "").strip() == previous_operation_id
        and str(retry.get("status") or "").strip() == "retryable"
        and str(retry.get("recovery_reason") or "").strip() == "transient_workspace_unavailable"
        and bool(retry.get("idempotency_key"))
    )
    return {
        "ok": ok,
        "contract_version": str(disabled_decision.get("contract_version") or ""),
        "default_status": str(disabled_decision.get("status") or ""),
        "default_eligible": bool(disabled_decision.get("eligible")),
        "default_will_execute": bool(disabled_decision.get("will_execute")),
        "production_gate_contract_version": str(production_gate.get("contract_version") or ""),
        "production_gate_status": str(production_gate.get("overall_status") or ""),
        "production_gate_missing_sections": list(missing_sections),
        "production_gate_blocked_reason": str(automatic_decision.get("blocked_reason") or ""),
        "production_automatic_retry_enabled_by_default": bool(
            production_gate.get("automatic_retry_enabled_by_default")
        ),
        "production_automatic_will_execute": bool(automatic_decision.get("will_execute")),
        "enabled_status": str(executed_decision.get("status") or ""),
        "enabled_will_execute": bool(executed_decision.get("will_execute")),
        "latest_operation_status": str(latest_operation.get("operation_status") or ""),
        "attempt_number": int(retry.get("attempt_number") or 0),
        "previous_operation_id_present": bool(str(retry.get("previous_operation_id") or "").strip()),
        "idempotency_key_present": bool(str(retry.get("idempotency_key") or "").strip()),
        "retry_status": str(retry.get("status") or ""),
        "recovery_reason": str(retry.get("recovery_reason") or ""),
        "failure_reason": "" if ok else "recovery_retry_scheduler_incomplete",
    }


def _run_child_executor_promotion_gate_contract_check(runtime_profile_payload: dict) -> dict:
    gate = dict((runtime_profile_payload or {}).get("child_executor_promotion_gate") or {})
    blockers = gate.get("blockers") if isinstance(gate.get("blockers"), list) else []
    prerequisites = gate.get("child_executor_execution_prerequisites")
    prerequisites = prerequisites if isinstance(prerequisites, dict) else {}
    missing_requirements = (
        prerequisites.get("missing_requirements")
        if isinstance(prerequisites.get("missing_requirements"), list)
        else []
    )
    requirement_entries = (
        prerequisites.get("requirements")
        if isinstance(prerequisites.get("requirements"), list)
        else []
    )
    contract_version = str(gate.get("contract_version") or "").strip()
    gate_status = str(gate.get("gate_status") or "").strip()
    failure_reason = str(gate.get("failure_reason") or "").strip()
    recommended_next_step = str(gate.get("recommended_next_step") or "").strip()
    prerequisites_contract_version = str(prerequisites.get("contract_version") or "").strip()
    prerequisites_status = str(prerequisites.get("overall_status") or "").strip()
    explicit_binding = dict(prerequisites.get("explicit_executor_binding") or {})
    explicit_binding_status = str(explicit_binding.get("binding_status") or "").strip()
    explicit_binding_ready = bool(explicit_binding.get("ready"))
    explicit_binding_source = str(explicit_binding.get("binding_source") or "").strip()
    context_budget_policy = dict(
        prerequisites.get("child_executor_context_budget_policy")
        or prerequisites.get("context_budget_policy")
        or {}
    )
    context_budget_policy_status = str(context_budget_policy.get("overall_status") or "").strip()
    context_budget_policy_ready = bool(context_budget_policy.get("ready"))
    context_budget_policy_missing_sections = (
        context_budget_policy.get("missing_sections")
        if isinstance(context_budget_policy.get("missing_sections"), list)
        else []
    )
    merge_handoff = dict(
        prerequisites.get("child_result_merge_handoff_contract")
        or prerequisites.get("merge_handoff_contract")
        or {}
    )
    merge_handoff_status = str(merge_handoff.get("overall_status") or "").strip()
    merge_handoff_ready = bool(merge_handoff.get("ready"))
    merge_handoff_missing_sections = (
        merge_handoff.get("missing_sections")
        if isinstance(merge_handoff.get("missing_sections"), list)
        else []
    )

    opt_in_sdk = EmbeddedAgentRuntimeSDK(workspace_store=InMemoryEmbeddedRunWorkspaceStore())
    opt_in_payload = {
        "input": "风险复核子任务",
        "child_context_budget": {"max_turns": 1},
        "merge_strategy": "append_summary",
        "worker_runtime_backend": "embedded_sdk_worker",
        "explicit_executor_binding_opt_in": True,
    }
    opt_in_gate = opt_in_sdk.evaluate_child_executor_gate(opt_in_payload)
    opt_in_prerequisites = dict(opt_in_gate.get("child_executor_execution_prerequisites") or {})
    opt_in_explicit_binding = dict(opt_in_prerequisites.get("explicit_executor_binding") or {})
    opt_in_context_budget_policy = dict(
        opt_in_prerequisites.get("child_executor_context_budget_policy")
        or opt_in_prerequisites.get("context_budget_policy")
        or {}
    )
    opt_in_merge_handoff = dict(
        opt_in_prerequisites.get("child_result_merge_handoff_contract")
        or opt_in_prerequisites.get("merge_handoff_contract")
        or {}
    )
    opt_in_binding = opt_in_sdk.bind_child_executor_routing(opt_in_payload)
    opt_in_execution = opt_in_sdk.execute_bound_child_executor(opt_in_binding)

    ok = (
        bool(contract_version)
        and gate_status == "blocked"
        and bool(gate.get("allowed")) is False
        and bool(failure_reason)
        and isinstance(gate.get("blockers"), list)
        and bool(recommended_next_step)
        and bool(prerequisites_contract_version)
        and prerequisites_status == "blocked"
        and bool(prerequisites.get("ready")) is False
        and isinstance(prerequisites.get("requirements"), list)
        and isinstance(prerequisites.get("missing_requirements"), list)
        and "explicit_executor_binding_opt_in" in [str(item) for item in missing_requirements]
        and "child_context_budget_defined" in [str(item) for item in missing_requirements]
        and "child_result_merge_semantics_defined" in [str(item) for item in missing_requirements]
        and explicit_binding_status == "blocked"
        and not explicit_binding_ready
        and context_budget_policy_status == "blocked"
        and not context_budget_policy_ready
        and "budget_source" in [str(item) for item in context_budget_policy_missing_sections]
        and "bounded_budget_limit" in [str(item) for item in context_budget_policy_missing_sections]
        and opt_in_explicit_binding.get("binding_status") == "ready"
        and bool(opt_in_explicit_binding.get("ready"))
        and opt_in_context_budget_policy.get("overall_status") == "ready"
        and bool(opt_in_context_budget_policy.get("ready"))
        and int(opt_in_context_budget_policy.get("max_turns") or 0) == 1
        and opt_in_merge_handoff.get("overall_status") == "ready"
        and bool(opt_in_merge_handoff.get("ready"))
        and opt_in_merge_handoff.get("merge_strategy") == "append_summary"
        and merge_handoff_status == "blocked"
        and not merge_handoff_ready
        and "merge_source" in [str(item) for item in merge_handoff_missing_sections]
        and opt_in_execution.get("execution_status") == "executed"
        and bool(opt_in_execution.get("will_execute"))
    )
    return {
        "ok": ok,
        "contract_version": contract_version,
        "gate_status": gate_status,
        "allowed": bool(gate.get("allowed")),
        "failure_reason": failure_reason if not ok else "",
        "gate_failure_reason": failure_reason,
        "blocker_count": len(blockers),
        "recommended_next_step": recommended_next_step,
        "prerequisites_contract_version": prerequisites_contract_version,
        "prerequisites_status": prerequisites_status,
        "prerequisites_ready": bool(prerequisites.get("ready")),
        "prerequisites_requirement_count": len(requirement_entries),
        "prerequisites_missing_requirement_count": len(missing_requirements),
        "prerequisites_missing_requirements": [str(item) for item in missing_requirements],
        "explicit_executor_binding_status": explicit_binding_status,
        "explicit_executor_binding_ready": explicit_binding_ready,
        "explicit_executor_binding_source": explicit_binding_source,
        "explicit_executor_binding_missing": "explicit_executor_binding_opt_in" in [str(item) for item in missing_requirements],
        "context_budget_policy_status": context_budget_policy_status,
        "context_budget_policy_ready": context_budget_policy_ready,
        "context_budget_policy_source": str(context_budget_policy.get("budget_source") or ""),
        "context_budget_policy_missing_sections": [str(item) for item in context_budget_policy_missing_sections],
        "context_budget_policy_missing": "child_context_budget_defined" in [str(item) for item in missing_requirements],
        "merge_handoff_status": merge_handoff_status,
        "merge_handoff_ready": merge_handoff_ready,
        "merge_handoff_strategy": str(merge_handoff.get("merge_strategy") or ""),
        "merge_handoff_source": str(merge_handoff.get("merge_source") or ""),
        "merge_handoff_missing_sections": [str(item) for item in merge_handoff_missing_sections],
        "merge_handoff_missing": "child_result_merge_semantics_defined" in [str(item) for item in missing_requirements],
        "opt_in_explicit_executor_binding_status": str(
            opt_in_explicit_binding.get("binding_status") or ""
        ),
        "opt_in_explicit_executor_binding_ready": bool(opt_in_explicit_binding.get("ready")),
        "opt_in_explicit_executor_binding_source": str(
            opt_in_explicit_binding.get("binding_source") or ""
        ),
        "opt_in_explicit_executor_binding_backend": str(
            opt_in_explicit_binding.get("selected_backend") or opt_in_explicit_binding.get("backend_id") or ""
        ),
        "opt_in_context_budget_policy_status": str(
            opt_in_context_budget_policy.get("overall_status") or ""
        ),
        "opt_in_context_budget_policy_ready": bool(opt_in_context_budget_policy.get("ready")),
        "opt_in_context_budget_policy_source": str(
            opt_in_context_budget_policy.get("budget_source") or ""
        ),
        "opt_in_context_budget_policy_max_turns": int(
            opt_in_context_budget_policy.get("max_turns") or 0
        ),
        "opt_in_merge_handoff_status": str(opt_in_merge_handoff.get("overall_status") or ""),
        "opt_in_merge_handoff_ready": bool(opt_in_merge_handoff.get("ready")),
        "opt_in_merge_handoff_strategy": str(opt_in_merge_handoff.get("merge_strategy") or ""),
        "opt_in_merge_handoff_source": str(opt_in_merge_handoff.get("merge_source") or ""),
        "opt_in_skeleton_execution_status": str(opt_in_execution.get("execution_status") or ""),
        "opt_in_skeleton_will_execute": bool(opt_in_execution.get("will_execute")),
        "opt_in_skeleton_execution_mode": str(opt_in_execution.get("execution_mode") or ""),
    }


def _run_child_executor_dispatch_contract_check(runtime_profile_payload: dict) -> dict:
    dispatch = dict((runtime_profile_payload or {}).get("child_executor_dispatch_contract") or {})
    handoff = dict(dispatch.get("child_executor_dispatch_attempt_handoff") or {})
    blockers = dispatch.get("blockers") if isinstance(dispatch.get("blockers"), list) else []
    contract_version = str(dispatch.get("contract_version") or "").strip()
    overall_status = str(dispatch.get("overall_status") or "").strip()
    recommended_next_step = str(dispatch.get("recommended_next_step") or "").strip()
    dispatch_ready = bool(dispatch.get("dispatch_ready"))
    will_dispatch = bool(dispatch.get("will_dispatch"))
    backend_dispatch_ready = bool(dispatch.get("backend_dispatch_ready"))
    relationship_seam_preserved = bool(dispatch.get("relationship_seam_preserved"))
    explicit_executor_binding_ready = bool(dispatch.get("explicit_executor_binding_ready"))
    explicit_executor_binding_status = str(dispatch.get("explicit_executor_binding_status") or "").strip()
    explicit_executor_binding_source = str(dispatch.get("explicit_executor_binding_source") or "").strip()

    opt_in_sdk = EmbeddedAgentRuntimeSDK(workspace_store=InMemoryEmbeddedRunWorkspaceStore())
    opt_in_payload = {
        "input": "风险复核子任务",
        "child_context_budget": {"max_turns": 1},
        "merge_strategy": "append_summary",
        "worker_runtime_backend": "embedded_sdk_worker",
        "explicit_executor_binding_opt_in": True,
    }
    opt_in_dispatch = build_child_executor_dispatch_contract(
        gate=opt_in_sdk.evaluate_child_executor_gate(opt_in_payload)
    )
    ready_adapter_contract = build_sandbox_worker_backend_adapter_contract(
        backend_id="sandbox_worker",
        input_contract={"required_fields": ["child_run_id"]},
        output_contract={"required_fields": ["output_ref", "audit_ref"]},
        resource_limits={"cpu_seconds": 30, "memory_mb": 512, "timeout_seconds": 60},
        isolation_guards={
            "process_or_worker_isolation": True,
            "environment_allowlist": ["PYTHONPATH"],
            "workspace_boundary": "run_workspace",
            "network_policy": "disabled_by_default",
        },
        audit_hooks={"record_dispatch": True},
        idempotency={"idempotency_key_required": True},
    )
    sandbox_entry = build_child_executor_sandbox_worker_backend_entry(
        backend_id="sandbox_worker",
        label="Sandbox worker",
        adapter_contract=ready_adapter_contract,
    )
    sandbox_registry = build_child_executor_backend_registry_contract(
        extra_backends=[sandbox_entry]
    )
    sandbox_gate = {
        "allowed": True,
        "gate_status": "allowed",
        "preflight": {
            "worker_runtime_backend": "sandbox_worker",
            "backend_registry": sandbox_registry,
        },
        "child_executor_execution_prerequisites": {
            "ready": True,
            "overall_status": "ready",
            "missing_requirements": [],
            "requirements": [
                {
                    "requirement": "worker_backend_dispatch_ready",
                    "status": "ready",
                    "evidence": sandbox_entry,
                },
                {
                    "requirement": "explicit_executor_binding_opt_in",
                    "status": "ready",
                    "evidence": {
                        "contract_version": "phase-ii-child-executor-explicit-binding-v1",
                        "binding_status": "ready",
                        "ready": True,
                        "binding_source": "smoke.opt_in_sandbox_backend",
                        "selected_backend": "sandbox_worker",
                        "backend_id": "sandbox_worker",
                        "adapter_kind": "sandbox_worker",
                        "missing_requirements": [],
                        "blockers": [],
                        "will_execute": False,
                        "will_dispatch": False,
                    },
                },
            ],
            "explicit_executor_binding": {
                "contract_version": "phase-ii-child-executor-explicit-binding-v1",
                "binding_status": "ready",
                "ready": True,
                "binding_source": "smoke.opt_in_sandbox_backend",
                "selected_backend": "sandbox_worker",
                "backend_id": "sandbox_worker",
                "adapter_kind": "sandbox_worker",
            },
        },
    }
    opt_in_sandbox_dispatch = build_child_executor_dispatch_contract(
        gate=sandbox_gate,
        backend_registry=sandbox_registry,
    )
    opt_in_handoff = dict(
        opt_in_sandbox_dispatch.get("child_executor_dispatch_attempt_handoff") or {}
    )
    unsafe_handoff = build_child_executor_dispatch_attempt_handoff_contract(
        dispatch_contract=opt_in_sandbox_dispatch,
        payload={"child_run_id": "unsafe-child", "handler": object()},
    )
    opt_in_dispatch_ready = bool(opt_in_dispatch.get("dispatch_ready"))
    opt_in_will_dispatch = bool(opt_in_dispatch.get("will_dispatch"))
    opt_in_backend_dispatch_ready = bool(opt_in_dispatch.get("backend_dispatch_ready"))
    opt_in_explicit_binding_ready = bool(opt_in_dispatch.get("explicit_executor_binding_ready"))
    dispatch_handoff_blocked = (
        str(handoff.get("overall_status") or "").strip() == "blocked"
        and not bool(handoff.get("ready"))
        and not bool(handoff.get("will_dispatch"))
        and "dispatch_contract_ready" in [str(item) for item in (handoff.get("missing_sections") or [])]
    )
    opt_in_handoff_ready = (
        str(opt_in_handoff.get("overall_status") or "").strip() == "ready"
        and bool(opt_in_handoff.get("ready"))
        and bool(opt_in_handoff.get("attempt_envelope_supported"))
        and bool(opt_in_handoff.get("attempt_validation_ready"))
        and not bool(opt_in_handoff.get("will_dispatch"))
    )
    unsafe_handoff_guarded = (
        str(unsafe_handoff.get("overall_status") or "").strip() == "blocked"
        and not bool(unsafe_handoff.get("unsafe_payload_guard_ready"))
        and "unsafe_payload_guard" in [str(item) for item in (unsafe_handoff.get("missing_sections") or [])]
        and "handler" in [str(item) for item in (unsafe_handoff.get("unsafe_payload_keys") or [])]
    )
    ok = (
        bool(contract_version)
        and overall_status == "blocked"
        and not dispatch_ready
        and not will_dispatch
        and not backend_dispatch_ready
        and relationship_seam_preserved
        and isinstance(dispatch.get("blockers"), list)
        and "worker_backend_dispatch_ready" in [str(item) for item in blockers]
        and "explicit_executor_binding_opt_in" in [str(item) for item in blockers]
        and not explicit_executor_binding_ready
        and explicit_executor_binding_status == "blocked"
        and opt_in_explicit_binding_ready
        and not opt_in_dispatch_ready
        and not opt_in_will_dispatch
        and not opt_in_backend_dispatch_ready
        and dispatch_handoff_blocked
        and opt_in_handoff_ready
        and unsafe_handoff_guarded
        and bool(recommended_next_step)
    )
    return {
        "ok": ok,
        "contract_version": contract_version,
        "dispatch_status": overall_status,
        "dispatch_ready": dispatch_ready,
        "will_dispatch": will_dispatch,
        "backend_dispatch_ready": backend_dispatch_ready,
        "relationship_seam_preserved": relationship_seam_preserved,
        "dispatch_blocker_count": len(blockers),
        "dispatch_blockers": [str(item) for item in blockers],
        "explicit_executor_binding_ready": explicit_executor_binding_ready,
        "explicit_executor_binding_status": explicit_executor_binding_status,
        "explicit_executor_binding_source": explicit_executor_binding_source,
        "opt_in_dispatch_status": str(opt_in_dispatch.get("overall_status") or ""),
        "opt_in_dispatch_ready": opt_in_dispatch_ready,
        "opt_in_will_dispatch": opt_in_will_dispatch,
        "opt_in_backend_dispatch_ready": opt_in_backend_dispatch_ready,
        "opt_in_explicit_executor_binding_ready": opt_in_explicit_binding_ready,
        "opt_in_explicit_executor_binding_status": str(
            opt_in_dispatch.get("explicit_executor_binding_status") or ""
        ),
        "opt_in_explicit_executor_binding_source": str(
            opt_in_dispatch.get("explicit_executor_binding_source") or ""
        ),
        "dispatch_attempt_handoff_status": str(handoff.get("overall_status") or ""),
        "dispatch_attempt_handoff_ready": bool(handoff.get("ready")),
        "dispatch_attempt_handoff_missing_sections": [
            str(item) for item in (handoff.get("missing_sections") or [])
        ],
        "dispatch_attempt_handoff_will_dispatch": bool(handoff.get("will_dispatch")),
        "opt_in_dispatch_attempt_handoff_status": str(opt_in_handoff.get("overall_status") or ""),
        "opt_in_dispatch_attempt_handoff_ready": bool(opt_in_handoff.get("ready")),
        "opt_in_attempt_envelope_supported": bool(
            opt_in_handoff.get("attempt_envelope_supported")
        ),
        "opt_in_attempt_validation_ready": bool(opt_in_handoff.get("attempt_validation_ready")),
        "opt_in_attempt_will_dispatch": bool(opt_in_handoff.get("will_dispatch")),
        "opt_in_unsafe_payload_guard_ready": bool(
            opt_in_handoff.get("unsafe_payload_guard_ready")
        ),
        "unsafe_payload_guard_status": str(unsafe_handoff.get("overall_status") or ""),
        "unsafe_payload_guard_ready": bool(unsafe_handoff.get("unsafe_payload_guard_ready")),
        "unsafe_payload_keys": [str(item) for item in (unsafe_handoff.get("unsafe_payload_keys") or [])],
        "recommended_next_step": recommended_next_step,
        "failure_reason": "" if ok else "child_executor_dispatch_contract_incomplete",
    }


def _run_child_executor_dispatcher_contract_check() -> dict:
    ready_contract = {
        "contract_version": "phase-ii-child-executor-dispatch-v1",
        "overall_status": "ready",
        "dispatch_ready": True,
        "will_dispatch": False,
        "backend_id": "smoke_worker",
        "backend_status": "ready",
        "backend_dispatch_ready": True,
        "gate_allowed": True,
        "prerequisites_ready": True,
        "blockers": [],
    }
    blocked_contract = {
        **ready_contract,
        "overall_status": "blocked",
        "dispatch_ready": False,
        "blockers": ["worker_backend_dispatch_ready"],
    }

    invoked: list[dict] = []

    def _adapter(payload):
        invoked.append(dict(payload or {}))
        return {
            "status": "completed",
            "child_run_id": str((payload or {}).get("child_run_id") or ""),
            "summary": "smoke child completed",
            "output_ref": "artifact://smoke-child/output",
        }

    default_attempt = ChildExecutorDispatcher(
        backend_adapters={"smoke_worker": _adapter}
    ).dispatch(
        dispatch_contract=ready_contract,
        payload={"parent_run_id": "parent-smoke", "child_run_id": "child-smoke"},
    )
    blocked_attempt = ChildExecutorDispatcher(
        enabled=True,
        backend_adapters={"smoke_worker": _adapter},
    ).dispatch(
        dispatch_contract=blocked_contract,
        payload={"parent_run_id": "parent-smoke", "child_run_id": "child-smoke"},
    )
    dispatched_attempt = ChildExecutorDispatcher(
        enabled=True,
        backend_adapters={"smoke_worker": _adapter},
    ).dispatch(
        dispatch_contract=ready_contract,
        payload={"parent_run_id": "parent-smoke", "child_run_id": "child-smoke"},
    )
    ok = (
        str(default_attempt.get("contract_version") or "").strip() == "phase-ii-child-executor-dispatcher-v1"
        and str(default_attempt.get("dispatch_status") or "").strip() == "blocked"
        and str(default_attempt.get("blocked_reason") or "").strip() == "dispatcher_disabled"
        and not bool(default_attempt.get("will_dispatch"))
        and str(blocked_attempt.get("blocked_reason") or "").strip() == "dispatch_contract_not_ready"
        and not bool(blocked_attempt.get("will_dispatch"))
        and str(dispatched_attempt.get("dispatch_status") or "").strip() == "dispatched"
        and bool(dispatched_attempt.get("will_dispatch"))
        and str((dispatched_attempt.get("backend_result") or {}).get("child_run_id") or "").strip() == "child-smoke"
        and len(invoked) == 1
    )
    return {
        "ok": ok,
        "contract_version": str(default_attempt.get("contract_version") or ""),
        "default_status": str(default_attempt.get("dispatch_status") or ""),
        "default_blocked_reason": str(default_attempt.get("blocked_reason") or ""),
        "default_will_dispatch": bool(default_attempt.get("will_dispatch")),
        "blocked_reason": str(blocked_attempt.get("blocked_reason") or ""),
        "blocked_will_dispatch": bool(blocked_attempt.get("will_dispatch")),
        "enabled_status": str(dispatched_attempt.get("dispatch_status") or ""),
        "enabled_will_dispatch": bool(dispatched_attempt.get("will_dispatch")),
        "backend_result_status": str((dispatched_attempt.get("backend_result") or {}).get("status") or ""),
        "backend_invocation_count": len(invoked),
        "failure_reason": "" if ok else "child_executor_dispatcher_incomplete",
    }


def _run_child_executor_dispatch_result_handoff_contract_check() -> dict:
    ready_contract = {
        "contract_version": "phase-ii-child-executor-dispatch-v1",
        "overall_status": "ready",
        "dispatch_ready": True,
        "will_dispatch": False,
        "backend_id": "sandbox_worker",
        "backend_adapter_kind": "sandbox_worker",
        "backend_status": "ready",
        "backend_dispatch_ready": True,
        "gate_allowed": True,
        "prerequisites_ready": True,
        "blockers": [],
    }

    def _sandbox_adapter(payload):
        return build_sandbox_dispatch_attempt_envelope(
            attempt_id="result-handoff-smoke-attempt",
            backend_id="sandbox_worker",
            child_run_id=str((payload or {}).get("child_run_id") or ""),
            status="completed",
            will_dispatch=True,
            sandbox_ref="sandbox://result-handoff-smoke-attempt",
            output_ref="artifact://result-handoff-child/output",
            audit_ref="trace://result-handoff-smoke-attempt",
        )

    ready_attempt = ChildExecutorDispatcher(
        enabled=True,
        backend_adapters={"sandbox_worker": _sandbox_adapter},
    ).dispatch(
        dispatch_contract=ready_contract,
        payload={"parent_run_id": "parent-smoke", "child_run_id": "result-handoff-child"},
    )
    blocked_attempt = ChildExecutorDispatcher(
        enabled=False,
        backend_adapters={"sandbox_worker": _sandbox_adapter},
    ).dispatch(
        dispatch_contract=ready_contract,
        payload={"parent_run_id": "parent-smoke", "child_run_id": "blocked-child"},
    )
    malformed_handoff = build_child_executor_dispatch_result_handoff_contract(
        dispatch_attempt={
            "dispatch_status": "dispatched",
            "dispatched": True,
            "will_dispatch": True,
            "backend_id": "sandbox_worker",
            "backend_result": {
                "status": "completed",
                "child_run_id": "malformed-child",
            },
            "audit": {},
        }
    )
    ready_handoff = dict(ready_attempt.get("dispatch_result_handoff") or {})
    blocked_handoff = dict(blocked_attempt.get("dispatch_result_handoff") or {})
    ready_missing_sections = [str(item) for item in (ready_handoff.get("missing_sections") or [])]
    blocked_missing_sections = [str(item) for item in (blocked_handoff.get("missing_sections") or [])]
    malformed_missing_sections = [
        str(item) for item in (malformed_handoff.get("missing_sections") or [])
    ]
    ready_handoff_ok = (
        str(ready_handoff.get("contract_version") or "").strip()
        == "phase-ii-child-executor-dispatch-result-handoff-v1"
        and str(ready_handoff.get("overall_status") or "").strip() == "ready"
        and bool(ready_handoff.get("ready"))
        and str(ready_handoff.get("child_run_id") or "").strip() == "result-handoff-child"
        and bool(ready_handoff.get("output_ref_present"))
        and bool(ready_handoff.get("audit_evidence_present"))
        and bool(ready_handoff.get("backend_result_schema_valid"))
        and not bool(ready_handoff.get("parent_merge_performed"))
        and not bool(ready_handoff.get("merge_authorization"))
        and not bool(ready_handoff.get("retry_scheduled"))
        and not bool(ready_handoff.get("production_dispatch_authorized"))
        and not ready_missing_sections
    )
    blocked_handoff_ok = (
        str(blocked_handoff.get("overall_status") or "").strip() == "blocked"
        and not bool(blocked_handoff.get("ready"))
        and str(blocked_handoff.get("dispatcher_blocked_reason") or "").strip()
        == "dispatcher_disabled"
        and "dispatch_success" in blocked_missing_sections
        and not bool(blocked_handoff.get("parent_merge_performed"))
    )
    malformed_handoff_ok = (
        str(malformed_handoff.get("overall_status") or "").strip() == "blocked"
        and not bool(malformed_handoff.get("ready"))
        and "output_ref" in malformed_missing_sections
        and "audit_evidence" in malformed_missing_sections
        and not bool(malformed_handoff.get("merge_authorization"))
    )
    ok = ready_handoff_ok and blocked_handoff_ok and malformed_handoff_ok
    return {
        "ok": ok,
        "contract_version": str(ready_handoff.get("contract_version") or ""),
        "ready_handoff_status": str(ready_handoff.get("overall_status") or ""),
        "ready_handoff_ready": bool(ready_handoff.get("ready")),
        "ready_output_ref_present": bool(ready_handoff.get("output_ref_present")),
        "ready_audit_evidence_present": bool(ready_handoff.get("audit_evidence_present")),
        "ready_backend_result_schema_valid": bool(
            ready_handoff.get("backend_result_schema_valid")
        ),
        "ready_parent_merge_performed": bool(ready_handoff.get("parent_merge_performed")),
        "ready_merge_authorization": bool(ready_handoff.get("merge_authorization")),
        "ready_retry_scheduled": bool(ready_handoff.get("retry_scheduled")),
        "ready_production_dispatch_authorized": bool(
            ready_handoff.get("production_dispatch_authorized")
        ),
        "blocked_handoff_status": str(blocked_handoff.get("overall_status") or ""),
        "blocked_dispatcher_reason": str(
            blocked_handoff.get("dispatcher_blocked_reason") or ""
        ),
        "blocked_missing_sections": blocked_missing_sections,
        "malformed_handoff_status": str(malformed_handoff.get("overall_status") or ""),
        "malformed_missing_sections": malformed_missing_sections,
        "failure_reason": "" if ok else "child_executor_dispatch_result_handoff_incomplete",
    }


def _run_child_executor_dispatch_result_retry_audit_policy_contract_check() -> dict:
    success_policy = build_child_executor_dispatch_result_retry_audit_policy_contract(
        result_handoff={
            "overall_status": "ready",
            "ready": True,
            "dispatch_status": "dispatched",
            "backend_result_status": "completed",
            "retryable": False,
            "audit_evidence_present": True,
            "idempotency_key": "child-dispatch:success",
        }
    )
    retryable_policy = build_child_executor_dispatch_result_retry_audit_policy_contract(
        result_handoff={
            "overall_status": "blocked",
            "ready": False,
            "dispatch_status": "dispatched",
            "backend_result_status": "failed",
            "backend_result_error_code": "sandbox_timeout",
            "retryable": True,
            "audit_evidence_present": True,
            "idempotency_key": "child-dispatch:retryable",
            "missing_sections": ["backend_result"],
        }
    )
    terminal_policy = build_child_executor_dispatch_result_retry_audit_policy_contract(
        result_handoff={
            "overall_status": "blocked",
            "ready": False,
            "dispatch_status": "blocked",
            "dispatcher_blocked_reason": "sandbox_payload_unsafe",
            "retryable": False,
            "audit_evidence_present": True,
            "idempotency_key": "child-dispatch:terminal",
        }
    )
    missing_idempotency_policy = build_child_executor_dispatch_result_retry_audit_policy_contract(
        result_handoff={
            "overall_status": "blocked",
            "ready": False,
            "dispatch_status": "dispatched",
            "backend_result_status": "failed",
            "backend_result_error_code": "sandbox_timeout",
            "retryable": True,
            "audit_evidence_present": True,
            "idempotency_key": "",
        }
    )
    success_ok = (
        str(success_policy.get("contract_version") or "").strip()
        == "phase-ii-child-executor-dispatch-result-retry-audit-policy-v1"
        and str(success_policy.get("overall_status") or "").strip() == "ready"
        and str(success_policy.get("retry_policy_status") or "").strip() == "not_required"
        and not bool(success_policy.get("retry_scheduled"))
        and not bool(success_policy.get("will_retry"))
    )
    retryable_ok = (
        str(retryable_policy.get("overall_status") or "").strip() == "ready"
        and str(retryable_policy.get("retry_policy_status") or "").strip() == "retryable"
        and bool(retryable_policy.get("retryable"))
        and bool(retryable_policy.get("audit_evidence_present"))
        and bool(retryable_policy.get("idempotency_evidence_present"))
        and bool(retryable_policy.get("scheduler_required"))
        and str(retryable_policy.get("retry_reason") or "").strip() == "sandbox_timeout"
        and not bool(retryable_policy.get("retry_scheduled"))
        and not bool(retryable_policy.get("will_retry"))
    )
    terminal_ok = (
        str(terminal_policy.get("overall_status") or "").strip() == "ready"
        and str(terminal_policy.get("retry_policy_status") or "").strip() == "terminal"
        and bool(terminal_policy.get("terminal"))
        and str(terminal_policy.get("dispatcher_blocked_reason") or "").strip()
        == "sandbox_payload_unsafe"
        and not bool(terminal_policy.get("will_retry"))
    )
    missing_idempotency_ok = (
        str(missing_idempotency_policy.get("overall_status") or "").strip() == "blocked"
        and str(missing_idempotency_policy.get("retry_policy_status") or "").strip()
        == "retryable"
        and "idempotency_evidence"
        in [str(item) for item in (missing_idempotency_policy.get("missing_sections") or [])]
        and not bool(missing_idempotency_policy.get("retry_scheduled"))
    )
    ok = success_ok and retryable_ok and terminal_ok and missing_idempotency_ok
    return {
        "ok": ok,
        "contract_version": str(success_policy.get("contract_version") or ""),
        "success_policy_status": str(success_policy.get("overall_status") or ""),
        "success_retry_policy_status": str(success_policy.get("retry_policy_status") or ""),
        "success_retry_scheduled": bool(success_policy.get("retry_scheduled")),
        "success_will_retry": bool(success_policy.get("will_retry")),
        "retryable_policy_status": str(retryable_policy.get("overall_status") or ""),
        "retryable_retry_policy_status": str(retryable_policy.get("retry_policy_status") or ""),
        "retryable_audit_evidence_present": bool(
            retryable_policy.get("audit_evidence_present")
        ),
        "retryable_idempotency_evidence_present": bool(
            retryable_policy.get("idempotency_evidence_present")
        ),
        "retryable_scheduler_required": bool(retryable_policy.get("scheduler_required")),
        "retryable_retry_reason": str(retryable_policy.get("retry_reason") or ""),
        "retryable_retry_scheduled": bool(retryable_policy.get("retry_scheduled")),
        "retryable_will_retry": bool(retryable_policy.get("will_retry")),
        "terminal_policy_status": str(terminal_policy.get("overall_status") or ""),
        "terminal_retry_policy_status": str(terminal_policy.get("retry_policy_status") or ""),
        "terminal_reason": str(terminal_policy.get("dispatcher_blocked_reason") or ""),
        "terminal_will_retry": bool(terminal_policy.get("will_retry")),
        "missing_idempotency_status": str(missing_idempotency_policy.get("overall_status") or ""),
        "missing_idempotency_missing_sections": [
            str(item) for item in (missing_idempotency_policy.get("missing_sections") or [])
        ],
        "missing_idempotency_retry_scheduled": bool(
            missing_idempotency_policy.get("retry_scheduled")
        ),
        "failure_reason": "" if ok else "child_executor_dispatch_result_retry_audit_incomplete",
    }


def _run_child_executor_sandbox_backend_contract_check() -> dict:
    ready_adapter_contract = build_sandbox_worker_backend_adapter_contract(
        backend_id="sandbox_worker",
        input_contract={"required_fields": ["child_run_id"]},
        output_contract={"required_fields": ["output_ref", "audit_ref"]},
        resource_limits={"cpu_seconds": 30, "memory_mb": 512, "timeout_seconds": 60},
        isolation_guards={
            "process_or_worker_isolation": True,
            "environment_allowlist": ["PYTHONPATH"],
            "workspace_boundary": "run_workspace",
            "network_policy": "disabled_by_default",
        },
        audit_hooks={"record_dispatch": True},
        idempotency={"idempotency_key_required": True},
    )
    incomplete_adapter_contract = build_sandbox_worker_backend_adapter_contract(
        backend_id="sandbox_worker",
        input_contract={"required_fields": ["child_run_id"]},
        output_contract={"required_fields": ["output_ref"]},
    )
    ready_contract = {
        "contract_version": "phase-ii-child-executor-dispatch-v1",
        "overall_status": "ready",
        "dispatch_ready": True,
        "will_dispatch": False,
        "backend_id": "sandbox_worker",
        "backend_adapter_kind": "sandbox_worker",
        "backend_status": "ready",
        "backend_dispatch_ready": True,
        "gate_allowed": True,
        "prerequisites_ready": True,
        "blockers": [],
    }
    invoked: list[dict] = []

    def _sandbox_adapter(payload):
        invoked.append(dict(payload or {}))
        return build_sandbox_dispatch_attempt_envelope(
            attempt_id="sandbox-smoke-attempt",
            backend_id="sandbox_worker",
            child_run_id=str((payload or {}).get("child_run_id") or ""),
            status="completed",
            will_dispatch=True,
            sandbox_ref="sandbox://sandbox-smoke-attempt",
            output_ref="artifact://sandbox-smoke-child/output",
            audit_ref="trace://sandbox-smoke-attempt",
        )

    dispatched_attempt = ChildExecutorDispatcher(
        enabled=True,
        backend_adapters={"sandbox_worker": _sandbox_adapter},
    ).dispatch(
        dispatch_contract=ready_contract,
        payload={"parent_run_id": "parent-smoke", "child_run_id": "child-smoke"},
    )
    unsafe_attempt = ChildExecutorDispatcher(
        enabled=True,
        backend_adapters={"sandbox_worker": _sandbox_adapter},
    ).dispatch(
        dispatch_contract=ready_contract,
        payload={"parent_run_id": "parent-smoke", "child_run_id": "unsafe-child", "handler": object()},
    )
    backend_result = dict(dispatched_attempt.get("backend_result") or {})
    missing_guards = [
        str(item)
        for item in (incomplete_adapter_contract.get("missing_guards") or [])
        if str(item or "").strip()
    ]
    ready_contract_status = bool(ready_adapter_contract.get("adapter_contract_ready"))
    missing_guard_fail_closed = (
        not bool(incomplete_adapter_contract.get("adapter_contract_ready"))
        and not bool(incomplete_adapter_contract.get("sandbox_guard_ready"))
        and "isolation" in missing_guards
    )
    unsafe_payload_blocked = (
        str(unsafe_attempt.get("dispatch_status") or "").strip() == "blocked"
        and str(unsafe_attempt.get("blocked_reason") or "").strip() == "sandbox_payload_unsafe"
        and str(unsafe_attempt.get("error_code") or "").strip() == "unsafe_payload"
    )
    compact_attempt_valid = (
        str(dispatched_attempt.get("dispatch_status") or "").strip() == "dispatched"
        and bool(dispatched_attempt.get("will_dispatch"))
        and str(backend_result.get("status") or "").strip() == "completed"
        and str(backend_result.get("sandbox_ref") or "").startswith("sandbox://")
        and str(backend_result.get("output_ref") or "").startswith("artifact://")
        and str(backend_result.get("audit_ref") or "").startswith("trace://")
    )
    ok = (
        str(ready_adapter_contract.get("contract_version") or "").strip()
        == "phase-ii-child-executor-sandbox-worker-backend-v1"
        and ready_contract_status
        and bool(ready_adapter_contract.get("sandbox_guard_ready"))
        and bool(ready_adapter_contract.get("audit_ready"))
        and bool(ready_adapter_contract.get("idempotency_ready"))
        and missing_guard_fail_closed
        and unsafe_payload_blocked
        and compact_attempt_valid
        and len(invoked) == 1
    )
    return {
        "ok": ok,
        "contract_version": str(ready_adapter_contract.get("contract_version") or ""),
        "ready_adapter_contract": ready_contract_status,
        "ready_sandbox_guard": bool(ready_adapter_contract.get("sandbox_guard_ready")),
        "ready_audit": bool(ready_adapter_contract.get("audit_ready")),
        "ready_idempotency": bool(ready_adapter_contract.get("idempotency_ready")),
        "missing_guard_fail_closed": missing_guard_fail_closed,
        "missing_guard_count": len(missing_guards),
        "unsafe_payload_blocked": unsafe_payload_blocked,
        "unsafe_blocked_reason": str(unsafe_attempt.get("blocked_reason") or ""),
        "compact_attempt_valid": compact_attempt_valid,
        "dispatch_status": str(dispatched_attempt.get("dispatch_status") or ""),
        "backend_result_status": str(backend_result.get("status") or ""),
        "backend_invocation_count": len(invoked),
        "default_worker_enabled": False,
        "failure_reason": "" if ok else "child_executor_sandbox_backend_incomplete",
    }


def _restore_local_fake_adapter_module_flags(previous_flags: dict[str, dict[str, object]]) -> None:
    for module_name, module_flags in previous_flags.items():
        module = sys.modules.get(module_name)
        if module is None:
            continue
        for attr_name, previous_value in module_flags.items():
            if hasattr(module, attr_name):
                setattr(module, attr_name, previous_value)


def _build_embedded_sdk_event_sample() -> list[dict]:
    sdk = EmbeddedAgentRuntimeSDK(continuation_registry=InMemoryEmbeddedContinuationRegistry())
    direct_run = sdk.create_run({"run_kind": "chat"})
    sdk.execute_run(direct_run["run"]["run_id"])

    approval_run = sdk.create_run({"run_kind": "chat"})
    executed = sdk.execute_run(
        approval_run["run"]["run_id"],
        tool_policy=lambda _run: {
            "status": "approval_required",
            "tool_name": "filesystem_write",
            "tool_args": {"path": "smoke.md"},
            "reason": "Smoke check validates approval event payloads.",
        },
        tool_executor=lambda _run: {
            "tool_name": "filesystem_write",
            "args": {"path": "smoke.md"},
            "result": "ok",
        },
    )
    sdk.submit_approval(executed["approval_request"]["request_id"], "approved")
    sdk.submit_approval(executed["approval_request"]["request_id"], "approved")
    sdk.resume_run(approval_run["run"]["run_id"], continue_loop=True)

    discarded_run = sdk.create_run({"run_kind": "chat"})
    discarded = sdk.execute_run(
        discarded_run["run"]["run_id"],
        tool_policy=lambda _run: {
            "status": "approval_required",
            "tool_name": "filesystem_write",
            "tool_args": {"path": "smoke-denied.md"},
            "reason": "Smoke check validates discarded continuation payloads.",
        },
        tool_executor=lambda _run: {
            "tool_name": "filesystem_write",
            "args": {"path": "smoke-denied.md"},
            "result": "should not run",
        },
    )
    sdk.submit_approval(discarded["approval_request"]["request_id"], "denied")
    sdk.submit_approval(discarded["approval_request"]["request_id"], "approved")

    return [
        *sdk.stream_events(direct_run["run"]["run_id"]),
        *sdk.stream_events(approval_run["run"]["run_id"]),
        *sdk.stream_events(discarded_run["run"]["run_id"]),
    ]


def _run_approval_lifecycle_recovery_alignment_check() -> dict:
    sdk = EmbeddedAgentRuntimeSDK(continuation_registry=InMemoryEmbeddedContinuationRegistry())
    approved_run = sdk.create_run({"run_kind": "chat"})
    approved_execution = sdk.execute_run(
        approved_run["run"]["run_id"],
        tool_policy=lambda _run: {
            "status": "approval_required",
            "tool_name": "filesystem_write",
            "tool_args": {"path": "smoke-approved.md"},
            "reason": "Smoke validates replayed approval lifecycle.",
        },
        tool_executor=lambda _run: {
            "tool_name": "filesystem_write",
            "args": {"path": "smoke-approved.md"},
            "result": "ok",
        },
    )
    sdk.submit_approval(approved_execution["approval_request"]["request_id"], "approved")
    replayed = sdk.submit_approval(approved_execution["approval_request"]["request_id"], "approved")

    denied_run = sdk.create_run({"run_kind": "chat"})
    denied_execution = sdk.execute_run(
        denied_run["run"]["run_id"],
        tool_policy=lambda _run: {
            "status": "approval_required",
            "tool_name": "filesystem_write",
            "tool_args": {"path": "smoke-denied-alignment.md"},
            "reason": "Smoke validates ignored approval lifecycle.",
        },
        tool_executor=lambda _run: {
            "tool_name": "filesystem_write",
            "args": {"path": "smoke-denied-alignment.md"},
            "result": "should not run",
        },
    )
    sdk.submit_approval(denied_execution["approval_request"]["request_id"], "denied")
    ignored = sdk.submit_approval(denied_execution["approval_request"]["request_id"], "approved")
    probe = sdk.probe_run_recovery(denied_run["run"]["run_id"])
    entrypoints = {
        (item.get("method"), item.get("mode") or ""): item
        for item in probe.get("recovery_entrypoints") or []
    }
    resolved_entrypoint = entrypoints.get(("submit_approval", "approved"), {})
    replayed_status = str((replayed.get("approval_submission") or {}).get("status") or "").strip()
    ignored_status = str((ignored.get("approval_submission") or {}).get("status") or "").strip()
    recovery_reason = str(resolved_entrypoint.get("recovery_reason") or "").strip()
    approval_status = str(((probe.get("approval_request") or {}).get("status")) or "").strip()
    ok = (
        replayed_status == "replayed"
        and ignored_status == "ignored"
        and recovery_reason == "already_resolved"
        and approval_status == "denied"
        and not bool(resolved_entrypoint.get("available"))
    )
    return {
        "ok": ok,
        "replayed_submission_status": replayed_status,
        "ignored_submission_status": ignored_status,
        "resolved_recovery_reason": recovery_reason,
        "resolved_approval_status": approval_status,
        "resolved_entrypoint_available": bool(resolved_entrypoint.get("available")),
        "failure_reason": "" if ok else "approval_lifecycle_recovery_alignment_incomplete",
    }


def _run_runtime_approved_tool_execution_bridge_check() -> dict:
    class _RuntimeTool:
        def __init__(self, name: str, result_prefix: str):
            self.name = name
            self.description = f"{name} smoke tool"
            self.parameters = {"path": {"type": "string", "required": True}}
            self.calls: list[dict] = []
            self.result_prefix = result_prefix

        def invoke(self, args):
            self.calls.append(dict(args))
            return f"{self.result_prefix}:{args['path']}"

    class _RuntimeRegistry(ToolRegistry):
        def __init__(self):
            super().__init__()
            self.ask_tool = _RuntimeTool("smoke_filesystem_write", "written")
            self.deny_tool = _RuntimeTool("smoke_dangerous_delete", "deleted")

        def list_all(self):
            return [self.ask_tool, self.deny_tool]

        def get(self, name):
            if name == self.ask_tool.name:
                return self.ask_tool
            if name == self.deny_tool.name:
                return self.deny_tool
            return None

    registry = _RuntimeRegistry()
    registry.register_tool_spec(
        ToolSpec(
            name="smoke_filesystem_write",
            description="Smoke write tool",
            permission_level="ask",
            deterministic=False,
            tags=("filesystem", "write"),
        )
    )
    registry.register_tool_spec(
        ToolSpec(
            name="smoke_dangerous_delete",
            description="Smoke delete tool",
            permission_level="deny",
            deterministic=False,
            tags=("filesystem", "delete"),
        )
    )
    tool_runtime_service = ToolRuntimeService(
        tool_registry=registry,
        mcp_registry_service=_EmptyMcpRegistryService(),
        framework_adapter_registry=_EmptyFrameworkAdapterRegistry(),
    )
    agent = create_agent(
        name="runtime_smoke_agent",
        model_name="doubao",
        sdk=EmbeddedAgentRuntimeSDK(),
        tool_runtime_service=tool_runtime_service,
    )
    run = agent.run("smoke approved runtime tool execution")
    executed = agent.execute(
        run["run"]["run_id"],
        tool_policy=lambda _run: {
            "status": "allowed",
            "tool_name": "smoke_filesystem_write",
            "tool_args": {"path": "smoke.md"},
        },
    )
    approval = dict(executed.get("approval_request") or {})
    approved = agent.approve(str(approval.get("request_id") or ""), "approved")
    tool_history = list((approved.get("run") or {}).get("tool_history") or [])
    policy_decision = dict(((tool_history[0] if tool_history else {}).get("execution") or {}).get("policy_decision") or {})
    override = dict(policy_decision.get("override") or {})
    deny_override = tool_runtime_service.execute_tool(
        "smoke_dangerous_delete",
        {"path": "smoke.md"},
        execution_options={
            "policy_override": {
                "status": "approved",
                "approval_request_id": "smoke-approval",
                "source": "runtime_contract_smoke",
            }
        },
    )
    ok = (
        str(approval.get("status") or "").strip() == "pending"
        and len(registry.ask_tool.calls) == 1
        and str(policy_decision.get("status") or "").strip() == "allowed"
        and str(policy_decision.get("original_status") or "").strip() == "approval_required"
        and str(override.get("status") or "").strip() == "approved"
        and str(deny_override.get("status") or "").strip() == "policy_denied"
        and len(registry.deny_tool.calls) == 0
    )
    return {
        "ok": ok,
        "ask_approval_status": approval.get("status"),
        "approved_tool_call_count": len(registry.ask_tool.calls),
        "approved_policy_status": policy_decision.get("status"),
        "approved_policy_original_status": policy_decision.get("original_status"),
        "approved_policy_override_status": override.get("status"),
        "deny_override_status": deny_override.get("status"),
        "deny_tool_call_count": len(registry.deny_tool.calls),
        "failure_reason": "" if ok else "runtime_approved_tool_execution_bridge_incomplete",
    }


def _run_sdk_tool_runtime_execution_bridge_check() -> dict:
    tool_runtime_service = ToolRuntimeService(
        tool_registry=ToolRegistry(),
        mcp_registry_service=_EmptyMcpRegistryService(),
        framework_adapter_registry=_EmptyFrameworkAdapterRegistry(),
    )
    sdk = EmbeddedAgentRuntimeSDK(tool_runtime_service=tool_runtime_service)
    auto_calls: list[dict] = []
    approved_calls: list[dict] = []
    deny_calls: list[dict] = []
    sdk.register_tool(
        ToolSpec(
            name="sdk_smoke_risk_lookup",
            description="SDK smoke auto tool",
            permission_level="auto",
            deterministic=True,
            tags=("sdk", "smoke"),
        ),
        handler=lambda args: auto_calls.append(dict(args)) or f"risk:{args['case_id']}",
        parameters={"case_id": {"type": "string", "required": True}},
    )
    sdk.register_tool(
        ToolSpec(
            name="sdk_smoke_filesystem_write",
            description="SDK smoke approval tool",
            permission_level="ask",
            deterministic=False,
            tags=("sdk", "filesystem"),
        ),
        handler=lambda args: approved_calls.append(dict(args)) or f"written:{args['path']}",
        parameters={"path": {"type": "string", "required": True}},
    )
    sdk.register_tool(
        ToolSpec(
            name="sdk_smoke_dangerous_delete",
            description="SDK smoke deny tool",
            permission_level="deny",
            deterministic=False,
            tags=("sdk", "filesystem"),
        ),
        handler=lambda args: deny_calls.append(dict(args)) or f"deleted:{args['path']}",
        parameters={"path": {"type": "string", "required": True}},
    )

    auto_run = sdk.create_run({"run_kind": "chat"})
    auto_executed = sdk.execute_run(
        auto_run["run"]["run_id"],
        tool_policy=lambda _run: {
            "status": "allowed",
            "tool_name": "sdk_smoke_risk_lookup",
            "tool_args": {"case_id": "case-1"},
        },
    )
    auto_history = list((auto_executed.get("run") or {}).get("tool_history") or [])

    approval_run = sdk.create_run({"run_kind": "chat"})
    waiting = sdk.execute_run(
        approval_run["run"]["run_id"],
        tool_policy=lambda _run: {
            "status": "allowed",
            "tool_name": "sdk_smoke_filesystem_write",
            "tool_args": {"path": "smoke.md"},
        },
    )
    approval = dict(waiting.get("approval_request") or {})
    approved = sdk.submit_approval(str(approval.get("request_id") or ""), "approved")
    approved_history = list((approved.get("run") or {}).get("tool_history") or [])
    approved_policy_decision = dict(
        ((approved_history[0] if approved_history else {}).get("execution") or {}).get("policy_decision") or {}
    )
    approved_override = dict(approved_policy_decision.get("override") or {})

    deny_run = sdk.create_run({"run_kind": "chat"})
    denied = sdk.execute_run(
        deny_run["run"]["run_id"],
        tool_policy=lambda _run: {
            "status": "allowed",
            "tool_name": "sdk_smoke_dangerous_delete",
            "tool_args": {"path": "smoke.md"},
        },
    )
    deny_decision = dict(((denied.get("run") or {}).get("metadata") or {}).get("execution_tool_decision") or {})
    deny_policy_decision = dict((deny_decision.get("metadata") or {}).get("tool_runtime_policy_decision") or {})

    ok = (
        len(auto_calls) == 1
        and len(auto_history) == 1
        and str(((auto_history[0] if auto_history else {}).get("execution") or {}).get("executor") or "") == "tool_runtime_service"
        and str(approval.get("status") or "").strip() == "pending"
        and len(approved_calls) == 1
        and str(approved_policy_decision.get("status") or "").strip() == "allowed"
        and str(approved_policy_decision.get("original_status") or "").strip() == "approval_required"
        and str(approved_override.get("status") or "").strip() == "approved"
        and str(deny_policy_decision.get("reason_code") or "").strip() == "permission_level_denied"
        and len(deny_calls) == 0
    )
    return {
        "ok": ok,
        "auto_tool_call_count": len(auto_calls),
        "auto_tool_history_count": len(auto_history),
        "ask_approval_status": approval.get("status"),
        "approved_tool_call_count": len(approved_calls),
        "approved_policy_status": approved_policy_decision.get("status"),
        "approved_policy_original_status": approved_policy_decision.get("original_status"),
        "approved_policy_override_status": approved_override.get("status"),
        "deny_override_status": "policy_denied" if str(deny_policy_decision.get("reason_code") or "").strip() == "permission_level_denied" else deny_policy_decision.get("status"),
        "deny_tool_call_count": len(deny_calls),
        "failure_reason": "" if ok else "sdk_tool_runtime_execution_bridge_incomplete",
    }


def _run_tool_runtime_timeout_retry_contract_check() -> dict:
    class _FlakyTool:
        name = "smoke_flaky_lookup"
        description = "Smoke flaky lookup"
        parameters = {}

        def __init__(self, fail_times: int):
            self.fail_times = fail_times
            self.calls = 0

        def invoke(self, args):
            self.calls += 1
            if self.calls <= self.fail_times:
                raise RuntimeError(f"temporary failure {self.calls}")
            return f"recovered:{args.get('case_id', 'unknown')}"

    class _SlowTool:
        name = "smoke_slow_lookup"
        description = "Smoke slow lookup"
        parameters = {}

        def __init__(self):
            self.calls = 0

        def invoke(self, _args):
            self.calls += 1
            time.sleep(0.02)
            return "slow result"

    class _SingleToolRegistry:
        def __init__(self, tool):
            self.tool = tool

        def list_all(self):
            return [self.tool]

        def get(self, name):
            return self.tool if name == self.tool.name else None

        def get_langchain_tools(self):
            return []

        def list_tool_specs(self):
            return []

        def get_doubao_tool_definitions(self):
            return []

    recovered_tool = _FlakyTool(fail_times=1)
    recovered_service = ToolRuntimeService(
        tool_registry=_SingleToolRegistry(recovered_tool),
        mcp_registry_service=_EmptyMcpRegistryService(),
        framework_adapter_registry=_EmptyFrameworkAdapterRegistry(),
    )
    contract = recovered_service.build_runtime_contract()
    execution_adapter = dict(contract.get("execution_adapter") or {})
    recovered = recovered_service.execute_tool(
        "smoke_flaky_lookup",
        {"case_id": "case-1"},
        execution_options={"max_attempts": 2},
    )

    exhausted_tool = _FlakyTool(fail_times=3)
    exhausted_service = ToolRuntimeService(
        tool_registry=_SingleToolRegistry(exhausted_tool),
        mcp_registry_service=_EmptyMcpRegistryService(),
        framework_adapter_registry=_EmptyFrameworkAdapterRegistry(),
    )
    exhausted = exhausted_service.execute_tool(
        "smoke_flaky_lookup",
        {"case_id": "case-1"},
        execution_options={"max_attempts": 2},
    )

    slow_tool = _SlowTool()
    timeout_service = ToolRuntimeService(
        tool_registry=_SingleToolRegistry(slow_tool),
        mcp_registry_service=_EmptyMcpRegistryService(),
        framework_adapter_registry=_EmptyFrameworkAdapterRegistry(),
    )
    timed_out = timeout_service.execute_tool(
        "smoke_slow_lookup",
        {},
        execution_options={"timeout_seconds": 0.001},
    )
    recovered_retry = dict((recovered.get("execution") or {}).get("retry") or {})
    exhausted_retry = dict((exhausted.get("execution") or {}).get("retry") or {})
    timeout_metadata = dict((timed_out.get("execution") or {}).get("timeout") or {})
    ok = (
        str(execution_adapter.get("retry_policy") or "").strip() == "sync_exception_retry"
        and str(execution_adapter.get("timeout_enforcement") or "").strip() == "post_call_elapsed_check"
        and str(recovered.get("status") or "").strip() == "ok"
        and str(recovered_retry.get("status") or "").strip() == "recovered"
        and int(recovered_retry.get("attempt_count") or 0) == 2
        and recovered_tool.calls == 2
        and str(exhausted.get("status") or "").strip() == "error"
        and str(exhausted_retry.get("status") or "").strip() == "exhausted"
        and int(exhausted_retry.get("attempt_count") or 0) == 2
        and exhausted_tool.calls == 2
        and str(timed_out.get("status") or "").strip() == "timeout"
        and str(timeout_metadata.get("status") or "").strip() == "exceeded"
        and str(timeout_metadata.get("enforcement") or "").strip() == "post_call_elapsed_check"
        and slow_tool.calls == 1
    )
    return {
        "ok": ok,
        "retry_policy": execution_adapter.get("retry_policy"),
        "timeout_enforcement": execution_adapter.get("timeout_enforcement"),
        "schema_validation": execution_adapter.get("schema_validation"),
        "recovered_status": recovered.get("status"),
        "recovered_retry_status": recovered_retry.get("status"),
        "recovered_attempt_count": recovered_retry.get("attempt_count"),
        "exhausted_status": exhausted.get("status"),
        "exhausted_retry_status": exhausted_retry.get("status"),
        "exhausted_attempt_count": exhausted_retry.get("attempt_count"),
        "timeout_status": timed_out.get("status"),
        "timeout_metadata_status": timeout_metadata.get("status"),
        "timeout_metadata_enforcement": timeout_metadata.get("enforcement"),
        "hard_cancellation_claimed": False,
        "sandbox_execution_claimed": False,
        "worker_timeout_claimed": False,
        "failure_reason": "" if ok else "tool_runtime_timeout_retry_contract_incomplete",
    }


def _run_subagent_lane_query_detail_contract_check(client=None) -> dict:
    query_id = "frontend-child-p10-i23-c1"
    detail = {}
    sample_source = "synthetic_builder_sample"
    if client is not None:
        status_code = 0
        try:
            response = client.get(f"/api/runtime-profile/subagent-lane-query-detail?query_id={query_id}")
            status_code = response.status_code
            payload = response.json()
        except Exception:
            payload = {}
        if (
            status_code == 200
            and isinstance(payload, dict)
            and str(payload.get("recording_state") or "").strip() == "recorded"
        ):
            detail = payload
            sample_source = "runtime_profile_endpoint"
    if not detail:
        detail = SubagentLaneQueryDetailBuilder.build_detail_from_events(
            query_id=query_id,
            events=_build_subagent_lane_query_detail_smoke_events(query_id),
        )

    forbidden_fields = {"history_items", "page", "next_cursor", "workspace"}
    ok = (
        str(detail.get("contract_version") or "").strip() == "phase-h-subagent-lane-query-detail-v1"
        and str(detail.get("channel") or "").strip() == "subagent_lane"
        and str(detail.get("recording_state") or "").strip() == "recorded"
        and str(detail.get("query_id") or "").strip() == query_id
        and int(detail.get("stage_count") or 0) >= 2
        and int(detail.get("recent_event_count") or 0) >= 2
        and not any(field in detail for field in forbidden_fields)
    )
    return {
        "ok": ok,
        "contract_version": detail.get("contract_version"),
        "sample_source": sample_source,
        "recording_state": detail.get("recording_state"),
        "query_id": detail.get("query_id"),
        "latest_stage": detail.get("latest_stage"),
        "stage_count": detail.get("stage_count"),
        "recent_event_count": detail.get("recent_event_count"),
        "failure_reason": "" if ok else "subagent_lane_query_detail_contract_incomplete",
    }


def _build_subagent_lane_query_detail_smoke_events(query_id: str) -> list[dict]:
    return [
        {
            "timestamp": "2026-05-22T00:00:01Z",
            "severity": "info",
            "summary": "frontend 子智能体开始规划",
            "payload": {
                "channel": "subagent_lane",
                "query_id": query_id,
                "stage": "planning",
                "dedupe_key": f"{query_id}:planning",
                "snapshot_ref": {"snapshot_id": "subagent-lane-smoke-1"},
            },
        },
        {
            "timestamp": "2026-05-22T00:00:02Z",
            "severity": "info",
            "summary": "已合并 frontend 子智能体结果到主响应",
            "payload": {
                "channel": "subagent_lane",
                "query_id": query_id,
                "stage": "final_output",
                "dedupe_key": f"{query_id}:final_output",
                "snapshot_ref": {"snapshot_id": "subagent-lane-smoke-2"},
            },
        },
    ]


class _EmptyMcpRegistryService:
    def build_capability_catalog(self):
        return {"capabilities": []}


class _EmptyFrameworkAdapterRegistry:
    def build_health_entries(self):
        return []


def _run_embedded_sdk_durable_recovery_check() -> dict:
    with tempfile.TemporaryDirectory() as tmp_dir:
        sqlite_path = Path(tmp_dir) / "embedded_workspace_smoke.db"
        engine = create_engine(
            f"sqlite:///{sqlite_path.as_posix()}",
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
                    "args": {"path": "smoke-durable.md"},
                    "result": "ok",
                }

            def _reviewer(_run):
                return {
                    "reviewer": "quality_gate",
                    "status": "approved",
                    "summary": "durable recovery ok",
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
                    "tool_args": {"path": "smoke-durable.md"},
                    "reason": "Smoke validates durable recovery chain.",
                },
                tool_executor=_tool_executor,
                reviewer=_reviewer,
            )

            reader = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
            probe = reader.probe_run_recovery(result["run"]["run_id"])
            approved = reader.submit_approval(executed["approval_request"]["request_id"], "approved")
            resumed = reader.resume_run(result["run"]["run_id"], continue_loop=True)
            backend = store.describe_backend()
            ok = (
                bool(probe.get("recoverable"))
                and str((probe.get("tool_continuation") or {}).get("recovery_reason") or "").strip() == "ready_via_registry"
                and str((probe.get("loop_continuation") or {}).get("recovery_reason") or "").strip() == "ready_via_registry"
                and str((resumed.get("run") or {}).get("state") or "").strip() == "done"
                and bool(backend.get("durable"))
                and not bool(backend.get("fallback_active"))
            )
            return {
                "ok": ok,
                "backend_kind": backend.get("backend_kind"),
                "backend_mode": backend.get("backend_mode"),
                "fallback_active": backend.get("fallback_active"),
                "probe_recoverable": probe.get("recoverable"),
                "tool_recovery_reason": (probe.get("tool_continuation") or {}).get("recovery_reason"),
                "loop_recovery_reason": (probe.get("loop_continuation") or {}).get("recovery_reason"),
                "resumed_state": (resumed.get("run") or {}).get("state"),
                "approved_state": (approved.get("run") or {}).get("state"),
                "failure_reason": "" if ok else "durable_recovery_chain_incomplete",
            }
        finally:
            Base.metadata.drop_all(bind=engine)
            engine.dispose()


def _run_durable_checkpoint_resume_cursor_check() -> dict:
    with tempfile.TemporaryDirectory() as tmp_dir:
        sqlite_path = Path(tmp_dir) / "checkpoint_cursor_smoke.db"
        engine = create_engine(
            f"sqlite:///{sqlite_path.as_posix()}",
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
                    "args": {"path": "checkpoint-cursor.md"},
                    "result": "ok",
                }

            def _reviewer(_run):
                return {
                    "reviewer": "quality_gate",
                    "status": "approved",
                    "summary": "checkpoint cursor ok",
                }

            registry.register("tool_executor.filesystem_write", _tool_executor)
            registry.register("reviewer.quality_gate", _reviewer)

            writer = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
            result = writer.create_run({"conversation_id": 42, "user_id": 7, "run_kind": "chat"})
            writer.execute_run(
                result["run"]["run_id"],
                tool_policy=lambda _run: {
                    "status": "approval_required",
                    "tool_name": "filesystem_write",
                    "tool_args": {"path": "checkpoint-cursor.md"},
                    "reason": "Smoke validates checkpoint cursor recovery.",
                },
                tool_executor=_tool_executor,
                reviewer=_reviewer,
            )

            reader = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
            probe = reader.probe_run_recovery(result["run"]["run_id"])
            checkpoint = dict(probe.get("checkpoint") or {})
            cursor = dict(probe.get("resume_cursor") or {})
            ok = (
                str(checkpoint.get("contract_version") or "").strip() == "phase-ii-durable-runtime-checkpoint-v1"
                and str(checkpoint.get("status") or "").strip() == "ready"
                and str(checkpoint.get("checkpoint_kind") or "").strip() == "approval_waiting"
                and str(cursor.get("contract_version") or "").strip() == "phase-ii-runtime-resume-cursor-v1"
                and str(cursor.get("cursor_status") or "").strip() == "ready"
                and str(cursor.get("entrypoint") or "").strip() == "submit_approval.approved"
                and str(cursor.get("recovery_reason") or "").strip() == "ready_via_registry"
            )
            return {
                "ok": ok,
                "checkpoint_status": checkpoint.get("status"),
                "checkpoint_kind": checkpoint.get("checkpoint_kind"),
                "cursor_status": cursor.get("cursor_status"),
                "cursor_entrypoint": cursor.get("entrypoint"),
                "cursor_recovery_reason": cursor.get("recovery_reason"),
                "failure_reason": "" if ok else "checkpoint_resume_cursor_alignment_incomplete",
            }
        finally:
            Base.metadata.drop_all(bind=engine)
            engine.dispose()


def _run_durable_recovery_loader_contract_check() -> dict:
    store = _SmokeDurableWorkspaceStore()
    registry = InMemoryEmbeddedContinuationRegistry()

    def _tool_executor(_run):
        return {
            "tool_name": "filesystem_write",
            "args": {"path": "durable-loader.md"},
            "result": "ok",
        }

    def _reviewer(_run):
        return {
            "reviewer": "quality_gate",
            "status": "approved",
            "summary": "durable loader ok",
        }

    registry.register("tool_executor.filesystem_write", _tool_executor)
    registry.register("reviewer.quality_gate", _reviewer)
    writer = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
    result = writer.create_run({"conversation_id": 42, "user_id": 7, "run_kind": "chat"})
    executed = writer.execute_run(
        result["run"]["run_id"],
        tool_policy=lambda _run: {
            "status": "approval_required",
            "tool_name": "filesystem_write",
            "tool_args": {"path": "durable-loader.md"},
            "reason": "Smoke validates durable recovery loader.",
        },
        tool_executor=_tool_executor,
        reviewer=_reviewer,
    )
    request_id = executed["approval_request"]["request_id"]
    reader = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry)
    probe = reader.probe_run_recovery(result["run"]["run_id"])
    loader = dict(probe.get("durable_recovery_loader") or {})

    missing_loader = DurableRecoveryLoader(
        workspace_store=_SmokeDurableWorkspaceStore(),
        continuation_registry=registry,
    ).load(run_id="missing-run")

    unresolved_loader = DurableRecoveryLoader(
        workspace_store=store,
        continuation_registry=InMemoryEmbeddedContinuationRegistry(),
    ).load(run_id=result["run"]["run_id"], approval_request_id=request_id)

    stale_approval = dict(store.get_approval_snapshot(request_id) or {})
    stale_approval["status"] = "denied"
    store.save_approval_snapshot(stale_approval)
    stale_loader = DurableRecoveryLoader(
        workspace_store=store,
        continuation_registry=registry,
    ).load(run_id=result["run"]["run_id"], approval_request_id=request_id)
    stale_approval["status"] = "pending"
    store.save_approval_snapshot(stale_approval)

    unsafe_descriptor = dict(store.get_tool_continuation_descriptor(request_id) or {})
    unsafe_descriptor["handler"] = "unsafe serialized handler"
    store.save_tool_continuation_descriptor(request_id, unsafe_descriptor)
    unsafe_probe = EmbeddedAgentRuntimeSDK(workspace_store=store, continuation_registry=registry).probe_run_recovery(
        result["run"]["run_id"]
    )
    unsafe_loader = dict(unsafe_probe.get("durable_recovery_loader") or {})
    lifecycle = dict(loader.get("descriptor_lifecycle") or {})
    unresolved_lifecycle = dict(unresolved_loader.get("descriptor_lifecycle") or {})
    stale_lifecycle = dict(stale_loader.get("descriptor_lifecycle") or {})
    unsafe_lifecycle = dict(unsafe_loader.get("descriptor_lifecycle") or {})
    default_handoff = dict(loader.get("loader_execution_handoff") or {})
    explicit_handoff = build_durable_loader_execution_handoff_decision(
        loader_candidate=loader,
        explicit_handoff_requested=True,
        recovery_executor_bound=False,
    )

    ok = (
        str(loader.get("contract_version") or "").strip() == "phase-ii-durable-recovery-loader-v1"
        and str(loader.get("status") or "").strip() == "ready"
        and bool(loader.get("ready"))
        and str(loader.get("recovery_reason") or "").strip() == "ready_via_registry"
        and bool((loader.get("binding_evidence") or {}).get("all_bindings_resolved"))
        and str(missing_loader.get("recovery_reason") or "").strip() == "run_snapshot_missing"
        and str(unresolved_loader.get("recovery_reason") or "").strip() == "missing_registered_binding"
        and str(stale_loader.get("recovery_reason") or "").strip() == "denied"
        and str(unsafe_loader.get("recovery_reason") or "").strip() == "descriptor_corrupted"
        and str(lifecycle.get("contract_version") or "").strip()
        == "phase-ii-continuation-descriptor-lifecycle-governance-v1"
        and bool(lifecycle.get("governed"))
        and bool(lifecycle.get("all_ready"))
        and "ready" in (lifecycle.get("states") or [])
        and "bound" in (unresolved_lifecycle.get("states") or [])
        and "stale" in (stale_lifecycle.get("states") or [])
        and "unsafe" in (unsafe_lifecycle.get("states") or [])
        and str(default_handoff.get("contract_version") or "").strip()
        == "phase-ii-durable-loader-execution-handoff-policy-v1"
        and str(default_handoff.get("status") or "").strip() == "blocked"
        and str(default_handoff.get("blocked_reason") or "").strip() == "explicit_handoff_required"
        and not bool(default_handoff.get("will_execute"))
        and str(explicit_handoff.get("status") or "").strip() == "blocked"
        and str(explicit_handoff.get("blocked_reason") or "").strip() == "recovery_executor_not_bound"
        and not bool(explicit_handoff.get("will_execute"))
        and not bool(loader.get("executes_recovery"))
        and not bool(loader.get("deserializes_callables"))
    )
    return {
        "ok": ok,
        "contract_version": str(loader.get("contract_version") or ""),
        "loader_status": str(loader.get("status") or ""),
        "loader_ready": bool(loader.get("ready")),
        "loader_recovery_reason": str(loader.get("recovery_reason") or ""),
        "all_bindings_resolved": bool((loader.get("binding_evidence") or {}).get("all_bindings_resolved")),
        "missing_recovery_reason": str(missing_loader.get("recovery_reason") or ""),
        "unresolved_recovery_reason": str(unresolved_loader.get("recovery_reason") or ""),
        "stale_recovery_reason": str(stale_loader.get("recovery_reason") or ""),
        "unsafe_recovery_reason": str(unsafe_loader.get("recovery_reason") or ""),
        "descriptor_lifecycle_contract_version": str(lifecycle.get("contract_version") or ""),
        "descriptor_lifecycle_governed": bool(lifecycle.get("governed")),
        "descriptor_lifecycle_states": sorted(
            set(
                list(lifecycle.get("states") or [])
                + list(unresolved_lifecycle.get("states") or [])
                + list(stale_lifecycle.get("states") or [])
                + list(unsafe_lifecycle.get("states") or [])
            )
        ),
        "descriptor_lifecycle_all_ready": bool(lifecycle.get("all_ready")),
        "descriptor_lifecycle_unsafe_keys": list(unsafe_lifecycle.get("unsafe_descriptor_keys") or []),
        "handoff_policy_contract_version": str(default_handoff.get("contract_version") or ""),
        "default_handoff_status": str(default_handoff.get("status") or ""),
        "default_handoff_blocked_reason": str(default_handoff.get("blocked_reason") or ""),
        "default_handoff_will_execute": bool(default_handoff.get("will_execute")),
        "explicit_handoff_status": str(explicit_handoff.get("status") or ""),
        "explicit_handoff_blocked_reason": str(explicit_handoff.get("blocked_reason") or ""),
        "explicit_handoff_will_execute": bool(explicit_handoff.get("will_execute")),
        "recovery_executor_bound": bool(explicit_handoff.get("recovery_executor_bound")),
        "executes_recovery": bool(loader.get("executes_recovery")),
        "deserializes_callables": bool(loader.get("deserializes_callables")),
        "failure_reason": "" if ok else "durable_recovery_loader_contract_incomplete",
    }


def _run_runtime_surface_run_recovery_contract_check() -> dict:
    with tempfile.TemporaryDirectory() as tmp_dir:
        sqlite_path = Path(tmp_dir) / "runtime_surface_recovery.db"
        engine = create_engine(
            f"sqlite:///{sqlite_path.as_posix()}",
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
                    "args": {"path": "surface-recovery.md"},
                    "result": "ok",
                }

            def _reviewer(_run):
                return {
                    "reviewer": "quality_gate",
                    "status": "approved",
                    "summary": "runtime surface recovery ok",
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
            writer.execute_run(
                result["run"]["run_id"],
                tool_policy=lambda _run: {
                    "status": "approval_required",
                    "tool_name": "filesystem_write",
                    "tool_args": {"path": "surface-recovery.md"},
                    "reason": "Smoke validates runtime surface run_recovery contract.",
                },
                tool_executor=_tool_executor,
                reviewer=_reviewer,
            )

            service = RuntimeSurfaceService()
            service.embedded_workspace_store = store
            service.continuation_registry = registry
            recovery = service.get_run_recovery(run_id=result["run"]["run_id"])
            workspace_backend = dict(recovery.get("workspace_backend") or {})
            ok = (
                str(recovery.get("contract_version") or "").strip() == "phase-ii-run-recovery-v1"
                and bool(recovery.get("available"))
                and bool(recovery.get("recoverable"))
                and str((recovery.get("tool_continuation") or {}).get("recovery_reason") or "").strip() == "ready_via_registry"
                and str((recovery.get("loop_continuation") or {}).get("recovery_reason") or "").strip() == "ready_via_registry"
                and str(workspace_backend.get("backend_kind") or "").strip() == "sqlalchemy"
                and bool(workspace_backend.get("durable"))
                and not bool(workspace_backend.get("fallback_active"))
            )
            return {
                "ok": ok,
                "contract_version": recovery.get("contract_version"),
                "run_recovery_available": recovery.get("available"),
                "probe_recoverable": recovery.get("recoverable"),
                "backend_kind": workspace_backend.get("backend_kind"),
                "backend_mode": workspace_backend.get("backend_mode"),
                "fallback_active": workspace_backend.get("fallback_active"),
                "tool_recovery_reason": (recovery.get("tool_continuation") or {}).get("recovery_reason"),
                "loop_recovery_reason": (recovery.get("loop_continuation") or {}).get("recovery_reason"),
                "failure_reason": "" if ok else "run_recovery_contract_incomplete",
            }
        finally:
            Base.metadata.drop_all(bind=engine)
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
