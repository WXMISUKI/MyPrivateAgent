import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ChatMessageItem from '../ChatMessageItem.vue'

function mountMessageItem(message, overrides = {}) {
  return mount(ChatMessageItem, {
    props: {
      message,
      index: 0,
      expandedThinking: {},
      feedbackReasons: [
        { id: 'incorrect', label: '内容不正确' },
        { id: 'other', label: '其他问题' }
      ],
      isFeedbackSubmitting: false,
      isNegativePanelOpen: false,
      selectedReasons: [],
      feedbackComment: '',
      feedbackError: '',
      ...overrides
    },
    global: {
      stubs: {
        MessageTextRenderer: {
          name: 'MessageTextRenderer',
          props: ['content'],
          template: '<div class="message-text-renderer">{{ content }}</div>'
        },
        AgentRuntimeDebugPanel: {
          name: 'AgentRuntimeDebugPanel',
          template: '<div class="runtime-debug-stub"></div>'
        },
        AgentStructuredCard: {
          name: 'AgentStructuredCard',
          template: '<div class="structured-card-stub"></div>'
        }
      }
    }
  })
}

describe('ChatMessageItem', () => {
  it('renders assistant content and feedback actions', () => {
    const wrapper = mountMessageItem({
      id: 101,
      role: 'assistant',
      content: '测试回复',
      timestamp: Date.now()
    })

    expect(wrapper.text()).toContain('测试回复')
    expect(wrapper.findAll('.action-btn')).toHaveLength(4)
  })

  it('renders tool call result block', async () => {
    const wrapper = mountMessageItem({
      id: 102,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      toolCalls: [
        {
          id: 'tool_1',
          name: 'weather_lookup',
          status: 'completed',
          args: { city: 'Shanghai' },
          result: '晴天'
        }
      ]
    })

    expect(wrapper.text()).toContain('工具调用')
    expect(wrapper.text()).toContain('已调用 1 个工具，点击查看详情')
    expect(wrapper.find('.tool-calls-box').attributes('open')).toBeUndefined()
    expect(wrapper.text()).not.toContain('weather_lookup')
    expect(wrapper.text()).not.toContain('晴天')

    await wrapper.find('.tool-calls-header').trigger('click')
    expect(wrapper.text()).toContain('weather_lookup')
    expect(wrapper.text()).toContain('晴天')
  })

  it('renders visible execution progress summary for assistant messages', () => {
    const wrapper = mountMessageItem({
      id: 105,
      role: 'assistant',
      content: '最终回答',
      timestamp: Date.now(),
      executionProgress: [
        { phase: 'intent_routing', content: '正在识别你的复合需求。' },
        { phase: 'tool_execution', content: '正在检索天气和交通信息。' }
      ]
    })

    expect(wrapper.text()).toContain('执行摘要')
    expect(wrapper.text()).toContain('正在识别你的复合需求。')
    expect(wrapper.text()).toContain('正在检索天气和交通信息。')
  })

  it('shows submitted feedback summary', () => {
    const wrapper = mountMessageItem({
      id: 103,
      role: 'assistant',
      content: '测试反馈',
      timestamp: Date.now(),
      feedback: {
        type: 'negative',
        runtime_scope: 'conversation',
        created_learning_id: 12,
        metadata: {
          selected_reasons: ['incorrect', 'other']
        }
      }
    })

    expect(wrapper.text()).toContain('反馈已记录')
    expect(wrapper.text()).toContain('点踩')
    expect(wrapper.text()).toContain('内容不正确')
  })

  it('hides duplicated raw text when assistant message is a structured card', () => {
    const wrapper = mount(ChatMessageItem, {
      props: {
        message: {
          id: 104,
          role: 'assistant',
          content: '{"city":"Shanghai"}',
          timestamp: Date.now(),
          renderMode: 'structured_card',
          cardSchema: 'weather.v1',
          cardData: {
            city: 'Shanghai',
            current: {
              weather: '晴',
              temperature: '26C',
              wind_speed: '3级',
              wind_direction: '东南风'
            }
          }
        },
        index: 0,
        expandedThinking: {},
        feedbackReasons: [],
        isFeedbackSubmitting: false,
        isNegativePanelOpen: false,
        selectedReasons: [],
        feedbackComment: '',
        feedbackError: ''
      },
      global: {
        stubs: {
          MessageTextRenderer: {
            name: 'MessageTextRenderer',
            props: ['content'],
            template: '<div class="message-text-renderer">{{ content }}</div>'
          },
          AgentRuntimeDebugPanel: {
            name: 'AgentRuntimeDebugPanel',
            template: '<div class="runtime-debug-stub"></div>'
          },
          AgentStructuredCard: {
            name: 'AgentStructuredCard',
            props: ['card'],
            template: '<div class="structured-card-stub">{{ card.city }}</div>'
          }
        }
      }
    })

    expect(wrapper.find('.structured-card-stub').exists()).toBe(true)
    expect(wrapper.text()).toContain('Shanghai')
    expect(wrapper.find('.message-text-renderer').exists()).toBe(false)
  })
})
