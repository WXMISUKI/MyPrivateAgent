import { describe, expect, it } from 'vitest'

import {
  buildCurrentGovernanceViewSnapshot,
  buildGovernanceViewSnapshot,
  buildGovernanceViewSnapshotId,
  buildGovernanceViewUrl,
  inferSnapshotCommandDomain,
} from '../governanceViewInterpretation'

describe('governanceTimelineSnapshotView', () => {
  it('builds governance view url with preserved non-governance query params', () => {
    const url = buildGovernanceViewUrl({
      locationHref: 'http://localhost/chat?tab=advanced&foo=bar',
      routeQuery: {
        tab: 'advanced',
        foo: 'bar',
        governance_filter: 'old',
      },
      activeFilter: 'framework_adapter',
      activeSeverity: 'warning',
      activeFrameworkAdapterErrorType: 'protocol_error',
      activeDedupeKey: 'dedupe-1',
      activeQueryId: 'query-1',
      activeQueryStage: 'planning',
      activeSnapshotId: 'SNAP-1',
    })

    expect(url).toContain('tab=advanced')
    expect(url).toContain('foo=bar')
    expect(url).toContain('governance_filter=framework_adapter')
    expect(url).toContain('governance_severity=warning')
    expect(url).toContain('governance_error_type=protocol_error')
    expect(url).toContain('governance_dedupe_key=dedupe-1')
    expect(url).toContain('governance_query_id=query-1')
    expect(url).toContain('governance_query_stage=planning')
    expect(url).toContain('governance_snapshot=SNAP-1')
  })

  it('builds governance view snapshot text with query and snapshot context', () => {
    const text = buildGovernanceViewSnapshot({
      currentSnapshotRef: {
        snapshot_id: 'FRAM-1',
        generated_at: '2026-05-01T12:00:16Z',
        source: 'framework_adapter',
        event_type: 'framework_adapter_external_error',
      },
      activeFilter: 'framework_adapter',
      activeSeverity: 'warning',
      activeFilterLabel: 'Framework Adapter',
      activeSeverityLabel: '仅告警',
      filteredTimeline: [{ title: 'Framework Adapter 外部错误' }],
      scopedTimeline: [{ title: 'A' }, { title: 'B' }],
      activeFrameworkAdapterErrorTypeLabel: '协议错误 (protocol_error)',
      activeDedupeKey: 'dedupe-1',
      activeDedupeKeyMatchLabel: '匹配事件 1 / 2',
      activeQueryId: 'query-1',
      currentQueryOverview: {
        latestStage: 'planning',
        warningCount: 2,
      },
      activeQueryStage: 'planning',
      autoFocusNotice: '因 Doctor 门禁失败，当前默认聚焦到 Main Chat 风险域，共 1 条告警。',
      currentViewUrl: 'http://localhost/chat?tab=advanced',
    })

    expect(text).toContain('快照ID: FRAM-1')
    expect(text).toContain('治理视图: Framework Adapter / 仅告警')
    expect(text).toContain('事件范围: 1 / 2')
    expect(text).toContain('错误类型: 协议错误 (protocol_error)')
    expect(text).toContain('幂等键: dedupe-1')
    expect(text).toContain('Query: query-1')
    expect(text).toContain('Query 阶段: planning')
    expect(text).toContain('阶段聚焦: planning')
    expect(text).toContain('后端引用: framework_adapter / framework_adapter_external_error')
    expect(text).toContain('链接: http://localhost/chat?tab=advanced')
  })

  it('builds current governance view snapshot with search and page context', () => {
    const text = buildCurrentGovernanceViewSnapshot({
      locationHref: 'http://localhost/chat?tab=advanced',
      routeQuery: { tab: 'advanced' },
      currentSnapshotRef: {
        snapshot_id: 'QUERY-1',
        generated_at: '2026-05-01T12:00:16Z',
        source: 'framework_adapter',
        event_type: 'framework_adapter_external_error',
      },
      activeFilter: 'main_chat',
      activeSeverity: 'warning',
      activeFilterLabel: 'Main Chat',
      activeSeverityLabel: '仅告警',
      filteredTimeline: [{ title: 'Main Chat Query History' }],
      scopedTimeline: [{ title: 'one' }, { title: 'two' }],
      activeQueryId: 'query-1',
      currentQueryOverview: {
        latestStage: 'planning',
        warningCount: 1,
      },
      activeQueryStage: 'planning',
      activeQuerySearch: 'query-id',
      activeQueryHistoryPage: 2,
      autoFocusNotice: 'auto',
      activeSnapshotId: 'SNAP-1',
    })

    expect(text).toContain('History 搜索: query-id')
    expect(text).toContain('History 页: 2')
    expect(text).toContain('链接: http://localhost/chat?tab=advanced&governance_filter=main_chat')
  })

  it('infers snapshot command domain and fallback snapshot id', () => {
    expect(inferSnapshotCommandDomain(
      { event_type: 'permission_approved', source: 'permission' },
      '',
      (_eventType, source) => source
    )).toBe('permission')

    expect(inferSnapshotCommandDomain(
      { event_type: 'runtime_event', source: 'runtime' },
      'mcp',
      (_eventType, source) => source
    )).toBe('mcp')

    expect(buildGovernanceViewSnapshotId('2026-05-01T12:00:16Z', {
      activeFilter: 'hook',
      activeSeverity: 'warning',
      filteredTimeline: [{ title: 'Hook blocked tool' }],
    })).toBe('HOOK-WARN-HOOKBLOC-202605011200')
  })
})
