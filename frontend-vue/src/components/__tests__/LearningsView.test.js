import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const { pushMock, routeState } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  routeState: {
    query: {}
  }
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: pushMock }),
  useRoute: () => routeState
}))

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn().mockResolvedValue({ data: {} })
  }
}))

import axios from 'axios'
import LearningsView from '../../views/LearningsView.vue'
import { useConversationStore } from '../../stores/conversation'

function mockLearningApis() {
  axios.get.mockImplementation((url) => {
    if (url.includes('/learnings/stats')) {
      return Promise.resolve({
        data: {
          total_learnings: 2,
          pending_learnings: 1,
          resolved_learnings: 1,
          reviewed_learnings: 1,
          average_quality_score: 4,
          disabled_learnings: 0,
          rolled_back_learnings: 0,
          total_errors: 0
        }
      })
    }
    if (url.includes('/learnings/errors')) {
      return Promise.resolve({ data: [] })
    }
    if (url.includes('/learnings/features')) {
      return Promise.resolve({ data: [] })
    }
    if (url.includes('/learnings/LRN-1/compare')) {
      return Promise.resolve({
        data: {
          learning_id: 'LRN-1',
          base_label: 'LVH-1',
          target_label: 'current',
          has_changes: true,
          changed_fields: [
            { field: 'review_status', before: 'approved', after: 'needs_changes' },
            { field: 'quality_score', before: '4', after: '3' }
          ]
        }
      })
    }
    if (url.includes('/learnings/LRN-1/history')) {
      return Promise.resolve({
        data: [
          {
            version_id: 'LVH-2',
            learning_id: 'LRN-1',
            event_type: 'review:needs_changes',
            status: 'pending',
            summary: 'Prompt A 触发的学习',
            change_note: 'needs more work',
            snapshot_ref: {
              snapshot_id: 'LEAR-APPLY-NA-20260503'
            },
            created_at: '2026-05-03T12:30:00Z'
          },
          {
            version_id: 'LVH-1',
            learning_id: 'LRN-1',
            event_type: 'review:approved',
            status: 'pending',
            summary: 'Prompt A 触发的学习',
            change_note: 'looks good',
            snapshot_ref: {
              snapshot_id: 'LEAR-REVIEW-NA-20260503'
            },
            created_at: '2026-05-03T12:10:00Z'
          }
        ]
      })
    }
    if (url.includes('/learnings')) {
      return Promise.resolve({
        data: [
          {
            learning_id: 'LRN-1',
            summary: 'Prompt A 触发的学习',
            details: '关联 user feedback',
            category: 'correction',
            priority: 'medium',
            status: 'pending',
            source: 'user_feedback',
            tags: ['prompt:prompt-a', 'practice:practice-1'],
            pattern_key: 'user_feedback:conversation:123',
            history_count: 2,
            conflict_flags: ['review_needs_changes', 'duplicate_pattern_key'],
            conflict_context: {
              duplicate_learning_ids: ['LRN-2']
            },
            latest_review: {
              review_id: 'LRV-1',
              review_status: 'approved',
              quality_score: 4,
              reviewer: 'reviewer-a',
              review_note: 'looks good',
              created_at: '2026-05-03T12:00:00Z'
            },
            created_at: '2026-05-03T10:00:00Z'
          },
          {
            learning_id: 'LRN-2',
            summary: '另一个学习',
            details: '不应命中当前筛选',
            category: 'insight',
            priority: 'low',
            status: 'resolved',
            source: 'conversation',
            tags: ['prompt:prompt-b'],
            pattern_key: 'conversation:other',
            history_count: 0,
            conflict_flags: [],
            conflict_context: {
              duplicate_learning_ids: []
            },
            created_at: '2026-05-02T10:00:00Z'
          }
        ]
      })
    }
    return Promise.resolve({ data: [] })
  })
}

describe('LearningsView', () => {
  beforeEach(() => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const conversationStore = useConversationStore()
    conversationStore.conversations = [{
      id: 321,
      title: 'trace test',
      modelName: 'doubao',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now()
    }]
    conversationStore.activeId = 321
    pushMock.mockReset()
    routeState.query = {}
    axios.get.mockReset()
    axios.post.mockReset()
    axios.post.mockResolvedValue({ data: {} })
    mockLearningApis()
  })

  it('applies route drill-down filters for user feedback learnings', async () => {
    routeState.query = {
      tab: 'learnings',
      source: 'user_feedback',
      tag: 'prompt:prompt-a',
      learning_id: 'LRN-1'
    }

    const wrapper = mount(LearningsView)
    await flushPromises()

    expect(wrapper.findAll('.learning-item')).toHaveLength(1)
    expect(wrapper.text()).toContain('LRN-1')
    expect(wrapper.text()).toContain('当前钻取')
    expect(wrapper.text()).toContain('来源: user_feedback')
    expect(wrapper.text()).toContain('Pattern: user_feedback:conversation:123')
    expect(wrapper.text()).toContain('prompt:prompt-a')
    expect(wrapper.text()).toContain('审核: approved')
    expect(wrapper.text()).toContain('质量: 4/5')
    expect(wrapper.text()).toContain('历史版本: 2')
    expect(wrapper.text()).toContain('审核需修改')
    expect(wrapper.text()).toContain('重复模式')
    expect(wrapper.text()).toContain('重复候选')
    expect(wrapper.text()).toContain('合并 LRN-2')
    expect(wrapper.text()).not.toContain('另一个学习')
  })

  it('clears drill-down filters back to the default learnings route', async () => {
    routeState.query = {
      tab: 'learnings',
      source: 'user_feedback',
      tag: 'prompt:prompt-a'
    }

    const wrapper = mount(LearningsView)
    await flushPromises()
    await wrapper.find('.clear-btn').trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/learnings?tab=learnings')
  })

  it('runs governance actions against the learning action routes', async () => {
    axios.post.mockResolvedValue({
      data: {
        snapshot_ref: {
          snapshot_id: 'LEAR-DISABLE-1'
        }
      }
    })
    const wrapper = mount(LearningsView)
    await flushPromises()

    const buttons = wrapper.findAll('.learning-action-btn')
    expect(buttons.some(item => item.text() === '禁用')).toBe(true)
    expect(buttons.some(item => item.text() === '提升')).toBe(true)

    const disableButton = buttons.find(item => item.text() === '禁用')
    await disableButton.trigger('click')
    await flushPromises()

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/learnings/LRN-1/disable'),
      expect.objectContaining({
        conversation_id: 321
      }),
      expect.any(Object)
    )
    expect(wrapper.text()).toContain('学习 LRN-1 已执行 disable (LEAR-DISABLE-1)')
  })

  it('submits a learning review through the governance review route', async () => {
    axios.post.mockImplementation((url, payload) => {
      if (url.includes('/review')) {
        return Promise.resolve({
          data: {
            review_id: 'LRV-2',
            learning_id: 'LRN-1',
            review_status: payload.review_status,
            quality_score: payload.quality_score,
            reviewer: 'tester',
            review_note: payload.review_note,
            snapshot_ref: {
              snapshot_id: 'LEAR-REVIEW-1'
            },
            created_at: '2026-05-03T12:30:00Z',
            updated_at: '2026-05-03T12:30:00Z'
          }
        })
      }
      return Promise.resolve({ data: {} })
    })

    const wrapper = mount(LearningsView)
    await flushPromises()

    const item = wrapper.findAll('.learning-item').find(node => node.text().includes('LRN-1'))
    const selects = item.findAll('select')
    await selects[0].setValue('needs_changes')
    await selects[1].setValue('3')
    await item.find('.review-input').setValue('建议补充示例')
    await item.find('.review-submit-btn').trigger('click')
    await flushPromises()

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/learnings/LRN-1/review'),
      expect.objectContaining({
        review_status: 'needs_changes',
        quality_score: 3,
        review_note: '建议补充示例',
        conversation_id: 321
      }),
      expect.any(Object)
    )
    expect(wrapper.text()).toContain('学习 LRN-1 已提交审核 (LEAR-REVIEW-1)')
  })

  it('loads learning history on demand', async () => {
    const wrapper = mount(LearningsView)
    await flushPromises()

    const item = wrapper.findAll('.learning-item').find(node => node.text().includes('LRN-1'))
    await item.find('.history-toggle-btn').trigger('click')
    await flushPromises()

    expect(axios.get).toHaveBeenCalledWith(
      expect.stringContaining('/learnings/LRN-1/history'),
      expect.any(Object)
    )
    expect(item.text()).toContain('版本历史')
    expect(item.text()).toContain('review:approved')
  })

  it('compares a version against the current learning state', async () => {
    const wrapper = mount(LearningsView)
    await flushPromises()

    const item = wrapper.findAll('.learning-item').find(node => node.text().includes('LRN-1'))
    await item.find('.history-toggle-btn').trigger('click')
    await flushPromises()
    await item.find('.history-entry-btn').trigger('click')
    await flushPromises()

    expect(axios.get).toHaveBeenCalledWith(
      expect.stringContaining('/learnings/LRN-1/compare?base_version_id=LVH-2'),
      expect.any(Object)
    )
    expect(item.text()).toContain('版本对比')
    expect(item.text()).toContain('审核状态')
    expect(item.text()).toContain('质量分')
  })

  it('merges duplicate learnings through the governance action route', async () => {
    axios.post.mockImplementation((url) => {
      if (url.includes('/merge-duplicate')) {
        return Promise.resolve({
          data: {
            snapshot_ref: {
              snapshot_id: 'LEAR-MERGE-1'
            }
          }
        })
      }
      return Promise.resolve({ data: {} })
    })

    const wrapper = mount(LearningsView)
    await flushPromises()

    const item = wrapper.findAll('.learning-item').find(node => node.text().includes('LRN-1'))
    await item.find('.duplicate-merge-btn').trigger('click')
    await flushPromises()

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/learnings/LRN-1/merge-duplicate'),
      expect.objectContaining({
        source_learning_id: 'LRN-2',
        conversation_id: 321
      }),
      expect.any(Object)
    )
    expect(wrapper.text()).toContain('已合并重复项 LRN-2 (LEAR-MERGE-1)')
  })

  it('applies a compared history version back to the current learning', async () => {
    axios.post.mockImplementation((url) => {
      if (url.includes('/apply-version')) {
        return Promise.resolve({
          data: {
            applied_version_id: 'LVH-1',
            note: '前端应用历史版本',
            snapshot_ref: {
              snapshot_id: 'LEAR-APPLIED-NA-20260503'
            },
            learning: {
              learning_id: 'LRN-1'
            }
          }
        })
      }
      return Promise.resolve({ data: {} })
    })

    const wrapper = mount(LearningsView)
    await flushPromises()

    const item = wrapper.findAll('.learning-item').find(node => node.text().includes('LRN-1'))
    await item.find('.history-toggle-btn').trigger('click')
    await flushPromises()
    await item.find('.history-entry-btn').trigger('click')
    await flushPromises()
    await item.find('.apply-version-btn').trigger('click')
    await flushPromises()

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/learnings/LRN-1/apply-version'),
      expect.objectContaining({
        version_id: 'LVH-1',
        conversation_id: 321
      }),
      expect.any(Object)
    )
    expect(wrapper.text()).toContain('学习 LRN-1 已应用版本 LVH-1 (LEAR-APPLIED-NA-20260503)')
  })

  it('applies only the selected compare fields back to the current learning', async () => {
    axios.post.mockImplementation((url) => {
      if (url.includes('/apply-version')) {
        return Promise.resolve({
          data: {
            applied_version_id: 'LVH-1',
            applied_fields: ['review_status'],
            snapshot_ref: {
              snapshot_id: 'LEAR-SELECTIVE-NA-20260503'
            },
            learning: {
              learning_id: 'LRN-1'
            }
          }
        })
      }
      return Promise.resolve({ data: {} })
    })

    const wrapper = mount(LearningsView)
    await flushPromises()

    const item = wrapper.findAll('.learning-item').find(node => node.text().includes('LRN-1'))
    await item.find('.history-toggle-btn').trigger('click')
    await flushPromises()
    await item.find('.history-entry-btn').trigger('click')
    await flushPromises()

    const checkboxes = item.findAll('input[type="checkbox"]')
    expect(checkboxes).toHaveLength(2)
    await checkboxes[1].setValue(false)
    await item.find('.apply-version-btn.secondary').trigger('click')
    await flushPromises()

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/learnings/LRN-1/apply-version'),
      expect.objectContaining({
        version_id: 'LVH-1',
        fields: ['review_status'],
        conversation_id: 321
      }),
      expect.any(Object)
    )
    expect(wrapper.text()).toContain('学习 LRN-1 已应用选定字段 (LEAR-SELECTIVE-NA-20260503)')
  })
})
