import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { mount, flushPromises } from '@vue/test-utils'

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn()
  }),
  useRoute: () => ({
    query: {}
  })
}))

vi.mock('../../api', () => ({
  healthApi: {
    getHealth: vi.fn().mockResolvedValue({
      data: {
        failover: {
          alert_level: 'medium'
        }
      }
    })
  },
  runtimeSurfaceApi: {
    getProfile: vi.fn().mockResolvedValue({
      data: {
        default_model: 'doubao',
        models: [{ name: 'doubao', display_name: '豆包' }],
        failover_thresholds: { medium: 0.1, high: 0.2 }
      }
    }),
    updateProfile: vi.fn().mockResolvedValue({ data: {} })
  },
  doctorApi: {
    getReport: vi.fn().mockResolvedValue({
      data: {
        scope: 'startup',
        status: 'ok',
        exit_code: 0
      }
    })
  },
  providerApi: {
    getFailoverAnalytics: vi.fn().mockResolvedValue({
      data: {
        switch_rate: 0.25,
        switched_children: 5,
        total_children: 20,
        total_switches: 7,
        top_provider_failover_pairs: []
      }
    })
  }
}))

import SettingsView from '../../views/SettingsView.vue'
import { useAuthStore } from '../../stores/auth'

describe('SettingsView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('uses runtime thresholds to evaluate failover risk and alert text', async () => {
    const authStore = useAuthStore()
    authStore.authMode = 'demo_guest'
    authStore.user = { username: 'tester' }

    const wrapper = mount(SettingsView, {
      global: {
        stubs: {
          ProviderConfigPanel: true,
          RuntimeSurfacePanel: true,
          DoctorPanel: true,
          GovernanceTimelinePanel: true,
          CapabilityGapSummaryPanel: true,
          McpManagementPanel: true
        }
      }
    })

    await flushPromises()
    await wrapper.findAll('.tab-btn')[1].trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('高风险')
    expect(wrapper.text()).toContain('已超过高风险阈值')
    expect(wrapper.text()).toContain('健康数据更新时间')
  })
})
