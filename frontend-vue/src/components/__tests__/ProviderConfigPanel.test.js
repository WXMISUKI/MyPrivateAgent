import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

vi.mock('../../api', () => ({
  providerApi: {
    list: vi.fn(),
    update: vi.fn(),
    test: vi.fn()
  }
}))

import ProviderConfigPanel from '../ProviderConfigPanel.vue'
import { providerApi } from '../../api'

describe('ProviderConfigPanel', () => {
  beforeEach(() => {
    providerApi.list.mockResolvedValue({
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
    })
    providerApi.update.mockResolvedValue({ data: { status: 'saved', config_source: 'local_override' } })
    providerApi.test.mockResolvedValue({
      data: {
        status: 'ok',
        message: '连接成功，发现 3 个模型',
        model_count: 3,
        latency_ms: 12
      }
    })
  })

  it('renders provider config entries and saves explicit changes', async () => {
    const wrapper = mount(ProviderConfigPanel)

    await flushPromises()

    expect(wrapper.text()).toContain('Provider 配置')
    expect(wrapper.text()).toContain('Ollama (本地)')
    expect(wrapper.text()).toContain('已配置')
    expect(providerApi.test).toHaveBeenCalledWith('ollama')

    const input = wrapper.find('input.field-input')
    await input.setValue('http://127.0.0.1:11435')
    await wrapper.find('button.save-btn').trigger('click')
    await flushPromises()

    expect(providerApi.update).toHaveBeenCalledWith('ollama', {
      base_url: 'http://127.0.0.1:11435'
    })
    expect(wrapper.text()).toContain('保存成功')
  })
})
