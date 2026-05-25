"""Opt-in dispatcher for real child executor backend invocation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, Mapping
from uuid import uuid4

from .child_executor_sandbox_worker_backend import (
    find_unsafe_sandbox_payload_keys,
    validate_sandbox_dispatch_attempt,
)


CHILD_EXECUTOR_DISPATCHER_CONTRACT_VERSION = "phase-ii-child-executor-dispatcher-v1"


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
            return attempt

        attempt["dispatch_status"] = "dispatched"
        attempt["dispatched"] = True
        attempt["will_dispatch"] = True
        attempt["backend_result"] = self._compact_backend_result(result)
        attempt["audit"] = self._record_audit(attempt)
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
        }

    def _block(self, attempt: Dict[str, Any], reason: str) -> Dict[str, Any]:
        attempt["dispatch_status"] = "blocked"
        attempt["dispatched"] = False
        attempt["will_dispatch"] = False
        attempt["blocked_reason"] = _normalize_text(reason)
        attempt["audit"] = self._record_audit(attempt)
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
