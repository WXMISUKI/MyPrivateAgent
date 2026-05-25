import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import GovernanceTimelineFilters from '../GovernanceTimelineFilters.vue'

describe('GovernanceTimelineFilters', () => {
  it('renders active filter chips and emits updates', async () => {
    const wrapper = mount(GovernanceTimelineFilters, {
      props: {
        severityFilters: [
          { key: 'all', label: '全部风险', count: 3 },
          { key: 'warning', label: '仅告警', count: 1 }
        ],
        timelineFilters: [
          { key: 'all', label: '全部', count: 3 },
          { key: 'permission', label: 'Permission', count: 1 }
        ],
        activeSeverity: 'warning',
        activeFilter: 'all'
      }
    })

    expect(wrapper.text()).toContain('仅告警 · 1')
    expect(wrapper.text()).toContain('Permission · 1')
    expect(wrapper.findAll('button.severity-chip').find(item => item.text().includes('仅告警')).classes()).toContain('active')
    expect(wrapper.findAll('button.filter-chip').find(item => item.text().includes('全部 · 3')).classes()).toContain('active')

    await wrapper.findAll('button.severity-chip').find(item => item.text().includes('全部风险')).trigger('click')
    await wrapper.findAll('button.filter-chip').find(item => item.text().includes('Permission')).trigger('click')

    expect(wrapper.emitted('update:activeSeverity')?.[0]).toEqual(['all'])
    expect(wrapper.emitted('update:activeFilter')?.[0]).toEqual(['permission'])
  })
})
