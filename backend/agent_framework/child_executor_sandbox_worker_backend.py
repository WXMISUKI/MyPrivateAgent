"""Contracts for sandbox-backed child executor worker adapters."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Mapping


CHILD_EXECUTOR_SANDBOX_WORKER_BACKEND_CONTRACT_VERSION = (
    "phase-ii-child-executor-sandbox-worker-backend-v1"
)
CHILD_EXECUTOR_SANDBOX_BACKEND_BINDING_CONTRACT_VERSION = (
    "phase-ii-child-executor-sandbox-backend-binding-v1"
)

REQUIRED_SANDBOX_GUARDS = (
    "isolation",
    "resource_limits",
    "timeout_policy",
    "environment_allowlist",
    "workspace_boundary",
    "network_policy",
    "audit_recording",
    "idempotency_key",
)

REQUIRED_SANDBOX_ATTEMPT_FIELDS = (
    "attempt_id",
    "backend_id",
    "child_run_id",
    "status",
    "will_dispatch",
    "dispatch_started_at",
    "dispatch_finished_at",
    "sandbox_ref",
    "output_ref",
    "audit_ref",
    "error_code",
    "retryable",
)

_UNSAFE_PAYLOAD_KEYS = {
    "callable",
    "handler",
    "provider_client",
    "process_handle",
    "open_stream",
    "stream_iterator",
    "tool_executor",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_bool(value: Any) -> bool:
    return bool(value)


def build_sandbox_worker_backend_adapter_contract(
    *,
    backend_id: str,
    adapter_kind: str = "sandbox_worker",
    sandbox_mode: str = "process_sandbox",
    execution_mode: str = "bounded_child_executor",
    input_contract: Mapping[str, Any] | None = None,
    output_contract: Mapping[str, Any] | None = None,
    resource_limits: Mapping[str, Any] | None = None,
    isolation_guards: Mapping[str, Any] | None = None,
    audit_hooks: Mapping[str, Any] | None = None,
    idempotency: Mapping[str, Any] | None = None,
    failure_modes: list[str] | None = None,
) -> Dict[str, Any]:
    """Build compact sandbox adapter contract evidence.

    The helper only describes readiness. It never starts a worker.
    """

    normalized_backend_id = _normalize_text(backend_id)
    normalized_input = dict(input_contract or {})
    normalized_output = dict(output_contract or {})
    normalized_limits = dict(resource_limits or {})
    normalized_guards = dict(isolation_guards or {})
    normalized_audit = dict(audit_hooks or {})
    normalized_idempotency = dict(idempotency or {})
    present_guards = set()
    if normalized_guards.get("process_or_worker_isolation"):
        present_guards.add("isolation")
    if normalized_limits:
        present_guards.add("resource_limits")
    if normalized_limits.get("timeout_seconds") or normalized_limits.get("timeout_policy"):
        present_guards.add("timeout_policy")
    if normalized_guards.get("environment_allowlist"):
        present_guards.add("environment_allowlist")
    if normalized_guards.get("workspace_boundary"):
        present_guards.add("workspace_boundary")
    if normalized_guards.get("network_policy"):
        present_guards.add("network_policy")
    if normalized_audit.get("record_dispatch"):
        present_guards.add("audit_recording")
    if normalized_idempotency.get("idempotency_key_required"):
        present_guards.add("idempotency_key")

    missing_guards = [
        guard for guard in REQUIRED_SANDBOX_GUARDS if guard not in present_guards
    ]
    ready = bool(
        normalized_backend_id
        and normalized_input
        and normalized_output
        and not missing_guards
    )
    return {
        "contract_version": CHILD_EXECUTOR_SANDBOX_WORKER_BACKEND_CONTRACT_VERSION,
        "backend_id": normalized_backend_id,
        "adapter_kind": _normalize_text(adapter_kind) or "sandbox_worker",
        "sandbox_mode": _normalize_text(sandbox_mode),
        "execution_mode": _normalize_text(execution_mode),
        "input_contract": normalized_input,
        "output_contract": normalized_output,
        "resource_limits": normalized_limits,
        "isolation_guards": normalized_guards,
        "audit_hooks": normalized_audit,
        "idempotency": normalized_idempotency,
        "failure_modes": [
            _normalize_text(item)
            for item in (failure_modes or [
                "sandbox_guard_missing",
                "unsafe_payload",
                "worker_start_failed",
                "worker_timeout",
            ])
            if _normalize_text(item)
        ],
        "required_guards": list(REQUIRED_SANDBOX_GUARDS),
        "missing_guards": missing_guards,
        "adapter_contract_ready": ready,
        "sandbox_guard_ready": not missing_guards,
        "audit_ready": "audit_recording" in present_guards,
        "idempotency_ready": "idempotency_key" in present_guards,
        "dispatch_ready_candidate": ready,
    }


def build_child_executor_sandbox_backend_binding_contract(
    *,
    backend_id: str,
    backend_registry_entry: Mapping[str, Any] | None = None,
    adapter_contract: Mapping[str, Any] | None = None,
    dispatcher_backend_adapters: Mapping[str, Any] | None = None,
    explicit_binding: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Describe whether a sandbox backend adapter is bound to the dispatcher.

    The binding contract is pure evidence. It inspects supplied metadata and
    callability, but never invokes the adapter.
    """

    normalized_backend_id = _normalize_text(backend_id)
    registry_entry = dict(backend_registry_entry or {})
    adapter = dict(adapter_contract or registry_entry.get("adapter_contract") or {})
    explicit = dict(explicit_binding or {})
    dispatcher_adapters = dict(dispatcher_backend_adapters or {})
    explicit_binding_present = bool(explicit.get("ready")) or bool(
        _normalize_text(explicit.get("binding_status"))
    )
    explicit_binding_ready = bool(explicit.get("ready")) and (
        _normalize_text(explicit.get("binding_status")) in {"", "ready"}
    )
    adapter_kind = _normalize_text(
        registry_entry.get("adapter_kind") or adapter.get("adapter_kind")
    )
    sandbox_backend_selected = adapter_kind == "sandbox_worker"
    adapter_contract_ready = bool(
        adapter.get("adapter_contract_ready")
        if "adapter_contract_ready" in adapter
        else registry_entry.get("adapter_contract_ready")
    )
    sandbox_guard_ready = bool(
        adapter.get("sandbox_guard_ready")
        if "sandbox_guard_ready" in adapter
        else registry_entry.get("sandbox_guard_ready")
    )
    audit_ready = bool(
        adapter.get("audit_ready")
        if "audit_ready" in adapter
        else registry_entry.get("audit_ready")
    )
    idempotency_ready = bool(
        adapter.get("idempotency_ready")
        if "idempotency_ready" in adapter
        else registry_entry.get("idempotency_ready")
    )
    callable_adapter = callable(dispatcher_adapters.get(normalized_backend_id))
    dry_run_attempt: Dict[str, Any] = {}
    validation = {
        "valid": False,
        "error_code": "sandbox_backend_not_selected",
        "missing_fields": list(REQUIRED_SANDBOX_ATTEMPT_FIELDS),
    }
    if normalized_backend_id and sandbox_backend_selected:
        dry_run_attempt = build_sandbox_dispatch_attempt_envelope(
            attempt_id="binding-dry-run-attempt",
            backend_id=normalized_backend_id,
            child_run_id="binding-dry-run-child",
            status="dry_run",
            will_dispatch=False,
            sandbox_ref="sandbox://binding-dry-run-attempt",
            output_ref="artifact://binding-dry-run-child/output",
            audit_ref="trace://binding-dry-run-attempt",
        )
        validation = validate_sandbox_dispatch_attempt(dry_run_attempt)

    attempt_envelope_supported = bool(validation.get("valid"))
    audit_idempotency_ready = audit_ready and idempotency_ready
    missing_sections: list[str] = []
    if not explicit_binding_present:
        missing_sections.append("explicit_binding")
    elif not explicit_binding_ready:
        missing_sections.append("explicit_binding_ready")
    if not normalized_backend_id:
        missing_sections.append("backend_id")
    if not registry_entry:
        missing_sections.append("backend_registry_entry")
    if not sandbox_backend_selected:
        missing_sections.append("sandbox_backend_selected")
    if not adapter_contract_ready:
        missing_sections.append("adapter_contract_ready")
    if not sandbox_guard_ready:
        missing_sections.append("sandbox_guard_ready")
    if not audit_ready:
        missing_sections.append("audit_ready")
    if not idempotency_ready:
        missing_sections.append("idempotency_ready")
    if not callable_adapter:
        missing_sections.append("dispatcher_backend_adapter")
    if not attempt_envelope_supported:
        missing_sections.append("attempt_envelope_supported")
    for item in (
        registry_entry.get("missing_guard_blockers")
        or adapter.get("missing_guard_blockers")
        or []
    ):
        value = _normalize_text(item)
        if value:
            missing_sections.append(value)

    missing_sections = list(dict.fromkeys(missing_sections))
    ready = not missing_sections
    return {
        "contract_version": CHILD_EXECUTOR_SANDBOX_BACKEND_BINDING_CONTRACT_VERSION,
        "overall_status": "ready" if ready else "blocked",
        "ready": ready,
        "backend_id": normalized_backend_id,
        "adapter_kind": adapter_kind,
        "adapter_contract_status": "ready" if adapter_contract_ready else "blocked",
        "adapter_contract_ready": adapter_contract_ready,
        "sandbox_backend_selected": sandbox_backend_selected,
        "sandbox_guard_ready": sandbox_guard_ready,
        "audit_ready": audit_ready,
        "idempotency_ready": idempotency_ready,
        "audit_idempotency_ready": audit_idempotency_ready,
        "binding_status": "ready" if ready else "blocked",
        "explicit_binding_present": explicit_binding_present,
        "explicit_binding_ready": explicit_binding_ready,
        "explicit_binding_source": _normalize_text(explicit.get("binding_source")),
        "dispatcher_binding_ready": callable_adapter,
        "dispatcher_adapter_callable": callable_adapter,
        "attempt_envelope_supported": attempt_envelope_supported,
        "attempt_validation_error_code": _normalize_text(validation.get("error_code")),
        "attempt_validation_missing_fields": [
            _normalize_text(item)
            for item in (validation.get("missing_fields") or [])
            if _normalize_text(item)
        ],
        "dry_run_attempt_status": _normalize_text(dry_run_attempt.get("status")),
        "will_dispatch": False,
        "production_dispatch_authorized": False,
        "missing_sections": missing_sections,
        "blocked_reason": "" if ready else (missing_sections[0] if missing_sections else "blocked"),
        "next_allowed_action": (
            "record_dispatcher_backend_binding"
            if ready
            else "complete_sandbox_backend_dispatcher_binding"
        ),
        "non_goals": [
            "invoke_backend_adapter",
            "start_child_executor_worker",
            "enable_dispatcher_by_default",
            "schedule_retry",
        ],
    }


def build_sandbox_dispatch_attempt_envelope(
    *,
    attempt_id: str,
    backend_id: str,
    child_run_id: str,
    status: str,
    will_dispatch: bool,
    dispatch_started_at: str | None = None,
    dispatch_finished_at: str | None = None,
    sandbox_ref: str = "",
    output_ref: str = "",
    audit_ref: str = "",
    error_code: str = "",
    retryable: bool = False,
) -> Dict[str, Any]:
    timestamp = _utc_now()
    return {
        "attempt_id": _normalize_text(attempt_id),
        "backend_id": _normalize_text(backend_id),
        "child_run_id": _normalize_text(child_run_id),
        "status": _normalize_text(status),
        "will_dispatch": _normalize_bool(will_dispatch),
        "dispatch_started_at": _normalize_text(dispatch_started_at) or timestamp,
        "dispatch_finished_at": _normalize_text(dispatch_finished_at) or timestamp,
        "sandbox_ref": _normalize_text(sandbox_ref),
        "output_ref": _normalize_text(output_ref),
        "audit_ref": _normalize_text(audit_ref),
        "error_code": _normalize_text(error_code),
        "retryable": _normalize_bool(retryable),
    }


def find_unsafe_sandbox_payload_keys(payload: Mapping[str, Any] | None) -> list[str]:
    payload_dict = dict(payload or {})
    return sorted(
        key for key in payload_dict if _normalize_text(key) in _UNSAFE_PAYLOAD_KEYS
    )


def validate_sandbox_dispatch_attempt(result: object) -> Dict[str, Any]:
    if not isinstance(result, Mapping):
        return {
            "valid": False,
            "error_code": "sandbox_attempt_not_object",
            "missing_fields": list(REQUIRED_SANDBOX_ATTEMPT_FIELDS),
            "attempt": {},
        }
    result_dict = dict(result)
    missing_fields = [
        field
        for field in REQUIRED_SANDBOX_ATTEMPT_FIELDS
        if field not in result_dict
    ]
    valid = not missing_fields
    return {
        "valid": valid,
        "error_code": "" if valid else "sandbox_attempt_missing_fields",
        "missing_fields": missing_fields,
        "attempt": {
            "attempt_id": _normalize_text(result_dict.get("attempt_id")),
            "backend_id": _normalize_text(result_dict.get("backend_id")),
            "child_run_id": _normalize_text(result_dict.get("child_run_id")),
            "status": _normalize_text(result_dict.get("status")),
            "will_dispatch": _normalize_bool(result_dict.get("will_dispatch")),
            "dispatch_started_at": _normalize_text(result_dict.get("dispatch_started_at")),
            "dispatch_finished_at": _normalize_text(result_dict.get("dispatch_finished_at")),
            "sandbox_ref": _normalize_text(result_dict.get("sandbox_ref")),
            "output_ref": _normalize_text(result_dict.get("output_ref")),
            "audit_ref": _normalize_text(result_dict.get("audit_ref")),
            "error_code": _normalize_text(result_dict.get("error_code")),
            "retryable": _normalize_bool(result_dict.get("retryable")),
        },
    }
