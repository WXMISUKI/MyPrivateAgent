import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import GovernanceTimelineEventStream from '../GovernanceTimelineEventStream.vue'

const entry = {
  key: 'event-1',
  severity: 'warning',
  kindLabel: 'Trace',
  domainLabel: 'Framework Adapter',
  sourceLabel: 'LangGraph',
  title: 'Framework Adapter 外部执行失败',
  timestamp: '20:00:16',
  content: '协议错误 (protocol_error)',
  detail: 'transport probe did not provide assistant identity evidence',
  payloadSummary: 'status=failed | gate_passed=false',
  payload: {
    status: 'failed',
    query_id: 'manual-chat-2',
    dedupe_key: 'framework_adapter_external_error:99:langgraph_draft:protocol_error:transport probe did not provide assistant identity evidence',
  },
}

describe('GovernanceTimelineEventStream', () => {
  it('renders event stream state and forwards filter updates', async () => {
    const wrapper = mount(GovernanceTimelineEventStream, {
      props: {
        filteredTimeline: [entry],
        scopedTimeline: [entry],
        activeFilter: 'all',
        activeSeverity: 'all',
        activeDedupeKey: 'framework_adapter_external_error:99:langgraph_draft:protocol_error:transport probe did not provide assistant identity evidence',
        activeDedupeKeyEmptyClearLabel: '清除幂等键聚焦 framework_adapter_external_error',
        copiedSnapshotKey: '',
        copiedCommandTarget: '',
        copiedPayloadKey: '',
        copiedDedupeKey: '',
        activeQueryId: '',
        severityFilters: [
          { key: 'all', label: '全部事件', count: 1 },
          { key: 'warning', label: '仅告警', count: 1 },
        ],
        timelineFilters: [
          { key: 'all', label: '全部', count: 1 },
          { key: 'framework_adapter', label: 'Framework Adapter', count: 1 },
        ],
        formatAuditTime: () => '20:00:16',
        formatPayloadJson: () => '{\n  "status": "failed"\n}',
        entrySnapshotRef: () => ({ snapshot_id: 'FRAM-REF-1' }),
        isSnapshotHighlighted: () => true,
        hasPayload: () => true,
        isPayloadExpanded: () => true,
        getTimelineDedupeKey: item => item.payload.dedupe_key,
        getTimelineQueryId: item => item.payload.query_id,
      },
    })

    expect(wrapper.text()).toContain('统一事件流')
    expect(wrapper.text()).toContain('Framework Adapter 外部执行失败')
    expect(wrapper.text()).toContain('复制引用')

    await wrapper.findAll('button.filter-chip').find(item => item.text().includes('仅告警')).trigger('click')
    await wrapper.findAll('button.filter-chip').find(item => item.text().includes('Framework Adapter')).trigger('click')

    expect(wrapper.emitted('update:active-severity')?.[0]).toEqual(['warning'])
    expect(wrapper.emitted('update:active-filter')?.[0]).toEqual(['framework_adapter'])
  })

  it('forwards event-card actions without swallowing payloads', async () => {
    const wrapper = mount(GovernanceTimelineEventStream, {
      props: {
        filteredTimeline: [entry],
        scopedTimeline: [entry],
        activeFilter: 'all',
        activeSeverity: 'all',
        activeDedupeKey: '',
        activeDedupeKeyEmptyClearLabel: '',
        copiedSnapshotKey: '',
        copiedCommandTarget: '',
        copiedPayloadKey: '',
        copiedDedupeKey: '',
        activeQueryId: '',
        severityFilters: [],
        timelineFilters: [],
        formatAuditTime: () => '20:00:16',
        formatPayloadJson: () => '{\n  "status": "failed"\n}',
        entrySnapshotRef: () => ({ snapshot_id: 'FRAM-REF-1' }),
        isSnapshotHighlighted: () => false,
        hasPayload: () => true,
        isPayloadExpanded: () => false,
        getTimelineDedupeKey: item => item.payload.dedupe_key,
        getTimelineQueryId: item => item.payload.query_id,
      },
    })

    const buttons = wrapper.findAll('button.payload-toggle-btn')
    await buttons.find(item => item.text().includes('展开 Payload')).trigger('click')
    await buttons.find(item => item.text().includes('复制引用')).trigger('click')
    await buttons.find(item => item.text().includes('复制命令')).trigger('click')
    await buttons.find(item => item.text().includes('复制 Payload')).trigger('click')
    await buttons.find(item => item.text().includes('复制幂等键')).trigger('click')
    await buttons.find(item => item.text().includes('聚焦幂等键')).trigger('click')
    await buttons.find(item => item.text().includes('聚焦 Query')).trigger('click')

    expect(wrapper.emitted('toggle-payload')?.[0]).toEqual([entry])
    expect(wrapper.emitted('copy-snapshot-ref')?.[0]).toEqual([entry])
    expect(wrapper.emitted('copy-snapshot-command')?.[0]).toEqual([entry])
    expect(wrapper.emitted('copy-payload')?.[0]).toEqual([entry])
    expect(wrapper.emitted('copy-dedupe-key')?.[0]).toEqual([entry])
    expect(wrapper.emitted('focus-dedupe-key')?.[0]).toEqual([entry])
    expect(wrapper.emitted('focus-query-id')?.[0]).toEqual([entry])
  })

  it('renders empty state for unmatched dedupe keys and clears focus', async () => {
    const wrapper = mount(GovernanceTimelineEventStream, {
      props: {
        filteredTimeline: [],
        scopedTimeline: [entry],
        activeFilter: 'all',
        activeSeverity: 'all',
        activeDedupeKey: entry.payload.dedupe_key,
        activeDedupeKeyEmptyClearLabel: '清除幂等键聚焦 framework_adapter_external_error',
        copiedSnapshotKey: '',
        copiedCommandTarget: '',
        copiedPayloadKey: '',
        copiedDedupeKey: '',
        activeQueryId: '',
        severityFilters: [],
        timelineFilters: [],
        formatAuditTime: () => '20:00:16',
        formatPayloadJson: () => '{\n  "status": "failed"\n}',
        entrySnapshotRef: () => ({ snapshot_id: 'FRAM-REF-1' }),
        isSnapshotHighlighted: () => false,
        hasPayload: () => true,
        isPayloadExpanded: () => false,
        getTimelineDedupeKey: item => item.payload.dedupe_key,
        getTimelineQueryId: item => item.payload.query_id,
      },
    })

    expect(wrapper.text()).toContain('当前幂等键没有匹配到治理事件')
    expect(wrapper.text()).toContain(entry.payload.dedupe_key)

    await wrapper.find('button.payload-toggle-btn').trigger('click')

    expect(wrapper.emitted('clear-dedupe-key')?.[0]).toEqual([])
  })
})
