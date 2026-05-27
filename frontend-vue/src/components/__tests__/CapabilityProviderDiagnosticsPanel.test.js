import { mount, flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const { listMock, heartbeatMock, testMock } = vi.hoisted(() => ({
  listMock: vi.fn(),
  heartbeatMock: vi.fn(),
  testMock: vi.fn()
}))

vi.mock('../../api', () => ({
  capabilityApi: {
    list: listMock,
    heartbeat: heartbeatMock,
    test: testMock
  }
}))

import CapabilityProviderDiagnosticsPanel from '../CapabilityProviderDiagnosticsPanel.vue'

describe('CapabilityProviderDiagnosticsPanel', () => {
  beforeEach(() => {
    vi.stubGlobal('atob', (value) => Buffer.from(value, 'base64').toString('binary'))
    if (!URL.createObjectURL) {
      URL.createObjectURL = vi.fn(() => 'blob:capability-test')
    }
    if (!URL.revokeObjectURL) {
      URL.revokeObjectURL = vi.fn()
    }
    listMock.mockReset()
    heartbeatMock.mockReset()
    testMock.mockReset()
    listMock.mockResolvedValue({
      data: {
        capabilities: [
          {
            capability_id: 'voice.tts.edge',
            kind: 'tts',
            provider: 'edge_tts',
            transport: 'http',
            status: 'ready',
            reason: ''
          }
        ]
      }
    })
    heartbeatMock.mockResolvedValue({
      data: {
        providers: [
          {
            provider_id: 'unifiedTTSandASR',
            status: 'ok',
            base_url: 'http://127.0.0.1:8010',
            capabilities: [{ capability_id: 'voice.tts.edge', status: 'ready' }]
          }
        ]
      }
    })
  })

  it('loads capabilities and heartbeat on mount', async () => {
    const wrapper = mount(CapabilityProviderDiagnosticsPanel)

    await flushPromises()

    expect(listMock).toHaveBeenCalledOnce()
    expect(heartbeatMock).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('voice.tts.edge')
    expect(wrapper.text()).toContain('unifiedTTSandASR')
  })

  it('runs a capability test and displays tts summary', async () => {
    testMock.mockResolvedValue({
      data: {
        ok: true,
        capability_id: 'voice.tts.edge',
        status: 'ok',
        latency_ms: 12,
        result_summary: {
          media_type: 'audio/mpeg',
          audio_base64_length: 8,
          audio_base64: 'QUJDRA=='
        }
      }
    })
    const wrapper = mount(CapabilityProviderDiagnosticsPanel)

    await flushPromises()
    await wrapper.find('[data-test="capability-test"]').trigger('click')
    await flushPromises()

    expect(testMock).toHaveBeenCalledWith('voice.tts.edge', { payload: {}, mode: 'default' })
    expect(wrapper.text()).toContain('测试通过')
    expect(wrapper.find('audio').exists()).toBe(true)
  })

  it('displays structured test errors', async () => {
    testMock.mockRejectedValue({
      response: {
        data: {
          error: {
            code: 'CAPABILITY_PROVIDER_UNREACHABLE',
            message: 'provider down'
          }
        }
      }
    })
    const wrapper = mount(CapabilityProviderDiagnosticsPanel)

    await flushPromises()
    await wrapper.find('[data-test="capability-test"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('CAPABILITY_PROVIDER_UNREACHABLE')
  })
})
