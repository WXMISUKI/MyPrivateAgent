import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import AppSidebar from '../AppSidebar.vue'

describe('AppSidebar', () => {
  it('exposes a dedicated Workflow Lab entry separate from chat actions', async () => {
    const wrapper = mount(AppSidebar, {
      props: {
        conversations: [],
        activeConversationId: null,
        collapsed: false
      }
    })

    await wrapper.findAll('.footer-btn')[1].trigger('click')

    expect(wrapper.emitted('open-workflow-lab')).toBeTruthy()
  })
})
