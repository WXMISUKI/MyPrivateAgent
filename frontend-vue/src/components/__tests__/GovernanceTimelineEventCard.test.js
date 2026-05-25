import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import GovernanceTimelineEventCard from '../GovernanceTimelineEventCard.vue'

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
    dedupe_key: 'framework_adapter_external_error:99:langgraph_draft:protocol_error:transport probe did not provide assistant identity evidence'
  }
}

describe('GovernanceTimelineEventCard', () => {
  it('renders event details and emits timeline actions', async () => {
    const wrapper = mount(GovernanceTimelineEventCard, {
      props: {
        entry,
        snapshotRef: { snapshot_id: 'FRAM-REF-1' },
        highlighted: true,
        hasPayload: true,
        payloadExpanded: true,
        payloadJson: '{\n  "status": "failed"\n}',
        copiedSnapshot: true,
        copiedCommand: true,
        copiedPayload: true,
        copiedDedupeKey: true,
        focusedDedupeKey: true,
        focusedQueryId: true,
        formattedTime: '20:00:16'
      }
    })

    expect(wrapper.classes()).toContain('timeline-item')
    expect(wrapper.classes()).toContain('severity-warning')
    expect(wrapper.classes()).toContain('highlighted')
    expect(wrapper.text()).toContain('Framework Adapter 外部执行失败')
    expect(wrapper.text()).toContain('协议错误 (protocol_error)')
    expect(wrapper.text()).toContain('引用 FRAM-REF-1')
    expect(wrapper.text()).toContain('status=failed | gate_passed=false')
    expect(wrapper.text()).toContain('Query manual-chat-2')
    expect(wrapper.text()).toContain('幂等键')
    expect(wrapper.text()).toContain('framework_adapter_external_error:99:langgraph_draft')
    expect(wrapper.find('.timeline-dedupe-key').text()).toContain('assistant identity evidence')
    expect(wrapper.find('.timeline-dedupe-key').attributes('title')).toBe(entry.payload.dedupe_key)
    expect(wrapper.find('.timeline-dedupe-key').attributes('aria-label')).toBe(`幂等键 ${entry.payload.dedupe_key}`)
    expect(wrapper.text()).toContain('已复制幂等键')
    const copiedDedupeButton = wrapper.findAll('button.payload-toggle-btn').find(item => item.text().includes('已复制幂等键'))
    expect(copiedDedupeButton.attributes('title')).toBe(entry.payload.dedupe_key)
    expect(copiedDedupeButton.attributes('aria-label')).toBe(`已复制幂等键 ${entry.payload.dedupe_key}`)
    expect(wrapper.text()).toContain('已聚焦幂等键')
    expect(wrapper.text()).toContain('已聚焦 Query')
    expect(wrapper.text()).toContain('"status": "failed"')
    const focusedDedupeButton = wrapper.findAll('button.payload-toggle-btn').find(item => item.text().includes('已聚焦幂等键'))
    expect(focusedDedupeButton.attributes('title')).toBe(entry.payload.dedupe_key)
    expect(focusedDedupeButton.attributes('aria-label')).toBe(`已聚焦幂等键 ${entry.payload.dedupe_key}`)
    const focusedQueryButton = wrapper.findAll('button.payload-toggle-btn').find(item => item.text().includes('已聚焦 Query'))
    expect(focusedQueryButton.attributes('title')).toBe(entry.payload.query_id)
    expect(focusedQueryButton.attributes('aria-label')).toBe(`已聚焦 Query ${entry.payload.query_id}`)

    await wrapper.findAll('button.payload-toggle-btn').find(item => item.text().includes('收起 Payload')).trigger('click')
    await wrapper.findAll('button.payload-toggle-btn').find(item => item.text().includes('已复制引用')).trigger('click')
    await wrapper.findAll('button.payload-toggle-btn').find(item => item.text().includes('已复制命令')).trigger('click')
    await wrapper.findAll('button.payload-toggle-btn').find(item => item.text().includes('已复制 Payload')).trigger('click')
    expect(focusedQueryButton.attributes('disabled')).toBeDefined()
    await wrapper.findAll('button.payload-toggle-btn').find(item => item.text().includes('已复制幂等键')).trigger('click')
    expect(focusedDedupeButton.attributes('disabled')).toBeDefined()

    expect(wrapper.emitted('toggle-payload')?.[0]).toEqual([entry])
    expect(wrapper.emitted('copy-snapshot-ref')?.[0]).toEqual([entry])
    expect(wrapper.emitted('copy-snapshot-command')?.[0]).toEqual([entry])
    expect(wrapper.emitted('copy-payload')?.[0]).toEqual([entry])
    expect(wrapper.emitted('copy-dedupe-key')?.[0]).toEqual([entry])
    expect(wrapper.emitted('focus-dedupe-key')).toBeUndefined()
    expect(wrapper.emitted('focus-query-id')).toBeUndefined()
  })

  it('emits focus action when the dedupe key is not active', async () => {
    const wrapper = mount(GovernanceTimelineEventCard, {
      props: {
        entry,
        hasPayload: true,
        formattedTime: '20:00:16'
      }
    })

    const copyDedupeButton = wrapper.findAll('button.payload-toggle-btn').find(item => item.text().includes('复制幂等键'))
    expect(copyDedupeButton.attributes('title')).toBe(entry.payload.dedupe_key)
    expect(copyDedupeButton.attributes('aria-label')).toBe(`复制幂等键 ${entry.payload.dedupe_key}`)
    await wrapper.findAll('button.payload-toggle-btn').find(item => item.text().includes('聚焦幂等键')).trigger('click')

    const focusDedupeButton = wrapper.findAll('button.payload-toggle-btn').find(item => item.text().includes('聚焦幂等键'))
    expect(focusDedupeButton.attributes('title')).toBe(entry.payload.dedupe_key)
    expect(focusDedupeButton.attributes('aria-label')).toBe(`聚焦幂等键 ${entry.payload.dedupe_key}`)
    expect(wrapper.emitted('focus-dedupe-key')?.[0]).toEqual([entry])
  })

  it('emits query focus action when the query is not active', async () => {
    const wrapper = mount(GovernanceTimelineEventCard, {
      props: {
        entry,
        hasPayload: true,
        formattedTime: '20:00:16'
      }
    })

    const focusQueryButton = wrapper.findAll('button.payload-toggle-btn').find(item => item.text().includes('聚焦 Query'))
    expect(focusQueryButton.attributes('title')).toBe(entry.payload.query_id)
    expect(focusQueryButton.attributes('aria-label')).toBe(`聚焦 Query ${entry.payload.query_id}`)

    await focusQueryButton.trigger('click')

    expect(wrapper.emitted('focus-query-id')?.[0]).toEqual([entry])
  })
})
