"""Runtime contract gate summary exposed through the runtime surface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping


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


class RuntimeContractGateService:
    """Read the latest quality gate report and summarize runtime contract checks."""

    CONTRACT_VERSION = "phase-f-runtime-contract-gate-v1"

    def __init__(self, report_path: str | Path | None = None):
        self.report_path = Path(report_path) if report_path else ROOT_DIR / "quality-gate-report.json"

    def build_runtime_contract(self) -> Dict[str, Any]:
        report = self._load_report()
        if not report:
            return self._empty_contract("quality_gate_report_missing")

        checks = self._extract_contract_checks(report)
        failed_checks = [item for item in checks if not item.get("ok")]
        if not checks:
            overall_status = "unknown"
            failure_reason = "contract_checks_missing"
            runtime_contract_summary = self._build_unknown_runtime_contract_summary()
            runtime_contract_artifact_schema = self._build_unknown_runtime_contract_artifact_schema()
        elif failed_checks:
            overall_status = "degraded"
            failure_reason = "contract_checks_failed"
            runtime_contract_summary = self._extract_runtime_contract_summary(report, checks)
            runtime_contract_artifact_schema = self._extract_runtime_contract_artifact_schema(
                report,
                runtime_contract_summary,
            )
        else:
            overall_status = "healthy"
            failure_reason = ""
            runtime_contract_summary = self._extract_runtime_contract_summary(report, checks)
            runtime_contract_artifact_schema = self._extract_runtime_contract_artifact_schema(
                report,
                runtime_contract_summary,
            )

        return {
            "contract_version": self.CONTRACT_VERSION,
            "available": True,
            "overall_status": overall_status,
            "generated_at": str(report.get("generated_at") or ""),
            "report_path": str(self.report_path),
            "check_count": len(checks),
            "failed_check_count": len(failed_checks),
            "failure_reason": failure_reason,
            "runtime_contract_summary": runtime_contract_summary,
            "runtime_contract_artifact_schema": runtime_contract_artifact_schema,
            "checks": checks,
        }

    def _load_report(self) -> Dict[str, Any]:
        try:
            payload = json.loads(self.report_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def _empty_contract(self, failure_reason: str) -> Dict[str, Any]:
        return {
            "contract_version": self.CONTRACT_VERSION,
            "available": False,
            "overall_status": "unknown",
            "generated_at": "",
            "report_path": str(self.report_path),
            "check_count": 0,
            "failed_check_count": 0,
            "failure_reason": failure_reason,
            "runtime_contract_summary": self._build_unknown_runtime_contract_summary(),
            "runtime_contract_artifact_schema": self._build_unknown_runtime_contract_artifact_schema(),
            "checks": [],
        }

    def _extract_contract_checks(self, report: Mapping[str, Any]) -> List[Dict[str, Any]]:
        checks: List[Dict[str, Any]] = []
        for step in self._iter_mapping_items(report.get("steps")):
            step_name = str(step.get("name") or "")
            for raw_check in self._iter_mapping_items(step.get("contract_checks")):
                checks.append(self._normalize_check(step_name, raw_check))
        return checks

    def _extract_runtime_contract_summary(
        self,
        report: Mapping[str, Any],
        checks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        for step in self._iter_mapping_items(report.get("steps")):
            summary = step.get("runtime_contract_summary")
            if isinstance(summary, Mapping):
                return self._normalize_runtime_contract_summary(summary, checks)
        return self._build_runtime_contract_summary(checks)

    def _iter_mapping_items(self, value: Any) -> List[Mapping[str, Any]]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, Mapping)]

    def _extract_runtime_contract_artifact_schema(
        self,
        report: Mapping[str, Any],
        runtime_contract_summary: Mapping[str, Any],
    ) -> Dict[str, Any]:
        for step in self._iter_mapping_items(report.get("steps")):
            artifact_schema = step.get("runtime_contract_artifact_schema")
            if isinstance(artifact_schema, Mapping):
                return self._normalize_runtime_contract_artifact_schema(artifact_schema)
        return self._build_runtime_contract_artifact_schema(runtime_contract_summary)

    def _normalize_runtime_contract_artifact_schema(self, artifact_schema: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "contract_version": str(
                artifact_schema.get("contract_version") or RUNTIME_CONTRACT_ARTIFACT_SCHEMA_VERSION
            ),
            "overall_status": str(artifact_schema.get("overall_status") or "unknown"),
            "summary_required_fields": self._normalize_required_summary_fields(
                artifact_schema.get("summary_required_fields")
            ),
            "summary_missing_fields": self._normalize_string_list(artifact_schema.get("summary_missing_fields")),
        }

    def _build_runtime_contract_artifact_schema(self, runtime_contract_summary: Mapping[str, Any]) -> Dict[str, Any]:
        missing_fields = [
            field_name
            for field_name in RUNTIME_CONTRACT_SUMMARY_REQUIRED_FIELDS
            if not self._has_path(runtime_contract_summary, field_name)
        ]
        return {
            "contract_version": RUNTIME_CONTRACT_ARTIFACT_SCHEMA_VERSION,
            "overall_status": "degraded" if missing_fields else "healthy",
            "summary_required_fields": list(RUNTIME_CONTRACT_SUMMARY_REQUIRED_FIELDS),
            "summary_missing_fields": missing_fields,
        }

    def _build_unknown_runtime_contract_artifact_schema(self) -> Dict[str, Any]:
        return {
            "contract_version": RUNTIME_CONTRACT_ARTIFACT_SCHEMA_VERSION,
            "overall_status": "unknown",
            "summary_required_fields": list(RUNTIME_CONTRACT_SUMMARY_REQUIRED_FIELDS),
            "summary_missing_fields": [],
        }

    def _normalize_required_summary_fields(self, value: Any) -> List[str]:
        normalized = self._normalize_string_list(value)
        merged = list(normalized or [])
        for field_name in RUNTIME_CONTRACT_SUMMARY_REQUIRED_FIELDS:
            if field_name not in merged:
                merged.append(field_name)
        return merged

    def _has_path(self, value: Mapping[str, Any], path: str) -> bool:
        current: Any = value
        for part in str(path or "").split("."):
            if not isinstance(current, Mapping) or part not in current:
                return False
            current = current[part]
        return True

    def _normalize_runtime_contract_summary(
        self,
        summary: Mapping[str, Any],
        checks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        fallback = self._build_runtime_contract_summary(checks)
        coverage = summary.get("approval_replay_coverage")
        if not isinstance(coverage, Mapping):
            coverage = fallback["approval_replay_coverage"]
        approval_lifecycle_coverage = summary.get("approval_lifecycle_recovery_coverage")
        if not isinstance(approval_lifecycle_coverage, Mapping):
            approval_lifecycle_coverage = fallback["approval_lifecycle_recovery_coverage"]
        approved_tool_coverage = summary.get("approved_tool_execution_coverage")
        if not isinstance(approved_tool_coverage, Mapping):
            approved_tool_coverage = fallback["approved_tool_execution_coverage"]
        sdk_tool_coverage = summary.get("sdk_tool_runtime_execution_coverage")
        if not isinstance(sdk_tool_coverage, Mapping):
            sdk_tool_coverage = fallback["sdk_tool_runtime_execution_coverage"]
        tool_timeout_retry_coverage = summary.get("tool_runtime_timeout_retry_coverage")
        if not isinstance(tool_timeout_retry_coverage, Mapping):
            tool_timeout_retry_coverage = fallback["tool_runtime_timeout_retry_coverage"]
        checkpoint_cursor_coverage = summary.get("checkpoint_resume_cursor_coverage")
        if not isinstance(checkpoint_cursor_coverage, Mapping):
            checkpoint_cursor_coverage = fallback["checkpoint_resume_cursor_coverage"]
        embedded_sdk_persistence_coverage = summary.get("embedded_sdk_persistence_coverage")
        if not isinstance(embedded_sdk_persistence_coverage, Mapping):
            embedded_sdk_persistence_coverage = fallback["embedded_sdk_persistence_coverage"]
        worker_ownership_store_mode_coverage = summary.get("worker_ownership_store_mode_coverage")
        if not isinstance(worker_ownership_store_mode_coverage, Mapping):
            worker_ownership_store_mode_coverage = fallback["worker_ownership_store_mode_coverage"]
        recovery_retry_evidence_coverage = summary.get("recovery_retry_evidence_coverage")
        if not isinstance(recovery_retry_evidence_coverage, Mapping):
            recovery_retry_evidence_coverage = fallback["recovery_retry_evidence_coverage"]
        recovery_retry_scheduler_coverage = summary.get("recovery_retry_scheduler_coverage")
        if not isinstance(recovery_retry_scheduler_coverage, Mapping):
            recovery_retry_scheduler_coverage = fallback["recovery_retry_scheduler_coverage"]
        durable_recovery_loader_coverage = summary.get("durable_recovery_loader_coverage")
        if not isinstance(durable_recovery_loader_coverage, Mapping):
            durable_recovery_loader_coverage = fallback["durable_recovery_loader_coverage"]
        continuation_descriptor_lifecycle_coverage = summary.get("continuation_descriptor_lifecycle_coverage")
        if not isinstance(continuation_descriptor_lifecycle_coverage, Mapping):
            continuation_descriptor_lifecycle_coverage = fallback["continuation_descriptor_lifecycle_coverage"]
        loader_execution_handoff_coverage = summary.get("loader_execution_handoff_coverage")
        if not isinstance(loader_execution_handoff_coverage, Mapping):
            loader_execution_handoff_coverage = fallback["loader_execution_handoff_coverage"]
        recovery_audit_operation_history_coverage = summary.get("recovery_audit_operation_history_coverage")
        if not isinstance(recovery_audit_operation_history_coverage, Mapping):
            recovery_audit_operation_history_coverage = fallback["recovery_audit_operation_history_coverage"]
        production_recovery_registry_checkpoint_policy_coverage = summary.get(
            "production_recovery_registry_checkpoint_policy_coverage"
        )
        if not isinstance(production_recovery_registry_checkpoint_policy_coverage, Mapping):
            production_recovery_registry_checkpoint_policy_coverage = fallback[
                "production_recovery_registry_checkpoint_policy_coverage"
            ]
        child_executor_gate_coverage = summary.get("child_executor_promotion_gate_coverage")
        if not isinstance(child_executor_gate_coverage, Mapping):
            child_executor_gate_coverage = fallback["child_executor_promotion_gate_coverage"]
        child_executor_prerequisites_coverage = summary.get("child_executor_execution_prerequisites_coverage")
        if not isinstance(child_executor_prerequisites_coverage, Mapping):
            child_executor_prerequisites_coverage = fallback["child_executor_execution_prerequisites_coverage"]
        child_executor_dispatch_coverage = summary.get("child_executor_dispatch_coverage")
        if not isinstance(child_executor_dispatch_coverage, Mapping):
            child_executor_dispatch_coverage = fallback["child_executor_dispatch_coverage"]
        child_executor_dispatcher_coverage = summary.get("child_executor_dispatcher_coverage")
        if not isinstance(child_executor_dispatcher_coverage, Mapping):
            child_executor_dispatcher_coverage = fallback["child_executor_dispatcher_coverage"]
        child_executor_dispatch_result_handoff_coverage = summary.get(
            "child_executor_dispatch_result_handoff_coverage"
        )
        if not isinstance(child_executor_dispatch_result_handoff_coverage, Mapping):
            child_executor_dispatch_result_handoff_coverage = fallback[
                "child_executor_dispatch_result_handoff_coverage"
            ]
        child_executor_dispatch_result_retry_audit_coverage = summary.get(
            "child_executor_dispatch_result_retry_audit_coverage"
        )
        if not isinstance(child_executor_dispatch_result_retry_audit_coverage, Mapping):
            child_executor_dispatch_result_retry_audit_coverage = fallback[
                "child_executor_dispatch_result_retry_audit_coverage"
            ]
        child_executor_sandbox_backend_coverage = summary.get("child_executor_sandbox_backend_coverage")
        if not isinstance(child_executor_sandbox_backend_coverage, Mapping):
            child_executor_sandbox_backend_coverage = fallback["child_executor_sandbox_backend_coverage"]
        subagent_lane_detail_coverage = summary.get("subagent_lane_query_detail_coverage")
        if not isinstance(subagent_lane_detail_coverage, Mapping):
            subagent_lane_detail_coverage = fallback["subagent_lane_query_detail_coverage"]
        check_count, check_count_fallback = self._coerce_non_negative_int(
            summary.get("check_count"),
            fallback["check_count"],
        )
        failed_check_count, failed_check_count_fallback = self._coerce_non_negative_int(
            summary.get("failed_check_count"),
            fallback["failed_check_count"],
        )
        missing_payload_count, missing_payload_count_fallback = self._coerce_non_negative_int(
            summary.get("missing_payload_count"),
            fallback["missing_payload_count"],
        )
        status = str(summary.get("overall_status") or fallback["overall_status"])
        if (
            check_count_fallback
            or failed_check_count_fallback
            or missing_payload_count_fallback
        ):
            status = fallback["overall_status"]
        return {
            "overall_status": status,
            "check_count": check_count,
            "failed_check_count": failed_check_count,
            "missing_payload_count": missing_payload_count,
            "approval_replay_coverage": {
                "event_payload_sample": self._coerce_truthy_flag(coverage.get("event_payload_sample")),
                "observed_status_kinds": self._normalize_string_list(coverage.get("observed_status_kinds")),
            },
            "approval_lifecycle_recovery_coverage": self._normalize_approval_lifecycle_recovery_coverage(
                approval_lifecycle_coverage
            ),
            "approved_tool_execution_coverage": self._normalize_approved_tool_execution_coverage(approved_tool_coverage),
            "sdk_tool_runtime_execution_coverage": self._normalize_sdk_tool_runtime_execution_coverage(sdk_tool_coverage),
            "tool_runtime_timeout_retry_coverage": self._normalize_tool_runtime_timeout_retry_coverage(
                tool_timeout_retry_coverage
            ),
            "checkpoint_resume_cursor_coverage": self._normalize_checkpoint_resume_cursor_coverage(
                checkpoint_cursor_coverage
            ),
            "embedded_sdk_persistence_coverage": self._normalize_embedded_sdk_persistence_coverage(
                embedded_sdk_persistence_coverage
            ),
            "worker_ownership_store_mode_coverage": self._normalize_worker_ownership_store_mode_coverage(
                worker_ownership_store_mode_coverage
            ),
            "recovery_retry_evidence_coverage": self._normalize_recovery_retry_evidence_coverage(
                recovery_retry_evidence_coverage
            ),
            "recovery_retry_scheduler_coverage": self._normalize_recovery_retry_scheduler_coverage(
                recovery_retry_scheduler_coverage
            ),
            "durable_recovery_loader_coverage": self._normalize_durable_recovery_loader_coverage(
                durable_recovery_loader_coverage
            ),
            "continuation_descriptor_lifecycle_coverage": self._normalize_continuation_descriptor_lifecycle_coverage(
                continuation_descriptor_lifecycle_coverage
            ),
            "loader_execution_handoff_coverage": self._normalize_loader_execution_handoff_coverage(
                loader_execution_handoff_coverage
            ),
            "recovery_audit_operation_history_coverage": self._normalize_recovery_audit_operation_history_coverage(
                recovery_audit_operation_history_coverage
            ),
            "production_recovery_registry_checkpoint_policy_coverage": (
                self._normalize_production_recovery_registry_checkpoint_policy_coverage(
                    production_recovery_registry_checkpoint_policy_coverage
                )
            ),
            "child_executor_promotion_gate_coverage": self._normalize_child_executor_promotion_gate_coverage(
                child_executor_gate_coverage
            ),
            "child_executor_execution_prerequisites_coverage": self._normalize_child_executor_execution_prerequisites_coverage(
                child_executor_prerequisites_coverage
            ),
            "child_executor_dispatch_coverage": self._normalize_child_executor_dispatch_coverage(
                child_executor_dispatch_coverage
            ),
            "child_executor_dispatcher_coverage": self._normalize_child_executor_dispatcher_coverage(
                child_executor_dispatcher_coverage
            ),
            "child_executor_dispatch_result_handoff_coverage": (
                self._normalize_child_executor_dispatch_result_handoff_coverage(
                    child_executor_dispatch_result_handoff_coverage
                )
            ),
            "child_executor_dispatch_result_retry_audit_coverage": (
                self._normalize_child_executor_dispatch_result_retry_audit_coverage(
                    child_executor_dispatch_result_retry_audit_coverage
                )
            ),
            "child_executor_sandbox_backend_coverage": self._normalize_child_executor_sandbox_backend_coverage(
                child_executor_sandbox_backend_coverage
            ),
            "subagent_lane_query_detail_coverage": self._normalize_subagent_lane_query_detail_coverage(subagent_lane_detail_coverage),
        }

    def _coerce_non_negative_int(self, value: Any, fallback: int) -> tuple[int, bool]:
        try:
            normalized = int(value)
        except (TypeError, ValueError):
            return fallback, True
        if normalized < 0:
            return fallback, True
        return normalized, False

    def _build_runtime_contract_summary(self, checks: List[Dict[str, Any]]) -> Dict[str, Any]:
        failed_checks = [check for check in checks if not bool(check.get("ok"))]
        event_payload_check = next(
            (check for check in checks if str(check.get("name") or "").strip() == "embedded_sdk_event_payloads"),
            {},
        )
        observed_status_kinds = self._normalize_string_list(event_payload_check.get("observed_status_kinds"))
        replay_coverage = (
            {"approval_replayed", "approval_ignored"}.issubset(set(observed_status_kinds))
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
            "overall_status": "healthy" if checks and not failed_checks else "degraded",
            "check_count": len(checks),
            "failed_check_count": len(failed_checks),
            "missing_payload_count": self._coerce_optional_non_negative_int(
                event_payload_check.get("missing_payload_count"),
            ) or 0,
            "approval_replay_coverage": {
                "event_payload_sample": replay_coverage,
                "observed_status_kinds": sorted(set(observed_status_kinds)),
            },
            "approval_lifecycle_recovery_coverage": self._build_approval_lifecycle_recovery_coverage(
                approval_lifecycle_check
            ),
            "approved_tool_execution_coverage": self._build_approved_tool_execution_coverage(approved_tool_bridge_check),
            "sdk_tool_runtime_execution_coverage": self._build_sdk_tool_runtime_execution_coverage(sdk_tool_bridge_check),
            "tool_runtime_timeout_retry_coverage": self._build_tool_runtime_timeout_retry_coverage(
                tool_runtime_timeout_retry_check
            ),
            "checkpoint_resume_cursor_coverage": self._build_checkpoint_resume_cursor_coverage(
                checkpoint_cursor_check
            ),
            "embedded_sdk_persistence_coverage": self._build_embedded_sdk_persistence_coverage(
                persistence_posture_check
            ),
            "worker_ownership_store_mode_coverage": self._build_worker_ownership_store_mode_coverage(
                worker_ownership_store_mode_check
            ),
            "recovery_retry_evidence_coverage": self._build_recovery_retry_evidence_coverage(
                recovery_retry_evidence_check
            ),
            "recovery_retry_scheduler_coverage": self._build_recovery_retry_scheduler_coverage(
                recovery_retry_scheduler_check
            ),
            "durable_recovery_loader_coverage": self._build_durable_recovery_loader_coverage(
                durable_recovery_loader_check
            ),
            "continuation_descriptor_lifecycle_coverage": self._build_continuation_descriptor_lifecycle_coverage(
                durable_recovery_loader_check
            ),
            "loader_execution_handoff_coverage": self._build_loader_execution_handoff_coverage(
                durable_recovery_loader_check
            ),
            "recovery_audit_operation_history_coverage": self._build_recovery_audit_operation_history_coverage(
                persistence_posture_check
            ),
            "production_recovery_registry_checkpoint_policy_coverage": (
                self._build_production_recovery_registry_checkpoint_policy_coverage(persistence_posture_check)
            ),
            "child_executor_promotion_gate_coverage": self._build_child_executor_promotion_gate_coverage(
                child_executor_gate_check
            ),
            "child_executor_execution_prerequisites_coverage": self._build_child_executor_execution_prerequisites_coverage(
                child_executor_gate_check
            ),
            "child_executor_dispatch_coverage": self._build_child_executor_dispatch_coverage(
                child_executor_dispatch_check
            ),
            "child_executor_dispatcher_coverage": self._build_child_executor_dispatcher_coverage(
                child_executor_dispatcher_check
            ),
            "child_executor_dispatch_result_handoff_coverage": (
                self._build_child_executor_dispatch_result_handoff_coverage(
                    child_executor_dispatch_result_handoff_check
                )
            ),
            "child_executor_dispatch_result_retry_audit_coverage": (
                self._build_child_executor_dispatch_result_retry_audit_coverage(
                    child_executor_dispatch_result_retry_audit_check
                )
            ),
            "child_executor_sandbox_backend_coverage": self._build_child_executor_sandbox_backend_coverage(
                child_executor_sandbox_backend_check
            ),
            "subagent_lane_query_detail_coverage": self._build_subagent_lane_query_detail_coverage(subagent_lane_detail_check),
        }

    def _build_unknown_runtime_contract_summary(self) -> Dict[str, Any]:
        return {
            "overall_status": "unknown",
            "check_count": 0,
            "failed_check_count": 0,
            "missing_payload_count": 0,
            "approval_replay_coverage": {
                "event_payload_sample": False,
                "observed_status_kinds": [],
            },
            "approval_lifecycle_recovery_coverage": self._build_approval_lifecycle_recovery_coverage({}),
            "approved_tool_execution_coverage": self._build_approved_tool_execution_coverage({}),
            "sdk_tool_runtime_execution_coverage": self._build_sdk_tool_runtime_execution_coverage({}),
            "tool_runtime_timeout_retry_coverage": self._build_tool_runtime_timeout_retry_coverage({}),
            "checkpoint_resume_cursor_coverage": self._build_checkpoint_resume_cursor_coverage({}),
            "embedded_sdk_persistence_coverage": self._build_embedded_sdk_persistence_coverage({}),
            "worker_ownership_store_mode_coverage": self._build_worker_ownership_store_mode_coverage({}),
            "recovery_retry_evidence_coverage": self._build_recovery_retry_evidence_coverage({}),
            "recovery_retry_scheduler_coverage": self._build_recovery_retry_scheduler_coverage({}),
            "durable_recovery_loader_coverage": self._build_durable_recovery_loader_coverage({}),
            "continuation_descriptor_lifecycle_coverage": self._build_continuation_descriptor_lifecycle_coverage({}),
            "loader_execution_handoff_coverage": self._build_loader_execution_handoff_coverage({}),
            "recovery_audit_operation_history_coverage": self._build_recovery_audit_operation_history_coverage({}),
            "production_recovery_registry_checkpoint_policy_coverage": (
                self._build_production_recovery_registry_checkpoint_policy_coverage({})
            ),
            "child_executor_promotion_gate_coverage": self._build_child_executor_promotion_gate_coverage({}),
            "child_executor_execution_prerequisites_coverage": self._build_child_executor_execution_prerequisites_coverage({}),
            "child_executor_dispatch_coverage": self._build_child_executor_dispatch_coverage({}),
            "child_executor_dispatcher_coverage": self._build_child_executor_dispatcher_coverage({}),
            "child_executor_dispatch_result_handoff_coverage": (
                self._build_child_executor_dispatch_result_handoff_coverage({})
            ),
            "child_executor_dispatch_result_retry_audit_coverage": (
                self._build_child_executor_dispatch_result_retry_audit_coverage({})
            ),
            "child_executor_sandbox_backend_coverage": self._build_child_executor_sandbox_backend_coverage({}),
            "subagent_lane_query_detail_coverage": self._build_subagent_lane_query_detail_coverage({}),
        }

    def _normalize_check(self, step_name: str, raw_check: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "step": step_name,
            "name": str(raw_check.get("name") or ""),
            "ok": bool(raw_check.get("ok")),
            "failure_reason": str(raw_check.get("failure_reason") or ""),
            "status_code": raw_check.get("status_code"),
            "contract_snapshot_status": raw_check.get("contract_snapshot_status"),
            "adapter_health_status": raw_check.get("adapter_health_status"),
            "missing_payload_count": self._coerce_optional_non_negative_int(raw_check.get("missing_payload_count")),
            "checked_event_count": self._coerce_optional_non_negative_int(raw_check.get("checked_event_count")),
            "observed_status_kinds": self._normalize_string_list(raw_check.get("observed_status_kinds")),
            "replayed_submission_status": str(raw_check.get("replayed_submission_status") or ""),
            "ignored_submission_status": str(raw_check.get("ignored_submission_status") or ""),
            "resolved_recovery_reason": str(raw_check.get("resolved_recovery_reason") or ""),
            "backend_kind": raw_check.get("backend_kind"),
            "backend_mode": raw_check.get("backend_mode"),
            "fallback_active": raw_check.get("fallback_active"),
            "probe_recoverable": raw_check.get("probe_recoverable"),
            "contract_version": raw_check.get("contract_version"),
            "run_recovery_available": raw_check.get("run_recovery_available"),
            "tool_recovery_reason": raw_check.get("tool_recovery_reason"),
            "loop_recovery_reason": raw_check.get("loop_recovery_reason"),
            "resumed_state": raw_check.get("resumed_state"),
            "approved_state": raw_check.get("approved_state"),
            "approved_tool_call_count": self._coerce_optional_non_negative_int(raw_check.get("approved_tool_call_count")),
            "auto_tool_call_count": self._coerce_optional_non_negative_int(raw_check.get("auto_tool_call_count")),
            "auto_tool_history_count": self._coerce_optional_non_negative_int(raw_check.get("auto_tool_history_count")),
            "approved_policy_original_status": str(raw_check.get("approved_policy_original_status") or ""),
            "approved_policy_override_status": str(raw_check.get("approved_policy_override_status") or ""),
            "deny_override_status": str(raw_check.get("deny_override_status") or ""),
            "deny_tool_call_count": self._coerce_optional_non_negative_int(raw_check.get("deny_tool_call_count")),
            "retry_policy": str(raw_check.get("retry_policy") or ""),
            "timeout_enforcement": str(raw_check.get("timeout_enforcement") or ""),
            "schema_validation": str(raw_check.get("schema_validation") or ""),
            "recovered_status": str(raw_check.get("recovered_status") or ""),
            "recovered_retry_status": str(raw_check.get("recovered_retry_status") or ""),
            "recovered_attempt_count": self._coerce_optional_non_negative_int(raw_check.get("recovered_attempt_count")),
            "exhausted_status": str(raw_check.get("exhausted_status") or ""),
            "exhausted_retry_status": str(raw_check.get("exhausted_retry_status") or ""),
            "exhausted_attempt_count": self._coerce_optional_non_negative_int(raw_check.get("exhausted_attempt_count")),
            "timeout_status": str(raw_check.get("timeout_status") or ""),
            "timeout_metadata_status": str(raw_check.get("timeout_metadata_status") or ""),
            "timeout_metadata_enforcement": str(raw_check.get("timeout_metadata_enforcement") or ""),
            "hard_cancellation_claimed": raw_check.get("hard_cancellation_claimed"),
            "sandbox_execution_claimed": raw_check.get("sandbox_execution_claimed"),
            "worker_timeout_claimed": raw_check.get("worker_timeout_claimed"),
            "checkpoint_status": str(raw_check.get("checkpoint_status") or ""),
            "checkpoint_kind": str(raw_check.get("checkpoint_kind") or ""),
            "cursor_status": str(raw_check.get("cursor_status") or ""),
            "cursor_entrypoint": str(raw_check.get("cursor_entrypoint") or ""),
            "cursor_recovery_reason": str(raw_check.get("cursor_recovery_reason") or ""),
            "memory_posture": str(raw_check.get("memory_posture") or ""),
            "durable_posture": str(raw_check.get("durable_posture") or ""),
            "degraded_posture": str(raw_check.get("degraded_posture") or ""),
            "memory_cross_process_block_reason": str(raw_check.get("memory_cross_process_block_reason") or ""),
            "degraded_cross_process_block_reason": str(raw_check.get("degraded_cross_process_block_reason") or ""),
            "durable_cross_process_candidate": raw_check.get("durable_cross_process_candidate"),
            "production_recovery_gate_contract_version": str(
                raw_check.get("production_recovery_gate_contract_version") or ""
            ),
            "production_recovery_gate_status": str(raw_check.get("production_recovery_gate_status") or ""),
            "production_recovery_gate_missing_sections": self._normalize_string_list(
                raw_check.get("production_recovery_gate_missing_sections")
            ),
            "production_recovery_default_enabled": raw_check.get("production_recovery_default_enabled"),
            "production_recovery_worker_ownership_gate_contract_version": str(
                raw_check.get("production_recovery_worker_ownership_gate_contract_version") or ""
            ),
            "production_recovery_worker_ownership_gate_status": str(
                raw_check.get("production_recovery_worker_ownership_gate_status") or ""
            ),
            "production_recovery_worker_ownership_default_enabled": raw_check.get(
                "production_recovery_worker_ownership_default_enabled"
            ),
            "production_recovery_worker_ownership_missing_sections": self._normalize_string_list(
                raw_check.get("production_recovery_worker_ownership_missing_sections")
            ),
            "recovery_audit_contract_version": str(raw_check.get("recovery_audit_contract_version") or ""),
            "recovery_audit_ready": raw_check.get("recovery_audit_ready"),
            "recovery_audit_operation_history_supported": raw_check.get(
                "recovery_audit_operation_history_supported"
            ),
            "recovery_audit_summary_supported": raw_check.get("recovery_audit_summary_supported"),
            "recovery_audit_timeline_writer_available": raw_check.get(
                "recovery_audit_timeline_writer_available"
            ),
            "recovery_audit_idempotent_trace_dedupe": raw_check.get(
                "recovery_audit_idempotent_trace_dedupe"
            ),
            "recovery_audit_authorization_source": raw_check.get("recovery_audit_authorization_source"),
            "registry_checkpoint_policy_contract_version": str(
                raw_check.get("registry_checkpoint_policy_contract_version") or ""
            ),
            "registry_checkpoint_policy_ready": raw_check.get("registry_checkpoint_policy_ready"),
            "registry_binding_policy_ready": raw_check.get("registry_binding_policy_ready"),
            "checkpoint_resume_cursor_policy_ready": raw_check.get(
                "checkpoint_resume_cursor_policy_ready"
            ),
            "registry_checkpoint_policy_authorization_source": raw_check.get(
                "registry_checkpoint_policy_authorization_source"
            ),
            "default_mode": str(raw_check.get("default_mode") or ""),
            "default_mode_source": str(raw_check.get("default_mode_source") or ""),
            "default_adapter_kind": str(raw_check.get("default_adapter_kind") or ""),
            "default_durable": raw_check.get("default_durable"),
            "production_gate_contract_version": str(raw_check.get("production_gate_contract_version") or ""),
            "production_gate_status": str(raw_check.get("production_gate_status") or ""),
            "production_gate_missing_sections": self._normalize_string_list(
                raw_check.get("production_gate_missing_sections")
            ),
            "production_default_enabled": raw_check.get("production_default_enabled"),
            "vendor_lock_contract_version": str(raw_check.get("vendor_lock_contract_version") or ""),
            "vendor_lock_status": str(raw_check.get("vendor_lock_status") or ""),
            "vendor_lock_missing_sections": self._normalize_string_list(
                raw_check.get("vendor_lock_missing_sections")
            ),
            "vendor_lock_current_posture": str(raw_check.get("vendor_lock_current_posture") or ""),
            "vendor_lock_sql_row_lease_fencing": raw_check.get("vendor_lock_sql_row_lease_fencing"),
            "vendor_lock_sql_row_lease_is_vendor_lock": raw_check.get(
                "vendor_lock_sql_row_lease_is_vendor_lock"
            ),
            "vendor_lock_adapter_present": raw_check.get("vendor_lock_adapter_present"),
            "vendor_lock_adapter_contract_version": str(
                raw_check.get("vendor_lock_adapter_contract_version") or ""
            ),
            "vendor_lock_adapter_status": str(raw_check.get("vendor_lock_adapter_status") or ""),
            "vendor_lock_adapter_kind": str(raw_check.get("vendor_lock_adapter_kind") or ""),
            "vendor_lock_adapter_target_backend": str(
                raw_check.get("vendor_lock_adapter_target_backend") or ""
            ),
            "vendor_lock_adapter_scope": str(raw_check.get("vendor_lock_adapter_scope") or ""),
            "vendor_lock_adapter_fencing_strategy": str(
                raw_check.get("vendor_lock_adapter_fencing_strategy") or ""
            ),
            "vendor_lock_adapter_ttl_renewal_strategy": str(
                raw_check.get("vendor_lock_adapter_ttl_renewal_strategy") or ""
            ),
            "vendor_lock_adapter_failover_strategy": str(
                raw_check.get("vendor_lock_adapter_failover_strategy") or ""
            ),
            "vendor_lock_adapter_stale_cleanup_strategy": str(
                raw_check.get("vendor_lock_adapter_stale_cleanup_strategy") or ""
            ),
            "vendor_lock_adapter_acquire_supported": raw_check.get(
                "vendor_lock_adapter_acquire_supported"
            ),
            "vendor_lock_adapter_renew_supported": raw_check.get(
                "vendor_lock_adapter_renew_supported"
            ),
            "vendor_lock_adapter_release_supported": raw_check.get(
                "vendor_lock_adapter_release_supported"
            ),
            "vendor_lock_adapter_probe_supported": raw_check.get(
                "vendor_lock_adapter_probe_supported"
            ),
            "vendor_lock_adapter_production_allowed": raw_check.get(
                "vendor_lock_adapter_production_allowed"
            ),
            "vendor_lock_adapter_sql_row_lease_is_vendor_lock": raw_check.get(
                "vendor_lock_adapter_sql_row_lease_is_vendor_lock"
            ),
            "vendor_lock_adapter_missing_sections": self._normalize_string_list(
                raw_check.get("vendor_lock_adapter_missing_sections")
            ),
            "postgres_probe_contract_version": str(
                raw_check.get("postgres_probe_contract_version") or ""
            ),
            "postgres_probe_status": str(raw_check.get("postgres_probe_status") or ""),
            "postgres_probe_missing_sections": self._normalize_string_list(
                raw_check.get("postgres_probe_missing_sections")
            ),
            "postgres_probe_executes": raw_check.get("postgres_probe_executes"),
            "postgres_probe_sql_row_lease_is_vendor_lock": raw_check.get(
                "postgres_probe_sql_row_lease_is_vendor_lock"
            ),
            "postgres_probe_ready_status": str(raw_check.get("postgres_probe_ready_status") or ""),
            "postgres_probe_ready_executes": raw_check.get("postgres_probe_ready_executes"),
            "postgres_execution_seam_contract_version": str(
                raw_check.get("postgres_execution_seam_contract_version") or ""
            ),
            "postgres_execution_default_status": str(
                raw_check.get("postgres_execution_default_status") or ""
            ),
            "postgres_execution_default_executor_bound": raw_check.get(
                "postgres_execution_default_executor_bound"
            ),
            "postgres_execution_default_enabled_by_default": raw_check.get(
                "postgres_execution_default_enabled_by_default"
            ),
            "postgres_execution_default_production_allowed": raw_check.get(
                "postgres_execution_default_production_allowed"
            ),
            "postgres_execution_default_missing_sections": self._normalize_string_list(
                raw_check.get("postgres_execution_default_missing_sections")
            ),
            "postgres_execution_default_probe_status": str(
                raw_check.get("postgres_execution_default_probe_status") or ""
            ),
            "postgres_execution_default_probe_executed": raw_check.get(
                "postgres_execution_default_probe_executed"
            ),
            "postgres_execution_opt_in_status": str(
                raw_check.get("postgres_execution_opt_in_status") or ""
            ),
            "postgres_execution_opt_in_executor_bound": raw_check.get(
                "postgres_execution_opt_in_executor_bound"
            ),
            "postgres_execution_opt_in_enabled_by_default": raw_check.get(
                "postgres_execution_opt_in_enabled_by_default"
            ),
            "postgres_execution_opt_in_production_allowed": raw_check.get(
                "postgres_execution_opt_in_production_allowed"
            ),
            "postgres_execution_opt_in_probe_status": str(
                raw_check.get("postgres_execution_opt_in_probe_status") or ""
            ),
            "postgres_execution_opt_in_probe_executed": raw_check.get(
                "postgres_execution_opt_in_probe_executed"
            ),
            "postgres_execution_opt_in_acquire_status": str(
                raw_check.get("postgres_execution_opt_in_acquire_status") or ""
            ),
            "postgres_execution_opt_in_acquire_executed": raw_check.get(
                "postgres_execution_opt_in_acquire_executed"
            ),
            "postgres_execution_opt_in_acquired": raw_check.get(
                "postgres_execution_opt_in_acquired"
            ),
            "postgres_execution_opt_in_envelope_count": raw_check.get(
                "postgres_execution_opt_in_envelope_count"
            ),
            "postgres_rollout_consumer_contract_version": str(
                raw_check.get("postgres_rollout_consumer_contract_version") or ""
            ),
            "postgres_rollout_consumer_default_status": str(
                raw_check.get("postgres_rollout_consumer_default_status") or ""
            ),
            "postgres_rollout_consumer_default_missing_sections": self._normalize_string_list(
                raw_check.get("postgres_rollout_consumer_default_missing_sections")
            ),
            "postgres_rollout_consumer_default_will_enable_default": raw_check.get(
                "postgres_rollout_consumer_default_will_enable_default"
            ),
            "postgres_rollout_consumer_default_executes_lock": raw_check.get(
                "postgres_rollout_consumer_default_executes_lock"
            ),
            "postgres_rollout_consumer_ready_status": str(
                raw_check.get("postgres_rollout_consumer_ready_status") or ""
            ),
            "postgres_rollout_consumer_ready_target_backend": str(
                raw_check.get("postgres_rollout_consumer_ready_target_backend") or ""
            ),
            "postgres_rollout_consumer_ready_lock_adapter_kind": str(
                raw_check.get("postgres_rollout_consumer_ready_lock_adapter_kind") or ""
            ),
            "postgres_rollout_consumer_ready_will_enable_default": raw_check.get(
                "postgres_rollout_consumer_ready_will_enable_default"
            ),
            "postgres_rollout_consumer_ready_executes_lock": raw_check.get(
                "postgres_rollout_consumer_ready_executes_lock"
            ),
            "postgres_rollout_consumer_input_source_status": str(
                raw_check.get("postgres_rollout_consumer_input_source_status") or ""
            ),
            "postgres_rollout_consumer_input_source_ready": raw_check.get(
                "postgres_rollout_consumer_input_source_ready"
            ),
            "postgres_rollout_consumer_input_source_kind": str(
                raw_check.get("postgres_rollout_consumer_input_source_kind") or ""
            ),
            "postgres_target_binding_contract_version": str(
                raw_check.get("postgres_target_binding_contract_version") or ""
            ),
            "postgres_target_binding_default_status": str(
                raw_check.get("postgres_target_binding_default_status") or ""
            ),
            "postgres_target_binding_default_missing_sections": self._normalize_string_list(
                raw_check.get("postgres_target_binding_default_missing_sections")
            ),
            "postgres_target_binding_default_will_enable_lock": raw_check.get(
                "postgres_target_binding_default_will_enable_lock"
            ),
            "postgres_target_binding_default_executes_lock": raw_check.get(
                "postgres_target_binding_default_executes_lock"
            ),
            "postgres_target_binding_ready_status": str(
                raw_check.get("postgres_target_binding_ready_status") or ""
            ),
            "postgres_target_binding_ready_target_backend": str(
                raw_check.get("postgres_target_binding_ready_target_backend") or ""
            ),
            "postgres_target_binding_ready_lock_adapter_kind": str(
                raw_check.get("postgres_target_binding_ready_lock_adapter_kind") or ""
            ),
            "postgres_target_binding_ready_will_enable_lock": raw_check.get(
                "postgres_target_binding_ready_will_enable_lock"
            ),
            "postgres_target_binding_ready_executes_lock": raw_check.get(
                "postgres_target_binding_ready_executes_lock"
            ),
            "postgres_target_binding_target_input_status": str(
                raw_check.get("postgres_target_binding_target_input_status") or ""
            ),
            "postgres_target_binding_target_decision_status": str(
                raw_check.get("postgres_target_binding_target_decision_status") or ""
            ),
            "postgres_target_binding_target_decision_production_allowed": raw_check.get(
                "postgres_target_binding_target_decision_production_allowed"
            ),
            "postgres_semantics_binding_contract_version": str(
                raw_check.get("postgres_semantics_binding_contract_version") or ""
            ),
            "postgres_semantics_binding_default_status": str(
                raw_check.get("postgres_semantics_binding_default_status") or ""
            ),
            "postgres_semantics_binding_default_missing_sections": self._normalize_string_list(
                raw_check.get("postgres_semantics_binding_default_missing_sections")
            ),
            "postgres_semantics_binding_default_will_enable_lock": raw_check.get(
                "postgres_semantics_binding_default_will_enable_lock"
            ),
            "postgres_semantics_binding_default_will_update_gate": raw_check.get(
                "postgres_semantics_binding_default_will_update_gate"
            ),
            "postgres_semantics_binding_default_executes_lock": raw_check.get(
                "postgres_semantics_binding_default_executes_lock"
            ),
            "postgres_semantics_binding_ready_status": str(
                raw_check.get("postgres_semantics_binding_ready_status") or ""
            ),
            "postgres_semantics_binding_ready_target_backend": str(
                raw_check.get("postgres_semantics_binding_ready_target_backend") or ""
            ),
            "postgres_semantics_binding_ready_lock_adapter_kind": str(
                raw_check.get("postgres_semantics_binding_ready_lock_adapter_kind") or ""
            ),
            "postgres_semantics_binding_ready_probe_status": str(
                raw_check.get("postgres_semantics_binding_ready_probe_status") or ""
            ),
            "postgres_semantics_binding_ready_adapter_status": str(
                raw_check.get("postgres_semantics_binding_ready_adapter_status") or ""
            ),
            "postgres_semantics_binding_ready_semantics_status": str(
                raw_check.get("postgres_semantics_binding_ready_semantics_status") or ""
            ),
            "postgres_semantics_binding_ready_will_enable_lock": raw_check.get(
                "postgres_semantics_binding_ready_will_enable_lock"
            ),
            "postgres_semantics_binding_ready_will_update_gate": raw_check.get(
                "postgres_semantics_binding_ready_will_update_gate"
            ),
            "postgres_semantics_binding_ready_executes_lock": raw_check.get(
                "postgres_semantics_binding_ready_executes_lock"
            ),
            "postgres_wiring_decision_contract_version": str(
                raw_check.get("postgres_wiring_decision_contract_version") or ""
            ),
            "postgres_wiring_decision_default_status": str(
                raw_check.get("postgres_wiring_decision_default_status") or ""
            ),
            "postgres_wiring_decision_default_missing_sections": self._normalize_string_list(
                raw_check.get("postgres_wiring_decision_default_missing_sections")
            ),
            "postgres_wiring_decision_default_wiring_allowed": raw_check.get(
                "postgres_wiring_decision_default_wiring_allowed"
            ),
            "postgres_wiring_decision_default_will_update_gate": raw_check.get(
                "postgres_wiring_decision_default_will_update_gate"
            ),
            "postgres_wiring_decision_default_will_enable_lock": raw_check.get(
                "postgres_wiring_decision_default_will_enable_lock"
            ),
            "postgres_wiring_decision_default_executes_lock": raw_check.get(
                "postgres_wiring_decision_default_executes_lock"
            ),
            "postgres_wiring_decision_ready_status": str(
                raw_check.get("postgres_wiring_decision_ready_status") or ""
            ),
            "postgres_wiring_decision_ready_semantics_binding_status": str(
                raw_check.get("postgres_wiring_decision_ready_semantics_binding_status") or ""
            ),
            "postgres_wiring_decision_ready_candidate_status": str(
                raw_check.get("postgres_wiring_decision_ready_candidate_status") or ""
            ),
            "postgres_wiring_decision_ready_wiring_allowed": raw_check.get(
                "postgres_wiring_decision_ready_wiring_allowed"
            ),
            "postgres_wiring_decision_ready_target_backend": str(
                raw_check.get("postgres_wiring_decision_ready_target_backend") or ""
            ),
            "postgres_wiring_decision_ready_lock_adapter_kind": str(
                raw_check.get("postgres_wiring_decision_ready_lock_adapter_kind") or ""
            ),
            "postgres_wiring_decision_ready_will_update_gate": raw_check.get(
                "postgres_wiring_decision_ready_will_update_gate"
            ),
            "postgres_wiring_decision_ready_will_enable_lock": raw_check.get(
                "postgres_wiring_decision_ready_will_enable_lock"
            ),
            "postgres_wiring_decision_ready_executes_lock": raw_check.get(
                "postgres_wiring_decision_ready_executes_lock"
            ),
            "production_dry_run_contract_version": str(
                raw_check.get("production_dry_run_contract_version") or ""
            ),
            "production_dry_run_default_status": str(
                raw_check.get("production_dry_run_default_status") or ""
            ),
            "production_dry_run_default_missing_sections": self._normalize_string_list(
                raw_check.get("production_dry_run_default_missing_sections")
            ),
            "production_dry_run_default_all_required_ready": raw_check.get(
                "production_dry_run_default_all_required_ready"
            ),
            "production_dry_run_default_would_allow": raw_check.get(
                "production_dry_run_default_would_allow"
            ),
            "production_dry_run_default_will_enable": raw_check.get(
                "production_dry_run_default_will_enable"
            ),
            "production_dry_run_default_executes_lock": raw_check.get(
                "production_dry_run_default_executes_lock"
            ),
            "production_dry_run_default_starts_worker": raw_check.get(
                "production_dry_run_default_starts_worker"
            ),
            "production_dry_run_default_runs_auto_claim": raw_check.get(
                "production_dry_run_default_runs_auto_claim"
            ),
            "production_dry_run_ready_status": str(
                raw_check.get("production_dry_run_ready_status") or ""
            ),
            "production_dry_run_ready_missing_sections": self._normalize_string_list(
                raw_check.get("production_dry_run_ready_missing_sections")
            ),
            "production_dry_run_ready_all_required_ready": raw_check.get(
                "production_dry_run_ready_all_required_ready"
            ),
            "production_dry_run_ready_would_allow": raw_check.get(
                "production_dry_run_ready_would_allow"
            ),
            "production_dry_run_ready_will_enable": raw_check.get(
                "production_dry_run_ready_will_enable"
            ),
            "production_dry_run_ready_executes_lock": raw_check.get(
                "production_dry_run_ready_executes_lock"
            ),
            "production_dry_run_ready_starts_worker": raw_check.get(
                "production_dry_run_ready_starts_worker"
            ),
            "production_dry_run_ready_runs_auto_claim": raw_check.get(
                "production_dry_run_ready_runs_auto_claim"
            ),
            "enablement_config_consumer_contract_version": str(
                raw_check.get("enablement_config_consumer_contract_version") or ""
            ),
            "enablement_config_consumer_default_status": str(
                raw_check.get("enablement_config_consumer_default_status") or ""
            ),
            "enablement_config_consumer_default_missing_sections": (
                self._normalize_string_list(
                    raw_check.get(
                        "enablement_config_consumer_default_missing_sections"
                    )
                )
            ),
            "enablement_config_consumer_default_will_enable": raw_check.get(
                "enablement_config_consumer_default_will_enable"
            ),
            "enablement_config_consumer_default_executes_lock": raw_check.get(
                "enablement_config_consumer_default_executes_lock"
            ),
            "enablement_config_consumer_default_starts_worker": raw_check.get(
                "enablement_config_consumer_default_starts_worker"
            ),
            "enablement_config_consumer_default_runs_auto_claim": raw_check.get(
                "enablement_config_consumer_default_runs_auto_claim"
            ),
            "enablement_config_consumer_ready_status": str(
                raw_check.get("enablement_config_consumer_ready_status") or ""
            ),
            "enablement_config_consumer_ready_missing_sections": (
                self._normalize_string_list(
                    raw_check.get("enablement_config_consumer_ready_missing_sections")
                )
            ),
            "enablement_config_consumer_ready_target_backend": str(
                raw_check.get("enablement_config_consumer_ready_target_backend") or ""
            ),
            "enablement_config_consumer_ready_lock_adapter_kind": str(
                raw_check.get("enablement_config_consumer_ready_lock_adapter_kind")
                or ""
            ),
            "enablement_config_consumer_ready_input_source_status": str(
                raw_check.get("enablement_config_consumer_ready_input_source_status")
                or ""
            ),
            "enablement_config_consumer_ready_dry_run_status": str(
                raw_check.get("enablement_config_consumer_ready_dry_run_status") or ""
            ),
            "enablement_config_consumer_ready_dry_run_would_allow": raw_check.get(
                "enablement_config_consumer_ready_dry_run_would_allow"
            ),
            "enablement_config_consumer_ready_will_enable": raw_check.get(
                "enablement_config_consumer_ready_will_enable"
            ),
            "enablement_config_consumer_ready_executes_lock": raw_check.get(
                "enablement_config_consumer_ready_executes_lock"
            ),
            "enablement_config_consumer_ready_starts_worker": raw_check.get(
                "enablement_config_consumer_ready_starts_worker"
            ),
            "enablement_config_consumer_ready_runs_auto_claim": raw_check.get(
                "enablement_config_consumer_ready_runs_auto_claim"
            ),
            "enablement_config_factory_binding_default_status": str(
                raw_check.get("enablement_config_factory_binding_default_status") or ""
            ),
            "enablement_config_factory_binding_ready_status": str(
                raw_check.get("enablement_config_factory_binding_ready_status") or ""
            ),
            "enablement_config_factory_binding_ready_config_id": str(
                raw_check.get("enablement_config_factory_binding_ready_config_id") or ""
            ),
            "enablement_config_factory_binding_will_enable": raw_check.get(
                "enablement_config_factory_binding_will_enable"
            ),
            "enablement_config_factory_binding_executes_lock": raw_check.get(
                "enablement_config_factory_binding_executes_lock"
            ),
            "enablement_config_factory_binding_starts_worker": raw_check.get(
                "enablement_config_factory_binding_starts_worker"
            ),
            "enablement_config_factory_binding_runs_auto_claim": raw_check.get(
                "enablement_config_factory_binding_runs_auto_claim"
            ),
            "vendor_lock_scope_defined": raw_check.get("vendor_lock_scope_defined"),
            "vendor_lock_fencing_guarantee_defined": raw_check.get(
                "vendor_lock_fencing_guarantee_defined"
            ),
            "vendor_lock_failover_semantics_defined": raw_check.get(
                "vendor_lock_failover_semantics_defined"
            ),
            "vendor_lock_ttl_renewal_semantics_defined": raw_check.get(
                "vendor_lock_ttl_renewal_semantics_defined"
            ),
            "vendor_lock_stale_owner_cleanup_defined": raw_check.get(
                "vendor_lock_stale_owner_cleanup_defined"
            ),
            "vendor_lock_production_allowed": raw_check.get("vendor_lock_production_allowed"),
            "vendor_lock_target_decision_contract_version": str(
                raw_check.get("vendor_lock_target_decision_contract_version") or ""
            ),
            "vendor_lock_target_decision_status": str(
                raw_check.get("vendor_lock_target_decision_status") or ""
            ),
            "vendor_lock_target_decision_recorded": raw_check.get(
                "vendor_lock_target_decision_recorded"
            ),
            "vendor_lock_target_backend": str(raw_check.get("vendor_lock_target_backend") or ""),
            "vendor_lock_target_adapter_kind": str(
                raw_check.get("vendor_lock_target_adapter_kind") or ""
            ),
            "vendor_lock_target_scope": str(raw_check.get("vendor_lock_target_scope") or ""),
            "vendor_lock_target_fencing_strategy": str(
                raw_check.get("vendor_lock_target_fencing_strategy") or ""
            ),
            "vendor_lock_target_ttl_renewal_strategy": str(
                raw_check.get("vendor_lock_target_ttl_renewal_strategy") or ""
            ),
            "vendor_lock_target_failover_strategy": str(
                raw_check.get("vendor_lock_target_failover_strategy") or ""
            ),
            "vendor_lock_target_stale_cleanup_strategy": str(
                raw_check.get("vendor_lock_target_stale_cleanup_strategy") or ""
            ),
            "vendor_lock_target_missing_sections": self._normalize_string_list(
                raw_check.get("vendor_lock_target_missing_sections")
            ),
            "vendor_lock_target_sql_row_lease_is_vendor_lock": raw_check.get(
                "vendor_lock_target_sql_row_lease_is_vendor_lock"
            ),
            "vendor_lock_target_production_allowed": raw_check.get(
                "vendor_lock_target_production_allowed"
            ),
            "vendor_lock_target_input_contract_version": str(
                raw_check.get("vendor_lock_target_input_contract_version") or ""
            ),
            "vendor_lock_target_input_source_status": str(
                raw_check.get("vendor_lock_target_input_source_status") or ""
            ),
            "vendor_lock_target_input_source_kind": str(
                raw_check.get("vendor_lock_target_input_source_kind") or ""
            ),
            "vendor_lock_target_input_decision_id": str(
                raw_check.get("vendor_lock_target_input_decision_id") or ""
            ),
            "vendor_lock_target_input_approved_by": str(
                raw_check.get("vendor_lock_target_input_approved_by") or ""
            ),
            "vendor_lock_target_input_approved_at": str(
                raw_check.get("vendor_lock_target_input_approved_at") or ""
            ),
            "vendor_lock_target_input_backend": str(
                raw_check.get("vendor_lock_target_input_backend") or ""
            ),
            "vendor_lock_target_input_adapter_kind": str(
                raw_check.get("vendor_lock_target_input_adapter_kind") or ""
            ),
            "vendor_lock_target_input_rollout_artifact": str(
                raw_check.get("vendor_lock_target_input_rollout_artifact") or ""
            ),
            "vendor_lock_target_input_config_key": str(
                raw_check.get("vendor_lock_target_input_config_key") or ""
            ),
            "vendor_lock_target_input_manual_approval_reference": str(
                raw_check.get("vendor_lock_target_input_manual_approval_reference") or ""
            ),
            "vendor_lock_target_input_missing_sections": self._normalize_string_list(
                raw_check.get("vendor_lock_target_input_missing_sections")
            ),
            "vendor_lock_target_input_sql_row_lease_is_vendor_lock": raw_check.get(
                "vendor_lock_target_input_sql_row_lease_is_vendor_lock"
            ),
            "renewal_supervisor_contract_version": str(
                raw_check.get("renewal_supervisor_contract_version") or ""
            ),
            "renewal_supervisor_status": str(raw_check.get("renewal_supervisor_status") or ""),
            "renewal_supervisor_missing_sections": self._normalize_string_list(
                raw_check.get("renewal_supervisor_missing_sections")
            ),
            "renewal_supervisor_enabled_by_default": raw_check.get(
                "renewal_supervisor_enabled_by_default"
            ),
            "renewal_supervisor_renew_once_supported": raw_check.get(
                "renewal_supervisor_renew_once_supported"
            ),
            "renewal_supervisor_owner_identity_required": raw_check.get(
                "renewal_supervisor_owner_identity_required"
            ),
            "renewal_supervisor_ttl_interval_policy_ready": raw_check.get(
                "renewal_supervisor_ttl_interval_policy_ready"
            ),
            "renewal_supervisor_controlled_lifecycle_supported": raw_check.get(
                "renewal_supervisor_controlled_lifecycle_supported"
            ),
            "renewal_supervisor_starts_by_default": raw_check.get(
                "renewal_supervisor_starts_by_default"
            ),
            "renewal_supervisor_active": raw_check.get("renewal_supervisor_active"),
            "renewal_supervisor_last_renewal_status": str(
                raw_check.get("renewal_supervisor_last_renewal_status") or ""
            ),
            "renewal_supervisor_stop_supported": raw_check.get(
                "renewal_supervisor_stop_supported"
            ),
            "renewal_supervisor_failure_fail_closed": raw_check.get(
                "renewal_supervisor_failure_fail_closed"
            ),
            "renewal_supervisor_lease_loss_fail_closed": raw_check.get(
                "renewal_supervisor_lease_loss_fail_closed"
            ),
            "renewal_supervisor_renew_once_status": str(
                raw_check.get("renewal_supervisor_renew_once_status") or ""
            ),
            "renewal_supervisor_renew_once_background_started": raw_check.get(
                "renewal_supervisor_renew_once_background_started"
            ),
            "renewal_supervisor_stale_fencing_status": str(
                raw_check.get("renewal_supervisor_stale_fencing_status") or ""
            ),
            "renewal_supervisor_stale_fencing_reason": str(
                raw_check.get("renewal_supervisor_stale_fencing_reason") or ""
            ),
            "renewal_supervisor_lifecycle_initial_active": raw_check.get(
                "renewal_supervisor_lifecycle_initial_active"
            ),
            "renewal_supervisor_lifecycle_started_active": raw_check.get(
                "renewal_supervisor_lifecycle_started_active"
            ),
            "renewal_supervisor_lifecycle_started_status": str(
                raw_check.get("renewal_supervisor_lifecycle_started_status") or ""
            ),
            "renewal_supervisor_lifecycle_started_count": raw_check.get(
                "renewal_supervisor_lifecycle_started_count"
            ),
            "renewal_supervisor_lifecycle_stopped_active": raw_check.get(
                "renewal_supervisor_lifecycle_stopped_active"
            ),
            "renewal_supervisor_lifecycle_stopped_count": raw_check.get(
                "renewal_supervisor_lifecycle_stopped_count"
            ),
            "rollout_readiness_contract_version": str(
                raw_check.get("rollout_readiness_contract_version") or ""
            ),
            "rollout_readiness_status": str(raw_check.get("rollout_readiness_status") or ""),
            "rollout_missing_sections": self._normalize_string_list(
                raw_check.get("rollout_missing_sections")
            ),
            "production_rollout_confirmed": raw_check.get("production_rollout_confirmed"),
            "rollout_migration_ready": raw_check.get("rollout_migration_ready"),
            "rollout_stale_fencing_verified": raw_check.get("rollout_stale_fencing_verified"),
            "rollout_rollback_plan_ready": raw_check.get("rollout_rollback_plan_ready"),
            "rollout_operationalization_status": str(
                raw_check.get("rollout_operationalization_status") or ""
            ),
            "rollout_mode": str(raw_check.get("rollout_mode") or ""),
            "rollout_missing_artifacts": self._normalize_string_list(
                raw_check.get("rollout_missing_artifacts")
            ),
            "rollout_rollback_plan_status": str(
                raw_check.get("rollout_rollback_plan_status") or ""
            ),
            "rollout_fallback_policy_status": str(
                raw_check.get("rollout_fallback_policy_status") or ""
            ),
            "rollout_renewal_lifecycle_verification_status": str(
                raw_check.get("rollout_renewal_lifecycle_verification_status") or ""
            ),
            "rollout_auto_claim_decision_status": str(
                raw_check.get("rollout_auto_claim_decision_status") or ""
            ),
            "rollout_confirmation_decision_contract_version": str(
                raw_check.get("rollout_confirmation_decision_contract_version") or ""
            ),
            "rollout_confirmation_decision_status": str(
                raw_check.get("rollout_confirmation_decision_status") or ""
            ),
            "rollout_decision_recorded": raw_check.get("rollout_decision_recorded"),
            "rollout_decision_id": str(raw_check.get("rollout_decision_id") or ""),
            "rollout_approved_by": str(raw_check.get("rollout_approved_by") or ""),
            "rollout_approved_at": str(raw_check.get("rollout_approved_at") or ""),
            "rollout_target_store_mode": str(raw_check.get("rollout_target_store_mode") or ""),
            "rollout_confirmation_missing_sections": self._normalize_string_list(
                raw_check.get("rollout_confirmation_missing_sections")
            ),
            "rollout_confirmation_production_rollout_confirmed": raw_check.get(
                "rollout_confirmation_production_rollout_confirmed"
            ),
            "rollout_confirmation_input_contract_version": str(
                raw_check.get("rollout_confirmation_input_contract_version") or ""
            ),
            "rollout_confirmation_input_source_status": str(
                raw_check.get("rollout_confirmation_input_source_status") or ""
            ),
            "rollout_confirmation_input_source_kind": str(
                raw_check.get("rollout_confirmation_input_source_kind") or ""
            ),
            "rollout_confirmation_input_decision_id": str(
                raw_check.get("rollout_confirmation_input_decision_id") or ""
            ),
            "rollout_confirmation_input_approved_by": str(
                raw_check.get("rollout_confirmation_input_approved_by") or ""
            ),
            "rollout_confirmation_input_approved_at": str(
                raw_check.get("rollout_confirmation_input_approved_at") or ""
            ),
            "rollout_confirmation_input_target_store_mode": str(
                raw_check.get("rollout_confirmation_input_target_store_mode") or ""
            ),
            "rollout_confirmation_input_rollback_plan_reference": str(
                raw_check.get("rollout_confirmation_input_rollback_plan_reference") or ""
            ),
            "rollout_confirmation_input_fallback_policy_reference": str(
                raw_check.get("rollout_confirmation_input_fallback_policy_reference") or ""
            ),
            "rollout_confirmation_input_renewal_lifecycle_reference": str(
                raw_check.get("rollout_confirmation_input_renewal_lifecycle_reference") or ""
            ),
            "rollout_confirmation_input_auto_claim_decision_reference": str(
                raw_check.get("rollout_confirmation_input_auto_claim_decision_reference") or ""
            ),
            "rollout_confirmation_input_missing_sections": self._normalize_string_list(
                raw_check.get("rollout_confirmation_input_missing_sections")
            ),
            "rollout_confirmation_input_sql_row_lease_is_authority": raw_check.get(
                "rollout_confirmation_input_sql_row_lease_is_authority"
            ),
            "auto_claim_policy_contract_version": str(
                raw_check.get("auto_claim_policy_contract_version") or ""
            ),
            "auto_claim_policy_status": str(raw_check.get("auto_claim_policy_status") or ""),
            "auto_claim_missing_sections": self._normalize_string_list(
                raw_check.get("auto_claim_missing_sections")
            ),
            "auto_claim_enabled_by_default": raw_check.get("auto_claim_enabled_by_default"),
            "auto_claim_descriptor_evidence_fallback": raw_check.get(
                "auto_claim_descriptor_evidence_fallback"
            ),
            "auto_claim_lease_validation_required": raw_check.get(
                "auto_claim_lease_validation_required"
            ),
            "auto_claim_entrypoint_allowlist_ready": raw_check.get(
                "auto_claim_entrypoint_allowlist_ready"
            ),
            "auto_claim_entrypoint_allowlist_contract_version": str(
                raw_check.get("auto_claim_entrypoint_allowlist_contract_version") or ""
            ),
            "auto_claim_entrypoint_allowlist_status": str(
                raw_check.get("auto_claim_entrypoint_allowlist_status") or ""
            ),
            "auto_claim_allowed_entrypoints": self._normalize_string_list(
                raw_check.get("auto_claim_allowed_entrypoints")
            ),
            "auto_claim_missing_entrypoints": self._normalize_string_list(
                raw_check.get("auto_claim_missing_entrypoints")
            ),
            "auto_claim_default_auto_claim_enabled": raw_check.get(
                "auto_claim_default_auto_claim_enabled"
            ),
            "auto_claim_requires_production_gate_ready": raw_check.get(
                "auto_claim_requires_production_gate_ready"
            ),
            "auto_claim_enablement_gate_contract_version": str(
                raw_check.get("auto_claim_enablement_gate_contract_version") or ""
            ),
            "auto_claim_enablement_gate_status": str(
                raw_check.get("auto_claim_enablement_gate_status") or ""
            ),
            "auto_claim_will_auto_claim": raw_check.get("auto_claim_will_auto_claim"),
            "auto_claim_requested_entrypoint": str(
                raw_check.get("auto_claim_requested_entrypoint") or ""
            ),
            "auto_claim_enablement_missing_sections": self._normalize_string_list(
                raw_check.get("auto_claim_enablement_missing_sections")
            ),
            "auto_claim_enablement_blocked_reason": str(
                raw_check.get("auto_claim_enablement_blocked_reason") or ""
            ),
            "ownership_audit_contract_version": str(
                raw_check.get("ownership_audit_contract_version") or ""
            ),
            "ownership_audit_status": str(raw_check.get("ownership_audit_status") or ""),
            "ownership_audit_missing_sections": self._normalize_string_list(
                raw_check.get("ownership_audit_missing_sections")
            ),
            "ownership_audit_compact_evidence": raw_check.get("ownership_audit_compact_evidence"),
            "ownership_audit_operation_history_ready": raw_check.get(
                "ownership_audit_operation_history_ready"
            ),
            "ownership_audit_recovery_operation_link_ready": raw_check.get(
                "ownership_audit_recovery_operation_link_ready"
            ),
            "ownership_audit_timeline_writer_ready": raw_check.get(
                "ownership_audit_timeline_writer_ready"
            ),
            "ownership_audit_idempotent_dedupe_ready": raw_check.get(
                "ownership_audit_idempotent_dedupe_ready"
            ),
            "ownership_audit_authorization_source": raw_check.get(
                "ownership_audit_authorization_source"
            ),
            "enablement_strategy_contract_version": str(
                raw_check.get("enablement_strategy_contract_version") or ""
            ),
            "enablement_strategy_status": str(raw_check.get("enablement_strategy_status") or ""),
            "enablement_strategy_blocking_sections": self._normalize_string_list(
                raw_check.get("enablement_strategy_blocking_sections")
            ),
            "production_default_enabled_requested": raw_check.get(
                "production_default_enabled_requested"
            ),
            "production_default_allowed": raw_check.get("production_default_allowed"),
            "enablement_input_source_contract_version": str(
                raw_check.get("enablement_input_source_contract_version") or ""
            ),
            "enablement_input_source_status": str(
                raw_check.get("enablement_input_source_status") or ""
            ),
            "enablement_input_source_kind": str(
                raw_check.get("enablement_input_source_kind") or ""
            ),
            "enablement_request_id": str(raw_check.get("enablement_request_id") or ""),
            "enablement_requested_by": str(raw_check.get("enablement_requested_by") or ""),
            "enablement_requested_at": str(raw_check.get("enablement_requested_at") or ""),
            "enablement_target_store_mode": str(
                raw_check.get("enablement_target_store_mode") or ""
            ),
            "enablement_rollout_artifact": str(
                raw_check.get("enablement_rollout_artifact") or ""
            ),
            "enablement_vendor_lock_decision_id": str(
                raw_check.get("enablement_vendor_lock_decision_id") or ""
            ),
            "enablement_renewal_lifecycle_reference": str(
                raw_check.get("enablement_renewal_lifecycle_reference") or ""
            ),
            "enablement_auto_claim_decision_reference": str(
                raw_check.get("enablement_auto_claim_decision_reference") or ""
            ),
            "enablement_audit_evidence_reference": str(
                raw_check.get("enablement_audit_evidence_reference") or ""
            ),
            "enablement_rollback_plan_reference": str(
                raw_check.get("enablement_rollback_plan_reference") or ""
            ),
            "enablement_fallback_policy_reference": str(
                raw_check.get("enablement_fallback_policy_reference") or ""
            ),
            "enablement_input_source_ready": raw_check.get("enablement_input_source_ready"),
            "enablement_input_source_missing_sections": self._normalize_string_list(
                raw_check.get("enablement_input_source_missing_sections")
            ),
            "enablement_explicit_required": raw_check.get("enablement_explicit_required"),
            "enablement_all_required_sections_ready": raw_check.get(
                "enablement_all_required_sections_ready"
            ),
            "enablement_fail_closed_when_blocked": raw_check.get(
                "enablement_fail_closed_when_blocked"
            ),
            "enablement_sql_row_lease_not_default_authority": raw_check.get(
                "enablement_sql_row_lease_not_default_authority"
            ),
            "configurable_knob_present": raw_check.get("configurable_knob_present"),
            "hot_reloadable_knob_present": raw_check.get("hot_reloadable_knob_present"),
            "strict_mode_status": str(raw_check.get("strict_mode_status") or ""),
            "fallback_mode_status": str(raw_check.get("fallback_mode_status") or ""),
            "attempt_number": self._coerce_optional_non_negative_int(raw_check.get("attempt_number")),
            "max_attempts": self._coerce_optional_non_negative_int(raw_check.get("max_attempts")),
            "retry_status": str(raw_check.get("retry_status") or ""),
            "retryable": raw_check.get("retryable"),
            "terminal": raw_check.get("terminal"),
            "recovery_reason": str(raw_check.get("recovery_reason") or ""),
            "idempotency_key_present": raw_check.get("idempotency_key_present"),
            "gate_status": str(raw_check.get("gate_status") or ""),
            "allowed": raw_check.get("allowed"),
            "gate_failure_reason": str(raw_check.get("gate_failure_reason") or ""),
            "blocker_count": self._coerce_optional_non_negative_int(raw_check.get("blocker_count")),
            "recommended_next_step": str(raw_check.get("recommended_next_step") or ""),
            "prerequisites_contract_version": str(raw_check.get("prerequisites_contract_version") or ""),
            "prerequisites_status": str(raw_check.get("prerequisites_status") or ""),
            "prerequisites_ready": raw_check.get("prerequisites_ready"),
            "prerequisites_requirement_count": self._coerce_optional_non_negative_int(
                raw_check.get("prerequisites_requirement_count")
            ),
            "prerequisites_missing_requirement_count": self._coerce_optional_non_negative_int(
                raw_check.get("prerequisites_missing_requirement_count")
            ),
            "prerequisites_missing_requirements": self._normalize_string_list(
                raw_check.get("prerequisites_missing_requirements")
            ),
            "explicit_executor_binding_status": str(raw_check.get("explicit_executor_binding_status") or ""),
            "explicit_executor_binding_ready": raw_check.get("explicit_executor_binding_ready"),
            "explicit_executor_binding_source": str(raw_check.get("explicit_executor_binding_source") or ""),
            "explicit_executor_binding_missing": raw_check.get("explicit_executor_binding_missing"),
            "opt_in_explicit_executor_binding_status": str(
                raw_check.get("opt_in_explicit_executor_binding_status") or ""
            ),
            "opt_in_explicit_executor_binding_ready": raw_check.get(
                "opt_in_explicit_executor_binding_ready"
            ),
            "opt_in_explicit_executor_binding_source": str(
                raw_check.get("opt_in_explicit_executor_binding_source") or ""
            ),
            "opt_in_explicit_executor_binding_backend": str(
                raw_check.get("opt_in_explicit_executor_binding_backend") or ""
            ),
            "opt_in_skeleton_execution_status": str(raw_check.get("opt_in_skeleton_execution_status") or ""),
            "opt_in_skeleton_will_execute": raw_check.get("opt_in_skeleton_will_execute"),
            "opt_in_skeleton_execution_mode": str(raw_check.get("opt_in_skeleton_execution_mode") or ""),
            "dispatch_status": str(raw_check.get("dispatch_status") or ""),
            "dispatch_ready": raw_check.get("dispatch_ready"),
            "will_dispatch": raw_check.get("will_dispatch"),
            "backend_dispatch_ready": raw_check.get("backend_dispatch_ready"),
            "relationship_seam_preserved": raw_check.get("relationship_seam_preserved"),
            "dispatch_blocker_count": self._coerce_optional_non_negative_int(raw_check.get("dispatch_blocker_count")),
            "dispatch_blockers": self._normalize_string_list(raw_check.get("dispatch_blockers")),
            "opt_in_dispatch_status": str(raw_check.get("opt_in_dispatch_status") or ""),
            "opt_in_dispatch_ready": raw_check.get("opt_in_dispatch_ready"),
            "opt_in_will_dispatch": raw_check.get("opt_in_will_dispatch"),
            "opt_in_backend_dispatch_ready": raw_check.get("opt_in_backend_dispatch_ready"),
            "dispatch_attempt_handoff_status": str(
                raw_check.get("dispatch_attempt_handoff_status") or ""
            ),
            "dispatch_attempt_handoff_ready": raw_check.get("dispatch_attempt_handoff_ready"),
            "dispatch_attempt_handoff_missing_sections": self._normalize_string_list(
                raw_check.get("dispatch_attempt_handoff_missing_sections")
            ),
            "dispatch_attempt_handoff_will_dispatch": raw_check.get(
                "dispatch_attempt_handoff_will_dispatch"
            ),
            "opt_in_dispatch_attempt_handoff_status": str(
                raw_check.get("opt_in_dispatch_attempt_handoff_status") or ""
            ),
            "opt_in_dispatch_attempt_handoff_ready": raw_check.get(
                "opt_in_dispatch_attempt_handoff_ready"
            ),
            "opt_in_attempt_envelope_supported": raw_check.get(
                "opt_in_attempt_envelope_supported"
            ),
            "opt_in_attempt_validation_ready": raw_check.get(
                "opt_in_attempt_validation_ready"
            ),
            "opt_in_attempt_will_dispatch": raw_check.get("opt_in_attempt_will_dispatch"),
            "opt_in_unsafe_payload_guard_ready": raw_check.get(
                "opt_in_unsafe_payload_guard_ready"
            ),
            "unsafe_payload_guard_status": str(raw_check.get("unsafe_payload_guard_status") or ""),
            "unsafe_payload_guard_ready": raw_check.get("unsafe_payload_guard_ready"),
            "unsafe_payload_keys": self._normalize_string_list(raw_check.get("unsafe_payload_keys")),
            "ready_handoff_status": str(raw_check.get("ready_handoff_status") or ""),
            "ready_handoff_ready": raw_check.get("ready_handoff_ready"),
            "ready_output_ref_present": raw_check.get("ready_output_ref_present"),
            "ready_audit_evidence_present": raw_check.get("ready_audit_evidence_present"),
            "ready_backend_result_schema_valid": raw_check.get(
                "ready_backend_result_schema_valid"
            ),
            "ready_parent_merge_performed": raw_check.get("ready_parent_merge_performed"),
            "ready_merge_authorization": raw_check.get("ready_merge_authorization"),
            "ready_retry_scheduled": raw_check.get("ready_retry_scheduled"),
            "ready_production_dispatch_authorized": raw_check.get(
                "ready_production_dispatch_authorized"
            ),
            "blocked_handoff_status": str(raw_check.get("blocked_handoff_status") or ""),
            "blocked_dispatcher_reason": str(raw_check.get("blocked_dispatcher_reason") or ""),
            "blocked_missing_sections": self._normalize_string_list(
                raw_check.get("blocked_missing_sections")
            ),
            "malformed_handoff_status": str(raw_check.get("malformed_handoff_status") or ""),
            "malformed_missing_sections": self._normalize_string_list(
                raw_check.get("malformed_missing_sections")
            ),
            "success_policy_status": str(raw_check.get("success_policy_status") or ""),
            "success_retry_policy_status": str(raw_check.get("success_retry_policy_status") or ""),
            "success_retry_scheduled": raw_check.get("success_retry_scheduled"),
            "success_will_retry": raw_check.get("success_will_retry"),
            "retryable_policy_status": str(raw_check.get("retryable_policy_status") or ""),
            "retryable_retry_policy_status": str(raw_check.get("retryable_retry_policy_status") or ""),
            "retryable_audit_evidence_present": raw_check.get("retryable_audit_evidence_present"),
            "retryable_idempotency_evidence_present": raw_check.get(
                "retryable_idempotency_evidence_present"
            ),
            "retryable_scheduler_required": raw_check.get("retryable_scheduler_required"),
            "retryable_retry_reason": str(raw_check.get("retryable_retry_reason") or ""),
            "retryable_retry_scheduled": raw_check.get("retryable_retry_scheduled"),
            "retryable_will_retry": raw_check.get("retryable_will_retry"),
            "terminal_policy_status": str(raw_check.get("terminal_policy_status") or ""),
            "terminal_retry_policy_status": str(raw_check.get("terminal_retry_policy_status") or ""),
            "terminal_reason": str(raw_check.get("terminal_reason") or ""),
            "terminal_will_retry": raw_check.get("terminal_will_retry"),
            "missing_idempotency_status": str(raw_check.get("missing_idempotency_status") or ""),
            "missing_idempotency_missing_sections": self._normalize_string_list(
                raw_check.get("missing_idempotency_missing_sections")
            ),
            "missing_idempotency_retry_scheduled": raw_check.get(
                "missing_idempotency_retry_scheduled"
            ),
            "default_status": str(raw_check.get("default_status") or ""),
            "default_eligible": raw_check.get("default_eligible"),
            "default_will_execute": raw_check.get("default_will_execute"),
            "production_gate_contract_version": str(raw_check.get("production_gate_contract_version") or ""),
            "production_gate_status": str(raw_check.get("production_gate_status") or ""),
            "production_gate_missing_sections": self._normalize_string_list(
                raw_check.get("production_gate_missing_sections")
            ),
            "production_gate_blocked_reason": str(raw_check.get("production_gate_blocked_reason") or ""),
            "production_automatic_retry_enabled_by_default": raw_check.get(
                "production_automatic_retry_enabled_by_default"
            ),
            "production_automatic_will_execute": raw_check.get("production_automatic_will_execute"),
            "default_blocked_reason": str(raw_check.get("default_blocked_reason") or ""),
            "default_will_dispatch": raw_check.get("default_will_dispatch"),
            "blocked_reason": str(raw_check.get("blocked_reason") or ""),
            "blocked_will_dispatch": raw_check.get("blocked_will_dispatch"),
            "enabled_status": str(raw_check.get("enabled_status") or ""),
            "enabled_will_execute": raw_check.get("enabled_will_execute"),
            "enabled_will_dispatch": raw_check.get("enabled_will_dispatch"),
            "ready_adapter_contract": raw_check.get("ready_adapter_contract"),
            "ready_sandbox_guard": raw_check.get("ready_sandbox_guard"),
            "ready_audit": raw_check.get("ready_audit"),
            "ready_idempotency": raw_check.get("ready_idempotency"),
            "missing_guard_fail_closed": raw_check.get("missing_guard_fail_closed"),
            "missing_guard_count": self._coerce_optional_non_negative_int(
                raw_check.get("missing_guard_count")
            ),
            "unsafe_payload_blocked": raw_check.get("unsafe_payload_blocked"),
            "unsafe_blocked_reason": str(raw_check.get("unsafe_blocked_reason") or ""),
            "compact_attempt_valid": raw_check.get("compact_attempt_valid"),
            "latest_operation_status": str(raw_check.get("latest_operation_status") or ""),
            "previous_operation_id_present": raw_check.get("previous_operation_id_present"),
            "backend_result_status": str(raw_check.get("backend_result_status") or ""),
            "backend_invocation_count": self._coerce_optional_non_negative_int(
                raw_check.get("backend_invocation_count")
            ),
            "default_worker_enabled": raw_check.get("default_worker_enabled"),
            "recording_state": str(raw_check.get("recording_state") or ""),
            "stage_count": self._coerce_optional_non_negative_int(raw_check.get("stage_count")),
            "recent_event_count": self._coerce_optional_non_negative_int(raw_check.get("recent_event_count")),
        }

    def _build_approval_lifecycle_recovery_coverage(self, check: Mapping[str, Any]) -> Dict[str, Any]:
        replayed_submission_status = str(check.get("replayed_submission_status") or "").strip()
        ignored_submission_status = str(check.get("ignored_submission_status") or "").strip()
        resolved_recovery_reason = str(check.get("resolved_recovery_reason") or "").strip()
        alignment_smoke = self._is_approval_lifecycle_recovery_aligned(
            bool(check.get("ok")) if check else False,
            replayed_submission_status,
            ignored_submission_status,
            resolved_recovery_reason,
        )
        return {
            "alignment_smoke": alignment_smoke,
            "replayed_submission_status": replayed_submission_status,
            "ignored_submission_status": ignored_submission_status,
            "resolved_recovery_reason": resolved_recovery_reason,
        }

    def _normalize_approval_lifecycle_recovery_coverage(self, coverage: Mapping[str, Any]) -> Dict[str, Any]:
        replayed_submission_status = str(coverage.get("replayed_submission_status") or "").strip()
        ignored_submission_status = str(coverage.get("ignored_submission_status") or "").strip()
        resolved_recovery_reason = str(coverage.get("resolved_recovery_reason") or "").strip()
        return {
            "alignment_smoke": self._is_approval_lifecycle_recovery_aligned(
                self._coerce_truthy_flag(coverage.get("alignment_smoke")),
                replayed_submission_status,
                ignored_submission_status,
                resolved_recovery_reason,
            ),
            "replayed_submission_status": replayed_submission_status,
            "ignored_submission_status": ignored_submission_status,
            "resolved_recovery_reason": resolved_recovery_reason,
        }

    def _is_approval_lifecycle_recovery_aligned(
        self,
        alignment_smoke: bool,
        replayed_submission_status: str,
        ignored_submission_status: str,
        resolved_recovery_reason: str,
    ) -> bool:
        return (
            bool(alignment_smoke)
            and replayed_submission_status == "replayed"
            and ignored_submission_status == "ignored"
            and resolved_recovery_reason == "already_resolved"
        )

    def _build_approved_tool_execution_coverage(self, check: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "bridge_smoke": bool(check.get("ok")) if check else False,
            "approved_tool_call_count": self._coerce_optional_non_negative_int(check.get("approved_tool_call_count")) or 0,
            "approved_policy_original_status": str(check.get("approved_policy_original_status") or ""),
            "approved_policy_override_status": str(check.get("approved_policy_override_status") or ""),
            "deny_override_status": str(check.get("deny_override_status") or ""),
            "deny_tool_call_count": self._coerce_optional_non_negative_int(check.get("deny_tool_call_count")) or 0,
        }

    def _normalize_approved_tool_execution_coverage(self, coverage: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "bridge_smoke": self._coerce_truthy_flag(coverage.get("bridge_smoke")),
            "approved_tool_call_count": self._coerce_optional_non_negative_int(coverage.get("approved_tool_call_count")) or 0,
            "approved_policy_original_status": str(coverage.get("approved_policy_original_status") or ""),
            "approved_policy_override_status": str(coverage.get("approved_policy_override_status") or ""),
            "deny_override_status": str(coverage.get("deny_override_status") or ""),
            "deny_tool_call_count": self._coerce_optional_non_negative_int(coverage.get("deny_tool_call_count")) or 0,
        }

    def _build_sdk_tool_runtime_execution_coverage(self, check: Mapping[str, Any]) -> Dict[str, Any]:
        return self._normalize_sdk_tool_runtime_execution_coverage({
            "bridge_smoke": bool(check.get("ok")) if check else False,
            "auto_tool_call_count": self._coerce_optional_non_negative_int(check.get("auto_tool_call_count")) or 0,
            "auto_tool_history_count": self._coerce_optional_non_negative_int(check.get("auto_tool_history_count")) or 0,
            "approved_tool_call_count": self._coerce_optional_non_negative_int(check.get("approved_tool_call_count")) or 0,
            "approved_policy_original_status": str(check.get("approved_policy_original_status") or ""),
            "approved_policy_override_status": str(check.get("approved_policy_override_status") or ""),
            "deny_override_status": str(check.get("deny_override_status") or ""),
            "deny_tool_call_count": self._coerce_optional_non_negative_int(check.get("deny_tool_call_count")) or 0,
        })

    def _normalize_sdk_tool_runtime_execution_coverage(self, coverage: Mapping[str, Any]) -> Dict[str, Any]:
        auto_tool_call_count = self._coerce_optional_non_negative_int(coverage.get("auto_tool_call_count")) or 0
        auto_tool_history_count = self._coerce_optional_non_negative_int(coverage.get("auto_tool_history_count")) or 0
        approved_tool_call_count = self._coerce_optional_non_negative_int(coverage.get("approved_tool_call_count")) or 0
        approved_policy_original_status = str(coverage.get("approved_policy_original_status") or "")
        approved_policy_override_status = str(coverage.get("approved_policy_override_status") or "")
        deny_override_status = str(coverage.get("deny_override_status") or "")
        deny_tool_call_count = self._coerce_optional_non_negative_int(coverage.get("deny_tool_call_count")) or 0
        bridge_smoke = (
            self._coerce_truthy_flag(coverage.get("bridge_smoke"))
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

    def _build_tool_runtime_timeout_retry_coverage(self, check: Mapping[str, Any]) -> Dict[str, Any]:
        return self._normalize_tool_runtime_timeout_retry_coverage({
            "timeout_retry_smoke": bool(check.get("ok")) if check else False,
            "retry_policy": str(check.get("retry_policy") or ""),
            "timeout_enforcement": str(check.get("timeout_enforcement") or ""),
            "recovered_status": str(check.get("recovered_status") or ""),
            "recovered_retry_status": str(check.get("recovered_retry_status") or ""),
            "recovered_attempt_count": self._coerce_optional_non_negative_int(check.get("recovered_attempt_count")) or 0,
            "exhausted_status": str(check.get("exhausted_status") or ""),
            "exhausted_retry_status": str(check.get("exhausted_retry_status") or ""),
            "exhausted_attempt_count": self._coerce_optional_non_negative_int(check.get("exhausted_attempt_count")) or 0,
            "timeout_status": str(check.get("timeout_status") or ""),
            "timeout_metadata_status": str(check.get("timeout_metadata_status") or ""),
            "timeout_metadata_enforcement": str(check.get("timeout_metadata_enforcement") or ""),
            "hard_cancellation_claimed": check.get("hard_cancellation_claimed"),
            "sandbox_execution_claimed": check.get("sandbox_execution_claimed"),
            "worker_timeout_claimed": check.get("worker_timeout_claimed"),
        })

    def _normalize_tool_runtime_timeout_retry_coverage(self, coverage: Mapping[str, Any]) -> Dict[str, Any]:
        retry_policy = str(coverage.get("retry_policy") or "")
        timeout_enforcement = str(coverage.get("timeout_enforcement") or "")
        recovered_status = str(coverage.get("recovered_status") or "")
        recovered_retry_status = str(coverage.get("recovered_retry_status") or "")
        recovered_attempt_count = self._coerce_optional_non_negative_int(coverage.get("recovered_attempt_count")) or 0
        exhausted_status = str(coverage.get("exhausted_status") or "")
        exhausted_retry_status = str(coverage.get("exhausted_retry_status") or "")
        exhausted_attempt_count = self._coerce_optional_non_negative_int(coverage.get("exhausted_attempt_count")) or 0
        timeout_status = str(coverage.get("timeout_status") or "")
        timeout_metadata_status = str(coverage.get("timeout_metadata_status") or "")
        timeout_metadata_enforcement = str(coverage.get("timeout_metadata_enforcement") or "")
        hard_cancellation_claimed = self._coerce_truthy_flag(coverage.get("hard_cancellation_claimed"))
        sandbox_execution_claimed = self._coerce_truthy_flag(coverage.get("sandbox_execution_claimed"))
        worker_timeout_claimed = self._coerce_truthy_flag(coverage.get("worker_timeout_claimed"))
        timeout_retry_smoke = (
            self._coerce_truthy_flag(coverage.get("timeout_retry_smoke"))
            and retry_policy == "sync_exception_retry"
            and timeout_enforcement == "post_call_elapsed_check"
            and recovered_status == "ok"
            and recovered_retry_status == "recovered"
            and recovered_attempt_count == 2
            and exhausted_status == "error"
            and exhausted_retry_status == "exhausted"
            and exhausted_attempt_count == 2
            and timeout_status == "timeout"
            and timeout_metadata_status == "exceeded"
            and timeout_metadata_enforcement == "post_call_elapsed_check"
            and not hard_cancellation_claimed
            and not sandbox_execution_claimed
            and not worker_timeout_claimed
        )
        return {
            "timeout_retry_smoke": timeout_retry_smoke,
            "retry_policy": retry_policy,
            "timeout_enforcement": timeout_enforcement,
            "recovered_status": recovered_status,
            "recovered_retry_status": recovered_retry_status,
            "recovered_attempt_count": recovered_attempt_count,
            "exhausted_status": exhausted_status,
            "exhausted_retry_status": exhausted_retry_status,
            "exhausted_attempt_count": exhausted_attempt_count,
            "timeout_status": timeout_status,
            "timeout_metadata_status": timeout_metadata_status,
            "timeout_metadata_enforcement": timeout_metadata_enforcement,
            "hard_cancellation_claimed": hard_cancellation_claimed,
            "sandbox_execution_claimed": sandbox_execution_claimed,
            "worker_timeout_claimed": worker_timeout_claimed,
        }

    def _build_checkpoint_resume_cursor_coverage(self, check: Mapping[str, Any]) -> Dict[str, Any]:
        return self._normalize_checkpoint_resume_cursor_coverage({
            "cursor_smoke": bool(check.get("ok")) if check else False,
            "checkpoint_status": str(check.get("checkpoint_status") or ""),
            "checkpoint_kind": str(check.get("checkpoint_kind") or ""),
            "cursor_status": str(check.get("cursor_status") or ""),
            "cursor_entrypoint": str(check.get("cursor_entrypoint") or ""),
            "cursor_recovery_reason": str(check.get("cursor_recovery_reason") or ""),
        })

    def _normalize_checkpoint_resume_cursor_coverage(self, coverage: Mapping[str, Any]) -> Dict[str, Any]:
        checkpoint_status = str(coverage.get("checkpoint_status") or "")
        checkpoint_kind = str(coverage.get("checkpoint_kind") or "")
        cursor_status = str(coverage.get("cursor_status") or "")
        cursor_entrypoint = str(coverage.get("cursor_entrypoint") or "")
        cursor_recovery_reason = str(coverage.get("cursor_recovery_reason") or "")
        cursor_smoke = (
            self._coerce_truthy_flag(coverage.get("cursor_smoke"))
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

    def _build_embedded_sdk_persistence_coverage(self, check: Mapping[str, Any]) -> Dict[str, Any]:
        return self._normalize_embedded_sdk_persistence_coverage({
            "persistence_smoke": bool(check.get("ok")) if check else False,
            "contract_version": str(check.get("contract_version") or ""),
            "memory_posture": str(check.get("memory_posture") or ""),
            "durable_posture": str(check.get("durable_posture") or ""),
            "degraded_posture": str(check.get("degraded_posture") or ""),
            "memory_cross_process_block_reason": str(check.get("memory_cross_process_block_reason") or ""),
            "degraded_cross_process_block_reason": str(check.get("degraded_cross_process_block_reason") or ""),
            "durable_cross_process_candidate": check.get("durable_cross_process_candidate"),
            "production_recovery_gate_contract_version": str(
                check.get("production_recovery_gate_contract_version") or ""
            ),
            "production_recovery_gate_status": str(check.get("production_recovery_gate_status") or ""),
            "production_recovery_gate_missing_sections": (
                check.get("production_recovery_gate_missing_sections")
                if isinstance(check.get("production_recovery_gate_missing_sections"), list)
                else []
            ),
            "production_recovery_default_enabled": check.get("production_recovery_default_enabled"),
            "production_recovery_worker_ownership_gate_contract_version": str(
                check.get("production_recovery_worker_ownership_gate_contract_version") or ""
            ),
            "production_recovery_worker_ownership_gate_status": str(
                check.get("production_recovery_worker_ownership_gate_status") or ""
            ),
            "production_recovery_worker_ownership_default_enabled": check.get(
                "production_recovery_worker_ownership_default_enabled"
            ),
            "production_recovery_worker_ownership_missing_sections": (
                check.get("production_recovery_worker_ownership_missing_sections")
                if isinstance(check.get("production_recovery_worker_ownership_missing_sections"), list)
                else []
            ),
        })

    def _normalize_embedded_sdk_persistence_coverage(self, coverage: Mapping[str, Any]) -> Dict[str, Any]:
        memory_posture = str(coverage.get("memory_posture") or "")
        durable_posture = str(coverage.get("durable_posture") or "")
        degraded_posture = str(coverage.get("degraded_posture") or "")
        memory_block_reason = str(coverage.get("memory_cross_process_block_reason") or "")
        degraded_block_reason = str(coverage.get("degraded_cross_process_block_reason") or "")
        durable_cross_process_candidate = self._coerce_truthy_flag(coverage.get("durable_cross_process_candidate"))
        production_gate_contract_version = str(coverage.get("production_recovery_gate_contract_version") or "")
        production_gate_status = str(coverage.get("production_recovery_gate_status") or "")
        production_gate_missing_sections = (
            coverage.get("production_recovery_gate_missing_sections")
            if isinstance(coverage.get("production_recovery_gate_missing_sections"), list)
            else []
        )
        production_default_enabled = self._coerce_truthy_flag(coverage.get("production_recovery_default_enabled"))
        worker_ownership_gate_contract_version = str(
            coverage.get("production_recovery_worker_ownership_gate_contract_version") or ""
        )
        worker_ownership_gate_status = str(
            coverage.get("production_recovery_worker_ownership_gate_status") or ""
        )
        worker_ownership_default_enabled = self._coerce_truthy_flag(
            coverage.get("production_recovery_worker_ownership_default_enabled")
        )
        worker_ownership_missing_sections = (
            coverage.get("production_recovery_worker_ownership_missing_sections")
            if isinstance(coverage.get("production_recovery_worker_ownership_missing_sections"), list)
            else []
        )
        persistence_smoke = (
            self._coerce_truthy_flag(coverage.get("persistence_smoke"))
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
            "contract_version": str(coverage.get("contract_version") or ""),
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

    def _build_worker_ownership_store_mode_coverage(self, check: Mapping[str, Any]) -> Dict[str, Any]:
        return self._normalize_worker_ownership_store_mode_coverage({
            "mode_smoke": bool(check.get("ok")) if check else False,
            "default_mode": str(check.get("default_mode") or ""),
            "default_mode_source": str(check.get("default_mode_source") or ""),
            "default_adapter_kind": str(check.get("default_adapter_kind") or ""),
            "default_durable": check.get("default_durable"),
            "production_gate_contract_version": str(check.get("production_gate_contract_version") or ""),
            "production_gate_status": str(check.get("production_gate_status") or ""),
            "production_gate_missing_sections": (
                check.get("production_gate_missing_sections")
                if isinstance(check.get("production_gate_missing_sections"), list)
                else []
            ),
            "production_default_enabled": check.get("production_default_enabled"),
            "vendor_lock_contract_version": str(check.get("vendor_lock_contract_version") or ""),
            "vendor_lock_status": str(check.get("vendor_lock_status") or ""),
            "vendor_lock_missing_sections": (
                check.get("vendor_lock_missing_sections")
                if isinstance(check.get("vendor_lock_missing_sections"), list)
                else []
            ),
            "vendor_lock_current_posture": str(check.get("vendor_lock_current_posture") or ""),
            "vendor_lock_sql_row_lease_fencing": check.get("vendor_lock_sql_row_lease_fencing"),
            "vendor_lock_sql_row_lease_is_vendor_lock": check.get(
                "vendor_lock_sql_row_lease_is_vendor_lock"
            ),
            "vendor_lock_adapter_present": check.get("vendor_lock_adapter_present"),
            "vendor_lock_adapter_contract_version": str(
                check.get("vendor_lock_adapter_contract_version") or ""
            ),
            "vendor_lock_adapter_status": str(check.get("vendor_lock_adapter_status") or ""),
            "vendor_lock_adapter_kind": str(check.get("vendor_lock_adapter_kind") or ""),
            "vendor_lock_adapter_target_backend": str(
                check.get("vendor_lock_adapter_target_backend") or ""
            ),
            "vendor_lock_adapter_scope": str(check.get("vendor_lock_adapter_scope") or ""),
            "vendor_lock_adapter_fencing_strategy": str(
                check.get("vendor_lock_adapter_fencing_strategy") or ""
            ),
            "vendor_lock_adapter_ttl_renewal_strategy": str(
                check.get("vendor_lock_adapter_ttl_renewal_strategy") or ""
            ),
            "vendor_lock_adapter_failover_strategy": str(
                check.get("vendor_lock_adapter_failover_strategy") or ""
            ),
            "vendor_lock_adapter_stale_cleanup_strategy": str(
                check.get("vendor_lock_adapter_stale_cleanup_strategy") or ""
            ),
            "vendor_lock_adapter_acquire_supported": check.get(
                "vendor_lock_adapter_acquire_supported"
            ),
            "vendor_lock_adapter_renew_supported": check.get(
                "vendor_lock_adapter_renew_supported"
            ),
            "vendor_lock_adapter_release_supported": check.get(
                "vendor_lock_adapter_release_supported"
            ),
            "vendor_lock_adapter_probe_supported": check.get(
                "vendor_lock_adapter_probe_supported"
            ),
            "vendor_lock_adapter_production_allowed": check.get(
                "vendor_lock_adapter_production_allowed"
            ),
            "vendor_lock_adapter_sql_row_lease_is_vendor_lock": check.get(
                "vendor_lock_adapter_sql_row_lease_is_vendor_lock"
            ),
            "vendor_lock_adapter_missing_sections": (
                check.get("vendor_lock_adapter_missing_sections")
                if isinstance(check.get("vendor_lock_adapter_missing_sections"), list)
                else []
            ),
            "postgres_probe_contract_version": str(
                check.get("postgres_probe_contract_version") or ""
            ),
            "postgres_probe_status": str(check.get("postgres_probe_status") or ""),
            "postgres_probe_missing_sections": (
                check.get("postgres_probe_missing_sections")
                if isinstance(check.get("postgres_probe_missing_sections"), list)
                else []
            ),
            "postgres_probe_executes": check.get("postgres_probe_executes"),
            "postgres_probe_sql_row_lease_is_vendor_lock": check.get(
                "postgres_probe_sql_row_lease_is_vendor_lock"
            ),
            "postgres_probe_ready_status": str(check.get("postgres_probe_ready_status") or ""),
            "postgres_probe_ready_executes": check.get("postgres_probe_ready_executes"),
            "postgres_execution_seam_contract_version": str(
                check.get("postgres_execution_seam_contract_version") or ""
            ),
            "postgres_execution_default_status": str(
                check.get("postgres_execution_default_status") or ""
            ),
            "postgres_execution_default_executor_bound": check.get(
                "postgres_execution_default_executor_bound"
            ),
            "postgres_execution_default_enabled_by_default": check.get(
                "postgres_execution_default_enabled_by_default"
            ),
            "postgres_execution_default_production_allowed": check.get(
                "postgres_execution_default_production_allowed"
            ),
            "postgres_execution_default_missing_sections": (
                check.get("postgres_execution_default_missing_sections")
                if isinstance(check.get("postgres_execution_default_missing_sections"), list)
                else []
            ),
            "postgres_execution_default_probe_status": str(
                check.get("postgres_execution_default_probe_status") or ""
            ),
            "postgres_execution_default_probe_executed": check.get(
                "postgres_execution_default_probe_executed"
            ),
            "postgres_execution_opt_in_status": str(
                check.get("postgres_execution_opt_in_status") or ""
            ),
            "postgres_execution_opt_in_executor_bound": check.get(
                "postgres_execution_opt_in_executor_bound"
            ),
            "postgres_execution_opt_in_enabled_by_default": check.get(
                "postgres_execution_opt_in_enabled_by_default"
            ),
            "postgres_execution_opt_in_production_allowed": check.get(
                "postgres_execution_opt_in_production_allowed"
            ),
            "postgres_execution_opt_in_probe_status": str(
                check.get("postgres_execution_opt_in_probe_status") or ""
            ),
            "postgres_execution_opt_in_probe_executed": check.get(
                "postgres_execution_opt_in_probe_executed"
            ),
            "postgres_execution_opt_in_acquire_status": str(
                check.get("postgres_execution_opt_in_acquire_status") or ""
            ),
            "postgres_execution_opt_in_acquire_executed": check.get(
                "postgres_execution_opt_in_acquire_executed"
            ),
            "postgres_execution_opt_in_acquired": check.get(
                "postgres_execution_opt_in_acquired"
            ),
            "postgres_execution_opt_in_envelope_count": check.get(
                "postgres_execution_opt_in_envelope_count"
            ),
            "postgres_rollout_consumer_contract_version": str(
                check.get("postgres_rollout_consumer_contract_version") or ""
            ),
            "postgres_rollout_consumer_default_status": str(
                check.get("postgres_rollout_consumer_default_status") or ""
            ),
            "postgres_rollout_consumer_default_missing_sections": (
                check.get("postgres_rollout_consumer_default_missing_sections")
                if isinstance(
                    check.get("postgres_rollout_consumer_default_missing_sections"), list
                )
                else []
            ),
            "postgres_rollout_consumer_default_will_enable_default": check.get(
                "postgres_rollout_consumer_default_will_enable_default"
            ),
            "postgres_rollout_consumer_default_executes_lock": check.get(
                "postgres_rollout_consumer_default_executes_lock"
            ),
            "postgres_rollout_consumer_ready_status": str(
                check.get("postgres_rollout_consumer_ready_status") or ""
            ),
            "postgres_rollout_consumer_ready_target_backend": str(
                check.get("postgres_rollout_consumer_ready_target_backend") or ""
            ),
            "postgres_rollout_consumer_ready_lock_adapter_kind": str(
                check.get("postgres_rollout_consumer_ready_lock_adapter_kind") or ""
            ),
            "postgres_rollout_consumer_ready_will_enable_default": check.get(
                "postgres_rollout_consumer_ready_will_enable_default"
            ),
            "postgres_rollout_consumer_ready_executes_lock": check.get(
                "postgres_rollout_consumer_ready_executes_lock"
            ),
            "postgres_rollout_consumer_input_source_status": str(
                check.get("postgres_rollout_consumer_input_source_status") or ""
            ),
            "postgres_rollout_consumer_input_source_ready": check.get(
                "postgres_rollout_consumer_input_source_ready"
            ),
            "postgres_rollout_consumer_input_source_kind": str(
                check.get("postgres_rollout_consumer_input_source_kind") or ""
            ),
            "postgres_target_binding_contract_version": str(
                check.get("postgres_target_binding_contract_version") or ""
            ),
            "postgres_target_binding_default_status": str(
                check.get("postgres_target_binding_default_status") or ""
            ),
            "postgres_target_binding_default_missing_sections": (
                check.get("postgres_target_binding_default_missing_sections")
                if isinstance(
                    check.get("postgres_target_binding_default_missing_sections"), list
                )
                else []
            ),
            "postgres_target_binding_default_will_enable_lock": check.get(
                "postgres_target_binding_default_will_enable_lock"
            ),
            "postgres_target_binding_default_executes_lock": check.get(
                "postgres_target_binding_default_executes_lock"
            ),
            "postgres_target_binding_ready_status": str(
                check.get("postgres_target_binding_ready_status") or ""
            ),
            "postgres_target_binding_ready_target_backend": str(
                check.get("postgres_target_binding_ready_target_backend") or ""
            ),
            "postgres_target_binding_ready_lock_adapter_kind": str(
                check.get("postgres_target_binding_ready_lock_adapter_kind") or ""
            ),
            "postgres_target_binding_ready_will_enable_lock": check.get(
                "postgres_target_binding_ready_will_enable_lock"
            ),
            "postgres_target_binding_ready_executes_lock": check.get(
                "postgres_target_binding_ready_executes_lock"
            ),
            "postgres_target_binding_target_input_status": str(
                check.get("postgres_target_binding_target_input_status") or ""
            ),
            "postgres_target_binding_target_decision_status": str(
                check.get("postgres_target_binding_target_decision_status") or ""
            ),
            "postgres_target_binding_target_decision_production_allowed": check.get(
                "postgres_target_binding_target_decision_production_allowed"
            ),
            "postgres_semantics_binding_contract_version": str(
                check.get("postgres_semantics_binding_contract_version") or ""
            ),
            "postgres_semantics_binding_default_status": str(
                check.get("postgres_semantics_binding_default_status") or ""
            ),
            "postgres_semantics_binding_default_missing_sections": (
                check.get("postgres_semantics_binding_default_missing_sections")
                if isinstance(
                    check.get("postgres_semantics_binding_default_missing_sections"), list
                )
                else []
            ),
            "postgres_semantics_binding_default_will_enable_lock": check.get(
                "postgres_semantics_binding_default_will_enable_lock"
            ),
            "postgres_semantics_binding_default_will_update_gate": check.get(
                "postgres_semantics_binding_default_will_update_gate"
            ),
            "postgres_semantics_binding_default_executes_lock": check.get(
                "postgres_semantics_binding_default_executes_lock"
            ),
            "postgres_semantics_binding_ready_status": str(
                check.get("postgres_semantics_binding_ready_status") or ""
            ),
            "postgres_semantics_binding_ready_target_backend": str(
                check.get("postgres_semantics_binding_ready_target_backend") or ""
            ),
            "postgres_semantics_binding_ready_lock_adapter_kind": str(
                check.get("postgres_semantics_binding_ready_lock_adapter_kind") or ""
            ),
            "postgres_semantics_binding_ready_probe_status": str(
                check.get("postgres_semantics_binding_ready_probe_status") or ""
            ),
            "postgres_semantics_binding_ready_adapter_status": str(
                check.get("postgres_semantics_binding_ready_adapter_status") or ""
            ),
            "postgres_semantics_binding_ready_semantics_status": str(
                check.get("postgres_semantics_binding_ready_semantics_status") or ""
            ),
            "postgres_semantics_binding_ready_will_enable_lock": check.get(
                "postgres_semantics_binding_ready_will_enable_lock"
            ),
            "postgres_semantics_binding_ready_will_update_gate": check.get(
                "postgres_semantics_binding_ready_will_update_gate"
            ),
            "postgres_semantics_binding_ready_executes_lock": check.get(
                "postgres_semantics_binding_ready_executes_lock"
            ),
            "postgres_wiring_decision_contract_version": str(
                check.get("postgres_wiring_decision_contract_version") or ""
            ),
            "postgres_wiring_decision_default_status": str(
                check.get("postgres_wiring_decision_default_status") or ""
            ),
            "postgres_wiring_decision_default_missing_sections": (
                check.get("postgres_wiring_decision_default_missing_sections")
                if isinstance(
                    check.get("postgres_wiring_decision_default_missing_sections"), list
                )
                else []
            ),
            "postgres_wiring_decision_default_wiring_allowed": check.get(
                "postgres_wiring_decision_default_wiring_allowed"
            ),
            "postgres_wiring_decision_default_will_update_gate": check.get(
                "postgres_wiring_decision_default_will_update_gate"
            ),
            "postgres_wiring_decision_default_will_enable_lock": check.get(
                "postgres_wiring_decision_default_will_enable_lock"
            ),
            "postgres_wiring_decision_default_executes_lock": check.get(
                "postgres_wiring_decision_default_executes_lock"
            ),
            "postgres_wiring_decision_ready_status": str(
                check.get("postgres_wiring_decision_ready_status") or ""
            ),
            "postgres_wiring_decision_ready_semantics_binding_status": str(
                check.get("postgres_wiring_decision_ready_semantics_binding_status") or ""
            ),
            "postgres_wiring_decision_ready_candidate_status": str(
                check.get("postgres_wiring_decision_ready_candidate_status") or ""
            ),
            "postgres_wiring_decision_ready_wiring_allowed": check.get(
                "postgres_wiring_decision_ready_wiring_allowed"
            ),
            "postgres_wiring_decision_ready_target_backend": str(
                check.get("postgres_wiring_decision_ready_target_backend") or ""
            ),
            "postgres_wiring_decision_ready_lock_adapter_kind": str(
                check.get("postgres_wiring_decision_ready_lock_adapter_kind") or ""
            ),
            "postgres_wiring_decision_ready_will_update_gate": check.get(
                "postgres_wiring_decision_ready_will_update_gate"
            ),
            "postgres_wiring_decision_ready_will_enable_lock": check.get(
                "postgres_wiring_decision_ready_will_enable_lock"
            ),
            "postgres_wiring_decision_ready_executes_lock": check.get(
                "postgres_wiring_decision_ready_executes_lock"
            ),
            "production_dry_run_contract_version": str(
                check.get("production_dry_run_contract_version") or ""
            ),
            "production_dry_run_default_status": str(
                check.get("production_dry_run_default_status") or ""
            ),
            "production_dry_run_default_missing_sections": (
                check.get("production_dry_run_default_missing_sections")
                if isinstance(check.get("production_dry_run_default_missing_sections"), list)
                else []
            ),
            "production_dry_run_default_all_required_ready": check.get(
                "production_dry_run_default_all_required_ready"
            ),
            "production_dry_run_default_would_allow": check.get(
                "production_dry_run_default_would_allow"
            ),
            "production_dry_run_default_will_enable": check.get(
                "production_dry_run_default_will_enable"
            ),
            "production_dry_run_default_executes_lock": check.get(
                "production_dry_run_default_executes_lock"
            ),
            "production_dry_run_default_starts_worker": check.get(
                "production_dry_run_default_starts_worker"
            ),
            "production_dry_run_default_runs_auto_claim": check.get(
                "production_dry_run_default_runs_auto_claim"
            ),
            "production_dry_run_ready_status": str(
                check.get("production_dry_run_ready_status") or ""
            ),
            "production_dry_run_ready_missing_sections": (
                check.get("production_dry_run_ready_missing_sections")
                if isinstance(check.get("production_dry_run_ready_missing_sections"), list)
                else []
            ),
            "production_dry_run_ready_all_required_ready": check.get(
                "production_dry_run_ready_all_required_ready"
            ),
            "production_dry_run_ready_would_allow": check.get(
                "production_dry_run_ready_would_allow"
            ),
            "production_dry_run_ready_will_enable": check.get(
                "production_dry_run_ready_will_enable"
            ),
            "production_dry_run_ready_executes_lock": check.get(
                "production_dry_run_ready_executes_lock"
            ),
            "production_dry_run_ready_starts_worker": check.get(
                "production_dry_run_ready_starts_worker"
            ),
            "production_dry_run_ready_runs_auto_claim": check.get(
                "production_dry_run_ready_runs_auto_claim"
            ),
            "enablement_config_consumer_contract_version": str(
                check.get("enablement_config_consumer_contract_version") or ""
            ),
            "enablement_config_consumer_default_status": str(
                check.get("enablement_config_consumer_default_status") or ""
            ),
            "enablement_config_consumer_default_missing_sections": (
                check.get("enablement_config_consumer_default_missing_sections")
                if isinstance(
                    check.get("enablement_config_consumer_default_missing_sections"),
                    list,
                )
                else []
            ),
            "enablement_config_consumer_default_will_enable": check.get(
                "enablement_config_consumer_default_will_enable"
            ),
            "enablement_config_consumer_default_executes_lock": check.get(
                "enablement_config_consumer_default_executes_lock"
            ),
            "enablement_config_consumer_default_starts_worker": check.get(
                "enablement_config_consumer_default_starts_worker"
            ),
            "enablement_config_consumer_default_runs_auto_claim": check.get(
                "enablement_config_consumer_default_runs_auto_claim"
            ),
            "enablement_config_consumer_ready_status": str(
                check.get("enablement_config_consumer_ready_status") or ""
            ),
            "enablement_config_consumer_ready_missing_sections": (
                check.get("enablement_config_consumer_ready_missing_sections")
                if isinstance(
                    check.get("enablement_config_consumer_ready_missing_sections"),
                    list,
                )
                else []
            ),
            "enablement_config_consumer_ready_target_backend": str(
                check.get("enablement_config_consumer_ready_target_backend") or ""
            ),
            "enablement_config_consumer_ready_lock_adapter_kind": str(
                check.get("enablement_config_consumer_ready_lock_adapter_kind") or ""
            ),
            "enablement_config_consumer_ready_input_source_status": str(
                check.get("enablement_config_consumer_ready_input_source_status") or ""
            ),
            "enablement_config_consumer_ready_dry_run_status": str(
                check.get("enablement_config_consumer_ready_dry_run_status") or ""
            ),
            "enablement_config_consumer_ready_dry_run_would_allow": check.get(
                "enablement_config_consumer_ready_dry_run_would_allow"
            ),
            "enablement_config_consumer_ready_will_enable": check.get(
                "enablement_config_consumer_ready_will_enable"
            ),
            "enablement_config_consumer_ready_executes_lock": check.get(
                "enablement_config_consumer_ready_executes_lock"
            ),
            "enablement_config_consumer_ready_starts_worker": check.get(
                "enablement_config_consumer_ready_starts_worker"
            ),
            "enablement_config_consumer_ready_runs_auto_claim": check.get(
                "enablement_config_consumer_ready_runs_auto_claim"
            ),
            "enablement_config_factory_binding_default_status": str(
                check.get("enablement_config_factory_binding_default_status") or ""
            ),
            "enablement_config_factory_binding_ready_status": str(
                check.get("enablement_config_factory_binding_ready_status") or ""
            ),
            "enablement_config_factory_binding_ready_config_id": str(
                check.get("enablement_config_factory_binding_ready_config_id") or ""
            ),
            "enablement_config_factory_binding_will_enable": check.get(
                "enablement_config_factory_binding_will_enable"
            ),
            "enablement_config_factory_binding_executes_lock": check.get(
                "enablement_config_factory_binding_executes_lock"
            ),
            "enablement_config_factory_binding_starts_worker": check.get(
                "enablement_config_factory_binding_starts_worker"
            ),
            "enablement_config_factory_binding_runs_auto_claim": check.get(
                "enablement_config_factory_binding_runs_auto_claim"
            ),
            "vendor_lock_scope_defined": check.get("vendor_lock_scope_defined"),
            "vendor_lock_fencing_guarantee_defined": check.get(
                "vendor_lock_fencing_guarantee_defined"
            ),
            "vendor_lock_failover_semantics_defined": check.get(
                "vendor_lock_failover_semantics_defined"
            ),
            "vendor_lock_ttl_renewal_semantics_defined": check.get(
                "vendor_lock_ttl_renewal_semantics_defined"
            ),
            "vendor_lock_stale_owner_cleanup_defined": check.get(
                "vendor_lock_stale_owner_cleanup_defined"
            ),
            "vendor_lock_production_allowed": check.get("vendor_lock_production_allowed"),
            "vendor_lock_target_decision_contract_version": str(
                check.get("vendor_lock_target_decision_contract_version") or ""
            ),
            "vendor_lock_target_decision_status": str(
                check.get("vendor_lock_target_decision_status") or ""
            ),
            "vendor_lock_target_decision_recorded": check.get(
                "vendor_lock_target_decision_recorded"
            ),
            "vendor_lock_target_backend": str(check.get("vendor_lock_target_backend") or ""),
            "vendor_lock_target_adapter_kind": str(
                check.get("vendor_lock_target_adapter_kind") or ""
            ),
            "vendor_lock_target_scope": str(check.get("vendor_lock_target_scope") or ""),
            "vendor_lock_target_fencing_strategy": str(
                check.get("vendor_lock_target_fencing_strategy") or ""
            ),
            "vendor_lock_target_ttl_renewal_strategy": str(
                check.get("vendor_lock_target_ttl_renewal_strategy") or ""
            ),
            "vendor_lock_target_failover_strategy": str(
                check.get("vendor_lock_target_failover_strategy") or ""
            ),
            "vendor_lock_target_stale_cleanup_strategy": str(
                check.get("vendor_lock_target_stale_cleanup_strategy") or ""
            ),
            "vendor_lock_target_missing_sections": (
                check.get("vendor_lock_target_missing_sections")
                if isinstance(check.get("vendor_lock_target_missing_sections"), list)
                else []
            ),
            "vendor_lock_target_sql_row_lease_is_vendor_lock": check.get(
                "vendor_lock_target_sql_row_lease_is_vendor_lock"
            ),
            "vendor_lock_target_production_allowed": check.get(
                "vendor_lock_target_production_allowed"
            ),
            "vendor_lock_target_input_contract_version": str(
                check.get("vendor_lock_target_input_contract_version") or ""
            ),
            "vendor_lock_target_input_source_status": str(
                check.get("vendor_lock_target_input_source_status") or ""
            ),
            "vendor_lock_target_input_source_kind": str(
                check.get("vendor_lock_target_input_source_kind") or ""
            ),
            "vendor_lock_target_input_decision_id": str(
                check.get("vendor_lock_target_input_decision_id") or ""
            ),
            "vendor_lock_target_input_approved_by": str(
                check.get("vendor_lock_target_input_approved_by") or ""
            ),
            "vendor_lock_target_input_approved_at": str(
                check.get("vendor_lock_target_input_approved_at") or ""
            ),
            "vendor_lock_target_input_backend": str(
                check.get("vendor_lock_target_input_backend") or ""
            ),
            "vendor_lock_target_input_adapter_kind": str(
                check.get("vendor_lock_target_input_adapter_kind") or ""
            ),
            "vendor_lock_target_input_rollout_artifact": str(
                check.get("vendor_lock_target_input_rollout_artifact") or ""
            ),
            "vendor_lock_target_input_config_key": str(
                check.get("vendor_lock_target_input_config_key") or ""
            ),
            "vendor_lock_target_input_manual_approval_reference": str(
                check.get("vendor_lock_target_input_manual_approval_reference") or ""
            ),
            "vendor_lock_target_input_missing_sections": (
                check.get("vendor_lock_target_input_missing_sections")
                if isinstance(check.get("vendor_lock_target_input_missing_sections"), list)
                else []
            ),
            "vendor_lock_target_input_sql_row_lease_is_vendor_lock": check.get(
                "vendor_lock_target_input_sql_row_lease_is_vendor_lock"
            ),
            "renewal_supervisor_contract_version": str(
                check.get("renewal_supervisor_contract_version") or ""
            ),
            "renewal_supervisor_status": str(check.get("renewal_supervisor_status") or ""),
            "renewal_supervisor_missing_sections": (
                check.get("renewal_supervisor_missing_sections")
                if isinstance(check.get("renewal_supervisor_missing_sections"), list)
                else []
            ),
            "renewal_supervisor_enabled_by_default": check.get(
                "renewal_supervisor_enabled_by_default"
            ),
            "renewal_supervisor_renew_once_supported": check.get(
                "renewal_supervisor_renew_once_supported"
            ),
            "renewal_supervisor_owner_identity_required": check.get(
                "renewal_supervisor_owner_identity_required"
            ),
            "renewal_supervisor_ttl_interval_policy_ready": check.get(
                "renewal_supervisor_ttl_interval_policy_ready"
            ),
            "renewal_supervisor_controlled_lifecycle_supported": check.get(
                "renewal_supervisor_controlled_lifecycle_supported"
            ),
            "renewal_supervisor_starts_by_default": check.get(
                "renewal_supervisor_starts_by_default"
            ),
            "renewal_supervisor_active": check.get("renewal_supervisor_active"),
            "renewal_supervisor_last_renewal_status": str(
                check.get("renewal_supervisor_last_renewal_status") or ""
            ),
            "renewal_supervisor_stop_supported": check.get(
                "renewal_supervisor_stop_supported"
            ),
            "renewal_supervisor_failure_fail_closed": check.get(
                "renewal_supervisor_failure_fail_closed"
            ),
            "renewal_supervisor_lease_loss_fail_closed": check.get(
                "renewal_supervisor_lease_loss_fail_closed"
            ),
            "renewal_supervisor_renew_once_status": str(
                check.get("renewal_supervisor_renew_once_status") or ""
            ),
            "renewal_supervisor_renew_once_background_started": check.get(
                "renewal_supervisor_renew_once_background_started"
            ),
            "renewal_supervisor_stale_fencing_status": str(
                check.get("renewal_supervisor_stale_fencing_status") or ""
            ),
            "renewal_supervisor_stale_fencing_reason": str(
                check.get("renewal_supervisor_stale_fencing_reason") or ""
            ),
            "renewal_supervisor_lifecycle_initial_active": check.get(
                "renewal_supervisor_lifecycle_initial_active"
            ),
            "renewal_supervisor_lifecycle_started_active": check.get(
                "renewal_supervisor_lifecycle_started_active"
            ),
            "renewal_supervisor_lifecycle_started_status": str(
                check.get("renewal_supervisor_lifecycle_started_status") or ""
            ),
            "renewal_supervisor_lifecycle_started_count": check.get(
                "renewal_supervisor_lifecycle_started_count"
            ),
            "renewal_supervisor_lifecycle_stopped_active": check.get(
                "renewal_supervisor_lifecycle_stopped_active"
            ),
            "renewal_supervisor_lifecycle_stopped_count": check.get(
                "renewal_supervisor_lifecycle_stopped_count"
            ),
            "rollout_readiness_contract_version": str(
                check.get("rollout_readiness_contract_version") or ""
            ),
            "rollout_readiness_status": str(check.get("rollout_readiness_status") or ""),
            "rollout_missing_sections": (
                check.get("rollout_missing_sections")
                if isinstance(check.get("rollout_missing_sections"), list)
                else []
            ),
            "production_rollout_confirmed": check.get("production_rollout_confirmed"),
            "rollout_migration_ready": check.get("rollout_migration_ready"),
            "rollout_stale_fencing_verified": check.get("rollout_stale_fencing_verified"),
            "rollout_rollback_plan_ready": check.get("rollout_rollback_plan_ready"),
            "rollout_operationalization_status": str(
                check.get("rollout_operationalization_status") or ""
            ),
            "rollout_mode": str(check.get("rollout_mode") or ""),
            "rollout_missing_artifacts": (
                check.get("rollout_missing_artifacts")
                if isinstance(check.get("rollout_missing_artifacts"), list)
                else []
            ),
            "rollout_rollback_plan_status": str(
                check.get("rollout_rollback_plan_status") or ""
            ),
            "rollout_fallback_policy_status": str(
                check.get("rollout_fallback_policy_status") or ""
            ),
            "rollout_renewal_lifecycle_verification_status": str(
                check.get("rollout_renewal_lifecycle_verification_status") or ""
            ),
            "rollout_auto_claim_decision_status": str(
                check.get("rollout_auto_claim_decision_status") or ""
            ),
            "rollout_confirmation_decision_contract_version": str(
                check.get("rollout_confirmation_decision_contract_version") or ""
            ),
            "rollout_confirmation_decision_status": str(
                check.get("rollout_confirmation_decision_status") or ""
            ),
            "rollout_decision_recorded": check.get("rollout_decision_recorded"),
            "rollout_decision_id": str(check.get("rollout_decision_id") or ""),
            "rollout_approved_by": str(check.get("rollout_approved_by") or ""),
            "rollout_approved_at": str(check.get("rollout_approved_at") or ""),
            "rollout_target_store_mode": str(check.get("rollout_target_store_mode") or ""),
            "rollout_confirmation_missing_sections": (
                check.get("rollout_confirmation_missing_sections")
                if isinstance(check.get("rollout_confirmation_missing_sections"), list)
                else []
            ),
            "rollout_confirmation_production_rollout_confirmed": check.get(
                "rollout_confirmation_production_rollout_confirmed"
            ),
            "rollout_confirmation_input_contract_version": str(
                check.get("rollout_confirmation_input_contract_version") or ""
            ),
            "rollout_confirmation_input_source_status": str(
                check.get("rollout_confirmation_input_source_status") or ""
            ),
            "rollout_confirmation_input_source_kind": str(
                check.get("rollout_confirmation_input_source_kind") or ""
            ),
            "rollout_confirmation_input_decision_id": str(
                check.get("rollout_confirmation_input_decision_id") or ""
            ),
            "rollout_confirmation_input_approved_by": str(
                check.get("rollout_confirmation_input_approved_by") or ""
            ),
            "rollout_confirmation_input_approved_at": str(
                check.get("rollout_confirmation_input_approved_at") or ""
            ),
            "rollout_confirmation_input_target_store_mode": str(
                check.get("rollout_confirmation_input_target_store_mode") or ""
            ),
            "rollout_confirmation_input_rollback_plan_reference": str(
                check.get("rollout_confirmation_input_rollback_plan_reference") or ""
            ),
            "rollout_confirmation_input_fallback_policy_reference": str(
                check.get("rollout_confirmation_input_fallback_policy_reference") or ""
            ),
            "rollout_confirmation_input_renewal_lifecycle_reference": str(
                check.get("rollout_confirmation_input_renewal_lifecycle_reference") or ""
            ),
            "rollout_confirmation_input_auto_claim_decision_reference": str(
                check.get("rollout_confirmation_input_auto_claim_decision_reference") or ""
            ),
            "rollout_confirmation_input_missing_sections": (
                check.get("rollout_confirmation_input_missing_sections")
                if isinstance(check.get("rollout_confirmation_input_missing_sections"), list)
                else []
            ),
            "rollout_confirmation_input_sql_row_lease_is_authority": check.get(
                "rollout_confirmation_input_sql_row_lease_is_authority"
            ),
            "auto_claim_policy_contract_version": str(
                check.get("auto_claim_policy_contract_version") or ""
            ),
            "auto_claim_policy_status": str(check.get("auto_claim_policy_status") or ""),
            "auto_claim_missing_sections": (
                check.get("auto_claim_missing_sections")
                if isinstance(check.get("auto_claim_missing_sections"), list)
                else []
            ),
            "auto_claim_enabled_by_default": check.get("auto_claim_enabled_by_default"),
            "auto_claim_descriptor_evidence_fallback": check.get(
                "auto_claim_descriptor_evidence_fallback"
            ),
            "auto_claim_lease_validation_required": check.get(
                "auto_claim_lease_validation_required"
            ),
            "auto_claim_entrypoint_allowlist_ready": check.get(
                "auto_claim_entrypoint_allowlist_ready"
            ),
            "auto_claim_entrypoint_allowlist_contract_version": str(
                check.get("auto_claim_entrypoint_allowlist_contract_version") or ""
            ),
            "auto_claim_entrypoint_allowlist_status": str(
                check.get("auto_claim_entrypoint_allowlist_status") or ""
            ),
            "auto_claim_allowed_entrypoints": (
                check.get("auto_claim_allowed_entrypoints")
                if isinstance(check.get("auto_claim_allowed_entrypoints"), list)
                else []
            ),
            "auto_claim_missing_entrypoints": (
                check.get("auto_claim_missing_entrypoints")
                if isinstance(check.get("auto_claim_missing_entrypoints"), list)
                else []
            ),
            "auto_claim_default_auto_claim_enabled": check.get(
                "auto_claim_default_auto_claim_enabled"
            ),
            "auto_claim_requires_production_gate_ready": check.get(
                "auto_claim_requires_production_gate_ready"
            ),
            "auto_claim_enablement_gate_contract_version": str(
                check.get("auto_claim_enablement_gate_contract_version") or ""
            ),
            "auto_claim_enablement_gate_status": str(
                check.get("auto_claim_enablement_gate_status") or ""
            ),
            "auto_claim_will_auto_claim": check.get("auto_claim_will_auto_claim"),
            "auto_claim_requested_entrypoint": str(
                check.get("auto_claim_requested_entrypoint") or ""
            ),
            "auto_claim_enablement_missing_sections": (
                check.get("auto_claim_enablement_missing_sections")
                if isinstance(check.get("auto_claim_enablement_missing_sections"), list)
                else []
            ),
            "auto_claim_enablement_blocked_reason": str(
                check.get("auto_claim_enablement_blocked_reason") or ""
            ),
            "ownership_audit_contract_version": str(
                check.get("ownership_audit_contract_version") or ""
            ),
            "ownership_audit_status": str(check.get("ownership_audit_status") or ""),
            "ownership_audit_missing_sections": (
                check.get("ownership_audit_missing_sections")
                if isinstance(check.get("ownership_audit_missing_sections"), list)
                else []
            ),
            "ownership_audit_compact_evidence": check.get(
                "ownership_audit_compact_evidence"
            ),
            "ownership_audit_operation_history_ready": check.get(
                "ownership_audit_operation_history_ready"
            ),
            "ownership_audit_recovery_operation_link_ready": check.get(
                "ownership_audit_recovery_operation_link_ready"
            ),
            "ownership_audit_timeline_writer_ready": check.get(
                "ownership_audit_timeline_writer_ready"
            ),
            "ownership_audit_idempotent_dedupe_ready": check.get(
                "ownership_audit_idempotent_dedupe_ready"
            ),
            "ownership_audit_authorization_source": check.get(
                "ownership_audit_authorization_source"
            ),
            "enablement_strategy_contract_version": str(
                check.get("enablement_strategy_contract_version") or ""
            ),
            "enablement_strategy_status": str(check.get("enablement_strategy_status") or ""),
            "enablement_strategy_blocking_sections": (
                check.get("enablement_strategy_blocking_sections")
                if isinstance(check.get("enablement_strategy_blocking_sections"), list)
                else []
            ),
            "production_default_enabled_requested": check.get(
                "production_default_enabled_requested"
            ),
            "production_default_allowed": check.get("production_default_allowed"),
            "enablement_input_source_contract_version": str(
                check.get("enablement_input_source_contract_version") or ""
            ),
            "enablement_input_source_status": str(
                check.get("enablement_input_source_status") or ""
            ),
            "enablement_input_source_kind": str(check.get("enablement_input_source_kind") or ""),
            "enablement_request_id": str(check.get("enablement_request_id") or ""),
            "enablement_requested_by": str(check.get("enablement_requested_by") or ""),
            "enablement_requested_at": str(check.get("enablement_requested_at") or ""),
            "enablement_target_store_mode": str(
                check.get("enablement_target_store_mode") or ""
            ),
            "enablement_rollout_artifact": str(check.get("enablement_rollout_artifact") or ""),
            "enablement_vendor_lock_decision_id": str(
                check.get("enablement_vendor_lock_decision_id") or ""
            ),
            "enablement_renewal_lifecycle_reference": str(
                check.get("enablement_renewal_lifecycle_reference") or ""
            ),
            "enablement_auto_claim_decision_reference": str(
                check.get("enablement_auto_claim_decision_reference") or ""
            ),
            "enablement_audit_evidence_reference": str(
                check.get("enablement_audit_evidence_reference") or ""
            ),
            "enablement_rollback_plan_reference": str(
                check.get("enablement_rollback_plan_reference") or ""
            ),
            "enablement_fallback_policy_reference": str(
                check.get("enablement_fallback_policy_reference") or ""
            ),
            "enablement_input_source_ready": check.get("enablement_input_source_ready"),
            "enablement_input_source_missing_sections": (
                check.get("enablement_input_source_missing_sections")
                if isinstance(check.get("enablement_input_source_missing_sections"), list)
                else []
            ),
            "enablement_explicit_required": check.get("enablement_explicit_required"),
            "enablement_all_required_sections_ready": check.get(
                "enablement_all_required_sections_ready"
            ),
            "enablement_fail_closed_when_blocked": check.get(
                "enablement_fail_closed_when_blocked"
            ),
            "enablement_sql_row_lease_not_default_authority": check.get(
                "enablement_sql_row_lease_not_default_authority"
            ),
            "configurable_knob_present": check.get("configurable_knob_present"),
            "hot_reloadable_knob_present": check.get("hot_reloadable_knob_present"),
            "strict_mode_status": str(check.get("strict_mode_status") or ""),
            "fallback_mode_status": str(check.get("fallback_mode_status") or ""),
        })

    def _normalize_worker_ownership_store_mode_coverage(self, coverage: Mapping[str, Any]) -> Dict[str, Any]:
        default_mode = str(coverage.get("default_mode") or "")
        default_mode_source = str(coverage.get("default_mode_source") or "")
        default_adapter_kind = str(coverage.get("default_adapter_kind") or "")
        default_durable = self._coerce_truthy_flag(coverage.get("default_durable"))
        production_gate_contract_version = str(coverage.get("production_gate_contract_version") or "")
        production_gate_status = str(coverage.get("production_gate_status") or "")
        production_gate_missing_sections = (
            coverage.get("production_gate_missing_sections")
            if isinstance(coverage.get("production_gate_missing_sections"), list)
            else []
        )
        production_default_enabled = self._coerce_truthy_flag(coverage.get("production_default_enabled"))
        vendor_lock_contract_version = str(coverage.get("vendor_lock_contract_version") or "")
        vendor_lock_status = str(coverage.get("vendor_lock_status") or "")
        vendor_lock_missing_sections = (
            coverage.get("vendor_lock_missing_sections")
            if isinstance(coverage.get("vendor_lock_missing_sections"), list)
            else []
        )
        vendor_lock_current_posture = str(coverage.get("vendor_lock_current_posture") or "")
        vendor_lock_sql_row_lease_fencing = self._coerce_truthy_flag(
            coverage.get("vendor_lock_sql_row_lease_fencing")
        )
        vendor_lock_sql_row_lease_is_vendor_lock = self._coerce_truthy_flag(
            coverage.get("vendor_lock_sql_row_lease_is_vendor_lock")
        )
        vendor_lock_adapter_present = self._coerce_truthy_flag(
            coverage.get("vendor_lock_adapter_present")
        )
        vendor_lock_adapter_contract_version = str(
            coverage.get("vendor_lock_adapter_contract_version") or ""
        )
        vendor_lock_adapter_status = str(coverage.get("vendor_lock_adapter_status") or "")
        vendor_lock_adapter_kind = str(coverage.get("vendor_lock_adapter_kind") or "")
        vendor_lock_adapter_target_backend = str(
            coverage.get("vendor_lock_adapter_target_backend") or ""
        )
        vendor_lock_adapter_scope = str(coverage.get("vendor_lock_adapter_scope") or "")
        vendor_lock_adapter_fencing_strategy = str(
            coverage.get("vendor_lock_adapter_fencing_strategy") or ""
        )
        vendor_lock_adapter_ttl_renewal_strategy = str(
            coverage.get("vendor_lock_adapter_ttl_renewal_strategy") or ""
        )
        vendor_lock_adapter_failover_strategy = str(
            coverage.get("vendor_lock_adapter_failover_strategy") or ""
        )
        vendor_lock_adapter_stale_cleanup_strategy = str(
            coverage.get("vendor_lock_adapter_stale_cleanup_strategy") or ""
        )
        vendor_lock_adapter_acquire_supported = self._coerce_truthy_flag(
            coverage.get("vendor_lock_adapter_acquire_supported")
        )
        vendor_lock_adapter_renew_supported = self._coerce_truthy_flag(
            coverage.get("vendor_lock_adapter_renew_supported")
        )
        vendor_lock_adapter_release_supported = self._coerce_truthy_flag(
            coverage.get("vendor_lock_adapter_release_supported")
        )
        vendor_lock_adapter_probe_supported = self._coerce_truthy_flag(
            coverage.get("vendor_lock_adapter_probe_supported")
        )
        vendor_lock_adapter_production_allowed = self._coerce_truthy_flag(
            coverage.get("vendor_lock_adapter_production_allowed")
        )
        vendor_lock_adapter_sql_row_lease_is_vendor_lock = self._coerce_truthy_flag(
            coverage.get("vendor_lock_adapter_sql_row_lease_is_vendor_lock")
        )
        vendor_lock_adapter_missing_sections = (
            coverage.get("vendor_lock_adapter_missing_sections")
            if isinstance(coverage.get("vendor_lock_adapter_missing_sections"), list)
            else []
        )
        postgres_probe_contract_version = str(
            coverage.get("postgres_probe_contract_version") or ""
        )
        postgres_probe_status = str(coverage.get("postgres_probe_status") or "")
        postgres_probe_missing_sections = (
            coverage.get("postgres_probe_missing_sections")
            if isinstance(coverage.get("postgres_probe_missing_sections"), list)
            else []
        )
        postgres_probe_executes = self._coerce_truthy_flag(
            coverage.get("postgres_probe_executes")
        )
        postgres_probe_sql_row_lease_is_vendor_lock = self._coerce_truthy_flag(
            coverage.get("postgres_probe_sql_row_lease_is_vendor_lock")
        )
        postgres_probe_ready_status = str(coverage.get("postgres_probe_ready_status") or "")
        postgres_probe_ready_executes = self._coerce_truthy_flag(
            coverage.get("postgres_probe_ready_executes")
        )
        postgres_execution_seam_contract_version = str(
            coverage.get("postgres_execution_seam_contract_version") or ""
        )
        postgres_execution_default_status = str(
            coverage.get("postgres_execution_default_status") or ""
        )
        postgres_execution_default_executor_bound = self._coerce_truthy_flag(
            coverage.get("postgres_execution_default_executor_bound")
        )
        postgres_execution_default_enabled_by_default = self._coerce_truthy_flag(
            coverage.get("postgres_execution_default_enabled_by_default")
        )
        postgres_execution_default_production_allowed = self._coerce_truthy_flag(
            coverage.get("postgres_execution_default_production_allowed")
        )
        postgres_execution_default_missing_sections = (
            coverage.get("postgres_execution_default_missing_sections")
            if isinstance(coverage.get("postgres_execution_default_missing_sections"), list)
            else []
        )
        postgres_execution_default_probe_status = str(
            coverage.get("postgres_execution_default_probe_status") or ""
        )
        postgres_execution_default_probe_executed = self._coerce_truthy_flag(
            coverage.get("postgres_execution_default_probe_executed")
        )
        postgres_execution_opt_in_status = str(
            coverage.get("postgres_execution_opt_in_status") or ""
        )
        postgres_execution_opt_in_executor_bound = self._coerce_truthy_flag(
            coverage.get("postgres_execution_opt_in_executor_bound")
        )
        postgres_execution_opt_in_enabled_by_default = self._coerce_truthy_flag(
            coverage.get("postgres_execution_opt_in_enabled_by_default")
        )
        postgres_execution_opt_in_production_allowed = self._coerce_truthy_flag(
            coverage.get("postgres_execution_opt_in_production_allowed")
        )
        postgres_execution_opt_in_probe_status = str(
            coverage.get("postgres_execution_opt_in_probe_status") or ""
        )
        postgres_execution_opt_in_probe_executed = self._coerce_truthy_flag(
            coverage.get("postgres_execution_opt_in_probe_executed")
        )
        postgres_execution_opt_in_acquire_status = str(
            coverage.get("postgres_execution_opt_in_acquire_status") or ""
        )
        postgres_execution_opt_in_acquire_executed = self._coerce_truthy_flag(
            coverage.get("postgres_execution_opt_in_acquire_executed")
        )
        postgres_execution_opt_in_acquired = self._coerce_truthy_flag(
            coverage.get("postgres_execution_opt_in_acquired")
        )
        postgres_execution_opt_in_envelope_count = self._coerce_optional_non_negative_int(
            coverage.get("postgres_execution_opt_in_envelope_count")
        )
        postgres_rollout_consumer_contract_version = str(
            coverage.get("postgres_rollout_consumer_contract_version") or ""
        )
        postgres_rollout_consumer_default_status = str(
            coverage.get("postgres_rollout_consumer_default_status") or ""
        )
        postgres_rollout_consumer_default_missing_sections = (
            coverage.get("postgres_rollout_consumer_default_missing_sections")
            if isinstance(
                coverage.get("postgres_rollout_consumer_default_missing_sections"), list
            )
            else []
        )
        postgres_rollout_consumer_default_will_enable_default = self._coerce_truthy_flag(
            coverage.get("postgres_rollout_consumer_default_will_enable_default")
        )
        postgres_rollout_consumer_default_executes_lock = self._coerce_truthy_flag(
            coverage.get("postgres_rollout_consumer_default_executes_lock")
        )
        postgres_rollout_consumer_ready_status = str(
            coverage.get("postgres_rollout_consumer_ready_status") or ""
        )
        postgres_rollout_consumer_ready_target_backend = str(
            coverage.get("postgres_rollout_consumer_ready_target_backend") or ""
        )
        postgres_rollout_consumer_ready_lock_adapter_kind = str(
            coverage.get("postgres_rollout_consumer_ready_lock_adapter_kind") or ""
        )
        postgres_rollout_consumer_ready_will_enable_default = self._coerce_truthy_flag(
            coverage.get("postgres_rollout_consumer_ready_will_enable_default")
        )
        postgres_rollout_consumer_ready_executes_lock = self._coerce_truthy_flag(
            coverage.get("postgres_rollout_consumer_ready_executes_lock")
        )
        postgres_rollout_consumer_input_source_status = str(
            coverage.get("postgres_rollout_consumer_input_source_status") or ""
        )
        postgres_rollout_consumer_input_source_ready = self._coerce_truthy_flag(
            coverage.get("postgres_rollout_consumer_input_source_ready")
        )
        postgres_rollout_consumer_input_source_kind = str(
            coverage.get("postgres_rollout_consumer_input_source_kind") or ""
        )
        postgres_target_binding_contract_version = str(
            coverage.get("postgres_target_binding_contract_version") or ""
        )
        postgres_target_binding_default_status = str(
            coverage.get("postgres_target_binding_default_status") or ""
        )
        postgres_target_binding_default_missing_sections = (
            coverage.get("postgres_target_binding_default_missing_sections")
            if isinstance(
                coverage.get("postgres_target_binding_default_missing_sections"), list
            )
            else []
        )
        postgres_target_binding_default_will_enable_lock = self._coerce_truthy_flag(
            coverage.get("postgres_target_binding_default_will_enable_lock")
        )
        postgres_target_binding_default_executes_lock = self._coerce_truthy_flag(
            coverage.get("postgres_target_binding_default_executes_lock")
        )
        postgres_target_binding_ready_status = str(
            coverage.get("postgres_target_binding_ready_status") or ""
        )
        postgres_target_binding_ready_target_backend = str(
            coverage.get("postgres_target_binding_ready_target_backend") or ""
        )
        postgres_target_binding_ready_lock_adapter_kind = str(
            coverage.get("postgres_target_binding_ready_lock_adapter_kind") or ""
        )
        postgres_target_binding_ready_will_enable_lock = self._coerce_truthy_flag(
            coverage.get("postgres_target_binding_ready_will_enable_lock")
        )
        postgres_target_binding_ready_executes_lock = self._coerce_truthy_flag(
            coverage.get("postgres_target_binding_ready_executes_lock")
        )
        postgres_target_binding_target_input_status = str(
            coverage.get("postgres_target_binding_target_input_status") or ""
        )
        postgres_target_binding_target_decision_status = str(
            coverage.get("postgres_target_binding_target_decision_status") or ""
        )
        postgres_target_binding_target_decision_production_allowed = (
            self._coerce_truthy_flag(
                coverage.get("postgres_target_binding_target_decision_production_allowed")
            )
        )
        postgres_semantics_binding_contract_version = str(
            coverage.get("postgres_semantics_binding_contract_version") or ""
        )
        postgres_semantics_binding_default_status = str(
            coverage.get("postgres_semantics_binding_default_status") or ""
        )
        postgres_semantics_binding_default_missing_sections = (
            coverage.get("postgres_semantics_binding_default_missing_sections")
            if isinstance(
                coverage.get("postgres_semantics_binding_default_missing_sections"), list
            )
            else []
        )
        postgres_semantics_binding_default_will_enable_lock = self._coerce_truthy_flag(
            coverage.get("postgres_semantics_binding_default_will_enable_lock")
        )
        postgres_semantics_binding_default_will_update_gate = self._coerce_truthy_flag(
            coverage.get("postgres_semantics_binding_default_will_update_gate")
        )
        postgres_semantics_binding_default_executes_lock = self._coerce_truthy_flag(
            coverage.get("postgres_semantics_binding_default_executes_lock")
        )
        postgres_semantics_binding_ready_status = str(
            coverage.get("postgres_semantics_binding_ready_status") or ""
        )
        postgres_semantics_binding_ready_target_backend = str(
            coverage.get("postgres_semantics_binding_ready_target_backend") or ""
        )
        postgres_semantics_binding_ready_lock_adapter_kind = str(
            coverage.get("postgres_semantics_binding_ready_lock_adapter_kind") or ""
        )
        postgres_semantics_binding_ready_probe_status = str(
            coverage.get("postgres_semantics_binding_ready_probe_status") or ""
        )
        postgres_semantics_binding_ready_adapter_status = str(
            coverage.get("postgres_semantics_binding_ready_adapter_status") or ""
        )
        postgres_semantics_binding_ready_semantics_status = str(
            coverage.get("postgres_semantics_binding_ready_semantics_status") or ""
        )
        postgres_semantics_binding_ready_will_enable_lock = self._coerce_truthy_flag(
            coverage.get("postgres_semantics_binding_ready_will_enable_lock")
        )
        postgres_semantics_binding_ready_will_update_gate = self._coerce_truthy_flag(
            coverage.get("postgres_semantics_binding_ready_will_update_gate")
        )
        postgres_semantics_binding_ready_executes_lock = self._coerce_truthy_flag(
            coverage.get("postgres_semantics_binding_ready_executes_lock")
        )
        postgres_wiring_decision_contract_version = str(
            coverage.get("postgres_wiring_decision_contract_version") or ""
        )
        postgres_wiring_decision_default_status = str(
            coverage.get("postgres_wiring_decision_default_status") or ""
        )
        postgres_wiring_decision_default_missing_sections = (
            coverage.get("postgres_wiring_decision_default_missing_sections")
            if isinstance(
                coverage.get("postgres_wiring_decision_default_missing_sections"), list
            )
            else []
        )
        postgres_wiring_decision_default_wiring_allowed = self._coerce_truthy_flag(
            coverage.get("postgres_wiring_decision_default_wiring_allowed")
        )
        postgres_wiring_decision_default_will_update_gate = self._coerce_truthy_flag(
            coverage.get("postgres_wiring_decision_default_will_update_gate")
        )
        postgres_wiring_decision_default_will_enable_lock = self._coerce_truthy_flag(
            coverage.get("postgres_wiring_decision_default_will_enable_lock")
        )
        postgres_wiring_decision_default_executes_lock = self._coerce_truthy_flag(
            coverage.get("postgres_wiring_decision_default_executes_lock")
        )
        postgres_wiring_decision_ready_status = str(
            coverage.get("postgres_wiring_decision_ready_status") or ""
        )
        postgres_wiring_decision_ready_semantics_binding_status = str(
            coverage.get("postgres_wiring_decision_ready_semantics_binding_status") or ""
        )
        postgres_wiring_decision_ready_candidate_status = str(
            coverage.get("postgres_wiring_decision_ready_candidate_status") or ""
        )
        postgres_wiring_decision_ready_wiring_allowed = self._coerce_truthy_flag(
            coverage.get("postgres_wiring_decision_ready_wiring_allowed")
        )
        postgres_wiring_decision_ready_target_backend = str(
            coverage.get("postgres_wiring_decision_ready_target_backend") or ""
        )
        postgres_wiring_decision_ready_lock_adapter_kind = str(
            coverage.get("postgres_wiring_decision_ready_lock_adapter_kind") or ""
        )
        postgres_wiring_decision_ready_will_update_gate = self._coerce_truthy_flag(
            coverage.get("postgres_wiring_decision_ready_will_update_gate")
        )
        postgres_wiring_decision_ready_will_enable_lock = self._coerce_truthy_flag(
            coverage.get("postgres_wiring_decision_ready_will_enable_lock")
        )
        postgres_wiring_decision_ready_executes_lock = self._coerce_truthy_flag(
            coverage.get("postgres_wiring_decision_ready_executes_lock")
        )
        production_dry_run_contract_version = str(
            coverage.get("production_dry_run_contract_version") or ""
        )
        production_dry_run_default_status = str(
            coverage.get("production_dry_run_default_status") or ""
        )
        production_dry_run_default_missing_sections = (
            coverage.get("production_dry_run_default_missing_sections")
            if isinstance(coverage.get("production_dry_run_default_missing_sections"), list)
            else []
        )
        production_dry_run_default_all_required_ready = self._coerce_truthy_flag(
            coverage.get("production_dry_run_default_all_required_ready")
        )
        production_dry_run_default_would_allow = self._coerce_truthy_flag(
            coverage.get("production_dry_run_default_would_allow")
        )
        production_dry_run_default_will_enable = self._coerce_truthy_flag(
            coverage.get("production_dry_run_default_will_enable")
        )
        production_dry_run_default_executes_lock = self._coerce_truthy_flag(
            coverage.get("production_dry_run_default_executes_lock")
        )
        production_dry_run_default_starts_worker = self._coerce_truthy_flag(
            coverage.get("production_dry_run_default_starts_worker")
        )
        production_dry_run_default_runs_auto_claim = self._coerce_truthy_flag(
            coverage.get("production_dry_run_default_runs_auto_claim")
        )
        production_dry_run_ready_status = str(
            coverage.get("production_dry_run_ready_status") or ""
        )
        production_dry_run_ready_missing_sections = (
            coverage.get("production_dry_run_ready_missing_sections")
            if isinstance(coverage.get("production_dry_run_ready_missing_sections"), list)
            else []
        )
        production_dry_run_ready_all_required_ready = self._coerce_truthy_flag(
            coverage.get("production_dry_run_ready_all_required_ready")
        )
        production_dry_run_ready_would_allow = self._coerce_truthy_flag(
            coverage.get("production_dry_run_ready_would_allow")
        )
        production_dry_run_ready_will_enable = self._coerce_truthy_flag(
            coverage.get("production_dry_run_ready_will_enable")
        )
        production_dry_run_ready_executes_lock = self._coerce_truthy_flag(
            coverage.get("production_dry_run_ready_executes_lock")
        )
        production_dry_run_ready_starts_worker = self._coerce_truthy_flag(
            coverage.get("production_dry_run_ready_starts_worker")
        )
        production_dry_run_ready_runs_auto_claim = self._coerce_truthy_flag(
            coverage.get("production_dry_run_ready_runs_auto_claim")
        )
        enablement_config_consumer_contract_version = str(
            coverage.get("enablement_config_consumer_contract_version") or ""
        )
        enablement_config_consumer_default_status = str(
            coverage.get("enablement_config_consumer_default_status") or ""
        )
        enablement_config_consumer_default_missing_sections = (
            coverage.get("enablement_config_consumer_default_missing_sections")
            if isinstance(
                coverage.get("enablement_config_consumer_default_missing_sections"),
                list,
            )
            else []
        )
        enablement_config_consumer_default_will_enable = self._coerce_truthy_flag(
            coverage.get("enablement_config_consumer_default_will_enable")
        )
        enablement_config_consumer_default_executes_lock = self._coerce_truthy_flag(
            coverage.get("enablement_config_consumer_default_executes_lock")
        )
        enablement_config_consumer_default_starts_worker = self._coerce_truthy_flag(
            coverage.get("enablement_config_consumer_default_starts_worker")
        )
        enablement_config_consumer_default_runs_auto_claim = self._coerce_truthy_flag(
            coverage.get("enablement_config_consumer_default_runs_auto_claim")
        )
        enablement_config_consumer_ready_status = str(
            coverage.get("enablement_config_consumer_ready_status") or ""
        )
        enablement_config_consumer_ready_missing_sections = (
            coverage.get("enablement_config_consumer_ready_missing_sections")
            if isinstance(
                coverage.get("enablement_config_consumer_ready_missing_sections"), list
            )
            else []
        )
        enablement_config_consumer_ready_target_backend = str(
            coverage.get("enablement_config_consumer_ready_target_backend") or ""
        )
        enablement_config_consumer_ready_lock_adapter_kind = str(
            coverage.get("enablement_config_consumer_ready_lock_adapter_kind") or ""
        )
        enablement_config_consumer_ready_input_source_status = str(
            coverage.get("enablement_config_consumer_ready_input_source_status") or ""
        )
        enablement_config_consumer_ready_dry_run_status = str(
            coverage.get("enablement_config_consumer_ready_dry_run_status") or ""
        )
        enablement_config_consumer_ready_dry_run_would_allow = (
            self._coerce_truthy_flag(
                coverage.get("enablement_config_consumer_ready_dry_run_would_allow")
            )
        )
        enablement_config_consumer_ready_will_enable = self._coerce_truthy_flag(
            coverage.get("enablement_config_consumer_ready_will_enable")
        )
        enablement_config_consumer_ready_executes_lock = self._coerce_truthy_flag(
            coverage.get("enablement_config_consumer_ready_executes_lock")
        )
        enablement_config_consumer_ready_starts_worker = self._coerce_truthy_flag(
            coverage.get("enablement_config_consumer_ready_starts_worker")
        )
        enablement_config_consumer_ready_runs_auto_claim = self._coerce_truthy_flag(
            coverage.get("enablement_config_consumer_ready_runs_auto_claim")
        )
        enablement_config_factory_binding_default_status = str(
            coverage.get("enablement_config_factory_binding_default_status") or ""
        )
        enablement_config_factory_binding_ready_status = str(
            coverage.get("enablement_config_factory_binding_ready_status") or ""
        )
        enablement_config_factory_binding_ready_config_id = str(
            coverage.get("enablement_config_factory_binding_ready_config_id") or ""
        )
        enablement_config_factory_binding_will_enable = self._coerce_truthy_flag(
            coverage.get("enablement_config_factory_binding_will_enable")
        )
        enablement_config_factory_binding_executes_lock = self._coerce_truthy_flag(
            coverage.get("enablement_config_factory_binding_executes_lock")
        )
        enablement_config_factory_binding_starts_worker = self._coerce_truthy_flag(
            coverage.get("enablement_config_factory_binding_starts_worker")
        )
        enablement_config_factory_binding_runs_auto_claim = self._coerce_truthy_flag(
            coverage.get("enablement_config_factory_binding_runs_auto_claim")
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
        vendor_lock_scope_defined = self._coerce_truthy_flag(
            coverage.get("vendor_lock_scope_defined")
        )
        vendor_lock_fencing_guarantee_defined = self._coerce_truthy_flag(
            coverage.get("vendor_lock_fencing_guarantee_defined")
        )
        vendor_lock_failover_semantics_defined = self._coerce_truthy_flag(
            coverage.get("vendor_lock_failover_semantics_defined")
        )
        vendor_lock_ttl_renewal_semantics_defined = self._coerce_truthy_flag(
            coverage.get("vendor_lock_ttl_renewal_semantics_defined")
        )
        vendor_lock_stale_owner_cleanup_defined = self._coerce_truthy_flag(
            coverage.get("vendor_lock_stale_owner_cleanup_defined")
        )
        vendor_lock_production_allowed = self._coerce_truthy_flag(
            coverage.get("vendor_lock_production_allowed")
        )
        vendor_lock_target_decision_contract_version = str(
            coverage.get("vendor_lock_target_decision_contract_version") or ""
        )
        vendor_lock_target_decision_status = str(
            coverage.get("vendor_lock_target_decision_status") or ""
        )
        vendor_lock_target_decision_recorded = self._coerce_truthy_flag(
            coverage.get("vendor_lock_target_decision_recorded")
        )
        vendor_lock_target_backend = str(coverage.get("vendor_lock_target_backend") or "")
        vendor_lock_target_adapter_kind = str(
            coverage.get("vendor_lock_target_adapter_kind") or ""
        )
        vendor_lock_target_scope = str(coverage.get("vendor_lock_target_scope") or "")
        vendor_lock_target_fencing_strategy = str(
            coverage.get("vendor_lock_target_fencing_strategy") or ""
        )
        vendor_lock_target_ttl_renewal_strategy = str(
            coverage.get("vendor_lock_target_ttl_renewal_strategy") or ""
        )
        vendor_lock_target_failover_strategy = str(
            coverage.get("vendor_lock_target_failover_strategy") or ""
        )
        vendor_lock_target_stale_cleanup_strategy = str(
            coverage.get("vendor_lock_target_stale_cleanup_strategy") or ""
        )
        vendor_lock_target_missing_sections = (
            coverage.get("vendor_lock_target_missing_sections")
            if isinstance(coverage.get("vendor_lock_target_missing_sections"), list)
            else []
        )
        vendor_lock_target_sql_row_lease_is_vendor_lock = self._coerce_truthy_flag(
            coverage.get("vendor_lock_target_sql_row_lease_is_vendor_lock")
        )
        vendor_lock_target_production_allowed = self._coerce_truthy_flag(
            coverage.get("vendor_lock_target_production_allowed")
        )
        vendor_lock_target_input_contract_version = str(
            coverage.get("vendor_lock_target_input_contract_version") or ""
        )
        vendor_lock_target_input_source_status = str(
            coverage.get("vendor_lock_target_input_source_status") or ""
        )
        vendor_lock_target_input_source_kind = str(
            coverage.get("vendor_lock_target_input_source_kind") or ""
        )
        vendor_lock_target_input_decision_id = str(
            coverage.get("vendor_lock_target_input_decision_id") or ""
        )
        vendor_lock_target_input_approved_by = str(
            coverage.get("vendor_lock_target_input_approved_by") or ""
        )
        vendor_lock_target_input_approved_at = str(
            coverage.get("vendor_lock_target_input_approved_at") or ""
        )
        vendor_lock_target_input_backend = str(
            coverage.get("vendor_lock_target_input_backend") or ""
        )
        vendor_lock_target_input_adapter_kind = str(
            coverage.get("vendor_lock_target_input_adapter_kind") or ""
        )
        vendor_lock_target_input_rollout_artifact = str(
            coverage.get("vendor_lock_target_input_rollout_artifact") or ""
        )
        vendor_lock_target_input_config_key = str(
            coverage.get("vendor_lock_target_input_config_key") or ""
        )
        vendor_lock_target_input_manual_approval_reference = str(
            coverage.get("vendor_lock_target_input_manual_approval_reference") or ""
        )
        vendor_lock_target_input_missing_sections = (
            coverage.get("vendor_lock_target_input_missing_sections")
            if isinstance(coverage.get("vendor_lock_target_input_missing_sections"), list)
            else []
        )
        vendor_lock_target_input_sql_row_lease_is_vendor_lock = self._coerce_truthy_flag(
            coverage.get("vendor_lock_target_input_sql_row_lease_is_vendor_lock")
        )
        renewal_supervisor_contract_version = str(
            coverage.get("renewal_supervisor_contract_version") or ""
        )
        renewal_supervisor_status = str(coverage.get("renewal_supervisor_status") or "")
        renewal_supervisor_missing_sections = (
            coverage.get("renewal_supervisor_missing_sections")
            if isinstance(coverage.get("renewal_supervisor_missing_sections"), list)
            else []
        )
        renewal_supervisor_enabled_by_default = self._coerce_truthy_flag(
            coverage.get("renewal_supervisor_enabled_by_default")
        )
        renewal_supervisor_renew_once_supported = self._coerce_truthy_flag(
            coverage.get("renewal_supervisor_renew_once_supported")
        )
        renewal_supervisor_owner_identity_required = self._coerce_truthy_flag(
            coverage.get("renewal_supervisor_owner_identity_required")
        )
        renewal_supervisor_ttl_interval_policy_ready = self._coerce_truthy_flag(
            coverage.get("renewal_supervisor_ttl_interval_policy_ready")
        )
        renewal_supervisor_controlled_lifecycle_supported = self._coerce_truthy_flag(
            coverage.get("renewal_supervisor_controlled_lifecycle_supported")
        )
        renewal_supervisor_starts_by_default = self._coerce_truthy_flag(
            coverage.get("renewal_supervisor_starts_by_default")
        )
        renewal_supervisor_active = self._coerce_truthy_flag(
            coverage.get("renewal_supervisor_active")
        )
        renewal_supervisor_last_renewal_status = str(
            coverage.get("renewal_supervisor_last_renewal_status") or ""
        )
        renewal_supervisor_stop_supported = self._coerce_truthy_flag(
            coverage.get("renewal_supervisor_stop_supported")
        )
        renewal_supervisor_failure_fail_closed = self._coerce_truthy_flag(
            coverage.get("renewal_supervisor_failure_fail_closed")
        )
        renewal_supervisor_lease_loss_fail_closed = self._coerce_truthy_flag(
            coverage.get("renewal_supervisor_lease_loss_fail_closed")
        )
        renewal_supervisor_renew_once_status = str(
            coverage.get("renewal_supervisor_renew_once_status") or ""
        )
        renewal_supervisor_renew_once_background_started = self._coerce_truthy_flag(
            coverage.get("renewal_supervisor_renew_once_background_started")
        )
        renewal_supervisor_stale_fencing_status = str(
            coverage.get("renewal_supervisor_stale_fencing_status") or ""
        )
        renewal_supervisor_stale_fencing_reason = str(
            coverage.get("renewal_supervisor_stale_fencing_reason") or ""
        )
        renewal_supervisor_lifecycle_initial_active = self._coerce_truthy_flag(
            coverage.get("renewal_supervisor_lifecycle_initial_active")
        )
        renewal_supervisor_lifecycle_started_active = self._coerce_truthy_flag(
            coverage.get("renewal_supervisor_lifecycle_started_active")
        )
        renewal_supervisor_lifecycle_started_status = str(
            coverage.get("renewal_supervisor_lifecycle_started_status") or ""
        )
        renewal_supervisor_lifecycle_started_count, _ = self._coerce_non_negative_int(
            coverage.get("renewal_supervisor_lifecycle_started_count"),
            0,
        )
        renewal_supervisor_lifecycle_stopped_active = self._coerce_truthy_flag(
            coverage.get("renewal_supervisor_lifecycle_stopped_active")
        )
        renewal_supervisor_lifecycle_stopped_count, _ = self._coerce_non_negative_int(
            coverage.get("renewal_supervisor_lifecycle_stopped_count"),
            0,
        )
        rollout_readiness_contract_version = str(
            coverage.get("rollout_readiness_contract_version") or ""
        )
        rollout_readiness_status = str(coverage.get("rollout_readiness_status") or "")
        rollout_missing_sections = (
            coverage.get("rollout_missing_sections")
            if isinstance(coverage.get("rollout_missing_sections"), list)
            else []
        )
        production_rollout_confirmed = self._coerce_truthy_flag(
            coverage.get("production_rollout_confirmed")
        )
        rollout_migration_ready = self._coerce_truthy_flag(coverage.get("rollout_migration_ready"))
        rollout_stale_fencing_verified = self._coerce_truthy_flag(
            coverage.get("rollout_stale_fencing_verified")
        )
        rollout_rollback_plan_ready = self._coerce_truthy_flag(
            coverage.get("rollout_rollback_plan_ready")
        )
        rollout_operationalization_status = str(
            coverage.get("rollout_operationalization_status") or ""
        )
        rollout_mode = str(coverage.get("rollout_mode") or "")
        rollout_missing_artifacts = (
            coverage.get("rollout_missing_artifacts")
            if isinstance(coverage.get("rollout_missing_artifacts"), list)
            else []
        )
        rollout_rollback_plan_status = str(
            coverage.get("rollout_rollback_plan_status") or ""
        )
        rollout_fallback_policy_status = str(
            coverage.get("rollout_fallback_policy_status") or ""
        )
        rollout_renewal_lifecycle_verification_status = str(
            coverage.get("rollout_renewal_lifecycle_verification_status") or ""
        )
        rollout_auto_claim_decision_status = str(
            coverage.get("rollout_auto_claim_decision_status") or ""
        )
        rollout_confirmation_decision_contract_version = str(
            coverage.get("rollout_confirmation_decision_contract_version") or ""
        )
        rollout_confirmation_decision_status = str(
            coverage.get("rollout_confirmation_decision_status") or ""
        )
        rollout_decision_recorded = self._coerce_truthy_flag(
            coverage.get("rollout_decision_recorded")
        )
        rollout_decision_id = str(coverage.get("rollout_decision_id") or "")
        rollout_approved_by = str(coverage.get("rollout_approved_by") or "")
        rollout_approved_at = str(coverage.get("rollout_approved_at") or "")
        rollout_target_store_mode = str(coverage.get("rollout_target_store_mode") or "")
        rollout_confirmation_missing_sections = (
            coverage.get("rollout_confirmation_missing_sections")
            if isinstance(coverage.get("rollout_confirmation_missing_sections"), list)
            else []
        )
        rollout_confirmation_production_rollout_confirmed = self._coerce_truthy_flag(
            coverage.get("rollout_confirmation_production_rollout_confirmed")
        )
        rollout_confirmation_input_contract_version = str(
            coverage.get("rollout_confirmation_input_contract_version") or ""
        )
        rollout_confirmation_input_source_status = str(
            coverage.get("rollout_confirmation_input_source_status") or ""
        )
        rollout_confirmation_input_source_kind = str(
            coverage.get("rollout_confirmation_input_source_kind") or ""
        )
        rollout_confirmation_input_decision_id = str(
            coverage.get("rollout_confirmation_input_decision_id") or ""
        )
        rollout_confirmation_input_approved_by = str(
            coverage.get("rollout_confirmation_input_approved_by") or ""
        )
        rollout_confirmation_input_approved_at = str(
            coverage.get("rollout_confirmation_input_approved_at") or ""
        )
        rollout_confirmation_input_target_store_mode = str(
            coverage.get("rollout_confirmation_input_target_store_mode") or ""
        )
        rollout_confirmation_input_rollback_plan_reference = str(
            coverage.get("rollout_confirmation_input_rollback_plan_reference") or ""
        )
        rollout_confirmation_input_fallback_policy_reference = str(
            coverage.get("rollout_confirmation_input_fallback_policy_reference") or ""
        )
        rollout_confirmation_input_renewal_lifecycle_reference = str(
            coverage.get("rollout_confirmation_input_renewal_lifecycle_reference") or ""
        )
        rollout_confirmation_input_auto_claim_decision_reference = str(
            coverage.get("rollout_confirmation_input_auto_claim_decision_reference") or ""
        )
        rollout_confirmation_input_missing_sections = (
            coverage.get("rollout_confirmation_input_missing_sections")
            if isinstance(coverage.get("rollout_confirmation_input_missing_sections"), list)
            else []
        )
        rollout_confirmation_input_sql_row_lease_is_authority = self._coerce_truthy_flag(
            coverage.get("rollout_confirmation_input_sql_row_lease_is_authority")
        )
        auto_claim_policy_contract_version = str(
            coverage.get("auto_claim_policy_contract_version") or ""
        )
        auto_claim_policy_status = str(coverage.get("auto_claim_policy_status") or "")
        auto_claim_missing_sections = (
            coverage.get("auto_claim_missing_sections")
            if isinstance(coverage.get("auto_claim_missing_sections"), list)
            else []
        )
        auto_claim_enabled_by_default = self._coerce_truthy_flag(
            coverage.get("auto_claim_enabled_by_default")
        )
        auto_claim_descriptor_evidence_fallback = self._coerce_truthy_flag(
            coverage.get("auto_claim_descriptor_evidence_fallback")
        )
        auto_claim_lease_validation_required = self._coerce_truthy_flag(
            coverage.get("auto_claim_lease_validation_required")
        )
        auto_claim_entrypoint_allowlist_ready = self._coerce_truthy_flag(
            coverage.get("auto_claim_entrypoint_allowlist_ready")
        )
        auto_claim_entrypoint_allowlist_contract_version = str(
            coverage.get("auto_claim_entrypoint_allowlist_contract_version") or ""
        )
        auto_claim_entrypoint_allowlist_status = str(
            coverage.get("auto_claim_entrypoint_allowlist_status") or ""
        )
        auto_claim_allowed_entrypoints = (
            coverage.get("auto_claim_allowed_entrypoints")
            if isinstance(coverage.get("auto_claim_allowed_entrypoints"), list)
            else []
        )
        auto_claim_missing_entrypoints = (
            coverage.get("auto_claim_missing_entrypoints")
            if isinstance(coverage.get("auto_claim_missing_entrypoints"), list)
            else []
        )
        auto_claim_default_auto_claim_enabled = self._coerce_truthy_flag(
            coverage.get("auto_claim_default_auto_claim_enabled")
        )
        auto_claim_requires_production_gate_ready = self._coerce_truthy_flag(
            coverage.get("auto_claim_requires_production_gate_ready")
        )
        auto_claim_enablement_gate_contract_version = str(
            coverage.get("auto_claim_enablement_gate_contract_version") or ""
        )
        auto_claim_enablement_gate_status = str(
            coverage.get("auto_claim_enablement_gate_status") or ""
        )
        auto_claim_will_auto_claim = self._coerce_truthy_flag(
            coverage.get("auto_claim_will_auto_claim")
        )
        auto_claim_requested_entrypoint = str(
            coverage.get("auto_claim_requested_entrypoint") or ""
        )
        auto_claim_enablement_missing_sections = (
            coverage.get("auto_claim_enablement_missing_sections")
            if isinstance(coverage.get("auto_claim_enablement_missing_sections"), list)
            else []
        )
        auto_claim_enablement_blocked_reason = str(
            coverage.get("auto_claim_enablement_blocked_reason") or ""
        )
        ownership_audit_contract_version = str(
            coverage.get("ownership_audit_contract_version") or ""
        )
        ownership_audit_status = str(coverage.get("ownership_audit_status") or "")
        ownership_audit_missing_sections = (
            coverage.get("ownership_audit_missing_sections")
            if isinstance(coverage.get("ownership_audit_missing_sections"), list)
            else []
        )
        ownership_audit_compact_evidence = self._coerce_truthy_flag(
            coverage.get("ownership_audit_compact_evidence")
        )
        ownership_audit_operation_history_ready = self._coerce_truthy_flag(
            coverage.get("ownership_audit_operation_history_ready")
        )
        ownership_audit_recovery_operation_link_ready = self._coerce_truthy_flag(
            coverage.get("ownership_audit_recovery_operation_link_ready")
        )
        ownership_audit_timeline_writer_ready = self._coerce_truthy_flag(
            coverage.get("ownership_audit_timeline_writer_ready")
        )
        ownership_audit_idempotent_dedupe_ready = self._coerce_truthy_flag(
            coverage.get("ownership_audit_idempotent_dedupe_ready")
        )
        ownership_audit_authorization_source = self._coerce_truthy_flag(
            coverage.get("ownership_audit_authorization_source")
        )
        enablement_strategy_contract_version = str(
            coverage.get("enablement_strategy_contract_version") or ""
        )
        enablement_strategy_status = str(coverage.get("enablement_strategy_status") or "")
        enablement_strategy_blocking_sections = (
            coverage.get("enablement_strategy_blocking_sections")
            if isinstance(coverage.get("enablement_strategy_blocking_sections"), list)
            else []
        )
        production_default_enabled_requested = self._coerce_truthy_flag(
            coverage.get("production_default_enabled_requested")
        )
        production_default_allowed = self._coerce_truthy_flag(
            coverage.get("production_default_allowed")
        )
        enablement_input_source_contract_version = str(
            coverage.get("enablement_input_source_contract_version") or ""
        )
        enablement_input_source_status = str(
            coverage.get("enablement_input_source_status") or ""
        )
        enablement_input_source_kind = str(coverage.get("enablement_input_source_kind") or "")
        enablement_request_id = str(coverage.get("enablement_request_id") or "")
        enablement_requested_by = str(coverage.get("enablement_requested_by") or "")
        enablement_requested_at = str(coverage.get("enablement_requested_at") or "")
        enablement_target_store_mode = str(coverage.get("enablement_target_store_mode") or "")
        enablement_rollout_artifact = str(coverage.get("enablement_rollout_artifact") or "")
        enablement_vendor_lock_decision_id = str(
            coverage.get("enablement_vendor_lock_decision_id") or ""
        )
        enablement_renewal_lifecycle_reference = str(
            coverage.get("enablement_renewal_lifecycle_reference") or ""
        )
        enablement_auto_claim_decision_reference = str(
            coverage.get("enablement_auto_claim_decision_reference") or ""
        )
        enablement_audit_evidence_reference = str(
            coverage.get("enablement_audit_evidence_reference") or ""
        )
        enablement_rollback_plan_reference = str(
            coverage.get("enablement_rollback_plan_reference") or ""
        )
        enablement_fallback_policy_reference = str(
            coverage.get("enablement_fallback_policy_reference") or ""
        )
        enablement_input_source_ready = self._coerce_truthy_flag(
            coverage.get("enablement_input_source_ready")
        )
        enablement_input_source_missing_sections = (
            coverage.get("enablement_input_source_missing_sections")
            if isinstance(coverage.get("enablement_input_source_missing_sections"), list)
            else []
        )
        enablement_explicit_required = self._coerce_truthy_flag(
            coverage.get("enablement_explicit_required")
        )
        enablement_all_required_sections_ready = self._coerce_truthy_flag(
            coverage.get("enablement_all_required_sections_ready")
        )
        enablement_fail_closed_when_blocked = self._coerce_truthy_flag(
            coverage.get("enablement_fail_closed_when_blocked")
        )
        enablement_sql_row_lease_not_default_authority = self._coerce_truthy_flag(
            coverage.get("enablement_sql_row_lease_not_default_authority")
        )
        configurable_knob_present = self._coerce_truthy_flag(coverage.get("configurable_knob_present"))
        hot_reloadable_knob_present = self._coerce_truthy_flag(coverage.get("hot_reloadable_knob_present"))
        strict_mode_status = str(coverage.get("strict_mode_status") or "")
        fallback_mode_status = str(coverage.get("fallback_mode_status") or "")
        mode_smoke = (
            self._coerce_truthy_flag(coverage.get("mode_smoke"))
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
            and "target_decision" in vendor_lock_missing_sections
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
            and "postgres_execution_seam"
            in postgres_rollout_consumer_default_missing_sections
            and not postgres_rollout_consumer_default_will_enable_default
            and not postgres_rollout_consumer_default_executes_lock
            and postgres_rollout_consumer_ready_status == "ready"
            and postgres_rollout_consumer_ready_target_backend == "postgres"
            and postgres_rollout_consumer_ready_lock_adapter_kind
            == "postgres_advisory_lock"
            and not postgres_rollout_consumer_ready_will_enable_default
            and not postgres_rollout_consumer_ready_executes_lock
            and postgres_rollout_consumer_input_source_status == "ready"
            and postgres_rollout_consumer_input_source_ready
            and postgres_rollout_consumer_input_source_kind == "rollout_artifact"
            and postgres_target_binding_contract_version
            == "phase-ii-worker-ownership-postgres-vendor-lock-target-artifact-binding-v1"
            and postgres_target_binding_default_status == "blocked"
            and "source_kind" in postgres_target_binding_default_missing_sections
            and "postgres_rollout_consumer"
            in postgres_target_binding_default_missing_sections
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
            and "target_artifact_binding"
            in postgres_semantics_binding_default_missing_sections
            and "postgres_execution_seam"
            in postgres_semantics_binding_default_missing_sections
            and not postgres_semantics_binding_default_will_enable_lock
            and not postgres_semantics_binding_default_will_update_gate
            and not postgres_semantics_binding_default_executes_lock
            and postgres_semantics_binding_ready_status == "ready"
            and postgres_semantics_binding_ready_target_backend == "postgres"
            and postgres_semantics_binding_ready_lock_adapter_kind
            == "postgres_advisory_lock"
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
            and "semantics_binding"
            in postgres_wiring_decision_default_missing_sections
            and "decision_recorded"
            in postgres_wiring_decision_default_missing_sections
            and not postgres_wiring_decision_default_wiring_allowed
            and not postgres_wiring_decision_default_will_update_gate
            and not postgres_wiring_decision_default_will_enable_lock
            and not postgres_wiring_decision_default_executes_lock
            and postgres_wiring_decision_ready_status == "ready"
            and postgres_wiring_decision_ready_semantics_binding_status == "ready"
            and postgres_wiring_decision_ready_candidate_status == "ready"
            and postgres_wiring_decision_ready_wiring_allowed
            and postgres_wiring_decision_ready_target_backend == "postgres"
            and postgres_wiring_decision_ready_lock_adapter_kind
            == "postgres_advisory_lock"
            and not postgres_wiring_decision_ready_will_update_gate
            and not postgres_wiring_decision_ready_will_enable_lock
            and not postgres_wiring_decision_ready_executes_lock
            and production_dry_run_contract_version
            == "phase-ii-worker-ownership-production-gate-composition-dry-run-v1"
            and production_dry_run_default_status == "blocked"
            and "vendor_lock_wiring_decision"
            in production_dry_run_default_missing_sections
            and "heartbeat_renewal_supervisor"
            in production_dry_run_default_missing_sections
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
            and renewal_supervisor_last_renewal_status.strip() == ""
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
            and "production_default_enablement_input_source"
            in enablement_strategy_blocking_sections
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
            "vendor_lock_adapter_stale_cleanup_strategy": (
                vendor_lock_adapter_stale_cleanup_strategy
            ),
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
            "postgres_probe_sql_row_lease_is_vendor_lock": (
                postgres_probe_sql_row_lease_is_vendor_lock
            ),
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
            "postgres_execution_opt_in_acquire_executed": (
                postgres_execution_opt_in_acquire_executed
            ),
            "postgres_execution_opt_in_acquired": postgres_execution_opt_in_acquired,
            "postgres_execution_opt_in_envelope_count": postgres_execution_opt_in_envelope_count,
            "postgres_rollout_consumer_contract_version": (
                postgres_rollout_consumer_contract_version
            ),
            "postgres_rollout_consumer_default_status": (
                postgres_rollout_consumer_default_status
            ),
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
            "postgres_target_binding_contract_version": (
                postgres_target_binding_contract_version
            ),
            "postgres_target_binding_default_status": (
                postgres_target_binding_default_status
            ),
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
            "postgres_semantics_binding_ready_status": (
                postgres_semantics_binding_ready_status
            ),
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
            "vendor_lock_target_decision_contract_version": (
                vendor_lock_target_decision_contract_version
            ),
            "vendor_lock_target_decision_status": vendor_lock_target_decision_status,
            "vendor_lock_target_decision_recorded": vendor_lock_target_decision_recorded,
            "vendor_lock_target_backend": vendor_lock_target_backend,
            "vendor_lock_target_adapter_kind": vendor_lock_target_adapter_kind,
            "vendor_lock_target_scope": vendor_lock_target_scope,
            "vendor_lock_target_fencing_strategy": vendor_lock_target_fencing_strategy,
            "vendor_lock_target_ttl_renewal_strategy": (
                vendor_lock_target_ttl_renewal_strategy
            ),
            "vendor_lock_target_failover_strategy": vendor_lock_target_failover_strategy,
            "vendor_lock_target_stale_cleanup_strategy": (
                vendor_lock_target_stale_cleanup_strategy
            ),
            "vendor_lock_target_missing_sections": list(vendor_lock_target_missing_sections),
            "vendor_lock_target_sql_row_lease_is_vendor_lock": (
                vendor_lock_target_sql_row_lease_is_vendor_lock
            ),
            "vendor_lock_target_production_allowed": vendor_lock_target_production_allowed,
            "vendor_lock_target_input_contract_version": (
                vendor_lock_target_input_contract_version
            ),
            "vendor_lock_target_input_source_status": vendor_lock_target_input_source_status,
            "vendor_lock_target_input_source_kind": vendor_lock_target_input_source_kind,
            "vendor_lock_target_input_decision_id": vendor_lock_target_input_decision_id,
            "vendor_lock_target_input_approved_by": vendor_lock_target_input_approved_by,
            "vendor_lock_target_input_approved_at": vendor_lock_target_input_approved_at,
            "vendor_lock_target_input_backend": vendor_lock_target_input_backend,
            "vendor_lock_target_input_adapter_kind": vendor_lock_target_input_adapter_kind,
            "vendor_lock_target_input_rollout_artifact": (
                vendor_lock_target_input_rollout_artifact
            ),
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
            "renewal_supervisor_ttl_interval_policy_ready": (
                renewal_supervisor_ttl_interval_policy_ready
            ),
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
            "rollout_confirmation_input_source_status": (
                rollout_confirmation_input_source_status
            ),
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
            "enablement_renewal_lifecycle_reference": (
                enablement_renewal_lifecycle_reference
            ),
            "enablement_auto_claim_decision_reference": (
                enablement_auto_claim_decision_reference
            ),
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
            "configurable_knob_present": configurable_knob_present,
            "hot_reloadable_knob_present": hot_reloadable_knob_present,
            "strict_mode_status": strict_mode_status,
            "fallback_mode_status": fallback_mode_status,
        }

    def _build_recovery_retry_evidence_coverage(self, check: Mapping[str, Any]) -> Dict[str, Any]:
        return self._normalize_recovery_retry_evidence_coverage({
            "retry_smoke": bool(check.get("ok")) if check else False,
            "contract_version": str(check.get("contract_version") or ""),
            "attempt_number": self._coerce_optional_non_negative_int(check.get("attempt_number")) or 0,
            "max_attempts": self._coerce_optional_non_negative_int(check.get("max_attempts")) or 0,
            "retry_status": str(check.get("retry_status") or ""),
            "retryable": check.get("retryable"),
            "terminal": check.get("terminal"),
            "recovery_reason": str(check.get("recovery_reason") or ""),
            "idempotency_key_present": check.get("idempotency_key_present"),
        })

    def _normalize_recovery_retry_evidence_coverage(self, coverage: Mapping[str, Any]) -> Dict[str, Any]:
        contract_version = str(coverage.get("contract_version") or "")
        attempt_number = self._coerce_optional_non_negative_int(coverage.get("attempt_number")) or 0
        max_attempts = self._coerce_optional_non_negative_int(coverage.get("max_attempts")) or 0
        retry_status = str(coverage.get("retry_status") or "")
        retryable = self._coerce_truthy_flag(coverage.get("retryable"))
        terminal = self._coerce_truthy_flag(coverage.get("terminal"))
        recovery_reason = str(coverage.get("recovery_reason") or "")
        idempotency_key_present = self._coerce_truthy_flag(coverage.get("idempotency_key_present"))
        retry_smoke = (
            self._coerce_truthy_flag(coverage.get("retry_smoke"))
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

    def _build_durable_recovery_loader_coverage(self, check: Mapping[str, Any]) -> Dict[str, Any]:
        return self._normalize_durable_recovery_loader_coverage({
            "loader_smoke": bool(check.get("ok")) if check else False,
            "contract_version": str(check.get("contract_version") or ""),
            "loader_status": str(check.get("loader_status") or ""),
            "loader_ready": check.get("loader_ready"),
            "loader_recovery_reason": str(check.get("loader_recovery_reason") or ""),
            "all_bindings_resolved": check.get("all_bindings_resolved"),
            "missing_recovery_reason": str(check.get("missing_recovery_reason") or ""),
            "unsafe_recovery_reason": str(check.get("unsafe_recovery_reason") or ""),
            "executes_recovery": check.get("executes_recovery"),
            "deserializes_callables": check.get("deserializes_callables"),
        })

    def _normalize_durable_recovery_loader_coverage(self, coverage: Mapping[str, Any]) -> Dict[str, Any]:
        contract_version = str(coverage.get("contract_version") or "")
        loader_status = str(coverage.get("loader_status") or "")
        loader_ready = self._coerce_truthy_flag(coverage.get("loader_ready"))
        loader_recovery_reason = str(coverage.get("loader_recovery_reason") or "")
        all_bindings_resolved = self._coerce_truthy_flag(coverage.get("all_bindings_resolved"))
        missing_recovery_reason = str(coverage.get("missing_recovery_reason") or "")
        unsafe_recovery_reason = str(coverage.get("unsafe_recovery_reason") or "")
        executes_recovery = self._coerce_truthy_flag(coverage.get("executes_recovery"))
        deserializes_callables = self._coerce_truthy_flag(coverage.get("deserializes_callables"))
        loader_smoke = (
            self._coerce_truthy_flag(coverage.get("loader_smoke"))
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

    def _build_continuation_descriptor_lifecycle_coverage(self, check: Mapping[str, Any]) -> Dict[str, Any]:
        return self._normalize_continuation_descriptor_lifecycle_coverage({
            "lifecycle_smoke": bool(check.get("ok")) if check else False,
            "contract_version": str(check.get("descriptor_lifecycle_contract_version") or ""),
            "governed": check.get("descriptor_lifecycle_governed"),
            "states": self._normalize_string_list(check.get("descriptor_lifecycle_states")),
            "all_ready": check.get("descriptor_lifecycle_all_ready"),
            "unsafe_descriptor_keys": self._normalize_string_list(check.get("descriptor_lifecycle_unsafe_keys")),
            "unresolved_recovery_reason": str(check.get("unresolved_recovery_reason") or ""),
            "stale_recovery_reason": str(check.get("stale_recovery_reason") or ""),
            "unsafe_recovery_reason": str(check.get("unsafe_recovery_reason") or ""),
        })

    def _normalize_continuation_descriptor_lifecycle_coverage(
        self,
        coverage: Mapping[str, Any],
    ) -> Dict[str, Any]:
        contract_version = str(coverage.get("contract_version") or "")
        governed = self._coerce_truthy_flag(coverage.get("governed"))
        states = self._normalize_string_list(coverage.get("states"))
        all_ready = self._coerce_truthy_flag(coverage.get("all_ready"))
        unsafe_keys = self._normalize_string_list(coverage.get("unsafe_descriptor_keys"))
        unresolved_reason = str(coverage.get("unresolved_recovery_reason") or "")
        stale_reason = str(coverage.get("stale_recovery_reason") or "")
        unsafe_reason = str(coverage.get("unsafe_recovery_reason") or "")
        lifecycle_smoke = (
            self._coerce_truthy_flag(coverage.get("lifecycle_smoke"))
            and contract_version == "phase-ii-continuation-descriptor-lifecycle-governance-v1"
            and governed
            and all_ready
            and {"ready", "bound", "stale", "unsafe"}.issubset(set(states))
            and "handler" in unsafe_keys
            and unresolved_reason == "missing_registered_binding"
            and stale_reason == "denied"
            and unsafe_reason == "descriptor_corrupted"
        )
        return {
            "lifecycle_smoke": lifecycle_smoke,
            "contract_version": contract_version,
            "governed": governed,
            "states": states,
            "all_ready": all_ready,
            "unsafe_descriptor_keys": unsafe_keys,
            "unresolved_recovery_reason": unresolved_reason,
            "stale_recovery_reason": stale_reason,
            "unsafe_recovery_reason": unsafe_reason,
        }

    def _build_loader_execution_handoff_coverage(self, check: Mapping[str, Any]) -> Dict[str, Any]:
        return self._normalize_loader_execution_handoff_coverage({
            "handoff_smoke": bool(check.get("ok")) if check else False,
            "contract_version": str(check.get("handoff_policy_contract_version") or ""),
            "default_status": str(check.get("default_handoff_status") or ""),
            "default_blocked_reason": str(check.get("default_handoff_blocked_reason") or ""),
            "default_will_execute": check.get("default_handoff_will_execute"),
            "explicit_status": str(check.get("explicit_handoff_status") or ""),
            "explicit_blocked_reason": str(check.get("explicit_handoff_blocked_reason") or ""),
            "explicit_will_execute": check.get("explicit_handoff_will_execute"),
            "recovery_executor_bound": check.get("recovery_executor_bound"),
        })

    def _normalize_loader_execution_handoff_coverage(self, coverage: Mapping[str, Any]) -> Dict[str, Any]:
        contract_version = str(coverage.get("contract_version") or "")
        default_status = str(coverage.get("default_status") or "")
        default_blocked_reason = str(coverage.get("default_blocked_reason") or "")
        default_will_execute = self._coerce_truthy_flag(coverage.get("default_will_execute"))
        explicit_status = str(coverage.get("explicit_status") or "")
        explicit_blocked_reason = str(coverage.get("explicit_blocked_reason") or "")
        explicit_will_execute = self._coerce_truthy_flag(coverage.get("explicit_will_execute"))
        recovery_executor_bound = self._coerce_truthy_flag(coverage.get("recovery_executor_bound"))
        handoff_smoke = (
            self._coerce_truthy_flag(coverage.get("handoff_smoke"))
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

    def _build_recovery_audit_operation_history_coverage(self, check: Mapping[str, Any]) -> Dict[str, Any]:
        return self._normalize_recovery_audit_operation_history_coverage({
            "audit_smoke": bool(check.get("ok")) if check else False,
            "contract_version": str(check.get("recovery_audit_contract_version") or ""),
            "ready": check.get("recovery_audit_ready"),
            "operation_history_supported": check.get("recovery_audit_operation_history_supported"),
            "audit_summary_supported": check.get("recovery_audit_summary_supported"),
            "timeline_writer_available": check.get("recovery_audit_timeline_writer_available"),
            "idempotent_trace_dedupe": check.get("recovery_audit_idempotent_trace_dedupe"),
            "authorization_source": check.get("recovery_audit_authorization_source"),
        })

    def _normalize_recovery_audit_operation_history_coverage(
        self,
        coverage: Mapping[str, Any],
    ) -> Dict[str, Any]:
        contract_version = str(coverage.get("contract_version") or "")
        ready = self._coerce_truthy_flag(coverage.get("ready"))
        operation_history_supported = self._coerce_truthy_flag(coverage.get("operation_history_supported"))
        audit_summary_supported = self._coerce_truthy_flag(coverage.get("audit_summary_supported"))
        timeline_writer_available = self._coerce_truthy_flag(coverage.get("timeline_writer_available"))
        idempotent_trace_dedupe = self._coerce_truthy_flag(coverage.get("idempotent_trace_dedupe"))
        authorization_source = self._coerce_truthy_flag(coverage.get("authorization_source"))
        audit_smoke = (
            self._coerce_truthy_flag(coverage.get("audit_smoke"))
            and contract_version == "phase-ii-recovery-audit-production-gate-v1"
            and ready
            and operation_history_supported
            and audit_summary_supported
            and timeline_writer_available
            and idempotent_trace_dedupe
            and not authorization_source
        )
        return {
            "audit_smoke": audit_smoke,
            "contract_version": contract_version,
            "ready": ready,
            "operation_history_supported": operation_history_supported,
            "audit_summary_supported": audit_summary_supported,
            "timeline_writer_available": timeline_writer_available,
            "idempotent_trace_dedupe": idempotent_trace_dedupe,
            "authorization_source": authorization_source,
        }

    def _build_production_recovery_registry_checkpoint_policy_coverage(
        self,
        check: Mapping[str, Any],
    ) -> Dict[str, Any]:
        return self._normalize_production_recovery_registry_checkpoint_policy_coverage({
            "policy_smoke": bool(check.get("ok")) if check else False,
            "contract_version": str(check.get("registry_checkpoint_policy_contract_version") or ""),
            "ready": check.get("registry_checkpoint_policy_ready"),
            "registry_binding_policy_ready": check.get("registry_binding_policy_ready"),
            "checkpoint_resume_cursor_policy_ready": check.get("checkpoint_resume_cursor_policy_ready"),
            "authorization_source": check.get("registry_checkpoint_policy_authorization_source"),
            "production_recovery_gate_missing_sections": (
                check.get("production_recovery_gate_missing_sections")
                if isinstance(check.get("production_recovery_gate_missing_sections"), list)
                else []
            ),
        })

    def _normalize_production_recovery_registry_checkpoint_policy_coverage(
        self,
        coverage: Mapping[str, Any],
    ) -> Dict[str, Any]:
        contract_version = str(coverage.get("contract_version") or "")
        ready = self._coerce_truthy_flag(coverage.get("ready"))
        registry_binding_policy_ready = self._coerce_truthy_flag(
            coverage.get("registry_binding_policy_ready")
        )
        checkpoint_resume_cursor_policy_ready = self._coerce_truthy_flag(
            coverage.get("checkpoint_resume_cursor_policy_ready")
        )
        authorization_source = self._coerce_truthy_flag(coverage.get("authorization_source"))
        missing_sections = (
            coverage.get("production_recovery_gate_missing_sections")
            if isinstance(coverage.get("production_recovery_gate_missing_sections"), list)
            else []
        )
        policy_smoke = (
            self._coerce_truthy_flag(coverage.get("policy_smoke"))
            and contract_version == "phase-ii-production-recovery-registry-checkpoint-policy-v1"
            and ready
            and registry_binding_policy_ready
            and checkpoint_resume_cursor_policy_ready
            and "registry_binding_resolution" not in missing_sections
            and "checkpoint_resume_cursor_gate" not in missing_sections
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

    def _build_recovery_retry_scheduler_coverage(self, check: Mapping[str, Any]) -> Dict[str, Any]:
        return self._normalize_recovery_retry_scheduler_coverage({
            "scheduler_smoke": bool(check.get("ok")) if check else False,
            "contract_version": str(check.get("contract_version") or ""),
            "default_status": str(check.get("default_status") or ""),
            "default_eligible": check.get("default_eligible"),
            "default_will_execute": check.get("default_will_execute"),
            "production_gate_contract_version": str(check.get("production_gate_contract_version") or ""),
            "production_gate_status": str(check.get("production_gate_status") or ""),
            "production_gate_missing_sections": (
                check.get("production_gate_missing_sections")
                if isinstance(check.get("production_gate_missing_sections"), list)
                else []
            ),
            "production_gate_blocked_reason": str(check.get("production_gate_blocked_reason") or ""),
            "production_automatic_retry_enabled_by_default": check.get(
                "production_automatic_retry_enabled_by_default"
            ),
            "production_automatic_will_execute": check.get("production_automatic_will_execute"),
            "enabled_status": str(check.get("enabled_status") or ""),
            "enabled_will_execute": check.get("enabled_will_execute"),
            "latest_operation_status": str(check.get("latest_operation_status") or ""),
            "attempt_number": self._coerce_optional_non_negative_int(check.get("attempt_number")) or 0,
            "retry_status": str(check.get("retry_status") or ""),
            "recovery_reason": str(check.get("recovery_reason") or ""),
            "previous_operation_id_present": check.get("previous_operation_id_present"),
            "idempotency_key_present": check.get("idempotency_key_present"),
        })

    def _normalize_recovery_retry_scheduler_coverage(self, coverage: Mapping[str, Any]) -> Dict[str, Any]:
        contract_version = str(coverage.get("contract_version") or "")
        default_status = str(coverage.get("default_status") or "")
        default_eligible = self._coerce_truthy_flag(coverage.get("default_eligible"))
        default_will_execute = self._coerce_truthy_flag(coverage.get("default_will_execute"))
        production_gate_contract_version = str(coverage.get("production_gate_contract_version") or "")
        production_gate_status = str(coverage.get("production_gate_status") or "")
        production_gate_missing_sections = (
            coverage.get("production_gate_missing_sections")
            if isinstance(coverage.get("production_gate_missing_sections"), list)
            else []
        )
        production_gate_blocked_reason = str(coverage.get("production_gate_blocked_reason") or "")
        production_automatic_enabled_by_default = self._coerce_truthy_flag(
            coverage.get("production_automatic_retry_enabled_by_default")
        )
        production_automatic_will_execute = self._coerce_truthy_flag(
            coverage.get("production_automatic_will_execute")
        )
        enabled_status = str(coverage.get("enabled_status") or "")
        enabled_will_execute = self._coerce_truthy_flag(coverage.get("enabled_will_execute"))
        latest_operation_status = str(coverage.get("latest_operation_status") or "")
        attempt_number = self._coerce_optional_non_negative_int(coverage.get("attempt_number")) or 0
        retry_status = str(coverage.get("retry_status") or "")
        recovery_reason = str(coverage.get("recovery_reason") or "")
        previous_operation_id_present = self._coerce_truthy_flag(coverage.get("previous_operation_id_present"))
        idempotency_key_present = self._coerce_truthy_flag(coverage.get("idempotency_key_present"))
        scheduler_smoke = (
            self._coerce_truthy_flag(coverage.get("scheduler_smoke"))
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

    def _build_child_executor_promotion_gate_coverage(self, check: Mapping[str, Any]) -> Dict[str, Any]:
        return self._normalize_child_executor_promotion_gate_coverage({
            "gate_smoke": bool(check.get("ok")) if check else False,
            "contract_version": str(check.get("contract_version") or ""),
            "gate_status": str(check.get("gate_status") or ""),
            "allowed": check.get("allowed"),
            "failure_reason": str(check.get("gate_failure_reason") or check.get("failure_reason") or ""),
            "blocker_count": self._coerce_optional_non_negative_int(check.get("blocker_count")) or 0,
            "recommended_next_step": str(check.get("recommended_next_step") or ""),
        })

    def _normalize_child_executor_promotion_gate_coverage(self, coverage: Mapping[str, Any]) -> Dict[str, Any]:
        contract_version = str(coverage.get("contract_version") or "")
        gate_status = str(coverage.get("gate_status") or "")
        allowed = self._coerce_truthy_flag(coverage.get("allowed"))
        failure_reason = str(coverage.get("failure_reason") or "")
        blocker_count = self._coerce_optional_non_negative_int(coverage.get("blocker_count")) or 0
        recommended_next_step = str(coverage.get("recommended_next_step") or "")
        gate_smoke = (
            self._coerce_truthy_flag(coverage.get("gate_smoke"))
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

    def _build_child_executor_execution_prerequisites_coverage(self, check: Mapping[str, Any]) -> Dict[str, Any]:
        return self._normalize_child_executor_execution_prerequisites_coverage({
            "prerequisites_smoke": bool(check.get("ok")) if check else False,
            "contract_version": str(check.get("prerequisites_contract_version") or ""),
            "overall_status": str(check.get("prerequisites_status") or ""),
            "ready": check.get("prerequisites_ready"),
            "requirement_count": self._coerce_optional_non_negative_int(
                check.get("prerequisites_requirement_count")
            ) or 0,
            "missing_requirement_count": self._coerce_optional_non_negative_int(
                check.get("prerequisites_missing_requirement_count")
            ) or 0,
            "missing_requirements": self._normalize_string_list(check.get("prerequisites_missing_requirements")),
            "explicit_executor_binding_status": str(check.get("explicit_executor_binding_status") or ""),
            "explicit_executor_binding_ready": check.get("explicit_executor_binding_ready"),
            "explicit_executor_binding_missing": check.get("explicit_executor_binding_missing"),
            "context_budget_policy_status": str(check.get("context_budget_policy_status") or ""),
            "context_budget_policy_ready": check.get("context_budget_policy_ready"),
            "context_budget_policy_missing": check.get("context_budget_policy_missing"),
            "context_budget_policy_missing_sections": self._normalize_string_list(
                check.get("context_budget_policy_missing_sections")
            ),
            "context_budget_policy_source": str(check.get("context_budget_policy_source") or ""),
            "merge_handoff_status": str(check.get("merge_handoff_status") or ""),
            "merge_handoff_ready": check.get("merge_handoff_ready"),
            "merge_handoff_missing": check.get("merge_handoff_missing"),
            "merge_handoff_missing_sections": self._normalize_string_list(
                check.get("merge_handoff_missing_sections")
            ),
            "merge_handoff_strategy": str(check.get("merge_handoff_strategy") or ""),
            "merge_handoff_source": str(check.get("merge_handoff_source") or ""),
            "opt_in_explicit_executor_binding_status": str(
                check.get("opt_in_explicit_executor_binding_status") or ""
            ),
            "opt_in_explicit_executor_binding_ready": check.get(
                "opt_in_explicit_executor_binding_ready"
            ),
            "opt_in_explicit_executor_binding_source": str(
                check.get("opt_in_explicit_executor_binding_source") or ""
            ),
            "opt_in_explicit_executor_binding_backend": str(
                check.get("opt_in_explicit_executor_binding_backend") or ""
            ),
            "opt_in_context_budget_policy_status": str(
                check.get("opt_in_context_budget_policy_status") or ""
            ),
            "opt_in_context_budget_policy_ready": check.get(
                "opt_in_context_budget_policy_ready"
            ),
            "opt_in_context_budget_policy_source": str(
                check.get("opt_in_context_budget_policy_source") or ""
            ),
            "opt_in_context_budget_policy_max_turns": self._coerce_optional_non_negative_int(
                check.get("opt_in_context_budget_policy_max_turns")
            ) or 0,
            "opt_in_merge_handoff_status": str(check.get("opt_in_merge_handoff_status") or ""),
            "opt_in_merge_handoff_ready": check.get("opt_in_merge_handoff_ready"),
            "opt_in_merge_handoff_strategy": str(check.get("opt_in_merge_handoff_strategy") or ""),
            "opt_in_merge_handoff_source": str(check.get("opt_in_merge_handoff_source") or ""),
            "opt_in_skeleton_execution_status": str(check.get("opt_in_skeleton_execution_status") or ""),
            "opt_in_skeleton_will_execute": check.get("opt_in_skeleton_will_execute"),
            "opt_in_skeleton_execution_mode": str(check.get("opt_in_skeleton_execution_mode") or ""),
        })

    def _normalize_child_executor_execution_prerequisites_coverage(
        self,
        coverage: Mapping[str, Any],
    ) -> Dict[str, Any]:
        contract_version = str(coverage.get("contract_version") or "")
        overall_status = str(coverage.get("overall_status") or "")
        ready = self._coerce_truthy_flag(coverage.get("ready"))
        requirement_count = self._coerce_optional_non_negative_int(coverage.get("requirement_count")) or 0
        missing_requirement_count = (
            self._coerce_optional_non_negative_int(coverage.get("missing_requirement_count")) or 0
        )
        missing_requirements = self._normalize_string_list(coverage.get("missing_requirements"))
        explicit_binding_status = str(coverage.get("explicit_executor_binding_status") or "")
        explicit_binding_ready = self._coerce_truthy_flag(coverage.get("explicit_executor_binding_ready"))
        explicit_binding_missing = self._coerce_truthy_flag(coverage.get("explicit_executor_binding_missing"))
        context_budget_policy_status = str(coverage.get("context_budget_policy_status") or "")
        context_budget_policy_ready = self._coerce_truthy_flag(coverage.get("context_budget_policy_ready"))
        context_budget_policy_missing = self._coerce_truthy_flag(coverage.get("context_budget_policy_missing"))
        context_budget_policy_missing_sections = self._normalize_string_list(
            coverage.get("context_budget_policy_missing_sections")
        )
        merge_handoff_status = str(coverage.get("merge_handoff_status") or "")
        merge_handoff_ready = self._coerce_truthy_flag(coverage.get("merge_handoff_ready"))
        merge_handoff_missing = self._coerce_truthy_flag(coverage.get("merge_handoff_missing"))
        merge_handoff_missing_sections = self._normalize_string_list(
            coverage.get("merge_handoff_missing_sections")
        )
        opt_in_explicit_binding_status = str(
            coverage.get("opt_in_explicit_executor_binding_status") or ""
        )
        opt_in_explicit_binding_ready = self._coerce_truthy_flag(
            coverage.get("opt_in_explicit_executor_binding_ready")
        )
        opt_in_context_budget_policy_status = str(
            coverage.get("opt_in_context_budget_policy_status") or ""
        )
        opt_in_context_budget_policy_ready = self._coerce_truthy_flag(
            coverage.get("opt_in_context_budget_policy_ready")
        )
        opt_in_context_budget_policy_max_turns = (
            self._coerce_optional_non_negative_int(
                coverage.get("opt_in_context_budget_policy_max_turns")
            )
            or 0
        )
        opt_in_merge_handoff_status = str(coverage.get("opt_in_merge_handoff_status") or "")
        opt_in_merge_handoff_ready = self._coerce_truthy_flag(
            coverage.get("opt_in_merge_handoff_ready")
        )
        opt_in_merge_handoff_strategy = str(coverage.get("opt_in_merge_handoff_strategy") or "")
        opt_in_skeleton_execution_status = str(
            coverage.get("opt_in_skeleton_execution_status") or ""
        )
        opt_in_skeleton_will_execute = self._coerce_truthy_flag(
            coverage.get("opt_in_skeleton_will_execute")
        )
        prerequisites_smoke = (
            self._coerce_truthy_flag(coverage.get("prerequisites_smoke"))
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
            "context_budget_policy_source": str(
                coverage.get("context_budget_policy_source") or ""
            ),
            "merge_handoff_status": merge_handoff_status,
            "merge_handoff_ready": merge_handoff_ready,
            "merge_handoff_missing": merge_handoff_missing,
            "merge_handoff_missing_sections": merge_handoff_missing_sections,
            "merge_handoff_strategy": str(coverage.get("merge_handoff_strategy") or ""),
            "merge_handoff_source": str(coverage.get("merge_handoff_source") or ""),
            "opt_in_explicit_executor_binding_status": opt_in_explicit_binding_status,
            "opt_in_explicit_executor_binding_ready": opt_in_explicit_binding_ready,
            "opt_in_explicit_executor_binding_source": str(
                coverage.get("opt_in_explicit_executor_binding_source") or ""
            ),
            "opt_in_explicit_executor_binding_backend": str(
                coverage.get("opt_in_explicit_executor_binding_backend") or ""
            ),
            "opt_in_context_budget_policy_status": opt_in_context_budget_policy_status,
            "opt_in_context_budget_policy_ready": opt_in_context_budget_policy_ready,
            "opt_in_context_budget_policy_source": str(
                coverage.get("opt_in_context_budget_policy_source") or ""
            ),
            "opt_in_context_budget_policy_max_turns": opt_in_context_budget_policy_max_turns,
            "opt_in_merge_handoff_status": opt_in_merge_handoff_status,
            "opt_in_merge_handoff_ready": opt_in_merge_handoff_ready,
            "opt_in_merge_handoff_strategy": opt_in_merge_handoff_strategy,
            "opt_in_merge_handoff_source": str(coverage.get("opt_in_merge_handoff_source") or ""),
            "opt_in_skeleton_execution_status": opt_in_skeleton_execution_status,
            "opt_in_skeleton_will_execute": opt_in_skeleton_will_execute,
            "opt_in_skeleton_execution_mode": str(
                coverage.get("opt_in_skeleton_execution_mode") or ""
            ),
        }

    def _build_child_executor_dispatch_coverage(self, check: Mapping[str, Any]) -> Dict[str, Any]:
        return self._normalize_child_executor_dispatch_coverage({
            "dispatch_smoke": bool(check.get("ok")) if check else False,
            "contract_version": str(check.get("contract_version") or ""),
            "overall_status": str(check.get("dispatch_status") or ""),
            "dispatch_ready": check.get("dispatch_ready"),
            "will_dispatch": check.get("will_dispatch"),
            "backend_dispatch_ready": check.get("backend_dispatch_ready"),
            "relationship_seam_preserved": check.get("relationship_seam_preserved"),
            "blocker_count": self._coerce_optional_non_negative_int(check.get("dispatch_blocker_count")) or 0,
            "dispatch_blockers": self._normalize_string_list(check.get("dispatch_blockers")),
            "explicit_executor_binding_ready": check.get("explicit_executor_binding_ready"),
            "explicit_executor_binding_status": str(check.get("explicit_executor_binding_status") or ""),
            "explicit_executor_binding_source": str(check.get("explicit_executor_binding_source") or ""),
            "opt_in_dispatch_status": str(check.get("opt_in_dispatch_status") or ""),
            "opt_in_dispatch_ready": check.get("opt_in_dispatch_ready"),
            "opt_in_will_dispatch": check.get("opt_in_will_dispatch"),
            "opt_in_backend_dispatch_ready": check.get("opt_in_backend_dispatch_ready"),
            "opt_in_explicit_executor_binding_ready": check.get(
                "opt_in_explicit_executor_binding_ready"
            ),
            "opt_in_explicit_executor_binding_status": str(
                check.get("opt_in_explicit_executor_binding_status") or ""
            ),
            "opt_in_explicit_executor_binding_source": str(
                check.get("opt_in_explicit_executor_binding_source") or ""
            ),
            "dispatch_attempt_handoff_status": str(
                check.get("dispatch_attempt_handoff_status") or ""
            ),
            "dispatch_attempt_handoff_ready": check.get("dispatch_attempt_handoff_ready"),
            "dispatch_attempt_handoff_missing_sections": self._normalize_string_list(
                check.get("dispatch_attempt_handoff_missing_sections")
            ),
            "dispatch_attempt_handoff_will_dispatch": check.get(
                "dispatch_attempt_handoff_will_dispatch"
            ),
            "opt_in_dispatch_attempt_handoff_status": str(
                check.get("opt_in_dispatch_attempt_handoff_status") or ""
            ),
            "opt_in_dispatch_attempt_handoff_ready": check.get(
                "opt_in_dispatch_attempt_handoff_ready"
            ),
            "opt_in_attempt_envelope_supported": check.get(
                "opt_in_attempt_envelope_supported"
            ),
            "opt_in_attempt_validation_ready": check.get("opt_in_attempt_validation_ready"),
            "opt_in_attempt_will_dispatch": check.get("opt_in_attempt_will_dispatch"),
            "opt_in_unsafe_payload_guard_ready": check.get(
                "opt_in_unsafe_payload_guard_ready"
            ),
            "unsafe_payload_guard_status": str(check.get("unsafe_payload_guard_status") or ""),
            "unsafe_payload_guard_ready": check.get("unsafe_payload_guard_ready"),
            "unsafe_payload_keys": self._normalize_string_list(check.get("unsafe_payload_keys")),
            "recommended_next_step": str(check.get("recommended_next_step") or ""),
        })

    def _normalize_child_executor_dispatch_coverage(
        self,
        coverage: Mapping[str, Any],
    ) -> Dict[str, Any]:
        contract_version = str(coverage.get("contract_version") or "")
        overall_status = str(coverage.get("overall_status") or "")
        dispatch_ready = self._coerce_truthy_flag(coverage.get("dispatch_ready"))
        will_dispatch = self._coerce_truthy_flag(coverage.get("will_dispatch"))
        backend_dispatch_ready = self._coerce_truthy_flag(coverage.get("backend_dispatch_ready"))
        relationship_seam_preserved = self._coerce_truthy_flag(coverage.get("relationship_seam_preserved"))
        blocker_count = self._coerce_optional_non_negative_int(coverage.get("blocker_count")) or 0
        dispatch_blockers = self._normalize_string_list(coverage.get("dispatch_blockers"))
        explicit_binding_ready = self._coerce_truthy_flag(coverage.get("explicit_executor_binding_ready"))
        explicit_binding_status = str(coverage.get("explicit_executor_binding_status") or "")
        opt_in_dispatch_status = str(coverage.get("opt_in_dispatch_status") or "")
        opt_in_dispatch_ready = self._coerce_truthy_flag(coverage.get("opt_in_dispatch_ready"))
        opt_in_will_dispatch = self._coerce_truthy_flag(coverage.get("opt_in_will_dispatch"))
        opt_in_backend_dispatch_ready = self._coerce_truthy_flag(
            coverage.get("opt_in_backend_dispatch_ready")
        )
        opt_in_explicit_binding_ready = self._coerce_truthy_flag(
            coverage.get("opt_in_explicit_executor_binding_ready")
        )
        opt_in_explicit_binding_status = str(
            coverage.get("opt_in_explicit_executor_binding_status") or ""
        )
        dispatch_attempt_handoff_status = str(coverage.get("dispatch_attempt_handoff_status") or "")
        dispatch_attempt_handoff_ready = self._coerce_truthy_flag(
            coverage.get("dispatch_attempt_handoff_ready")
        )
        dispatch_attempt_handoff_missing_sections = self._normalize_string_list(
            coverage.get("dispatch_attempt_handoff_missing_sections")
        )
        dispatch_attempt_handoff_will_dispatch = self._coerce_truthy_flag(
            coverage.get("dispatch_attempt_handoff_will_dispatch")
        )
        opt_in_dispatch_attempt_handoff_status = str(
            coverage.get("opt_in_dispatch_attempt_handoff_status") or ""
        )
        opt_in_dispatch_attempt_handoff_ready = self._coerce_truthy_flag(
            coverage.get("opt_in_dispatch_attempt_handoff_ready")
        )
        opt_in_attempt_envelope_supported = self._coerce_truthy_flag(
            coverage.get("opt_in_attempt_envelope_supported")
        )
        opt_in_attempt_validation_ready = self._coerce_truthy_flag(
            coverage.get("opt_in_attempt_validation_ready")
        )
        opt_in_attempt_will_dispatch = self._coerce_truthy_flag(
            coverage.get("opt_in_attempt_will_dispatch")
        )
        opt_in_unsafe_payload_guard_ready = self._coerce_truthy_flag(
            coverage.get("opt_in_unsafe_payload_guard_ready")
        )
        unsafe_payload_guard_status = str(coverage.get("unsafe_payload_guard_status") or "")
        unsafe_payload_guard_ready = self._coerce_truthy_flag(
            coverage.get("unsafe_payload_guard_ready")
        )
        unsafe_payload_keys = self._normalize_string_list(coverage.get("unsafe_payload_keys"))
        recommended_next_step = str(coverage.get("recommended_next_step") or "")
        dispatch_smoke = (
            self._coerce_truthy_flag(coverage.get("dispatch_smoke"))
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
            "explicit_executor_binding_source": str(coverage.get("explicit_executor_binding_source") or ""),
            "opt_in_dispatch_status": opt_in_dispatch_status,
            "opt_in_dispatch_ready": opt_in_dispatch_ready,
            "opt_in_will_dispatch": opt_in_will_dispatch,
            "opt_in_backend_dispatch_ready": opt_in_backend_dispatch_ready,
            "opt_in_explicit_executor_binding_ready": opt_in_explicit_binding_ready,
            "opt_in_explicit_executor_binding_status": opt_in_explicit_binding_status,
            "opt_in_explicit_executor_binding_source": str(
                coverage.get("opt_in_explicit_executor_binding_source") or ""
            ),
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

    def _build_child_executor_dispatcher_coverage(self, check: Mapping[str, Any]) -> Dict[str, Any]:
        return self._normalize_child_executor_dispatcher_coverage({
            "dispatcher_smoke": bool(check.get("ok")) if check else False,
            "contract_version": str(check.get("contract_version") or ""),
            "default_status": str(check.get("default_status") or ""),
            "default_blocked_reason": str(check.get("default_blocked_reason") or ""),
            "default_will_dispatch": check.get("default_will_dispatch"),
            "blocked_reason": str(check.get("blocked_reason") or ""),
            "blocked_will_dispatch": check.get("blocked_will_dispatch"),
            "enabled_status": str(check.get("enabled_status") or ""),
            "enabled_will_dispatch": check.get("enabled_will_dispatch"),
            "backend_result_status": str(check.get("backend_result_status") or ""),
            "backend_invocation_count": self._coerce_optional_non_negative_int(
                check.get("backend_invocation_count")
            ) or 0,
        })

    def _normalize_child_executor_dispatcher_coverage(
        self,
        coverage: Mapping[str, Any],
    ) -> Dict[str, Any]:
        contract_version = str(coverage.get("contract_version") or "")
        default_status = str(coverage.get("default_status") or "")
        default_blocked_reason = str(coverage.get("default_blocked_reason") or "")
        default_will_dispatch = self._coerce_truthy_flag(coverage.get("default_will_dispatch"))
        blocked_reason = str(coverage.get("blocked_reason") or "")
        blocked_will_dispatch = self._coerce_truthy_flag(coverage.get("blocked_will_dispatch"))
        enabled_status = str(coverage.get("enabled_status") or "")
        enabled_will_dispatch = self._coerce_truthy_flag(coverage.get("enabled_will_dispatch"))
        backend_result_status = str(coverage.get("backend_result_status") or "")
        backend_invocation_count = (
            self._coerce_optional_non_negative_int(coverage.get("backend_invocation_count")) or 0
        )
        dispatcher_smoke = (
            self._coerce_truthy_flag(coverage.get("dispatcher_smoke"))
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

    def _build_child_executor_dispatch_result_handoff_coverage(
        self,
        check: Mapping[str, Any],
    ) -> Dict[str, Any]:
        return self._normalize_child_executor_dispatch_result_handoff_coverage({
            "result_handoff_smoke": bool(check.get("ok")) if check else False,
            "contract_version": str(check.get("contract_version") or ""),
            "ready_handoff_status": str(check.get("ready_handoff_status") or ""),
            "ready_handoff_ready": check.get("ready_handoff_ready"),
            "ready_output_ref_present": check.get("ready_output_ref_present"),
            "ready_audit_evidence_present": check.get("ready_audit_evidence_present"),
            "ready_backend_result_schema_valid": check.get(
                "ready_backend_result_schema_valid"
            ),
            "ready_parent_merge_performed": check.get("ready_parent_merge_performed"),
            "ready_merge_authorization": check.get("ready_merge_authorization"),
            "ready_retry_scheduled": check.get("ready_retry_scheduled"),
            "ready_production_dispatch_authorized": check.get(
                "ready_production_dispatch_authorized"
            ),
            "blocked_handoff_status": str(check.get("blocked_handoff_status") or ""),
            "blocked_dispatcher_reason": str(check.get("blocked_dispatcher_reason") or ""),
            "blocked_missing_sections": self._normalize_string_list(
                check.get("blocked_missing_sections")
            ),
            "malformed_handoff_status": str(check.get("malformed_handoff_status") or ""),
            "malformed_missing_sections": self._normalize_string_list(
                check.get("malformed_missing_sections")
            ),
        })

    def _normalize_child_executor_dispatch_result_handoff_coverage(
        self,
        coverage: Mapping[str, Any],
    ) -> Dict[str, Any]:
        contract_version = str(coverage.get("contract_version") or "")
        ready_handoff_status = str(coverage.get("ready_handoff_status") or "")
        ready_handoff_ready = self._coerce_truthy_flag(coverage.get("ready_handoff_ready"))
        ready_output_ref_present = self._coerce_truthy_flag(
            coverage.get("ready_output_ref_present")
        )
        ready_audit_evidence_present = self._coerce_truthy_flag(
            coverage.get("ready_audit_evidence_present")
        )
        ready_backend_result_schema_valid = self._coerce_truthy_flag(
            coverage.get("ready_backend_result_schema_valid")
        )
        ready_parent_merge_performed = self._coerce_truthy_flag(
            coverage.get("ready_parent_merge_performed")
        )
        ready_merge_authorization = self._coerce_truthy_flag(
            coverage.get("ready_merge_authorization")
        )
        ready_retry_scheduled = self._coerce_truthy_flag(
            coverage.get("ready_retry_scheduled")
        )
        ready_production_dispatch_authorized = self._coerce_truthy_flag(
            coverage.get("ready_production_dispatch_authorized")
        )
        blocked_handoff_status = str(coverage.get("blocked_handoff_status") or "")
        blocked_dispatcher_reason = str(coverage.get("blocked_dispatcher_reason") or "")
        blocked_missing_sections = self._normalize_string_list(
            coverage.get("blocked_missing_sections")
        )
        malformed_handoff_status = str(coverage.get("malformed_handoff_status") or "")
        malformed_missing_sections = self._normalize_string_list(
            coverage.get("malformed_missing_sections")
        )
        result_handoff_smoke = (
            self._coerce_truthy_flag(coverage.get("result_handoff_smoke"))
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

    def _build_child_executor_dispatch_result_retry_audit_coverage(
        self,
        check: Mapping[str, Any],
    ) -> Dict[str, Any]:
        return self._normalize_child_executor_dispatch_result_retry_audit_coverage({
            "retry_audit_smoke": bool(check.get("ok")) if check else False,
            "contract_version": str(check.get("contract_version") or ""),
            "success_policy_status": str(check.get("success_policy_status") or ""),
            "success_retry_policy_status": str(check.get("success_retry_policy_status") or ""),
            "success_retry_scheduled": check.get("success_retry_scheduled"),
            "success_will_retry": check.get("success_will_retry"),
            "retryable_policy_status": str(check.get("retryable_policy_status") or ""),
            "retryable_retry_policy_status": str(check.get("retryable_retry_policy_status") or ""),
            "retryable_audit_evidence_present": check.get("retryable_audit_evidence_present"),
            "retryable_idempotency_evidence_present": check.get(
                "retryable_idempotency_evidence_present"
            ),
            "retryable_scheduler_required": check.get("retryable_scheduler_required"),
            "retryable_retry_reason": str(check.get("retryable_retry_reason") or ""),
            "retryable_retry_scheduled": check.get("retryable_retry_scheduled"),
            "retryable_will_retry": check.get("retryable_will_retry"),
            "terminal_policy_status": str(check.get("terminal_policy_status") or ""),
            "terminal_retry_policy_status": str(check.get("terminal_retry_policy_status") or ""),
            "terminal_reason": str(check.get("terminal_reason") or ""),
            "terminal_will_retry": check.get("terminal_will_retry"),
            "missing_idempotency_status": str(check.get("missing_idempotency_status") or ""),
            "missing_idempotency_missing_sections": self._normalize_string_list(
                check.get("missing_idempotency_missing_sections")
            ),
            "missing_idempotency_retry_scheduled": check.get(
                "missing_idempotency_retry_scheduled"
            ),
        })

    def _normalize_child_executor_dispatch_result_retry_audit_coverage(
        self,
        coverage: Mapping[str, Any],
    ) -> Dict[str, Any]:
        contract_version = str(coverage.get("contract_version") or "")
        success_policy_status = str(coverage.get("success_policy_status") or "")
        success_retry_policy_status = str(coverage.get("success_retry_policy_status") or "")
        success_retry_scheduled = self._coerce_truthy_flag(coverage.get("success_retry_scheduled"))
        success_will_retry = self._coerce_truthy_flag(coverage.get("success_will_retry"))
        retryable_policy_status = str(coverage.get("retryable_policy_status") or "")
        retryable_retry_policy_status = str(coverage.get("retryable_retry_policy_status") or "")
        retryable_audit_evidence_present = self._coerce_truthy_flag(
            coverage.get("retryable_audit_evidence_present")
        )
        retryable_idempotency_evidence_present = self._coerce_truthy_flag(
            coverage.get("retryable_idempotency_evidence_present")
        )
        retryable_scheduler_required = self._coerce_truthy_flag(
            coverage.get("retryable_scheduler_required")
        )
        retryable_retry_reason = str(coverage.get("retryable_retry_reason") or "")
        retryable_retry_scheduled = self._coerce_truthy_flag(
            coverage.get("retryable_retry_scheduled")
        )
        retryable_will_retry = self._coerce_truthy_flag(coverage.get("retryable_will_retry"))
        terminal_policy_status = str(coverage.get("terminal_policy_status") or "")
        terminal_retry_policy_status = str(coverage.get("terminal_retry_policy_status") or "")
        terminal_reason = str(coverage.get("terminal_reason") or "")
        terminal_will_retry = self._coerce_truthy_flag(coverage.get("terminal_will_retry"))
        missing_idempotency_status = str(coverage.get("missing_idempotency_status") or "")
        missing_idempotency_missing_sections = self._normalize_string_list(
            coverage.get("missing_idempotency_missing_sections")
        )
        missing_idempotency_retry_scheduled = self._coerce_truthy_flag(
            coverage.get("missing_idempotency_retry_scheduled")
        )
        retry_audit_smoke = (
            self._coerce_truthy_flag(coverage.get("retry_audit_smoke"))
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

    def _build_child_executor_sandbox_backend_coverage(self, check: Mapping[str, Any]) -> Dict[str, Any]:
        return self._normalize_child_executor_sandbox_backend_coverage({
            "sandbox_backend_smoke": bool(check.get("ok")) if check else False,
            "contract_version": str(check.get("contract_version") or ""),
            "ready_adapter_contract": check.get("ready_adapter_contract"),
            "ready_sandbox_guard": check.get("ready_sandbox_guard"),
            "ready_audit": check.get("ready_audit"),
            "ready_idempotency": check.get("ready_idempotency"),
            "missing_guard_fail_closed": check.get("missing_guard_fail_closed"),
            "missing_guard_count": self._coerce_optional_non_negative_int(
                check.get("missing_guard_count")
            ) or 0,
            "unsafe_payload_blocked": check.get("unsafe_payload_blocked"),
            "unsafe_blocked_reason": str(check.get("unsafe_blocked_reason") or ""),
            "compact_attempt_valid": check.get("compact_attempt_valid"),
            "dispatch_status": str(check.get("dispatch_status") or ""),
            "backend_result_status": str(check.get("backend_result_status") or ""),
            "backend_invocation_count": self._coerce_optional_non_negative_int(
                check.get("backend_invocation_count")
            ) or 0,
            "default_worker_enabled": check.get("default_worker_enabled"),
        })

    def _normalize_child_executor_sandbox_backend_coverage(
        self,
        coverage: Mapping[str, Any],
    ) -> Dict[str, Any]:
        contract_version = str(coverage.get("contract_version") or "")
        ready_adapter_contract = self._coerce_truthy_flag(coverage.get("ready_adapter_contract"))
        ready_sandbox_guard = self._coerce_truthy_flag(coverage.get("ready_sandbox_guard"))
        ready_audit = self._coerce_truthy_flag(coverage.get("ready_audit"))
        ready_idempotency = self._coerce_truthy_flag(coverage.get("ready_idempotency"))
        missing_guard_fail_closed = self._coerce_truthy_flag(coverage.get("missing_guard_fail_closed"))
        missing_guard_count = (
            self._coerce_optional_non_negative_int(coverage.get("missing_guard_count")) or 0
        )
        unsafe_payload_blocked = self._coerce_truthy_flag(coverage.get("unsafe_payload_blocked"))
        unsafe_blocked_reason = str(coverage.get("unsafe_blocked_reason") or "")
        compact_attempt_valid = self._coerce_truthy_flag(coverage.get("compact_attempt_valid"))
        dispatch_status = str(coverage.get("dispatch_status") or "")
        backend_result_status = str(coverage.get("backend_result_status") or "")
        backend_invocation_count = (
            self._coerce_optional_non_negative_int(coverage.get("backend_invocation_count")) or 0
        )
        default_worker_enabled = self._coerce_truthy_flag(coverage.get("default_worker_enabled"))
        sandbox_backend_smoke = (
            self._coerce_truthy_flag(coverage.get("sandbox_backend_smoke"))
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

    def _build_subagent_lane_query_detail_coverage(self, check: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "detail_smoke": bool(check.get("ok")) if check else False,
            "contract_version": str(check.get("contract_version") or ""),
            "recording_state": str(check.get("recording_state") or ""),
            "stage_count": self._coerce_optional_non_negative_int(check.get("stage_count")) or 0,
            "recent_event_count": self._coerce_optional_non_negative_int(check.get("recent_event_count")) or 0,
        }

    def _normalize_subagent_lane_query_detail_coverage(self, coverage: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "detail_smoke": self._coerce_truthy_flag(coverage.get("detail_smoke")),
            "contract_version": str(coverage.get("contract_version") or ""),
            "recording_state": str(coverage.get("recording_state") or ""),
            "stage_count": self._coerce_optional_non_negative_int(coverage.get("stage_count")) or 0,
            "recent_event_count": self._coerce_optional_non_negative_int(coverage.get("recent_event_count")) or 0,
        }

    def _coerce_optional_non_negative_int(self, value: Any) -> int | None:
        try:
            normalized = int(value)
        except (TypeError, ValueError):
            return None
        return normalized if normalized >= 0 else None

    def _normalize_string_list(self, value: Any) -> List[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if str(item or "").strip()]

    def _coerce_truthy_flag(self, value: Any) -> bool:
        if value is True:
            return True
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "ok", "yes"}
        return False


_runtime_contract_gate_service: RuntimeContractGateService | None = None


def get_runtime_contract_gate_service() -> RuntimeContractGateService:
    global _runtime_contract_gate_service
    if _runtime_contract_gate_service is None:
        _runtime_contract_gate_service = RuntimeContractGateService()
    return _runtime_contract_gate_service
