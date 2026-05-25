import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import CommandPalette from '../CommandPalette.vue'

vi.mock('../../api', () => ({
  commandApi: {
    list: vi.fn().mockResolvedValue({ data: [] })
  }
}))

async function mountPalette(props = {}) {
  const wrapper = mount(CommandPalette, {
    attachTo: document.body,
    props: {
      visible: true,
      ...props
    }
  })

  await nextTick()
  return wrapper
}

function getOverlay() {
  return document.body.querySelector('.command-palette-overlay')
}

function getInput() {
  return document.body.querySelector('.command-input')
}

function getCommandItems() {
  return Array.from(document.body.querySelectorAll('.command-item'))
}

afterEach(() => {
  localStorage.removeItem('governance_recent_snapshot_commands')
  document.body.innerHTML = ''
})

describe('CommandPalette', () => {
  it('renders the default command list when visible', async () => {
    const wrapper = await mountPalette()

    const items = getCommandItems()
    expect(items.length).toBeGreaterThanOrEqual(5)
    expect(document.body.textContent).toContain('/new')
    expect(document.body.textContent).toContain('/feedback')

    wrapper.unmount()
  })

  it('shows recent snapshot commands ahead of the base command list', async () => {
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
        copiedAt: '2026-05-03T01:00:00Z'
      }
    ]))

    const wrapper = await mountPalette()

    const items = getCommandItems()
    expect(document.body.textContent).toContain('最近治理快照')
    expect(document.body.textContent).toContain('全部命令')
    expect(items[0].textContent).toContain('/mcp snapshot MCP-REF-1')
    expect(items[0].textContent).toContain('最近')
    expect(items[0].textContent).toContain('MCP Probe 完成')
    expect(items[0].textContent).toContain('status=ok')

    wrapper.unmount()
  })

  it('filters commands by query and executes the selected command on enter', async () => {
    const wrapper = await mountPalette()
    const input = getInput()

    input.value = 'feed'
    input.dispatchEvent(new Event('input'))
    await nextTick()
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }))
    await nextTick()

    expect(wrapper.emitted('execute')).toHaveLength(1)
    expect(wrapper.emitted('execute')[0][0]).toMatchObject({
      id: 'feedback',
      action: 'open_feedback_analytics'
    })
    expect(wrapper.emitted('close')).toHaveLength(1)

    wrapper.unmount()
  })

  it('supports keyboard navigation before executing a command', async () => {
    const wrapper = await mountPalette()
    const input = getInput()

    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown' }))
    await nextTick()
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }))
    await nextTick()

    expect(wrapper.emitted('execute')).toHaveLength(1)
    expect(wrapper.emitted('execute')[0][0]).toMatchObject({
      id: 'clear',
      action: 'clear_conversation'
    })

    wrapper.unmount()
  })

  it('executes recent snapshot command suggestions with preset params', async () => {
    localStorage.setItem('governance_recent_snapshot_commands', JSON.stringify([
      {
        commandText: '/snapshot MCP-REF-1',
        commandName: 'snapshot',
        action: 'open_snapshot',
        params: ['MCP-REF-1'],
        domain: '',
        snapshotId: 'MCP-REF-1',
        eventLabel: 'Embedded Runtime Bootstrap 更新',
        summary: 'workspace_mode=memory_only · runtime=memory_preview',
        copiedAt: '2026-05-03T01:00:00Z'
      }
    ]))

    const wrapper = await mountPalette()
    const firstItem = getCommandItems()[0]
    firstItem.click()
    await nextTick()

    expect(wrapper.emitted('execute')).toHaveLength(1)
    expect(wrapper.emitted('execute')[0][0]).toMatchObject({
      params: ['MCP-REF-1']
    })

    wrapper.unmount()
  })

  it('finds recent snapshot commands by event label and summary text', async () => {
    localStorage.setItem('governance_recent_snapshot_commands', JSON.stringify([
      {
        commandText: '/snapshot RUNT-BOOT-321',
        commandName: 'snapshot',
        action: 'open_snapshot',
        params: ['RUNT-BOOT-321'],
        domain: 'runtime_control',
        snapshotId: 'RUNT-BOOT-321',
        eventLabel: 'Embedded Runtime Bootstrap 更新',
        summary: 'workspace_mode=memory_only · runtime=memory_preview',
        copiedAt: '2026-05-03T01:00:00Z'
      }
    ]))

    const wrapper = await mountPalette()
    const input = getInput()

    input.value = 'memory_preview'
    input.dispatchEvent(new Event('input'))
    await nextTick()

    let items = getCommandItems()
    expect(items).toHaveLength(1)
    expect(items[0].textContent).toContain('/snapshot RUNT-BOOT-321')

    input.value = 'bootstrap'
    input.dispatchEvent(new Event('input'))
    await nextTick()

    items = getCommandItems()
    expect(items).toHaveLength(1)
    expect(items[0].textContent).toContain('Embedded Runtime Bootstrap 更新')

    wrapper.unmount()
  })

  it('closes on escape and overlay click', async () => {
    const wrapper = await mountPalette()
    const input = getInput()

    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await nextTick()

    expect(wrapper.emitted('close')).toHaveLength(1)

    await wrapper.setProps({ visible: true })
    await nextTick()
    const overlay = getOverlay()
    overlay.click()
    await nextTick()

    expect(wrapper.emitted('close')).toHaveLength(2)

    wrapper.unmount()
  })
})
