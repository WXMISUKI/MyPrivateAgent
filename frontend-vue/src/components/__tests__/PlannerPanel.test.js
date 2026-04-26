import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import PlannerPanel from '../PlannerPanel.vue'

function mountPlannerPanel(overrides = {}) {
  return mount(PlannerPanel, {
    props: {
      collapsed: false,
      plan: null,
      draftObjective: '',
      newItemTitle: '',
      isGenerating: false,
      errorMessage: '',
      ...overrides
    }
  })
}

describe('PlannerPanel', () => {
  it('renders child executions and merge summary for scheduler items', () => {
    const wrapper = mountPlannerPanel({
      plan: {
        id: 1,
        status: 'in_progress',
        summary: '执行中',
        objective: '完善多智能体调度',
        progress: {
          completed: 1,
          total: 3
        },
        items: [
          {
            id: 11,
            step_order: 1,
            title: '联调前后端并补测试',
            details: '需要并行推进',
            status: 'in_progress',
            owner: '主智能体',
            agent_role: 'planner',
            agent_id: 'scheduler-p1-i11',
            handoff_status: 'executing',
            child_executions: [
              {
                child_execution_id: 'backend-child-p1-i11-c1',
                agent_role: 'backend',
                agent_id: 'backend-agent-p1-i11-c1',
                status: 'completed',
                summary: '后端接口已完成'
              },
              {
                child_execution_id: 'frontend-child-p1-i11-c2',
                agent_role: 'frontend',
                agent_id: 'frontend-agent-p1-i11-c2',
                status: 'failed',
                error: '前端构建失败'
              }
            ],
            merge_summary: {
              merge_status: 'partial_failed',
              merge_strategy: 'role_sections',
              child_count: 2,
              merged_output: '[backend] 后端接口已完成\n\n未完成的子执行：frontend=前端构建失败'
            },
            audit_trail: [
              {
                timestamp: '2026-04-25T18:00:00Z',
                event_type: 'scheduler_fanout_prepared',
                content: '已为当前步骤准备 2 个子执行单元'
              },
              {
                timestamp: '2026-04-25T18:00:05Z',
                event_type: 'child_failed',
                content: '前端子执行失败'
              }
            ],
            run_trace: [
              {
                timestamp: '2026-04-25T18:00:06Z',
                source: 'scheduler',
                event_type: 'scheduler_cancelled',
                severity: 'warning',
                summary: '调度器已取消剩余子执行任务',
                detail: '检测到子执行失败，按策略取消剩余任务。'
              }
            ]
          }
        ]
      }
    })

    expect(wrapper.text()).toContain('调度状态')
    expect(wrapper.text()).toContain('部分失败')
    expect(wrapper.text()).toContain('子执行：2')
    expect(wrapper.text()).toContain('后端')
    expect(wrapper.text()).toContain('测试')
    expect(wrapper.text()).toContain('后端接口已完成')
    expect(wrapper.text()).toContain('前端构建失败')
    expect(wrapper.text()).toContain('执行时间线')
    expect(wrapper.text()).toContain('运行 Trace')
    expect(wrapper.text()).toContain('子执行失败')
    expect(wrapper.text()).toContain('已为当前步骤准备 2 个子执行单元')
    expect(wrapper.text()).toContain('Scheduler')
    expect(wrapper.text()).toContain('调度器已取消剩余子执行任务')
  })
})
