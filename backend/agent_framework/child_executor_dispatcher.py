"""Opt-in dispatcher for real child executor backend invocation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, Mapping
from uuid import uuid4

from .child_executor_sandbox_worker_backend import (
    REQUIRED_SANDBOX_ATTEMPT_FIELDS,
    find_unsafe_sandbox_payload_keys,
    build_sandbox_dispatch_attempt_envelope,
    validate_sandbox_dispatch_attempt,
)


CHILD_EXECUTOR_DISPATCHER_CONTRACT_VERSION = "phase-ii-child-executor-dispatcher-v1"
CHILD_EXECUTOR_DISPATCH_ATTEMPT_HANDOFF_CONTRACT_VERSION = (
    "phase-ii-child-executor-dispatch-attempt-handoff-v1"
)
CHILD_EXECUTOR_DISPATCH_RESULT_HANDOFF_CONTRACT_VERSION = (
    "phase-ii-child-executor-dispatch-result-handoff-v1"
)
CHILD_EXECUTOR_DISPATCH_RESULT_RETRY_AUDIT_POLICY_CONTRACT_VERSION = (
    "phase-ii-child-executor-dispatch-result-retry-audit-policy-v1"
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def build_child_executor_dispatcher_contract() -> Dict[str, Any]:
    return {
        "contract_version": CHILD_EXECUTOR_DISPATCHER_CONTRACT_VERSION,
        "implemented": True,
        "enabled_by_default": False,
        "opt_in_required": True,
        "requires_dispatch_contract": True,
        "requires_dispatch_ready": True,
        "requires_backend_adapter": True,
        "side_effect_boundary": "backend_adapter_dispatch",
        "default_will_dispatch": False,
        "non_executable_payload": True,
        "fail_closed_reasons": [
            "dispatch_contract_missing",
            "dispatch_contract_not_ready",
            "backend_adapter_missing",
            "backend_adapter_failed",
            "backend_result_invalid",
            "sandbox_payload_unsafe",
            "sandbox_attempt_invalid",
        ],
    }


def build_child_executor_dispatch_attempt_handoff_contract(
    *,
    dispatch_contract: Mapping[str, Any] | None = None,
    dispatcher_contract: Mapping[str, Any] | None = None,
    payload: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Describe whether a sandbox dispatch attempt envelope can be handed off.

    This is a read-only contract builder. It validates a dry-run envelope shape
    and unsafe-payload guard posture, but never invokes a backend adapter.
    """

    contract = dict(dispatch_contract or {})
    dispatcher = dict(dispatcher_contract or build_child_executor_dispatcher_contract())
    backend_id = _normalize_text(contract.get("backend_id"))
    backend_adapter_kind = _normalize_text(contract.get("backend_adapter_kind"))
    dispatch_contract_ready = bool(contract.get("dispatch_ready"))
    dispatcher_enabled_by_default = bool(dispatcher.get("enabled_by_default"))
    dispatcher_opt_in_required = bool(dispatcher.get("opt_in_required"))
    sandbox_backend_selected = backend_adapter_kind == "sandbox_worker"
    sandbox_attempt_schema_ready = sandbox_backend_selected and bool(backend_id)
    unsafe_payload_keys = find_unsafe_sandbox_payload_keys(payload)
    unsafe_payload_guard_ready = not unsafe_payload_keys
    dry_run_attempt: Dict[str, Any] = {}
    validation = {
        "valid": False,
        "error_code": "sandbox_backend_not_selected",
        "missing_fields": list(REQUIRED_SANDBOX_ATTEMPT_FIELDS),
        "attempt": {},
    }
    if sandbox_attempt_schema_ready:
        dry_run_attempt = build_sandbox_dispatch_attempt_envelope(
            attempt_id="handoff-dry-run-attempt",
            backend_id=backend_id,
            child_run_id="handoff-dry-run-child",
            status="dry_run",
            will_dispatch=False,
            sandbox_ref="sandbox://handoff-dry-run-attempt",
            output_ref="artifact://handoff-dry-run-child/output",
            audit_ref="trace://handoff-dry-run-attempt",
        )
        validation = validate_sandbox_dispatch_attempt(dry_run_attempt)

    attempt_validation_ready = bool(validation.get("valid"))
    attempt_envelope_supported = sandbox_attempt_schema_ready and attempt_validation_ready
    audit_required = True
    idempotency_required = True
    missing_sections: list[str] = []
    if not dispatch_contract_ready:
        missing_sections.append("dispatch_contract_ready")
    if not backend_id:
        missing_sections.append("backend_id")
    if not dispatcher_opt_in_required:
        missing_sections.append("dispatcher_opt_in_required")
    if dispatcher_enabled_by_default:
        missing_sections.append("dispatcher_default_disabled")
    if not sandbox_backend_selected:
        missing_sections.append("sandbox_backend_selected")
    if not sandbox_attempt_schema_ready:
        missing_sections.append("sandbox_attempt_schema")
    if not attempt_envelope_supported:
        missing_sections.append("attempt_envelope_supported")
    if not attempt_validation_ready:
        missing_sections.append("attempt_validation_ready")
    if not audit_required:
        missing_sections.append("audit_required")
    if not idempotency_required:
        missing_sections.append("idempotency_required")
    if not unsafe_payload_guard_ready:
        missing_sections.append("unsafe_payload_guard")

    missing_sections = list(dict.fromkeys(missing_sections))
    ready = not missing_sections
    return {
        "contract_version": CHILD_EXECUTOR_DISPATCH_ATTEMPT_HANDOFF_CONTRACT_VERSION,
        "overall_status": "ready" if ready else "blocked",
        "ready": ready,
        "dispatch_contract_ready": dispatch_contract_ready,
        "dispatcher_enabled_by_default": dispatcher_enabled_by_default,
        "dispatcher_opt_in_required": dispatcher_opt_in_required,
        "backend_id": backend_id,
        "backend_adapter_kind": backend_adapter_kind,
        "sandbox_backend_selected": sandbox_backend_selected,
        "sandbox_attempt_schema_ready": sandbox_attempt_schema_ready,
        "attempt_envelope_supported": attempt_envelope_supported,
        "attempt_validation_ready": attempt_validation_ready,
        "attempt_validation_error_code": _normalize_text(validation.get("error_code")),
        "attempt_validation_missing_fields": [
            _normalize_text(item)
            for item in (validation.get("missing_fields") or [])
            if _normalize_text(item)
        ],
        "dry_run_attempt_status": _normalize_text(dry_run_attempt.get("status")),
        "audit_required": audit_required,
        "idempotency_required": idempotency_required,
        "unsafe_payload_guard_ready": unsafe_payload_guard_ready,
        "unsafe_payload_keys": unsafe_payload_keys,
        "will_dispatch": False,
        "missing_sections": missing_sections,
        "blocked_reason": "" if ready else (missing_sections[0] if missing_sections else "blocked"),
        "next_allowed_action": (
            "inject_explicit_dispatcher_and_backend_adapter"
            if ready
            else "complete_dispatch_attempt_handoff_contract"
        ),
        "non_goals": [
            "start_child_executor_worker",
            "enable_dispatcher_by_default",
            "execute_sandbox_worker_code",
        ],
    }


def build_child_executor_dispatch_result_handoff_contract(
    *,
    dispatch_attempt: Mapping[str, Any] | None = None,
    backend_result: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Normalize dispatcher backend output into compact handoff evidence.

    The contract is intentionally non-authorizing: it can prove that a result
    is ready for governance/audit handoff, but it never claims parent merge,
    retry scheduling, or production worker default enablement.
    """

    attempt = dict(dispatch_attempt or {})
    result = dict(backend_result or attempt.get("backend_result") or {})
    audit = dict(attempt.get("audit") or {})
    dispatch_status = _normalize_text(attempt.get("dispatch_status"))
    blocked_reason = _normalize_text(attempt.get("blocked_reason"))
    backend_id = _normalize_text(attempt.get("backend_id") or result.get("backend_id"))
    child_run_id = _normalize_text(
        result.get("child_run_id") or (attempt.get("payload_summary") or {}).get("child_run_id")
    )
    backend_result_status = _normalize_text(result.get("status"))
    output_ref = _normalize_text(result.get("output_ref"))
    audit_ref = _normalize_text(result.get("audit_ref"))
    sandbox_ref = _normalize_text(result.get("sandbox_ref"))
    retryable = bool(result.get("retryable"))
    idempotency_key = _normalize_text(
        result.get("idempotency_key")
        or result.get("attempt_id")
        or attempt.get("attempt_id")
    )
    dispatched = bool(attempt.get("dispatched"))
    will_dispatch = bool(attempt.get("will_dispatch"))
    backend_result_present = bool(result)
    output_ref_present = bool(output_ref)
    audit_evidence_present = bool(
        audit_ref
        or audit.get("trace_written")
        or _normalize_text(audit.get("dedupe_key"))
        or _normalize_text(audit.get("attempt_id"))
    )
    validation = {"valid": True, "error_code": "", "missing_fields": []}
    if sandbox_ref or _normalize_text(result.get("backend_id")) == "sandbox_worker":
        validation = validate_sandbox_dispatch_attempt(result)

    missing_sections: list[str] = []
    if dispatch_status != "dispatched" or not dispatched:
        missing_sections.append("dispatch_success")
    if not backend_result_present:
        missing_sections.append("backend_result")
    if not child_run_id:
        missing_sections.append("child_run_id")
    if not output_ref_present:
        missing_sections.append("output_ref")
    if not audit_evidence_present:
        missing_sections.append("audit_evidence")
    if not bool(validation.get("valid")):
        missing_sections.append("backend_result_schema")
    for item in attempt.get("missing_backend_result_fields") or []:
        field = _normalize_text(item)
        if field:
            missing_sections.append(f"backend_result.{field}")
    missing_sections = list(dict.fromkeys(missing_sections))

    retry_audit_policy = build_child_executor_dispatch_result_retry_audit_policy_contract(
        result_handoff={
            "overall_status": "ready" if not missing_sections else "blocked",
            "ready": not missing_sections,
            "dispatch_status": dispatch_status,
            "dispatcher_blocked_reason": blocked_reason,
            "dispatched": dispatched,
            "will_dispatch": will_dispatch,
            "backend_id": backend_id,
            "child_run_id": child_run_id,
            "backend_result_status": backend_result_status,
            "backend_result_error_code": _normalize_text(
                validation.get("error_code") or attempt.get("error_code") or result.get("error_code")
            ),
            "retryable": retryable,
            "audit_evidence_present": audit_evidence_present,
            "idempotency_key": idempotency_key,
            "missing_sections": missing_sections,
            "blocked_reason": blocked_reason or (missing_sections[0] if missing_sections else ""),
        }
    )
    ready = not missing_sections
    return {
        "contract_version": CHILD_EXECUTOR_DISPATCH_RESULT_HANDOFF_CONTRACT_VERSION,
        "overall_status": "ready" if ready else "blocked",
        "ready": ready,
        "dispatch_status": dispatch_status,
        "dispatcher_blocked_reason": blocked_reason,
        "dispatched": dispatched,
        "will_dispatch": will_dispatch,
        "backend_id": backend_id,
        "child_run_id": child_run_id,
        "backend_result_present": backend_result_present,
        "backend_result_status": backend_result_status,
        "output_ref": output_ref,
        "output_ref_present": output_ref_present,
        "audit_ref": audit_ref,
        "audit_evidence_present": audit_evidence_present,
        "sandbox_ref": sandbox_ref,
        "backend_result_schema_valid": bool(validation.get("valid")),
        "backend_result_error_code": _normalize_text(
            validation.get("error_code") or attempt.get("error_code")
        ),
        "backend_result_missing_fields": [
            _normalize_text(item)
            for item in (
                validation.get("missing_fields")
                or attempt.get("missing_backend_result_fields")
                or []
            )
            if _normalize_text(item)
        ],
        "idempotency_key_present": bool(idempotency_key),
        "retryable": retryable,
        "dispatch_result_retry_audit_policy": retry_audit_policy,
        "retry_scheduled": False,
        "parent_merge_performed": False,
        "merge_authorization": False,
        "production_dispatch_authorized": False,
        "missing_sections": missing_sections,
        "blocked_reason": "" if ready else (blocked_reason or missing_sections[0] if missing_sections else "blocked"),
        "next_allowed_action": (
            "record_child_executor_result_audit"
            if ready
            else "complete_dispatch_result_handoff_contract"
        ),
        "non_goals": [
            "merge_child_result_into_parent",
            "schedule_child_executor_retry",
            "enable_dispatcher_by_default",
            "start_child_executor_worker",
        ],
    }


def build_child_executor_dispatch_result_retry_audit_policy_contract(
    *,
    result_handoff: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Classify child dispatch result retry posture without executing retry."""

    handoff = dict(result_handoff or {})
    handoff_status = _normalize_text(handoff.get("overall_status"))
    handoff_ready = bool(handoff.get("ready"))
    dispatch_status = _normalize_text(handoff.get("dispatch_status"))
    backend_result_status = _normalize_text(handoff.get("backend_result_status"))
    error_code = _normalize_text(handoff.get("backend_result_error_code"))
    dispatcher_blocked_reason = _normalize_text(handoff.get("dispatcher_blocked_reason"))
    blocked_reason = _normalize_text(handoff.get("blocked_reason") or dispatcher_blocked_reason)
    retryable = bool(handoff.get("retryable"))
    audit_evidence_present = bool(handoff.get("audit_evidence_present"))
    idempotency_key = _normalize_text(handoff.get("idempotency_key"))
    idempotency_evidence_present = bool(idempotency_key)
    missing_sections = [
        _normalize_text(item)
        for item in (handoff.get("missing_sections") or [])
        if _normalize_text(item)
    ]
    success_statuses = {"completed", "succeeded", "success", "ok"}
    terminal_blocked_reasons = {
        "sandbox_payload_unsafe",
        "sandbox_attempt_invalid",
        "backend_adapter_missing",
        "backend_result_invalid",
        "dispatch_contract_missing",
        "dispatch_contract_not_ready",
    }
    if handoff_ready and backend_result_status in success_statuses and not retryable:
        retry_policy_status = "not_required"
    elif retryable:
        retry_policy_status = "retryable"
    elif blocked_reason in terminal_blocked_reasons or "backend_result_schema" in missing_sections:
        retry_policy_status = "terminal"
    elif handoff_status == "blocked":
        retry_policy_status = "terminal"
    else:
        retry_policy_status = "blocked"

    policy_missing_sections: list[str] = []
    if retry_policy_status == "retryable":
        if not audit_evidence_present:
            policy_missing_sections.append("audit_evidence")
        if not idempotency_evidence_present:
            policy_missing_sections.append("idempotency_evidence")
        if not error_code and not blocked_reason and not backend_result_status:
            policy_missing_sections.append("retry_reason")
    if retry_policy_status == "blocked" and not handoff:
        policy_missing_sections.append("result_handoff")
    policy_missing_sections = list(dict.fromkeys(policy_missing_sections))
    ready = not policy_missing_sections
    return {
        "contract_version": CHILD_EXECUTOR_DISPATCH_RESULT_RETRY_AUDIT_POLICY_CONTRACT_VERSION,
        "overall_status": "ready" if ready else "blocked",
        "ready": ready,
        "retry_policy_status": retry_policy_status,
        "retryable": retry_policy_status == "retryable",
        "terminal": retry_policy_status == "terminal",
        "retry_reason": error_code or blocked_reason or backend_result_status,
        "error_code": error_code,
        "dispatcher_blocked_reason": dispatcher_blocked_reason,
        "audit_evidence_present": audit_evidence_present,
        "idempotency_evidence_present": idempotency_evidence_present,
        "idempotency_key_present": idempotency_evidence_present,
        "scheduler_required": retry_policy_status == "retryable",
        "retry_scheduled": False,
        "will_retry": False,
        "backoff_policy_bound": False,
        "missing_sections": policy_missing_sections,
        "blocked_reason": "" if ready else (policy_missing_sections[0] if policy_missing_sections else "blocked"),
        "next_allowed_action": (
            "record_retry_audit_evidence"
            if ready
            else "complete_retry_audit_policy_evidence"
        ),
        "non_goals": [
            "schedule_child_executor_retry",
            "execute_retry",
            "start_child_executor_worker",
            "merge_child_result_into_parent",
        ],
    }


class ChildExecutorDispatcher:
    """Invoke a child executor backend only when dispatch readiness is explicit."""

    def __init__(
        self,
        *,
        backend_adapters: Mapping[str, Callable[[Mapping[str, Any]], Mapping[str, Any] | None]] | None = None,
        enabled: bool = False,
        audit_recorder: Any | None = None,
    ) -> None:
        self._backend_adapters = dict(backend_adapters or {})
        self._enabled = bool(enabled)
        self._audit_recorder = audit_recorder

    def dispatch(
        self,
        *,
        dispatch_contract: Mapping[str, Any] | None,
        payload: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        contract = dict(dispatch_contract or {})
        attempt = self._base_attempt(contract)
        attempt["payload_summary"] = self._summarize_payload(payload)
        if not contract:
            return self._block(attempt, "dispatch_contract_missing")
        if not self._enabled:
            return self._block(attempt, "dispatcher_disabled")
        if not bool(contract.get("dispatch_ready")):
            blockers = [
                _normalize_text(item)
                for item in list(contract.get("blockers") or [])
                if _normalize_text(item)
            ]
            attempt["blockers"] = blockers
            return self._block(attempt, "dispatch_contract_not_ready")
        if _normalize_text(contract.get("backend_adapter_kind")) == "sandbox_worker":
            unsafe_keys = find_unsafe_sandbox_payload_keys(payload)
            if unsafe_keys:
                attempt["unsafe_payload_keys"] = unsafe_keys
                attempt["error_code"] = "unsafe_payload"
                return self._block(attempt, "sandbox_payload_unsafe")
            binding = dict(contract.get("child_executor_sandbox_backend_binding") or {})
            if binding and not bool(binding.get("ready")):
                return self._block(attempt, "sandbox_backend_binding_not_ready")

        backend_id = _normalize_text(contract.get("backend_id"))
        adapter = self._backend_adapters.get(backend_id)
        if not callable(adapter):
            return self._block(attempt, "backend_adapter_missing")
        attempt["will_dispatch"] = True
        try:
            result = adapter(dict(payload or {}))
        except Exception as exc:
            attempt["error"] = str(exc)
            return self._block(attempt, "backend_adapter_failed")
        if not isinstance(result, Mapping):
            return self._block(attempt, "backend_result_invalid")
        if _normalize_text(contract.get("backend_adapter_kind")) == "sandbox_worker":
            validation = validate_sandbox_dispatch_attempt(result)
            if not validation["valid"]:
                attempt["error_code"] = validation["error_code"]
                attempt["missing_backend_result_fields"] = validation["missing_fields"]
                return self._block(attempt, "sandbox_attempt_invalid")
            attempt["dispatch_status"] = "dispatched"
            attempt["dispatched"] = True
            attempt["will_dispatch"] = bool(validation["attempt"]["will_dispatch"])
            attempt["backend_result"] = validation["attempt"]
            attempt["audit"] = self._record_audit(attempt)
            attempt["dispatch_result_handoff"] = build_child_executor_dispatch_result_handoff_contract(
                dispatch_attempt=attempt
            )
            return attempt

        attempt["dispatch_status"] = "dispatched"
        attempt["dispatched"] = True
        attempt["will_dispatch"] = True
        attempt["backend_result"] = self._compact_backend_result(result)
        attempt["audit"] = self._record_audit(attempt)
        attempt["dispatch_result_handoff"] = build_child_executor_dispatch_result_handoff_contract(
            dispatch_attempt=attempt
        )
        return attempt

    def _base_attempt(self, contract: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "contract_version": CHILD_EXECUTOR_DISPATCHER_CONTRACT_VERSION,
            "attempt_id": f"child_executor_dispatch:{uuid4().hex}",
            "dispatch_status": "blocked",
            "dispatched": False,
            "enabled": self._enabled,
            "will_dispatch": False,
            "backend_id": _normalize_text(contract.get("backend_id")),
            "dispatch_contract_version": _normalize_text(contract.get("contract_version")),
            "dispatch_contract_status": _normalize_text(contract.get("overall_status")),
            "dispatch_ready": bool(contract.get("dispatch_ready")),
            "recorded_at": _utc_now(),
            "sandbox_backend_binding_status": _normalize_text(
                (contract.get("child_executor_sandbox_backend_binding") or {}).get("overall_status")
            ),
            "sandbox_backend_binding_ready": bool(
                (contract.get("child_executor_sandbox_backend_binding") or {}).get("ready")
            ),
            "sandbox_backend_binding_missing_sections": [
                _normalize_text(item)
                for item in (
                    (contract.get("child_executor_sandbox_backend_binding") or {}).get("missing_sections")
                    or []
                )
                if _normalize_text(item)
            ],
        }

    def _block(self, attempt: Dict[str, Any], reason: str) -> Dict[str, Any]:
        attempt["dispatch_status"] = "blocked"
        attempt["dispatched"] = False
        attempt["will_dispatch"] = False
        attempt["blocked_reason"] = _normalize_text(reason)
        attempt["audit"] = self._record_audit(attempt)
        attempt["dispatch_result_handoff"] = build_child_executor_dispatch_result_handoff_contract(
            dispatch_attempt=attempt
        )
        return attempt

    @staticmethod
    def _summarize_payload(payload: Mapping[str, Any] | None) -> Dict[str, Any]:
        payload_dict = dict(payload or {})
        return {
            "parent_run_id": _normalize_text(payload_dict.get("parent_run_id")),
            "child_run_id": _normalize_text(payload_dict.get("child_run_id")),
            "intent_label": _normalize_text(payload_dict.get("intent_label")),
            "input_preview_length": len(_normalize_text(payload_dict.get("input_preview"))),
        }

    @staticmethod
    def _compact_backend_result(result: Mapping[str, Any]) -> Dict[str, Any]:
        result_dict = dict(result or {})
        return {
            "status": _normalize_text(result_dict.get("status") or "completed"),
            "child_run_id": _normalize_text(result_dict.get("child_run_id")),
            "summary": _normalize_text(result_dict.get("summary")),
            "output_ref": _normalize_text(result_dict.get("output_ref")),
        }

    def _record_audit(self, attempt: Mapping[str, Any]) -> Dict[str, Any]:
        if self._audit_recorder is None:
            return {"trace_written": False, "reason": "audit_recorder_not_configured"}
        record_dispatch = getattr(self._audit_recorder, "record_dispatch", None)
        if not callable(record_dispatch):
            return {"trace_written": False, "reason": "audit_recorder_unavailable"}
        try:
            return dict(record_dispatch(dispatch_attempt=dict(attempt)) or {})
        except Exception as exc:
            return {"trace_written": False, "reason": "audit_record_failed", "error": str(exc)}
