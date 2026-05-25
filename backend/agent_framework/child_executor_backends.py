from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping

from .child_executor_sandbox_worker_backend import (
    build_sandbox_worker_backend_adapter_contract,
)


CHILD_EXECUTOR_BACKEND_REGISTRY_CONTRACT_VERSION = "phase-ii-child-executor-backend-registry-v1"

DEFAULT_CHILD_EXECUTOR_BACKENDS = (
    {
        "backend_id": "embedded_sdk_worker",
        "label": "Embedded SDK worker candidate",
        "status": "candidate",
        "dispatch_ready": False,
        "dispatch_mode": "not_implemented",
        "supported_handoff_mode": "relationship_only",
        "adapter_kind": "",
        "adapter_contract_ready": False,
        "sandbox_guard_ready": False,
        "audit_ready": False,
        "idempotency_ready": False,
        "missing_guard_blockers": [],
        "adapter_contract": {},
        "blockers": [
            "real_child_executor_dispatch_not_implemented",
            "worker_backend_binding_not_enabled",
        ],
    },
)


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def build_child_executor_sandbox_worker_backend_entry(
    *,
    backend_id: str,
    label: str,
    adapter_contract: Mapping[str, Any] | None = None,
    status: str = "ready",
    supported_handoff_mode: str = "sandbox_worker",
) -> Dict[str, Any]:
    contract = dict(adapter_contract or build_sandbox_worker_backend_adapter_contract(backend_id=backend_id))
    missing_guard_blockers = [
        f"sandbox_guard_missing:{_normalize_text(item)}"
        for item in (contract.get("missing_guards") or [])
        if _normalize_text(item)
    ]
    adapter_ready = bool(contract.get("adapter_contract_ready"))
    sandbox_ready = bool(contract.get("sandbox_guard_ready"))
    audit_ready = bool(contract.get("audit_ready"))
    idempotency_ready = bool(contract.get("idempotency_ready"))
    dispatch_ready = adapter_ready and sandbox_ready and audit_ready and idempotency_ready
    blockers = []
    if not adapter_ready:
        blockers.append("sandbox_adapter_contract_not_ready")
    if not sandbox_ready:
        blockers.append("sandbox_guard_not_ready")
    if not audit_ready:
        blockers.append("sandbox_audit_not_ready")
    if not idempotency_ready:
        blockers.append("sandbox_idempotency_not_ready")
    blockers.extend(missing_guard_blockers)
    return {
        "backend_id": _normalize_text(backend_id),
        "label": _normalize_text(label),
        "status": _normalize_text(status) if dispatch_ready else "blocked",
        "dispatch_ready": dispatch_ready,
        "dispatch_mode": "sandbox_worker",
        "supported_handoff_mode": _normalize_text(supported_handoff_mode),
        "adapter_kind": _normalize_text(contract.get("adapter_kind")) or "sandbox_worker",
        "adapter_contract_ready": adapter_ready,
        "sandbox_guard_ready": sandbox_ready,
        "audit_ready": audit_ready,
        "idempotency_ready": idempotency_ready,
        "missing_guard_blockers": missing_guard_blockers,
        "adapter_contract": contract,
        "blockers": list(dict.fromkeys(blockers)),
    }


def _normalize_backend_entry(entry: Mapping[str, Any]) -> Dict[str, Any]:
    normalized = dict(entry or {})
    return {
        "backend_id": _normalize_text(normalized.get("backend_id")),
        "label": _normalize_text(normalized.get("label")),
        "status": _normalize_text(normalized.get("status")),
        "dispatch_ready": bool(normalized.get("dispatch_ready")),
        "dispatch_mode": _normalize_text(normalized.get("dispatch_mode")),
        "supported_handoff_mode": _normalize_text(normalized.get("supported_handoff_mode")),
        "adapter_kind": _normalize_text(normalized.get("adapter_kind")),
        "adapter_contract_ready": bool(normalized.get("adapter_contract_ready")),
        "sandbox_guard_ready": bool(normalized.get("sandbox_guard_ready")),
        "audit_ready": bool(normalized.get("audit_ready")),
        "idempotency_ready": bool(normalized.get("idempotency_ready")),
        "missing_guard_blockers": [
            _normalize_text(item)
            for item in (normalized.get("missing_guard_blockers") or [])
            if _normalize_text(item)
        ],
        "adapter_contract": dict(normalized.get("adapter_contract") or {}),
        "blockers": [
            _normalize_text(item)
            for item in (normalized.get("blockers") or [])
            if _normalize_text(item)
        ],
    }


def build_child_executor_backend_registry_contract(
    *,
    extra_backends: Iterable[Mapping[str, Any]] | None = None,
) -> Dict[str, Any]:
    backends = [_normalize_backend_entry(item) for item in DEFAULT_CHILD_EXECUTOR_BACKENDS]
    backends.extend(_normalize_backend_entry(item) for item in (extra_backends or []))
    backends_by_id = {str(item["backend_id"]): dict(item) for item in backends}
    ready_backends = [item for item in backends if bool(item.get("dispatch_ready"))]
    return {
        "contract_version": CHILD_EXECUTOR_BACKEND_REGISTRY_CONTRACT_VERSION,
        "overall_status": "ready" if ready_backends else "relationship_only",
        "default_backend_id": "embedded_sdk_worker",
        "backend_count": len(backends),
        "ready_backend_count": len(ready_backends),
        "backends": backends,
        "backends_by_id": backends_by_id,
        "non_goals": [
            "real_child_executor_dispatch",
            "worker_process_allocation",
            "sandbox_or_queue_execution",
        ],
    }


def resolve_child_executor_backend(backend_id: str | None) -> Dict[str, Any]:
    normalized_backend_id = str(backend_id or "").strip()
    registry = build_child_executor_backend_registry_contract()
    backend = dict((registry.get("backends_by_id") or {}).get(normalized_backend_id) or {})
    if not normalized_backend_id:
        return {
            "backend_id": "",
            "known": False,
            "status": "missing",
            "dispatch_ready": False,
            "dispatch_mode": "",
            "supported_handoff_mode": "",
            "blockers": ["worker_runtime_backend_missing"],
        }
    if not backend:
        return {
            "backend_id": normalized_backend_id,
            "known": False,
            "status": "unknown",
            "dispatch_ready": False,
            "dispatch_mode": "",
            "supported_handoff_mode": "",
            "blockers": ["unknown_child_executor_backend"],
        }
    return {
        "backend_id": normalized_backend_id,
        "known": True,
        "status": str(backend.get("status") or "").strip(),
        "dispatch_ready": bool(backend.get("dispatch_ready")),
        "dispatch_mode": str(backend.get("dispatch_mode") or "").strip(),
        "supported_handoff_mode": str(backend.get("supported_handoff_mode") or "").strip(),
        "adapter_kind": str(backend.get("adapter_kind") or "").strip(),
        "adapter_contract_ready": bool(backend.get("adapter_contract_ready")),
        "sandbox_guard_ready": bool(backend.get("sandbox_guard_ready")),
        "audit_ready": bool(backend.get("audit_ready")),
        "idempotency_ready": bool(backend.get("idempotency_ready")),
        "missing_guard_blockers": [
            str(item).strip()
            for item in (backend.get("missing_guard_blockers") or [])
            if str(item or "").strip()
        ],
        "adapter_contract": dict(backend.get("adapter_contract") or {}),
        "blockers": [
            str(item).strip()
            for item in (backend.get("blockers") or [])
            if str(item or "").strip()
        ],
    }
