"""Recovery operation contracts for Embedded SDK recovery attempts."""

from __future__ import annotations

from typing import Any, Dict
from uuid import uuid4

from .persistence import build_embedded_sdk_persistence_interface
from .recovery_audit_readiness import build_recovery_audit_production_readiness_contract


EMBEDDED_SDK_RECOVERY_OPERATION_STATUSES = [
    "attempted",
    "recovered",
    "blocked",
    "failed",
]

EMBEDDED_SDK_RECOVERY_OPERATION_ENTRYPOINTS = [
    {
        "entrypoint": "submit_approval.approved",
        "method": "submit_approval",
        "mode": "approved",
        "continuation_kind": "tool_approval",
        "auditable": True,
    },
    {
        "entrypoint": "resume_run.continue_loop",
        "method": "resume_run",
        "mode": "continue_loop",
        "continuation_kind": "loop",
        "auditable": True,
    },
]

EMBEDDED_SDK_RECOVERY_RETRY_MAX_ATTEMPTS = 3
EMBEDDED_SDK_RECOVERY_RETRY_BACKOFF_STRATEGY = "bounded_exponential"
EMBEDDED_SDK_RECOVERY_RETRYABLE_REASONS = [
    "transient_workspace_unavailable",
    "workspace_backend_fallback_active",
    "workspace_backend_unavailable",
]
EMBEDDED_SDK_RECOVERY_TERMINAL_REASONS = [
    "missing_registered_binding",
    "denied",
    "already_resolved",
    "stale_worker_fencing_token",
    "worker_ownership_lost",
]


def build_recovery_operation_contract() -> Dict[str, Any]:
    return {
        "contract_version": "phase-ii-durable-recovery-operation-v1",
        "operation_statuses": list(EMBEDDED_SDK_RECOVERY_OPERATION_STATUSES),
        "entrypoints": [dict(item) for item in EMBEDDED_SDK_RECOVERY_OPERATION_ENTRYPOINTS],
        "retry_policy": build_recovery_retry_policy_contract(),
        "recovery_audit_production_readiness": build_recovery_audit_production_readiness_contract(),
        "worker_ownership": {
            "implemented": False,
            "boundary": "worker_lease_not_implemented",
            "description": "Recovery operation evidence is recorded, but cross-instance worker ownership is not implemented.",
        },
        "non_executable_payload": True,
    }


def build_recovery_retry_policy_contract() -> Dict[str, Any]:
    return {
        "contract_version": "phase-ii-recovery-retry-protocol-v1",
        "implemented": False,
        "evidence_supported": True,
        "max_attempts": EMBEDDED_SDK_RECOVERY_RETRY_MAX_ATTEMPTS,
        "backoff_strategy": EMBEDDED_SDK_RECOVERY_RETRY_BACKOFF_STRATEGY,
        "retryable_reasons": list(EMBEDDED_SDK_RECOVERY_RETRYABLE_REASONS),
        "terminal_reasons": list(EMBEDDED_SDK_RECOVERY_TERMINAL_REASONS),
        "non_executable_payload": True,
    }


def is_recovery_reason_retryable(recovery_reason: str) -> bool:
    return str(recovery_reason or "").strip() in EMBEDDED_SDK_RECOVERY_RETRYABLE_REASONS


def is_recovery_reason_terminal(recovery_reason: str) -> bool:
    return str(recovery_reason or "").strip() in EMBEDDED_SDK_RECOVERY_TERMINAL_REASONS


def recovery_entrypoint_for_continuation_kind(continuation_kind: str) -> str:
    normalized_kind = str(continuation_kind or "").strip()
    if normalized_kind == "tool_approval":
        return "submit_approval.approved"
    if normalized_kind == "loop":
        return "resume_run.continue_loop"
    return ""


def build_recovery_retry_evidence(
    *,
    attempt_number: int,
    previous_operation_id: str,
    idempotency_key: str,
    recovery_reason: str,
    max_attempts: int = EMBEDDED_SDK_RECOVERY_RETRY_MAX_ATTEMPTS,
) -> Dict[str, Any]:
    normalized_reason = str(recovery_reason or "").strip()
    normalized_attempt = max(int(attempt_number or 0), 1)
    normalized_max_attempts = max(int(max_attempts or 0), 1)
    retryable = is_recovery_reason_retryable(normalized_reason)
    terminal = is_recovery_reason_terminal(normalized_reason)
    if terminal:
        status = "terminal"
    elif normalized_attempt >= normalized_max_attempts:
        status = "exhausted"
    elif retryable:
        status = "retryable"
    else:
        status = "not_retryable"
    retry_terminal = terminal or status == "exhausted"
    return {
        "contract_version": "phase-ii-recovery-retry-protocol-v1",
        "attempt_number": normalized_attempt,
        "max_attempts": normalized_max_attempts,
        "previous_operation_id": str(previous_operation_id or "").strip(),
        "idempotency_key": str(idempotency_key or "").strip(),
        "recovery_reason": normalized_reason,
        "retryable": retryable,
        "terminal": retry_terminal,
        "status": status,
        "backoff_strategy": EMBEDDED_SDK_RECOVERY_RETRY_BACKOFF_STRATEGY,
    }


def _build_default_worker_ownership_payload() -> Dict[str, Any]:
    return {
        "implemented": False,
        "boundary": "worker_lease_not_implemented",
        "blocked_reason": "worker_ownership_not_implemented",
    }


def _compact_worker_ownership_payload(worker_ownership: Dict[str, Any] | None) -> Dict[str, Any]:
    if not worker_ownership:
        return _build_default_worker_ownership_payload()

    ownership = dict(worker_ownership or {})
    compact = {
        "implemented": bool(ownership.get("implemented", True)),
        "worker_id": str(ownership.get("worker_id") or "").strip(),
        "lease_id": str(ownership.get("lease_id") or "").strip(),
        "fencing_token": int(ownership.get("fencing_token") or 0),
        "lease_status": str(ownership.get("lease_status") or "").strip(),
    }
    for optional_key in [
        "contract_version",
        "adapter_kind",
        "owned",
        "run_id",
        "claimed_at",
        "lease_expires_at",
        "last_heartbeat_at",
        "reason",
        "blocked_reason",
        "boundary",
        "auto_claim_enablement_gate",
    ]:
        if optional_key in ownership:
            compact[optional_key] = ownership[optional_key]
    return compact


def _compact_recovery_retry_payload(retry: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not retry:
        return None

    retry_dict = dict(retry or {})
    compact = {
        "contract_version": str(
            retry_dict.get("contract_version") or "phase-ii-recovery-retry-protocol-v1"
        ).strip(),
        "attempt_number": max(int(retry_dict.get("attempt_number") or 0), 1),
        "max_attempts": max(int(retry_dict.get("max_attempts") or 0), 1),
        "previous_operation_id": str(retry_dict.get("previous_operation_id") or "").strip(),
        "idempotency_key": str(retry_dict.get("idempotency_key") or "").strip(),
        "recovery_reason": str(retry_dict.get("recovery_reason") or "").strip(),
        "retryable": bool(retry_dict.get("retryable")),
        "terminal": bool(retry_dict.get("terminal")),
        "status": str(retry_dict.get("status") or "").strip(),
    }
    for optional_key in ["backoff_strategy", "next_delay_seconds", "blocked_reason"]:
        if optional_key in retry_dict:
            compact[optional_key] = retry_dict[optional_key]
    return compact


def build_recovery_operation_record(
    *,
    run_id: str,
    entrypoint: str,
    operation_status: str,
    recovery_reason: str,
    continuation_kind: str,
    continuation_id: str,
    workspace_backend: Dict[str, Any],
    recorded_at: str,
    binding_ids: Dict[str, str] | None = None,
    blocked_reason: str = "",
    descriptor_present: bool = False,
    missing_binding_ids: list[str] | None = None,
    persistence_interface: Dict[str, Any] | None = None,
    worker_ownership: Dict[str, Any] | None = None,
    retry: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    normalized_entrypoint = str(entrypoint or "").strip()
    normalized_status = str(operation_status or "").strip() or "attempted"
    if normalized_status not in EMBEDDED_SDK_RECOVERY_OPERATION_STATUSES:
        normalized_status = "failed"
    workspace_backend_dict = dict(workspace_backend or {})
    persistence = dict(
        persistence_interface
        or build_embedded_sdk_persistence_interface(workspace_backend_dict)
    )
    normalized_run_id = str(run_id or "").strip()
    normalized_continuation_id = str(continuation_id or "").strip()
    record = {
        "contract_version": "phase-ii-durable-recovery-operation-v1",
        "operation_id": f"recovery_operation:{normalized_run_id}:{normalized_entrypoint or 'unknown'}:{uuid4().hex}",
        "run_id": normalized_run_id,
        "entrypoint": normalized_entrypoint,
        "operation_status": normalized_status,
        "recovery_reason": str(recovery_reason or "").strip(),
        "blocked_reason": str(blocked_reason or "").strip(),
        "checkpoint_id": f"checkpoint:{normalized_run_id}:{normalized_continuation_id or normalized_run_id}",
        "resume_cursor_id": f"cursor:{normalized_run_id}:{normalized_entrypoint or 'none'}",
        "continuation_ref": {
            "continuation_kind": str(continuation_kind or "").strip(),
            "continuation_id": normalized_continuation_id,
            "descriptor_present": bool(descriptor_present),
            "binding_ids": dict(binding_ids or {}),
            "missing_binding_ids": list(missing_binding_ids or []),
        },
        "workspace_backend": {
            "backend_kind": str(workspace_backend_dict.get("backend_kind") or "").strip(),
            "backend_mode": str(workspace_backend_dict.get("backend_mode") or "").strip(),
            "durable": bool(workspace_backend_dict.get("durable")),
            "fallback_active": bool(workspace_backend_dict.get("fallback_active")),
            "fallback_reason": str(workspace_backend_dict.get("fallback_reason") or "").strip(),
            "last_error": str(workspace_backend_dict.get("last_error") or "").strip(),
        },
        "persistence_posture": str(persistence.get("persistence_posture") or "").strip(),
        "worker_ownership": _compact_worker_ownership_payload(worker_ownership),
        "recorded_at": recorded_at,
    }
    retry_payload = _compact_recovery_retry_payload(retry)
    if retry_payload is not None:
        record["retry"] = retry_payload
    return record
