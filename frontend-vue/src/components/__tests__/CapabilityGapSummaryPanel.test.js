import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { mount, flushPromises } from '@vue/test-utils'

const { getSummaryMock, updateRemediationStatusMock, pushMock } = vi.hoisted(() => ({
  getSummaryMock: vi.fn(),
  updateRemediationStatusMock: vi.fn(),
  pushMock: vi.fn()
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: pushMock
  })
}))

vi.mock('../../api', () => ({
  capabilityGapApi: {
    getSummary: getSummaryMock,
    updateRemediationStatus: updateRemediationStatusMock
  }
}))

import CapabilityGapSummaryPanel from '../CapabilityGapSummaryPanel.vue'
import { useConversationStore } from '../../stores/conversation'
import { usePlannerStore } from '../../stores/planner'

describe('CapabilityGapSummaryPanel', () => {
  let pinia

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    getSummaryMock.mockReset()
    updateRemediationStatusMock.mockReset()
    pushMock.mockReset()
    getSummaryMock.mockResolvedValue({
      data: {
        total_gap_events: 1,
        top_missing_parts: [{ name: 'tooling', count: 1 }],
        suggested_investments: [],
        recent_examples: [],
        pending_actions: [],
        remediation_targets: [
          {
            action_id: 'fix_final_synthesis_chain',
            owner: 'agent-core',
            module: 'planning',
            playbook_title: '补齐最终收尾链路',
            status: 'open',
            status_detail: {}
          }
        ],
        remediation_status_counts: {
          open: 1,
          in_progress: 0,
          blocked: 0,
          done: 0,
          verified: 0
        },
        remediation_progress: {
          window_days: 14,
          recent_progress: [],
          long_blocked: [],
          pending_start: [],
          recent_progress_count: 0,
          long_blocked_count: 0,
          pending_start_count: 1
        },
        escalation_recommendations: []
      }
    })
    updateRemediationStatusMock.mockResolvedValue({
      data: {
        action_id: 'fix_final_synthesis_chain',
        status: 'done',
        timeline_recording: {
          snapshot_ref: {
            snapshot_id: 'GOV-REF-1',
            generated_at: '2026-05-01T12:00:07Z',
            conversation_id: 321,
            source: 'governance',
            event_type: 'remediation_status_updated'
          }
        }
      }
    })

    const conversationStore = useConversationStore()
    const plannerStore = usePlannerStore()
    conversationStore.conversations = [{
      id: 321,
      title: 'gap test',
      modelName: 'doubao',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now()
    }]
    conversationStore.activeId = 321
    plannerStore.loadPlans = vi.fn().mockResolvedValue([])
  })

  it('sends conversation context when remediation status changes', async () => {
    const wrapper = mount(CapabilityGapSummaryPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    const select = wrapper.find('select.remediation-status-select')
    await select.setValue('done')
    await flushPromises()

    expect(updateRemediationStatusMock).toHaveBeenCalledWith('fix_final_synthesis_chain', {
      status: 'done',
      owner: 'agent-core',
      module: 'planning',
      updated_by: 'runtime-panel',
      conversation_id: 321
    })
    expect(usePlannerStore().loadPlans).toHaveBeenCalledWith({ conversationId: 321 })
    expect(wrapper.text()).toContain('最近治理快照')
    expect(wrapper.text()).toContain('GOV-REF-1')
  })

  it('opens governance timeline for latest remediation snapshot', async () => {
    const wrapper = mount(CapabilityGapSummaryPanel, {
      global: {
        plugins: [pinia]
      }
    })
    await flushPromises()

    const select = wrapper.find('select.remediation-status-select')
    await select.setValue('done')
    await flushPromises()
    await flushPromises()

    const snapshotButton = wrapper.findAll('button').find(item => item.text().includes('查看时间线'))
    expect(snapshotButton).toBeTruthy()
    await snapshotButton.trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/settings?tab=advanced&governance_snapshot=GOV-REF-1')
  })
})
