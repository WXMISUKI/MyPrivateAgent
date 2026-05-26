import json
import tempfile
import unittest
from pathlib import Path

from backend.services.runtime_contract_gate_service import RuntimeContractGateService


class RuntimeContractGateServiceTests(unittest.TestCase):
    def test_build_runtime_contract_summarizes_quality_gate_contract_checks(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-14T00:00:00Z",
                        "steps": [
                            {
                                "name": "Backend runtime_contract_smoke.py",
                                "contract_checks": [
                                    {
                                        "name": "runtime_profile_contract_snapshot",
                                        "ok": True,
                                        "status_code": 200,
                                        "contract_snapshot_status": "healthy",
                                        "adapter_health_status": "healthy",
                                    },
                                    {
                                        "name": "embedded_sdk_event_payloads",
                                        "ok": False,
                                        "missing_payload_count": 1,
                                        "checked_event_count": 6,
                                        "failure_reason": "sdk_event_payload_contract_incomplete",
                                    },
                                    {
                                        "name": "embedded_sdk_durable_recovery",
                                        "ok": False,
                                        "backend_kind": "sqlalchemy",
                                        "backend_mode": "strict_sql",
                                        "fallback_active": True,
                                        "probe_recoverable": False,
                                        "tool_recovery_reason": "workspace_backend_fallback_active",
                                        "loop_recovery_reason": "workspace_backend_fallback_active",
                                        "resumed_state": "",
                                        "approved_state": "",
                                        "failure_reason": "durable_recovery_chain_incomplete",
                                    },
                                    {
                                        "name": "runtime_surface_run_recovery",
                                        "ok": False,
                                        "contract_version": "phase-ii-run-recovery-v1",
                                        "run_recovery_available": True,
                                        "backend_kind": "sqlalchemy",
                                        "backend_mode": "strict_sql",
                                        "fallback_active": False,
                                        "probe_recoverable": False,
                                        "tool_recovery_reason": "missing_registered_binding",
                                        "loop_recovery_reason": "missing_registered_binding",
                                        "failure_reason": "run_recovery_contract_incomplete",
                                    },
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        self.assertEqual(contract["contract_version"], "phase-f-runtime-contract-gate-v1")
        self.assertTrue(contract["available"])
        self.assertEqual(contract["overall_status"], "degraded")
        self.assertEqual(contract["generated_at"], "2026-05-14T00:00:00Z")
        self.assertEqual(contract["check_count"], 4)
        self.assertEqual(contract["failed_check_count"], 3)
        self.assertEqual(contract["failure_reason"], "contract_checks_failed")
        self.assertEqual(contract["checks"][1]["name"], "embedded_sdk_event_payloads")
        self.assertEqual(contract["checks"][1]["missing_payload_count"], 1)
        self.assertEqual(contract["checks"][2]["name"], "embedded_sdk_durable_recovery")
        self.assertEqual(contract["checks"][2]["backend_mode"], "strict_sql")
        self.assertTrue(contract["checks"][2]["fallback_active"])
        self.assertEqual(contract["checks"][3]["name"], "runtime_surface_run_recovery")
        self.assertEqual(contract["checks"][3]["contract_version"], "phase-ii-run-recovery-v1")
        self.assertTrue(contract["checks"][3]["run_recovery_available"])

    def test_build_runtime_contract_exposes_report_runtime_contract_summary(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-21T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "runtime_contract_summary": {
                                    "overall_status": "healthy",
                                    "check_count": 5,
                                    "failed_check_count": 0,
                                    "missing_payload_count": 0,
                                    "approval_replay_coverage": {
                                        "event_payload_sample": True,
                                        "observed_status_kinds": [
                                            "approval_created",
                                            "approval_resolved",
                                            "approval_replayed",
                                            "approval_ignored",
                                        ],
                                    },
                                    "approval_lifecycle_recovery_coverage": {
                                        "alignment_smoke": True,
                                        "replayed_submission_status": "replayed",
                                        "ignored_submission_status": "ignored",
                                        "resolved_recovery_reason": "already_resolved",
                                    },
                                },
                                "runtime_contract_artifact_schema": {
                                    "contract_version": "phase-f-runtime-contract-artifact-schema-v1",
                                    "overall_status": "healthy",
                                    "summary_required_fields": [
                                        "overall_status",
                                        "approval_lifecycle_recovery_coverage.alignment_smoke",
                                        "child_executor_promotion_gate_coverage.gate_smoke",
                                        "subagent_lane_query_detail_coverage.detail_smoke",
                                    ],
                                    "summary_missing_fields": [],
                                },
                                "contract_checks": [
                                    {"name": "runtime_profile_contract_snapshot", "ok": True},
                                    {
                                        "name": "embedded_sdk_event_payloads",
                                        "ok": True,
                                        "missing_payload_count": 0,
                                        "observed_status_kinds": [
                                            "approval_created",
                                            "approval_resolved",
                                            "approval_replayed",
                                            "approval_ignored",
                                        ],
                                    },
                                    {"name": "embedded_sdk_durable_recovery", "ok": True},
                                    {"name": "runtime_surface_run_recovery", "ok": True},
                                    {
                                        "name": "runtime_approved_tool_execution_bridge",
                                        "ok": True,
                                        "approved_tool_call_count": 1,
                                        "approved_policy_original_status": "approval_required",
                                        "approved_policy_override_status": "approved",
                                        "deny_override_status": "policy_denied",
                                        "deny_tool_call_count": 0,
                                    },
                                    {
                                        "name": "sdk_tool_runtime_execution_bridge",
                                        "ok": True,
                                        "auto_tool_call_count": 1,
                                        "auto_tool_history_count": 1,
                                        "approved_tool_call_count": 1,
                                        "approved_policy_original_status": "approval_required",
                                        "approved_policy_override_status": "approved",
                                        "deny_override_status": "policy_denied",
                                        "deny_tool_call_count": 0,
                                    },
                                    {
                                        "name": "subagent_lane_query_detail",
                                        "ok": True,
                                        "contract_version": "phase-h-subagent-lane-query-detail-v1",
                                        "recording_state": "recorded",
                                        "stage_count": 2,
                                        "recent_event_count": 2,
                                    },
                                    {
                                        "name": "embedded_sdk_persistence_posture",
                                        "ok": True,
                                        "contract_version": "phase-ii-embedded-sdk-persistence-interface-v1",
                                        "memory_posture": "memory_preview",
                                        "durable_posture": "durable_ready",
                                        "degraded_posture": "durable_degraded",
                                        "memory_cross_process_block_reason": "workspace_backend_not_durable",
                                        "degraded_cross_process_block_reason": "workspace_backend_fallback_active",
                                        "durable_cross_process_candidate": True,
                                        "production_recovery_gate_contract_version": "phase-ii-durable-workspace-production-recovery-gate-v1",
                                        "production_recovery_gate_status": "blocked",
                                        "production_recovery_gate_missing_sections": [
                                            "worker_ownership_production_gate",
                                            "durable_backend_migration_rollout",
                                        ],
                                        "production_recovery_default_enabled": False,
                                        "production_recovery_worker_ownership_gate_contract_version": (
                                            "phase-ii-worker-ownership-production-gate-v1"
                                        ),
                                        "production_recovery_worker_ownership_gate_status": "blocked",
                                        "production_recovery_worker_ownership_default_enabled": False,
                                        "production_recovery_worker_ownership_missing_sections": [
                                            "vendor_lock_semantics",
                                            "heartbeat_renewal_supervisor",
                                        ],
                                        "recovery_audit_contract_version": "phase-ii-recovery-audit-production-gate-v1",
                                        "recovery_audit_ready": True,
                                        "recovery_audit_operation_history_supported": True,
                                        "recovery_audit_summary_supported": True,
                                        "recovery_audit_timeline_writer_available": True,
                                        "recovery_audit_idempotent_trace_dedupe": True,
                                        "recovery_audit_authorization_source": False,
                                        "registry_checkpoint_policy_contract_version": "phase-ii-production-recovery-registry-checkpoint-policy-v1",
                                        "registry_checkpoint_policy_ready": True,
                                        "registry_binding_policy_ready": True,
                                        "checkpoint_resume_cursor_policy_ready": True,
                                        "registry_checkpoint_policy_authorization_source": False,
                                    },
                                    {
                                        "name": "worker_ownership_store_mode",
                                        "ok": True,
                                        "default_mode": "memory_only",
                                        "default_mode_source": "default",
                                        "default_adapter_kind": "in_memory",
                                        "default_durable": False,
                                        "configurable_knob_present": True,
                                        "hot_reloadable_knob_present": True,
                                        "strict_mode_status": "sqlalchemy_durable",
                                        "fallback_mode_status": "fallback_to_memory",
                                        "production_gate_contract_version": "phase-ii-worker-ownership-production-gate-v1",
                                        "production_gate_status": "blocked",
                                        "production_gate_missing_sections": [
                                            "vendor_lock_semantics",
                                            "heartbeat_renewal_supervisor",
                                            "ownership_audit_evidence",
                                            "fail_closed_default_decision",
                                        ],
                                        "production_default_enabled": False,
                                        "vendor_lock_contract_version": (
                                            "phase-ii-worker-ownership-vendor-lock-semantics-v1"
                                        ),
                                        "vendor_lock_status": "blocked",
                                        "vendor_lock_missing_sections": [
                                            "vendor_lock_adapter",
                                            "target_decision",
                                        ],
                                        "vendor_lock_current_posture": "sql_row_lease_fencing",
                                        "vendor_lock_sql_row_lease_fencing": True,
                                        "vendor_lock_sql_row_lease_is_vendor_lock": False,
                                        "vendor_lock_adapter_present": False,
                                        "vendor_lock_adapter_contract_version": (
                                            "phase-ii-worker-ownership-vendor-lock-adapter-v1"
                                        ),
                                        "vendor_lock_adapter_status": "blocked",
                                        "vendor_lock_adapter_kind": "",
                                        "vendor_lock_adapter_target_backend": "",
                                        "vendor_lock_adapter_scope": "",
                                        "vendor_lock_adapter_fencing_strategy": "",
                                        "vendor_lock_adapter_ttl_renewal_strategy": "",
                                        "vendor_lock_adapter_failover_strategy": "",
                                        "vendor_lock_adapter_stale_cleanup_strategy": "",
                                        "vendor_lock_adapter_acquire_supported": False,
                                        "vendor_lock_adapter_renew_supported": False,
                                        "vendor_lock_adapter_release_supported": False,
                                        "vendor_lock_adapter_probe_supported": False,
                                        "vendor_lock_adapter_production_allowed": False,
                                        "vendor_lock_adapter_sql_row_lease_is_vendor_lock": False,
                                        "vendor_lock_adapter_missing_sections": [
                                            "adapter_kind",
                                            "target_backend",
                                        ],
                                        "postgres_probe_contract_version": (
                                            "phase-ii-worker-ownership-postgres-vendor-lock-probe-v1"
                                        ),
                                        "postgres_probe_status": "blocked",
                                        "postgres_probe_missing_sections": [
                                            "advisory_lock_family",
                                            "probe_safety",
                                        ],
                                        "postgres_probe_executes": False,
                                        "postgres_probe_sql_row_lease_is_vendor_lock": False,
                                        "postgres_probe_ready_status": "ready",
                                        "postgres_probe_ready_executes": False,
                                        "postgres_execution_seam_contract_version": (
                                            "phase-ii-worker-ownership-postgres-advisory-lock-execution-seam-v1"
                                        ),
                                        "postgres_execution_default_status": "blocked",
                                        "postgres_execution_default_executor_bound": False,
                                        "postgres_execution_default_enabled_by_default": False,
                                        "postgres_execution_default_production_allowed": False,
                                        "postgres_execution_default_missing_sections": [
                                            "executor_binding",
                                        ],
                                        "postgres_execution_default_probe_status": "blocked",
                                        "postgres_execution_default_probe_executed": False,
                                        "postgres_execution_opt_in_status": "ready",
                                        "postgres_execution_opt_in_executor_bound": True,
                                        "postgres_execution_opt_in_enabled_by_default": False,
                                        "postgres_execution_opt_in_production_allowed": False,
                                        "postgres_execution_opt_in_probe_status": "ready",
                                        "postgres_execution_opt_in_probe_executed": True,
                                        "postgres_execution_opt_in_acquire_status": "acquired",
                                        "postgres_execution_opt_in_acquire_executed": True,
                                        "postgres_execution_opt_in_acquired": True,
                                        "postgres_execution_opt_in_envelope_count": 2,
                                        "postgres_rollout_consumer_contract_version": (
                                            "phase-ii-worker-ownership-postgres-rollout-artifact-consumer-v1"
                                        ),
                                        "postgres_rollout_consumer_default_status": "blocked",
                                        "postgres_rollout_consumer_default_missing_sections": [
                                            "source_kind",
                                            "postgres_execution_seam",
                                        ],
                                        "postgres_rollout_consumer_default_will_enable_default": False,
                                        "postgres_rollout_consumer_default_executes_lock": False,
                                        "postgres_rollout_consumer_ready_status": "ready",
                                        "postgres_rollout_consumer_ready_target_backend": "postgres",
                                        "postgres_rollout_consumer_ready_lock_adapter_kind": (
                                            "postgres_advisory_lock"
                                        ),
                                        "postgres_rollout_consumer_ready_will_enable_default": False,
                                        "postgres_rollout_consumer_ready_executes_lock": False,
                                        "postgres_rollout_consumer_input_source_status": "ready",
                                        "postgres_rollout_consumer_input_source_ready": True,
                                        "postgres_rollout_consumer_input_source_kind": "rollout_artifact",
                                        "postgres_target_binding_contract_version": (
                                            "phase-ii-worker-ownership-postgres-vendor-lock-target-artifact-binding-v1"
                                        ),
                                        "postgres_target_binding_default_status": "blocked",
                                        "postgres_target_binding_default_missing_sections": [
                                            "source_kind",
                                            "postgres_rollout_consumer",
                                        ],
                                        "postgres_target_binding_default_will_enable_lock": False,
                                        "postgres_target_binding_default_executes_lock": False,
                                        "postgres_target_binding_ready_status": "ready",
                                        "postgres_target_binding_ready_target_backend": "postgres",
                                        "postgres_target_binding_ready_lock_adapter_kind": (
                                            "postgres_advisory_lock"
                                        ),
                                        "postgres_target_binding_ready_will_enable_lock": False,
                                        "postgres_target_binding_ready_executes_lock": False,
                                        "postgres_target_binding_target_input_status": "ready",
                                        "postgres_target_binding_target_decision_status": "ready",
                                        "postgres_target_binding_target_decision_production_allowed": True,
                                        "postgres_semantics_binding_contract_version": (
                                            "phase-ii-worker-ownership-postgres-vendor-lock-semantics-binding-v1"
                                        ),
                                        "postgres_semantics_binding_default_status": "blocked",
                                        "postgres_semantics_binding_default_missing_sections": [
                                            "target_artifact_binding",
                                            "postgres_execution_seam",
                                        ],
                                        "postgres_semantics_binding_default_will_enable_lock": False,
                                        "postgres_semantics_binding_default_will_update_gate": False,
                                        "postgres_semantics_binding_default_executes_lock": False,
                                        "postgres_semantics_binding_ready_status": "ready",
                                        "postgres_semantics_binding_ready_target_backend": "postgres",
                                        "postgres_semantics_binding_ready_lock_adapter_kind": (
                                            "postgres_advisory_lock"
                                        ),
                                        "postgres_semantics_binding_ready_probe_status": "ready",
                                        "postgres_semantics_binding_ready_adapter_status": "ready",
                                        "postgres_semantics_binding_ready_semantics_status": "ready",
                                        "postgres_semantics_binding_ready_will_enable_lock": False,
                                        "postgres_semantics_binding_ready_will_update_gate": False,
                                        "postgres_semantics_binding_ready_executes_lock": False,
                                        "postgres_wiring_decision_contract_version": (
                                            "phase-ii-worker-ownership-postgres-vendor-lock-production-gate"
                                            "-wiring-decision-v1"
                                        ),
                                        "postgres_wiring_decision_default_status": "blocked",
                                        "postgres_wiring_decision_default_missing_sections": [
                                            "semantics_binding",
                                            "decision_recorded",
                                        ],
                                        "postgres_wiring_decision_default_wiring_allowed": False,
                                        "postgres_wiring_decision_default_will_update_gate": False,
                                        "postgres_wiring_decision_default_will_enable_lock": False,
                                        "postgres_wiring_decision_default_executes_lock": False,
                                        "postgres_wiring_decision_ready_status": "ready",
                                        "postgres_wiring_decision_ready_semantics_binding_status": "ready",
                                        "postgres_wiring_decision_ready_candidate_status": "ready",
                                        "postgres_wiring_decision_ready_wiring_allowed": True,
                                        "postgres_wiring_decision_ready_target_backend": "postgres",
                                        "postgres_wiring_decision_ready_lock_adapter_kind": (
                                            "postgres_advisory_lock"
                                        ),
                                        "postgres_wiring_decision_ready_will_update_gate": False,
                                        "postgres_wiring_decision_ready_will_enable_lock": False,
                                        "postgres_wiring_decision_ready_executes_lock": False,
                                        "production_dry_run_contract_version": (
                                            "phase-ii-worker-ownership-production-gate-composition-dry-run-v1"
                                        ),
                                        "production_dry_run_default_status": "blocked",
                                        "production_dry_run_default_missing_sections": [
                                            "vendor_lock_wiring_decision",
                                            "heartbeat_renewal_supervisor",
                                            "rollout_confirmation",
                                            "recovery_entry_auto_claim_enablement",
                                            "ownership_audit_evidence",
                                            "production_default_enablement_input_source",
                                        ],
                                        "production_dry_run_default_all_required_ready": False,
                                        "production_dry_run_default_would_allow": False,
                                        "production_dry_run_default_will_enable": False,
                                        "production_dry_run_default_executes_lock": False,
                                        "production_dry_run_default_starts_worker": False,
                                        "production_dry_run_default_runs_auto_claim": False,
                                        "production_dry_run_ready_status": "ready",
                                        "production_dry_run_ready_missing_sections": [],
                                        "production_dry_run_ready_all_required_ready": True,
                                        "production_dry_run_ready_would_allow": True,
                                        "production_dry_run_ready_will_enable": False,
                                        "production_dry_run_ready_executes_lock": False,
                                        "production_dry_run_ready_starts_worker": False,
                                        "production_dry_run_ready_runs_auto_claim": False,
                                        "enablement_config_consumer_contract_version": (
                                            "phase-ii-worker-ownership-production-enablement-runtime-config"
                                            "-consumer-v1"
                                        ),
                                        "enablement_config_consumer_default_status": "blocked",
                                        "enablement_config_consumer_default_missing_sections": [
                                            "source_kind",
                                            "config_id",
                                            "enablement_input_source",
                                            "composition_dry_run",
                                        ],
                                        "enablement_config_consumer_default_will_enable": False,
                                        "enablement_config_consumer_default_executes_lock": False,
                                        "enablement_config_consumer_default_starts_worker": False,
                                        "enablement_config_consumer_default_runs_auto_claim": False,
                                        "enablement_config_consumer_ready_status": "ready",
                                        "enablement_config_consumer_ready_missing_sections": [],
                                        "enablement_config_consumer_ready_target_backend": "postgres",
                                        "enablement_config_consumer_ready_lock_adapter_kind": (
                                            "postgres_advisory_lock"
                                        ),
                                        "enablement_config_consumer_ready_input_source_status": "ready",
                                        "enablement_config_consumer_ready_dry_run_status": "ready",
                                        "enablement_config_consumer_ready_dry_run_would_allow": True,
                                        "enablement_config_consumer_ready_will_enable": False,
                                        "enablement_config_consumer_ready_executes_lock": False,
                                        "enablement_config_consumer_ready_starts_worker": False,
                                        "enablement_config_consumer_ready_runs_auto_claim": False,
                                        "enablement_config_factory_binding_default_status": "blocked",
                                        "enablement_config_factory_binding_ready_status": "ready",
                                        "enablement_config_factory_binding_ready_config_id": (
                                            "factory-binding-001"
                                        ),
                                        "enablement_config_factory_binding_will_enable": False,
                                        "enablement_config_factory_binding_executes_lock": False,
                                        "enablement_config_factory_binding_starts_worker": False,
                                        "enablement_config_factory_binding_runs_auto_claim": False,
                                        "vendor_lock_scope_defined": False,
                                        "vendor_lock_fencing_guarantee_defined": False,
                                        "vendor_lock_failover_semantics_defined": False,
                                        "vendor_lock_ttl_renewal_semantics_defined": False,
                                        "vendor_lock_stale_owner_cleanup_defined": False,
                                        "vendor_lock_production_allowed": False,
                                        "vendor_lock_target_decision_contract_version": (
                                            "phase-ii-worker-ownership-vendor-lock-target-decision-v1"
                                        ),
                                        "vendor_lock_target_decision_status": "blocked",
                                        "vendor_lock_target_decision_recorded": False,
                                        "vendor_lock_target_backend": "",
                                        "vendor_lock_target_adapter_kind": "",
                                        "vendor_lock_target_scope": "",
                                        "vendor_lock_target_fencing_strategy": "",
                                        "vendor_lock_target_ttl_renewal_strategy": "",
                                        "vendor_lock_target_failover_strategy": "",
                                        "vendor_lock_target_stale_cleanup_strategy": "",
                                        "vendor_lock_target_missing_sections": [
                                            "input_source",
                                            "decision_recorded",
                                            "target_backend",
                                        ],
                                        "vendor_lock_target_sql_row_lease_is_vendor_lock": False,
                                        "vendor_lock_target_production_allowed": False,
                                        "vendor_lock_target_input_contract_version": (
                                            "phase-ii-worker-ownership-vendor-lock-target-decision-input-v1"
                                        ),
                                        "vendor_lock_target_input_source_status": "blocked",
                                        "vendor_lock_target_input_source_kind": "",
                                        "vendor_lock_target_input_decision_id": "",
                                        "vendor_lock_target_input_approved_by": "",
                                        "vendor_lock_target_input_approved_at": "",
                                        "vendor_lock_target_input_backend": "",
                                        "vendor_lock_target_input_adapter_kind": "",
                                        "vendor_lock_target_input_rollout_artifact": "",
                                        "vendor_lock_target_input_config_key": "",
                                        "vendor_lock_target_input_manual_approval_reference": "",
                                        "vendor_lock_target_input_missing_sections": [
                                            "input_source_kind",
                                            "decision_id",
                                        ],
                                        "vendor_lock_target_input_sql_row_lease_is_vendor_lock": False,
                                        "renewal_supervisor_contract_version": (
                                            "phase-ii-worker-ownership-renewal-supervisor-v1"
                                        ),
                                        "renewal_supervisor_status": "blocked",
                                        "renewal_supervisor_missing_sections": [
                                            "background_supervisor",
                                        ],
                                        "renewal_supervisor_enabled_by_default": False,
                                        "renewal_supervisor_renew_once_supported": True,
                                        "renewal_supervisor_owner_identity_required": True,
                                        "renewal_supervisor_ttl_interval_policy_ready": True,
                                        "renewal_supervisor_controlled_lifecycle_supported": True,
                                        "renewal_supervisor_starts_by_default": False,
                                        "renewal_supervisor_active": False,
                                        "renewal_supervisor_last_renewal_status": "",
                                        "renewal_supervisor_stop_supported": True,
                                        "renewal_supervisor_failure_fail_closed": True,
                                        "renewal_supervisor_lease_loss_fail_closed": True,
                                        "renewal_supervisor_renew_once_status": "renewed",
                                        "renewal_supervisor_renew_once_background_started": False,
                                        "renewal_supervisor_stale_fencing_status": "blocked",
                                        "renewal_supervisor_stale_fencing_reason": "stale_worker_fencing_token",
                                        "renewal_supervisor_lifecycle_initial_active": False,
                                        "renewal_supervisor_lifecycle_started_active": True,
                                        "renewal_supervisor_lifecycle_started_status": "renewed",
                                        "renewal_supervisor_lifecycle_started_count": 1,
                                        "renewal_supervisor_lifecycle_stopped_active": False,
                                        "renewal_supervisor_lifecycle_stopped_count": 1,
                                        "rollout_readiness_contract_version": (
                                            "phase-ii-worker-ownership-rollout-readiness-v1"
                                        ),
                                        "rollout_readiness_status": "blocked",
                                        "rollout_missing_sections": [
                                            "strict_mode_rollout",
                                        ],
                                        "production_rollout_confirmed": False,
                                        "rollout_migration_ready": True,
                                        "rollout_stale_fencing_verified": True,
                                        "rollout_rollback_plan_ready": False,
                                        "rollout_operationalization_status": "blocked",
                                        "rollout_mode": "readiness_only",
                                        "rollout_missing_artifacts": [
                                            "rollback_plan",
                                            "rollout_confirmation_decision",
                                        ],
                                        "rollout_rollback_plan_status": "missing",
                                        "rollout_fallback_policy_status": "missing",
                                        "rollout_renewal_lifecycle_verification_status": "missing",
                                        "rollout_auto_claim_decision_status": "missing",
                                        "rollout_confirmation_decision_contract_version": (
                                            "phase-ii-worker-ownership-rollout-confirmation-decision-v1"
                                        ),
                                        "rollout_confirmation_decision_status": "blocked",
                                        "rollout_decision_recorded": False,
                                        "rollout_decision_id": "",
                                        "rollout_approved_by": "",
                                        "rollout_approved_at": "",
                                        "rollout_target_store_mode": "",
                                        "rollout_confirmation_missing_sections": [
                                            "decision_recorded",
                                        ],
                                        "rollout_confirmation_production_rollout_confirmed": False,
                                        "rollout_confirmation_input_contract_version": (
                                            "phase-ii-worker-ownership-rollout-confirmation-input-source-v1"
                                        ),
                                        "rollout_confirmation_input_source_status": "blocked",
                                        "rollout_confirmation_input_source_kind": "",
                                        "rollout_confirmation_input_decision_id": "",
                                        "rollout_confirmation_input_approved_by": "",
                                        "rollout_confirmation_input_approved_at": "",
                                        "rollout_confirmation_input_target_store_mode": "",
                                        "rollout_confirmation_input_rollback_plan_reference": "",
                                        "rollout_confirmation_input_fallback_policy_reference": "",
                                        "rollout_confirmation_input_renewal_lifecycle_reference": "",
                                        "rollout_confirmation_input_auto_claim_decision_reference": "",
                                        "rollout_confirmation_input_missing_sections": [
                                            "input_source_kind",
                                            "decision_id",
                                        ],
                                        "rollout_confirmation_input_sql_row_lease_is_authority": False,
                                        "auto_claim_policy_contract_version": (
                                            "phase-ii-worker-ownership-auto-claim-policy-v1"
                                        ),
                                        "auto_claim_policy_status": "blocked",
                                        "auto_claim_missing_sections": [
                                            "explicit_runtime_configuration",
                                        ],
                                        "auto_claim_enabled_by_default": False,
                                        "auto_claim_descriptor_evidence_fallback": True,
                                        "auto_claim_lease_validation_required": True,
                                        "auto_claim_entrypoint_allowlist_ready": True,
                                        "auto_claim_entrypoint_allowlist_contract_version": (
                                            "phase-ii-worker-ownership-auto-claim-entrypoint-allowlist-v1"
                                        ),
                                        "auto_claim_entrypoint_allowlist_status": "ready",
                                        "auto_claim_allowed_entrypoints": [
                                            "submit_approval.approved",
                                            "resume_run.continue_loop",
                                        ],
                                        "auto_claim_missing_entrypoints": [],
                                        "auto_claim_default_auto_claim_enabled": False,
                                        "auto_claim_requires_production_gate_ready": True,
                                        "auto_claim_enablement_gate_contract_version": (
                                            "phase-ii-worker-ownership-explicit-auto-claim-enablement-gate-v1"
                                        ),
                                        "auto_claim_enablement_gate_status": "blocked",
                                        "auto_claim_will_auto_claim": False,
                                        "auto_claim_requested_entrypoint": "submit_approval.approved",
                                        "auto_claim_enablement_missing_sections": [
                                            "explicit_runtime_configuration",
                                        ],
                                        "auto_claim_enablement_blocked_reason": (
                                            "explicit_runtime_configuration_missing"
                                        ),
                                        "ownership_audit_contract_version": (
                                            "phase-ii-worker-ownership-audit-evidence-v1"
                                        ),
                                        "ownership_audit_status": "blocked",
                                        "ownership_audit_missing_sections": [
                                            "operation_history",
                                        ],
                                        "ownership_audit_compact_evidence": True,
                                        "ownership_audit_operation_history_ready": False,
                                        "ownership_audit_recovery_operation_link_ready": False,
                                        "ownership_audit_timeline_writer_ready": False,
                                        "ownership_audit_idempotent_dedupe_ready": False,
                                        "ownership_audit_authorization_source": False,
                                        "enablement_strategy_contract_version": (
                                            "phase-ii-worker-ownership-production-enablement-strategy-v1"
                                        ),
                                        "enablement_strategy_status": "blocked",
                                        "enablement_strategy_blocking_sections": [
                                            "vendor_lock_semantics",
                                            "production_default_enablement_input_source",
                                        ],
                                        "production_default_enabled_requested": False,
                                        "production_default_allowed": False,
                                        "enablement_input_source_contract_version": (
                                            "phase-ii-worker-ownership-production-default-enablement-input-source-v1"
                                        ),
                                        "enablement_input_source_status": "blocked",
                                        "enablement_input_source_kind": "",
                                        "enablement_request_id": "",
                                        "enablement_requested_by": "",
                                        "enablement_requested_at": "",
                                        "enablement_target_store_mode": "",
                                        "enablement_rollout_artifact": "",
                                        "enablement_vendor_lock_decision_id": "",
                                        "enablement_renewal_lifecycle_reference": "",
                                        "enablement_auto_claim_decision_reference": "",
                                        "enablement_audit_evidence_reference": "",
                                        "enablement_rollback_plan_reference": "",
                                        "enablement_fallback_policy_reference": "",
                                        "enablement_input_source_ready": False,
                                        "enablement_input_source_missing_sections": [
                                            "input_source_kind",
                                        ],
                                        "enablement_explicit_required": True,
                                        "enablement_all_required_sections_ready": False,
                                        "enablement_fail_closed_when_blocked": True,
                                        "enablement_sql_row_lease_not_default_authority": True,
                                    },
                                    {
                                        "name": "child_executor_promotion_gate",
                                        "ok": True,
                                        "contract_version": "phase-ii-child-executor-gate-v1",
                                        "gate_status": "blocked",
                                        "allowed": False,
                                        "gate_failure_reason": "child_executor_preflight_blocked",
                                        "blocker_count": 2,
                                        "recommended_next_step": "keep_relationship_only",
                                    },
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        self.assertEqual(contract["overall_status"], "healthy")
        self.assertEqual(contract["runtime_contract_summary"]["overall_status"], "healthy")
        self.assertEqual(contract["runtime_contract_summary"]["check_count"], 5)
        self.assertEqual(contract["runtime_contract_summary"]["missing_payload_count"], 0)
        self.assertTrue(
            contract["runtime_contract_summary"]["approval_replay_coverage"]["event_payload_sample"]
        )
        lifecycle_coverage = contract["runtime_contract_summary"]["approval_lifecycle_recovery_coverage"]
        self.assertTrue(lifecycle_coverage["alignment_smoke"])
        self.assertEqual(lifecycle_coverage["replayed_submission_status"], "replayed")
        self.assertEqual(lifecycle_coverage["ignored_submission_status"], "ignored")
        self.assertEqual(lifecycle_coverage["resolved_recovery_reason"], "already_resolved")
        approved_coverage = contract["runtime_contract_summary"]["approved_tool_execution_coverage"]
        self.assertTrue(approved_coverage["bridge_smoke"])
        self.assertEqual(approved_coverage["approved_tool_call_count"], 1)
        self.assertEqual(approved_coverage["approved_policy_original_status"], "approval_required")
        self.assertEqual(approved_coverage["approved_policy_override_status"], "approved")
        self.assertEqual(approved_coverage["deny_override_status"], "policy_denied")
        self.assertEqual(approved_coverage["deny_tool_call_count"], 0)
        sdk_coverage = contract["runtime_contract_summary"]["sdk_tool_runtime_execution_coverage"]
        self.assertTrue(sdk_coverage["bridge_smoke"])
        self.assertEqual(sdk_coverage["auto_tool_call_count"], 1)
        self.assertEqual(sdk_coverage["auto_tool_history_count"], 1)
        self.assertEqual(sdk_coverage["approved_tool_call_count"], 1)
        self.assertEqual(sdk_coverage["approved_policy_original_status"], "approval_required")
        self.assertEqual(sdk_coverage["approved_policy_override_status"], "approved")
        self.assertEqual(sdk_coverage["deny_override_status"], "policy_denied")
        self.assertEqual(sdk_coverage["deny_tool_call_count"], 0)
        persistence_coverage = contract["runtime_contract_summary"]["embedded_sdk_persistence_coverage"]
        self.assertTrue(persistence_coverage["persistence_smoke"])
        self.assertEqual(
            persistence_coverage["contract_version"],
            "phase-ii-embedded-sdk-persistence-interface-v1",
        )
        self.assertEqual(persistence_coverage["memory_posture"], "memory_preview")
        self.assertEqual(persistence_coverage["durable_posture"], "durable_ready")
        self.assertEqual(persistence_coverage["degraded_posture"], "durable_degraded")
        self.assertEqual(
            persistence_coverage["production_recovery_gate_contract_version"],
            "phase-ii-durable-workspace-production-recovery-gate-v1",
        )
        self.assertEqual(persistence_coverage["production_recovery_gate_status"], "blocked")
        self.assertNotIn(
            "descriptor_lifecycle_governance",
            persistence_coverage["production_recovery_gate_missing_sections"],
        )
        self.assertNotIn(
            "loader_execution_handoff_policy",
            persistence_coverage["production_recovery_gate_missing_sections"],
        )
        self.assertNotIn(
            "recovery_audit_operation_history",
            persistence_coverage["production_recovery_gate_missing_sections"],
        )
        self.assertNotIn(
            "registry_binding_resolution",
            persistence_coverage["production_recovery_gate_missing_sections"],
        )
        self.assertNotIn(
            "checkpoint_resume_cursor_gate",
            persistence_coverage["production_recovery_gate_missing_sections"],
        )
        self.assertFalse(persistence_coverage["production_recovery_default_enabled"])
        recovery_audit_coverage = contract["runtime_contract_summary"]["recovery_audit_operation_history_coverage"]
        self.assertTrue(recovery_audit_coverage["audit_smoke"])
        self.assertEqual(
            recovery_audit_coverage["contract_version"],
            "phase-ii-recovery-audit-production-gate-v1",
        )
        self.assertTrue(recovery_audit_coverage["ready"])
        self.assertTrue(recovery_audit_coverage["operation_history_supported"])
        self.assertTrue(recovery_audit_coverage["audit_summary_supported"])
        self.assertTrue(recovery_audit_coverage["timeline_writer_available"])
        self.assertTrue(recovery_audit_coverage["idempotent_trace_dedupe"])
        self.assertFalse(recovery_audit_coverage["authorization_source"])
        registry_checkpoint_coverage = contract["runtime_contract_summary"][
            "production_recovery_registry_checkpoint_policy_coverage"
        ]
        self.assertTrue(registry_checkpoint_coverage["policy_smoke"])
        self.assertEqual(
            registry_checkpoint_coverage["contract_version"],
            "phase-ii-production-recovery-registry-checkpoint-policy-v1",
        )
        self.assertTrue(registry_checkpoint_coverage["ready"])
        self.assertTrue(registry_checkpoint_coverage["registry_binding_policy_ready"])
        self.assertTrue(registry_checkpoint_coverage["checkpoint_resume_cursor_policy_ready"])
        self.assertFalse(registry_checkpoint_coverage["authorization_source"])
        ownership_coverage = contract["runtime_contract_summary"]["worker_ownership_store_mode_coverage"]
        self.assertTrue(ownership_coverage["mode_smoke"])
        self.assertEqual(ownership_coverage["default_mode"], "memory_only")
        self.assertEqual(ownership_coverage["default_adapter_kind"], "in_memory")
        self.assertFalse(ownership_coverage["default_durable"])
        self.assertEqual(ownership_coverage["strict_mode_status"], "sqlalchemy_durable")
        self.assertEqual(ownership_coverage["fallback_mode_status"], "fallback_to_memory")
        self.assertEqual(
            ownership_coverage["production_gate_contract_version"],
            "phase-ii-worker-ownership-production-gate-v1",
        )
        self.assertEqual(ownership_coverage["production_gate_status"], "blocked")
        self.assertIn("vendor_lock_semantics", ownership_coverage["production_gate_missing_sections"])
        self.assertIn("ownership_audit_evidence", ownership_coverage["production_gate_missing_sections"])
        self.assertIn("fail_closed_default_decision", ownership_coverage["production_gate_missing_sections"])
        self.assertFalse(ownership_coverage["production_default_enabled"])
        self.assertEqual(
            ownership_coverage["vendor_lock_contract_version"],
            "phase-ii-worker-ownership-vendor-lock-semantics-v1",
        )
        self.assertEqual(ownership_coverage["vendor_lock_status"], "blocked")
        self.assertEqual(ownership_coverage["vendor_lock_current_posture"], "sql_row_lease_fencing")
        self.assertTrue(ownership_coverage["vendor_lock_sql_row_lease_fencing"])
        self.assertFalse(ownership_coverage["vendor_lock_sql_row_lease_is_vendor_lock"])
        self.assertFalse(ownership_coverage["vendor_lock_adapter_present"])
        self.assertEqual(
            ownership_coverage["vendor_lock_adapter_contract_version"],
            "phase-ii-worker-ownership-vendor-lock-adapter-v1",
        )
        self.assertEqual(ownership_coverage["vendor_lock_adapter_status"], "blocked")
        self.assertEqual(ownership_coverage["vendor_lock_adapter_kind"], "")
        self.assertEqual(ownership_coverage["vendor_lock_adapter_target_backend"], "")
        self.assertFalse(ownership_coverage["vendor_lock_adapter_acquire_supported"])
        self.assertFalse(ownership_coverage["vendor_lock_adapter_renew_supported"])
        self.assertFalse(ownership_coverage["vendor_lock_adapter_release_supported"])
        self.assertFalse(ownership_coverage["vendor_lock_adapter_probe_supported"])
        self.assertFalse(ownership_coverage["vendor_lock_adapter_production_allowed"])
        self.assertFalse(
            ownership_coverage["vendor_lock_adapter_sql_row_lease_is_vendor_lock"]
        )
        self.assertIn(
            "adapter_kind",
            ownership_coverage["vendor_lock_adapter_missing_sections"],
        )
        self.assertEqual(
            ownership_coverage["postgres_probe_contract_version"],
            "phase-ii-worker-ownership-postgres-vendor-lock-probe-v1",
        )
        self.assertEqual(ownership_coverage["postgres_probe_status"], "blocked")
        self.assertFalse(ownership_coverage["postgres_probe_executes"])
        self.assertFalse(ownership_coverage["postgres_probe_sql_row_lease_is_vendor_lock"])
        self.assertIn(
            "advisory_lock_family",
            ownership_coverage["postgres_probe_missing_sections"],
        )
        self.assertEqual(ownership_coverage["postgres_probe_ready_status"], "ready")
        self.assertFalse(ownership_coverage["postgres_probe_ready_executes"])
        self.assertFalse(ownership_coverage["vendor_lock_production_allowed"])
        self.assertIn("vendor_lock_adapter", ownership_coverage["vendor_lock_missing_sections"])
        self.assertIn("target_decision", ownership_coverage["vendor_lock_missing_sections"])
        self.assertEqual(
            ownership_coverage["vendor_lock_target_decision_contract_version"],
            "phase-ii-worker-ownership-vendor-lock-target-decision-v1",
        )
        self.assertEqual(ownership_coverage["vendor_lock_target_decision_status"], "blocked")
        self.assertFalse(ownership_coverage["vendor_lock_target_decision_recorded"])
        self.assertEqual(ownership_coverage["vendor_lock_target_backend"], "")
        self.assertIn(
            "input_source",
            ownership_coverage["vendor_lock_target_missing_sections"],
        )
        self.assertIn(
            "decision_recorded",
            ownership_coverage["vendor_lock_target_missing_sections"],
        )
        self.assertEqual(
            ownership_coverage["vendor_lock_target_input_contract_version"],
            "phase-ii-worker-ownership-vendor-lock-target-decision-input-v1",
        )
        self.assertEqual(
            ownership_coverage["vendor_lock_target_input_source_status"],
            "blocked",
        )
        self.assertIn(
            "input_source_kind",
            ownership_coverage["vendor_lock_target_input_missing_sections"],
        )
        self.assertFalse(
            ownership_coverage["vendor_lock_target_sql_row_lease_is_vendor_lock"]
        )
        self.assertFalse(
            ownership_coverage["vendor_lock_target_input_sql_row_lease_is_vendor_lock"]
        )
        self.assertFalse(ownership_coverage["vendor_lock_target_production_allowed"])
        self.assertTrue(ownership_coverage["renewal_supervisor_renew_once_supported"])
        self.assertTrue(ownership_coverage["renewal_supervisor_owner_identity_required"])
        self.assertTrue(ownership_coverage["renewal_supervisor_ttl_interval_policy_ready"])
        self.assertTrue(ownership_coverage["renewal_supervisor_controlled_lifecycle_supported"])
        self.assertFalse(ownership_coverage["renewal_supervisor_starts_by_default"])
        self.assertFalse(ownership_coverage["renewal_supervisor_active"])
        self.assertEqual(ownership_coverage["renewal_supervisor_last_renewal_status"], "")
        self.assertTrue(ownership_coverage["renewal_supervisor_stop_supported"])
        self.assertTrue(ownership_coverage["renewal_supervisor_failure_fail_closed"])
        self.assertEqual(ownership_coverage["renewal_supervisor_renew_once_status"], "renewed")
        self.assertFalse(ownership_coverage["renewal_supervisor_renew_once_background_started"])
        self.assertEqual(ownership_coverage["renewal_supervisor_stale_fencing_status"], "blocked")
        self.assertEqual(
            ownership_coverage["renewal_supervisor_stale_fencing_reason"],
            "stale_worker_fencing_token",
        )
        self.assertFalse(ownership_coverage["renewal_supervisor_lifecycle_initial_active"])
        self.assertTrue(ownership_coverage["renewal_supervisor_lifecycle_started_active"])
        self.assertEqual(
            ownership_coverage["renewal_supervisor_lifecycle_started_status"],
            "renewed",
        )
        self.assertGreaterEqual(
            ownership_coverage["renewal_supervisor_lifecycle_started_count"],
            1,
        )
        self.assertFalse(ownership_coverage["renewal_supervisor_lifecycle_stopped_active"])
        self.assertGreaterEqual(
            ownership_coverage["renewal_supervisor_lifecycle_stopped_count"],
            1,
        )
        self.assertEqual(ownership_coverage["rollout_operationalization_status"], "blocked")
        self.assertEqual(ownership_coverage["rollout_mode"], "readiness_only")
        self.assertIn("rollback_plan", ownership_coverage["rollout_missing_artifacts"])
        self.assertIn(
            "rollout_confirmation_decision",
            ownership_coverage["rollout_missing_artifacts"],
        )
        self.assertEqual(ownership_coverage["rollout_rollback_plan_status"], "missing")
        self.assertEqual(ownership_coverage["rollout_fallback_policy_status"], "missing")
        self.assertEqual(
            ownership_coverage["rollout_renewal_lifecycle_verification_status"],
            "missing",
        )
        self.assertEqual(ownership_coverage["rollout_auto_claim_decision_status"], "missing")
        self.assertEqual(
            ownership_coverage["rollout_confirmation_decision_contract_version"],
            "phase-ii-worker-ownership-rollout-confirmation-decision-v1",
        )
        self.assertEqual(
            ownership_coverage["rollout_confirmation_decision_status"],
            "blocked",
        )
        self.assertFalse(ownership_coverage["rollout_decision_recorded"])
        self.assertEqual(ownership_coverage["rollout_target_store_mode"], "")
        self.assertIn(
            "decision_recorded",
            ownership_coverage["rollout_confirmation_missing_sections"],
        )
        self.assertFalse(
            ownership_coverage["rollout_confirmation_production_rollout_confirmed"]
        )
        self.assertEqual(
            ownership_coverage["ownership_audit_contract_version"],
            "phase-ii-worker-ownership-audit-evidence-v1",
        )
        self.assertEqual(ownership_coverage["ownership_audit_status"], "blocked")
        self.assertTrue(ownership_coverage["ownership_audit_compact_evidence"])
        self.assertFalse(ownership_coverage["ownership_audit_authorization_source"])
        self.assertIn("operation_history", ownership_coverage["ownership_audit_missing_sections"])
        self.assertEqual(
            ownership_coverage["enablement_strategy_contract_version"],
            "phase-ii-worker-ownership-production-enablement-strategy-v1",
        )
        self.assertEqual(ownership_coverage["enablement_strategy_status"], "blocked")
        self.assertIn(
            "vendor_lock_semantics",
            ownership_coverage["enablement_strategy_blocking_sections"],
        )
        self.assertIn(
            "production_default_enablement_input_source",
            ownership_coverage["enablement_strategy_blocking_sections"],
        )
        self.assertFalse(ownership_coverage["production_default_enabled_requested"])
        self.assertFalse(ownership_coverage["production_default_allowed"])
        self.assertEqual(
            ownership_coverage["enablement_input_source_contract_version"],
            "phase-ii-worker-ownership-production-default-enablement-input-source-v1",
        )
        self.assertEqual(ownership_coverage["enablement_input_source_status"], "blocked")
        self.assertEqual(ownership_coverage["enablement_input_source_kind"], "")
        self.assertEqual(ownership_coverage["enablement_rollout_artifact"], "")
        self.assertFalse(ownership_coverage["enablement_input_source_ready"])
        self.assertIn(
            "input_source_kind",
            ownership_coverage["enablement_input_source_missing_sections"],
        )
        self.assertTrue(ownership_coverage["enablement_explicit_required"])
        self.assertFalse(ownership_coverage["enablement_all_required_sections_ready"])
        self.assertTrue(ownership_coverage["enablement_fail_closed_when_blocked"])
        self.assertTrue(ownership_coverage["enablement_sql_row_lease_not_default_authority"])
        child_gate_coverage = contract["runtime_contract_summary"]["child_executor_promotion_gate_coverage"]
        self.assertTrue(child_gate_coverage["gate_smoke"])
        self.assertEqual(child_gate_coverage["contract_version"], "phase-ii-child-executor-gate-v1")
        self.assertEqual(child_gate_coverage["gate_status"], "blocked")
        self.assertFalse(child_gate_coverage["allowed"])
        self.assertEqual(child_gate_coverage["failure_reason"], "child_executor_preflight_blocked")
        self.assertEqual(child_gate_coverage["blocker_count"], 2)
        self.assertEqual(child_gate_coverage["recommended_next_step"], "keep_relationship_only")
        subagent_coverage = contract["runtime_contract_summary"]["subagent_lane_query_detail_coverage"]
        self.assertTrue(subagent_coverage["detail_smoke"])
        self.assertEqual(subagent_coverage["contract_version"], "phase-h-subagent-lane-query-detail-v1")
        self.assertEqual(subagent_coverage["recording_state"], "recorded")
        self.assertEqual(subagent_coverage["stage_count"], 2)
        self.assertEqual(subagent_coverage["recent_event_count"], 2)
        artifact_schema = contract["runtime_contract_artifact_schema"]
        self.assertEqual(artifact_schema["contract_version"], "phase-f-runtime-contract-artifact-schema-v1")
        self.assertEqual(artifact_schema["overall_status"], "healthy")
        self.assertEqual(artifact_schema["summary_missing_fields"], [])
        self.assertIn(
            "subagent_lane_query_detail_coverage.detail_smoke",
            artifact_schema["summary_required_fields"],
        )
        self.assertIn(
            "approval_lifecycle_recovery_coverage.alignment_smoke",
            artifact_schema["summary_required_fields"],
        )
        self.assertIn(
            "sdk_tool_runtime_execution_coverage.bridge_smoke",
            artifact_schema["summary_required_fields"],
        )
        self.assertIn(
            "embedded_sdk_persistence_coverage.persistence_smoke",
            artifact_schema["summary_required_fields"],
        )
        self.assertIn(
            "worker_ownership_store_mode_coverage.mode_smoke",
            artifact_schema["summary_required_fields"],
        )
        self.assertIn(
            "child_executor_promotion_gate_coverage.gate_smoke",
            artifact_schema["summary_required_fields"],
        )
        self.assertIn("approval_replayed", contract["checks"][1]["observed_status_kinds"])

    def test_build_runtime_contract_derives_approval_lifecycle_recovery_coverage_from_checks(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-22T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "contract_checks": [
                                    {"name": "runtime_profile_contract_snapshot", "ok": True},
                                    {
                                        "name": "approval_lifecycle_recovery_alignment",
                                        "ok": True,
                                        "replayed_submission_status": "replayed",
                                        "ignored_submission_status": "ignored",
                                        "resolved_recovery_reason": "already_resolved",
                                    },
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        coverage = contract["runtime_contract_summary"]["approval_lifecycle_recovery_coverage"]
        self.assertTrue(coverage["alignment_smoke"])
        self.assertEqual(coverage["replayed_submission_status"], "replayed")
        self.assertEqual(coverage["ignored_submission_status"], "ignored")
        self.assertEqual(coverage["resolved_recovery_reason"], "already_resolved")

    def test_build_runtime_contract_fails_closed_when_approval_lifecycle_summary_evidence_disagrees(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-22T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "runtime_contract_summary": {
                                    "overall_status": "healthy",
                                    "check_count": 1,
                                    "failed_check_count": 0,
                                    "missing_payload_count": 0,
                                    "approval_lifecycle_recovery_coverage": {
                                        "alignment_smoke": True,
                                        "replayed_submission_status": "replayed",
                                        "ignored_submission_status": "accepted",
                                        "resolved_recovery_reason": "missing_registered_binding",
                                    },
                                },
                                "contract_checks": [
                                    {"name": "runtime_profile_contract_snapshot", "ok": True},
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        coverage = contract["runtime_contract_summary"]["approval_lifecycle_recovery_coverage"]
        self.assertFalse(coverage["alignment_smoke"])
        self.assertEqual(coverage["replayed_submission_status"], "replayed")
        self.assertEqual(coverage["ignored_submission_status"], "accepted")
        self.assertEqual(coverage["resolved_recovery_reason"], "missing_registered_binding")

    def test_build_runtime_contract_returns_unknown_when_report_is_missing(self):
        contract = RuntimeContractGateService(report_path="missing-quality-gate-report.json").build_runtime_contract()

        self.assertFalse(contract["available"])
        self.assertEqual(contract["overall_status"], "unknown")
        self.assertEqual(contract["failure_reason"], "quality_gate_report_missing")
        self.assertEqual(contract["check_count"], 0)
        self.assertEqual(contract["runtime_contract_summary"]["overall_status"], "unknown")
        self.assertEqual(contract["runtime_contract_summary"]["check_count"], 0)
        self.assertFalse(
            contract["runtime_contract_summary"]["approval_replay_coverage"]["event_payload_sample"]
        )
        self.assertFalse(
            contract["runtime_contract_summary"]["approved_tool_execution_coverage"]["bridge_smoke"]
        )
        self.assertFalse(
            contract["runtime_contract_summary"]["subagent_lane_query_detail_coverage"]["detail_smoke"]
        )
        self.assertFalse(
            contract["runtime_contract_summary"]["worker_ownership_store_mode_coverage"]["mode_smoke"]
        )
        self.assertFalse(
            contract["runtime_contract_summary"]["child_executor_promotion_gate_coverage"]["gate_smoke"]
        )
        self.assertEqual(contract["runtime_contract_artifact_schema"]["overall_status"], "unknown")

    def test_build_runtime_contract_derives_worker_ownership_store_mode_coverage_from_checks(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-24T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "contract_checks": [
                                    {
                                        "name": "worker_ownership_store_mode",
                                        "ok": True,
                                        "default_mode": "memory_only",
                                        "default_mode_source": "default",
                                        "default_adapter_kind": "in_memory",
                                        "default_durable": False,
                                        "configurable_knob_present": True,
                                        "hot_reloadable_knob_present": True,
                                        "strict_mode_status": "sqlalchemy_durable",
                                        "fallback_mode_status": "fallback_to_memory",
                                        "production_gate_contract_version": "phase-ii-worker-ownership-production-gate-v1",
                                        "production_gate_status": "blocked",
                                        "production_gate_missing_sections": [
                                            "vendor_lock_semantics",
                                            "heartbeat_renewal_supervisor",
                                            "ownership_audit_evidence",
                                            "fail_closed_default_decision",
                                        ],
                                        "production_default_enabled": False,
                                        "vendor_lock_contract_version": (
                                            "phase-ii-worker-ownership-vendor-lock-semantics-v1"
                                        ),
                                        "vendor_lock_status": "blocked",
                                        "vendor_lock_missing_sections": [
                                            "vendor_lock_adapter",
                                            "target_decision",
                                        ],
                                        "vendor_lock_current_posture": "sql_row_lease_fencing",
                                        "vendor_lock_sql_row_lease_fencing": True,
                                        "vendor_lock_sql_row_lease_is_vendor_lock": False,
                                        "vendor_lock_adapter_present": False,
                                        "vendor_lock_adapter_contract_version": (
                                            "phase-ii-worker-ownership-vendor-lock-adapter-v1"
                                        ),
                                        "vendor_lock_adapter_status": "blocked",
                                        "vendor_lock_adapter_kind": "",
                                        "vendor_lock_adapter_target_backend": "",
                                        "vendor_lock_adapter_scope": "",
                                        "vendor_lock_adapter_fencing_strategy": "",
                                        "vendor_lock_adapter_ttl_renewal_strategy": "",
                                        "vendor_lock_adapter_failover_strategy": "",
                                        "vendor_lock_adapter_stale_cleanup_strategy": "",
                                        "vendor_lock_adapter_acquire_supported": False,
                                        "vendor_lock_adapter_renew_supported": False,
                                        "vendor_lock_adapter_release_supported": False,
                                        "vendor_lock_adapter_probe_supported": False,
                                        "vendor_lock_adapter_production_allowed": False,
                                        "vendor_lock_adapter_sql_row_lease_is_vendor_lock": False,
                                        "vendor_lock_adapter_missing_sections": [
                                            "adapter_kind",
                                            "target_backend",
                                        ],
                                        "postgres_probe_contract_version": (
                                            "phase-ii-worker-ownership-postgres-vendor-lock-probe-v1"
                                        ),
                                        "postgres_probe_status": "blocked",
                                        "postgres_probe_missing_sections": [
                                            "advisory_lock_family",
                                            "probe_safety",
                                        ],
                                        "postgres_probe_executes": False,
                                        "postgres_probe_sql_row_lease_is_vendor_lock": False,
                                        "postgres_probe_ready_status": "ready",
                                        "postgres_probe_ready_executes": False,
                                        "postgres_execution_seam_contract_version": (
                                            "phase-ii-worker-ownership-postgres-advisory-lock-execution-seam-v1"
                                        ),
                                        "postgres_execution_default_status": "blocked",
                                        "postgres_execution_default_executor_bound": False,
                                        "postgres_execution_default_enabled_by_default": False,
                                        "postgres_execution_default_production_allowed": False,
                                        "postgres_execution_default_missing_sections": [
                                            "executor_binding",
                                        ],
                                        "postgres_execution_default_probe_status": "blocked",
                                        "postgres_execution_default_probe_executed": False,
                                        "postgres_execution_opt_in_status": "ready",
                                        "postgres_execution_opt_in_executor_bound": True,
                                        "postgres_execution_opt_in_enabled_by_default": False,
                                        "postgres_execution_opt_in_production_allowed": False,
                                        "postgres_execution_opt_in_probe_status": "ready",
                                        "postgres_execution_opt_in_probe_executed": True,
                                        "postgres_execution_opt_in_acquire_status": "acquired",
                                        "postgres_execution_opt_in_acquire_executed": True,
                                        "postgres_execution_opt_in_acquired": True,
                                        "postgres_execution_opt_in_envelope_count": 2,
                                        "postgres_rollout_consumer_contract_version": (
                                            "phase-ii-worker-ownership-postgres-rollout-artifact-consumer-v1"
                                        ),
                                        "postgres_rollout_consumer_default_status": "blocked",
                                        "postgres_rollout_consumer_default_missing_sections": [
                                            "source_kind",
                                            "postgres_execution_seam",
                                        ],
                                        "postgres_rollout_consumer_default_will_enable_default": False,
                                        "postgres_rollout_consumer_default_executes_lock": False,
                                        "postgres_rollout_consumer_ready_status": "ready",
                                        "postgres_rollout_consumer_ready_target_backend": "postgres",
                                        "postgres_rollout_consumer_ready_lock_adapter_kind": (
                                            "postgres_advisory_lock"
                                        ),
                                        "postgres_rollout_consumer_ready_will_enable_default": False,
                                        "postgres_rollout_consumer_ready_executes_lock": False,
                                        "postgres_rollout_consumer_input_source_status": "ready",
                                        "postgres_rollout_consumer_input_source_ready": True,
                                        "postgres_rollout_consumer_input_source_kind": "rollout_artifact",
                                        "postgres_target_binding_contract_version": (
                                            "phase-ii-worker-ownership-postgres-vendor-lock-target-artifact-binding-v1"
                                        ),
                                        "postgres_target_binding_default_status": "blocked",
                                        "postgres_target_binding_default_missing_sections": [
                                            "source_kind",
                                            "postgres_rollout_consumer",
                                        ],
                                        "postgres_target_binding_default_will_enable_lock": False,
                                        "postgres_target_binding_default_executes_lock": False,
                                        "postgres_target_binding_ready_status": "ready",
                                        "postgres_target_binding_ready_target_backend": "postgres",
                                        "postgres_target_binding_ready_lock_adapter_kind": (
                                            "postgres_advisory_lock"
                                        ),
                                        "postgres_target_binding_ready_will_enable_lock": False,
                                        "postgres_target_binding_ready_executes_lock": False,
                                        "postgres_target_binding_target_input_status": "ready",
                                        "postgres_target_binding_target_decision_status": "ready",
                                        "postgres_target_binding_target_decision_production_allowed": True,
                                        "postgres_semantics_binding_contract_version": (
                                            "phase-ii-worker-ownership-postgres-vendor-lock-semantics-binding-v1"
                                        ),
                                        "postgres_semantics_binding_default_status": "blocked",
                                        "postgres_semantics_binding_default_missing_sections": [
                                            "target_artifact_binding",
                                            "postgres_execution_seam",
                                        ],
                                        "postgres_semantics_binding_default_will_enable_lock": False,
                                        "postgres_semantics_binding_default_will_update_gate": False,
                                        "postgres_semantics_binding_default_executes_lock": False,
                                        "postgres_semantics_binding_ready_status": "ready",
                                        "postgres_semantics_binding_ready_target_backend": "postgres",
                                        "postgres_semantics_binding_ready_lock_adapter_kind": (
                                            "postgres_advisory_lock"
                                        ),
                                        "postgres_semantics_binding_ready_probe_status": "ready",
                                        "postgres_semantics_binding_ready_adapter_status": "ready",
                                        "postgres_semantics_binding_ready_semantics_status": "ready",
                                        "postgres_semantics_binding_ready_will_enable_lock": False,
                                        "postgres_semantics_binding_ready_will_update_gate": False,
                                        "postgres_semantics_binding_ready_executes_lock": False,
                                        "postgres_wiring_decision_contract_version": (
                                            "phase-ii-worker-ownership-postgres-vendor-lock-production-gate"
                                            "-wiring-decision-v1"
                                        ),
                                        "postgres_wiring_decision_default_status": "blocked",
                                        "postgres_wiring_decision_default_missing_sections": [
                                            "semantics_binding",
                                            "decision_recorded",
                                        ],
                                        "postgres_wiring_decision_default_wiring_allowed": False,
                                        "postgres_wiring_decision_default_will_update_gate": False,
                                        "postgres_wiring_decision_default_will_enable_lock": False,
                                        "postgres_wiring_decision_default_executes_lock": False,
                                        "postgres_wiring_decision_ready_status": "ready",
                                        "postgres_wiring_decision_ready_semantics_binding_status": "ready",
                                        "postgres_wiring_decision_ready_candidate_status": "ready",
                                        "postgres_wiring_decision_ready_wiring_allowed": True,
                                        "postgres_wiring_decision_ready_target_backend": "postgres",
                                        "postgres_wiring_decision_ready_lock_adapter_kind": (
                                            "postgres_advisory_lock"
                                        ),
                                        "postgres_wiring_decision_ready_will_update_gate": False,
                                        "postgres_wiring_decision_ready_will_enable_lock": False,
                                        "postgres_wiring_decision_ready_executes_lock": False,
                                        "production_dry_run_contract_version": (
                                            "phase-ii-worker-ownership-production-gate-composition-dry-run-v1"
                                        ),
                                        "production_dry_run_default_status": "blocked",
                                        "production_dry_run_default_missing_sections": [
                                            "vendor_lock_wiring_decision",
                                            "heartbeat_renewal_supervisor",
                                            "rollout_confirmation",
                                            "recovery_entry_auto_claim_enablement",
                                            "ownership_audit_evidence",
                                            "production_default_enablement_input_source",
                                        ],
                                        "production_dry_run_default_all_required_ready": False,
                                        "production_dry_run_default_would_allow": False,
                                        "production_dry_run_default_will_enable": False,
                                        "production_dry_run_default_executes_lock": False,
                                        "production_dry_run_default_starts_worker": False,
                                        "production_dry_run_default_runs_auto_claim": False,
                                        "production_dry_run_ready_status": "ready",
                                        "production_dry_run_ready_missing_sections": [],
                                        "production_dry_run_ready_all_required_ready": True,
                                        "production_dry_run_ready_would_allow": True,
                                        "production_dry_run_ready_will_enable": False,
                                        "production_dry_run_ready_executes_lock": False,
                                        "production_dry_run_ready_starts_worker": False,
                                        "production_dry_run_ready_runs_auto_claim": False,
                                        "enablement_config_consumer_contract_version": (
                                            "phase-ii-worker-ownership-production-enablement-runtime-config"
                                            "-consumer-v1"
                                        ),
                                        "enablement_config_consumer_default_status": "blocked",
                                        "enablement_config_consumer_default_missing_sections": [
                                            "source_kind",
                                            "config_id",
                                            "enablement_input_source",
                                            "composition_dry_run",
                                        ],
                                        "enablement_config_consumer_default_will_enable": False,
                                        "enablement_config_consumer_default_executes_lock": False,
                                        "enablement_config_consumer_default_starts_worker": False,
                                        "enablement_config_consumer_default_runs_auto_claim": False,
                                        "enablement_config_consumer_ready_status": "ready",
                                        "enablement_config_consumer_ready_missing_sections": [],
                                        "enablement_config_consumer_ready_target_backend": "postgres",
                                        "enablement_config_consumer_ready_lock_adapter_kind": (
                                            "postgres_advisory_lock"
                                        ),
                                        "enablement_config_consumer_ready_input_source_status": "ready",
                                        "enablement_config_consumer_ready_dry_run_status": "ready",
                                        "enablement_config_consumer_ready_dry_run_would_allow": True,
                                        "enablement_config_consumer_ready_will_enable": False,
                                        "enablement_config_consumer_ready_executes_lock": False,
                                        "enablement_config_consumer_ready_starts_worker": False,
                                        "enablement_config_consumer_ready_runs_auto_claim": False,
                                        "enablement_config_factory_binding_default_status": "blocked",
                                        "enablement_config_factory_binding_ready_status": "ready",
                                        "enablement_config_factory_binding_ready_config_id": (
                                            "factory-binding-001"
                                        ),
                                        "enablement_config_factory_binding_will_enable": False,
                                        "enablement_config_factory_binding_executes_lock": False,
                                        "enablement_config_factory_binding_starts_worker": False,
                                        "enablement_config_factory_binding_runs_auto_claim": False,
                                        "vendor_lock_scope_defined": False,
                                        "vendor_lock_fencing_guarantee_defined": False,
                                        "vendor_lock_failover_semantics_defined": False,
                                        "vendor_lock_ttl_renewal_semantics_defined": False,
                                        "vendor_lock_stale_owner_cleanup_defined": False,
                                        "vendor_lock_production_allowed": False,
                                        "vendor_lock_target_decision_contract_version": (
                                            "phase-ii-worker-ownership-vendor-lock-target-decision-v1"
                                        ),
                                        "vendor_lock_target_decision_status": "blocked",
                                        "vendor_lock_target_decision_recorded": False,
                                        "vendor_lock_target_backend": "",
                                        "vendor_lock_target_adapter_kind": "",
                                        "vendor_lock_target_scope": "",
                                        "vendor_lock_target_fencing_strategy": "",
                                        "vendor_lock_target_ttl_renewal_strategy": "",
                                        "vendor_lock_target_failover_strategy": "",
                                        "vendor_lock_target_stale_cleanup_strategy": "",
                                        "vendor_lock_target_missing_sections": [
                                            "input_source",
                                            "decision_recorded",
                                            "target_backend",
                                        ],
                                        "vendor_lock_target_sql_row_lease_is_vendor_lock": False,
                                        "vendor_lock_target_production_allowed": False,
                                        "vendor_lock_target_input_contract_version": (
                                            "phase-ii-worker-ownership-vendor-lock-target-decision-input-v1"
                                        ),
                                        "vendor_lock_target_input_source_status": "blocked",
                                        "vendor_lock_target_input_source_kind": "",
                                        "vendor_lock_target_input_decision_id": "",
                                        "vendor_lock_target_input_approved_by": "",
                                        "vendor_lock_target_input_approved_at": "",
                                        "vendor_lock_target_input_backend": "",
                                        "vendor_lock_target_input_adapter_kind": "",
                                        "vendor_lock_target_input_rollout_artifact": "",
                                        "vendor_lock_target_input_config_key": "",
                                        "vendor_lock_target_input_manual_approval_reference": "",
                                        "vendor_lock_target_input_missing_sections": [
                                            "input_source_kind",
                                            "decision_id",
                                        ],
                                        "vendor_lock_target_input_sql_row_lease_is_vendor_lock": False,
                                        "renewal_supervisor_contract_version": (
                                            "phase-ii-worker-ownership-renewal-supervisor-v1"
                                        ),
                                        "renewal_supervisor_status": "blocked",
                                        "renewal_supervisor_missing_sections": [
                                            "background_supervisor",
                                        ],
                                        "renewal_supervisor_enabled_by_default": False,
                                        "renewal_supervisor_renew_once_supported": True,
                                        "renewal_supervisor_owner_identity_required": True,
                                        "renewal_supervisor_ttl_interval_policy_ready": True,
                                        "renewal_supervisor_controlled_lifecycle_supported": True,
                                        "renewal_supervisor_starts_by_default": False,
                                        "renewal_supervisor_active": False,
                                        "renewal_supervisor_last_renewal_status": "",
                                        "renewal_supervisor_stop_supported": True,
                                        "renewal_supervisor_failure_fail_closed": True,
                                        "renewal_supervisor_lease_loss_fail_closed": True,
                                        "renewal_supervisor_renew_once_status": "renewed",
                                        "renewal_supervisor_renew_once_background_started": False,
                                        "renewal_supervisor_stale_fencing_status": "blocked",
                                        "renewal_supervisor_stale_fencing_reason": "stale_worker_fencing_token",
                                        "renewal_supervisor_lifecycle_initial_active": False,
                                        "renewal_supervisor_lifecycle_started_active": True,
                                        "renewal_supervisor_lifecycle_started_status": "renewed",
                                        "renewal_supervisor_lifecycle_started_count": 1,
                                        "renewal_supervisor_lifecycle_stopped_active": False,
                                        "renewal_supervisor_lifecycle_stopped_count": 1,
                                        "rollout_readiness_contract_version": (
                                            "phase-ii-worker-ownership-rollout-readiness-v1"
                                        ),
                                        "rollout_readiness_status": "blocked",
                                        "rollout_missing_sections": [
                                            "strict_mode_rollout",
                                        ],
                                        "production_rollout_confirmed": False,
                                        "rollout_migration_ready": True,
                                        "rollout_stale_fencing_verified": True,
                                        "rollout_rollback_plan_ready": False,
                                        "rollout_operationalization_status": "blocked",
                                        "rollout_mode": "readiness_only",
                                        "rollout_missing_artifacts": [
                                            "rollback_plan",
                                            "rollout_confirmation_decision",
                                        ],
                                        "rollout_rollback_plan_status": "missing",
                                        "rollout_fallback_policy_status": "missing",
                                        "rollout_renewal_lifecycle_verification_status": "missing",
                                        "rollout_auto_claim_decision_status": "missing",
                                        "rollout_confirmation_decision_contract_version": (
                                            "phase-ii-worker-ownership-rollout-confirmation-decision-v1"
                                        ),
                                        "rollout_confirmation_decision_status": "blocked",
                                        "rollout_decision_recorded": False,
                                        "rollout_decision_id": "",
                                        "rollout_approved_by": "",
                                        "rollout_approved_at": "",
                                        "rollout_target_store_mode": "",
                                        "rollout_confirmation_missing_sections": [
                                            "decision_recorded",
                                        ],
                                        "rollout_confirmation_production_rollout_confirmed": False,
                                        "rollout_confirmation_input_contract_version": (
                                            "phase-ii-worker-ownership-rollout-confirmation-input-source-v1"
                                        ),
                                        "rollout_confirmation_input_source_status": "blocked",
                                        "rollout_confirmation_input_source_kind": "",
                                        "rollout_confirmation_input_decision_id": "",
                                        "rollout_confirmation_input_approved_by": "",
                                        "rollout_confirmation_input_approved_at": "",
                                        "rollout_confirmation_input_target_store_mode": "",
                                        "rollout_confirmation_input_rollback_plan_reference": "",
                                        "rollout_confirmation_input_fallback_policy_reference": "",
                                        "rollout_confirmation_input_renewal_lifecycle_reference": "",
                                        "rollout_confirmation_input_auto_claim_decision_reference": "",
                                        "rollout_confirmation_input_missing_sections": [
                                            "input_source_kind",
                                            "decision_id",
                                        ],
                                        "rollout_confirmation_input_sql_row_lease_is_authority": False,
                                        "auto_claim_policy_contract_version": (
                                            "phase-ii-worker-ownership-auto-claim-policy-v1"
                                        ),
                                        "auto_claim_policy_status": "blocked",
                                        "auto_claim_missing_sections": [
                                            "explicit_runtime_configuration",
                                        ],
                                        "auto_claim_enabled_by_default": False,
                                        "auto_claim_descriptor_evidence_fallback": True,
                                        "auto_claim_lease_validation_required": True,
                                        "auto_claim_entrypoint_allowlist_ready": True,
                                        "auto_claim_entrypoint_allowlist_contract_version": (
                                            "phase-ii-worker-ownership-auto-claim-entrypoint-allowlist-v1"
                                        ),
                                        "auto_claim_entrypoint_allowlist_status": "ready",
                                        "auto_claim_allowed_entrypoints": [
                                            "submit_approval.approved",
                                            "resume_run.continue_loop",
                                        ],
                                        "auto_claim_missing_entrypoints": [],
                                        "auto_claim_default_auto_claim_enabled": False,
                                        "auto_claim_requires_production_gate_ready": True,
                                        "auto_claim_enablement_gate_contract_version": (
                                            "phase-ii-worker-ownership-explicit-auto-claim-enablement-gate-v1"
                                        ),
                                        "auto_claim_enablement_gate_status": "blocked",
                                        "auto_claim_will_auto_claim": False,
                                        "auto_claim_requested_entrypoint": "submit_approval.approved",
                                        "auto_claim_enablement_missing_sections": [
                                            "explicit_runtime_configuration",
                                        ],
                                        "auto_claim_enablement_blocked_reason": (
                                            "explicit_runtime_configuration_missing"
                                        ),
                                        "ownership_audit_contract_version": (
                                            "phase-ii-worker-ownership-audit-evidence-v1"
                                        ),
                                        "ownership_audit_status": "blocked",
                                        "ownership_audit_missing_sections": [
                                            "operation_history",
                                        ],
                                        "ownership_audit_compact_evidence": True,
                                        "ownership_audit_operation_history_ready": False,
                                        "ownership_audit_recovery_operation_link_ready": False,
                                        "ownership_audit_timeline_writer_ready": False,
                                        "ownership_audit_idempotent_dedupe_ready": False,
                                        "ownership_audit_authorization_source": False,
                                        "enablement_strategy_contract_version": (
                                            "phase-ii-worker-ownership-production-enablement-strategy-v1"
                                        ),
                                        "enablement_strategy_status": "blocked",
                                        "enablement_strategy_blocking_sections": [
                                            "vendor_lock_semantics",
                                            "production_default_enablement_input_source",
                                        ],
                                        "production_default_enabled_requested": False,
                                        "production_default_allowed": False,
                                        "enablement_input_source_contract_version": (
                                            "phase-ii-worker-ownership-production-default-enablement-input-source-v1"
                                        ),
                                        "enablement_input_source_status": "blocked",
                                        "enablement_input_source_kind": "",
                                        "enablement_request_id": "",
                                        "enablement_requested_by": "",
                                        "enablement_requested_at": "",
                                        "enablement_target_store_mode": "",
                                        "enablement_rollout_artifact": "",
                                        "enablement_vendor_lock_decision_id": "",
                                        "enablement_renewal_lifecycle_reference": "",
                                        "enablement_auto_claim_decision_reference": "",
                                        "enablement_audit_evidence_reference": "",
                                        "enablement_rollback_plan_reference": "",
                                        "enablement_fallback_policy_reference": "",
                                        "enablement_input_source_ready": False,
                                        "enablement_input_source_missing_sections": [
                                            "input_source_kind",
                                        ],
                                        "enablement_explicit_required": True,
                                        "enablement_all_required_sections_ready": False,
                                        "enablement_fail_closed_when_blocked": True,
                                        "enablement_sql_row_lease_not_default_authority": True,
                                    },
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        coverage = contract["runtime_contract_summary"]["worker_ownership_store_mode_coverage"]
        self.assertTrue(coverage["mode_smoke"])
        self.assertEqual(coverage["default_mode"], "memory_only")
        self.assertEqual(coverage["strict_mode_status"], "sqlalchemy_durable")
        self.assertEqual(coverage["fallback_mode_status"], "fallback_to_memory")
        self.assertEqual(coverage["production_gate_status"], "blocked")
        self.assertIn("heartbeat_renewal_supervisor", coverage["production_gate_missing_sections"])
        self.assertIn("fail_closed_default_decision", coverage["production_gate_missing_sections"])
        self.assertEqual(
            coverage["vendor_lock_contract_version"],
            "phase-ii-worker-ownership-vendor-lock-semantics-v1",
        )
        self.assertEqual(coverage["vendor_lock_status"], "blocked")
        self.assertEqual(coverage["vendor_lock_current_posture"], "sql_row_lease_fencing")
        self.assertTrue(coverage["vendor_lock_sql_row_lease_fencing"])
        self.assertFalse(coverage["vendor_lock_sql_row_lease_is_vendor_lock"])
        self.assertFalse(coverage["vendor_lock_adapter_present"])
        self.assertEqual(
            coverage["vendor_lock_adapter_contract_version"],
            "phase-ii-worker-ownership-vendor-lock-adapter-v1",
        )
        self.assertEqual(coverage["vendor_lock_adapter_status"], "blocked")
        self.assertEqual(coverage["vendor_lock_adapter_kind"], "")
        self.assertEqual(coverage["vendor_lock_adapter_target_backend"], "")
        self.assertFalse(coverage["vendor_lock_adapter_acquire_supported"])
        self.assertFalse(coverage["vendor_lock_adapter_renew_supported"])
        self.assertFalse(coverage["vendor_lock_adapter_release_supported"])
        self.assertFalse(coverage["vendor_lock_adapter_probe_supported"])
        self.assertFalse(coverage["vendor_lock_adapter_production_allowed"])
        self.assertFalse(coverage["vendor_lock_adapter_sql_row_lease_is_vendor_lock"])
        self.assertIn("adapter_kind", coverage["vendor_lock_adapter_missing_sections"])
        self.assertEqual(
            coverage["postgres_probe_contract_version"],
            "phase-ii-worker-ownership-postgres-vendor-lock-probe-v1",
        )
        self.assertEqual(coverage["postgres_probe_status"], "blocked")
        self.assertFalse(coverage["postgres_probe_executes"])
        self.assertFalse(coverage["postgres_probe_sql_row_lease_is_vendor_lock"])
        self.assertIn("advisory_lock_family", coverage["postgres_probe_missing_sections"])
        self.assertEqual(coverage["postgres_probe_ready_status"], "ready")
        self.assertFalse(coverage["postgres_probe_ready_executes"])
        self.assertFalse(coverage["vendor_lock_production_allowed"])
        self.assertIn("vendor_lock_adapter", coverage["vendor_lock_missing_sections"])
        self.assertIn("target_decision", coverage["vendor_lock_missing_sections"])
        self.assertEqual(
            coverage["vendor_lock_target_decision_contract_version"],
            "phase-ii-worker-ownership-vendor-lock-target-decision-v1",
        )
        self.assertEqual(coverage["vendor_lock_target_decision_status"], "blocked")
        self.assertFalse(coverage["vendor_lock_target_decision_recorded"])
        self.assertEqual(coverage["vendor_lock_target_backend"], "")
        self.assertIn("input_source", coverage["vendor_lock_target_missing_sections"])
        self.assertIn("decision_recorded", coverage["vendor_lock_target_missing_sections"])
        self.assertEqual(
            coverage["vendor_lock_target_input_contract_version"],
            "phase-ii-worker-ownership-vendor-lock-target-decision-input-v1",
        )
        self.assertEqual(coverage["vendor_lock_target_input_source_status"], "blocked")
        self.assertIn(
            "input_source_kind",
            coverage["vendor_lock_target_input_missing_sections"],
        )
        self.assertFalse(coverage["vendor_lock_target_sql_row_lease_is_vendor_lock"])
        self.assertFalse(coverage["vendor_lock_target_input_sql_row_lease_is_vendor_lock"])
        self.assertFalse(coverage["vendor_lock_target_production_allowed"])
        self.assertEqual(
            coverage["renewal_supervisor_contract_version"],
            "phase-ii-worker-ownership-renewal-supervisor-v1",
        )
        self.assertEqual(coverage["renewal_supervisor_status"], "blocked")
        self.assertIn("background_supervisor", coverage["renewal_supervisor_missing_sections"])
        self.assertFalse(coverage["renewal_supervisor_enabled_by_default"])
        self.assertTrue(coverage["renewal_supervisor_renew_once_supported"])
        self.assertTrue(coverage["renewal_supervisor_owner_identity_required"])
        self.assertTrue(coverage["renewal_supervisor_ttl_interval_policy_ready"])
        self.assertTrue(coverage["renewal_supervisor_controlled_lifecycle_supported"])
        self.assertFalse(coverage["renewal_supervisor_starts_by_default"])
        self.assertFalse(coverage["renewal_supervisor_active"])
        self.assertEqual(coverage["renewal_supervisor_last_renewal_status"], "")
        self.assertTrue(coverage["renewal_supervisor_stop_supported"])
        self.assertTrue(coverage["renewal_supervisor_failure_fail_closed"])
        self.assertTrue(coverage["renewal_supervisor_lease_loss_fail_closed"])
        self.assertEqual(coverage["renewal_supervisor_renew_once_status"], "renewed")
        self.assertFalse(coverage["renewal_supervisor_renew_once_background_started"])
        self.assertEqual(coverage["renewal_supervisor_stale_fencing_status"], "blocked")
        self.assertEqual(
            coverage["renewal_supervisor_stale_fencing_reason"],
            "stale_worker_fencing_token",
        )
        self.assertFalse(coverage["renewal_supervisor_lifecycle_initial_active"])
        self.assertTrue(coverage["renewal_supervisor_lifecycle_started_active"])
        self.assertEqual(coverage["renewal_supervisor_lifecycle_started_status"], "renewed")
        self.assertGreaterEqual(coverage["renewal_supervisor_lifecycle_started_count"], 1)
        self.assertFalse(coverage["renewal_supervisor_lifecycle_stopped_active"])
        self.assertGreaterEqual(coverage["renewal_supervisor_lifecycle_stopped_count"], 1)
        self.assertEqual(
            coverage["rollout_readiness_contract_version"],
            "phase-ii-worker-ownership-rollout-readiness-v1",
        )
        self.assertEqual(coverage["rollout_readiness_status"], "blocked")
        self.assertIn("strict_mode_rollout", coverage["rollout_missing_sections"])
        self.assertFalse(coverage["production_rollout_confirmed"])
        self.assertTrue(coverage["rollout_migration_ready"])
        self.assertTrue(coverage["rollout_stale_fencing_verified"])
        self.assertFalse(coverage["rollout_rollback_plan_ready"])
        self.assertEqual(coverage["rollout_operationalization_status"], "blocked")
        self.assertEqual(coverage["rollout_mode"], "readiness_only")
        self.assertIn("rollback_plan", coverage["rollout_missing_artifacts"])
        self.assertIn("rollout_confirmation_decision", coverage["rollout_missing_artifacts"])
        self.assertEqual(coverage["rollout_rollback_plan_status"], "missing")
        self.assertEqual(coverage["rollout_fallback_policy_status"], "missing")
        self.assertEqual(
            coverage["rollout_renewal_lifecycle_verification_status"],
            "missing",
        )
        self.assertEqual(coverage["rollout_auto_claim_decision_status"], "missing")
        self.assertEqual(
            coverage["rollout_confirmation_decision_contract_version"],
            "phase-ii-worker-ownership-rollout-confirmation-decision-v1",
        )
        self.assertEqual(coverage["rollout_confirmation_decision_status"], "blocked")
        self.assertFalse(coverage["rollout_decision_recorded"])
        self.assertEqual(coverage["rollout_target_store_mode"], "")
        self.assertIn("decision_recorded", coverage["rollout_confirmation_missing_sections"])
        self.assertFalse(coverage["rollout_confirmation_production_rollout_confirmed"])
        self.assertEqual(
            coverage["rollout_confirmation_input_contract_version"],
            "phase-ii-worker-ownership-rollout-confirmation-input-source-v1",
        )
        self.assertEqual(coverage["rollout_confirmation_input_source_status"], "blocked")
        self.assertIn(
            "input_source_kind",
            coverage["rollout_confirmation_input_missing_sections"],
        )
        self.assertFalse(coverage["rollout_confirmation_input_sql_row_lease_is_authority"])
        self.assertEqual(
            coverage["auto_claim_policy_contract_version"],
            "phase-ii-worker-ownership-auto-claim-policy-v1",
        )
        self.assertEqual(coverage["auto_claim_policy_status"], "blocked")
        self.assertIn("explicit_runtime_configuration", coverage["auto_claim_missing_sections"])
        self.assertFalse(coverage["auto_claim_enabled_by_default"])
        self.assertTrue(coverage["auto_claim_descriptor_evidence_fallback"])
        self.assertTrue(coverage["auto_claim_lease_validation_required"])
        self.assertTrue(coverage["auto_claim_entrypoint_allowlist_ready"])
        self.assertEqual(
            coverage["auto_claim_entrypoint_allowlist_contract_version"],
            "phase-ii-worker-ownership-auto-claim-entrypoint-allowlist-v1",
        )
        self.assertEqual(coverage["auto_claim_entrypoint_allowlist_status"], "ready")
        self.assertIn("submit_approval.approved", coverage["auto_claim_allowed_entrypoints"])
        self.assertIn("resume_run.continue_loop", coverage["auto_claim_allowed_entrypoints"])
        self.assertEqual(coverage["auto_claim_missing_entrypoints"], [])
        self.assertFalse(coverage["auto_claim_default_auto_claim_enabled"])
        self.assertTrue(coverage["auto_claim_requires_production_gate_ready"])
        self.assertEqual(
            coverage["auto_claim_enablement_gate_contract_version"],
            "phase-ii-worker-ownership-explicit-auto-claim-enablement-gate-v1",
        )
        self.assertEqual(coverage["auto_claim_enablement_gate_status"], "blocked")
        self.assertFalse(coverage["auto_claim_will_auto_claim"])
        self.assertEqual(coverage["auto_claim_requested_entrypoint"], "submit_approval.approved")
        self.assertIn(
            "explicit_runtime_configuration",
            coverage["auto_claim_enablement_missing_sections"],
        )
        self.assertEqual(
            coverage["auto_claim_enablement_blocked_reason"],
            "explicit_runtime_configuration_missing",
        )
        self.assertEqual(
            coverage["ownership_audit_contract_version"],
            "phase-ii-worker-ownership-audit-evidence-v1",
        )
        self.assertEqual(coverage["ownership_audit_status"], "blocked")
        self.assertTrue(coverage["ownership_audit_compact_evidence"])
        self.assertFalse(coverage["ownership_audit_authorization_source"])
        self.assertIn("operation_history", coverage["ownership_audit_missing_sections"])
        self.assertEqual(
            coverage["enablement_strategy_contract_version"],
            "phase-ii-worker-ownership-production-enablement-strategy-v1",
        )
        self.assertEqual(coverage["enablement_strategy_status"], "blocked")
        self.assertIn("vendor_lock_semantics", coverage["enablement_strategy_blocking_sections"])
        self.assertIn(
            "production_default_enablement_input_source",
            coverage["enablement_strategy_blocking_sections"],
        )
        self.assertFalse(coverage["production_default_enabled_requested"])
        self.assertFalse(coverage["production_default_allowed"])
        self.assertEqual(
            coverage["enablement_input_source_contract_version"],
            "phase-ii-worker-ownership-production-default-enablement-input-source-v1",
        )
        self.assertEqual(coverage["enablement_input_source_status"], "blocked")
        self.assertFalse(coverage["enablement_input_source_ready"])
        self.assertIn("input_source_kind", coverage["enablement_input_source_missing_sections"])
        self.assertTrue(coverage["enablement_explicit_required"])
        self.assertFalse(coverage["enablement_all_required_sections_ready"])
        self.assertTrue(coverage["enablement_fail_closed_when_blocked"])
        self.assertTrue(coverage["enablement_sql_row_lease_not_default_authority"])
        self.assertTrue(coverage["enablement_config_factory_binding_smoke"])
        self.assertEqual(
            coverage["enablement_config_factory_binding_ready_config_id"],
            "factory-binding-001",
        )
        self.assertFalse(coverage["enablement_config_factory_binding_will_enable"])
        self.assertFalse(coverage["enablement_config_factory_binding_executes_lock"])
        self.assertFalse(coverage["enablement_config_factory_binding_starts_worker"])
        self.assertFalse(coverage["enablement_config_factory_binding_runs_auto_claim"])

    def test_build_runtime_contract_fails_closed_when_worker_ownership_mode_summary_evidence_disagrees(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-24T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "runtime_contract_summary": {
                                    "overall_status": "healthy",
                                    "check_count": 1,
                                    "failed_check_count": 0,
                                    "missing_payload_count": 0,
                                    "worker_ownership_store_mode_coverage": {
                                        "mode_smoke": True,
                                        "default_mode": "strict_sql",
                                        "default_mode_source": "default",
                                        "default_adapter_kind": "sqlalchemy",
                                        "default_durable": True,
                                        "configurable_knob_present": True,
                                        "hot_reloadable_knob_present": True,
                                        "strict_mode_status": "sqlalchemy_durable",
                                        "fallback_mode_status": "fallback_to_memory",
                                    },
                                },
                                "contract_checks": [
                                    {"name": "runtime_profile_contract_snapshot", "ok": True},
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        coverage = contract["runtime_contract_summary"]["worker_ownership_store_mode_coverage"]
        self.assertFalse(coverage["mode_smoke"])
        self.assertEqual(coverage["default_mode"], "strict_sql")

    def test_build_runtime_contract_derives_child_executor_promotion_gate_coverage_from_checks(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-24T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "contract_checks": [
                                    {
                                        "name": "child_executor_promotion_gate",
                                        "ok": True,
                                        "contract_version": "phase-ii-child-executor-gate-v1",
                                        "gate_status": "blocked",
                                        "allowed": False,
                                        "gate_failure_reason": "child_executor_preflight_blocked",
                                        "blocker_count": 2,
                                        "recommended_next_step": "keep_relationship_only",
                                    },
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        coverage = contract["runtime_contract_summary"]["child_executor_promotion_gate_coverage"]
        self.assertTrue(coverage["gate_smoke"])
        self.assertEqual(coverage["contract_version"], "phase-ii-child-executor-gate-v1")
        self.assertEqual(coverage["gate_status"], "blocked")
        self.assertFalse(coverage["allowed"])
        self.assertEqual(coverage["failure_reason"], "child_executor_preflight_blocked")

    def test_build_runtime_contract_derives_recovery_retry_evidence_coverage_from_checks(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-24T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "contract_checks": [
                                    {
                                        "name": "recovery_retry_evidence",
                                        "ok": True,
                                        "contract_version": "phase-ii-recovery-retry-protocol-v1",
                                        "attempt_number": 3,
                                        "max_attempts": 3,
                                        "retry_status": "exhausted",
                                        "retryable": True,
                                        "terminal": True,
                                        "recovery_reason": "workspace_backend_not_durable",
                                        "idempotency_key_present": True,
                                    },
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        coverage = contract["runtime_contract_summary"]["recovery_retry_evidence_coverage"]
        self.assertTrue(coverage["retry_smoke"])
        self.assertEqual(coverage["contract_version"], "phase-ii-recovery-retry-protocol-v1")
        self.assertEqual(coverage["attempt_number"], 3)
        self.assertEqual(coverage["max_attempts"], 3)
        self.assertEqual(coverage["retry_status"], "exhausted")
        self.assertTrue(coverage["retryable"])
        self.assertTrue(coverage["terminal"])
        self.assertEqual(coverage["recovery_reason"], "workspace_backend_not_durable")
        self.assertTrue(coverage["idempotency_key_present"])

    def test_build_runtime_contract_derives_recovery_retry_scheduler_production_gate_coverage(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-24T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "contract_checks": [
                                    {
                                        "name": "recovery_retry_scheduler",
                                        "ok": True,
                                        "contract_version": "phase-ii-recovery-retry-scheduler-v1",
                                        "default_status": "disabled",
                                        "default_eligible": True,
                                        "default_will_execute": False,
                                        "production_gate_contract_version": "phase-ii-recovery-retry-production-scheduler-gate-v1",
                                        "production_gate_status": "blocked",
                                        "production_gate_missing_sections": ["durable_scheduling_state"],
                                        "production_gate_blocked_reason": "production_scheduler_gate_blocked",
                                        "production_automatic_retry_enabled_by_default": False,
                                        "production_automatic_will_execute": False,
                                        "enabled_status": "executed",
                                        "enabled_will_execute": True,
                                        "latest_operation_status": "recovered",
                                        "attempt_number": 1,
                                        "retry_status": "retryable",
                                        "recovery_reason": "transient_workspace_unavailable",
                                        "previous_operation_id_present": True,
                                        "idempotency_key_present": True,
                                    },
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        coverage = contract["runtime_contract_summary"]["recovery_retry_scheduler_coverage"]
        self.assertTrue(coverage["scheduler_smoke"])
        self.assertEqual(
            coverage["production_gate_contract_version"],
            "phase-ii-recovery-retry-production-scheduler-gate-v1",
        )
        self.assertEqual(coverage["production_gate_status"], "blocked")
        self.assertEqual(
            coverage["production_gate_blocked_reason"],
            "production_scheduler_gate_blocked",
        )
        self.assertFalse(coverage["production_automatic_will_execute"])

    def test_build_runtime_contract_derives_tool_runtime_timeout_retry_coverage(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-26T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "contract_checks": [
                                    {
                                        "name": "tool_runtime_timeout_retry",
                                        "ok": True,
                                        "retry_policy": "sync_exception_retry",
                                        "timeout_enforcement": "post_call_elapsed_check",
                                        "recovered_status": "ok",
                                        "recovered_retry_status": "recovered",
                                        "recovered_attempt_count": 2,
                                        "exhausted_status": "error",
                                        "exhausted_retry_status": "exhausted",
                                        "exhausted_attempt_count": 2,
                                        "timeout_status": "timeout",
                                        "timeout_metadata_status": "exceeded",
                                        "timeout_metadata_enforcement": "post_call_elapsed_check",
                                        "hard_cancellation_claimed": False,
                                        "sandbox_execution_claimed": False,
                                        "worker_timeout_claimed": False,
                                    },
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        coverage = contract["runtime_contract_summary"]["tool_runtime_timeout_retry_coverage"]
        self.assertTrue(coverage["timeout_retry_smoke"])
        self.assertEqual(coverage["retry_policy"], "sync_exception_retry")
        self.assertEqual(coverage["timeout_enforcement"], "post_call_elapsed_check")
        self.assertEqual(coverage["recovered_retry_status"], "recovered")
        self.assertEqual(coverage["exhausted_retry_status"], "exhausted")
        self.assertEqual(coverage["timeout_metadata_status"], "exceeded")

    def test_build_runtime_contract_derives_child_executor_dispatch_coverage_from_checks(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-24T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "contract_checks": [
                                    {
                                        "name": "child_executor_dispatch_contract",
                                        "ok": True,
                                        "contract_version": "phase-ii-child-executor-dispatch-v1",
                                        "dispatch_status": "blocked",
                                        "dispatch_ready": False,
                                        "will_dispatch": False,
                                        "backend_dispatch_ready": False,
                                        "relationship_seam_preserved": True,
                                        "dispatch_blocker_count": 2,
                                        "dispatch_blockers": [
                                            "worker_backend_dispatch_ready",
                                            "explicit_executor_binding_opt_in",
                                        ],
                                        "explicit_executor_binding_ready": False,
                                        "explicit_executor_binding_status": "blocked",
                                        "explicit_executor_binding_source": "",
                                        "opt_in_dispatch_status": "blocked",
                                        "opt_in_dispatch_ready": False,
                                        "opt_in_will_dispatch": False,
                                        "opt_in_backend_dispatch_ready": False,
                                        "opt_in_explicit_executor_binding_ready": True,
                                        "opt_in_explicit_executor_binding_status": "ready",
                                        "opt_in_explicit_executor_binding_source": (
                                            "payload.explicit_executor_binding_opt_in"
                                        ),
                                        "recommended_next_step": "implement_child_executor_backend_dispatch",
                                    },
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        coverage = contract["runtime_contract_summary"]["child_executor_dispatch_coverage"]
        self.assertTrue(coverage["dispatch_smoke"])
        self.assertEqual(coverage["contract_version"], "phase-ii-child-executor-dispatch-v1")
        self.assertEqual(coverage["overall_status"], "blocked")
        self.assertFalse(coverage["dispatch_ready"])
        self.assertFalse(coverage["will_dispatch"])
        self.assertFalse(coverage["backend_dispatch_ready"])
        self.assertEqual(coverage["blocker_count"], 2)

    def test_build_runtime_contract_derives_child_executor_dispatcher_coverage_from_checks(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-24T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "contract_checks": [
                                    {
                                        "name": "child_executor_dispatcher",
                                        "ok": True,
                                        "contract_version": "phase-ii-child-executor-dispatcher-v1",
                                        "default_status": "blocked",
                                        "default_blocked_reason": "dispatcher_disabled",
                                        "default_will_dispatch": False,
                                        "blocked_reason": "dispatch_contract_not_ready",
                                        "blocked_will_dispatch": False,
                                        "enabled_status": "dispatched",
                                        "enabled_will_dispatch": True,
                                        "backend_result_status": "completed",
                                        "backend_invocation_count": 1,
                                    },
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        coverage = contract["runtime_contract_summary"]["child_executor_dispatcher_coverage"]
        self.assertTrue(coverage["dispatcher_smoke"])
        self.assertEqual(coverage["contract_version"], "phase-ii-child-executor-dispatcher-v1")
        self.assertEqual(coverage["default_blocked_reason"], "dispatcher_disabled")
        self.assertEqual(coverage["blocked_reason"], "dispatch_contract_not_ready")
        self.assertEqual(coverage["enabled_status"], "dispatched")
        self.assertEqual(coverage["backend_invocation_count"], 1)

    def test_build_runtime_contract_derives_child_executor_sandbox_backend_coverage_from_checks(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-24T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "contract_checks": [
                                    {
                                        "name": "child_executor_sandbox_backend",
                                        "ok": True,
                                        "contract_version": "phase-ii-child-executor-sandbox-worker-backend-v1",
                                        "ready_adapter_contract": True,
                                        "ready_sandbox_guard": True,
                                        "ready_audit": True,
                                        "ready_idempotency": True,
                                        "missing_guard_fail_closed": True,
                                        "missing_guard_count": 3,
                                        "unsafe_payload_blocked": True,
                                        "unsafe_blocked_reason": "sandbox_payload_unsafe",
                                        "compact_attempt_valid": True,
                                        "dispatch_status": "dispatched",
                                        "backend_result_status": "completed",
                                        "backend_invocation_count": 1,
                                        "default_worker_enabled": False,
                                    },
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        coverage = contract["runtime_contract_summary"]["child_executor_sandbox_backend_coverage"]
        self.assertTrue(coverage["sandbox_backend_smoke"])
        self.assertEqual(
            coverage["contract_version"],
            "phase-ii-child-executor-sandbox-worker-backend-v1",
        )
        self.assertTrue(coverage["ready_adapter_contract"])
        self.assertTrue(coverage["missing_guard_fail_closed"])
        self.assertTrue(coverage["unsafe_payload_blocked"])
        self.assertTrue(coverage["compact_attempt_valid"])
        self.assertFalse(coverage["default_worker_enabled"])

    def test_build_runtime_contract_fails_closed_when_child_executor_gate_summary_evidence_disagrees(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-24T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "runtime_contract_summary": {
                                    "overall_status": "healthy",
                                    "check_count": 1,
                                    "failed_check_count": 0,
                                    "missing_payload_count": 0,
                                    "child_executor_promotion_gate_coverage": {
                                        "gate_smoke": True,
                                        "contract_version": "phase-ii-child-executor-gate-v1",
                                        "gate_status": "passed",
                                        "allowed": True,
                                        "failure_reason": "",
                                        "blocker_count": 0,
                                        "recommended_next_step": "execute_child",
                                    },
                                },
                                "contract_checks": [
                                    {"name": "runtime_profile_contract_snapshot", "ok": True},
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        coverage = contract["runtime_contract_summary"]["child_executor_promotion_gate_coverage"]
        self.assertFalse(coverage["gate_smoke"])
        self.assertEqual(coverage["gate_status"], "passed")

    def test_build_runtime_contract_fails_closed_when_child_executor_dispatch_summary_evidence_disagrees(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-24T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "runtime_contract_summary": {
                                    "overall_status": "healthy",
                                    "check_count": 1,
                                    "failed_check_count": 0,
                                    "missing_payload_count": 0,
                                    "child_executor_dispatch_coverage": {
                                        "dispatch_smoke": True,
                                        "contract_version": "phase-ii-child-executor-dispatch-v1",
                                        "overall_status": "ready",
                                        "dispatch_ready": True,
                                        "will_dispatch": True,
                                        "backend_dispatch_ready": True,
                                        "relationship_seam_preserved": False,
                                        "blocker_count": 0,
                                        "recommended_next_step": "dispatch_now",
                                    },
                                },
                                "contract_checks": [
                                    {"name": "runtime_profile_contract_snapshot", "ok": True},
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        coverage = contract["runtime_contract_summary"]["child_executor_dispatch_coverage"]
        self.assertFalse(coverage["dispatch_smoke"])
        self.assertEqual(coverage["overall_status"], "ready")
        self.assertTrue(coverage["dispatch_ready"])

    def test_build_runtime_contract_fails_closed_when_child_executor_dispatcher_summary_evidence_disagrees(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-24T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "runtime_contract_summary": {
                                    "overall_status": "healthy",
                                    "check_count": 1,
                                    "failed_check_count": 0,
                                    "missing_payload_count": 0,
                                    "child_executor_dispatcher_coverage": {
                                        "dispatcher_smoke": True,
                                        "contract_version": "phase-ii-child-executor-dispatcher-v1",
                                        "default_status": "blocked",
                                        "default_blocked_reason": "dispatcher_disabled",
                                        "default_will_dispatch": False,
                                        "blocked_reason": "dispatch_contract_not_ready",
                                        "blocked_will_dispatch": False,
                                        "enabled_status": "blocked",
                                        "enabled_will_dispatch": False,
                                        "backend_result_status": "",
                                        "backend_invocation_count": 0,
                                    },
                                },
                                "contract_checks": [
                                    {"name": "runtime_profile_contract_snapshot", "ok": True},
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        coverage = contract["runtime_contract_summary"]["child_executor_dispatcher_coverage"]
        self.assertFalse(coverage["dispatcher_smoke"])
        self.assertEqual(coverage["enabled_status"], "blocked")
        self.assertFalse(coverage["enabled_will_dispatch"])

    def test_build_runtime_contract_fails_closed_when_child_executor_sandbox_backend_summary_evidence_disagrees(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-24T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "runtime_contract_summary": {
                                    "overall_status": "healthy",
                                    "check_count": 1,
                                    "failed_check_count": 0,
                                    "missing_payload_count": 0,
                                    "child_executor_sandbox_backend_coverage": {
                                        "sandbox_backend_smoke": True,
                                        "contract_version": "phase-ii-child-executor-sandbox-worker-backend-v1",
                                        "ready_adapter_contract": True,
                                        "ready_sandbox_guard": True,
                                        "ready_audit": True,
                                        "ready_idempotency": True,
                                        "missing_guard_fail_closed": True,
                                        "missing_guard_count": 0,
                                        "unsafe_payload_blocked": True,
                                        "unsafe_blocked_reason": "sandbox_payload_unsafe",
                                        "compact_attempt_valid": True,
                                        "dispatch_status": "dispatched",
                                        "backend_result_status": "completed",
                                        "backend_invocation_count": 1,
                                        "default_worker_enabled": False,
                                    },
                                },
                                "contract_checks": [
                                    {"name": "runtime_profile_contract_snapshot", "ok": True},
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        coverage = contract["runtime_contract_summary"]["child_executor_sandbox_backend_coverage"]
        self.assertFalse(coverage["sandbox_backend_smoke"])
        self.assertEqual(coverage["missing_guard_count"], 0)

    def test_build_runtime_contract_fails_closed_when_recovery_retry_summary_evidence_disagrees(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-24T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "runtime_contract_summary": {
                                    "overall_status": "healthy",
                                    "check_count": 1,
                                    "failed_check_count": 0,
                                    "missing_payload_count": 0,
                                    "recovery_retry_evidence_coverage": {
                                        "retry_smoke": True,
                                        "contract_version": "phase-ii-recovery-retry-protocol-v1",
                                        "attempt_number": 2,
                                        "max_attempts": 3,
                                        "retry_status": "attempted",
                                        "retryable": True,
                                        "terminal": False,
                                        "recovery_reason": "workspace_backend_not_durable",
                                        "idempotency_key_present": False,
                                    },
                                },
                                "contract_checks": [
                                    {"name": "runtime_profile_contract_snapshot", "ok": True},
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        coverage = contract["runtime_contract_summary"]["recovery_retry_evidence_coverage"]
        self.assertFalse(coverage["retry_smoke"])
        self.assertEqual(coverage["attempt_number"], 2)
        self.assertEqual(coverage["retry_status"], "attempted")
        self.assertFalse(coverage["terminal"])

    def test_build_runtime_contract_returns_unknown_summary_when_contract_checks_are_missing(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-21T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "stdout": "PASS: quality_gate_smoke",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        self.assertTrue(contract["available"])
        self.assertEqual(contract["overall_status"], "unknown")
        self.assertEqual(contract["failure_reason"], "contract_checks_missing")
        self.assertEqual(contract["runtime_contract_summary"]["overall_status"], "unknown")
        self.assertEqual(contract["runtime_contract_summary"]["missing_payload_count"], 0)
        self.assertEqual(contract["runtime_contract_artifact_schema"]["overall_status"], "unknown")

    def test_build_runtime_contract_derives_artifact_schema_for_old_reports(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-22T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "runtime_contract_summary": {
                                    "overall_status": "healthy",
                                    "check_count": 2,
                                    "failed_check_count": 0,
                                    "missing_payload_count": 0,
                                    "approval_replay_coverage": {
                                        "event_payload_sample": True,
                                        "observed_status_kinds": ["approval_replayed", "approval_ignored"],
                                    },
                                    "approved_tool_execution_coverage": {
                                        "bridge_smoke": True,
                                    },
                                    "subagent_lane_query_detail_coverage": {
                                        "detail_smoke": True,
                                    },
                                },
                                "contract_checks": [
                                    {"name": "embedded_sdk_event_payloads", "ok": True},
                                    {"name": "subagent_lane_query_detail", "ok": True},
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        artifact_schema = contract["runtime_contract_artifact_schema"]
        self.assertEqual(artifact_schema["overall_status"], "healthy")
        self.assertEqual(artifact_schema["summary_missing_fields"], [])

    def test_build_runtime_contract_reports_degraded_artifact_schema_for_missing_summary_nested_field(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-22T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "runtime_contract_artifact_schema": {
                                    "contract_version": "phase-f-runtime-contract-artifact-schema-v1",
                                    "overall_status": "degraded",
                                    "summary_required_fields": [
                                        "subagent_lane_query_detail_coverage.detail_smoke",
                                    ],
                                    "summary_missing_fields": [
                                        "subagent_lane_query_detail_coverage.detail_smoke",
                                    ],
                                },
                                "contract_checks": [
                                    {"name": "embedded_sdk_event_payloads", "ok": True},
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        artifact_schema = contract["runtime_contract_artifact_schema"]
        self.assertEqual(artifact_schema["overall_status"], "degraded")
        self.assertEqual(
            artifact_schema["summary_missing_fields"],
            ["subagent_lane_query_detail_coverage.detail_smoke"],
        )

    def test_build_runtime_contract_ignores_non_list_steps_and_contract_checks(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-22T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "contract_checks": 1,
                            },
                            {
                                "name": "Quality gate smoke retry",
                                "runtime_contract_summary": {
                                    "overall_status": "healthy",
                                    "check_count": 1,
                                },
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        self.assertTrue(contract["available"])
        self.assertEqual(contract["overall_status"], "unknown")
        self.assertEqual(contract["failure_reason"], "contract_checks_missing")
        self.assertEqual(contract["check_count"], 0)
        self.assertEqual(contract["runtime_contract_summary"]["overall_status"], "unknown")

        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-22T00:00:00Z",
                        "steps": 1,
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        self.assertTrue(contract["available"])
        self.assertEqual(contract["overall_status"], "unknown")
        self.assertEqual(contract["failure_reason"], "contract_checks_missing")
        self.assertEqual(contract["check_count"], 0)
        self.assertEqual(contract["runtime_contract_summary"]["overall_status"], "unknown")

    def test_build_runtime_contract_ignores_non_list_observed_status_kinds(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-22T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "runtime_contract_summary": {
                                    "overall_status": "healthy",
                                    "check_count": 1,
                                    "failed_check_count": 0,
                                    "missing_payload_count": 0,
                                    "approval_replay_coverage": {
                                        "event_payload_sample": True,
                                        "observed_status_kinds": "approval_replayed",
                                    },
                                },
                                "contract_checks": [
                                    {
                                        "name": "embedded_sdk_event_payloads",
                                        "ok": True,
                                        "missing_payload_count": 0,
                                        "observed_status_kinds": 1,
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        self.assertEqual(contract["overall_status"], "healthy")
        self.assertEqual(contract["checks"][0]["observed_status_kinds"], [])
        self.assertEqual(
            contract["runtime_contract_summary"]["approval_replay_coverage"]["observed_status_kinds"],
            [],
        )

    def test_build_runtime_contract_treats_string_false_approval_replay_coverage_as_missing(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-22T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "runtime_contract_summary": {
                                    "overall_status": "healthy",
                                    "check_count": 1,
                                    "failed_check_count": 0,
                                    "missing_payload_count": 0,
                                    "approval_replay_coverage": {
                                        "event_payload_sample": "false",
                                        "observed_status_kinds": ["approval_replayed"],
                                    },
                                },
                                "contract_checks": [
                                    {
                                        "name": "embedded_sdk_event_payloads",
                                        "ok": True,
                                        "missing_payload_count": 0,
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        self.assertEqual(contract["overall_status"], "healthy")
        self.assertFalse(
            contract["runtime_contract_summary"]["approval_replay_coverage"]["event_payload_sample"]
        )

    def test_build_runtime_contract_falls_back_when_summary_counts_are_invalid(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-21T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "runtime_contract_summary": {
                                    "overall_status": "healthy",
                                    "check_count": "n/a",
                                    "failed_check_count": "broken",
                                    "missing_payload_count": "unknown",
                                    "approval_replay_coverage": {
                                        "event_payload_sample": True,
                                        "observed_status_kinds": ["approval_replayed"],
                                    },
                                },
                                "contract_checks": [
                                    {"name": "runtime_profile_contract_snapshot", "ok": True},
                                    {
                                        "name": "embedded_sdk_event_payloads",
                                        "ok": False,
                                        "missing_payload_count": 2,
                                        "observed_status_kinds": ["approval_replayed"],
                                        "failure_reason": "sdk_event_payload_contract_incomplete",
                                    },
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        summary = contract["runtime_contract_summary"]
        self.assertEqual(contract["overall_status"], "degraded")
        self.assertEqual(summary["overall_status"], "degraded")
        self.assertEqual(summary["check_count"], 2)
        self.assertEqual(summary["failed_check_count"], 1)
        self.assertEqual(summary["missing_payload_count"], 2)

    def test_build_runtime_contract_ignores_invalid_check_payload_counts(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "quality-gate-report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-05-21T00:00:00Z",
                        "steps": [
                            {
                                "name": "Quality gate smoke",
                                "contract_checks": [
                                    {"name": "runtime_profile_contract_snapshot", "ok": True},
                                    {
                                        "name": "embedded_sdk_event_payloads",
                                        "ok": False,
                                        "missing_payload_count": "unknown",
                                        "checked_event_count": "n/a",
                                        "observed_status_kinds": ["approval_replayed"],
                                        "failure_reason": "sdk_event_payload_contract_incomplete",
                                    },
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            contract = RuntimeContractGateService(report_path=report_path).build_runtime_contract()

        summary = contract["runtime_contract_summary"]
        payload_check = contract["checks"][1]
        self.assertEqual(contract["overall_status"], "degraded")
        self.assertEqual(summary["missing_payload_count"], 0)
        self.assertIsNone(payload_check["missing_payload_count"])
        self.assertIsNone(payload_check["checked_event_count"])


if __name__ == "__main__":
    unittest.main()
