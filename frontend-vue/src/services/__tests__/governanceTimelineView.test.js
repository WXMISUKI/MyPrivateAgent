import { describe, expect, it } from 'vitest'

import {
  buildActiveSnapshotNotice,
  buildCombinedTimeline,
  buildCurrentSnapshotRef,
  buildGovernanceTimelineOutcomes,
  buildGovernanceOverviewCards,
  buildRecommendedFocusFilter,
  buildRecommendedFocusSignature,
  buildSeverityFilters,
  buildTimelineFilters,
  buildAutoFocusNotice,
  filterTimelineEntries,
  scopeTimelineBySeverity,
} from '../governanceTimelineView'

describe('governanceTimelineView', () => {
  const timeline = [
    {
      key: 'doctor-warning',
      domain: 'doctor',
      severity: 'warning',
      title: 'Doctor 门禁失败',
      timestamp: '2026-05-01T12:00:05Z',
      payload: {
        stage: 'planning',
        query_id: 'manual-chat-1',
        dedupe_key: 'doctor:1',
        snapshot_ref: {
          snapshot_id: 'DOCTOR-1',
          generated_at: '2026-05-01T12:00:05Z',
        },
      },
    },
    {
      key: 'main-chat-warning',
      domain: 'main_chat',
      severity: 'warning',
      title: 'Main chat planning warning',
      timestamp: '2026-05-01T12:00:20Z',
      payload: {
        stage: 'planning',
        query_id: 'manual-chat-1',
        dedupe_key: 'query:planning:1',
        snapshot_ref: {
          snapshot_id: 'QUERY-PLAN-1',
          generated_at: '2026-05-01T12:00:20Z',
        },
      },
    },
    {
      key: 'main-chat-final',
      domain: 'main_chat',
      severity: 'info',
      title: 'Main chat final output',
      timestamp: '2026-05-01T12:00:21Z',
      payload: {
        stage: 'final_output',
        query_id: 'manual-chat-1',
        dedupe_key: 'query:final:1',
      },
    },
    {
      key: 'mcp-success',
      domain: 'mcp',
      severity: 'info',
      title: 'MCP 服务已完成 Probe',
      timestamp: '2026-05-01T12:00:09Z',
      payload: {
        dedupe_key: 'mcp:filesystem:ok',
        snapshot_ref: {
          snapshot_id: 'MCP-1',
          generated_at: '2026-05-01T12:00:09Z',
        },
      },
    },
  ]

  const entrySnapshotRef = (entry) => entry?.payload?.snapshot_ref || null
  const getTimelineQueryId = (entry) => entry?.payload?.query_id || ''
  const getTimelineDedupeKey = (entry) => entry?.payload?.dedupe_key || ''
  const getFrameworkAdapterExternalErrorType = () => ''
  const formatTimelineDomain = (domain) => ({
    doctor: 'Doctor',
    main_chat: 'Main Chat',
    mcp: 'MCP',
    other: '其他',
  }[domain] || domain)
  const toTimestamp = (value) => new Date(value).getTime()
  const getSeverityRank = (severity) => ({ warning: 3, info: 1 }[severity] || 0)

  it('builds severity filters and timeline filters from timeline entries', () => {
    const severityFilters = buildSeverityFilters(timeline)
    expect(severityFilters).toEqual([
      { key: 'all', label: '全部事件', count: 4 },
      { key: 'warning', label: '仅告警', count: 2 },
    ])

    const warningTimeline = scopeTimelineBySeverity(timeline, 'warning')
    expect(warningTimeline).toHaveLength(2)

    const timelineFilters = buildTimelineFilters(timeline, formatTimelineDomain)
    expect(timelineFilters).toEqual([
      { key: 'all', label: '全部', count: 4 },
      { key: 'doctor', label: 'Doctor', count: 1 },
      { key: 'mcp', label: 'MCP', count: 1 },
      { key: 'main_chat', label: 'Main Chat', count: 2 },
    ])
  })

  it('filters timeline entries by domain query stage dedupe and snapshot', () => {
    const scopedTimeline = scopeTimelineBySeverity(timeline, 'all')
    const filtered = filterTimelineEntries(scopedTimeline, {
      activeFilter: 'main_chat',
      activeQueryId: 'manual-chat-1',
      activeQueryStage: 'planning',
      activeFrameworkAdapterErrorType: '',
      activeDedupeKey: '',
      activeSnapshotId: 'QUERY-PLAN-1',
      getTimelineQueryId,
      getTimelineDedupeKey,
      entrySnapshotRef,
      getFrameworkAdapterExternalErrorType,
    })
    expect(filtered.map(item => item.key)).toEqual(['main-chat-warning'])

    const fallback = filterTimelineEntries(scopedTimeline, {
      activeFilter: 'main_chat',
      activeQueryId: 'manual-chat-1',
      activeQueryStage: '',
      activeFrameworkAdapterErrorType: '',
      activeDedupeKey: '',
      activeSnapshotId: 'UNKNOWN',
      getTimelineQueryId,
      getTimelineDedupeKey,
      entrySnapshotRef,
      getFrameworkAdapterExternalErrorType,
    })
    expect(fallback.map(item => item.key)).toEqual(['main-chat-warning', 'main-chat-final'])
  })

  it('derives snapshot fallback and active snapshot notice', () => {
    const filteredTimeline = [timeline[2]]
    const scopedTimeline = [timeline[1], timeline[2]]
    const snapshotRef = buildCurrentSnapshotRef(filteredTimeline, scopedTimeline, timeline, entry => entrySnapshotRef(entry))
    expect(snapshotRef).toEqual({
      snapshot_id: 'QUERY-PLAN-1',
      generated_at: '2026-05-01T12:00:20Z',
    })

    expect(buildActiveSnapshotNotice('', timeline, entrySnapshotRef)).toBe('当前展示的是常规治理视图')
    expect(buildActiveSnapshotNotice('UNKNOWN', timeline, entrySnapshotRef)).toBe('当前会话未找到对应快照，已回退到常规治理视图')
    expect(buildActiveSnapshotNotice('QUERY-PLAN-1', timeline, entrySnapshotRef)).toBe('已聚焦到 Main chat planning warning')
  })

  it('builds governance overview cards and recommended focus outputs', () => {
    const timelineFilters = buildTimelineFilters(timeline, formatTimelineDomain)
    const cards = buildGovernanceOverviewCards(timeline, timelineFilters, {
      formatTimelineDomain,
      toTimestamp,
      getSeverityRank,
    })

    expect(cards.map(item => item.key)).toEqual(['main_chat', 'mcp', 'doctor'])
    expect(cards[0]).toMatchObject({
      key: 'main_chat',
      count: 2,
      warningCount: 1,
      latestTitle: 'Main chat planning warning',
    })

    const recommendedFocusFilter = buildRecommendedFocusFilter(
      { title: 'Doctor 门禁失败' },
      'Doctor 门禁失败',
      cards
    )
    expect(recommendedFocusFilter).toBe('main_chat')

    expect(buildRecommendedFocusSignature({ id: 23 }, 'main_chat', { timestamp: '2026-05-01T12:00:05Z' }))
      .toBe('23:2026-05-01T12:00:05Z:main_chat')

    expect(buildAutoFocusNotice({
      recommendedFocusSignature: '23:2026-05-01T12:00:05Z:main_chat',
      routeGovernanceFilter: '',
      lastAutoFocusSignature: '23:2026-05-01T12:00:05Z:main_chat',
      activeFilter: 'main_chat',
      recommendedFocusFilter: 'main_chat',
      governanceOverviewCards: cards,
    })).toBe('因 Doctor 门禁失败，当前默认聚焦到 Main Chat 风险域，共 1 条告警。')
  })

  it('normalizes combined timeline entries and adds synthetic diagnostics', () => {
    const focusItem = {
      audit_trail: [
        {
          timestamp: '2026-05-01T12:00:00Z',
          event_type: 'doctor_run_started',
          content: 'Doctor started',
          payload: { source: 'audit' },
        },
      ],
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:17Z',
          source: 'framework_adapter',
          event_type: 'framework_adapter_external_error',
          severity: 'warning',
          summary: 'external error',
          detail: 'detail',
          payload: {
            framework_adapters: {
              latest_external_pilot_failure: {
                error_type: 'protocol_error',
                snapshot_ref: {
                  snapshot_id: 'FRAM-EXT-1',
                  generated_at: '2026-05-01T12:00:17Z',
                },
              },
              external_pilot_failure_counts: {
                protocol_error: 2,
              },
            },
          },
        },
      ],
    }

    const timeline = buildCombinedTimeline(focusItem, {
      normalizePayload: payload => (payload && typeof payload === 'object' && !Array.isArray(payload) ? payload : null),
      inferTimelineDomain: (eventType, source) => source || (eventType.includes('doctor') ? 'doctor' : 'other'),
      formatTimelineDomain: domain => domain,
      normalizeSeverity: () => 'info',
      formatAuditEvent: eventType => eventType,
      formatPayloadSummary: payload => JSON.stringify(payload),
      formatTraceSource: source => source,
      formatFrameworkAdapterExternalErrorTag: payload => payload?.error_type || '',
      formatFrameworkAdapterExternalErrorDetail: payload => payload?.detail || '',
      normalizeSnapshotRef: snapshotRef => snapshotRef || null,
      toTimestamp,
      normalizeText: value => String(value || '').trim(),
    })

    expect(timeline).toHaveLength(3)
    expect(timeline[0]).toMatchObject({
      key: 'trace-2026-05-01T12:00:17Z-framework_adapter-framework_adapter_external_error-0',
      domain: 'framework_adapter',
      severity: 'warning',
      title: 'framework_adapter_external_error',
      content: 'external error',
    })
    expect(timeline[1]).toMatchObject({
      key: 'trace-framework-adapter-external-failure-diagnostic-2026-05-01T12:00:17Z-0',
      domain: 'framework_adapter',
      severity: 'warning',
      title: 'framework_adapter_external_failure_diagnostic',
      content: 'protocol_error',
    })
    expect(timeline[2]).toMatchObject({
      key: 'audit-2026-05-01T12:00:00Z-doctor_run_started-0',
      kind: 'audit',
      title: 'doctor_run_started',
    })
  })

  it('derives latest governance outcomes and framework adapter remediation', () => {
    const combinedTimeline = [
      {
        domain: 'doctor',
        kind: 'trace',
        title: 'doctor_gate_failed',
        timestamp: '2026-05-01T12:00:21Z',
        severity: 'warning',
        payload: {},
      },
      {
        domain: 'doctor',
        kind: 'trace',
        title: 'doctor_run_completed',
        timestamp: '2026-05-01T12:00:20Z',
        severity: 'info',
        payload: {
          framework_adapters: {
            remediation_actions: [
              { adapter_id: 'langgraph_draft', status: 'pending' },
              { adapter_id: 'langgraph_draft', status: 'applied' },
            ],
          },
        },
      },
      {
        domain: 'permission',
        title: 'permission_approved',
      },
      {
        domain: 'mcp',
        title: 'mcp_server_probed',
      },
      {
        domain: 'framework_adapter',
        title: 'framework_adapter_external_failure_diagnostic',
      },
    ]

    const outcomes = buildGovernanceTimelineOutcomes(combinedTimeline, {
      formatAuditEvent: eventType => eventType,
      normalizeText: value => String(value || '').trim(),
      formatFrameworkAdapterDisplayName: (_frameworkName, adapterId) => adapterId === 'langgraph_draft' ? 'LangGraph Draft' : adapterId,
      buildFrameworkAdapterRemediationStatusTags: actions => actions.map(item => item.status),
      formatFrameworkAdapterRemediationContent: (displayName, actionCount, statusTags) => `${displayName}:${actionCount}:${statusTags.join(',')}`,
      buildFrameworkAdapterRemediationCommand: actions => `run:${actions.length}`,
    })

    expect(outcomes.lastDoctorOutcome?.title).toBe('doctor_gate_failed')
    expect(outcomes.lastPermissionOutcome?.title).toBe('permission_approved')
    expect(outcomes.lastMcpOutcome?.title).toBe('mcp_server_probed')
    expect(outcomes.lastFrameworkAdapterExternalFailureDiagnostic?.title).toBe('framework_adapter_external_failure_diagnostic')
    expect(outcomes.lastFrameworkAdapterRemediation).toMatchObject({
      title: 'doctor_run_completed',
      adapterId: 'langgraph_draft',
      displayName: 'LangGraph Draft',
      statusTags: ['pending', 'applied'],
      commandText: 'run:2',
    })
  })
})
