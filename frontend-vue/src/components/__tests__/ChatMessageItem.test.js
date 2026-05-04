import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const { pushMock } = vi.hoisted(() => ({
  pushMock: vi.fn()
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: pushMock })
}))
import ChatMessageItem from '../chat/ChatMessageItem.vue'

function mountMessage(message) {
  return mount(ChatMessageItem, {
    props: {
      message,
      index: 0,
      expandedThinking: {},
      feedbackReasons: [],
      isFeedbackSubmitting: false,
      isNegativePanelOpen: false,
      selectedReasons: [],
      feedbackComment: '',
      feedbackError: '',
    },
    global: {
      stubs: {
        MessageTextRenderer: true,
        AgentRuntimeDebugPanel: true,
        AgentStructuredCard: true
      }
    }
  })
}

describe('ChatMessageItem', () => {
  beforeEach(() => {
    pushMock.mockReset()
  })

  it('shows feedback learning bridge details on assistant messages', () => {
    const wrapper = mountMessage({
      id: 1,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      feedback: {
        type: 'negative',
        runtime_scope: 'chat',
        created_learning_id: 'LRN-20260503-ABC',
        metadata: {
          selected_count: 2,
          prompt_keys: ['prompt-a'],
          practice_ids: ['practice-1']
        }
      }
    })

    expect(wrapper.text()).toContain('反馈 / 学习闭环')
    expect(wrapper.text()).toContain('scope: chat')
    expect(wrapper.text()).toContain('命中: 2')
    expect(wrapper.text()).toContain('learning: LRN-20260503-ABC')
    expect(wrapper.text()).toContain('prompt: prompt-a')
    expect(wrapper.text()).toContain('practice: practice-1')
  })

  it('routes to the learning record from the feedback bridge', async () => {
    const wrapper = mountMessage({
      id: 1,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      feedback: {
        type: 'negative',
        runtime_scope: 'chat',
        created_learning_id: 'LRN-20260503-ABC',
        metadata: {}
      }
    })

    await wrapper.find('.bridge-link-btn').trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/learnings?tab=learnings&learning_id=LRN-20260503-ABC&source=user_feedback')
  })
})
