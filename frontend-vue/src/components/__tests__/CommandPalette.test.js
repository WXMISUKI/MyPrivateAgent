import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { nextTick } from 'vue'
import CommandPalette from '../CommandPalette.vue'

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

describe('CommandPalette', () => {
  it('renders the default command list when visible', async () => {
    const wrapper = await mountPalette()

    const items = getCommandItems()
    expect(items.length).toBeGreaterThanOrEqual(5)
    expect(document.body.textContent).toContain('/new')
    expect(document.body.textContent).toContain('/feedback')

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
