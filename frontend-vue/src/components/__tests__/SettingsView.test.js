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
  providerApi: {
    list: vi.fn().mockResolvedValue({
      data: [
        {
          name: 'ollama',
          display_name: 'Ollama (本地)',
          requires_api_key: false,
          configured: true,
          api_key_masked: null,
          base_url: 'http://localhost:11434',
          model_name: '',
          config_source: 'env'
        }
      ]
    }),
    update: vi.fn().mockResolvedValue({ data: { status: 'saved' } }),
    test: vi.fn().mockResolvedValue({
      data: {
        status: 'ok',
        message: '连接成功，发现 3 个模型',
        model_count: 3,
        latency_ms: 12
      }
    }),
    getFailoverAnalytics: vi.fn().mockResolvedValue({
      data: {
        switch_rate: 0.25,
        switched_children: 5,
        total_children: 20,
        total_switches: 7,
        top_provider_failover_pairs: []
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
  providerOnboardingApi: {
    list: vi.fn().mockResolvedValue({ data: { entries: [] } }),
    readiness: vi.fn().mockResolvedValue({ data: {} })
  },
  serviceProviderApi: {
    list: vi.fn().mockResolvedValue({ data: { providers: [] } })
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
          ProviderOnboardingPanel: true,
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

    expect(wrapper.text()).toContain('Provider Failover 看板')
    expect(wrapper.text()).toContain('切换率')
    expect(wrapper.text()).toContain('5/20')
    expect(wrapper.text()).toContain('高风险')
    expect(wrapper.text()).toContain('已超过高风险阈值')
    expect(wrapper.text()).toContain('健康数据更新时间')
    expect(wrapper.text()).toContain('Provider 配置')
  })
})
