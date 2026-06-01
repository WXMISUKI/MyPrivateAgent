import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const { listMock, heartbeatMock, testMock, invokeMock } = vi.hoisted(() => ({
  listMock: vi.fn(),
  heartbeatMock: vi.fn(),
  testMock: vi.fn(),
  invokeMock: vi.fn()
}))

vi.mock('../../api', () => ({
  capabilityApi: {
    list: listMock,
    heartbeat: heartbeatMock,
    test: testMock,
    invoke: invokeMock
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
    invokeMock.mockReset()
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

  it('shows OCR validation error when no file is selected', async () => {
    listMock.mockResolvedValueOnce({
      data: {
        capabilities: [
          {
            capability_id: 'document.ocr.extract',
            kind: 'ocr',
            provider: 'paddleocr',
            transport: 'http',
            status: 'ready',
            reason: ''
          }
        ]
      }
    })
    const wrapper = mount(CapabilityProviderDiagnosticsPanel)
    await flushPromises()

    expect(wrapper.find('[data-test="ocr-invoke"]').exists()).toBe(true)
    await wrapper.find('[data-test="ocr-invoke"]').trigger('click')
    await flushPromises()

    expect(invokeMock).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('请先选择 OCR 文件')
  })

  it('renders provider circuit breaker state from heartbeat', async () => {
    heartbeatMock.mockResolvedValueOnce({
      data: {
        providers: [
          {
            provider_id: 'unifiedTTSandASR',
            status: 'unreachable',
            base_url: 'http://127.0.0.1:8010',
            reason: 'heartbeat circuit opened',
            circuit_breaker: {
              state: 'open',
              failure_count: 3,
              retry_after_seconds: 12.34
            },
            capabilities: [{ capability_id: 'voice.tts.edge', status: 'unreachable' }]
          }
        ]
      }
    })
    const wrapper = mount(CapabilityProviderDiagnosticsPanel)
    await flushPromises()

    expect(wrapper.text()).toContain('circuit: open')
    expect(wrapper.text()).toContain('failures: 3')
    expect(wrapper.text()).toContain('retry in 12.34s')
  })

  it('renders OCR structured result sections', async () => {
    listMock.mockResolvedValueOnce({
      data: {
        capabilities: [
          {
            capability_id: 'document.ocr.extract',
            kind: 'ocr',
            provider: 'paddleocr',
            transport: 'http',
            status: 'ready',
            reason: ''
          }
        ]
      }
    })
    const wrapper = mount(CapabilityProviderDiagnosticsPanel)
    await flushPromises()

    wrapper.vm.testResults['document.ocr.extract'] = {
      ok: true,
      result: {
        text: 'hello world',
        pages: [{ page_number: 1, text: 'hello world', confidence: 0.98 }],
        blocks: [{ block_id: 'p1-b1', text: 'hello world', confidence: 0.98, bbox: [1, 2, 3, 4] }],
        warnings: ['low quality image'],
        raw: { ocrResults: [] }
      }
    }
    await nextTick()

    expect(wrapper.text()).toContain('文本长度: 11')
    expect(wrapper.text()).toContain('warning: low quality image')
    expect(wrapper.text()).toContain('Blocks / 置信度')
    expect(wrapper.text()).toContain('Raw JSON')
  })

  it('shows layout validation error when no file is selected', async () => {
    listMock.mockResolvedValueOnce({
      data: {
        capabilities: [
          {
            capability_id: 'document.layout.parse',
            kind: 'layout',
            provider: 'paddleocr',
            transport: 'http',
            status: 'ready',
            reason: ''
          }
        ]
      }
    })
    const wrapper = mount(CapabilityProviderDiagnosticsPanel)
    await flushPromises()

    expect(wrapper.find('[data-test="layout-invoke"]').exists()).toBe(true)
    await wrapper.find('[data-test="layout-invoke"]').trigger('click')
    await flushPromises()

    expect(invokeMock).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('请先选择 Layout 文件')
  })

  it('renders layout structured result sections', async () => {
    listMock.mockResolvedValueOnce({
      data: {
        capabilities: [
          {
            capability_id: 'document.layout.parse',
            kind: 'layout',
            provider: 'paddleocr',
            transport: 'http',
            status: 'ready',
            reason: ''
          }
        ]
      }
    })
    const wrapper = mount(CapabilityProviderDiagnosticsPanel)
    await flushPromises()

    wrapper.vm.testResults['document.layout.parse'] = {
      ok: true,
      result: {
        markdown: '# Doc',
        elements: [{ type: 'title' }],
        tables: [{ rows: 2 }],
        warnings: ['small font'],
        raw: { pages: 1 }
      }
    }
    await nextTick()

    expect(wrapper.text()).toContain('Markdown 长度: 5')
    expect(wrapper.text()).toContain('warning: small font')
    expect(wrapper.text()).toContain('Tables')
    expect(wrapper.text()).toContain('Raw JSON')
  })

  it('invokes layout capability with configured payload fields', async () => {
    listMock.mockResolvedValueOnce({
      data: {
        capabilities: [
          {
            capability_id: 'document.layout.parse',
            kind: 'layout',
            provider: 'paddleocr',
            transport: 'http',
            status: 'ready',
            reason: ''
          }
        ]
      }
    })
    invokeMock.mockResolvedValue({
      data: { ok: true, result: { markdown: '', elements: [], tables: [], pages: [], warnings: [], raw: {} } }
    })
    const wrapper = mount(CapabilityProviderDiagnosticsPanel)
    await flushPromises()

    const file = new File([new Uint8Array([65, 66, 67])], 'layout.pdf', { type: 'application/pdf' })
    file.arrayBuffer = async () => new Uint8Array([65, 66, 67]).buffer
    const fileInput = wrapper.find('input[type="file"]')
    Object.defineProperty(fileInput.element, 'files', {
      value: [file],
      configurable: true
    })
    await fileInput.trigger('change')

    const select = wrapper.find('select')
    await select.setValue('json')
    const numberInput = wrapper.find('input[type="number"]')
    await numberInput.setValue('7')
    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    await checkboxes[0].setValue(false)
    await checkboxes[1].setValue(false)

    await wrapper.find('[data-test="layout-invoke"]').trigger('click')
    await flushPromises()

    expect(invokeMock).toHaveBeenCalledTimes(1)
    const [, payload] = invokeMock.mock.calls[0]
    expect(payload.media_type).toBe('application/pdf')
    expect(payload.output_format).toBe('json')
    expect(payload.include_tables).toBe(false)
    expect(payload.include_layout).toBe(false)
    expect(payload.max_pages).toBe(7)
  })

  it('shows VLM validation error when no file is selected', async () => {
    listMock.mockResolvedValueOnce({
      data: {
        capabilities: [
          {
            capability_id: 'document.vlm.parse',
            kind: 'vlm',
            provider: 'document_vlm_provider',
            transport: 'http',
            status: 'ready',
            reason: ''
          }
        ]
      }
    })
    const wrapper = mount(CapabilityProviderDiagnosticsPanel)
    await flushPromises()

    expect(wrapper.find('[data-test="vlm-invoke"]').exists()).toBe(true)
    await wrapper.find('[data-test="vlm-invoke"]').trigger('click')
    await flushPromises()

    expect(invokeMock).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('请先选择 VLM 文件')
  })

  it('renders VLM structured result sections', async () => {
    listMock.mockResolvedValueOnce({
      data: {
        capabilities: [
          {
            capability_id: 'document.vlm.parse',
            kind: 'vlm',
            provider: 'document_vlm_provider',
            transport: 'http',
            status: 'ready',
            reason: ''
          }
        ]
      }
    })
    const wrapper = mount(CapabilityProviderDiagnosticsPanel)
    await flushPromises()

    wrapper.vm.testResults['document.vlm.parse'] = {
      ok: true,
      result: {
        summary: 'contract summary',
        sections: [{ title: 'intro' }],
        answers: [{ key: 'buyer', value: 'Acme' }],
        evidence: [{ page: 1 }],
        warnings: ['low resolution'],
        raw: { model: 'vlm-x' }
      }
    }
    await nextTick()

    expect(wrapper.text()).toContain('Summary 长度: 16')
    expect(wrapper.text()).toContain('warning: low resolution')
    expect(wrapper.text()).toContain('Answers')
    expect(wrapper.text()).toContain('Raw JSON')
  })
})
