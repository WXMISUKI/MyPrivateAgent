import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import MessageList from '../MessageList.vue'

function buildProps(overrides = {}) {
  return {
    messages: [],
    isLoading: false,
    expandedThinking: {},
    feedbackReasons: [],
    feedbackReasonSelections: {},
    isFeedbackSubmitting: () => false,
    isNegativePanelOpen: () => false,
    feedbackCommentFor: () => '',
    feedbackErrorFor: () => '',
    messageKey: (message, index) => String(message?.id ?? index),
    ...overrides
  }
}

describe('MessageList', () => {
  it('renders no message items when there are no messages', () => {
    const wrapper = mount(MessageList, {
      props: buildProps(),
      global: {
        stubs: {
          ChatMessageItem: {
            name: 'ChatMessageItem',
            template: '<div class="chat-message-item-stub"></div>'
          }
        }
      }
    })

    expect(wrapper.findAll('.chat-message-item-stub')).toHaveLength(0)
  })

  it('renders message items for message list', () => {
    const wrapper = mount(MessageList, {
      props: buildProps({
        messages: [
          { id: 1, role: 'user', content: '你好', timestamp: Date.now() },
          { id: 2, role: 'assistant', content: '你好，我可以帮你什么？', timestamp: Date.now() }
        ]
      }),
      global: {
        stubs: {
          ChatMessageItem: {
            name: 'ChatMessageItem',
            template: '<div class="chat-message-item-stub"></div>'
          }
        }
      }
    })

    expect(wrapper.findAll('.chat-message-item-stub')).toHaveLength(2)
  })
})
