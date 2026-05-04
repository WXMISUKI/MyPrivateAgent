import { mount, flushPromises } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('../../api', () => ({
  runtimeSurfaceApi: {
    getProfile: vi.fn().mockResolvedValue({
      data: {
        auth_mode: 'demo_guest',
        default_model: 'doubao',
        models: [{ name: 'doubao', display_name: '豆包' }],
        providers: [],
        command_contract: {
          total_commands: 1,
          framework_commands: [{ id: 'snapshot', name: 'snapshot', description: '治理快照' }],
          governance_commands: []
        }
      }
    }),
    updateProfile: vi.fn().mockResolvedValue({ data: {} })
  }
}))

import RuntimeSurfacePanel from '../RuntimeSurfacePanel.vue'

afterEach(() => {
  localStorage.removeItem('governance_recent_snapshot_commands')
  document.body.innerHTML = ''
})

function mountPanel() {
  return mount(RuntimeSurfacePanel, {
    attachTo: document.body
  })
}

describe('RuntimeSurfacePanel', () => {
  it('renders recent governance snapshot commands from local storage', async () => {
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

    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).toContain('最近治理快照命令')
    expect(wrapper.text()).toContain('/mcp snapshot MCP-REF-1')
    expect(wrapper.text()).toContain('快照: MCP-REF-1')

    wrapper.unmount()
  })

  it('copies a recent governance snapshot command', async () => {
    localStorage.setItem('governance_recent_snapshot_commands', JSON.stringify([
      {
        commandText: '/snapshot MCP-REF-1',
        commandName: 'snapshot',
        action: 'open_snapshot',
        params: ['MCP-REF-1'],
        domain: '',
        snapshotId: 'MCP-REF-1',
        copiedAt: '2026-05-03T10:00:00Z'
      }
    ]))

    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText }
    })

    const wrapper = mountPanel()
    await flushPromises()

    await wrapper.get('.recent-copy-btn').trigger('click')
    await flushPromises()

    expect(writeText).toHaveBeenCalledWith('/snapshot MCP-REF-1')
    expect(wrapper.text()).toContain('最近复制：')

    wrapper.unmount()
  })
})
