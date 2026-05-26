import io
import json
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from backend.scripts import runtime_contract_smoke


class _StubResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class _StubTestClient:
    def __init__(self, _app):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, path):
        self.calls.append(("GET", path, None))
        if path == "/api/runtime-profile":
            return _StubResponse(
                200,
                {
                    "contract_snapshot": {
                        "overall_status": "healthy",
                        "contracts": [
                            {
                                "contract_name": "command_contract",
                                "stable_fields": ["embedded_sdk", "embedded_sdk.event_status_kinds"],
                                "missing_fields": [],
                            }
                        ],
                    },
                    "adapter_health": {"overall_status": "healthy"},
                    "runtime_contract_gate": {
                        "runtime_contract_artifact_schema": {
                            "contract_version": "phase-f-runtime-contract-artifact-schema-v1",
                            "overall_status": "healthy",
                            "summary_required_fields": [
                                "overall_status",
                                "subagent_lane_query_detail_coverage.detail_smoke",
                            ],
                            "summary_missing_fields": [],
                        }
                    },
                    "child_executor_promotion_gate": {
                        "contract_version": "phase-ii-child-executor-gate-v1",
                        "gate_status": "blocked",
                        "allowed": False,
                        "failure_reason": "child_executor_preflight_blocked",
                        "executor_path": "",
                        "recommended_next_step": "keep_relationship_only",
                        "blockers": ["child_context_budget_missing", "worker_runtime_backend_missing"],
                        "child_executor_execution_prerequisites": {
                            "contract_version": "phase-ii-child-executor-execution-prerequisites-v1",
                            "overall_status": "blocked",
                            "ready": False,
                            "requirements": [
                                {
                                    "requirement": "child_context_budget_defined",
                                    "status": "blocked",
                                    "blocker": "child_context_budget_defined",
                                }
                            ],
                            "missing_requirements": ["child_context_budget_defined"],
                        },
                    },
                    "child_executor_dispatch_contract": {
                        "contract_version": "phase-ii-child-executor-dispatch-v1",
                        "overall_status": "blocked",
                        "dispatch_ready": False,
                        "will_dispatch": False,
                        "backend_dispatch_ready": False,
                        "relationship_seam_preserved": True,
                        "blockers": ["worker_backend_dispatch_ready"],
                        "recommended_next_step": "implement_child_executor_backend_dispatch",
                    },
                },
            )
        if path.startswith("/api/runtime-profile/subagent-lane-query-detail"):
            return _StubResponse(
                200,
                {
                    "contract_version": "phase-h-subagent-lane-query-detail-v1",
                    "channel": "subagent_lane",
                    "recording_state": "recorded",
                    "query_id": "frontend-child-p10-i23-c1",
                    "stage_chain": ["planning", "final_output"],
                    "recent_events": [
                        {"stage": "planning", "summary": "frontend 子智能体开始规划"},
                        {"stage": "final_output", "summary": "已合并 frontend 子智能体结果到主响应"},
                    ],
                    "latest_stage": "final_output",
                    "latest_summary": "已合并 frontend 子智能体结果到主响应",
                    "stage_count": 2,
                    "recent_event_count": 2,
                    "reason": "",
                },
            )
        raise AssertionError(f"unexpected GET path: {path}")

    def post(self, path, json=None):
        self.calls.append(("POST", path, json))
        if path == "/api/runtime-framework-adapters/pilot-run":
            return _StubResponse(
                200,
                {
                    "adapter_id": "local_fake_framework",
                    "events": [
                        {"type": "status"},
                        {"type": "reasoning"},
                        {"type": "content"},
                    ],
                    "final_output": "Local fake adapter processed: 生成巡检计划",
                },
            )
        raise AssertionError(f"unexpected POST path: {path}")


class RuntimeContractSmokeTests(unittest.TestCase):
    def test_embedded_sdk_event_sample_includes_resolved_approval_replay_events(self):
        events = runtime_contract_smoke._build_embedded_sdk_event_sample()
        status_kinds = {str(event.get("status_kind") or "") for event in events}

        self.assertIn("approval_replayed", status_kinds)
        self.assertIn("approval_ignored", status_kinds)

        validation = runtime_contract_smoke.validate_embedded_sdk_event_payloads(events)
        self.assertTrue(validation["valid"])
        replay_events = [
            event
            for event in events
            if event.get("status_kind") in {"approval_replayed", "approval_ignored"}
        ]
        self.assertEqual(
            {event["approval_submission"]["status"] for event in replay_events},
            {"replayed", "ignored"},
        )

    def test_runtime_approved_tool_execution_bridge_check_covers_ask_and_deny_paths(self):
        result = runtime_contract_smoke._run_runtime_approved_tool_execution_bridge_check()

        self.assertTrue(result["ok"])
        self.assertEqual(result["ask_approval_status"], "pending")
        self.assertEqual(result["approved_tool_call_count"], 1)
        self.assertEqual(result["approved_policy_status"], "allowed")
        self.assertEqual(result["approved_policy_original_status"], "approval_required")
        self.assertEqual(result["approved_policy_override_status"], "approved")
        self.assertEqual(result["deny_override_status"], "policy_denied")
        self.assertEqual(result["deny_tool_call_count"], 0)

    def test_embedded_sdk_persistence_posture_check_covers_memory_durable_and_degraded(self):
        result = runtime_contract_smoke._run_embedded_sdk_persistence_posture_check()

        self.assertTrue(result["ok"])
        self.assertEqual(result["contract_version"], "phase-ii-embedded-sdk-persistence-interface-v1")
        self.assertEqual(result["memory_posture"], "memory_preview")
        self.assertEqual(result["durable_posture"], "durable_ready")
        self.assertEqual(result["degraded_posture"], "durable_degraded")
        self.assertTrue(result["durable_cross_process_candidate"])
        self.assertEqual(result["memory_cross_process_block_reason"], "workspace_backend_not_durable")
        self.assertEqual(result["degraded_cross_process_block_reason"], "workspace_backend_fallback_active")
        self.assertEqual(
            result["production_recovery_gate_contract_version"],
            "phase-ii-durable-workspace-production-recovery-gate-v1",
        )
        self.assertEqual(result["production_recovery_gate_status"], "blocked")
        self.assertNotIn(
            "descriptor_lifecycle_governance",
            result["production_recovery_gate_missing_sections"],
        )
        self.assertNotIn(
            "loader_execution_handoff_policy",
            result["production_recovery_gate_missing_sections"],
        )
        self.assertNotIn(
            "recovery_audit_operation_history",
            result["production_recovery_gate_missing_sections"],
        )
        self.assertNotIn(
            "registry_binding_resolution",
            result["production_recovery_gate_missing_sections"],
        )
        self.assertNotIn(
            "checkpoint_resume_cursor_gate",
            result["production_recovery_gate_missing_sections"],
        )
        self.assertEqual(
            result["recovery_audit_contract_version"],
            "phase-ii-recovery-audit-production-gate-v1",
        )
        self.assertTrue(result["recovery_audit_ready"])
        self.assertTrue(result["recovery_audit_operation_history_supported"])
        self.assertTrue(result["recovery_audit_summary_supported"])
        self.assertTrue(result["recovery_audit_timeline_writer_available"])
        self.assertTrue(result["recovery_audit_idempotent_trace_dedupe"])
        self.assertFalse(result["recovery_audit_authorization_source"])
        self.assertEqual(
            result["registry_checkpoint_policy_contract_version"],
            "phase-ii-production-recovery-registry-checkpoint-policy-v1",
        )
        self.assertTrue(result["registry_checkpoint_policy_ready"])
        self.assertTrue(result["registry_binding_policy_ready"])
        self.assertTrue(result["checkpoint_resume_cursor_policy_ready"])
        self.assertFalse(result["registry_checkpoint_policy_authorization_source"])
        self.assertFalse(result["production_recovery_default_enabled"])

    def test_worker_ownership_store_mode_check_covers_default_strict_and_fallback_modes(self):
        result = runtime_contract_smoke._run_worker_ownership_store_mode_contract_check()

        self.assertTrue(result["ok"])
        self.assertEqual(result["default_mode"], "memory_only")
        self.assertEqual(result["default_mode_source"], "default")
        self.assertEqual(result["default_adapter_kind"], "in_memory")
        self.assertFalse(result["default_durable"])
        self.assertEqual(
            result["operational_readiness_contract_version"],
            "phase-ii-worker-ownership-operations-v1",
        )
        self.assertEqual(result["default_operational_readiness_status"], "preview_or_degraded")
        self.assertFalse(result["default_operational_production_ready"])
        self.assertEqual(result["auto_claim_mode_default"], "descriptor_evidence_only")
        self.assertEqual(
            result["production_gate_contract_version"],
            "phase-ii-worker-ownership-production-gate-v1",
        )
        self.assertEqual(result["production_gate_status"], "blocked")
        self.assertIn("vendor_lock_semantics", result["production_gate_missing_sections"])
        self.assertIn("heartbeat_renewal_supervisor", result["production_gate_missing_sections"])
        self.assertFalse(result["production_default_enabled"])
        self.assertEqual(
            result["vendor_lock_contract_version"],
            "phase-ii-worker-ownership-vendor-lock-semantics-v1",
        )
        self.assertEqual(result["vendor_lock_status"], "blocked")
        self.assertEqual(result["vendor_lock_current_posture"], "sql_row_lease_fencing")
        self.assertTrue(result["vendor_lock_sql_row_lease_fencing"])
        self.assertFalse(result["vendor_lock_sql_row_lease_is_vendor_lock"])
        self.assertFalse(result["vendor_lock_adapter_present"])
        self.assertEqual(
            result["vendor_lock_adapter_contract_version"],
            "phase-ii-worker-ownership-vendor-lock-adapter-v1",
        )
        self.assertEqual(result["vendor_lock_adapter_status"], "blocked")
        self.assertEqual(result["vendor_lock_adapter_kind"], "")
        self.assertEqual(result["vendor_lock_adapter_target_backend"], "")
        self.assertFalse(result["vendor_lock_adapter_acquire_supported"])
        self.assertFalse(result["vendor_lock_adapter_renew_supported"])
        self.assertFalse(result["vendor_lock_adapter_release_supported"])
        self.assertFalse(result["vendor_lock_adapter_probe_supported"])
        self.assertFalse(result["vendor_lock_adapter_production_allowed"])
        self.assertFalse(result["vendor_lock_adapter_sql_row_lease_is_vendor_lock"])
        self.assertIn("adapter_kind", result["vendor_lock_adapter_missing_sections"])
        self.assertIn("target_backend", result["vendor_lock_adapter_missing_sections"])
        self.assertEqual(
            result["postgres_probe_contract_version"],
            "phase-ii-worker-ownership-postgres-vendor-lock-probe-v1",
        )
        self.assertEqual(result["postgres_probe_status"], "blocked")
        self.assertFalse(result["postgres_probe_executes"])
        self.assertFalse(result["postgres_probe_sql_row_lease_is_vendor_lock"])
        self.assertIn("advisory_lock_family", result["postgres_probe_missing_sections"])
        self.assertEqual(result["postgres_probe_ready_status"], "ready")
        self.assertFalse(result["postgres_probe_ready_executes"])
        self.assertEqual(
            result["postgres_execution_seam_contract_version"],
            "phase-ii-worker-ownership-postgres-advisory-lock-execution-seam-v1",
        )
        self.assertEqual(result["postgres_execution_default_status"], "blocked")
        self.assertFalse(result["postgres_execution_default_executor_bound"])
        self.assertFalse(result["postgres_execution_default_enabled_by_default"])
        self.assertFalse(result["postgres_execution_default_production_allowed"])
        self.assertIn("executor_binding", result["postgres_execution_default_missing_sections"])
        self.assertEqual(result["postgres_execution_default_probe_status"], "blocked")
        self.assertFalse(result["postgres_execution_default_probe_executed"])
        self.assertEqual(result["postgres_execution_opt_in_status"], "ready")
        self.assertTrue(result["postgres_execution_opt_in_executor_bound"])
        self.assertFalse(result["postgres_execution_opt_in_enabled_by_default"])
        self.assertFalse(result["postgres_execution_opt_in_production_allowed"])
        self.assertEqual(result["postgres_execution_opt_in_probe_status"], "ready")
        self.assertTrue(result["postgres_execution_opt_in_probe_executed"])
        self.assertEqual(result["postgres_execution_opt_in_acquire_status"], "acquired")
        self.assertTrue(result["postgres_execution_opt_in_acquire_executed"])
        self.assertTrue(result["postgres_execution_opt_in_acquired"])
        self.assertEqual(result["postgres_execution_opt_in_envelope_count"], 2)
        self.assertEqual(
            result["postgres_rollout_consumer_contract_version"],
            "phase-ii-worker-ownership-postgres-rollout-artifact-consumer-v1",
        )
        self.assertEqual(result["postgres_rollout_consumer_default_status"], "blocked")
        self.assertIn(
            "source_kind",
            result["postgres_rollout_consumer_default_missing_sections"],
        )
        self.assertIn(
            "postgres_execution_seam",
            result["postgres_rollout_consumer_default_missing_sections"],
        )
        self.assertFalse(result["postgres_rollout_consumer_default_will_enable_default"])
        self.assertFalse(result["postgres_rollout_consumer_default_executes_lock"])
        self.assertEqual(result["postgres_rollout_consumer_ready_status"], "ready")
        self.assertEqual(result["postgres_rollout_consumer_ready_target_backend"], "postgres")
        self.assertEqual(
            result["postgres_rollout_consumer_ready_lock_adapter_kind"],
            "postgres_advisory_lock",
        )
        self.assertFalse(result["postgres_rollout_consumer_ready_will_enable_default"])
        self.assertFalse(result["postgres_rollout_consumer_ready_executes_lock"])
        self.assertEqual(result["postgres_rollout_consumer_input_source_status"], "ready")
        self.assertTrue(result["postgres_rollout_consumer_input_source_ready"])
        self.assertEqual(
            result["postgres_rollout_consumer_input_source_kind"],
            "rollout_artifact",
        )
        self.assertEqual(
            result["postgres_target_binding_contract_version"],
            "phase-ii-worker-ownership-postgres-vendor-lock-target-artifact-binding-v1",
        )
        self.assertEqual(result["postgres_target_binding_default_status"], "blocked")
        self.assertIn(
            "source_kind",
            result["postgres_target_binding_default_missing_sections"],
        )
        self.assertIn(
            "postgres_rollout_consumer",
            result["postgres_target_binding_default_missing_sections"],
        )
        self.assertFalse(result["postgres_target_binding_default_will_enable_lock"])
        self.assertFalse(result["postgres_target_binding_default_executes_lock"])
        self.assertEqual(result["postgres_target_binding_ready_status"], "ready")
        self.assertEqual(result["postgres_target_binding_ready_target_backend"], "postgres")
        self.assertEqual(
            result["postgres_target_binding_ready_lock_adapter_kind"],
            "postgres_advisory_lock",
        )
        self.assertFalse(result["postgres_target_binding_ready_will_enable_lock"])
        self.assertFalse(result["postgres_target_binding_ready_executes_lock"])
        self.assertEqual(result["postgres_target_binding_target_input_status"], "ready")
        self.assertEqual(result["postgres_target_binding_target_decision_status"], "ready")
        self.assertTrue(
            result["postgres_target_binding_target_decision_production_allowed"]
        )
        self.assertEqual(
            result["postgres_semantics_binding_contract_version"],
            "phase-ii-worker-ownership-postgres-vendor-lock-semantics-binding-v1",
        )
        self.assertEqual(result["postgres_semantics_binding_default_status"], "blocked")
        self.assertIn(
            "target_artifact_binding",
            result["postgres_semantics_binding_default_missing_sections"],
        )
        self.assertIn(
            "postgres_execution_seam",
            result["postgres_semantics_binding_default_missing_sections"],
        )
        self.assertFalse(result["postgres_semantics_binding_default_will_enable_lock"])
        self.assertFalse(result["postgres_semantics_binding_default_will_update_gate"])
        self.assertFalse(result["postgres_semantics_binding_default_executes_lock"])
        self.assertEqual(result["postgres_semantics_binding_ready_status"], "ready")
        self.assertEqual(
            result["postgres_semantics_binding_ready_target_backend"],
            "postgres",
        )
        self.assertEqual(
            result["postgres_semantics_binding_ready_lock_adapter_kind"],
            "postgres_advisory_lock",
        )
        self.assertEqual(result["postgres_semantics_binding_ready_probe_status"], "ready")
        self.assertEqual(result["postgres_semantics_binding_ready_adapter_status"], "ready")
        self.assertEqual(result["postgres_semantics_binding_ready_semantics_status"], "ready")
        self.assertFalse(result["postgres_semantics_binding_ready_will_enable_lock"])
        self.assertFalse(result["postgres_semantics_binding_ready_will_update_gate"])
        self.assertFalse(result["postgres_semantics_binding_ready_executes_lock"])
        self.assertEqual(
            result["postgres_wiring_decision_contract_version"],
            (
                "phase-ii-worker-ownership-postgres-vendor-lock-production-gate"
                "-wiring-decision-v1"
            ),
        )
        self.assertEqual(result["postgres_wiring_decision_default_status"], "blocked")
        self.assertIn(
            "semantics_binding",
            result["postgres_wiring_decision_default_missing_sections"],
        )
        self.assertIn(
            "decision_recorded",
            result["postgres_wiring_decision_default_missing_sections"],
        )
        self.assertFalse(result["postgres_wiring_decision_default_wiring_allowed"])
        self.assertFalse(result["postgres_wiring_decision_default_will_update_gate"])
        self.assertFalse(result["postgres_wiring_decision_default_will_enable_lock"])
        self.assertFalse(result["postgres_wiring_decision_default_executes_lock"])
        self.assertEqual(result["postgres_wiring_decision_ready_status"], "ready")
        self.assertEqual(
            result["postgres_wiring_decision_ready_semantics_binding_status"],
            "ready",
        )
        self.assertEqual(result["postgres_wiring_decision_ready_candidate_status"], "ready")
        self.assertTrue(result["postgres_wiring_decision_ready_wiring_allowed"])
        self.assertEqual(result["postgres_wiring_decision_ready_target_backend"], "postgres")
        self.assertEqual(
            result["postgres_wiring_decision_ready_lock_adapter_kind"],
            "postgres_advisory_lock",
        )
        self.assertFalse(result["postgres_wiring_decision_ready_will_update_gate"])
        self.assertFalse(result["postgres_wiring_decision_ready_will_enable_lock"])
        self.assertFalse(result["postgres_wiring_decision_ready_executes_lock"])
        self.assertEqual(
            result["production_dry_run_contract_version"],
            "phase-ii-worker-ownership-production-gate-composition-dry-run-v1",
        )
        self.assertEqual(result["production_dry_run_default_status"], "blocked")
        self.assertIn(
            "vendor_lock_wiring_decision",
            result["production_dry_run_default_missing_sections"],
        )
        self.assertIn(
            "heartbeat_renewal_supervisor",
            result["production_dry_run_default_missing_sections"],
        )
        self.assertIn(
            "rollout_confirmation",
            result["production_dry_run_default_missing_sections"],
        )
        self.assertIn(
            "recovery_entry_auto_claim_enablement",
            result["production_dry_run_default_missing_sections"],
        )
        self.assertIn(
            "ownership_audit_evidence",
            result["production_dry_run_default_missing_sections"],
        )
        self.assertIn(
            "production_default_enablement_input_source",
            result["production_dry_run_default_missing_sections"],
        )
        self.assertFalse(result["production_dry_run_default_all_required_ready"])
        self.assertFalse(result["production_dry_run_default_would_allow"])
        self.assertFalse(result["production_dry_run_default_will_enable"])
        self.assertFalse(result["production_dry_run_default_executes_lock"])
        self.assertFalse(result["production_dry_run_default_starts_worker"])
        self.assertFalse(result["production_dry_run_default_runs_auto_claim"])
        self.assertEqual(result["production_dry_run_ready_status"], "ready")
        self.assertEqual(result["production_dry_run_ready_missing_sections"], [])
        self.assertTrue(result["production_dry_run_ready_all_required_ready"])
        self.assertTrue(result["production_dry_run_ready_would_allow"])
        self.assertFalse(result["production_dry_run_ready_will_enable"])
        self.assertFalse(result["production_dry_run_ready_executes_lock"])
        self.assertFalse(result["production_dry_run_ready_starts_worker"])
        self.assertFalse(result["production_dry_run_ready_runs_auto_claim"])
        self.assertFalse(result["vendor_lock_scope_defined"])
        self.assertFalse(result["vendor_lock_fencing_guarantee_defined"])
        self.assertFalse(result["vendor_lock_failover_semantics_defined"])
        self.assertFalse(result["vendor_lock_ttl_renewal_semantics_defined"])
        self.assertFalse(result["vendor_lock_stale_owner_cleanup_defined"])
        self.assertFalse(result["vendor_lock_production_allowed"])
        self.assertIn("vendor_lock_adapter", result["vendor_lock_missing_sections"])
        self.assertIn("target_decision", result["vendor_lock_missing_sections"])
        self.assertEqual(
            result["vendor_lock_target_decision_contract_version"],
            "phase-ii-worker-ownership-vendor-lock-target-decision-v1",
        )
        self.assertEqual(result["vendor_lock_target_decision_status"], "blocked")
        self.assertFalse(result["vendor_lock_target_decision_recorded"])
        self.assertEqual(result["vendor_lock_target_backend"], "")
        self.assertEqual(result["vendor_lock_target_adapter_kind"], "")
        self.assertEqual(result["vendor_lock_target_scope"], "")
        self.assertEqual(result["vendor_lock_target_fencing_strategy"], "")
        self.assertEqual(result["vendor_lock_target_ttl_renewal_strategy"], "")
        self.assertEqual(result["vendor_lock_target_failover_strategy"], "")
        self.assertEqual(result["vendor_lock_target_stale_cleanup_strategy"], "")
        self.assertEqual(
            result["vendor_lock_target_input_contract_version"],
            "phase-ii-worker-ownership-vendor-lock-target-decision-input-v1",
        )
        self.assertEqual(result["vendor_lock_target_input_source_status"], "blocked")
        self.assertEqual(result["vendor_lock_target_input_source_kind"], "")
        self.assertEqual(result["vendor_lock_target_input_decision_id"], "")
        self.assertEqual(result["vendor_lock_target_input_backend"], "")
        self.assertEqual(result["vendor_lock_target_input_adapter_kind"], "")
        self.assertIn(
            "input_source_kind",
            result["vendor_lock_target_input_missing_sections"],
        )
        self.assertFalse(result["vendor_lock_target_input_sql_row_lease_is_vendor_lock"])
        self.assertIn("decision_recorded", result["vendor_lock_target_missing_sections"])
        self.assertIn("input_source", result["vendor_lock_target_missing_sections"])
        self.assertIn("target_backend", result["vendor_lock_target_missing_sections"])
        self.assertFalse(result["vendor_lock_target_sql_row_lease_is_vendor_lock"])
        self.assertFalse(result["vendor_lock_target_production_allowed"])
        self.assertEqual(
            result["renewal_supervisor_contract_version"],
            "phase-ii-worker-ownership-renewal-supervisor-v1",
        )
        self.assertEqual(result["renewal_supervisor_status"], "blocked")
        self.assertFalse(result["renewal_supervisor_enabled_by_default"])
        self.assertTrue(result["renewal_supervisor_renew_once_supported"])
        self.assertTrue(result["renewal_supervisor_owner_identity_required"])
        self.assertTrue(result["renewal_supervisor_ttl_interval_policy_ready"])
        self.assertTrue(result["renewal_supervisor_controlled_lifecycle_supported"])
        self.assertFalse(result["renewal_supervisor_starts_by_default"])
        self.assertFalse(result["renewal_supervisor_active"])
        self.assertEqual(result["renewal_supervisor_last_renewal_status"], "")
        self.assertTrue(result["renewal_supervisor_stop_supported"])
        self.assertTrue(result["renewal_supervisor_failure_fail_closed"])
        self.assertTrue(result["renewal_supervisor_lease_loss_fail_closed"])
        self.assertEqual(result["renewal_supervisor_renew_once_status"], "renewed")
        self.assertFalse(result["renewal_supervisor_renew_once_background_started"])
        self.assertEqual(result["renewal_supervisor_stale_fencing_status"], "blocked")
        self.assertEqual(
            result["renewal_supervisor_stale_fencing_reason"],
            "stale_worker_fencing_token",
        )
        self.assertFalse(result["renewal_supervisor_lifecycle_initial_active"])
        self.assertTrue(result["renewal_supervisor_lifecycle_started_active"])
        self.assertEqual(result["renewal_supervisor_lifecycle_started_status"], "renewed")
        self.assertGreaterEqual(result["renewal_supervisor_lifecycle_started_count"], 1)
        self.assertFalse(result["renewal_supervisor_lifecycle_stopped_active"])
        self.assertGreaterEqual(result["renewal_supervisor_lifecycle_stopped_count"], 1)
        self.assertIn("background_supervisor", result["renewal_supervisor_missing_sections"])
        self.assertEqual(
            result["rollout_readiness_contract_version"],
            "phase-ii-worker-ownership-rollout-readiness-v1",
        )
        self.assertEqual(result["rollout_readiness_status"], "blocked")
        self.assertFalse(result["production_rollout_confirmed"])
        self.assertTrue(result["rollout_migration_ready"])
        self.assertTrue(result["rollout_stale_fencing_verified"])
        self.assertFalse(result["rollout_rollback_plan_ready"])
        self.assertEqual(result["rollout_operationalization_status"], "blocked")
        self.assertEqual(result["rollout_mode"], "readiness_only")
        self.assertIn("rollback_plan", result["rollout_missing_artifacts"])
        self.assertIn("rollout_confirmation_decision", result["rollout_missing_artifacts"])
        self.assertEqual(result["rollout_rollback_plan_status"], "missing")
        self.assertEqual(result["rollout_fallback_policy_status"], "missing")
        self.assertEqual(
            result["rollout_renewal_lifecycle_verification_status"],
            "missing",
        )
        self.assertEqual(result["rollout_auto_claim_decision_status"], "missing")
        self.assertEqual(
            result["rollout_confirmation_decision_contract_version"],
            "phase-ii-worker-ownership-rollout-confirmation-decision-v1",
        )
        self.assertEqual(result["rollout_confirmation_decision_status"], "blocked")
        self.assertFalse(result["rollout_decision_recorded"])
        self.assertEqual(result["rollout_target_store_mode"], "")
        self.assertIn("decision_recorded", result["rollout_confirmation_missing_sections"])
        self.assertFalse(result["rollout_confirmation_production_rollout_confirmed"])
        self.assertEqual(
            result["rollout_confirmation_input_contract_version"],
            "phase-ii-worker-ownership-rollout-confirmation-input-source-v1",
        )
        self.assertEqual(result["rollout_confirmation_input_source_status"], "blocked")
        self.assertEqual(result["rollout_confirmation_input_source_kind"], "")
        self.assertEqual(result["rollout_confirmation_input_decision_id"], "")
        self.assertEqual(result["rollout_confirmation_input_target_store_mode"], "")
        self.assertIn("input_source_kind", result["rollout_confirmation_input_missing_sections"])
        self.assertIn("decision_id", result["rollout_confirmation_input_missing_sections"])
        self.assertFalse(result["rollout_confirmation_input_sql_row_lease_is_authority"])
        self.assertIn("strict_mode_rollout", result["rollout_missing_sections"])
        self.assertEqual(
            result["auto_claim_policy_contract_version"],
            "phase-ii-worker-ownership-auto-claim-policy-v1",
        )
        self.assertEqual(result["auto_claim_policy_status"], "blocked")
        self.assertFalse(result["auto_claim_enabled_by_default"])
        self.assertTrue(result["auto_claim_descriptor_evidence_fallback"])
        self.assertTrue(result["auto_claim_lease_validation_required"])
        self.assertTrue(result["auto_claim_entrypoint_allowlist_ready"])
        self.assertEqual(
            result["auto_claim_entrypoint_allowlist_contract_version"],
            "phase-ii-worker-ownership-auto-claim-entrypoint-allowlist-v1",
        )
        self.assertEqual(result["auto_claim_entrypoint_allowlist_status"], "ready")
        self.assertIn("submit_approval.approved", result["auto_claim_allowed_entrypoints"])
        self.assertIn("resume_run.continue_loop", result["auto_claim_allowed_entrypoints"])
        self.assertEqual(result["auto_claim_missing_entrypoints"], [])
        self.assertFalse(result["auto_claim_default_auto_claim_enabled"])
        self.assertTrue(result["auto_claim_requires_production_gate_ready"])
        self.assertEqual(
            result["auto_claim_enablement_gate_contract_version"],
            "phase-ii-worker-ownership-explicit-auto-claim-enablement-gate-v1",
        )
        self.assertEqual(result["auto_claim_enablement_gate_status"], "blocked")
        self.assertFalse(result["auto_claim_will_auto_claim"])
        self.assertEqual(result["auto_claim_requested_entrypoint"], "submit_approval.approved")
        self.assertIn(
            "explicit_runtime_configuration",
            result["auto_claim_enablement_missing_sections"],
        )
        self.assertEqual(
            result["auto_claim_enablement_blocked_reason"],
            "explicit_runtime_configuration_missing",
        )
        self.assertIn("explicit_runtime_configuration", result["auto_claim_missing_sections"])
        self.assertEqual(
            result["ownership_audit_contract_version"],
            "phase-ii-worker-ownership-audit-evidence-v1",
        )
        self.assertEqual(result["ownership_audit_status"], "blocked")
        self.assertTrue(result["ownership_audit_compact_evidence"])
        self.assertFalse(result["ownership_audit_operation_history_ready"])
        self.assertFalse(result["ownership_audit_recovery_operation_link_ready"])
        self.assertFalse(result["ownership_audit_timeline_writer_ready"])
        self.assertFalse(result["ownership_audit_idempotent_dedupe_ready"])
        self.assertFalse(result["ownership_audit_authorization_source"])
        self.assertIn("operation_history", result["ownership_audit_missing_sections"])
        self.assertEqual(
            result["enablement_strategy_contract_version"],
            "phase-ii-worker-ownership-production-enablement-strategy-v1",
        )
        self.assertEqual(result["enablement_strategy_status"], "blocked")
        self.assertFalse(result["production_default_enabled_requested"])
        self.assertFalse(result["production_default_allowed"])
        self.assertEqual(
            result["enablement_input_source_contract_version"],
            "phase-ii-worker-ownership-production-default-enablement-input-source-v1",
        )
        self.assertEqual(result["enablement_input_source_status"], "blocked")
        self.assertEqual(result["enablement_input_source_kind"], "")
        self.assertEqual(result["enablement_rollout_artifact"], "")
        self.assertFalse(result["enablement_input_source_ready"])
        self.assertIn("input_source_kind", result["enablement_input_source_missing_sections"])
        self.assertTrue(result["enablement_explicit_required"])
        self.assertFalse(result["enablement_all_required_sections_ready"])
        self.assertTrue(result["enablement_fail_closed_when_blocked"])
        self.assertTrue(result["enablement_sql_row_lease_not_default_authority"])
        self.assertIn("vendor_lock_semantics", result["enablement_strategy_blocking_sections"])
        self.assertIn(
            "production_default_enablement_input_source",
            result["enablement_strategy_blocking_sections"],
        )
        self.assertEqual(result["default_production_gate_status"], "blocked")
        self.assertTrue(result["configurable_knob_present"])
        self.assertTrue(result["hot_reloadable_knob_present"])
        self.assertEqual(result["strict_mode_status"], "sqlalchemy_durable")
        self.assertEqual(result["strict_operational_readiness_status"], "production_ready")
        self.assertEqual(result["strict_vendor_lock_posture"], "sql_row_lease_fencing")
        self.assertTrue(result["strict_migration_ready"])
        self.assertEqual(result["fallback_mode_status"], "fallback_to_memory")
        self.assertEqual(result["fallback_operational_readiness_status"], "preview_or_degraded")
        self.assertTrue(result["fallback_active"])

    def test_durable_recovery_loader_check_covers_ready_missing_and_unsafe_paths(self):
        result = runtime_contract_smoke._run_durable_recovery_loader_contract_check()

        self.assertTrue(result["ok"])
        self.assertEqual(result["contract_version"], "phase-ii-durable-recovery-loader-v1")
        self.assertEqual(result["loader_status"], "ready")
        self.assertTrue(result["loader_ready"])
        self.assertEqual(result["loader_recovery_reason"], "ready_via_registry")
        self.assertTrue(result["all_bindings_resolved"])
        self.assertEqual(result["missing_recovery_reason"], "run_snapshot_missing")
        self.assertEqual(result["unsafe_recovery_reason"], "descriptor_corrupted")
        self.assertFalse(result["executes_recovery"])
        self.assertFalse(result["deserializes_callables"])

    def test_recovery_retry_scheduler_check_covers_disabled_and_enabled_paths(self):
        result = runtime_contract_smoke._run_recovery_retry_scheduler_contract_check()

        self.assertTrue(result["ok"])
        self.assertEqual(result["contract_version"], "phase-ii-recovery-retry-scheduler-v1")
        self.assertEqual(result["default_status"], "disabled")
        self.assertTrue(result["default_eligible"])
        self.assertFalse(result["default_will_execute"])
        self.assertEqual(
            result["production_gate_contract_version"],
            "phase-ii-recovery-retry-production-scheduler-gate-v1",
        )
        self.assertEqual(result["production_gate_status"], "blocked")
        self.assertIn("durable_scheduling_state", result["production_gate_missing_sections"])
        self.assertEqual(
            result["production_gate_blocked_reason"],
            "production_scheduler_gate_blocked",
        )
        self.assertFalse(result["production_automatic_retry_enabled_by_default"])
        self.assertFalse(result["production_automatic_will_execute"])
        self.assertEqual(result["enabled_status"], "executed")
        self.assertTrue(result["enabled_will_execute"])
        self.assertEqual(result["latest_operation_status"], "recovered")
        self.assertEqual(result["attempt_number"], 1)
        self.assertTrue(result["previous_operation_id_present"])
        self.assertTrue(result["idempotency_key_present"])
        self.assertEqual(result["retry_status"], "retryable")
        self.assertEqual(result["recovery_reason"], "transient_workspace_unavailable")

    def test_child_executor_dispatcher_check_covers_default_blocked_and_enabled_paths(self):
        result = runtime_contract_smoke._run_child_executor_dispatcher_contract_check()

        self.assertTrue(result["ok"])
        self.assertEqual(result["contract_version"], "phase-ii-child-executor-dispatcher-v1")
        self.assertEqual(result["default_status"], "blocked")
        self.assertEqual(result["default_blocked_reason"], "dispatcher_disabled")
        self.assertFalse(result["default_will_dispatch"])
        self.assertEqual(result["blocked_reason"], "dispatch_contract_not_ready")
        self.assertFalse(result["blocked_will_dispatch"])
        self.assertEqual(result["enabled_status"], "dispatched")
        self.assertTrue(result["enabled_will_dispatch"])
        self.assertEqual(result["backend_result_status"], "completed")
        self.assertEqual(result["backend_invocation_count"], 1)

    def test_child_executor_sandbox_backend_check_covers_adapter_gate_paths(self):
        result = runtime_contract_smoke._run_child_executor_sandbox_backend_contract_check()

        self.assertTrue(result["ok"])
        self.assertEqual(
            result["contract_version"],
            "phase-ii-child-executor-sandbox-worker-backend-v1",
        )
        self.assertTrue(result["ready_adapter_contract"])
        self.assertTrue(result["ready_sandbox_guard"])
        self.assertTrue(result["ready_audit"])
        self.assertTrue(result["ready_idempotency"])
        self.assertTrue(result["missing_guard_fail_closed"])
        self.assertGreater(result["missing_guard_count"], 0)
        self.assertTrue(result["unsafe_payload_blocked"])
        self.assertEqual(result["unsafe_blocked_reason"], "sandbox_payload_unsafe")
        self.assertTrue(result["compact_attempt_valid"])
        self.assertEqual(result["dispatch_status"], "dispatched")
        self.assertEqual(result["backend_result_status"], "completed")
        self.assertEqual(result["backend_invocation_count"], 1)
        self.assertFalse(result["default_worker_enabled"])

    def test_sdk_tool_runtime_execution_bridge_check_covers_auto_ask_and_deny_paths(self):
        result = runtime_contract_smoke._run_sdk_tool_runtime_execution_bridge_check()

        self.assertTrue(result["ok"])
        self.assertEqual(result["auto_tool_call_count"], 1)
        self.assertEqual(result["auto_tool_history_count"], 1)
        self.assertEqual(result["ask_approval_status"], "pending")
        self.assertEqual(result["approved_tool_call_count"], 1)
        self.assertEqual(result["approved_policy_status"], "allowed")
        self.assertEqual(result["approved_policy_original_status"], "approval_required")
        self.assertEqual(result["approved_policy_override_status"], "approved")
        self.assertEqual(result["deny_override_status"], "policy_denied")
        self.assertEqual(result["deny_tool_call_count"], 0)

    def test_tool_runtime_timeout_retry_check_covers_retry_and_elapsed_timeout_metadata(self):
        result = runtime_contract_smoke._run_tool_runtime_timeout_retry_contract_check()

        self.assertTrue(result["ok"])
        self.assertEqual(result["retry_policy"], "sync_exception_retry")
        self.assertEqual(result["timeout_enforcement"], "post_call_elapsed_check")
        self.assertEqual(result["recovered_status"], "ok")
        self.assertEqual(result["recovered_retry_status"], "recovered")
        self.assertEqual(result["recovered_attempt_count"], 2)
        self.assertEqual(result["exhausted_status"], "error")
        self.assertEqual(result["exhausted_retry_status"], "exhausted")
        self.assertEqual(result["exhausted_attempt_count"], 2)
        self.assertEqual(result["timeout_status"], "timeout")
        self.assertEqual(result["timeout_metadata_status"], "exceeded")
        self.assertEqual(result["timeout_metadata_enforcement"], "post_call_elapsed_check")
        self.assertFalse(result["hard_cancellation_claimed"])
        self.assertFalse(result["sandbox_execution_claimed"])
        self.assertFalse(result["worker_timeout_claimed"])

    @patch("backend.scripts.runtime_contract_smoke.create_app")
    @patch("backend.scripts.runtime_contract_smoke._run_embedded_sdk_durable_recovery_check")
    @patch("backend.scripts.runtime_contract_smoke._run_recovery_retry_evidence_contract_check")
    @patch("backend.scripts.runtime_contract_smoke.TestClient", return_value=_StubTestClient(object()))
    def test_runtime_contract_smoke_returns_zero_when_checks_pass(
        self,
        _mock_client,
        mock_retry_check,
        mock_durable_check,
        _mock_app,
    ):
        mock_durable_check.return_value = {
            "ok": True,
            "backend_kind": "sqlalchemy",
            "backend_mode": "strict_sql",
            "fallback_active": False,
            "probe_recoverable": True,
            "tool_recovery_reason": "ready_via_registry",
            "loop_recovery_reason": "ready_via_registry",
            "resumed_state": "done",
            "approved_state": "observing",
            "failure_reason": "",
        }
        mock_retry_check.return_value = {
            "ok": True,
            "contract_version": "phase-ii-recovery-retry-protocol-v1",
            "attempt_number": 3,
            "max_attempts": 3,
            "retry_status": "exhausted",
            "retryable": True,
            "terminal": True,
            "recovery_reason": "workspace_backend_not_durable",
            "idempotency_key_present": True,
            "failure_reason": "",
        }
        output = io.StringIO()
        with redirect_stdout(output):
            code = runtime_contract_smoke.main()

        payload = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["checks"][0]["name"], "runtime_profile_contract_snapshot")
        self.assertEqual(payload["checks"][0]["runtime_contract_artifact_schema_status"], "healthy")
        self.assertEqual(payload["checks"][0]["runtime_contract_artifact_schema_missing_field_count"], 0)
        self.assertEqual(payload["checks"][0]["runtime_contract_artifact_schema_missing_fields"], [])
        self.assertEqual(payload["checks"][1]["name"], "framework_adapter_pilot_run")
        self.assertEqual(payload["checks"][2]["name"], "embedded_sdk_event_payloads")
        self.assertEqual(payload["checks"][3]["name"], "embedded_sdk_durable_recovery")
        self.assertEqual(payload["checks"][4]["name"], "durable_checkpoint_resume_cursor")
        checks_by_name = {check["name"]: check for check in payload["checks"]}
        self.assertIn("embedded_sdk_persistence_posture", checks_by_name)
        self.assertIn("runtime_surface_run_recovery", checks_by_name)
        self.assertIn("approval_lifecycle_recovery_alignment", checks_by_name)
        self.assertIn("runtime_approved_tool_execution_bridge", checks_by_name)
        self.assertIn("sdk_tool_runtime_execution_bridge", checks_by_name)
        self.assertIn("tool_runtime_timeout_retry", checks_by_name)
        self.assertIn("worker_ownership_store_mode", checks_by_name)
        self.assertIn("recovery_retry_evidence", checks_by_name)
        self.assertIn("recovery_retry_scheduler", checks_by_name)
        self.assertIn("durable_recovery_loader", checks_by_name)
        self.assertIn("child_executor_promotion_gate", checks_by_name)
        self.assertIn("child_executor_dispatch_contract", checks_by_name)
        self.assertIn("child_executor_dispatcher", checks_by_name)
        self.assertIn("subagent_lane_query_detail", checks_by_name)
        for check_name in (
            "embedded_sdk_event_payloads",
            "embedded_sdk_durable_recovery",
            "durable_checkpoint_resume_cursor",
            "embedded_sdk_persistence_posture",
            "worker_ownership_store_mode",
            "recovery_retry_evidence",
            "recovery_retry_scheduler",
            "durable_recovery_loader",
            "child_executor_promotion_gate",
            "child_executor_dispatch_contract",
            "child_executor_dispatcher",
            "runtime_surface_run_recovery",
            "approval_lifecycle_recovery_alignment",
            "runtime_approved_tool_execution_bridge",
            "sdk_tool_runtime_execution_bridge",
            "tool_runtime_timeout_retry",
            "subagent_lane_query_detail",
        ):
            self.assertTrue(checks_by_name[check_name]["ok"])
        self.assertGreaterEqual(checks_by_name["embedded_sdk_event_payloads"]["checked_event_count"], 1)
        self.assertIn("approval_replayed", checks_by_name["embedded_sdk_event_payloads"]["observed_status_kinds"])
        self.assertIn("approval_ignored", checks_by_name["embedded_sdk_event_payloads"]["observed_status_kinds"])
        self.assertEqual(
            checks_by_name["approval_lifecycle_recovery_alignment"]["replayed_submission_status"],
            "replayed",
        )
        self.assertEqual(
            checks_by_name["approval_lifecycle_recovery_alignment"]["ignored_submission_status"],
            "ignored",
        )
        self.assertEqual(
            checks_by_name["approval_lifecycle_recovery_alignment"]["resolved_recovery_reason"],
            "already_resolved",
        )
        self.assertEqual(checks_by_name["runtime_approved_tool_execution_bridge"]["approved_policy_override_status"], "approved")
        self.assertEqual(checks_by_name["sdk_tool_runtime_execution_bridge"]["approved_policy_override_status"], "approved")
        self.assertEqual(checks_by_name["tool_runtime_timeout_retry"]["recovered_retry_status"], "recovered")
        self.assertEqual(checks_by_name["tool_runtime_timeout_retry"]["exhausted_retry_status"], "exhausted")
        self.assertEqual(checks_by_name["tool_runtime_timeout_retry"]["timeout_metadata_status"], "exceeded")
        self.assertEqual(checks_by_name["worker_ownership_store_mode"]["default_mode"], "memory_only")
        self.assertEqual(checks_by_name["worker_ownership_store_mode"]["strict_mode_status"], "sqlalchemy_durable")
        self.assertEqual(
            checks_by_name["worker_ownership_store_mode"]["strict_operational_readiness_status"],
            "production_ready",
        )
        self.assertEqual(
            checks_by_name["worker_ownership_store_mode"]["strict_vendor_lock_posture"],
            "sql_row_lease_fencing",
        )
        self.assertEqual(checks_by_name["worker_ownership_store_mode"]["fallback_mode_status"], "fallback_to_memory")
        self.assertEqual(checks_by_name["recovery_retry_evidence"]["attempt_number"], 3)
        self.assertEqual(checks_by_name["recovery_retry_evidence"]["retry_status"], "exhausted")
        self.assertTrue(checks_by_name["recovery_retry_evidence"]["idempotency_key_present"])
        self.assertEqual(checks_by_name["recovery_retry_scheduler"]["default_status"], "disabled")
        self.assertEqual(checks_by_name["recovery_retry_scheduler"]["production_gate_status"], "blocked")
        self.assertFalse(checks_by_name["recovery_retry_scheduler"]["production_automatic_will_execute"])
        self.assertEqual(checks_by_name["recovery_retry_scheduler"]["enabled_status"], "executed")
        self.assertEqual(checks_by_name["durable_recovery_loader"]["loader_status"], "ready")
        self.assertIn("ready", checks_by_name["durable_recovery_loader"]["descriptor_lifecycle_states"])
        self.assertIn("bound", checks_by_name["durable_recovery_loader"]["descriptor_lifecycle_states"])
        self.assertIn("stale", checks_by_name["durable_recovery_loader"]["descriptor_lifecycle_states"])
        self.assertIn("unsafe", checks_by_name["durable_recovery_loader"]["descriptor_lifecycle_states"])
        self.assertEqual(
            checks_by_name["durable_recovery_loader"]["handoff_policy_contract_version"],
            "phase-ii-durable-loader-execution-handoff-policy-v1",
        )
        self.assertEqual(checks_by_name["durable_recovery_loader"]["default_handoff_status"], "blocked")
        self.assertEqual(
            checks_by_name["durable_recovery_loader"]["default_handoff_blocked_reason"],
            "explicit_handoff_required",
        )
        self.assertEqual(checks_by_name["durable_recovery_loader"]["explicit_handoff_status"], "blocked")
        self.assertEqual(
            checks_by_name["durable_recovery_loader"]["explicit_handoff_blocked_reason"],
            "recovery_executor_not_bound",
        )
        self.assertFalse(checks_by_name["durable_recovery_loader"]["explicit_handoff_will_execute"])
        self.assertEqual(checks_by_name["durable_recovery_loader"]["unsafe_recovery_reason"], "descriptor_corrupted")
        self.assertEqual(checks_by_name["child_executor_promotion_gate"]["gate_status"], "blocked")
        self.assertFalse(checks_by_name["child_executor_promotion_gate"]["allowed"])
        self.assertEqual(
            checks_by_name["child_executor_promotion_gate"]["gate_failure_reason"],
            "child_executor_preflight_blocked",
        )
        self.assertEqual(checks_by_name["child_executor_dispatch_contract"]["dispatch_status"], "blocked")
        self.assertFalse(checks_by_name["child_executor_dispatch_contract"]["dispatch_ready"])
        self.assertFalse(checks_by_name["child_executor_dispatch_contract"]["will_dispatch"])
        self.assertEqual(checks_by_name["child_executor_dispatcher"]["default_status"], "blocked")
        self.assertEqual(checks_by_name["child_executor_dispatcher"]["enabled_status"], "dispatched")
        self.assertIn(
            "worker_backend_dispatch_ready",
            checks_by_name["child_executor_dispatch_contract"]["dispatch_blockers"],
        )
        self.assertEqual(
            checks_by_name["subagent_lane_query_detail"]["contract_version"],
            "phase-h-subagent-lane-query-detail-v1",
        )
        self.assertEqual(checks_by_name["subagent_lane_query_detail"]["recording_state"], "recorded")
        self.assertEqual(checks_by_name["subagent_lane_query_detail"]["stage_count"], 2)
        self.assertEqual(checks_by_name["subagent_lane_query_detail"]["recent_event_count"], 2)

    @patch.dict(os.environ, {"ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER": "false"})
    @patch("backend.scripts.runtime_contract_smoke.create_app")
    @patch("backend.scripts.runtime_contract_smoke._run_embedded_sdk_durable_recovery_check")
    @patch("backend.scripts.runtime_contract_smoke._run_recovery_retry_evidence_contract_check")
    @patch("backend.scripts.runtime_contract_smoke.TestClient", return_value=_StubTestClient(object()))
    def test_runtime_contract_smoke_temporarily_enables_local_fake_adapter(
        self,
        _mock_client,
        mock_retry_check,
        mock_durable_check,
        mock_app,
    ):
        observed_fake_adapter_flags = []

        def _create_app(*_args, **_kwargs):
            observed_fake_adapter_flags.append(os.environ.get("ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER"))
            return object()

        mock_app.side_effect = _create_app
        mock_durable_check.return_value = {
            "ok": True,
            "backend_kind": "sqlalchemy",
            "backend_mode": "strict_sql",
            "fallback_active": False,
            "probe_recoverable": True,
            "tool_recovery_reason": "ready_via_registry",
            "loop_recovery_reason": "ready_via_registry",
            "resumed_state": "done",
            "approved_state": "observing",
            "failure_reason": "",
        }
        mock_retry_check.return_value = {
            "ok": True,
            "contract_version": "phase-ii-recovery-retry-protocol-v1",
            "attempt_number": 3,
            "max_attempts": 3,
            "retry_status": "exhausted",
            "retryable": True,
            "terminal": True,
            "recovery_reason": "workspace_backend_not_durable",
            "idempotency_key_present": True,
            "failure_reason": "",
        }

        output = io.StringIO()
        with redirect_stdout(output):
            code = runtime_contract_smoke.main()

        self.assertEqual(code, 0)
        self.assertEqual(observed_fake_adapter_flags, ["true"])
        self.assertEqual(os.environ.get("ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER"), "false")

    @patch("backend.scripts.runtime_contract_smoke.create_app")
    @patch("backend.scripts.runtime_contract_smoke._run_embedded_sdk_durable_recovery_check")
    @patch("backend.scripts.runtime_contract_smoke._run_runtime_surface_run_recovery_contract_check")
    @patch("backend.scripts.runtime_contract_smoke.TestClient")
    def test_runtime_contract_smoke_fails_when_contract_snapshot_is_degraded(self, mock_client, mock_run_recovery_check, mock_durable_check, _mock_app):
        mock_durable_check.return_value = {
            "ok": True,
            "failure_reason": "",
        }
        mock_run_recovery_check.return_value = {
            "ok": True,
            "failure_reason": "",
        }
        class _DegradedClient(_StubTestClient):
            def get(self, path):
                self.calls.append(("GET", path, None))
                if path == "/api/runtime-profile":
                    return _StubResponse(
                        200,
                        {
                            "contract_snapshot": {"overall_status": "degraded"},
                            "adapter_health": {"overall_status": "healthy"},
                        },
                    )
                raise AssertionError(f"unexpected GET path: {path}")

        mock_client.return_value = _DegradedClient(object())
        output = io.StringIO()
        with redirect_stdout(output):
            code = runtime_contract_smoke.main()

        payload = json.loads(output.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(payload["status"], "fail")
        self.assertFalse(payload["checks"][0]["ok"])
        self.assertEqual(payload["checks"][0]["contract_snapshot_status"], "degraded")
        self.assertEqual(payload["checks"][0]["runtime_contract_artifact_schema_status"], "")
        self.assertEqual(payload["checks"][0]["runtime_contract_artifact_schema_missing_field_count"], 0)
        self.assertEqual(payload["checks"][0]["runtime_contract_artifact_schema_missing_fields"], [])

    @patch("backend.scripts.runtime_contract_smoke.create_app")
    @patch("backend.scripts.runtime_contract_smoke._run_embedded_sdk_durable_recovery_check")
    @patch("backend.scripts.runtime_contract_smoke._run_runtime_surface_run_recovery_contract_check")
    @patch("backend.scripts.runtime_contract_smoke.TestClient")
    def test_runtime_contract_smoke_fails_when_adapter_pilot_returns_incomplete_events(self, mock_client, mock_run_recovery_check, mock_durable_check, _mock_app):
        mock_durable_check.return_value = {
            "ok": True,
            "failure_reason": "",
        }
        mock_run_recovery_check.return_value = {
            "ok": True,
            "failure_reason": "",
        }
        class _BrokenPilotClient(_StubTestClient):
            def post(self, path, json=None):
                self.calls.append(("POST", path, json))
                if path == "/api/runtime-framework-adapters/pilot-run":
                    return _StubResponse(
                        200,
                        {
                            "adapter_id": "local_fake_framework",
                            "events": [{"type": "status"}],
                            "final_output": "",
                        },
                    )
                raise AssertionError(f"unexpected POST path: {path}")

        mock_client.return_value = _BrokenPilotClient(object())
        output = io.StringIO()
        with redirect_stdout(output):
            code = runtime_contract_smoke.main()

        payload = json.loads(output.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(payload["status"], "fail")
        self.assertTrue(payload["checks"][0]["ok"])
        self.assertFalse(payload["checks"][1]["ok"])
        self.assertEqual(payload["checks"][1]["event_count"], 1)

    @patch("backend.scripts.runtime_contract_smoke.validate_embedded_sdk_event_payloads")
    @patch("backend.scripts.runtime_contract_smoke._run_embedded_sdk_durable_recovery_check")
    @patch("backend.scripts.runtime_contract_smoke._run_runtime_surface_run_recovery_contract_check")
    @patch("backend.scripts.runtime_contract_smoke.create_app")
    @patch("backend.scripts.runtime_contract_smoke.TestClient", return_value=_StubTestClient(object()))
    def test_runtime_contract_smoke_fails_when_sdk_event_payload_validation_fails(
        self,
        _mock_client,
        _mock_run_recovery_check,
        _mock_durable_check,
        _mock_app,
        mock_validate,
    ):
        _mock_durable_check.return_value = {
            "ok": True,
            "failure_reason": "",
        }
        _mock_run_recovery_check.return_value = {
            "ok": True,
            "failure_reason": "",
        }
        mock_validate.return_value = {
            "valid": False,
            "checked_event_count": 2,
            "missing_payload_count": 1,
            "missing_payloads": [
                {
                    "index": 1,
                    "status_kind": "execution_loop_done",
                    "missing_fields": ["completed_steps"],
                }
            ],
        }
        output = io.StringIO()
        with redirect_stdout(output):
            code = runtime_contract_smoke.main()

        payload = json.loads(output.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(payload["status"], "fail")
        self.assertTrue(payload["checks"][0]["ok"])
        self.assertTrue(payload["checks"][1]["ok"])
        self.assertFalse(payload["checks"][2]["ok"])
        self.assertEqual(payload["checks"][2]["missing_payload_count"], 1)
        self.assertEqual(
            payload["checks"][2]["missing_payloads"][0]["missing_fields"],
            ["completed_steps"],
        )

    @patch("backend.scripts.runtime_contract_smoke.create_app")
    @patch("backend.scripts.runtime_contract_smoke.TestClient", return_value=_StubTestClient(object()))
    @patch("backend.scripts.runtime_contract_smoke._run_embedded_sdk_durable_recovery_check")
    @patch("backend.scripts.runtime_contract_smoke._run_runtime_surface_run_recovery_contract_check")
    def test_runtime_contract_smoke_fails_when_durable_recovery_check_fails(
        self,
        mock_run_recovery_check,
        mock_durable_check,
        _mock_client,
        _mock_app,
    ):
        mock_run_recovery_check.return_value = {
            "ok": True,
            "failure_reason": "",
        }
        mock_durable_check.return_value = {
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
        }

        output = io.StringIO()
        with redirect_stdout(output):
            code = runtime_contract_smoke.main()

        payload = json.loads(output.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(payload["status"], "fail")
        self.assertFalse(payload["checks"][3]["ok"])
        self.assertEqual(payload["checks"][3]["name"], "embedded_sdk_durable_recovery")
        self.assertEqual(payload["checks"][3]["failure_reason"], "durable_recovery_chain_incomplete")

    @patch("backend.scripts.runtime_contract_smoke.create_app")
    @patch("backend.scripts.runtime_contract_smoke.TestClient", return_value=_StubTestClient(object()))
    @patch("backend.scripts.runtime_contract_smoke._run_embedded_sdk_durable_recovery_check")
    @patch("backend.scripts.runtime_contract_smoke._run_runtime_surface_run_recovery_contract_check")
    def test_runtime_contract_smoke_fails_when_run_recovery_contract_check_fails(
        self,
        mock_run_recovery_check,
        mock_durable_check,
        _mock_client,
        _mock_app,
    ):
        mock_durable_check.return_value = {
            "ok": True,
            "failure_reason": "",
        }
        mock_run_recovery_check.return_value = {
            "ok": False,
            "contract_version": "phase-ii-run-recovery-v1",
            "run_recovery_available": True,
            "probe_recoverable": False,
            "tool_recovery_reason": "missing_registered_binding",
            "loop_recovery_reason": "missing_registered_binding",
            "failure_reason": "run_recovery_contract_incomplete",
        }

        output = io.StringIO()
        with redirect_stdout(output):
            code = runtime_contract_smoke.main()

        payload = json.loads(output.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(payload["status"], "fail")
        checks_by_name = {check["name"]: check for check in payload["checks"]}
        self.assertFalse(checks_by_name["runtime_surface_run_recovery"]["ok"])
        self.assertEqual(
            checks_by_name["runtime_surface_run_recovery"]["failure_reason"],
            "run_recovery_contract_incomplete",
        )


if __name__ == "__main__":
    unittest.main()
