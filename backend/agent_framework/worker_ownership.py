"""Runtime worker ownership lease and fencing contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import threading
from typing import Any, Callable, Dict
from uuid import uuid4

try:
    from ..config import WORKER_OWNERSHIP_STORE_MODE
except ImportError:  # pragma: no cover - package import compatibility
    from backend.config import WORKER_OWNERSHIP_STORE_MODE


RUNTIME_WORKER_OWNERSHIP_CONTRACT_VERSION = "phase-ii-runtime-worker-ownership-v1"
WORKER_OWNERSHIP_OPERATIONAL_READINESS_CONTRACT_VERSION = "phase-ii-worker-ownership-operations-v1"
WORKER_OWNERSHIP_PRODUCTION_GATE_CONTRACT_VERSION = "phase-ii-worker-ownership-production-gate-v1"
WORKER_OWNERSHIP_RENEWAL_SUPERVISOR_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-renewal-supervisor-v1"
)
WORKER_OWNERSHIP_ROLLOUT_READINESS_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-rollout-readiness-v1"
)
WORKER_OWNERSHIP_PRODUCTION_ROLLOUT_OPERATIONALIZATION_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-production-rollout-operationalization-v1"
)
WORKER_OWNERSHIP_ROLLOUT_CONFIRMATION_DECISION_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-rollout-confirmation-decision-v1"
)
WORKER_OWNERSHIP_ROLLOUT_CONFIRMATION_INPUT_SOURCE_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-rollout-confirmation-input-source-v1"
)
WORKER_OWNERSHIP_AUTO_CLAIM_POLICY_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-auto-claim-policy-v1"
)
WORKER_OWNERSHIP_AUTO_CLAIM_ENTRYPOINT_ALLOWLIST_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-auto-claim-entrypoint-allowlist-v1"
)
WORKER_OWNERSHIP_EXPLICIT_AUTO_CLAIM_ENABLEMENT_GATE_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-explicit-auto-claim-enablement-gate-v1"
)
WORKER_OWNERSHIP_AUDIT_EVIDENCE_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-audit-evidence-v1"
)
WORKER_OWNERSHIP_VENDOR_LOCK_SEMANTICS_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-vendor-lock-semantics-v1"
)
WORKER_OWNERSHIP_VENDOR_LOCK_ADAPTER_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-vendor-lock-adapter-v1"
)
WORKER_OWNERSHIP_POSTGRES_VENDOR_LOCK_PROBE_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-postgres-vendor-lock-probe-v1"
)
WORKER_OWNERSHIP_POSTGRES_ADVISORY_LOCK_EXECUTION_SEAM_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-postgres-advisory-lock-execution-seam-v1"
)
WORKER_OWNERSHIP_VENDOR_LOCK_TARGET_DECISION_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-vendor-lock-target-decision-v1"
)
WORKER_OWNERSHIP_VENDOR_LOCK_TARGET_DECISION_INPUT_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-vendor-lock-target-decision-input-v1"
)
WORKER_OWNERSHIP_PRODUCTION_ENABLEMENT_STRATEGY_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-production-enablement-strategy-v1"
)
WORKER_OWNERSHIP_PRODUCTION_DEFAULT_ENABLEMENT_INPUT_SOURCE_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-production-default-enablement-input-source-v1"
)
WORKER_OWNERSHIP_POSTGRES_ROLLOUT_ARTIFACT_CONSUMER_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-postgres-rollout-artifact-consumer-v1"
)
WORKER_OWNERSHIP_POSTGRES_VENDOR_LOCK_TARGET_ARTIFACT_BINDING_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-postgres-vendor-lock-target-artifact-binding-v1"
)
WORKER_OWNERSHIP_POSTGRES_VENDOR_LOCK_SEMANTICS_BINDING_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-postgres-vendor-lock-semantics-binding-v1"
)
WORKER_OWNERSHIP_POSTGRES_VENDOR_LOCK_PRODUCTION_GATE_WIRING_DECISION_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-postgres-vendor-lock-production-gate-wiring-decision-v1"
)
WORKER_OWNERSHIP_PRODUCTION_GATE_COMPOSITION_DRY_RUN_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-production-gate-composition-dry-run-v1"
)
WORKER_OWNERSHIP_PRODUCTION_ENABLEMENT_RUNTIME_CONFIG_CONSUMER_CONTRACT_VERSION = (
    "phase-ii-worker-ownership-production-enablement-runtime-config-consumer-v1"
)

WORKER_OWNERSHIP_STATUS_CLAIMED = "claimed"
WORKER_OWNERSHIP_STATUS_BLOCKED = "blocked"
WORKER_OWNERSHIP_STATUS_REFRESHED = "refreshed"
WORKER_OWNERSHIP_STATUS_VALIDATED = "validated"
WORKER_OWNERSHIP_STATUS_EXPIRED = "expired"

WORKER_OWNERSHIP_REASON_WORKER_OWNERSHIP_LOST = "worker_ownership_lost"
WORKER_OWNERSHIP_REASON_STALE_FENCING_TOKEN = "stale_worker_fencing_token"
WORKER_OWNERSHIP_REASON_LEASE_NOT_FOUND = "worker_lease_not_found"
WORKER_OWNERSHIP_REASON_LEASE_EXPIRED = "worker_lease_expired"
WORKER_OWNERSHIP_REASON_INVALID_LEASE = "worker_lease_mismatch"
WORKER_OWNERSHIP_REASON_POSTGRES_ADVISORY_LOCK_EXECUTOR_MISSING = (
    "postgres_advisory_lock_executor_missing"
)
WORKER_OWNERSHIP_REASON_POSTGRES_ADVISORY_LOCK_OWNER_IDENTITY_MISSING = (
    "postgres_advisory_lock_owner_identity_missing"
)
WORKER_OWNERSHIP_REASON_POSTGRES_ADVISORY_LOCK_NOT_ACQUIRED = (
    "postgres_advisory_lock_not_acquired"
)
WORKER_OWNERSHIP_REASON_POSTGRES_ADVISORY_LOCK_EXECUTOR_FAILED = (
    "postgres_advisory_lock_executor_failed"
)

ALLOWED_WORKER_OWNERSHIP_STORE_MODES = {"memory_only", "prefer_sql_with_fallback", "strict_sql"}
DEFAULT_WORKER_OWNERSHIP_AUTO_CLAIM_ENTRYPOINTS = (
    "submit_approval.approved",
    "resume_run.continue_loop",
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _isoformat(value: datetime | None) -> str:
    return value.isoformat() if value is not None else ""


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_text_list(values: Any) -> list[str]:
    if not isinstance(values, (list, tuple, set)):
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _normalize_text(value)
        if not text or text in seen:
            continue
        normalized.append(text)
        seen.add(text)
    return normalized


def _ensure_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def build_worker_ownership_contract(
    *,
    adapter_kind: str = "in_memory",
    durable: bool = False,
) -> Dict[str, Any]:
    return {
        "contract_version": RUNTIME_WORKER_OWNERSHIP_CONTRACT_VERSION,
        "adapter_kind": str(adapter_kind or "").strip() or "in_memory",
        "operations": ["claim_run", "heartbeat", "validate_ownership", "get_lease"],
        "lease_fields": [
            "run_id",
            "worker_id",
            "lease_id",
            "fencing_token",
            "claimed_at",
            "lease_expires_at",
            "last_heartbeat_at",
            "lease_status",
        ],
        "fail_closed_reasons": [
            WORKER_OWNERSHIP_REASON_WORKER_OWNERSHIP_LOST,
            WORKER_OWNERSHIP_REASON_STALE_FENCING_TOKEN,
            WORKER_OWNERSHIP_REASON_LEASE_NOT_FOUND,
            WORKER_OWNERSHIP_REASON_LEASE_EXPIRED,
            WORKER_OWNERSHIP_REASON_INVALID_LEASE,
        ],
        "durable": bool(durable),
        "non_executable_payload": True,
    }


def _build_production_gate_section(
    *,
    name: str,
    ready: bool,
    evidence: Dict[str, Any] | None = None,
    missing_reason: str = "",
) -> Dict[str, Any]:
    return {
        "name": name,
        "status": "ready" if ready else "blocked",
        "ready": bool(ready),
        "missing_reason": "" if ready else _normalize_text(missing_reason),
        "evidence": dict(evidence or {}),
    }


def build_worker_ownership_renewal_supervisor_contract(
    *,
    heartbeat_operation_present: bool = False,
    renew_once_supported: bool = False,
    owner_identity_required: bool = False,
    controlled_lifecycle_supported: bool = False,
    starts_by_default: bool = False,
    active: bool = False,
    last_renewal_status: str = "",
    stop_supported: bool = False,
    failure_fail_closed: bool = False,
    background_supervisor_present: bool = False,
    renewal_owner_identity_present: bool = False,
    ttl_interval_policy_present: bool = False,
    lease_loss_fail_closed: bool = False,
    supervisor_enabled_by_default: bool = False,
    lease_ttl_seconds: int | None = None,
    renew_interval_seconds: int | None = None,
) -> Dict[str, Any]:
    """Describe renewal supervisor readiness without starting any background work."""

    owner_identity_ready = bool(renewal_owner_identity_present) or bool(owner_identity_required)
    ttl_interval_policy_ready = bool(ttl_interval_policy_present)
    sections = [
        ("heartbeat_operation", bool(heartbeat_operation_present)),
        ("background_supervisor", bool(background_supervisor_present)),
        ("renewal_owner_identity", owner_identity_ready),
        ("ttl_interval_policy", ttl_interval_policy_ready),
        ("lease_loss_fail_closed", bool(lease_loss_fail_closed)),
    ]
    missing_sections = [name for name, ready in sections if not ready]
    overall_status = "ready" if not missing_sections else "blocked"
    return {
        "contract_version": WORKER_OWNERSHIP_RENEWAL_SUPERVISOR_CONTRACT_VERSION,
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "supervisor_enabled_by_default": bool(supervisor_enabled_by_default)
        and overall_status == "ready",
        "policy": {
            "heartbeat_operation_present": bool(heartbeat_operation_present),
            "renew_once_supported": bool(renew_once_supported),
            "owner_identity_required": bool(owner_identity_required),
            "controlled_lifecycle_supported": bool(controlled_lifecycle_supported),
            "starts_by_default": bool(starts_by_default) and bool(supervisor_enabled_by_default),
            "active": bool(active),
            "last_renewal_status": _normalize_text(last_renewal_status),
            "stop_supported": bool(stop_supported),
            "failure_fail_closed": bool(failure_fail_closed),
            "background_supervisor_present": bool(background_supervisor_present),
            "renewal_owner_identity_present": owner_identity_ready,
            "ttl_interval_policy_present": ttl_interval_policy_ready,
            "ttl_interval_policy_ready": ttl_interval_policy_ready,
            "lease_ttl_seconds": int(lease_ttl_seconds or 0),
            "renew_interval_seconds": int(renew_interval_seconds or 0),
            "lease_loss_fail_closed": bool(lease_loss_fail_closed),
        },
        "missing_sections": missing_sections,
        "next_allowed_action": (
            "consider_explicit_supervisor_enablement"
            if overall_status == "ready"
            else "define_background_renewal_supervisor_owner_ttl_interval_and_loss_policy"
        ),
        "non_goals": [
            "no_background_lease_renewal_loop",
            "no_default_supervisor_enablement",
            "no_vendor_lock_semantics",
            "no_recovery_entry_auto_claim",
            "no_thread_or_timer_start",
        ],
    }


def build_worker_ownership_vendor_lock_adapter_contract(
    *,
    adapter_kind: str = "",
    target_backend: str = "",
    lock_scope: str = "",
    fencing_strategy: str = "",
    ttl_renewal_strategy: str = "",
    failover_strategy: str = "",
    stale_owner_cleanup_strategy: str = "",
    acquire_supported: bool = False,
    renew_supported: bool = False,
    release_supported: bool = False,
    probe_supported: bool = False,
    production_lock_allowed: bool = False,
    sql_row_lease_is_vendor_lock: bool = False,
    backend_probe: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Describe an opt-in vendor lock adapter boundary without lock side effects."""

    normalized_adapter_kind = _normalize_text(adapter_kind)
    normalized_target_backend = _normalize_text(target_backend)
    normalized_lock_scope = _normalize_text(lock_scope)
    normalized_fencing = _normalize_text(fencing_strategy)
    normalized_ttl = _normalize_text(ttl_renewal_strategy)
    normalized_failover = _normalize_text(failover_strategy)
    normalized_cleanup = _normalize_text(stale_owner_cleanup_strategy)
    probe = dict(
        backend_probe
        or (
            build_worker_ownership_postgres_vendor_lock_probe_contract()
            if normalized_target_backend == "postgres"
            or normalized_adapter_kind == "postgres_advisory_lock"
            else {}
        )
    )
    probe_status = _normalize_text(probe.get("overall_status"))
    probe_ready = not probe or probe_status == "ready"
    sections = [
        ("adapter_kind", bool(normalized_adapter_kind)),
        ("target_backend", bool(normalized_target_backend)),
        ("lock_scope", bool(normalized_lock_scope)),
        ("fencing_strategy", bool(normalized_fencing)),
        ("ttl_renewal_strategy", bool(normalized_ttl)),
        ("failover_strategy", bool(normalized_failover)),
        ("stale_owner_cleanup_strategy", bool(normalized_cleanup)),
        ("acquire_support", bool(acquire_supported)),
        ("renew_support", bool(renew_supported)),
        ("release_support", bool(release_supported)),
        ("probe_support", bool(probe_supported)),
        ("backend_probe", probe_ready),
        ("production_lock_allowment", bool(production_lock_allowed)),
        ("sql_row_lease_not_vendor_lock", not bool(sql_row_lease_is_vendor_lock)),
    ]
    missing_sections = [name for name, ready in sections if not ready]
    overall_status = "ready" if not missing_sections else "blocked"
    return {
        "contract_version": WORKER_OWNERSHIP_VENDOR_LOCK_ADAPTER_CONTRACT_VERSION,
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "adapter_kind": normalized_adapter_kind,
        "target_backend": normalized_target_backend,
        "lock_scope": normalized_lock_scope,
        "fencing_strategy": normalized_fencing,
        "ttl_renewal_strategy": normalized_ttl,
        "failover_strategy": normalized_failover,
        "stale_owner_cleanup_strategy": normalized_cleanup,
        "acquire_supported": bool(acquire_supported),
        "renew_supported": bool(renew_supported),
        "release_supported": bool(release_supported),
        "probe_supported": bool(probe_supported),
        "production_lock_allowed": bool(production_lock_allowed) and overall_status == "ready",
        "sql_row_lease_is_vendor_lock": False,
        "backend_probe": probe,
        "missing_sections": missing_sections,
        "next_allowed_action": (
            "consider_concrete_vendor_lock_backend_slice"
            if overall_status == "ready"
            else "define_vendor_lock_adapter_backend_scope_capabilities_and_allowment"
        ),
        "non_goals": [
            "no_vendor_specific_lock_backend",
            "no_lock_acquisition_side_effect",
            "no_sql_row_lease_as_vendor_lock",
            "no_default_production_ownership_enablement",
            "no_recovery_entry_auto_claim",
            "no_background_worker_start",
        ],
    }


def build_worker_ownership_postgres_advisory_lock_execution_seam_contract(
    *,
    executor_bound: bool = False,
    probe_once_supported: bool = False,
    acquire_once_supported: bool = False,
    renew_once_supported: bool = False,
    release_once_supported: bool = False,
    lock_key_derivation_ready: bool = False,
    owner_identity_required: bool = True,
    fencing_token_required: bool = True,
    fail_closed: bool = True,
    enabled_by_default: bool = False,
    production_lock_allowed: bool = False,
) -> Dict[str, Any]:
    """Describe opt-in PostgreSQL advisory lock execution without connecting to Postgres."""

    sections = [
        ("executor_binding", bool(executor_bound)),
        ("probe_once_support", bool(probe_once_supported)),
        ("acquire_once_support", bool(acquire_once_supported)),
        ("renew_once_support", bool(renew_once_supported)),
        ("release_once_support", bool(release_once_supported)),
        ("lock_key_derivation", bool(lock_key_derivation_ready)),
        ("owner_identity_required", bool(owner_identity_required)),
        ("fencing_token_required", bool(fencing_token_required)),
        ("fail_closed", bool(fail_closed)),
    ]
    missing_sections = [name for name, ready in sections if not ready]
    overall_status = "ready" if not missing_sections else "blocked"
    return {
        "contract_version": (
            WORKER_OWNERSHIP_POSTGRES_ADVISORY_LOCK_EXECUTION_SEAM_CONTRACT_VERSION
        ),
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "executor_bound": bool(executor_bound),
        "enabled_by_default": bool(enabled_by_default) and overall_status == "ready",
        "production_lock_allowed": bool(production_lock_allowed) and overall_status == "ready",
        "policy": {
            "probe_once_supported": bool(probe_once_supported),
            "acquire_once_supported": bool(acquire_once_supported),
            "renew_once_supported": bool(renew_once_supported),
            "release_once_supported": bool(release_once_supported),
            "lock_key_derivation_ready": bool(lock_key_derivation_ready),
            "owner_identity_required": bool(owner_identity_required),
            "fencing_token_required": bool(fencing_token_required),
            "fail_closed": bool(fail_closed),
            "starts_by_default": False,
            "background_loop_present": False,
            "sql_row_lease_is_vendor_lock": False,
        },
        "missing_sections": missing_sections,
        "next_allowed_action": (
            "consider_postgres_vendor_lock_rollout_evidence"
            if overall_status == "ready"
            else "inject_executor_and_verify_one_shot_advisory_lock_operations"
        ),
        "non_goals": [
            "no_default_postgres_connection",
            "no_background_lock_loop",
            "no_default_production_ownership_enablement",
            "no_sql_row_lease_as_vendor_lock",
            "no_recovery_entry_auto_claim",
        ],
    }


def build_worker_ownership_postgres_vendor_lock_probe_contract(
    *,
    advisory_lock_family: str = "",
    lock_key_derivation: str = "",
    lock_scope: str = "",
    fencing_token_binding: str = "",
    ttl_renewal_strategy: str = "",
    failover_behavior: str = "",
    stale_owner_cleanup_strategy: str = "",
    probe_safety: str = "",
    executes_probe: bool = False,
    sql_row_lease_is_vendor_lock: bool = False,
    execution_seam_contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Describe PostgreSQL advisory lock readiness without executing SQL."""

    normalized_family = _normalize_text(advisory_lock_family)
    normalized_key = _normalize_text(lock_key_derivation)
    normalized_scope = _normalize_text(lock_scope)
    normalized_fencing = _normalize_text(fencing_token_binding)
    normalized_ttl = _normalize_text(ttl_renewal_strategy)
    normalized_failover = _normalize_text(failover_behavior)
    normalized_cleanup = _normalize_text(stale_owner_cleanup_strategy)
    normalized_safety = _normalize_text(probe_safety)
    sections = [
        ("advisory_lock_family", bool(normalized_family)),
        ("lock_key_derivation", bool(normalized_key)),
        ("lock_scope", bool(normalized_scope)),
        ("fencing_token_binding", bool(normalized_fencing)),
        ("ttl_renewal_strategy", bool(normalized_ttl)),
        ("failover_behavior", bool(normalized_failover)),
        ("stale_owner_cleanup_strategy", bool(normalized_cleanup)),
        ("probe_safety", bool(normalized_safety) and not bool(executes_probe)),
        ("sql_row_lease_not_vendor_lock", not bool(sql_row_lease_is_vendor_lock)),
    ]
    missing_sections = [name for name, ready in sections if not ready]
    overall_status = "ready" if not missing_sections else "blocked"
    execution_seam = dict(
        execution_seam_contract
        or build_worker_ownership_postgres_advisory_lock_execution_seam_contract()
    )
    return {
        "contract_version": WORKER_OWNERSHIP_POSTGRES_VENDOR_LOCK_PROBE_CONTRACT_VERSION,
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "target_backend": "postgres",
        "advisory_lock_family": normalized_family,
        "lock_key_derivation": normalized_key,
        "lock_scope": normalized_scope,
        "fencing_token_binding": normalized_fencing,
        "ttl_renewal_strategy": normalized_ttl,
        "failover_behavior": normalized_failover,
        "stale_owner_cleanup_strategy": normalized_cleanup,
        "probe_safety": normalized_safety,
        "executes_probe": False,
        "sql_row_lease_is_vendor_lock": False,
        "execution_seam": execution_seam,
        "missing_sections": missing_sections,
        "next_allowed_action": (
            "consider_opt_in_postgres_advisory_lock_adapter"
            if overall_status == "ready"
            else "define_postgres_advisory_lock_family_key_scope_fencing_failover_cleanup_and_probe_safety"
        ),
        "non_goals": [
            "no_postgres_connection",
            "no_advisory_lock_sql_execution",
            "no_sql_row_lease_as_vendor_lock",
            "no_default_production_ownership_enablement",
            "no_recovery_entry_auto_claim",
        ],
    }


def build_worker_ownership_vendor_lock_semantics_contract(
    *,
    current_posture: str = "local_preview_only",
    sql_row_lease_fencing: bool = False,
    vendor_lock_adapter_present: bool = False,
    lock_scope_defined: bool = False,
    fencing_guarantee_defined: bool = False,
    failover_semantics_defined: bool = False,
    ttl_renewal_semantics_defined: bool = False,
    stale_owner_cleanup_defined: bool = False,
    production_lock_allowed: bool = False,
    lock_adapter_kind: str = "",
    lock_scope: str = "",
    target_decision_contract: Dict[str, Any] | None = None,
    adapter_contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Describe vendor lock semantics readiness without implementing a lock adapter."""

    adapter = dict(
        adapter_contract
        or build_worker_ownership_vendor_lock_adapter_contract(
            adapter_kind=lock_adapter_kind,
            target_backend=lock_adapter_kind,
            lock_scope=lock_scope,
            fencing_strategy="fencing_token" if fencing_guarantee_defined else "",
            ttl_renewal_strategy="lease_ttl_renewal" if ttl_renewal_semantics_defined else "",
            failover_strategy="documented_failover" if failover_semantics_defined else "",
            stale_owner_cleanup_strategy=(
                "documented_stale_owner_cleanup" if stale_owner_cleanup_defined else ""
            ),
            acquire_supported=vendor_lock_adapter_present,
            renew_supported=vendor_lock_adapter_present,
            release_supported=vendor_lock_adapter_present,
            probe_supported=vendor_lock_adapter_present,
            production_lock_allowed=production_lock_allowed,
            sql_row_lease_is_vendor_lock=False,
        )
    )
    adapter_ready = _normalize_text(adapter.get("overall_status")) == "ready"
    target_decision = dict(
        target_decision_contract
        or build_worker_ownership_vendor_lock_target_decision_contract(
            decision_recorded=bool(vendor_lock_adapter_present or lock_adapter_kind or lock_scope),
            target_backend=_normalize_text(lock_adapter_kind),
            lock_adapter_kind=lock_adapter_kind,
            lock_scope=lock_scope,
            fencing_strategy="fencing_token" if fencing_guarantee_defined else "",
            ttl_renewal_strategy="lease_ttl_renewal" if ttl_renewal_semantics_defined else "",
            failover_strategy="documented_failover" if failover_semantics_defined else "",
            stale_owner_cleanup_strategy=(
                "documented_stale_owner_cleanup" if stale_owner_cleanup_defined else ""
            ),
            sql_row_lease_is_vendor_lock=False,
            production_lock_allowed=production_lock_allowed,
        )
    )
    target_decision_ready = _normalize_text(target_decision.get("overall_status")) == "ready"
    sections = [
        ("vendor_lock_adapter", adapter_ready),
        ("target_decision", target_decision_ready),
        ("lock_scope", bool(lock_scope_defined)),
        ("fencing_guarantee", bool(fencing_guarantee_defined)),
        ("failover_semantics", bool(failover_semantics_defined)),
        ("ttl_renewal_semantics", bool(ttl_renewal_semantics_defined)),
        ("stale_owner_cleanup", bool(stale_owner_cleanup_defined)),
        ("production_lock_allowment", bool(production_lock_allowed)),
    ]
    missing_sections = [name for name, ready in sections if not ready]
    overall_status = "ready" if not missing_sections else "blocked"
    normalized_posture = _normalize_text(current_posture) or "local_preview_only"
    return {
        "contract_version": WORKER_OWNERSHIP_VENDOR_LOCK_SEMANTICS_CONTRACT_VERSION,
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "production_lock_allowed": bool(production_lock_allowed) and overall_status == "ready",
        "current_posture": normalized_posture,
        "policy": {
            "sql_row_lease_fencing": bool(sql_row_lease_fencing),
            "sql_row_lease_is_vendor_lock": False,
            "vendor_lock_adapter_present": adapter_ready,
            "lock_adapter_kind": _normalize_text(lock_adapter_kind),
            "lock_scope_defined": bool(lock_scope_defined),
            "lock_scope": _normalize_text(lock_scope),
            "fencing_guarantee_defined": bool(fencing_guarantee_defined),
            "failover_semantics_defined": bool(failover_semantics_defined),
            "ttl_renewal_semantics_defined": bool(ttl_renewal_semantics_defined),
            "stale_owner_cleanup_defined": bool(stale_owner_cleanup_defined),
            "adapter_contract": adapter,
            "target_decision": target_decision,
        },
        "missing_sections": missing_sections,
        "next_allowed_action": (
            "consider_explicit_vendor_lock_enablement"
            if overall_status == "ready"
            else "define_vendor_lock_adapter_scope_fencing_failover_ttl_renewal_cleanup_and_allowment"
        ),
        "non_goals": [
            "no_vendor_specific_lock_adapter",
            "no_sql_row_lease_as_vendor_lock",
            "no_default_production_ownership_enablement",
            "no_background_worker_start",
        ],
    }


def build_worker_ownership_vendor_lock_target_decision_contract(
    *,
    decision_recorded: bool = False,
    target_backend: str = "",
    lock_adapter_kind: str = "",
    lock_scope: str = "",
    fencing_strategy: str = "",
    ttl_renewal_strategy: str = "",
    failover_strategy: str = "",
    stale_owner_cleanup_strategy: str = "",
    sql_row_lease_is_vendor_lock: bool = False,
    production_lock_allowed: bool = False,
    input_source_contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Describe the chosen vendor lock target without implementing an adapter."""

    normalized_target_backend = _normalize_text(target_backend)
    normalized_adapter_kind = _normalize_text(lock_adapter_kind)
    normalized_lock_scope = _normalize_text(lock_scope)
    normalized_fencing = _normalize_text(fencing_strategy)
    normalized_ttl = _normalize_text(ttl_renewal_strategy)
    normalized_failover = _normalize_text(failover_strategy)
    normalized_cleanup = _normalize_text(stale_owner_cleanup_strategy)
    target_is_sql_row_lease = normalized_target_backend.lower() in {
        "sql_row_lease",
        "sql_row_lease_fencing",
        "sqlalchemy_row_lease",
    }
    input_source = dict(
        input_source_contract
        or build_worker_ownership_vendor_lock_target_decision_input_contract(
            target_backend=normalized_target_backend,
            lock_adapter_kind=normalized_adapter_kind,
            sql_row_lease_is_vendor_lock=sql_row_lease_is_vendor_lock,
        )
    )
    input_source_ready = _normalize_text(input_source.get("overall_status")) == "ready"
    sections = [
        ("input_source", input_source_ready),
        ("decision_recorded", bool(decision_recorded)),
        ("target_backend", bool(normalized_target_backend) and not target_is_sql_row_lease),
        ("lock_adapter_kind", bool(normalized_adapter_kind)),
        ("lock_scope", bool(normalized_lock_scope)),
        ("fencing_strategy", bool(normalized_fencing)),
        ("ttl_renewal_strategy", bool(normalized_ttl)),
        ("failover_strategy", bool(normalized_failover)),
        ("stale_owner_cleanup_strategy", bool(normalized_cleanup)),
        ("sql_row_lease_not_vendor_lock", not bool(sql_row_lease_is_vendor_lock)),
        ("production_lock_allowment", bool(production_lock_allowed)),
    ]
    missing_sections = [name for name, ready in sections if not ready]
    overall_status = "ready" if not missing_sections else "blocked"
    return {
        "contract_version": WORKER_OWNERSHIP_VENDOR_LOCK_TARGET_DECISION_CONTRACT_VERSION,
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "decision_recorded": bool(decision_recorded),
        "target_backend": normalized_target_backend,
        "lock_adapter_kind": normalized_adapter_kind,
        "lock_scope": normalized_lock_scope,
        "fencing_strategy": normalized_fencing,
        "ttl_renewal_strategy": normalized_ttl,
        "failover_strategy": normalized_failover,
        "stale_owner_cleanup_strategy": normalized_cleanup,
        "input_source": input_source,
        "sql_row_lease_is_vendor_lock": bool(sql_row_lease_is_vendor_lock),
        "production_lock_allowed": bool(production_lock_allowed) and overall_status == "ready",
        "missing_sections": missing_sections,
        "next_allowed_action": (
            "use_target_decision_as_vendor_lock_adapter_input"
            if overall_status == "ready"
            else "record_vendor_lock_backend_adapter_scope_fencing_ttl_failover_cleanup_and_allowment"
        ),
        "non_goals": [
            "no_vendor_specific_lock_adapter",
            "no_sql_row_lease_as_vendor_lock",
            "no_default_production_ownership_enablement",
            "no_background_worker_start",
        ],
    }


def build_worker_ownership_vendor_lock_target_decision_input_contract(
    *,
    input_source_kind: str = "",
    decision_id: str = "",
    approved_by: str = "",
    approved_at: str = "",
    target_backend: str = "",
    lock_adapter_kind: str = "",
    rollout_artifact: str = "",
    config_key: str = "",
    manual_approval_reference: str = "",
    sql_row_lease_is_vendor_lock: bool = False,
) -> Dict[str, Any]:
    """Describe where a vendor lock target decision came from."""

    normalized_kind = _normalize_text(input_source_kind)
    normalized_decision_id = _normalize_text(decision_id)
    normalized_approved_by = _normalize_text(approved_by)
    normalized_approved_at = _normalize_text(approved_at)
    normalized_backend = _normalize_text(target_backend)
    normalized_adapter = _normalize_text(lock_adapter_kind)
    normalized_rollout_artifact = _normalize_text(rollout_artifact)
    normalized_config_key = _normalize_text(config_key)
    normalized_manual_ref = _normalize_text(manual_approval_reference)
    allowed_kinds = {
        "config",
        "ops_decision_record",
        "rollout_artifact",
        "manual_approval",
    }
    target_is_sql_row_lease = normalized_backend.lower() in {
        "sql_row_lease",
        "sql_row_lease_fencing",
        "sqlalchemy_row_lease",
    }
    source_reference_ready = (
        (normalized_kind == "config" and bool(normalized_config_key))
        or (normalized_kind == "ops_decision_record" and bool(normalized_decision_id))
        or (normalized_kind == "rollout_artifact" and bool(normalized_rollout_artifact))
        or (normalized_kind == "manual_approval" and bool(normalized_manual_ref))
    )
    sections = [
        ("input_source_kind", normalized_kind in allowed_kinds),
        ("decision_id", bool(normalized_decision_id)),
        ("approved_by", bool(normalized_approved_by)),
        ("approved_at", bool(normalized_approved_at)),
        ("target_backend", bool(normalized_backend) and not target_is_sql_row_lease),
        ("lock_adapter_kind", bool(normalized_adapter)),
        ("source_reference", source_reference_ready),
        ("sql_row_lease_not_vendor_lock", not bool(sql_row_lease_is_vendor_lock)),
    ]
    missing_sections = [name for name, ready in sections if not ready]
    overall_status = "ready" if not missing_sections else "blocked"
    return {
        "contract_version": WORKER_OWNERSHIP_VENDOR_LOCK_TARGET_DECISION_INPUT_CONTRACT_VERSION,
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "input_source_kind": normalized_kind,
        "decision_id": normalized_decision_id,
        "approved_by": normalized_approved_by,
        "approved_at": normalized_approved_at,
        "target_backend": normalized_backend,
        "lock_adapter_kind": normalized_adapter,
        "rollout_artifact": normalized_rollout_artifact,
        "config_key": normalized_config_key,
        "manual_approval_reference": normalized_manual_ref,
        "sql_row_lease_is_vendor_lock": bool(sql_row_lease_is_vendor_lock),
        "missing_sections": missing_sections,
        "next_allowed_action": (
            "use_input_source_as_vendor_lock_target_decision_authority"
            if overall_status == "ready"
            else "record_vendor_lock_target_decision_source_id_approval_backend_and_adapter"
        ),
        "non_goals": [
            "no_vendor_specific_lock_adapter",
            "no_sql_row_lease_as_vendor_lock",
            "no_default_production_ownership_enablement",
            "no_background_worker_start",
        ],
    }


def build_worker_ownership_rollout_readiness_contract(
    *,
    strict_mode_rollout_confirmed: bool = False,
    fallback_policy_confirmed: bool = False,
    migration_ready: bool = False,
    renewal_verification_ready: bool = False,
    stale_fencing_verified: bool = False,
    auto_claim_decision_recorded: bool = False,
    audit_evidence_ready: bool = False,
    rollback_plan_ready: bool = False,
    production_rollout_confirmed: bool = False,
    operationalization_contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Describe production rollout readiness without mutating deployment state."""

    operationalization = dict(
        operationalization_contract
        or build_worker_ownership_production_rollout_operationalization_contract(
            strict_mode_rollout_confirmed=strict_mode_rollout_confirmed,
            fallback_policy_confirmed=fallback_policy_confirmed,
            migration_ready=migration_ready,
            renewal_lifecycle_verified=renewal_verification_ready,
            stale_fencing_verified=stale_fencing_verified,
            auto_claim_decision_recorded=auto_claim_decision_recorded,
            audit_evidence_ready=audit_evidence_ready,
            rollback_plan_ready=rollback_plan_ready,
            production_rollout_confirmed=production_rollout_confirmed,
        )
    )
    sections = [
        ("strict_mode_rollout", bool(strict_mode_rollout_confirmed)),
        ("fallback_policy", bool(fallback_policy_confirmed)),
        ("migration", bool(migration_ready)),
        ("renewal_verification", bool(renewal_verification_ready)),
        ("stale_fencing", bool(stale_fencing_verified)),
        ("auto_claim_decision", bool(auto_claim_decision_recorded)),
        ("audit_evidence", bool(audit_evidence_ready)),
        ("rollback_plan", bool(rollback_plan_ready)),
    ]
    missing_sections = [name for name, ready in sections if not ready]
    overall_status = "ready" if not missing_sections else "blocked"
    return {
        "contract_version": WORKER_OWNERSHIP_ROLLOUT_READINESS_CONTRACT_VERSION,
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "production_rollout_confirmed": bool(production_rollout_confirmed)
        and overall_status == "ready"
        and _normalize_text(operationalization.get("overall_status")) == "ready",
        "checklist": {
            "strict_mode_rollout_confirmed": bool(strict_mode_rollout_confirmed),
            "fallback_policy_confirmed": bool(fallback_policy_confirmed),
            "migration_ready": bool(migration_ready),
            "renewal_verification_ready": bool(renewal_verification_ready),
            "stale_fencing_verified": bool(stale_fencing_verified),
            "auto_claim_decision_recorded": bool(auto_claim_decision_recorded),
            "audit_evidence_ready": bool(audit_evidence_ready),
            "rollback_plan_ready": bool(rollback_plan_ready),
        },
        "operationalization": operationalization,
        "missing_sections": missing_sections,
        "next_allowed_action": (
            "consider_explicit_production_rollout"
            if overall_status == "ready"
            else "confirm_strict_mode_fallback_migration_renewal_fencing_auto_claim_audit_and_rollback"
        ),
        "non_goals": [
            "no_deployment_state_mutation",
            "no_production_ownership_enablement",
            "no_recovery_entry_auto_claim",
            "no_background_worker_start",
        ],
    }


def build_worker_ownership_production_rollout_operationalization_contract(
    *,
    strict_mode_rollout_confirmed: bool = False,
    fallback_policy_confirmed: bool = False,
    migration_ready: bool = False,
    renewal_lifecycle_verified: bool = False,
    stale_fencing_verified: bool = False,
    auto_claim_decision_recorded: bool = False,
    audit_evidence_ready: bool = False,
    rollback_plan_ready: bool = False,
    production_rollout_confirmed: bool = False,
    rollout_mode: str = "readiness_only",
    confirmation_decision_contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Describe production rollout operational evidence without executing rollout."""

    confirmation_decision = dict(
        confirmation_decision_contract
        or build_worker_ownership_rollout_confirmation_decision_contract(
            production_rollout_confirmed=production_rollout_confirmed,
            target_store_mode="strict_sql" if strict_mode_rollout_confirmed else "",
            rollback_plan_acknowledged=rollback_plan_ready,
            fallback_policy_acknowledged=fallback_policy_confirmed,
            renewal_lifecycle_verified=renewal_lifecycle_verified,
            auto_claim_decision_recorded=auto_claim_decision_recorded,
        )
    )
    decision_ready = _normalize_text(confirmation_decision.get("overall_status")) == "ready"
    confirmation_input_source = dict(confirmation_decision.get("input_source") or {})
    artifact_readiness = {
        "strict_mode_rollout": bool(strict_mode_rollout_confirmed),
        "fallback_policy": bool(fallback_policy_confirmed),
        "migration": bool(migration_ready),
        "renewal_lifecycle_verification": bool(renewal_lifecycle_verified),
        "stale_fencing": bool(stale_fencing_verified),
        "auto_claim_decision": bool(auto_claim_decision_recorded),
        "audit_evidence": bool(audit_evidence_ready),
        "rollback_plan": bool(rollback_plan_ready),
        "explicit_rollout_confirmation": bool(production_rollout_confirmed),
        "rollout_confirmation_decision": decision_ready,
    }
    missing_artifacts = [name for name, ready in artifact_readiness.items() if not ready]
    overall_status = "ready" if not missing_artifacts else "blocked"
    return {
        "contract_version": WORKER_OWNERSHIP_PRODUCTION_ROLLOUT_OPERATIONALIZATION_CONTRACT_VERSION,
        "overall_status": overall_status,
        "production_rollout_confirmed": bool(production_rollout_confirmed)
        and overall_status == "ready",
        "rollout_mode": _normalize_text(rollout_mode) or "readiness_only",
        "required_artifacts": list(artifact_readiness.keys()),
        "missing_artifacts": missing_artifacts,
        "rollback_plan_status": "ready" if rollback_plan_ready else "missing",
        "fallback_policy_status": "ready" if fallback_policy_confirmed else "missing",
        "renewal_lifecycle_verification_status": (
            "verified" if renewal_lifecycle_verified else "missing"
        ),
        "auto_claim_decision_status": "recorded" if auto_claim_decision_recorded else "missing",
        "confirmation_decision": confirmation_decision,
        "rollout_confirmation_input_source": confirmation_input_source,
        "rollout_confirmation_decision_status": _normalize_text(
            confirmation_decision.get("overall_status")
        )
        or "blocked",
        "rollout_decision_recorded": bool(confirmation_decision.get("decision_recorded")),
        "rollout_decision_id": _normalize_text(confirmation_decision.get("decision_id")),
        "rollout_approved_by": _normalize_text(confirmation_decision.get("approved_by")),
        "rollout_approved_at": _normalize_text(confirmation_decision.get("approved_at")),
        "rollout_target_store_mode": _normalize_text(
            confirmation_decision.get("target_store_mode")
        ),
        "rollout_confirmation_missing_sections": list(
            confirmation_decision.get("missing_sections")
            if isinstance(confirmation_decision.get("missing_sections"), list)
            else []
        ),
        "rollout_confirmation_input_contract_version": _normalize_text(
            confirmation_input_source.get("contract_version")
        ),
        "rollout_confirmation_input_source_status": _normalize_text(
            confirmation_input_source.get("overall_status")
        )
        or "blocked",
        "rollout_confirmation_input_source_kind": _normalize_text(
            confirmation_input_source.get("input_source_kind")
        ),
        "rollout_confirmation_input_decision_id": _normalize_text(
            confirmation_input_source.get("decision_id")
        ),
        "rollout_confirmation_input_approved_by": _normalize_text(
            confirmation_input_source.get("approved_by")
        ),
        "rollout_confirmation_input_approved_at": _normalize_text(
            confirmation_input_source.get("approved_at")
        ),
        "rollout_confirmation_input_target_store_mode": _normalize_text(
            confirmation_input_source.get("target_store_mode")
        ),
        "rollout_confirmation_input_rollback_plan_reference": _normalize_text(
            confirmation_input_source.get("rollback_plan_reference")
        ),
        "rollout_confirmation_input_fallback_policy_reference": _normalize_text(
            confirmation_input_source.get("fallback_policy_reference")
        ),
        "rollout_confirmation_input_renewal_lifecycle_reference": _normalize_text(
            confirmation_input_source.get("renewal_lifecycle_reference")
        ),
        "rollout_confirmation_input_auto_claim_decision_reference": _normalize_text(
            confirmation_input_source.get("auto_claim_decision_reference")
        ),
        "rollout_confirmation_input_missing_sections": list(
            confirmation_input_source.get("missing_sections")
            if isinstance(confirmation_input_source.get("missing_sections"), list)
            else []
        ),
        "rollout_confirmation_input_sql_row_lease_is_authority": bool(
            confirmation_input_source.get("sql_row_lease_is_rollout_authority")
        ),
        "next_allowed_action": (
            "consider_explicit_production_rollout"
            if overall_status == "ready"
            else "complete_rollout_artifacts_before_default_enablement"
        ),
        "non_goals": [
            "no_deployment_state_mutation",
            "no_production_ownership_enablement",
            "no_recovery_entry_auto_claim",
            "no_vendor_lock_implementation",
        ],
    }


def build_worker_ownership_rollout_confirmation_decision_contract(
    *,
    production_rollout_confirmed: bool = False,
    decision_recorded: bool = False,
    decision_id: str = "",
    approved_by: str = "",
    approved_at: str = "",
    target_store_mode: str = "",
    rollback_plan_acknowledged: bool = False,
    fallback_policy_acknowledged: bool = False,
    renewal_lifecycle_verified: bool = False,
    auto_claim_decision_recorded: bool = False,
    input_source_contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Describe explicit rollout confirmation decision evidence without executing rollout."""

    normalized_target_store_mode = _normalize_text(target_store_mode)
    input_source = dict(
        input_source_contract
        or build_worker_ownership_rollout_confirmation_input_source_contract(
            decision_id=decision_id,
            approved_by=approved_by,
            approved_at=approved_at,
            target_store_mode=normalized_target_store_mode,
            rollback_plan_reference="acknowledged" if rollback_plan_acknowledged else "",
            fallback_policy_reference="acknowledged" if fallback_policy_acknowledged else "",
            renewal_lifecycle_reference="verified" if renewal_lifecycle_verified else "",
            auto_claim_decision_reference="recorded" if auto_claim_decision_recorded else "",
        )
    )
    input_source_ready = _normalize_text(input_source.get("overall_status")) == "ready"
    section_readiness = {
        "input_source": input_source_ready,
        "decision_recorded": bool(decision_recorded),
        "decision_id": bool(_normalize_text(decision_id)),
        "approved_by": bool(_normalize_text(approved_by)),
        "approved_at": bool(_normalize_text(approved_at)),
        "target_store_mode": normalized_target_store_mode == "strict_sql",
        "rollback_plan_acknowledged": bool(rollback_plan_acknowledged),
        "fallback_policy_acknowledged": bool(fallback_policy_acknowledged),
        "renewal_lifecycle_verified": bool(renewal_lifecycle_verified),
        "auto_claim_decision_recorded": bool(auto_claim_decision_recorded),
        "production_rollout_confirmed": bool(production_rollout_confirmed),
    }
    missing_sections = [
        name for name, ready in section_readiness.items() if not ready
    ]
    overall_status = "ready" if not missing_sections else "blocked"
    confirmed = bool(production_rollout_confirmed) and overall_status == "ready"
    return {
        "contract_version": WORKER_OWNERSHIP_ROLLOUT_CONFIRMATION_DECISION_CONTRACT_VERSION,
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "production_rollout_confirmed": confirmed,
        "decision_recorded": bool(decision_recorded),
        "decision_id": _normalize_text(decision_id),
        "approved_by": _normalize_text(approved_by),
        "approved_at": _normalize_text(approved_at),
        "target_store_mode": normalized_target_store_mode,
        "input_source": input_source,
        "rollback_plan_acknowledged": bool(rollback_plan_acknowledged),
        "fallback_policy_acknowledged": bool(fallback_policy_acknowledged),
        "renewal_lifecycle_verified": bool(renewal_lifecycle_verified),
        "auto_claim_decision_recorded": bool(auto_claim_decision_recorded),
        "missing_sections": missing_sections,
        "next_allowed_action": (
            "consider_production_rollout_gate"
            if overall_status == "ready"
            else "record_rollout_decision_approval_target_mode_rollback_fallback_renewal_and_auto_claim"
        ),
        "non_goals": [
            "no_deployment_state_mutation",
            "no_production_ownership_enablement",
            "no_recovery_entry_auto_claim",
            "no_vendor_lock_implementation",
            "no_background_worker_start",
        ],
    }


def build_worker_ownership_rollout_confirmation_input_source_contract(
    *,
    input_source_kind: str = "",
    decision_id: str = "",
    approved_by: str = "",
    approved_at: str = "",
    target_store_mode: str = "",
    rollback_plan_reference: str = "",
    fallback_policy_reference: str = "",
    renewal_lifecycle_reference: str = "",
    auto_claim_decision_reference: str = "",
    deployment_artifact: str = "",
    config_key: str = "",
    manual_approval_reference: str = "",
    change_ticket: str = "",
) -> Dict[str, Any]:
    """Describe where a production rollout confirmation decision came from."""

    normalized_kind = _normalize_text(input_source_kind)
    normalized_decision_id = _normalize_text(decision_id)
    normalized_approved_by = _normalize_text(approved_by)
    normalized_approved_at = _normalize_text(approved_at)
    normalized_target_store_mode = _normalize_text(target_store_mode)
    normalized_rollback = _normalize_text(rollback_plan_reference)
    normalized_fallback = _normalize_text(fallback_policy_reference)
    normalized_renewal = _normalize_text(renewal_lifecycle_reference)
    normalized_auto_claim = _normalize_text(auto_claim_decision_reference)
    normalized_deployment_artifact = _normalize_text(deployment_artifact)
    normalized_config_key = _normalize_text(config_key)
    normalized_manual_ref = _normalize_text(manual_approval_reference)
    normalized_change_ticket = _normalize_text(change_ticket)
    allowed_kinds = {
        "config",
        "ops_decision_record",
        "deployment_artifact",
        "change_ticket",
        "manual_approval",
    }
    sql_row_lease_is_authority = normalized_target_store_mode.lower() in {
        "sql_row_lease",
        "sql_row_lease_fencing",
        "sqlalchemy_row_lease",
    }
    source_reference_ready = (
        (normalized_kind == "config" and bool(normalized_config_key))
        or (normalized_kind == "ops_decision_record" and bool(normalized_decision_id))
        or (normalized_kind == "deployment_artifact" and bool(normalized_deployment_artifact))
        or (normalized_kind == "change_ticket" and bool(normalized_change_ticket or normalized_decision_id))
        or (normalized_kind == "manual_approval" and bool(normalized_manual_ref))
    )
    section_readiness = {
        "input_source_kind": normalized_kind in allowed_kinds,
        "decision_id": bool(normalized_decision_id),
        "approved_by": bool(normalized_approved_by),
        "approved_at": bool(normalized_approved_at),
        "target_store_mode": normalized_target_store_mode == "strict_sql",
        "rollback_plan_reference": bool(normalized_rollback),
        "fallback_policy_reference": bool(normalized_fallback),
        "renewal_lifecycle_reference": bool(normalized_renewal),
        "auto_claim_decision_reference": bool(normalized_auto_claim),
        "source_reference": source_reference_ready,
        "sql_row_lease_not_rollout_authority": not sql_row_lease_is_authority,
    }
    missing_sections = [
        name for name, ready in section_readiness.items() if not ready
    ]
    overall_status = "ready" if not missing_sections else "blocked"
    return {
        "contract_version": WORKER_OWNERSHIP_ROLLOUT_CONFIRMATION_INPUT_SOURCE_CONTRACT_VERSION,
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "input_source_kind": normalized_kind,
        "decision_id": normalized_decision_id,
        "approved_by": normalized_approved_by,
        "approved_at": normalized_approved_at,
        "target_store_mode": normalized_target_store_mode,
        "rollback_plan_reference": normalized_rollback,
        "fallback_policy_reference": normalized_fallback,
        "renewal_lifecycle_reference": normalized_renewal,
        "auto_claim_decision_reference": normalized_auto_claim,
        "deployment_artifact": normalized_deployment_artifact,
        "config_key": normalized_config_key,
        "manual_approval_reference": normalized_manual_ref,
        "change_ticket": normalized_change_ticket,
        "sql_row_lease_is_rollout_authority": sql_row_lease_is_authority,
        "missing_sections": missing_sections,
        "next_allowed_action": (
            "use_rollout_confirmation_input_source_as_decision_evidence"
            if overall_status == "ready"
            else "record_rollout_confirmation_source_approval_target_mode_rollback_fallback_renewal_and_auto_claim_reference"
        ),
        "non_goals": [
            "no_deployment_state_mutation",
            "no_production_ownership_enablement",
            "no_recovery_entry_auto_claim",
            "no_vendor_lock_implementation",
            "no_background_worker_start",
        ],
    }


def build_worker_ownership_auto_claim_policy_contract(
    *,
    explicit_runtime_configuration: bool = False,
    production_gate_ready_required: bool = False,
    durable_ownership_required: bool = False,
    descriptor_evidence_fallback: bool = False,
    idempotency_evidence_ready: bool = False,
    audit_evidence_ready: bool = False,
    entrypoint_allowlist_ready: bool = False,
    entrypoint_allowlist_contract: Dict[str, Any] | None = None,
    enablement_gate_contract: Dict[str, Any] | None = None,
    lease_validation_required: bool = False,
    auto_claim_enabled_by_default: bool = False,
) -> Dict[str, Any]:
    """Describe recovery-entry auto-claim policy without claiming ownership."""

    allowlist_contract = dict(
        entrypoint_allowlist_contract
        or build_worker_ownership_auto_claim_entrypoint_allowlist_contract()
    )
    allowlist_ready = bool(entrypoint_allowlist_ready) or (
        _normalize_text(allowlist_contract.get("overall_status")) == "ready"
        and bool(allowlist_contract.get("ready"))
    )
    enablement_gate = dict(
        enablement_gate_contract
        or build_worker_ownership_explicit_auto_claim_enablement_gate_contract(
            explicit_runtime_configuration=explicit_runtime_configuration,
            production_gate_ready=production_gate_ready_required,
            durable_ownership_ready=durable_ownership_required,
            descriptor_evidence_fallback=descriptor_evidence_fallback,
            idempotency_evidence_ready=idempotency_evidence_ready,
            audit_evidence_ready=audit_evidence_ready,
            lease_validation_ready=lease_validation_required,
            allowed_entrypoints=allowlist_contract.get("allowed_entrypoints")
            if isinstance(allowlist_contract.get("allowed_entrypoints"), list)
            else None,
            requested_entrypoint="submit_approval.approved",
        )
    )
    sections = [
        ("explicit_runtime_configuration", bool(explicit_runtime_configuration)),
        ("production_gate_ready_required", bool(production_gate_ready_required)),
        ("durable_ownership_required", bool(durable_ownership_required)),
        ("descriptor_evidence_fallback", bool(descriptor_evidence_fallback)),
        ("idempotency_evidence", bool(idempotency_evidence_ready)),
        ("audit_evidence", bool(audit_evidence_ready)),
        ("entrypoint_allowlist", allowlist_ready),
        ("lease_validation", bool(lease_validation_required)),
    ]
    missing_sections = [name for name, ready in sections if not ready]
    overall_status = "ready" if not missing_sections else "blocked"
    return {
        "contract_version": WORKER_OWNERSHIP_AUTO_CLAIM_POLICY_CONTRACT_VERSION,
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "auto_claim_enabled_by_default": bool(auto_claim_enabled_by_default)
        and overall_status == "ready",
        "policy": {
            "explicit_runtime_configuration": bool(explicit_runtime_configuration),
            "production_gate_ready_required": bool(production_gate_ready_required),
            "durable_ownership_required": bool(durable_ownership_required),
            "descriptor_evidence_fallback": bool(descriptor_evidence_fallback),
            "idempotency_evidence_ready": bool(idempotency_evidence_ready),
            "audit_evidence_ready": bool(audit_evidence_ready),
            "entrypoint_allowlist_ready": allowlist_ready,
            "entrypoint_allowlist": allowlist_contract,
            "enablement_gate": enablement_gate,
            "lease_validation_required": bool(lease_validation_required),
        },
        "missing_sections": missing_sections,
        "next_allowed_action": (
            "consider_explicit_auto_claim_enablement"
            if overall_status == "ready"
            else "define_explicit_config_gate_durable_descriptor_idempotency_audit_allowlist_and_lease_policy"
        ),
        "non_goals": [
            "no_default_recovery_entry_auto_claim",
            "no_claim_run_side_effect",
            "no_recovery_execution_change",
            "no_background_worker_start",
        ],
    }


def build_worker_ownership_explicit_auto_claim_enablement_gate_contract(
    *,
    explicit_runtime_configuration: bool = False,
    production_gate_ready: bool = False,
    durable_ownership_ready: bool = False,
    descriptor_evidence_fallback: bool = False,
    idempotency_evidence_ready: bool = False,
    audit_evidence_ready: bool = False,
    lease_validation_ready: bool = False,
    rollout_auto_claim_decision_recorded: bool = False,
    requested_entrypoint: str = "submit_approval.approved",
    allowed_entrypoints: list[str] | tuple[str, ...] | None = None,
) -> Dict[str, Any]:
    """Describe explicit recovery auto-claim enablement without claiming ownership."""

    allowed = _normalize_text_list(
        allowed_entrypoints or DEFAULT_WORKER_OWNERSHIP_AUTO_CLAIM_ENTRYPOINTS
    )
    entrypoint = _normalize_text(requested_entrypoint) or "submit_approval.approved"
    entrypoint_allowlisted = entrypoint in allowed
    sections = [
        ("explicit_runtime_configuration", bool(explicit_runtime_configuration)),
        ("production_gate_ready", bool(production_gate_ready)),
        ("durable_ownership", bool(durable_ownership_ready)),
        ("descriptor_evidence_fallback", bool(descriptor_evidence_fallback)),
        ("idempotency_evidence", bool(idempotency_evidence_ready)),
        ("audit_evidence", bool(audit_evidence_ready)),
        ("lease_validation", bool(lease_validation_ready)),
        ("rollout_auto_claim_decision", bool(rollout_auto_claim_decision_recorded)),
        ("entrypoint_allowlisted", entrypoint_allowlisted),
    ]
    missing_sections = [name for name, ready in sections if not ready]
    overall_status = "ready" if not missing_sections else "blocked"
    blocked_reason = ""
    if missing_sections:
        blocked_reason = (
            "entrypoint_not_allowlisted"
            if "entrypoint_allowlisted" in missing_sections
            else f"{missing_sections[0]}_missing"
        )
    return {
        "contract_version": WORKER_OWNERSHIP_EXPLICIT_AUTO_CLAIM_ENABLEMENT_GATE_CONTRACT_VERSION,
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "will_auto_claim": overall_status == "ready",
        "requested_entrypoint": entrypoint,
        "allowed_entrypoints": allowed,
        "missing_sections": missing_sections,
        "blocked_reason": blocked_reason,
        "policy": {
            "explicit_runtime_configuration": bool(explicit_runtime_configuration),
            "production_gate_ready": bool(production_gate_ready),
            "durable_ownership_ready": bool(durable_ownership_ready),
            "descriptor_evidence_fallback": bool(descriptor_evidence_fallback),
            "idempotency_evidence_ready": bool(idempotency_evidence_ready),
            "audit_evidence_ready": bool(audit_evidence_ready),
            "lease_validation_ready": bool(lease_validation_ready),
            "rollout_auto_claim_decision_recorded": bool(
                rollout_auto_claim_decision_recorded
            ),
            "entrypoint_allowlisted": entrypoint_allowlisted,
        },
        "next_allowed_action": (
            "allow_explicit_auto_claim_execution"
            if overall_status == "ready"
            else "complete_explicit_config_production_gate_durable_idempotency_audit_rollout_lease_and_allowlist_evidence"
        ),
        "non_goals": [
            "no_default_recovery_entry_auto_claim",
            "no_claim_run_side_effect",
            "no_recovery_execution_change",
            "no_production_default_enablement",
        ],
    }


def build_worker_ownership_auto_claim_entrypoint_allowlist_contract(
    *,
    allowed_entrypoints: list[str] | tuple[str, ...] | None = None,
    required_entrypoints: list[str] | tuple[str, ...] | None = None,
    default_auto_claim_enabled: bool = False,
    requires_production_gate_ready: bool = True,
) -> Dict[str, Any]:
    """Describe recovery-entry auto-claim entrypoints without authorizing claims."""

    required = _normalize_text_list(
        required_entrypoints or DEFAULT_WORKER_OWNERSHIP_AUTO_CLAIM_ENTRYPOINTS
    )
    allowed = _normalize_text_list(
        allowed_entrypoints or DEFAULT_WORKER_OWNERSHIP_AUTO_CLAIM_ENTRYPOINTS
    )
    missing_entrypoints = [entrypoint for entrypoint in required if entrypoint not in allowed]
    overall_status = "ready" if not missing_entrypoints else "blocked"
    return {
        "contract_version": WORKER_OWNERSHIP_AUTO_CLAIM_ENTRYPOINT_ALLOWLIST_CONTRACT_VERSION,
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "allowed_entrypoints": allowed,
        "required_entrypoints": required,
        "missing_entrypoints": missing_entrypoints,
        "default_auto_claim_enabled": bool(default_auto_claim_enabled)
        and overall_status == "ready",
        "requires_production_gate_ready": bool(requires_production_gate_ready),
        "next_allowed_action": (
            "use_allowlist_as_policy_input_only"
            if overall_status == "ready"
            else "define_required_recovery_entry_auto_claim_entrypoints"
        ),
        "non_goals": [
            "no_default_recovery_entry_auto_claim",
            "no_claim_run_side_effect",
            "no_recovery_execution_change",
            "no_api_endpoint",
        ],
    }


def build_worker_ownership_audit_evidence_contract(
    *,
    compact_ownership_evidence: bool = True,
    operation_history_ready: bool = False,
    recovery_operation_link_ready: bool = False,
    timeline_writer_ready: bool = False,
    idempotent_dedupe_ready: bool = False,
    authorization_source: bool = False,
) -> Dict[str, Any]:
    """Describe ownership audit evidence readiness without authorizing execution."""

    sections = [
        ("compact_ownership_evidence", bool(compact_ownership_evidence)),
        ("operation_history", bool(operation_history_ready)),
        ("recovery_operation_link", bool(recovery_operation_link_ready)),
        ("timeline_writer", bool(timeline_writer_ready)),
        ("idempotent_dedupe", bool(idempotent_dedupe_ready)),
        ("non_authorization_source", not bool(authorization_source)),
    ]
    missing_sections = [name for name, ready in sections if not ready]
    overall_status = "ready" if not missing_sections else "blocked"
    return {
        "contract_version": WORKER_OWNERSHIP_AUDIT_EVIDENCE_CONTRACT_VERSION,
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "authorization_source": bool(authorization_source),
        "evidence": {
            "compact_ownership_evidence": bool(compact_ownership_evidence),
            "operation_history_ready": bool(operation_history_ready),
            "recovery_operation_link_ready": bool(recovery_operation_link_ready),
            "timeline_writer_ready": bool(timeline_writer_ready),
            "idempotent_dedupe_ready": bool(idempotent_dedupe_ready),
            "authorization_source": bool(authorization_source),
        },
        "missing_sections": missing_sections,
        "next_allowed_action": (
            "use_audit_evidence_as_descriptive_signal_only"
            if overall_status == "ready"
            else "connect_operation_history_recovery_link_timeline_writer_and_idempotent_dedupe"
        ),
        "non_goals": [
            "no_audit_writer_side_effect",
            "no_audit_as_authorization_source",
            "no_recovery_execution_change",
            "no_default_worker_ownership_enablement",
        ],
    }


def build_worker_ownership_production_default_enablement_input_source_contract(
    *,
    input_source_kind: str = "",
    request_id: str = "",
    requested_by: str = "",
    requested_at: str = "",
    target_store_mode: str = "",
    rollout_artifact: str = "",
    vendor_lock_decision_id: str = "",
    renewal_lifecycle_reference: str = "",
    auto_claim_decision_reference: str = "",
    audit_evidence_reference: str = "",
    rollback_plan_reference: str = "",
    fallback_policy_reference: str = "",
) -> Dict[str, Any]:
    """Describe the source of a production-default enablement request."""

    normalized_kind = _normalize_text(input_source_kind)
    normalized_request_id = _normalize_text(request_id)
    normalized_requested_by = _normalize_text(requested_by)
    normalized_requested_at = _normalize_text(requested_at)
    normalized_target_mode = _normalize_text(target_store_mode)
    normalized_rollout = _normalize_text(rollout_artifact)
    normalized_vendor_lock = _normalize_text(vendor_lock_decision_id)
    normalized_renewal = _normalize_text(renewal_lifecycle_reference)
    normalized_auto_claim = _normalize_text(auto_claim_decision_reference)
    normalized_audit = _normalize_text(audit_evidence_reference)
    normalized_rollback = _normalize_text(rollback_plan_reference)
    normalized_fallback = _normalize_text(fallback_policy_reference)
    allowed_kinds = {
        "config",
        "ops_decision_record",
        "rollout_artifact",
        "manual_approval",
    }
    allowed_target_modes = {"strict_sql"}
    source_reference_ready = (
        (normalized_kind == "config" and bool(normalized_request_id))
        or (normalized_kind == "ops_decision_record" and bool(normalized_request_id))
        or (normalized_kind == "rollout_artifact" and bool(normalized_rollout))
        or (normalized_kind == "manual_approval" and bool(normalized_request_id))
    )
    sections = [
        ("input_source_kind", normalized_kind in allowed_kinds),
        ("request_id", bool(normalized_request_id)),
        ("requested_by", bool(normalized_requested_by)),
        ("requested_at", bool(normalized_requested_at)),
        ("target_store_mode", normalized_target_mode in allowed_target_modes),
        ("rollout_artifact", bool(normalized_rollout) and source_reference_ready),
        ("vendor_lock_decision", bool(normalized_vendor_lock)),
        ("renewal_lifecycle_reference", bool(normalized_renewal)),
        ("auto_claim_decision_reference", bool(normalized_auto_claim)),
        ("audit_evidence_reference", bool(normalized_audit)),
        ("rollback_plan_reference", bool(normalized_rollback)),
        ("fallback_policy_reference", bool(normalized_fallback)),
    ]
    missing_sections = [name for name, ready in sections if not ready]
    overall_status = "ready" if not missing_sections else "blocked"
    return {
        "contract_version": (
            WORKER_OWNERSHIP_PRODUCTION_DEFAULT_ENABLEMENT_INPUT_SOURCE_CONTRACT_VERSION
        ),
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "input_source_kind": normalized_kind,
        "request_id": normalized_request_id,
        "requested_by": normalized_requested_by,
        "requested_at": normalized_requested_at,
        "target_store_mode": normalized_target_mode,
        "rollout_artifact": normalized_rollout,
        "vendor_lock_decision_id": normalized_vendor_lock,
        "renewal_lifecycle_reference": normalized_renewal,
        "auto_claim_decision_reference": normalized_auto_claim,
        "audit_evidence_reference": normalized_audit,
        "rollback_plan_reference": normalized_rollback,
        "fallback_policy_reference": normalized_fallback,
        "production_default_enablement_authorized": overall_status == "ready",
        "missing_sections": missing_sections,
        "next_allowed_action": (
            "use_enablement_input_source_as_default_enablement_evidence"
            if overall_status == "ready"
            else "record_default_enablement_source_rollout_vendor_lock_renewal_auto_claim_audit_rollback_and_fallback"
        ),
        "non_goals": [
            "no_default_production_ownership_enablement",
            "no_rollout_execution",
            "no_worker_start",
            "no_recovery_entry_auto_claim",
        ],
    }


def build_worker_ownership_postgres_rollout_artifact_consumer_contract(
    *,
    artifact: Dict[str, Any] | None = None,
    source_kind: str = "",
    artifact_id: str = "",
    approved_by: str = "",
    approved_at: str = "",
    target_store_mode: str = "",
    target_backend: str = "",
    lock_adapter_kind: str = "",
    rollout_artifact: str = "",
    vendor_lock_decision_id: str = "",
    renewal_lifecycle_reference: str = "",
    auto_claim_decision_reference: str = "",
    audit_evidence_reference: str = "",
    rollback_plan_reference: str = "",
    fallback_policy_reference: str = "",
    postgres_execution_seam_contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Normalize a caller-owned PostgreSQL rollout artifact into read-only evidence."""

    payload = dict(artifact or {})

    def _payload_text(key: str, fallback: str = "") -> str:
        explicit = _normalize_text(fallback)
        if explicit:
            return explicit
        return _normalize_text(payload.get(key))

    normalized_source_kind = _payload_text("source_kind", source_kind)
    normalized_artifact_id = _payload_text("artifact_id", artifact_id)
    normalized_approved_by = _payload_text("approved_by", approved_by)
    normalized_approved_at = _payload_text("approved_at", approved_at)
    normalized_target_store_mode = _payload_text("target_store_mode", target_store_mode)
    normalized_target_backend = _payload_text("target_backend", target_backend)
    normalized_lock_adapter_kind = _payload_text("lock_adapter_kind", lock_adapter_kind)
    normalized_rollout_artifact = _payload_text("rollout_artifact", rollout_artifact)
    normalized_vendor_lock_decision = _payload_text(
        "vendor_lock_decision_id", vendor_lock_decision_id
    )
    normalized_renewal_lifecycle = _payload_text(
        "renewal_lifecycle_reference", renewal_lifecycle_reference
    )
    normalized_auto_claim_decision = _payload_text(
        "auto_claim_decision_reference", auto_claim_decision_reference
    )
    normalized_audit_evidence = _payload_text(
        "audit_evidence_reference", audit_evidence_reference
    )
    normalized_rollback_plan = _payload_text(
        "rollback_plan_reference", rollback_plan_reference
    )
    normalized_fallback_policy = _payload_text(
        "fallback_policy_reference", fallback_policy_reference
    )
    seam_contract = dict(
        postgres_execution_seam_contract
        or build_worker_ownership_postgres_advisory_lock_execution_seam_contract()
    )
    seam_status = _normalize_text(seam_contract.get("overall_status")) or "blocked"
    input_source_kind = (
        "config" if normalized_source_kind == "runtime_config" else "rollout_artifact"
    )
    enablement_input_source = (
        build_worker_ownership_production_default_enablement_input_source_contract(
            input_source_kind=input_source_kind,
            request_id=normalized_artifact_id,
            requested_by=normalized_approved_by,
            requested_at=normalized_approved_at,
            target_store_mode=normalized_target_store_mode,
            rollout_artifact=normalized_rollout_artifact,
            vendor_lock_decision_id=normalized_vendor_lock_decision,
            renewal_lifecycle_reference=normalized_renewal_lifecycle,
            auto_claim_decision_reference=normalized_auto_claim_decision,
            audit_evidence_reference=normalized_audit_evidence,
            rollback_plan_reference=normalized_rollback_plan,
            fallback_policy_reference=normalized_fallback_policy,
        )
    )
    allowed_source_kinds = {"runtime_config", "rollout_artifact"}
    sections = [
        ("source_kind", normalized_source_kind in allowed_source_kinds),
        ("artifact_id", bool(normalized_artifact_id)),
        ("approved_by", bool(normalized_approved_by)),
        ("approved_at", bool(normalized_approved_at)),
        ("target_store_mode", normalized_target_store_mode == "strict_sql"),
        ("target_backend", normalized_target_backend == "postgres"),
        ("lock_adapter_kind", normalized_lock_adapter_kind == "postgres_advisory_lock"),
        ("rollout_artifact", bool(normalized_rollout_artifact)),
        ("vendor_lock_decision", bool(normalized_vendor_lock_decision)),
        ("renewal_lifecycle_reference", bool(normalized_renewal_lifecycle)),
        ("auto_claim_decision_reference", bool(normalized_auto_claim_decision)),
        ("audit_evidence_reference", bool(normalized_audit_evidence)),
        ("rollback_plan_reference", bool(normalized_rollback_plan)),
        ("fallback_policy_reference", bool(normalized_fallback_policy)),
        ("postgres_execution_seam", seam_status == "ready"),
        (
            "enablement_input_source",
            _normalize_text(enablement_input_source.get("overall_status")) == "ready",
        ),
    ]
    missing_sections = [name for name, ready in sections if not ready]
    overall_status = "ready" if not missing_sections else "blocked"
    return {
        "contract_version": (
            WORKER_OWNERSHIP_POSTGRES_ROLLOUT_ARTIFACT_CONSUMER_CONTRACT_VERSION
        ),
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "source_kind": normalized_source_kind,
        "artifact_id": normalized_artifact_id,
        "approved_by": normalized_approved_by,
        "approved_at": normalized_approved_at,
        "target_store_mode": normalized_target_store_mode,
        "target_backend": normalized_target_backend,
        "lock_adapter_kind": normalized_lock_adapter_kind,
        "rollout_artifact": normalized_rollout_artifact,
        "vendor_lock_decision_id": normalized_vendor_lock_decision,
        "renewal_lifecycle_reference": normalized_renewal_lifecycle,
        "auto_claim_decision_reference": normalized_auto_claim_decision,
        "audit_evidence_reference": normalized_audit_evidence,
        "rollback_plan_reference": normalized_rollback_plan,
        "fallback_policy_reference": normalized_fallback_policy,
        "postgres_execution_seam_required": True,
        "postgres_execution_seam_status": seam_status,
        "postgres_execution_seam_contract_version": _normalize_text(
            seam_contract.get("contract_version")
        ),
        "postgres_execution_seam_missing_sections": list(
            seam_contract.get("missing_sections")
            if isinstance(seam_contract.get("missing_sections"), list)
            else []
        ),
        "enablement_input_source": enablement_input_source,
        "will_enable_production_default": False,
        "executes_advisory_lock": False,
        "sql_row_lease_is_vendor_lock": False,
        "missing_sections": missing_sections,
        "next_allowed_action": (
            "pass_enablement_input_source_to_explicit_strategy_after_all_gates_are_ready"
            if overall_status == "ready"
            else "provide_rollout_artifact_and_ready_postgres_execution_seam_evidence"
        ),
        "non_goals": [
            "no_default_production_ownership_enablement",
            "no_advisory_lock_execution",
            "no_artifact_file_loading",
            "no_runtime_config_fetch",
            "no_recovery_entry_auto_claim",
        ],
    }


def build_worker_ownership_postgres_vendor_lock_target_artifact_binding_contract(
    *,
    artifact: Dict[str, Any] | None = None,
    source_kind: str = "",
    artifact_id: str = "",
    approved_by: str = "",
    approved_at: str = "",
    target_backend: str = "",
    lock_adapter_kind: str = "",
    lock_scope: str = "",
    fencing_strategy: str = "",
    ttl_renewal_strategy: str = "",
    failover_strategy: str = "",
    stale_owner_cleanup_strategy: str = "",
    rollout_artifact: str = "",
    config_key: str = "",
    manual_approval_reference: str = "",
    postgres_rollout_consumer_contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Bind a PostgreSQL rollout artifact to vendor lock target decision evidence."""

    payload = dict(artifact or {})

    def _payload_text(key: str, fallback: str = "") -> str:
        explicit = _normalize_text(fallback)
        if explicit:
            return explicit
        return _normalize_text(payload.get(key))

    normalized_source_kind = _payload_text("source_kind", source_kind)
    normalized_artifact_id = _payload_text("artifact_id", artifact_id)
    normalized_approved_by = _payload_text("approved_by", approved_by)
    normalized_approved_at = _payload_text("approved_at", approved_at)
    normalized_target_backend = _payload_text("target_backend", target_backend)
    normalized_lock_adapter = _payload_text("lock_adapter_kind", lock_adapter_kind)
    normalized_lock_scope = _payload_text("lock_scope", lock_scope)
    normalized_fencing = _payload_text("fencing_strategy", fencing_strategy)
    normalized_ttl = _payload_text("ttl_renewal_strategy", ttl_renewal_strategy)
    normalized_failover = _payload_text("failover_strategy", failover_strategy)
    normalized_cleanup = _payload_text(
        "stale_owner_cleanup_strategy", stale_owner_cleanup_strategy
    )
    normalized_rollout_artifact = _payload_text("rollout_artifact", rollout_artifact)
    normalized_config_key = _payload_text("config_key", config_key)
    normalized_manual_ref = _payload_text(
        "manual_approval_reference", manual_approval_reference
    )
    consumer = dict(
        postgres_rollout_consumer_contract
        or build_worker_ownership_postgres_rollout_artifact_consumer_contract(
            artifact=payload
        )
    )
    consumer_status = _normalize_text(consumer.get("overall_status")) or "blocked"
    input_source_kind = (
        "config" if normalized_source_kind == "runtime_config" else "rollout_artifact"
    )
    target_input = build_worker_ownership_vendor_lock_target_decision_input_contract(
        input_source_kind=input_source_kind,
        decision_id=normalized_artifact_id,
        approved_by=normalized_approved_by,
        approved_at=normalized_approved_at,
        target_backend=normalized_target_backend,
        lock_adapter_kind=normalized_lock_adapter,
        rollout_artifact=normalized_rollout_artifact,
        config_key=normalized_config_key,
        manual_approval_reference=normalized_manual_ref,
        sql_row_lease_is_vendor_lock=False,
    )
    target_decision = build_worker_ownership_vendor_lock_target_decision_contract(
        decision_recorded=True,
        target_backend=normalized_target_backend,
        lock_adapter_kind=normalized_lock_adapter,
        lock_scope=normalized_lock_scope,
        fencing_strategy=normalized_fencing,
        ttl_renewal_strategy=normalized_ttl,
        failover_strategy=normalized_failover,
        stale_owner_cleanup_strategy=normalized_cleanup,
        sql_row_lease_is_vendor_lock=False,
        production_lock_allowed=True,
        input_source_contract=target_input,
    )
    allowed_source_kinds = {"runtime_config", "rollout_artifact"}
    sections = [
        ("source_kind", normalized_source_kind in allowed_source_kinds),
        ("artifact_id", bool(normalized_artifact_id)),
        ("approved_by", bool(normalized_approved_by)),
        ("approved_at", bool(normalized_approved_at)),
        ("target_backend", normalized_target_backend == "postgres"),
        ("lock_adapter_kind", normalized_lock_adapter == "postgres_advisory_lock"),
        ("lock_scope", bool(normalized_lock_scope)),
        ("fencing_strategy", bool(normalized_fencing)),
        ("ttl_renewal_strategy", bool(normalized_ttl)),
        ("failover_strategy", bool(normalized_failover)),
        ("stale_owner_cleanup_strategy", bool(normalized_cleanup)),
        (
            "source_reference",
            bool(normalized_rollout_artifact)
            or bool(normalized_config_key)
            or bool(normalized_manual_ref),
        ),
        ("postgres_rollout_consumer", consumer_status == "ready"),
        (
            "target_decision_input",
            _normalize_text(target_input.get("overall_status")) == "ready",
        ),
        (
            "target_decision",
            _normalize_text(target_decision.get("overall_status")) == "ready",
        ),
        ("sql_row_lease_not_vendor_lock", True),
    ]
    missing_sections = [name for name, ready in sections if not ready]
    overall_status = "ready" if not missing_sections else "blocked"
    return {
        "contract_version": (
            WORKER_OWNERSHIP_POSTGRES_VENDOR_LOCK_TARGET_ARTIFACT_BINDING_CONTRACT_VERSION
        ),
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "source_kind": normalized_source_kind,
        "artifact_id": normalized_artifact_id,
        "approved_by": normalized_approved_by,
        "approved_at": normalized_approved_at,
        "target_backend": normalized_target_backend,
        "lock_adapter_kind": normalized_lock_adapter,
        "lock_scope": normalized_lock_scope,
        "fencing_strategy": normalized_fencing,
        "ttl_renewal_strategy": normalized_ttl,
        "failover_strategy": normalized_failover,
        "stale_owner_cleanup_strategy": normalized_cleanup,
        "rollout_artifact": normalized_rollout_artifact,
        "config_key": normalized_config_key,
        "manual_approval_reference": normalized_manual_ref,
        "postgres_rollout_consumer_status": consumer_status,
        "postgres_rollout_consumer_contract_version": _normalize_text(
            consumer.get("contract_version")
        ),
        "postgres_rollout_consumer_missing_sections": list(
            consumer.get("missing_sections")
            if isinstance(consumer.get("missing_sections"), list)
            else []
        ),
        "target_decision_input": target_input,
        "target_decision": target_decision,
        "will_enable_production_lock": False,
        "executes_advisory_lock": False,
        "sql_row_lease_is_vendor_lock": False,
        "missing_sections": missing_sections,
        "next_allowed_action": (
            "pass_target_decision_to_vendor_lock_semantics_after_all_gates_are_ready"
            if overall_status == "ready"
            else "provide_postgres_rollout_artifact_target_decision_and_ready_consumer_evidence"
        ),
        "non_goals": [
            "no_default_production_ownership_enablement",
            "no_production_lock_enablement",
            "no_advisory_lock_execution",
            "no_artifact_file_loading",
            "no_recovery_entry_auto_claim",
        ],
    }


def build_worker_ownership_postgres_vendor_lock_semantics_binding_contract(
    *,
    target_artifact_binding_contract: Dict[str, Any] | None = None,
    postgres_execution_seam_contract: Dict[str, Any] | None = None,
    postgres_probe_contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Assemble PostgreSQL vendor lock semantics evidence without enabling it."""

    target_binding = dict(
        target_artifact_binding_contract
        or build_worker_ownership_postgres_vendor_lock_target_artifact_binding_contract()
    )
    target_decision = dict(target_binding.get("target_decision") or {})
    target_binding_status = _normalize_text(target_binding.get("overall_status")) or "blocked"
    target_decision_status = _normalize_text(target_decision.get("overall_status")) or "blocked"
    normalized_backend = _normalize_text(
        target_binding.get("target_backend") or target_decision.get("target_backend")
    )
    normalized_adapter = _normalize_text(
        target_binding.get("lock_adapter_kind") or target_decision.get("lock_adapter_kind")
    )
    normalized_scope = _normalize_text(
        target_binding.get("lock_scope") or target_decision.get("lock_scope")
    )
    normalized_fencing = _normalize_text(
        target_binding.get("fencing_strategy") or target_decision.get("fencing_strategy")
    )
    normalized_ttl = _normalize_text(
        target_binding.get("ttl_renewal_strategy")
        or target_decision.get("ttl_renewal_strategy")
    )
    normalized_failover = _normalize_text(
        target_binding.get("failover_strategy") or target_decision.get("failover_strategy")
    )
    normalized_cleanup = _normalize_text(
        target_binding.get("stale_owner_cleanup_strategy")
        or target_decision.get("stale_owner_cleanup_strategy")
    )
    execution_seam = dict(
        postgres_execution_seam_contract
        or build_worker_ownership_postgres_advisory_lock_execution_seam_contract()
    )
    execution_seam_status = _normalize_text(execution_seam.get("overall_status")) or "blocked"
    probe = dict(
        postgres_probe_contract
        or build_worker_ownership_postgres_vendor_lock_probe_contract(
            advisory_lock_family="pg_try_advisory_lock" if normalized_backend == "postgres" else "",
            lock_key_derivation="hash_run_id_to_bigint" if normalized_backend == "postgres" else "",
            lock_scope="session" if normalized_backend == "postgres" else "",
            fencing_token_binding=(
                "lease_fencing_token" if normalized_fencing else ""
            ),
            ttl_renewal_strategy=(
                "heartbeat_validates_session_lock" if normalized_ttl else ""
            ),
            failover_behavior=(
                "session_disconnect_releases_lock" if normalized_failover else ""
            ),
            stale_owner_cleanup_strategy=(
                "connection_pool_reaper" if normalized_cleanup else ""
            ),
            probe_safety="metadata_only" if normalized_backend == "postgres" else "",
            execution_seam_contract=execution_seam,
        )
    )
    probe_status = _normalize_text(probe.get("overall_status")) or "blocked"
    adapter = build_worker_ownership_vendor_lock_adapter_contract(
        adapter_kind=normalized_adapter,
        target_backend=normalized_backend,
        lock_scope=normalized_scope,
        fencing_strategy=normalized_fencing,
        ttl_renewal_strategy=normalized_ttl,
        failover_strategy=normalized_failover,
        stale_owner_cleanup_strategy=normalized_cleanup,
        acquire_supported=execution_seam_status == "ready",
        renew_supported=execution_seam_status == "ready",
        release_supported=execution_seam_status == "ready",
        probe_supported=probe_status == "ready",
        production_lock_allowed=True,
        sql_row_lease_is_vendor_lock=False,
        backend_probe=probe,
    )
    adapter_status = _normalize_text(adapter.get("overall_status")) or "blocked"
    semantics = build_worker_ownership_vendor_lock_semantics_contract(
        current_posture=(
            "postgres_advisory_lock_candidate"
            if adapter_status == "ready"
            else "sql_row_lease_fencing"
        ),
        sql_row_lease_fencing=True,
        vendor_lock_adapter_present=adapter_status == "ready",
        lock_scope_defined=bool(normalized_scope),
        fencing_guarantee_defined=bool(normalized_fencing),
        failover_semantics_defined=bool(normalized_failover),
        ttl_renewal_semantics_defined=bool(normalized_ttl),
        stale_owner_cleanup_defined=bool(normalized_cleanup),
        production_lock_allowed=True,
        lock_adapter_kind=normalized_adapter,
        lock_scope=normalized_scope,
        target_decision_contract=target_decision,
        adapter_contract=adapter,
    )
    semantics_status = _normalize_text(semantics.get("overall_status")) or "blocked"
    sections = [
        ("target_artifact_binding", target_binding_status == "ready"),
        ("target_decision", target_decision_status == "ready"),
        ("postgres_execution_seam", execution_seam_status == "ready"),
        ("postgres_probe", probe_status == "ready"),
        ("vendor_lock_adapter", adapter_status == "ready"),
        ("vendor_lock_semantics", semantics_status == "ready"),
        ("target_backend", normalized_backend == "postgres"),
        ("lock_adapter_kind", normalized_adapter == "postgres_advisory_lock"),
        ("sql_row_lease_not_vendor_lock", True),
    ]
    missing_sections = [name for name, ready in sections if not ready]
    overall_status = "ready" if not missing_sections else "blocked"
    return {
        "contract_version": (
            WORKER_OWNERSHIP_POSTGRES_VENDOR_LOCK_SEMANTICS_BINDING_CONTRACT_VERSION
        ),
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "target_binding_status": target_binding_status,
        "target_binding_contract_version": _normalize_text(
            target_binding.get("contract_version")
        ),
        "target_binding_missing_sections": list(
            target_binding.get("missing_sections")
            if isinstance(target_binding.get("missing_sections"), list)
            else []
        ),
        "target_decision_status": target_decision_status,
        "postgres_execution_seam_status": execution_seam_status,
        "postgres_probe_status": probe_status,
        "vendor_lock_adapter_status": adapter_status,
        "vendor_lock_semantics_status": semantics_status,
        "target_backend": normalized_backend,
        "lock_adapter_kind": normalized_adapter,
        "lock_scope": normalized_scope,
        "fencing_strategy": normalized_fencing,
        "ttl_renewal_strategy": normalized_ttl,
        "failover_strategy": normalized_failover,
        "stale_owner_cleanup_strategy": normalized_cleanup,
        "postgres_probe": probe,
        "vendor_lock_adapter": adapter,
        "vendor_lock_semantics": semantics,
        "will_enable_production_lock": False,
        "will_update_production_gate": False,
        "executes_advisory_lock": False,
        "sql_row_lease_is_vendor_lock": False,
        "missing_sections": missing_sections,
        "next_allowed_action": (
            "review_candidate_before_explicit_production_gate_wiring"
            if overall_status == "ready"
            else "provide_ready_postgres_target_binding_and_execution_seam_evidence"
        ),
        "non_goals": [
            "no_default_production_ownership_enablement",
            "no_production_gate_update",
            "no_advisory_lock_execution",
            "no_postgres_connection",
            "no_recovery_entry_auto_claim",
        ],
    }


def build_worker_ownership_postgres_vendor_lock_production_gate_wiring_decision_contract(
    *,
    semantics_binding_contract: Dict[str, Any] | None = None,
    decision_recorded: bool = False,
    decision_id: str = "",
    approved_by: str = "",
    approved_at: str = "",
    production_rollout_confirmed: bool = False,
    rollback_plan_reference: str = "",
    fallback_policy_reference: str = "",
) -> Dict[str, Any]:
    """Record explicit approval to use a PostgreSQL semantics candidate later."""

    semantics_binding = dict(
        semantics_binding_contract
        or build_worker_ownership_postgres_vendor_lock_semantics_binding_contract()
    )
    semantics_candidate = dict(semantics_binding.get("vendor_lock_semantics") or {})
    binding_status = _normalize_text(semantics_binding.get("overall_status")) or "blocked"
    candidate_status = _normalize_text(semantics_candidate.get("overall_status")) or "blocked"
    normalized_decision_id = _normalize_text(decision_id)
    normalized_approved_by = _normalize_text(approved_by)
    normalized_approved_at = _normalize_text(approved_at)
    normalized_rollback = _normalize_text(rollback_plan_reference)
    normalized_fallback = _normalize_text(fallback_policy_reference)
    normalized_backend = _normalize_text(semantics_binding.get("target_backend"))
    normalized_adapter = _normalize_text(semantics_binding.get("lock_adapter_kind"))
    sections = [
        ("semantics_binding", binding_status == "ready"),
        ("vendor_lock_semantics_candidate", candidate_status == "ready"),
        ("decision_recorded", bool(decision_recorded)),
        ("decision_id", bool(normalized_decision_id)),
        ("approved_by", bool(normalized_approved_by)),
        ("approved_at", bool(normalized_approved_at)),
        ("production_rollout_confirmed", bool(production_rollout_confirmed)),
        ("rollback_plan_reference", bool(normalized_rollback)),
        ("fallback_policy_reference", bool(normalized_fallback)),
        ("target_backend", normalized_backend == "postgres"),
        ("lock_adapter_kind", normalized_adapter == "postgres_advisory_lock"),
        ("sql_row_lease_not_vendor_lock", True),
    ]
    missing_sections = [name for name, ready in sections if not ready]
    overall_status = "ready" if not missing_sections else "blocked"
    wiring_allowed = overall_status == "ready"
    return {
        "contract_version": (
            WORKER_OWNERSHIP_POSTGRES_VENDOR_LOCK_PRODUCTION_GATE_WIRING_DECISION_CONTRACT_VERSION
        ),
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "decision_recorded": bool(decision_recorded),
        "decision_id": normalized_decision_id,
        "approved_by": normalized_approved_by,
        "approved_at": normalized_approved_at,
        "semantics_binding_status": binding_status,
        "semantics_binding_contract_version": _normalize_text(
            semantics_binding.get("contract_version")
        ),
        "candidate_semantics_status": candidate_status,
        "target_backend": normalized_backend,
        "lock_adapter_kind": normalized_adapter,
        "production_rollout_confirmed": bool(production_rollout_confirmed),
        "rollback_plan_reference": normalized_rollback,
        "fallback_policy_reference": normalized_fallback,
        "wiring_allowed": wiring_allowed,
        "will_update_production_gate": False,
        "will_enable_production_lock": False,
        "executes_advisory_lock": False,
        "sql_row_lease_is_vendor_lock": False,
        "semantics_binding": semantics_binding,
        "vendor_lock_semantics_candidate": semantics_candidate,
        "missing_sections": missing_sections,
        "next_allowed_action": (
            "use_as_explicit_input_to_future_production_gate_wiring"
            if wiring_allowed
            else "record_wiring_decision_approval_rollout_rollback_and_fallback_evidence"
        ),
        "non_goals": [
            "no_default_production_gate_update",
            "no_default_production_ownership_enablement",
            "no_production_lock_enablement",
            "no_advisory_lock_execution",
            "no_recovery_entry_auto_claim",
        ],
    }


def build_worker_ownership_production_enablement_strategy_contract(
    *,
    section_readiness: Dict[str, bool] | None = None,
    production_default_enabled_requested: bool = False,
    enablement_input_source_contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Describe the final production-default enablement decision without enabling it."""

    readiness = {
        str(name or "").strip(): bool(ready)
        for name, ready in dict(section_readiness or {}).items()
        if str(name or "").strip()
    }
    required_sections = [
        "durable_ownership_store",
        "vendor_lock_semantics",
        "heartbeat_renewal_supervisor",
        "migration_checklist",
        "rollout_checklist",
        "recovery_entry_auto_claim_policy",
        "stale_fencing_fail_closed",
        "ownership_audit_evidence",
    ]
    input_source = dict(
        enablement_input_source_contract
        or build_worker_ownership_production_default_enablement_input_source_contract()
    )
    input_source_ready = _normalize_text(input_source.get("overall_status")) == "ready"
    blocking_sections = [name for name in required_sections if not readiness.get(name)]
    if not input_source_ready:
        blocking_sections.append("production_default_enablement_input_source")
    explicit_enablement_requested = bool(production_default_enabled_requested)
    production_default_allowed = not blocking_sections and explicit_enablement_requested
    overall_status = "ready" if production_default_allowed else "blocked"
    return {
        "contract_version": WORKER_OWNERSHIP_PRODUCTION_ENABLEMENT_STRATEGY_CONTRACT_VERSION,
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "production_default_enabled_requested": explicit_enablement_requested,
        "production_default_allowed": production_default_allowed,
        "required_sections": required_sections,
        "blocking_sections": blocking_sections,
        "input_source": input_source,
        "policy": {
            "explicit_enablement_required": True,
            "all_required_sections_ready": not blocking_sections,
            "input_source_ready": input_source_ready,
            "fail_closed_when_blocked": True,
            "sql_row_lease_is_not_default_authority": True,
        },
        "next_allowed_action": (
            "allow_explicit_production_default_enablement"
            if production_default_allowed
            else "resolve_blocking_sections_and_request_explicit_default_enablement"
        ),
        "non_goals": [
            "no_implicit_production_default_enablement",
            "no_sql_row_lease_as_default_authority",
            "no_worker_start",
            "no_recovery_execution_change",
        ],
    }


def build_worker_ownership_production_gate_composition_dry_run_contract(
    *,
    vendor_lock_wiring_decision_contract: Dict[str, Any] | None = None,
    renewal_supervisor_contract: Dict[str, Any] | None = None,
    rollout_confirmation_decision_contract: Dict[str, Any] | None = None,
    auto_claim_enablement_gate_contract: Dict[str, Any] | None = None,
    ownership_audit_evidence_contract: Dict[str, Any] | None = None,
    production_default_enablement_input_source_contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Compose production gate readiness evidence without enabling production."""

    wiring = dict(
        vendor_lock_wiring_decision_contract
        or build_worker_ownership_postgres_vendor_lock_production_gate_wiring_decision_contract()
    )
    renewal = dict(
        renewal_supervisor_contract
        or build_worker_ownership_renewal_supervisor_contract(
            heartbeat_operation_present=True,
            renew_once_supported=True,
            owner_identity_required=True,
            controlled_lifecycle_supported=True,
            starts_by_default=False,
            active=False,
            stop_supported=True,
            failure_fail_closed=True,
            ttl_interval_policy_present=True,
            lease_loss_fail_closed=True,
        )
    )
    rollout = dict(
        rollout_confirmation_decision_contract
        or build_worker_ownership_rollout_confirmation_decision_contract()
    )
    auto_claim = dict(
        auto_claim_enablement_gate_contract
        or build_worker_ownership_explicit_auto_claim_enablement_gate_contract()
    )
    audit = dict(
        ownership_audit_evidence_contract
        or build_worker_ownership_audit_evidence_contract()
    )
    enablement_input = dict(
        production_default_enablement_input_source_contract
        or build_worker_ownership_production_default_enablement_input_source_contract()
    )
    section_readiness = {
        "vendor_lock_wiring_decision": (
            _normalize_text(wiring.get("overall_status")) == "ready"
            and bool(wiring.get("wiring_allowed"))
            and not bool(wiring.get("will_update_production_gate"))
            and not bool(wiring.get("will_enable_production_lock"))
            and not bool(wiring.get("executes_advisory_lock"))
        ),
        "heartbeat_renewal_supervisor": (
            _normalize_text(renewal.get("overall_status")) == "ready"
            and bool(renewal.get("supervisor_enabled_by_default"))
            and bool((renewal.get("policy") or {}).get("controlled_lifecycle_supported"))
            and bool((renewal.get("policy") or {}).get("failure_fail_closed"))
        ),
        "rollout_confirmation": (
            _normalize_text(rollout.get("overall_status")) == "ready"
            and bool(rollout.get("production_rollout_confirmed"))
        ),
        "recovery_entry_auto_claim_enablement": (
            _normalize_text(auto_claim.get("overall_status")) == "ready"
            and bool(auto_claim.get("will_auto_claim"))
        ),
        "ownership_audit_evidence": (
            _normalize_text(audit.get("overall_status")) == "ready"
            and not bool(audit.get("authorization_source"))
        ),
        "production_default_enablement_input_source": (
            _normalize_text(enablement_input.get("overall_status")) == "ready"
            and bool(enablement_input.get("production_default_enablement_authorized"))
        ),
    }
    missing_sections = [
        name for name, ready in section_readiness.items() if not ready
    ]
    blocking_reasons = [
        f"{name}_blocked" for name in missing_sections
    ]
    all_required_sections_ready = not missing_sections
    overall_status = "ready" if all_required_sections_ready else "blocked"
    production_default_would_be_allowed = all_required_sections_ready
    return {
        "contract_version": (
            WORKER_OWNERSHIP_PRODUCTION_GATE_COMPOSITION_DRY_RUN_CONTRACT_VERSION
        ),
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "all_required_sections_ready": all_required_sections_ready,
        "production_default_would_be_allowed": production_default_would_be_allowed,
        "required_sections": list(section_readiness.keys()),
        "missing_sections": missing_sections,
        "blocking_reasons": blocking_reasons,
        "will_enable_production_default": False,
        "executes_lock": False,
        "starts_background_worker": False,
        "runs_recovery_auto_claim": False,
        "evidence": {
            "vendor_lock_wiring_decision_status": _normalize_text(
                wiring.get("overall_status")
            )
            or "blocked",
            "vendor_lock_wiring_allowed": bool(wiring.get("wiring_allowed")),
            "vendor_lock_will_update_gate": bool(
                wiring.get("will_update_production_gate")
            ),
            "vendor_lock_will_enable_lock": bool(
                wiring.get("will_enable_production_lock")
            ),
            "vendor_lock_executes_lock": bool(wiring.get("executes_advisory_lock")),
            "renewal_supervisor_status": _normalize_text(
                renewal.get("overall_status")
            )
            or "blocked",
            "renewal_supervisor_enabled_by_default": bool(
                renewal.get("supervisor_enabled_by_default")
            ),
            "renewal_controlled_lifecycle_supported": bool(
                (renewal.get("policy") or {}).get("controlled_lifecycle_supported")
            ),
            "renewal_failure_fail_closed": bool(
                (renewal.get("policy") or {}).get("failure_fail_closed")
            ),
            "rollout_confirmation_status": _normalize_text(
                rollout.get("overall_status")
            )
            or "blocked",
            "production_rollout_confirmed": bool(
                rollout.get("production_rollout_confirmed")
            ),
            "auto_claim_enablement_gate_status": _normalize_text(
                auto_claim.get("overall_status")
            )
            or "blocked",
            "auto_claim_will_auto_claim": bool(auto_claim.get("will_auto_claim")),
            "ownership_audit_status": _normalize_text(audit.get("overall_status"))
            or "blocked",
            "ownership_audit_authorization_source": bool(
                audit.get("authorization_source")
            ),
            "enablement_input_source_status": _normalize_text(
                enablement_input.get("overall_status")
            )
            or "blocked",
            "enablement_input_source_authorized": bool(
                enablement_input.get("production_default_enablement_authorized")
            ),
        },
        "inputs": {
            "vendor_lock_wiring_decision": wiring,
            "renewal_supervisor": renewal,
            "rollout_confirmation": rollout,
            "auto_claim_enablement_gate": auto_claim,
            "ownership_audit_evidence": audit,
            "production_default_enablement_input_source": enablement_input,
        },
        "next_allowed_action": (
            "use_dry_run_as_input_to_future_explicit_enablement_execution_seam"
            if all_required_sections_ready
            else "complete_required_worker_ownership_production_readiness_evidence"
        ),
        "non_goals": [
            "no_default_production_ownership_enablement",
            "no_advisory_lock_execution",
            "no_background_worker_start",
            "no_recovery_entry_auto_claim",
            "no_durable_recovery_gate_unblock",
        ],
    }


def build_worker_ownership_production_enablement_runtime_config_consumer_contract(
    *,
    config: Dict[str, Any] | None = None,
    source_kind: str = "",
    config_id: str = "",
    approved_by: str = "",
    approved_at: str = "",
    target_store_mode: str = "",
    target_backend: str = "",
    lock_adapter_kind: str = "",
    rollout_artifact: str = "",
    vendor_lock_decision_id: str = "",
    renewal_lifecycle_reference: str = "",
    auto_claim_decision_reference: str = "",
    audit_evidence_reference: str = "",
    rollback_plan_reference: str = "",
    fallback_policy_reference: str = "",
    composition_dry_run_contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Normalize caller-owned production enablement config into read-only evidence."""

    payload = dict(config or {})

    def _payload_text(key: str, fallback: str = "") -> str:
        explicit = _normalize_text(fallback)
        if explicit:
            return explicit
        return _normalize_text(payload.get(key))

    normalized_source_kind = _payload_text("source_kind", source_kind)
    normalized_config_id = _payload_text("config_id", config_id)
    normalized_approved_by = _payload_text("approved_by", approved_by)
    normalized_approved_at = _payload_text("approved_at", approved_at)
    normalized_target_store_mode = _payload_text("target_store_mode", target_store_mode)
    normalized_target_backend = _payload_text("target_backend", target_backend)
    normalized_lock_adapter_kind = _payload_text("lock_adapter_kind", lock_adapter_kind)
    normalized_rollout_artifact = _payload_text("rollout_artifact", rollout_artifact)
    normalized_vendor_lock_decision = _payload_text(
        "vendor_lock_decision_id", vendor_lock_decision_id
    )
    normalized_renewal_lifecycle = _payload_text(
        "renewal_lifecycle_reference", renewal_lifecycle_reference
    )
    normalized_auto_claim_decision = _payload_text(
        "auto_claim_decision_reference", auto_claim_decision_reference
    )
    normalized_audit_evidence = _payload_text(
        "audit_evidence_reference", audit_evidence_reference
    )
    normalized_rollback_plan = _payload_text(
        "rollback_plan_reference", rollback_plan_reference
    )
    normalized_fallback_policy = _payload_text(
        "fallback_policy_reference", fallback_policy_reference
    )
    input_source_kind = (
        "rollout_artifact"
        if normalized_source_kind == "rollout_artifact"
        else "config"
    )
    enablement_input_source = (
        build_worker_ownership_production_default_enablement_input_source_contract(
            input_source_kind=input_source_kind,
            request_id=normalized_config_id,
            requested_by=normalized_approved_by,
            requested_at=normalized_approved_at,
            target_store_mode=normalized_target_store_mode,
            rollout_artifact=normalized_rollout_artifact,
            vendor_lock_decision_id=normalized_vendor_lock_decision,
            renewal_lifecycle_reference=normalized_renewal_lifecycle,
            auto_claim_decision_reference=normalized_auto_claim_decision,
            audit_evidence_reference=normalized_audit_evidence,
            rollback_plan_reference=normalized_rollback_plan,
            fallback_policy_reference=normalized_fallback_policy,
        )
    )
    dry_run = dict(
        composition_dry_run_contract
        or build_worker_ownership_production_gate_composition_dry_run_contract(
            production_default_enablement_input_source_contract=enablement_input_source
        )
    )
    allowed_source_kinds = {
        "runtime_config",
        "rollout_artifact",
        "ops_decision_record",
        "manual_approval",
    }
    sections = [
        ("source_kind", normalized_source_kind in allowed_source_kinds),
        ("config_id", bool(normalized_config_id)),
        ("approved_by", bool(normalized_approved_by)),
        ("approved_at", bool(normalized_approved_at)),
        ("target_store_mode", normalized_target_store_mode == "strict_sql"),
        ("target_backend", normalized_target_backend == "postgres"),
        ("lock_adapter_kind", normalized_lock_adapter_kind == "postgres_advisory_lock"),
        ("rollout_artifact", bool(normalized_rollout_artifact)),
        ("vendor_lock_decision", bool(normalized_vendor_lock_decision)),
        ("renewal_lifecycle_reference", bool(normalized_renewal_lifecycle)),
        ("auto_claim_decision_reference", bool(normalized_auto_claim_decision)),
        ("audit_evidence_reference", bool(normalized_audit_evidence)),
        ("rollback_plan_reference", bool(normalized_rollback_plan)),
        ("fallback_policy_reference", bool(normalized_fallback_policy)),
        (
            "enablement_input_source",
            _normalize_text(enablement_input_source.get("overall_status")) == "ready",
        ),
        ("composition_dry_run", _normalize_text(dry_run.get("overall_status")) == "ready"),
    ]
    missing_sections = [name for name, ready in sections if not ready]
    overall_status = "ready" if not missing_sections else "blocked"
    return {
        "contract_version": (
            WORKER_OWNERSHIP_PRODUCTION_ENABLEMENT_RUNTIME_CONFIG_CONSUMER_CONTRACT_VERSION
        ),
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "source_kind": normalized_source_kind,
        "config_id": normalized_config_id,
        "approved_by": normalized_approved_by,
        "approved_at": normalized_approved_at,
        "target_store_mode": normalized_target_store_mode,
        "target_backend": normalized_target_backend,
        "lock_adapter_kind": normalized_lock_adapter_kind,
        "rollout_artifact": normalized_rollout_artifact,
        "vendor_lock_decision_id": normalized_vendor_lock_decision,
        "renewal_lifecycle_reference": normalized_renewal_lifecycle,
        "auto_claim_decision_reference": normalized_auto_claim_decision,
        "audit_evidence_reference": normalized_audit_evidence,
        "rollback_plan_reference": normalized_rollback_plan,
        "fallback_policy_reference": normalized_fallback_policy,
        "enablement_input_source": enablement_input_source,
        "composition_dry_run": dry_run,
        "composition_dry_run_status": _normalize_text(dry_run.get("overall_status"))
        or "blocked",
        "composition_dry_run_would_allow": bool(
            dry_run.get("production_default_would_be_allowed")
        ),
        "will_enable_production_default": False,
        "executes_lock": False,
        "starts_background_worker": False,
        "runs_recovery_auto_claim": False,
        "missing_sections": missing_sections,
        "next_allowed_action": (
            "pass_consumer_evidence_to_future_explicit_enablement_execution_seam"
            if overall_status == "ready"
            else "provide_runtime_config_enablement_metadata_and_ready_dry_run_evidence"
        ),
        "non_goals": [
            "no_file_or_remote_config_read",
            "no_environment_mutation",
            "no_default_production_ownership_enablement",
            "no_advisory_lock_execution",
            "no_background_worker_start",
            "no_recovery_entry_auto_claim",
        ],
    }


def build_worker_ownership_production_gate_contract(
    *,
    ownership_contract: Dict[str, Any] | None = None,
    store_mode: str = "memory_only",
    migration_ready: bool = False,
    vendor_lock_semantics_ready: bool = False,
    vendor_lock_semantics_contract: Dict[str, Any] | None = None,
    renewal_supervisor_ready: bool = False,
    renewal_supervisor_contract: Dict[str, Any] | None = None,
    rollout_checklist_ready: bool = False,
    rollout_readiness_contract: Dict[str, Any] | None = None,
    recovery_entry_auto_claim_policy_ready: bool = False,
    auto_claim_policy_contract: Dict[str, Any] | None = None,
    audit_evidence_ready: bool = False,
    audit_evidence_contract: Dict[str, Any] | None = None,
    production_default_enabled: bool = False,
) -> Dict[str, Any]:
    """Describe production-default ownership readiness without enabling it."""

    contract = dict(ownership_contract or {})
    adapter_kind = _normalize_text(contract.get("adapter_kind")) or "in_memory"
    durable = bool(contract.get("durable"))
    fallback_active = bool(contract.get("fallback_active"))
    normalized_mode = _normalize_text(store_mode).lower() or "memory_only"
    operations = set(contract.get("operations") or [])
    stale_fencing_ready = (
        "validate_ownership" in operations
        and WORKER_OWNERSHIP_REASON_STALE_FENCING_TOKEN in set(contract.get("fail_closed_reasons") or [])
    )
    vendor_lock_contract = dict(
        vendor_lock_semantics_contract
        or build_worker_ownership_vendor_lock_semantics_contract(
            current_posture="sql_row_lease_fencing" if durable else "local_preview_only",
            sql_row_lease_fencing=durable,
            vendor_lock_adapter_present=vendor_lock_semantics_ready,
            lock_scope_defined=vendor_lock_semantics_ready,
            fencing_guarantee_defined=vendor_lock_semantics_ready,
            failover_semantics_defined=vendor_lock_semantics_ready,
            ttl_renewal_semantics_defined=vendor_lock_semantics_ready,
            stale_owner_cleanup_defined=vendor_lock_semantics_ready,
            production_lock_allowed=False,
        )
    )
    vendor_lock_policy = dict(vendor_lock_contract.get("policy") or {})
    vendor_lock_adapter_contract = dict(vendor_lock_policy.get("adapter_contract") or {})
    vendor_lock_adapter_backend_probe = dict(
        vendor_lock_adapter_contract.get("backend_probe") or {}
    )
    vendor_lock_postgres_execution_seam = dict(
        vendor_lock_adapter_backend_probe.get("execution_seam") or {}
    )
    vendor_lock_postgres_execution_policy = dict(
        vendor_lock_postgres_execution_seam.get("policy") or {}
    )
    vendor_lock_target_decision = dict(vendor_lock_policy.get("target_decision") or {})
    vendor_lock_target_input_source = dict(
        vendor_lock_target_decision.get("input_source") or {}
    )
    vendor_lock_status = _normalize_text(vendor_lock_contract.get("overall_status")) or "blocked"
    vendor_lock_allowed = bool(vendor_lock_contract.get("production_lock_allowed"))
    vendor_lock_section_ready = vendor_lock_status == "ready" and vendor_lock_allowed
    vendor_lock_missing_sections = (
        vendor_lock_contract.get("missing_sections")
        if isinstance(vendor_lock_contract.get("missing_sections"), list)
        else []
    )
    renewal_contract = dict(
        renewal_supervisor_contract
        or build_worker_ownership_renewal_supervisor_contract(
            heartbeat_operation_present="heartbeat" in operations,
            renew_once_supported="heartbeat" in operations and "validate_ownership" in operations,
            owner_identity_required=True,
            controlled_lifecycle_supported=True,
            starts_by_default=False,
            active=False,
            stop_supported=True,
            failure_fail_closed=True,
            ttl_interval_policy_present=True,
            lease_loss_fail_closed=WORKER_OWNERSHIP_REASON_LEASE_EXPIRED
            in set(contract.get("fail_closed_reasons") or []),
        )
    )
    renewal_policy = dict(renewal_contract.get("policy") or {})
    renewal_status = _normalize_text(renewal_contract.get("overall_status")) or "blocked"
    renewal_enabled_by_default = bool(renewal_contract.get("supervisor_enabled_by_default"))
    renewal_section_ready = (
        "heartbeat" in operations
        and renewal_status == "ready"
        and renewal_enabled_by_default
    )
    renewal_missing_sections = (
        renewal_contract.get("missing_sections")
        if isinstance(renewal_contract.get("missing_sections"), list)
        else []
    )
    rollout_contract = dict(
        rollout_readiness_contract
        or build_worker_ownership_rollout_readiness_contract(
            strict_mode_rollout_confirmed=normalized_mode == "strict_sql" and rollout_checklist_ready,
            fallback_policy_confirmed=rollout_checklist_ready,
            migration_ready=migration_ready,
            renewal_verification_ready=rollout_checklist_ready,
            stale_fencing_verified=stale_fencing_ready,
            auto_claim_decision_recorded=rollout_checklist_ready,
            audit_evidence_ready=audit_evidence_ready,
            rollback_plan_ready=rollout_checklist_ready,
            production_rollout_confirmed=False,
        )
    )
    rollout_checklist = dict(rollout_contract.get("checklist") or {})
    rollout_operationalization = dict(rollout_contract.get("operationalization") or {})
    rollout_confirmation_decision = dict(
        rollout_operationalization.get("confirmation_decision") or {}
    )
    rollout_confirmation_input_source = dict(
        rollout_confirmation_decision.get("input_source")
        or rollout_operationalization.get("rollout_confirmation_input_source")
        or {}
    )
    rollout_status = _normalize_text(rollout_contract.get("overall_status")) or "blocked"
    production_rollout_confirmed = bool(rollout_contract.get("production_rollout_confirmed"))
    rollout_section_ready = rollout_status == "ready" and production_rollout_confirmed
    rollout_missing_sections = (
        rollout_contract.get("missing_sections")
        if isinstance(rollout_contract.get("missing_sections"), list)
        else []
    )
    auto_claim_contract = dict(
        auto_claim_policy_contract
        or build_worker_ownership_auto_claim_policy_contract(
            explicit_runtime_configuration=recovery_entry_auto_claim_policy_ready,
            production_gate_ready_required=recovery_entry_auto_claim_policy_ready,
            durable_ownership_required=durable,
            descriptor_evidence_fallback=True,
            idempotency_evidence_ready=recovery_entry_auto_claim_policy_ready,
            audit_evidence_ready=audit_evidence_ready,
            entrypoint_allowlist_ready=recovery_entry_auto_claim_policy_ready,
            lease_validation_required="validate_ownership" in operations,
            auto_claim_enabled_by_default=False,
        )
    )
    auto_claim_policy = dict(auto_claim_contract.get("policy") or {})
    auto_claim_entrypoint_allowlist = dict(auto_claim_policy.get("entrypoint_allowlist") or {})
    auto_claim_enablement_gate = dict(auto_claim_policy.get("enablement_gate") or {})
    auto_claim_status = _normalize_text(auto_claim_contract.get("overall_status")) or "blocked"
    auto_claim_enabled_by_default = bool(auto_claim_contract.get("auto_claim_enabled_by_default"))
    auto_claim_section_ready = auto_claim_status == "ready" and auto_claim_enabled_by_default
    auto_claim_missing_sections = (
        auto_claim_contract.get("missing_sections")
        if isinstance(auto_claim_contract.get("missing_sections"), list)
        else []
    )
    audit_contract = dict(
        audit_evidence_contract
        or build_worker_ownership_audit_evidence_contract(
            compact_ownership_evidence=True,
            operation_history_ready=audit_evidence_ready,
            recovery_operation_link_ready=audit_evidence_ready,
            timeline_writer_ready=audit_evidence_ready,
            idempotent_dedupe_ready=audit_evidence_ready,
            authorization_source=False,
        )
    )
    audit_contract_evidence = dict(audit_contract.get("evidence") or {})
    audit_status = _normalize_text(audit_contract.get("overall_status")) or "blocked"
    audit_authorization_source = bool(audit_contract.get("authorization_source"))
    audit_section_ready = audit_status == "ready" and not audit_authorization_source
    audit_missing_sections = (
        audit_contract.get("missing_sections")
        if isinstance(audit_contract.get("missing_sections"), list)
        else []
    )
    sections = [
        _build_production_gate_section(
            name="durable_ownership_store",
            ready=durable and not fallback_active,
            evidence={
                "adapter_kind": adapter_kind,
                "durable": durable,
                "fallback_active": fallback_active,
                "store_mode": normalized_mode,
            },
            missing_reason="durable_ownership_store_missing",
        ),
        _build_production_gate_section(
            name="vendor_lock_semantics",
            ready=vendor_lock_section_ready,
            evidence={
                "vendor_lock_contract_version": _normalize_text(
                    vendor_lock_contract.get("contract_version")
                ),
                "vendor_lock_status": vendor_lock_status,
                "vendor_lock_missing_sections": list(vendor_lock_missing_sections),
                "current_posture": _normalize_text(vendor_lock_contract.get("current_posture"))
                or ("sql_row_lease_fencing" if durable else "local_preview_only"),
                "sql_row_lease_fencing": bool(vendor_lock_policy.get("sql_row_lease_fencing")),
                "sql_row_lease_is_vendor_lock": bool(
                    vendor_lock_policy.get("sql_row_lease_is_vendor_lock")
                ),
                "vendor_lock_adapter_present": bool(
                    vendor_lock_policy.get("vendor_lock_adapter_present")
                ),
                "vendor_lock_adapter_contract_version": _normalize_text(
                    vendor_lock_adapter_contract.get("contract_version")
                ),
                "vendor_lock_adapter_status": _normalize_text(
                    vendor_lock_adapter_contract.get("overall_status")
                )
                or "blocked",
                "vendor_lock_adapter_kind": _normalize_text(
                    vendor_lock_adapter_contract.get("adapter_kind")
                ),
                "vendor_lock_adapter_target_backend": _normalize_text(
                    vendor_lock_adapter_contract.get("target_backend")
                ),
                "vendor_lock_adapter_scope": _normalize_text(
                    vendor_lock_adapter_contract.get("lock_scope")
                ),
                "vendor_lock_adapter_fencing_strategy": _normalize_text(
                    vendor_lock_adapter_contract.get("fencing_strategy")
                ),
                "vendor_lock_adapter_ttl_renewal_strategy": _normalize_text(
                    vendor_lock_adapter_contract.get("ttl_renewal_strategy")
                ),
                "vendor_lock_adapter_failover_strategy": _normalize_text(
                    vendor_lock_adapter_contract.get("failover_strategy")
                ),
                "vendor_lock_adapter_stale_cleanup_strategy": _normalize_text(
                    vendor_lock_adapter_contract.get("stale_owner_cleanup_strategy")
                ),
                "vendor_lock_adapter_acquire_supported": bool(
                    vendor_lock_adapter_contract.get("acquire_supported")
                ),
                "vendor_lock_adapter_renew_supported": bool(
                    vendor_lock_adapter_contract.get("renew_supported")
                ),
                "vendor_lock_adapter_release_supported": bool(
                    vendor_lock_adapter_contract.get("release_supported")
                ),
                "vendor_lock_adapter_probe_supported": bool(
                    vendor_lock_adapter_contract.get("probe_supported")
                ),
                "vendor_lock_adapter_production_allowed": bool(
                    vendor_lock_adapter_contract.get("production_lock_allowed")
                ),
                "vendor_lock_adapter_sql_row_lease_is_vendor_lock": bool(
                    vendor_lock_adapter_contract.get("sql_row_lease_is_vendor_lock")
                ),
                "vendor_lock_adapter_missing_sections": list(
                    vendor_lock_adapter_contract.get("missing_sections")
                    if isinstance(vendor_lock_adapter_contract.get("missing_sections"), list)
                    else []
                ),
                "vendor_lock_postgres_probe_contract_version": _normalize_text(
                    vendor_lock_adapter_backend_probe.get("contract_version")
                ),
                "vendor_lock_postgres_probe_status": _normalize_text(
                    vendor_lock_adapter_backend_probe.get("overall_status")
                )
                or "blocked",
                "vendor_lock_postgres_advisory_lock_family": _normalize_text(
                    vendor_lock_adapter_backend_probe.get("advisory_lock_family")
                ),
                "vendor_lock_postgres_lock_key_derivation": _normalize_text(
                    vendor_lock_adapter_backend_probe.get("lock_key_derivation")
                ),
                "vendor_lock_postgres_lock_scope": _normalize_text(
                    vendor_lock_adapter_backend_probe.get("lock_scope")
                ),
                "vendor_lock_postgres_fencing_token_binding": _normalize_text(
                    vendor_lock_adapter_backend_probe.get("fencing_token_binding")
                ),
                "vendor_lock_postgres_ttl_renewal_strategy": _normalize_text(
                    vendor_lock_adapter_backend_probe.get("ttl_renewal_strategy")
                ),
                "vendor_lock_postgres_failover_behavior": _normalize_text(
                    vendor_lock_adapter_backend_probe.get("failover_behavior")
                ),
                "vendor_lock_postgres_stale_owner_cleanup_strategy": _normalize_text(
                    vendor_lock_adapter_backend_probe.get("stale_owner_cleanup_strategy")
                ),
                "vendor_lock_postgres_probe_safety": _normalize_text(
                    vendor_lock_adapter_backend_probe.get("probe_safety")
                ),
                "vendor_lock_postgres_probe_executes": bool(
                    vendor_lock_adapter_backend_probe.get("executes_probe")
                ),
                "vendor_lock_postgres_sql_row_lease_is_vendor_lock": bool(
                    vendor_lock_adapter_backend_probe.get("sql_row_lease_is_vendor_lock")
                ),
                "vendor_lock_postgres_probe_missing_sections": list(
                    vendor_lock_adapter_backend_probe.get("missing_sections")
                    if isinstance(vendor_lock_adapter_backend_probe.get("missing_sections"), list)
                    else []
                ),
                "vendor_lock_postgres_execution_seam_contract_version": _normalize_text(
                    vendor_lock_postgres_execution_seam.get("contract_version")
                ),
                "vendor_lock_postgres_execution_seam_status": _normalize_text(
                    vendor_lock_postgres_execution_seam.get("overall_status")
                )
                or "blocked",
                "vendor_lock_postgres_executor_bound": bool(
                    vendor_lock_postgres_execution_seam.get("executor_bound")
                ),
                "vendor_lock_postgres_probe_once_supported": bool(
                    vendor_lock_postgres_execution_policy.get("probe_once_supported")
                ),
                "vendor_lock_postgres_acquire_once_supported": bool(
                    vendor_lock_postgres_execution_policy.get("acquire_once_supported")
                ),
                "vendor_lock_postgres_renew_once_supported": bool(
                    vendor_lock_postgres_execution_policy.get("renew_once_supported")
                ),
                "vendor_lock_postgres_release_once_supported": bool(
                    vendor_lock_postgres_execution_policy.get("release_once_supported")
                ),
                "vendor_lock_postgres_lock_key_derivation_ready": bool(
                    vendor_lock_postgres_execution_policy.get("lock_key_derivation_ready")
                ),
                "vendor_lock_postgres_execution_enabled_by_default": bool(
                    vendor_lock_postgres_execution_seam.get("enabled_by_default")
                ),
                "vendor_lock_postgres_execution_production_allowed": bool(
                    vendor_lock_postgres_execution_seam.get("production_lock_allowed")
                ),
                "vendor_lock_postgres_execution_missing_sections": list(
                    vendor_lock_postgres_execution_seam.get("missing_sections")
                    if isinstance(vendor_lock_postgres_execution_seam.get("missing_sections"), list)
                    else []
                ),
                "lock_adapter_kind": _normalize_text(vendor_lock_policy.get("lock_adapter_kind")),
                "lock_scope_defined": bool(vendor_lock_policy.get("lock_scope_defined")),
                "lock_scope": _normalize_text(vendor_lock_policy.get("lock_scope")),
                "fencing_guarantee_defined": bool(
                    vendor_lock_policy.get("fencing_guarantee_defined")
                ),
                "failover_semantics_defined": bool(
                    vendor_lock_policy.get("failover_semantics_defined")
                ),
                "ttl_renewal_semantics_defined": bool(
                    vendor_lock_policy.get("ttl_renewal_semantics_defined")
                ),
                "stale_owner_cleanup_defined": bool(
                    vendor_lock_policy.get("stale_owner_cleanup_defined")
                ),
                "production_lock_allowed": vendor_lock_allowed,
                "vendor_lock_target_decision_contract_version": _normalize_text(
                    vendor_lock_target_decision.get("contract_version")
                ),
                "vendor_lock_target_decision_status": _normalize_text(
                    vendor_lock_target_decision.get("overall_status")
                )
                or "blocked",
                "vendor_lock_target_decision_recorded": bool(
                    vendor_lock_target_decision.get("decision_recorded")
                ),
                "vendor_lock_target_backend": _normalize_text(
                    vendor_lock_target_decision.get("target_backend")
                ),
                "vendor_lock_target_adapter_kind": _normalize_text(
                    vendor_lock_target_decision.get("lock_adapter_kind")
                ),
                "vendor_lock_target_scope": _normalize_text(
                    vendor_lock_target_decision.get("lock_scope")
                ),
                "vendor_lock_target_fencing_strategy": _normalize_text(
                    vendor_lock_target_decision.get("fencing_strategy")
                ),
                "vendor_lock_target_ttl_renewal_strategy": _normalize_text(
                    vendor_lock_target_decision.get("ttl_renewal_strategy")
                ),
                "vendor_lock_target_failover_strategy": _normalize_text(
                    vendor_lock_target_decision.get("failover_strategy")
                ),
                "vendor_lock_target_stale_cleanup_strategy": _normalize_text(
                    vendor_lock_target_decision.get("stale_owner_cleanup_strategy")
                ),
                "vendor_lock_target_missing_sections": list(
                    vendor_lock_target_decision.get("missing_sections")
                    if isinstance(vendor_lock_target_decision.get("missing_sections"), list)
                    else []
                ),
                "vendor_lock_target_sql_row_lease_is_vendor_lock": bool(
                    vendor_lock_target_decision.get("sql_row_lease_is_vendor_lock")
                ),
                "vendor_lock_target_production_allowed": bool(
                    vendor_lock_target_decision.get("production_lock_allowed")
                ),
                "vendor_lock_target_input_contract_version": _normalize_text(
                    vendor_lock_target_input_source.get("contract_version")
                ),
                "vendor_lock_target_input_source_status": _normalize_text(
                    vendor_lock_target_input_source.get("overall_status")
                )
                or "blocked",
                "vendor_lock_target_input_source_kind": _normalize_text(
                    vendor_lock_target_input_source.get("input_source_kind")
                ),
                "vendor_lock_target_input_decision_id": _normalize_text(
                    vendor_lock_target_input_source.get("decision_id")
                ),
                "vendor_lock_target_input_approved_by": _normalize_text(
                    vendor_lock_target_input_source.get("approved_by")
                ),
                "vendor_lock_target_input_approved_at": _normalize_text(
                    vendor_lock_target_input_source.get("approved_at")
                ),
                "vendor_lock_target_input_backend": _normalize_text(
                    vendor_lock_target_input_source.get("target_backend")
                ),
                "vendor_lock_target_input_adapter_kind": _normalize_text(
                    vendor_lock_target_input_source.get("lock_adapter_kind")
                ),
                "vendor_lock_target_input_rollout_artifact": _normalize_text(
                    vendor_lock_target_input_source.get("rollout_artifact")
                ),
                "vendor_lock_target_input_config_key": _normalize_text(
                    vendor_lock_target_input_source.get("config_key")
                ),
                "vendor_lock_target_input_manual_approval_reference": _normalize_text(
                    vendor_lock_target_input_source.get("manual_approval_reference")
                ),
                "vendor_lock_target_input_missing_sections": list(
                    vendor_lock_target_input_source.get("missing_sections")
                    if isinstance(vendor_lock_target_input_source.get("missing_sections"), list)
                    else []
                ),
                "vendor_lock_target_input_sql_row_lease_is_vendor_lock": bool(
                    vendor_lock_target_input_source.get("sql_row_lease_is_vendor_lock")
                ),
            },
            missing_reason="vendor_lock_semantics_missing",
        ),
        _build_production_gate_section(
            name="heartbeat_renewal_supervisor",
            ready=renewal_section_ready,
            evidence={
                "heartbeat_operation_present": "heartbeat" in operations,
                "renew_once_supported": bool(renewal_policy.get("renew_once_supported")),
                "owner_identity_required": bool(renewal_policy.get("owner_identity_required")),
                "controlled_lifecycle_supported": bool(
                    renewal_policy.get("controlled_lifecycle_supported")
                ),
                "starts_by_default": bool(renewal_policy.get("starts_by_default")),
                "active": bool(renewal_policy.get("active")),
                "last_renewal_status": _normalize_text(
                    renewal_policy.get("last_renewal_status")
                ),
                "stop_supported": bool(renewal_policy.get("stop_supported")),
                "failure_fail_closed": bool(renewal_policy.get("failure_fail_closed")),
                "background_supervisor_present": bool(
                    renewal_policy.get("background_supervisor_present")
                ),
                "ttl_interval_policy_ready": bool(
                    renewal_policy.get("ttl_interval_policy_ready")
                ),
                "lease_ttl_seconds": int(renewal_policy.get("lease_ttl_seconds") or 0),
                "renew_interval_seconds": int(renewal_policy.get("renew_interval_seconds") or 0),
                "renewal_supervisor_contract_version": _normalize_text(
                    renewal_contract.get("contract_version")
                ),
                "renewal_supervisor_status": renewal_status,
                "renewal_supervisor_missing_sections": list(renewal_missing_sections),
                "supervisor_enabled_by_default": renewal_enabled_by_default,
                "lease_loss_fail_closed": bool(renewal_policy.get("lease_loss_fail_closed")),
            },
            missing_reason="heartbeat_renewal_supervisor_missing",
        ),
        _build_production_gate_section(
            name="migration_checklist",
            ready=migration_ready,
            evidence={
                "table": "runtime_worker_ownership_leases",
                "migration_ready": migration_ready,
            },
            missing_reason="runtime_worker_ownership_migration_not_confirmed",
        ),
        _build_production_gate_section(
            name="rollout_checklist",
            ready=rollout_section_ready,
            evidence={
                "rollout_readiness_contract_version": _normalize_text(
                    rollout_contract.get("contract_version")
                ),
                "rollout_readiness_status": rollout_status,
                "rollout_missing_sections": list(rollout_missing_sections),
                "production_rollout_confirmed": production_rollout_confirmed,
                "strict_mode_rollout_confirmed": bool(
                    rollout_checklist.get("strict_mode_rollout_confirmed")
                ),
                "fallback_policy_confirmed": bool(rollout_checklist.get("fallback_policy_confirmed")),
                "migration_ready": bool(rollout_checklist.get("migration_ready")),
                "stale_fencing_verified": bool(rollout_checklist.get("stale_fencing_verified")),
                "rollback_plan_ready": bool(rollout_checklist.get("rollback_plan_ready")),
                "rollout_operationalization_status": _normalize_text(
                    rollout_operationalization.get("overall_status")
                )
                or "blocked",
                "rollout_mode": _normalize_text(
                    rollout_operationalization.get("rollout_mode")
                )
                or "readiness_only",
                "rollout_missing_artifacts": list(
                    rollout_operationalization.get("missing_artifacts")
                    if isinstance(rollout_operationalization.get("missing_artifacts"), list)
                    else []
                ),
                "rollback_plan_status": _normalize_text(
                    rollout_operationalization.get("rollback_plan_status")
                )
                or ("ready" if rollout_checklist.get("rollback_plan_ready") else "missing"),
                "fallback_policy_status": _normalize_text(
                    rollout_operationalization.get("fallback_policy_status")
                )
                or ("ready" if rollout_checklist.get("fallback_policy_confirmed") else "missing"),
                "renewal_lifecycle_verification_status": _normalize_text(
                    rollout_operationalization.get("renewal_lifecycle_verification_status")
                )
                or ("verified" if rollout_checklist.get("renewal_verification_ready") else "missing"),
                "auto_claim_decision_status": _normalize_text(
                    rollout_operationalization.get("auto_claim_decision_status")
                )
                or ("recorded" if rollout_checklist.get("auto_claim_decision_recorded") else "missing"),
                "rollout_confirmation_decision_contract_version": _normalize_text(
                    rollout_confirmation_decision.get("contract_version")
                ),
                "rollout_confirmation_decision_status": _normalize_text(
                    rollout_confirmation_decision.get("overall_status")
                )
                or "blocked",
                "rollout_decision_recorded": bool(
                    rollout_confirmation_decision.get("decision_recorded")
                ),
                "rollout_decision_id": _normalize_text(
                    rollout_confirmation_decision.get("decision_id")
                ),
                "rollout_approved_by": _normalize_text(
                    rollout_confirmation_decision.get("approved_by")
                ),
                "rollout_approved_at": _normalize_text(
                    rollout_confirmation_decision.get("approved_at")
                ),
                "rollout_target_store_mode": _normalize_text(
                    rollout_confirmation_decision.get("target_store_mode")
                ),
                "rollout_confirmation_missing_sections": list(
                    rollout_confirmation_decision.get("missing_sections")
                    if isinstance(
                        rollout_confirmation_decision.get("missing_sections"), list
                    )
                    else []
                ),
                "rollout_confirmation_production_rollout_confirmed": bool(
                    rollout_confirmation_decision.get("production_rollout_confirmed")
                ),
                "rollout_confirmation_input_contract_version": _normalize_text(
                    rollout_confirmation_input_source.get("contract_version")
                ),
                "rollout_confirmation_input_source_status": _normalize_text(
                    rollout_confirmation_input_source.get("overall_status")
                )
                or "blocked",
                "rollout_confirmation_input_source_kind": _normalize_text(
                    rollout_confirmation_input_source.get("input_source_kind")
                ),
                "rollout_confirmation_input_decision_id": _normalize_text(
                    rollout_confirmation_input_source.get("decision_id")
                ),
                "rollout_confirmation_input_approved_by": _normalize_text(
                    rollout_confirmation_input_source.get("approved_by")
                ),
                "rollout_confirmation_input_approved_at": _normalize_text(
                    rollout_confirmation_input_source.get("approved_at")
                ),
                "rollout_confirmation_input_target_store_mode": _normalize_text(
                    rollout_confirmation_input_source.get("target_store_mode")
                ),
                "rollout_confirmation_input_rollback_plan_reference": _normalize_text(
                    rollout_confirmation_input_source.get("rollback_plan_reference")
                ),
                "rollout_confirmation_input_fallback_policy_reference": _normalize_text(
                    rollout_confirmation_input_source.get("fallback_policy_reference")
                ),
                "rollout_confirmation_input_renewal_lifecycle_reference": _normalize_text(
                    rollout_confirmation_input_source.get("renewal_lifecycle_reference")
                ),
                "rollout_confirmation_input_auto_claim_decision_reference": _normalize_text(
                    rollout_confirmation_input_source.get("auto_claim_decision_reference")
                ),
                "rollout_confirmation_input_missing_sections": list(
                    rollout_confirmation_input_source.get("missing_sections")
                    if isinstance(
                        rollout_confirmation_input_source.get("missing_sections"), list
                    )
                    else []
                ),
                "rollout_confirmation_input_sql_row_lease_is_authority": bool(
                    rollout_confirmation_input_source.get(
                        "sql_row_lease_is_rollout_authority"
                    )
                ),
            },
            missing_reason="worker_ownership_rollout_checklist_incomplete",
        ),
        _build_production_gate_section(
            name="recovery_entry_auto_claim_policy",
            ready=auto_claim_section_ready,
            evidence={
                "auto_claim_policy_contract_version": _normalize_text(
                    auto_claim_contract.get("contract_version")
                ),
                "auto_claim_policy_status": auto_claim_status,
                "auto_claim_missing_sections": list(auto_claim_missing_sections),
                "auto_claim_enabled_by_default": auto_claim_enabled_by_default,
                "descriptor_evidence_fallback": bool(
                    auto_claim_policy.get("descriptor_evidence_fallback")
                ),
                "requires_valid_worker_ownership_gate": bool(
                    auto_claim_policy.get("production_gate_ready_required")
                ),
                "entrypoint_allowlist_ready": bool(
                    auto_claim_policy.get("entrypoint_allowlist_ready")
                ),
                "auto_claim_entrypoint_allowlist_contract_version": _normalize_text(
                    auto_claim_entrypoint_allowlist.get("contract_version")
                ),
                "auto_claim_entrypoint_allowlist_status": _normalize_text(
                    auto_claim_entrypoint_allowlist.get("overall_status")
                )
                or "blocked",
                "auto_claim_allowed_entrypoints": list(
                    auto_claim_entrypoint_allowlist.get("allowed_entrypoints")
                    if isinstance(
                        auto_claim_entrypoint_allowlist.get("allowed_entrypoints"), list
                    )
                    else []
                ),
                "auto_claim_missing_entrypoints": list(
                    auto_claim_entrypoint_allowlist.get("missing_entrypoints")
                    if isinstance(
                        auto_claim_entrypoint_allowlist.get("missing_entrypoints"), list
                    )
                    else []
                ),
                "auto_claim_default_auto_claim_enabled": bool(
                    auto_claim_entrypoint_allowlist.get("default_auto_claim_enabled")
                ),
                "auto_claim_requires_production_gate_ready": bool(
                    auto_claim_entrypoint_allowlist.get("requires_production_gate_ready")
                ),
                "auto_claim_enablement_gate_contract_version": _normalize_text(
                    auto_claim_enablement_gate.get("contract_version")
                ),
                "auto_claim_enablement_gate_status": _normalize_text(
                    auto_claim_enablement_gate.get("overall_status")
                )
                or "blocked",
                "auto_claim_will_auto_claim": bool(
                    auto_claim_enablement_gate.get("will_auto_claim")
                ),
                "auto_claim_requested_entrypoint": _normalize_text(
                    auto_claim_enablement_gate.get("requested_entrypoint")
                ),
                "auto_claim_enablement_missing_sections": list(
                    auto_claim_enablement_gate.get("missing_sections")
                    if isinstance(auto_claim_enablement_gate.get("missing_sections"), list)
                    else []
                ),
                "auto_claim_enablement_blocked_reason": _normalize_text(
                    auto_claim_enablement_gate.get("blocked_reason")
                ),
                "lease_validation_required": bool(
                    auto_claim_policy.get("lease_validation_required")
                ),
                "audit_evidence_required": bool(auto_claim_policy.get("audit_evidence_ready")),
                "default_auto_claim_allowed": auto_claim_enabled_by_default,
            },
            missing_reason="recovery_entry_auto_claim_policy_missing",
        ),
        _build_production_gate_section(
            name="stale_fencing_fail_closed",
            ready=stale_fencing_ready,
            evidence={
                "validate_ownership_present": "validate_ownership" in operations,
                "stale_fencing_reason": WORKER_OWNERSHIP_REASON_STALE_FENCING_TOKEN,
            },
            missing_reason="stale_fencing_fail_closed_missing",
        ),
        _build_production_gate_section(
            name="ownership_audit_evidence",
            ready=audit_section_ready,
            evidence={
                "ownership_audit_contract_version": _normalize_text(
                    audit_contract.get("contract_version")
                ),
                "ownership_audit_status": audit_status,
                "ownership_audit_missing_sections": list(audit_missing_sections),
                "compact_ownership_evidence": bool(
                    audit_contract_evidence.get("compact_ownership_evidence")
                ),
                "operation_history_ready": bool(
                    audit_contract_evidence.get("operation_history_ready")
                ),
                "recovery_operation_link_ready": bool(
                    audit_contract_evidence.get("recovery_operation_link_ready")
                ),
                "timeline_writer_ready": bool(
                    audit_contract_evidence.get("timeline_writer_ready")
                ),
                "idempotent_dedupe_ready": bool(
                    audit_contract_evidence.get("idempotent_dedupe_ready")
                ),
                "authorization_source": audit_authorization_source,
                "audit_evidence_ready": audit_section_ready,
            },
            missing_reason="ownership_audit_evidence_missing",
        ),
    ]
    section_readiness = {
        str(section.get("name") or "").strip(): bool(section.get("ready"))
        for section in sections
    }
    enablement_strategy = build_worker_ownership_production_enablement_strategy_contract(
        section_readiness=section_readiness,
        production_default_enabled_requested=production_default_enabled,
    )
    enablement_policy = dict(enablement_strategy.get("policy") or {})
    enablement_input_source = dict(enablement_strategy.get("input_source") or {})
    enablement_blocking_sections = (
        enablement_strategy.get("blocking_sections")
        if isinstance(enablement_strategy.get("blocking_sections"), list)
        else []
    )
    sections.append(
        _build_production_gate_section(
            name="fail_closed_default_decision",
            ready=bool(enablement_strategy.get("production_default_allowed")),
            evidence={
                "enablement_strategy_contract_version": _normalize_text(
                    enablement_strategy.get("contract_version")
                ),
                "enablement_strategy_status": _normalize_text(
                    enablement_strategy.get("overall_status")
                ),
                "production_default_enabled_requested": bool(
                    enablement_strategy.get("production_default_enabled_requested")
                ),
                "production_default_allowed": bool(
                    enablement_strategy.get("production_default_allowed")
                ),
                "enablement_input_source_contract_version": _normalize_text(
                    enablement_input_source.get("contract_version")
                ),
                "enablement_input_source_status": _normalize_text(
                    enablement_input_source.get("overall_status")
                )
                or "blocked",
                "enablement_input_source_kind": _normalize_text(
                    enablement_input_source.get("input_source_kind")
                ),
                "enablement_request_id": _normalize_text(
                    enablement_input_source.get("request_id")
                ),
                "enablement_requested_by": _normalize_text(
                    enablement_input_source.get("requested_by")
                ),
                "enablement_requested_at": _normalize_text(
                    enablement_input_source.get("requested_at")
                ),
                "enablement_target_store_mode": _normalize_text(
                    enablement_input_source.get("target_store_mode")
                ),
                "enablement_rollout_artifact": _normalize_text(
                    enablement_input_source.get("rollout_artifact")
                ),
                "enablement_vendor_lock_decision_id": _normalize_text(
                    enablement_input_source.get("vendor_lock_decision_id")
                ),
                "enablement_renewal_lifecycle_reference": _normalize_text(
                    enablement_input_source.get("renewal_lifecycle_reference")
                ),
                "enablement_auto_claim_decision_reference": _normalize_text(
                    enablement_input_source.get("auto_claim_decision_reference")
                ),
                "enablement_audit_evidence_reference": _normalize_text(
                    enablement_input_source.get("audit_evidence_reference")
                ),
                "enablement_rollback_plan_reference": _normalize_text(
                    enablement_input_source.get("rollback_plan_reference")
                ),
                "enablement_fallback_policy_reference": _normalize_text(
                    enablement_input_source.get("fallback_policy_reference")
                ),
                "enablement_input_source_ready": bool(
                    enablement_policy.get("input_source_ready")
                ),
                "enablement_input_source_missing_sections": list(
                    enablement_input_source.get("missing_sections")
                    if isinstance(enablement_input_source.get("missing_sections"), list)
                    else []
                ),
                "required_sections": list(enablement_strategy.get("required_sections") or []),
                "blocking_sections": list(enablement_blocking_sections),
                "explicit_enablement_required": bool(
                    enablement_policy.get("explicit_enablement_required")
                ),
                "all_required_sections_ready": bool(
                    enablement_policy.get("all_required_sections_ready")
                ),
                "fail_closed_when_blocked": bool(
                    enablement_policy.get("fail_closed_when_blocked")
                ),
                "sql_row_lease_is_not_default_authority": bool(
                    enablement_policy.get("sql_row_lease_is_not_default_authority")
                ),
                "blocked_gate_prevents_default_ownership": not bool(
                    enablement_strategy.get("production_default_allowed")
                ),
            },
            missing_reason="production_default_enablement_strategy_blocked",
        )
    )
    missing_sections = [
        str(section.get("name") or "").strip()
        for section in sections
        if not bool(section.get("ready"))
    ]
    overall_status = "ready" if not missing_sections else "blocked"
    return {
        "contract_version": WORKER_OWNERSHIP_PRODUCTION_GATE_CONTRACT_VERSION,
        "overall_status": overall_status,
        "ready": overall_status == "ready",
        "production_default_enabled": bool(production_default_enabled) and overall_status == "ready",
        "sections": sections,
        "missing_sections": missing_sections,
        "next_allowed_action": (
            "consider_explicit_production_enablement"
            if overall_status == "ready"
            else "implement_vendor_lock_renewal_rollout_and_auto_claim_policy"
        ),
        "non_goals": [
            "no_vendor_specific_lock_adapter",
            "no_background_renewal_supervisor",
            "no_default_recovery_entry_auto_claim",
            "no_implicit_production_ownership_from_sql_row_lease",
        ],
    }


def build_worker_ownership_operational_readiness_contract(
    *,
    ownership_contract: Dict[str, Any] | None = None,
    store_mode: str = "memory_only",
    auto_claim_enabled: bool = False,
    vendor_lock_semantics_contract: Dict[str, Any] | None = None,
    renewal_supervisor_contract: Dict[str, Any] | None = None,
    rollout_readiness_contract: Dict[str, Any] | None = None,
    auto_claim_policy_contract: Dict[str, Any] | None = None,
    audit_evidence_contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Describe production readiness without implying a vendor-level lock."""

    contract = dict(ownership_contract or {})
    adapter_kind = _normalize_text(contract.get("adapter_kind")) or "in_memory"
    durable = bool(contract.get("durable"))
    fallback_active = bool(contract.get("fallback_active"))
    normalized_mode = _normalize_text(store_mode).lower() or "memory_only"
    operations = set(contract.get("operations") or [])
    renewal_supported = "heartbeat" in operations
    vendor_lock_contract = dict(
        vendor_lock_semantics_contract
        or build_worker_ownership_vendor_lock_semantics_contract(
            current_posture="sql_row_lease_fencing" if durable else "local_preview_only",
            sql_row_lease_fencing=durable,
            production_lock_allowed=False,
        )
    )
    renewal_contract = dict(
        renewal_supervisor_contract
        or build_worker_ownership_renewal_supervisor_contract(
            heartbeat_operation_present=renewal_supported,
            renew_once_supported=renewal_supported and "validate_ownership" in operations,
            owner_identity_required=True,
            controlled_lifecycle_supported=True,
            starts_by_default=False,
            active=False,
            stop_supported=True,
            failure_fail_closed=True,
            ttl_interval_policy_present=True,
            lease_loss_fail_closed=WORKER_OWNERSHIP_REASON_LEASE_EXPIRED
            in set(contract.get("fail_closed_reasons") or []),
        )
    )
    migration_ready = durable and adapter_kind == "sqlalchemy" and not fallback_active
    production_ready = migration_ready and renewal_supported
    rollout_contract = dict(
        rollout_readiness_contract
        or build_worker_ownership_rollout_readiness_contract(
            strict_mode_rollout_confirmed=False,
            fallback_policy_confirmed=False,
            migration_ready=migration_ready,
            renewal_verification_ready=False,
            stale_fencing_verified=WORKER_OWNERSHIP_REASON_STALE_FENCING_TOKEN
            in set(contract.get("fail_closed_reasons") or []),
            auto_claim_decision_recorded=False,
            audit_evidence_ready=False,
            rollback_plan_ready=False,
            production_rollout_confirmed=False,
        )
    )
    auto_claim_contract = dict(
        auto_claim_policy_contract
        or build_worker_ownership_auto_claim_policy_contract(
            explicit_runtime_configuration=auto_claim_enabled,
            production_gate_ready_required=False,
            durable_ownership_required=durable,
            descriptor_evidence_fallback=True,
            idempotency_evidence_ready=False,
            audit_evidence_ready=False,
            entrypoint_allowlist_ready=False,
            lease_validation_required="validate_ownership" in operations,
            auto_claim_enabled_by_default=False,
        )
    )
    audit_contract = dict(
        audit_evidence_contract
        or build_worker_ownership_audit_evidence_contract(
            compact_ownership_evidence=True,
            operation_history_ready=False,
            recovery_operation_link_ready=False,
            timeline_writer_ready=False,
            idempotent_dedupe_ready=False,
            authorization_source=False,
        )
    )
    production_gate = build_worker_ownership_production_gate_contract(
        ownership_contract=contract,
        store_mode=normalized_mode,
        migration_ready=migration_ready,
        vendor_lock_semantics_ready=False,
        vendor_lock_semantics_contract=vendor_lock_contract,
        renewal_supervisor_ready=False,
        renewal_supervisor_contract=renewal_contract,
        rollout_checklist_ready=False,
        rollout_readiness_contract=rollout_contract,
        recovery_entry_auto_claim_policy_ready=False,
        auto_claim_policy_contract=auto_claim_contract,
        audit_evidence_ready=False,
        audit_evidence_contract=audit_contract,
        production_default_enabled=False,
    )
    return {
        "contract_version": WORKER_OWNERSHIP_OPERATIONAL_READINESS_CONTRACT_VERSION,
        "store_mode": normalized_mode,
        "adapter_kind": adapter_kind,
        "durable": durable,
        "production_ready": production_ready,
        "readiness_status": "production_ready" if production_ready else "preview_or_degraded",
        "renewal_supported": renewal_supported,
        "heartbeat_operation": "heartbeat" if renewal_supported else "",
        "stale_lease_fail_closed": True,
        "recovery_entry_claim_mode": "opt_in_auto_claim" if auto_claim_enabled else "descriptor_evidence_only",
        "auto_claim_enabled": bool(auto_claim_enabled),
        "vendor_lock_posture": "sql_row_lease_fencing" if durable else "local_preview_only",
        "vendor_lock_semantics": vendor_lock_contract,
        "renewal_supervisor": renewal_contract,
        "production_rollout": rollout_contract,
        "auto_claim_policy": auto_claim_contract,
        "ownership_audit": audit_contract,
        "migration_checklist": {
            "table": "runtime_worker_ownership_leases",
            "migration_required": durable,
            "migration_ready": migration_ready,
        },
        "rollout_checklist": [
            "set_WORKER_OWNERSHIP_STORE_MODE",
            "apply_runtime_worker_ownership_leases_migration",
            "verify_heartbeat_renewal",
            "verify_stale_fencing_fail_closed",
            "decide_recovery_entry_auto_claim",
        ],
        "fallback_active": fallback_active,
        "fallback_reason": _normalize_text(contract.get("fallback_reason")),
        "production_gate": production_gate,
    }


class PostgresAdvisoryLockExecutionSeam:
    """Opt-in PostgreSQL advisory lock seam; execution is caller-owned."""

    def __init__(
        self,
        *,
        executor: Callable[[Dict[str, Any]], Dict[str, Any]] | None = None,
    ) -> None:
        self._executor = executor

    def contract(self) -> Dict[str, Any]:
        executor_bound = callable(self._executor)
        return build_worker_ownership_postgres_advisory_lock_execution_seam_contract(
            executor_bound=executor_bound,
            probe_once_supported=executor_bound,
            acquire_once_supported=executor_bound,
            renew_once_supported=executor_bound,
            release_once_supported=executor_bound,
            lock_key_derivation_ready=True,
            owner_identity_required=True,
            fencing_token_required=True,
            fail_closed=True,
            enabled_by_default=False,
            production_lock_allowed=False,
        )

    def status(self) -> Dict[str, Any]:
        contract = self.contract()
        return {
            "contract_version": contract["contract_version"],
            "overall_status": contract["overall_status"],
            "executor_bound": contract["executor_bound"],
            "enabled_by_default": contract["enabled_by_default"],
            "production_lock_allowed": contract["production_lock_allowed"],
            "starts_by_default": False,
            "background_loop_present": False,
        }

    def probe_once(self) -> Dict[str, Any]:
        return self._execute(
            operation="probe",
            sql="SELECT 1",
            success_status="ready",
            success_flag="probed",
            run_id="",
            worker_id="",
            lease_id="",
            fencing_token=0,
            require_owner=False,
        )

    def acquire_once(
        self,
        *,
        run_id: str,
        worker_id: str,
        lease_id: str = "",
        fencing_token: int,
    ) -> Dict[str, Any]:
        return self._execute(
            operation="acquire",
            sql="SELECT pg_try_advisory_lock(:lock_key)",
            success_status="acquired",
            success_flag="acquired",
            run_id=run_id,
            worker_id=worker_id,
            lease_id=lease_id,
            fencing_token=fencing_token,
            require_owner=True,
        )

    def renew_once(
        self,
        *,
        run_id: str,
        worker_id: str,
        lease_id: str = "",
        fencing_token: int,
    ) -> Dict[str, Any]:
        return self._execute(
            operation="renew",
            sql="SELECT pg_try_advisory_lock(:lock_key)",
            success_status="renewed",
            success_flag="renewed",
            run_id=run_id,
            worker_id=worker_id,
            lease_id=lease_id,
            fencing_token=fencing_token,
            require_owner=True,
        )

    def release_once(
        self,
        *,
        run_id: str,
        worker_id: str,
        lease_id: str = "",
        fencing_token: int,
    ) -> Dict[str, Any]:
        return self._execute(
            operation="release",
            sql="SELECT pg_advisory_unlock(:lock_key)",
            success_status="released",
            success_flag="released",
            run_id=run_id,
            worker_id=worker_id,
            lease_id=lease_id,
            fencing_token=fencing_token,
            require_owner=True,
        )

    def _execute(
        self,
        *,
        operation: str,
        sql: str,
        success_status: str,
        success_flag: str,
        run_id: str,
        worker_id: str,
        lease_id: str,
        fencing_token: int,
        require_owner: bool,
    ) -> Dict[str, Any]:
        normalized_run_id = _normalize_text(run_id)
        normalized_worker_id = _normalize_text(worker_id)
        normalized_lease_id = _normalize_text(lease_id)
        normalized_fencing = int(fencing_token or 0)
        lock_key = self._derive_lock_key(normalized_run_id) if normalized_run_id else 0
        base = {
            "contract_version": (
                WORKER_OWNERSHIP_POSTGRES_ADVISORY_LOCK_EXECUTION_SEAM_CONTRACT_VERSION
            ),
            "operation": operation,
            "target_backend": "postgres",
            "executor_bound": callable(self._executor),
            "executed": False,
            "enabled_by_default": False,
            "production_lock_allowed": False,
            "run_id": normalized_run_id,
            "worker_id": normalized_worker_id,
            "lease_id": normalized_lease_id,
            "fencing_token": normalized_fencing,
            "lock_key": lock_key,
            "sql": sql,
            "acquired": False,
            "renewed": False,
            "released": False,
            "probed": False,
        }
        if not callable(self._executor):
            return {
                **base,
                "status": "blocked",
                "reason": WORKER_OWNERSHIP_REASON_POSTGRES_ADVISORY_LOCK_EXECUTOR_MISSING,
            }
        if require_owner and (
            not normalized_run_id or not normalized_worker_id or normalized_fencing <= 0
        ):
            return {
                **base,
                "status": "blocked",
                "reason": WORKER_OWNERSHIP_REASON_POSTGRES_ADVISORY_LOCK_OWNER_IDENTITY_MISSING,
            }

        envelope = {
            "operation": operation,
            "target_backend": "postgres",
            "sql": sql,
            "lock_key": lock_key,
            "run_id": normalized_run_id,
            "worker_id": normalized_worker_id,
            "lease_id": normalized_lease_id,
            "fencing_token": normalized_fencing,
            "production_lock_allowed": False,
        }
        try:
            result = dict(self._executor(envelope) or {})
        except Exception as exc:  # pragma: no cover - defensive fail-closed guard
            return {
                **base,
                "status": "blocked",
                "reason": WORKER_OWNERSHIP_REASON_POSTGRES_ADVISORY_LOCK_EXECUTOR_FAILED,
                "error": str(exc),
            }

        success = bool(result.get(success_flag))
        if operation == "probe":
            success = bool(result.get("ok"))
        if not success:
            return {
                **base,
                "status": "blocked",
                "reason": (
                    WORKER_OWNERSHIP_REASON_POSTGRES_ADVISORY_LOCK_NOT_ACQUIRED
                    if operation == "acquire"
                    else WORKER_OWNERSHIP_REASON_POSTGRES_ADVISORY_LOCK_EXECUTOR_FAILED
                ),
                "executed": True,
                "executor_ok": bool(result.get("ok")),
            }
        return {
            **base,
            "status": success_status,
            "reason": "",
            "executed": True,
            "executor_ok": bool(result.get("ok")),
            success_flag: True,
        }

    def _derive_lock_key(self, run_id: str) -> int:
        digest = hashlib.sha256(run_id.encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "big", signed=False) & ((1 << 63) - 1)


@dataclass(frozen=True)
class RuntimeWorkerLease:
    run_id: str
    worker_id: str
    lease_id: str
    fencing_token: int
    claimed_at: datetime
    lease_expires_at: datetime
    last_heartbeat_at: datetime
    lease_status: str = WORKER_OWNERSHIP_STATUS_CLAIMED
    adapter_kind: str = "in_memory"
    durable: bool = False

    def is_expired(self, now: datetime | None = None) -> bool:
        checked_at = _ensure_utc(now or _utc_now()) or _utc_now()
        lease_expires_at = _ensure_utc(self.lease_expires_at) or checked_at
        return lease_expires_at <= checked_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_version": RUNTIME_WORKER_OWNERSHIP_CONTRACT_VERSION,
            "implemented": True,
            "adapter_kind": self.adapter_kind,
            "durable": self.durable,
            "run_id": self.run_id,
            "worker_id": self.worker_id,
            "lease_id": self.lease_id,
            "fencing_token": self.fencing_token,
            "claimed_at": _isoformat(self.claimed_at),
            "lease_expires_at": _isoformat(self.lease_expires_at),
            "last_heartbeat_at": _isoformat(self.last_heartbeat_at),
            "lease_status": self.lease_status,
        }


class WorkerOwnershipRenewalSupervisor:
    """Explicit one-shot renewal seam; it never starts background work."""

    def __init__(
        self,
        *,
        store: Any | None,
        lease_ttl_seconds: int = 60,
        renew_interval_seconds: int = 20,
    ) -> None:
        self._store = store
        self.lease_ttl_seconds = max(int(lease_ttl_seconds or 0), 1)
        self.renew_interval_seconds = max(int(renew_interval_seconds or 0), 1)
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._active = False
        self._target: Dict[str, Any] = {}
        self._last_renewal: Dict[str, Any] = {}
        self._renewal_count = 0

    def build_contract(self) -> Dict[str, Any]:
        status = self.status()
        return build_worker_ownership_renewal_supervisor_contract(
            heartbeat_operation_present=callable(getattr(self._store, "heartbeat", None)),
            renew_once_supported=callable(getattr(self._store, "heartbeat", None))
            and callable(getattr(self._store, "validate_ownership", None)),
            owner_identity_required=True,
            controlled_lifecycle_supported=True,
            starts_by_default=False,
            active=bool(status.get("active")),
            last_renewal_status=str(status.get("last_renewal_status") or ""),
            stop_supported=True,
            failure_fail_closed=True,
            background_supervisor_present=False,
            renewal_owner_identity_present=True,
            ttl_interval_policy_present=True,
            lease_loss_fail_closed=True,
            supervisor_enabled_by_default=False,
            lease_ttl_seconds=self.lease_ttl_seconds,
            renew_interval_seconds=self.renew_interval_seconds,
        )

    def renew_once(
        self,
        *,
        run_id: str,
        worker_id: str,
        lease_id: str,
        fencing_token: int,
    ) -> Dict[str, Any]:
        normalized_run_id = _normalize_text(run_id)
        normalized_worker_id = _normalize_text(worker_id)
        normalized_lease_id = _normalize_text(lease_id)
        if self._store is None:
            return self._blocked(
                reason="worker_ownership_store_missing",
                blocked_reason="renewal_store_missing",
                run_id=normalized_run_id,
                worker_id=normalized_worker_id,
                lease_id=normalized_lease_id,
                fencing_token=fencing_token,
            )

        validate_ownership = getattr(self._store, "validate_ownership", None)
        heartbeat = getattr(self._store, "heartbeat", None)
        if not callable(validate_ownership) or not callable(heartbeat):
            return self._blocked(
                reason="worker_ownership_store_missing",
                blocked_reason="renewal_store_missing",
                run_id=normalized_run_id,
                worker_id=normalized_worker_id,
                lease_id=normalized_lease_id,
                fencing_token=fencing_token,
            )
        if not normalized_run_id or not normalized_worker_id or not normalized_lease_id:
            return self._blocked(
                reason=WORKER_OWNERSHIP_REASON_INVALID_LEASE,
                blocked_reason="renewal_owner_identity_missing",
                run_id=normalized_run_id,
                worker_id=normalized_worker_id,
                lease_id=normalized_lease_id,
                fencing_token=fencing_token,
            )

        validation = dict(
            validate_ownership(
                normalized_run_id,
                normalized_worker_id,
                normalized_lease_id,
                int(fencing_token or 0),
            )
        )
        if not validation.get("owned"):
            return self._with_renewal_status(validation, renewed=False)

        heartbeat_result = dict(
            heartbeat(
                normalized_run_id,
                normalized_worker_id,
                normalized_lease_id,
                lease_ttl_seconds=self.lease_ttl_seconds,
            )
        )
        return self._with_renewal_status(heartbeat_result, renewed=bool(heartbeat_result.get("owned")))

    def start(
        self,
        *,
        run_id: str,
        worker_id: str,
        lease_id: str,
        fencing_token: int,
    ) -> Dict[str, Any]:
        with self._lock:
            if self._active:
                return self._status_locked()
            self._target = {
                "run_id": _normalize_text(run_id),
                "worker_id": _normalize_text(worker_id),
                "lease_id": _normalize_text(lease_id),
                "fencing_token": int(fencing_token or 0),
            }
            self._stop_event.clear()

        first = self.renew_once(**self._target)
        with self._lock:
            self._last_renewal = dict(first)
            if first.get("renewed"):
                self._renewal_count += 1
                self._active = True
                self._thread = threading.Thread(
                    target=self._run_loop,
                    name=f"worker-ownership-renewal:{self._target.get('run_id')}",
                    daemon=True,
                )
                self._thread.start()
            else:
                self._active = False
                self._stop_event.set()
            return self._status_locked()

    def stop(self) -> Dict[str, Any]:
        with self._lock:
            self._active = False
            self._stop_event.set()
            thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=min(float(self.renew_interval_seconds), 1.0))
        with self._lock:
            self._thread = None
            return self._status_locked()

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return self._status_locked()

    def _run_loop(self) -> None:
        while not self._stop_event.wait(float(self.renew_interval_seconds)):
            with self._lock:
                if not self._active:
                    return
                target = dict(self._target)
            result = self.renew_once(**target)
            with self._lock:
                self._last_renewal = dict(result)
                if result.get("renewed"):
                    self._renewal_count += 1
                    continue
                self._active = False
                self._stop_event.set()
                return

    def _with_renewal_status(self, payload: Dict[str, Any], *, renewed: bool) -> Dict[str, Any]:
        result = dict(payload)
        result["renewed"] = bool(renewed)
        result["renewal_status"] = "renewed" if renewed else "blocked"
        result["background_supervisor_started"] = False
        result["lease_ttl_seconds"] = self.lease_ttl_seconds
        result["renew_interval_seconds"] = self.renew_interval_seconds
        if not renewed:
            result["owned"] = False
        return result

    def _blocked(
        self,
        *,
        reason: str,
        blocked_reason: str,
        run_id: str,
        worker_id: str,
        lease_id: str,
        fencing_token: int,
    ) -> Dict[str, Any]:
        return {
            "contract_version": RUNTIME_WORKER_OWNERSHIP_CONTRACT_VERSION,
            "implemented": True,
            "run_id": run_id,
            "worker_id": worker_id,
            "lease_id": lease_id,
            "fencing_token": int(fencing_token or 0),
            "lease_status": WORKER_OWNERSHIP_STATUS_BLOCKED,
            "owned": False,
            "renewed": False,
            "renewal_status": "blocked",
            "reason": reason,
            "blocked_reason": blocked_reason,
            "background_supervisor_started": False,
            "lease_ttl_seconds": self.lease_ttl_seconds,
            "renew_interval_seconds": self.renew_interval_seconds,
        }

    def _status_locked(self) -> Dict[str, Any]:
        last = dict(self._last_renewal)
        return {
            "controlled_lifecycle_supported": True,
            "starts_by_default": False,
            "active": bool(self._active),
            "stop_supported": True,
            "failure_fail_closed": True,
            "last_renewal_status": _normalize_text(last.get("renewal_status")),
            "last_failure_reason": _normalize_text(last.get("reason")),
            "last_blocked_reason": _normalize_text(last.get("blocked_reason")),
            "renewal_count": int(self._renewal_count),
            "lease_ttl_seconds": self.lease_ttl_seconds,
            "renew_interval_seconds": self.renew_interval_seconds,
        }


class InMemoryRuntimeWorkerOwnershipStore:
    """Preview ownership store that preserves lease/fencing semantics in-process."""

    def __init__(self, now_fn: Callable[[], datetime] | None = None) -> None:
        self._leases: Dict[str, RuntimeWorkerLease] = {}
        self._fencing_tokens: Dict[str, int] = {}
        self._now_fn = now_fn or _utc_now

    def claim_run(
        self,
        run_id: str,
        worker_id: str,
        lease_ttl_seconds: int = 60,
    ) -> Dict[str, Any]:
        normalized_run_id = _normalize_text(run_id)
        normalized_worker_id = _normalize_text(worker_id)
        now = self._now()
        current = self._leases.get(normalized_run_id)
        if current and not current.is_expired(now):
            if current.worker_id == normalized_worker_id:
                refreshed = self._refresh_lease(current, now, lease_ttl_seconds, WORKER_OWNERSHIP_STATUS_REFRESHED)
                self._leases[normalized_run_id] = refreshed
                return self._success(refreshed)
            return self._blocked(
                current,
                WORKER_OWNERSHIP_REASON_WORKER_OWNERSHIP_LOST,
                "active_worker_lease_exists",
            )

        next_token = self._next_fencing_token(normalized_run_id)
        lease = RuntimeWorkerLease(
            run_id=normalized_run_id,
            worker_id=normalized_worker_id,
            lease_id=f"worker_lease:{normalized_run_id}:{uuid4().hex}",
            fencing_token=next_token,
            claimed_at=now,
            lease_expires_at=now + timedelta(seconds=max(int(lease_ttl_seconds or 0), 1)),
            last_heartbeat_at=now,
            lease_status=WORKER_OWNERSHIP_STATUS_CLAIMED,
        )
        self._leases[normalized_run_id] = lease
        return self._success(lease)

    def heartbeat(
        self,
        run_id: str,
        worker_id: str,
        lease_id: str,
        lease_ttl_seconds: int = 60,
    ) -> Dict[str, Any]:
        now = self._now()
        current = self._leases.get(_normalize_text(run_id))
        validation = self._validate_current_lease(
            current=current,
            worker_id=worker_id,
            lease_id=lease_id,
            fencing_token=current.fencing_token if current else None,
            now=now,
        )
        if not validation["valid"]:
            return validation["ownership"]

        refreshed = self._refresh_lease(current, now, lease_ttl_seconds, WORKER_OWNERSHIP_STATUS_REFRESHED)
        self._leases[current.run_id] = refreshed
        return self._success(refreshed)

    def validate_ownership(
        self,
        run_id: str,
        worker_id: str,
        lease_id: str,
        fencing_token: int,
    ) -> Dict[str, Any]:
        current = self._leases.get(_normalize_text(run_id))
        validation = self._validate_current_lease(
            current=current,
            worker_id=worker_id,
            lease_id=lease_id,
            fencing_token=fencing_token,
            now=self._now(),
        )
        if not validation["valid"]:
            return validation["ownership"]
        return self._success(
            RuntimeWorkerLease(
                run_id=current.run_id,
                worker_id=current.worker_id,
                lease_id=current.lease_id,
                fencing_token=current.fencing_token,
                claimed_at=current.claimed_at,
                lease_expires_at=current.lease_expires_at,
                last_heartbeat_at=current.last_heartbeat_at,
                lease_status=WORKER_OWNERSHIP_STATUS_VALIDATED,
            )
        )

    def get_lease(self, run_id: str) -> Dict[str, Any] | None:
        lease = self._leases.get(_normalize_text(run_id))
        return lease.to_dict() if lease is not None else None

    def build_contract(self) -> Dict[str, Any]:
        return build_worker_ownership_contract(adapter_kind="in_memory", durable=False)

    def _now(self) -> datetime:
        now = self._now_fn()
        return now if now.tzinfo else now.replace(tzinfo=timezone.utc)

    def _next_fencing_token(self, run_id: str) -> int:
        next_token = int(self._fencing_tokens.get(run_id, 0)) + 1
        self._fencing_tokens[run_id] = next_token
        return next_token

    def _refresh_lease(
        self,
        lease: RuntimeWorkerLease,
        now: datetime,
        lease_ttl_seconds: int,
        lease_status: str,
    ) -> RuntimeWorkerLease:
        return RuntimeWorkerLease(
            run_id=lease.run_id,
            worker_id=lease.worker_id,
            lease_id=lease.lease_id,
            fencing_token=lease.fencing_token,
            claimed_at=lease.claimed_at,
            lease_expires_at=now + timedelta(seconds=max(int(lease_ttl_seconds or 0), 1)),
            last_heartbeat_at=now,
            lease_status=lease_status,
            adapter_kind=lease.adapter_kind,
            durable=lease.durable,
        )

    def _validate_current_lease(
        self,
        *,
        current: RuntimeWorkerLease | None,
        worker_id: str,
        lease_id: str,
        fencing_token: int | None,
        now: datetime,
    ) -> Dict[str, Any]:
        normalized_worker_id = _normalize_text(worker_id)
        normalized_lease_id = _normalize_text(lease_id)
        if current is None:
            return {
                "valid": False,
                "ownership": self._blocked(None, WORKER_OWNERSHIP_REASON_LEASE_NOT_FOUND, "worker_lease_missing"),
            }
        if current.is_expired(now):
            return {
                "valid": False,
                "ownership": self._blocked(current, WORKER_OWNERSHIP_REASON_LEASE_EXPIRED, "worker_lease_expired"),
            }
        if current.worker_id != normalized_worker_id or current.lease_id != normalized_lease_id:
            return {
                "valid": False,
                "ownership": self._blocked(current, WORKER_OWNERSHIP_REASON_INVALID_LEASE, "worker_lease_mismatch"),
            }
        if int(fencing_token or 0) != current.fencing_token:
            return {
                "valid": False,
                "ownership": self._blocked(
                    current,
                    WORKER_OWNERSHIP_REASON_STALE_FENCING_TOKEN,
                    "stale_worker_fencing_token",
                ),
            }
        return {"valid": True, "ownership": self._success(current)}

    def _success(self, lease: RuntimeWorkerLease) -> Dict[str, Any]:
        payload = lease.to_dict()
        payload["owned"] = True
        payload["blocked_reason"] = ""
        return payload

    def _blocked(
        self,
        lease: RuntimeWorkerLease | None,
        reason: str,
        blocked_reason: str,
    ) -> Dict[str, Any]:
        payload = lease.to_dict() if lease is not None else {
            "contract_version": RUNTIME_WORKER_OWNERSHIP_CONTRACT_VERSION,
            "implemented": True,
            "adapter_kind": "in_memory",
            "durable": False,
            "run_id": "",
            "worker_id": "",
            "lease_id": "",
            "fencing_token": 0,
            "claimed_at": "",
            "lease_expires_at": "",
            "last_heartbeat_at": "",
        }
        payload["owned"] = False
        payload["lease_status"] = WORKER_OWNERSHIP_STATUS_BLOCKED
        payload["reason"] = reason
        payload["blocked_reason"] = blocked_reason
        return payload


class SQLAlchemyRuntimeWorkerOwnershipStore:
    """Durable ownership store backed by the app SQLAlchemy session factory."""

    def __init__(self, session_factory: Any, now_fn: Callable[[], datetime] | None = None) -> None:
        self._session_factory = session_factory
        self._now_fn = now_fn or _utc_now

    def claim_run(
        self,
        run_id: str,
        worker_id: str,
        lease_ttl_seconds: int = 60,
    ) -> Dict[str, Any]:
        normalized_run_id = _normalize_text(run_id)
        normalized_worker_id = _normalize_text(worker_id)
        if not normalized_run_id or not normalized_worker_id:
            return self._blocked(None, WORKER_OWNERSHIP_REASON_INVALID_LEASE, "worker_lease_invalid")
        now = self._now()
        db = self._session_factory()
        try:
            record = self._get_record(db, normalized_run_id)
            current = self._lease_from_record(record) if record is not None else None
            if current and not current.is_expired(now):
                if current.worker_id == normalized_worker_id:
                    refreshed = self._refresh_lease(current, now, lease_ttl_seconds, WORKER_OWNERSHIP_STATUS_REFRESHED)
                    self._write_record(db, record, refreshed)
                    db.commit()
                    return self._success(refreshed)
                return self._blocked(
                    current,
                    WORKER_OWNERSHIP_REASON_WORKER_OWNERSHIP_LOST,
                    "active_worker_lease_exists",
                )

            next_token = int(current.fencing_token if current else 0) + 1
            lease = RuntimeWorkerLease(
                run_id=normalized_run_id,
                worker_id=normalized_worker_id,
                lease_id=f"worker_lease:{normalized_run_id}:{uuid4().hex}",
                fencing_token=next_token,
                claimed_at=now,
                lease_expires_at=now + timedelta(seconds=max(int(lease_ttl_seconds or 0), 1)),
                last_heartbeat_at=now,
                lease_status=WORKER_OWNERSHIP_STATUS_CLAIMED,
                adapter_kind="sqlalchemy",
                durable=True,
            )
            self._write_record(db, record, lease)
            db.commit()
            return self._success(lease)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def heartbeat(
        self,
        run_id: str,
        worker_id: str,
        lease_id: str,
        lease_ttl_seconds: int = 60,
    ) -> Dict[str, Any]:
        now = self._now()
        db = self._session_factory()
        try:
            record = self._get_record(db, _normalize_text(run_id))
            current = self._lease_from_record(record) if record is not None else None
            validation = self._validate_current_lease(
                current=current,
                worker_id=worker_id,
                lease_id=lease_id,
                fencing_token=current.fencing_token if current else None,
                now=now,
            )
            if not validation["valid"]:
                return validation["ownership"]

            refreshed = self._refresh_lease(current, now, lease_ttl_seconds, WORKER_OWNERSHIP_STATUS_REFRESHED)
            self._write_record(db, record, refreshed)
            db.commit()
            return self._success(refreshed)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def validate_ownership(
        self,
        run_id: str,
        worker_id: str,
        lease_id: str,
        fencing_token: int,
    ) -> Dict[str, Any]:
        db = self._session_factory()
        try:
            record = self._get_record(db, _normalize_text(run_id))
            current = self._lease_from_record(record) if record is not None else None
            validation = self._validate_current_lease(
                current=current,
                worker_id=worker_id,
                lease_id=lease_id,
                fencing_token=fencing_token,
                now=self._now(),
            )
            if not validation["valid"]:
                return validation["ownership"]
            return self._success(
                RuntimeWorkerLease(
                    run_id=current.run_id,
                    worker_id=current.worker_id,
                    lease_id=current.lease_id,
                    fencing_token=current.fencing_token,
                    claimed_at=current.claimed_at,
                    lease_expires_at=current.lease_expires_at,
                    last_heartbeat_at=current.last_heartbeat_at,
                    lease_status=WORKER_OWNERSHIP_STATUS_VALIDATED,
                    adapter_kind="sqlalchemy",
                    durable=True,
                )
            )
        finally:
            db.close()

    def get_lease(self, run_id: str) -> Dict[str, Any] | None:
        db = self._session_factory()
        try:
            record = self._get_record(db, _normalize_text(run_id))
            lease = self._lease_from_record(record) if record is not None else None
            return lease.to_dict() if lease is not None else None
        finally:
            db.close()

    def build_contract(self) -> Dict[str, Any]:
        return build_worker_ownership_contract(adapter_kind="sqlalchemy", durable=True)

    def _now(self) -> datetime:
        return _ensure_utc(self._now_fn()) or _utc_now()

    def _get_record(self, db: Any, run_id: str) -> Any:
        try:
            from models import RuntimeWorkerOwnershipRecord
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.models import RuntimeWorkerOwnershipRecord

        return db.query(RuntimeWorkerOwnershipRecord).filter(
            RuntimeWorkerOwnershipRecord.run_id == run_id
        ).first()

    def _write_record(self, db: Any, record: Any, lease: RuntimeWorkerLease) -> None:
        try:
            from models import RuntimeWorkerOwnershipRecord
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.models import RuntimeWorkerOwnershipRecord

        if record is None:
            record = RuntimeWorkerOwnershipRecord(run_id=lease.run_id)
            db.add(record)
        record.worker_id = lease.worker_id
        record.lease_id = lease.lease_id
        record.fencing_token = lease.fencing_token
        record.claimed_at = _ensure_utc(lease.claimed_at)
        record.lease_expires_at = _ensure_utc(lease.lease_expires_at)
        record.last_heartbeat_at = _ensure_utc(lease.last_heartbeat_at)
        record.lease_status = lease.lease_status

    def _lease_from_record(self, record: Any) -> RuntimeWorkerLease:
        return RuntimeWorkerLease(
            run_id=_normalize_text(record.run_id),
            worker_id=_normalize_text(record.worker_id),
            lease_id=_normalize_text(record.lease_id),
            fencing_token=int(record.fencing_token or 0),
            claimed_at=_ensure_utc(record.claimed_at) or _utc_now(),
            lease_expires_at=_ensure_utc(record.lease_expires_at) or _utc_now(),
            last_heartbeat_at=_ensure_utc(record.last_heartbeat_at) or _utc_now(),
            lease_status=_normalize_text(record.lease_status) or WORKER_OWNERSHIP_STATUS_CLAIMED,
            adapter_kind="sqlalchemy",
            durable=True,
        )

    def _refresh_lease(
        self,
        lease: RuntimeWorkerLease,
        now: datetime,
        lease_ttl_seconds: int,
        lease_status: str,
    ) -> RuntimeWorkerLease:
        return RuntimeWorkerLease(
            run_id=lease.run_id,
            worker_id=lease.worker_id,
            lease_id=lease.lease_id,
            fencing_token=lease.fencing_token,
            claimed_at=lease.claimed_at,
            lease_expires_at=now + timedelta(seconds=max(int(lease_ttl_seconds or 0), 1)),
            last_heartbeat_at=now,
            lease_status=lease_status,
            adapter_kind="sqlalchemy",
            durable=True,
        )

    def _validate_current_lease(
        self,
        *,
        current: RuntimeWorkerLease | None,
        worker_id: str,
        lease_id: str,
        fencing_token: int | None,
        now: datetime,
    ) -> Dict[str, Any]:
        normalized_worker_id = _normalize_text(worker_id)
        normalized_lease_id = _normalize_text(lease_id)
        if current is None:
            return {
                "valid": False,
                "ownership": self._blocked(None, WORKER_OWNERSHIP_REASON_LEASE_NOT_FOUND, "worker_lease_missing"),
            }
        if current.is_expired(now):
            return {
                "valid": False,
                "ownership": self._blocked(current, WORKER_OWNERSHIP_REASON_LEASE_EXPIRED, "worker_lease_expired"),
            }
        if current.worker_id != normalized_worker_id or current.lease_id != normalized_lease_id:
            return {
                "valid": False,
                "ownership": self._blocked(current, WORKER_OWNERSHIP_REASON_INVALID_LEASE, "worker_lease_mismatch"),
            }
        if int(fencing_token or 0) != current.fencing_token:
            return {
                "valid": False,
                "ownership": self._blocked(
                    current,
                    WORKER_OWNERSHIP_REASON_STALE_FENCING_TOKEN,
                    "stale_worker_fencing_token",
                ),
            }
        return {"valid": True, "ownership": self._success(current)}

    def _success(self, lease: RuntimeWorkerLease) -> Dict[str, Any]:
        payload = lease.to_dict()
        payload["owned"] = True
        payload["blocked_reason"] = ""
        return payload

    def _blocked(
        self,
        lease: RuntimeWorkerLease | None,
        reason: str,
        blocked_reason: str,
    ) -> Dict[str, Any]:
        payload = lease.to_dict() if lease is not None else {
            "contract_version": RUNTIME_WORKER_OWNERSHIP_CONTRACT_VERSION,
            "implemented": True,
            "adapter_kind": "sqlalchemy",
            "durable": True,
            "run_id": "",
            "worker_id": "",
            "lease_id": "",
            "fencing_token": 0,
            "claimed_at": "",
            "lease_expires_at": "",
            "last_heartbeat_at": "",
        }
        payload["owned"] = False
        payload["lease_status"] = WORKER_OWNERSHIP_STATUS_BLOCKED
        payload["reason"] = reason
        payload["blocked_reason"] = blocked_reason
        return payload


_runtime_worker_ownership_store: Any | None = None
_runtime_worker_ownership_store_mode: str | None = None
_runtime_worker_ownership_fallback_reason = ""


class WorkerOwnershipStoreFallback:
    """In-memory fallback that keeps configured mode evidence visible."""

    def __init__(self, fallback: InMemoryRuntimeWorkerOwnershipStore, *, configured_mode: str, fallback_reason: str) -> None:
        self._fallback = fallback
        self.configured_mode = str(configured_mode or "").strip()
        self.fallback_reason = str(fallback_reason or "").strip()

    def claim_run(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return self._fallback.claim_run(*args, **kwargs)

    def heartbeat(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return self._fallback.heartbeat(*args, **kwargs)

    def validate_ownership(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return self._fallback.validate_ownership(*args, **kwargs)

    def get_lease(self, *args: Any, **kwargs: Any) -> Dict[str, Any] | None:
        return self._fallback.get_lease(*args, **kwargs)

    def build_contract(self) -> Dict[str, Any]:
        contract = self._fallback.build_contract()
        contract["configured_mode"] = self.configured_mode
        contract["fallback_active"] = True
        contract["fallback_reason"] = self.fallback_reason
        return contract


def get_runtime_worker_ownership_store() -> Any:
    global _runtime_worker_ownership_store, _runtime_worker_ownership_store_mode, _runtime_worker_ownership_fallback_reason
    mode = get_worker_ownership_store_mode()
    if _runtime_worker_ownership_store is not None and _runtime_worker_ownership_store_mode == mode:
        return _runtime_worker_ownership_store
    _runtime_worker_ownership_store_mode = mode
    _runtime_worker_ownership_fallback_reason = ""
    if mode == "memory_only":
        _runtime_worker_ownership_store = InMemoryRuntimeWorkerOwnershipStore()
        return _runtime_worker_ownership_store
    try:
        try:
            from database import Base, SessionLocal, engine
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.database import Base, SessionLocal, engine
        try:
            import models  # noqa: F401
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            import backend.models  # noqa: F401

        Base.metadata.create_all(bind=engine)
        _runtime_worker_ownership_store = SQLAlchemyRuntimeWorkerOwnershipStore(SessionLocal)
        return _runtime_worker_ownership_store
    except Exception as exc:
        if mode == "strict_sql":
            raise RuntimeError(
                "Worker ownership store strict_sql mode requires a working SQL backend."
            ) from exc
        _runtime_worker_ownership_fallback_reason = str(exc or "").strip()
        _runtime_worker_ownership_store = WorkerOwnershipStoreFallback(
            InMemoryRuntimeWorkerOwnershipStore(),
            configured_mode=mode,
            fallback_reason=_runtime_worker_ownership_fallback_reason,
        )
    return _runtime_worker_ownership_store


def get_worker_ownership_store_mode() -> str:
    mode = str(WORKER_OWNERSHIP_STORE_MODE or "").strip().lower() or "memory_only"
    return mode if mode in ALLOWED_WORKER_OWNERSHIP_STORE_MODES else "memory_only"


def set_worker_ownership_store_mode(mode: str) -> str:
    normalized_mode = str(mode or "").strip().lower()
    if normalized_mode not in ALLOWED_WORKER_OWNERSHIP_STORE_MODES:
        raise ValueError(
            "worker_ownership_store_mode only supports memory_only / prefer_sql_with_fallback / strict_sql"
        )
    global WORKER_OWNERSHIP_STORE_MODE, _runtime_worker_ownership_store, _runtime_worker_ownership_store_mode
    WORKER_OWNERSHIP_STORE_MODE = normalized_mode
    _runtime_worker_ownership_store = None
    _runtime_worker_ownership_store_mode = None
    return WORKER_OWNERSHIP_STORE_MODE
