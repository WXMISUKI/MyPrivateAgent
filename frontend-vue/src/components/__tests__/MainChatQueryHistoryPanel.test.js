import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import MainChatQueryHistoryPanel from '../MainChatQueryHistoryPanel.vue'

const history = {
  readModelLayer: 'query_history',
  sourceChannel: 'main_chat',
  identityKind: 'query_id',
  items: [
    {
      queryId: 'manual-chat-2',
      latestStage: 'final_output',
      latestSummary: 'Main chat final output 2',
      latestTimestamp: '2026-05-01T12:00:20Z',
      latestSnapshotId: 'QUER-FINAL-321-20260501120020',
      stageCounts: { planning: 1, final_output: 1 },
      reason: '',
    }
  ],
  hasMore: false,
  reason: '',
}

describe('MainChatQueryHistoryPanel', () => {
  it('renders current context and emits query and stage selection events', async () => {
    const wrapper = mount(MainChatQueryHistoryPanel, {
      props: {
        history,
        loading: false,
        error: '',
        search: '',
        statusText: '共 1 条 · 第 1 页',
        contextLabel: '当前聚焦：manual-chat-2 / planning',
        activeQueryId: 'manual-chat-2',
        filteredItems: history.items,
        isStageFocused: () => true,
        formatStageTags: () => [
          { key: 'planning', label: 'planning 1', active: true },
          { key: 'final_output', label: 'final_output 1', active: false },
        ],
        formatSnapshotTime: () => '2026/5/1 20:00:20',
      }
    })

    expect(wrapper.text()).toContain('Main Chat Query History')
    expect(wrapper.text()).toContain('layer query_history')
    expect(wrapper.text()).toContain('source main_chat')
    expect(wrapper.text()).toContain('当前聚焦：manual-chat-2 / planning')
    expect(wrapper.find('.main-chat-history-item').classes()).toContain('active')
    expect(wrapper.find('.main-chat-history-item').classes()).toContain('stage-focused')
    expect(wrapper.find('.main-chat-history-stage-tag.active').text()).toContain('planning 1')

    await wrapper.find('.main-chat-history-entry').trigger('click')
    await wrapper.findAll('.main-chat-history-stage-tag')[0].trigger('click')

    expect(wrapper.emitted('select-query')?.[0]).toEqual(['manual-chat-2'])
    expect(wrapper.emitted('select-stage')?.[0]).toEqual([{ queryId: 'manual-chat-2', stage: 'planning' }])
  })
})
