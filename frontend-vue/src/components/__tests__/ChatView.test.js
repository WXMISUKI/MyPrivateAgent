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

describe('ChatView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    pushMock.mockReset()
  })

  it('renders health alert banner when failover alert level is high', async () => {
    const wrapper = mount(ChatView, {
      global: {
        stubs: {
          CommandPalette: true,
          MessageList: true,
          PlannerPanel: true
        }
      }
    })

    await flushPromises()
    expect(wrapper.text()).toContain('Provider Failover 高风险')
  })

  it('does not render alert banner when muteHealthAlerts is enabled', async () => {
    const settingsStore = useSettingsStore()
    settingsStore.setMuteHealthAlerts(true)

    const wrapper = mount(ChatView, {
      global: {
        stubs: {
          CommandPalette: true,
          MessageList: true,
          PlannerPanel: true
        }
      }
    })

    await flushPromises()
    expect(wrapper.text()).not.toContain('Provider Failover 高风险')
  })

  it('routes doctor governance slash command to governance doctor panel', async () => {
    const wrapper = mount(ChatView, {
      global: {
        stubs: {
          CommandPalette: true,
          MessageList: true,
          PlannerPanel: true
        }
      }
    })

    await flushPromises()
    await wrapper.find('textarea').setValue('/doctor governance')
    await wrapper.find('textarea').trigger('keydown.enter')

    expect(pushMock).toHaveBeenCalledWith('/settings?tab=advanced&doctor=governance')
  })

  it('routes doctor governance warning slash command to doctor warning view', async () => {
    const wrapper = mount(ChatView, {
      global: {
        stubs: {
          CommandPalette: true,
          MessageList: true,
          PlannerPanel: true
        }
      }
    })

    await flushPromises()
    await wrapper.find('textarea').setValue('/doctor governance warning')
    await wrapper.find('textarea').trigger('keydown.enter')

    expect(pushMock).toHaveBeenCalledWith('/settings?tab=advanced&doctor=governance&governance_severity=warning')
  })

  it('routes permissions warning slash command to governance warning view', async () => {
    const wrapper = mount(ChatView, {
      global: {
        stubs: {
          CommandPalette: true,
          MessageList: true,
          PlannerPanel: true
        }
      }
    })

    await flushPromises()
    await wrapper.find('textarea').setValue('/permissions warning')
    await wrapper.find('textarea').trigger('keydown.enter')

    expect(pushMock).toHaveBeenCalledWith('/settings?tab=advanced&governance_filter=permission&governance_severity=warning')
  })

  it('routes gaps slash command to governance domain view by default', async () => {
    const wrapper = mount(ChatView, {
      global: {
        stubs: {
          CommandPalette: true,
          MessageList: true,
          PlannerPanel: true
        }
      }
    })

    await flushPromises()
    await wrapper.find('textarea').setValue('/gaps')
    await wrapper.find('textarea').trigger('keydown.enter')

    expect(pushMock).toHaveBeenCalledWith('/settings?tab=advanced&governance_filter=governance')
  })

  it('routes snapshot slash command to governance snapshot view', async () => {
    const wrapper = mount(ChatView, {
      global: {
        stubs: {
          CommandPalette: true,
          MessageList: true,
          PlannerPanel: true
        }
      }
    })

    await flushPromises()
    await wrapper.find('textarea').setValue('/snapshot MCP-REF-1')
    await wrapper.find('textarea').trigger('keydown.enter')

    expect(pushMock).toHaveBeenCalledWith('/settings?tab=advanced&governance_snapshot=MCP-REF-1')
  })

  it('routes mcp snapshot slash command to domain-scoped governance snapshot view', async () => {
    const wrapper = mount(ChatView, {
      global: {
        stubs: {
          CommandPalette: true,
          MessageList: true,
          PlannerPanel: true
        }
      }
    })

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
        copiedAt: '2026-05-03T10:00:00Z'
      }
    ]))

    const wrapper = mount(ChatView, {
      global: {
        stubs: {
          CommandPalette: true,
          MessageList: true,
          PlannerPanel: true
        }
      }
    })

    await flushPromises()
    await wrapper.find('textarea').setValue('/help')
    await wrapper.find('textarea').trigger('keydown.enter')

    expect(wrapper.find('textarea').element.value).toContain('最近治理快照命令')
    expect(wrapper.find('textarea').element.value).toContain('/mcp snapshot MCP-REF-1')

    localStorage.removeItem('governance_recent_snapshot_commands')
  })
})
