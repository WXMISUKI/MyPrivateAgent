import unittest

from backend.services.runtime_contract_snapshot_service import RuntimeContractSnapshotService


def _build_complete_profile():
    return {
        "tool_runtime": {
            "contract_version": "phase-b-tool-runtime-v1",
            "total_tools": 2,
            "base_tool_count": 1,
            "langchain_tool_count": 1,
            "tool_spec_count": 2,
            "doubao_definition_count": 1,
            "mcp_capability_count": 1,
            "high_risk_tool_count": 0,
            "tools": [],
            "mcp_capabilities": [],
        },
        "mcp_runtime": {
            "contract_version": "phase-b-mcp-runtime-v1",
            "overall_status": "healthy",
            "capability_count": 1,
            "enabled_servers": 1,
            "components": [],
        },
        "skill_contract": {
            "contract_version": "phase-b-skill-definition-v1",
            "total_definitions": 1,
            "definitions": [],
        },
        "memory_contract": {
            "contract_version": "phase-b-memory-entry-v1",
            "active": True,
            "loaded_layers": [],
            "missing_layers": [],
            "memory_entries": [],
            "layer_order": [],
        },
        "command_contract": {
            "contract_version": "phase-b-command-runtime-v1",
            "total_commands": 1,
            "command_definitions": [],
            "embedded_sdk": {
                "contract_version": "phase-b-embedded-sdk-v1",
                "methods": [],
                "volatile_runtime_state": [
                    "_runs",
                    "_events",
                    "_approvals",
                    "_artifacts",
                    "_tool_continuations",
                    "_loop_continuations",
                ],
                "persistence_seams": [
                    "run_workspace_snapshot",
                    "run_event_log",
                    "approval_snapshot",
                    "tool_approval_continuation_descriptor",
                    "loop_continuation_descriptor",
                    "artifact_store_seam",
                ],
                "recovery_entrypoints": [
                    {
                        "method": "probe_run_recovery",
                        "recovery_scope": "continuation_descriptor_recoverability_probe",
                        "cross_process_ready": False,
                        "requires_durable_workspace": False,
                        "requires_registry_bindings": False,
                    },
                    {
                        "method": "submit_approval",
                        "mode": "approved",
                        "recovery_scope": "approved_tool_continuation_resume",
                        "cross_process_ready": True,
                        "requires_durable_workspace": True,
                        "requires_registry_bindings": True,
                    },
                    {
                        "method": "resume_run",
                        "mode": "default",
                        "recovery_scope": "observing_to_generating_state_resume",
                        "cross_process_ready": False,
                        "requires_durable_workspace": False,
                        "requires_registry_bindings": False,
                    },
                    {
                        "method": "resume_run",
                        "mode": "continue_loop",
                        "recovery_scope": "observing_to_done_loop_continuation",
                        "cross_process_ready": True,
                        "requires_durable_workspace": True,
                        "requires_registry_bindings": True,
                    },
                ],
                "delegate_preflight": {
                    "contract_version": "phase-ii-child-executor-preflight-v1",
                    "status": "relationship_only",
                    "real_child_executor_ready": False,
                    "current_scope": ["create_child_run_relationship"],
                    "promotion_requirements": [
                        "child_run_recovery_boundary_defined",
                        "child_context_budget_defined",
                        "child_result_merge_semantics_defined",
                        "worker_runtime_backend_selected",
                    ],
                    "non_goals": ["real_child_executor_dispatch"],
                    "approved_reference_slices": [],
                },
                "event_status_kinds": [
                    {
                        "status_kind": "approval_created",
                        "required_payload": ["approval_request_id", "approval_request"],
                    },
                    {
                        "status_kind": "approval_resolved",
                        "required_payload": ["approval_request_id", "approval_request", "decision"],
                    },
                    {
                        "status_kind": "approval_replayed",
                        "required_payload": [
                            "approval_request_id",
                            "approval_request",
                            "original_decision",
                            "attempted_decision",
                        ],
                    },
                    {
                        "status_kind": "approval_ignored",
                        "required_payload": [
                            "approval_request_id",
                            "approval_request",
                            "original_decision",
                            "attempted_decision",
                        ],
                    },
                    {
                        "status_kind": "execution_loop_done",
                        "required_payload": ["run", "completed_steps"],
                    },
                    {
                        "status_kind": "loop_continuation_registered",
                        "required_payload": ["loop_continuation"],
                    },
                    {
                        "status_kind": "loop_continuation_consumed",
                        "required_payload": ["loop_continuation"],
                    },
                    {
                        "status_kind": "loop_continuation_discarded",
                        "required_payload": ["loop_continuation"],
                    },
                ],
            },
            "agent_harness_facade": {
                "contract_version": "phase-e-agent-harness-facade-v1",
                "runtime_backend": "EmbeddedAgentRuntimeSDK",
                "methods": [],
                "delegate_preflight": {
                    "contract_version": "phase-ii-child-executor-preflight-v1",
                    "status": "relationship_only",
                    "real_child_executor_ready": False,
                    "current_scope": ["create_child_run_relationship"],
                    "promotion_requirements": [
                        "child_run_recovery_boundary_defined",
                        "child_context_budget_defined",
                        "child_result_merge_semantics_defined",
                        "worker_runtime_backend_selected",
                    ],
                    "non_goals": ["real_child_executor_dispatch"],
                    "approved_reference_slices": [],
                },
            },
        },
        "adapter_health": {
            "contract_version": "phase-b-adapter-health-v1",
            "overall_status": "healthy",
            "adapter_count": 3,
            "unavailable_count": 0,
            "adapters": [],
        },
        "runtime_contract_gate": {
            "contract_version": "phase-f-runtime-contract-gate-v1",
            "available": True,
            "overall_status": "healthy",
            "check_count": 2,
            "failed_check_count": 0,
            "runtime_contract_summary": {
                "overall_status": "healthy",
                "check_count": 2,
                "failed_check_count": 0,
                "missing_payload_count": 0,
                "approval_replay_coverage": {
                    "event_payload_sample": True,
                    "observed_status_kinds": ["approval_replayed", "approval_ignored"],
                },
                "approval_lifecycle_recovery_coverage": {
                    "alignment_smoke": True,
                    "replayed_submission_status": "replayed",
                    "ignored_submission_status": "ignored",
                    "resolved_recovery_reason": "already_resolved",
                },
                "approved_tool_execution_coverage": {
                    "bridge_smoke": True,
                    "approved_tool_call_count": 1,
                    "approved_policy_original_status": "requires_approval",
                    "approved_policy_override_status": "approved",
                    "deny_override_status": "denied",
                    "deny_tool_call_count": 0,
                },
                "sdk_tool_runtime_execution_coverage": {
                    "bridge_smoke": True,
                    "auto_tool_call_count": 1,
                    "auto_tool_history_count": 1,
                    "approved_tool_call_count": 1,
                    "approved_policy_original_status": "approval_required",
                    "approved_policy_override_status": "approved",
                    "deny_override_status": "policy_denied",
                    "deny_tool_call_count": 0,
                },
                "tool_runtime_timeout_retry_coverage": {
                    "timeout_retry_smoke": True,
                    "retry_policy": "sync_exception_retry",
                    "timeout_enforcement": "post_call_elapsed_check",
                    "recovered_retry_status": "recovered",
                    "recovered_attempt_count": 2,
                    "exhausted_retry_status": "exhausted",
                    "exhausted_attempt_count": 2,
                    "timeout_metadata_status": "exceeded",
                    "timeout_metadata_enforcement": "post_call_elapsed_check",
                    "hard_cancellation_claimed": False,
                    "sandbox_execution_claimed": False,
                    "worker_timeout_claimed": False,
                },
                "checkpoint_resume_cursor_coverage": {
                    "cursor_smoke": True,
                    "checkpoint_status": "ready",
                    "checkpoint_kind": "approval_waiting",
                    "cursor_status": "ready",
                    "cursor_entrypoint": "submit_approval.approved",
                    "cursor_recovery_reason": "ready_via_registry",
                },
                "embedded_sdk_persistence_coverage": {
                    "persistence_smoke": True,
                    "contract_version": "phase-ii-embedded-sdk-persistence-interface-v1",
                    "memory_posture": "memory_preview",
                    "durable_posture": "durable_ready",
                    "degraded_posture": "durable_degraded",
                    "production_recovery_worker_ownership_gate_status": "blocked",
                    "production_recovery_worker_ownership_missing_sections": [
                        "vendor_lock_semantics",
                    ],
                },
                "embedded_sdk_production_recovery_authorization_coverage": {
                    "authorization_smoke": True,
                    "contract_version": "phase-ii-embedded-sdk-production-recovery-authorization-v1",
                    "blocked_status": "blocked",
                    "ready_status": "ready",
                },
                "worker_ownership_store_mode_coverage": {
                    "mode_smoke": True,
                    "enablement_config_factory_binding_smoke": True,
                    "default_mode": "memory_only",
                    "default_mode_source": "default",
                    "default_adapter_kind": "in_memory",
                    "default_durable": False,
                    "configurable_knob_present": True,
                    "hot_reloadable_knob_present": True,
                    "strict_mode_status": "sqlalchemy_durable",
                    "fallback_mode_status": "fallback_to_memory",
                },
                "recovery_retry_evidence_coverage": {
                    "retry_smoke": True,
                    "contract_version": "phase-ii-recovery-retry-protocol-v1",
                    "attempt_number": 3,
                    "max_attempts": 3,
                    "retry_status": "exhausted",
                    "retryable": True,
                    "terminal": True,
                    "recovery_reason": "workspace_backend_not_durable",
                    "idempotency_key_present": True,
                },
                "recovery_retry_scheduler_coverage": {
                    "scheduler_smoke": True,
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
                },
                "durable_recovery_loader_coverage": {
                    "loader_smoke": True,
                    "contract_version": "phase-ii-durable-recovery-loader-v1",
                    "loader_status": "ready",
                    "loader_ready": True,
                    "loader_recovery_reason": "ready_via_registry",
                    "all_bindings_resolved": True,
                    "missing_recovery_reason": "run_snapshot_missing",
                    "unsafe_recovery_reason": "descriptor_corrupted",
                    "executes_recovery": False,
                    "deserializes_callables": False,
                },
                "continuation_descriptor_lifecycle_coverage": {
                    "lifecycle_smoke": True,
                    "contract_version": "phase-ii-continuation-descriptor-lifecycle-governance-v1",
                    "governed": True,
                    "states": ["ready", "bound", "stale", "unsafe"],
                    "all_ready": True,
                    "unsafe_descriptor_keys": ["handler"],
                    "unresolved_recovery_reason": "missing_registered_binding",
                    "stale_recovery_reason": "denied",
                    "unsafe_recovery_reason": "descriptor_corrupted",
                },
                "loader_execution_handoff_coverage": {
                    "handoff_smoke": True,
                    "contract_version": "phase-ii-durable-loader-execution-handoff-policy-v1",
                    "default_status": "blocked",
                    "default_blocked_reason": "explicit_handoff_required",
                    "default_will_execute": False,
                    "explicit_status": "blocked",
                    "explicit_blocked_reason": "recovery_executor_not_bound",
                    "explicit_will_execute": False,
                    "recovery_executor_bound": False,
                },
                "recovery_audit_operation_history_coverage": {
                    "audit_smoke": True,
                    "contract_version": "phase-ii-recovery-audit-production-gate-v1",
                    "ready": True,
                    "operation_history_supported": True,
                    "audit_summary_supported": True,
                    "timeline_writer_available": True,
                    "idempotent_trace_dedupe": True,
                    "authorization_source": False,
                },
                "production_recovery_registry_checkpoint_policy_coverage": {
                    "policy_smoke": True,
                    "contract_version": "phase-ii-production-recovery-registry-checkpoint-policy-v1",
                    "ready": True,
                    "registry_binding_policy_ready": True,
                    "checkpoint_resume_cursor_policy_ready": True,
                    "authorization_source": False,
                },
                "child_executor_promotion_gate_coverage": {
                    "gate_smoke": True,
                    "contract_version": "phase-ii-child-executor-gate-v1",
                    "gate_status": "blocked",
                    "allowed": False,
                    "failure_reason": "child_executor_preflight_blocked",
                    "blocker_count": 2,
                    "recommended_next_step": "keep_relationship_only",
                },
                "child_executor_execution_prerequisites_coverage": {
                    "prerequisites_smoke": True,
                    "contract_version": "phase-ii-child-executor-execution-prerequisites-v1",
                    "overall_status": "blocked",
                    "ready": False,
                    "missing_requirement_count": 2,
                    "context_budget_policy_status": "blocked",
                    "context_budget_policy_missing_sections": ["budget_source", "bounded_budget_limit"],
                    "opt_in_context_budget_policy_ready": True,
                    "merge_handoff_status": "blocked",
                    "merge_handoff_missing_sections": ["merge_source", "merge_strategy", "intent_policy"],
                    "opt_in_merge_handoff_ready": True,
                    "recommended_next_step": "keep_relationship_only",
                },
                "child_executor_dispatch_coverage": {
                    "dispatch_smoke": True,
                    "contract_version": "phase-ii-child-executor-dispatch-v1",
                    "overall_status": "blocked",
                    "dispatch_ready": False,
                    "will_dispatch": False,
                    "backend_dispatch_ready": False,
                    "relationship_seam_preserved": True,
                    "blocker_count": 2,
                    "dispatch_attempt_handoff_status": "blocked",
                    "dispatch_attempt_handoff_ready": False,
                    "opt_in_dispatch_attempt_handoff_ready": True,
                    "opt_in_attempt_validation_ready": True,
                    "opt_in_ready_dispatch_status": "ready",
                    "opt_in_ready_dispatch_ready": True,
                    "opt_in_ready_handoff_ready": True,
                    "opt_in_ready_will_dispatch": False,
                    "recommended_next_step": "implement_child_executor_backend_dispatch",
                },
                "child_executor_dispatcher_coverage": {
                    "dispatcher_smoke": True,
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
                "child_executor_dispatch_result_handoff_coverage": {
                    "result_handoff_smoke": True,
                    "contract_version": "phase-ii-child-executor-dispatch-result-handoff-v1",
                    "ready_handoff_status": "ready",
                    "ready_handoff_ready": True,
                    "ready_output_ref_present": True,
                    "ready_audit_evidence_present": True,
                    "ready_backend_result_schema_valid": True,
                    "ready_parent_merge_performed": False,
                    "ready_merge_authorization": False,
                    "ready_retry_scheduled": False,
                    "ready_production_dispatch_authorized": False,
                    "blocked_handoff_status": "blocked",
                    "blocked_dispatcher_reason": "dispatcher_disabled",
                    "blocked_missing_sections": ["dispatch_success"],
                    "malformed_handoff_status": "blocked",
                    "malformed_missing_sections": ["output_ref", "audit_evidence"],
                },
                "child_executor_dispatch_result_retry_audit_coverage": {
                    "retry_audit_smoke": True,
                    "contract_version": "phase-ii-child-executor-dispatch-result-retry-audit-policy-v1",
                    "success_policy_status": "ready",
                    "success_retry_policy_status": "not_required",
                    "success_retry_scheduled": False,
                    "success_will_retry": False,
                    "retryable_policy_status": "ready",
                    "retryable_retry_policy_status": "retryable",
                    "retryable_audit_evidence_present": True,
                    "retryable_idempotency_evidence_present": True,
                    "retryable_scheduler_required": True,
                    "retryable_retry_reason": "sandbox_timeout",
                    "retryable_retry_scheduled": False,
                    "retryable_will_retry": False,
                    "terminal_policy_status": "ready",
                    "terminal_retry_policy_status": "terminal",
                    "terminal_reason": "sandbox_payload_unsafe",
                    "terminal_will_retry": False,
                    "missing_idempotency_status": "blocked",
                    "missing_idempotency_missing_sections": ["idempotency_evidence"],
                    "missing_idempotency_retry_scheduled": False,
                },
                "child_executor_dispatch_retry_scheduler_handoff_coverage": {
                    "handoff_smoke": True,
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
                "child_executor_dispatch_retry_scheduler_binding_gate_coverage": {
                    "binding_smoke": True,
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
                "child_executor_dispatch_retry_scheduler_execution_authorization_coverage": {
                    "authorization_smoke": True,
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
                "child_executor_sandbox_backend_coverage": {
                    "sandbox_backend_smoke": True,
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
                "child_executor_sandbox_backend_binding_coverage": {
                    "binding_smoke": True,
                    "contract_version": "phase-ii-child-executor-sandbox-backend-binding-v1",
                    "default_status": "blocked",
                    "default_missing_sections": ["explicit_binding"],
                    "missing_callable_status": "blocked",
                    "missing_callable_missing_sections": ["dispatcher_backend_adapter"],
                    "ready_status": "ready",
                    "ready_dispatcher_binding_ready": True,
                    "ready_attempt_envelope_supported": True,
                    "ready_audit_idempotency_ready": True,
                    "ready_will_dispatch": False,
                    "dispatch_contract_binding_status": "ready",
                    "dispatch_contract_binding_ready": True,
                    "dispatch_contract_ready": True,
                    "dispatch_contract_will_dispatch": False,
                },
                "subagent_lane_query_detail_coverage": {
                    "detail_smoke": True,
                    "contract_version": "phase-ii-subagent-lane-query-detail-v1",
                    "recording_state": "recorded",
                    "stage_count": 3,
                    "recent_event_count": 2,
                },
            },
            "runtime_contract_artifact_schema": {
                "contract_version": "phase-f-runtime-contract-artifact-schema-v1",
                "overall_status": "healthy",
                "summary_required_fields": [
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
                    "worker_ownership_store_mode_coverage",
                    "worker_ownership_store_mode_coverage.mode_smoke",
                    "recovery_retry_evidence_coverage",
                    "recovery_retry_evidence_coverage.retry_smoke",
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
                    "child_executor_dispatch_coverage.opt_in_ready_dispatch_status",
                    "child_executor_dispatch_coverage.opt_in_ready_dispatch_ready",
                    "child_executor_dispatch_coverage.opt_in_ready_handoff_ready",
                    "child_executor_dispatch_coverage.opt_in_ready_will_dispatch",
                    "child_executor_dispatcher_coverage",
                    "child_executor_dispatcher_coverage.dispatcher_smoke",
                    "child_executor_sandbox_backend_binding_coverage",
                    "child_executor_sandbox_backend_binding_coverage.binding_smoke",
                    "child_executor_sandbox_backend_binding_coverage.ready_status",
                    "child_executor_sandbox_backend_binding_coverage.missing_callable_status",
                    "child_executor_sandbox_backend_coverage",
                    "child_executor_sandbox_backend_coverage.sandbox_backend_smoke",
                    "child_executor_sandbox_backend_coverage.execution_seam_supported",
                    "child_executor_sandbox_backend_coverage.execution_completed_status",
                    "child_executor_sandbox_backend_coverage.execution_missing_idempotency_status",
                    "child_executor_sandbox_backend_coverage.execution_handler_failure_status",
                    "subagent_lane_query_detail_coverage",
                    "subagent_lane_query_detail_coverage.detail_smoke",
                ],
                "summary_missing_fields": [],
            },
            "checks": [],
        },
        "child_executor_dispatch_contract": {
            "contract_version": "phase-ii-child-executor-dispatch-v1",
            "overall_status": "blocked",
            "dispatch_ready": False,
            "will_dispatch": False,
            "dispatch_mode": "not_implemented",
            "backend_id": "embedded_sdk_worker",
            "backend_status": "candidate",
            "backend_dispatch_ready": False,
            "gate_allowed": False,
            "prerequisites_ready": False,
            "relationship_seam_preserved": True,
            "blockers": ["promotion_gate_allowed", "worker_backend_dispatch_ready"],
            "required_contracts": [
                "child_executor_backend_registry",
                "child_executor_promotion_gate",
                "child_executor_execution_prerequisites",
            ],
            "child_executor_dispatch_attempt_handoff": {
                "contract_version": "phase-ii-child-executor-dispatch-attempt-handoff-v1",
                "overall_status": "blocked",
                "ready": False,
                "will_dispatch": False,
            },
            "recommended_next_step": "implement_child_executor_backend_dispatch",
        },
        "main_chat_query_detail": {
            "contract_version": "phase-g-main-chat-query-detail-v1",
            "connected": True,
            "read_model_layer": "query_detail",
            "source_channel": "main_chat",
            "identity_kind": "query_id",
            "query_id": "manual-chat-1",
            "recording_state": "recorded",
            "stage_chain": ["planning"],
            "dedupe_keys": ["query_control:main_chat:planning:321:manual-chat-1"],
            "dedupe_key_count": 1,
            "recent_events": [
                {
                    "timestamp": "2026-05-16T10:00:00Z",
                    "stage": "planning",
                    "summary": "Main chat planning",
                    "severity": "info",
                    "snapshot_id": "QUER-PLAN-321-20260516100000",
                    "dedupe_key": "query_control:main_chat:planning:321:manual-chat-1",
                }
            ],
            "recent_event_count": 1,
            "latest_snapshot_id": "QUER-PLAN-321-20260516100000",
            "latest_warning_summary": "",
            "latest_stage": "planning",
            "latest_summary": "Main chat planning",
            "stage_count": 1,
            "warning_count": 0,
            "event_count": 1,
            "reason": "",
        },
        "external_adapter_recent_summary": {
            "contract_version": "phase-i-external-adapter-recent-summary-v1",
            "connected": True,
            "recording_state": "recorded",
            "items": [
                {
                    "query_id": "external-run-1",
                    "latest_stage": "final_output",
                    "latest_summary": "External adapter returned output",
                    "latest_timestamp": "2026-05-18T10:01:00Z",
                    "recording_state": "recorded",
                }
            ],
            "latest_query_id": "external-run-1",
            "latest_stage": "final_output",
            "latest_summary": "External adapter returned output",
            "latest_timestamp": "2026-05-18T10:01:00Z",
            "total_items": 1,
            "reason": "",
        },
        "channel_promotion_gate": {
            "contract_version": "phase-h-channel-promotion-gate-v1",
            "overall_status": "guarded",
            "layer_order": ["readiness", "recent_summary", "query_detail", "query_history", "query_workspace"],
            "channels": [
                {
                    "channel": "main_chat",
                    "baseline": True,
                    "readiness_status": "ready",
                    "current_layer": "query_workspace",
                    "promotion_status": "baseline",
                    "allowed_layers": [],
                    "blocked_layers": [],
                    "blocking_reasons": [],
                    "evidence": {"canonical_baseline": True, "runtime_surface_primary": True},
                },
                {
                    "channel": "subagent_lane",
                    "baseline": False,
                    "readiness_status": "ready",
                    "current_layer": "query_detail",
                    "promotion_status": "query_detail_ready",
                    "allowed_layers": ["query_detail"],
                    "blocked_layers": [],
                    "blocking_reasons": [],
                    "evidence": {
                        "recent_summary_status": "recorded",
                        "ready_for_detail": True,
                        "required_capabilities": {
                            "stable_query_id": True,
                            "stage_chain_candidate": True,
                            "recent_summary_recorded": True,
                            "separates_child_run_events": True,
                        },
                        "recommended_next_change": "subagent-lane-query-detail-contract",
                    },
                },
                {
                    "channel": "external_adapter",
                    "baseline": False,
                    "readiness_status": "candidate",
                    "current_layer": "recent_summary",
                    "promotion_status": "recent_summary_candidate",
                    "allowed_layers": ["recent_summary"],
                    "blocked_layers": ["query_detail", "query_history", "query_workspace"],
                    "blocking_reasons": ["detail_not_generalized"],
                    "evidence": {"recent_summary_status": "unavailable", "ready_for_detail": False},
                },
            ],
            "channels_by_id": {
                "main_chat": {
                    "channel": "main_chat",
                    "baseline": True,
                    "readiness_status": "ready",
                    "current_layer": "query_workspace",
                    "promotion_status": "baseline",
                    "allowed_layers": [],
                    "blocked_layers": [],
                    "blocking_reasons": [],
                    "evidence": {"canonical_baseline": True, "runtime_surface_primary": True},
                },
                "subagent_lane": {
                    "channel": "subagent_lane",
                    "baseline": False,
                    "readiness_status": "ready",
                    "current_layer": "query_detail",
                    "promotion_status": "query_detail_ready",
                    "allowed_layers": ["query_detail"],
                    "blocked_layers": [],
                    "blocking_reasons": [],
                    "evidence": {
                        "recent_summary_status": "recorded",
                        "ready_for_detail": True,
                        "required_capabilities": {
                            "stable_query_id": True,
                            "stage_chain_candidate": True,
                            "recent_summary_recorded": True,
                            "separates_child_run_events": True,
                        },
                        "recommended_next_change": "subagent-lane-query-detail-contract",
                    },
                },
                "external_adapter": {
                    "channel": "external_adapter",
                    "baseline": False,
                    "readiness_status": "candidate",
                    "current_layer": "recent_summary",
                    "promotion_status": "recent_summary_candidate",
                    "allowed_layers": ["recent_summary"],
                    "blocked_layers": ["query_detail", "query_history", "query_workspace"],
                    "blocking_reasons": ["detail_not_generalized"],
                    "evidence": {"recent_summary_status": "unavailable", "ready_for_detail": False},
                },
            },
            "over_promotion_guard": {
                "blocked_channels": ["subagent_lane", "external_adapter"],
                "blocked_layers": {
                    "query_detail": ["external_adapter"],
                    "query_history": ["subagent_lane", "external_adapter"],
                    "query_workspace": ["subagent_lane", "external_adapter"],
                },
                "reason": "promotion_must_follow_readiness_then_summary_then_detail_then_history_then_workspace",
            },
        },
        "self_improvement_ledger": {
            "contract_version": "phase-g-self-improvement-ledger-v1",
            "overall_status": "ready",
            "record_types": ["learning", "error", "feature_request"],
            "tracked_sources": ["conversation", "error", "user_feedback", "quality_gate", "runtime_contract"],
            "promotion_targets": ["AGENTS.md", "docs", "system_prompt", "best_practice", "skill"],
            "governance_states": ["pending", "in_progress", "resolved", "promoted", "disabled", "rolled_back"],
            "quality_controls": ["review", "version_history", "duplicate_merge", "rollback", "restore"],
            "runtime_surface_enabled": True,
            "health_summary": {
                "total_learning_count": 0,
                "pending_learning_count": 0,
                "resolved_learning_count": 0,
                "promoted_learning_count": 0,
                "disabled_learning_count": 0,
                "rolled_back_learning_count": 0,
                "reviewed_learning_count": 0,
                "average_learning_quality_score": None,
                "total_error_count": 0,
                "pending_error_count": 0,
                "total_feature_request_count": 0,
                "pending_feature_request_count": 0,
                "attention_items": [],
            },
        },
        "query_control_plane": {
            "contract_version": "phase-g-query-control-plane-v1",
            "overall_status": "design_ready",
            "lifecycle_stages": ["input_received", "context_assembly", "planning", "model_stream", "tool_decision", "tool_execution", "observation", "review", "final_output"],
            "execution_channels": ["main_chat", "embedded_sdk", "external_adapter", "subagent_lane"],
            "required_trace_events": ["input_received", "context_assembly", "planning", "model_stream", "tool_decision", "tool_execution", "observation", "review", "final_output"],
            "adapter_boundaries": {"provider_adapter": "normalizes model streams into runtime events"},
            "governance_requirements": ["traceable_lifecycle_stage"],
            "runtime_surface_enabled": True,
        },
        "runtime_plane_governance_profile": {
            "contract_version": "runtime-surface-runtime-plane-profile-v1",
            "projection_contract_status": "ready",
            "projection_contract_version": "runtime-plane-governance-read-model-v1",
            "supported_adapter_ids": ["simple_agent", "tool_agent", "approval_agent"],
            "supported_adapter_count": 3,
            "latest_projection_available": False,
            "reason": "projection_source_unavailable",
            "latest_projection": None,
            "boundaries": {
                "read_model_only": True,
                "will_execute_adapter": False,
                "will_persist_projection": False,
                "will_persist_trace": False,
                "will_submit_approval": False,
                "default_chat_changed": False,
                "frontend_ui_changed": False,
            },
        },
    }


class RuntimeContractSnapshotServiceTests(unittest.TestCase):
    def test_build_snapshot_records_stable_contract_fields_and_fingerprint(self):
        snapshot = RuntimeContractSnapshotService().build_snapshot(_build_complete_profile())

        self.assertEqual(snapshot["contract_version"], "phase-c-runtime-contract-snapshot-v1")
        self.assertEqual(snapshot["overall_status"], "healthy")
        self.assertEqual(snapshot["contract_count"], 14)
        self.assertEqual(snapshot["missing_contract_count"], 0)
        self.assertEqual(snapshot["missing_field_count"], 0)
        self.assertEqual(len(snapshot["fingerprint"]), 64)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        self.assertEqual(by_name["tool_runtime"]["version"], "phase-b-tool-runtime-v1")
        self.assertIn("high_risk_tool_count", by_name["tool_runtime"]["stable_fields"])
        self.assertEqual(by_name["tool_runtime"]["missing_fields"], [])
        self.assertEqual(len(by_name["tool_runtime"]["fingerprint"]), 64)
        self.assertIn("embedded_sdk", by_name["command_contract"]["stable_fields"])
        self.assertIn("embedded_sdk.volatile_runtime_state", by_name["command_contract"]["stable_fields"])
        self.assertIn("embedded_sdk.persistence_seams", by_name["command_contract"]["stable_fields"])
        self.assertIn("embedded_sdk.recovery_entrypoints", by_name["command_contract"]["stable_fields"])
        self.assertIn("embedded_sdk.delegate_preflight.status", by_name["command_contract"]["stable_fields"])
        self.assertIn("embedded_sdk.event_status_kinds", by_name["command_contract"]["stable_fields"])
        self.assertIn("agent_harness_facade.delegate_preflight.status", by_name["command_contract"]["stable_fields"])
        self.assertEqual(by_name["command_contract"]["missing_status_kinds"], {})
        self.assertEqual(by_name["command_contract"]["missing_status_kind_count"], 0)
        self.assertEqual(by_name["command_contract"]["missing_event_payloads"], {})
        self.assertEqual(by_name["command_contract"]["missing_event_payload_count"], 0)
        self.assertIn("adapters", by_name["adapter_health"]["stable_fields"])
        self.assertIn("checks", by_name["runtime_contract_gate"]["stable_fields"])
        self.assertIn("runtime_contract_summary", by_name["runtime_contract_gate"]["stable_fields"])
        self.assertIn(
            "runtime_contract_summary.subagent_lane_query_detail_coverage",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.checkpoint_resume_cursor_coverage",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.checkpoint_resume_cursor_coverage.cursor_smoke",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.embedded_sdk_persistence_coverage",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.embedded_sdk_persistence_coverage.persistence_smoke",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.worker_ownership_store_mode_coverage",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.worker_ownership_store_mode_coverage.mode_smoke",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.durable_recovery_loader_coverage",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.recovery_retry_scheduler_coverage",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.recovery_retry_scheduler_coverage.scheduler_smoke",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.durable_recovery_loader_coverage.loader_smoke",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.continuation_descriptor_lifecycle_coverage",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.continuation_descriptor_lifecycle_coverage.lifecycle_smoke",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.loader_execution_handoff_coverage",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.loader_execution_handoff_coverage.handoff_smoke",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.recovery_audit_operation_history_coverage",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.recovery_audit_operation_history_coverage.audit_smoke",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.production_recovery_registry_checkpoint_policy_coverage",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.production_recovery_registry_checkpoint_policy_coverage.policy_smoke",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_promotion_gate_coverage",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_promotion_gate_coverage.gate_smoke",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_coverage",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_coverage.dispatch_smoke",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_coverage.dispatch_attempt_handoff_status",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_coverage.opt_in_dispatch_attempt_handoff_ready",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_coverage.opt_in_attempt_validation_ready",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_coverage.opt_in_ready_dispatch_status",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_coverage.opt_in_ready_dispatch_ready",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_coverage.opt_in_ready_handoff_ready",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_coverage.opt_in_ready_will_dispatch",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatcher_coverage",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatcher_coverage.dispatcher_smoke",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_result_handoff_coverage",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_result_handoff_coverage.result_handoff_smoke",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_result_retry_audit_coverage",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_result_retry_audit_coverage.retry_audit_smoke",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_result_retry_audit_coverage.retryable_retry_policy_status",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_result_retry_audit_coverage.missing_idempotency_status",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_retry_scheduler_handoff_coverage",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_retry_scheduler_handoff_coverage.handoff_smoke",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_retry_scheduler_handoff_coverage.default_status",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_retry_scheduler_handoff_coverage.bound_status",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_retry_scheduler_binding_gate_coverage",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_retry_scheduler_binding_gate_coverage.binding_smoke",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_retry_scheduler_binding_gate_coverage.default_status",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_retry_scheduler_binding_gate_coverage.ready_status",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_retry_scheduler_execution_authorization_coverage",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_retry_scheduler_execution_authorization_coverage.authorization_smoke",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_retry_scheduler_execution_authorization_coverage.default_status",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_retry_scheduler_execution_authorization_coverage.ready_status",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_sandbox_backend_binding_coverage",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_sandbox_backend_binding_coverage.binding_smoke",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_sandbox_backend_binding_coverage.ready_status",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_sandbox_backend_binding_coverage.missing_callable_status",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_sandbox_backend_coverage",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_sandbox_backend_coverage.sandbox_backend_smoke",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_sandbox_backend_coverage.execution_seam_supported",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_sandbox_backend_coverage.execution_completed_status",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_sandbox_backend_coverage.execution_missing_idempotency_status",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.child_executor_sandbox_backend_coverage.execution_handler_failure_status",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.approval_lifecycle_recovery_coverage",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.approval_lifecycle_recovery_coverage.alignment_smoke",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn(
            "runtime_contract_summary.subagent_lane_query_detail_coverage.detail_smoke",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn("runtime_contract_artifact_schema", by_name["runtime_contract_gate"]["stable_fields"])
        self.assertIn(
            "runtime_contract_artifact_schema.summary_missing_fields",
            by_name["runtime_contract_gate"]["stable_fields"],
        )
        self.assertIn("child_executor_dispatch_contract", by_name)
        self.assertIn("dispatch_ready", by_name["child_executor_dispatch_contract"]["stable_fields"])
        self.assertIn("will_dispatch", by_name["child_executor_dispatch_contract"]["stable_fields"])
        self.assertIn("backend_dispatch_ready", by_name["child_executor_dispatch_contract"]["stable_fields"])
        self.assertIn(
            "child_executor_dispatch_attempt_handoff.ready",
            by_name["child_executor_dispatch_contract"]["stable_fields"],
        )
        self.assertIn("main_chat_query_detail", by_name)
        self.assertIn("read_model_layer", by_name["main_chat_query_detail"]["stable_fields"])
        self.assertIn("source_channel", by_name["main_chat_query_detail"]["stable_fields"])
        self.assertIn("identity_kind", by_name["main_chat_query_detail"]["stable_fields"])
        self.assertIn("external_adapter_recent_summary", by_name)
        self.assertIn("recording_state", by_name["external_adapter_recent_summary"]["stable_fields"])
        self.assertIn("latest_query_id", by_name["external_adapter_recent_summary"]["stable_fields"])
        self.assertIn("channel_promotion_gate", by_name)
        self.assertIn("channels_by_id", by_name["channel_promotion_gate"]["stable_fields"])
        self.assertIn("channels_by_id.main_chat", by_name["channel_promotion_gate"]["stable_fields"])
        self.assertIn("channels_by_id.subagent_lane", by_name["channel_promotion_gate"]["stable_fields"])
        self.assertIn("channels_by_id.external_adapter", by_name["channel_promotion_gate"]["stable_fields"])
        self.assertIn("tracked_sources", by_name["self_improvement_ledger"]["stable_fields"])
        self.assertIn("quality_controls", by_name["self_improvement_ledger"]["stable_fields"])
        self.assertIn("health_summary", by_name["self_improvement_ledger"]["stable_fields"])
        self.assertIn("lifecycle_stages", by_name["query_control_plane"]["stable_fields"])
        self.assertIn("execution_channels", by_name["query_control_plane"]["stable_fields"])
        self.assertIn("runtime_plane_governance_profile", by_name)
        self.assertIn("projection_contract_status", by_name["runtime_plane_governance_profile"]["stable_fields"])
        self.assertIn("boundaries.will_execute_adapter", by_name["runtime_plane_governance_profile"]["stable_fields"])

    def test_build_snapshot_degrades_when_required_contracts_or_fields_are_missing(self):
        profile = _build_complete_profile()
        del profile["skill_contract"]
        del profile["command_contract"]["embedded_sdk"]["event_status_kinds"]
        del profile["command_contract"]["embedded_sdk"]["delegate_preflight"]
        del profile["command_contract"]["agent_harness_facade"]["delegate_preflight"]
        del profile["adapter_health"]["adapters"]
        del profile["runtime_contract_gate"]["runtime_contract_summary"]
        del profile["runtime_contract_gate"]["runtime_contract_artifact_schema"]
        del profile["main_chat_query_detail"]["source_channel"]
        del profile["external_adapter_recent_summary"]["recording_state"]
        del profile["channel_promotion_gate"]["channels_by_id"]["external_adapter"]
        del profile["self_improvement_ledger"]["quality_controls"]
        del profile["self_improvement_ledger"]["health_summary"]
        del profile["query_control_plane"]["required_trace_events"]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(snapshot["missing_contract_count"], 1)
        self.assertEqual(snapshot["missing_field_count"], 111)
        self.assertEqual(by_name["skill_contract"]["status"], "missing")
        self.assertEqual(
            by_name["command_contract"]["missing_fields"],
            [
                "embedded_sdk.delegate_preflight",
                "embedded_sdk.delegate_preflight.status",
                "embedded_sdk.delegate_preflight.promotion_requirements",
                "embedded_sdk.event_status_kinds",
                "agent_harness_facade.delegate_preflight",
                "agent_harness_facade.delegate_preflight.status",
            ],
        )
        self.assertEqual(by_name["adapter_health"]["missing_fields"], ["adapters"])
        self.assertEqual(
            by_name["runtime_contract_gate"]["missing_fields"],
            [
                "runtime_contract_summary",
                "runtime_contract_summary.overall_status",
                "runtime_contract_summary.check_count",
                "runtime_contract_summary.failed_check_count",
                "runtime_contract_summary.missing_payload_count",
                "runtime_contract_summary.approval_replay_coverage",
                "runtime_contract_summary.approval_lifecycle_recovery_coverage",
                "runtime_contract_summary.approval_lifecycle_recovery_coverage.alignment_smoke",
                "runtime_contract_summary.approved_tool_execution_coverage",
                "runtime_contract_summary.sdk_tool_runtime_execution_coverage",
                "runtime_contract_summary.sdk_tool_runtime_execution_coverage.bridge_smoke",
                "runtime_contract_summary.tool_runtime_timeout_retry_coverage",
                "runtime_contract_summary.tool_runtime_timeout_retry_coverage.timeout_retry_smoke",
                "runtime_contract_summary.checkpoint_resume_cursor_coverage",
                "runtime_contract_summary.checkpoint_resume_cursor_coverage.cursor_smoke",
                "runtime_contract_summary.embedded_sdk_persistence_coverage",
                "runtime_contract_summary.embedded_sdk_persistence_coverage.persistence_smoke",
                "runtime_contract_summary.embedded_sdk_persistence_coverage.production_recovery_worker_ownership_gate_status",
                "runtime_contract_summary.embedded_sdk_persistence_coverage.production_recovery_worker_ownership_missing_sections",
                "runtime_contract_summary.embedded_sdk_production_recovery_authorization_coverage",
                "runtime_contract_summary.embedded_sdk_production_recovery_authorization_coverage.authorization_smoke",
                "runtime_contract_summary.embedded_sdk_production_recovery_authorization_coverage.blocked_status",
                "runtime_contract_summary.embedded_sdk_production_recovery_authorization_coverage.ready_status",
                "runtime_contract_summary.worker_ownership_store_mode_coverage",
                "runtime_contract_summary.worker_ownership_store_mode_coverage.mode_smoke",
                "runtime_contract_summary.worker_ownership_store_mode_coverage.enablement_config_factory_binding_smoke",
                "runtime_contract_summary.recovery_retry_evidence_coverage",
                "runtime_contract_summary.recovery_retry_evidence_coverage.retry_smoke",
                "runtime_contract_summary.recovery_retry_scheduler_coverage",
                "runtime_contract_summary.recovery_retry_scheduler_coverage.scheduler_smoke",
                "runtime_contract_summary.durable_recovery_loader_coverage",
                "runtime_contract_summary.durable_recovery_loader_coverage.loader_smoke",
                "runtime_contract_summary.continuation_descriptor_lifecycle_coverage",
                "runtime_contract_summary.continuation_descriptor_lifecycle_coverage.lifecycle_smoke",
                "runtime_contract_summary.loader_execution_handoff_coverage",
                "runtime_contract_summary.loader_execution_handoff_coverage.handoff_smoke",
                "runtime_contract_summary.recovery_audit_operation_history_coverage",
                "runtime_contract_summary.recovery_audit_operation_history_coverage.audit_smoke",
                "runtime_contract_summary.production_recovery_registry_checkpoint_policy_coverage",
                "runtime_contract_summary.production_recovery_registry_checkpoint_policy_coverage.policy_smoke",
                "runtime_contract_summary.child_executor_promotion_gate_coverage",
                "runtime_contract_summary.child_executor_promotion_gate_coverage.gate_smoke",
                "runtime_contract_summary.child_executor_execution_prerequisites_coverage",
                "runtime_contract_summary.child_executor_execution_prerequisites_coverage.prerequisites_smoke",
                "runtime_contract_summary.child_executor_execution_prerequisites_coverage.context_budget_policy_status",
                "runtime_contract_summary.child_executor_execution_prerequisites_coverage.context_budget_policy_missing_sections",
                "runtime_contract_summary.child_executor_execution_prerequisites_coverage.opt_in_context_budget_policy_ready",
                "runtime_contract_summary.child_executor_execution_prerequisites_coverage.merge_handoff_status",
                "runtime_contract_summary.child_executor_execution_prerequisites_coverage.merge_handoff_missing_sections",
                "runtime_contract_summary.child_executor_execution_prerequisites_coverage.opt_in_merge_handoff_ready",
                "runtime_contract_summary.child_executor_dispatch_coverage",
                "runtime_contract_summary.child_executor_dispatch_coverage.dispatch_smoke",
                "runtime_contract_summary.child_executor_dispatch_coverage.dispatch_attempt_handoff_status",
                "runtime_contract_summary.child_executor_dispatch_coverage.opt_in_dispatch_attempt_handoff_ready",
                "runtime_contract_summary.child_executor_dispatch_coverage.opt_in_attempt_validation_ready",
                "runtime_contract_summary.child_executor_dispatch_coverage.opt_in_ready_dispatch_status",
                "runtime_contract_summary.child_executor_dispatch_coverage.opt_in_ready_dispatch_ready",
                "runtime_contract_summary.child_executor_dispatch_coverage.opt_in_ready_handoff_ready",
                "runtime_contract_summary.child_executor_dispatch_coverage.opt_in_ready_will_dispatch",
                "runtime_contract_summary.child_executor_dispatcher_coverage",
                "runtime_contract_summary.child_executor_dispatcher_coverage.dispatcher_smoke",
                "runtime_contract_summary.child_executor_dispatch_result_handoff_coverage",
                "runtime_contract_summary.child_executor_dispatch_result_handoff_coverage.result_handoff_smoke",
                "runtime_contract_summary.child_executor_dispatch_result_handoff_coverage.ready_handoff_status",
                "runtime_contract_summary.child_executor_dispatch_result_handoff_coverage.malformed_handoff_status",
                "runtime_contract_summary.child_executor_dispatch_result_retry_audit_coverage",
                "runtime_contract_summary.child_executor_dispatch_result_retry_audit_coverage.retry_audit_smoke",
                "runtime_contract_summary.child_executor_dispatch_result_retry_audit_coverage.retryable_retry_policy_status",
                "runtime_contract_summary.child_executor_dispatch_result_retry_audit_coverage.missing_idempotency_status",
                "runtime_contract_summary.child_executor_dispatch_retry_scheduler_handoff_coverage",
                "runtime_contract_summary.child_executor_dispatch_retry_scheduler_handoff_coverage.handoff_smoke",
                "runtime_contract_summary.child_executor_dispatch_retry_scheduler_handoff_coverage.default_status",
                "runtime_contract_summary.child_executor_dispatch_retry_scheduler_handoff_coverage.bound_status",
                "runtime_contract_summary.child_executor_dispatch_retry_scheduler_binding_gate_coverage",
                "runtime_contract_summary.child_executor_dispatch_retry_scheduler_binding_gate_coverage.binding_smoke",
                "runtime_contract_summary.child_executor_dispatch_retry_scheduler_binding_gate_coverage.default_status",
                "runtime_contract_summary.child_executor_dispatch_retry_scheduler_binding_gate_coverage.ready_status",
                "runtime_contract_summary.child_executor_dispatch_retry_scheduler_execution_authorization_coverage",
                "runtime_contract_summary.child_executor_dispatch_retry_scheduler_execution_authorization_coverage.authorization_smoke",
                "runtime_contract_summary.child_executor_dispatch_retry_scheduler_execution_authorization_coverage.default_status",
                "runtime_contract_summary.child_executor_dispatch_retry_scheduler_execution_authorization_coverage.ready_status",
                "runtime_contract_summary.child_executor_sandbox_backend_binding_coverage",
                "runtime_contract_summary.child_executor_sandbox_backend_binding_coverage.binding_smoke",
                "runtime_contract_summary.child_executor_sandbox_backend_binding_coverage.ready_status",
                "runtime_contract_summary.child_executor_sandbox_backend_binding_coverage.missing_callable_status",
                "runtime_contract_summary.child_executor_sandbox_backend_coverage",
                "runtime_contract_summary.child_executor_sandbox_backend_coverage.sandbox_backend_smoke",
                "runtime_contract_summary.child_executor_sandbox_backend_coverage.execution_seam_supported",
                "runtime_contract_summary.child_executor_sandbox_backend_coverage.execution_completed_status",
                "runtime_contract_summary.child_executor_sandbox_backend_coverage.execution_missing_idempotency_status",
                "runtime_contract_summary.child_executor_sandbox_backend_coverage.execution_handler_failure_status",
                "runtime_contract_summary.subagent_lane_query_detail_coverage",
                "runtime_contract_summary.subagent_lane_query_detail_coverage.detail_smoke",
                "runtime_contract_artifact_schema",
                "runtime_contract_artifact_schema.contract_version",
                "runtime_contract_artifact_schema.overall_status",
                "runtime_contract_artifact_schema.summary_required_fields",
                "runtime_contract_artifact_schema.summary_missing_fields",
            ],
        )
        self.assertEqual(
            by_name["main_chat_query_detail"]["missing_fields"],
            ["source_channel"],
        )
        self.assertEqual(
            by_name["external_adapter_recent_summary"]["missing_fields"],
            ["recording_state"],
        )
        self.assertEqual(by_name["self_improvement_ledger"]["missing_fields"], ["quality_controls", "health_summary"])
        self.assertEqual(by_name["query_control_plane"]["missing_fields"], ["required_trace_events"])

    def test_build_snapshot_degrades_when_required_sdk_event_status_kind_is_missing(self):
        profile = _build_complete_profile()
        profile["command_contract"]["embedded_sdk"]["event_status_kinds"] = [
            {"status_kind": "approval_created"},
            {"status_kind": "approval_resolved"},
            {"status_kind": "execution_loop_done"},
            {"status_kind": "loop_continuation_registered"},
            {"status_kind": "loop_continuation_discarded"},
        ]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        command_contract = by_name["command_contract"]
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(snapshot["missing_status_kind_count"], 3)
        self.assertEqual(command_contract["status"], "degraded")
        self.assertEqual(
            command_contract["missing_status_kinds"],
            {"embedded_sdk.event_status_kinds": ["approval_replayed", "approval_ignored", "loop_continuation_consumed"]},
        )
        self.assertEqual(command_contract["missing_status_kind_count"], 3)

    def test_build_snapshot_degrades_when_core_sdk_event_status_kind_is_missing(self):
        profile = _build_complete_profile()
        profile["command_contract"]["embedded_sdk"]["event_status_kinds"] = [
            {"status_kind": "approval_created"},
            {"status_kind": "loop_continuation_registered"},
            {"status_kind": "loop_continuation_consumed"},
            {"status_kind": "loop_continuation_discarded"},
        ]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        command_contract = by_name["command_contract"]
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(snapshot["missing_status_kind_count"], 4)
        self.assertEqual(
            command_contract["missing_status_kinds"],
            {"embedded_sdk.event_status_kinds": ["approval_resolved", "approval_replayed", "approval_ignored", "execution_loop_done"]},
        )

    def test_build_snapshot_degrades_when_required_sdk_event_payload_is_missing(self):
        profile = _build_complete_profile()
        event_status_kinds = profile["command_contract"]["embedded_sdk"]["event_status_kinds"]
        event_status_kinds[0]["required_payload"] = ["approval_request_id"]
        event_status_kinds[2]["required_payload"] = ["approval_request_id", "approval_request"]
        event_status_kinds[3]["required_payload"] = ["approval_request_id", "approval_request"]
        event_status_kinds[4]["required_payload"] = ["run"]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        command_contract = by_name["command_contract"]
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(snapshot["missing_event_payload_count"], 6)
        self.assertEqual(command_contract["status"], "degraded")
        self.assertEqual(
            command_contract["missing_event_payloads"],
            {
                "embedded_sdk.event_status_kinds": {
                    "approval_created": ["approval_request"],
                    "approval_replayed": ["original_decision", "attempted_decision"],
                    "approval_ignored": ["original_decision", "attempted_decision"],
                    "execution_loop_done": ["completed_steps"],
                }
            },
        )
        self.assertEqual(command_contract["missing_event_payload_count"], 6)

    def test_build_snapshot_degrades_when_subagent_detail_coverage_is_missing_from_summary(self):
        profile = _build_complete_profile()
        del profile["runtime_contract_gate"]["runtime_contract_summary"]["subagent_lane_query_detail_coverage"]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        runtime_contract_gate = by_name["runtime_contract_gate"]
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(runtime_contract_gate["status"], "degraded")
        self.assertIn(
            "runtime_contract_summary.subagent_lane_query_detail_coverage",
            runtime_contract_gate["missing_fields"],
        )

    def test_build_snapshot_degrades_when_runtime_plane_profile_boundary_is_missing(self):
        profile = _build_complete_profile()
        del profile["runtime_plane_governance_profile"]["boundaries"]["will_execute_adapter"]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        runtime_plane_profile = by_name["runtime_plane_governance_profile"]
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(runtime_plane_profile["status"], "degraded")
        self.assertIn(
            "boundaries.will_execute_adapter",
            runtime_plane_profile["missing_fields"],
        )

    def test_build_snapshot_degrades_when_subagent_detail_smoke_flag_is_missing_from_summary(self):
        profile = _build_complete_profile()
        del profile["runtime_contract_gate"]["runtime_contract_summary"]["subagent_lane_query_detail_coverage"]["detail_smoke"]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        runtime_contract_gate = by_name["runtime_contract_gate"]
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(runtime_contract_gate["status"], "degraded")
        self.assertIn(
            "runtime_contract_summary.subagent_lane_query_detail_coverage.detail_smoke",
            runtime_contract_gate["missing_fields"],
        )

    def test_build_snapshot_degrades_when_worker_ownership_store_mode_coverage_is_missing_from_summary(self):
        profile = _build_complete_profile()
        del profile["runtime_contract_gate"]["runtime_contract_summary"]["worker_ownership_store_mode_coverage"]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        runtime_contract_gate = by_name["runtime_contract_gate"]
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(runtime_contract_gate["status"], "degraded")
        self.assertIn(
            "runtime_contract_summary.worker_ownership_store_mode_coverage",
            runtime_contract_gate["missing_fields"],
        )

    def test_build_snapshot_degrades_when_worker_ownership_mode_smoke_flag_is_missing_from_summary(self):
        profile = _build_complete_profile()
        del profile["runtime_contract_gate"]["runtime_contract_summary"]["worker_ownership_store_mode_coverage"]["mode_smoke"]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        runtime_contract_gate = by_name["runtime_contract_gate"]
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(runtime_contract_gate["status"], "degraded")
        self.assertIn(
            "runtime_contract_summary.worker_ownership_store_mode_coverage.mode_smoke",
            runtime_contract_gate["missing_fields"],
        )

    def test_build_snapshot_degrades_when_worker_ownership_config_factory_binding_smoke_is_missing_from_summary(self):
        profile = _build_complete_profile()
        del profile["runtime_contract_gate"]["runtime_contract_summary"]["worker_ownership_store_mode_coverage"][
            "enablement_config_factory_binding_smoke"
        ]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        runtime_contract_gate = by_name["runtime_contract_gate"]
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(runtime_contract_gate["status"], "degraded")
        self.assertIn(
            (
                "runtime_contract_summary.worker_ownership_store_mode_coverage."
                "enablement_config_factory_binding_smoke"
            ),
            runtime_contract_gate["missing_fields"],
        )

    def test_build_snapshot_degrades_when_recovery_retry_evidence_coverage_is_missing_from_summary(self):
        profile = _build_complete_profile()
        del profile["runtime_contract_gate"]["runtime_contract_summary"]["recovery_retry_evidence_coverage"]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        runtime_contract_gate = by_name["runtime_contract_gate"]
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(runtime_contract_gate["status"], "degraded")
        self.assertIn(
            "runtime_contract_summary.recovery_retry_evidence_coverage",
            runtime_contract_gate["missing_fields"],
        )

    def test_build_snapshot_degrades_when_recovery_retry_smoke_flag_is_missing_from_summary(self):
        profile = _build_complete_profile()
        del profile["runtime_contract_gate"]["runtime_contract_summary"]["recovery_retry_evidence_coverage"]["retry_smoke"]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        runtime_contract_gate = by_name["runtime_contract_gate"]
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(runtime_contract_gate["status"], "degraded")
        self.assertIn(
            "runtime_contract_summary.recovery_retry_evidence_coverage.retry_smoke",
            runtime_contract_gate["missing_fields"],
        )

    def test_build_snapshot_degrades_when_child_executor_promotion_gate_coverage_is_missing_from_summary(self):
        profile = _build_complete_profile()
        del profile["runtime_contract_gate"]["runtime_contract_summary"]["child_executor_promotion_gate_coverage"]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        runtime_contract_gate = by_name["runtime_contract_gate"]
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(runtime_contract_gate["status"], "degraded")
        self.assertIn(
            "runtime_contract_summary.child_executor_promotion_gate_coverage",
            runtime_contract_gate["missing_fields"],
        )

    def test_build_snapshot_degrades_when_child_executor_gate_smoke_flag_is_missing_from_summary(self):
        profile = _build_complete_profile()
        del profile["runtime_contract_gate"]["runtime_contract_summary"]["child_executor_promotion_gate_coverage"]["gate_smoke"]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        runtime_contract_gate = by_name["runtime_contract_gate"]
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(runtime_contract_gate["status"], "degraded")
        self.assertIn(
            "runtime_contract_summary.child_executor_promotion_gate_coverage.gate_smoke",
            runtime_contract_gate["missing_fields"],
        )

    def test_build_snapshot_degrades_when_child_executor_dispatch_coverage_is_missing_from_summary(self):
        profile = _build_complete_profile()
        del profile["runtime_contract_gate"]["runtime_contract_summary"]["child_executor_dispatch_coverage"]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        runtime_contract_gate = by_name["runtime_contract_gate"]
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(runtime_contract_gate["status"], "degraded")
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_coverage",
            runtime_contract_gate["missing_fields"],
        )

    def test_build_snapshot_degrades_when_child_executor_dispatch_smoke_flag_is_missing_from_summary(self):
        profile = _build_complete_profile()
        del profile["runtime_contract_gate"]["runtime_contract_summary"]["child_executor_dispatch_coverage"]["dispatch_smoke"]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        runtime_contract_gate = by_name["runtime_contract_gate"]
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(runtime_contract_gate["status"], "degraded")
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatch_coverage.dispatch_smoke",
            runtime_contract_gate["missing_fields"],
        )

    def test_build_snapshot_degrades_when_child_executor_dispatcher_coverage_is_missing_from_summary(self):
        profile = _build_complete_profile()
        del profile["runtime_contract_gate"]["runtime_contract_summary"]["child_executor_dispatcher_coverage"]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        runtime_contract_gate = by_name["runtime_contract_gate"]
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(runtime_contract_gate["status"], "degraded")
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatcher_coverage",
            runtime_contract_gate["missing_fields"],
        )

    def test_build_snapshot_degrades_when_child_executor_dispatcher_smoke_flag_is_missing_from_summary(self):
        profile = _build_complete_profile()
        del profile["runtime_contract_gate"]["runtime_contract_summary"]["child_executor_dispatcher_coverage"][
            "dispatcher_smoke"
        ]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        runtime_contract_gate = by_name["runtime_contract_gate"]
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(runtime_contract_gate["status"], "degraded")
        self.assertIn(
            "runtime_contract_summary.child_executor_dispatcher_coverage.dispatcher_smoke",
            runtime_contract_gate["missing_fields"],
        )

    def test_build_snapshot_degrades_when_child_executor_sandbox_backend_coverage_is_missing_from_summary(self):
        profile = _build_complete_profile()
        del profile["runtime_contract_gate"]["runtime_contract_summary"]["child_executor_sandbox_backend_coverage"]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        runtime_contract_gate = by_name["runtime_contract_gate"]
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(runtime_contract_gate["status"], "degraded")
        self.assertIn(
            "runtime_contract_summary.child_executor_sandbox_backend_coverage",
            runtime_contract_gate["missing_fields"],
        )

    def test_build_snapshot_degrades_when_child_executor_sandbox_backend_smoke_flag_is_missing_from_summary(self):
        profile = _build_complete_profile()
        del profile["runtime_contract_gate"]["runtime_contract_summary"]["child_executor_sandbox_backend_coverage"][
            "sandbox_backend_smoke"
        ]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        runtime_contract_gate = by_name["runtime_contract_gate"]
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(runtime_contract_gate["status"], "degraded")
        self.assertIn(
            "runtime_contract_summary.child_executor_sandbox_backend_coverage.sandbox_backend_smoke",
            runtime_contract_gate["missing_fields"],
        )

    def test_build_snapshot_degrades_when_approval_lifecycle_recovery_coverage_is_missing_from_summary(self):
        profile = _build_complete_profile()
        del profile["runtime_contract_gate"]["runtime_contract_summary"]["approval_lifecycle_recovery_coverage"]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        runtime_contract_gate = by_name["runtime_contract_gate"]
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(runtime_contract_gate["status"], "degraded")
        self.assertIn(
            "runtime_contract_summary.approval_lifecycle_recovery_coverage",
            runtime_contract_gate["missing_fields"],
        )

    def test_build_snapshot_degrades_when_runtime_contract_artifact_schema_is_missing(self):
        profile = _build_complete_profile()
        del profile["runtime_contract_gate"]["runtime_contract_artifact_schema"]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        runtime_contract_gate = by_name["runtime_contract_gate"]
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(runtime_contract_gate["status"], "degraded")
        self.assertIn("runtime_contract_artifact_schema", runtime_contract_gate["missing_fields"])

    def test_build_snapshot_degrades_when_runtime_contract_artifact_schema_missing_fields_list_is_missing(self):
        profile = _build_complete_profile()
        del profile["runtime_contract_gate"]["runtime_contract_artifact_schema"]["summary_missing_fields"]

        snapshot = RuntimeContractSnapshotService().build_snapshot(profile)

        by_name = {item["contract_name"]: item for item in snapshot["contracts"]}
        runtime_contract_gate = by_name["runtime_contract_gate"]
        self.assertEqual(snapshot["overall_status"], "degraded")
        self.assertEqual(runtime_contract_gate["status"], "degraded")
        self.assertIn(
            "runtime_contract_artifact_schema.summary_missing_fields",
            runtime_contract_gate["missing_fields"],
        )


if __name__ == "__main__":
    unittest.main()
