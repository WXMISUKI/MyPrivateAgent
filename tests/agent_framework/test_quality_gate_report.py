import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.scripts.quality_gate_report import GateStep, _render_summary, _run_step


class QualityGateReportTests(unittest.TestCase):
    @patch("backend.scripts.quality_gate_report.subprocess.run")
    def test_run_step_extracts_runtime_contract_smoke_checks_from_json_stdout(self, mock_run):
        mock_run.return_value = SimpleNamespace(
            returncode=0,
            stdout=(
                '{"status":"ok","checks":['
                '{"name":"runtime_profile_contract_snapshot","ok":true},'
                '{"name":"embedded_sdk_event_payloads","ok":true,"missing_payload_count":0},'
                '{"name":"embedded_sdk_durable_recovery","ok":true,"backend_kind":"sqlalchemy"}'
                ']}'
            ),
            stderr="",
        )

        result = _run_step(GateStep("Backend runtime_contract_smoke.py", ["python", "backend/scripts/runtime_contract_smoke.py"]))

        self.assertTrue(result["passed"])
        self.assertEqual(result["structured_output"]["status"], "ok")
        self.assertEqual(
            [item["name"] for item in result["structured_output"]["checks"]],
            ["runtime_profile_contract_snapshot", "embedded_sdk_event_payloads", "embedded_sdk_durable_recovery"],
        )
        self.assertEqual(result["contract_checks"][1]["name"], "embedded_sdk_event_payloads")

    def test_render_summary_includes_runtime_contract_check_table_when_present(self):
        summary = _render_summary({
            "passed": True,
            "step_count": 1,
            "failed_steps": [],
            "steps": [
                {
                    "name": "Backend runtime_contract_smoke.py",
                    "passed": True,
                    "exit_code": 0,
                    "duration_seconds": 0.1,
                    "contract_checks": [
                        {
                            "name": "embedded_sdk_event_payloads",
                            "ok": True,
                            "failure_reason": "",
                        }
                    ],
                }
            ],
        })

        self.assertIn("## Runtime Contract Checks", summary)
        self.assertIn("| Backend runtime_contract_smoke.py | embedded_sdk_event_payloads | PASS |  |", summary)

    def test_render_summary_escapes_runtime_contract_check_table_cells(self):
        summary = _render_summary({
            "passed": False,
            "step_count": 1,
            "failed_steps": [],
            "steps": [
                {
                    "name": "Quality | gate",
                    "passed": False,
                    "exit_code": 1,
                    "duration_seconds": 0.1,
                    "contract_checks": [
                        {
                            "name": "embedded|sdk",
                            "ok": False,
                            "failure_reason": "missing|payload\nline2",
                        }
                    ],
                }
            ],
        })

        self.assertIn("| Quality \\| gate | embedded\\|sdk | FAIL | missing\\|payload line2 |", summary)

    def test_render_summary_ignores_non_object_runtime_contract_checks(self):
        summary = _render_summary({
            "passed": False,
            "step_count": 1,
            "failed_steps": [],
            "steps": [
                {
                    "name": "Quality gate",
                    "passed": False,
                    "exit_code": 1,
                    "duration_seconds": 0.1,
                    "contract_checks": [
                        "bad-check",
                        None,
                        {
                            "name": "embedded_sdk_event_payloads",
                            "ok": False,
                            "failure_reason": "missing_payload",
                        },
                    ],
                }
            ],
        })

        self.assertIn("## Runtime Contract Checks", summary)
        self.assertIn("| Quality gate | embedded_sdk_event_payloads | FAIL | missing_payload |", summary)
        self.assertNotIn("bad-check", summary)

    def test_render_summary_ignores_non_object_steps(self):
        summary = _render_summary({
            "passed": False,
            "step_count": 3,
            "failed_steps": [{"name": "Quality gate", "exit_code": 1}, "bad-step"],
            "steps": [
                "bad-step",
                None,
                {
                    "name": "Quality gate",
                    "passed": False,
                    "exit_code": 1,
                    "duration_seconds": 0.1,
                    "contract_checks": [
                        {
                            "name": "embedded_sdk_event_payloads",
                            "ok": False,
                            "failure_reason": "missing_payload",
                        },
                    ],
                },
            ],
        })

        self.assertIn("| Quality gate | FAIL | 1 | 0.1 |", summary)
        self.assertIn("| Quality gate | embedded_sdk_event_payloads | FAIL | missing_payload |", summary)
        self.assertIn("- Quality gate", summary)
        self.assertNotIn("bad-step", summary)

    def test_render_summary_handles_step_objects_with_missing_fields(self):
        summary = _render_summary({
            "passed": False,
            "step_count": 2,
            "failed_steps": [{"exit_code": 1}, {"name": "Quality gate"}],
            "steps": [
                {
                    "name": "Quality gate",
                    "contract_checks": [
                        {
                            "name": "embedded_sdk_event_payloads",
                        }
                    ],
                },
                {
                    "contract_checks": [
                        {
                            "name": "runtime_surface_run_recovery",
                        }
                    ],
                },
            ],
        })

        self.assertIn("| Quality gate | FAIL |  |  |", summary)
        self.assertIn("| Quality gate | embedded_sdk_event_payloads | FAIL |  |", summary)
        self.assertIn("|  | runtime_surface_run_recovery | FAIL |  |", summary)
        self.assertIn("- Quality gate", summary)

    def test_render_summary_handles_missing_top_level_fields(self):
        summary = _render_summary({
            "steps": [
                {
                    "name": "Quality gate",
                    "passed": True,
                    "exit_code": 0,
                    "duration_seconds": 0.1,
                }
            ],
        })

        self.assertIn("- Status: FAIL", summary)
        self.assertIn("- Steps: 1", summary)
        self.assertIn("- Failed: 0", summary)
        self.assertIn("| Quality gate | PASS | 0 | 0.1 |", summary)

    def test_render_summary_ignores_non_list_steps_fields(self):
        summary = _render_summary({
            "passed": "false",
            "step_count": 3,
            "failed_steps": 1,
            "steps": 2,
        })

        self.assertIn("- Status: FAIL", summary)
        self.assertIn("- Steps: 3", summary)
        self.assertIn("- Failed: 0", summary)
        self.assertNotIn("## Failed Steps", summary)

    def test_render_summary_derives_failed_steps_when_missing(self):
        summary = _render_summary({
            "passed": False,
            "step_count": 2,
            "steps": [
                {
                    "name": "Smoke",
                    "passed": True,
                    "exit_code": 0,
                    "duration_seconds": 0.1,
                },
                {
                    "name": "Runtime contract smoke",
                    "passed": False,
                    "exit_code": 1,
                    "duration_seconds": 0.2,
                },
            ],
        })

        self.assertIn("- Failed: 1", summary)
        self.assertIn("## Failed Steps", summary)
        self.assertIn("- Runtime contract smoke", summary)

    def test_render_summary_treats_string_false_status_as_fail(self):
        summary = _render_summary({
            "passed": "false",
            "step_count": 1,
            "failed_steps": [{"name": "Runtime contract smoke"}],
            "steps": [
                {
                    "name": "Runtime contract smoke",
                    "passed": "false",
                    "exit_code": 1,
                    "duration_seconds": 0.2,
                },
            ],
        })

        self.assertIn("- Status: FAIL", summary)
        self.assertIn("| Runtime contract smoke | FAIL | 1 | 0.2 |", summary)

    @patch("backend.scripts.quality_gate_report.subprocess.run")
    def test_run_step_extracts_runtime_contract_checks_from_mixed_smoke_stdout(self, mock_run):
        mock_run.return_value = SimpleNamespace(
            returncode=0,
            stdout=(
                "\n==> Backend smoke_check.py\n"
                "PASS: smoke_check\n"
                "\n==> Backend runtime_contract_smoke.py\n"
                "{\n"
                '  "status": "ok",\n'
                '  "checks": [\n'
                '    {"name":"runtime_profile_contract_snapshot","ok":true},\n'
                '    {"name":"embedded_sdk_event_payloads","ok":true,"event_count":12,"missing_payload_count":0,'
                '"observed_status_kinds":["approval_created","approval_resolved","approval_replayed","approval_ignored"]},\n'
                '    {"name":"embedded_sdk_durable_recovery","ok":true},\n'
                '    {"name":"runtime_surface_run_recovery","ok":true},\n'
                '    {"name":"runtime_approved_tool_execution_bridge","ok":true,'
                '"approved_tool_call_count":1,'
                '"approved_policy_original_status":"approval_required",'
                '"approved_policy_override_status":"approved",'
                '"deny_override_status":"policy_denied",'
                '"deny_tool_call_count":0},\n'
                '    {"name":"sdk_tool_runtime_execution_bridge","ok":true,'
                '"auto_tool_call_count":1,'
                '"auto_tool_history_count":1,'
                '"approved_tool_call_count":1,'
                '"approved_policy_original_status":"approval_required",'
                '"approved_policy_override_status":"approved",'
                '"deny_override_status":"policy_denied",'
                '"deny_tool_call_count":0},\n'
                '    {"name":"tool_runtime_timeout_retry","ok":true,'
                '"retry_policy":"sync_exception_retry",'
                '"timeout_enforcement":"post_call_elapsed_check",'
                '"recovered_status":"ok",'
                '"recovered_retry_status":"recovered",'
                '"recovered_attempt_count":2,'
                '"exhausted_status":"error",'
                '"exhausted_retry_status":"exhausted",'
                '"exhausted_attempt_count":2,'
                '"timeout_status":"timeout",'
                '"timeout_metadata_status":"exceeded",'
                '"timeout_metadata_enforcement":"post_call_elapsed_check",'
                '"hard_cancellation_claimed":false,'
                '"sandbox_execution_claimed":false,'
                '"worker_timeout_claimed":false},\n'
                '    {"name":"approval_lifecycle_recovery_alignment","ok":true,'
                '"replayed_submission_status":"replayed",'
                '"ignored_submission_status":"ignored",'
                '"resolved_recovery_reason":"already_resolved"},\n'
                '    {"name":"embedded_sdk_persistence_posture","ok":true,'
                '"contract_version":"phase-ii-embedded-sdk-persistence-interface-v1",'
                '"memory_posture":"memory_preview",'
                '"durable_posture":"durable_ready",'
                '"degraded_posture":"durable_degraded",'
                '"memory_cross_process_block_reason":"workspace_backend_not_durable",'
                '"degraded_cross_process_block_reason":"workspace_backend_fallback_active",'
                '"durable_cross_process_candidate":true,'
                '"production_recovery_gate_contract_version":"phase-ii-durable-workspace-production-recovery-gate-v1",'
                '"production_recovery_gate_status":"blocked",'
                '"production_recovery_gate_missing_sections":["worker_ownership_production_gate","durable_backend_migration_rollout"],'
                '"production_recovery_default_enabled":false,'
                '"production_recovery_worker_ownership_gate_contract_version":"phase-ii-worker-ownership-production-gate-v1",'
                '"production_recovery_worker_ownership_gate_status":"blocked",'
                '"production_recovery_worker_ownership_default_enabled":false,'
                '"production_recovery_worker_ownership_missing_sections":["vendor_lock_semantics","heartbeat_renewal_supervisor"],'
                '"recovery_audit_contract_version":"phase-ii-recovery-audit-production-gate-v1",'
                '"recovery_audit_ready":true,'
                '"recovery_audit_operation_history_supported":true,'
                '"recovery_audit_summary_supported":true,'
                '"recovery_audit_timeline_writer_available":true,'
                '"recovery_audit_idempotent_trace_dedupe":true,'
                '"recovery_audit_authorization_source":false,'
                '"registry_checkpoint_policy_contract_version":"phase-ii-production-recovery-registry-checkpoint-policy-v1",'
                '"registry_checkpoint_policy_ready":true,'
                '"registry_binding_policy_ready":true,'
                '"checkpoint_resume_cursor_policy_ready":true,'
                '"registry_checkpoint_policy_authorization_source":false},\n'
                '    {"name":"worker_ownership_store_mode","ok":true,'
                '"default_mode":"memory_only",'
                '"default_mode_source":"default",'
                '"default_adapter_kind":"in_memory",'
                '"default_durable":false,'
                '"configurable_knob_present":true,'
                '"hot_reloadable_knob_present":true,'
                '"strict_mode_status":"sqlalchemy_durable",'
                '"production_gate_contract_version":"phase-ii-worker-ownership-production-gate-v1",'
                '"production_gate_status":"blocked",'
                '"production_gate_missing_sections":["vendor_lock_semantics","heartbeat_renewal_supervisor","ownership_audit_evidence","fail_closed_default_decision","production_default_enablement_input_source"],'
                '"production_default_enabled":false,'
                '"vendor_lock_contract_version":"phase-ii-worker-ownership-vendor-lock-semantics-v1",'
                '"vendor_lock_status":"blocked",'
                '"vendor_lock_missing_sections":["vendor_lock_adapter","target_decision"],'
                '"vendor_lock_current_posture":"sql_row_lease_fencing",'
                '"vendor_lock_sql_row_lease_fencing":true,'
                '"vendor_lock_sql_row_lease_is_vendor_lock":false,'
                '"vendor_lock_adapter_present":false,'
                '"vendor_lock_adapter_contract_version":"phase-ii-worker-ownership-vendor-lock-adapter-v1",'
                '"vendor_lock_adapter_status":"blocked",'
                '"vendor_lock_adapter_kind":"",'
                '"vendor_lock_adapter_target_backend":"",'
                '"vendor_lock_adapter_scope":"",'
                '"vendor_lock_adapter_fencing_strategy":"",'
                '"vendor_lock_adapter_ttl_renewal_strategy":"",'
                '"vendor_lock_adapter_failover_strategy":"",'
                '"vendor_lock_adapter_stale_cleanup_strategy":"",'
                '"vendor_lock_adapter_acquire_supported":false,'
                '"vendor_lock_adapter_renew_supported":false,'
                '"vendor_lock_adapter_release_supported":false,'
                '"vendor_lock_adapter_probe_supported":false,'
                '"vendor_lock_adapter_production_allowed":false,'
                '"vendor_lock_adapter_sql_row_lease_is_vendor_lock":false,'
                '"vendor_lock_adapter_missing_sections":["adapter_kind","target_backend"],'
                '"postgres_probe_contract_version":"phase-ii-worker-ownership-postgres-vendor-lock-probe-v1",'
                '"postgres_probe_status":"blocked",'
                '"postgres_probe_missing_sections":["advisory_lock_family","probe_safety"],'
                '"postgres_probe_executes":false,'
                '"postgres_probe_sql_row_lease_is_vendor_lock":false,'
                '"postgres_probe_ready_status":"ready",'
                '"postgres_probe_ready_executes":false,'
                '"postgres_execution_seam_contract_version":"phase-ii-worker-ownership-postgres-advisory-lock-execution-seam-v1",'
                '"postgres_execution_default_status":"blocked",'
                '"postgres_execution_default_executor_bound":false,'
                '"postgres_execution_default_enabled_by_default":false,'
                '"postgres_execution_default_production_allowed":false,'
                '"postgres_execution_default_missing_sections":["executor_binding"],'
                '"postgres_execution_default_probe_status":"blocked",'
                '"postgres_execution_default_probe_executed":false,'
                '"postgres_execution_opt_in_status":"ready",'
                '"postgres_execution_opt_in_executor_bound":true,'
                '"postgres_execution_opt_in_enabled_by_default":false,'
                '"postgres_execution_opt_in_production_allowed":false,'
                '"postgres_execution_opt_in_probe_status":"ready",'
                '"postgres_execution_opt_in_probe_executed":true,'
                '"postgres_execution_opt_in_acquire_status":"acquired",'
                '"postgres_execution_opt_in_acquire_executed":true,'
                '"postgres_execution_opt_in_acquired":true,'
                '"postgres_execution_opt_in_envelope_count":2,'
                '"postgres_rollout_consumer_contract_version":"phase-ii-worker-ownership-postgres-rollout-artifact-consumer-v1",'
                '"postgres_rollout_consumer_default_status":"blocked",'
                '"postgres_rollout_consumer_default_missing_sections":["source_kind","postgres_execution_seam"],'
                '"postgres_rollout_consumer_default_will_enable_default":false,'
                '"postgres_rollout_consumer_default_executes_lock":false,'
                '"postgres_rollout_consumer_ready_status":"ready",'
                '"postgres_rollout_consumer_ready_target_backend":"postgres",'
                '"postgres_rollout_consumer_ready_lock_adapter_kind":"postgres_advisory_lock",'
                '"postgres_rollout_consumer_ready_will_enable_default":false,'
                '"postgres_rollout_consumer_ready_executes_lock":false,'
                '"postgres_rollout_consumer_input_source_status":"ready",'
                '"postgres_rollout_consumer_input_source_ready":true,'
                '"postgres_rollout_consumer_input_source_kind":"rollout_artifact",'
                '"postgres_target_binding_contract_version":"phase-ii-worker-ownership-postgres-vendor-lock-target-artifact-binding-v1",'
                '"postgres_target_binding_default_status":"blocked",'
                '"postgres_target_binding_default_missing_sections":["source_kind","postgres_rollout_consumer"],'
                '"postgres_target_binding_default_will_enable_lock":false,'
                '"postgres_target_binding_default_executes_lock":false,'
                '"postgres_target_binding_ready_status":"ready",'
                '"postgres_target_binding_ready_target_backend":"postgres",'
                '"postgres_target_binding_ready_lock_adapter_kind":"postgres_advisory_lock",'
                '"postgres_target_binding_ready_will_enable_lock":false,'
                '"postgres_target_binding_ready_executes_lock":false,'
                '"postgres_target_binding_target_input_status":"ready",'
                '"postgres_target_binding_target_decision_status":"ready",'
                '"postgres_target_binding_target_decision_production_allowed":true,'
                '"postgres_semantics_binding_contract_version":"phase-ii-worker-ownership-postgres-vendor-lock-semantics-binding-v1",'
                '"postgres_semantics_binding_default_status":"blocked",'
                '"postgres_semantics_binding_default_missing_sections":["target_artifact_binding","postgres_execution_seam"],'
                '"postgres_semantics_binding_default_will_enable_lock":false,'
                '"postgres_semantics_binding_default_will_update_gate":false,'
                '"postgres_semantics_binding_default_executes_lock":false,'
                '"postgres_semantics_binding_ready_status":"ready",'
                '"postgres_semantics_binding_ready_target_backend":"postgres",'
                '"postgres_semantics_binding_ready_lock_adapter_kind":"postgres_advisory_lock",'
                '"postgres_semantics_binding_ready_probe_status":"ready",'
                '"postgres_semantics_binding_ready_adapter_status":"ready",'
                '"postgres_semantics_binding_ready_semantics_status":"ready",'
                '"postgres_semantics_binding_ready_will_enable_lock":false,'
                '"postgres_semantics_binding_ready_will_update_gate":false,'
                '"postgres_semantics_binding_ready_executes_lock":false,'
                '"postgres_wiring_decision_contract_version":"phase-ii-worker-ownership-postgres-vendor-lock-production-gate-wiring-decision-v1",'
                '"postgres_wiring_decision_default_status":"blocked",'
                '"postgres_wiring_decision_default_missing_sections":["semantics_binding","decision_recorded"],'
                '"postgres_wiring_decision_default_wiring_allowed":false,'
                '"postgres_wiring_decision_default_will_update_gate":false,'
                '"postgres_wiring_decision_default_will_enable_lock":false,'
                '"postgres_wiring_decision_default_executes_lock":false,'
                '"postgres_wiring_decision_ready_status":"ready",'
                '"postgres_wiring_decision_ready_semantics_binding_status":"ready",'
                '"postgres_wiring_decision_ready_candidate_status":"ready",'
                '"postgres_wiring_decision_ready_wiring_allowed":true,'
                '"postgres_wiring_decision_ready_target_backend":"postgres",'
                '"postgres_wiring_decision_ready_lock_adapter_kind":"postgres_advisory_lock",'
                '"postgres_wiring_decision_ready_will_update_gate":false,'
                '"postgres_wiring_decision_ready_will_enable_lock":false,'
                '"postgres_wiring_decision_ready_executes_lock":false,'
                '"production_dry_run_contract_version":"phase-ii-worker-ownership-production-gate-composition-dry-run-v1",'
                '"production_dry_run_default_status":"blocked",'
                '"production_dry_run_default_missing_sections":["vendor_lock_wiring_decision","heartbeat_renewal_supervisor","rollout_confirmation","recovery_entry_auto_claim_enablement","ownership_audit_evidence","production_default_enablement_input_source"],'
                '"production_dry_run_default_all_required_ready":false,'
                '"production_dry_run_default_would_allow":false,'
                '"production_dry_run_default_will_enable":false,'
                '"production_dry_run_default_executes_lock":false,'
                '"production_dry_run_default_starts_worker":false,'
                '"production_dry_run_default_runs_auto_claim":false,'
                '"production_dry_run_ready_status":"ready",'
                '"production_dry_run_ready_missing_sections":[],'
                '"production_dry_run_ready_all_required_ready":true,'
                '"production_dry_run_ready_would_allow":true,'
                '"production_dry_run_ready_will_enable":false,'
                '"production_dry_run_ready_executes_lock":false,'
                '"production_dry_run_ready_starts_worker":false,'
                '"production_dry_run_ready_runs_auto_claim":false,'
                '"enablement_config_consumer_contract_version":"phase-ii-worker-ownership-production-enablement-runtime-config-consumer-v1",'
                '"enablement_config_consumer_default_status":"blocked",'
                '"enablement_config_consumer_default_missing_sections":["source_kind","config_id","enablement_input_source","composition_dry_run"],'
                '"enablement_config_consumer_default_will_enable":false,'
                '"enablement_config_consumer_default_executes_lock":false,'
                '"enablement_config_consumer_default_starts_worker":false,'
                '"enablement_config_consumer_default_runs_auto_claim":false,'
                '"enablement_config_consumer_ready_status":"ready",'
                '"enablement_config_consumer_ready_missing_sections":[],'
                '"enablement_config_consumer_ready_target_backend":"postgres",'
                '"enablement_config_consumer_ready_lock_adapter_kind":"postgres_advisory_lock",'
                '"enablement_config_consumer_ready_input_source_status":"ready",'
                '"enablement_config_consumer_ready_dry_run_status":"ready",'
                '"enablement_config_consumer_ready_dry_run_would_allow":true,'
                '"enablement_config_consumer_ready_will_enable":false,'
                '"enablement_config_consumer_ready_executes_lock":false,'
                '"enablement_config_consumer_ready_starts_worker":false,'
                '"enablement_config_consumer_ready_runs_auto_claim":false,'
                '"enablement_config_factory_binding_default_status":"blocked",'
                '"enablement_config_factory_binding_ready_status":"ready",'
                '"enablement_config_factory_binding_ready_config_id":"factory-binding-smoke",'
                '"enablement_config_factory_binding_will_enable":false,'
                '"enablement_config_factory_binding_executes_lock":false,'
                '"enablement_config_factory_binding_starts_worker":false,'
                '"enablement_config_factory_binding_runs_auto_claim":false,'
                '"vendor_lock_scope_defined":false,'
                '"vendor_lock_fencing_guarantee_defined":false,'
                '"vendor_lock_failover_semantics_defined":false,'
                '"vendor_lock_ttl_renewal_semantics_defined":false,'
                '"vendor_lock_stale_owner_cleanup_defined":false,'
                '"vendor_lock_production_allowed":false,'
                '"vendor_lock_target_decision_contract_version":"phase-ii-worker-ownership-vendor-lock-target-decision-v1",'
                '"vendor_lock_target_decision_status":"blocked",'
                '"vendor_lock_target_decision_recorded":false,'
                '"vendor_lock_target_backend":"",'
                '"vendor_lock_target_adapter_kind":"",'
                '"vendor_lock_target_scope":"",'
                '"vendor_lock_target_fencing_strategy":"",'
                '"vendor_lock_target_ttl_renewal_strategy":"",'
                '"vendor_lock_target_failover_strategy":"",'
                '"vendor_lock_target_stale_cleanup_strategy":"",'
                '"vendor_lock_target_missing_sections":["input_source","decision_recorded","target_backend"],'
                '"vendor_lock_target_sql_row_lease_is_vendor_lock":false,'
                '"vendor_lock_target_production_allowed":false,'
                '"vendor_lock_target_input_contract_version":"phase-ii-worker-ownership-vendor-lock-target-decision-input-v1",'
                '"vendor_lock_target_input_source_status":"blocked",'
                '"vendor_lock_target_input_source_kind":"",'
                '"vendor_lock_target_input_decision_id":"",'
                '"vendor_lock_target_input_approved_by":"",'
                '"vendor_lock_target_input_approved_at":"",'
                '"vendor_lock_target_input_backend":"",'
                '"vendor_lock_target_input_adapter_kind":"",'
                '"vendor_lock_target_input_rollout_artifact":"",'
                '"vendor_lock_target_input_config_key":"",'
                '"vendor_lock_target_input_manual_approval_reference":"",'
                '"vendor_lock_target_input_missing_sections":["input_source_kind","decision_id"],'
                '"vendor_lock_target_input_sql_row_lease_is_vendor_lock":false,'
                '"renewal_supervisor_contract_version":"phase-ii-worker-ownership-renewal-supervisor-v1",'
                '"renewal_supervisor_status":"blocked",'
                '"renewal_supervisor_missing_sections":["background_supervisor"],'
                '"renewal_supervisor_enabled_by_default":false,'
                '"renewal_supervisor_renew_once_supported":true,'
                '"renewal_supervisor_owner_identity_required":true,'
                '"renewal_supervisor_ttl_interval_policy_ready":true,'
                '"renewal_supervisor_controlled_lifecycle_supported":true,'
                '"renewal_supervisor_starts_by_default":false,'
                '"renewal_supervisor_active":false,'
                '"renewal_supervisor_last_renewal_status":"",'
                '"renewal_supervisor_stop_supported":true,'
                '"renewal_supervisor_failure_fail_closed":true,'
                '"renewal_supervisor_lease_loss_fail_closed":true,'
                '"renewal_supervisor_renew_once_status":"renewed",'
                '"renewal_supervisor_renew_once_background_started":false,'
                '"renewal_supervisor_stale_fencing_status":"blocked",'
                '"renewal_supervisor_stale_fencing_reason":"stale_worker_fencing_token",'
                '"renewal_supervisor_lifecycle_initial_active":false,'
                '"renewal_supervisor_lifecycle_started_active":true,'
                '"renewal_supervisor_lifecycle_started_status":"renewed",'
                '"renewal_supervisor_lifecycle_started_count":1,'
                '"renewal_supervisor_lifecycle_stopped_active":false,'
                '"renewal_supervisor_lifecycle_stopped_count":1,'
                '"rollout_readiness_contract_version":"phase-ii-worker-ownership-rollout-readiness-v1",'
                '"rollout_readiness_status":"blocked",'
                '"rollout_missing_sections":["strict_mode_rollout"],'
                '"production_rollout_confirmed":false,'
                '"rollout_migration_ready":true,'
                '"rollout_stale_fencing_verified":true,'
                '"rollout_rollback_plan_ready":false,'
                '"rollout_operationalization_status":"blocked",'
                '"rollout_mode":"readiness_only",'
                '"rollout_missing_artifacts":["rollback_plan","rollout_confirmation_decision"],'
                '"rollout_rollback_plan_status":"missing",'
                '"rollout_fallback_policy_status":"missing",'
                '"rollout_renewal_lifecycle_verification_status":"missing",'
                '"rollout_auto_claim_decision_status":"missing",'
                '"rollout_confirmation_decision_contract_version":"phase-ii-worker-ownership-rollout-confirmation-decision-v1",'
                '"rollout_confirmation_decision_status":"blocked",'
                '"rollout_decision_recorded":false,'
                '"rollout_decision_id":"",'
                '"rollout_approved_by":"",'
                '"rollout_approved_at":"",'
                '"rollout_target_store_mode":"",'
                '"rollout_confirmation_missing_sections":["decision_recorded"],'
                '"rollout_confirmation_production_rollout_confirmed":false,'
                '"rollout_confirmation_input_contract_version":"phase-ii-worker-ownership-rollout-confirmation-input-source-v1",'
                '"rollout_confirmation_input_source_status":"blocked",'
                '"rollout_confirmation_input_source_kind":"",'
                '"rollout_confirmation_input_decision_id":"",'
                '"rollout_confirmation_input_approved_by":"",'
                '"rollout_confirmation_input_approved_at":"",'
                '"rollout_confirmation_input_target_store_mode":"",'
                '"rollout_confirmation_input_rollback_plan_reference":"",'
                '"rollout_confirmation_input_fallback_policy_reference":"",'
                '"rollout_confirmation_input_renewal_lifecycle_reference":"",'
                '"rollout_confirmation_input_auto_claim_decision_reference":"",'
                '"rollout_confirmation_input_missing_sections":["input_source_kind","decision_id","approved_by","approved_at","target_store_mode","rollback_plan_reference","fallback_policy_reference","renewal_lifecycle_reference","auto_claim_decision_reference","source_reference"],'
                '"rollout_confirmation_input_sql_row_lease_is_authority":false,'
                '"auto_claim_policy_contract_version":"phase-ii-worker-ownership-auto-claim-policy-v1",'
                '"auto_claim_policy_status":"blocked",'
                '"auto_claim_missing_sections":["explicit_runtime_configuration"],'
                '"auto_claim_enabled_by_default":false,'
                '"auto_claim_descriptor_evidence_fallback":true,'
                '"auto_claim_lease_validation_required":true,'
                '"auto_claim_entrypoint_allowlist_ready":true,'
                '"auto_claim_entrypoint_allowlist_contract_version":"phase-ii-worker-ownership-auto-claim-entrypoint-allowlist-v1",'
                '"auto_claim_entrypoint_allowlist_status":"ready",'
                '"auto_claim_allowed_entrypoints":["submit_approval.approved","resume_run.continue_loop"],'
                '"auto_claim_missing_entrypoints":[],'
                '"auto_claim_default_auto_claim_enabled":false,'
                '"auto_claim_requires_production_gate_ready":true,'
                '"auto_claim_enablement_gate_contract_version":"phase-ii-worker-ownership-explicit-auto-claim-enablement-gate-v1",'
                '"auto_claim_enablement_gate_status":"blocked",'
                '"auto_claim_will_auto_claim":false,'
                '"auto_claim_requested_entrypoint":"submit_approval.approved",'
                '"auto_claim_enablement_missing_sections":["explicit_runtime_configuration"],'
                '"auto_claim_enablement_blocked_reason":"explicit_runtime_configuration_missing",'
                '"ownership_audit_contract_version":"phase-ii-worker-ownership-audit-evidence-v1",'
                '"ownership_audit_status":"blocked",'
                '"ownership_audit_missing_sections":["operation_history"],'
                '"ownership_audit_compact_evidence":true,'
                '"ownership_audit_operation_history_ready":false,'
                '"ownership_audit_recovery_operation_link_ready":false,'
                '"ownership_audit_timeline_writer_ready":false,'
                '"ownership_audit_idempotent_dedupe_ready":false,'
                '"ownership_audit_authorization_source":false,'
                '"enablement_strategy_contract_version":"phase-ii-worker-ownership-production-enablement-strategy-v1",'
                '"enablement_strategy_status":"blocked",'
                '"enablement_strategy_blocking_sections":["vendor_lock_semantics","rollout_checklist","production_default_enablement_input_source"],'
                '"production_default_enabled_requested":false,'
                '"production_default_allowed":false,'
                '"enablement_input_source_contract_version":"phase-ii-worker-ownership-production-default-enablement-input-source-v1",'
                '"enablement_input_source_status":"blocked",'
                '"enablement_input_source_kind":"",'
                '"enablement_request_id":"",'
                '"enablement_requested_by":"",'
                '"enablement_requested_at":"",'
                '"enablement_target_store_mode":"",'
                '"enablement_rollout_artifact":"",'
                '"enablement_vendor_lock_decision_id":"",'
                '"enablement_renewal_lifecycle_reference":"",'
                '"enablement_auto_claim_decision_reference":"",'
                '"enablement_audit_evidence_reference":"",'
                '"enablement_rollback_plan_reference":"",'
                '"enablement_fallback_policy_reference":"",'
                '"enablement_input_source_ready":false,'
                '"enablement_input_source_missing_sections":["input_source_kind"],'
                '"enablement_explicit_required":true,'
                '"enablement_all_required_sections_ready":false,'
                '"enablement_fail_closed_when_blocked":true,'
                '"enablement_sql_row_lease_not_default_authority":true,'
                '"fallback_mode_status":"fallback_to_memory"},\n'
                '    {"name":"child_executor_promotion_gate","ok":true,'
                '"contract_version":"phase-ii-child-executor-gate-v1",'
                '"gate_status":"blocked",'
                '"allowed":false,'
                '"gate_failure_reason":"child_executor_preflight_blocked",'
                '"blocker_count":2,'
                '"recommended_next_step":"keep_relationship_only"},\n'
                '    {"name":"subagent_lane_query_detail","ok":true,'
                '"contract_version":"phase-h-subagent-lane-query-detail-v1",'
                '"recording_state":"recorded",'
                '"stage_count":2,'
                '"recent_event_count":2}\n'
                "  ]\n"
                "}\n"
                "\nPASS: quality_gate_smoke\n"
            ),
            stderr="",
        )

        result = _run_step(GateStep("Quality gate smoke", ["powershell", "-File", "backend/scripts/quality_gate_smoke.ps1"]))

        self.assertTrue(result["passed"])
        self.assertEqual(
            [item["name"] for item in result["contract_checks"]],
            [
                "runtime_profile_contract_snapshot",
                "embedded_sdk_event_payloads",
                "embedded_sdk_durable_recovery",
                "runtime_surface_run_recovery",
                "runtime_approved_tool_execution_bridge",
                "sdk_tool_runtime_execution_bridge",
                "tool_runtime_timeout_retry",
                "approval_lifecycle_recovery_alignment",
                "embedded_sdk_persistence_posture",
                "worker_ownership_store_mode",
                "child_executor_promotion_gate",
                "subagent_lane_query_detail",
            ],
        )
        self.assertEqual(result["runtime_contract_summary"]["overall_status"], "healthy")
        self.assertEqual(result["runtime_contract_summary"]["check_count"], 12)
        self.assertEqual(result["runtime_contract_summary"]["missing_payload_count"], 0)
        self.assertTrue(result["runtime_contract_summary"]["approval_replay_coverage"]["event_payload_sample"])
        approved_coverage = result["runtime_contract_summary"]["approved_tool_execution_coverage"]
        self.assertTrue(approved_coverage["bridge_smoke"])
        self.assertEqual(approved_coverage["approved_tool_call_count"], 1)
        self.assertEqual(approved_coverage["approved_policy_original_status"], "approval_required")
        self.assertEqual(approved_coverage["approved_policy_override_status"], "approved")
        self.assertEqual(approved_coverage["deny_override_status"], "policy_denied")
        self.assertEqual(approved_coverage["deny_tool_call_count"], 0)
        sdk_coverage = result["runtime_contract_summary"]["sdk_tool_runtime_execution_coverage"]
        self.assertTrue(sdk_coverage["bridge_smoke"])
        self.assertEqual(sdk_coverage["auto_tool_call_count"], 1)
        self.assertEqual(sdk_coverage["auto_tool_history_count"], 1)
        self.assertEqual(sdk_coverage["approved_tool_call_count"], 1)
        self.assertEqual(sdk_coverage["approved_policy_original_status"], "approval_required")
        self.assertEqual(sdk_coverage["approved_policy_override_status"], "approved")
        self.assertEqual(sdk_coverage["deny_override_status"], "policy_denied")
        self.assertEqual(sdk_coverage["deny_tool_call_count"], 0)
        tool_timeout_retry_coverage = result["runtime_contract_summary"]["tool_runtime_timeout_retry_coverage"]
        self.assertTrue(tool_timeout_retry_coverage["timeout_retry_smoke"])
        self.assertEqual(tool_timeout_retry_coverage["recovered_retry_status"], "recovered")
        self.assertEqual(tool_timeout_retry_coverage["exhausted_retry_status"], "exhausted")
        self.assertEqual(tool_timeout_retry_coverage["timeout_metadata_status"], "exceeded")
        lifecycle_coverage = result["runtime_contract_summary"]["approval_lifecycle_recovery_coverage"]
        self.assertTrue(lifecycle_coverage["alignment_smoke"])
        self.assertEqual(lifecycle_coverage["replayed_submission_status"], "replayed")
        self.assertEqual(lifecycle_coverage["ignored_submission_status"], "ignored")
        self.assertEqual(lifecycle_coverage["resolved_recovery_reason"], "already_resolved")
        persistence_coverage = result["runtime_contract_summary"]["embedded_sdk_persistence_coverage"]
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
        recovery_audit_coverage = result["runtime_contract_summary"]["recovery_audit_operation_history_coverage"]
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
        registry_checkpoint_coverage = result["runtime_contract_summary"][
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
        ownership_coverage = result["runtime_contract_summary"]["worker_ownership_store_mode_coverage"]
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
        self.assertFalse(ownership_coverage["production_default_enabled"])
        self.assertEqual(
            ownership_coverage["vendor_lock_contract_version"],
            "phase-ii-worker-ownership-vendor-lock-semantics-v1",
        )
        self.assertEqual(ownership_coverage["vendor_lock_status"], "blocked")
        self.assertIn("vendor_lock_adapter", ownership_coverage["vendor_lock_missing_sections"])
        self.assertIn("target_decision", ownership_coverage["vendor_lock_missing_sections"])
        self.assertFalse(ownership_coverage["vendor_lock_sql_row_lease_is_vendor_lock"])
        self.assertFalse(ownership_coverage["vendor_lock_production_allowed"])
        self.assertEqual(
            ownership_coverage["vendor_lock_target_decision_contract_version"],
            "phase-ii-worker-ownership-vendor-lock-target-decision-v1",
        )
        self.assertEqual(ownership_coverage["vendor_lock_target_decision_status"], "blocked")
        self.assertFalse(ownership_coverage["vendor_lock_target_decision_recorded"])
        self.assertEqual(ownership_coverage["vendor_lock_target_backend"], "")
        self.assertIn(
            "decision_recorded",
            ownership_coverage["vendor_lock_target_missing_sections"],
        )
        self.assertIn(
            "input_source",
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
        self.assertEqual(ownership_coverage["vendor_lock_target_input_source_kind"], "")
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
        self.assertEqual(
            ownership_coverage["renewal_supervisor_contract_version"],
            "phase-ii-worker-ownership-renewal-supervisor-v1",
        )
        self.assertEqual(ownership_coverage["renewal_supervisor_status"], "blocked")
        self.assertFalse(ownership_coverage["renewal_supervisor_enabled_by_default"])
        self.assertTrue(ownership_coverage["renewal_supervisor_renew_once_supported"])
        self.assertTrue(ownership_coverage["renewal_supervisor_owner_identity_required"])
        self.assertTrue(ownership_coverage["renewal_supervisor_ttl_interval_policy_ready"])
        self.assertTrue(ownership_coverage["renewal_supervisor_controlled_lifecycle_supported"])
        self.assertFalse(ownership_coverage["renewal_supervisor_starts_by_default"])
        self.assertFalse(ownership_coverage["renewal_supervisor_active"])
        self.assertEqual(ownership_coverage["renewal_supervisor_last_renewal_status"], "")
        self.assertTrue(ownership_coverage["renewal_supervisor_stop_supported"])
        self.assertTrue(ownership_coverage["renewal_supervisor_failure_fail_closed"])
        self.assertTrue(ownership_coverage["renewal_supervisor_lease_loss_fail_closed"])
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
        self.assertIn(
            "background_supervisor",
            ownership_coverage["renewal_supervisor_missing_sections"],
        )
        self.assertEqual(
            ownership_coverage["rollout_readiness_contract_version"],
            "phase-ii-worker-ownership-rollout-readiness-v1",
        )
        self.assertEqual(ownership_coverage["rollout_readiness_status"], "blocked")
        self.assertFalse(ownership_coverage["production_rollout_confirmed"])
        self.assertTrue(ownership_coverage["rollout_migration_ready"])
        self.assertTrue(ownership_coverage["rollout_stale_fencing_verified"])
        self.assertFalse(ownership_coverage["rollout_rollback_plan_ready"])
        self.assertEqual(ownership_coverage["rollout_operationalization_status"], "blocked")
        self.assertEqual(ownership_coverage["rollout_mode"], "readiness_only")
        self.assertIn("rollback_plan", ownership_coverage["rollout_missing_artifacts"])
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
            ownership_coverage["rollout_confirmation_input_contract_version"],
            "phase-ii-worker-ownership-rollout-confirmation-input-source-v1",
        )
        self.assertEqual(
            ownership_coverage["rollout_confirmation_input_source_status"],
            "blocked",
        )
        self.assertIn(
            "input_source_kind",
            ownership_coverage["rollout_confirmation_input_missing_sections"],
        )
        self.assertFalse(
            ownership_coverage["rollout_confirmation_input_sql_row_lease_is_authority"]
        )
        self.assertIn("strict_mode_rollout", ownership_coverage["rollout_missing_sections"])
        self.assertEqual(
            ownership_coverage["auto_claim_policy_contract_version"],
            "phase-ii-worker-ownership-auto-claim-policy-v1",
        )
        self.assertEqual(ownership_coverage["auto_claim_policy_status"], "blocked")
        self.assertFalse(ownership_coverage["auto_claim_enabled_by_default"])
        self.assertTrue(ownership_coverage["auto_claim_descriptor_evidence_fallback"])
        self.assertTrue(ownership_coverage["auto_claim_lease_validation_required"])
        self.assertTrue(ownership_coverage["auto_claim_entrypoint_allowlist_ready"])
        self.assertEqual(
            ownership_coverage["auto_claim_entrypoint_allowlist_contract_version"],
            "phase-ii-worker-ownership-auto-claim-entrypoint-allowlist-v1",
        )
        self.assertEqual(
            ownership_coverage["auto_claim_entrypoint_allowlist_status"],
            "ready",
        )
        self.assertIn(
            "submit_approval.approved",
            ownership_coverage["auto_claim_allowed_entrypoints"],
        )
        self.assertIn(
            "resume_run.continue_loop",
            ownership_coverage["auto_claim_allowed_entrypoints"],
        )
        self.assertEqual(ownership_coverage["auto_claim_missing_entrypoints"], [])
        self.assertFalse(ownership_coverage["auto_claim_default_auto_claim_enabled"])
        self.assertTrue(ownership_coverage["auto_claim_requires_production_gate_ready"])
        self.assertEqual(
            ownership_coverage["auto_claim_enablement_gate_contract_version"],
            "phase-ii-worker-ownership-explicit-auto-claim-enablement-gate-v1",
        )
        self.assertEqual(ownership_coverage["auto_claim_enablement_gate_status"], "blocked")
        self.assertFalse(ownership_coverage["auto_claim_will_auto_claim"])
        self.assertEqual(
            ownership_coverage["auto_claim_requested_entrypoint"],
            "submit_approval.approved",
        )
        self.assertIn(
            "explicit_runtime_configuration",
            ownership_coverage["auto_claim_enablement_missing_sections"],
        )
        self.assertEqual(
            ownership_coverage["auto_claim_enablement_blocked_reason"],
            "explicit_runtime_configuration_missing",
        )
        self.assertIn(
            "explicit_runtime_configuration",
            ownership_coverage["auto_claim_missing_sections"],
        )
        self.assertEqual(
            ownership_coverage["ownership_audit_contract_version"],
            "phase-ii-worker-ownership-audit-evidence-v1",
        )
        self.assertEqual(ownership_coverage["ownership_audit_status"], "blocked")
        self.assertTrue(ownership_coverage["ownership_audit_compact_evidence"])
        self.assertFalse(ownership_coverage["ownership_audit_operation_history_ready"])
        self.assertFalse(ownership_coverage["ownership_audit_recovery_operation_link_ready"])
        self.assertFalse(ownership_coverage["ownership_audit_timeline_writer_ready"])
        self.assertFalse(ownership_coverage["ownership_audit_idempotent_dedupe_ready"])
        self.assertFalse(ownership_coverage["ownership_audit_authorization_source"])
        self.assertIn(
            "operation_history",
            ownership_coverage["ownership_audit_missing_sections"],
        )
        child_gate_coverage = result["runtime_contract_summary"]["child_executor_promotion_gate_coverage"]
        self.assertTrue(child_gate_coverage["gate_smoke"])
        self.assertEqual(child_gate_coverage["contract_version"], "phase-ii-child-executor-gate-v1")
        self.assertEqual(child_gate_coverage["gate_status"], "blocked")
        self.assertFalse(child_gate_coverage["allowed"])
        self.assertEqual(child_gate_coverage["failure_reason"], "child_executor_preflight_blocked")
        self.assertEqual(child_gate_coverage["blocker_count"], 2)
        self.assertEqual(child_gate_coverage["recommended_next_step"], "keep_relationship_only")
        subagent_coverage = result["runtime_contract_summary"]["subagent_lane_query_detail_coverage"]
        self.assertTrue(subagent_coverage["detail_smoke"])
        self.assertEqual(subagent_coverage["contract_version"], "phase-h-subagent-lane-query-detail-v1")
        self.assertEqual(subagent_coverage["recording_state"], "recorded")
        self.assertEqual(subagent_coverage["stage_count"], 2)
        self.assertEqual(subagent_coverage["recent_event_count"], 2)
        schema_guard = result["runtime_contract_artifact_schema"]
        self.assertEqual(schema_guard["contract_version"], "phase-f-runtime-contract-artifact-schema-v1")
        self.assertEqual(schema_guard["overall_status"], "healthy")
        self.assertEqual(schema_guard["summary_missing_fields"], [])
        self.assertIn(
            "subagent_lane_query_detail_coverage.detail_smoke",
            schema_guard["summary_required_fields"],
        )
        self.assertIn(
            "approval_lifecycle_recovery_coverage.alignment_smoke",
            schema_guard["summary_required_fields"],
        )
        self.assertIn(
            "sdk_tool_runtime_execution_coverage.bridge_smoke",
            schema_guard["summary_required_fields"],
        )
        self.assertIn(
            "tool_runtime_timeout_retry_coverage.timeout_retry_smoke",
            schema_guard["summary_required_fields"],
        )
        self.assertIn(
            "embedded_sdk_persistence_coverage.persistence_smoke",
            schema_guard["summary_required_fields"],
        )
        self.assertIn(
            "worker_ownership_store_mode_coverage.mode_smoke",
            schema_guard["summary_required_fields"],
        )
        self.assertIn(
            "child_executor_promotion_gate_coverage.gate_smoke",
            schema_guard["summary_required_fields"],
        )

    def test_runtime_contract_summary_defaults_approval_lifecycle_recovery_coverage_for_legacy_reports(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
            {"name": "runtime_profile_contract_snapshot", "ok": True},
            {
                "name": "embedded_sdk_event_payloads",
                "ok": True,
                "observed_status_kinds": ["approval_replayed", "approval_ignored"],
            },
        ])

        coverage = summary["approval_lifecycle_recovery_coverage"]
        self.assertFalse(coverage["alignment_smoke"])
        self.assertEqual(coverage["replayed_submission_status"], "")
        self.assertEqual(coverage["ignored_submission_status"], "")
        self.assertEqual(coverage["resolved_recovery_reason"], "")

    def test_runtime_contract_summary_requires_production_retry_gate_blocked_evidence(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
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
            }
        ])

        coverage = summary["recovery_retry_scheduler_coverage"]
        self.assertTrue(coverage["scheduler_smoke"])
        self.assertEqual(
            coverage["production_gate_contract_version"],
            "phase-ii-recovery-retry-production-scheduler-gate-v1",
        )
        self.assertEqual(coverage["production_gate_status"], "blocked")
        self.assertFalse(coverage["production_automatic_will_execute"])

        dirty_summary = _build_runtime_contract_summary([
            {
                "name": "recovery_retry_scheduler",
                "ok": True,
                "contract_version": "phase-ii-recovery-retry-scheduler-v1",
                "default_status": "disabled",
                "default_eligible": True,
                "default_will_execute": False,
                "enabled_status": "executed",
                "enabled_will_execute": True,
                "latest_operation_status": "recovered",
                "attempt_number": 1,
                "retry_status": "retryable",
                "recovery_reason": "transient_workspace_unavailable",
                "previous_operation_id_present": True,
                "idempotency_key_present": True,
            }
        ])

        self.assertFalse(dirty_summary["recovery_retry_scheduler_coverage"]["scheduler_smoke"])

    def test_runtime_contract_summary_derives_tool_runtime_timeout_retry_coverage(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
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
            }
        ])

        coverage = summary["tool_runtime_timeout_retry_coverage"]
        self.assertTrue(coverage["timeout_retry_smoke"])
        self.assertEqual(coverage["retry_policy"], "sync_exception_retry")
        self.assertEqual(coverage["timeout_enforcement"], "post_call_elapsed_check")
        self.assertEqual(coverage["recovered_retry_status"], "recovered")
        self.assertEqual(coverage["exhausted_retry_status"], "exhausted")
        self.assertEqual(coverage["timeout_metadata_status"], "exceeded")

        dirty_summary = _build_runtime_contract_summary([
            {
                "name": "tool_runtime_timeout_retry",
                "ok": True,
                "retry_policy": "sync_exception_retry",
                "timeout_enforcement": "hard_cancellation",
                "recovered_status": "ok",
                "recovered_retry_status": "recovered",
                "recovered_attempt_count": 2,
                "exhausted_status": "error",
                "exhausted_retry_status": "exhausted",
                "exhausted_attempt_count": 2,
                "timeout_status": "timeout",
                "timeout_metadata_status": "exceeded",
                "timeout_metadata_enforcement": "hard_cancellation",
            }
        ])

        self.assertFalse(dirty_summary["tool_runtime_timeout_retry_coverage"]["timeout_retry_smoke"])

    def test_runtime_contract_artifact_schema_degrades_when_summary_nested_field_is_missing(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_artifact_schema

        schema_guard = _build_runtime_contract_artifact_schema({
            "overall_status": "healthy",
            "check_count": 1,
            "failed_check_count": 0,
            "missing_payload_count": 0,
            "approval_replay_coverage": {
                "event_payload_sample": True,
            },
            "approval_lifecycle_recovery_coverage": {
                "alignment_smoke": True,
            },
            "approved_tool_execution_coverage": {
                "bridge_smoke": True,
            },
            "worker_ownership_store_mode_coverage": {
                "mode_smoke": True,
            },
            "subagent_lane_query_detail_coverage": {
                "recording_state": "recorded",
            },
        })

        self.assertEqual(schema_guard["overall_status"], "degraded")
        self.assertIn(
            "subagent_lane_query_detail_coverage.detail_smoke",
            schema_guard["summary_missing_fields"],
        )

    def test_render_summary_includes_runtime_contract_summary_when_present(self):
        summary = _render_summary({
            "passed": True,
            "step_count": 1,
            "failed_steps": [],
            "steps": [
                {
                    "name": "Quality gate smoke",
                    "passed": True,
                    "exit_code": 0,
                    "duration_seconds": 0.1,
                    "contract_checks": [
                        {"name": "embedded_sdk_event_payloads", "ok": True, "failure_reason": ""},
                        {"name": "runtime_surface_run_recovery", "ok": True, "failure_reason": ""},
                    ],
                    "runtime_contract_summary": {
                        "overall_status": "healthy",
                        "check_count": 2,
                        "failed_check_count": 0,
                        "missing_payload_count": 0,
                        "approval_replay_coverage": {
                            "event_payload_sample": True,
                        },
                        "approval_lifecycle_recovery_coverage": {
                            "alignment_smoke": True,
                            "replayed_submission_status": "replayed",
                            "ignored_submission_status": "ignored",
                            "resolved_recovery_reason": "already_resolved",
                        },
            "approved_tool_execution_coverage": {
                "bridge_smoke": True,
            },
            "worker_ownership_store_mode_coverage": {
                "mode_smoke": True,
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
                "vendor_lock_contract_version": "phase-ii-worker-ownership-vendor-lock-semantics-v1",
                "vendor_lock_status": "blocked",
                "vendor_lock_missing_sections": ["vendor_lock_adapter", "target_decision"],
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
                "vendor_lock_adapter_missing_sections": ["adapter_kind", "target_backend"],
                "postgres_probe_contract_version": (
                    "phase-ii-worker-ownership-postgres-vendor-lock-probe-v1"
                ),
                "postgres_probe_status": "blocked",
                "postgres_probe_missing_sections": ["advisory_lock_family", "probe_safety"],
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
                "postgres_execution_default_missing_sections": ["executor_binding"],
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
                "vendor_lock_target_input_missing_sections": ["input_source_kind", "decision_id"],
                "vendor_lock_target_input_sql_row_lease_is_vendor_lock": False,
                "renewal_supervisor_contract_version": (
                    "phase-ii-worker-ownership-renewal-supervisor-v1"
                ),
                "renewal_supervisor_status": "blocked",
                "renewal_supervisor_missing_sections": ["background_supervisor"],
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
                "rollout_missing_sections": ["strict_mode_rollout"],
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
                "rollout_confirmation_missing_sections": ["decision_recorded"],
                "rollout_confirmation_production_rollout_confirmed": False,
                "rollout_confirmation_input_contract_version": (
                    "phase-ii-worker-ownership-rollout-confirmation-input-source-v1"
                ),
                "rollout_confirmation_input_source_status": "blocked",
                "rollout_confirmation_input_source_kind": "",
                "rollout_confirmation_input_decision_id": "",
                "rollout_confirmation_input_missing_sections": [
                    "input_source_kind",
                    "decision_id",
                ],
                "rollout_confirmation_input_sql_row_lease_is_authority": False,
                "ownership_audit_contract_version": "phase-ii-worker-ownership-audit-evidence-v1",
                "ownership_audit_status": "blocked",
                "ownership_audit_missing_sections": ["operation_history"],
                "ownership_audit_compact_evidence": True,
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
                "enablement_input_source_missing_sections": ["input_source_kind"],
                "enablement_explicit_required": True,
                "enablement_all_required_sections_ready": False,
                "enablement_fail_closed_when_blocked": True,
                "enablement_sql_row_lease_not_default_authority": True,
            },
            "subagent_lane_query_detail_coverage": {
                "detail_smoke": True,
            },
            "child_executor_dispatch_coverage": {
                "dispatch_smoke": True,
                "contract_version": "phase-ii-child-executor-dispatch-v1",
                "overall_status": "blocked",
                "dispatch_ready": False,
                "will_dispatch": False,
                "backend_dispatch_ready": False,
                "relationship_seam_preserved": True,
                "blocker_count": 1,
                "dispatch_blockers": ["explicit_executor_binding_opt_in"],
                "explicit_executor_binding_ready": False,
                "explicit_executor_binding_status": "blocked",
                "opt_in_dispatch_status": "ready",
                "opt_in_dispatch_ready": True,
                "opt_in_will_dispatch": False,
                "opt_in_backend_dispatch_ready": True,
                "opt_in_ready_dispatch_status": "ready",
                "opt_in_ready_dispatch_ready": True,
                "opt_in_ready_handoff_ready": True,
                "opt_in_ready_will_dispatch": False,
                "opt_in_sandbox_dispatch_ready": True,
                "opt_in_sandbox_execution_seam_supported": True,
                "opt_in_sandbox_payload_idempotency_ready": True,
                "missing_idempotency_dispatch_status": "blocked",
                "missing_idempotency_dispatch_ready": False,
                "missing_idempotency_dispatch_blockers": ["sandbox_payload_idempotency_ready"],
                "unsafe_dispatch_status": "blocked",
                "unsafe_dispatch_ready": False,
                "unsafe_dispatch_blockers": ["sandbox_payload_unsafe"],
                "unsafe_dispatch_payload_keys": ["handler"],
                "opt_in_explicit_executor_binding_ready": True,
                "opt_in_explicit_executor_binding_status": "ready",
                "dispatch_attempt_handoff_status": "blocked",
                "dispatch_attempt_handoff_ready": False,
                "dispatch_attempt_handoff_missing_sections": ["dispatch_contract_ready"],
                "dispatch_attempt_handoff_will_dispatch": False,
                "opt_in_dispatch_attempt_handoff_status": "ready",
                "opt_in_dispatch_attempt_handoff_ready": True,
                "opt_in_attempt_envelope_supported": True,
                "opt_in_attempt_validation_ready": True,
                "opt_in_attempt_will_dispatch": False,
                "opt_in_unsafe_payload_guard_ready": True,
                "unsafe_payload_guard_status": "blocked",
                "unsafe_payload_guard_ready": False,
                "unsafe_payload_keys": ["handler"],
                "recommended_next_step": "implement_child_executor_backend_dispatch",
            },
                    },
                }
            ],
        })

        self.assertIn("## Runtime Contract Summary", summary)
        self.assertIn("| Step | Status | Checks | Failed | Missing Payloads | Approval Replay Coverage | Approval Lifecycle Recovery | Approved Tool Bridge | SDK Tool Bridge | Checkpoint Cursor | Worker Ownership Mode | Recovery Audit | Registry/Checkpoint Policy | Recovery Retry | Retry Scheduler | Durable Loader | Descriptor Lifecycle | Loader Handoff | Child Executor Gate | Child Executor Dispatch | Child Executor Dispatcher | Child Result Handoff | Child Retry Audit | Child Sandbox Binding | Subagent Lane Detail |", summary)
        self.assertIn("| Quality gate smoke | healthy | 2 | 0 | 0 | yes | yes | yes | no | no | yes | no | no | no | no | no | no | no | no | yes | no | no | no | no | yes |", summary)

    def test_render_summary_fails_closed_when_approval_lifecycle_recovery_evidence_disagrees(self):
        summary = _render_summary({
            "passed": True,
            "step_count": 1,
            "failed_steps": [],
            "steps": [
                {
                    "name": "Quality gate smoke",
                    "passed": True,
                    "exit_code": 0,
                    "duration_seconds": 0.1,
                    "runtime_contract_summary": {
                        "overall_status": "healthy",
                        "check_count": 1,
                        "failed_check_count": 0,
                        "missing_payload_count": 0,
                        "approval_replay_coverage": {
                            "event_payload_sample": True,
                        },
                        "approval_lifecycle_recovery_coverage": {
                            "alignment_smoke": True,
                            "replayed_submission_status": "replayed",
                            "ignored_submission_status": "accepted",
                            "resolved_recovery_reason": "already_resolved",
                        },
                        "approved_tool_execution_coverage": {
                            "bridge_smoke": True,
                        },
                        "worker_ownership_store_mode_coverage": {
                            "mode_smoke": True,
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
                            "vendor_lock_contract_version": "phase-ii-worker-ownership-vendor-lock-semantics-v1",
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
                            "renewal_supervisor_missing_sections": ["background_supervisor"],
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
                            "rollout_missing_sections": ["strict_mode_rollout"],
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
                            "rollout_confirmation_missing_sections": ["decision_recorded"],
                            "rollout_confirmation_production_rollout_confirmed": False,
                            "rollout_confirmation_input_contract_version": (
                                "phase-ii-worker-ownership-rollout-confirmation-input-source-v1"
                            ),
                            "rollout_confirmation_input_source_status": "blocked",
                            "rollout_confirmation_input_source_kind": "",
                            "rollout_confirmation_input_decision_id": "",
                            "rollout_confirmation_input_missing_sections": [
                                "input_source_kind",
                                "decision_id",
                            ],
                            "rollout_confirmation_input_sql_row_lease_is_authority": False,
                            "ownership_audit_contract_version": "phase-ii-worker-ownership-audit-evidence-v1",
                            "ownership_audit_status": "blocked",
                            "ownership_audit_missing_sections": ["operation_history"],
                            "ownership_audit_compact_evidence": True,
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
                        "subagent_lane_query_detail_coverage": {
                            "detail_smoke": True,
                        },
                        "child_executor_dispatch_coverage": {
                            "dispatch_smoke": True,
                            "contract_version": "phase-ii-child-executor-dispatch-v1",
                            "overall_status": "blocked",
                            "dispatch_ready": False,
                            "will_dispatch": False,
                            "backend_dispatch_ready": False,
                            "relationship_seam_preserved": True,
                            "blocker_count": 1,
                            "dispatch_blockers": ["explicit_executor_binding_opt_in"],
                            "explicit_executor_binding_ready": False,
                            "explicit_executor_binding_status": "blocked",
                            "opt_in_dispatch_status": "ready",
                            "opt_in_dispatch_ready": True,
                            "opt_in_will_dispatch": False,
                            "opt_in_backend_dispatch_ready": True,
                            "opt_in_ready_dispatch_status": "ready",
                            "opt_in_ready_dispatch_ready": True,
                            "opt_in_ready_handoff_ready": True,
                            "opt_in_ready_will_dispatch": False,
                            "opt_in_sandbox_dispatch_ready": True,
                            "opt_in_sandbox_execution_seam_supported": True,
                            "opt_in_sandbox_payload_idempotency_ready": True,
                            "missing_idempotency_dispatch_status": "blocked",
                            "missing_idempotency_dispatch_ready": False,
                            "missing_idempotency_dispatch_blockers": [
                                "sandbox_payload_idempotency_ready"
                            ],
                            "unsafe_dispatch_status": "blocked",
                            "unsafe_dispatch_ready": False,
                            "unsafe_dispatch_blockers": ["sandbox_payload_unsafe"],
                            "unsafe_dispatch_payload_keys": ["handler"],
                            "opt_in_explicit_executor_binding_ready": True,
                            "opt_in_explicit_executor_binding_status": "ready",
                            "dispatch_attempt_handoff_status": "blocked",
                            "dispatch_attempt_handoff_ready": False,
                            "dispatch_attempt_handoff_missing_sections": ["dispatch_contract_ready"],
                            "dispatch_attempt_handoff_will_dispatch": False,
                            "opt_in_dispatch_attempt_handoff_status": "ready",
                            "opt_in_dispatch_attempt_handoff_ready": True,
                            "opt_in_attempt_envelope_supported": True,
                            "opt_in_attempt_validation_ready": True,
                            "opt_in_attempt_will_dispatch": False,
                            "opt_in_unsafe_payload_guard_ready": True,
                            "unsafe_payload_guard_status": "blocked",
                            "unsafe_payload_guard_ready": False,
                            "unsafe_payload_keys": ["handler"],
                            "recommended_next_step": "implement_child_executor_backend_dispatch",
                        },
                    },
                }
            ],
        })

        self.assertIn("| Quality gate smoke | healthy | 1 | 0 | 0 | yes | no | yes | no | no | yes | no | no | no | no | no | no | no | no | yes | no | no | no | no | yes |", summary)

    def test_runtime_contract_summary_defaults_child_executor_promotion_gate_coverage_for_legacy_reports(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
            {"name": "runtime_profile_contract_snapshot", "ok": True},
        ])

        coverage = summary["child_executor_promotion_gate_coverage"]
        self.assertFalse(coverage["gate_smoke"])
        self.assertEqual(coverage["contract_version"], "")
        self.assertEqual(coverage["gate_status"], "")

    def test_runtime_contract_summary_requires_complete_child_executor_promotion_gate_evidence(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
            {
                "name": "child_executor_promotion_gate",
                "ok": True,
                "contract_version": "phase-ii-child-executor-gate-v1",
                "gate_status": "blocked",
                "allowed": False,
                "gate_failure_reason": "",
                "blocker_count": 1,
                "recommended_next_step": "keep_relationship_only",
            },
        ])

        coverage = summary["child_executor_promotion_gate_coverage"]
        self.assertFalse(coverage["gate_smoke"])
        self.assertEqual(coverage["failure_reason"], "")

    def test_runtime_contract_summary_defaults_child_executor_dispatch_coverage_for_legacy_reports(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
            {"name": "runtime_profile_contract_snapshot", "ok": True},
        ])

        coverage = summary["child_executor_dispatch_coverage"]
        self.assertFalse(coverage["dispatch_smoke"])
        self.assertEqual(coverage["contract_version"], "")
        self.assertEqual(coverage["overall_status"], "")

    def test_runtime_contract_summary_requires_complete_child_executor_dispatch_evidence(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
            {
                "name": "child_executor_dispatch_contract",
                "ok": True,
                "contract_version": "phase-ii-child-executor-dispatch-v1",
                "dispatch_status": "blocked",
                "dispatch_ready": False,
                "will_dispatch": False,
                "backend_dispatch_ready": False,
                "relationship_seam_preserved": True,
                "dispatch_blocker_count": 0,
                "recommended_next_step": "implement_child_executor_backend_dispatch",
            },
        ])

        coverage = summary["child_executor_dispatch_coverage"]
        self.assertFalse(coverage["dispatch_smoke"])
        self.assertEqual(coverage["blocker_count"], 0)

    def test_runtime_contract_summary_derives_child_executor_dispatcher_coverage(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
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
        ])

        coverage = summary["child_executor_dispatcher_coverage"]
        self.assertTrue(coverage["dispatcher_smoke"])
        self.assertEqual(coverage["contract_version"], "phase-ii-child-executor-dispatcher-v1")
        self.assertEqual(coverage["default_blocked_reason"], "dispatcher_disabled")
        self.assertEqual(coverage["blocked_reason"], "dispatch_contract_not_ready")
        self.assertEqual(coverage["backend_invocation_count"], 1)

    def test_runtime_contract_summary_fails_closed_when_child_executor_dispatcher_evidence_disagrees(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
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
                "backend_invocation_count": 2,
            },
        ])

        coverage = summary["child_executor_dispatcher_coverage"]
        self.assertFalse(coverage["dispatcher_smoke"])
        self.assertEqual(coverage["backend_invocation_count"], 2)

    def test_runtime_contract_summary_derives_child_executor_retry_scheduler_handoff_coverage(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
            {
                "name": "child_executor_dispatch_retry_scheduler_handoff",
                "ok": True,
                "contract_version": "phase-ii-child-executor-dispatch-retry-scheduler-handoff-v1",
                "default_status": "blocked",
                "default_handoff_ready": False,
                "default_retryable_result_detected": True,
                "default_scheduler_bound": False,
                "default_missing_sections": ["scheduler_binding"],
                "default_will_schedule_retry": False,
                "missing_idempotency_status": "blocked",
                "missing_idempotency_sections": ["idempotency_evidence"],
                "missing_audit_status": "blocked",
                "missing_audit_sections": ["audit_evidence"],
                "terminal_status": "blocked",
                "terminal_retryable_result_detected": False,
                "terminal_missing_sections": ["retryable_policy"],
                "bound_status": "ready",
                "bound_handoff_ready": True,
                "bound_scheduler_bound": True,
                "bound_will_schedule_retry": False,
            },
        ])

        coverage = summary["child_executor_dispatch_retry_scheduler_handoff_coverage"]
        self.assertTrue(coverage["handoff_smoke"])
        self.assertEqual(
            coverage["contract_version"],
            "phase-ii-child-executor-dispatch-retry-scheduler-handoff-v1",
        )
        self.assertEqual(coverage["default_status"], "blocked")
        self.assertEqual(coverage["bound_status"], "ready")
        self.assertFalse(coverage["bound_will_schedule_retry"])

    def test_runtime_contract_summary_fails_closed_when_child_executor_retry_scheduler_handoff_evidence_disagrees(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
            {
                "name": "child_executor_dispatch_retry_scheduler_handoff",
                "ok": True,
                "contract_version": "phase-ii-child-executor-dispatch-retry-scheduler-handoff-v1",
                "default_status": "blocked",
                "default_handoff_ready": False,
                "default_retryable_result_detected": True,
                "default_scheduler_bound": False,
                "default_missing_sections": ["scheduler_binding"],
                "default_will_schedule_retry": False,
                "missing_idempotency_status": "blocked",
                "missing_idempotency_sections": ["idempotency_evidence"],
                "missing_audit_status": "blocked",
                "missing_audit_sections": ["audit_evidence"],
                "terminal_status": "blocked",
                "terminal_retryable_result_detected": False,
                "terminal_missing_sections": ["retryable_policy"],
                "bound_status": "ready",
                "bound_handoff_ready": True,
                "bound_scheduler_bound": True,
                "bound_will_schedule_retry": True,
            },
        ])

        coverage = summary["child_executor_dispatch_retry_scheduler_handoff_coverage"]
        self.assertFalse(coverage["handoff_smoke"])
        self.assertTrue(coverage["bound_will_schedule_retry"])

    def test_runtime_contract_summary_derives_child_executor_retry_scheduler_binding_gate_coverage(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
            {
                "name": "child_executor_dispatch_retry_scheduler_binding_gate",
                "ok": True,
                "contract_version": "phase-ii-child-executor-dispatch-retry-scheduler-binding-gate-v1",
                "default_status": "blocked",
                "default_handoff_ready": True,
                "default_binding_ready": False,
                "default_missing_sections": ["scheduler_binding_decision"],
                "default_will_schedule_retry": False,
                "ready_status": "ready",
                "ready_binding_ready": True,
                "ready_binding_source": "runtime_config.child_dispatch_retry_scheduler",
                "ready_will_schedule_retry": False,
                "production_blocked_status": "blocked",
                "production_blocked_sections": ["production_scheduler_gate"],
                "missing_audit_idempotency_status": "blocked",
                "missing_audit_idempotency_sections": ["idempotency_dedupe", "audit_timeline"],
                "missing_worker_attempts_status": "blocked",
                "missing_worker_attempts_sections": ["worker_ownership", "bounded_attempts"],
            },
        ])

        coverage = summary["child_executor_dispatch_retry_scheduler_binding_gate_coverage"]
        self.assertTrue(coverage["binding_smoke"])
        self.assertEqual(
            coverage["contract_version"],
            "phase-ii-child-executor-dispatch-retry-scheduler-binding-gate-v1",
        )
        self.assertEqual(coverage["default_status"], "blocked")
        self.assertEqual(coverage["ready_status"], "ready")
        self.assertFalse(coverage["ready_will_schedule_retry"])

    def test_runtime_contract_summary_fails_closed_when_child_executor_retry_scheduler_binding_gate_evidence_disagrees(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
            {
                "name": "child_executor_dispatch_retry_scheduler_binding_gate",
                "ok": True,
                "contract_version": "phase-ii-child-executor-dispatch-retry-scheduler-binding-gate-v1",
                "default_status": "blocked",
                "default_handoff_ready": True,
                "default_binding_ready": False,
                "default_missing_sections": ["scheduler_binding_decision"],
                "default_will_schedule_retry": False,
                "ready_status": "ready",
                "ready_binding_ready": True,
                "ready_binding_source": "runtime_config.child_dispatch_retry_scheduler",
                "ready_will_schedule_retry": True,
                "production_blocked_status": "blocked",
                "production_blocked_sections": ["production_scheduler_gate"],
                "missing_audit_idempotency_status": "blocked",
                "missing_audit_idempotency_sections": ["idempotency_dedupe", "audit_timeline"],
                "missing_worker_attempts_status": "blocked",
                "missing_worker_attempts_sections": ["worker_ownership", "bounded_attempts"],
            },
        ])

        coverage = summary["child_executor_dispatch_retry_scheduler_binding_gate_coverage"]
        self.assertFalse(coverage["binding_smoke"])
        self.assertTrue(coverage["ready_will_schedule_retry"])

    def test_runtime_contract_summary_derives_child_executor_retry_scheduler_execution_authorization_coverage(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
            {
                "name": "child_executor_dispatch_retry_scheduler_execution_authorization",
                "ok": True,
                "contract_version": "phase-ii-child-executor-dispatch-retry-scheduler-execution-authorization-v1",
                "default_status": "blocked",
                "default_binding_gate_ready": True,
                "default_authorization_ready": False,
                "default_missing_sections": ["execution_authorization_request"],
                "default_will_schedule_retry": False,
                "default_retry_scheduled": False,
                "ready_status": "ready",
                "ready_authorization_ready": True,
                "ready_authorization_source": "runtime_config.child_dispatch_retry_scheduler_execution",
                "ready_will_schedule_retry": False,
                "ready_retry_scheduled": False,
                "production_blocked_status": "blocked",
                "production_blocked_sections": ["production_scheduler_gate"],
                "missing_durable_status": "blocked",
                "missing_durable_sections": ["durable_schedule_state"],
                "missing_audit_idempotency_status": "blocked",
                "missing_audit_idempotency_sections": ["idempotency_dedupe", "audit_timeline"],
                "missing_worker_attempts_status": "blocked",
                "missing_worker_attempts_sections": ["worker_ownership", "bounded_attempts"],
            },
        ])

        coverage = summary[
            "child_executor_dispatch_retry_scheduler_execution_authorization_coverage"
        ]
        self.assertTrue(coverage["authorization_smoke"])
        self.assertEqual(
            coverage["contract_version"],
            "phase-ii-child-executor-dispatch-retry-scheduler-execution-authorization-v1",
        )
        self.assertEqual(coverage["default_status"], "blocked")
        self.assertEqual(coverage["ready_status"], "ready")
        self.assertFalse(coverage["ready_will_schedule_retry"])
        self.assertFalse(coverage["ready_retry_scheduled"])

    def test_runtime_contract_summary_fails_closed_when_child_executor_retry_scheduler_execution_authorization_evidence_disagrees(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
            {
                "name": "child_executor_dispatch_retry_scheduler_execution_authorization",
                "ok": True,
                "contract_version": "phase-ii-child-executor-dispatch-retry-scheduler-execution-authorization-v1",
                "default_status": "blocked",
                "default_binding_gate_ready": True,
                "default_authorization_ready": False,
                "default_missing_sections": ["execution_authorization_request"],
                "default_will_schedule_retry": False,
                "default_retry_scheduled": False,
                "ready_status": "ready",
                "ready_authorization_ready": True,
                "ready_authorization_source": "runtime_config.child_dispatch_retry_scheduler_execution",
                "ready_will_schedule_retry": True,
                "ready_retry_scheduled": False,
                "production_blocked_status": "blocked",
                "production_blocked_sections": ["production_scheduler_gate"],
                "missing_durable_status": "blocked",
                "missing_durable_sections": ["durable_schedule_state"],
                "missing_audit_idempotency_status": "blocked",
                "missing_audit_idempotency_sections": ["idempotency_dedupe", "audit_timeline"],
                "missing_worker_attempts_status": "blocked",
                "missing_worker_attempts_sections": ["worker_ownership", "bounded_attempts"],
            },
        ])

        coverage = summary[
            "child_executor_dispatch_retry_scheduler_execution_authorization_coverage"
        ]
        self.assertFalse(coverage["authorization_smoke"])
        self.assertTrue(coverage["ready_will_schedule_retry"])

    def test_runtime_contract_summary_derives_child_executor_sandbox_backend_coverage(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
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
                "execution_seam_supported": True,
                "execution_default_enabled": False,
                "execution_completed_status": "completed",
                "execution_completed_valid": True,
                "execution_completed_will_dispatch": True,
                "execution_missing_idempotency_status": "blocked",
                "execution_missing_idempotency_error_code": "sandbox_payload_missing_fields",
                "execution_unsafe_status": "blocked",
                "execution_unsafe_error_code": "sandbox_payload_unsafe",
                "execution_handler_failure_status": "failed",
                "execution_handler_failure_error_code": "sandbox_executor_failed",
                "execution_handler_failure_retryable": True,
                "execution_invocation_count": 3,
                "execution_executor_invocation_count": 1,
                "execution_dispatcher_status": "dispatched",
                "execution_dispatcher_invocation_count": 1,
                "execution_parent_merge_performed": False,
                "execution_retry_scheduled": False,
                "execution_production_authorized": False,
            },
        ])

        coverage = summary["child_executor_sandbox_backend_coverage"]
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
        self.assertTrue(coverage["execution_seam_supported"])
        self.assertFalse(coverage["execution_default_enabled"])
        self.assertEqual(coverage["execution_completed_status"], "completed")
        self.assertEqual(coverage["execution_missing_idempotency_status"], "blocked")
        self.assertEqual(coverage["execution_handler_failure_status"], "failed")

    def test_runtime_contract_summary_fails_closed_when_child_executor_sandbox_backend_evidence_disagrees(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
            {
                "name": "child_executor_sandbox_backend",
                "ok": True,
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
                "execution_seam_supported": True,
                "execution_default_enabled": False,
                "execution_completed_status": "completed",
                "execution_completed_valid": True,
                "execution_completed_will_dispatch": True,
                "execution_missing_idempotency_status": "blocked",
                "execution_missing_idempotency_error_code": "sandbox_payload_missing_fields",
                "execution_unsafe_status": "blocked",
                "execution_unsafe_error_code": "sandbox_payload_unsafe",
                "execution_handler_failure_status": "failed",
                "execution_handler_failure_error_code": "sandbox_executor_failed",
                "execution_handler_failure_retryable": True,
                "execution_invocation_count": 3,
                "execution_executor_invocation_count": 1,
                "execution_dispatcher_status": "dispatched",
                "execution_dispatcher_invocation_count": 1,
                "execution_parent_merge_performed": False,
                "execution_retry_scheduled": False,
                "execution_production_authorized": False,
            },
        ])

        coverage = summary["child_executor_sandbox_backend_coverage"]
        self.assertFalse(coverage["sandbox_backend_smoke"])
        self.assertEqual(coverage["missing_guard_count"], 0)

    def test_runtime_contract_summary_defaults_worker_ownership_store_mode_coverage_for_legacy_reports(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
            {"name": "runtime_profile_contract_snapshot", "ok": True},
        ])

        coverage = summary["worker_ownership_store_mode_coverage"]
        self.assertFalse(coverage["mode_smoke"])
        self.assertEqual(coverage["default_mode"], "")
        self.assertEqual(coverage["strict_mode_status"], "")
        self.assertEqual(coverage["renewal_supervisor_status"], "")
        self.assertEqual(coverage["rollout_readiness_status"], "")
        self.assertEqual(coverage["auto_claim_policy_status"], "")
        self.assertEqual(coverage["ownership_audit_status"], "")
        self.assertFalse(coverage["enablement_config_factory_binding_smoke"])

    def test_runtime_contract_summary_requires_worker_ownership_config_factory_binding(
        self,
    ):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
            {
                "name": "worker_ownership_store_mode",
                "ok": True,
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
                "enablement_config_consumer_ready_lock_adapter_kind": "postgres_advisory_lock",
                "enablement_config_consumer_ready_input_source_status": "ready",
                "enablement_config_consumer_ready_dry_run_status": "ready",
                "enablement_config_consumer_ready_dry_run_would_allow": True,
                "enablement_config_consumer_ready_will_enable": False,
                "enablement_config_consumer_ready_executes_lock": False,
                "enablement_config_consumer_ready_starts_worker": False,
                "enablement_config_consumer_ready_runs_auto_claim": False,
                "enablement_config_factory_binding_default_status": "blocked",
                "enablement_config_factory_binding_ready_status": "ready",
                "enablement_config_factory_binding_ready_config_id": "factory-binding-001",
                "enablement_config_factory_binding_will_enable": False,
                "enablement_config_factory_binding_executes_lock": False,
                "enablement_config_factory_binding_starts_worker": False,
                "enablement_config_factory_binding_runs_auto_claim": False,
            },
        ])

        coverage = summary["worker_ownership_store_mode_coverage"]
        self.assertTrue(coverage["enablement_config_factory_binding_smoke"])
        self.assertEqual(
            coverage["enablement_config_factory_binding_ready_config_id"],
            "factory-binding-001",
        )

    def test_parse_embedded_structured_stdout_prefers_runtime_contract_checks(self):
        from backend.scripts.quality_gate_report import _parse_structured_stdout

        payload = _parse_structured_stdout(
            '==> smoke_check.py\n{"status":"ok","checks":[{"path":"/api/health","ok":true}]}\n'
            '==> runtime_contract_smoke.py\n'
            '{"status":"ok","checks":[{"name":"runtime_profile_contract_snapshot","ok":true},'
            '{"name":"worker_ownership_store_mode","ok":true}]}\n'
        )

        self.assertEqual(payload["checks"][0]["name"], "runtime_profile_contract_snapshot")
        self.assertEqual(payload["checks"][1]["name"], "worker_ownership_store_mode")

    def test_runtime_contract_summary_requires_complete_worker_ownership_store_mode_evidence(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
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
                "fallback_mode_status": "missing",
                "production_gate_contract_version": "phase-ii-worker-ownership-production-gate-v1",
                "production_gate_status": "blocked",
                "production_gate_missing_sections": [
                    "vendor_lock_semantics",
                    "heartbeat_renewal_supervisor",
                ],
                "production_default_enabled": False,
                "renewal_supervisor_contract_version": "phase-ii-worker-ownership-renewal-supervisor-v1",
                "renewal_supervisor_status": "blocked",
                "renewal_supervisor_missing_sections": ["background_supervisor"],
                "renewal_supervisor_enabled_by_default": False,
                "renewal_supervisor_lease_loss_fail_closed": True,
                "rollout_readiness_contract_version": "phase-ii-worker-ownership-rollout-readiness-v1",
                "rollout_readiness_status": "blocked",
                "rollout_missing_sections": ["strict_mode_rollout"],
                "production_rollout_confirmed": False,
                "rollout_migration_ready": True,
                "rollout_stale_fencing_verified": True,
                "rollout_rollback_plan_ready": False,
                "auto_claim_policy_contract_version": "phase-ii-worker-ownership-auto-claim-policy-v1",
                "auto_claim_policy_status": "blocked",
                "auto_claim_missing_sections": ["explicit_runtime_configuration"],
                "auto_claim_enabled_by_default": False,
                "auto_claim_descriptor_evidence_fallback": True,
                "auto_claim_lease_validation_required": True,
                "auto_claim_entrypoint_allowlist_ready": False,
            },
        ])

        coverage = summary["worker_ownership_store_mode_coverage"]
        self.assertFalse(coverage["mode_smoke"])
        self.assertEqual(coverage["fallback_mode_status"], "missing")

    def test_runtime_contract_summary_requires_renewal_supervisor_evidence_for_worker_ownership_mode(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
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
                ],
                "production_default_enabled": False,
            },
        ])

        coverage = summary["worker_ownership_store_mode_coverage"]
        self.assertFalse(coverage["mode_smoke"])
        self.assertEqual(coverage["renewal_supervisor_status"], "")

    def test_runtime_contract_summary_requires_rollout_evidence_for_worker_ownership_mode(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
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
                    "rollout_checklist",
                ],
                "production_default_enabled": False,
                "renewal_supervisor_contract_version": "phase-ii-worker-ownership-renewal-supervisor-v1",
                "renewal_supervisor_status": "blocked",
                "renewal_supervisor_missing_sections": ["background_supervisor"],
                "renewal_supervisor_enabled_by_default": False,
                "renewal_supervisor_lease_loss_fail_closed": True,
            },
        ])

        coverage = summary["worker_ownership_store_mode_coverage"]
        self.assertFalse(coverage["mode_smoke"])
        self.assertEqual(coverage["rollout_readiness_status"], "")

    def test_runtime_contract_summary_requires_auto_claim_policy_evidence_for_worker_ownership_mode(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
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
                    "rollout_checklist",
                    "recovery_entry_auto_claim_policy",
                ],
                "production_default_enabled": False,
                "renewal_supervisor_contract_version": "phase-ii-worker-ownership-renewal-supervisor-v1",
                "renewal_supervisor_status": "blocked",
                "renewal_supervisor_missing_sections": ["background_supervisor"],
                "renewal_supervisor_enabled_by_default": False,
                "renewal_supervisor_lease_loss_fail_closed": True,
                "rollout_readiness_contract_version": "phase-ii-worker-ownership-rollout-readiness-v1",
                "rollout_readiness_status": "blocked",
                "rollout_missing_sections": ["strict_mode_rollout"],
                "production_rollout_confirmed": False,
                "rollout_migration_ready": True,
                "rollout_stale_fencing_verified": True,
                "rollout_rollback_plan_ready": False,
            },
        ])

        coverage = summary["worker_ownership_store_mode_coverage"]
        self.assertFalse(coverage["mode_smoke"])
        self.assertEqual(coverage["auto_claim_policy_status"], "")

    def test_runtime_contract_summary_requires_audit_evidence_for_worker_ownership_mode(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
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
                    "rollout_checklist",
                    "recovery_entry_auto_claim_policy",
                    "ownership_audit_evidence",
                ],
                "production_default_enabled": False,
                "renewal_supervisor_contract_version": "phase-ii-worker-ownership-renewal-supervisor-v1",
                "renewal_supervisor_status": "blocked",
                "renewal_supervisor_missing_sections": ["background_supervisor"],
                "renewal_supervisor_enabled_by_default": False,
                "renewal_supervisor_lease_loss_fail_closed": True,
                "rollout_readiness_contract_version": "phase-ii-worker-ownership-rollout-readiness-v1",
                "rollout_readiness_status": "blocked",
                "rollout_missing_sections": ["strict_mode_rollout"],
                "production_rollout_confirmed": False,
                "rollout_migration_ready": True,
                "rollout_stale_fencing_verified": True,
                "rollout_rollback_plan_ready": False,
                "auto_claim_policy_contract_version": "phase-ii-worker-ownership-auto-claim-policy-v1",
                "auto_claim_policy_status": "blocked",
                "auto_claim_missing_sections": ["explicit_runtime_configuration"],
                "auto_claim_enabled_by_default": False,
                "auto_claim_descriptor_evidence_fallback": True,
                "auto_claim_lease_validation_required": True,
                "auto_claim_entrypoint_allowlist_ready": False,
            },
        ])

        coverage = summary["worker_ownership_store_mode_coverage"]
        self.assertFalse(coverage["mode_smoke"])
        self.assertEqual(coverage["ownership_audit_status"], "")

    def test_runtime_contract_summary_defaults_recovery_retry_evidence_coverage_for_legacy_reports(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
            {"name": "runtime_profile_contract_snapshot", "ok": True},
        ])

        coverage = summary["recovery_retry_evidence_coverage"]
        self.assertFalse(coverage["retry_smoke"])
        self.assertEqual(coverage["contract_version"], "")
        self.assertEqual(coverage["attempt_number"], 0)
        self.assertEqual(coverage["retry_status"], "")

    def test_runtime_contract_summary_requires_complete_recovery_retry_evidence(self):
        from backend.scripts.quality_gate_report import _build_runtime_contract_summary

        summary = _build_runtime_contract_summary([
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
                "idempotency_key_present": False,
            },
        ])

        coverage = summary["recovery_retry_evidence_coverage"]
        self.assertFalse(coverage["retry_smoke"])
        self.assertFalse(coverage["idempotency_key_present"])

    def test_render_summary_includes_runtime_contract_artifact_schema_when_present(self):
        summary = _render_summary({
            "passed": False,
            "step_count": 1,
            "failed_steps": [],
            "steps": [
                {
                    "name": "Quality gate smoke",
                    "passed": False,
                    "exit_code": 1,
                    "duration_seconds": 0.1,
                    "runtime_contract_artifact_schema": {
                        "contract_version": "phase-f-runtime-contract-artifact-schema-v1",
                        "overall_status": "degraded",
                        "summary_required_fields": ["overall_status", "subagent_lane_query_detail_coverage.detail_smoke"],
                        "summary_missing_fields": ["subagent_lane_query_detail_coverage.detail_smoke"],
                    },
                }
            ],
        })

        self.assertIn("## Runtime Contract Artifact Schema", summary)
        self.assertIn("| Quality gate smoke | degraded | subagent_lane_query_detail_coverage.detail_smoke |", summary)

    def test_render_summary_escapes_runtime_contract_summary_table_cells(self):
        summary = _render_summary({
            "passed": True,
            "step_count": 1,
            "failed_steps": [],
            "steps": [
                {
                    "name": "Quality | gate",
                    "passed": True,
                    "exit_code": 0,
                    "duration_seconds": 0.1,
                    "runtime_contract_summary": {
                        "overall_status": "healthy|manual",
                        "check_count": "2|bad",
                        "failed_check_count": "1\nline",
                        "missing_payload_count": "0|bad",
                        "approval_replay_coverage": {
                            "event_payload_sample": True,
                        },
                    },
                }
            ],
        })

        self.assertIn("| Quality \\| gate | healthy\\|manual | 2\\|bad | 1 line | 0\\|bad | yes |", summary)

    def test_render_summary_ignores_non_object_runtime_contract_summary(self):
        summary = _render_summary({
            "passed": True,
            "step_count": 1,
            "failed_steps": [],
            "steps": [
                {
                    "name": "Quality gate",
                    "passed": True,
                    "exit_code": 0,
                    "duration_seconds": 0.1,
                    "runtime_contract_summary": "bad-summary",
                },
                {
                    "name": "Runtime contract smoke",
                    "passed": True,
                    "exit_code": 0,
                    "duration_seconds": 0.1,
                    "runtime_contract_summary": {
                        "overall_status": "healthy",
                        "check_count": 1,
                        "failed_check_count": 0,
                        "missing_payload_count": 0,
                        "approval_replay_coverage": {
                            "event_payload_sample": True,
                        },
                    },
                },
            ],
        })

        self.assertIn("## Runtime Contract Summary", summary)
        self.assertIn("| Runtime contract smoke | healthy | 1 | 0 | 0 | yes |", summary)
        self.assertNotIn("bad-summary", summary)

    def test_render_summary_treats_non_object_approval_replay_coverage_as_missing(self):
        summary = _render_summary({
            "passed": True,
            "step_count": 1,
            "failed_steps": [],
            "steps": [
                {
                    "name": "Runtime contract smoke",
                    "passed": True,
                    "exit_code": 0,
                    "duration_seconds": 0.1,
                    "runtime_contract_summary": {
                        "overall_status": "healthy",
                        "check_count": 1,
                        "failed_check_count": 0,
                        "missing_payload_count": 0,
                        "approval_replay_coverage": "covered",
                    },
                },
            ],
        })

        self.assertIn("## Runtime Contract Summary", summary)
        self.assertIn("| Runtime contract smoke | healthy | 1 | 0 | 0 | no |", summary)

    def test_render_summary_treats_string_false_approval_replay_coverage_as_missing(self):
        summary = _render_summary({
            "passed": True,
            "step_count": 1,
            "failed_steps": [],
            "steps": [
                {
                    "name": "Runtime contract smoke",
                    "passed": True,
                    "exit_code": 0,
                    "duration_seconds": 0.1,
                    "runtime_contract_summary": {
                        "overall_status": "healthy",
                        "check_count": 1,
                        "failed_check_count": 0,
                        "missing_payload_count": 0,
                        "approval_replay_coverage": {
                            "event_payload_sample": "false",
                        },
                    },
                },
            ],
        })

        self.assertIn("| Runtime contract smoke | healthy | 1 | 0 | 0 | no |", summary)

    @patch("backend.scripts.quality_gate_report.subprocess.run")
    def test_run_step_ignores_invalid_runtime_contract_payload_count(self, mock_run):
        mock_run.return_value = SimpleNamespace(
            returncode=1,
            stdout=(
                '{"status":"fail","checks":['
                '{"name":"runtime_profile_contract_snapshot","ok":true},'
                '{"name":"embedded_sdk_event_payloads","ok":false,'
                '"missing_payload_count":"unknown",'
                '"observed_status_kinds":["approval_replayed"]}'
                ']}'
            ),
            stderr="",
        )

        result = _run_step(GateStep("Backend runtime_contract_smoke.py", ["python", "backend/scripts/runtime_contract_smoke.py"]))

        self.assertFalse(result["passed"])
        self.assertEqual(result["runtime_contract_summary"]["overall_status"], "degraded")
        self.assertEqual(result["runtime_contract_summary"]["missing_payload_count"], 0)

    @patch("backend.scripts.quality_gate_report.subprocess.run")
    def test_run_step_ignores_non_list_observed_status_kinds(self, mock_run):
        mock_run.return_value = SimpleNamespace(
            returncode=0,
            stdout=(
                '{"status":"ok","checks":['
                '{"name":"embedded_sdk_event_payloads","ok":true,'
                '"missing_payload_count":0,'
                '"observed_status_kinds":"approval_replayed"}'
                ']}'
            ),
            stderr="",
        )

        result = _run_step(GateStep("Backend runtime_contract_smoke.py", ["python", "backend/scripts/runtime_contract_smoke.py"]))

        self.assertEqual(
            result["runtime_contract_summary"]["approval_replay_coverage"]["observed_status_kinds"],
            [],
        )

    @patch("backend.scripts.quality_gate_report.subprocess.run")
    def test_run_step_ignores_non_object_runtime_contract_checks(self, mock_run):
        mock_run.return_value = SimpleNamespace(
            returncode=1,
            stdout=(
                '{"status":"fail","checks":['
                '{"name":"runtime_profile_contract_snapshot","ok":true},'
                '"bad-check",'
                'null,'
                '{"name":"embedded_sdk_event_payloads","ok":false,"missing_payload_count":1}'
                ']}'
            ),
            stderr="",
        )

        result = _run_step(GateStep("Backend runtime_contract_smoke.py", ["python", "backend/scripts/runtime_contract_smoke.py"]))

        self.assertFalse(result["passed"])
        self.assertEqual(
            [item["name"] for item in result["contract_checks"]],
            ["runtime_profile_contract_snapshot", "embedded_sdk_event_payloads"],
        )
        self.assertEqual(result["runtime_contract_summary"]["check_count"], 2)
        self.assertEqual(result["runtime_contract_summary"]["failed_check_count"], 1)


if __name__ == "__main__":
    unittest.main()
