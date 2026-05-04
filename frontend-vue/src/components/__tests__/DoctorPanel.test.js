import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const { routeQuery, getReportMock, pushMock } = vi.hoisted(() => ({
  routeQuery: {},
  getReportMock: vi.fn(),
  pushMock: vi.fn()
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({
    query: routeQuery
  }),
  useRouter: () => ({
    push: pushMock
  })
}))

vi.mock('../../api', () => ({
  doctorApi: {
    getReport: getReportMock
  }
}))

import DoctorPanel from '../DoctorPanel.vue'
import { useConversationStore } from '../../stores/conversation'
import { usePlannerStore } from '../../stores/planner'

describe('DoctorPanel', () => {
  let pinia

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    Object.keys(routeQuery).forEach((key) => delete routeQuery[key])
    pushMock.mockReset()
    getReportMock.mockReset()
    getReportMock.mockResolvedValue({
      data: {
        scope: 'startup',
        status: 'ok',
        exit_code: 0,
        timeline_recording: {
          snapshot_ref: {
            snapshot_id: 'DOC-REF-1',
            generated_at: '2026-05-01T12:00:00Z',
            conversation_id: 321,
            source: 'doctor',
            event_type: 'doctor_run_completed'
          }
        }
      }
    })

    const conversationStore = useConversationStore()
    const plannerStore = usePlannerStore()
    conversationStore.conversations = [{
      id: 321,
      title: 'doctor test',
      modelName: 'doubao',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now()
    }]
    conversationStore.activeId = 321
    plannerStore.loadPlans = vi.fn().mockResolvedValue([])
  })

  it('auto-runs startup doctor when route query requests it', async () => {
    routeQuery.doctor = 'startup'

    const wrapper = mount(DoctorPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    expect(getReportMock).toHaveBeenCalledWith({ conversation_id: 321 })
    expect(wrapper.text()).toContain('最近一次诊断')
    expect(wrapper.text()).toContain('scope: startup')
    expect(wrapper.text()).toContain('最近治理快照')
    expect(wrapper.text()).toContain('DOC-REF-1')
    expect(usePlannerStore().loadPlans).toHaveBeenCalledWith({ conversationId: 321 })
  })

  it('runs governance doctor with gate parameters when clicked', async () => {
    getReportMock.mockResolvedValueOnce({
      data: {
        scope: 'capability_gap',
        status: 'warn',
        gate_passed: false,
        exit_code: 2,
        non_closed_action_count: 12
      }
    })

    const wrapper = mount(DoctorPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await wrapper.findAll('button')[1].trigger('click')
    await flushPromises()

    expect(getReportMock).toHaveBeenCalledWith({
      capability_gaps: true,
      conversation_id: 321,
      window_days: 14,
      limit: 200,
      max_open_actions: 10,
      max_long_blocked_actions: 0
    })
    expect(wrapper.text()).toContain('未通过')
    expect(wrapper.text()).toContain('12')
  })

  it('navigates to governance timeline when snapshot card is clicked', async () => {
    routeQuery.doctor = 'startup'
    const wrapper = mount(DoctorPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()
    await flushPromises()

    const snapshotButton = wrapper.findAll('button').find(item => item.text().includes('查看时间线'))
    expect(snapshotButton).toBeTruthy()
    await snapshotButton.trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/settings?tab=advanced&governance_snapshot=DOC-REF-1')
  })
})
