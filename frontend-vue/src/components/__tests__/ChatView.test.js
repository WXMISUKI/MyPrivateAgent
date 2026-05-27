import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { mount, flushPromises } from '@vue/test-utils'

const { pushMock } = vi.hoisted(() => ({
  pushMock: vi.fn()
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: pushMock }),
  useRoute: () => ({ query: {} })
}))

vi.mock('axios', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: [] })
  }
}))

vi.mock('../../api', () => ({
  healthApi: {
    getHealth: vi.fn().mockResolvedValue({
      data: {
        failover: {
          alert_level: 'high'
        }
      }
    })
  }
}))

import ChatView from '../../views/ChatView.vue'
import { useSettingsStore } from '../../stores/settings'

function mountChatView() {
  return mount(ChatView, {
    global: {
      stubs: {
        CommandPalette: true,
        MessageList: true,
        PlannerPanel: true
      }
    }
  })
}

function installSpeechRecognitionMock() {
  const instances = []
  class SpeechRecognitionMock {
    constructor() {
      this.lang = ''
      this.continuous = false
      this.interimResults = false
      this.start = vi.fn()
      this.stop = vi.fn()
      this.abort = vi.fn()
      instances.push(this)
    }
  }
  window.SpeechRecognition = SpeechRecognitionMock
  return instances
}

function buildSpeechResult(transcript, isFinal) {
  return {
    0: { transcript },
    isFinal,
    length: 1
  }
}

describe('ChatView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    pushMock.mockReset()
    delete window.SpeechRecognition
    delete window.webkitSpeechRecognition
  })

  it('renders health alert banner when failover alert level is high', async () => {
    const wrapper = mountChatView()

    await flushPromises()
    expect(wrapper.text()).toContain('Provider Failover 高风险')
  })

  it('does not render alert banner when muteHealthAlerts is enabled', async () => {
    const settingsStore = useSettingsStore()
    settingsStore.setMuteHealthAlerts(true)

    const wrapper = mountChatView()

    await flushPromises()
    expect(wrapper.text()).not.toContain('Provider Failover 高风险')
  })

  it('toggles runtime trace expert switch through settings store', async () => {
    const settingsStore = useSettingsStore()
    const wrapper = mountChatView()

    await flushPromises()
    const toggle = wrapper.find('.runtime-trace-toggle input')
    expect(settingsStore.enableMainChatRuntimeTrace).toBe(false)

    await toggle.setValue(true)

    expect(settingsStore.enableMainChatRuntimeTrace).toBe(true)
    expect(wrapper.text()).toContain('已附加 main_chat runtime trace 上下文')
  })

  it('routes doctor governance slash command to governance doctor panel', async () => {
    const wrapper = mountChatView()

    await flushPromises()
    await wrapper.find('textarea').setValue('/doctor governance')
    await wrapper.find('textarea').trigger('keydown.enter')

    expect(pushMock).toHaveBeenCalledWith('/settings?tab=advanced&doctor=governance')
  })

  it('routes doctor governance warning slash command to doctor warning view', async () => {
    const wrapper = mountChatView()

    await flushPromises()
    await wrapper.find('textarea').setValue('/doctor governance warning')
    await wrapper.find('textarea').trigger('keydown.enter')

    expect(pushMock).toHaveBeenCalledWith('/settings?tab=advanced&doctor=governance&governance_severity=warning')
  })

  it('routes permissions warning slash command to governance warning view', async () => {
    const wrapper = mountChatView()

    await flushPromises()
    await wrapper.find('textarea').setValue('/permissions warning')
    await wrapper.find('textarea').trigger('keydown.enter')

    expect(pushMock).toHaveBeenCalledWith('/settings?tab=advanced&governance_filter=permission&governance_severity=warning')
  })

  it('routes gaps slash command to governance domain view by default', async () => {
    const wrapper = mountChatView()

    await flushPromises()
    await wrapper.find('textarea').setValue('/gaps')
    await wrapper.find('textarea').trigger('keydown.enter')

    expect(pushMock).toHaveBeenCalledWith('/settings?tab=advanced&governance_filter=governance')
  })

  it('routes snapshot slash command to governance snapshot view', async () => {
    const wrapper = mountChatView()

    await flushPromises()
    await wrapper.find('textarea').setValue('/snapshot MCP-REF-1')
    await wrapper.find('textarea').trigger('keydown.enter')

    expect(pushMock).toHaveBeenCalledWith('/settings?tab=advanced&governance_snapshot=MCP-REF-1')
  })

  it('routes mcp snapshot slash command to domain-scoped governance snapshot view', async () => {
    const wrapper = mountChatView()

    await flushPromises()
    await wrapper.find('textarea').setValue('/mcp snapshot MCP-REF-1')
    await wrapper.find('textarea').trigger('keydown.enter')

    expect(pushMock).toHaveBeenCalledWith('/settings?tab=advanced&governance_filter=mcp&governance_snapshot=MCP-REF-1')
  })

  it('includes recent governance snapshot commands in help text', async () => {
    localStorage.setItem('governance_recent_snapshot_commands', JSON.stringify([
      {
        commandText: '/mcp snapshot MCP-REF-1',
        commandName: 'mcp',
        action: 'open_mcp',
        params: ['snapshot', 'MCP-REF-1'],
        domain: 'mcp',
        snapshotId: 'MCP-REF-1',
        eventLabel: 'MCP Probe 完成',
        summary: 'status=ok',
        copiedAt: '2026-05-03T10:00:00Z'
      }
    ]))

    const wrapper = mountChatView()

    await flushPromises()
    await wrapper.find('textarea').setValue('/help')
    await wrapper.find('textarea').trigger('keydown.enter')

    expect(wrapper.find('textarea').element.value).toContain('最近治理快照命令')
    expect(wrapper.find('textarea').element.value).toContain('/mcp snapshot MCP-REF-1')
    expect(wrapper.find('textarea').element.value).toContain('事件 MCP Probe 完成')
    expect(wrapper.find('textarea').element.value).toContain('摘要 status=ok')

    localStorage.removeItem('governance_recent_snapshot_commands')
  })

  it('starts browser speech recognition from the microphone button', async () => {
    const speechInstances = installSpeechRecognitionMock()
    const wrapper = mountChatView()

    await flushPromises()
    const voiceButton = wrapper.find('.voice-input-btn')
    await voiceButton.trigger('click')

    expect(speechInstances).toHaveLength(1)
    expect(speechInstances[0].lang).toBe('zh-CN')
    expect(speechInstances[0].continuous).toBe(true)
    expect(speechInstances[0].interimResults).toBe(true)
    expect(speechInstances[0].start).toHaveBeenCalled()
    expect(wrapper.text()).toContain('正在听写')
  })

  it('writes interim and final speech transcripts into the textarea', async () => {
    const speechInstances = installSpeechRecognitionMock()
    const wrapper = mountChatView()

    await flushPromises()
    await wrapper.find('textarea').setValue('请帮我')
    await wrapper.find('.voice-input-btn').trigger('click')

    speechInstances[0].onresult({
      resultIndex: 0,
      results: [buildSpeechResult('查询天气', false)]
    })
    await flushPromises()
    expect(wrapper.find('textarea').element.value).toBe('请帮我 查询天气')

    speechInstances[0].onresult({
      resultIndex: 0,
      results: [buildSpeechResult('查询天气', true)]
    })
    await flushPromises()
    expect(wrapper.find('textarea').element.value).toBe('请帮我 查询天气')
  })

  it('stops active speech recognition when clicking the microphone button again', async () => {
    const speechInstances = installSpeechRecognitionMock()
    const wrapper = mountChatView()

    await flushPromises()
    await wrapper.find('.voice-input-btn').trigger('click')
    await wrapper.find('.voice-input-btn').trigger('click')

    expect(speechInstances[0].stop).toHaveBeenCalled()
  })

  it('disables voice input when speech recognition is unsupported', async () => {
    const wrapper = mountChatView()

    await flushPromises()
    const voiceButton = wrapper.find('.voice-input-btn')

    expect(voiceButton.attributes('disabled')).toBeDefined()
    await wrapper.find('textarea').setValue('手动输入仍可使用')
    expect(wrapper.find('textarea').element.value).toBe('手动输入仍可使用')
  })
})
