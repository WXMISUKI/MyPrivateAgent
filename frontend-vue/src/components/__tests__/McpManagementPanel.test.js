import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

vi.mock('../../api', () => ({
  mcpApi: {
    listServers: vi.fn(),
    createServer: vi.fn(),
    updateServer: vi.fn(),
    deleteServer: vi.fn(),
    enableServer: vi.fn(),
    disableServer: vi.fn(),
    getCatalog: vi.fn(),
    probeServer: vi.fn(),
    handshakeServer: vi.fn(),
    callTool: vi.fn()
  }
}))

import McpManagementPanel from '../McpManagementPanel.vue'
import { useMcpStore } from '../../stores/mcp'

describe('McpManagementPanel', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders existing servers and capability catalog', async () => {
    const store = useMcpStore()
    store.catalog = {
      total_servers: 1,
      enabled_servers: 1,
      capabilities: [{ capability: 'filesystem.read', server_names: ['filesystem'] }]
    }
    store.servers = [{
      name: 'filesystem',
      display_name: 'Filesystem MCP',
      transport: 'stdio',
      command: 'cmd',
      args: ['/c', 'echo', 'hello'],
      enabled: true,
      capabilities: ['filesystem.read'],
      description: 'Read workspace files',
      metadata: {}
    }]
    store.refreshAll = vi.fn().mockResolvedValue(undefined)

    const wrapper = mount(McpManagementPanel)
    await nextTick()

    expect(wrapper.text()).toContain('MCP 服务管理')
    expect(wrapper.text()).toContain('Filesystem MCP')
    expect(wrapper.text()).toContain('filesystem.read')
  })

  it('submits create server form with normalized payload', async () => {
    const store = useMcpStore()
    store.catalog = { total_servers: 0, enabled_servers: 0, capabilities: [] }
    store.servers = []
    store.refreshAll = vi.fn().mockResolvedValue(undefined)
    store.createServer = vi.fn().mockResolvedValue(undefined)

    const wrapper = mount(McpManagementPanel)
    await nextTick()

    await wrapper.find('input[placeholder="filesystem"]').setValue('knowledge-base')
    await wrapper.find('input[placeholder="Filesystem MCP"]').setValue('Knowledge Base MCP')
    await wrapper.find('select').setValue('http')
    await wrapper.find('input[placeholder="http://localhost:9001/mcp"]').setValue('http://localhost:9001/mcp')
    await wrapper.find('input[placeholder="filesystem.read, search.query"]').setValue('search.query, docs.read')

    const textareas = wrapper.findAll('textarea')
    await textareas[0].setValue('Knowledge base server')
    await textareas[1].setValue('{"timeout_seconds": 10}')

    await wrapper.find('button.primary-btn').trigger('click')

    expect(store.createServer).toHaveBeenCalledWith({
      name: 'knowledge-base',
      display_name: 'Knowledge Base MCP',
      transport: 'http',
      command: null,
      args: [],
      url: 'http://localhost:9001/mcp',
      enabled: true,
      description: 'Knowledge base server',
      capabilities: ['search.query', 'docs.read'],
      tags: [],
      metadata: { timeout_seconds: 10 }
    })
  })
})
