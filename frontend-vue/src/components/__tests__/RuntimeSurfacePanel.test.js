import { mount, flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

const { getProfileMock, getMainChatQueryHistoryMock, getSubagentLaneRecentSummaryMock, getChildExecutorOutputReplayMock, getChildExecutorOutputSummaryMock, getChildExecutorMergedSemanticsMock, updateProfileMock, updateEmbeddedRuntimeBootstrapMock, runFrameworkAdapterPilotMock, precheckFrameworkAdapterMock, runExternalFrameworkAdapterPilotMock } = vi.hoisted(() => ({
  getProfileMock: vi.fn(),
  getMainChatQueryHistoryMock: vi.fn(),
  getSubagentLaneRecentSummaryMock: vi.fn(),
  getChildExecutorOutputReplayMock: vi.fn(),
  getChildExecutorOutputSummaryMock: vi.fn(),
  getChildExecutorMergedSemanticsMock: vi.fn(),
  updateProfileMock: vi.fn(),
  updateEmbeddedRuntimeBootstrapMock: vi.fn(),
  runFrameworkAdapterPilotMock: vi.fn(),
  precheckFrameworkAdapterMock: vi.fn(),
  runExternalFrameworkAdapterPilotMock: vi.fn()
}))

const { routeQuery, pushMock } = vi.hoisted(() => ({
  routeQuery: {},
  pushMock: vi.fn()
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({
    query: routeQuery
  }),
  useRouter: () => ({
    push: pushMock
  })
}))

vi.mock('../../api', () => ({
  runtimeSurfaceApi: {
    getProfile: getProfileMock,
    getMainChatQueryHistory: getMainChatQueryHistoryMock,
    getSubagentLaneRecentSummary: getSubagentLaneRecentSummaryMock,
    getChildExecutorOutputReplay: getChildExecutorOutputReplayMock,
    getChildExecutorOutputSummary: getChildExecutorOutputSummaryMock,
    getChildExecutorMergedSemantics: getChildExecutorMergedSemanticsMock,
    updateProfile: updateProfileMock,
    updateEmbeddedRuntimeBootstrap: updateEmbeddedRuntimeBootstrapMock,
    precheckFrameworkAdapter: precheckFrameworkAdapterMock,
    runFrameworkAdapterPilot: runFrameworkAdapterPilotMock,
    runExternalFrameworkAdapterPilot: runExternalFrameworkAdapterPilotMock
  }
}))

import RuntimeSurfacePanel from '../RuntimeSurfacePanel.vue'
import { useConversationStore } from '../../stores/conversation'
import { usePlannerStore } from '../../stores/planner'
import { useSettingsStore } from '../../stores/settings'

let pinia

function buildProfile(overrides = {}) {
  return {
    auth_mode: 'demo_guest',
    default_model: 'doubao',
    models: [{ name: 'doubao', display_name: '豆包' }],
    providers: [],
    runtime_core: {
      runtime_core: true,
      run_id: 'run-main-01',
      parent_run_id: 'root-run-00',
      child_run_id: 'child-7',
      scheduler_run_id: 'sched-run-01',
      run_kind: 'chat',
      status: 'waiting_approval',
      trace_count: 6,
      child_merge_intent: 'risk_review',
      child_merge_entities: ['交易', '风险'],
      child_merge_entity_count: 2,
      child_merge_focus_count: 3,
      child_merge_action_count: 3,
      child_merge_primary_entities: ['交易', '风险'],
      child_merge_conclusion: '建议人工复核关键风险点后继续主流程',
      latest_trace_event: {
        event_type: 'tool_permission_required',
        source: 'governance',
        severity: 'warning',
        summary: '等待 shell_command 审批',
        detail: 'request_id=approval-1'
      }
    },
    run_recovery: {
      contract_version: 'phase-ii-run-recovery-v1',
      available: true,
      run_id: 'run-main-01',
      run_state: 'observing',
      recoverable: true,
      tool_continuation: {
        recovery_status: 'recoverable',
        recovery_reason: 'ready_via_registry',
        descriptor_present: true,
        executable_available: true
      },
      loop_continuation: {
        recovery_status: 'recoverable',
        recovery_reason: 'ready_via_registry',
        descriptor_present: true,
        executable_available: true
      },
      workspace_backend: {
        backend_kind: 'sqlalchemy',
        durable: true,
        fallback_active: false,
        fallback_reason: ''
      },
      reason: ''
    },
    governance_overview: {
      run: {
        run_id: 'sched-run-01',
        parent_run_id: 'root-run-00',
        child_run_id: 'child-7',
        scheduler_run_id: 'sched-run-01',
        run_kind: 'scheduler',
        status: 'running',
        trace_count: 6,
        latest_trace_event: {
          event_type: 'scheduler_execution_started',
          source: 'scheduler',
          severity: 'info',
          summary: '调度执行中',
          detail: 'child_count=2'
        },
        child_merge_intent: 'risk_review',
        child_merge_entities: ['交易', '风险'],
        child_merge_entity_count: 2,
        child_merge_focus_count: 3,
        child_merge_action_count: 3,
        child_merge_primary_entities: ['交易', '风险'],
        child_merge_conclusion: '建议人工复核关键风险点后继续主流程'
      },
      run_recovery: {
        contract_version: 'phase-ii-run-recovery-v1',
        available: true,
        run_id: 'run-main-01',
        run_state: 'observing',
        recoverable: true,
        tool_continuation: {
          recovery_status: 'recoverable',
          recovery_reason: 'ready_via_registry',
          descriptor_present: true,
          executable_available: true
        },
        loop_continuation: {
          recovery_status: 'recoverable',
          recovery_reason: 'ready_via_registry',
          descriptor_present: true,
          executable_available: true
        },
        workspace_backend: {
          backend_kind: 'sqlalchemy',
          durable: true,
          fallback_active: false,
          fallback_reason: ''
        },
        reason: ''
      },
      child_executor_preflight: {
        contract_version: 'phase-ii-child-executor-preflight-v1',
        status: 'promotion_candidate',
        promotion_ready: true,
        real_child_executor_ready: true,
        executor_binding_status: 'ready',
        executor_binding_blockers: [],
        recommended_next_step: 'wire_executor_backend',
        delegate_gate_status: 'passed',
        delegate_gate_allowed: true,
        delegate_gate_failure_reason: '',
        delegate_promotion_requirements: ['child_run_recovery_boundary_defined', 'child_context_budget_defined'],
        delegate_missing_requirements: [],
        delegate_non_goals: ['real_child_executor_dispatch'],
        delegate_current_scope: ['create_child_run_relationship'],
        workspace_backend: {
          backend_kind: 'sqlalchemy',
          backend_mode: 'strict_sql',
          durable: true,
          operation_fallback_allowed: false,
          fallback_active: false,
          fallback_reason: '',
          last_error: '',
        }
      },
      approval: {
        request_count: 2,
        pending_count: 1,
        latest_request: {
          request_id: 'approval-1',
          status: 'pending',
          tool_name: 'shell_command',
          permission_level: 'elevated'
        }
      },
      audit: {
        event_count: 3,
        latest_event: {
          event_type: 'remediation_status_updated',
          source: 'governance',
          severity: 'info',
          summary: '整改已同步',
          detail: 'fix_runtime_contract'
        }
      },
      main_chat: {
        recording_state: 'recorded',
        trace_event_count: 1,
        stage_counts: {
          planning: 1
        },
        last_success_stage: 'planning',
        last_warning_stage: '',
        recent_queries: [
          {
            query_id: 'manual-chat-1',
            latest_stage: 'planning',
            latest_summary: 'Main chat planning',
            latest_timestamp: '2026-05-16T10:00:00Z',
            latest_snapshot_id: 'QUER-PLAN-321-20260516100000',
            stage_counts: { planning: 1 },
            last_success_stage: 'planning',
            last_warning_stage: '',
            recording_state: 'recorded'
          }
        ],
        latest_stage: 'planning',
        latest_query_id: 'manual-chat-1',
        latest_summary: 'Main chat planning',
        latest_timestamp: '2026-05-16T10:00:00Z',
        latest_snapshot_id: 'QUER-PLAN-321-20260516100000',
        reason: ''
      }
    },
    main_chat_trace_overview: {
      contract_version: 'phase-g-main-chat-trace-overview-v1',
      connected: true,
      has_runtime_target: true,
      trace_event_count: 1,
      stage_counts: {
        planning: 1
      },
      last_success_stage: 'planning',
      last_warning_stage: '',
      recent_queries: [
        {
          query_id: 'manual-chat-1',
          latest_stage: 'planning',
          latest_summary: 'Main chat planning',
          latest_timestamp: '2026-05-16T10:00:00Z',
          latest_snapshot_id: 'QUER-PLAN-321-20260516100000',
          stage_counts: { planning: 1 },
          last_success_stage: 'planning',
          last_warning_stage: '',
          recording_state: 'recorded'
        }
      ],
      latest_stage: 'planning',
      latest_query_id: 'manual-chat-1',
      latest_summary: 'Main chat planning',
      latest_detail: 'phase=planning',
      latest_timestamp: '2026-05-16T10:00:00Z',
      latest_snapshot_id: 'QUER-PLAN-321-20260516100000',
      recording_state: 'recorded',
      reason: ''
    },
    main_chat_query_detail: {
      contract_version: 'phase-g-main-chat-query-detail-v1',
      connected: true,
      query_id: 'manual-chat-1',
      recording_state: 'recorded',
      latest_summary: 'Main chat planning',
      stage_chain: ['planning'],
      dedupe_keys: ['query_control:main_chat:planning:321:manual-chat-1'],
      recent_events: [
        {
          timestamp: '2026-05-16T10:00:00Z',
          stage: 'planning',
          summary: 'Main chat planning',
          severity: 'info',
          snapshot_id: 'QUER-PLAN-321-20260516100000',
          dedupe_key: 'query_control:main_chat:planning:321:manual-chat-1'
        }
      ],
      latest_snapshot_id: 'QUER-PLAN-321-20260516100000',
      latest_warning_summary: '',
      latest_stage: 'planning',
      stage_count: 1,
      warning_count: 0,
      event_count: 1,
      reason: ''
    },
    tool_runtime: {
      contract_version: 'phase-b-tool-runtime-v1',
      total_tools: 5,
      base_tool_count: 1,
      langchain_tool_count: 2,
      tool_spec_count: 4,
      doubao_definition_count: 2,
      mcp_capability_count: 3,
      high_risk_tool_count: 1,
      tools: [
        { name: 'mcp_filesystem_write', kind: 'langchain', risk_level: 'high', permission_level: 'high_risk' }
      ]
    },
    mcp_runtime: {
      contract_version: 'phase-b-mcp-runtime-v1',
      overall_status: 'healthy',
      capability_count: 2,
      enabled_servers: 1,
      components: [
        { component_id: 'mcp_registry', display_name: 'MCP Registry', status: 'healthy', detail: '2 capabilities registered' },
        { component_id: 'mcp_session_manager', display_name: 'MCP Session Manager', status: 'healthy', detail: 'session boundary ready' },
        { component_id: 'mcp_capability_router', display_name: 'MCP Capability Router', status: 'healthy', detail: 'capability router ready' },
        { component_id: 'mcp_audit', display_name: 'MCP Audit', status: 'healthy', detail: '0 runtime audit records buffered' }
      ]
    },
    adapter_health: {
      contract_version: 'phase-b-adapter-health-v1',
      overall_status: 'not_configured',
      adapter_count: 3,
      unavailable_count: 0,
      latest_external_pilot_failure: {
        event_type: 'framework_adapter_external_error',
        error_type: 'protocol_error',
        adapter_id: 'langgraph_draft',
        framework_name: 'LangGraph',
        detail: 'transport probe did not provide assistant identity evidence',
        snapshot_ref: {
          snapshot_id: 'FRAM-EXT-ERR-321-20260513010000',
          generated_at: '2026-05-13T01:00:00Z',
          conversation_id: 321,
          source: 'framework_adapter',
          event_type: 'framework_adapter_external_error'
        }
      },
      external_pilot_failure_counts: {
        total: 3,
        window_scope: 'recent_plan_items',
        sample_size: 50,
        by_error_type: {
          protocol_error: 2,
          connectivity_error: 1
        }
      },
      adapters: [
        {
          adapter_id: 'tool_registry',
          display_name: 'Tool Registry',
          status: 'healthy',
          configuration_status: 'ready',
          execution_mode: 'internal_registry',
          package_installed: true,
          runtime_enabled: true,
          required_env: [],
          missing_env: [],
          required_packages: [],
          missing_packages: [],
          execution_block_reason: ''
        },
        {
          adapter_id: 'mcp_runtime',
          display_name: 'MCP Runtime',
          status: 'healthy',
          configuration_status: 'ready',
          execution_mode: 'internal_runtime',
          package_installed: true,
          runtime_enabled: true,
          required_env: [],
          missing_env: [],
          required_packages: [],
          missing_packages: [],
          execution_block_reason: ''
        },
        {
          adapter_id: 'langgraph_draft',
          display_name: 'LangGraph',
          framework_name: 'LangGraph',
          adapter_type: 'agent_framework',
          status: 'not_configured',
          detail: 'LangGraph draft adapter is blocked: missing required package: langgraph',
          configuration_status: 'missing_package',
          execution_mode: 'draft_external_runtime',
          package_installed: false,
          runtime_enabled: false,
          required_env: ['LANGGRAPH_RUNTIME_ENDPOINT', 'LANGGRAPH_ASSISTANT_ID'],
          missing_env: ['LANGGRAPH_RUNTIME_ENDPOINT', 'LANGGRAPH_ASSISTANT_ID'],
          required_packages: ['langgraph'],
          missing_packages: ['langgraph'],
          execution_block_reason: 'missing required package: langgraph'
        }
      ]
    },
    skill_contract: {
      contract_version: 'phase-b-skill-definition-v1',
      total_definitions: 1,
      definitions: [
        {
          skill_id: 1,
          name: 'Frontend UI Review',
          version: '1.0.0',
          scope: 'chat',
          selection_reason: 'registered_enabled_skill',
          required_capabilities: ['filesystem.read']
        }
      ]
    },
    memory_contract: {
      contract_version: 'phase-b-memory-entry-v1',
      active: true,
      loaded_layers: [{ name: 'global', path: 'GLOBAL_AGENT.md' }],
      missing_layers: [],
      layer_order: ['global', 'project', 'local', 'org_policy'],
      memory_entries: [
        {
          memory_id: 'memory:global',
          source: 'agent_memory_layer',
          scope: 'global',
          confidence: 1,
          retrieval_reason: 'loaded_layer:global'
        }
      ]
    },
    subagent_contract: {
      total_profiles: 1,
      profiles: [
        {
          name: 'planner',
          description: '聚焦目标拆解、执行顺序与风险分级。',
          context_policy: 'shared',
          allowed_tools: ['planner.read'],
          preferred_models: ['doubao'],
          trigger_conditions: ['task_decomposition']
        }
      ]
    },
    command_contract: {
      contract_version: 'phase-b-command-runtime-v1',
      total_commands: 1,
      command_definitions: [
        {
          command_id: 'doctor',
          name: 'doctor',
          permission_level: 'read',
          execution_handler: 'command_handlers.run_doctor',
          required_capabilities: ['governance.runtime_read']
        }
      ],
      embedded_sdk: {
        contract_version: 'phase-b-embedded-sdk-v1',
        methods: [
          { method: 'create_run', stability: 'draft' },
          { method: 'stream_events', stability: 'draft' },
          { method: 'register_tool', stability: 'draft' },
          { method: 'submit_approval', stability: 'draft' },
          { method: 'resume_run', stability: 'draft' }
        ]
      },
      framework_commands: [{ id: 'snapshot', name: 'snapshot', description: '治理快照' }],
      governance_commands: []
    },
    embedded_runtime_bootstrap: {
      contract_version: 'phase-ii-embedded-runtime-factory-v1',
      runtime_backend: 'EmbeddedAgentRuntimeSDK',
      shared_default_runtime: true,
      default_runtime_profile: {
        db_mode: 'sqlite',
        embedded_workspace_store_mode: 'strict_sql',
        default_runtime_mode: 'durable_default',
        recovery_posture: 'cross_process_candidate',
        recommended_bootstrap: 'EmbeddedRuntimeFactory',
        configurable_bootstrap_knobs: ['embedded_workspace_store_mode'],
        hot_reloadable_bootstrap_knobs: ['embedded_workspace_store_mode'],
        restart_required_bootstrap_knobs: []
      },
      workspace_backend: {
        backend_kind: 'sqlalchemy',
        backend_mode: 'strict_sql',
        durable: true,
        operation_fallback_allowed: false,
        fallback_active: false,
        fallback_reason: '',
        last_error: ''
      },
      default_recovery_expectation: {
        cross_process_candidate: true,
        cross_process_block_reason: ''
      },
      bootstrap_recovery_validation: {
        contract_version: 'phase-ii-embedded-runtime-bootstrap-validation-v1',
        validation_status: 'passed',
        actual_recoverable: true,
        expected_recoverable: true,
        workspace_backend_kind: 'sqlalchemy',
        workspace_backend_mode: 'strict_sql',
        tool_recovery_reason: 'ready_via_registry',
        loop_recovery_reason: 'ready_via_registry'
      }
    },
    embedded_runtime_boundaries: {
      contract_version: 'phase-ii-embedded-runtime-boundaries-v1',
      connected: true,
      volatile_runtime_state: ['_runs', '_events', '_approvals', '_artifacts', '_tool_continuations', '_loop_continuations'],
      persistence_seams: ['run_workspace_snapshot', 'run_event_log', 'approval_snapshot', 'tool_approval_continuation_descriptor', 'loop_continuation_descriptor', 'artifact_store_seam'],
      recovery_entrypoints: [
        { method: 'probe_run_recovery', recovery_scope: 'continuation_descriptor_recoverability_probe' },
        { method: 'resume_run', mode: 'default', recovery_scope: 'observing_to_generating_state_resume' },
        { method: 'resume_run', mode: 'continue_loop', recovery_scope: 'observing_to_done_loop_continuation' }
      ],
      delegate_preflight_status: 'relationship_only',
      facade_delegate_preflight_status: 'relationship_only',
      real_child_executor_ready: false,
      delegate_executor_binding_status: 'blocked',
      delegate_executor_binding_blockers: ['child_context_budget_defined', 'child_result_merge_semantics_defined', 'worker_runtime_backend_selected'],
      delegate_recommended_next_step: 'keep_relationship_only',
      delegate_gate_status: 'blocked',
      delegate_gate_allowed: false,
      delegate_gate_failure_reason: 'child_executor_preflight_blocked',
      delegate_route_status: 'blocked',
      delegate_route_executor_path: '',
      delegate_route_reason: 'child_executor_preflight_blocked',
      delegate_route_recommended_action: 'keep_relationship_only',
      delegate_binding_status: 'blocked',
      delegate_binding_id: '',
      delegate_binding_reason: 'child_executor_route_blocked',
      delegate_binding_recommended_action: 'keep_relationship_only',
      delegate_stub_status: 'blocked',
      delegate_stub_binding_id: '',
      delegate_stub_executor_path: '',
      delegate_stub_reason: 'child_executor_route_blocked',
      delegate_stub_recommended_action: 'keep_relationship_only',
      delegate_execution_status: 'blocked',
      delegate_execution_binding_id: '',
      delegate_execution_executor_path: '',
      delegate_execution_mode: '',
      delegate_execution_output_summary: '',
      delegate_execution_reason: 'child_executor_binding_blocked',
      delegate_execution_output_text: '',
      delegate_execution_output_envelope: {},
      delegate_execution_recommended_action: 'keep_relationship_only',
      delegate_merge_status: '',
      delegate_merge_ready: false,
      delegate_merge_reason: '',
      delegate_merge_strategy: '',
      delegate_merged_summary: '',
      delegate_merged_output: '',
      delegate_merge_artifact_ref: {},
      delegate_merge_section_count: 0,
      delegate_replay_record_count: 0,
      delegate_replay_records: [],
      delegate_artifact_summary: {
        record_count: 0,
        latest_artifact_id: '',
        latest_merge_strategy: '',
        latest_merged_summary: '',
        latest_merged_output: '',
        artifact_ids: [],
        merge_strategies: [],
      },
      delegate_current_scope: [
        'create_child_run_relationship',
        'inherit_parent_run_identity_defaults',
        'persist_child_run_snapshot',
        'emit_child_run_created_event'
      ],
      delegate_promotion_requirements: [
        'child_run_recovery_boundary_defined',
        'child_context_budget_defined',
        'child_result_merge_semantics_defined',
        'worker_runtime_backend_selected'
      ],
      delegate_non_goals: ['real_child_executor_dispatch', 'multi_process_recovery', 'parallel_worker_budget_enforcement'],
      workspace_backend: {
        backend_kind: 'sqlalchemy',
        backend_mode: 'strict_sql',
        durable: true,
        operation_fallback_allowed: false,
        fallback_active: false,
        fallback_reason: '',
        last_error: '',
      },
      approved_reference_slices: [
        {
          source: 'learn-claude-code',
          role: 'conceptual_reference',
          slices: ['docs/zh/s11-error-recovery.md']
        },
        {
          source: 'claude-code',
          role: 'control_plane_reference',
          slices: ['src/utils/swarm/inProcessRunner.ts']
        }
      ]
    },
    contract_snapshot: {
      contract_version: 'phase-c-runtime-contract-snapshot-v1',
      overall_status: 'healthy',
      contract_count: 6,
      missing_contract_count: 0,
      missing_field_count: 0,
      fingerprint: 'abc123runtimecontractfingerprint',
      contracts: [
        {
          contract_name: 'tool_runtime',
          version: 'phase-b-tool-runtime-v1',
          status: 'healthy',
          field_count: 9,
          stable_fields: ['contract_version', 'total_tools', 'tools'],
          missing_fields: [],
          fingerprint: 'toolruntimefingerprint'
        },
        {
          contract_name: 'adapter_health',
          version: 'phase-b-adapter-health-v1',
          status: 'healthy',
          field_count: 5,
          stable_fields: ['contract_version', 'adapters'],
          missing_fields: [],
          fingerprint: 'adapterhealthfingerprint'
        }
      ]
    },
    runtime_contract_gate: {
      contract_version: 'phase-f-runtime-contract-gate-v1',
      available: true,
      overall_status: 'degraded',
      generated_at: '2026-05-13T08:00:00Z',
      report_path: 'quality-gate-report.json',
      check_count: 3,
      failed_check_count: 1,
      failure_reason: 'contract_checks_failed',
      runtime_contract_summary: {
        overall_status: 'degraded',
        check_count: 3,
        failed_check_count: 1,
        missing_payload_count: 0,
        approval_replay_coverage: {
          event_payload_sample: true,
          observed_status_kinds: ['approval_replayed', 'approval_ignored']
        }
      },
      checks: [
        {
          step: 'runtime_contract_smoke',
          name: 'embedded_sdk_event_payloads',
          ok: true,
          checked_event_count: 5,
          missing_payload_count: 0,
          observed_status_kinds: ['approval_replayed', 'approval_ignored']
        },
        {
          step: 'runtime_contract_smoke',
          name: 'adapter_health_status',
          ok: false,
          failure_reason: 'adapter health degraded',
          adapter_health_status: 'degraded'
        },
        {
          step: 'runtime_contract_smoke',
          name: 'embedded_sdk_durable_recovery',
          ok: false,
          failure_reason: 'durable_recovery_chain_incomplete',
          backend_kind: 'sqlalchemy',
          backend_mode: 'strict_sql',
          fallback_active: true,
          probe_recoverable: false,
          tool_recovery_reason: 'workspace_backend_fallback_active',
          loop_recovery_reason: 'workspace_backend_fallback_active',
          resumed_state: ''
        }
      ]
    },
    ...overrides
  }
}

function buildMainChatHistory(overrides = {}) {
  return {
    recording_state: 'recorded',
    items: [
      {
        query_id: 'manual-chat-3',
        latest_stage: 'review',
        latest_summary: 'Main chat review 3',
        latest_timestamp: '2026-05-16T10:10:00Z',
        latest_snapshot_id: 'QUER-REVIEW-3',
        stage_counts: { review: 1 },
        last_success_stage: 'review',
        last_warning_stage: '',
        recording_state: 'recorded',
      },
      {
        query_id: 'manual-chat-2',
        latest_stage: 'final_output',
        latest_summary: 'Main chat final output 2',
        latest_timestamp: '2026-05-16T10:05:00Z',
        latest_snapshot_id: 'QUER-FINAL-2',
        stage_counts: { final_output: 1 },
        last_success_stage: 'final_output',
        last_warning_stage: '',
        recording_state: 'recorded',
      },
    ],
    page: 1,
    page_size: 5,
    total_items: 3,
    has_more: true,
    next_cursor: '2026-05-16T10:05:00Z|manual-chat-2',
    reason: '',
    ...overrides,
  }
}

function buildSubagentLaneRecentSummary(overrides = {}) {
  return {
    recording_state: 'recorded',
    items: [
      {
        query_id: 'frontend-child-p10-i23-c1',
        latest_stage: 'final_output',
        latest_summary: '已合并 frontend 子智能体结果到主响应',
        latest_timestamp: '2026-05-17T10:00:00Z',
        latest_snapshot_id: '',
        last_success_stage: 'final_output',
        last_warning_stage: '',
        recording_state: 'recorded',
      },
    ],
    latest_query_id: 'frontend-child-p10-i23-c1',
    latest_stage: 'final_output',
    latest_summary: '已合并 frontend 子智能体结果到主响应',
    latest_timestamp: '2026-05-17T10:00:00Z',
    total_items: 1,
    reason: '',
    ...overrides,
  }
}

function buildChildExecutorOutputReplay(overrides = {}) {
  return {
    contract_version: 'phase-ii-child-executor-replay-v1',
    parent_run_id: 'run-main-01',
    record_count: 1,
    records: [
      {
        binding_id: 'binding:embedded_sdk_worker_candidate:run-main-01',
        execution_status: 'executed',
        executor_path: 'embedded_sdk_worker_candidate',
        result_type: 'risk_assessment',
        conclusion: '建议人工复核关键风险点后继续主流程',
        merge_status: 'merged',
        merge_strategy: 'append_summary',
        merged_summary: 'risk_reviewer 已通过 embedded_sdk_worker_skeleton 执行最小路径',
        artifact_id: 'child-output:binding:embedded_sdk_worker_candidate:run-main-01'
      }
    ],
    latest_merged_summary: 'risk_reviewer 已通过 embedded_sdk_worker_skeleton 执行最小路径',
    latest_merged_output: '风险复核结论：建议人工复核关键风险点后继续主流程',
    ...overrides,
  }
}

function buildChildExecutorOutputSummary(overrides = {}) {
  return {
    contract_version: 'phase-ii-child-executor-artifact-summary-v1',
    parent_run_id: 'run-main-01',
    record_count: 1,
    latest_artifact_id: 'child-output:binding:embedded_sdk_worker_candidate:run-main-01',
    latest_merge_strategy: 'append_summary',
    latest_result_type: 'risk_assessment',
    latest_conclusion: '建议人工复核关键风险点后继续主流程',
    latest_merged_summary: 'risk_reviewer 已通过 embedded_sdk_worker_skeleton 执行最小路径',
    latest_merged_output: '风险复核结论：建议人工复核关键风险点后继续主流程',
    latest_entities: ['交易', '风险'],
    latest_focus_points: ['识别输入中的高风险对象与异常信号', '确认是否需要人工审批或二次复核'],
    latest_action_items: ['优先复核交易的上下游证据', '检查是否存在跨账户异常'],
    latest_merged_semantics: {
      intent_label: 'risk_review',
      entities: ['交易', '风险'],
      focus_points: ['识别输入中的高风险对象与异常信号', '确认是否需要人工审批或二次复核'],
      action_items: ['优先复核交易的上下游证据', '检查是否存在跨账户异常'],
      merge_behavior: {
        entities: 'append_dedup',
        focus_points: 'append_dedup',
        action_items: 'append_dedup',
      },
    },
    artifact_ids: ['child-output:binding:embedded_sdk_worker_candidate:run-main-01'],
    merge_strategies: ['append_summary'],
    result_types: ['risk_assessment'],
    entity_sets: [['交易', '风险']],
    ...overrides,
  }
}

function buildChildExecutorMergedSemantics(overrides = {}) {
  return {
    contract_version: 'phase-ii-child-executor-merged-semantics-v2',
    parent_run_id: 'run-main-01',
    record_count: 1,
    available: true,
    intent_catalog_version: 'phase-ii-child-intent-catalog-v1',
    supported_intents: ['risk_review', 'planning', 'general_analysis'],
    intent_label: 'risk_review',
    entities: ['交易', '风险'],
    focus_points: ['识别输入中的高风险对象与异常信号', '确认是否需要人工审批或二次复核'],
    action_items: ['优先复核交易的上下游证据', '检查是否存在跨账户异常'],
    merge_behavior: {
      entities: 'append_dedup',
      focus_points: 'append_dedup',
      action_items: 'append_dedup',
    },
    merged_sections: {
      merged_entities: {
        section_id: 'merged_entities',
        title: 'Merged Entities',
        merge_mode: 'append_dedup',
        items: ['交易', '风险'],
      },
      merged_focus: {
        section_id: 'merged_focus',
        title: 'Merged Focus',
        merge_mode: 'append_dedup',
        items: ['识别输入中的高风险对象与异常信号', '确认是否需要人工审批或二次复核'],
      },
      merged_actions: {
        section_id: 'merged_actions',
        title: 'Merged Actions',
        merge_mode: 'append_dedup',
        items: ['优先复核交易的上下游证据', '检查是否存在跨账户异常'],
      },
      latest_conclusion: {
        section_id: 'latest_conclusion',
        title: 'Latest Conclusion',
        merge_mode: 'replace_latest',
        text: '建议人工复核关键风险点后继续主流程',
      },
    },
    parent_state_surface: {
      intent_label: 'risk_review',
      entity_count: 2,
      focus_count: 2,
      action_count: 2,
      primary_entities: ['交易', '风险'],
      latest_conclusion: '建议人工复核关键风险点后继续主流程',
    },
    latest_merged_summary: 'risk_reviewer 已通过 embedded_sdk_worker_skeleton 执行最小路径',
    latest_merged_output: '风险复核结论：建议人工复核关键风险点后继续主流程',
    latest_merge_strategy: 'append_summary',
    latest_result_type: 'risk_assessment',
    ...overrides,
  }
}

afterEach(() => {
  localStorage.removeItem('governance_recent_snapshot_commands')
  document.body.innerHTML = ''
})

beforeEach(() => {
  Object.keys(routeQuery).forEach(key => delete routeQuery[key])
  pinia = createPinia()
  setActivePinia(pinia)
  getProfileMock.mockReset()
  getMainChatQueryHistoryMock.mockReset()
  getSubagentLaneRecentSummaryMock.mockReset()
  getChildExecutorOutputReplayMock.mockReset()
  getChildExecutorOutputSummaryMock.mockReset()
  getChildExecutorMergedSemanticsMock.mockReset()
  updateProfileMock.mockReset()
  runFrameworkAdapterPilotMock.mockReset()
  precheckFrameworkAdapterMock.mockReset()
  runExternalFrameworkAdapterPilotMock.mockReset()
  pushMock.mockReset()
  getProfileMock.mockResolvedValue({ data: buildProfile() })
  getMainChatQueryHistoryMock.mockResolvedValue({ data: buildMainChatHistory() })
  getSubagentLaneRecentSummaryMock.mockResolvedValue({ data: buildSubagentLaneRecentSummary() })
  getChildExecutorOutputReplayMock.mockResolvedValue({ data: buildChildExecutorOutputReplay() })
  getChildExecutorOutputSummaryMock.mockResolvedValue({ data: buildChildExecutorOutputSummary() })
  getChildExecutorMergedSemanticsMock.mockResolvedValue({ data: buildChildExecutorMergedSemantics() })
  updateProfileMock.mockResolvedValue({ data: {} })
  updateEmbeddedRuntimeBootstrapMock.mockResolvedValue({
    data: {
      contract_version: 'phase-ii-embedded-runtime-factory-v1',
      default_runtime_profile: {
        embedded_workspace_store_mode: 'memory_only',
        default_runtime_mode: 'memory_preview',
        recovery_posture: 'in_process_only',
      },
      workspace_backend: {
        backend_kind: 'in_memory',
        backend_mode: 'memory_only',
        durable: false,
        fallback_active: false,
        fallback_reason: '',
        last_error: '',
      },
      bootstrap_recovery_validation: {
        contract_version: 'phase-ii-embedded-runtime-bootstrap-validation-v1',
        validation_status: 'passed',
        actual_recoverable: false,
        expected_recoverable: false,
        workspace_backend_kind: 'in_memory',
        workspace_backend_mode: 'memory_only',
      },
      post_update_verification: {
        effective_change: true,
        current_runtime_mode: 'memory_preview',
        current_recovery_posture: 'in_process_only',
        current_workspace_backend_kind: 'in_memory',
        current_workspace_backend_mode: 'memory_only',
        recovery_contract_aligned: true,
      },
      timeline_recording: {
        conversation_id: 321,
        snapshot_ref: {
          snapshot_id: 'RUNT-BOOT-321-20260520000000',
          generated_at: '2026-05-20T00:00:00Z',
          conversation_id: 321,
          source: 'runtime_control',
          event_type: 'embedded_runtime_bootstrap_updated',
        }
      }
    }
  })
  precheckFrameworkAdapterMock.mockResolvedValue({
    data: {
      adapter_id: 'langgraph_draft',
      framework_name: 'LangGraph',
      ready: false,
      status: 'not_configured',
      configuration_status: 'missing_package',
      execution_mode: 'draft_external_runtime',
      package_installed: false,
      runtime_enabled: false,
      required_packages: ['langgraph'],
      missing_packages: ['langgraph'],
      required_env: ['LANGGRAPH_RUNTIME_ENDPOINT', 'LANGGRAPH_ASSISTANT_ID'],
      missing_env: ['LANGGRAPH_RUNTIME_ENDPOINT', 'LANGGRAPH_ASSISTANT_ID'],
      execution_block_reason: 'missing required package: langgraph',
      detail: 'LangGraph draft adapter is blocked: missing required package: langgraph',
      timeline_recording: {
        conversation_id: 321,
        snapshot_ref: {
          snapshot_id: 'FRAM-PRECHECK-321',
          generated_at: '2026-05-12T00:00:00Z',
          conversation_id: 321,
          source: 'framework_adapter',
          event_type: 'framework_adapter_precheck_completed'
        }
      }
    }
  })
  runFrameworkAdapterPilotMock.mockResolvedValue({
    data: {
      adapter_id: 'local_fake_framework',
      run_id: 'ui-pilot-run-1',
      events: [{ type: 'status' }, { type: 'reasoning' }, { type: 'content' }],
      final_output: 'Local fake adapter processed: 请生成一份运行时巡检计划摘要',
      snapshot_ref: {
        snapshot_id: 'FRAM-FRAMEWORK_A-321-20260511000000',
        generated_at: '2026-05-11T00:00:00Z',
        conversation_id: 321,
        source: 'framework_adapter',
        event_type: 'framework_adapter_run_completed'
      }
    }
  })
  runExternalFrameworkAdapterPilotMock.mockResolvedValue({
    data: {
      adapter_id: 'langgraph_draft',
      framework_name: 'LangGraph',
      status: 'ok',
      error: null,
      events: [{ type: 'status' }, { type: 'reasoning' }, { type: 'content' }],
      final_output: 'LangGraph external answer',
      snapshot_ref: {
        snapshot_id: 'FRAM-EXT-321-20260513000000',
        generated_at: '2026-05-13T00:00:00Z',
        conversation_id: 321,
        source: 'framework_adapter',
        event_type: 'framework_adapter_external_pilot_completed'
      }
    }
  })

  const conversationStore = useConversationStore()
  conversationStore.conversations = [{
    id: 321,
    title: 'runtime pilot',
    modelName: 'doubao',
    messages: [],
    createdAt: Date.now(),
    updatedAt: Date.now()
  }]
  conversationStore.activeId = 321

  const plannerStore = usePlannerStore()
  plannerStore.plans = [{
    id: 10,
    objective: '治理时间线联动',
    active_item_id: 23,
    items: [
      {
        id: 23,
        title: '执行 adapter pilot',
        status: 'in_progress',
        run_trace: [],
        audit_trail: []
      }
    ]
  }]
  plannerStore.currentPlanId = 10
  plannerStore.loadPlans = vi.fn().mockResolvedValue(plannerStore.plans)
})

function mountPanel() {
  return mount(RuntimeSurfacePanel, {
    attachTo: document.body,
    global: {
      plugins: [pinia]
    }
  })
}

function buildAdapterHealthContractWithLangGraph(overrides = {}) {
  const profile = buildProfile()
  return {
    ...profile.adapter_health,
    adapters: profile.adapter_health.adapters.map((adapter) => {
      if (adapter.adapter_id !== 'langgraph_draft') {
        return adapter
      }
      return {
        ...adapter,
        ...overrides
      }
    })
  }
}

describe('RuntimeSurfacePanel', () => {
  it('renders runtime core and governance overview contracts', async () => {
    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).toContain('Runtime Core 合同')
    expect(wrapper.text()).toContain('run-main-01')
    expect(wrapper.text()).toContain('waiting_approval')
    expect(wrapper.text()).toContain('request_id=approval-1')
    expect(wrapper.text()).toContain('Parent Merge State')
    expect(wrapper.text()).toContain('Run Recovery')
    expect(wrapper.text()).toContain('ready_via_registry')
    expect(wrapper.text()).toContain('workspace_backend')
    expect(wrapper.text()).toContain('sqlalchemy')
    expect(wrapper.text()).toContain('child_merge_entity_count')
    expect(wrapper.text()).toContain('child_merge_focus_count')
    expect(wrapper.text()).toContain('child_merge_action_count')
    expect(wrapper.text()).toContain('child_merge_primary_entities')
    expect(wrapper.text()).toContain('治理总览合同')
    expect(wrapper.text()).toContain('sched-run-01')
    expect(wrapper.text()).toContain('1 个待处理')
    expect(wrapper.text()).toContain('shell_command')
    expect(wrapper.text()).toContain('整改已同步')
    expect(wrapper.text()).toContain('Run Recovery')
    expect(wrapper.text()).toContain('ready_via_registry')
    expect(wrapper.text()).toContain('Child Executor Preflight')
    expect(wrapper.text()).toContain('promotion_candidate')
    expect(wrapper.text()).toContain('wire_executor_backend')
    expect(wrapper.text()).toContain('治理 Query')
    expect(wrapper.text()).toContain('manual-chat-1')
    expect(wrapper.text()).toContain('recorded')
    expect(wrapper.text()).toContain('planning')
    expect(wrapper.text()).toContain('最近 Query')
    expect(wrapper.text()).toContain('Main Chat Recent Queries')
    expect(wrapper.text()).toContain('Query History Contract')
    expect(wrapper.text()).toContain('Query History Items')
    expect(wrapper.text()).toContain('Main chat review 3')
    expect(wrapper.text()).toContain('Query Recent Events')
    expect(getProfileMock).toHaveBeenCalledWith({
      conversation_id: 321,
      plan_id: 10,
      item_id: 23
    })
    expect(getMainChatQueryHistoryMock).toHaveBeenCalledWith({
      conversation_id: 321,
      plan_id: 10,
      item_id: 23,
      page: 1,
      page_size: 5
    })

    wrapper.unmount()
  })

  it('updates embedded runtime bootstrap through dedicated control plane endpoint', async () => {
    const wrapper = mountPanel()
    await flushPromises()

    const bootstrapSelect = wrapper.get('[data-testid="embedded-runtime-bootstrap-mode"]')
    await bootstrapSelect.setValue('memory_only')
    await wrapper.get('[data-testid="embedded-runtime-bootstrap-save"]').trigger('click')
    await flushPromises()

    expect(updateEmbeddedRuntimeBootstrapMock).toHaveBeenCalledWith({
      embedded_workspace_store_mode: 'memory_only',
      conversation_id: 321
    })
    expect(wrapper.text()).toContain('Embedded Runtime Bootstrap')
    expect(wrapper.text()).toContain('memory_preview')
    expect(wrapper.text()).toContain('RUNT-BOOT-321-20260520000000')
    expect(wrapper.text()).toContain('Embedded Runtime Bootstrap 更新')
    expect(wrapper.text()).toContain('workspace_mode=memory_only · runtime=memory_preview · recovery=in_process_only · backend=memory_only')

    wrapper.unmount()
  })

  it('toggles main chat runtime trace expert switch through settings store', async () => {
    const settingsStore = useSettingsStore()
    const wrapper = mountPanel()
    await flushPromises()

    expect(settingsStore.enableMainChatRuntimeTrace).toBe(false)

    const toggle = wrapper.find('.trace-toggle-row input')
    await toggle.setValue(true)

    expect(settingsStore.enableMainChatRuntimeTrace).toBe(true)
    expect(wrapper.text()).toContain('普通 chat 会附加受控 execution_context')
    expect(wrapper.text()).toContain('recorded')
    expect(wrapper.text()).toContain('manual-chat-1')

    wrapper.unmount()
  })

  it('surfaces runtime contract gate health in the top summary', async () => {
    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).toContain('契约门禁')
    expect(wrapper.text()).toContain('degraded')
    expect(wrapper.text()).toContain('failed checks: 1')

    wrapper.unmount()
  })

  it('navigates to governance timeline runtime contract warnings from the top gate summary', async () => {
    const wrapper = mountPanel()
    await flushPromises()

    const gateButton = wrapper.findAll('button').find(button => button.text().includes('查看治理事件'))
    expect(gateButton).toBeTruthy()

    await gateButton.trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/settings?tab=advanced&governance_filter=runtime_contract&governance_severity=warning')

    wrapper.unmount()
  })

  it('renders phase a placeholder information when runtime contracts are missing', async () => {
    getProfileMock.mockResolvedValueOnce({
      data: buildProfile({
        runtime_core: undefined,
        governance_overview: undefined
      })
    })

    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).toContain('Runtime Core 合同')
    expect(wrapper.text()).toContain('等待后端接入 runtime_core contract')
    expect(wrapper.text()).toContain('治理总览合同')
    expect(wrapper.text()).toContain('等待后端接入 governance_overview contract')

    wrapper.unmount()
  })

  it('renders phase b tool runtime and adapter health contracts', async () => {
    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).toContain('Tool Runtime 合同')
    expect(wrapper.text()).toContain('phase-b-tool-runtime-v1')
    expect(wrapper.text()).toContain('5')
    expect(wrapper.text()).toContain('LangChain 工具')
    expect(wrapper.text()).toContain('MCP capability')
    expect(wrapper.text()).toContain('高风险工具')
    expect(wrapper.text()).toContain('Adapter Health')
    expect(wrapper.text()).toContain('phase-b-adapter-health-v1')
    expect(wrapper.text()).toContain('not_configured')
    expect(wrapper.text()).toContain('LangGraph')
    expect(wrapper.text()).toContain('config: 缺包')
    expect(wrapper.text()).toContain('mode: 外部草稿运行时')
    expect(wrapper.text()).toContain('pkg: 缺失')
    expect(wrapper.text()).toContain('runtime: 未启用')
    expect(wrapper.text()).toContain('依赖包: langgraph')
    expect(wrapper.text()).toContain('缺失依赖包: langgraph')
    expect(wrapper.text()).toContain('环境变量: LANGGRAPH_RUNTIME_ENDPOINT')
    expect(wrapper.text()).toContain('环境变量: LANGGRAPH_ASSISTANT_ID')
    expect(wrapper.text()).toContain('缺失环境变量: LANGGRAPH_RUNTIME_ENDPOINT')
    expect(wrapper.text()).toContain('缺失环境变量: LANGGRAPH_ASSISTANT_ID')
    expect(wrapper.text()).toContain('阻塞原因: 缺少必需依赖包 (missing required package: langgraph)')
    expect(wrapper.text()).toContain('运行预检')
    expect(wrapper.text()).toContain('当前缺包，建议先安装依赖，再执行预检确认 env / runtime 开关状态。')
    expect(wrapper.text()).toContain('最近一次 LangGraph External Pilot 失败')
    expect(wrapper.text()).toContain('错误: 协议错误 (protocol_error)')
    expect(wrapper.text()).toContain('失败总数: 3')
    expect(wrapper.text()).toContain('统计窗口: 最近 PlanItem')
    expect(wrapper.text()).toContain('样本数: 50')
    expect(wrapper.text()).toContain('错误分布: 协议错误 2 · 连通性错误 1')
    expect(wrapper.text()).toContain('错误详情: transport probe did not provide assistant identity evidence')
    expect(wrapper.text()).toContain('FRAM-EXT-ERR-321-20260513010000')
    expect(wrapper.text()).toContain('adapter_id: langgraph_draft')
    expect(wrapper.text()).toContain('查看时间线')

    wrapper.unmount()
  })

  it('navigates to framework adapter diagnostic timeline when clicking failure distribution entry', async () => {
    const wrapper = mountPanel()
    await flushPromises()

    const distributionButton = wrapper.findAll('button').find(button => button.text().includes('协议错误 2'))
    expect(distributionButton).toBeTruthy()

    await distributionButton.trigger('click')
    await flushPromises()

    expect(pushMock).toHaveBeenCalledWith('/settings?tab=advanced&governance_filter=framework_adapter&governance_severity=warning&governance_error_type=protocol_error')

    wrapper.unmount()
  })

  it('navigates to governance timeline main_chat query view from recent query list', async () => {
    const wrapper = mountPanel()
    await flushPromises()

    const queryButton = wrapper.findAll('button').find(button => button.text().includes('manual-chat-1'))
    expect(queryButton).toBeTruthy()

    await queryButton.trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/settings?tab=advanced&governance_filter=main_chat&governance_query_id=manual-chat-1')

    wrapper.unmount()
  })

  it('loads more main chat query history items', async () => {
    getMainChatQueryHistoryMock
      .mockResolvedValueOnce({ data: buildMainChatHistory() })
      .mockResolvedValueOnce({
        data: buildMainChatHistory({
          items: [
            {
              query_id: 'manual-chat-1',
              latest_stage: 'planning',
              latest_summary: 'Main chat planning 1',
              latest_timestamp: '2026-05-16T10:00:00Z',
              latest_snapshot_id: 'QUER-PLAN-1',
              stage_counts: { planning: 1 },
              last_success_stage: 'planning',
              last_warning_stage: '',
              recording_state: 'recorded',
            },
          ],
          page: 2,
          total_items: 3,
          has_more: false,
          next_cursor: '',
        })
      })

    const wrapper = mountPanel()
    await flushPromises()

    const loadMoreButton = wrapper.findAll('button').find(button => button.text().includes('加载更多'))
    expect(loadMoreButton).toBeTruthy()

    await loadMoreButton.trigger('click')
    await flushPromises()

    expect(getMainChatQueryHistoryMock).toHaveBeenLastCalledWith({
      conversation_id: 321,
      plan_id: 10,
      item_id: 23,
      page: 2,
      page_size: 5
    })
    expect(wrapper.text()).toContain('Main chat planning 1')

    wrapper.unmount()
  })

  it('passes governance_query_id into runtime profile context and renders query detail contract', async () => {
    routeQuery.governance_query_id = 'manual-chat-1'
    const wrapper = mountPanel()
    await flushPromises()

    expect(getProfileMock).toHaveBeenCalledWith({
      conversation_id: 321,
      plan_id: 10,
      item_id: 23,
      query_id: 'manual-chat-1'
    })
    expect(wrapper.text()).toContain('Query Detail Contract')
    expect(wrapper.text()).toContain('layer')
    expect(wrapper.text()).toContain('source')
    expect(wrapper.text()).toContain('identity')
    expect(wrapper.text()).toContain('manual-chat-1')
    expect(wrapper.text()).toContain('Query Stage Chain')
    expect(wrapper.text()).toContain('Main chat planning')
    expect(wrapper.text()).toContain('stage_count')
    expect(wrapper.text()).toContain('warning_count')

    wrapper.unmount()
  })

  it('marks active framework adapter failure distribution entry from route state', async () => {
    routeQuery.governance_filter = 'framework_adapter'
    routeQuery.governance_severity = 'warning'
    routeQuery.governance_error_type = 'protocol_error'

    const wrapper = mountPanel()
    await flushPromises()

    const protocolButton = wrapper.findAll('button').find(button => button.text().includes('协议错误 2'))
    const connectivityButton = wrapper.findAll('button').find(button => button.text().includes('连通性错误 1'))

    expect(protocolButton).toBeTruthy()
    expect(connectivityButton).toBeTruthy()
    expect(protocolButton.classes()).toContain('active')
    expect(connectivityButton.classes()).not.toContain('active')

    wrapper.unmount()
  })

  it.each([
    {
      label: '缺环境变量',
      overrides: {
        detail: 'LangGraph draft adapter is blocked: missing required env: LANGGRAPH_RUNTIME_ENDPOINT',
        configuration_status: 'missing_env',
        package_installed: true,
        missing_packages: [],
        execution_block_reason: 'missing required env: LANGGRAPH_RUNTIME_ENDPOINT'
      },
      expectedHint: '当前缺环境变量，建议先补齐配置，再执行预检确认 readiness。'
    },
    {
      label: '运行时开关未启用',
      overrides: {
        detail: 'LangGraph draft adapter is blocked: runtime execution is not enabled',
        configuration_status: 'runtime_disabled',
        package_installed: true,
        runtime_enabled: false,
        missing_packages: [],
        missing_env: [],
        execution_block_reason: 'runtime execution is not enabled'
      },
      expectedHint: '当前运行时执行开关未启用，可先执行预检确认配置是否已就绪。'
    },
    {
      label: '已就绪',
      overrides: {
        detail: 'LangGraph draft adapter is ready',
        status: 'healthy',
        configuration_status: 'ready',
        package_installed: true,
        runtime_enabled: true,
        missing_packages: [],
        missing_env: [],
        execution_block_reason: ''
      },
      expectedHint: '当前已就绪，可执行预检确认 readiness，不进入真实执行链。'
    }
  ])('renders adapter precheck hint for $label state', async ({ overrides, expectedHint }) => {
    getProfileMock.mockResolvedValue({
      data: buildProfile({
        adapter_health: buildAdapterHealthContractWithLangGraph(overrides)
      })
    })

    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).toContain(expectedHint)

    wrapper.unmount()
  })

  it('runs framework adapter precheck and renders remediation command', async () => {
    const wrapper = mountPanel()
    await flushPromises()

    const trigger = wrapper.findAll('button').find(button => button.text().includes('运行预检'))
    expect(trigger).toBeTruthy()

    await trigger.trigger('click')
    await flushPromises()

    expect(precheckFrameworkAdapterMock).toHaveBeenCalledTimes(1)
    expect(precheckFrameworkAdapterMock).toHaveBeenCalledWith({
      adapter_id: 'langgraph_draft',
      conversation_id: 321,
      execution_context: {
        run_kind: 'framework_adapter_precheck',
        plan_id: 10,
        plan_item_id: 23
      }
    })
    expect(wrapper.text()).toContain('最近 LangGraph Precheck')
    expect(wrapper.text()).toContain('状态: 缺包')
    expect(wrapper.text()).toContain('就绪度: 未就绪')
    expect(wrapper.text()).toContain('configuration_status')
    expect(wrapper.text()).toContain('缺包 (missing_package)')
    expect(wrapper.text()).toContain('外部草稿运行时 (draft_external_runtime)')
    expect(wrapper.text()).toContain('缺少必需依赖包 (missing required package: langgraph)')
    expect(wrapper.text()).toContain('复制修复命令')
    expect(wrapper.text()).toContain('FRAM-PRECHECK-321')
    expect(wrapper.text()).toContain('查看时间线')
    expect(wrapper.text()).toContain('ready')
    expect(wrapper.text()).toContain('false')
    expect(wrapper.text()).toContain('adapter_id: langgraph_draft')

    wrapper.unmount()
  })

  it('runs langgraph external pilot and renders latest result', async () => {
    getProfileMock.mockResolvedValueOnce({
      data: buildProfile({
        adapter_health: buildAdapterHealthContractWithLangGraph({
          status: 'healthy',
          detail: 'LangGraph draft adapter is registered and ready for runtime binding.',
          configuration_status: 'ready',
          package_installed: true,
          runtime_enabled: true,
          required_packages: [],
          missing_packages: [],
          required_env: [],
          missing_env: [],
          execution_block_reason: ''
        })
      })
    })

    const wrapper = mountPanel()
    await flushPromises()
    const plannerStore = usePlannerStore()

    const trigger = wrapper.findAll('button').find(button => button.text().includes('运行 External Pilot'))
    expect(trigger).toBeTruthy()

    await trigger.trigger('click')
    await flushPromises()

    expect(runExternalFrameworkAdapterPilotMock).toHaveBeenCalledTimes(1)
    expect(runExternalFrameworkAdapterPilotMock.mock.calls[0][0]).toMatchObject({
      adapter_id: 'langgraph_draft',
      conversation_id: 321,
      execution_context: {
        run_kind: 'framework_adapter_external_pilot',
        plan_id: 10,
        plan_item_id: 23
      }
    })
    expect(plannerStore.loadPlans).toHaveBeenCalledWith({ conversationId: 321 })
    expect(wrapper.text()).toContain('最近 LangGraph External Pilot')
    expect(wrapper.text()).toContain('状态: 已完成')
    expect(wrapper.text()).toContain('输出: 已产生')
    expect(wrapper.text()).toContain('status')
    expect(wrapper.text()).toContain('ok')
    expect(wrapper.text()).toContain('FRAM-EXT-321-20260513000000')
    expect(wrapper.text()).toContain('LangGraph external answer')
    expect(wrapper.text()).toContain('复制快照命令')
    expect(wrapper.text()).toContain('adapter_id: langgraph_draft')

    wrapper.unmount()
  })

  it('renders external pilot failure details when runtime returns a failed result', async () => {
    getProfileMock.mockResolvedValueOnce({
      data: buildProfile({
        adapter_health: buildAdapterHealthContractWithLangGraph({
          status: 'healthy',
          detail: 'LangGraph draft adapter is registered and ready for runtime binding.',
          configuration_status: 'ready',
          package_installed: true,
          runtime_enabled: true,
          required_packages: [],
          missing_packages: [],
          required_env: [],
          missing_env: [],
          execution_block_reason: ''
        })
      })
    })
    runExternalFrameworkAdapterPilotMock.mockResolvedValueOnce({
      data: {
        adapter_id: 'langgraph_draft',
        framework_name: 'LangGraph',
        status: 'failed',
        error: {
          error_type: 'connectivity_error',
          detail: 'connect failed'
        },
        events: [{ type: 'error' }],
        final_output: '',
        snapshot_ref: {
          snapshot_id: 'FRAM-EXT-321-20260513000001',
          generated_at: '2026-05-13T00:00:01Z',
          conversation_id: 321,
          source: 'framework_adapter',
          event_type: 'framework_adapter_external_pilot_completed'
        }
      }
    })

    const wrapper = mountPanel()
    await flushPromises()

    const trigger = wrapper.findAll('button').find(button => button.text().includes('运行 External Pilot'))
    expect(trigger).toBeTruthy()

    await trigger.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('最近 LangGraph External Pilot')
    expect(wrapper.text()).toContain('状态: 失败')
    expect(wrapper.text()).toContain('输出: 无内容')
    expect(wrapper.text()).toContain('错误: 连通性错误 (connectivity_error)')
    expect(wrapper.text()).toContain('错误详情: connect failed')
    expect(wrapper.text()).toContain('FRAM-EXT-321-20260513000001')
    expect(wrapper.text()).toContain('查看时间线')

    wrapper.unmount()
  })

  it('renders configuration failure wording for external pilot results', async () => {
    getProfileMock.mockResolvedValueOnce({
      data: buildProfile({
        adapter_health: buildAdapterHealthContractWithLangGraph({
          status: 'healthy',
          detail: 'LangGraph draft adapter is registered and ready for runtime binding.',
          configuration_status: 'ready',
          package_installed: true,
          runtime_enabled: true,
          required_packages: [],
          missing_packages: [],
          required_env: [],
          missing_env: [],
          execution_block_reason: ''
        })
      })
    })
    runExternalFrameworkAdapterPilotMock.mockResolvedValueOnce({
      data: {
        adapter_id: 'langgraph_draft',
        framework_name: 'LangGraph',
        status: 'failed',
        error: {
          error_type: 'configuration_error',
          detail: 'runtime endpoint must be a valid http/https URL'
        },
        events: [{ type: 'error' }],
        final_output: '',
        snapshot_ref: {
          snapshot_id: 'FRAM-EXT-321-20260513000002',
          generated_at: '2026-05-13T00:00:02Z',
          conversation_id: 321,
          source: 'framework_adapter',
          event_type: 'framework_adapter_external_pilot_completed'
        }
      }
    })

    const wrapper = mountPanel()
    await flushPromises()

    const trigger = wrapper.findAll('button').find(button => button.text().includes('运行 External Pilot'))
    expect(trigger).toBeTruthy()

    await trigger.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('错误: 配置错误 (configuration_error)')
    expect(wrapper.text()).toContain('错误详情: runtime endpoint must be a valid http/https URL')

    wrapper.unmount()
  })

  it('renders phase b mcp runtime component health contract', async () => {
    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).toContain('MCP Runtime 合同')
    expect(wrapper.text()).toContain('phase-b-mcp-runtime-v1')
    expect(wrapper.text()).toContain('healthy')
    expect(wrapper.text()).toContain('capabilities: 2')
    expect(wrapper.text()).toContain('MCP Session Manager')
    expect(wrapper.text()).toContain('MCP Capability Router')
    expect(wrapper.text()).toContain('MCP Audit')

    wrapper.unmount()
  })

  it('renders phase b skill definitions and memory entries', async () => {
    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).toContain('SkillDefinition 合同')
    expect(wrapper.text()).toContain('phase-b-skill-definition-v1')
    expect(wrapper.text()).toContain('Frontend UI Review')
    expect(wrapper.text()).toContain('filesystem.read')
    expect(wrapper.text()).toContain('MemoryEntry 合同')
    expect(wrapper.text()).toContain('phase-b-memory-entry-v1')
    expect(wrapper.text()).toContain('memory:global')
    expect(wrapper.text()).toContain('loaded_layer:global')

    wrapper.unmount()
  })

  it('renders subagent lane recent summary trial contract', async () => {
    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).toContain('Subagent 注册能力面')
    expect(wrapper.text()).toContain('Subagent Lane Recent Summary')
    expect(wrapper.text()).toContain('frontend-child-p10-i23-c1')
    expect(wrapper.text()).toContain('final_output')
    expect(wrapper.text()).toContain('已合并 frontend 子智能体结果到主响应')
    expect(getSubagentLaneRecentSummaryMock).toHaveBeenCalledWith({
      conversation_id: 321,
      plan_id: 10,
      item_id: 23
    })

    wrapper.unmount()
  })

  it('renders phase b command definitions and embedded sdk draft methods', async () => {
    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).toContain('Slash Command 层')
    expect(wrapper.text()).toContain('phase-b-command-runtime-v1')
    expect(wrapper.text()).toContain('CommandDefinition')
    expect(wrapper.text()).toContain('command_handlers.run_doctor')
    expect(wrapper.text()).toContain('governance.runtime_read')
    expect(wrapper.text()).toContain('Embedded SDK')
    expect(wrapper.text()).toContain('phase-b-embedded-sdk-v1')
    expect(wrapper.text()).toContain('create_run')
    expect(wrapper.text()).toContain('resume_run')

    wrapper.unmount()
  })

  it('renders embedded runtime boundaries contract from runtime profile', async () => {
    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).toContain('Embedded Runtime Boundaries')
    expect(wrapper.text()).toContain('phase-ii-embedded-runtime-boundaries-v1')
    expect(wrapper.text()).toContain('relationship_only')
    expect(wrapper.text()).toContain('executor_binding_status')
    expect(wrapper.text()).toContain('blocked')
    expect(wrapper.text()).toContain('keep_relationship_only')
    expect(wrapper.text()).toContain('gate_status')
    expect(wrapper.text()).toContain('route_status')
    expect(wrapper.text()).toContain('Routing Seam')
    expect(wrapper.text()).toContain('binding_status')
    expect(wrapper.text()).toContain('Binding Seam')
    expect(wrapper.text()).toContain('stub_status')
    expect(wrapper.text()).toContain('Executor Stub')
    expect(wrapper.text()).toContain('execution_status')
    expect(wrapper.text()).toContain('Executor Skeleton')
    expect(wrapper.text()).toContain('output_summary')
    expect(wrapper.text()).toContain('artifact_id')
    expect(wrapper.text()).toContain('merge_hint')
    expect(wrapper.text()).toContain('merge_ready')
    expect(wrapper.text()).toContain('section_count')
    expect(wrapper.text()).toContain('merge_status')
    expect(wrapper.text()).toContain('Parent Merge')
    expect(wrapper.text()).toContain('Replay Read Model')
    expect(wrapper.text()).toContain('record_count')
    expect(wrapper.text()).toContain('Artifact Summary')
    expect(wrapper.text()).toContain('latest_artifact_id')
    expect(wrapper.text()).toContain('latest_result_type')
    expect(wrapper.text()).toContain('risk_assessment')
    expect(wrapper.text()).toContain('建议人工复核关键风险点后继续主流程')
    expect(wrapper.text()).toContain('latest_entities')
    expect(wrapper.text()).toContain('交易、风险')
    expect(wrapper.text()).toContain('Latest Processing Semantics')
    expect(wrapper.text()).toContain('focus_points')
    expect(wrapper.text()).toContain('action_items')
    expect(wrapper.text()).toContain('Latest Merge Semantics')
    expect(wrapper.text()).toContain('intent_catalog_version')
    expect(wrapper.text()).toContain('phase-ii-child-intent-catalog-v1')
    expect(wrapper.text()).toContain('supported_intents')
    expect(wrapper.text()).toContain('intent_label')
    expect(wrapper.text()).toContain('risk_review')
    expect(wrapper.text()).toContain('entities_mode')
    expect(wrapper.text()).toContain('append_dedup')
    expect(wrapper.text()).toContain('Parent Merge Sections')
    expect(wrapper.text()).toContain('merged_entities')
    expect(wrapper.text()).toContain('merged_focus')
    expect(wrapper.text()).toContain('merged_actions')
    expect(wrapper.text()).toContain('latest_conclusion')
    expect(wrapper.text()).toContain('child_merge_intent')
    expect(wrapper.text()).toContain('child_merge_entities')
    expect(wrapper.text()).toContain('child_merge_entity_count')
    expect(wrapper.text()).toContain('child_merge_focus_count')
    expect(wrapper.text()).toContain('child_merge_action_count')
    expect(wrapper.text()).toContain('child_merge_primary_entities')
    expect(wrapper.text()).toContain('child_merge_conclusion')
    expect(wrapper.text()).toContain('risk_reviewer 已通过 embedded_sdk_worker_skeleton 执行最小路径')
    expect(getChildExecutorOutputReplayMock).toHaveBeenCalledWith({ parent_run_id: 'run-main-01' })
    expect(getChildExecutorOutputSummaryMock).toHaveBeenCalledWith({ parent_run_id: 'run-main-01' })
    expect(getChildExecutorMergedSemanticsMock).toHaveBeenCalledWith({ parent_run_id: 'run-main-01' })
    expect(wrapper.text()).toContain('_tool_continuations')
    expect(wrapper.text()).toContain('run_workspace_snapshot')
    expect(wrapper.text()).toContain('Workspace Backend')
    expect(wrapper.text()).toContain('sqlalchemy')
    expect(wrapper.text()).toContain('strict_sql')
    expect(wrapper.text()).toContain('operation_fallback_allowed')
    expect(wrapper.text()).toContain('workspace backend 正常')
    expect(wrapper.text()).toContain('probe_run_recovery')
    expect(wrapper.text()).toContain('create_child_run_relationship')
    expect(wrapper.text()).toContain('child_run_recovery_boundary_defined')
    expect(wrapper.text()).toContain('Executor Binding Blockers')
    expect(wrapper.text()).toContain('real_child_executor_dispatch')
    expect(wrapper.text()).toContain('learn-claude-code')
    expect(wrapper.text()).toContain('docs/zh/s11-error-recovery.md')
    expect(wrapper.text()).toContain('参考切面数: 1')
    expect(wrapper.text()).toContain('概念分层参考')
    expect(wrapper.text()).toContain('控制面机制参考')
    expect(wrapper.text()).toContain('用于校正运行时术语、恢复语义和任务分层边界')
    expect(wrapper.text()).toContain('用于参考执行后端、权限同步、重连与 runner lifecycle')
    expect(wrapper.text()).toContain('src/utils/swarm/inProcessRunner.ts')

    wrapper.unmount()
  })

  it('renders phase c runtime contract snapshot guard', async () => {
    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).toContain('Contract Snapshot')
    expect(wrapper.text()).toContain('phase-c-runtime-contract-snapshot-v1')
    expect(wrapper.text()).toContain('missing contracts: 0')
    expect(wrapper.text()).toContain('missing fields: 0')
    expect(wrapper.text()).toContain('abc123runtimecontractfingerprint')
    expect(wrapper.text()).toContain('tool_runtime')
    expect(wrapper.text()).toContain('adapter_health')

    wrapper.unmount()
  })

  it('renders runtime contract gate health from quality gate checks', async () => {
    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).toContain('Contract Gate')
    expect(wrapper.text()).toContain('phase-f-runtime-contract-gate-v1')
    expect(wrapper.text()).toContain('degraded')
    expect(wrapper.text()).toContain('checks: 3')
    expect(wrapper.text()).toContain('failed checks: 1')
    expect(wrapper.text()).toContain('quality-gate-report.json')
    expect(wrapper.text()).toContain('missing payloads: 0')
    expect(wrapper.text()).toContain('approval replay coverage')
    expect(wrapper.text()).toContain('covered')
    expect(wrapper.text()).toContain('approval_replayed')
    expect(wrapper.text()).toContain('embedded_sdk_event_payloads')
    expect(wrapper.text()).toContain('adapter_health_status')
    expect(wrapper.text()).toContain('adapter health degraded')
    expect(wrapper.text()).toContain('embedded_sdk_durable_recovery')
    expect(wrapper.text()).toContain('durable_recovery_chain_incomplete')
    expect(wrapper.text()).toContain('backend: sqlalchemy')
    expect(wrapper.text()).toContain('mode: strict_sql')
    expect(wrapper.text()).toContain('tool: workspace_backend_fallback_active')

    wrapper.unmount()
  })

  it('renders local fake framework adapter pilot health in adapter contracts', async () => {
    getProfileMock.mockResolvedValueOnce({
      data: buildProfile({
        adapter_health: {
          contract_version: 'phase-b-adapter-health-v1',
          overall_status: 'healthy',
          adapter_count: 3,
          unavailable_count: 0,
          adapters: [
            { adapter_id: 'tool_registry', display_name: 'Tool Registry', status: 'healthy' },
            { adapter_id: 'mcp_runtime', display_name: 'MCP Runtime', status: 'healthy' },
            {
              adapter_id: 'local_fake_framework',
              display_name: 'LocalFakeFramework',
              framework_name: 'LocalFakeFramework',
              adapter_type: 'agent_framework',
              status: 'healthy',
              detail: 'Local fake adapter pilot is active.'
            }
          ]
        },
        contract_snapshot: {
          contract_version: 'phase-c-runtime-contract-snapshot-v1',
          overall_status: 'healthy',
          contract_count: 6,
          missing_contract_count: 0,
          missing_field_count: 0,
          fingerprint: 'pilot-contract-fingerprint',
          contracts: [
            {
              contract_name: 'adapter_health',
              version: 'phase-b-adapter-health-v1',
              status: 'healthy',
              field_count: 5,
              stable_fields: ['contract_version', 'adapters'],
              missing_fields: [],
              fingerprint: 'adapter-health-pilot-fingerprint'
            }
          ]
        }
      })
    })

    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).toContain('LocalFakeFramework')
    expect(wrapper.text()).toContain('Local fake adapter pilot is active.')
    expect(wrapper.text()).toContain('pilot-contract-fingerprint')

    wrapper.unmount()
  })

  it('runs local fake framework adapter pilot and renders latest result', async () => {
    getProfileMock.mockResolvedValueOnce({
      data: buildProfile({
        adapter_health: {
          contract_version: 'phase-b-adapter-health-v1',
          overall_status: 'healthy',
          adapter_count: 3,
          unavailable_count: 0,
          adapters: [
            { adapter_id: 'tool_registry', display_name: 'Tool Registry', status: 'healthy' },
            { adapter_id: 'mcp_runtime', display_name: 'MCP Runtime', status: 'healthy' },
            {
              adapter_id: 'local_fake_framework',
              display_name: 'LocalFakeFramework',
              adapter_type: 'agent_framework',
              status: 'healthy',
              detail: 'Local fake adapter pilot is active.'
            }
          ]
        }
      })
    })
    getProfileMock.mockResolvedValue({
      data: buildProfile({
        adapter_health: {
          contract_version: 'phase-b-adapter-health-v1',
          overall_status: 'healthy',
          adapter_count: 3,
          unavailable_count: 0,
          adapters: [
            { adapter_id: 'tool_registry', display_name: 'Tool Registry', status: 'healthy' },
            { adapter_id: 'mcp_runtime', display_name: 'MCP Runtime', status: 'healthy' },
            {
              adapter_id: 'local_fake_framework',
              display_name: 'LocalFakeFramework',
              adapter_type: 'agent_framework',
              status: 'healthy',
              detail: 'Local fake adapter pilot is active.'
            }
          ]
        }
      })
    })

    const wrapper = mountPanel()
    await flushPromises()
    const plannerStore = usePlannerStore()

    const trigger = wrapper.findAll('button').find(button => button.text().includes('运行 Pilot'))
    expect(trigger).toBeTruthy()

    await trigger.trigger('click')
    await flushPromises()

    expect(runFrameworkAdapterPilotMock).toHaveBeenCalledTimes(1)
    expect(runFrameworkAdapterPilotMock.mock.calls[0][0]).toMatchObject({
      adapter_id: 'local_fake_framework',
      conversation_id: 321,
      execution_context: {
        run_kind: 'framework_adapter',
        plan_id: 10,
        plan_item_id: 23
      }
    })
    expect(plannerStore.loadPlans).toHaveBeenCalledWith({ conversationId: 321 })
    expect(wrapper.text()).toContain('最近 LocalFakeFramework Pilot')
    expect(wrapper.text()).toContain('状态: 已完成')
    expect(wrapper.text()).toContain('输出: 已产生')
    expect(wrapper.text()).toContain('ui-pilot-run-1')
    expect(wrapper.text()).toContain('FRAM-FRAMEWORK_A-321-20260511000000')
    expect(wrapper.text()).toContain('Local fake adapter processed: 请生成一份运行时巡检计划摘要')
    expect(wrapper.text()).toContain('/snapshot FRAM-FRAMEWORK_A-321-20260511000000')
    expect(wrapper.text()).toContain('最近治理快照命令')
    expect(wrapper.text()).toContain('adapter_id: local_fake_framework')

    wrapper.unmount()
  })

  it('navigates to governance timeline from the latest pilot result', async () => {
    getProfileMock.mockResolvedValueOnce({
      data: buildProfile({
        adapter_health: {
          contract_version: 'phase-b-adapter-health-v1',
          overall_status: 'healthy',
          adapter_count: 3,
          unavailable_count: 0,
          adapters: [
            { adapter_id: 'tool_registry', display_name: 'Tool Registry', status: 'healthy' },
            { adapter_id: 'mcp_runtime', display_name: 'MCP Runtime', status: 'healthy' },
            {
              adapter_id: 'local_fake_framework',
              display_name: 'LocalFakeFramework',
              adapter_type: 'agent_framework',
              status: 'healthy',
              detail: 'Local fake adapter pilot is active.'
            }
          ]
        }
      })
    })
    getProfileMock.mockResolvedValue({
      data: buildProfile({
        adapter_health: {
          contract_version: 'phase-b-adapter-health-v1',
          overall_status: 'healthy',
          adapter_count: 3,
          unavailable_count: 0,
          adapters: [
            { adapter_id: 'tool_registry', display_name: 'Tool Registry', status: 'healthy' },
            { adapter_id: 'mcp_runtime', display_name: 'MCP Runtime', status: 'healthy' },
            {
              adapter_id: 'local_fake_framework',
              display_name: 'LocalFakeFramework',
              adapter_type: 'agent_framework',
              status: 'healthy',
              detail: 'Local fake adapter pilot is active.'
            }
          ]
        }
      })
    })

    const wrapper = mountPanel()
    await flushPromises()

    const trigger = wrapper.findAll('button').find(button => button.text().includes('运行 Pilot'))
    expect(trigger).toBeTruthy()

    await trigger.trigger('click')
    await flushPromises()

    const timelineButton = wrapper.findAll('button').find(button => button.text().includes('查看时间线'))
    expect(timelineButton).toBeTruthy()

    await timelineButton.trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/settings?tab=advanced&governance_snapshot=FRAM-FRAMEWORK_A-321-20260511000000')

    wrapper.unmount()
  })

  it('renders phase b placeholders when capability layer contracts are missing', async () => {
    getProfileMock.mockResolvedValueOnce({
      data: buildProfile({
        tool_runtime: undefined,
        mcp_runtime: undefined,
        skill_contract: undefined,
        memory_contract: undefined,
        adapter_health: undefined,
        contract_snapshot: undefined
      })
    })

    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).toContain('等待后端接入 tool_runtime contract')
    expect(wrapper.text()).toContain('等待后端接入 mcp_runtime contract')
    expect(wrapper.text()).toContain('等待后端接入 skill_contract')
    expect(wrapper.text()).toContain('等待后端接入 memory_contract')
    expect(wrapper.text()).toContain('等待后端接入 adapter_health contract')
    expect(wrapper.text()).toContain('等待后端接入 contract_snapshot')

    wrapper.unmount()
  })

  it('renders recent governance snapshot commands from local storage', async () => {
    localStorage.setItem('governance_recent_snapshot_commands', JSON.stringify([
      {
        commandText: '/mcp snapshot MCP-REF-1',
        commandName: 'mcp',
        action: 'open_mcp',
        params: ['snapshot', 'MCP-REF-1'],
        domain: 'mcp',
        snapshotId: 'MCP-REF-1',
        eventLabel: 'MCP Probe 完成',
        summary: 'status=ok',
        copiedAt: '2026-05-03T10:00:00Z'
      }
    ]))

    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).toContain('最近治理快照命令')
    expect(wrapper.text()).toContain('/mcp snapshot MCP-REF-1')
    expect(wrapper.text()).toContain('快照: MCP-REF-1')
    expect(wrapper.text()).toContain('事件: MCP Probe 完成')
    expect(wrapper.text()).toContain('status=ok')

    wrapper.unmount()
  })

  it('copies a recent governance snapshot command', async () => {
    localStorage.setItem('governance_recent_snapshot_commands', JSON.stringify([
      {
        commandText: '/snapshot MCP-REF-1',
        commandName: 'snapshot',
        action: 'open_snapshot',
        params: ['MCP-REF-1'],
        domain: '',
        snapshotId: 'MCP-REF-1',
        eventLabel: 'MCP Probe 完成',
        summary: 'status=ok',
        copiedAt: '2026-05-03T10:00:00Z'
      }
    ]))

    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText }
    })

    const wrapper = mountPanel()
    await flushPromises()

    const copyTrigger = wrapper.findAll('button').find(button => button.text().includes('复制命令'))
    expect(copyTrigger).toBeTruthy()

    await copyTrigger.trigger('click')
    await flushPromises()

    expect(writeText).toHaveBeenCalledWith('/snapshot MCP-REF-1')
    expect(wrapper.text()).toContain('最近复制：')
    expect(wrapper.text()).toContain('MCP Probe 完成')
    expect(wrapper.text()).toContain('status=ok')

    wrapper.unmount()
  })
})
