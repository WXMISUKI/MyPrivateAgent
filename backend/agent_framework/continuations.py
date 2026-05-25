"""Stable continuation descriptor helpers for Embedded SDK recovery seams."""

from __future__ import annotations

from typing import Any, Dict


CONTINUATION_RECOVERY_STATUS_RECOVERABLE = "recoverable"
CONTINUATION_RECOVERY_STATUS_UNRECOVERABLE = "unrecoverable"

CONTINUATION_RECOVERY_REASON_DESCRIPTOR_MISSING = "descriptor_missing"
CONTINUATION_RECOVERY_REASON_READY_IN_PROCESS = "ready_in_process"
CONTINUATION_RECOVERY_REASON_READY_VIA_REGISTRY = "ready_via_registry"
CONTINUATION_RECOVERY_REASON_MISSING_EXECUTABLE_CONTINUATION = "missing_executable_continuation"
CONTINUATION_RECOVERY_REASON_MISSING_REGISTERED_BINDING = "missing_registered_binding"
CONTINUATION_RECOVERY_REASON_WORKSPACE_BACKEND_NOT_DURABLE = "workspace_backend_not_durable"
CONTINUATION_RECOVERY_REASON_WORKSPACE_BACKEND_FALLBACK_ACTIVE = "workspace_backend_fallback_active"
CONTINUATION_RECOVERY_REASON_DESCRIPTOR_CORRUPTED = "descriptor_corrupted"
CONTINUATION_RECOVERY_REASON_ALREADY_RESOLVED = "already_resolved"
CONTINUATION_RECOVERY_REASON_DENIED = "denied"


def build_continuation_recovery(
    *,
    continuation_kind: str,
    status: str,
    reason: str,
    descriptor_present: bool,
    executable_available: bool,
    attempted_at: str | None = None,
    request_id: str | None = None,
    resume_mode: str | None = None,
    binding_ids: Dict[str, str] | None = None,
    missing_binding_ids: list[str] | None = None,
) -> Dict[str, Any]:
    recovery: Dict[str, Any] = {
        "continuation_kind": str(continuation_kind or "").strip(),
        "recovery_status": str(status or "").strip(),
        "recovery_reason": str(reason or "").strip(),
        "descriptor_present": bool(descriptor_present),
        "executable_available": bool(executable_available),
    }
    if attempted_at:
        recovery["recovery_attempted_at"] = str(attempted_at).strip()
    if request_id:
        recovery["request_id"] = str(request_id).strip()
    if resume_mode:
        recovery["resume_mode"] = str(resume_mode).strip()
    if isinstance(binding_ids, dict) and binding_ids:
        recovery["binding_ids"] = {
            str(key).strip(): str(value).strip()
            for key, value in binding_ids.items()
            if str(key).strip() and str(value).strip()
        }
    if missing_binding_ids:
        recovery["missing_binding_ids"] = [
            str(binding_id).strip()
            for binding_id in list(missing_binding_ids)
            if str(binding_id).strip()
        ]
    return recovery


def build_tool_approval_continuation_descriptor(
    *,
    request_id: str,
    status: str,
    tool_name: str | None = None,
    tool_call_id: str | None = None,
    decision: str | None = None,
    tool_result: Any = None,
    tool_executor_binding_id: str | None = None,
    recovery: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    descriptor: Dict[str, Any] = {
        "status": str(status or "").strip(),
        "request_id": str(request_id or "").strip(),
    }
    if tool_name:
        descriptor["tool_name"] = str(tool_name).strip()
    if tool_call_id:
        descriptor["tool_call_id"] = str(tool_call_id).strip()
    if decision:
        descriptor["decision"] = str(decision).strip()
    if tool_result is not None:
        descriptor["tool_result"] = tool_result
    if tool_executor_binding_id:
        descriptor["tool_executor_binding_id"] = str(tool_executor_binding_id).strip()
    if isinstance(recovery, dict) and recovery:
        descriptor.update(dict(recovery))
    return descriptor


def build_loop_continuation_descriptor(
    *,
    request_id: str,
    status: str,
    resume_mode: str | None = None,
    source: str | None = None,
    completed_state: str | None = None,
    decision: str | None = None,
    has_reflector: bool | None = None,
    has_reviewer: bool | None = None,
    has_fallback_handler: bool | None = None,
    reflector_binding_id: str | None = None,
    reviewer_binding_id: str | None = None,
    fallback_handler_binding_id: str | None = None,
    max_iterations: int | None = None,
    recovery: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    descriptor: Dict[str, Any] = {
        "status": str(status or "").strip(),
        "request_id": str(request_id or "").strip(),
    }
    if resume_mode:
        descriptor["resume_mode"] = str(resume_mode).strip()
    if source:
        descriptor["source"] = str(source).strip()
    if completed_state:
        descriptor["completed_state"] = str(completed_state).strip()
    if decision:
        descriptor["decision"] = str(decision).strip()
    if has_reflector is not None:
        descriptor["has_reflector"] = bool(has_reflector)
    if has_reviewer is not None:
        descriptor["has_reviewer"] = bool(has_reviewer)
    if has_fallback_handler is not None:
        descriptor["has_fallback_handler"] = bool(has_fallback_handler)
    if reflector_binding_id:
        descriptor["reflector_binding_id"] = str(reflector_binding_id).strip()
    if reviewer_binding_id:
        descriptor["reviewer_binding_id"] = str(reviewer_binding_id).strip()
    if fallback_handler_binding_id:
        descriptor["fallback_handler_binding_id"] = str(fallback_handler_binding_id).strip()
    if max_iterations is not None:
        descriptor["max_iterations"] = int(max_iterations)
    if isinstance(recovery, dict) and recovery:
        descriptor.update(dict(recovery))
    return descriptor
