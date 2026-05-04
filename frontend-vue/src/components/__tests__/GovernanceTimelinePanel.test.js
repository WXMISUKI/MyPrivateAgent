import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const { routeQuery, replaceMock } = vi.hoisted(() => ({
  routeQuery: {},
  replaceMock: vi.fn(() => Promise.resolve())
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({
    query: routeQuery
  }),
  useRouter: () => ({
    replace: replaceMock
  })
}))

import GovernanceTimelinePanel from '../GovernanceTimelinePanel.vue'
import { useConversationStore } from '../../stores/conversation'
import { usePlannerStore } from '../../stores/planner'

describe('GovernanceTimelinePanel', () => {
  let pinia
  let clipboardWriteTextMock

  beforeEach(() => {
    vi.useRealTimers()
    pinia = createPinia()
    setActivePinia(pinia)
    Object.keys(routeQuery).forEach((key) => delete routeQuery[key])
    replaceMock.mockClear()
    clipboardWriteTextMock = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(globalThis.navigator, 'clipboard', {
      configurable: true,
      value: {
        writeText: clipboardWriteTextMock
      }
    })

    const conversationStore = useConversationStore()
    const plannerStore = usePlannerStore()
    conversationStore.conversations = [{
      id: 321,
      title: 'trace test',
      modelName: 'doubao',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now()
    }]
    conversationStore.activeId = 321

    plannerStore.loadPlans = vi.fn().mockResolvedValue([])
    plannerStore.upsertPlan({
      id: 10,
      objective: '完善 doctor trace',
      active_item_id: 23,
      items: [
        {
          id: 23,
          title: '执行治理门禁',
          status: 'in_progress',
          audit_trail: [
            {
              timestamp: '2026-05-01T12:00:00Z',
              event_type: 'doctor_run_started',
              content: 'Doctor `capability_gap` 诊断已开始'
            },
            {
              timestamp: '2026-05-01T12:00:07Z',
              event_type: 'remediation_status_updated',
              content: '整改动作 `fix_final_synthesis_chain` 已更新为 `done`'
            }
          ],
          run_trace: [
            {
              timestamp: '2026-05-01T12:00:05Z',
              source: 'doctor',
              event_type: 'doctor_gate_failed',
              severity: 'warning',
              summary: 'Doctor `capability_gap` 门禁未通过',
              detail: 'exit_code=2 non_closed_action_count=12'
            },
            {
              timestamp: '2026-05-01T12:00:06Z',
              source: 'scheduler',
              event_type: 'scheduler_merged',
              severity: 'success',
              summary: '调度器已完成结果合并',
              detail: 'merge_status=completed'
            },
            {
              timestamp: '2026-05-01T12:00:08Z',
              source: 'permission',
              event_type: 'permission_approved',
              severity: 'success',
              summary: '工具 `mcp_filesystem_read` 权限请求已批准',
              detail: 'approved',
              payload: {
                snapshot_ref: {
                  snapshot_id: 'PERM-REF-1',
                  generated_at: '2026-05-01T12:00:08Z',
                  conversation_id: 321,
                  source: 'permission',
                  event_type: 'permission_approved'
                },
                request_id: 'perm-1',
                tool_name: 'mcp_filesystem_read'
              }
            },
            {
              timestamp: '2026-05-01T12:00:09Z',
              source: 'mcp',
              event_type: 'mcp_server_probed',
              severity: 'info',
              summary: 'MCP 服务 `filesystem` 已完成 Probe',
              detail: 'status=ok',
              payload: {
                snapshot_ref: {
                  snapshot_id: 'MCP-REF-1',
                  generated_at: '2026-05-01T12:00:09Z',
                  conversation_id: 321,
                  source: 'mcp',
                  event_type: 'mcp_server_probed'
                },
                server_name: 'filesystem',
                status: 'ok'
              }
            },
            {
              timestamp: '2026-05-01T12:00:10Z',
              source: 'hook',
              event_type: 'pre_tool_use_blocked',
              severity: 'warning',
              summary: 'Hook 已阻断高风险工具调用',
              detail: 'policy=pre_tool_use'
            },
            {
              timestamp: '2026-05-01T12:00:11Z',
              source: 'runtime',
              event_type: 'agent_state_changed',
              severity: 'info',
              summary: '运行时状态已迁移到 WAITING_PERMISSION',
              detail: 'state=WAITING_PERMISSION'
            },
            {
              timestamp: '2026-05-01T12:00:12Z',
              source: 'learning',
              event_type: 'learning_version_applied',
              severity: 'info',
              summary: 'Learning `LRN-1` 已应用历史版本',
              detail: 'version_id=LVH-1 fields=review_status',
              payload: {
                snapshot_ref: {
                  snapshot_id: 'LEAR-REF-1',
                  generated_at: '2026-05-01T12:00:12Z',
                  conversation_id: 321,
                  source: 'learning',
                  event_type: 'learning_version_applied'
                },
                learning_id: 'LRN-1',
                applied_version_id: 'LVH-1',
                applied_fields: ['review_status']
              }
            }
          ]
        }
      ]
    }, true)
  })

  it('renders doctor and scheduler events from the current plan timeline', async () => {
    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(usePlannerStore().loadPlans).toHaveBeenCalledWith({ conversationId: 321 })
    expect(wrapper.text()).toContain('治理时间线')
    expect(wrapper.text()).toContain('复制当前视图')
    expect(wrapper.text()).toContain('最近一次 Doctor 结果')
    expect(wrapper.text()).toContain('最近一次权限结果')
    expect(wrapper.text()).toContain('最近一次 MCP 结果')
    expect(wrapper.text()).toContain('最近一次整改结果')
    expect(wrapper.text()).toContain('最近一次调度结果')
    expect(wrapper.text()).toContain('最近一次 Hook 结果')
    expect(wrapper.text()).toContain('最近一次 Runtime 结果')
    expect(wrapper.text()).toContain('最近一次 Learning 结果')
    expect(wrapper.text()).toContain('Doctor 门禁失败')
    expect(wrapper.text()).toContain('Doctor')
    expect(wrapper.text()).toContain('Scheduler')
    expect(wrapper.text()).toContain('Permission')
    expect(wrapper.text()).toContain('MCP')
    expect(wrapper.text()).toContain('Governance')
    expect(wrapper.text()).toContain('Hook')
    expect(wrapper.text()).toContain('Runtime')
    expect(wrapper.text()).toContain('Learning')
    expect(wrapper.text()).toContain('调度器已完成结果合并')
    expect(wrapper.text()).toContain('工具 `mcp_filesystem_read` 权限请求已批准')
    expect(wrapper.text()).toContain('Learning `LRN-1` 已应用历史版本')
    expect(wrapper.text()).toContain('当前筛选')
    expect(wrapper.text()).toContain('风险模式')
    expect(wrapper.text()).toContain('全部事件')
    expect(wrapper.text()).toContain('治理快照')
    expect(wrapper.text()).toContain('LEAR-REF-1')
    expect(wrapper.text()).toContain('Hook')
    expect(wrapper.text()).toContain('自动聚焦')
    expect(wrapper.text()).toContain('因 Doctor 门禁失败，当前默认聚焦到 Hook 风险域，共 1 条告警。')
    expect(wrapper.find('.timeline-list').text()).toContain('Hook 已阻断高风险工具调用')
    expect(wrapper.find('.timeline-list').text()).not.toContain('MCP 服务 `filesystem` 已完成 Probe')
    const overviewCards = wrapper.findAll('.governance-overview-card').map(item => item.text())
    expect(overviewCards).toEqual(expect.arrayContaining([
      expect.stringContaining('Doctor'),
      expect.stringContaining('2'),
      expect.stringContaining('告警 1'),
      expect.stringContaining('Doctor 门禁失败'),
      expect.stringContaining('Permission'),
      expect.stringContaining('1'),
      expect.stringContaining('告警 0'),
      expect.stringContaining('权限批准'),
      expect.stringContaining('MCP'),
      expect.stringContaining('MCP Probe 完成'),
      expect.stringContaining('Governance'),
      expect.stringContaining('整改状态更新'),
      expect.stringContaining('Scheduler'),
      expect.stringContaining('结果合并'),
      expect.stringContaining('Hook'),
      expect.stringContaining('Hook 阻断'),
      expect.stringContaining('Runtime'),
      expect.stringContaining('运行时状态迁移'),
      expect.stringContaining('Learning'),
      expect.stringContaining('Learning 版本应用'),
      expect.stringContaining('Warn'),
      expect.stringContaining('Info'),
      expect.stringContaining('20:00:11')
    ]))
  })

  it('sorts overview cards by latest update time', async () => {
    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const overviewCardLabels = wrapper
      .findAll('.governance-overview-card .summary-label')
      .map(item => item.text())

    expect(overviewCardLabels).toEqual([
      'Learning',
      'Runtime',
      'Hook',
      'MCP',
      'Permission',
      'Governance',
      'Scheduler',
      'Doctor'
    ])
  })

  it('supports overview warning shortcut for domain-scoped risk view', async () => {
    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const hookCard = wrapper.findAll('.governance-overview-card').find(item => item.text().includes('Hook'))
    expect(hookCard).toBeTruthy()
    const warningButton = hookCard.find('.overview-risk-btn')
    expect(warningButton.text()).toContain('仅告警 · 1')
    await warningButton.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('当前筛选')
    expect(wrapper.text()).toContain('Hook')
    expect(wrapper.text()).toContain('风险模式')
    expect(wrapper.text()).toContain('仅告警')
    expect(wrapper.find('.timeline-list').text()).toContain('Hook 已阻断高风险工具调用')
    expect(wrapper.find('.timeline-list').text()).not.toContain('Doctor `capability_gap` 门禁未通过')
    expect(hookCard.find('.overview-risk-btn').classes()).toContain('active')
  })

  it('applies filter when summary cards are clicked', async () => {
    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const permissionSummaryCard = wrapper.findAll('button').find(item => item.text().includes('最近一次权限结果'))
    expect(permissionSummaryCard).toBeTruthy()
    await permissionSummaryCard.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('当前筛选')
    expect(wrapper.text()).toContain('Permission')
    expect(wrapper.find('.timeline-list').text()).toContain('工具 `mcp_filesystem_read` 权限请求已批准')
    expect(wrapper.find('.timeline-list').text()).not.toContain('MCP 服务 `filesystem` 已完成 Probe')
    expect(replaceMock).toHaveBeenCalled()
  })

  it('supports MCP summary card navigation', async () => {
    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const mcpSummaryCard = wrapper.findAll('button').find(item => item.text().includes('最近一次 MCP 结果'))
    expect(mcpSummaryCard).toBeTruthy()
    await mcpSummaryCard.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('当前筛选')
    expect(wrapper.text()).toContain('MCP')
    expect(wrapper.find('.timeline-list').text()).toContain('MCP 服务 `filesystem` 已完成 Probe')
    expect(wrapper.find('.timeline-list').text()).not.toContain('工具 `mcp_filesystem_read` 权限请求已批准')
  })

  it('supports Hook summary card navigation', async () => {
    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const hookSummaryCard = wrapper.findAll('button').find(item => item.text().includes('最近一次 Hook 结果'))
    expect(hookSummaryCard).toBeTruthy()
    await hookSummaryCard.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('当前筛选')
    expect(wrapper.text()).toContain('Hook')
    expect(wrapper.find('.timeline-list').text()).toContain('Hook 已阻断高风险工具调用')
    expect(wrapper.find('.timeline-list').text()).not.toContain('MCP 服务 `filesystem` 已完成 Probe')
  })

  it('supports Learning summary card navigation', async () => {
    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const learningSummaryCard = wrapper.findAll('button').find(item => item.text().includes('最近一次 Learning 结果'))
    expect(learningSummaryCard).toBeTruthy()
    await learningSummaryCard.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('当前筛选')
    expect(wrapper.text()).toContain('Learning')
    expect(wrapper.find('.timeline-list').text()).toContain('Learning `LRN-1` 已应用历史版本')
    expect(wrapper.find('.timeline-list').text()).not.toContain('MCP 服务 `filesystem` 已完成 Probe')
  })

  it('filters timeline entries by governance domain', async () => {
    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()
    expect(wrapper.text()).toContain('MCP 服务 `filesystem` 已完成 Probe')
    expect(wrapper.text()).toContain('整改动作 `fix_final_synthesis_chain` 已更新为 `done`')

    const permissionFilter = wrapper.findAll('button.filter-chip').find(item => item.text().includes('Permission'))
    expect(permissionFilter).toBeTruthy()
    await permissionFilter.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('权限批准')
    expect(wrapper.find('.timeline-list').text()).toContain('工具 `mcp_filesystem_read` 权限请求已批准')
    expect(wrapper.find('.timeline-list').text()).not.toContain('MCP 服务 `filesystem` 已完成 Probe')
    expect(wrapper.find('.timeline-list').text()).not.toContain('整改动作 `fix_final_synthesis_chain` 已更新为 `done`')
    expect(replaceMock).toHaveBeenCalled()
  })

  it('supports warning-only severity mode', async () => {
    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const allFilter = wrapper.findAll('button.filter-chip').find(item => item.text().includes('全部 ·'))
    expect(allFilter).toBeTruthy()
    await allFilter.trigger('click')
    await flushPromises()

    const warningChip = wrapper.findAll('button.severity-chip').find(item => item.text().includes('仅告警'))
    expect(warningChip).toBeTruthy()
    await warningChip.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('风险模式')
    expect(wrapper.text()).toContain('仅告警')
    expect(wrapper.find('.timeline-list').text()).toContain('Doctor `capability_gap` 门禁未通过')
    expect(wrapper.find('.timeline-list').text()).toContain('Hook 已阻断高风险工具调用')
    expect(wrapper.find('.timeline-list').text()).not.toContain('调度器已完成结果合并')
    expect(wrapper.find('.timeline-list').text()).not.toContain('工具 `mcp_filesystem_read` 权限请求已批准')
    expect(replaceMock).toHaveBeenCalled()
  })

  it('copies current governance view with filter and severity state', async () => {
    routeQuery.tab = 'advanced'

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const hookCard = wrapper.findAll('.governance-overview-card').find(item => item.text().includes('Hook'))
    expect(hookCard).toBeTruthy()
    await hookCard.find('.overview-risk-btn').trigger('click')
    await flushPromises()

    clipboardWriteTextMock.mockClear()
    const copyViewButton = wrapper.findAll('button').find(item => item.text().includes('复制当前视图'))
    expect(copyViewButton).toBeTruthy()
    await copyViewButton.trigger('click')
    await flushPromises()

    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('快照ID: LEAR-REF-1'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('生成时间: 2026-05-01T12:00:12Z'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('治理视图: Hook / 仅告警'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('事件范围: 1 / 2'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('聚焦原因: 因 Doctor 门禁失败，当前默认聚焦到 Hook 风险域，共 1 条告警。'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('后端引用: learning / learning_version_applied'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('governance_filter=hook'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('governance_severity=warning'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('tab=advanced'))
    expect(wrapper.text()).toContain('已复制视图')
  })

  it('supports route-driven filter and payload expansion', async () => {
    routeQuery.governance_filter = 'mcp'

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('当前筛选')
    expect(wrapper.text()).toContain('MCP')
    expect(wrapper.text()).not.toContain('自动聚焦')
    expect(wrapper.text()).toContain('MCP 服务 `filesystem` 已完成 Probe')
    expect(wrapper.find('.timeline-list').text()).not.toContain('工具 `mcp_filesystem_read` 权限请求已批准')
    expect(wrapper.find('.timeline-list').text()).not.toContain('Hook 已阻断高风险工具调用')

    const expandButton = wrapper.findAll('button').find(item => item.text().includes('展开 Payload'))
    expect(expandButton).toBeTruthy()
    await expandButton.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('"server_name": "filesystem"')
    expect(wrapper.text()).toContain('"status": "ok"')

    const copyButton = wrapper.findAll('button').find(item => item.text().includes('复制 Payload'))
    expect(copyButton).toBeTruthy()
    await copyButton.trigger('click')
    await flushPromises()

    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('"server_name": "filesystem"'))
    expect(wrapper.text()).toContain('已复制 Payload')
  })

  it('supports route-driven snapshot focus and highlights matched event', async () => {
    routeQuery.governance_snapshot = 'MCP-REF-1'

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('快照聚焦')
    expect(wrapper.text()).toContain('MCP-REF-1')
    expect(wrapper.text()).toContain('已聚焦到 MCP Probe 完成')
    expect(wrapper.find('.timeline-list').text()).toContain('MCP 服务 `filesystem` 已完成 Probe')
    expect(wrapper.find('.timeline-list').text()).not.toContain('工具 `mcp_filesystem_read` 权限请求已批准')
    expect(wrapper.find('.timeline-item.highlighted').text()).toContain('引用 MCP-REF-1')
  })

  it('shows and copies event-level snapshot refs', async () => {
    routeQuery.governance_filter = 'mcp'

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(wrapper.find('.timeline-list').text()).toContain('引用 MCP-REF-1')

    const copyRefButton = wrapper.findAll('button').find(item => item.text().includes('复制引用'))
    expect(copyRefButton).toBeTruthy()
    await copyRefButton.trigger('click')
    await flushPromises()

    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('快照ID: MCP-REF-1'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('来源: mcp / mcp_server_probed'))
    expect(wrapper.text()).toContain('已复制引用')
  })

  it('copies snapshot slash command from the current governance view', async () => {
    routeQuery.governance_filter = 'mcp'

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    clipboardWriteTextMock.mockClear()
    const copyCommandButton = wrapper.findAll('button').find(item => item.text().includes('复制快照命令'))
    expect(copyCommandButton).toBeTruthy()
    await copyCommandButton.trigger('click')
    await flushPromises()

    expect(clipboardWriteTextMock).toHaveBeenCalledWith('/mcp snapshot MCP-REF-1')
    expect(wrapper.text()).toContain('已复制命令')
    expect(wrapper.text()).toContain('最近复制命令')
    expect(wrapper.text()).toContain('/mcp snapshot MCP-REF-1')
  })

  it('copies snapshot slash command for a timeline entry', async () => {
    routeQuery.governance_filter = 'mcp'

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    clipboardWriteTextMock.mockClear()
    const copyCommandButton = wrapper.findAll('button').find(item => item.text().includes('复制命令'))
    expect(copyCommandButton).toBeTruthy()
    await copyCommandButton.trigger('click')
    await flushPromises()

    expect(clipboardWriteTextMock).toHaveBeenCalledWith('/mcp snapshot MCP-REF-1')
    expect(wrapper.text()).toContain('已复制命令')
  })

  it('includes governance_snapshot when copying current view', async () => {
    routeQuery.governance_snapshot = 'MCP-REF-1'
    routeQuery.tab = 'advanced'

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    clipboardWriteTextMock.mockClear()
    const copyViewButton = wrapper.findAll('button').find(item => item.text().includes('复制当前视图'))
    expect(copyViewButton).toBeTruthy()
    await copyViewButton.trigger('click')
    await flushPromises()

    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('governance_snapshot=MCP-REF-1'))
  })

  it('supports route-driven warning scope without auto-focus override', async () => {
    routeQuery.governance_filter = 'all'
    routeQuery.governance_severity = 'warning'

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('风险模式')
    expect(wrapper.text()).toContain('仅告警')
    expect(wrapper.text()).not.toContain('自动聚焦')
    expect(wrapper.find('.timeline-list').text()).toContain('Doctor `capability_gap` 门禁未通过')
    expect(wrapper.find('.timeline-list').text()).toContain('Hook 已阻断高风险工具调用')
    expect(wrapper.find('.timeline-list').text()).not.toContain('调度器已完成结果合并')
    expect(wrapper.find('.timeline-list').text()).not.toContain('MCP 服务 `filesystem` 已完成 Probe')
  })

  it('falls back to execCommand copy when clipboard api is unavailable', async () => {
    routeQuery.governance_filter = 'mcp'
    Object.defineProperty(globalThis.navigator, 'clipboard', {
      configurable: true,
      value: undefined
    })
    const execCommandMock = vi.fn(() => true)
    document.execCommand = execCommandMock

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const copyButton = wrapper.findAll('button').find(item => item.text().includes('复制 Payload'))
    expect(copyButton).toBeTruthy()
    await copyButton.trigger('click')
    await flushPromises()

    expect(execCommandMock).toHaveBeenCalledWith('copy')
    expect(wrapper.text()).toContain('已复制 Payload')
  })

  it('auto clears copied payload state after a short delay', async () => {
    vi.useFakeTimers()
    routeQuery.governance_filter = 'mcp'

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const copyButton = wrapper.findAll('button').find(item => item.text().includes('复制 Payload'))
    expect(copyButton).toBeTruthy()
    await copyButton.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('已复制 Payload')

    await vi.advanceTimersByTimeAsync(1600)
    await flushPromises()

    expect(wrapper.text()).not.toContain('已复制 Payload')
    expect(wrapper.text()).toContain('复制 Payload')
  })

  it('auto clears copied snapshot ref state after a short delay', async () => {
    vi.useFakeTimers()
    routeQuery.governance_filter = 'mcp'

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const copyRefButton = wrapper.findAll('button').find(item => item.text().includes('复制引用'))
    expect(copyRefButton).toBeTruthy()
    await copyRefButton.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('已复制引用')

    await vi.advanceTimersByTimeAsync(1600)
    await flushPromises()

    expect(wrapper.text()).not.toContain('已复制引用')
    expect(wrapper.text()).toContain('复制引用')
  })
})
