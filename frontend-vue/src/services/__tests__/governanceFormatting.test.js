import { describe, expect, it } from 'vitest'

import {
  formatAuditEvent,
  formatEmbeddedRuntimeBootstrapSummary,
  formatPayloadSummary,
  formatTimelineDomain,
  formatTraceSource,
  inferTimelineDomain,
  normalizeSeverity,
  stringifyPayloadValue,
} from '../governanceFormatting'

describe('governanceFormatting', () => {
  it('formats audit events and timeline domains', () => {
    expect(formatAuditEvent('doctor_gate_failed')).toBe('Doctor 门禁失败')
    expect(formatAuditEvent('framework_adapter_external_failure_diagnostic')).toBe('Framework Adapter 外部执行失败诊断')
    expect(formatTimelineDomain('runtime_contract')).toBe('Runtime Contract')
    expect(formatTimelineDomain('main_chat')).toBe('Main Chat')
  })

  it('infers timeline domain from source event and payload', () => {
    expect(inferTimelineDomain('query_control_planning', 'query_control', { channel: 'main_chat' })).toBe('main_chat')
    expect(inferTimelineDomain('permission_approved', '', null)).toBe('permission')
    expect(inferTimelineDomain('runtime_contract_gate_degraded', '', null)).toBe('runtime_contract')
    expect(inferTimelineDomain('framework_adapter_output', '', null)).toBe('framework_adapter')
    expect(inferTimelineDomain('unknown_event', 'mcp', null)).toBe('mcp')
  })

  it('normalizes severity and trace source labels', () => {
    expect(normalizeSeverity('doctor_gate_failed')).toBe('warning')
    expect(normalizeSeverity('permission_approved')).toBe('success')
    expect(normalizeSeverity('doctor_run_started')).toBe('info')
    expect(formatTraceSource('framework_adapter')).toBe('Framework Adapter')
    expect(formatTraceSource('doctor')).toBe('Doctor')
  })

  it('formats payload summary and value serialization', () => {
    expect(stringifyPayloadValue(['a', 'b'])).toBe('a, b')
    expect(formatPayloadSummary({
      action_id: 'A1',
      status: 'done',
      server_name: 'filesystem',
      tool_name: 'read',
      ignored: 'x',
    })).toBe('action_id=A1 | status=done | server_name=filesystem | tool_name=read')
    expect(formatEmbeddedRuntimeBootstrapSummary({
      requested_embedded_workspace_store_mode: 'memory_only',
      current_runtime_mode: 'memory_preview',
      current_recovery_posture: 'in_process_only',
      current_workspace_backend_mode: 'memory_only',
      bootstrap_recovery_validation_status: 'passed',
    })).toBe('workspace_mode=memory_only · runtime=memory_preview · recovery=in_process_only · backend=memory_only · validation=passed')
    expect(formatPayloadSummary({
      requested_embedded_workspace_store_mode: 'memory_only',
      current_runtime_mode: 'memory_preview',
      current_recovery_posture: 'in_process_only',
      current_workspace_backend_mode: 'memory_only',
      bootstrap_recovery_validation_status: 'passed',
    })).toBe('workspace_mode=memory_only · runtime=memory_preview · recovery=in_process_only · backend=memory_only · validation=passed')
    expect(formatPayloadSummary({
      overall_status: 'degraded',
      failed_check_count: 1,
      runtime_contract_summary: {
        missing_payload_count: 2,
        approval_replay_coverage: {
          event_payload_sample: false,
            observed_status_kinds: ['approval_created', 'approval_resolved'],
          },
          approval_lifecycle_recovery_coverage: {
            alignment_smoke: true,
            contract_version: 'phase-ii-approval-lifecycle-recovery-v1',
            replayed_submission_status: 'replayed',
            ignored_submission_status: 'ignored',
            resolved_recovery_reason: 'already_resolved',
          },
          approved_tool_execution_coverage: {
            bridge_smoke: true,
            contract_version: 'phase-ii-runtime-approved-tool-execution-v1',
            approved_tool_call_count: 1,
          },
          sdk_tool_runtime_execution_coverage: {
            bridge_smoke: true,
            contract_version: 'phase-ii-sdk-tool-runtime-execution-v1',
            approved_tool_call_count: 1,
          },
          embedded_sdk_persistence_coverage: {
            persistence_smoke: true,
            contract_version: 'phase-ii-embedded-sdk-persistence-v1',
            durable_cross_process_candidate: true,
          },
          worker_ownership_store_mode_coverage: {
            mode_smoke: true,
            contract_version: 'phase-ii-worker-ownership-store-mode-v1',
            default_mode: 'memory_only',
          },
          child_executor_promotion_gate_coverage: {
            gate_smoke: true,
            contract_version: 'phase-ii-child-executor-promotion-gate-v1',
            gate_status: 'blocked',
          },
          child_executor_execution_prerequisites_coverage: {
            prerequisites_smoke: true,
            contract_version: 'phase-ii-child-executor-execution-prerequisites-v1',
            ready: false,
          },
          child_executor_dispatch_coverage: {
            dispatch_smoke: true,
            contract_version: 'phase-ii-child-executor-dispatch-v1',
            dispatch_ready: false,
          },
          child_executor_dispatcher_coverage: {
            dispatcher_smoke: true,
            contract_version: 'phase-ii-child-executor-dispatcher-v1',
            default_status: 'blocked',
          },
          subagent_lane_query_detail_coverage: {
            detail_smoke: true,
            contract_version: 'phase-h-subagent-lane-query-detail-v1',
            recording_state: 'recorded',
            stage_count: 2,
            recent_event_count: 2,
          },
          recovery_retry_evidence_coverage: {
            retry_smoke: true,
            contract_version: 'phase-ii-recovery-retry-protocol-v1',
            retry_status: 'exhausted',
          },
          recovery_retry_scheduler_coverage: {
            scheduler_smoke: true,
            contract_version: 'phase-ii-recovery-retry-scheduler-v1',
            default_status: 'disabled',
          },
          durable_recovery_loader_coverage: {
            loader_smoke: true,
            contract_version: 'phase-ii-durable-recovery-loader-v1',
            loader_status: 'ready',
          },
          checkpoint_resume_cursor_coverage: {
            cursor_smoke: true,
            contract_version: 'phase-ii-durable-checkpoint-resume-v1',
            checkpoint_status: 'ready',
            resume_cursor_status: 'ready',
          },
        },
    })).toBe('runtime_contract=degraded · failed=1 · missing_payloads=2 · approval_replay=missing · approval_lifecycle=covered · approved_tool=covered · sdk_tool=covered · embedded_persistence=covered · worker_ownership=covered · child_executor_gate=covered · child_executor_prerequisites=covered · child_executor_dispatch=covered · child_executor_dispatcher=covered · subagent_detail=covered · recovery_retry=covered · recovery_retry_scheduler=covered · durable_loader=covered · checkpoint_cursor=covered')
    expect(formatPayloadSummary({
      overall_status: 'degraded',
      failed_check_count: 1,
      runtime_contract_summary: {
        missing_payload_count: 2,
        approval_replay_coverage: {
          event_payload_sample: false,
          observed_status_kinds: ['approval_created', 'approval_resolved'],
        },
      },
    })).toBe('runtime_contract=degraded · failed=1 · missing_payloads=2 · approval_replay=missing · approval_lifecycle=missing · approved_tool=missing · sdk_tool=missing · embedded_persistence=missing · worker_ownership=missing · child_executor_gate=missing · child_executor_prerequisites=missing · child_executor_dispatch=missing · child_executor_dispatcher=missing · subagent_detail=missing · recovery_retry=missing · recovery_retry_scheduler=missing · durable_loader=missing · checkpoint_cursor=missing')
    expect(formatPayloadSummary({
      overall_status: 'unknown',
      runtime_contract_summary: {
        overall_status: 'unknown',
        check_count: 0,
        failed_check_count: 0,
        missing_payload_count: 0,
        approval_replay_coverage: {
          event_payload_sample: false,
          observed_status_kinds: [],
        },
      },
    })).toBe('runtime_contract=unknown · failed=0 · missing_payloads=0 · approval_replay=unknown · approval_lifecycle=unknown · approved_tool=unknown · sdk_tool=unknown · embedded_persistence=unknown · worker_ownership=unknown · child_executor_gate=unknown · child_executor_prerequisites=unknown · child_executor_dispatch=unknown · child_executor_dispatcher=unknown · subagent_detail=unknown · recovery_retry=unknown · recovery_retry_scheduler=unknown · durable_loader=unknown · checkpoint_cursor=unknown')
  })
})
