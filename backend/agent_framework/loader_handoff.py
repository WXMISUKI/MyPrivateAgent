"""Fail-closed handoff policy between durable loader and future recovery executor."""

from __future__ import annotations

from typing import Any, Dict, Mapping


DURABLE_LOADER_HANDOFF_POLICY_CONTRACT_VERSION = (
    "phase-ii-durable-loader-execution-handoff-policy-v1"
)


def build_durable_loader_execution_handoff_policy_contract() -> Dict[str, Any]:
    return {
        "contract_version": DURABLE_LOADER_HANDOFF_POLICY_CONTRACT_VERSION,
        "policy_kind": "durable_loader_to_recovery_executor_handoff",
        "default_handoff_enabled": False,
        "executes_recovery": False,
        "deserializes_callables": False,
        "allowed_entrypoints": [
            "submit_approval.approved",
            "resume_run.continue_loop",
        ],
        "required_evidence": [
            "loader_candidate_ready",
            "explicit_handoff_request",
            "recovery_executor_binding",
            "worker_ownership_gate",
            "recovery_audit_operation_history",
        ],
        "fail_closed_reasons": [
            "loader_candidate_not_ready",
            "explicit_handoff_required",
            "recovery_executor_not_bound",
            "worker_ownership_gate_missing",
            "recovery_audit_operation_history_missing",
        ],
    }


def build_durable_loader_execution_handoff_decision(
    *,
    loader_candidate: Mapping[str, Any] | None = None,
    explicit_handoff_requested: bool = False,
    recovery_executor_bound: bool = False,
    entrypoint: str = "",
) -> Dict[str, Any]:
    candidate = dict(loader_candidate or {})
    policy = build_durable_loader_execution_handoff_policy_contract()
    candidate_ready = bool(candidate.get("ready")) and str(candidate.get("status") or "").strip() == "ready"
    normalized_entrypoint = str(entrypoint or "").strip()
    if not normalized_entrypoint:
        normalized_entrypoint = _infer_entrypoint(candidate)
    blocked_reason = ""
    if not candidate_ready:
        blocked_reason = "loader_candidate_not_ready"
    elif not explicit_handoff_requested:
        blocked_reason = "explicit_handoff_required"
    elif not recovery_executor_bound:
        blocked_reason = "recovery_executor_not_bound"
    status = "blocked" if blocked_reason else "handoff_ready"
    return {
        "contract_version": DURABLE_LOADER_HANDOFF_POLICY_CONTRACT_VERSION,
        "policy_kind": policy["policy_kind"],
        "status": status,
        "ready": status == "handoff_ready",
        "blocked_reason": blocked_reason,
        "entrypoint": normalized_entrypoint,
        "explicit_handoff_requested": bool(explicit_handoff_requested),
        "recovery_executor_bound": bool(recovery_executor_bound),
        "loader_candidate_ready": candidate_ready,
        "will_execute": False,
        "executes_recovery": False,
        "deserializes_callables": False,
        "default_handoff_enabled": False,
        "policy": policy,
    }


def _infer_entrypoint(candidate: Mapping[str, Any]) -> str:
    approval_request_id = str(candidate.get("approval_request_id") or "").strip()
    if approval_request_id:
        return "submit_approval.approved"
    return "resume_run.continue_loop"
