import { normalizePayload, normalizeText } from './governanceValueUtils'

export function stringifyPayloadValue(value) {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value)
  }
  if (Array.isArray(value)) {
    return value.join(', ')
  }
  try {
    return JSON.stringify(value)
  } catch (_err) {
    return String(value)
  }
}

export function normalizeSeverity(eventType) {
  if (eventType === 'doctor_gate_failed') return 'warning'
  if (String(eventType || '').includes('failed') || String(eventType || '').includes('blocked')) return 'warning'
  if (String(eventType || '').includes('denied')) return 'warning'
  if (
    String(eventType || '').includes('approved') ||
    String(eventType || '').includes('completed') ||
    String(eventType || '').includes('updated') ||
    String(eventType || '').includes('enabled')
  ) return 'success'
  return 'info'
}

export function formatAuditEvent(eventType) {
  const labelMap = {
    doctor_run_started: 'Doctor 启动',
    doctor_run_completed: 'Doctor 完成',
    doctor_gate_failed: 'Doctor 门禁失败',
    scheduler_fanout_prepared: '调度拆分',
    scheduler_execution_started: '调度启动',
    scheduler_merged: '结果合并',
    scheduler_cancelled: '调度取消',
    child_running: '子执行启动',
    child_completed: '子执行完成',
    child_failed: '子执行失败',
    child_retrying: '子执行重试',
    child_cancelled: '子执行取消',
    permission_approved: '权限批准',
    permission_denied: '权限拒绝',
    tool_permission_required: '等待工具授权',
    remediation_status_updated: '整改状态更新',
    mcp_server_created: 'MCP 服务创建',
    mcp_server_updated: 'MCP 服务更新',
    mcp_server_deleted: 'MCP 服务删除',
    mcp_server_enabled: 'MCP 服务启用',
    mcp_server_disabled: 'MCP 服务停用',
    mcp_server_probed: 'MCP Probe 完成',
    mcp_server_handshake_completed: 'MCP Handshake 完成',
    mcp_tool_call_completed: 'MCP 工具调用完成',
    pre_tool_use_blocked: 'Hook 阻断',
    agent_state_changed: '运行时状态迁移',
    learning_version_applied: 'Learning 版本应用',
    framework_adapter_status: 'Framework Adapter 状态',
    framework_adapter_reasoning: 'Framework Adapter 推理',
    framework_adapter_output: 'Framework Adapter 输出',
    framework_adapter_run_completed: 'Framework Adapter 完成',
    framework_adapter_precheck_completed: 'Framework Adapter 预检完成',
    framework_adapter_external_pilot_completed: 'Framework Adapter 外部执行完成',
    framework_adapter_external_error: 'Framework Adapter 外部执行失败',
    framework_adapter_external_failure_diagnostic: 'Framework Adapter 外部执行失败诊断',
    embedded_runtime_bootstrap_updated: 'Embedded Runtime Bootstrap 更新',
  }
  return labelMap[eventType] || eventType || '未知事件'
}

export function inferTimelineDomain(eventType, source, payload = null) {
  const payloadData = normalizePayload(payload)
  if (normalizeText(source) === 'query_control' && normalizeText(payloadData?.channel) === 'main_chat') {
    return 'main_chat'
  }
  const sourceText = normalizeText(source)
  if (sourceText) {
    if (['doctor', 'permission', 'mcp', 'governance', 'scheduler', 'hook', 'runtime', 'framework_adapter'].includes(sourceText)) {
      return sourceText
    }
    if (sourceText === 'runtime_control') {
      return 'runtime'
    }
  }
  const eventText = normalizeText(eventType)
  if (eventText.startsWith('doctor_')) return 'doctor'
  if (eventText.startsWith('permission_') || eventText === 'tool_permission_required') return 'permission'
  if (eventText.startsWith('mcp_')) return 'mcp'
  if (eventText.startsWith('learning_')) return 'learning'
  if (eventText.startsWith('scheduler_') || eventText.startsWith('child_')) return 'scheduler'
  if (eventText.startsWith('remediation_')) return 'governance'
  if (eventText.includes('hook') || eventText === 'pre_tool_use_blocked') return 'hook'
  if (sourceText === 'runtime_contract' || eventText.startsWith('runtime_contract_')) return 'runtime_contract'
  if (eventText.startsWith('agent_state_') || eventText.startsWith('runtime_')) return 'runtime'
  if (eventText.startsWith('framework_adapter_')) return 'framework_adapter'
  return 'other'
}

export function formatTimelineDomain(domain) {
  const labelMap = {
    doctor: 'Doctor',
    permission: 'Permission',
    mcp: 'MCP',
    governance: 'Governance',
    scheduler: 'Scheduler',
    hook: 'Hook',
    runtime_contract: 'Runtime Contract',
    runtime: 'Runtime',
    main_chat: 'Main Chat',
    learning: 'Learning',
    framework_adapter: 'Framework Adapter',
    other: 'Other',
  }
  return labelMap[domain] || domain || 'Other'
}

export function formatPayloadSummary(payload) {
  const data = normalizePayload(payload)
  if (!data) return ''
  const embeddedRuntimeBootstrapSummary = formatEmbeddedRuntimeBootstrapSummary(data)
  if (embeddedRuntimeBootstrapSummary) return embeddedRuntimeBootstrapSummary
  const runtimeContractSummary = formatRuntimeContractGateSummary(data)
  if (runtimeContractSummary) return runtimeContractSummary
  const priorityKeys = [
    'action_id',
    'status',
    'server_name',
    'tool_name',
    'request_id',
    'scope',
    'exit_code',
    'gate_passed',
    'requested_embedded_workspace_store_mode',
    'current_runtime_mode',
    'current_recovery_posture',
    'bootstrap_recovery_validation_status',
  ]
  const fragments = []
  for (const key of priorityKeys) {
    if (data[key] === undefined || data[key] === null || data[key] === '') {
      continue
    }
    fragments.push(`${key}=${stringifyPayloadValue(data[key])}`)
  }
  return fragments.slice(0, 4).join(' | ')
}

export function formatRuntimeContractGateSummary(payload) {
  const data = normalizePayload(payload)
  if (!data) return ''
  const summary = normalizePayload(data.runtime_contract_summary)
  if (!summary) return ''
  const coverage = normalizePayload(summary.approval_replay_coverage)
  const approvalLifecycleCoverage = normalizePayload(summary.approval_lifecycle_recovery_coverage)
  const approvedToolCoverage = normalizePayload(summary.approved_tool_execution_coverage)
  const sdkToolCoverage = normalizePayload(summary.sdk_tool_runtime_execution_coverage)
  const embeddedPersistenceCoverage = normalizePayload(summary.embedded_sdk_persistence_coverage)
  const workerOwnershipCoverage = normalizePayload(summary.worker_ownership_store_mode_coverage)
  const childExecutorGateCoverage = normalizePayload(summary.child_executor_promotion_gate_coverage)
  const childExecutorPrerequisitesCoverage = normalizePayload(summary.child_executor_execution_prerequisites_coverage)
  const childExecutorDispatchCoverage = normalizePayload(summary.child_executor_dispatch_coverage)
  const childExecutorDispatcherCoverage = normalizePayload(summary.child_executor_dispatcher_coverage)
  const subagentDetailCoverage = normalizePayload(summary.subagent_lane_query_detail_coverage)
  const recoveryRetryCoverage = normalizePayload(summary.recovery_retry_evidence_coverage)
  const recoveryRetrySchedulerCoverage = normalizePayload(summary.recovery_retry_scheduler_coverage)
  const durableLoaderCoverage = normalizePayload(summary.durable_recovery_loader_coverage)
  const checkpointCursorCoverage = normalizePayload(summary.checkpoint_resume_cursor_coverage)
  const status = normalizeText(summary.overall_status || data.overall_status)
  const failedCount = Number(summary.failed_check_count ?? data.failed_check_count ?? 0)
  const missingPayloadCount = Number(summary.missing_payload_count ?? 0)
  const replayCovered = Boolean(coverage?.event_payload_sample)
  const replayLabel = status === 'unknown' ? 'unknown' : replayCovered ? 'covered' : 'missing'
  const approvalLifecycleCovered = Boolean(approvalLifecycleCoverage?.alignment_smoke)
  const approvalLifecycleLabel = status === 'unknown' ? 'unknown' : approvalLifecycleCovered ? 'covered' : 'missing'
  const approvedToolCovered = Boolean(approvedToolCoverage?.bridge_smoke)
  const approvedToolLabel = status === 'unknown' ? 'unknown' : approvedToolCovered ? 'covered' : 'missing'
  const sdkToolCovered = Boolean(sdkToolCoverage?.bridge_smoke)
  const sdkToolLabel = status === 'unknown' ? 'unknown' : sdkToolCovered ? 'covered' : 'missing'
  const embeddedPersistenceCovered = Boolean(embeddedPersistenceCoverage?.persistence_smoke)
  const embeddedPersistenceLabel = status === 'unknown' ? 'unknown' : embeddedPersistenceCovered ? 'covered' : 'missing'
  const workerOwnershipCovered = Boolean(workerOwnershipCoverage?.mode_smoke)
  const workerOwnershipLabel = status === 'unknown' ? 'unknown' : workerOwnershipCovered ? 'covered' : 'missing'
  const childExecutorGateCovered = Boolean(childExecutorGateCoverage?.gate_smoke)
  const childExecutorGateLabel = status === 'unknown' ? 'unknown' : childExecutorGateCovered ? 'covered' : 'missing'
  const childExecutorPrerequisitesCovered = Boolean(childExecutorPrerequisitesCoverage?.prerequisites_smoke)
  const childExecutorPrerequisitesLabel = status === 'unknown' ? 'unknown' : childExecutorPrerequisitesCovered ? 'covered' : 'missing'
  const childExecutorDispatchCovered = Boolean(childExecutorDispatchCoverage?.dispatch_smoke)
  const childExecutorDispatchLabel = status === 'unknown' ? 'unknown' : childExecutorDispatchCovered ? 'covered' : 'missing'
  const childExecutorDispatcherCovered = Boolean(childExecutorDispatcherCoverage?.dispatcher_smoke)
  const childExecutorDispatcherLabel = status === 'unknown' ? 'unknown' : childExecutorDispatcherCovered ? 'covered' : 'missing'
  const subagentDetailCovered = Boolean(subagentDetailCoverage?.detail_smoke)
  const subagentDetailLabel = status === 'unknown' ? 'unknown' : subagentDetailCovered ? 'covered' : 'missing'
  const recoveryRetryCovered = Boolean(recoveryRetryCoverage?.retry_smoke)
  const recoveryRetryLabel = status === 'unknown' ? 'unknown' : recoveryRetryCovered ? 'covered' : 'missing'
  const recoveryRetrySchedulerCovered = Boolean(recoveryRetrySchedulerCoverage?.scheduler_smoke)
  const recoveryRetrySchedulerLabel = status === 'unknown' ? 'unknown' : recoveryRetrySchedulerCovered ? 'covered' : 'missing'
  const durableLoaderCovered = Boolean(durableLoaderCoverage?.loader_smoke)
  const durableLoaderLabel = status === 'unknown' ? 'unknown' : durableLoaderCovered ? 'covered' : 'missing'
  const checkpointCursorCovered = Boolean(checkpointCursorCoverage?.cursor_smoke)
  const checkpointCursorLabel = status === 'unknown' ? 'unknown' : checkpointCursorCovered ? 'covered' : 'missing'
  const fragments = []
  if (status) fragments.push(`runtime_contract=${status}`)
  fragments.push(`failed=${Number.isFinite(failedCount) ? failedCount : 0}`)
  fragments.push(`missing_payloads=${Number.isFinite(missingPayloadCount) ? missingPayloadCount : 0}`)
  fragments.push(`approval_replay=${replayLabel}`)
  fragments.push(`approval_lifecycle=${approvalLifecycleLabel}`)
  fragments.push(`approved_tool=${approvedToolLabel}`)
  fragments.push(`sdk_tool=${sdkToolLabel}`)
  fragments.push(`embedded_persistence=${embeddedPersistenceLabel}`)
  fragments.push(`worker_ownership=${workerOwnershipLabel}`)
  fragments.push(`child_executor_gate=${childExecutorGateLabel}`)
  fragments.push(`child_executor_prerequisites=${childExecutorPrerequisitesLabel}`)
  fragments.push(`child_executor_dispatch=${childExecutorDispatchLabel}`)
  fragments.push(`child_executor_dispatcher=${childExecutorDispatcherLabel}`)
  fragments.push(`subagent_detail=${subagentDetailLabel}`)
  fragments.push(`recovery_retry=${recoveryRetryLabel}`)
  fragments.push(`recovery_retry_scheduler=${recoveryRetrySchedulerLabel}`)
  fragments.push(`durable_loader=${durableLoaderLabel}`)
  fragments.push(`checkpoint_cursor=${checkpointCursorLabel}`)
  return fragments.join(' · ')
}

export function formatTraceSource(source) {
  const labelMap = {
    doctor: 'Doctor',
    scheduler: 'Scheduler',
    subagent: 'Subagent',
    permission: 'Permission',
    hook: 'Hook',
    tool: 'Tool',
    mcp: 'MCP',
    runtime: 'Runtime',
    runtime_control: 'Runtime Control',
    policy: 'Policy',
    skill: 'Skill',
    agent: 'Agent',
    framework_adapter: 'Framework Adapter',
  }
  return labelMap[source] || source || ''
}

export function formatEmbeddedRuntimeBootstrapSummary(payload) {
  const data = normalizePayload(payload)
  if (!data) return ''
  const requestedMode = String(data.requested_embedded_workspace_store_mode || '').trim()
  const runtimeMode = String(data.current_runtime_mode || '').trim()
  const recoveryPosture = String(data.current_recovery_posture || '').trim()
  const backendMode = String(data.current_workspace_backend_mode || '').trim()
  const validationStatus = String(data.bootstrap_recovery_validation_status || '').trim()
  if (!requestedMode && !runtimeMode && !recoveryPosture && !backendMode && !validationStatus) {
    return ''
  }
  const fragments = []
  if (requestedMode) fragments.push(`workspace_mode=${requestedMode}`)
  if (runtimeMode) fragments.push(`runtime=${runtimeMode}`)
  if (recoveryPosture) fragments.push(`recovery=${recoveryPosture}`)
  if (backendMode) fragments.push(`backend=${backendMode}`)
  if (validationStatus) fragments.push(`validation=${validationStatus}`)
  return fragments.join(' · ')
}
