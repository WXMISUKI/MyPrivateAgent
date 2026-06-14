import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

const apiMocks = vi.hoisted(() => ({
  providerOnboardingApi: {
    list: vi.fn(),
    readiness: vi.fn()
  },
  serviceProviderApi: {
    list: vi.fn()
  }
}))

vi.mock('../../api', () => ({
  providerOnboardingApi: apiMocks.providerOnboardingApi,
  serviceProviderApi: apiMocks.serviceProviderApi
}))

import ProviderOnboardingPanel from '../ProviderOnboardingPanel.vue'

describe('ProviderOnboardingPanel', () => {
  beforeEach(() => {
    apiMocks.providerOnboardingApi.list.mockReset()
    apiMocks.providerOnboardingApi.readiness.mockReset()
    apiMocks.serviceProviderApi.list.mockReset()
  })

  it('renders onboarding checklist and live provider readiness without invoke actions', async () => {
    apiMocks.providerOnboardingApi.list.mockResolvedValue({
      data: {
        entries: [{
          onboarding_id: 'knowledge-rag-provider',
          provider_id: 'unifiedKnowledgeProvider',
          kind: 'knowledge',
          default_base_url: 'http://127.0.0.1:8020',
          capability_ids: ['knowledge.rag.retrieve'],
          env: {
            enable_var: 'ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER',
            base_url_var: 'KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL'
          },
          docs: ['docs/guides/external_rag_provider_development.md'],
          management: {
            service_provider_detail: '/api/service-providers/unifiedKnowledgeProvider',
            service_provider_evidence_preview: '/api/service-providers/unifiedKnowledgeProvider/evidence-preview'
          },
          boundaries: {
            default_chat_grounding: 'disabled'
          }
        }]
      }
    })
    apiMocks.providerOnboardingApi.readiness.mockResolvedValue({
      data: {
        onboarding_id: 'knowledge-rag-provider',
        configuration_status: 'configured',
        recommended_action: 'run_live_service_provider_probe',
        checks: [{
          id: 'enable_flag',
          env_var: 'ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER',
          status: 'present'
        }]
      }
    })
    apiMocks.serviceProviderApi.list.mockResolvedValue({
      data: {
        providers: [{
          provider_id: 'unifiedKnowledgeProvider',
          overall_status: 'ready',
          configured: true,
          enabled: true,
          base_url: 'http://127.0.0.1:8020',
          capabilities: [{
            capability_id: 'knowledge.rag.retrieve',
            status: 'ready',
            invocation_boundary: 'explicit_only'
          }],
          boundaries: {
            graphrag_execution: 'gated'
          }
        }]
      }
    })

    const wrapper = mount(ProviderOnboardingPanel)
    await flushPromises()

    expect(wrapper.text()).toContain('unifiedKnowledgeProvider')
    expect(wrapper.text()).toContain('ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER')
    expect(wrapper.text()).toContain('knowledge.rag.retrieve')
    expect(wrapper.text()).toContain('run_live_service_provider_probe')
    expect(wrapper.text()).toContain('/api/service-providers/unifiedKnowledgeProvider/evidence-preview')
    expect(wrapper.text()).toContain('default_chat_grounding: disabled')
    expect(wrapper.text()).toContain('graphrag_execution: gated')
    expect(wrapper.text()).not.toContain('测试能力')
    expect(wrapper.text()).not.toContain('提交')
  })

  it('keeps onboarding entry visible when live provider is missing', async () => {
    apiMocks.providerOnboardingApi.list.mockResolvedValue({
      data: {
        entries: [{
          onboarding_id: 'document-vlm-provider',
          provider_id: 'documentVlmProvider',
          kind: 'vlm',
          default_base_url: 'http://127.0.0.1:8082',
          capability_ids: ['document.vlm.parse'],
          env: {}
        }]
      }
    })
    apiMocks.providerOnboardingApi.readiness.mockResolvedValue({
      data: {
        onboarding_id: 'document-vlm-provider',
        configuration_status: 'unconfigured',
        recommended_action: 'configure_required_provider_environment',
        checks: []
      }
    })
    apiMocks.serviceProviderApi.list.mockResolvedValue({ data: { providers: [] } })

    const wrapper = mount(ProviderOnboardingPanel)
    await flushPromises()

    expect(wrapper.text()).toContain('documentVlmProvider')
    expect(wrapper.text()).toContain('not_registered')
    expect(wrapper.text()).toContain('当前 service-provider 管理列表中未注册该 Provider')
  })
})
