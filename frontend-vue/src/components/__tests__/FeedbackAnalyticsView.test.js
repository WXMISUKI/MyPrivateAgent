import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

const { pushMock } = vi.hoisted(() => ({
  pushMock: vi.fn()
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: pushMock })
}))

vi.mock('axios', () => ({
  default: {
    get: vi.fn()
  }
}))

import axios from 'axios'
import FeedbackAnalyticsView from '../../views/FeedbackAnalyticsView.vue'

function mockAnalyticsApi() {
  axios.get.mockResolvedValue({
    data: {
      total_feedback: 8,
      positive_count: 3,
      negative_count: 5,
      neutral_count: 0,
      negative_rate: 0.625,
      scope_stats: [
        { key: 'chat', total: 5, negative: 2, negative_rate: 0.4 }
      ],
      prompt_stats: [
        { key: 'prompt-a', total: 4, negative: 3, negative_rate: 0.75 }
      ],
      practice_stats: [
        { key: 'practice-1', total: 3, negative: 2, negative_rate: 0.6667 }
      ],
      rollback_candidates: [
        { kind: 'prompt', key: 'prompt-a', total: 4, negative: 3, negative_rate: 0.75 },
        { kind: 'practice', key: 'practice-1', total: 3, negative: 2, negative_rate: 0.6667 }
      ]
    }
  })
}

describe('FeedbackAnalyticsView', () => {
  beforeEach(() => {
    pushMock.mockReset()
    axios.get.mockReset()
    mockAnalyticsApi()
  })

  it('routes rollback candidates to matching learning drill-down views', async () => {
    const wrapper = mount(FeedbackAnalyticsView)
    await flushPromises()

    await wrapper.get('[data-testid="rollback-drilldown-prompt-prompt-a"]').trigger('click')
    await wrapper.get('[data-testid="scope-drilldown-chat"]').trigger('click')
    await wrapper.get('[data-testid="practice-drilldown-practice-1"]').trigger('click')

    expect(pushMock).toHaveBeenNthCalledWith(
      1,
      '/learnings?tab=learnings&source=user_feedback&search=prompt-a&tag=prompt%3Aprompt-a'
    )
    expect(pushMock).toHaveBeenNthCalledWith(
      2,
      '/learnings?tab=learnings&source=user_feedback&search=chat&tag=scope%3Achat'
    )
    expect(pushMock).toHaveBeenNthCalledWith(
      3,
      '/learnings?tab=learnings&source=user_feedback&search=practice-1&tag=practice%3Apractice-1'
    )
  })
})
