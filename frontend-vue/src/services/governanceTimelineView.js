import {
  normalizePayload,
  normalizeSnapshotRef,
  normalizeText,
  toTimestamp,
} from './governanceValueUtils'

export function buildCombinedTimeline(focusItem, options = {}) {
  const {
    inferTimelineDomain = () => 'other',
    formatTimelineDomain = value => value,
    normalizeSeverity = () => 'info',
    formatAuditEvent = value => value,
    formatPayloadSummary = () => '',
    formatTraceSource = value => value,
    formatFrameworkAdapterExternalErrorTag = () => '',
    formatFrameworkAdapterExternalErrorDetail = () => '',
    normalizeText: normalizeTextFn = normalizeText,
  } = options
  if (!focusItem) {
    return []
  }

  const auditEntries = (focusItem.audit_trail || []).map((entry, index) => ({
    payload: normalizePayload(entry.payload),
    key: `audit-${entry.timestamp || 'na'}-${entry.event_type || 'unknown'}-${index}`,
    timestamp: entry.timestamp,
    kind: 'audit',
    kindLabel: 'Audit',
    domain: inferTimelineDomain(entry.event_type, '', normalizePayload(entry.payload)),
    domainLabel: formatTimelineDomain(inferTimelineDomain(entry.event_type, '', normalizePayload(entry.payload))),
    sourceLabel: '',
    severity: normalizeSeverity(entry.event_type),
    title: formatAuditEvent(entry.event_type),
    content: entry.content || '无说明',
    detail: '',
    payloadSummary: formatPayloadSummary(entry.payload),
  }))

  const traceEntries = (focusItem.run_trace || []).map((entry, index) => {
    const payload = normalizePayload(entry.payload)
    const isFrameworkAdapterExternalError = normalizeTextFn(entry.event_type) === 'framework_adapter_external_error'
    const domain = inferTimelineDomain(entry.event_type, entry.source, payload)
    return {
      key: `trace-${entry.timestamp || 'na'}-${entry.source || 'runtime'}-${entry.event_type || 'unknown'}-${index}`,
      timestamp: entry.timestamp,
      kind: 'trace',
      kindLabel: 'Trace',
      domain,
      domainLabel: formatTimelineDomain(domain),
      sourceLabel: formatTraceSource(entry.source),
      severity: entry.severity || 'info',
      title: formatAuditEvent(entry.event_type),
      content: isFrameworkAdapterExternalError
        ? formatFrameworkAdapterExternalErrorTag(payload) || entry.summary || '无摘要'
        : (entry.summary || '无摘要'),
      detail: isFrameworkAdapterExternalError
        ? formatFrameworkAdapterExternalErrorDetail(payload) || entry.detail || ''
        : (entry.detail || ''),
      payload,
      payloadSummary: formatPayloadSummary(payload),
    }
  })

  const syntheticDiagnosticEntries = (focusItem.run_trace || []).flatMap((entry, index) => {
    const payload = normalizePayload(entry.payload)
    const failure = normalizePayload(payload?.framework_adapters?.latest_external_pilot_failure)
    const failureCounts = normalizePayload(payload?.framework_adapters?.external_pilot_failure_counts)
    const snapshotRef = normalizeSnapshotRef(failure?.snapshot_ref)
    if (!failure || !snapshotRef) {
      return []
    }
    const syntheticPayload = {
      ...failure,
      snapshot_ref: snapshotRef,
      external_pilot_failure_counts: failureCounts,
    }
    return [{
      key: `trace-framework-adapter-external-failure-diagnostic-${entry.timestamp || 'na'}-${index}`,
      timestamp: entry.timestamp || snapshotRef.generated_at || '',
      kind: 'trace',
      kindLabel: 'Trace',
      domain: 'framework_adapter',
      domainLabel: formatTimelineDomain('framework_adapter'),
      sourceLabel: 'Doctor',
      severity: 'warning',
      title: formatAuditEvent('framework_adapter_external_failure_diagnostic'),
      content: formatFrameworkAdapterExternalErrorTag(failure) || '无摘要',
      detail: formatFrameworkAdapterExternalErrorDetail(failure) || '',
      payload: syntheticPayload,
      payloadSummary: formatPayloadSummary(syntheticPayload),
    }]
  })

  return [...traceEntries, ...syntheticDiagnosticEntries, ...auditEntries]
    .sort((left, right) => toTimestamp(right.timestamp) - toTimestamp(left.timestamp))
    .slice(0, 20)
}

export function buildSeverityFilters(timeline) {
  const items = Array.isArray(timeline) ? timeline : []
  const warningCount = items.filter(entry => entry?.severity === 'warning').length
  return [
    { key: 'all', label: '全部事件', count: items.length },
    { key: 'warning', label: '仅告警', count: warningCount },
  ]
}

export function scopeTimelineBySeverity(timeline, activeSeverity) {
  const items = Array.isArray(timeline) ? timeline : []
  if (activeSeverity === 'warning') {
    return items.filter(entry => entry?.severity === 'warning')
  }
  return items
}

export function buildTimelineFilters(scopedTimeline, formatTimelineDomain) {
  const counters = new Map()
  for (const entry of Array.isArray(scopedTimeline) ? scopedTimeline : []) {
    const key = normalizeText(entry?.domain) || 'other'
    counters.set(key, Number(counters.get(key) || 0) + 1)
  }
  const orderedKeys = ['all', 'doctor', 'permission', 'mcp', 'governance', 'scheduler', 'hook', 'runtime_contract', 'runtime', 'main_chat', 'learning', 'framework_adapter', 'other']
  return orderedKeys
    .filter(key => key === 'all' || counters.has(key))
    .map(key => ({
      key,
      label: key === 'all' ? '全部' : formatTimelineDomain(key),
      count: key === 'all' ? (Array.isArray(scopedTimeline) ? scopedTimeline.length : 0) : Number(counters.get(key) || 0),
    }))
}

export function buildDedupeCandidateTimeline(scopedTimeline, options = {}) {
  const {
    activeFilter = 'all',
    activeQueryId = '',
    activeQueryStage = '',
    activeFrameworkAdapterErrorType = '',
    getTimelineQueryId = () => '',
    getFrameworkAdapterExternalErrorType = () => '',
  } = options
  const domainScoped = activeFilter === 'all'
    ? (Array.isArray(scopedTimeline) ? scopedTimeline : [])
    : (Array.isArray(scopedTimeline) ? scopedTimeline : []).filter(entry => entry?.domain === activeFilter)
  const queryScoped = activeQueryId
    ? domainScoped.filter(entry => getTimelineQueryId(entry) === activeQueryId)
    : domainScoped
  const stageScoped = activeQueryStage
    ? queryScoped.filter(entry => normalizeText(entry?.payload?.stage) === activeQueryStage)
    : queryScoped
  return (activeFilter === 'framework_adapter' && activeFrameworkAdapterErrorType)
    ? stageScoped.filter(entry => getFrameworkAdapterExternalErrorType(entry) === activeFrameworkAdapterErrorType)
    : stageScoped
}

export function filterTimelineEntries(scopedTimeline, options = {}) {
  const {
    activeDedupeKey = '',
    activeSnapshotId = '',
    getTimelineDedupeKey = () => '',
    entrySnapshotRef = () => null,
  } = options
  const dedupeCandidateTimeline = buildDedupeCandidateTimeline(scopedTimeline, options)
  const dedupeScoped = activeDedupeKey
    ? dedupeCandidateTimeline.filter(entry => getTimelineDedupeKey(entry) === activeDedupeKey)
    : dedupeCandidateTimeline
  if (!activeSnapshotId) {
    return dedupeScoped
  }
  const snapshotMatched = dedupeScoped.filter(entry => entrySnapshotRef(entry)?.snapshot_id === activeSnapshotId)
  return snapshotMatched.length ? snapshotMatched : dedupeScoped
}

export function buildCurrentSnapshotRef(filteredTimeline, scopedTimeline, combinedTimeline, entrySnapshotRef) {
  const candidates = [
    ...(Array.isArray(filteredTimeline) ? filteredTimeline : []),
    ...(Array.isArray(scopedTimeline) ? scopedTimeline : []),
    ...(Array.isArray(combinedTimeline) ? combinedTimeline : []),
  ]
  for (const entry of candidates) {
    const snapshotRef = entrySnapshotRef(entry)
    if (snapshotRef) {
      return snapshotRef
    }
  }
  return null
}

export function buildActiveSnapshotNotice(activeSnapshotId, combinedTimeline, entrySnapshotRef) {
  if (!activeSnapshotId) {
    return '当前展示的是常规治理视图'
  }
  const matched = (Array.isArray(combinedTimeline) ? combinedTimeline : [])
    .find(entry => entrySnapshotRef(entry)?.snapshot_id === activeSnapshotId)
  if (!matched) {
    return '当前会话未找到对应快照，已回退到常规治理视图'
  }
  return `已聚焦到 ${matched.title}`
}

export function buildGovernanceOverviewCards(combinedTimeline, timelineFilters, options = {}) {
  const { formatTimelineDomain = value => value, toTimestamp: toTimestampFn = toTimestamp, getSeverityRank = () => 0 } = options
  const order = ['doctor', 'permission', 'mcp', 'governance', 'scheduler', 'hook', 'runtime', 'main_chat', 'learning', 'framework_adapter']
  const countMap = new Map((Array.isArray(timelineFilters) ? timelineFilters : []).map(item => [item.key, item.count]))
  const latestByDomain = new Map()
  const warningCountByDomain = new Map()
  for (const entry of Array.isArray(combinedTimeline) ? combinedTimeline : []) {
    if (!latestByDomain.has(entry?.domain)) {
      latestByDomain.set(entry.domain, entry)
    }
    if (entry?.severity === 'warning') {
      warningCountByDomain.set(entry.domain, Number(warningCountByDomain.get(entry.domain) || 0) + 1)
    }
  }
  return order
    .filter(key => Number(countMap.get(key) || 0) > 0)
    .map(key => ({
      key,
      label: formatTimelineDomain(key),
      count: Number(countMap.get(key) || 0),
      warningCount: Number(warningCountByDomain.get(key) || 0),
      severity: latestByDomain.get(key)?.severity || 'info',
      latestTitle: latestByDomain.get(key)?.title || '',
      latestTimestamp: latestByDomain.get(key)?.timestamp || '',
      sortIndex: order.indexOf(key),
    }))
    .sort((left, right) => {
      const timestampDelta = toTimestampFn(right.latestTimestamp) - toTimestampFn(left.latestTimestamp)
      if (timestampDelta !== 0) {
        return timestampDelta
      }
      const severityDelta = getSeverityRank(right.severity) - getSeverityRank(left.severity)
      if (severityDelta !== 0) {
        return severityDelta
      }
      return left.sortIndex - right.sortIndex
    })
}

export function buildRecommendedFocusFilter(lastDoctorOutcome, doctorGateFailedTitle, governanceOverviewCards) {
  if (!lastDoctorOutcome || lastDoctorOutcome.title !== doctorGateFailedTitle) {
    return 'all'
  }
  const highestRiskDomain = (Array.isArray(governanceOverviewCards) ? governanceOverviewCards : [])
    .find(card => card.key !== 'doctor' && card.severity === 'warning')
  if (highestRiskDomain) {
    return highestRiskDomain.key
  }
  return 'doctor'
}

export function buildRecommendedFocusSignature(focusItem, recommendedFocusFilter, lastDoctorOutcome) {
  if (!focusItem || recommendedFocusFilter === 'all') {
    return ''
  }
  return [
    focusItem.id || 'na',
    lastDoctorOutcome?.timestamp || 'na',
    recommendedFocusFilter,
  ].join(':')
}

export function buildAutoFocusNotice(options = {}) {
  const {
    recommendedFocusSignature = '',
    routeGovernanceFilter = '',
    lastAutoFocusSignature = '',
    activeFilter = 'all',
    recommendedFocusFilter = 'all',
    governanceOverviewCards = [],
  } = options
  if (!recommendedFocusSignature || routeGovernanceFilter) {
    return ''
  }
  if (lastAutoFocusSignature !== recommendedFocusSignature) {
    return ''
  }
  if (activeFilter !== recommendedFocusFilter) {
    return ''
  }
  const matchedCard = (Array.isArray(governanceOverviewCards) ? governanceOverviewCards : [])
    .find(card => card.key === recommendedFocusFilter)
  if (!matchedCard) {
    return ''
  }
  if (recommendedFocusFilter === 'doctor') {
    return '因 Doctor 门禁失败，当前默认聚焦到 Doctor 域。'
  }
  return `因 Doctor 门禁失败，当前默认聚焦到 ${matchedCard.label} 风险域，共 ${matchedCard.warningCount} 条告警。`
}

export function buildGovernanceTimelineOutcomes(combinedTimeline, options = {}) {
  const {
    formatAuditEvent = value => value,
    normalizeText: normalizeTextFn = normalizeText,
    formatFrameworkAdapterDisplayName = (_frameworkName, adapterId) => adapterId,
    buildFrameworkAdapterRemediationStatusTags = () => [],
    formatFrameworkAdapterRemediationContent = () => '',
    buildFrameworkAdapterRemediationCommand = () => '',
  } = options
  const timeline = Array.isArray(combinedTimeline) ? combinedTimeline : []
  const findOutcome = predicate => timeline.find(predicate) || null

  const lastDoctorOutcome = findOutcome(item =>
    item.domain === 'doctor' && item.kind === 'trace' && (
      item.title === formatAuditEvent('doctor_gate_failed') ||
      item.title === formatAuditEvent('doctor_run_completed')
    )
  )
  const lastPermissionOutcome = findOutcome(item =>
    item.domain === 'permission' && (
      item.title === formatAuditEvent('permission_approved') ||
      item.title === formatAuditEvent('permission_denied') ||
      item.title === formatAuditEvent('tool_permission_required')
    )
  )
  const lastMcpOutcome = findOutcome(item =>
    item.domain === 'mcp' && (
      item.title === formatAuditEvent('mcp_tool_call_completed') ||
      item.title === formatAuditEvent('mcp_server_handshake_completed') ||
      item.title === formatAuditEvent('mcp_server_probed') ||
      item.title === formatAuditEvent('mcp_server_created') ||
      item.title === formatAuditEvent('mcp_server_updated')
    )
  )
  const lastGovernanceOutcome = findOutcome(item =>
    item.domain === 'governance' && item.title === formatAuditEvent('remediation_status_updated')
  )
  const lastSchedulerOutcome = findOutcome(item =>
    item.domain === 'scheduler' && (
      item.title === formatAuditEvent('scheduler_merged') ||
      item.title === formatAuditEvent('scheduler_execution_started') ||
      item.title === formatAuditEvent('child_completed') ||
      item.title === formatAuditEvent('child_failed')
    )
  )
  const lastHookOutcome = findOutcome(item =>
    item.domain === 'hook' && (
      item.title === formatAuditEvent('pre_tool_use_blocked') ||
      String(item.title || '').includes('Hook')
    )
  )
  const lastLearningOutcome = findOutcome(item =>
    item.domain === 'learning' && (
      item.title === formatAuditEvent('learning_version_applied') ||
      String(item.title || '').includes('Learning')
    )
  )
  const lastRuntimeOutcome = findOutcome(item =>
    item.domain === 'runtime' && (
      item.title === formatAuditEvent('embedded_runtime_bootstrap_updated') ||
      item.title === formatAuditEvent('agent_state_changed') ||
      String(item.title || '').includes('运行时')
    )
  )
  const lastFrameworkAdapterPilotOutcome = findOutcome(item =>
    item.domain === 'framework_adapter' && (
      item.title === formatAuditEvent('framework_adapter_output') ||
      item.title === formatAuditEvent('framework_adapter_run_completed') ||
      item.title === formatAuditEvent('framework_adapter_status') ||
      item.title === formatAuditEvent('framework_adapter_reasoning')
    )
  )
  const lastFrameworkAdapterPrecheckOutcome = findOutcome(item =>
    item.domain === 'framework_adapter' && item.title === formatAuditEvent('framework_adapter_precheck_completed')
  )
  const lastFrameworkAdapterExternalPilotOutcome = findOutcome(item =>
    item.domain === 'framework_adapter' && (
      item.title === formatAuditEvent('framework_adapter_external_pilot_completed') ||
      item.title === formatAuditEvent('framework_adapter_external_error')
    )
  )
  const lastFrameworkAdapterExternalFailureDiagnostic = findOutcome(item =>
    item.domain === 'framework_adapter' && item.title === formatAuditEvent('framework_adapter_external_failure_diagnostic')
  )

  const remediationEntry = findOutcome(item =>
    item.domain === 'doctor' &&
    item.title === formatAuditEvent('doctor_run_completed') &&
    Array.isArray(item?.payload?.framework_adapters?.remediation_actions) &&
    item.payload.framework_adapters.remediation_actions.length > 0
  )
  let lastFrameworkAdapterRemediation = null
  if (remediationEntry) {
    const remediationActions = Array.isArray(remediationEntry?.payload?.framework_adapters?.remediation_actions)
      ? remediationEntry.payload.framework_adapters.remediation_actions
      : []
    const primaryAdapterId = remediationActions
      .map(item => normalizeTextFn(item?.adapter_id))
      .find(Boolean)
    const displayName = formatFrameworkAdapterDisplayName('', primaryAdapterId)
    const statusTags = buildFrameworkAdapterRemediationStatusTags(remediationActions)
    lastFrameworkAdapterRemediation = {
      title: formatAuditEvent('doctor_run_completed'),
      content: formatFrameworkAdapterRemediationContent(displayName, remediationActions.length, statusTags),
      severity: remediationEntry.severity || 'info',
      timestamp: remediationEntry.timestamp,
      adapterId: primaryAdapterId,
      displayName,
      statusTags,
      remediationActions,
      commandText: buildFrameworkAdapterRemediationCommand(remediationActions),
    }
  }

  return {
    lastDoctorOutcome,
    lastPermissionOutcome,
    lastMcpOutcome,
    lastGovernanceOutcome,
    lastSchedulerOutcome,
    lastHookOutcome,
    lastLearningOutcome,
    lastRuntimeOutcome,
    lastFrameworkAdapterPilotOutcome,
    lastFrameworkAdapterPrecheckOutcome,
    lastFrameworkAdapterExternalPilotOutcome,
    lastFrameworkAdapterExternalFailureDiagnostic,
    lastFrameworkAdapterRemediation,
  }
}
