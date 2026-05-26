"""Run the quality gate checks and emit a machine-readable report."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
RUNTIME_CONTRACT_ARTIFACT_SCHEMA_VERSION = "phase-f-runtime-contract-artifact-schema-v1"
RUNTIME_CONTRACT_SUMMARY_REQUIRED_FIELDS = (
    "overall_status",
    "check_count",
    "failed_check_count",
    "missing_payload_count",
    "approval_replay_coverage",
    "approval_lifecycle_recovery_coverage",
    "approval_lifecycle_recovery_coverage.alignment_smoke",
    "approved_tool_execution_coverage",
    "sdk_tool_runtime_execution_coverage",
    "sdk_tool_runtime_execution_coverage.bridge_smoke",
    "tool_runtime_timeout_retry_coverage",
    "tool_runtime_timeout_retry_coverage.timeout_retry_smoke",
    "checkpoint_resume_cursor_coverage",
    "checkpoint_resume_cursor_coverage.cursor_smoke",
    "embedded_sdk_persistence_coverage",
    "embedded_sdk_persistence_coverage.persistence_smoke",
    "embedded_sdk_persistence_coverage.production_recovery_worker_ownership_gate_status",
    "embedded_sdk_persistence_coverage.production_recovery_worker_ownership_missing_sections",
    "worker_ownership_store_mode_coverage",
    "worker_ownership_store_mode_coverage.mode_smoke",
    "worker_ownership_store_mode_coverage.enablement_config_factory_binding_smoke",
    "recovery_retry_evidence_coverage",
    "recovery_retry_evidence_coverage.retry_smoke",
    "recovery_retry_scheduler_coverage",
    "recovery_retry_scheduler_coverage.scheduler_smoke",
    "durable_recovery_loader_coverage",
    "durable_recovery_loader_coverage.loader_smoke",
    "continuation_descriptor_lifecycle_coverage",
    "continuation_descriptor_lifecycle_coverage.lifecycle_smoke",
    "loader_execution_handoff_coverage",
    "loader_execution_handoff_coverage.handoff_smoke",
    "recovery_audit_operation_history_coverage",
    "recovery_audit_operation_history_coverage.audit_smoke",
    "production_recovery_registry_checkpoint_policy_coverage",
    "production_recovery_registry_checkpoint_policy_coverage.policy_smoke",
    "child_executor_promotion_gate_coverage",
    "child_executor_promotion_gate_coverage.gate_smoke",
    "child_executor_execution_prerequisites_coverage",
    "child_executor_execution_prerequisites_coverage.prerequisites_smoke",
    "child_executor_execution_prerequisites_coverage.context_budget_policy_status",
    "child_executor_execution_prerequisites_coverage.context_budget_policy_missing_sections",
    "child_executor_execution_prerequisites_coverage.opt_in_context_budget_policy_ready",
    "child_executor_execution_prerequisites_coverage.merge_handoff_status",
    "child_executor_execution_prerequisites_coverage.merge_handoff_missing_sections",
    "child_executor_execution_prerequisites_coverage.opt_in_merge_handoff_ready",
    "child_executor_dispatch_coverage",
    "child_executor_dispatch_coverage.dispatch_smoke",
    "child_executor_dispatch_coverage.dispatch_attempt_handoff_status",
    "child_executor_dispatch_coverage.opt_in_dispatch_attempt_handoff_ready",
    "child_executor_dispatch_coverage.opt_in_attempt_validation_ready",
    "child_executor_dispatcher_coverage",
    "child_executor_dispatcher_coverage.dispatcher_smoke",
    "child_executor_dispatch_result_handoff_coverage",
    "child_executor_dispatch_result_handoff_coverage.result_handoff_smoke",
    "child_executor_dispatch_result_handoff_coverage.ready_handoff_status",
    "child_executor_dispatch_result_handoff_coverage.malformed_handoff_status",
    "child_executor_dispatch_result_retry_audit_coverage",
    "child_executor_dispatch_result_retry_audit_coverage.retry_audit_smoke",
    "child_executor_dispatch_result_retry_audit_coverage.retryable_retry_policy_status",
    "child_executor_dispatch_result_retry_audit_coverage.missing_idempotency_status",
    "child_executor_sandbox_backend_coverage",
    "child_executor_sandbox_backend_coverage.sandbox_backend_smoke",
    "subagent_lane_query_detail_coverage",
    "subagent_lane_query_detail_coverage.detail_smoke",
)


@dataclass(frozen=True)
class GateStep:
    name: str
    command: list[str]
    cwd: Path = ROOT_DIR


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run quality gate checks and write a summary report.")
    parser.add_argument("--output", type=str, default="quality-gate-report.json", help="JSON report path.")
    parser.add_argument("--summary", type=str, default="quality-gate-summary.md", help="Markdown summary path.")
    parser.add_argument("--window-days", type=int, default=14, choices=[0, 7, 14, 30])
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--max-open-actions", type=int, default=10)
    parser.add_argument("--max-long-blocked-actions", type=int, default=0)
    return parser


def _run_step(step: GateStep) -> dict[str, Any]:
    started_at = monotonic()
    completed = subprocess.run(
        step.command,
        cwd=str(step.cwd),
        capture_output=True,
        text=True,
    )
    duration_seconds = round(monotonic() - started_at, 3)
    result = {
        "name": step.name,
        "command": " ".join(shlex.quote(part) for part in step.command),
        "cwd": str(step.cwd),
        "exit_code": completed.returncode,
        "passed": completed.returncode == 0,
        "duration_seconds": duration_seconds,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    structured_output = _parse_structured_stdout(completed.stdout)
    if structured_output:
        result["structured_output"] = structured_output
        if isinstance(structured_output.get("checks"), list):
            result["contract_checks"] = _normalize_contract_checks(structured_output["checks"])
            result["runtime_contract_summary"] = _build_runtime_contract_summary(result["contract_checks"])
            result["runtime_contract_artifact_schema"] = _build_runtime_contract_artifact_schema(
                result["runtime_contract_summary"]
            )
    return result


def _parse_structured_stdout(stdout: str) -> dict[str, Any]:
    text = str(stdout or "").strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return _parse_embedded_structured_stdout(text)
    return payload if isinstance(payload, dict) else {}


def _parse_embedded_structured_stdout(text: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    candidates: list[dict[str, Any]] = []
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            payload, _end = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            candidates.append(payload)
    for payload in candidates:
        checks = payload.get("checks")
        if not isinstance(checks, list):
            continue
        check_names = {
            str(check.get("name") or "").strip()
            for check in checks
            if isinstance(check, dict)
        }
        if "runtime_profile_contract_snapshot" in check_names or "worker_ownership_store_mode" in check_names:
            return payload
    for payload in candidates:
        if isinstance(payload.get("checks"), list):
            return payload
    return candidates[-1] if candidates else {}


def _build_runtime_contract_summary(checks: list[dict[str, Any]]) -> dict[str, Any]:
    failed_checks = [check for check in checks if not bool(check.get("ok"))]
    check_names = [str(check.get("name") or "").strip() for check in checks]
    event_payload_check = next(
        (check for check in checks if str(check.get("name") or "").strip() == "embedded_sdk_event_payloads"),
        {},
    )
    observed_status_kinds = set(_normalize_string_list(event_payload_check.get("observed_status_kinds")))
    approval_replay_covered = (
        {"approval_replayed", "approval_ignored"}.issubset(observed_status_kinds)
        if observed_status_kinds
        else bool(event_payload_check.get("ok"))
    )
    approved_tool_bridge_check = next(
        (check for check in checks if str(check.get("name") or "").strip() == "runtime_approved_tool_execution_bridge"),
        {},
    )
    sdk_tool_bridge_check = next(
        (check for check in checks if str(check.get("name") or "").strip() == "sdk_tool_runtime_execution_bridge"),
        {},
    )
    tool_runtime_timeout_retry_check = next(
        (check for check in checks if str(check.get("name") or "").strip() == "tool_runtime_timeout_retry"),
        {},
    )
    approval_lifecycle_check = next(
        (check for check in checks if str(check.get("name") or "").strip() == "approval_lifecycle_recovery_alignment"),
        {},
    )
    subagent_lane_detail_check = next(
        (check for check in checks if str(check.get("name") or "").strip() == "subagent_lane_query_detail"),
        {},
    )
    checkpoint_cursor_check = next(
        (check for check in checks if str(check.get("name") or "").strip() == "durable_checkpoint_resume_cursor"),
        {},
    )
    persistence_posture_check = next(
        (check for check in checks if str(check.get("name") or "").strip() == "embedded_sdk_persistence_posture"),
        {},
    )
    worker_ownership_store_mode_check = next(
        (check for check in checks if str(check.get("name") or "").strip() == "worker_ownership_store_mode"),
        {},
    )
    recovery_retry_evidence_check = next(
        (check for check in checks if str(check.get("name") or "").strip() == "recovery_retry_evidence"),
        {},
    )
    recovery_retry_scheduler_check = next(
        (check for check in checks if str(check.get("name") or "").strip() == "recovery_retry_scheduler"),
        {},
    )
    durable_recovery_loader_check = next(
        (check for check in checks if str(check.get("name") or "").strip() == "durable_recovery_loader"),
        {},
    )
    child_executor_gate_check = next(
        (check for check in checks if str(check.get("name") or "").strip() == "child_executor_promotion_gate"),
        {},
    )
    child_executor_dispatch_check = next(
        (check for check in checks if str(check.get("name") or "").strip() == "child_executor_dispatch_contract"),
        {},
    )
    child_executor_dispatcher_check = next(
        (check for check in checks if str(check.get("name") or "").strip() == "child_executor_dispatcher"),
        {},
    )
    child_executor_dispatch_result_handoff_check = next(
        (
            check
            for check in checks
            if str(check.get("name") or "").strip() == "child_executor_dispatch_result_handoff"
        ),
        {},
    )
    child_executor_dispatch_result_retry_audit_check = next(
        (
            check
            for check in checks
            if str(check.get("name") or "").strip()
            == "child_executor_dispatch_result_retry_audit_policy"
        ),
        {},
    )
    child_executor_sandbox_backend_check = next(
        (check for check in checks if str(check.get("name") or "").strip() == "child_executor_sandbox_backend"),
        {},
    )
    return {
        "overall_status": "healthy" if not failed_checks and checks else "degraded",
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_checks": [str(check.get("name") or "") for check in failed_checks],
        "check_names": check_names,
        "missing_payload_count": _coerce_non_negative_int(event_payload_check.get("missing_payload_count"), 0),
        "approval_replay_coverage": {
            "event_payload_sample": approval_replay_covered,
            "observed_status_kinds": sorted(observed_status_kinds),
        },
        "approval_lifecycle_recovery_coverage": _build_approval_lifecycle_recovery_coverage(
            approval_lifecycle_check
        ),
        "approved_tool_execution_coverage": _build_approved_tool_execution_coverage(approved_tool_bridge_check),
        "sdk_tool_runtime_execution_coverage": _build_sdk_tool_runtime_execution_coverage(sdk_tool_bridge_check),
        "tool_runtime_timeout_retry_coverage": _build_tool_runtime_timeout_retry_coverage(
            tool_runtime_timeout_retry_check
        ),
        "checkpoint_resume_cursor_coverage": _build_checkpoint_resume_cursor_coverage(checkpoint_cursor_check),
        "embedded_sdk_persistence_coverage": _build_embedded_sdk_persistence_coverage(persistence_posture_check),
        "worker_ownership_store_mode_coverage": _build_worker_ownership_store_mode_coverage(
            worker_ownership_store_mode_check
        ),
        "recovery_retry_evidence_coverage": _build_recovery_retry_evidence_coverage(
            recovery_retry_evidence_check
        ),
        "recovery_retry_scheduler_coverage": _build_recovery_retry_scheduler_coverage(
            recovery_retry_scheduler_check
        ),
        "durable_recovery_loader_coverage": _build_durable_recovery_loader_coverage(
            durable_recovery_loader_check
        ),
        "continuation_descriptor_lifecycle_coverage": _build_continuation_descriptor_lifecycle_coverage(
            durable_recovery_loader_check
        ),
        "loader_execution_handoff_coverage": _build_loader_execution_handoff_coverage(
            durable_recovery_loader_check
        ),
        "recovery_audit_operation_history_coverage": _build_recovery_audit_operation_history_coverage(
            persistence_posture_check
        ),
        "production_recovery_registry_checkpoint_policy_coverage": (
            _build_production_recovery_registry_checkpoint_policy_coverage(persistence_posture_check)
        ),
        "child_executor_promotion_gate_coverage": _build_child_executor_promotion_gate_coverage(
            child_executor_gate_check
        ),
        "child_executor_execution_prerequisites_coverage": _build_child_executor_execution_prerequisites_coverage(
            child_executor_gate_check
        ),
        "child_executor_dispatch_coverage": _build_child_executor_dispatch_coverage(
            child_executor_dispatch_check
        ),
        "child_executor_dispatcher_coverage": _build_child_executor_dispatcher_coverage(
            child_executor_dispatcher_check
        ),
        "child_executor_dispatch_result_handoff_coverage": (
            _build_child_executor_dispatch_result_handoff_coverage(
                child_executor_dispatch_result_handoff_check
            )
        ),
        "child_executor_dispatch_result_retry_audit_coverage": (
            _build_child_executor_dispatch_result_retry_audit_coverage(
                child_executor_dispatch_result_retry_audit_check
            )
        ),
        "child_executor_sandbox_backend_coverage": _build_child_executor_sandbox_backend_coverage(
            child_executor_sandbox_backend_check
        ),
        "subagent_lane_query_detail_coverage": _build_subagent_lane_query_detail_coverage(subagent_lane_detail_check),
    }


def _build_runtime_contract_artifact_schema(runtime_contract_summary: dict[str, Any]) -> dict[str, Any]:
    missing_fields = [
        field_name
        for field_name in RUNTIME_CONTRACT_SUMMARY_REQUIRED_FIELDS
        if not _has_path(runtime_contract_summary, field_name)
    ]
    return {
        "contract_version": RUNTIME_CONTRACT_ARTIFACT_SCHEMA_VERSION,
        "overall_status": "degraded" if missing_fields else "healthy",
        "summary_required_fields": list(RUNTIME_CONTRACT_SUMMARY_REQUIRED_FIELDS),
        "summary_missing_fields": missing_fields,
    }


def _normalize_contract_checks(checks: list[Any]) -> list[dict[str, Any]]:
    return [dict(check) for check in checks if isinstance(check, dict)]


def _has_path(value: dict[str, Any], path: str) -> bool:
    current: Any = value
    for part in str(path or "").split("."):
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    return True


def _coerce_non_negative_int(value: Any, fallback: int) -> int:
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        return fallback
    return normalized if normalized >= 0 else fallback


def _build_approved_tool_execution_coverage(check: dict[str, Any]) -> dict[str, Any]:
    return {
        "bridge_smoke": bool(check.get("ok")) if check else False,
        "approved_tool_call_count": _coerce_non_negative_int(check.get("approved_tool_call_count"), 0),
        "approved_policy_original_status": str(check.get("approved_policy_original_status") or "").strip(),
        "approved_policy_override_status": str(check.get("approved_policy_override_status") or "").strip(),
        "deny_override_status": str(check.get("deny_override_status") or "").strip(),
        "deny_tool_call_count": _coerce_non_negative_int(check.get("deny_tool_call_count"), 0),
    }


def _build_sdk_tool_runtime_execution_coverage(check: dict[str, Any]) -> dict[str, Any]:
    bridge_smoke = (
        bool(check.get("ok"))
        and _coerce_non_negative_int(check.get("auto_tool_call_count"), 0) == 1
        and _coerce_non_negative_int(check.get("auto_tool_history_count"), 0) == 1
        and _coerce_non_negative_int(check.get("approved_tool_call_count"), 0) == 1
        and str(check.get("approved_policy_original_status") or "").strip() == "approval_required"
        and str(check.get("approved_policy_override_status") or "").strip() == "approved"
        and str(check.get("deny_override_status") or "").strip() == "policy_denied"
        and _coerce_non_negative_int(check.get("deny_tool_call_count"), 0) == 0
    )
    return {
        "bridge_smoke": bridge_smoke,
        "auto_tool_call_count": _coerce_non_negative_int(check.get("auto_tool_call_count"), 0),
        "auto_tool_history_count": _coerce_non_negative_int(check.get("auto_tool_history_count"), 0),
        "approved_tool_call_count": _coerce_non_negative_int(check.get("approved_tool_call_count"), 0),
        "approved_policy_original_status": str(check.get("approved_policy_original_status") or "").strip(),
        "approved_policy_override_status": str(check.get("approved_policy_override_status") or "").strip(),
        "deny_override_status": str(check.get("deny_override_status") or "").strip(),
        "deny_tool_call_count": _coerce_non_negative_int(check.get("deny_tool_call_count"), 0),
    }


def _build_tool_runtime_timeout_retry_coverage(check: dict[str, Any]) -> dict[str, Any]:
    retry_policy = str(check.get("retry_policy") or "").strip()
    timeout_enforcement = str(check.get("timeout_enforcement") or "").strip()
    recovered_retry_status = str(check.get("recovered_retry_status") or "").strip()
    exhausted_retry_status = str(check.get("exhausted_retry_status") or "").strip()
    timeout_metadata_status = str(check.get("timeout_metadata_status") or "").strip()
    timeout_metadata_enforcement = str(check.get("timeout_metadata_enforcement") or "").strip()
    timeout_retry_smoke = (
        bool(check.get("ok"))
        and retry_policy == "sync_exception_retry"
        and timeout_enforcement == "post_call_elapsed_check"
        and str(check.get("recovered_status") or "").strip() == "ok"
        and recovered_retry_status == "recovered"
        and _coerce_non_negative_int(check.get("recovered_attempt_count"), 0) == 2
        and str(check.get("exhausted_status") or "").strip() == "error"
        and exhausted_retry_status == "exhausted"
        and _coerce_non_negative_int(check.get("exhausted_attempt_count"), 0) == 2
        and str(check.get("timeout_status") or "").strip() == "timeout"
        and timeout_metadata_status == "exceeded"
        and timeout_metadata_enforcement == "post_call_elapsed_check"
        and not bool(check.get("hard_cancellation_claimed"))
        and not bool(check.get("sandbox_execution_claimed"))
        and not bool(check.get("worker_timeout_claimed"))
    )
    return {
        "timeout_retry_smoke": timeout_retry_smoke,
        "retry_policy": retry_policy,
        "timeout_enforcement": timeout_enforcement,
        "recovered_retry_status": recovered_retry_status,
        "recovered_attempt_count": _coerce_non_negative_int(check.get("recovered_attempt_count"), 0),
        "exhausted_retry_status": exhausted_retry_status,
        "exhausted_attempt_count": _coerce_non_negative_int(check.get("exhausted_attempt_count"), 0),
        "timeout_status": str(check.get("timeout_status") or "").strip(),
        "timeout_metadata_status": timeout_metadata_status,
        "timeout_metadata_enforcement": timeout_metadata_enforcement,
        "hard_cancellation_claimed": bool(check.get("hard_cancellation_claimed")),
        "sandbox_execution_claimed": bool(check.get("sandbox_execution_claimed")),
        "worker_timeout_claimed": bool(check.get("worker_timeout_claimed")),
    }


def _build_approval_lifecycle_recovery_coverage(check: dict[str, Any]) -> dict[str, Any]:
    replayed_submission_status = str(check.get("replayed_submission_status") or "").strip()
    ignored_submission_status = str(check.get("ignored_submission_status") or "").strip()
    resolved_recovery_reason = str(check.get("resolved_recovery_reason") or "").strip()
    alignment_smoke = (
        bool(check.get("ok"))
        and replayed_submission_status == "replayed"
        and ignored_submission_status == "ignored"
        and resolved_recovery_reason == "already_resolved"
    )
    return {
        "alignment_smoke": alignment_smoke,
        "replayed_submission_status": replayed_submission_status,
        "ignored_submission_status": ignored_submission_status,
        "resolved_recovery_reason": resolved_recovery_reason,
    }


def _build_subagent_lane_query_detail_coverage(check: dict[str, Any]) -> dict[str, Any]:
    return {
        "detail_smoke": bool(check.get("ok")) if check else False,
        "contract_version": str(check.get("contract_version") or "").strip(),
        "recording_state": str(check.get("recording_state") or "").strip(),
        "stage_count": _coerce_non_negative_int(check.get("stage_count"), 0),
        "recent_event_count": _coerce_non_negative_int(check.get("recent_event_count"), 0),
    }


def _build_checkpoint_resume_cursor_coverage(check: dict[str, Any]) -> dict[str, Any]:
    checkpoint_status = str(check.get("checkpoint_status") or "").strip()
    checkpoint_kind = str(check.get("checkpoint_kind") or "").strip()
    cursor_status = str(check.get("cursor_status") or "").strip()
    cursor_entrypoint = str(check.get("cursor_entrypoint") or "").strip()
    cursor_recovery_reason = str(check.get("cursor_recovery_reason") or "").strip()
    cursor_smoke = (
        bool(check.get("ok"))
        and checkpoint_status == "ready"
        and checkpoint_kind == "approval_waiting"
        and cursor_status == "ready"
        and cursor_entrypoint == "submit_approval.approved"
        and cursor_recovery_reason == "ready_via_registry"
    )
    return {
        "cursor_smoke": cursor_smoke,
        "checkpoint_status": checkpoint_status,
        "checkpoint_kind": checkpoint_kind,
        "cursor_status": cursor_status,
        "cursor_entrypoint": cursor_entrypoint,
        "cursor_recovery_reason": cursor_recovery_reason,
    }


def _build_embedded_sdk_persistence_coverage(check: dict[str, Any]) -> dict[str, Any]:
    memory_posture = str(check.get("memory_posture") or "").strip()
    durable_posture = str(check.get("durable_posture") or "").strip()
    degraded_posture = str(check.get("degraded_posture") or "").strip()
    memory_block_reason = str(check.get("memory_cross_process_block_reason") or "").strip()
    degraded_block_reason = str(check.get("degraded_cross_process_block_reason") or "").strip()
    durable_cross_process_candidate = bool(check.get("durable_cross_process_candidate"))
    production_gate_contract_version = str(check.get("production_recovery_gate_contract_version") or "").strip()
    production_gate_status = str(check.get("production_recovery_gate_status") or "").strip()
    production_gate_missing_sections = (
        check.get("production_recovery_gate_missing_sections")
        if isinstance(check.get("production_recovery_gate_missing_sections"), list)
        else []
    )
    production_default_enabled = bool(check.get("production_recovery_default_enabled"))
    worker_ownership_gate_contract_version = str(
        check.get("production_recovery_worker_ownership_gate_contract_version") or ""
    ).strip()
    worker_ownership_gate_status = str(
        check.get("production_recovery_worker_ownership_gate_status") or ""
    ).strip()
    worker_ownership_default_enabled = bool(
        check.get("production_recovery_worker_ownership_default_enabled")
    )
    worker_ownership_missing_sections = (
        check.get("production_recovery_worker_ownership_missing_sections")
        if isinstance(check.get("production_recovery_worker_ownership_missing_sections"), list)
        else []
    )
    persistence_smoke = (
        bool(check.get("ok"))
        and memory_posture == "memory_preview"
        and durable_posture == "durable_ready"
        and degraded_posture == "durable_degraded"
        and memory_block_reason == "workspace_backend_not_durable"
        and degraded_block_reason == "workspace_backend_fallback_active"
        and durable_cross_process_candidate
        and production_gate_contract_version == "phase-ii-durable-workspace-production-recovery-gate-v1"
        and production_gate_status == "blocked"
        and "descriptor_lifecycle_governance" not in production_gate_missing_sections
        and "registry_binding_resolution" not in production_gate_missing_sections
        and "checkpoint_resume_cursor_gate" not in production_gate_missing_sections
        and "loader_execution_handoff_policy" not in production_gate_missing_sections
        and "recovery_audit_operation_history" not in production_gate_missing_sections
        and "durable_backend_migration_rollout" in production_gate_missing_sections
        and "worker_ownership_production_gate" in production_gate_missing_sections
        and worker_ownership_gate_contract_version == "phase-ii-worker-ownership-production-gate-v1"
        and worker_ownership_gate_status == "blocked"
        and not worker_ownership_default_enabled
        and "vendor_lock_semantics" in worker_ownership_missing_sections
        and "heartbeat_renewal_supervisor" in worker_ownership_missing_sections
        and not production_default_enabled
    )
    return {
        "persistence_smoke": persistence_smoke,
        "contract_version": str(check.get("contract_version") or "").strip(),
        "memory_posture": memory_posture,
        "durable_posture": durable_posture,
        "degraded_posture": degraded_posture,
        "memory_cross_process_block_reason": memory_block_reason,
        "degraded_cross_process_block_reason": degraded_block_reason,
        "durable_cross_process_candidate": durable_cross_process_candidate,
        "production_recovery_gate_contract_version": production_gate_contract_version,
        "production_recovery_gate_status": production_gate_status,
        "production_recovery_gate_missing_sections": list(production_gate_missing_sections),
        "production_recovery_default_enabled": production_default_enabled,
        "production_recovery_worker_ownership_gate_contract_version": worker_ownership_gate_contract_version,
        "production_recovery_worker_ownership_gate_status": worker_ownership_gate_status,
        "production_recovery_worker_ownership_default_enabled": worker_ownership_default_enabled,
        "production_recovery_worker_ownership_missing_sections": list(worker_ownership_missing_sections),
    }


def _build_recovery_audit_operation_history_coverage(check: dict[str, Any]) -> dict[str, Any]:
    contract_version = str(check.get("recovery_audit_contract_version") or "").strip()
    audit_ready = bool(check.get("recovery_audit_ready"))
    operation_history_supported = bool(check.get("recovery_audit_operation_history_supported"))
    audit_summary_supported = bool(check.get("recovery_audit_summary_supported"))
    timeline_writer_available = bool(check.get("recovery_audit_timeline_writer_available"))
    idempotent_trace_dedupe = bool(check.get("recovery_audit_idempotent_trace_dedupe"))
    authorization_source = bool(check.get("recovery_audit_authorization_source"))
    audit_smoke = (
        bool(check.get("ok"))
        and contract_version == "phase-ii-recovery-audit-production-gate-v1"
        and audit_ready
        and operation_history_supported
        and audit_summary_supported
        and timeline_writer_available
        and idempotent_trace_dedupe
        and not authorization_source
    )
    return {
        "audit_smoke": audit_smoke,
        "contract_version": contract_version,
        "ready": audit_ready,
        "operation_history_supported": operation_history_supported,
        "audit_summary_supported": audit_summary_supported,
        "timeline_writer_available": timeline_writer_available,
        "idempotent_trace_dedupe": idempotent_trace_dedupe,
        "authorization_source": authorization_source,
    }


def _build_production_recovery_registry_checkpoint_policy_coverage(check: dict[str, Any]) -> dict[str, Any]:
    contract_version = str(check.get("registry_checkpoint_policy_contract_version") or "").strip()
    ready = bool(check.get("registry_checkpoint_policy_ready"))
    registry_binding_policy_ready = bool(check.get("registry_binding_policy_ready"))
    checkpoint_resume_cursor_policy_ready = bool(check.get("checkpoint_resume_cursor_policy_ready"))
    authorization_source = bool(check.get("registry_checkpoint_policy_authorization_source"))
    production_gate_missing_sections = (
        check.get("production_recovery_gate_missing_sections")
        if isinstance(check.get("production_recovery_gate_missing_sections"), list)
        else []
    )
    policy_smoke = (
        bool(check.get("ok"))
        and contract_version == "phase-ii-production-recovery-registry-checkpoint-policy-v1"
        and ready
        and registry_binding_policy_ready
        and checkpoint_resume_cursor_policy_ready
        and "registry_binding_resolution" not in production_gate_missing_sections
        and "checkpoint_resume_cursor_gate" not in production_gate_missing_sections
        and not authorization_source
    )
    return {
        "policy_smoke": policy_smoke,
        "contract_version": contract_version,
        "ready": ready,
        "registry_binding_policy_ready": registry_binding_policy_ready,
        "checkpoint_resume_cursor_policy_ready": checkpoint_resume_cursor_policy_ready,
        "authorization_source": authorization_source,
    }


def _build_worker_ownership_store_mode_coverage(check: dict[str, Any]) -> dict[str, Any]:
    default_mode = str(check.get("default_mode") or "").strip()
    default_mode_source = str(check.get("default_mode_source") or "").strip()
    default_adapter_kind = str(check.get("default_adapter_kind") or "").strip()
    strict_mode_status = str(check.get("strict_mode_status") or "").strip()
    fallback_mode_status = str(check.get("fallback_mode_status") or "").strip()
    production_gate_contract_version = str(check.get("production_gate_contract_version") or "").strip()
    production_gate_status = str(check.get("production_gate_status") or "").strip()
    production_gate_missing_sections = (
        check.get("production_gate_missing_sections")
        if isinstance(check.get("production_gate_missing_sections"), list)
        else []
    )
    production_default_enabled = bool(check.get("production_default_enabled"))
    vendor_lock_contract_version = str(check.get("vendor_lock_contract_version") or "").strip()
    vendor_lock_status = str(check.get("vendor_lock_status") or "").strip()
    vendor_lock_missing_sections = (
        check.get("vendor_lock_missing_sections")
        if isinstance(check.get("vendor_lock_missing_sections"), list)
        else []
    )
    vendor_lock_current_posture = str(check.get("vendor_lock_current_posture") or "").strip()
    vendor_lock_sql_row_lease_fencing = bool(check.get("vendor_lock_sql_row_lease_fencing"))
    vendor_lock_sql_row_lease_is_vendor_lock = bool(
        check.get("vendor_lock_sql_row_lease_is_vendor_lock")
    )
    vendor_lock_adapter_present = bool(check.get("vendor_lock_adapter_present"))
    vendor_lock_adapter_contract_version = str(
        check.get("vendor_lock_adapter_contract_version") or ""
    ).strip()
    vendor_lock_adapter_status = str(check.get("vendor_lock_adapter_status") or "").strip()
    vendor_lock_adapter_kind = str(check.get("vendor_lock_adapter_kind") or "").strip()
    vendor_lock_adapter_target_backend = str(
        check.get("vendor_lock_adapter_target_backend") or ""
    ).strip()
    vendor_lock_adapter_scope = str(check.get("vendor_lock_adapter_scope") or "").strip()
    vendor_lock_adapter_fencing_strategy = str(
        check.get("vendor_lock_adapter_fencing_strategy") or ""
    ).strip()
    vendor_lock_adapter_ttl_renewal_strategy = str(
        check.get("vendor_lock_adapter_ttl_renewal_strategy") or ""
    ).strip()
    vendor_lock_adapter_failover_strategy = str(
        check.get("vendor_lock_adapter_failover_strategy") or ""
    ).strip()
    vendor_lock_adapter_stale_cleanup_strategy = str(
        check.get("vendor_lock_adapter_stale_cleanup_strategy") or ""
    ).strip()
    vendor_lock_adapter_acquire_supported = bool(
        check.get("vendor_lock_adapter_acquire_supported")
    )
    vendor_lock_adapter_renew_supported = bool(check.get("vendor_lock_adapter_renew_supported"))
    vendor_lock_adapter_release_supported = bool(
        check.get("vendor_lock_adapter_release_supported")
    )
    vendor_lock_adapter_probe_supported = bool(check.get("vendor_lock_adapter_probe_supported"))
    vendor_lock_adapter_production_allowed = bool(
        check.get("vendor_lock_adapter_production_allowed")
    )
    vendor_lock_adapter_sql_row_lease_is_vendor_lock = bool(
        check.get("vendor_lock_adapter_sql_row_lease_is_vendor_lock")
    )
    vendor_lock_adapter_missing_sections = (
        check.get("vendor_lock_adapter_missing_sections")
        if isinstance(check.get("vendor_lock_adapter_missing_sections"), list)
        else []
    )
    postgres_probe_contract_version = str(check.get("postgres_probe_contract_version") or "").strip()
    postgres_probe_status = str(check.get("postgres_probe_status") or "").strip()
    postgres_probe_missing_sections = (
        check.get("postgres_probe_missing_sections")
        if isinstance(check.get("postgres_probe_missing_sections"), list)
        else []
    )
    postgres_probe_executes = bool(check.get("postgres_probe_executes"))
    postgres_probe_sql_row_lease_is_vendor_lock = bool(
        check.get("postgres_probe_sql_row_lease_is_vendor_lock")
    )
    postgres_probe_ready_status = str(check.get("postgres_probe_ready_status") or "").strip()
    postgres_probe_ready_executes = bool(check.get("postgres_probe_ready_executes"))
    postgres_execution_seam_contract_version = str(
        check.get("postgres_execution_seam_contract_version") or ""
    ).strip()
    postgres_execution_default_status = str(
        check.get("postgres_execution_default_status") or ""
    ).strip()
    postgres_execution_default_executor_bound = bool(
        check.get("postgres_execution_default_executor_bound")
    )
    postgres_execution_default_enabled_by_default = bool(
        check.get("postgres_execution_default_enabled_by_default")
    )
    postgres_execution_default_production_allowed = bool(
        check.get("postgres_execution_default_production_allowed")
    )
    postgres_execution_default_missing_sections = (
        check.get("postgres_execution_default_missing_sections")
        if isinstance(check.get("postgres_execution_default_missing_sections"), list)
        else []
    )
    postgres_execution_default_probe_status = str(
        check.get("postgres_execution_default_probe_status") or ""
    ).strip()
    postgres_execution_default_probe_executed = bool(
        check.get("postgres_execution_default_probe_executed")
    )
    postgres_execution_opt_in_status = str(
        check.get("postgres_execution_opt_in_status") or ""
    ).strip()
    postgres_execution_opt_in_executor_bound = bool(
        check.get("postgres_execution_opt_in_executor_bound")
    )
    postgres_execution_opt_in_enabled_by_default = bool(
        check.get("postgres_execution_opt_in_enabled_by_default")
    )
    postgres_execution_opt_in_production_allowed = bool(
        check.get("postgres_execution_opt_in_production_allowed")
    )
    postgres_execution_opt_in_probe_status = str(
        check.get("postgres_execution_opt_in_probe_status") or ""
    ).strip()
    postgres_execution_opt_in_probe_executed = bool(
        check.get("postgres_execution_opt_in_probe_executed")
    )
    postgres_execution_opt_in_acquire_status = str(
        check.get("postgres_execution_opt_in_acquire_status") or ""
    ).strip()
    postgres_execution_opt_in_acquire_executed = bool(
        check.get("postgres_execution_opt_in_acquire_executed")
    )
    postgres_execution_opt_in_acquired = bool(check.get("postgres_execution_opt_in_acquired"))
    postgres_execution_opt_in_envelope_count = _coerce_non_negative_int(
        check.get("postgres_execution_opt_in_envelope_count"),
        0,
    )
    postgres_rollout_consumer_contract_version = str(
        check.get("postgres_rollout_consumer_contract_version") or ""
    ).strip()
    postgres_rollout_consumer_default_status = str(
        check.get("postgres_rollout_consumer_default_status") or ""
    ).strip()
    postgres_rollout_consumer_default_missing_sections = (
        check.get("postgres_rollout_consumer_default_missing_sections")
        if isinstance(check.get("postgres_rollout_consumer_default_missing_sections"), list)
        else []
    )
    postgres_rollout_consumer_default_will_enable_default = bool(
        check.get("postgres_rollout_consumer_default_will_enable_default")
    )
    postgres_rollout_consumer_default_executes_lock = bool(
        check.get("postgres_rollout_consumer_default_executes_lock")
    )
    postgres_rollout_consumer_ready_status = str(
        check.get("postgres_rollout_consumer_ready_status") or ""
    ).strip()
    postgres_rollout_consumer_ready_target_backend = str(
        check.get("postgres_rollout_consumer_ready_target_backend") or ""
    ).strip()
    postgres_rollout_consumer_ready_lock_adapter_kind = str(
        check.get("postgres_rollout_consumer_ready_lock_adapter_kind") or ""
    ).strip()
    postgres_rollout_consumer_ready_will_enable_default = bool(
        check.get("postgres_rollout_consumer_ready_will_enable_default")
    )
    postgres_rollout_consumer_ready_executes_lock = bool(
        check.get("postgres_rollout_consumer_ready_executes_lock")
    )
    postgres_rollout_consumer_input_source_status = str(
        check.get("postgres_rollout_consumer_input_source_status") or ""
    ).strip()
    postgres_rollout_consumer_input_source_ready = bool(
        check.get("postgres_rollout_consumer_input_source_ready")
    )
    postgres_rollout_consumer_input_source_kind = str(
        check.get("postgres_rollout_consumer_input_source_kind") or ""
    ).strip()
    postgres_target_binding_contract_version = str(
        check.get("postgres_target_binding_contract_version") or ""
    ).strip()
    postgres_target_binding_default_status = str(
        check.get("postgres_target_binding_default_status") or ""
    ).strip()
    postgres_target_binding_default_missing_sections = (
        check.get("postgres_target_binding_default_missing_sections")
        if isinstance(check.get("postgres_target_binding_default_missing_sections"), list)
        else []
    )
    postgres_target_binding_default_will_enable_lock = bool(
        check.get("postgres_target_binding_default_will_enable_lock")
    )
    postgres_target_binding_default_executes_lock = bool(
        check.get("postgres_target_binding_default_executes_lock")
    )
    postgres_target_binding_ready_status = str(
        check.get("postgres_target_binding_ready_status") or ""
    ).strip()
    postgres_target_binding_ready_target_backend = str(
        check.get("postgres_target_binding_ready_target_backend") or ""
    ).strip()
    postgres_target_binding_ready_lock_adapter_kind = str(
        check.get("postgres_target_binding_ready_lock_adapter_kind") or ""
    ).strip()
    postgres_target_binding_ready_will_enable_lock = bool(
        check.get("postgres_target_binding_ready_will_enable_lock")
    )
    postgres_target_binding_ready_executes_lock = bool(
        check.get("postgres_target_binding_ready_executes_lock")
    )
    postgres_target_binding_target_input_status = str(
        check.get("postgres_target_binding_target_input_status") or ""
    ).strip()
    postgres_target_binding_target_decision_status = str(
        check.get("postgres_target_binding_target_decision_status") or ""
    ).strip()
    postgres_target_binding_target_decision_production_allowed = bool(
        check.get("postgres_target_binding_target_decision_production_allowed")
    )
    postgres_semantics_binding_contract_version = str(
        check.get("postgres_semantics_binding_contract_version") or ""
    ).strip()
    postgres_semantics_binding_default_status = str(
        check.get("postgres_semantics_binding_default_status") or ""
    ).strip()
    postgres_semantics_binding_default_missing_sections = (
        check.get("postgres_semantics_binding_default_missing_sections")
        if isinstance(check.get("postgres_semantics_binding_default_missing_sections"), list)
        else []
    )
    postgres_semantics_binding_default_will_enable_lock = bool(
        check.get("postgres_semantics_binding_default_will_enable_lock")
    )
    postgres_semantics_binding_default_will_update_gate = bool(
        check.get("postgres_semantics_binding_default_will_update_gate")
    )
    postgres_semantics_binding_default_executes_lock = bool(
        check.get("postgres_semantics_binding_default_executes_lock")
    )
    postgres_semantics_binding_ready_status = str(
        check.get("postgres_semantics_binding_ready_status") or ""
    ).strip()
    postgres_semantics_binding_ready_target_backend = str(
        check.get("postgres_semantics_binding_ready_target_backend") or ""
    ).strip()
    postgres_semantics_binding_ready_lock_adapter_kind = str(
        check.get("postgres_semantics_binding_ready_lock_adapter_kind") or ""
    ).strip()
    postgres_semantics_binding_ready_probe_status = str(
        check.get("postgres_semantics_binding_ready_probe_status") or ""
    ).strip()
    postgres_semantics_binding_ready_adapter_status = str(
        check.get("postgres_semantics_binding_ready_adapter_status") or ""
    ).strip()
    postgres_semantics_binding_ready_semantics_status = str(
        check.get("postgres_semantics_binding_ready_semantics_status") or ""
    ).strip()
    postgres_semantics_binding_ready_will_enable_lock = bool(
        check.get("postgres_semantics_binding_ready_will_enable_lock")
    )
    postgres_semantics_binding_ready_will_update_gate = bool(
        check.get("postgres_semantics_binding_ready_will_update_gate")
    )
    postgres_semantics_binding_ready_executes_lock = bool(
        check.get("postgres_semantics_binding_ready_executes_lock")
    )
    postgres_wiring_decision_contract_version = str(
        check.get("postgres_wiring_decision_contract_version") or ""
    ).strip()
    postgres_wiring_decision_default_status = str(
        check.get("postgres_wiring_decision_default_status") or ""
    ).strip()
    postgres_wiring_decision_default_missing_sections = (
        check.get("postgres_wiring_decision_default_missing_sections")
        if isinstance(check.get("postgres_wiring_decision_default_missing_sections"), list)
        else []
    )
    postgres_wiring_decision_default_wiring_allowed = bool(
        check.get("postgres_wiring_decision_default_wiring_allowed")
    )
    postgres_wiring_decision_default_will_update_gate = bool(
        check.get("postgres_wiring_decision_default_will_update_gate")
    )
    postgres_wiring_decision_default_will_enable_lock = bool(
        check.get("postgres_wiring_decision_default_will_enable_lock")
    )
    postgres_wiring_decision_default_executes_lock = bool(
        check.get("postgres_wiring_decision_default_executes_lock")
    )
    postgres_wiring_decision_ready_status = str(
        check.get("postgres_wiring_decision_ready_status") or ""
    ).strip()
    postgres_wiring_decision_ready_semantics_binding_status = str(
        check.get("postgres_wiring_decision_ready_semantics_binding_status") or ""
    ).strip()
    postgres_wiring_decision_ready_candidate_status = str(
        check.get("postgres_wiring_decision_ready_candidate_status") or ""
    ).strip()
    postgres_wiring_decision_ready_wiring_allowed = bool(
        check.get("postgres_wiring_decision_ready_wiring_allowed")
    )
    postgres_wiring_decision_ready_target_backend = str(
        check.get("postgres_wiring_decision_ready_target_backend") or ""
    ).strip()
    postgres_wiring_decision_ready_lock_adapter_kind = str(
        check.get("postgres_wiring_decision_ready_lock_adapter_kind") or ""
    ).strip()
    postgres_wiring_decision_ready_will_update_gate = bool(
        check.get("postgres_wiring_decision_ready_will_update_gate")
    )
    postgres_wiring_decision_ready_will_enable_lock = bool(
        check.get("postgres_wiring_decision_ready_will_enable_lock")
    )
    postgres_wiring_decision_ready_executes_lock = bool(
        check.get("postgres_wiring_decision_ready_executes_lock")
    )
    production_dry_run_contract_version = str(
        check.get("production_dry_run_contract_version") or ""
    ).strip()
    production_dry_run_default_status = str(
        check.get("production_dry_run_default_status") or ""
    ).strip()
    production_dry_run_default_missing_sections = (
        check.get("production_dry_run_default_missing_sections")
        if isinstance(check.get("production_dry_run_default_missing_sections"), list)
        else []
    )
    production_dry_run_default_all_required_ready = bool(
        check.get("production_dry_run_default_all_required_ready")
    )
    production_dry_run_default_would_allow = bool(
        check.get("production_dry_run_default_would_allow")
    )
    production_dry_run_default_will_enable = bool(
        check.get("production_dry_run_default_will_enable")
    )
    production_dry_run_default_executes_lock = bool(
        check.get("production_dry_run_default_executes_lock")
    )
    production_dry_run_default_starts_worker = bool(
        check.get("production_dry_run_default_starts_worker")
    )
    production_dry_run_default_runs_auto_claim = bool(
        check.get("production_dry_run_default_runs_auto_claim")
    )
    production_dry_run_ready_status = str(
        check.get("production_dry_run_ready_status") or ""
    ).strip()
    production_dry_run_ready_missing_sections = (
        check.get("production_dry_run_ready_missing_sections")
        if isinstance(check.get("production_dry_run_ready_missing_sections"), list)
        else []
    )
    production_dry_run_ready_all_required_ready = bool(
        check.get("production_dry_run_ready_all_required_ready")
    )
    production_dry_run_ready_would_allow = bool(
        check.get("production_dry_run_ready_would_allow")
    )
    production_dry_run_ready_will_enable = bool(
        check.get("production_dry_run_ready_will_enable")
    )
    production_dry_run_ready_executes_lock = bool(
        check.get("production_dry_run_ready_executes_lock")
    )
    production_dry_run_ready_starts_worker = bool(
        check.get("production_dry_run_ready_starts_worker")
    )
    production_dry_run_ready_runs_auto_claim = bool(
        check.get("production_dry_run_ready_runs_auto_claim")
    )
    enablement_config_consumer_contract_version = str(
        check.get("enablement_config_consumer_contract_version") or ""
    ).strip()
    enablement_config_consumer_default_status = str(
        check.get("enablement_config_consumer_default_status") or ""
    ).strip()
    enablement_config_consumer_default_missing_sections = (
        check.get("enablement_config_consumer_default_missing_sections")
        if isinstance(
            check.get("enablement_config_consumer_default_missing_sections"), list
        )
        else []
    )
    enablement_config_consumer_default_will_enable = bool(
        check.get("enablement_config_consumer_default_will_enable")
    )
    enablement_config_consumer_default_executes_lock = bool(
        check.get("enablement_config_consumer_default_executes_lock")
    )
    enablement_config_consumer_default_starts_worker = bool(
        check.get("enablement_config_consumer_default_starts_worker")
    )
    enablement_config_consumer_default_runs_auto_claim = bool(
        check.get("enablement_config_consumer_default_runs_auto_claim")
    )
    enablement_config_consumer_ready_status = str(
        check.get("enablement_config_consumer_ready_status") or ""
    ).strip()
    enablement_config_consumer_ready_missing_sections = (
        check.get("enablement_config_consumer_ready_missing_sections")
        if isinstance(
            check.get("enablement_config_consumer_ready_missing_sections"), list
        )
        else []
    )
    enablement_config_consumer_ready_target_backend = str(
        check.get("enablement_config_consumer_ready_target_backend") or ""
    ).strip()
    enablement_config_consumer_ready_lock_adapter_kind = str(
        check.get("enablement_config_consumer_ready_lock_adapter_kind") or ""
    ).strip()
    enablement_config_consumer_ready_input_source_status = str(
        check.get("enablement_config_consumer_ready_input_source_status") or ""
    ).strip()
    enablement_config_consumer_ready_dry_run_status = str(
        check.get("enablement_config_consumer_ready_dry_run_status") or ""
    ).strip()
    enablement_config_consumer_ready_dry_run_would_allow = bool(
        check.get("enablement_config_consumer_ready_dry_run_would_allow")
    )
    enablement_config_consumer_ready_will_enable = bool(
        check.get("enablement_config_consumer_ready_will_enable")
    )
    enablement_config_consumer_ready_executes_lock = bool(
        check.get("enablement_config_consumer_ready_executes_lock")
    )
    enablement_config_consumer_ready_starts_worker = bool(
        check.get("enablement_config_consumer_ready_starts_worker")
    )
    enablement_config_consumer_ready_runs_auto_claim = bool(
        check.get("enablement_config_consumer_ready_runs_auto_claim")
    )
    enablement_config_factory_binding_default_status = str(
        check.get("enablement_config_factory_binding_default_status") or ""
    ).strip()
    enablement_config_factory_binding_ready_status = str(
        check.get("enablement_config_factory_binding_ready_status") or ""
    ).strip()
    enablement_config_factory_binding_ready_config_id = str(
        check.get("enablement_config_factory_binding_ready_config_id") or ""
    ).strip()
    enablement_config_factory_binding_will_enable = bool(
        check.get("enablement_config_factory_binding_will_enable")
    )
    enablement_config_factory_binding_executes_lock = bool(
        check.get("enablement_config_factory_binding_executes_lock")
    )
    enablement_config_factory_binding_starts_worker = bool(
        check.get("enablement_config_factory_binding_starts_worker")
    )
    enablement_config_factory_binding_runs_auto_claim = bool(
        check.get("enablement_config_factory_binding_runs_auto_claim")
    )
    enablement_config_factory_binding_smoke = (
        enablement_config_factory_binding_default_status == "blocked"
        and enablement_config_factory_binding_ready_status == "ready"
        and bool(enablement_config_factory_binding_ready_config_id)
        and not enablement_config_factory_binding_will_enable
        and not enablement_config_factory_binding_executes_lock
        and not enablement_config_factory_binding_starts_worker
        and not enablement_config_factory_binding_runs_auto_claim
    )
    vendor_lock_scope_defined = bool(check.get("vendor_lock_scope_defined"))
    vendor_lock_fencing_guarantee_defined = bool(
        check.get("vendor_lock_fencing_guarantee_defined")
    )
    vendor_lock_failover_semantics_defined = bool(
        check.get("vendor_lock_failover_semantics_defined")
    )
    vendor_lock_ttl_renewal_semantics_defined = bool(
        check.get("vendor_lock_ttl_renewal_semantics_defined")
    )
    vendor_lock_stale_owner_cleanup_defined = bool(
        check.get("vendor_lock_stale_owner_cleanup_defined")
    )
    vendor_lock_production_allowed = bool(check.get("vendor_lock_production_allowed"))
    vendor_lock_target_decision_contract_version = str(
        check.get("vendor_lock_target_decision_contract_version") or ""
    ).strip()
    vendor_lock_target_decision_status = str(
        check.get("vendor_lock_target_decision_status") or ""
    ).strip()
    vendor_lock_target_decision_recorded = bool(
        check.get("vendor_lock_target_decision_recorded")
    )
    vendor_lock_target_backend = str(check.get("vendor_lock_target_backend") or "").strip()
    vendor_lock_target_adapter_kind = str(
        check.get("vendor_lock_target_adapter_kind") or ""
    ).strip()
    vendor_lock_target_scope = str(check.get("vendor_lock_target_scope") or "").strip()
    vendor_lock_target_fencing_strategy = str(
        check.get("vendor_lock_target_fencing_strategy") or ""
    ).strip()
    vendor_lock_target_ttl_renewal_strategy = str(
        check.get("vendor_lock_target_ttl_renewal_strategy") or ""
    ).strip()
    vendor_lock_target_failover_strategy = str(
        check.get("vendor_lock_target_failover_strategy") or ""
    ).strip()
    vendor_lock_target_stale_cleanup_strategy = str(
        check.get("vendor_lock_target_stale_cleanup_strategy") or ""
    ).strip()
    vendor_lock_target_missing_sections = (
        check.get("vendor_lock_target_missing_sections")
        if isinstance(check.get("vendor_lock_target_missing_sections"), list)
        else []
    )
    vendor_lock_target_sql_row_lease_is_vendor_lock = bool(
        check.get("vendor_lock_target_sql_row_lease_is_vendor_lock")
    )
    vendor_lock_target_production_allowed = bool(
        check.get("vendor_lock_target_production_allowed")
    )
    vendor_lock_target_input_contract_version = str(
        check.get("vendor_lock_target_input_contract_version") or ""
    ).strip()
    vendor_lock_target_input_source_status = str(
        check.get("vendor_lock_target_input_source_status") or ""
    ).strip()
    vendor_lock_target_input_source_kind = str(
        check.get("vendor_lock_target_input_source_kind") or ""
    ).strip()
    vendor_lock_target_input_decision_id = str(
        check.get("vendor_lock_target_input_decision_id") or ""
    ).strip()
    vendor_lock_target_input_approved_by = str(
        check.get("vendor_lock_target_input_approved_by") or ""
    ).strip()
    vendor_lock_target_input_approved_at = str(
        check.get("vendor_lock_target_input_approved_at") or ""
    ).strip()
    vendor_lock_target_input_backend = str(
        check.get("vendor_lock_target_input_backend") or ""
    ).strip()
    vendor_lock_target_input_adapter_kind = str(
        check.get("vendor_lock_target_input_adapter_kind") or ""
    ).strip()
    vendor_lock_target_input_rollout_artifact = str(
        check.get("vendor_lock_target_input_rollout_artifact") or ""
    ).strip()
    vendor_lock_target_input_config_key = str(
        check.get("vendor_lock_target_input_config_key") or ""
    ).strip()
    vendor_lock_target_input_manual_approval_reference = str(
        check.get("vendor_lock_target_input_manual_approval_reference") or ""
    ).strip()
    vendor_lock_target_input_missing_sections = (
        check.get("vendor_lock_target_input_missing_sections")
        if isinstance(check.get("vendor_lock_target_input_missing_sections"), list)
        else []
    )
    vendor_lock_target_input_sql_row_lease_is_vendor_lock = bool(
        check.get("vendor_lock_target_input_sql_row_lease_is_vendor_lock")
    )
    renewal_supervisor_contract_version = str(
        check.get("renewal_supervisor_contract_version") or ""
    ).strip()
    renewal_supervisor_status = str(check.get("renewal_supervisor_status") or "").strip()
    renewal_supervisor_missing_sections = (
        check.get("renewal_supervisor_missing_sections")
        if isinstance(check.get("renewal_supervisor_missing_sections"), list)
        else []
    )
    renewal_supervisor_enabled_by_default = bool(
        check.get("renewal_supervisor_enabled_by_default")
    )
    renewal_supervisor_renew_once_supported = bool(
        check.get("renewal_supervisor_renew_once_supported")
    )
    renewal_supervisor_owner_identity_required = bool(
        check.get("renewal_supervisor_owner_identity_required")
    )
    renewal_supervisor_ttl_interval_policy_ready = bool(
        check.get("renewal_supervisor_ttl_interval_policy_ready")
    )
    renewal_supervisor_controlled_lifecycle_supported = bool(
        check.get("renewal_supervisor_controlled_lifecycle_supported")
    )
    renewal_supervisor_starts_by_default = bool(check.get("renewal_supervisor_starts_by_default"))
    renewal_supervisor_active = bool(check.get("renewal_supervisor_active"))
    renewal_supervisor_last_renewal_status = str(
        check.get("renewal_supervisor_last_renewal_status") or ""
    ).strip()
    renewal_supervisor_stop_supported = bool(check.get("renewal_supervisor_stop_supported"))
    renewal_supervisor_failure_fail_closed = bool(
        check.get("renewal_supervisor_failure_fail_closed")
    )
    renewal_supervisor_lease_loss_fail_closed = bool(
        check.get("renewal_supervisor_lease_loss_fail_closed")
    )
    renewal_supervisor_renew_once_status = str(
        check.get("renewal_supervisor_renew_once_status") or ""
    ).strip()
    renewal_supervisor_renew_once_background_started = bool(
        check.get("renewal_supervisor_renew_once_background_started")
    )
    renewal_supervisor_stale_fencing_status = str(
        check.get("renewal_supervisor_stale_fencing_status") or ""
    ).strip()
    renewal_supervisor_stale_fencing_reason = str(
        check.get("renewal_supervisor_stale_fencing_reason") or ""
    ).strip()
    renewal_supervisor_lifecycle_initial_active = bool(
        check.get("renewal_supervisor_lifecycle_initial_active")
    )
    renewal_supervisor_lifecycle_started_active = bool(
        check.get("renewal_supervisor_lifecycle_started_active")
    )
    renewal_supervisor_lifecycle_started_status = str(
        check.get("renewal_supervisor_lifecycle_started_status") or ""
    ).strip()
    renewal_supervisor_lifecycle_started_count = _coerce_non_negative_int(
        check.get("renewal_supervisor_lifecycle_started_count"),
        0,
    )
    renewal_supervisor_lifecycle_stopped_active = bool(
        check.get("renewal_supervisor_lifecycle_stopped_active")
    )
    renewal_supervisor_lifecycle_stopped_count = _coerce_non_negative_int(
        check.get("renewal_supervisor_lifecycle_stopped_count"),
        0,
    )
    rollout_readiness_contract_version = str(
        check.get("rollout_readiness_contract_version") or ""
    ).strip()
    rollout_readiness_status = str(check.get("rollout_readiness_status") or "").strip()
    rollout_missing_sections = (
        check.get("rollout_missing_sections")
        if isinstance(check.get("rollout_missing_sections"), list)
        else []
    )
    production_rollout_confirmed = bool(check.get("production_rollout_confirmed"))
    rollout_migration_ready = bool(check.get("rollout_migration_ready"))
    rollout_stale_fencing_verified = bool(check.get("rollout_stale_fencing_verified"))
    rollout_rollback_plan_ready = bool(check.get("rollout_rollback_plan_ready"))
    rollout_operationalization_status = str(
        check.get("rollout_operationalization_status") or ""
    ).strip()
    rollout_mode = str(check.get("rollout_mode") or "").strip()
    rollout_missing_artifacts = (
        check.get("rollout_missing_artifacts")
        if isinstance(check.get("rollout_missing_artifacts"), list)
        else []
    )
    rollout_rollback_plan_status = str(
        check.get("rollout_rollback_plan_status") or ""
    ).strip()
    rollout_fallback_policy_status = str(
        check.get("rollout_fallback_policy_status") or ""
    ).strip()
    rollout_renewal_lifecycle_verification_status = str(
        check.get("rollout_renewal_lifecycle_verification_status") or ""
    ).strip()
    rollout_auto_claim_decision_status = str(
        check.get("rollout_auto_claim_decision_status") or ""
    ).strip()
    rollout_confirmation_decision_contract_version = str(
        check.get("rollout_confirmation_decision_contract_version") or ""
    ).strip()
    rollout_confirmation_decision_status = str(
        check.get("rollout_confirmation_decision_status") or ""
    ).strip()
    rollout_decision_recorded = bool(check.get("rollout_decision_recorded"))
    rollout_decision_id = str(check.get("rollout_decision_id") or "").strip()
    rollout_approved_by = str(check.get("rollout_approved_by") or "").strip()
    rollout_approved_at = str(check.get("rollout_approved_at") or "").strip()
    rollout_target_store_mode = str(check.get("rollout_target_store_mode") or "").strip()
    rollout_confirmation_missing_sections = (
        check.get("rollout_confirmation_missing_sections")
        if isinstance(check.get("rollout_confirmation_missing_sections"), list)
        else []
    )
    rollout_confirmation_production_rollout_confirmed = bool(
        check.get("rollout_confirmation_production_rollout_confirmed")
    )
    rollout_confirmation_input_contract_version = str(
        check.get("rollout_confirmation_input_contract_version") or ""
    ).strip()
    rollout_confirmation_input_source_status = str(
        check.get("rollout_confirmation_input_source_status") or ""
    ).strip()
    rollout_confirmation_input_source_kind = str(
        check.get("rollout_confirmation_input_source_kind") or ""
    ).strip()
    rollout_confirmation_input_decision_id = str(
        check.get("rollout_confirmation_input_decision_id") or ""
    ).strip()
    rollout_confirmation_input_approved_by = str(
        check.get("rollout_confirmation_input_approved_by") or ""
    ).strip()
    rollout_confirmation_input_approved_at = str(
        check.get("rollout_confirmation_input_approved_at") or ""
    ).strip()
    rollout_confirmation_input_target_store_mode = str(
        check.get("rollout_confirmation_input_target_store_mode") or ""
    ).strip()
    rollout_confirmation_input_rollback_plan_reference = str(
        check.get("rollout_confirmation_input_rollback_plan_reference") or ""
    ).strip()
    rollout_confirmation_input_fallback_policy_reference = str(
        check.get("rollout_confirmation_input_fallback_policy_reference") or ""
    ).strip()
    rollout_confirmation_input_renewal_lifecycle_reference = str(
        check.get("rollout_confirmation_input_renewal_lifecycle_reference") or ""
    ).strip()
    rollout_confirmation_input_auto_claim_decision_reference = str(
        check.get("rollout_confirmation_input_auto_claim_decision_reference") or ""
    ).strip()
    rollout_confirmation_input_missing_sections = (
        check.get("rollout_confirmation_input_missing_sections")
        if isinstance(check.get("rollout_confirmation_input_missing_sections"), list)
        else []
    )
    rollout_confirmation_input_sql_row_lease_is_authority = bool(
        check.get("rollout_confirmation_input_sql_row_lease_is_authority")
    )
    auto_claim_policy_contract_version = str(
        check.get("auto_claim_policy_contract_version") or ""
    ).strip()
    auto_claim_policy_status = str(check.get("auto_claim_policy_status") or "").strip()
    auto_claim_missing_sections = (
        check.get("auto_claim_missing_sections")
        if isinstance(check.get("auto_claim_missing_sections"), list)
        else []
    )
    auto_claim_enabled_by_default = bool(check.get("auto_claim_enabled_by_default"))
    auto_claim_descriptor_evidence_fallback = bool(
        check.get("auto_claim_descriptor_evidence_fallback")
    )
    auto_claim_lease_validation_required = bool(check.get("auto_claim_lease_validation_required"))
    auto_claim_entrypoint_allowlist_ready = bool(
        check.get("auto_claim_entrypoint_allowlist_ready")
    )
    auto_claim_entrypoint_allowlist_contract_version = str(
        check.get("auto_claim_entrypoint_allowlist_contract_version") or ""
    ).strip()
    auto_claim_entrypoint_allowlist_status = str(
        check.get("auto_claim_entrypoint_allowlist_status") or ""
    ).strip()
    auto_claim_allowed_entrypoints = (
        check.get("auto_claim_allowed_entrypoints")
        if isinstance(check.get("auto_claim_allowed_entrypoints"), list)
        else []
    )
    auto_claim_missing_entrypoints = (
        check.get("auto_claim_missing_entrypoints")
        if isinstance(check.get("auto_claim_missing_entrypoints"), list)
        else []
    )
    auto_claim_default_auto_claim_enabled = bool(
        check.get("auto_claim_default_auto_claim_enabled")
    )
    auto_claim_requires_production_gate_ready = bool(
        check.get("auto_claim_requires_production_gate_ready")
    )
    auto_claim_enablement_gate_contract_version = str(
        check.get("auto_claim_enablement_gate_contract_version") or ""
    ).strip()
    auto_claim_enablement_gate_status = str(
        check.get("auto_claim_enablement_gate_status") or ""
    ).strip()
    auto_claim_will_auto_claim = bool(check.get("auto_claim_will_auto_claim"))
    auto_claim_requested_entrypoint = str(
        check.get("auto_claim_requested_entrypoint") or ""
    ).strip()
    auto_claim_enablement_missing_sections = (
        check.get("auto_claim_enablement_missing_sections")
        if isinstance(check.get("auto_claim_enablement_missing_sections"), list)
        else []
    )
    auto_claim_enablement_blocked_reason = str(
        check.get("auto_claim_enablement_blocked_reason") or ""
    ).strip()
    ownership_audit_contract_version = str(
        check.get("ownership_audit_contract_version") or ""
    ).strip()
    ownership_audit_status = str(check.get("ownership_audit_status") or "").strip()
    ownership_audit_missing_sections = (
        check.get("ownership_audit_missing_sections")
        if isinstance(check.get("ownership_audit_missing_sections"), list)
        else []
    )
    ownership_audit_compact_evidence = bool(check.get("ownership_audit_compact_evidence"))
    ownership_audit_operation_history_ready = bool(
        check.get("ownership_audit_operation_history_ready")
    )
    ownership_audit_recovery_operation_link_ready = bool(
        check.get("ownership_audit_recovery_operation_link_ready")
    )
    ownership_audit_timeline_writer_ready = bool(
        check.get("ownership_audit_timeline_writer_ready")
    )
    ownership_audit_idempotent_dedupe_ready = bool(
        check.get("ownership_audit_idempotent_dedupe_ready")
    )
    ownership_audit_authorization_source = bool(
        check.get("ownership_audit_authorization_source")
    )
    enablement_strategy_contract_version = str(
        check.get("enablement_strategy_contract_version") or ""
    ).strip()
    enablement_strategy_status = str(check.get("enablement_strategy_status") or "").strip()
    enablement_strategy_blocking_sections = (
        check.get("enablement_strategy_blocking_sections")
        if isinstance(check.get("enablement_strategy_blocking_sections"), list)
        else []
    )
    production_default_enabled_requested = bool(
        check.get("production_default_enabled_requested")
    )
    production_default_allowed = bool(check.get("production_default_allowed"))
    enablement_input_source_contract_version = str(
        check.get("enablement_input_source_contract_version") or ""
    ).strip()
    enablement_input_source_status = str(
        check.get("enablement_input_source_status") or ""
    ).strip()
    enablement_input_source_kind = str(check.get("enablement_input_source_kind") or "").strip()
    enablement_request_id = str(check.get("enablement_request_id") or "").strip()
    enablement_requested_by = str(check.get("enablement_requested_by") or "").strip()
    enablement_requested_at = str(check.get("enablement_requested_at") or "").strip()
    enablement_target_store_mode = str(check.get("enablement_target_store_mode") or "").strip()
    enablement_rollout_artifact = str(check.get("enablement_rollout_artifact") or "").strip()
    enablement_vendor_lock_decision_id = str(
        check.get("enablement_vendor_lock_decision_id") or ""
    ).strip()
    enablement_renewal_lifecycle_reference = str(
        check.get("enablement_renewal_lifecycle_reference") or ""
    ).strip()
    enablement_auto_claim_decision_reference = str(
        check.get("enablement_auto_claim_decision_reference") or ""
    ).strip()
    enablement_audit_evidence_reference = str(
        check.get("enablement_audit_evidence_reference") or ""
    ).strip()
    enablement_rollback_plan_reference = str(
        check.get("enablement_rollback_plan_reference") or ""
    ).strip()
    enablement_fallback_policy_reference = str(
        check.get("enablement_fallback_policy_reference") or ""
    ).strip()
    enablement_input_source_ready = bool(check.get("enablement_input_source_ready"))
    enablement_input_source_missing_sections = (
        check.get("enablement_input_source_missing_sections")
        if isinstance(check.get("enablement_input_source_missing_sections"), list)
        else []
    )
    enablement_explicit_required = bool(check.get("enablement_explicit_required"))
    enablement_all_required_sections_ready = bool(
        check.get("enablement_all_required_sections_ready")
    )
    enablement_fail_closed_when_blocked = bool(
        check.get("enablement_fail_closed_when_blocked")
    )
    enablement_sql_row_lease_not_default_authority = bool(
        check.get("enablement_sql_row_lease_not_default_authority")
    )
    default_durable = bool(check.get("default_durable"))
    configurable_knob_present = bool(check.get("configurable_knob_present"))
    hot_reloadable_knob_present = bool(check.get("hot_reloadable_knob_present"))
    mode_smoke = (
        bool(check.get("ok"))
        and default_mode == "memory_only"
        and default_mode_source == "default"
        and default_adapter_kind == "in_memory"
        and not default_durable
        and configurable_knob_present
        and hot_reloadable_knob_present
        and strict_mode_status == "sqlalchemy_durable"
        and fallback_mode_status == "fallback_to_memory"
        and production_gate_contract_version == "phase-ii-worker-ownership-production-gate-v1"
        and production_gate_status == "blocked"
        and "vendor_lock_semantics" in production_gate_missing_sections
        and "heartbeat_renewal_supervisor" in production_gate_missing_sections
        and not production_default_enabled
        and vendor_lock_contract_version
        == "phase-ii-worker-ownership-vendor-lock-semantics-v1"
        and vendor_lock_status == "blocked"
        and vendor_lock_current_posture == "sql_row_lease_fencing"
        and "vendor_lock_adapter" in vendor_lock_missing_sections
        and vendor_lock_sql_row_lease_fencing
        and not vendor_lock_sql_row_lease_is_vendor_lock
        and not vendor_lock_adapter_present
        and vendor_lock_adapter_contract_version
        == "phase-ii-worker-ownership-vendor-lock-adapter-v1"
        and vendor_lock_adapter_status == "blocked"
        and vendor_lock_adapter_kind == ""
        and vendor_lock_adapter_target_backend == ""
        and vendor_lock_adapter_scope == ""
        and vendor_lock_adapter_fencing_strategy == ""
        and vendor_lock_adapter_ttl_renewal_strategy == ""
        and vendor_lock_adapter_failover_strategy == ""
        and vendor_lock_adapter_stale_cleanup_strategy == ""
        and not vendor_lock_adapter_acquire_supported
        and not vendor_lock_adapter_renew_supported
        and not vendor_lock_adapter_release_supported
        and not vendor_lock_adapter_probe_supported
        and not vendor_lock_adapter_production_allowed
        and not vendor_lock_adapter_sql_row_lease_is_vendor_lock
        and "adapter_kind" in vendor_lock_adapter_missing_sections
        and "target_backend" in vendor_lock_adapter_missing_sections
        and postgres_probe_contract_version
        == "phase-ii-worker-ownership-postgres-vendor-lock-probe-v1"
        and postgres_probe_status == "blocked"
        and not postgres_probe_executes
        and not postgres_probe_sql_row_lease_is_vendor_lock
        and "advisory_lock_family" in postgres_probe_missing_sections
        and "probe_safety" in postgres_probe_missing_sections
        and postgres_probe_ready_status == "ready"
        and not postgres_probe_ready_executes
        and postgres_execution_seam_contract_version
        == "phase-ii-worker-ownership-postgres-advisory-lock-execution-seam-v1"
        and postgres_execution_default_status == "blocked"
        and not postgres_execution_default_executor_bound
        and not postgres_execution_default_enabled_by_default
        and not postgres_execution_default_production_allowed
        and "executor_binding" in postgres_execution_default_missing_sections
        and postgres_execution_default_probe_status == "blocked"
        and not postgres_execution_default_probe_executed
        and postgres_execution_opt_in_status == "ready"
        and postgres_execution_opt_in_executor_bound
        and not postgres_execution_opt_in_enabled_by_default
        and not postgres_execution_opt_in_production_allowed
        and postgres_execution_opt_in_probe_status == "ready"
        and postgres_execution_opt_in_probe_executed
        and postgres_execution_opt_in_acquire_status == "acquired"
        and postgres_execution_opt_in_acquire_executed
        and postgres_execution_opt_in_acquired
        and postgres_execution_opt_in_envelope_count == 2
        and postgres_rollout_consumer_contract_version
        == "phase-ii-worker-ownership-postgres-rollout-artifact-consumer-v1"
        and postgres_rollout_consumer_default_status == "blocked"
        and "source_kind" in postgres_rollout_consumer_default_missing_sections
        and "postgres_execution_seam" in postgres_rollout_consumer_default_missing_sections
        and not postgres_rollout_consumer_default_will_enable_default
        and not postgres_rollout_consumer_default_executes_lock
        and postgres_rollout_consumer_ready_status == "ready"
        and postgres_rollout_consumer_ready_target_backend == "postgres"
        and postgres_rollout_consumer_ready_lock_adapter_kind == "postgres_advisory_lock"
        and not postgres_rollout_consumer_ready_will_enable_default
        and not postgres_rollout_consumer_ready_executes_lock
        and postgres_rollout_consumer_input_source_status == "ready"
        and postgres_rollout_consumer_input_source_ready
        and postgres_rollout_consumer_input_source_kind == "rollout_artifact"
        and postgres_target_binding_contract_version
        == "phase-ii-worker-ownership-postgres-vendor-lock-target-artifact-binding-v1"
        and postgres_target_binding_default_status == "blocked"
        and "source_kind" in postgres_target_binding_default_missing_sections
        and "postgres_rollout_consumer" in postgres_target_binding_default_missing_sections
        and not postgres_target_binding_default_will_enable_lock
        and not postgres_target_binding_default_executes_lock
        and postgres_target_binding_ready_status == "ready"
        and postgres_target_binding_ready_target_backend == "postgres"
        and postgres_target_binding_ready_lock_adapter_kind == "postgres_advisory_lock"
        and not postgres_target_binding_ready_will_enable_lock
        and not postgres_target_binding_ready_executes_lock
        and postgres_target_binding_target_input_status == "ready"
        and postgres_target_binding_target_decision_status == "ready"
        and postgres_target_binding_target_decision_production_allowed
        and postgres_semantics_binding_contract_version
        == "phase-ii-worker-ownership-postgres-vendor-lock-semantics-binding-v1"
        and postgres_semantics_binding_default_status == "blocked"
        and "target_artifact_binding" in postgres_semantics_binding_default_missing_sections
        and "postgres_execution_seam" in postgres_semantics_binding_default_missing_sections
        and not postgres_semantics_binding_default_will_enable_lock
        and not postgres_semantics_binding_default_will_update_gate
        and not postgres_semantics_binding_default_executes_lock
        and postgres_semantics_binding_ready_status == "ready"
        and postgres_semantics_binding_ready_target_backend == "postgres"
        and postgres_semantics_binding_ready_lock_adapter_kind == "postgres_advisory_lock"
        and postgres_semantics_binding_ready_probe_status == "ready"
        and postgres_semantics_binding_ready_adapter_status == "ready"
        and postgres_semantics_binding_ready_semantics_status == "ready"
        and not postgres_semantics_binding_ready_will_enable_lock
        and not postgres_semantics_binding_ready_will_update_gate
        and not postgres_semantics_binding_ready_executes_lock
        and postgres_wiring_decision_contract_version
        == (
            "phase-ii-worker-ownership-postgres-vendor-lock-production-gate"
            "-wiring-decision-v1"
        )
        and postgres_wiring_decision_default_status == "blocked"
        and "semantics_binding" in postgres_wiring_decision_default_missing_sections
        and "decision_recorded" in postgres_wiring_decision_default_missing_sections
        and not postgres_wiring_decision_default_wiring_allowed
        and not postgres_wiring_decision_default_will_update_gate
        and not postgres_wiring_decision_default_will_enable_lock
        and not postgres_wiring_decision_default_executes_lock
        and postgres_wiring_decision_ready_status == "ready"
        and postgres_wiring_decision_ready_semantics_binding_status == "ready"
        and postgres_wiring_decision_ready_candidate_status == "ready"
        and postgres_wiring_decision_ready_wiring_allowed
        and postgres_wiring_decision_ready_target_backend == "postgres"
        and postgres_wiring_decision_ready_lock_adapter_kind == "postgres_advisory_lock"
        and not postgres_wiring_decision_ready_will_update_gate
        and not postgres_wiring_decision_ready_will_enable_lock
        and not postgres_wiring_decision_ready_executes_lock
        and production_dry_run_contract_version
        == "phase-ii-worker-ownership-production-gate-composition-dry-run-v1"
        and production_dry_run_default_status == "blocked"
        and "vendor_lock_wiring_decision" in production_dry_run_default_missing_sections
        and "heartbeat_renewal_supervisor" in production_dry_run_default_missing_sections
        and "rollout_confirmation" in production_dry_run_default_missing_sections
        and "recovery_entry_auto_claim_enablement"
        in production_dry_run_default_missing_sections
        and "ownership_audit_evidence" in production_dry_run_default_missing_sections
        and "production_default_enablement_input_source"
        in production_dry_run_default_missing_sections
        and not production_dry_run_default_all_required_ready
        and not production_dry_run_default_would_allow
        and not production_dry_run_default_will_enable
        and not production_dry_run_default_executes_lock
        and not production_dry_run_default_starts_worker
        and not production_dry_run_default_runs_auto_claim
        and production_dry_run_ready_status == "ready"
        and production_dry_run_ready_missing_sections == []
        and production_dry_run_ready_all_required_ready
        and production_dry_run_ready_would_allow
        and not production_dry_run_ready_will_enable
        and not production_dry_run_ready_executes_lock
        and not production_dry_run_ready_starts_worker
        and not production_dry_run_ready_runs_auto_claim
        and enablement_config_consumer_contract_version
        == (
            "phase-ii-worker-ownership-production-enablement-runtime-config"
            "-consumer-v1"
        )
        and enablement_config_consumer_default_status == "blocked"
        and "source_kind" in enablement_config_consumer_default_missing_sections
        and "config_id" in enablement_config_consumer_default_missing_sections
        and "enablement_input_source"
        in enablement_config_consumer_default_missing_sections
        and "composition_dry_run"
        in enablement_config_consumer_default_missing_sections
        and not enablement_config_consumer_default_will_enable
        and not enablement_config_consumer_default_executes_lock
        and not enablement_config_consumer_default_starts_worker
        and not enablement_config_consumer_default_runs_auto_claim
        and enablement_config_consumer_ready_status == "ready"
        and enablement_config_consumer_ready_missing_sections == []
        and enablement_config_consumer_ready_target_backend == "postgres"
        and enablement_config_consumer_ready_lock_adapter_kind
        == "postgres_advisory_lock"
        and enablement_config_consumer_ready_input_source_status == "ready"
        and enablement_config_consumer_ready_dry_run_status == "ready"
        and enablement_config_consumer_ready_dry_run_would_allow
        and not enablement_config_consumer_ready_will_enable
        and not enablement_config_consumer_ready_executes_lock
        and not enablement_config_consumer_ready_starts_worker
        and not enablement_config_consumer_ready_runs_auto_claim
        and enablement_config_factory_binding_smoke
        and not vendor_lock_scope_defined
        and not vendor_lock_fencing_guarantee_defined
        and not vendor_lock_failover_semantics_defined
        and not vendor_lock_ttl_renewal_semantics_defined
        and not vendor_lock_stale_owner_cleanup_defined
        and not vendor_lock_production_allowed
        and vendor_lock_target_decision_contract_version
        == "phase-ii-worker-ownership-vendor-lock-target-decision-v1"
        and vendor_lock_target_decision_status == "blocked"
        and not vendor_lock_target_decision_recorded
        and vendor_lock_target_backend == ""
        and vendor_lock_target_adapter_kind == ""
        and vendor_lock_target_scope == ""
        and vendor_lock_target_fencing_strategy == ""
        and vendor_lock_target_ttl_renewal_strategy == ""
        and vendor_lock_target_failover_strategy == ""
        and vendor_lock_target_stale_cleanup_strategy == ""
        and vendor_lock_target_input_contract_version
        == "phase-ii-worker-ownership-vendor-lock-target-decision-input-v1"
        and vendor_lock_target_input_source_status == "blocked"
        and vendor_lock_target_input_source_kind == ""
        and vendor_lock_target_input_decision_id == ""
        and vendor_lock_target_input_approved_by == ""
        and vendor_lock_target_input_approved_at == ""
        and vendor_lock_target_input_backend == ""
        and vendor_lock_target_input_adapter_kind == ""
        and vendor_lock_target_input_rollout_artifact == ""
        and vendor_lock_target_input_config_key == ""
        and vendor_lock_target_input_manual_approval_reference == ""
        and "input_source_kind" in vendor_lock_target_input_missing_sections
        and "decision_id" in vendor_lock_target_input_missing_sections
        and not vendor_lock_target_input_sql_row_lease_is_vendor_lock
        and "input_source" in vendor_lock_target_missing_sections
        and "decision_recorded" in vendor_lock_target_missing_sections
        and "target_backend" in vendor_lock_target_missing_sections
        and not vendor_lock_target_sql_row_lease_is_vendor_lock
        and not vendor_lock_target_production_allowed
        and renewal_supervisor_contract_version
        == "phase-ii-worker-ownership-renewal-supervisor-v1"
        and renewal_supervisor_status == "blocked"
        and "background_supervisor" in renewal_supervisor_missing_sections
        and not renewal_supervisor_enabled_by_default
        and renewal_supervisor_renew_once_supported
        and renewal_supervisor_owner_identity_required
        and renewal_supervisor_ttl_interval_policy_ready
        and renewal_supervisor_controlled_lifecycle_supported
        and not renewal_supervisor_starts_by_default
        and not renewal_supervisor_active
        and renewal_supervisor_last_renewal_status == ""
        and renewal_supervisor_stop_supported
        and renewal_supervisor_failure_fail_closed
        and renewal_supervisor_lease_loss_fail_closed
        and renewal_supervisor_renew_once_status == "renewed"
        and not renewal_supervisor_renew_once_background_started
        and renewal_supervisor_stale_fencing_status == "blocked"
        and renewal_supervisor_stale_fencing_reason == "stale_worker_fencing_token"
        and not renewal_supervisor_lifecycle_initial_active
        and renewal_supervisor_lifecycle_started_active
        and renewal_supervisor_lifecycle_started_status == "renewed"
        and renewal_supervisor_lifecycle_started_count >= 1
        and not renewal_supervisor_lifecycle_stopped_active
        and renewal_supervisor_lifecycle_stopped_count >= 1
        and rollout_readiness_contract_version
        == "phase-ii-worker-ownership-rollout-readiness-v1"
        and rollout_readiness_status == "blocked"
        and "strict_mode_rollout" in rollout_missing_sections
        and not production_rollout_confirmed
        and rollout_migration_ready
        and rollout_stale_fencing_verified
        and not rollout_rollback_plan_ready
        and rollout_operationalization_status == "blocked"
        and rollout_mode == "readiness_only"
        and "rollback_plan" in rollout_missing_artifacts
        and rollout_rollback_plan_status == "missing"
        and rollout_fallback_policy_status == "missing"
        and rollout_renewal_lifecycle_verification_status == "missing"
        and rollout_auto_claim_decision_status == "missing"
        and rollout_confirmation_decision_contract_version
        == "phase-ii-worker-ownership-rollout-confirmation-decision-v1"
        and rollout_confirmation_decision_status == "blocked"
        and not rollout_decision_recorded
        and rollout_target_store_mode == ""
        and "decision_recorded" in rollout_confirmation_missing_sections
        and not rollout_confirmation_production_rollout_confirmed
        and rollout_confirmation_input_contract_version
        == "phase-ii-worker-ownership-rollout-confirmation-input-source-v1"
        and rollout_confirmation_input_source_status == "blocked"
        and rollout_confirmation_input_source_kind == ""
        and rollout_confirmation_input_decision_id == ""
        and "input_source_kind" in rollout_confirmation_input_missing_sections
        and "decision_id" in rollout_confirmation_input_missing_sections
        and not rollout_confirmation_input_sql_row_lease_is_authority
        and auto_claim_policy_contract_version
        == "phase-ii-worker-ownership-auto-claim-policy-v1"
        and auto_claim_policy_status == "blocked"
        and "explicit_runtime_configuration" in auto_claim_missing_sections
        and not auto_claim_enabled_by_default
        and auto_claim_descriptor_evidence_fallback
        and auto_claim_lease_validation_required
        and auto_claim_entrypoint_allowlist_ready
        and auto_claim_entrypoint_allowlist_contract_version
        == "phase-ii-worker-ownership-auto-claim-entrypoint-allowlist-v1"
        and auto_claim_entrypoint_allowlist_status == "ready"
        and "submit_approval.approved" in auto_claim_allowed_entrypoints
        and "resume_run.continue_loop" in auto_claim_allowed_entrypoints
        and not auto_claim_missing_entrypoints
        and not auto_claim_default_auto_claim_enabled
        and auto_claim_requires_production_gate_ready
        and auto_claim_enablement_gate_contract_version
        == "phase-ii-worker-ownership-explicit-auto-claim-enablement-gate-v1"
        and auto_claim_enablement_gate_status == "blocked"
        and not auto_claim_will_auto_claim
        and auto_claim_requested_entrypoint == "submit_approval.approved"
        and "explicit_runtime_configuration" in auto_claim_enablement_missing_sections
        and auto_claim_enablement_blocked_reason
        == "explicit_runtime_configuration_missing"
        and ownership_audit_contract_version
        == "phase-ii-worker-ownership-audit-evidence-v1"
        and ownership_audit_status == "blocked"
        and "operation_history" in ownership_audit_missing_sections
        and ownership_audit_compact_evidence
        and not ownership_audit_operation_history_ready
        and not ownership_audit_recovery_operation_link_ready
        and not ownership_audit_timeline_writer_ready
        and not ownership_audit_idempotent_dedupe_ready
        and not ownership_audit_authorization_source
        and enablement_strategy_contract_version
        == "phase-ii-worker-ownership-production-enablement-strategy-v1"
        and enablement_strategy_status == "blocked"
        and "vendor_lock_semantics" in enablement_strategy_blocking_sections
        and "production_default_enablement_input_source" in enablement_strategy_blocking_sections
        and not production_default_enabled_requested
        and not production_default_allowed
        and enablement_input_source_contract_version
        == "phase-ii-worker-ownership-production-default-enablement-input-source-v1"
        and enablement_input_source_status == "blocked"
        and enablement_input_source_kind == ""
        and enablement_request_id == ""
        and enablement_target_store_mode == ""
        and enablement_rollout_artifact == ""
        and not enablement_input_source_ready
        and "input_source_kind" in enablement_input_source_missing_sections
        and enablement_explicit_required
        and not enablement_all_required_sections_ready
        and enablement_fail_closed_when_blocked
        and enablement_sql_row_lease_not_default_authority
    )
    return {
        "mode_smoke": mode_smoke,
        "default_mode": default_mode,
        "default_mode_source": default_mode_source,
        "default_adapter_kind": default_adapter_kind,
        "default_durable": default_durable,
        "configurable_knob_present": configurable_knob_present,
        "hot_reloadable_knob_present": hot_reloadable_knob_present,
        "strict_mode_status": strict_mode_status,
        "fallback_mode_status": fallback_mode_status,
        "production_gate_contract_version": production_gate_contract_version,
        "production_gate_status": production_gate_status,
        "production_gate_missing_sections": list(production_gate_missing_sections),
        "production_default_enabled": production_default_enabled,
        "vendor_lock_contract_version": vendor_lock_contract_version,
        "vendor_lock_status": vendor_lock_status,
        "vendor_lock_missing_sections": list(vendor_lock_missing_sections),
        "vendor_lock_current_posture": vendor_lock_current_posture,
        "vendor_lock_sql_row_lease_fencing": vendor_lock_sql_row_lease_fencing,
        "vendor_lock_sql_row_lease_is_vendor_lock": vendor_lock_sql_row_lease_is_vendor_lock,
        "vendor_lock_adapter_present": vendor_lock_adapter_present,
        "vendor_lock_adapter_contract_version": vendor_lock_adapter_contract_version,
        "vendor_lock_adapter_status": vendor_lock_adapter_status,
        "vendor_lock_adapter_kind": vendor_lock_adapter_kind,
        "vendor_lock_adapter_target_backend": vendor_lock_adapter_target_backend,
        "vendor_lock_adapter_scope": vendor_lock_adapter_scope,
        "vendor_lock_adapter_fencing_strategy": vendor_lock_adapter_fencing_strategy,
        "vendor_lock_adapter_ttl_renewal_strategy": vendor_lock_adapter_ttl_renewal_strategy,
        "vendor_lock_adapter_failover_strategy": vendor_lock_adapter_failover_strategy,
        "vendor_lock_adapter_stale_cleanup_strategy": vendor_lock_adapter_stale_cleanup_strategy,
        "vendor_lock_adapter_acquire_supported": vendor_lock_adapter_acquire_supported,
        "vendor_lock_adapter_renew_supported": vendor_lock_adapter_renew_supported,
        "vendor_lock_adapter_release_supported": vendor_lock_adapter_release_supported,
        "vendor_lock_adapter_probe_supported": vendor_lock_adapter_probe_supported,
        "vendor_lock_adapter_production_allowed": vendor_lock_adapter_production_allowed,
        "vendor_lock_adapter_sql_row_lease_is_vendor_lock": (
            vendor_lock_adapter_sql_row_lease_is_vendor_lock
        ),
        "vendor_lock_adapter_missing_sections": list(vendor_lock_adapter_missing_sections),
        "postgres_probe_contract_version": postgres_probe_contract_version,
        "postgres_probe_status": postgres_probe_status,
        "postgres_probe_missing_sections": list(postgres_probe_missing_sections),
        "postgres_probe_executes": postgres_probe_executes,
        "postgres_probe_sql_row_lease_is_vendor_lock": postgres_probe_sql_row_lease_is_vendor_lock,
        "postgres_probe_ready_status": postgres_probe_ready_status,
        "postgres_probe_ready_executes": postgres_probe_ready_executes,
        "postgres_execution_seam_contract_version": postgres_execution_seam_contract_version,
        "postgres_execution_default_status": postgres_execution_default_status,
        "postgres_execution_default_executor_bound": postgres_execution_default_executor_bound,
        "postgres_execution_default_enabled_by_default": (
            postgres_execution_default_enabled_by_default
        ),
        "postgres_execution_default_production_allowed": (
            postgres_execution_default_production_allowed
        ),
        "postgres_execution_default_missing_sections": list(
            postgres_execution_default_missing_sections
        ),
        "postgres_execution_default_probe_status": postgres_execution_default_probe_status,
        "postgres_execution_default_probe_executed": postgres_execution_default_probe_executed,
        "postgres_execution_opt_in_status": postgres_execution_opt_in_status,
        "postgres_execution_opt_in_executor_bound": postgres_execution_opt_in_executor_bound,
        "postgres_execution_opt_in_enabled_by_default": (
            postgres_execution_opt_in_enabled_by_default
        ),
        "postgres_execution_opt_in_production_allowed": (
            postgres_execution_opt_in_production_allowed
        ),
        "postgres_execution_opt_in_probe_status": postgres_execution_opt_in_probe_status,
        "postgres_execution_opt_in_probe_executed": postgres_execution_opt_in_probe_executed,
        "postgres_execution_opt_in_acquire_status": postgres_execution_opt_in_acquire_status,
        "postgres_execution_opt_in_acquire_executed": postgres_execution_opt_in_acquire_executed,
        "postgres_execution_opt_in_acquired": postgres_execution_opt_in_acquired,
        "postgres_execution_opt_in_envelope_count": postgres_execution_opt_in_envelope_count,
        "postgres_rollout_consumer_contract_version": postgres_rollout_consumer_contract_version,
        "postgres_rollout_consumer_default_status": postgres_rollout_consumer_default_status,
        "postgres_rollout_consumer_default_missing_sections": list(
            postgres_rollout_consumer_default_missing_sections
        ),
        "postgres_rollout_consumer_default_will_enable_default": (
            postgres_rollout_consumer_default_will_enable_default
        ),
        "postgres_rollout_consumer_default_executes_lock": (
            postgres_rollout_consumer_default_executes_lock
        ),
        "postgres_rollout_consumer_ready_status": postgres_rollout_consumer_ready_status,
        "postgres_rollout_consumer_ready_target_backend": (
            postgres_rollout_consumer_ready_target_backend
        ),
        "postgres_rollout_consumer_ready_lock_adapter_kind": (
            postgres_rollout_consumer_ready_lock_adapter_kind
        ),
        "postgres_rollout_consumer_ready_will_enable_default": (
            postgres_rollout_consumer_ready_will_enable_default
        ),
        "postgres_rollout_consumer_ready_executes_lock": (
            postgres_rollout_consumer_ready_executes_lock
        ),
        "postgres_rollout_consumer_input_source_status": (
            postgres_rollout_consumer_input_source_status
        ),
        "postgres_rollout_consumer_input_source_ready": (
            postgres_rollout_consumer_input_source_ready
        ),
        "postgres_rollout_consumer_input_source_kind": (
            postgres_rollout_consumer_input_source_kind
        ),
        "postgres_target_binding_contract_version": postgres_target_binding_contract_version,
        "postgres_target_binding_default_status": postgres_target_binding_default_status,
        "postgres_target_binding_default_missing_sections": list(
            postgres_target_binding_default_missing_sections
        ),
        "postgres_target_binding_default_will_enable_lock": (
            postgres_target_binding_default_will_enable_lock
        ),
        "postgres_target_binding_default_executes_lock": (
            postgres_target_binding_default_executes_lock
        ),
        "postgres_target_binding_ready_status": postgres_target_binding_ready_status,
        "postgres_target_binding_ready_target_backend": (
            postgres_target_binding_ready_target_backend
        ),
        "postgres_target_binding_ready_lock_adapter_kind": (
            postgres_target_binding_ready_lock_adapter_kind
        ),
        "postgres_target_binding_ready_will_enable_lock": (
            postgres_target_binding_ready_will_enable_lock
        ),
        "postgres_target_binding_ready_executes_lock": (
            postgres_target_binding_ready_executes_lock
        ),
        "postgres_target_binding_target_input_status": (
            postgres_target_binding_target_input_status
        ),
        "postgres_target_binding_target_decision_status": (
            postgres_target_binding_target_decision_status
        ),
        "postgres_target_binding_target_decision_production_allowed": (
            postgres_target_binding_target_decision_production_allowed
        ),
        "postgres_semantics_binding_contract_version": (
            postgres_semantics_binding_contract_version
        ),
        "postgres_semantics_binding_default_status": (
            postgres_semantics_binding_default_status
        ),
        "postgres_semantics_binding_default_missing_sections": list(
            postgres_semantics_binding_default_missing_sections
        ),
        "postgres_semantics_binding_default_will_enable_lock": (
            postgres_semantics_binding_default_will_enable_lock
        ),
        "postgres_semantics_binding_default_will_update_gate": (
            postgres_semantics_binding_default_will_update_gate
        ),
        "postgres_semantics_binding_default_executes_lock": (
            postgres_semantics_binding_default_executes_lock
        ),
        "postgres_semantics_binding_ready_status": postgres_semantics_binding_ready_status,
        "postgres_semantics_binding_ready_target_backend": (
            postgres_semantics_binding_ready_target_backend
        ),
        "postgres_semantics_binding_ready_lock_adapter_kind": (
            postgres_semantics_binding_ready_lock_adapter_kind
        ),
        "postgres_semantics_binding_ready_probe_status": (
            postgres_semantics_binding_ready_probe_status
        ),
        "postgres_semantics_binding_ready_adapter_status": (
            postgres_semantics_binding_ready_adapter_status
        ),
        "postgres_semantics_binding_ready_semantics_status": (
            postgres_semantics_binding_ready_semantics_status
        ),
        "postgres_semantics_binding_ready_will_enable_lock": (
            postgres_semantics_binding_ready_will_enable_lock
        ),
        "postgres_semantics_binding_ready_will_update_gate": (
            postgres_semantics_binding_ready_will_update_gate
        ),
        "postgres_semantics_binding_ready_executes_lock": (
            postgres_semantics_binding_ready_executes_lock
        ),
        "postgres_wiring_decision_contract_version": (
            postgres_wiring_decision_contract_version
        ),
        "postgres_wiring_decision_default_status": (
            postgres_wiring_decision_default_status
        ),
        "postgres_wiring_decision_default_missing_sections": list(
            postgres_wiring_decision_default_missing_sections
        ),
        "postgres_wiring_decision_default_wiring_allowed": (
            postgres_wiring_decision_default_wiring_allowed
        ),
        "postgres_wiring_decision_default_will_update_gate": (
            postgres_wiring_decision_default_will_update_gate
        ),
        "postgres_wiring_decision_default_will_enable_lock": (
            postgres_wiring_decision_default_will_enable_lock
        ),
        "postgres_wiring_decision_default_executes_lock": (
            postgres_wiring_decision_default_executes_lock
        ),
        "postgres_wiring_decision_ready_status": (
            postgres_wiring_decision_ready_status
        ),
        "postgres_wiring_decision_ready_semantics_binding_status": (
            postgres_wiring_decision_ready_semantics_binding_status
        ),
        "postgres_wiring_decision_ready_candidate_status": (
            postgres_wiring_decision_ready_candidate_status
        ),
        "postgres_wiring_decision_ready_wiring_allowed": (
            postgres_wiring_decision_ready_wiring_allowed
        ),
        "postgres_wiring_decision_ready_target_backend": (
            postgres_wiring_decision_ready_target_backend
        ),
        "postgres_wiring_decision_ready_lock_adapter_kind": (
            postgres_wiring_decision_ready_lock_adapter_kind
        ),
        "postgres_wiring_decision_ready_will_update_gate": (
            postgres_wiring_decision_ready_will_update_gate
        ),
        "postgres_wiring_decision_ready_will_enable_lock": (
            postgres_wiring_decision_ready_will_enable_lock
        ),
        "postgres_wiring_decision_ready_executes_lock": (
            postgres_wiring_decision_ready_executes_lock
        ),
        "production_dry_run_contract_version": production_dry_run_contract_version,
        "production_dry_run_default_status": production_dry_run_default_status,
        "production_dry_run_default_missing_sections": list(
            production_dry_run_default_missing_sections
        ),
        "production_dry_run_default_all_required_ready": (
            production_dry_run_default_all_required_ready
        ),
        "production_dry_run_default_would_allow": (
            production_dry_run_default_would_allow
        ),
        "production_dry_run_default_will_enable": (
            production_dry_run_default_will_enable
        ),
        "production_dry_run_default_executes_lock": (
            production_dry_run_default_executes_lock
        ),
        "production_dry_run_default_starts_worker": (
            production_dry_run_default_starts_worker
        ),
        "production_dry_run_default_runs_auto_claim": (
            production_dry_run_default_runs_auto_claim
        ),
        "production_dry_run_ready_status": production_dry_run_ready_status,
        "production_dry_run_ready_missing_sections": list(
            production_dry_run_ready_missing_sections
        ),
        "production_dry_run_ready_all_required_ready": (
            production_dry_run_ready_all_required_ready
        ),
        "production_dry_run_ready_would_allow": production_dry_run_ready_would_allow,
        "production_dry_run_ready_will_enable": production_dry_run_ready_will_enable,
        "production_dry_run_ready_executes_lock": production_dry_run_ready_executes_lock,
        "production_dry_run_ready_starts_worker": production_dry_run_ready_starts_worker,
        "production_dry_run_ready_runs_auto_claim": (
            production_dry_run_ready_runs_auto_claim
        ),
        "enablement_config_consumer_contract_version": (
            enablement_config_consumer_contract_version
        ),
        "enablement_config_consumer_default_status": (
            enablement_config_consumer_default_status
        ),
        "enablement_config_consumer_default_missing_sections": list(
            enablement_config_consumer_default_missing_sections
        ),
        "enablement_config_consumer_default_will_enable": (
            enablement_config_consumer_default_will_enable
        ),
        "enablement_config_consumer_default_executes_lock": (
            enablement_config_consumer_default_executes_lock
        ),
        "enablement_config_consumer_default_starts_worker": (
            enablement_config_consumer_default_starts_worker
        ),
        "enablement_config_consumer_default_runs_auto_claim": (
            enablement_config_consumer_default_runs_auto_claim
        ),
        "enablement_config_consumer_ready_status": (
            enablement_config_consumer_ready_status
        ),
        "enablement_config_consumer_ready_missing_sections": list(
            enablement_config_consumer_ready_missing_sections
        ),
        "enablement_config_consumer_ready_target_backend": (
            enablement_config_consumer_ready_target_backend
        ),
        "enablement_config_consumer_ready_lock_adapter_kind": (
            enablement_config_consumer_ready_lock_adapter_kind
        ),
        "enablement_config_consumer_ready_input_source_status": (
            enablement_config_consumer_ready_input_source_status
        ),
        "enablement_config_consumer_ready_dry_run_status": (
            enablement_config_consumer_ready_dry_run_status
        ),
        "enablement_config_consumer_ready_dry_run_would_allow": (
            enablement_config_consumer_ready_dry_run_would_allow
        ),
        "enablement_config_consumer_ready_will_enable": (
            enablement_config_consumer_ready_will_enable
        ),
        "enablement_config_consumer_ready_executes_lock": (
            enablement_config_consumer_ready_executes_lock
        ),
        "enablement_config_consumer_ready_starts_worker": (
            enablement_config_consumer_ready_starts_worker
        ),
        "enablement_config_consumer_ready_runs_auto_claim": (
            enablement_config_consumer_ready_runs_auto_claim
        ),
        "enablement_config_factory_binding_smoke": (
            enablement_config_factory_binding_smoke
        ),
        "enablement_config_factory_binding_default_status": (
            enablement_config_factory_binding_default_status
        ),
        "enablement_config_factory_binding_ready_status": (
            enablement_config_factory_binding_ready_status
        ),
        "enablement_config_factory_binding_ready_config_id": (
            enablement_config_factory_binding_ready_config_id
        ),
        "enablement_config_factory_binding_will_enable": (
            enablement_config_factory_binding_will_enable
        ),
        "enablement_config_factory_binding_executes_lock": (
            enablement_config_factory_binding_executes_lock
        ),
        "enablement_config_factory_binding_starts_worker": (
            enablement_config_factory_binding_starts_worker
        ),
        "enablement_config_factory_binding_runs_auto_claim": (
            enablement_config_factory_binding_runs_auto_claim
        ),
        "vendor_lock_scope_defined": vendor_lock_scope_defined,
        "vendor_lock_fencing_guarantee_defined": vendor_lock_fencing_guarantee_defined,
        "vendor_lock_failover_semantics_defined": vendor_lock_failover_semantics_defined,
        "vendor_lock_ttl_renewal_semantics_defined": vendor_lock_ttl_renewal_semantics_defined,
        "vendor_lock_stale_owner_cleanup_defined": vendor_lock_stale_owner_cleanup_defined,
        "vendor_lock_production_allowed": vendor_lock_production_allowed,
        "vendor_lock_target_decision_contract_version": vendor_lock_target_decision_contract_version,
        "vendor_lock_target_decision_status": vendor_lock_target_decision_status,
        "vendor_lock_target_decision_recorded": vendor_lock_target_decision_recorded,
        "vendor_lock_target_backend": vendor_lock_target_backend,
        "vendor_lock_target_adapter_kind": vendor_lock_target_adapter_kind,
        "vendor_lock_target_scope": vendor_lock_target_scope,
        "vendor_lock_target_fencing_strategy": vendor_lock_target_fencing_strategy,
        "vendor_lock_target_ttl_renewal_strategy": vendor_lock_target_ttl_renewal_strategy,
        "vendor_lock_target_failover_strategy": vendor_lock_target_failover_strategy,
        "vendor_lock_target_stale_cleanup_strategy": vendor_lock_target_stale_cleanup_strategy,
        "vendor_lock_target_missing_sections": list(vendor_lock_target_missing_sections),
        "vendor_lock_target_sql_row_lease_is_vendor_lock": (
            vendor_lock_target_sql_row_lease_is_vendor_lock
        ),
        "vendor_lock_target_production_allowed": vendor_lock_target_production_allowed,
        "vendor_lock_target_input_contract_version": vendor_lock_target_input_contract_version,
        "vendor_lock_target_input_source_status": vendor_lock_target_input_source_status,
        "vendor_lock_target_input_source_kind": vendor_lock_target_input_source_kind,
        "vendor_lock_target_input_decision_id": vendor_lock_target_input_decision_id,
        "vendor_lock_target_input_approved_by": vendor_lock_target_input_approved_by,
        "vendor_lock_target_input_approved_at": vendor_lock_target_input_approved_at,
        "vendor_lock_target_input_backend": vendor_lock_target_input_backend,
        "vendor_lock_target_input_adapter_kind": vendor_lock_target_input_adapter_kind,
        "vendor_lock_target_input_rollout_artifact": vendor_lock_target_input_rollout_artifact,
        "vendor_lock_target_input_config_key": vendor_lock_target_input_config_key,
        "vendor_lock_target_input_manual_approval_reference": (
            vendor_lock_target_input_manual_approval_reference
        ),
        "vendor_lock_target_input_missing_sections": list(
            vendor_lock_target_input_missing_sections
        ),
        "vendor_lock_target_input_sql_row_lease_is_vendor_lock": (
            vendor_lock_target_input_sql_row_lease_is_vendor_lock
        ),
        "renewal_supervisor_contract_version": renewal_supervisor_contract_version,
        "renewal_supervisor_status": renewal_supervisor_status,
        "renewal_supervisor_missing_sections": list(renewal_supervisor_missing_sections),
        "renewal_supervisor_enabled_by_default": renewal_supervisor_enabled_by_default,
        "renewal_supervisor_renew_once_supported": renewal_supervisor_renew_once_supported,
        "renewal_supervisor_owner_identity_required": renewal_supervisor_owner_identity_required,
        "renewal_supervisor_ttl_interval_policy_ready": renewal_supervisor_ttl_interval_policy_ready,
        "renewal_supervisor_controlled_lifecycle_supported": (
            renewal_supervisor_controlled_lifecycle_supported
        ),
        "renewal_supervisor_starts_by_default": renewal_supervisor_starts_by_default,
        "renewal_supervisor_active": renewal_supervisor_active,
        "renewal_supervisor_last_renewal_status": renewal_supervisor_last_renewal_status,
        "renewal_supervisor_stop_supported": renewal_supervisor_stop_supported,
        "renewal_supervisor_failure_fail_closed": renewal_supervisor_failure_fail_closed,
        "renewal_supervisor_lease_loss_fail_closed": renewal_supervisor_lease_loss_fail_closed,
        "renewal_supervisor_renew_once_status": renewal_supervisor_renew_once_status,
        "renewal_supervisor_renew_once_background_started": (
            renewal_supervisor_renew_once_background_started
        ),
        "renewal_supervisor_stale_fencing_status": renewal_supervisor_stale_fencing_status,
        "renewal_supervisor_stale_fencing_reason": renewal_supervisor_stale_fencing_reason,
        "renewal_supervisor_lifecycle_initial_active": renewal_supervisor_lifecycle_initial_active,
        "renewal_supervisor_lifecycle_started_active": renewal_supervisor_lifecycle_started_active,
        "renewal_supervisor_lifecycle_started_status": renewal_supervisor_lifecycle_started_status,
        "renewal_supervisor_lifecycle_started_count": renewal_supervisor_lifecycle_started_count,
        "renewal_supervisor_lifecycle_stopped_active": renewal_supervisor_lifecycle_stopped_active,
        "renewal_supervisor_lifecycle_stopped_count": renewal_supervisor_lifecycle_stopped_count,
        "rollout_readiness_contract_version": rollout_readiness_contract_version,
        "rollout_readiness_status": rollout_readiness_status,
        "rollout_missing_sections": list(rollout_missing_sections),
        "production_rollout_confirmed": production_rollout_confirmed,
        "rollout_migration_ready": rollout_migration_ready,
        "rollout_stale_fencing_verified": rollout_stale_fencing_verified,
        "rollout_rollback_plan_ready": rollout_rollback_plan_ready,
        "rollout_operationalization_status": rollout_operationalization_status,
        "rollout_mode": rollout_mode,
        "rollout_missing_artifacts": list(rollout_missing_artifacts),
        "rollout_rollback_plan_status": rollout_rollback_plan_status,
        "rollout_fallback_policy_status": rollout_fallback_policy_status,
        "rollout_renewal_lifecycle_verification_status": (
            rollout_renewal_lifecycle_verification_status
        ),
        "rollout_auto_claim_decision_status": rollout_auto_claim_decision_status,
        "rollout_confirmation_decision_contract_version": (
            rollout_confirmation_decision_contract_version
        ),
        "rollout_confirmation_decision_status": rollout_confirmation_decision_status,
        "rollout_decision_recorded": rollout_decision_recorded,
        "rollout_decision_id": rollout_decision_id,
        "rollout_approved_by": rollout_approved_by,
        "rollout_approved_at": rollout_approved_at,
        "rollout_target_store_mode": rollout_target_store_mode,
        "rollout_confirmation_missing_sections": list(
            rollout_confirmation_missing_sections
        ),
        "rollout_confirmation_production_rollout_confirmed": (
            rollout_confirmation_production_rollout_confirmed
        ),
        "rollout_confirmation_input_contract_version": (
            rollout_confirmation_input_contract_version
        ),
        "rollout_confirmation_input_source_status": rollout_confirmation_input_source_status,
        "rollout_confirmation_input_source_kind": rollout_confirmation_input_source_kind,
        "rollout_confirmation_input_decision_id": rollout_confirmation_input_decision_id,
        "rollout_confirmation_input_approved_by": rollout_confirmation_input_approved_by,
        "rollout_confirmation_input_approved_at": rollout_confirmation_input_approved_at,
        "rollout_confirmation_input_target_store_mode": (
            rollout_confirmation_input_target_store_mode
        ),
        "rollout_confirmation_input_rollback_plan_reference": (
            rollout_confirmation_input_rollback_plan_reference
        ),
        "rollout_confirmation_input_fallback_policy_reference": (
            rollout_confirmation_input_fallback_policy_reference
        ),
        "rollout_confirmation_input_renewal_lifecycle_reference": (
            rollout_confirmation_input_renewal_lifecycle_reference
        ),
        "rollout_confirmation_input_auto_claim_decision_reference": (
            rollout_confirmation_input_auto_claim_decision_reference
        ),
        "rollout_confirmation_input_missing_sections": list(
            rollout_confirmation_input_missing_sections
        ),
        "rollout_confirmation_input_sql_row_lease_is_authority": (
            rollout_confirmation_input_sql_row_lease_is_authority
        ),
        "auto_claim_policy_contract_version": auto_claim_policy_contract_version,
        "auto_claim_policy_status": auto_claim_policy_status,
        "auto_claim_missing_sections": list(auto_claim_missing_sections),
        "auto_claim_enabled_by_default": auto_claim_enabled_by_default,
        "auto_claim_descriptor_evidence_fallback": auto_claim_descriptor_evidence_fallback,
        "auto_claim_lease_validation_required": auto_claim_lease_validation_required,
        "auto_claim_entrypoint_allowlist_ready": auto_claim_entrypoint_allowlist_ready,
        "auto_claim_entrypoint_allowlist_contract_version": (
            auto_claim_entrypoint_allowlist_contract_version
        ),
        "auto_claim_entrypoint_allowlist_status": auto_claim_entrypoint_allowlist_status,
        "auto_claim_allowed_entrypoints": list(auto_claim_allowed_entrypoints),
        "auto_claim_missing_entrypoints": list(auto_claim_missing_entrypoints),
        "auto_claim_default_auto_claim_enabled": auto_claim_default_auto_claim_enabled,
        "auto_claim_requires_production_gate_ready": auto_claim_requires_production_gate_ready,
        "auto_claim_enablement_gate_contract_version": (
            auto_claim_enablement_gate_contract_version
        ),
        "auto_claim_enablement_gate_status": auto_claim_enablement_gate_status,
        "auto_claim_will_auto_claim": auto_claim_will_auto_claim,
        "auto_claim_requested_entrypoint": auto_claim_requested_entrypoint,
        "auto_claim_enablement_missing_sections": list(
            auto_claim_enablement_missing_sections
        ),
        "auto_claim_enablement_blocked_reason": auto_claim_enablement_blocked_reason,
        "ownership_audit_contract_version": ownership_audit_contract_version,
        "ownership_audit_status": ownership_audit_status,
        "ownership_audit_missing_sections": list(ownership_audit_missing_sections),
        "ownership_audit_compact_evidence": ownership_audit_compact_evidence,
        "ownership_audit_operation_history_ready": ownership_audit_operation_history_ready,
        "ownership_audit_recovery_operation_link_ready": ownership_audit_recovery_operation_link_ready,
        "ownership_audit_timeline_writer_ready": ownership_audit_timeline_writer_ready,
        "ownership_audit_idempotent_dedupe_ready": ownership_audit_idempotent_dedupe_ready,
        "ownership_audit_authorization_source": ownership_audit_authorization_source,
        "enablement_strategy_contract_version": enablement_strategy_contract_version,
        "enablement_strategy_status": enablement_strategy_status,
        "enablement_strategy_blocking_sections": list(enablement_strategy_blocking_sections),
        "production_default_enabled_requested": production_default_enabled_requested,
        "production_default_allowed": production_default_allowed,
        "enablement_input_source_contract_version": enablement_input_source_contract_version,
        "enablement_input_source_status": enablement_input_source_status,
        "enablement_input_source_kind": enablement_input_source_kind,
        "enablement_request_id": enablement_request_id,
        "enablement_requested_by": enablement_requested_by,
        "enablement_requested_at": enablement_requested_at,
        "enablement_target_store_mode": enablement_target_store_mode,
        "enablement_rollout_artifact": enablement_rollout_artifact,
        "enablement_vendor_lock_decision_id": enablement_vendor_lock_decision_id,
        "enablement_renewal_lifecycle_reference": enablement_renewal_lifecycle_reference,
        "enablement_auto_claim_decision_reference": enablement_auto_claim_decision_reference,
        "enablement_audit_evidence_reference": enablement_audit_evidence_reference,
        "enablement_rollback_plan_reference": enablement_rollback_plan_reference,
        "enablement_fallback_policy_reference": enablement_fallback_policy_reference,
        "enablement_input_source_ready": enablement_input_source_ready,
        "enablement_input_source_missing_sections": list(
            enablement_input_source_missing_sections
        ),
        "enablement_explicit_required": enablement_explicit_required,
        "enablement_all_required_sections_ready": enablement_all_required_sections_ready,
        "enablement_fail_closed_when_blocked": enablement_fail_closed_when_blocked,
        "enablement_sql_row_lease_not_default_authority": enablement_sql_row_lease_not_default_authority,
    }


def _build_recovery_retry_evidence_coverage(check: dict[str, Any]) -> dict[str, Any]:
    contract_version = str(check.get("contract_version") or "").strip()
    retry_status = str(check.get("retry_status") or "").strip()
    recovery_reason = str(check.get("recovery_reason") or "").strip()
    attempt_number = _coerce_non_negative_int(check.get("attempt_number"), 0)
    max_attempts = _coerce_non_negative_int(check.get("max_attempts"), 0)
    retryable = bool(check.get("retryable"))
    terminal = bool(check.get("terminal"))
    idempotency_key_present = bool(check.get("idempotency_key_present"))
    retry_smoke = (
        bool(check.get("ok"))
        and contract_version == "phase-ii-recovery-retry-protocol-v1"
        and attempt_number == 3
        and max_attempts == 3
        and retry_status == "exhausted"
        and terminal
        and recovery_reason == "workspace_backend_not_durable"
        and idempotency_key_present
    )
    return {
        "retry_smoke": retry_smoke,
        "contract_version": contract_version,
        "attempt_number": attempt_number,
        "max_attempts": max_attempts,
        "retry_status": retry_status,
        "retryable": retryable,
        "terminal": terminal,
        "recovery_reason": recovery_reason,
        "idempotency_key_present": idempotency_key_present,
    }


def _build_durable_recovery_loader_coverage(check: dict[str, Any]) -> dict[str, Any]:
    contract_version = str(check.get("contract_version") or "").strip()
    loader_status = str(check.get("loader_status") or "").strip()
    loader_recovery_reason = str(check.get("loader_recovery_reason") or "").strip()
    missing_recovery_reason = str(check.get("missing_recovery_reason") or "").strip()
    unsafe_recovery_reason = str(check.get("unsafe_recovery_reason") or "").strip()
    loader_ready = bool(check.get("loader_ready"))
    all_bindings_resolved = bool(check.get("all_bindings_resolved"))
    executes_recovery = bool(check.get("executes_recovery"))
    deserializes_callables = bool(check.get("deserializes_callables"))
    loader_smoke = (
        bool(check.get("ok"))
        and contract_version == "phase-ii-durable-recovery-loader-v1"
        and loader_status == "ready"
        and loader_ready
        and loader_recovery_reason == "ready_via_registry"
        and all_bindings_resolved
        and missing_recovery_reason == "run_snapshot_missing"
        and unsafe_recovery_reason == "descriptor_corrupted"
        and not executes_recovery
        and not deserializes_callables
    )
    return {
        "loader_smoke": loader_smoke,
        "contract_version": contract_version,
        "loader_status": loader_status,
        "loader_ready": loader_ready,
        "loader_recovery_reason": loader_recovery_reason,
        "all_bindings_resolved": all_bindings_resolved,
        "missing_recovery_reason": missing_recovery_reason,
        "unsafe_recovery_reason": unsafe_recovery_reason,
        "executes_recovery": executes_recovery,
        "deserializes_callables": deserializes_callables,
    }


def _build_continuation_descriptor_lifecycle_coverage(check: dict[str, Any]) -> dict[str, Any]:
    contract_version = str(check.get("descriptor_lifecycle_contract_version") or "").strip()
    states = _normalize_string_list(check.get("descriptor_lifecycle_states"))
    unsafe_keys = _normalize_string_list(check.get("descriptor_lifecycle_unsafe_keys"))
    governed = bool(check.get("descriptor_lifecycle_governed"))
    all_ready = bool(check.get("descriptor_lifecycle_all_ready"))
    lifecycle_smoke = (
        bool(check.get("ok"))
        and contract_version == "phase-ii-continuation-descriptor-lifecycle-governance-v1"
        and governed
        and all_ready
        and {"ready", "bound", "stale", "unsafe"}.issubset(set(states))
        and "handler" in unsafe_keys
        and str(check.get("unresolved_recovery_reason") or "").strip() == "missing_registered_binding"
        and str(check.get("stale_recovery_reason") or "").strip() == "denied"
        and str(check.get("unsafe_recovery_reason") or "").strip() == "descriptor_corrupted"
    )
    return {
        "lifecycle_smoke": lifecycle_smoke,
        "contract_version": contract_version,
        "governed": governed,
        "states": states,
        "all_ready": all_ready,
        "unsafe_descriptor_keys": unsafe_keys,
        "unresolved_recovery_reason": str(check.get("unresolved_recovery_reason") or "").strip(),
        "stale_recovery_reason": str(check.get("stale_recovery_reason") or "").strip(),
        "unsafe_recovery_reason": str(check.get("unsafe_recovery_reason") or "").strip(),
    }


def _build_loader_execution_handoff_coverage(check: dict[str, Any]) -> dict[str, Any]:
    contract_version = str(check.get("handoff_policy_contract_version") or "").strip()
    default_status = str(check.get("default_handoff_status") or "").strip()
    default_blocked_reason = str(check.get("default_handoff_blocked_reason") or "").strip()
    default_will_execute = bool(check.get("default_handoff_will_execute"))
    explicit_status = str(check.get("explicit_handoff_status") or "").strip()
    explicit_blocked_reason = str(check.get("explicit_handoff_blocked_reason") or "").strip()
    explicit_will_execute = bool(check.get("explicit_handoff_will_execute"))
    recovery_executor_bound = bool(check.get("recovery_executor_bound"))
    handoff_smoke = (
        bool(check.get("ok"))
        and contract_version == "phase-ii-durable-loader-execution-handoff-policy-v1"
        and default_status == "blocked"
        and default_blocked_reason == "explicit_handoff_required"
        and not default_will_execute
        and explicit_status == "blocked"
        and explicit_blocked_reason == "recovery_executor_not_bound"
        and not explicit_will_execute
        and not recovery_executor_bound
    )
    return {
        "handoff_smoke": handoff_smoke,
        "contract_version": contract_version,
        "default_status": default_status,
        "default_blocked_reason": default_blocked_reason,
        "default_will_execute": default_will_execute,
        "explicit_status": explicit_status,
        "explicit_blocked_reason": explicit_blocked_reason,
        "explicit_will_execute": explicit_will_execute,
        "recovery_executor_bound": recovery_executor_bound,
    }


def _build_recovery_retry_scheduler_coverage(check: dict[str, Any]) -> dict[str, Any]:
    contract_version = str(check.get("contract_version") or "").strip()
    default_status = str(check.get("default_status") or "").strip()
    default_eligible = bool(check.get("default_eligible"))
    default_will_execute = bool(check.get("default_will_execute"))
    production_gate_contract_version = str(check.get("production_gate_contract_version") or "").strip()
    production_gate_status = str(check.get("production_gate_status") or "").strip()
    production_gate_missing_sections = (
        check.get("production_gate_missing_sections")
        if isinstance(check.get("production_gate_missing_sections"), list)
        else []
    )
    production_gate_blocked_reason = str(check.get("production_gate_blocked_reason") or "").strip()
    production_automatic_enabled_by_default = bool(
        check.get("production_automatic_retry_enabled_by_default")
    )
    production_automatic_will_execute = bool(check.get("production_automatic_will_execute"))
    enabled_status = str(check.get("enabled_status") or "").strip()
    enabled_will_execute = bool(check.get("enabled_will_execute"))
    latest_operation_status = str(check.get("latest_operation_status") or "").strip()
    attempt_number = _coerce_non_negative_int(check.get("attempt_number"), 0)
    retry_status = str(check.get("retry_status") or "").strip()
    recovery_reason = str(check.get("recovery_reason") or "").strip()
    previous_operation_id_present = bool(check.get("previous_operation_id_present"))
    idempotency_key_present = bool(check.get("idempotency_key_present"))
    scheduler_smoke = (
        bool(check.get("ok"))
        and contract_version == "phase-ii-recovery-retry-scheduler-v1"
        and default_status == "disabled"
        and default_eligible
        and not default_will_execute
        and production_gate_contract_version == "phase-ii-recovery-retry-production-scheduler-gate-v1"
        and production_gate_status == "blocked"
        and "durable_scheduling_state" in production_gate_missing_sections
        and production_gate_blocked_reason == "production_scheduler_gate_blocked"
        and not production_automatic_enabled_by_default
        and not production_automatic_will_execute
        and enabled_status == "executed"
        and enabled_will_execute
        and latest_operation_status == "recovered"
        and attempt_number == 1
        and retry_status == "retryable"
        and recovery_reason == "transient_workspace_unavailable"
        and previous_operation_id_present
        and idempotency_key_present
    )
    return {
        "scheduler_smoke": scheduler_smoke,
        "contract_version": contract_version,
        "default_status": default_status,
        "default_eligible": default_eligible,
        "default_will_execute": default_will_execute,
        "production_gate_contract_version": production_gate_contract_version,
        "production_gate_status": production_gate_status,
        "production_gate_missing_sections": list(production_gate_missing_sections),
        "production_gate_blocked_reason": production_gate_blocked_reason,
        "production_automatic_retry_enabled_by_default": production_automatic_enabled_by_default,
        "production_automatic_will_execute": production_automatic_will_execute,
        "enabled_status": enabled_status,
        "enabled_will_execute": enabled_will_execute,
        "latest_operation_status": latest_operation_status,
        "attempt_number": attempt_number,
        "retry_status": retry_status,
        "recovery_reason": recovery_reason,
        "previous_operation_id_present": previous_operation_id_present,
        "idempotency_key_present": idempotency_key_present,
    }


def _build_child_executor_promotion_gate_coverage(check: dict[str, Any]) -> dict[str, Any]:
    contract_version = str(check.get("contract_version") or "").strip()
    gate_status = str(check.get("gate_status") or "").strip()
    failure_reason = str(check.get("gate_failure_reason") or check.get("failure_reason") or "").strip()
    recommended_next_step = str(check.get("recommended_next_step") or "").strip()
    blocker_count = _coerce_non_negative_int(check.get("blocker_count"), 0)
    allowed = bool(check.get("allowed"))
    gate_smoke = (
        bool(check.get("ok"))
        and bool(contract_version)
        and gate_status == "blocked"
        and not allowed
        and bool(failure_reason)
        and blocker_count >= 0
        and bool(recommended_next_step)
    )
    return {
        "gate_smoke": gate_smoke,
        "contract_version": contract_version,
        "gate_status": gate_status,
        "allowed": allowed,
        "failure_reason": failure_reason,
        "blocker_count": blocker_count,
        "recommended_next_step": recommended_next_step,
    }


def _build_child_executor_execution_prerequisites_coverage(check: dict[str, Any]) -> dict[str, Any]:
    contract_version = str(check.get("prerequisites_contract_version") or "").strip()
    overall_status = str(check.get("prerequisites_status") or "").strip()
    ready = bool(check.get("prerequisites_ready"))
    requirement_count = _coerce_non_negative_int(check.get("prerequisites_requirement_count"), 0)
    missing_requirement_count = _coerce_non_negative_int(
        check.get("prerequisites_missing_requirement_count"),
        0,
    )
    missing_requirements = _normalize_string_list(check.get("prerequisites_missing_requirements"))
    explicit_binding_status = str(check.get("explicit_executor_binding_status") or "").strip()
    explicit_binding_ready = bool(check.get("explicit_executor_binding_ready"))
    explicit_binding_missing = bool(check.get("explicit_executor_binding_missing"))
    context_budget_policy_status = str(check.get("context_budget_policy_status") or "").strip()
    context_budget_policy_ready = bool(check.get("context_budget_policy_ready"))
    context_budget_policy_missing = bool(check.get("context_budget_policy_missing"))
    context_budget_policy_missing_sections = _normalize_string_list(
        check.get("context_budget_policy_missing_sections")
    )
    merge_handoff_status = str(check.get("merge_handoff_status") or "").strip()
    merge_handoff_ready = bool(check.get("merge_handoff_ready"))
    merge_handoff_missing = bool(check.get("merge_handoff_missing"))
    merge_handoff_missing_sections = _normalize_string_list(
        check.get("merge_handoff_missing_sections")
    )
    opt_in_explicit_binding_status = str(
        check.get("opt_in_explicit_executor_binding_status") or ""
    ).strip()
    opt_in_explicit_binding_ready = bool(
        check.get("opt_in_explicit_executor_binding_ready")
    )
    opt_in_context_budget_policy_status = str(
        check.get("opt_in_context_budget_policy_status") or ""
    ).strip()
    opt_in_context_budget_policy_ready = bool(
        check.get("opt_in_context_budget_policy_ready")
    )
    opt_in_context_budget_policy_max_turns = _coerce_non_negative_int(
        check.get("opt_in_context_budget_policy_max_turns"),
        0,
    )
    opt_in_merge_handoff_status = str(check.get("opt_in_merge_handoff_status") or "").strip()
    opt_in_merge_handoff_ready = bool(check.get("opt_in_merge_handoff_ready"))
    opt_in_merge_handoff_strategy = str(check.get("opt_in_merge_handoff_strategy") or "").strip()
    opt_in_skeleton_execution_status = str(
        check.get("opt_in_skeleton_execution_status") or ""
    ).strip()
    opt_in_skeleton_will_execute = bool(check.get("opt_in_skeleton_will_execute"))
    prerequisites_smoke = (
        bool(check.get("ok"))
        and bool(contract_version)
        and overall_status == "blocked"
        and not ready
        and requirement_count > 0
        and missing_requirement_count == len(missing_requirements)
        and explicit_binding_missing
        and "explicit_executor_binding_opt_in" in missing_requirements
        and explicit_binding_status == "blocked"
        and not explicit_binding_ready
        and context_budget_policy_missing
        and "child_context_budget_defined" in missing_requirements
        and context_budget_policy_status == "blocked"
        and not context_budget_policy_ready
        and "budget_source" in context_budget_policy_missing_sections
        and "bounded_budget_limit" in context_budget_policy_missing_sections
        and merge_handoff_missing
        and "child_result_merge_semantics_defined" in missing_requirements
        and merge_handoff_status == "blocked"
        and not merge_handoff_ready
        and "merge_source" in merge_handoff_missing_sections
        and opt_in_explicit_binding_status == "ready"
        and opt_in_explicit_binding_ready
        and opt_in_context_budget_policy_status == "ready"
        and opt_in_context_budget_policy_ready
        and opt_in_context_budget_policy_max_turns > 0
        and opt_in_merge_handoff_status == "ready"
        and opt_in_merge_handoff_ready
        and opt_in_merge_handoff_strategy in {"append_summary", "role_sections"}
        and opt_in_skeleton_execution_status == "executed"
        and opt_in_skeleton_will_execute
    )
    return {
        "prerequisites_smoke": prerequisites_smoke,
        "contract_version": contract_version,
        "overall_status": overall_status,
        "ready": ready,
        "requirement_count": requirement_count,
        "missing_requirement_count": missing_requirement_count,
        "missing_requirements": missing_requirements,
        "explicit_executor_binding_status": explicit_binding_status,
        "explicit_executor_binding_ready": explicit_binding_ready,
        "explicit_executor_binding_missing": explicit_binding_missing,
        "context_budget_policy_status": context_budget_policy_status,
        "context_budget_policy_ready": context_budget_policy_ready,
        "context_budget_policy_missing": context_budget_policy_missing,
        "context_budget_policy_missing_sections": context_budget_policy_missing_sections,
        "context_budget_policy_source": str(check.get("context_budget_policy_source") or "").strip(),
        "merge_handoff_status": merge_handoff_status,
        "merge_handoff_ready": merge_handoff_ready,
        "merge_handoff_missing": merge_handoff_missing,
        "merge_handoff_missing_sections": merge_handoff_missing_sections,
        "merge_handoff_strategy": str(check.get("merge_handoff_strategy") or "").strip(),
        "merge_handoff_source": str(check.get("merge_handoff_source") or "").strip(),
        "opt_in_explicit_executor_binding_status": opt_in_explicit_binding_status,
        "opt_in_explicit_executor_binding_ready": opt_in_explicit_binding_ready,
        "opt_in_explicit_executor_binding_source": str(
            check.get("opt_in_explicit_executor_binding_source") or ""
        ).strip(),
        "opt_in_explicit_executor_binding_backend": str(
            check.get("opt_in_explicit_executor_binding_backend") or ""
        ).strip(),
        "opt_in_context_budget_policy_status": opt_in_context_budget_policy_status,
        "opt_in_context_budget_policy_ready": opt_in_context_budget_policy_ready,
        "opt_in_context_budget_policy_source": str(
            check.get("opt_in_context_budget_policy_source") or ""
        ).strip(),
        "opt_in_context_budget_policy_max_turns": opt_in_context_budget_policy_max_turns,
        "opt_in_merge_handoff_status": opt_in_merge_handoff_status,
        "opt_in_merge_handoff_ready": opt_in_merge_handoff_ready,
        "opt_in_merge_handoff_strategy": opt_in_merge_handoff_strategy,
        "opt_in_merge_handoff_source": str(check.get("opt_in_merge_handoff_source") or "").strip(),
        "opt_in_skeleton_execution_status": opt_in_skeleton_execution_status,
        "opt_in_skeleton_will_execute": opt_in_skeleton_will_execute,
        "opt_in_skeleton_execution_mode": str(
            check.get("opt_in_skeleton_execution_mode") or ""
        ).strip(),
    }


def _build_child_executor_dispatch_coverage(check: dict[str, Any]) -> dict[str, Any]:
    contract_version = str(check.get("contract_version") or "").strip()
    overall_status = str(check.get("dispatch_status") or "").strip()
    dispatch_ready = bool(check.get("dispatch_ready"))
    will_dispatch = bool(check.get("will_dispatch"))
    backend_dispatch_ready = bool(check.get("backend_dispatch_ready"))
    relationship_seam_preserved = bool(check.get("relationship_seam_preserved"))
    blocker_count = _coerce_non_negative_int(check.get("dispatch_blocker_count"), 0)
    dispatch_blockers = _normalize_string_list(check.get("dispatch_blockers"))
    explicit_binding_ready = bool(check.get("explicit_executor_binding_ready"))
    explicit_binding_status = str(check.get("explicit_executor_binding_status") or "").strip()
    opt_in_dispatch_status = str(check.get("opt_in_dispatch_status") or "").strip()
    opt_in_dispatch_ready = bool(check.get("opt_in_dispatch_ready"))
    opt_in_will_dispatch = bool(check.get("opt_in_will_dispatch"))
    opt_in_backend_dispatch_ready = bool(check.get("opt_in_backend_dispatch_ready"))
    opt_in_explicit_binding_ready = bool(
        check.get("opt_in_explicit_executor_binding_ready")
    )
    opt_in_explicit_binding_status = str(
        check.get("opt_in_explicit_executor_binding_status") or ""
    ).strip()
    dispatch_attempt_handoff_status = str(
        check.get("dispatch_attempt_handoff_status") or ""
    ).strip()
    dispatch_attempt_handoff_ready = bool(check.get("dispatch_attempt_handoff_ready"))
    dispatch_attempt_handoff_missing_sections = _normalize_string_list(
        check.get("dispatch_attempt_handoff_missing_sections")
    )
    dispatch_attempt_handoff_will_dispatch = bool(
        check.get("dispatch_attempt_handoff_will_dispatch")
    )
    opt_in_dispatch_attempt_handoff_status = str(
        check.get("opt_in_dispatch_attempt_handoff_status") or ""
    ).strip()
    opt_in_dispatch_attempt_handoff_ready = bool(
        check.get("opt_in_dispatch_attempt_handoff_ready")
    )
    opt_in_attempt_envelope_supported = bool(
        check.get("opt_in_attempt_envelope_supported")
    )
    opt_in_attempt_validation_ready = bool(check.get("opt_in_attempt_validation_ready"))
    opt_in_attempt_will_dispatch = bool(check.get("opt_in_attempt_will_dispatch"))
    opt_in_unsafe_payload_guard_ready = bool(check.get("opt_in_unsafe_payload_guard_ready"))
    unsafe_payload_guard_status = str(check.get("unsafe_payload_guard_status") or "").strip()
    unsafe_payload_guard_ready = bool(check.get("unsafe_payload_guard_ready"))
    unsafe_payload_keys = _normalize_string_list(check.get("unsafe_payload_keys"))
    recommended_next_step = str(check.get("recommended_next_step") or "").strip()
    dispatch_smoke = (
        bool(check.get("ok"))
        and bool(contract_version)
        and overall_status == "blocked"
        and not dispatch_ready
        and not will_dispatch
        and not backend_dispatch_ready
        and relationship_seam_preserved
        and blocker_count > 0
        and "explicit_executor_binding_opt_in" in dispatch_blockers
        and explicit_binding_status == "blocked"
        and not explicit_binding_ready
        and opt_in_dispatch_status == "blocked"
        and not opt_in_dispatch_ready
        and not opt_in_will_dispatch
        and not opt_in_backend_dispatch_ready
        and opt_in_explicit_binding_ready
        and opt_in_explicit_binding_status == "ready"
        and dispatch_attempt_handoff_status == "blocked"
        and not dispatch_attempt_handoff_ready
        and "dispatch_contract_ready" in dispatch_attempt_handoff_missing_sections
        and not dispatch_attempt_handoff_will_dispatch
        and opt_in_dispatch_attempt_handoff_status == "ready"
        and opt_in_dispatch_attempt_handoff_ready
        and opt_in_attempt_envelope_supported
        and opt_in_attempt_validation_ready
        and not opt_in_attempt_will_dispatch
        and opt_in_unsafe_payload_guard_ready
        and unsafe_payload_guard_status == "blocked"
        and not unsafe_payload_guard_ready
        and "handler" in unsafe_payload_keys
        and bool(recommended_next_step)
    )
    return {
        "dispatch_smoke": dispatch_smoke,
        "contract_version": contract_version,
        "overall_status": overall_status,
        "dispatch_ready": dispatch_ready,
        "will_dispatch": will_dispatch,
        "backend_dispatch_ready": backend_dispatch_ready,
        "relationship_seam_preserved": relationship_seam_preserved,
        "blocker_count": blocker_count,
        "dispatch_blockers": dispatch_blockers,
        "explicit_executor_binding_ready": explicit_binding_ready,
        "explicit_executor_binding_status": explicit_binding_status,
        "explicit_executor_binding_source": str(
            check.get("explicit_executor_binding_source") or ""
        ).strip(),
        "opt_in_dispatch_status": opt_in_dispatch_status,
        "opt_in_dispatch_ready": opt_in_dispatch_ready,
        "opt_in_will_dispatch": opt_in_will_dispatch,
        "opt_in_backend_dispatch_ready": opt_in_backend_dispatch_ready,
        "opt_in_explicit_executor_binding_ready": opt_in_explicit_binding_ready,
        "opt_in_explicit_executor_binding_status": opt_in_explicit_binding_status,
        "opt_in_explicit_executor_binding_source": str(
            check.get("opt_in_explicit_executor_binding_source") or ""
        ).strip(),
        "dispatch_attempt_handoff_status": dispatch_attempt_handoff_status,
        "dispatch_attempt_handoff_ready": dispatch_attempt_handoff_ready,
        "dispatch_attempt_handoff_missing_sections": dispatch_attempt_handoff_missing_sections,
        "dispatch_attempt_handoff_will_dispatch": dispatch_attempt_handoff_will_dispatch,
        "opt_in_dispatch_attempt_handoff_status": opt_in_dispatch_attempt_handoff_status,
        "opt_in_dispatch_attempt_handoff_ready": opt_in_dispatch_attempt_handoff_ready,
        "opt_in_attempt_envelope_supported": opt_in_attempt_envelope_supported,
        "opt_in_attempt_validation_ready": opt_in_attempt_validation_ready,
        "opt_in_attempt_will_dispatch": opt_in_attempt_will_dispatch,
        "opt_in_unsafe_payload_guard_ready": opt_in_unsafe_payload_guard_ready,
        "unsafe_payload_guard_status": unsafe_payload_guard_status,
        "unsafe_payload_guard_ready": unsafe_payload_guard_ready,
        "unsafe_payload_keys": unsafe_payload_keys,
        "recommended_next_step": recommended_next_step,
    }


def _build_child_executor_dispatcher_coverage(check: dict[str, Any]) -> dict[str, Any]:
    contract_version = str(check.get("contract_version") or "").strip()
    default_status = str(check.get("default_status") or "").strip()
    default_blocked_reason = str(check.get("default_blocked_reason") or "").strip()
    default_will_dispatch = bool(check.get("default_will_dispatch"))
    blocked_reason = str(check.get("blocked_reason") or "").strip()
    blocked_will_dispatch = bool(check.get("blocked_will_dispatch"))
    enabled_status = str(check.get("enabled_status") or "").strip()
    enabled_will_dispatch = bool(check.get("enabled_will_dispatch"))
    backend_result_status = str(check.get("backend_result_status") or "").strip()
    backend_invocation_count = _coerce_non_negative_int(check.get("backend_invocation_count"), 0)
    dispatcher_smoke = (
        bool(check.get("ok"))
        and contract_version == "phase-ii-child-executor-dispatcher-v1"
        and default_status == "blocked"
        and default_blocked_reason == "dispatcher_disabled"
        and not default_will_dispatch
        and blocked_reason == "dispatch_contract_not_ready"
        and not blocked_will_dispatch
        and enabled_status == "dispatched"
        and enabled_will_dispatch
        and backend_result_status == "completed"
        and backend_invocation_count == 1
    )
    return {
        "dispatcher_smoke": dispatcher_smoke,
        "contract_version": contract_version,
        "default_status": default_status,
        "default_blocked_reason": default_blocked_reason,
        "default_will_dispatch": default_will_dispatch,
        "blocked_reason": blocked_reason,
        "blocked_will_dispatch": blocked_will_dispatch,
        "enabled_status": enabled_status,
        "enabled_will_dispatch": enabled_will_dispatch,
        "backend_result_status": backend_result_status,
        "backend_invocation_count": backend_invocation_count,
    }


def _build_child_executor_dispatch_result_handoff_coverage(check: dict[str, Any]) -> dict[str, Any]:
    contract_version = str(check.get("contract_version") or "").strip()
    ready_handoff_status = str(check.get("ready_handoff_status") or "").strip()
    ready_handoff_ready = bool(check.get("ready_handoff_ready"))
    ready_output_ref_present = bool(check.get("ready_output_ref_present"))
    ready_audit_evidence_present = bool(check.get("ready_audit_evidence_present"))
    ready_backend_result_schema_valid = bool(check.get("ready_backend_result_schema_valid"))
    ready_parent_merge_performed = bool(check.get("ready_parent_merge_performed"))
    ready_merge_authorization = bool(check.get("ready_merge_authorization"))
    ready_retry_scheduled = bool(check.get("ready_retry_scheduled"))
    ready_production_dispatch_authorized = bool(
        check.get("ready_production_dispatch_authorized")
    )
    blocked_handoff_status = str(check.get("blocked_handoff_status") or "").strip()
    blocked_dispatcher_reason = str(check.get("blocked_dispatcher_reason") or "").strip()
    blocked_missing_sections = _normalize_string_list(check.get("blocked_missing_sections"))
    malformed_handoff_status = str(check.get("malformed_handoff_status") or "").strip()
    malformed_missing_sections = _normalize_string_list(
        check.get("malformed_missing_sections")
    )
    result_handoff_smoke = (
        bool(check.get("ok"))
        and contract_version == "phase-ii-child-executor-dispatch-result-handoff-v1"
        and ready_handoff_status == "ready"
        and ready_handoff_ready
        and ready_output_ref_present
        and ready_audit_evidence_present
        and ready_backend_result_schema_valid
        and not ready_parent_merge_performed
        and not ready_merge_authorization
        and not ready_retry_scheduled
        and not ready_production_dispatch_authorized
        and blocked_handoff_status == "blocked"
        and blocked_dispatcher_reason == "dispatcher_disabled"
        and "dispatch_success" in blocked_missing_sections
        and malformed_handoff_status == "blocked"
        and "output_ref" in malformed_missing_sections
        and "audit_evidence" in malformed_missing_sections
    )
    return {
        "result_handoff_smoke": result_handoff_smoke,
        "contract_version": contract_version,
        "ready_handoff_status": ready_handoff_status,
        "ready_handoff_ready": ready_handoff_ready,
        "ready_output_ref_present": ready_output_ref_present,
        "ready_audit_evidence_present": ready_audit_evidence_present,
        "ready_backend_result_schema_valid": ready_backend_result_schema_valid,
        "ready_parent_merge_performed": ready_parent_merge_performed,
        "ready_merge_authorization": ready_merge_authorization,
        "ready_retry_scheduled": ready_retry_scheduled,
        "ready_production_dispatch_authorized": ready_production_dispatch_authorized,
        "blocked_handoff_status": blocked_handoff_status,
        "blocked_dispatcher_reason": blocked_dispatcher_reason,
        "blocked_missing_sections": blocked_missing_sections,
        "malformed_handoff_status": malformed_handoff_status,
        "malformed_missing_sections": malformed_missing_sections,
    }


def _build_child_executor_dispatch_result_retry_audit_coverage(check: dict[str, Any]) -> dict[str, Any]:
    contract_version = str(check.get("contract_version") or "").strip()
    success_policy_status = str(check.get("success_policy_status") or "").strip()
    success_retry_policy_status = str(check.get("success_retry_policy_status") or "").strip()
    success_retry_scheduled = bool(check.get("success_retry_scheduled"))
    success_will_retry = bool(check.get("success_will_retry"))
    retryable_policy_status = str(check.get("retryable_policy_status") or "").strip()
    retryable_retry_policy_status = str(check.get("retryable_retry_policy_status") or "").strip()
    retryable_audit_evidence_present = bool(check.get("retryable_audit_evidence_present"))
    retryable_idempotency_evidence_present = bool(
        check.get("retryable_idempotency_evidence_present")
    )
    retryable_scheduler_required = bool(check.get("retryable_scheduler_required"))
    retryable_retry_reason = str(check.get("retryable_retry_reason") or "").strip()
    retryable_retry_scheduled = bool(check.get("retryable_retry_scheduled"))
    retryable_will_retry = bool(check.get("retryable_will_retry"))
    terminal_policy_status = str(check.get("terminal_policy_status") or "").strip()
    terminal_retry_policy_status = str(check.get("terminal_retry_policy_status") or "").strip()
    terminal_reason = str(check.get("terminal_reason") or "").strip()
    terminal_will_retry = bool(check.get("terminal_will_retry"))
    missing_idempotency_status = str(check.get("missing_idempotency_status") or "").strip()
    missing_idempotency_missing_sections = _normalize_string_list(
        check.get("missing_idempotency_missing_sections")
    )
    missing_idempotency_retry_scheduled = bool(
        check.get("missing_idempotency_retry_scheduled")
    )
    retry_audit_smoke = (
        bool(check.get("ok"))
        and contract_version
        == "phase-ii-child-executor-dispatch-result-retry-audit-policy-v1"
        and success_policy_status == "ready"
        and success_retry_policy_status == "not_required"
        and not success_retry_scheduled
        and not success_will_retry
        and retryable_policy_status == "ready"
        and retryable_retry_policy_status == "retryable"
        and retryable_audit_evidence_present
        and retryable_idempotency_evidence_present
        and retryable_scheduler_required
        and retryable_retry_reason == "sandbox_timeout"
        and not retryable_retry_scheduled
        and not retryable_will_retry
        and terminal_policy_status == "ready"
        and terminal_retry_policy_status == "terminal"
        and terminal_reason == "sandbox_payload_unsafe"
        and not terminal_will_retry
        and missing_idempotency_status == "blocked"
        and "idempotency_evidence" in missing_idempotency_missing_sections
        and not missing_idempotency_retry_scheduled
    )
    return {
        "retry_audit_smoke": retry_audit_smoke,
        "contract_version": contract_version,
        "success_policy_status": success_policy_status,
        "success_retry_policy_status": success_retry_policy_status,
        "success_retry_scheduled": success_retry_scheduled,
        "success_will_retry": success_will_retry,
        "retryable_policy_status": retryable_policy_status,
        "retryable_retry_policy_status": retryable_retry_policy_status,
        "retryable_audit_evidence_present": retryable_audit_evidence_present,
        "retryable_idempotency_evidence_present": retryable_idempotency_evidence_present,
        "retryable_scheduler_required": retryable_scheduler_required,
        "retryable_retry_reason": retryable_retry_reason,
        "retryable_retry_scheduled": retryable_retry_scheduled,
        "retryable_will_retry": retryable_will_retry,
        "terminal_policy_status": terminal_policy_status,
        "terminal_retry_policy_status": terminal_retry_policy_status,
        "terminal_reason": terminal_reason,
        "terminal_will_retry": terminal_will_retry,
        "missing_idempotency_status": missing_idempotency_status,
        "missing_idempotency_missing_sections": missing_idempotency_missing_sections,
        "missing_idempotency_retry_scheduled": missing_idempotency_retry_scheduled,
    }


def _build_child_executor_sandbox_backend_coverage(check: dict[str, Any]) -> dict[str, Any]:
    contract_version = str(check.get("contract_version") or "").strip()
    ready_adapter_contract = bool(check.get("ready_adapter_contract"))
    ready_sandbox_guard = bool(check.get("ready_sandbox_guard"))
    ready_audit = bool(check.get("ready_audit"))
    ready_idempotency = bool(check.get("ready_idempotency"))
    missing_guard_fail_closed = bool(check.get("missing_guard_fail_closed"))
    missing_guard_count = _coerce_non_negative_int(check.get("missing_guard_count"), 0)
    unsafe_payload_blocked = bool(check.get("unsafe_payload_blocked"))
    unsafe_blocked_reason = str(check.get("unsafe_blocked_reason") or "").strip()
    compact_attempt_valid = bool(check.get("compact_attempt_valid"))
    dispatch_status = str(check.get("dispatch_status") or "").strip()
    backend_result_status = str(check.get("backend_result_status") or "").strip()
    backend_invocation_count = _coerce_non_negative_int(check.get("backend_invocation_count"), 0)
    default_worker_enabled = bool(check.get("default_worker_enabled"))
    sandbox_backend_smoke = (
        bool(check.get("ok"))
        and contract_version == "phase-ii-child-executor-sandbox-worker-backend-v1"
        and ready_adapter_contract
        and ready_sandbox_guard
        and ready_audit
        and ready_idempotency
        and missing_guard_fail_closed
        and missing_guard_count > 0
        and unsafe_payload_blocked
        and unsafe_blocked_reason == "sandbox_payload_unsafe"
        and compact_attempt_valid
        and dispatch_status == "dispatched"
        and backend_result_status == "completed"
        and backend_invocation_count == 1
        and not default_worker_enabled
    )
    return {
        "sandbox_backend_smoke": sandbox_backend_smoke,
        "contract_version": contract_version,
        "ready_adapter_contract": ready_adapter_contract,
        "ready_sandbox_guard": ready_sandbox_guard,
        "ready_audit": ready_audit,
        "ready_idempotency": ready_idempotency,
        "missing_guard_fail_closed": missing_guard_fail_closed,
        "missing_guard_count": missing_guard_count,
        "unsafe_payload_blocked": unsafe_payload_blocked,
        "unsafe_blocked_reason": unsafe_blocked_reason,
        "compact_attempt_valid": compact_attempt_valid,
        "dispatch_status": dispatch_status,
        "backend_result_status": backend_result_status,
        "backend_invocation_count": backend_invocation_count,
        "default_worker_enabled": default_worker_enabled,
    }


def _normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item or "").strip()]


def _build_steps(args: argparse.Namespace) -> list[GateStep]:
    python = sys.executable
    if os.name == "nt":
        return [
            GateStep(
                "Quality gate smoke",
                [
                    "cmd",
                    "/c",
                    "powershell",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    "backend/scripts/quality_gate_smoke.ps1",
                    "-CondaEnv",
                    "myenv",
                ],
            )
        ]
    return [
        GateStep("Backend smoke_check.py", [python, "backend/scripts/smoke_check.py"]),
        GateStep("Backend auth_session_smoke.py", [python, "backend/scripts/auth_session_smoke.py"]),
        GateStep("Backend multi_agent_policy_smoke.py", [python, "backend/scripts/multi_agent_policy_smoke.py"]),
        GateStep("Backend multi_agent_provider_failover_smoke.py", [python, "backend/scripts/multi_agent_provider_failover_smoke.py"]),
        GateStep("Backend runtime_contract_smoke.py", [python, "backend/scripts/runtime_contract_smoke.py"]),
        GateStep(
            "Backend governance regression tests",
            [
                python,
                "-m",
                "unittest",
                "tests.agent_framework.test_doctor_script",
                "tests.agent_framework.test_health_router",
                "tests.agent_framework.test_runtime_contract_smoke",
                "tests.agent_framework.test_runtime_surface_config_service",
            ],
        ),
        GateStep(
            "Backend capability-gap governance smoke",
            [
                python,
                "backend/scripts/capability_gap_governance_smoke.py",
                "--window-days",
                str(args.window_days),
                "--limit",
                str(args.limit),
                "--max-open-actions",
                str(args.max_open_actions),
                "--max-long-blocked-actions",
                str(args.max_long_blocked_actions),
            ],
        ),
        GateStep(
            "Frontend health-alert smoke",
            [
                "npm",
                "test",
                "--",
                "--run",
                "src/components/__tests__/ChatView.test.js",
                "src/components/__tests__/SettingsView.test.js",
            ],
            cwd=ROOT_DIR / "frontend-vue",
        ),
    ]


def _render_summary(report: dict[str, Any]) -> str:
    steps = _normalize_report_steps(report.get("steps") or [])
    failed_steps = _normalize_failed_steps(report, steps)
    step_count = report.get("step_count", len(steps))
    lines = [
        "# Quality Gate Report",
        "",
        f"- Status: {'PASS' if _coerce_passed_flag(report.get('passed')) else 'FAIL'}",
        f"- Steps: {step_count}",
        f"- Failed: {len(failed_steps)}",
        "",
        "| Step | Status | Exit | Seconds |",
        "| --- | --- | ---: | ---: |",
    ]
    for step in steps:
        status = "PASS" if _coerce_passed_flag(step.get("passed")) else "FAIL"
        lines.append(
            f"| {_format_markdown_table_cell(step.get('name', ''))} | {status} | "
            f"{_format_markdown_table_cell(step.get('exit_code', ''))} | "
            f"{_format_markdown_table_cell(step.get('duration_seconds', ''))} |"
        )
    if failed_steps:
        lines.append("")
        lines.append("## Failed Steps")
        for step in failed_steps:
            name = _format_markdown_list_text(step.get("name", ""))
            if name:
                lines.append(f"- {name}")
    contract_check_rows = [
        (step, check)
        for step in steps
        for check in _normalize_contract_checks(step.get("contract_checks") or [])
    ]
    if contract_check_rows:
        lines.extend([
            "",
            "## Runtime Contract Checks",
            "",
            "| Step | Check | Status | Reason |",
            "| --- | --- | --- | --- |",
        ])
        for step, check in contract_check_rows:
            status = "PASS" if check.get("ok") else "FAIL"
            lines.append(
                f"| {_format_markdown_table_cell(step.get('name', ''))} | "
                f"{_format_markdown_table_cell(check.get('name', ''))} | {status} | "
                f"{_format_markdown_table_cell(check.get('failure_reason', ''))} |"
            )
    summary_rows = [
        (step, step.get("runtime_contract_summary") or {})
        for step in steps
        if isinstance(step.get("runtime_contract_summary"), dict)
    ]
    if summary_rows:
        lines.extend([
            "",
            "## Runtime Contract Summary",
            "",
            "| Step | Status | Checks | Failed | Missing Payloads | Approval Replay Coverage | Approval Lifecycle Recovery | Approved Tool Bridge | SDK Tool Bridge | Checkpoint Cursor | Worker Ownership Mode | Recovery Audit | Registry/Checkpoint Policy | Recovery Retry | Retry Scheduler | Durable Loader | Descriptor Lifecycle | Loader Handoff | Child Executor Gate | Child Executor Dispatch | Child Executor Dispatcher | Child Result Handoff | Child Retry Audit | Subagent Lane Detail |",
            "| --- | --- | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ])
        for step, runtime_summary in summary_rows:
            approval_coverage = runtime_summary.get("approval_replay_coverage") or {}
            if not isinstance(approval_coverage, dict):
                approval_coverage = {}
            coverage_label = "yes" if _coerce_truthy_flag(approval_coverage.get("event_payload_sample")) else "no"
            lifecycle_coverage = runtime_summary.get("approval_lifecycle_recovery_coverage") or {}
            if not isinstance(lifecycle_coverage, dict):
                lifecycle_coverage = {}
            lifecycle_label = "yes" if _is_approval_lifecycle_recovery_coverage_aligned(lifecycle_coverage) else "no"
            approved_tool_coverage = runtime_summary.get("approved_tool_execution_coverage") or {}
            if not isinstance(approved_tool_coverage, dict):
                approved_tool_coverage = {}
            approved_tool_label = "yes" if _coerce_truthy_flag(approved_tool_coverage.get("bridge_smoke")) else "no"
            sdk_tool_coverage = runtime_summary.get("sdk_tool_runtime_execution_coverage") or {}
            if not isinstance(sdk_tool_coverage, dict):
                sdk_tool_coverage = {}
            sdk_tool_label = "yes" if _coerce_truthy_flag(sdk_tool_coverage.get("bridge_smoke")) else "no"
            checkpoint_cursor_coverage = runtime_summary.get("checkpoint_resume_cursor_coverage") or {}
            if not isinstance(checkpoint_cursor_coverage, dict):
                checkpoint_cursor_coverage = {}
            checkpoint_cursor_label = "yes" if _is_checkpoint_resume_cursor_coverage_aligned(checkpoint_cursor_coverage) else "no"
            worker_ownership_coverage = runtime_summary.get("worker_ownership_store_mode_coverage") or {}
            if not isinstance(worker_ownership_coverage, dict):
                worker_ownership_coverage = {}
            worker_ownership_label = "yes" if _is_worker_ownership_store_mode_coverage_aligned(worker_ownership_coverage) else "no"
            recovery_audit_coverage = runtime_summary.get("recovery_audit_operation_history_coverage") or {}
            if not isinstance(recovery_audit_coverage, dict):
                recovery_audit_coverage = {}
            recovery_audit_label = "yes" if _is_recovery_audit_operation_history_coverage_aligned(recovery_audit_coverage) else "no"
            registry_checkpoint_coverage = (
                runtime_summary.get("production_recovery_registry_checkpoint_policy_coverage") or {}
            )
            if not isinstance(registry_checkpoint_coverage, dict):
                registry_checkpoint_coverage = {}
            registry_checkpoint_label = (
                "yes"
                if _is_production_recovery_registry_checkpoint_policy_coverage_aligned(
                    registry_checkpoint_coverage
                )
                else "no"
            )
            recovery_retry_coverage = runtime_summary.get("recovery_retry_evidence_coverage") or {}
            if not isinstance(recovery_retry_coverage, dict):
                recovery_retry_coverage = {}
            recovery_retry_label = "yes" if _is_recovery_retry_evidence_coverage_aligned(recovery_retry_coverage) else "no"
            retry_scheduler_coverage = runtime_summary.get("recovery_retry_scheduler_coverage") or {}
            if not isinstance(retry_scheduler_coverage, dict):
                retry_scheduler_coverage = {}
            retry_scheduler_label = "yes" if _is_recovery_retry_scheduler_coverage_aligned(retry_scheduler_coverage) else "no"
            durable_loader_coverage = runtime_summary.get("durable_recovery_loader_coverage") or {}
            if not isinstance(durable_loader_coverage, dict):
                durable_loader_coverage = {}
            durable_loader_label = "yes" if _is_durable_recovery_loader_coverage_aligned(durable_loader_coverage) else "no"
            lifecycle_coverage = runtime_summary.get("continuation_descriptor_lifecycle_coverage") or {}
            if not isinstance(lifecycle_coverage, dict):
                lifecycle_coverage = {}
            lifecycle_descriptor_label = "yes" if _is_continuation_descriptor_lifecycle_coverage_aligned(lifecycle_coverage) else "no"
            handoff_coverage = runtime_summary.get("loader_execution_handoff_coverage") or {}
            if not isinstance(handoff_coverage, dict):
                handoff_coverage = {}
            handoff_label = "yes" if _is_loader_execution_handoff_coverage_aligned(handoff_coverage) else "no"
            child_executor_gate_coverage = runtime_summary.get("child_executor_promotion_gate_coverage") or {}
            if not isinstance(child_executor_gate_coverage, dict):
                child_executor_gate_coverage = {}
            child_executor_gate_label = "yes" if _is_child_executor_promotion_gate_coverage_aligned(child_executor_gate_coverage) else "no"
            child_executor_dispatch_coverage = runtime_summary.get("child_executor_dispatch_coverage") or {}
            if not isinstance(child_executor_dispatch_coverage, dict):
                child_executor_dispatch_coverage = {}
            child_executor_dispatch_label = "yes" if _coerce_truthy_flag(child_executor_dispatch_coverage.get("dispatch_smoke")) else "no"
            child_executor_dispatcher_coverage = runtime_summary.get("child_executor_dispatcher_coverage") or {}
            if not isinstance(child_executor_dispatcher_coverage, dict):
                child_executor_dispatcher_coverage = {}
            child_executor_dispatcher_label = "yes" if _is_child_executor_dispatcher_coverage_aligned(child_executor_dispatcher_coverage) else "no"
            child_executor_result_handoff_coverage = runtime_summary.get("child_executor_dispatch_result_handoff_coverage") or {}
            if not isinstance(child_executor_result_handoff_coverage, dict):
                child_executor_result_handoff_coverage = {}
            child_executor_result_handoff_label = "yes" if _is_child_executor_dispatch_result_handoff_coverage_aligned(child_executor_result_handoff_coverage) else "no"
            child_executor_retry_audit_coverage = runtime_summary.get("child_executor_dispatch_result_retry_audit_coverage") or {}
            if not isinstance(child_executor_retry_audit_coverage, dict):
                child_executor_retry_audit_coverage = {}
            child_executor_retry_audit_label = "yes" if _is_child_executor_dispatch_result_retry_audit_coverage_aligned(child_executor_retry_audit_coverage) else "no"
            subagent_detail_coverage = runtime_summary.get("subagent_lane_query_detail_coverage") or {}
            if not isinstance(subagent_detail_coverage, dict):
                subagent_detail_coverage = {}
            subagent_detail_label = "yes" if _coerce_truthy_flag(subagent_detail_coverage.get("detail_smoke")) else "no"
            lines.append(
                f"| {_format_markdown_table_cell(step.get('name', ''))} | "
                f"{_format_markdown_table_cell(runtime_summary.get('overall_status', ''))} | "
                f"{_format_markdown_table_cell(runtime_summary.get('check_count', 0))} | "
                f"{_format_markdown_table_cell(runtime_summary.get('failed_check_count', 0))} | "
                f"{_format_markdown_table_cell(runtime_summary.get('missing_payload_count', 0))} | "
                f"{coverage_label} | {lifecycle_label} | {approved_tool_label} | {sdk_tool_label} | {checkpoint_cursor_label} | {worker_ownership_label} | {recovery_audit_label} | {registry_checkpoint_label} | {recovery_retry_label} | {retry_scheduler_label} | {durable_loader_label} | {lifecycle_descriptor_label} | {handoff_label} | {child_executor_gate_label} | {child_executor_dispatch_label} | {child_executor_dispatcher_label} | {child_executor_result_handoff_label} | {child_executor_retry_audit_label} | {subagent_detail_label} |"
            )
    schema_rows = [
        (step, step.get("runtime_contract_artifact_schema") or {})
        for step in steps
        if isinstance(step.get("runtime_contract_artifact_schema"), dict)
    ]
    if schema_rows:
        lines.extend([
            "",
            "## Runtime Contract Artifact Schema",
            "",
            "| Step | Status | Missing Summary Fields |",
            "| --- | --- | --- |",
        ])
        for step, artifact_schema in schema_rows:
            missing_fields = artifact_schema.get("summary_missing_fields")
            missing_label = ", ".join(str(item) for item in missing_fields) if isinstance(missing_fields, list) else ""
            lines.append(
                f"| {_format_markdown_table_cell(step.get('name', ''))} | "
                f"{_format_markdown_table_cell(artifact_schema.get('overall_status', ''))} | "
                f"{_format_markdown_table_cell(missing_label)} |"
            )
    return "\n".join(lines) + "\n"


def _format_markdown_table_cell(value: Any) -> str:
    return _format_markdown_list_text(value).replace("|", "\\|")


def _format_markdown_list_text(value: Any) -> str:
    return " ".join(str("" if value is None else value).split())


def _normalize_report_steps(steps: Any) -> list[dict[str, Any]]:
    if not isinstance(steps, list):
        return []
    return [dict(step) for step in steps if isinstance(step, dict)]


def _normalize_failed_steps(report: dict[str, Any], steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if "failed_steps" in report:
        return _normalize_report_steps(report.get("failed_steps") or [])
    return [step for step in steps if not _coerce_passed_flag(step.get("passed"))]


def _coerce_passed_flag(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "pass", "passed", "ok", "yes"}
    return False


def _coerce_truthy_flag(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "ok", "yes"}
    return False


def _is_approval_lifecycle_recovery_coverage_aligned(coverage: dict[str, Any]) -> bool:
    return (
        _coerce_truthy_flag(coverage.get("alignment_smoke"))
        and str(coverage.get("replayed_submission_status") or "").strip() == "replayed"
        and str(coverage.get("ignored_submission_status") or "").strip() == "ignored"
        and str(coverage.get("resolved_recovery_reason") or "").strip() == "already_resolved"
    )


def _is_checkpoint_resume_cursor_coverage_aligned(coverage: dict[str, Any]) -> bool:
    return (
        _coerce_truthy_flag(coverage.get("cursor_smoke"))
        and str(coverage.get("checkpoint_status") or "").strip() == "ready"
        and str(coverage.get("checkpoint_kind") or "").strip() == "approval_waiting"
        and str(coverage.get("cursor_status") or "").strip() == "ready"
        and str(coverage.get("cursor_entrypoint") or "").strip() == "submit_approval.approved"
        and str(coverage.get("cursor_recovery_reason") or "").strip() == "ready_via_registry"
    )


def _is_worker_ownership_store_mode_coverage_aligned(coverage: dict[str, Any]) -> bool:
    return (
        _coerce_truthy_flag(coverage.get("mode_smoke"))
        and str(coverage.get("default_mode") or "").strip() == "memory_only"
        and str(coverage.get("default_mode_source") or "").strip() == "default"
        and str(coverage.get("default_adapter_kind") or "").strip() == "in_memory"
        and not _coerce_truthy_flag(coverage.get("default_durable"))
        and _coerce_truthy_flag(coverage.get("configurable_knob_present"))
        and _coerce_truthy_flag(coverage.get("hot_reloadable_knob_present"))
        and str(coverage.get("strict_mode_status") or "").strip() == "sqlalchemy_durable"
        and str(coverage.get("fallback_mode_status") or "").strip() == "fallback_to_memory"
        and str(coverage.get("production_gate_contract_version") or "").strip()
        == "phase-ii-worker-ownership-production-gate-v1"
        and str(coverage.get("production_gate_status") or "").strip() == "blocked"
        and "vendor_lock_semantics" in (coverage.get("production_gate_missing_sections") or [])
        and "heartbeat_renewal_supervisor" in (coverage.get("production_gate_missing_sections") or [])
        and "ownership_audit_evidence" in (coverage.get("production_gate_missing_sections") or [])
        and not _coerce_truthy_flag(coverage.get("production_default_enabled"))
        and str(coverage.get("vendor_lock_contract_version") or "").strip()
        == "phase-ii-worker-ownership-vendor-lock-semantics-v1"
        and str(coverage.get("vendor_lock_status") or "").strip() == "blocked"
        and str(coverage.get("vendor_lock_current_posture") or "").strip() == "sql_row_lease_fencing"
        and "vendor_lock_adapter" in (coverage.get("vendor_lock_missing_sections") or [])
        and "target_decision" in (coverage.get("vendor_lock_missing_sections") or [])
        and _coerce_truthy_flag(coverage.get("vendor_lock_sql_row_lease_fencing"))
        and not _coerce_truthy_flag(coverage.get("vendor_lock_sql_row_lease_is_vendor_lock"))
        and not _coerce_truthy_flag(coverage.get("vendor_lock_adapter_present"))
        and str(coverage.get("vendor_lock_adapter_contract_version") or "").strip()
        == "phase-ii-worker-ownership-vendor-lock-adapter-v1"
        and str(coverage.get("vendor_lock_adapter_status") or "").strip() == "blocked"
        and str(coverage.get("vendor_lock_adapter_kind") or "").strip() == ""
        and str(coverage.get("vendor_lock_adapter_target_backend") or "").strip() == ""
        and str(coverage.get("vendor_lock_adapter_scope") or "").strip() == ""
        and str(coverage.get("vendor_lock_adapter_fencing_strategy") or "").strip() == ""
        and str(coverage.get("vendor_lock_adapter_ttl_renewal_strategy") or "").strip() == ""
        and str(coverage.get("vendor_lock_adapter_failover_strategy") or "").strip() == ""
        and str(coverage.get("vendor_lock_adapter_stale_cleanup_strategy") or "").strip() == ""
        and not _coerce_truthy_flag(coverage.get("vendor_lock_adapter_acquire_supported"))
        and not _coerce_truthy_flag(coverage.get("vendor_lock_adapter_renew_supported"))
        and not _coerce_truthy_flag(coverage.get("vendor_lock_adapter_release_supported"))
        and not _coerce_truthy_flag(coverage.get("vendor_lock_adapter_probe_supported"))
        and not _coerce_truthy_flag(coverage.get("vendor_lock_adapter_production_allowed"))
        and not _coerce_truthy_flag(
            coverage.get("vendor_lock_adapter_sql_row_lease_is_vendor_lock")
        )
        and "adapter_kind" in (coverage.get("vendor_lock_adapter_missing_sections") or [])
        and "target_backend" in (coverage.get("vendor_lock_adapter_missing_sections") or [])
        and str(coverage.get("postgres_probe_contract_version") or "").strip()
        == "phase-ii-worker-ownership-postgres-vendor-lock-probe-v1"
        and str(coverage.get("postgres_probe_status") or "").strip() == "blocked"
        and not _coerce_truthy_flag(coverage.get("postgres_probe_executes"))
        and not _coerce_truthy_flag(coverage.get("postgres_probe_sql_row_lease_is_vendor_lock"))
        and "advisory_lock_family" in (coverage.get("postgres_probe_missing_sections") or [])
        and "probe_safety" in (coverage.get("postgres_probe_missing_sections") or [])
        and str(coverage.get("postgres_probe_ready_status") or "").strip() == "ready"
        and not _coerce_truthy_flag(coverage.get("postgres_probe_ready_executes"))
        and str(coverage.get("postgres_execution_seam_contract_version") or "").strip()
        == "phase-ii-worker-ownership-postgres-advisory-lock-execution-seam-v1"
        and str(coverage.get("postgres_execution_default_status") or "").strip() == "blocked"
        and not _coerce_truthy_flag(coverage.get("postgres_execution_default_executor_bound"))
        and not _coerce_truthy_flag(
            coverage.get("postgres_execution_default_enabled_by_default")
        )
        and not _coerce_truthy_flag(
            coverage.get("postgres_execution_default_production_allowed")
        )
        and "executor_binding"
        in (coverage.get("postgres_execution_default_missing_sections") or [])
        and str(coverage.get("postgres_execution_default_probe_status") or "").strip()
        == "blocked"
        and not _coerce_truthy_flag(coverage.get("postgres_execution_default_probe_executed"))
        and str(coverage.get("postgres_execution_opt_in_status") or "").strip() == "ready"
        and _coerce_truthy_flag(coverage.get("postgres_execution_opt_in_executor_bound"))
        and not _coerce_truthy_flag(
            coverage.get("postgres_execution_opt_in_enabled_by_default")
        )
        and not _coerce_truthy_flag(coverage.get("postgres_execution_opt_in_production_allowed"))
        and str(coverage.get("postgres_execution_opt_in_probe_status") or "").strip()
        == "ready"
        and _coerce_truthy_flag(coverage.get("postgres_execution_opt_in_probe_executed"))
        and str(coverage.get("postgres_execution_opt_in_acquire_status") or "").strip()
        == "acquired"
        and _coerce_truthy_flag(coverage.get("postgres_execution_opt_in_acquire_executed"))
        and _coerce_truthy_flag(coverage.get("postgres_execution_opt_in_acquired"))
        and _coerce_non_negative_int(
            coverage.get("postgres_execution_opt_in_envelope_count"), 0
        )
        == 2
        and str(coverage.get("postgres_rollout_consumer_contract_version") or "").strip()
        == "phase-ii-worker-ownership-postgres-rollout-artifact-consumer-v1"
        and str(coverage.get("postgres_rollout_consumer_default_status") or "").strip()
        == "blocked"
        and "source_kind"
        in (coverage.get("postgres_rollout_consumer_default_missing_sections") or [])
        and "postgres_execution_seam"
        in (coverage.get("postgres_rollout_consumer_default_missing_sections") or [])
        and not _coerce_truthy_flag(
            coverage.get("postgres_rollout_consumer_default_will_enable_default")
        )
        and not _coerce_truthy_flag(
            coverage.get("postgres_rollout_consumer_default_executes_lock")
        )
        and str(coverage.get("postgres_rollout_consumer_ready_status") or "").strip()
        == "ready"
        and str(
            coverage.get("postgres_rollout_consumer_ready_target_backend") or ""
        ).strip()
        == "postgres"
        and str(
            coverage.get("postgres_rollout_consumer_ready_lock_adapter_kind") or ""
        ).strip()
        == "postgres_advisory_lock"
        and not _coerce_truthy_flag(
            coverage.get("postgres_rollout_consumer_ready_will_enable_default")
        )
        and not _coerce_truthy_flag(
            coverage.get("postgres_rollout_consumer_ready_executes_lock")
        )
        and str(
            coverage.get("postgres_rollout_consumer_input_source_status") or ""
        ).strip()
        == "ready"
        and _coerce_truthy_flag(
            coverage.get("postgres_rollout_consumer_input_source_ready")
        )
        and str(coverage.get("postgres_rollout_consumer_input_source_kind") or "").strip()
        == "rollout_artifact"
        and str(coverage.get("postgres_target_binding_contract_version") or "").strip()
        == "phase-ii-worker-ownership-postgres-vendor-lock-target-artifact-binding-v1"
        and str(coverage.get("postgres_target_binding_default_status") or "").strip()
        == "blocked"
        and "source_kind"
        in (
            coverage.get("postgres_target_binding_default_missing_sections")
            if isinstance(
                coverage.get("postgres_target_binding_default_missing_sections"), list
            )
            else []
        )
        and "postgres_rollout_consumer"
        in (
            coverage.get("postgres_target_binding_default_missing_sections")
            if isinstance(
                coverage.get("postgres_target_binding_default_missing_sections"), list
            )
            else []
        )
        and not _coerce_truthy_flag(
            coverage.get("postgres_target_binding_default_will_enable_lock")
        )
        and not _coerce_truthy_flag(
            coverage.get("postgres_target_binding_default_executes_lock")
        )
        and str(coverage.get("postgres_target_binding_ready_status") or "").strip()
        == "ready"
        and str(
            coverage.get("postgres_target_binding_ready_target_backend") or ""
        ).strip()
        == "postgres"
        and str(
            coverage.get("postgres_target_binding_ready_lock_adapter_kind") or ""
        ).strip()
        == "postgres_advisory_lock"
        and not _coerce_truthy_flag(
            coverage.get("postgres_target_binding_ready_will_enable_lock")
        )
        and not _coerce_truthy_flag(
            coverage.get("postgres_target_binding_ready_executes_lock")
        )
        and str(
            coverage.get("postgres_target_binding_target_input_status") or ""
        ).strip()
        == "ready"
        and str(
            coverage.get("postgres_target_binding_target_decision_status") or ""
        ).strip()
        == "ready"
        and _coerce_truthy_flag(
            coverage.get("postgres_target_binding_target_decision_production_allowed")
        )
        and str(coverage.get("postgres_semantics_binding_contract_version") or "").strip()
        == "phase-ii-worker-ownership-postgres-vendor-lock-semantics-binding-v1"
        and str(coverage.get("postgres_semantics_binding_default_status") or "").strip()
        == "blocked"
        and "target_artifact_binding"
        in (coverage.get("postgres_semantics_binding_default_missing_sections") or [])
        and "postgres_execution_seam"
        in (coverage.get("postgres_semantics_binding_default_missing_sections") or [])
        and not _coerce_truthy_flag(
            coverage.get("postgres_semantics_binding_default_will_enable_lock")
        )
        and not _coerce_truthy_flag(
            coverage.get("postgres_semantics_binding_default_will_update_gate")
        )
        and not _coerce_truthy_flag(
            coverage.get("postgres_semantics_binding_default_executes_lock")
        )
        and str(coverage.get("postgres_semantics_binding_ready_status") or "").strip()
        == "ready"
        and str(
            coverage.get("postgres_semantics_binding_ready_target_backend") or ""
        ).strip()
        == "postgres"
        and str(
            coverage.get("postgres_semantics_binding_ready_lock_adapter_kind") or ""
        ).strip()
        == "postgres_advisory_lock"
        and str(
            coverage.get("postgres_semantics_binding_ready_probe_status") or ""
        ).strip()
        == "ready"
        and str(
            coverage.get("postgres_semantics_binding_ready_adapter_status") or ""
        ).strip()
        == "ready"
        and str(
            coverage.get("postgres_semantics_binding_ready_semantics_status") or ""
        ).strip()
        == "ready"
        and not _coerce_truthy_flag(
            coverage.get("postgres_semantics_binding_ready_will_enable_lock")
        )
        and not _coerce_truthy_flag(
            coverage.get("postgres_semantics_binding_ready_will_update_gate")
        )
        and not _coerce_truthy_flag(
            coverage.get("postgres_semantics_binding_ready_executes_lock")
        )
        and str(coverage.get("postgres_wiring_decision_contract_version") or "").strip()
        == (
            "phase-ii-worker-ownership-postgres-vendor-lock-production-gate"
            "-wiring-decision-v1"
        )
        and str(coverage.get("postgres_wiring_decision_default_status") or "").strip()
        == "blocked"
        and "semantics_binding"
        in (coverage.get("postgres_wiring_decision_default_missing_sections") or [])
        and "decision_recorded"
        in (coverage.get("postgres_wiring_decision_default_missing_sections") or [])
        and not _coerce_truthy_flag(
            coverage.get("postgres_wiring_decision_default_wiring_allowed")
        )
        and not _coerce_truthy_flag(
            coverage.get("postgres_wiring_decision_default_will_update_gate")
        )
        and not _coerce_truthy_flag(
            coverage.get("postgres_wiring_decision_default_will_enable_lock")
        )
        and not _coerce_truthy_flag(
            coverage.get("postgres_wiring_decision_default_executes_lock")
        )
        and str(coverage.get("postgres_wiring_decision_ready_status") or "").strip()
        == "ready"
        and str(
            coverage.get("postgres_wiring_decision_ready_semantics_binding_status") or ""
        ).strip()
        == "ready"
        and str(coverage.get("postgres_wiring_decision_ready_candidate_status") or "").strip()
        == "ready"
        and _coerce_truthy_flag(
            coverage.get("postgres_wiring_decision_ready_wiring_allowed")
        )
        and str(
            coverage.get("postgres_wiring_decision_ready_target_backend") or ""
        ).strip()
        == "postgres"
        and str(
            coverage.get("postgres_wiring_decision_ready_lock_adapter_kind") or ""
        ).strip()
        == "postgres_advisory_lock"
        and not _coerce_truthy_flag(
            coverage.get("postgres_wiring_decision_ready_will_update_gate")
        )
        and not _coerce_truthy_flag(
            coverage.get("postgres_wiring_decision_ready_will_enable_lock")
        )
        and not _coerce_truthy_flag(
            coverage.get("postgres_wiring_decision_ready_executes_lock")
        )
        and str(coverage.get("production_dry_run_contract_version") or "").strip()
        == "phase-ii-worker-ownership-production-gate-composition-dry-run-v1"
        and str(coverage.get("production_dry_run_default_status") or "").strip()
        == "blocked"
        and "vendor_lock_wiring_decision"
        in (coverage.get("production_dry_run_default_missing_sections") or [])
        and "heartbeat_renewal_supervisor"
        in (coverage.get("production_dry_run_default_missing_sections") or [])
        and "rollout_confirmation"
        in (coverage.get("production_dry_run_default_missing_sections") or [])
        and "recovery_entry_auto_claim_enablement"
        in (coverage.get("production_dry_run_default_missing_sections") or [])
        and "ownership_audit_evidence"
        in (coverage.get("production_dry_run_default_missing_sections") or [])
        and "production_default_enablement_input_source"
        in (coverage.get("production_dry_run_default_missing_sections") or [])
        and not _coerce_truthy_flag(
            coverage.get("production_dry_run_default_all_required_ready")
        )
        and not _coerce_truthy_flag(
            coverage.get("production_dry_run_default_would_allow")
        )
        and not _coerce_truthy_flag(
            coverage.get("production_dry_run_default_will_enable")
        )
        and not _coerce_truthy_flag(
            coverage.get("production_dry_run_default_executes_lock")
        )
        and not _coerce_truthy_flag(
            coverage.get("production_dry_run_default_starts_worker")
        )
        and not _coerce_truthy_flag(
            coverage.get("production_dry_run_default_runs_auto_claim")
        )
        and str(coverage.get("production_dry_run_ready_status") or "").strip()
        == "ready"
        and (coverage.get("production_dry_run_ready_missing_sections") or []) == []
        and _coerce_truthy_flag(
            coverage.get("production_dry_run_ready_all_required_ready")
        )
        and _coerce_truthy_flag(coverage.get("production_dry_run_ready_would_allow"))
        and not _coerce_truthy_flag(
            coverage.get("production_dry_run_ready_will_enable")
        )
        and not _coerce_truthy_flag(
            coverage.get("production_dry_run_ready_executes_lock")
        )
        and not _coerce_truthy_flag(
            coverage.get("production_dry_run_ready_starts_worker")
        )
        and not _coerce_truthy_flag(
            coverage.get("production_dry_run_ready_runs_auto_claim")
        )
        and str(
            coverage.get("enablement_config_consumer_contract_version") or ""
        ).strip()
        == (
            "phase-ii-worker-ownership-production-enablement-runtime-config"
            "-consumer-v1"
        )
        and str(
            coverage.get("enablement_config_consumer_default_status") or ""
        ).strip()
        == "blocked"
        and "source_kind"
        in (coverage.get("enablement_config_consumer_default_missing_sections") or [])
        and "config_id"
        in (coverage.get("enablement_config_consumer_default_missing_sections") or [])
        and "enablement_input_source"
        in (coverage.get("enablement_config_consumer_default_missing_sections") or [])
        and "composition_dry_run"
        in (coverage.get("enablement_config_consumer_default_missing_sections") or [])
        and not _coerce_truthy_flag(
            coverage.get("enablement_config_consumer_default_will_enable")
        )
        and not _coerce_truthy_flag(
            coverage.get("enablement_config_consumer_default_executes_lock")
        )
        and not _coerce_truthy_flag(
            coverage.get("enablement_config_consumer_default_starts_worker")
        )
        and not _coerce_truthy_flag(
            coverage.get("enablement_config_consumer_default_runs_auto_claim")
        )
        and str(
            coverage.get("enablement_config_consumer_ready_status") or ""
        ).strip()
        == "ready"
        and (
            coverage.get("enablement_config_consumer_ready_missing_sections") or []
        )
        == []
        and str(
            coverage.get("enablement_config_consumer_ready_target_backend") or ""
        ).strip()
        == "postgres"
        and str(
            coverage.get("enablement_config_consumer_ready_lock_adapter_kind") or ""
        ).strip()
        == "postgres_advisory_lock"
        and str(
            coverage.get("enablement_config_consumer_ready_input_source_status") or ""
        ).strip()
        == "ready"
        and str(
            coverage.get("enablement_config_consumer_ready_dry_run_status") or ""
        ).strip()
        == "ready"
        and _coerce_truthy_flag(
            coverage.get("enablement_config_consumer_ready_dry_run_would_allow")
        )
        and not _coerce_truthy_flag(
            coverage.get("enablement_config_consumer_ready_will_enable")
        )
        and not _coerce_truthy_flag(
            coverage.get("enablement_config_consumer_ready_executes_lock")
        )
        and not _coerce_truthy_flag(
            coverage.get("enablement_config_consumer_ready_starts_worker")
        )
        and not _coerce_truthy_flag(
            coverage.get("enablement_config_consumer_ready_runs_auto_claim")
        )
        and not _coerce_truthy_flag(coverage.get("vendor_lock_production_allowed"))
        and str(coverage.get("vendor_lock_target_decision_contract_version") or "").strip()
        == "phase-ii-worker-ownership-vendor-lock-target-decision-v1"
        and str(coverage.get("vendor_lock_target_decision_status") or "").strip() == "blocked"
        and not _coerce_truthy_flag(coverage.get("vendor_lock_target_decision_recorded"))
        and str(coverage.get("vendor_lock_target_backend") or "").strip() == ""
        and str(coverage.get("vendor_lock_target_adapter_kind") or "").strip() == ""
        and str(coverage.get("vendor_lock_target_scope") or "").strip() == ""
        and str(coverage.get("vendor_lock_target_fencing_strategy") or "").strip() == ""
        and str(coverage.get("vendor_lock_target_ttl_renewal_strategy") or "").strip() == ""
        and str(coverage.get("vendor_lock_target_failover_strategy") or "").strip() == ""
        and str(coverage.get("vendor_lock_target_stale_cleanup_strategy") or "").strip() == ""
        and str(coverage.get("vendor_lock_target_input_contract_version") or "").strip()
        == "phase-ii-worker-ownership-vendor-lock-target-decision-input-v1"
        and str(coverage.get("vendor_lock_target_input_source_status") or "").strip()
        == "blocked"
        and str(coverage.get("vendor_lock_target_input_source_kind") or "").strip() == ""
        and str(coverage.get("vendor_lock_target_input_decision_id") or "").strip() == ""
        and str(coverage.get("vendor_lock_target_input_approved_by") or "").strip() == ""
        and str(coverage.get("vendor_lock_target_input_approved_at") or "").strip() == ""
        and str(coverage.get("vendor_lock_target_input_backend") or "").strip() == ""
        and str(coverage.get("vendor_lock_target_input_adapter_kind") or "").strip() == ""
        and str(coverage.get("vendor_lock_target_input_rollout_artifact") or "").strip() == ""
        and str(coverage.get("vendor_lock_target_input_config_key") or "").strip() == ""
        and str(
            coverage.get("vendor_lock_target_input_manual_approval_reference") or ""
        ).strip()
        == ""
        and "input_source_kind"
        in (coverage.get("vendor_lock_target_input_missing_sections") or [])
        and "decision_id" in (coverage.get("vendor_lock_target_input_missing_sections") or [])
        and not _coerce_truthy_flag(
            coverage.get("vendor_lock_target_input_sql_row_lease_is_vendor_lock")
        )
        and "input_source" in (coverage.get("vendor_lock_target_missing_sections") or [])
        and "decision_recorded" in (coverage.get("vendor_lock_target_missing_sections") or [])
        and "target_backend" in (coverage.get("vendor_lock_target_missing_sections") or [])
        and not _coerce_truthy_flag(
            coverage.get("vendor_lock_target_sql_row_lease_is_vendor_lock")
        )
        and not _coerce_truthy_flag(coverage.get("vendor_lock_target_production_allowed"))
        and str(coverage.get("renewal_supervisor_contract_version") or "").strip()
        == "phase-ii-worker-ownership-renewal-supervisor-v1"
        and str(coverage.get("renewal_supervisor_status") or "").strip() == "blocked"
        and "background_supervisor" in (coverage.get("renewal_supervisor_missing_sections") or [])
        and not _coerce_truthy_flag(coverage.get("renewal_supervisor_enabled_by_default"))
        and _coerce_truthy_flag(coverage.get("renewal_supervisor_renew_once_supported"))
        and _coerce_truthy_flag(coverage.get("renewal_supervisor_owner_identity_required"))
        and _coerce_truthy_flag(coverage.get("renewal_supervisor_ttl_interval_policy_ready"))
        and _coerce_truthy_flag(coverage.get("renewal_supervisor_controlled_lifecycle_supported"))
        and not _coerce_truthy_flag(coverage.get("renewal_supervisor_starts_by_default"))
        and not _coerce_truthy_flag(coverage.get("renewal_supervisor_active"))
        and str(coverage.get("renewal_supervisor_last_renewal_status") or "").strip() == ""
        and _coerce_truthy_flag(coverage.get("renewal_supervisor_stop_supported"))
        and _coerce_truthy_flag(coverage.get("renewal_supervisor_failure_fail_closed"))
        and _coerce_truthy_flag(coverage.get("renewal_supervisor_lease_loss_fail_closed"))
        and str(coverage.get("renewal_supervisor_renew_once_status") or "").strip() == "renewed"
        and not _coerce_truthy_flag(coverage.get("renewal_supervisor_renew_once_background_started"))
        and str(coverage.get("renewal_supervisor_stale_fencing_status") or "").strip() == "blocked"
        and str(coverage.get("renewal_supervisor_stale_fencing_reason") or "").strip()
        == "stale_worker_fencing_token"
        and not _coerce_truthy_flag(coverage.get("renewal_supervisor_lifecycle_initial_active"))
        and _coerce_truthy_flag(coverage.get("renewal_supervisor_lifecycle_started_active"))
        and str(coverage.get("renewal_supervisor_lifecycle_started_status") or "").strip() == "renewed"
        and _coerce_non_negative_int(coverage.get("renewal_supervisor_lifecycle_started_count"), 0) >= 1
        and not _coerce_truthy_flag(coverage.get("renewal_supervisor_lifecycle_stopped_active"))
        and _coerce_non_negative_int(coverage.get("renewal_supervisor_lifecycle_stopped_count"), 0) >= 1
        and str(coverage.get("rollout_readiness_contract_version") or "").strip()
        == "phase-ii-worker-ownership-rollout-readiness-v1"
        and str(coverage.get("rollout_readiness_status") or "").strip() == "blocked"
        and "strict_mode_rollout" in (coverage.get("rollout_missing_sections") or [])
        and not _coerce_truthy_flag(coverage.get("production_rollout_confirmed"))
        and _coerce_truthy_flag(coverage.get("rollout_migration_ready"))
        and _coerce_truthy_flag(coverage.get("rollout_stale_fencing_verified"))
        and not _coerce_truthy_flag(coverage.get("rollout_rollback_plan_ready"))
        and str(coverage.get("rollout_operationalization_status") or "").strip() == "blocked"
        and str(coverage.get("rollout_mode") or "").strip() == "readiness_only"
        and "rollback_plan" in (coverage.get("rollout_missing_artifacts") or [])
        and str(coverage.get("rollout_rollback_plan_status") or "").strip() == "missing"
        and str(coverage.get("rollout_fallback_policy_status") or "").strip() == "missing"
        and str(coverage.get("rollout_renewal_lifecycle_verification_status") or "").strip()
        == "missing"
        and str(coverage.get("rollout_auto_claim_decision_status") or "").strip() == "missing"
        and str(coverage.get("rollout_confirmation_decision_contract_version") or "").strip()
        == "phase-ii-worker-ownership-rollout-confirmation-decision-v1"
        and str(coverage.get("rollout_confirmation_decision_status") or "").strip() == "blocked"
        and not _coerce_truthy_flag(coverage.get("rollout_decision_recorded"))
        and str(coverage.get("rollout_target_store_mode") or "").strip() == ""
        and "decision_recorded" in (coverage.get("rollout_confirmation_missing_sections") or [])
        and not _coerce_truthy_flag(
            coverage.get("rollout_confirmation_production_rollout_confirmed")
        )
        and str(coverage.get("rollout_confirmation_input_contract_version") or "").strip()
        == "phase-ii-worker-ownership-rollout-confirmation-input-source-v1"
        and str(coverage.get("rollout_confirmation_input_source_status") or "").strip()
        == "blocked"
        and str(coverage.get("rollout_confirmation_input_source_kind") or "").strip() == ""
        and str(coverage.get("rollout_confirmation_input_decision_id") or "").strip() == ""
        and "input_source_kind"
        in (coverage.get("rollout_confirmation_input_missing_sections") or [])
        and "decision_id" in (coverage.get("rollout_confirmation_input_missing_sections") or [])
        and not _coerce_truthy_flag(
            coverage.get("rollout_confirmation_input_sql_row_lease_is_authority")
        )
        and str(coverage.get("ownership_audit_contract_version") or "").strip()
        == "phase-ii-worker-ownership-audit-evidence-v1"
        and str(coverage.get("ownership_audit_status") or "").strip() == "blocked"
        and "operation_history" in (coverage.get("ownership_audit_missing_sections") or [])
        and _coerce_truthy_flag(coverage.get("ownership_audit_compact_evidence"))
        and not _coerce_truthy_flag(coverage.get("ownership_audit_authorization_source"))
        and str(coverage.get("enablement_strategy_contract_version") or "").strip()
        == "phase-ii-worker-ownership-production-enablement-strategy-v1"
        and str(coverage.get("enablement_strategy_status") or "").strip() == "blocked"
        and "vendor_lock_semantics" in (coverage.get("enablement_strategy_blocking_sections") or [])
        and "production_default_enablement_input_source"
        in (coverage.get("enablement_strategy_blocking_sections") or [])
        and not _coerce_truthy_flag(coverage.get("production_default_enabled_requested"))
        and not _coerce_truthy_flag(coverage.get("production_default_allowed"))
        and str(coverage.get("enablement_input_source_contract_version") or "").strip()
        == "phase-ii-worker-ownership-production-default-enablement-input-source-v1"
        and str(coverage.get("enablement_input_source_status") or "").strip() == "blocked"
        and str(coverage.get("enablement_input_source_kind") or "").strip() == ""
        and str(coverage.get("enablement_request_id") or "").strip() == ""
        and str(coverage.get("enablement_target_store_mode") or "").strip() == ""
        and str(coverage.get("enablement_rollout_artifact") or "").strip() == ""
        and not _coerce_truthy_flag(coverage.get("enablement_input_source_ready"))
        and "input_source_kind"
        in (coverage.get("enablement_input_source_missing_sections") or [])
        and _coerce_truthy_flag(coverage.get("enablement_explicit_required"))
        and _coerce_truthy_flag(coverage.get("enablement_fail_closed_when_blocked"))
        and _coerce_truthy_flag(coverage.get("enablement_sql_row_lease_not_default_authority"))
    )


def _is_recovery_audit_operation_history_coverage_aligned(coverage: dict[str, Any]) -> bool:
    return (
        _coerce_truthy_flag(coverage.get("audit_smoke"))
        and str(coverage.get("contract_version") or "").strip()
        == "phase-ii-recovery-audit-production-gate-v1"
        and _coerce_truthy_flag(coverage.get("ready"))
        and _coerce_truthy_flag(coverage.get("operation_history_supported"))
        and _coerce_truthy_flag(coverage.get("audit_summary_supported"))
        and _coerce_truthy_flag(coverage.get("timeline_writer_available"))
        and _coerce_truthy_flag(coverage.get("idempotent_trace_dedupe"))
        and not _coerce_truthy_flag(coverage.get("authorization_source"))
    )


def _is_production_recovery_registry_checkpoint_policy_coverage_aligned(
    coverage: dict[str, Any],
) -> bool:
    return (
        _coerce_truthy_flag(coverage.get("policy_smoke"))
        and str(coverage.get("contract_version") or "").strip()
        == "phase-ii-production-recovery-registry-checkpoint-policy-v1"
        and _coerce_truthy_flag(coverage.get("ready"))
        and _coerce_truthy_flag(coverage.get("registry_binding_policy_ready"))
        and _coerce_truthy_flag(coverage.get("checkpoint_resume_cursor_policy_ready"))
        and not _coerce_truthy_flag(coverage.get("authorization_source"))
    )


def _is_recovery_retry_evidence_coverage_aligned(coverage: dict[str, Any]) -> bool:
    return (
        _coerce_truthy_flag(coverage.get("retry_smoke"))
        and str(coverage.get("contract_version") or "").strip() == "phase-ii-recovery-retry-protocol-v1"
        and _coerce_non_negative_int(coverage.get("attempt_number"), 0) == 3
        and _coerce_non_negative_int(coverage.get("max_attempts"), 0) == 3
        and str(coverage.get("retry_status") or "").strip() == "exhausted"
        and _coerce_truthy_flag(coverage.get("terminal"))
        and str(coverage.get("recovery_reason") or "").strip() == "workspace_backend_not_durable"
        and _coerce_truthy_flag(coverage.get("idempotency_key_present"))
    )


def _is_durable_recovery_loader_coverage_aligned(coverage: dict[str, Any]) -> bool:
    return (
        _coerce_truthy_flag(coverage.get("loader_smoke"))
        and str(coverage.get("contract_version") or "").strip() == "phase-ii-durable-recovery-loader-v1"
        and str(coverage.get("loader_status") or "").strip() == "ready"
        and _coerce_truthy_flag(coverage.get("loader_ready"))
        and str(coverage.get("loader_recovery_reason") or "").strip() == "ready_via_registry"
        and _coerce_truthy_flag(coverage.get("all_bindings_resolved"))
        and str(coverage.get("missing_recovery_reason") or "").strip() == "run_snapshot_missing"
        and str(coverage.get("unsafe_recovery_reason") or "").strip() == "descriptor_corrupted"
        and not _coerce_truthy_flag(coverage.get("executes_recovery"))
        and not _coerce_truthy_flag(coverage.get("deserializes_callables"))
    )


def _is_continuation_descriptor_lifecycle_coverage_aligned(coverage: dict[str, Any]) -> bool:
    states = set(_normalize_string_list(coverage.get("states")))
    unsafe_keys = set(_normalize_string_list(coverage.get("unsafe_descriptor_keys")))
    return (
        _coerce_truthy_flag(coverage.get("lifecycle_smoke"))
        and str(coverage.get("contract_version") or "").strip()
        == "phase-ii-continuation-descriptor-lifecycle-governance-v1"
        and _coerce_truthy_flag(coverage.get("governed"))
        and _coerce_truthy_flag(coverage.get("all_ready"))
        and {"ready", "bound", "stale", "unsafe"}.issubset(states)
        and "handler" in unsafe_keys
        and str(coverage.get("unresolved_recovery_reason") or "").strip() == "missing_registered_binding"
        and str(coverage.get("stale_recovery_reason") or "").strip() == "denied"
        and str(coverage.get("unsafe_recovery_reason") or "").strip() == "descriptor_corrupted"
    )


def _is_loader_execution_handoff_coverage_aligned(coverage: dict[str, Any]) -> bool:
    return (
        _coerce_truthy_flag(coverage.get("handoff_smoke"))
        and str(coverage.get("contract_version") or "").strip()
        == "phase-ii-durable-loader-execution-handoff-policy-v1"
        and str(coverage.get("default_status") or "").strip() == "blocked"
        and str(coverage.get("default_blocked_reason") or "").strip() == "explicit_handoff_required"
        and not _coerce_truthy_flag(coverage.get("default_will_execute"))
        and str(coverage.get("explicit_status") or "").strip() == "blocked"
        and str(coverage.get("explicit_blocked_reason") or "").strip() == "recovery_executor_not_bound"
        and not _coerce_truthy_flag(coverage.get("explicit_will_execute"))
        and not _coerce_truthy_flag(coverage.get("recovery_executor_bound"))
    )


def _is_recovery_retry_scheduler_coverage_aligned(coverage: dict[str, Any]) -> bool:
    return (
        _coerce_truthy_flag(coverage.get("scheduler_smoke"))
        and str(coverage.get("contract_version") or "").strip() == "phase-ii-recovery-retry-scheduler-v1"
        and str(coverage.get("default_status") or "").strip() == "disabled"
        and _coerce_truthy_flag(coverage.get("default_eligible"))
        and not _coerce_truthy_flag(coverage.get("default_will_execute"))
        and str(coverage.get("enabled_status") or "").strip() == "executed"
        and _coerce_truthy_flag(coverage.get("enabled_will_execute"))
        and str(coverage.get("latest_operation_status") or "").strip() == "recovered"
        and _coerce_non_negative_int(coverage.get("attempt_number"), 0) == 1
        and str(coverage.get("retry_status") or "").strip() == "retryable"
        and str(coverage.get("recovery_reason") or "").strip() == "transient_workspace_unavailable"
        and _coerce_truthy_flag(coverage.get("previous_operation_id_present"))
        and _coerce_truthy_flag(coverage.get("idempotency_key_present"))
    )


def _is_child_executor_promotion_gate_coverage_aligned(coverage: dict[str, Any]) -> bool:
    return (
        _coerce_truthy_flag(coverage.get("gate_smoke"))
        and bool(str(coverage.get("contract_version") or "").strip())
        and str(coverage.get("gate_status") or "").strip() == "blocked"
        and not _coerce_truthy_flag(coverage.get("allowed"))
        and bool(str(coverage.get("failure_reason") or "").strip())
        and _coerce_non_negative_int(coverage.get("blocker_count"), 0) >= 0
        and bool(str(coverage.get("recommended_next_step") or "").strip())
    )


def _is_child_executor_dispatcher_coverage_aligned(coverage: dict[str, Any]) -> bool:
    return (
        _coerce_truthy_flag(coverage.get("dispatcher_smoke"))
        and str(coverage.get("contract_version") or "").strip() == "phase-ii-child-executor-dispatcher-v1"
        and str(coverage.get("default_status") or "").strip() == "blocked"
        and str(coverage.get("default_blocked_reason") or "").strip() == "dispatcher_disabled"
        and not _coerce_truthy_flag(coverage.get("default_will_dispatch"))
        and str(coverage.get("blocked_reason") or "").strip() == "dispatch_contract_not_ready"
        and not _coerce_truthy_flag(coverage.get("blocked_will_dispatch"))
        and str(coverage.get("enabled_status") or "").strip() == "dispatched"
        and _coerce_truthy_flag(coverage.get("enabled_will_dispatch"))
        and str(coverage.get("backend_result_status") or "").strip() == "completed"
        and _coerce_non_negative_int(coverage.get("backend_invocation_count"), 0) == 1
    )


def _is_child_executor_dispatch_result_handoff_coverage_aligned(
    coverage: dict[str, Any],
) -> bool:
    return (
        _coerce_truthy_flag(coverage.get("result_handoff_smoke"))
        and str(coverage.get("contract_version") or "").strip()
        == "phase-ii-child-executor-dispatch-result-handoff-v1"
        and str(coverage.get("ready_handoff_status") or "").strip() == "ready"
        and _coerce_truthy_flag(coverage.get("ready_handoff_ready"))
        and _coerce_truthy_flag(coverage.get("ready_output_ref_present"))
        and _coerce_truthy_flag(coverage.get("ready_audit_evidence_present"))
        and _coerce_truthy_flag(coverage.get("ready_backend_result_schema_valid"))
        and not _coerce_truthy_flag(coverage.get("ready_parent_merge_performed"))
        and not _coerce_truthy_flag(coverage.get("ready_merge_authorization"))
        and not _coerce_truthy_flag(coverage.get("ready_retry_scheduled"))
        and not _coerce_truthy_flag(coverage.get("ready_production_dispatch_authorized"))
        and str(coverage.get("blocked_handoff_status") or "").strip() == "blocked"
        and str(coverage.get("blocked_dispatcher_reason") or "").strip()
        == "dispatcher_disabled"
        and "dispatch_success" in _normalize_string_list(coverage.get("blocked_missing_sections"))
        and str(coverage.get("malformed_handoff_status") or "").strip() == "blocked"
        and "output_ref" in _normalize_string_list(coverage.get("malformed_missing_sections"))
        and "audit_evidence" in _normalize_string_list(
            coverage.get("malformed_missing_sections")
        )
    )


def _is_child_executor_dispatch_result_retry_audit_coverage_aligned(
    coverage: dict[str, Any],
) -> bool:
    return (
        _coerce_truthy_flag(coverage.get("retry_audit_smoke"))
        and str(coverage.get("contract_version") or "").strip()
        == "phase-ii-child-executor-dispatch-result-retry-audit-policy-v1"
        and str(coverage.get("success_policy_status") or "").strip() == "ready"
        and str(coverage.get("success_retry_policy_status") or "").strip()
        == "not_required"
        and not _coerce_truthy_flag(coverage.get("success_retry_scheduled"))
        and not _coerce_truthy_flag(coverage.get("success_will_retry"))
        and str(coverage.get("retryable_policy_status") or "").strip() == "ready"
        and str(coverage.get("retryable_retry_policy_status") or "").strip()
        == "retryable"
        and _coerce_truthy_flag(coverage.get("retryable_audit_evidence_present"))
        and _coerce_truthy_flag(coverage.get("retryable_idempotency_evidence_present"))
        and _coerce_truthy_flag(coverage.get("retryable_scheduler_required"))
        and str(coverage.get("retryable_retry_reason") or "").strip()
        == "sandbox_timeout"
        and not _coerce_truthy_flag(coverage.get("retryable_retry_scheduled"))
        and not _coerce_truthy_flag(coverage.get("retryable_will_retry"))
        and str(coverage.get("terminal_policy_status") or "").strip() == "ready"
        and str(coverage.get("terminal_retry_policy_status") or "").strip()
        == "terminal"
        and str(coverage.get("terminal_reason") or "").strip()
        == "sandbox_payload_unsafe"
        and not _coerce_truthy_flag(coverage.get("terminal_will_retry"))
        and str(coverage.get("missing_idempotency_status") or "").strip()
        == "blocked"
        and "idempotency_evidence"
        in _normalize_string_list(coverage.get("missing_idempotency_missing_sections"))
        and not _coerce_truthy_flag(coverage.get("missing_idempotency_retry_scheduled"))
    )


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    steps = [_run_step(step) for step in _build_steps(args)]
    failed_steps = [step for step in steps if not step["passed"]]
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "root_dir": str(ROOT_DIR),
        "python": sys.executable,
        "platform": sys.platform,
        "passed": len(failed_steps) == 0,
        "step_count": len(steps),
        "failed_steps": [{"name": step["name"], "exit_code": step["exit_code"]} for step in failed_steps],
        "steps": steps,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(_render_summary(report), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
