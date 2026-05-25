import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import MainChatQueryDetailPanel from '../MainChatQueryDetailPanel.vue'

const detail = {
  readModelLayer: 'query_detail',
  sourceChannel: 'main_chat',
  identityKind: 'query_id',
  stageChain: ['planning', 'final_output'],
  latestSnapshotId: 'QUER-FINAL-321-20260501120020',
  dedupeKeyCount: 2,
  latestWarningSummary: '',
  recentEvents: [
    {
      timestamp: '2026-05-01T12:00:19Z',
      stage: 'planning',
      summary: 'Main chat planning 1',
      severity: 'info',
    }
  ],
}

describe('MainChatQueryDetailPanel', () => {
  it('renders query detail and emits stage focus actions', async () => {
    const wrapper = mount(MainChatQueryDetailPanel, {
      props: {
        detail,
        activeStage: 'planning',
      }
    })

    expect(wrapper.text()).toContain('Query Detail')
    expect(wrapper.text()).toContain('layer: query_detail')
    expect(wrapper.text()).toContain('source: main_chat')
    expect(wrapper.text()).toContain('identity: query_id')
    expect(wrapper.text()).toContain('QUER-FINAL-321-20260501120020')
    expect(wrapper.find('.query-stage-chip.active').text()).toContain('planning')
    expect(wrapper.find('.query-detail-event-link').text()).toContain('Main chat planning 1')

    await wrapper.find('.query-stage-chip').trigger('click')
    await wrapper.find('.query-detail-event-link').trigger('click')

    expect(wrapper.emitted('focus-stage')?.[0]).toEqual(['planning'])
    expect(wrapper.emitted('focus-stage')?.[1]).toEqual(['planning'])
  })
})
