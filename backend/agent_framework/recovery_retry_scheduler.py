"""Opt-in scheduler for bounded Embedded SDK recovery retries."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Mapping

from .recovery_operations import (
    EMBEDDED_SDK_RECOVERY_RETRY_MAX_ATTEMPTS,
    build_recovery_operation_contract,
    build_recovery_retry_evidence,
    is_recovery_reason_retryable,
    is_recovery_reason_terminal,
)


RECOVERY_RETRY_SCHEDULER_CONTRACT_VERSION = "phase-ii-recovery-retry-scheduler-v1"
RECOVERY_RETRY_PRODUCTION_SCHEDULER_GATE_CONTRACT_VERSION = (
    "phase-ii-recovery-retry-production-scheduler-gate-v1"
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _build_gate_section(
    *,
    name: str,
    ready: bool,
    evidence: Mapping[str, Any] | None = None,
    missing_reason: str = "",
) -> Dict[str, Any]:
    return {
        "name": name,
        "status": "ready" if ready else "blocked",
        "ready": bool(ready),
        "missing_reason": "" if ready else _normalize_text(missing_reason),
        "evidence": dict(evidence or {}),
    }


def build_recovery_retry_production_scheduler_gate_contract(
    *,
    durable_scheduling_state_ready: bool = False,
    deterministic_idempotency_dedupe_ready: bool = False,
    backoff_clock_ready: bool = False,
    worker_ownership_ready: bool = False,
    recovery_audit_timeline_ready: bool = False,
) -> Dict[str, Any]:
    """Build the fail-closed gate for production automatic recovery retry."""

    operation_contract = build_recovery_operation_contract()
    retry_policy = dict(operation_contract.get("retry_policy") or {})
    supported_entrypoints = [
        dict(item)
        for item in operation_contract.get("entrypoints", [])
        if isinstance(item, dict)
    ]
    sections = [
        _build_gate_section(
            name="durable_scheduling_state",
            ready=durable_scheduling_state_ready,
            evidence={
                "required_state": "durable_retry_schedule",
                "process_local_timers_allowed": False,
            },
            missing_reason="durable_retry_schedule_state_missing",
        ),
        _build_gate_section(
            name="deterministic_idempotency_dedupe",
            ready=deterministic_idempotency_dedupe_ready,
            evidence={
                "idempotency_key_strategy": "run_entrypoint_previous_operation_attempt",
                "dedupe_scope": "run_entrypoint_previous_operation_attempt",
            },
            missing_reason="durable_retry_dedupe_state_missing",
        ),
        _build_gate_section(
            name="backoff_clock",
            ready=backoff_clock_ready,
            evidence={
                "backoff_strategy": _normalize_text(retry_policy.get("backoff_strategy")),
                "requires_next_eligible_at": True,
            },
            missing_reason="durable_backoff_clock_missing",
        ),
        _build_gate_section(
            name="terminal_classifier",
            ready=True,
            evidence={
                "retryable_reasons": list(retry_policy.get("retryable_reasons") or []),
                "terminal_reasons": list(retry_policy.get("terminal_reasons") or []),
                "exhaustion_supported": True,
            },
        ),
        _build_gate_section(
            name="worker_ownership",
            ready=worker_ownership_ready,
            evidence={
                "requires_valid_lease": True,
                "requires_fencing_token": True,
                "bypass_allowed": False,
            },
            missing_reason="worker_ownership_production_evidence_missing",
        ),
        _build_gate_section(
            name="recovery_audit_timeline",
            ready=recovery_audit_timeline_ready,
            evidence={
                "operation_evidence_source": "recovery_operation_history",
                "parallel_retry_event_model_allowed": False,
            },
            missing_reason="recovery_audit_timeline_not_production_bound",
        ),
        _build_gate_section(
            name="entrypoint_allowlist",
            ready=bool(supported_entrypoints),
            evidence={
                "supported_entrypoints": supported_entrypoints,
                "executes_only_recovery_entrypoints": True,
            },
            missing_reason="supported_recovery_entrypoints_missing",
        ),
        _build_gate_section(
            name="bounded_attempts",
            ready=int(retry_policy.get("max_attempts") or 0) > 0,
            evidence={
                "max_attempts": int(retry_policy.get("max_attempts") or 0),
                "retry_policy_contract_version": _normalize_text(retry_policy.get("contract_version")),
            },
            missing_reason="bounded_attempt_policy_missing",
        ),
        _build_gate_section(
            name="fail_closed_execution_decision",
            ready=True,
            evidence={
                "gate_required_before_background_retry": True,
                "blocked_gate_prevents_execution": True,
            },
        ),
    ]
    missing_sections = [
        str(section.get("name") or "").strip()
        for section in sections
        if not bool(section.get("ready"))
    ]
    overall_status = "ready" if not missing_sections else "blocked"
    return {
        "contract_version": RECOVERY_RETRY_PRODUCTION_SCHEDULER_GATE_CONTRACT_VERSION,
        "overall_status": overall_status,
        "automatic_retry_enabled_by_default": False,
        "ready": overall_status == "ready",
        "sections": sections,
        "missing_sections": missing_sections,
        "next_allowed_action": (
            "consider_explicit_production_enablement"
            if overall_status == "ready"
            else "implement_durable_retry_schedule_store_and_ownership_audit_gate"
        ),
        "non_goals": [
            "no_background_retry_loop",
            "no_default_retry_execution",
            "no_process_local_timer_as_source_of_truth",
            "no_parallel_retry_event_model",
            "no_worker_ownership_bypass",
        ],
    }


def build_recovery_retry_scheduler_contract() -> Dict[str, Any]:
    operation_contract = build_recovery_operation_contract()
    retry_policy = dict(operation_contract.get("retry_policy") or {})
    production_gate = build_recovery_retry_production_scheduler_gate_contract()
    return {
        "contract_version": RECOVERY_RETRY_SCHEDULER_CONTRACT_VERSION,
        "implemented": True,
        "enabled_by_default": False,
        "opt_in_required": True,
        "production_automatic_retry_supported": False,
        "production_scheduler_gate": production_gate,
        "executes_only_recovery_entrypoints": True,
        "retry_policy": retry_policy,
        "supported_entrypoints": [
            dict(item)
            for item in operation_contract.get("entrypoints", [])
            if isinstance(item, dict)
        ],
        "idempotency_key_strategy": "run_entrypoint_previous_operation_attempt",
        "audit_trace_supported": True,
        "non_executable_payload": True,
    }


class RecoveryRetryScheduler:
    """Schedule one bounded retry attempt from existing recovery operation evidence."""

    def __init__(
        self,
        *,
        sdk: Any,
        enabled: bool = False,
        production_automatic_retry: bool = False,
        production_scheduler_gate: Mapping[str, Any] | None = None,
        audit_recorder: Any | None = None,
        user_id: int | None = None,
        conversation_id: int | None = None,
    ) -> None:
        self._sdk = sdk
        self._enabled = bool(enabled)
        self._production_automatic_retry = bool(production_automatic_retry)
        self._production_scheduler_gate = dict(
            production_scheduler_gate
            or build_recovery_retry_production_scheduler_gate_contract()
        )
        self._audit_recorder = audit_recorder
        self._user_id = user_id
        self._conversation_id = conversation_id

    def schedule_next_attempt(self, run_id: str) -> Dict[str, Any]:
        normalized_run_id = _normalize_text(run_id)
        decision = self._base_decision(normalized_run_id)
        probe = self._probe(normalized_run_id)
        latest_operation = dict(probe.get("latest_recovery_operation") or {})
        decision["previous_operation"] = self._compact_previous_operation(latest_operation)

        if not latest_operation:
            return self._block(decision, "previous_recovery_operation_missing")
        retry_decision = self._build_retry_attempt(latest_operation)
        decision["retry_attempt"] = dict(retry_decision.get("retry_attempt") or {})
        decision["classifier"] = dict(retry_decision.get("classifier") or {})
        if not bool(retry_decision.get("eligible")):
            decision["status"] = "terminal" if decision["classifier"].get("terminal") else "blocked"
            decision["recovery_reason"] = _normalize_text(decision["classifier"].get("recovery_reason"))
            decision["will_execute"] = False
            return decision
        decision["eligible"] = True
        if not self._enabled:
            decision["status"] = "disabled"
            decision["will_execute"] = False
            return decision
        if self._production_automatic_retry:
            production_gate = self._evaluate_production_scheduler_gate()
            decision["production_scheduler_gate"] = production_gate
            if not bool(production_gate.get("ready")):
                decision["status"] = "blocked"
                decision["blocked_reason"] = "production_scheduler_gate_blocked"
                decision["will_execute"] = False
                return decision

        decision["will_execute"] = True
        try:
            result = self._execute_retry(latest_operation, dict(decision["retry_attempt"]))
        except Exception as exc:
            decision["status"] = "failed_closed"
            decision["will_execute"] = False
            decision["error"] = str(exc)
            refreshed_probe = self._safe_probe(normalized_run_id)
            latest_after_error = dict(refreshed_probe.get("latest_recovery_operation") or {})
            if latest_after_error:
                decision["latest_operation"] = latest_after_error
                decision["audit_trace"] = self._record_audit(latest_after_error, refreshed_probe)
            return decision

        decision["status"] = "executed"
        decision["result_state"] = _normalize_text((result.get("run") or {}).get("state")) if isinstance(result, dict) else ""
        refreshed_probe = self._safe_probe(normalized_run_id)
        latest_operation_after_retry = dict(refreshed_probe.get("latest_recovery_operation") or {})
        decision["latest_operation"] = latest_operation_after_retry
        decision["audit_trace"] = self._record_audit(latest_operation_after_retry, refreshed_probe)
        return decision

    def _base_decision(self, run_id: str) -> Dict[str, Any]:
        return {
            "contract_version": RECOVERY_RETRY_SCHEDULER_CONTRACT_VERSION,
            "run_id": run_id,
            "enabled": self._enabled,
            "production_automatic_retry": self._production_automatic_retry,
            "status": "blocked",
            "eligible": False,
            "will_execute": False,
            "scheduled_at": _utc_now(),
        }

    def _probe(self, run_id: str) -> Dict[str, Any]:
        probe = getattr(self._sdk, "probe_run_recovery", None)
        if not callable(probe):
            raise RuntimeError("recovery_probe_unavailable")
        return dict(probe(run_id) or {})

    def _safe_probe(self, run_id: str) -> Dict[str, Any]:
        try:
            return self._probe(run_id)
        except Exception:
            return {}

    @staticmethod
    def _block(decision: Dict[str, Any], reason: str) -> Dict[str, Any]:
        decision["status"] = "blocked"
        decision["blocked_reason"] = _normalize_text(reason)
        decision["will_execute"] = False
        return decision

    def _build_retry_attempt(self, previous_operation: Mapping[str, Any]) -> Dict[str, Any]:
        previous_operation_id = _normalize_text(previous_operation.get("operation_id"))
        run_id = _normalize_text(previous_operation.get("run_id"))
        entrypoint = _normalize_text(previous_operation.get("entrypoint"))
        recovery_reason = _normalize_text(previous_operation.get("recovery_reason") or previous_operation.get("blocked_reason"))
        previous_retry = previous_operation.get("retry") if isinstance(previous_operation.get("retry"), Mapping) else {}
        previous_attempt = int((previous_retry or {}).get("attempt_number") or 0)
        max_attempts = int((previous_retry or {}).get("max_attempts") or EMBEDDED_SDK_RECOVERY_RETRY_MAX_ATTEMPTS)
        attempt_number = previous_attempt + 1
        classifier = {
            "recovery_reason": recovery_reason,
            "retryable": is_recovery_reason_retryable(recovery_reason),
            "terminal": is_recovery_reason_terminal(recovery_reason),
            "previous_retry_status": _normalize_text((previous_retry or {}).get("status")),
            "previous_attempt_number": previous_attempt,
            "max_attempts": max_attempts,
        }
        if not previous_operation_id:
            classifier["blocked_reason"] = "previous_operation_id_missing"
            return {"eligible": False, "classifier": classifier}
        if not entrypoint:
            classifier["blocked_reason"] = "entrypoint_missing"
            return {"eligible": False, "classifier": classifier}
        if classifier["terminal"] or classifier["previous_retry_status"] in {"terminal", "exhausted"}:
            classifier["blocked_reason"] = "terminal_retry_decision"
            return {"eligible": False, "classifier": classifier}
        if attempt_number > max_attempts or not classifier["retryable"]:
            classifier["blocked_reason"] = "retry_not_allowed"
            return {"eligible": False, "classifier": classifier}

        idempotency_key = self._build_idempotency_key(
            run_id=run_id,
            entrypoint=entrypoint,
            previous_operation_id=previous_operation_id,
            attempt_number=attempt_number,
        )
        retry_attempt = {
            "attempt_number": attempt_number,
            "max_attempts": max_attempts,
            "previous_operation_id": previous_operation_id,
            "idempotency_key": idempotency_key,
            "recovery_reason": recovery_reason,
        }
        retry_attempt["evidence"] = build_recovery_retry_evidence(
            attempt_number=attempt_number,
            max_attempts=max_attempts,
            previous_operation_id=previous_operation_id,
            idempotency_key=idempotency_key,
            recovery_reason=recovery_reason,
        )
        return {
            "eligible": True,
            "retry_attempt": retry_attempt,
            "classifier": classifier,
        }

    @staticmethod
    def _build_idempotency_key(
        *,
        run_id: str,
        entrypoint: str,
        previous_operation_id: str,
        attempt_number: int,
    ) -> str:
        parts = [
            "recovery_retry",
            run_id or "unknown_run",
            entrypoint or "unknown_entrypoint",
            previous_operation_id or "unknown_operation",
            f"attempt_{attempt_number}",
        ]
        return ":".join(part.replace(":", "_") for part in parts)

    def _execute_retry(self, previous_operation: Mapping[str, Any], retry_attempt: Dict[str, Any]) -> Dict[str, Any]:
        entrypoint = _normalize_text(previous_operation.get("entrypoint"))
        run_id = _normalize_text(previous_operation.get("run_id"))
        continuation_ref = previous_operation.get("continuation_ref") if isinstance(previous_operation.get("continuation_ref"), Mapping) else {}
        continuation_id = _normalize_text((continuation_ref or {}).get("continuation_id"))
        if entrypoint == "submit_approval.approved":
            submit_approval = getattr(self._sdk, "submit_approval", None)
            if not callable(submit_approval):
                raise RuntimeError("submit_approval_unavailable")
            return dict(submit_approval(continuation_id, "approved", retry_attempt=retry_attempt) or {})
        if entrypoint == "resume_run.continue_loop":
            resume_run = getattr(self._sdk, "resume_run", None)
            if not callable(resume_run):
                raise RuntimeError("resume_run_unavailable")
            return dict(resume_run(run_id, continue_loop=True, retry_attempt=retry_attempt) or {})
        raise RuntimeError("unsupported_recovery_entrypoint")

    def _evaluate_production_scheduler_gate(self) -> Dict[str, Any]:
        gate = dict(self._production_scheduler_gate or {})
        sections = gate.get("sections") if isinstance(gate.get("sections"), list) else []
        missing_sections = gate.get("missing_sections")
        if not isinstance(missing_sections, list):
            missing_sections = [
                _normalize_text(section.get("name"))
                for section in sections
                if isinstance(section, Mapping) and not bool(section.get("ready"))
            ]
        ready = (
            _normalize_text(gate.get("contract_version"))
            == RECOVERY_RETRY_PRODUCTION_SCHEDULER_GATE_CONTRACT_VERSION
            and _normalize_text(gate.get("overall_status")) == "ready"
            and not bool(gate.get("automatic_retry_enabled_by_default"))
            and not missing_sections
        )
        gate["ready"] = ready
        gate["overall_status"] = "ready" if ready else "blocked"
        gate["automatic_retry_enabled_by_default"] = False
        gate["missing_sections"] = list(missing_sections or [])
        return gate

    def _record_audit(self, operation: Mapping[str, Any], probe: Mapping[str, Any]) -> Dict[str, Any]:
        if not operation or self._audit_recorder is None:
            return {"trace_written": False, "reason": "audit_recorder_not_configured"}
        record_operation = getattr(self._audit_recorder, "record_operation", None)
        if not callable(record_operation):
            return {"trace_written": False, "reason": "audit_recorder_unavailable"}
        try:
            return dict(record_operation(
                operation=operation,
                user_id=self._user_id,
                conversation_id=self._conversation_id,
                run_id=_normalize_text(probe.get("run_id") or operation.get("run_id")),
            ) or {})
        except Exception as exc:
            return {"trace_written": False, "reason": "audit_record_failed", "error": str(exc)}

    @staticmethod
    def _compact_previous_operation(operation: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "operation_id": _normalize_text(operation.get("operation_id")),
            "run_id": _normalize_text(operation.get("run_id")),
            "entrypoint": _normalize_text(operation.get("entrypoint")),
            "operation_status": _normalize_text(operation.get("operation_status")),
            "recovery_reason": _normalize_text(operation.get("recovery_reason")),
            "retry_status": _normalize_text((operation.get("retry") or {}).get("status") if isinstance(operation.get("retry"), Mapping) else ""),
        }
