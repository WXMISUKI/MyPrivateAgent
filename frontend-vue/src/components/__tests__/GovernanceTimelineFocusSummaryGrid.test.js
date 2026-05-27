import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import GovernanceTimelineFocusSummaryGrid from '../GovernanceTimelineFocusSummaryGrid.vue'

function mountGrid(overrides = {}) {
  return mount(GovernanceTimelineFocusSummaryGrid, {
    props: {
      currentPlanObjectiveLabel: '完善治理时间线',
      focusItemTitleLabel: '拆分 summary grid',
      auditCount: 2,
      traceCount: 5,
      currentRunOverview: {
        id: 'run-1',
        summary: 'running',
        notice: 'child_display_id ready',
      },
      approvalOverview: {
        pendingLabel: '1 pending',
        primaryDetail: 'shell_command',
        secondaryDetail: 'standard',
      },
      activeFilter: 'main_chat',
      activeFilterLabel: 'Main Chat',
      activeSeverity: 'warning',
      activeSeverityLabel: '仅告警',
      activeFrameworkAdapterErrorType: 'protocol_error',
      activeFrameworkAdapterErrorTypeLabel: 'Protocol Error',
      activeFrameworkAdapterErrorTypeClearLabel: '清除错误类型 protocol_error',
      activeDedupeKey: 'dedupe-main-chat-001',
      activeDedupeKeyPreview: 'dedupe-main-chat-001',
      activeDedupeKeyMatchLabel: '匹配 2 条',
      activeDedupeKeyMatchAriaLabel: '幂等键匹配 2 条',
      activeDedupeKeyCopyLabel: '复制当前幂等键 dedupe-main-chat-001',
      activeDedupeKeyClearLabel: '清除幂等键 dedupe-main-chat-001',
      copiedActiveDedupeKey: false,
      activeQueryId: 'query-1',
      activeQueryStage: 'planning',
      currentQueryOverview: {
        latestStage: 'planning',
        stageCount: 3,
        warningCount: 1,
        latestSnapshotId: 'SNAP-1',
        latestSummary: 'ready',
      },
      mainChatQueryHistory: {
        recordingState: 'recorded',
        totalItems: 8,
        page: 2,
        pageSize: 4,
      },
      currentSnapshotId: 'SNAP-1',
      currentSnapshotGeneratedAt: '2026-05-27T10:00:00Z',
      activeSnapshotLabel: 'SNAP-1',
      activeSnapshotNotice: '当前快照聚焦',
      formatSnapshotTime: value => `time:${value}`,
      ...overrides,
    },
  })
}

describe('GovernanceTimelineFocusSummaryGrid', () => {
  it('renders focus summary, query, history, and snapshot cards', () => {
    const wrapper = mountGrid()

    expect(wrapper.text()).toContain('当前计划')
    expect(wrapper.text()).toContain('完善治理时间线')
    expect(wrapper.text()).toContain('聚焦步骤')
    expect(wrapper.text()).toContain('拆分 summary grid')
    expect(wrapper.text()).toContain('Query 摘要')
    expect(wrapper.text()).toContain('阶段 3 · 告警 1')
    expect(wrapper.text()).toContain('Main Chat Query History')
    expect(wrapper.text()).toContain('page 2 · size 4')
    expect(wrapper.text()).toContain('time:2026-05-27T10:00:00Z')
  })

  it('forwards focus clear and copy actions to the parent', async () => {
    const wrapper = mountGrid()

    await wrapper.get('button[aria-label="清除错误类型 protocol_error"]').trigger('click')
    await wrapper.get('button[aria-label="复制当前幂等键 dedupe-main-chat-001"]').trigger('click')
    await wrapper.get('button[aria-label="清除幂等键 dedupe-main-chat-001"]').trigger('click')
    await wrapper.get('button[aria-label="清除 Query query-1"]').trigger('click')
    await wrapper.get('button[aria-label="清除阶段 planning"]').trigger('click')

    expect(wrapper.emitted('clear-framework-adapter-error-type')).toHaveLength(1)
    expect(wrapper.emitted('copy-active-dedupe-key')).toHaveLength(1)
    expect(wrapper.emitted('clear-dedupe-key')).toHaveLength(1)
    expect(wrapper.emitted('clear-query')).toHaveLength(1)
    expect(wrapper.emitted('clear-stage')).toHaveLength(1)
  })
})
