import hashlib
import inspect
import json
import re
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

try:
    from services.startup_diagnostics_service import get_startup_diagnostics_service
    from services.framework_adapter_runtime_service import get_framework_adapter_runtime_service
    from services.runtime_surface_service import get_runtime_surface_service
    from services.scheduler_runtime_diagnostics_service import get_scheduler_runtime_diagnostics_service
    from services.capability_gap_service import get_capability_gap_service
    from services.doctor_runtime_service import get_doctor_runtime_service
    from services.framework_adapter_diagnostics_service import get_framework_adapter_diagnostics_service
    from services.run_trace_service import get_run_trace_service
    from services.remediation_status_service import get_remediation_status_service
    from services.provider_failover_analytics_service import get_provider_failover_analytics_service
    from database import get_db
    from schemas_runtime_surface import FrameworkAdapterExternalPilotRunRequest, FrameworkAdapterPilotRunRequest, FrameworkAdapterPrecheckRequest, RuntimeSurfaceEmbeddedRuntimeBootstrapUpdateRequest, RuntimeSurfaceUpdateRequest
    from config import CORS_ALLOWED_ORIGINS, CORS_ALLOWED_ORIGIN_REGEX, ENABLE_LANGGRAPH_EXTERNAL_PILOT, ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.startup_diagnostics_service import get_startup_diagnostics_service
    from backend.services.framework_adapter_runtime_service import get_framework_adapter_runtime_service
    from backend.services.runtime_surface_service import get_runtime_surface_service
    from backend.services.scheduler_runtime_diagnostics_service import get_scheduler_runtime_diagnostics_service
    from backend.services.capability_gap_service import get_capability_gap_service
    from backend.services.doctor_runtime_service import get_doctor_runtime_service
    from backend.services.framework_adapter_diagnostics_service import get_framework_adapter_diagnostics_service
    from backend.services.run_trace_service import get_run_trace_service
    from backend.services.remediation_status_service import get_remediation_status_service
    from backend.services.provider_failover_analytics_service import get_provider_failover_analytics_service
    from backend.database import get_db
    from backend.schemas_runtime_surface import FrameworkAdapterExternalPilotRunRequest, FrameworkAdapterPilotRunRequest, FrameworkAdapterPrecheckRequest, RuntimeSurfaceEmbeddedRuntimeBootstrapUpdateRequest, RuntimeSurfaceUpdateRequest
    from backend.config import CORS_ALLOWED_ORIGINS, CORS_ALLOWED_ORIGIN_REGEX, ENABLE_LANGGRAPH_EXTERNAL_PILOT, ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER


router = APIRouter(prefix="/api", tags=["系统"])

_RUNTIME_CONTRACT_GATE_TRACE_FINGERPRINTS: set[str] = set()


def _get_runtime_profile_with_optional_db(runtime_surface_service, db: Session) -> dict:
    get_runtime_profile_method = getattr(runtime_surface_service, "get_runtime_profile")
    try:
        signature = inspect.signature(get_runtime_profile_method)
    except (TypeError, ValueError):
        return get_runtime_profile_method()
    if "db" in signature.parameters:
        return get_runtime_profile_method(db=db)
    return get_runtime_profile_method()


def _parse_iso_datetime(value: str | None) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        normalized = text.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _resolve_failover_alert_level(switch_rate: float, medium: float, high: float) -> str:
    if switch_rate > high:
        return "high"
    if switch_rate > medium:
        return "medium"
    return "low"


def _collect_latest_framework_adapter_external_error_summary(
    *,
    db: Session,
    limit: int = 50,
) -> dict | None:
    return get_framework_adapter_diagnostics_service().collect_latest_external_error_summary(
        db=db,
        limit=limit,
    )


def _collect_framework_adapter_external_error_counts(
    *,
    db: Session,
    limit: int = 50,
) -> dict | None:
    return get_framework_adapter_diagnostics_service().collect_external_error_counts(
        db=db,
        limit=limit,
    )


def _attach_framework_adapter_runtime_diagnostics(
    *,
    report: dict,
    db: Session,
) -> dict:
    checks = report.get("checks") or {}
    framework_adapter_check = checks.get("framework_adapters")
    if not isinstance(framework_adapter_check, dict):
        return report
    latest_external_error = _collect_latest_framework_adapter_external_error_summary(db=db)
    if latest_external_error:
        framework_adapter_check["latest_external_pilot_failure"] = latest_external_error
    external_error_counts = _collect_framework_adapter_external_error_counts(db=db)
    if external_error_counts:
        framework_adapter_check["external_pilot_failure_counts"] = external_error_counts
    return report


def _build_runtime_contract_gate_trace_fingerprint(
    *,
    conversation_id: int | None,
    plan_id: int | None,
    item_id: int | None,
    runtime_contract_gate: dict,
) -> str:
    gate = dict(runtime_contract_gate or {})
    raw_runtime_contract_summary = gate.get("runtime_contract_summary")
    runtime_contract_summary = _normalize_runtime_contract_gate_summary(raw_runtime_contract_summary)
    runtime_contract_artifact_schema = _normalize_runtime_contract_artifact_schema(
        gate.get("runtime_contract_artifact_schema")
    )
    failed_checks = [
        {
            "name": check.get("name"),
            "failure_reason": check.get("failure_reason"),
            "status_code": check.get("status_code"),
            "contract_snapshot_status": check.get("contract_snapshot_status"),
            "adapter_health_status": check.get("adapter_health_status"),
            "missing_payload_count": check.get("missing_payload_count"),
            "observed_status_kinds": check.get("observed_status_kinds") or [],
        }
        for check in (gate.get("checks") or [])
        if isinstance(check, dict) and not bool(check.get("ok"))
    ]
    payload = {
        "conversation_id": conversation_id,
        "plan_id": plan_id,
        "item_id": item_id,
        "contract_version": gate.get("contract_version"),
        "overall_status": gate.get("overall_status"),
        "report_path": gate.get("report_path"),
        "check_count": gate.get("check_count"),
        "failed_check_count": gate.get("failed_check_count"),
        "failure_reason": gate.get("failure_reason"),
        "runtime_contract_summary": runtime_contract_summary,
        "runtime_contract_artifact_schema": runtime_contract_artifact_schema,
        "failed_checks": failed_checks,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize_runtime_contract_gate_summary(summary: object) -> dict:
    if not isinstance(summary, dict):
        return {
            "overall_status": "",
            "check_count": 0,
            "failed_check_count": 0,
            "missing_payload_count": 0,
            "approval_replay_coverage": {
                "event_payload_sample": False,
                "observed_status_kinds": [],
            },
            "approval_lifecycle_recovery_coverage": _normalize_approval_lifecycle_recovery_coverage({}),
            "approved_tool_execution_coverage": _normalize_approved_tool_execution_coverage({}),
            "sdk_tool_runtime_execution_coverage": _normalize_sdk_tool_runtime_execution_coverage({}),
            "embedded_sdk_persistence_coverage": _normalize_embedded_sdk_persistence_coverage({}),
            "worker_ownership_store_mode_coverage": _normalize_worker_ownership_store_mode_coverage({}),
            "checkpoint_resume_cursor_coverage": _normalize_checkpoint_resume_cursor_coverage({}),
            "child_executor_promotion_gate_coverage": _normalize_child_executor_promotion_gate_coverage({}),
            "child_executor_execution_prerequisites_coverage": _normalize_child_executor_execution_prerequisites_coverage({}),
            "child_executor_dispatch_coverage": _normalize_child_executor_dispatch_coverage({}),
            "recovery_retry_evidence_coverage": _normalize_recovery_retry_evidence_coverage({}),
            "recovery_retry_scheduler_coverage": _normalize_recovery_retry_scheduler_coverage({}),
            "durable_recovery_loader_coverage": _normalize_durable_recovery_loader_coverage({}),
            "child_executor_dispatcher_coverage": _normalize_child_executor_dispatcher_coverage({}),
            "child_executor_dispatch_result_handoff_coverage": (
                _normalize_child_executor_dispatch_result_handoff_coverage({})
            ),
            "child_executor_dispatch_result_retry_audit_coverage": (
                _normalize_child_executor_dispatch_result_retry_audit_coverage({})
            ),
            "child_executor_sandbox_backend_binding_coverage": (
                _normalize_child_executor_sandbox_backend_binding_coverage({})
            ),
            "subagent_lane_query_detail_coverage": _normalize_subagent_lane_query_detail_coverage({}),
        }
    coverage = summary.get("approval_replay_coverage")
    if not isinstance(coverage, dict):
        coverage = {}
    lifecycle_coverage = summary.get("approval_lifecycle_recovery_coverage")
    if not isinstance(lifecycle_coverage, dict):
        lifecycle_coverage = {}
    approved_tool_coverage = summary.get("approved_tool_execution_coverage")
    if not isinstance(approved_tool_coverage, dict):
        approved_tool_coverage = {}
    sdk_tool_coverage = summary.get("sdk_tool_runtime_execution_coverage")
    if not isinstance(sdk_tool_coverage, dict):
        sdk_tool_coverage = {}
    embedded_persistence_coverage = summary.get("embedded_sdk_persistence_coverage")
    if not isinstance(embedded_persistence_coverage, dict):
        embedded_persistence_coverage = {}
    worker_ownership_coverage = summary.get("worker_ownership_store_mode_coverage")
    if not isinstance(worker_ownership_coverage, dict):
        worker_ownership_coverage = {}
    checkpoint_cursor_coverage = summary.get("checkpoint_resume_cursor_coverage")
    if not isinstance(checkpoint_cursor_coverage, dict):
        checkpoint_cursor_coverage = {}
    child_executor_gate_coverage = summary.get("child_executor_promotion_gate_coverage")
    if not isinstance(child_executor_gate_coverage, dict):
        child_executor_gate_coverage = {}
    child_executor_prerequisites_coverage = summary.get("child_executor_execution_prerequisites_coverage")
    if not isinstance(child_executor_prerequisites_coverage, dict):
        child_executor_prerequisites_coverage = {}
    child_executor_dispatch_coverage = summary.get("child_executor_dispatch_coverage")
    if not isinstance(child_executor_dispatch_coverage, dict):
        child_executor_dispatch_coverage = {}
    recovery_retry_coverage = summary.get("recovery_retry_evidence_coverage")
    if not isinstance(recovery_retry_coverage, dict):
        recovery_retry_coverage = {}
    recovery_retry_scheduler_coverage = summary.get("recovery_retry_scheduler_coverage")
    if not isinstance(recovery_retry_scheduler_coverage, dict):
        recovery_retry_scheduler_coverage = {}
    durable_recovery_loader_coverage = summary.get("durable_recovery_loader_coverage")
    if not isinstance(durable_recovery_loader_coverage, dict):
        durable_recovery_loader_coverage = {}
    child_executor_dispatcher_coverage = summary.get("child_executor_dispatcher_coverage")
    if not isinstance(child_executor_dispatcher_coverage, dict):
        child_executor_dispatcher_coverage = {}
    child_executor_dispatch_result_handoff_coverage = summary.get(
        "child_executor_dispatch_result_handoff_coverage"
    )
    if not isinstance(child_executor_dispatch_result_handoff_coverage, dict):
        child_executor_dispatch_result_handoff_coverage = {}
    child_executor_dispatch_result_retry_audit_coverage = summary.get(
        "child_executor_dispatch_result_retry_audit_coverage"
    )
    if not isinstance(child_executor_dispatch_result_retry_audit_coverage, dict):
        child_executor_dispatch_result_retry_audit_coverage = {}
    child_executor_sandbox_backend_binding_coverage = summary.get(
        "child_executor_sandbox_backend_binding_coverage"
    )
    if not isinstance(child_executor_sandbox_backend_binding_coverage, dict):
        child_executor_sandbox_backend_binding_coverage = {}
    subagent_lane_detail_coverage = summary.get("subagent_lane_query_detail_coverage")
    if not isinstance(subagent_lane_detail_coverage, dict):
        subagent_lane_detail_coverage = {}
    return {
        "overall_status": str(summary.get("overall_status") or ""),
        "check_count": _coerce_runtime_contract_non_negative_int(summary.get("check_count")),
        "failed_check_count": _coerce_runtime_contract_non_negative_int(summary.get("failed_check_count")),
        "missing_payload_count": _coerce_runtime_contract_non_negative_int(summary.get("missing_payload_count")),
        "approval_replay_coverage": {
            "event_payload_sample": bool(coverage.get("event_payload_sample")),
            "observed_status_kinds": [
                str(status_kind)
                for status_kind in coverage.get("observed_status_kinds") or []
                if str(status_kind or "").strip()
            ],
        },
        "approval_lifecycle_recovery_coverage": _normalize_approval_lifecycle_recovery_coverage(
            lifecycle_coverage
        ),
        "approved_tool_execution_coverage": _normalize_approved_tool_execution_coverage(approved_tool_coverage),
        "sdk_tool_runtime_execution_coverage": _normalize_sdk_tool_runtime_execution_coverage(sdk_tool_coverage),
        "embedded_sdk_persistence_coverage": _normalize_embedded_sdk_persistence_coverage(
            embedded_persistence_coverage
        ),
        "worker_ownership_store_mode_coverage": _normalize_worker_ownership_store_mode_coverage(
            worker_ownership_coverage
        ),
        "checkpoint_resume_cursor_coverage": _normalize_checkpoint_resume_cursor_coverage(
            checkpoint_cursor_coverage
        ),
        "child_executor_promotion_gate_coverage": _normalize_child_executor_promotion_gate_coverage(
            child_executor_gate_coverage
        ),
        "child_executor_execution_prerequisites_coverage": _normalize_child_executor_execution_prerequisites_coverage(
            child_executor_prerequisites_coverage
        ),
        "child_executor_dispatch_coverage": _normalize_child_executor_dispatch_coverage(
            child_executor_dispatch_coverage
        ),
        "recovery_retry_evidence_coverage": _normalize_recovery_retry_evidence_coverage(
            recovery_retry_coverage
        ),
        "recovery_retry_scheduler_coverage": _normalize_recovery_retry_scheduler_coverage(
            recovery_retry_scheduler_coverage
        ),
        "durable_recovery_loader_coverage": _normalize_durable_recovery_loader_coverage(
            durable_recovery_loader_coverage
        ),
        "child_executor_dispatcher_coverage": _normalize_child_executor_dispatcher_coverage(
            child_executor_dispatcher_coverage
        ),
        "child_executor_dispatch_result_handoff_coverage": (
            _normalize_child_executor_dispatch_result_handoff_coverage(
                child_executor_dispatch_result_handoff_coverage
            )
        ),
        "child_executor_dispatch_result_retry_audit_coverage": (
            _normalize_child_executor_dispatch_result_retry_audit_coverage(
                child_executor_dispatch_result_retry_audit_coverage
            )
        ),
        "child_executor_sandbox_backend_binding_coverage": (
            _normalize_child_executor_sandbox_backend_binding_coverage(
                child_executor_sandbox_backend_binding_coverage
            )
        ),
        "subagent_lane_query_detail_coverage": _normalize_subagent_lane_query_detail_coverage(
            subagent_lane_detail_coverage
        ),
    }


def _normalize_runtime_contract_artifact_schema(artifact_schema: object) -> dict:
    if not isinstance(artifact_schema, dict):
        return {
            "contract_version": "",
            "overall_status": "",
            "summary_required_fields": [],
            "summary_missing_fields": [],
        }
    return {
        "contract_version": str(artifact_schema.get("contract_version") or "").strip(),
        "overall_status": str(artifact_schema.get("overall_status") or "").strip(),
        "summary_required_fields": [
            str(field_name)
            for field_name in artifact_schema.get("summary_required_fields") or []
            if str(field_name or "").strip()
        ],
        "summary_missing_fields": [
            str(field_name)
            for field_name in artifact_schema.get("summary_missing_fields") or []
            if str(field_name or "").strip()
        ],
    }


def _normalize_approval_lifecycle_recovery_coverage(coverage: dict) -> dict:
    replayed_submission_status = str(coverage.get("replayed_submission_status") or "").strip()
    ignored_submission_status = str(coverage.get("ignored_submission_status") or "").strip()
    resolved_recovery_reason = str(coverage.get("resolved_recovery_reason") or "").strip()
    return {
        "alignment_smoke": (
            bool(coverage.get("alignment_smoke"))
            and replayed_submission_status == "replayed"
            and ignored_submission_status == "ignored"
            and resolved_recovery_reason == "already_resolved"
        ),
        "replayed_submission_status": replayed_submission_status,
        "ignored_submission_status": ignored_submission_status,
        "resolved_recovery_reason": resolved_recovery_reason,
    }


def _normalize_approved_tool_execution_coverage(coverage: dict) -> dict:
    return {
        "bridge_smoke": bool(coverage.get("bridge_smoke")),
        "approved_tool_call_count": _coerce_runtime_contract_non_negative_int(
            coverage.get("approved_tool_call_count")
        ),
        "approved_policy_original_status": str(coverage.get("approved_policy_original_status") or "").strip(),
        "approved_policy_override_status": str(coverage.get("approved_policy_override_status") or "").strip(),
        "deny_override_status": str(coverage.get("deny_override_status") or "").strip(),
        "deny_tool_call_count": _coerce_runtime_contract_non_negative_int(coverage.get("deny_tool_call_count")),
    }


def _normalize_sdk_tool_runtime_execution_coverage(coverage: dict) -> dict:
    auto_tool_call_count = _coerce_runtime_contract_non_negative_int(coverage.get("auto_tool_call_count"))
    auto_tool_history_count = _coerce_runtime_contract_non_negative_int(coverage.get("auto_tool_history_count"))
    approved_tool_call_count = _coerce_runtime_contract_non_negative_int(coverage.get("approved_tool_call_count"))
    approved_policy_original_status = str(coverage.get("approved_policy_original_status") or "").strip()
    approved_policy_override_status = str(coverage.get("approved_policy_override_status") or "").strip()
    deny_override_status = str(coverage.get("deny_override_status") or "").strip()
    deny_tool_call_count = _coerce_runtime_contract_non_negative_int(coverage.get("deny_tool_call_count"))
    bridge_smoke = (
        bool(coverage.get("bridge_smoke"))
        and auto_tool_call_count == 1
        and auto_tool_history_count == 1
        and approved_tool_call_count == 1
        and approved_policy_original_status == "approval_required"
        and approved_policy_override_status == "approved"
        and deny_override_status == "policy_denied"
        and deny_tool_call_count == 0
    )
    return {
        "bridge_smoke": bridge_smoke,
        "auto_tool_call_count": auto_tool_call_count,
        "auto_tool_history_count": auto_tool_history_count,
        "approved_tool_call_count": approved_tool_call_count,
        "approved_policy_original_status": approved_policy_original_status,
        "approved_policy_override_status": approved_policy_override_status,
        "deny_override_status": deny_override_status,
        "deny_tool_call_count": deny_tool_call_count,
    }


def _normalize_embedded_sdk_persistence_coverage(coverage: dict) -> dict:
    memory_posture = str(coverage.get("memory_posture") or "").strip()
    durable_posture = str(coverage.get("durable_posture") or "").strip()
    degraded_posture = str(coverage.get("degraded_posture") or "").strip()
    memory_block_reason = str(coverage.get("memory_cross_process_block_reason") or "").strip()
    degraded_block_reason = str(coverage.get("degraded_cross_process_block_reason") or "").strip()
    durable_cross_process_candidate = bool(coverage.get("durable_cross_process_candidate"))
    production_gate_contract_version = str(
        coverage.get("production_recovery_gate_contract_version") or ""
    ).strip()
    production_gate_status = str(coverage.get("production_recovery_gate_status") or "").strip()
    production_gate_missing_sections = (
        coverage.get("production_recovery_gate_missing_sections")
        if isinstance(coverage.get("production_recovery_gate_missing_sections"), list)
        else []
    )
    production_default_enabled = bool(coverage.get("production_recovery_default_enabled"))
    worker_ownership_gate_contract_version = str(
        coverage.get("production_recovery_worker_ownership_gate_contract_version") or ""
    ).strip()
    worker_ownership_gate_status = str(
        coverage.get("production_recovery_worker_ownership_gate_status") or ""
    ).strip()
    worker_ownership_default_enabled = bool(
        coverage.get("production_recovery_worker_ownership_default_enabled")
    )
    worker_ownership_missing_sections = (
        coverage.get("production_recovery_worker_ownership_missing_sections")
        if isinstance(coverage.get("production_recovery_worker_ownership_missing_sections"), list)
        else []
    )
    persistence_smoke = (
        bool(coverage.get("persistence_smoke"))
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
        "contract_version": str(coverage.get("contract_version") or "").strip(),
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


def _normalize_worker_ownership_store_mode_coverage(coverage: dict) -> dict:
    default_mode = str(coverage.get("default_mode") or "").strip()
    default_mode_source = str(coverage.get("default_mode_source") or "").strip()
    default_adapter_kind = str(coverage.get("default_adapter_kind") or "").strip()
    default_durable = bool(coverage.get("default_durable"))
    configurable_knob_present = bool(coverage.get("configurable_knob_present"))
    hot_reloadable_knob_present = bool(coverage.get("hot_reloadable_knob_present"))
    strict_mode_status = str(coverage.get("strict_mode_status") or "").strip()
    fallback_mode_status = str(coverage.get("fallback_mode_status") or "").strip()
    mode_smoke = (
        bool(coverage.get("mode_smoke"))
        and default_mode == "memory_only"
        and default_mode_source == "default"
        and default_adapter_kind == "in_memory"
        and not default_durable
        and configurable_knob_present
        and hot_reloadable_knob_present
        and strict_mode_status == "sqlalchemy_durable"
        and fallback_mode_status == "fallback_to_memory"
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
    }


def _normalize_checkpoint_resume_cursor_coverage(coverage: dict) -> dict:
    checkpoint_status = str(coverage.get("checkpoint_status") or "").strip()
    checkpoint_kind = str(coverage.get("checkpoint_kind") or "").strip()
    cursor_status = str(coverage.get("cursor_status") or "").strip()
    cursor_entrypoint = str(coverage.get("cursor_entrypoint") or "").strip()
    cursor_recovery_reason = str(coverage.get("cursor_recovery_reason") or "").strip()
    cursor_smoke = (
        bool(coverage.get("cursor_smoke"))
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


def _normalize_child_executor_promotion_gate_coverage(coverage: dict) -> dict:
    contract_version = str(coverage.get("contract_version") or "").strip()
    gate_status = str(coverage.get("gate_status") or "").strip()
    allowed = bool(coverage.get("allowed"))
    failure_reason = str(coverage.get("failure_reason") or "").strip()
    blocker_count = _coerce_runtime_contract_non_negative_int(coverage.get("blocker_count"))
    recommended_next_step = str(coverage.get("recommended_next_step") or "").strip()
    gate_smoke = (
        bool(coverage.get("gate_smoke"))
        and bool(contract_version)
        and gate_status == "blocked"
        and not allowed
        and bool(failure_reason)
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


def _normalize_child_executor_execution_prerequisites_coverage(coverage: dict) -> dict:
    contract_version = str(coverage.get("contract_version") or "").strip()
    overall_status = str(coverage.get("overall_status") or "").strip()
    ready = bool(coverage.get("ready"))
    requirement_count = _coerce_runtime_contract_non_negative_int(coverage.get("requirement_count"))
    missing_requirement_count = _coerce_runtime_contract_non_negative_int(
        coverage.get("missing_requirement_count")
    )
    raw_missing_requirements = coverage.get("missing_requirements")
    missing_requirements = [
        str(item).strip()
        for item in (raw_missing_requirements if isinstance(raw_missing_requirements, list) else [])
        if str(item or "").strip()
    ]
    raw_budget_missing_sections = coverage.get("context_budget_policy_missing_sections")
    context_budget_policy_missing_sections = [
        str(item).strip()
        for item in (raw_budget_missing_sections if isinstance(raw_budget_missing_sections, list) else [])
        if str(item or "").strip()
    ]
    raw_merge_handoff_missing_sections = coverage.get("merge_handoff_missing_sections")
    merge_handoff_missing_sections = [
        str(item).strip()
        for item in (raw_merge_handoff_missing_sections if isinstance(raw_merge_handoff_missing_sections, list) else [])
        if str(item or "").strip()
    ]
    prerequisites_smoke = (
        bool(coverage.get("prerequisites_smoke"))
        and bool(contract_version)
        and overall_status == "blocked"
        and not ready
        and requirement_count > 0
        and missing_requirement_count == len(missing_requirements)
    )
    return {
        "prerequisites_smoke": prerequisites_smoke,
        "contract_version": contract_version,
        "overall_status": overall_status,
        "ready": ready,
        "requirement_count": requirement_count,
        "missing_requirement_count": missing_requirement_count,
        "missing_requirements": missing_requirements,
        "context_budget_policy_status": str(coverage.get("context_budget_policy_status") or "").strip(),
        "context_budget_policy_ready": bool(coverage.get("context_budget_policy_ready")),
        "context_budget_policy_missing": bool(coverage.get("context_budget_policy_missing")),
        "context_budget_policy_missing_sections": context_budget_policy_missing_sections,
        "context_budget_policy_source": str(coverage.get("context_budget_policy_source") or "").strip(),
        "opt_in_context_budget_policy_status": str(
            coverage.get("opt_in_context_budget_policy_status") or ""
        ).strip(),
        "opt_in_context_budget_policy_ready": bool(
            coverage.get("opt_in_context_budget_policy_ready")
        ),
        "opt_in_context_budget_policy_source": str(
            coverage.get("opt_in_context_budget_policy_source") or ""
        ).strip(),
        "opt_in_context_budget_policy_max_turns": _coerce_runtime_contract_non_negative_int(
            coverage.get("opt_in_context_budget_policy_max_turns")
        ),
        "merge_handoff_status": str(coverage.get("merge_handoff_status") or "").strip(),
        "merge_handoff_ready": bool(coverage.get("merge_handoff_ready")),
        "merge_handoff_missing": bool(coverage.get("merge_handoff_missing")),
        "merge_handoff_missing_sections": merge_handoff_missing_sections,
        "merge_handoff_strategy": str(coverage.get("merge_handoff_strategy") or "").strip(),
        "merge_handoff_source": str(coverage.get("merge_handoff_source") or "").strip(),
        "opt_in_merge_handoff_status": str(coverage.get("opt_in_merge_handoff_status") or "").strip(),
        "opt_in_merge_handoff_ready": bool(coverage.get("opt_in_merge_handoff_ready")),
        "opt_in_merge_handoff_strategy": str(coverage.get("opt_in_merge_handoff_strategy") or "").strip(),
        "opt_in_merge_handoff_source": str(coverage.get("opt_in_merge_handoff_source") or "").strip(),
    }


def _normalize_child_executor_dispatch_coverage(coverage: dict) -> dict:
    contract_version = str(coverage.get("contract_version") or "").strip()
    overall_status = str(coverage.get("overall_status") or "").strip()
    dispatch_ready = bool(coverage.get("dispatch_ready"))
    will_dispatch = bool(coverage.get("will_dispatch"))
    backend_dispatch_ready = bool(coverage.get("backend_dispatch_ready"))
    relationship_seam_preserved = bool(coverage.get("relationship_seam_preserved"))
    blocker_count = _coerce_runtime_contract_non_negative_int(coverage.get("blocker_count"))
    recommended_next_step = str(coverage.get("recommended_next_step") or "").strip()
    dispatch_attempt_handoff_status = str(
        coverage.get("dispatch_attempt_handoff_status") or ""
    ).strip()
    dispatch_attempt_handoff_ready = bool(coverage.get("dispatch_attempt_handoff_ready"))
    opt_in_dispatch_attempt_handoff_ready = bool(
        coverage.get("opt_in_dispatch_attempt_handoff_ready")
    )
    opt_in_attempt_validation_ready = bool(
        coverage.get("opt_in_attempt_validation_ready")
    )
    dispatch_smoke = (
        bool(coverage.get("dispatch_smoke"))
        and bool(contract_version)
        and overall_status == "blocked"
        and not dispatch_ready
        and not will_dispatch
        and not backend_dispatch_ready
        and relationship_seam_preserved
        and blocker_count > 0
        and dispatch_attempt_handoff_status == "blocked"
        and not dispatch_attempt_handoff_ready
        and opt_in_dispatch_attempt_handoff_ready
        and opt_in_attempt_validation_ready
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
        "dispatch_attempt_handoff_status": dispatch_attempt_handoff_status,
        "dispatch_attempt_handoff_ready": dispatch_attempt_handoff_ready,
        "opt_in_dispatch_attempt_handoff_ready": opt_in_dispatch_attempt_handoff_ready,
        "opt_in_attempt_validation_ready": opt_in_attempt_validation_ready,
        "recommended_next_step": recommended_next_step,
    }


def _normalize_recovery_retry_evidence_coverage(coverage: dict) -> dict:
    contract_version = str(coverage.get("contract_version") or "").strip()
    attempt_number = _coerce_runtime_contract_non_negative_int(coverage.get("attempt_number"))
    max_attempts = _coerce_runtime_contract_non_negative_int(coverage.get("max_attempts"))
    retry_status = str(coverage.get("retry_status") or "").strip()
    retryable = bool(coverage.get("retryable"))
    terminal = bool(coverage.get("terminal"))
    recovery_reason = str(coverage.get("recovery_reason") or "").strip()
    idempotency_key_present = bool(coverage.get("idempotency_key_present"))
    retry_smoke = (
        bool(coverage.get("retry_smoke"))
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


def _normalize_recovery_retry_scheduler_coverage(coverage: dict) -> dict:
    contract_version = str(coverage.get("contract_version") or "").strip()
    default_status = str(coverage.get("default_status") or "").strip()
    default_eligible = bool(coverage.get("default_eligible"))
    default_will_execute = bool(coverage.get("default_will_execute"))
    enabled_status = str(coverage.get("enabled_status") or "").strip()
    enabled_will_execute = bool(coverage.get("enabled_will_execute"))
    latest_operation_status = str(coverage.get("latest_operation_status") or "").strip()
    attempt_number = _coerce_runtime_contract_non_negative_int(coverage.get("attempt_number"))
    retry_status = str(coverage.get("retry_status") or "").strip()
    recovery_reason = str(coverage.get("recovery_reason") or "").strip()
    previous_operation_id_present = bool(coverage.get("previous_operation_id_present"))
    idempotency_key_present = bool(coverage.get("idempotency_key_present"))
    scheduler_smoke = (
        bool(coverage.get("scheduler_smoke"))
        and contract_version == "phase-ii-recovery-retry-scheduler-v1"
        and default_status == "disabled"
        and default_eligible
        and not default_will_execute
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
        "enabled_status": enabled_status,
        "enabled_will_execute": enabled_will_execute,
        "latest_operation_status": latest_operation_status,
        "attempt_number": attempt_number,
        "retry_status": retry_status,
        "recovery_reason": recovery_reason,
        "previous_operation_id_present": previous_operation_id_present,
        "idempotency_key_present": idempotency_key_present,
    }


def _normalize_durable_recovery_loader_coverage(coverage: dict) -> dict:
    contract_version = str(coverage.get("contract_version") or "").strip()
    loader_status = str(coverage.get("loader_status") or "").strip()
    loader_ready = bool(coverage.get("loader_ready"))
    loader_recovery_reason = str(coverage.get("loader_recovery_reason") or "").strip()
    all_bindings_resolved = bool(coverage.get("all_bindings_resolved"))
    missing_recovery_reason = str(coverage.get("missing_recovery_reason") or "").strip()
    unsafe_recovery_reason = str(coverage.get("unsafe_recovery_reason") or "").strip()
    executes_recovery = bool(coverage.get("executes_recovery"))
    deserializes_callables = bool(coverage.get("deserializes_callables"))
    loader_smoke = (
        bool(coverage.get("loader_smoke"))
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


def _normalize_child_executor_dispatcher_coverage(coverage: dict) -> dict:
    contract_version = str(coverage.get("contract_version") or "").strip()
    default_status = str(coverage.get("default_status") or "").strip()
    default_blocked_reason = str(coverage.get("default_blocked_reason") or "").strip()
    default_will_dispatch = bool(coverage.get("default_will_dispatch"))
    blocked_reason = str(coverage.get("blocked_reason") or "").strip()
    blocked_will_dispatch = bool(coverage.get("blocked_will_dispatch"))
    enabled_status = str(coverage.get("enabled_status") or "").strip()
    enabled_will_dispatch = bool(coverage.get("enabled_will_dispatch"))
    backend_result_status = str(coverage.get("backend_result_status") or "").strip()
    backend_invocation_count = _coerce_runtime_contract_non_negative_int(
        coverage.get("backend_invocation_count")
    )
    dispatcher_smoke = (
        bool(coverage.get("dispatcher_smoke"))
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


def _normalize_child_executor_dispatch_result_handoff_coverage(coverage: dict) -> dict:
    contract_version = str(coverage.get("contract_version") or "").strip()
    ready_handoff_status = str(coverage.get("ready_handoff_status") or "").strip()
    ready_handoff_ready = bool(coverage.get("ready_handoff_ready"))
    ready_output_ref_present = bool(coverage.get("ready_output_ref_present"))
    ready_audit_evidence_present = bool(coverage.get("ready_audit_evidence_present"))
    ready_backend_result_schema_valid = bool(
        coverage.get("ready_backend_result_schema_valid")
    )
    ready_parent_merge_performed = bool(coverage.get("ready_parent_merge_performed"))
    ready_merge_authorization = bool(coverage.get("ready_merge_authorization"))
    ready_retry_scheduled = bool(coverage.get("ready_retry_scheduled"))
    ready_production_dispatch_authorized = bool(
        coverage.get("ready_production_dispatch_authorized")
    )
    blocked_handoff_status = str(coverage.get("blocked_handoff_status") or "").strip()
    blocked_dispatcher_reason = str(coverage.get("blocked_dispatcher_reason") or "").strip()
    blocked_missing_sections = [
        str(item)
        for item in coverage.get("blocked_missing_sections") or []
        if str(item or "").strip()
    ]
    malformed_handoff_status = str(coverage.get("malformed_handoff_status") or "").strip()
    malformed_missing_sections = [
        str(item)
        for item in coverage.get("malformed_missing_sections") or []
        if str(item or "").strip()
    ]
    result_handoff_smoke = (
        bool(coverage.get("result_handoff_smoke"))
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


def _normalize_child_executor_dispatch_result_retry_audit_coverage(coverage: dict) -> dict:
    contract_version = str(coverage.get("contract_version") or "").strip()
    success_policy_status = str(coverage.get("success_policy_status") or "").strip()
    success_retry_policy_status = str(coverage.get("success_retry_policy_status") or "").strip()
    success_retry_scheduled = bool(coverage.get("success_retry_scheduled"))
    success_will_retry = bool(coverage.get("success_will_retry"))
    retryable_policy_status = str(coverage.get("retryable_policy_status") or "").strip()
    retryable_retry_policy_status = str(coverage.get("retryable_retry_policy_status") or "").strip()
    retryable_audit_evidence_present = bool(coverage.get("retryable_audit_evidence_present"))
    retryable_idempotency_evidence_present = bool(
        coverage.get("retryable_idempotency_evidence_present")
    )
    retryable_scheduler_required = bool(coverage.get("retryable_scheduler_required"))
    retryable_retry_reason = str(coverage.get("retryable_retry_reason") or "").strip()
    retryable_retry_scheduled = bool(coverage.get("retryable_retry_scheduled"))
    retryable_will_retry = bool(coverage.get("retryable_will_retry"))
    terminal_policy_status = str(coverage.get("terminal_policy_status") or "").strip()
    terminal_retry_policy_status = str(coverage.get("terminal_retry_policy_status") or "").strip()
    terminal_reason = str(coverage.get("terminal_reason") or "").strip()
    terminal_will_retry = bool(coverage.get("terminal_will_retry"))
    missing_idempotency_status = str(coverage.get("missing_idempotency_status") or "").strip()
    missing_idempotency_missing_sections = [
        str(item)
        for item in coverage.get("missing_idempotency_missing_sections") or []
        if str(item or "").strip()
    ]
    missing_idempotency_retry_scheduled = bool(
        coverage.get("missing_idempotency_retry_scheduled")
    )
    retry_audit_smoke = (
        bool(coverage.get("retry_audit_smoke"))
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


def _normalize_child_executor_sandbox_backend_binding_coverage(coverage: dict) -> dict:
    contract_version = str(coverage.get("contract_version") or "").strip()
    default_status = str(coverage.get("default_status") or "").strip()
    default_missing_sections = [
        str(item)
        for item in coverage.get("default_missing_sections") or []
        if str(item or "").strip()
    ]
    missing_callable_status = str(coverage.get("missing_callable_status") or "").strip()
    missing_callable_missing_sections = [
        str(item)
        for item in coverage.get("missing_callable_missing_sections") or []
        if str(item or "").strip()
    ]
    ready_status = str(coverage.get("ready_status") or "").strip()
    ready_dispatcher_binding_ready = bool(coverage.get("ready_dispatcher_binding_ready"))
    ready_attempt_envelope_supported = bool(coverage.get("ready_attempt_envelope_supported"))
    ready_audit_idempotency_ready = bool(coverage.get("ready_audit_idempotency_ready"))
    ready_will_dispatch = bool(coverage.get("ready_will_dispatch"))
    dispatch_contract_binding_status = str(
        coverage.get("dispatch_contract_binding_status") or ""
    ).strip()
    dispatch_contract_binding_ready = bool(coverage.get("dispatch_contract_binding_ready"))
    dispatch_contract_ready = bool(coverage.get("dispatch_contract_ready"))
    dispatch_contract_will_dispatch = bool(coverage.get("dispatch_contract_will_dispatch"))
    binding_smoke = (
        bool(coverage.get("binding_smoke"))
        and contract_version == "phase-ii-child-executor-sandbox-backend-binding-v1"
        and default_status == "blocked"
        and "explicit_binding" in default_missing_sections
        and missing_callable_status == "blocked"
        and "dispatcher_backend_adapter" in missing_callable_missing_sections
        and ready_status == "ready"
        and ready_dispatcher_binding_ready
        and ready_attempt_envelope_supported
        and ready_audit_idempotency_ready
        and not ready_will_dispatch
        and dispatch_contract_binding_status == "ready"
        and dispatch_contract_binding_ready
        and dispatch_contract_ready
        and not dispatch_contract_will_dispatch
    )
    return {
        "binding_smoke": binding_smoke,
        "contract_version": contract_version,
        "default_status": default_status,
        "default_missing_sections": default_missing_sections,
        "missing_callable_status": missing_callable_status,
        "missing_callable_missing_sections": missing_callable_missing_sections,
        "ready_status": ready_status,
        "ready_dispatcher_binding_ready": ready_dispatcher_binding_ready,
        "ready_attempt_envelope_supported": ready_attempt_envelope_supported,
        "ready_audit_idempotency_ready": ready_audit_idempotency_ready,
        "ready_will_dispatch": ready_will_dispatch,
        "dispatch_contract_binding_status": dispatch_contract_binding_status,
        "dispatch_contract_binding_ready": dispatch_contract_binding_ready,
        "dispatch_contract_ready": dispatch_contract_ready,
        "dispatch_contract_will_dispatch": dispatch_contract_will_dispatch,
    }


def _normalize_subagent_lane_query_detail_coverage(coverage: dict) -> dict:
    return {
        "detail_smoke": bool(coverage.get("detail_smoke")),
        "contract_version": str(coverage.get("contract_version") or "").strip(),
        "recording_state": str(coverage.get("recording_state") or "").strip(),
        "stage_count": _coerce_runtime_contract_non_negative_int(coverage.get("stage_count")),
        "recent_event_count": _coerce_runtime_contract_non_negative_int(coverage.get("recent_event_count")),
    }


def _coerce_runtime_contract_non_negative_int(value: object) -> int:
    try:
        normalized = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return normalized if normalized >= 0 else 0


def _record_doctor_timeline(
    *,
    db: Session,
    conversation_id: int | None,
    scope: str,
    params: dict,
    report: dict,
) -> dict:
    trace_service = get_run_trace_service(db)
    snapshot_ref = trace_service.build_snapshot_ref(
        source="doctor",
        event_type="doctor_run_completed",
        conversation_id=conversation_id,
    )
    base_payload = {
        "scope": scope,
        "conversation_id": conversation_id,
        "params": dict(params or {}),
        "snapshot_ref": snapshot_ref,
    }
    started_trace = trace_service.append_latest_active_item_trace(
        user_id=None,
        conversation_id=conversation_id,
        source="doctor",
        event_type="doctor_run_started",
        summary=f"Doctor `{scope}` 诊断已开始",
        detail="已发起一次框架诊断执行。",
        severity="info",
        payload=base_payload,
    )
    started_audit = trace_service.append_latest_active_item_audit(
        user_id=None,
        conversation_id=conversation_id,
        event_type="doctor_run_started",
        content=f"Doctor `{scope}` 诊断已开始",
        payload=base_payload,
    )

    result_payload = {
        **base_payload,
        "status": report.get("status"),
        "exit_code": report.get("exit_code"),
        "gate_passed": report.get("gate_passed"),
        "non_closed_action_count": report.get("non_closed_action_count"),
        "score": report.get("score"),
    }
    framework_adapter_check = ((report.get("checks") or {}).get("framework_adapters") or {})
    if framework_adapter_check:
        result_payload["framework_adapters"] = {
            "status": framework_adapter_check.get("status"),
            "details": list(framework_adapter_check.get("details") or []),
            "remediation_actions": list(framework_adapter_check.get("remediation_actions") or []),
        }
        if framework_adapter_check.get("latest_external_pilot_failure"):
            result_payload["framework_adapters"]["latest_external_pilot_failure"] = dict(
                framework_adapter_check.get("latest_external_pilot_failure") or {}
            )
        if framework_adapter_check.get("external_pilot_failure_counts"):
            result_payload["framework_adapters"]["external_pilot_failure_counts"] = dict(
                framework_adapter_check.get("external_pilot_failure_counts") or {}
            )
    completed_trace = trace_service.append_latest_active_item_trace(
        user_id=None,
        conversation_id=conversation_id,
        source="doctor",
        event_type="doctor_run_completed",
        summary=f"Doctor `{scope}` 诊断已完成",
        detail=f"status={report.get('status')} exit_code={report.get('exit_code')}",
        severity="success" if int(report.get("exit_code") or 0) == 0 else "warning",
        payload=result_payload,
    )
    completed_audit = trace_service.append_latest_active_item_audit(
        user_id=None,
        conversation_id=conversation_id,
        event_type="doctor_run_completed",
        content=f"Doctor `{scope}` 诊断已完成",
        payload=result_payload,
    )

    gate_trace = False
    gate_audit = False
    gate_failed_dedupe_key = (
        f"doctor_gate_failed:{conversation_id}:{scope}:"
        f"{report.get('exit_code')}:{report.get('non_closed_action_count')}"
    )
    result_payload["dedupe_key"] = gate_failed_dedupe_key
    gate_failed_dedupe_source = ""
    if report.get("gate_passed") is False or int(report.get("exit_code") or 0) > 0:
        if trace_service.has_runtime_trace_dedupe_key(
            user_id=None,
            conversation_id=conversation_id,
            source="doctor",
            event_type="doctor_gate_failed",
            dedupe_key=gate_failed_dedupe_key,
        ):
            gate_failed_dedupe_source = "persisted_trace"
        else:
            gate_trace = trace_service.append_latest_active_item_trace(
                user_id=None,
                conversation_id=conversation_id,
                source="doctor",
                event_type="doctor_gate_failed",
                summary=f"Doctor `{scope}` 门禁未通过",
                detail=(
                    f"exit_code={report.get('exit_code')} "
                    f"non_closed_action_count={report.get('non_closed_action_count')}"
                ).strip(),
                severity="warning",
                payload=result_payload,
            )
            gate_audit = trace_service.append_latest_active_item_audit(
                user_id=None,
                conversation_id=conversation_id,
                event_type="doctor_gate_failed",
                content=f"Doctor `{scope}` 门禁未通过",
                payload=result_payload,
            )

    return {
        "trace_started": started_trace,
        "audit_started": started_audit,
        "trace_completed": completed_trace,
        "audit_completed": completed_audit,
        "trace_gate_failed": gate_trace,
        "audit_gate_failed": gate_audit,
        "gate_failed_dedupe_key": gate_failed_dedupe_key,
        "gate_failed_dedupe_source": gate_failed_dedupe_source,
        "conversation_id": conversation_id,
        "snapshot_ref": snapshot_ref,
    }


def _record_runtime_contract_gate_timeline(
    *,
    db: Session,
    conversation_id: int | None,
    plan_id: int | None,
    item_id: int | None,
    runtime_contract_gate: dict,
) -> dict:
    gate = dict(runtime_contract_gate or {})
    failed_checks = [
        dict(check)
        for check in (gate.get("checks") or [])
        if isinstance(check, dict) and not bool(check.get("ok"))
    ]
    raw_runtime_contract_summary = gate.get("runtime_contract_summary")
    runtime_contract_summary = _normalize_runtime_contract_gate_summary(raw_runtime_contract_summary)
    runtime_contract_artifact_schema = _normalize_runtime_contract_artifact_schema(
        gate.get("runtime_contract_artifact_schema")
    )
    recording = {
        "conversation_id": conversation_id,
        "plan_id": plan_id,
        "item_id": item_id,
        "trace_written": False,
        "reason": "",
        "snapshot_ref": None,
    }
    if str(gate.get("overall_status") or "").strip() != "degraded":
        recording["reason"] = "runtime_contract_gate_not_degraded"
        return recording
    if conversation_id is None and plan_id is None and item_id is None:
        recording["reason"] = "runtime_context_missing"
        return recording

    fingerprint = _build_runtime_contract_gate_trace_fingerprint(
        conversation_id=conversation_id,
        plan_id=plan_id,
        item_id=item_id,
        runtime_contract_gate=gate,
    )
    dedupe_key = f"runtime_contract_gate_degraded:{fingerprint}"
    recording["fingerprint"] = fingerprint
    recording["dedupe_key"] = dedupe_key
    if fingerprint in _RUNTIME_CONTRACT_GATE_TRACE_FINGERPRINTS:
        recording["reason"] = "duplicate_runtime_contract_gate_trace"
        recording["dedupe_source"] = "memory"
        return recording

    trace_service = get_run_trace_service(db)
    if trace_service.has_runtime_trace_dedupe_key(
        user_id=None,
        conversation_id=conversation_id,
        plan_id=plan_id,
        item_id=item_id,
        source="runtime_contract",
        event_type="runtime_contract_gate_degraded",
        dedupe_key=dedupe_key,
    ) or trace_service.has_runtime_trace_fingerprint(
        user_id=None,
        conversation_id=conversation_id,
        plan_id=plan_id,
        item_id=item_id,
        source="runtime_contract",
        event_type="runtime_contract_gate_degraded",
        fingerprint=fingerprint,
    ):
        _RUNTIME_CONTRACT_GATE_TRACE_FINGERPRINTS.add(fingerprint)
        recording["reason"] = "duplicate_runtime_contract_gate_trace"
        recording["dedupe_source"] = "persisted_trace"
        return recording

    snapshot_ref = trace_service.build_snapshot_ref(
        source="runtime_contract",
        event_type="runtime_contract_gate_degraded",
        conversation_id=conversation_id,
        generated_at=gate.get("generated_at"),
    )
    payload = {
        "snapshot_ref": snapshot_ref,
        "contract_version": gate.get("contract_version"),
        "overall_status": gate.get("overall_status"),
        "available": bool(gate.get("available")),
        "generated_at": gate.get("generated_at"),
        "report_path": gate.get("report_path"),
        "check_count": int(gate.get("check_count") or 0),
        "failed_check_count": int(gate.get("failed_check_count") or len(failed_checks)),
        "failure_reason": gate.get("failure_reason") or "",
        "runtime_contract_summary": runtime_contract_summary,
        "runtime_contract_artifact_schema": runtime_contract_artifact_schema,
        "failed_checks": failed_checks,
        "fingerprint": fingerprint,
        "dedupe_key": dedupe_key,
    }
    approval_lifecycle_label = _format_runtime_contract_approval_lifecycle_label(
        raw_runtime_contract_summary,
        runtime_contract_summary,
    )
    approved_tool_label = _format_runtime_contract_coverage_label(
        raw_runtime_contract_summary,
        runtime_contract_summary,
        coverage_name="approved_tool_execution_coverage",
        smoke_field="bridge_smoke",
    )
    sdk_tool_label = _format_runtime_contract_coverage_label(
        raw_runtime_contract_summary,
        runtime_contract_summary,
        coverage_name="sdk_tool_runtime_execution_coverage",
        smoke_field="bridge_smoke",
    )
    embedded_persistence_label = _format_runtime_contract_coverage_label(
        raw_runtime_contract_summary,
        runtime_contract_summary,
        coverage_name="embedded_sdk_persistence_coverage",
        smoke_field="persistence_smoke",
    )
    worker_ownership_label = _format_runtime_contract_coverage_label(
        raw_runtime_contract_summary,
        runtime_contract_summary,
        coverage_name="worker_ownership_store_mode_coverage",
        smoke_field="mode_smoke",
    )
    child_executor_gate_label = _format_runtime_contract_coverage_label(
        raw_runtime_contract_summary,
        runtime_contract_summary,
        coverage_name="child_executor_promotion_gate_coverage",
        smoke_field="gate_smoke",
    )
    child_executor_prerequisites_label = _format_runtime_contract_coverage_label(
        raw_runtime_contract_summary,
        runtime_contract_summary,
        coverage_name="child_executor_execution_prerequisites_coverage",
        smoke_field="prerequisites_smoke",
    )
    child_executor_dispatch_label = _format_runtime_contract_coverage_label(
        raw_runtime_contract_summary,
        runtime_contract_summary,
        coverage_name="child_executor_dispatch_coverage",
        smoke_field="dispatch_smoke",
    )
    checkpoint_cursor_label = _format_runtime_contract_checkpoint_cursor_label(
        raw_runtime_contract_summary,
        runtime_contract_summary,
    )
    recovery_retry_label = _format_runtime_contract_recovery_retry_label(
        raw_runtime_contract_summary,
        runtime_contract_summary,
    )
    recovery_retry_scheduler_label = _format_runtime_contract_recovery_retry_scheduler_label(
        raw_runtime_contract_summary,
        runtime_contract_summary,
    )
    durable_loader_label = _format_runtime_contract_coverage_label(
        raw_runtime_contract_summary,
        runtime_contract_summary,
        coverage_name="durable_recovery_loader_coverage",
        smoke_field="loader_smoke",
    )
    child_executor_dispatcher_label = _format_runtime_contract_child_executor_dispatcher_label(
        raw_runtime_contract_summary,
        runtime_contract_summary,
    )
    child_executor_result_handoff_label = _format_runtime_contract_coverage_label(
        raw_runtime_contract_summary,
        runtime_contract_summary,
        coverage_name="child_executor_dispatch_result_handoff_coverage",
        smoke_field="result_handoff_smoke",
    )
    child_executor_retry_audit_label = _format_runtime_contract_coverage_label(
        raw_runtime_contract_summary,
        runtime_contract_summary,
        coverage_name="child_executor_dispatch_result_retry_audit_coverage",
        smoke_field="retry_audit_smoke",
    )
    child_executor_sandbox_binding_label = _format_runtime_contract_coverage_label(
        raw_runtime_contract_summary,
        runtime_contract_summary,
        coverage_name="child_executor_sandbox_backend_binding_coverage",
        smoke_field="binding_smoke",
    )
    subagent_detail_label = _format_runtime_contract_coverage_label(
        raw_runtime_contract_summary,
        runtime_contract_summary,
        coverage_name="subagent_lane_query_detail_coverage",
        smoke_field="detail_smoke",
    )
    trace_written = trace_service.append_runtime_trace(
        user_id=None,
        conversation_id=conversation_id,
        plan_id=plan_id,
        item_id=item_id,
        source="runtime_contract",
        event_type="runtime_contract_gate_degraded",
        summary="Runtime contract gate degraded",
        detail=(
            f"failed_check_count={payload['failed_check_count']} "
            f"approval_lifecycle={approval_lifecycle_label} "
            f"approved_tool={approved_tool_label} "
            f"sdk_tool={sdk_tool_label} "
            f"embedded_persistence={embedded_persistence_label} "
            f"worker_ownership={worker_ownership_label} "
            f"child_executor_gate={child_executor_gate_label} "
            f"child_executor_prerequisites={child_executor_prerequisites_label} "
            f"child_executor_dispatch={child_executor_dispatch_label} "
            f"checkpoint_cursor={checkpoint_cursor_label} "
            f"recovery_retry={recovery_retry_label} "
            f"recovery_retry_scheduler={recovery_retry_scheduler_label} "
            f"durable_loader={durable_loader_label} "
            f"child_executor_dispatcher={child_executor_dispatcher_label} "
            f"child_executor_result_handoff={child_executor_result_handoff_label} "
            f"child_executor_retry_audit={child_executor_retry_audit_label} "
            f"child_executor_sandbox_binding={child_executor_sandbox_binding_label} "
            f"subagent_detail={subagent_detail_label}"
        ),
        severity="warning",
        payload=payload,
    )
    recording.update({
        "trace_written": bool(trace_written),
        "reason": "" if trace_written else "trace_target_missing",
        "snapshot_ref": snapshot_ref,
    })
    if trace_written:
        _RUNTIME_CONTRACT_GATE_TRACE_FINGERPRINTS.add(fingerprint)
    return recording


def _format_runtime_contract_approval_lifecycle_label(
    raw_runtime_contract_summary: object,
    runtime_contract_summary: dict,
) -> str:
    if not isinstance(raw_runtime_contract_summary, dict) or not isinstance(runtime_contract_summary, dict):
        return "unknown"
    coverage = runtime_contract_summary.get("approval_lifecycle_recovery_coverage")
    if not isinstance(coverage, dict):
        return "unknown"
    return "covered" if bool(coverage.get("alignment_smoke")) else "missing"


def _format_runtime_contract_checkpoint_cursor_label(
    raw_runtime_contract_summary: object,
    runtime_contract_summary: dict,
) -> str:
    if not isinstance(raw_runtime_contract_summary, dict) or not isinstance(runtime_contract_summary, dict):
        return "unknown"
    coverage = runtime_contract_summary.get("checkpoint_resume_cursor_coverage")
    if not isinstance(coverage, dict):
        return "unknown"
    return "covered" if bool(coverage.get("cursor_smoke")) else "missing"


def _format_runtime_contract_coverage_label(
    raw_runtime_contract_summary: object,
    runtime_contract_summary: dict,
    *,
    coverage_name: str,
    smoke_field: str,
) -> str:
    if not isinstance(raw_runtime_contract_summary, dict) or not isinstance(runtime_contract_summary, dict):
        return "unknown"
    coverage = runtime_contract_summary.get(coverage_name)
    if not isinstance(coverage, dict):
        return "unknown"
    return "covered" if bool(coverage.get(smoke_field)) else "missing"


def _format_runtime_contract_recovery_retry_label(
    raw_runtime_contract_summary: object,
    runtime_contract_summary: dict,
) -> str:
    if not isinstance(raw_runtime_contract_summary, dict) or not isinstance(runtime_contract_summary, dict):
        return "unknown"
    coverage = runtime_contract_summary.get("recovery_retry_evidence_coverage")
    if not isinstance(coverage, dict):
        return "unknown"
    return "covered" if bool(coverage.get("retry_smoke")) else "missing"


def _format_runtime_contract_recovery_retry_scheduler_label(
    raw_runtime_contract_summary: object,
    runtime_contract_summary: dict,
) -> str:
    if not isinstance(raw_runtime_contract_summary, dict) or not isinstance(runtime_contract_summary, dict):
        return "unknown"
    coverage = runtime_contract_summary.get("recovery_retry_scheduler_coverage")
    if not isinstance(coverage, dict):
        return "unknown"
    return "covered" if bool(coverage.get("scheduler_smoke")) else "missing"


def _format_runtime_contract_child_executor_dispatcher_label(
    raw_runtime_contract_summary: object,
    runtime_contract_summary: dict,
) -> str:
    if not isinstance(raw_runtime_contract_summary, dict) or not isinstance(runtime_contract_summary, dict):
        return "unknown"
    coverage = runtime_contract_summary.get("child_executor_dispatcher_coverage")
    if not isinstance(coverage, dict):
        return "unknown"
    return "covered" if bool(coverage.get("dispatcher_smoke")) else "missing"


def _record_governance_action(
    *,
    db: Session,
    conversation_id: int | None,
    source: str,
    event_type: str,
    summary: str,
    detail: str = "",
    severity: str = "info",
    payload: dict | None = None,
) -> dict:
    trace_service = get_run_trace_service(db)
    snapshot_ref = trace_service.build_snapshot_ref(
        source=source,
        event_type=event_type,
        conversation_id=conversation_id,
    )
    payload = {
        **(payload or {}),
        "snapshot_ref": snapshot_ref,
    }
    trace_written = trace_service.append_latest_active_item_trace(
        user_id=None,
        conversation_id=conversation_id,
        source=source,
        event_type=event_type,
        summary=summary,
        detail=detail,
        severity=severity,
        payload=payload,
    )
    audit_written = trace_service.append_latest_active_item_audit(
        user_id=None,
        conversation_id=conversation_id,
        event_type=event_type,
        content=summary,
        payload=payload,
    )
    return {
        "trace_written": trace_written,
        "audit_written": audit_written,
        "conversation_id": conversation_id,
        "snapshot_ref": snapshot_ref,
    }


@router.get("/health/live")
def liveness():
    """Lightweight liveness probe — confirms the process is running."""
    return {"status": "ok"}


@router.get("/health/ready")
def readiness(db: Session = Depends(get_db)):
    """Readiness probe — checks database connectivity."""
    checks = {"database": "ok"}
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
    except Exception as e:
        checks["database"] = f"error: {e}"
        raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": checks})
    return {"status": "ready", "checks": checks}


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """轻量健康检查与启动诊断摘要。"""
    report = get_startup_diagnostics_service().collect_report()
    report = _attach_framework_adapter_runtime_diagnostics(report=report, db=db)
    try:
        failover_summary = get_provider_failover_analytics_service(db).get_summary(window_days=7, limit=500)
        runtime_profile = get_runtime_surface_service().get_runtime_profile()
        thresholds = runtime_profile.get("failover_thresholds") or {}
        medium = float(thresholds.get("medium", 0.2))
        high = float(thresholds.get("high", 0.4))
        switch_rate = float(failover_summary.get("switch_rate", 0.0))
        failover_summary["alert_thresholds"] = {"medium": medium, "high": high}
        failover_summary["alert_level"] = _resolve_failover_alert_level(switch_rate, medium, high)
        report["failover"] = failover_summary
    except Exception as exc:
        report["failover"] = {"status": "unavailable", "error": str(exc)}
    try:
        report["runtime_backend"] = get_scheduler_runtime_diagnostics_service(db).collect_status(limit=20)
    except Exception as exc:
        report["runtime_backend"] = {"status": "unavailable", "error": str(exc)}
    return report


@router.get("/health/cors")
def cors_diagnostics(request: Request):
    """Return effective CORS settings and match result for current request Origin."""
    origin = str(request.headers.get("origin") or "").strip()
    allowed_origins = [str(item).strip().rstrip("/") for item in CORS_ALLOWED_ORIGINS if str(item).strip()]
    origin_regex = str(CORS_ALLOWED_ORIGIN_REGEX or "").strip() or None

    exact_match = origin.rstrip("/") in allowed_origins if origin else False
    regex_match = False
    regex_error = None
    if origin and origin_regex:
        try:
            regex_match = re.fullmatch(origin_regex, origin) is not None
        except re.error as exc:
            regex_error = str(exc)

    return {
        "request_origin": origin or None,
        "allow_credentials": True,
        "configured_allow_origins": allowed_origins,
        "configured_allow_origin_regex": origin_regex,
        "matched_by_exact_origin": exact_match,
        "matched_by_regex": regex_match,
        "is_allowed": bool(exact_match or regex_match),
        "regex_error": regex_error,
        "preflight_headers": {
            "access-control-request-method": request.headers.get("access-control-request-method"),
            "access-control-request-headers": request.headers.get("access-control-request-headers"),
        },
    }


@router.get("/runtime-profile")
def get_runtime_profile(
    conversation_id: int | None = None,
    plan_id: int | None = None,
    item_id: int | None = None,
    query_id: str | None = None,
    run_id: str | None = None,
    parent_run_id: str | None = None,
    child_run_id: str | None = None,
    scheduler_run_id: str | None = None,
    db: Session = Depends(get_db),
):
    """返回当前 demo/runtime 的可配置表面。"""
    profile = get_runtime_surface_service().get_runtime_profile(
        db=db,
        conversation_id=conversation_id,
        plan_id=plan_id,
        item_id=item_id,
        query_id=query_id,
        run_id=run_id,
        parent_run_id=parent_run_id,
        child_run_id=child_run_id,
        scheduler_run_id=scheduler_run_id,
    )
    runtime_contract_gate = profile.get("runtime_contract_gate") or {}
    if isinstance(runtime_contract_gate, dict):
        recording = _record_runtime_contract_gate_timeline(
            db=db,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
            runtime_contract_gate=runtime_contract_gate,
        )
        if recording.get("trace_written") or recording.get("reason"):
            profile["runtime_contract_gate_timeline_recording"] = recording
    return profile


@router.get("/runtime-profile/main-chat-query-detail")
def get_main_chat_query_detail(
    conversation_id: int | None = None,
    plan_id: int | None = None,
    item_id: int | None = None,
    query_id: str | None = None,
    db: Session = Depends(get_db),
):
    """返回 main_chat query 级治理详情合同。"""
    return get_runtime_surface_service().get_main_chat_query_detail(
        db=db,
        conversation_id=conversation_id,
        plan_id=plan_id,
        item_id=item_id,
        query_id=query_id,
    )


@router.get("/runtime-profile/main-chat-query-history")
def get_main_chat_query_history(
    conversation_id: int | None = None,
    plan_id: int | None = None,
    item_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """返回 main_chat query 历史摘要合同。"""
    return get_runtime_surface_service().get_main_chat_query_history(
        db=db,
        conversation_id=conversation_id,
        plan_id=plan_id,
        item_id=item_id,
        page=page,
        page_size=page_size,
    )


@router.get("/runtime-profile/subagent-lane-recent-summary")
def get_subagent_lane_recent_summary(
    conversation_id: int | None = None,
    plan_id: int | None = None,
    item_id: int | None = None,
    db: Session = Depends(get_db),
):
    """返回 subagent_lane recent summary 试点合同。"""
    return get_runtime_surface_service().get_subagent_lane_recent_summary(
        db=db,
        conversation_id=conversation_id,
        plan_id=plan_id,
        item_id=item_id,
    )


@router.get("/runtime-profile/external-adapter-recent-summary")
def get_external_adapter_recent_summary(
    conversation_id: int | None = None,
    plan_id: int | None = None,
    item_id: int | None = None,
    db: Session = Depends(get_db),
):
    """返回 external_adapter recent summary 试点合同。"""
    return get_runtime_surface_service().get_external_adapter_recent_summary(
        db=db,
        conversation_id=conversation_id,
        plan_id=plan_id,
        item_id=item_id,
    )


@router.get("/runtime-profile/subagent-lane-query-detail-readiness")
def get_subagent_lane_query_detail_readiness(
    conversation_id: int | None = None,
    plan_id: int | None = None,
    item_id: int | None = None,
    db: Session = Depends(get_db),
):
    """返回 subagent_lane query detail 推进门禁合同。"""
    return get_runtime_surface_service().get_subagent_lane_query_detail_readiness(
        db=db,
        conversation_id=conversation_id,
        plan_id=plan_id,
        item_id=item_id,
    )


@router.get("/runtime-profile/channel-promotion-gate")
def get_channel_promotion_gate(
    conversation_id: int | None = None,
    plan_id: int | None = None,
    item_id: int | None = None,
    db: Session = Depends(get_db),
):
    """返回 channel 推广门禁合同。"""
    return get_runtime_surface_service().get_channel_promotion_gate(
        db=db,
        conversation_id=conversation_id,
        plan_id=plan_id,
        item_id=item_id,
    )


@router.get("/runtime-profile/subagent-lane-query-detail")
def get_subagent_lane_query_detail(
    conversation_id: int | None = None,
    plan_id: int | None = None,
    item_id: int | None = None,
    query_id: str | None = None,
    db: Session = Depends(get_db),
):
    """返回 subagent_lane query 级治理详情合同。"""
    return get_runtime_surface_service().get_subagent_lane_query_detail(
        db=db,
        conversation_id=conversation_id,
        plan_id=plan_id,
        item_id=item_id,
        query_id=query_id,
    )


@router.get("/runtime-profile/child-executor-output-replay")
def get_child_executor_output_replay(
    parent_run_id: str,
    db: Session = Depends(get_db),
):
    """返回 child executor 输出回放合同。"""
    return get_runtime_surface_service().get_child_executor_output_replay(
        parent_run_id=parent_run_id,
    )


@router.get("/runtime-profile/child-executor-output-summary")
def get_child_executor_output_summary(
    parent_run_id: str,
    db: Session = Depends(get_db),
):
    """返回 child executor 输出摘要合同。"""
    return get_runtime_surface_service().get_child_executor_output_summary(
        parent_run_id=parent_run_id,
    )


@router.get("/runtime-profile/child-executor-merged-semantics")
def get_child_executor_merged_semantics(
    parent_run_id: str,
    db: Session = Depends(get_db),
):
    """返回 child executor parent merged semantics 合同。"""
    return get_runtime_surface_service().get_child_executor_merged_semantics(
        parent_run_id=parent_run_id,
    )


@router.get("/runtime-profile/run-recovery")
def get_run_recovery(
    run_id: str,
    db: Session = Depends(get_db),
):
    """返回 run 级 recovery probe 合同。"""
    return get_runtime_surface_service().get_run_recovery(
        run_id=run_id,
    )


@router.get("/runtime-profile/embedded-runtime-bootstrap")
def get_embedded_runtime_bootstrap(
    db: Session = Depends(get_db),
):
    """返回默认 embedded runtime bootstrap 合同。"""
    return get_runtime_surface_service().get_embedded_runtime_bootstrap()


@router.patch("/runtime-profile/embedded-runtime-bootstrap")
def update_embedded_runtime_bootstrap(
    request: RuntimeSurfaceEmbeddedRuntimeBootstrapUpdateRequest,
    db: Session = Depends(get_db),
):
    """更新默认 embedded runtime bootstrap 的最小可配置表面。"""
    try:
        payload = request.model_dump(exclude_none=True)
        conversation_id = payload.pop("conversation_id", None)
        updated = get_runtime_surface_service().update_embedded_runtime_bootstrap(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if conversation_id is not None:
        verification = dict(updated.get("post_update_verification") or {})
        validation = dict(updated.get("bootstrap_recovery_validation") or {})
        requested_mode = str(payload.get("embedded_workspace_store_mode") or "").strip()
        updated["timeline_recording"] = _record_governance_action(
            db=db,
            conversation_id=int(conversation_id),
            source="runtime_control",
            event_type="embedded_runtime_bootstrap_updated",
            summary=f"Embedded runtime bootstrap 已切换到 `{requested_mode}`",
            detail=(
                f"runtime_mode={verification.get('current_runtime_mode') or '-'} "
                f"recovery_posture={verification.get('current_recovery_posture') or '-'}"
            ).strip(),
            severity="success" if updated.get("update_status") == "applied" else "warning",
            payload={
                "requested_embedded_workspace_store_mode": requested_mode,
                "update_status": updated.get("update_status"),
                "applied_changes": list(updated.get("applied_changes") or []),
                "hot_reload_applied": bool(updated.get("hot_reload_applied")),
                "restart_required": bool(updated.get("restart_required")),
                "current_runtime_mode": verification.get("current_runtime_mode"),
                "current_recovery_posture": verification.get("current_recovery_posture"),
                "current_workspace_backend_kind": verification.get("current_workspace_backend_kind"),
                "current_workspace_backend_mode": verification.get("current_workspace_backend_mode"),
                "recovery_contract_aligned": verification.get("recovery_contract_aligned"),
                "bootstrap_recovery_validation_status": validation.get("validation_status"),
                "bootstrap_recovery_actual_recoverable": validation.get("actual_recoverable"),
            },
        )
    return updated


@router.get("/runtime-backend")
def get_runtime_backend_status(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """返回 scheduler runtime backend 诊断状态。"""
    return get_scheduler_runtime_diagnostics_service(db).collect_status(limit=limit)


@router.post("/runtime-backend/reconcile")
def reconcile_runtime_backend(
    plan_id: int | None = None,
    item_id: int | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """将 metadata runtime 显式回填到 relational runtime 表。"""
    return get_scheduler_runtime_diagnostics_service(db).reconcile_to_relational(
        plan_id=plan_id,
        item_id=item_id,
        limit=limit,
    )


@router.get("/doctor")
def run_doctor(
    capability_gaps: bool = False,
    window_days: int = 0,
    limit: int = 100,
    max_open_actions: int | None = None,
    max_long_blocked_actions: int | None = None,
    conversation_id: int | None = None,
    db: Session = Depends(get_db),
):
    service = get_doctor_runtime_service()
    if capability_gaps:
        report = service.run_capability_gap_report(
            limit=limit,
            window_days=window_days,
            max_open_actions=max_open_actions,
            max_long_blocked_actions=max_long_blocked_actions,
        )
        report["timeline_recording"] = _record_doctor_timeline(
            db=db,
            conversation_id=conversation_id,
            scope="capability_gap",
            params={
                "window_days": window_days,
                "limit": limit,
                "max_open_actions": max_open_actions,
                "max_long_blocked_actions": max_long_blocked_actions,
            },
            report=report,
        )
        return report
    report = service.run_startup_report()
    report = _attach_framework_adapter_runtime_diagnostics(report=report, db=db)
    report["timeline_recording"] = _record_doctor_timeline(
        db=db,
        conversation_id=conversation_id,
        scope="startup",
        params={},
        report=report,
    )
    return report


@router.patch("/runtime-profile")
def update_runtime_profile(request: RuntimeSurfaceUpdateRequest):
    """更新当前 demo/runtime 的最小可配置表面。"""
    try:
        return get_runtime_surface_service().update_runtime_profile(request.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/runtime-framework-adapters/pilot-run")
def run_framework_adapter_pilot(
    request: FrameworkAdapterPilotRunRequest,
    db: Session = Depends(get_db),
):
    """Execute a controlled local framework-adapter pilot run for governance validation."""
    if not ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER:
        raise HTTPException(
            status_code=409,
            detail="framework adapter pilot is disabled; set ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER=true to enable it",
        )
    try:
        return get_framework_adapter_runtime_service().execute_adapter_run(
            adapter_id=request.adapter_id,
            run_id=request.run_id,
            messages=[item.model_dump() for item in request.messages],
            execution_context=request.execution_context or {},
            db=db,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/runtime-framework-adapters/external-pilot")
def run_framework_adapter_external_pilot(
    request: FrameworkAdapterExternalPilotRunRequest,
    db: Session = Depends(get_db),
):
    """Execute a controlled external framework-adapter pilot run for governance validation."""
    if not ENABLE_LANGGRAPH_EXTERNAL_PILOT:
        raise HTTPException(
            status_code=409,
            detail="framework adapter external pilot is disabled; set ENABLE_LANGGRAPH_EXTERNAL_PILOT=true to enable it",
        )
    try:
        return get_framework_adapter_runtime_service().execute_external_adapter_run(
            adapter_id=request.adapter_id,
            run_id=request.run_id,
            messages=[item.model_dump() for item in request.messages],
            execution_context=request.execution_context or {},
            db=db,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/runtime-framework-adapters/precheck")
def precheck_framework_adapter(
    request: FrameworkAdapterPrecheckRequest,
    db: Session = Depends(get_db),
):
    """Return readiness diagnostics for a registered framework adapter without executing a pilot run."""
    try:
        return get_framework_adapter_runtime_service().precheck_adapter(
            adapter_id=request.adapter_id,
            db=db,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            execution_context=request.execution_context or {},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/capability-gaps")
def get_capability_gaps(
    limit: int = 100,
    missing_part: str | None = None,
    keyword: str | None = None,
    profile: str | None = None,
    completion_stage: str | None = None,
    error_category: str | None = None,
    hook_event_type: str | None = None,
    subagent_role: str | None = None,
    provider: str | None = None,
    model_name: str | None = None,
    window_days: int | None = None,
    db: Session = Depends(get_db),
):
    """返回近期能力缺口汇总，用于框架能力盘点。"""
    summary = get_capability_gap_service(db).get_summary(
        limit=limit,
        missing_part=missing_part,
        keyword=keyword,
        profile=profile,
        completion_stage=completion_stage,
        error_category=error_category,
        hook_event_type=hook_event_type,
        subagent_role=subagent_role,
        provider=provider,
        model_name=model_name,
        window_days=window_days,
    )
    status_map = get_remediation_status_service(db).status_map()
    remediation_status_counts: dict[str, int] = {
        "open": 0,
        "in_progress": 0,
        "blocked": 0,
        "done": 0,
        "verified": 0,
    }
    for target in summary.get("remediation_targets") or []:
        action_id = str(target.get("action_id") or "").strip()
        if not action_id:
            continue
        target["status"] = (status_map.get(action_id) or {}).get("status", "open")
        target["status_detail"] = status_map.get(action_id)
        status_key = str(target.get("status") or "open").strip()
        remediation_status_counts[status_key] = int(remediation_status_counts.get(status_key, 0)) + 1
    summary["remediation_status_counts"] = remediation_status_counts
    summary["non_closed_action_count"] = (
        int(remediation_status_counts.get("open", 0))
        + int(remediation_status_counts.get("in_progress", 0))
        + int(remediation_status_counts.get("blocked", 0))
    )
    progress_window_days = 14
    if window_days in {7, 14, 30}:
        progress_window_days = int(window_days)
    now_utc = datetime.now(timezone.utc)
    recent_threshold = now_utc - timedelta(days=progress_window_days)
    stale_threshold = now_utc - timedelta(days=30)
    recent_progress: list[dict] = []
    long_blocked: list[dict] = []
    pending_start: list[dict] = []
    for target in summary.get("remediation_targets") or []:
        action_id = str(target.get("action_id") or "").strip()
        status = str(target.get("status") or "open").strip()
        status_detail = target.get("status_detail") or {}
        updated_at = _parse_iso_datetime(status_detail.get("updated_at"))
        item = {
            "action_id": action_id,
            "status": status,
            "owner": str(target.get("owner") or "").strip(),
            "module": str(target.get("module") or "").strip(),
            "playbook_title": str(target.get("playbook_title") or "").strip(),
            "updated_at": status_detail.get("updated_at"),
        }
        if updated_at and updated_at >= recent_threshold:
            recent_progress.append(item)
        if status == "blocked":
            if updated_at is None or updated_at < stale_threshold:
                long_blocked.append(item)
        if status == "open":
            pending_start.append(item)
    summary["remediation_progress"] = {
        "window_days": progress_window_days,
        "recent_progress": recent_progress,
        "long_blocked": long_blocked,
        "pending_start": pending_start,
        "recent_progress_count": len(recent_progress),
        "long_blocked_count": len(long_blocked),
        "pending_start_count": len(pending_start),
    }
    return summary


@router.get("/remediation-status")
def get_remediation_statuses(db: Session = Depends(get_db)):
    """返回整改状态清单。"""
    return {"items": get_remediation_status_service(db).list_statuses()}


@router.patch("/remediation-status/{action_id}")
def update_remediation_status(
    action_id: str,
    payload: dict,
    db: Session = Depends(get_db),
):
    """更新单个整改动作状态。"""
    try:
        updated = get_remediation_status_service(db).upsert_status(
            action_id=action_id,
            status=str(payload.get("status") or ""),
            owner=payload.get("owner"),
            module=payload.get("module"),
            note=payload.get("note"),
            updated_by=payload.get("updated_by"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    conversation_id = payload.get("conversation_id")
    timeline_recording = _record_governance_action(
        db=db,
        conversation_id=int(conversation_id) if conversation_id is not None else None,
        source="governance",
        event_type="remediation_status_updated",
        summary=f"整改动作 `{action_id}` 已更新为 `{updated.get('status')}`",
        detail=f"owner={updated.get('owner') or '-'} updated_by={updated.get('updated_by') or '-'}",
        severity="success" if updated.get("status") in {"done", "verified"} else "info",
        payload={
            "action_id": action_id,
            "status": updated.get("status"),
            "owner": updated.get("owner"),
            "module": updated.get("module"),
            "updated_by": updated.get("updated_by"),
            "note": updated.get("note"),
        },
    )
    updated["timeline_recording"] = timeline_recording
    return updated
