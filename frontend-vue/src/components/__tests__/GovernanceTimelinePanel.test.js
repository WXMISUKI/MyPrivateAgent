import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const { routeQuery, replaceMock, pushMock } = vi.hoisted(() => ({
  routeQuery: {},
  replaceMock: vi.fn(() => Promise.resolve()),
  pushMock: vi.fn(() => Promise.resolve())
}))

const { getRuntimeProfileMock, getMainChatQueryDetailMock, getMainChatQueryHistoryMock } = vi.hoisted(() => ({
  getRuntimeProfileMock: vi.fn().mockResolvedValue({ data: {} }),
  getMainChatQueryDetailMock: vi.fn().mockResolvedValue({ data: {} }),
  getMainChatQueryHistoryMock: vi.fn().mockResolvedValue({ data: {} })
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({
    query: routeQuery
  }),
  useRouter: () => ({
    replace: replaceMock,
    push: pushMock
  })
}))

vi.mock('../../api', () => ({
  runtimeSurfaceApi: {
    getProfile: getRuntimeProfileMock,
    getMainChatQueryDetail: getMainChatQueryDetailMock,
    getMainChatQueryHistory: getMainChatQueryHistoryMock
  }
}))

import GovernanceTimelinePanel from '../GovernanceTimelinePanel.vue'
import { useConversationStore } from '../../stores/conversation'
import { usePlannerStore } from '../../stores/planner'

function seedPlan(overrides = {}) {
  const plannerStore = usePlannerStore()
  plannerStore.upsertPlan({
    id: 10,
    objective: '完善 doctor trace',
    active_item_id: 23,
    items: [
      {
        id: 23,
        title: '执行治理门禁',
        status: 'in_progress',
        scheduler_run: {
          run_id: 'sched-run-01',
          scheduler_run_id: 'sched-run-01',
          run_kind: 'scheduler',
          state: 'running',
          active_children: 1,
          approval_request_count: 2
        },
        approval_requests: [
          {
            request_id: 'approval-1',
            status: 'pending',
            tool_name: 'shell_command',
            permission_level: 'elevated',
            run_id: 'sched-run-01',
            run_kind: 'scheduler'
          },
          {
            request_id: 'approval-2',
            status: 'approved',
            tool_name: 'list_mcp_resources',
            permission_level: 'standard',
            run_id: 'sched-run-01',
            run_kind: 'scheduler'
          }
        ],
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
            timestamp: '2026-05-01T12:00:04Z',
            source: 'doctor',
            event_type: 'doctor_run_completed',
            severity: 'info',
            summary: 'Doctor `capability_gap` 诊断已完成',
            detail: 'status=warn exit_code=2',
            payload: {
              snapshot_ref: {
                snapshot_id: 'DOCT-REF-1',
                generated_at: '2026-05-01T12:00:04Z',
                conversation_id: 321,
                source: 'doctor',
                event_type: 'doctor_run_completed'
              },
              status: 'warn',
              exit_code: 2,
              gate_passed: false,
              framework_adapters: {
                status: 'warn',
                details: ['langgraph_draft: status=not_configured | config=missing_package'],
                latest_external_pilot_failure: {
                  error_type: 'protocol_error',
                  adapter_id: 'langgraph_draft',
                  framework_name: 'LangGraph',
                  detail: 'transport probe did not provide assistant identity evidence',
                  snapshot_ref: {
                    snapshot_id: 'FRAM-EXT-DIAG-321-20260501120017',
                    generated_at: '2026-05-01T12:00:17Z',
                    conversation_id: 321,
                    source: 'framework_adapter',
                    event_type: 'framework_adapter_external_error'
                  }
                },
                external_pilot_failure_counts: {
                  total: 4,
                  window_scope: 'recent_plan_items',
                  sample_size: 50,
                  by_error_type: {
                    protocol_error: 3,
                    connectivity_error: 1
                  }
                },
                remediation_actions: [
                  {
                    adapter_id: 'langgraph_draft',
                    type: 'install_package',
                    message: '安装缺失依赖包',
                    packages: ['langgraph']
                  },
                  {
                    adapter_id: 'langgraph_draft',
                    type: 'configure_env',
                    message: '补齐运行时环境变量',
                    env: ['LANGGRAPH_RUNTIME_ENDPOINT', 'LANGGRAPH_ASSISTANT_ID']
                  }
                ]
              }
            }
          },
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
            timestamp: '2026-05-01T12:00:18Z',
            source: 'runtime_control',
            event_type: 'embedded_runtime_bootstrap_updated',
            severity: 'success',
            summary: 'Embedded runtime bootstrap 已切换到 `memory_only`',
            detail: 'runtime_mode=memory_preview recovery_posture=in_process_only',
            payload: {
              snapshot_ref: {
                snapshot_id: 'RUNT-BOOT-321-20260501120018',
                generated_at: '2026-05-01T12:00:18Z',
                conversation_id: 321,
                source: 'runtime_control',
                event_type: 'embedded_runtime_bootstrap_updated'
              },
              requested_embedded_workspace_store_mode: 'memory_only',
              update_status: 'applied',
              current_runtime_mode: 'memory_preview',
              current_recovery_posture: 'in_process_only',
              current_workspace_backend_mode: 'memory_only',
              bootstrap_recovery_validation_status: 'passed'
            }
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
          },
          {
            timestamp: '2026-05-01T12:00:14Z',
            source: 'framework_adapter',
            event_type: 'framework_adapter_precheck_completed',
            severity: 'info',
            summary: 'Framework adapter `LangGraph` precheck completed',
            detail: 'status=not_configured config=missing_env',
            payload: {
              snapshot_ref: {
                snapshot_id: 'FRAM-PRECHECK-321-20260501120014',
                generated_at: '2026-05-01T12:00:14Z',
                conversation_id: 321,
                source: 'framework_adapter',
                event_type: 'framework_adapter_precheck_completed'
              },
              adapter_id: 'langgraph_draft',
              framework_name: 'LangGraph',
              ready: false,
              status: 'not_configured',
              configuration_status: 'missing_env',
              missing_env: ['LANGGRAPH_RUNTIME_ENDPOINT', 'LANGGRAPH_ASSISTANT_ID'],
              execution_block_reason: 'missing required environment variables'
            }
          },
          {
            timestamp: '2026-05-01T12:00:13Z',
            source: 'framework_adapter',
            event_type: 'framework_adapter_output',
            severity: 'success',
            summary: 'Framework adapter `LocalFakeFramework` produced output',
            detail: 'Local fake adapter processed: 请生成一份运行时巡检计划摘要',
            payload: {
              snapshot_ref: {
                snapshot_id: 'FRAM-FRAMEWORK_A-321-20260501120013',
                generated_at: '2026-05-01T12:00:13Z',
                conversation_id: 321,
                source: 'framework_adapter',
                event_type: 'framework_adapter_run_completed'
              },
              adapter_id: 'local_fake_framework',
              framework_name: 'LocalFakeFramework',
              content: 'Local fake adapter processed: 请生成一份运行时巡检计划摘要'
            }
          },
          {
            timestamp: '2026-05-01T12:00:15Z',
            source: 'framework_adapter',
            event_type: 'framework_adapter_external_pilot_completed',
            severity: 'success',
            summary: 'Framework adapter `LangGraph` external pilot completed',
            detail: 'status=ok',
            payload: {
              snapshot_ref: {
                snapshot_id: 'FRAM-EXT-321-20260501120015',
                generated_at: '2026-05-01T12:00:15Z',
                conversation_id: 321,
                source: 'framework_adapter',
                event_type: 'framework_adapter_external_pilot_completed'
              },
              adapter_id: 'langgraph_draft',
              framework_name: 'LangGraph',
              status: 'ok',
              final_output: 'LangGraph external answer'
            }
          },
          {
            timestamp: '2026-05-01T12:00:16Z',
            source: 'framework_adapter',
            event_type: 'framework_adapter_external_error',
            severity: 'warning',
            summary: 'Framework adapter `LangGraph` external pilot failed',
            detail: 'connect failed',
            payload: {
              snapshot_ref: {
                snapshot_id: 'FRAM-EXT-ERR-321-20260501120016',
                generated_at: '2026-05-01T12:00:16Z',
                conversation_id: 321,
                source: 'framework_adapter',
                event_type: 'framework_adapter_external_error'
              },
              adapter_id: 'langgraph_draft',
              framework_name: 'LangGraph',
              error_type: 'connectivity_error',
              detail: 'connect failed'
            }
          }
        ],
        ...overrides
      }
    ]
  }, true)
}

describe('GovernanceTimelinePanel', () => {
  let pinia
  let clipboardWriteTextMock

  beforeEach(() => {
    vi.useRealTimers()
    pinia = createPinia()
    setActivePinia(pinia)
    localStorage.removeItem('governance_recent_snapshot_commands')
    Object.keys(routeQuery).forEach((key) => delete routeQuery[key])
    replaceMock.mockClear()
    pushMock.mockClear()
    getRuntimeProfileMock.mockClear()
    getRuntimeProfileMock.mockResolvedValue({ data: {} })
    getMainChatQueryDetailMock.mockClear()
    getMainChatQueryDetailMock.mockResolvedValue({ data: {} })
    getMainChatQueryHistoryMock.mockClear()
    getMainChatQueryHistoryMock.mockResolvedValue({ data: {} })
    clipboardWriteTextMock = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(globalThis.navigator, 'clipboard', {
      configurable: true,
      value: {
        writeText: clipboardWriteTextMock
      }
    })

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

    usePlannerStore().loadPlans = vi.fn().mockResolvedValue([])
    seedPlan()
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
    expect(wrapper.text()).toContain('最近一次 LocalFakeFramework Pilot')
    expect(wrapper.text()).toContain('最近一次 LangGraph Precheck')
    expect(wrapper.text()).toContain('最近一次 LangGraph External Pilot')
    expect(wrapper.text()).toContain('最近一次 LangGraph External Pilot 失败诊断')
    expect(wrapper.text()).toContain('Framework Adapter 外部执行失败')
    expect(wrapper.text()).toContain('连通性错误 (connectivity_error)')
    expect(wrapper.text()).toContain('connect failed')
    expect(wrapper.text()).toContain('协议错误 (protocol_error)')
    expect(wrapper.text()).toContain('失败总数: 4')
    expect(wrapper.text()).toContain('统计窗口: 最近 PlanItem')
    expect(wrapper.text()).toContain('样本数: 50')
    expect(wrapper.text()).toContain('错误分布: 协议错误 3 · 连通性错误 1')
    expect(wrapper.text()).toContain('transport probe did not provide assistant identity evidence')
    expect(wrapper.text()).toContain('最近一次 LangGraph 修复建议')
    expect(wrapper.text()).toContain('LangGraph · 缺包 / 缺环境变量')
    expect(wrapper.text()).toContain('打开运行时面板')
    expect(wrapper.text()).toContain('复制修复命令')
    expect(wrapper.text()).toContain('Framework Adapter 预检完成')
    expect(wrapper.text()).toContain('Doctor 门禁失败')
    expect(wrapper.text()).toContain('Doctor')
    expect(wrapper.text()).toContain('Scheduler')
    expect(wrapper.text()).toContain('Permission')
    expect(wrapper.text()).toContain('MCP')
    expect(wrapper.text()).toContain('Governance')
    expect(wrapper.text()).toContain('Hook')
    expect(wrapper.text()).toContain('Runtime')
    expect(wrapper.text()).toContain('Learning')
    expect(wrapper.text()).toContain('Framework Adapter')
    expect(wrapper.text()).toContain('Embedded Runtime Bootstrap 更新')
    expect(wrapper.text()).toContain('Embedded runtime bootstrap 已切换到 `memory_only`')
    expect(wrapper.text()).toContain('最近一次 Runtime 结果20:00:18Embedded Runtime Bootstrap 更新Embedded runtime bootstrap 已切换到 `memory_only`Runtime Control')
    expect(wrapper.text()).toContain('调度器已完成结果合并')
    expect(wrapper.text()).toContain('工具 `mcp_filesystem_read` 权限请求已批准')
    expect(wrapper.text()).toContain('Learning `LRN-1` 已应用历史版本')
    expect(wrapper.text()).toContain('Framework adapter `LocalFakeFramework` produced output')
    expect(wrapper.text()).toContain('Framework adapter `LangGraph` precheck completed')
    expect(wrapper.text()).toContain('Framework adapter `LangGraph` external pilot completed')
    expect(wrapper.text()).toContain('adapter_id: local_fake_framework')
    expect(wrapper.text()).toContain('adapter_id: langgraph_draft')
    expect(wrapper.text()).toContain('状态: 缺包')
    expect(wrapper.text()).toContain('状态: 缺环境变量')
    expect(wrapper.text()).toContain('langgraph_draft · install_package · 安装缺失依赖包')
    expect(wrapper.text()).toContain('langgraph_draft · configure_env · 补齐运行时环境变量')
    expect(wrapper.text()).toContain('当前筛选')
    expect(wrapper.text()).toContain('风险模式')
    expect(wrapper.text()).toContain('全部事件')
    expect(wrapper.text()).toContain('治理快照')
    expect(wrapper.text()).toContain('FRAM-EXT-ERR-321-20260501120016')
    expect(wrapper.text()).toContain('Hook')
    expect(wrapper.text()).toContain('自动聚焦')
    expect(wrapper.text()).toContain('因 Doctor 门禁失败，当前默认聚焦到 Framework Adapter 风险域，共 2 条告警。')
    expect(wrapper.find('.timeline-list').text()).toContain('连通性错误 (connectivity_error)')
    expect(wrapper.find('.timeline-list').text()).not.toContain('MCP 服务 `filesystem` 已完成 Probe')
    const overviewCards = wrapper.findAllComponents({ name: 'GovernanceTimelineOverviewCards' }).at(0).findAll('.governance-overview-card').map(item => item.text())
    expect(overviewCards).toContain('Framework AdapterWarn5总事件 5 · 告警 2Framework Adapter 外部执行失败20:00:16仅告警 · 2')
    expect(overviewCards).toContain('LearningInfo1总事件 1 · 告警 0Learning 版本应用20:00:12无告警')
    expect(overviewCards).toContain('RuntimeOK2总事件 2 · 告警 0Embedded Runtime Bootstrap 更新20:00:18无告警')
    expect(overviewCards).toContain('HookWarn1总事件 1 · 告警 1Hook 阻断20:00:10仅告警 · 1')
    expect(overviewCards).toContain('MCPInfo1总事件 1 · 告警 0MCP Probe 完成20:00:09无告警')
    expect(overviewCards).toContain('PermissionOK1总事件 1 · 告警 0权限批准20:00:08无告警')
    expect(overviewCards).toContain('GovernanceOK1总事件 1 · 告警 0整改状态更新20:00:07无告警')
    expect(overviewCards).toContain('SchedulerOK1总事件 1 · 告警 0结果合并20:00:06无告警')
    expect(overviewCards).toContain('DoctorWarn3总事件 3 · 告警 1Doctor 门禁失败20:00:05仅告警 · 1')

    const runtimeOverviewCard = wrapper.findAllComponents({ name: 'GovernanceTimelineOverviewCards' }).at(0).findAll('.governance-overview-card')
      .find(item => item.text().includes('RuntimeOK2总事件 2 · 告警 0Embedded Runtime Bootstrap 更新20:00:18无告警'))
    expect(runtimeOverviewCard).toBeTruthy()
    await runtimeOverviewCard.find('.overview-card-main').trigger('click')
    await flushPromises()

    expect(wrapper.find('.timeline-list').text()).toContain('Runtime Control')
    expect(wrapper.find('.timeline-list').text()).toContain('workspace_mode=memory_only · runtime=memory_preview · recovery=in_process_only · backend=memory_only · validation=passed')
  })

  it('supports framework adapter remediation actions', async () => {
    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const openButton = wrapper.findAll('button').find(item => item.text().includes('打开运行时面板'))
    expect(openButton).toBeTruthy()
    await openButton.trigger('click')
    expect(pushMock).toHaveBeenCalledWith('/settings?tab=advanced')

    expect(wrapper.text()).toContain('状态: 缺包')
    expect(wrapper.text()).toContain('状态: 缺环境变量')

    const copyButton = wrapper
      .findComponent({ name: 'GovernanceTimelineFrameworkAdapterRemediationCard' })
      .findAll('button')
      .find(item => item.text().includes('复制修复命令'))
    expect(copyButton).toBeTruthy()
    await copyButton.trigger('click')
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('pip install langgraph'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('LANGGRAPH_RUNTIME_ENDPOINT=<value>'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('ENABLE_LANGGRAPH_RUNTIME_EXECUTION=true'))
  })

  it('shows phase a run and pending approval overview', async () => {
    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const planObjectiveLabel = wrapper.find('.plan-objective-label')
    expect(planObjectiveLabel.exists()).toBe(true)
    expect(planObjectiveLabel.text()).toBe('完善 doctor trace')
    expect(planObjectiveLabel.attributes('title')).toBe('完善 doctor trace')
    expect(planObjectiveLabel.attributes('aria-label')).toBe('当前计划 完善 doctor trace')
    const focusStepLabel = wrapper.find('.focus-step-label')
    expect(focusStepLabel.exists()).toBe(true)
    expect(focusStepLabel.text()).toBe('执行治理门禁')
    expect(focusStepLabel.attributes('title')).toBe('执行治理门禁')
    expect(focusStepLabel.attributes('aria-label')).toBe('聚焦步骤 执行治理门禁')
    const auditCountLabel = wrapper.find('.audit-count-label')
    expect(auditCountLabel.exists()).toBe(true)
    expect(auditCountLabel.text()).toBe('2')
    expect(auditCountLabel.attributes('title')).toBe('2')
    expect(auditCountLabel.attributes('aria-label')).toBe('审计事件 2')
    const traceCountLabel = wrapper.find('.trace-count-label')
    expect(traceCountLabel.exists()).toBe(true)
    expect(traceCountLabel.text()).toBe('13')
    expect(traceCountLabel.attributes('title')).toBe('13')
    expect(traceCountLabel.attributes('aria-label')).toBe('运行 Trace 13')
    expect(wrapper.text()).toContain('当前执行实例')
    expect(wrapper.text()).toContain('sched-run-01')
    expect(wrapper.text()).toContain('scheduler · running')
    expect(wrapper.text()).toContain('待处理审批')
    expect(wrapper.text()).toContain('1 个待处理')
    expect(wrapper.text()).toContain('shell_command')
    expect(wrapper.text()).toContain('approval-1')
  })

  it('prefers the latest pending approval when multiple approvals coexist', async () => {
    seedPlan({
      approval_requests: [
        {
          request_id: 'approval-older',
          status: 'pending',
          tool_name: 'shell_command',
          permission_level: 'elevated',
          created_at: '2026-05-01T12:00:01Z'
        },
        {
          request_id: 'approval-approved',
          status: 'approved',
          tool_name: 'list_mcp_resources',
          permission_level: 'standard',
          updated_at: '2026-05-01T12:00:09Z'
        },
        {
          request_id: 'approval-newer',
          status: 'pending',
          tool_name: 'request_user_input',
          permission_level: 'standard',
          updated_at: '2026-05-01T12:00:10Z'
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('待处理审批')
    expect(wrapper.text()).toContain('2 个待处理')
    expect(wrapper.text()).toContain('request_user_input')
    expect(wrapper.text()).toContain('approval-newer')
    expect(wrapper.text()).not.toContain('shell_command · approval-older')
  })

  it('prefers updated_at over lower priority timestamps when selecting the latest pending approval', async () => {
    seedPlan({
      approval_requests: [
        {
          request_id: 'approval-with-updated-at',
          status: 'pending',
          tool_name: 'shell_command',
          permission_level: 'elevated',
          updated_at: '2026-05-01T12:00:02Z'
        },
        {
          request_id: 'approval-created-only',
          status: 'pending',
          tool_name: 'request_user_input',
          permission_level: 'standard',
          created_at: '2026-05-01T12:00:10Z'
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('approval-with-updated-at')
    expect(wrapper.text()).toContain('shell_command')
    expect(wrapper.text()).not.toContain('request_user_input · approval-created-only')
  })

  it('falls back to created_at when updated_at is unavailable for pending approvals', async () => {
    seedPlan({
      approval_requests: [
        {
          request_id: 'approval-created-older',
          status: 'pending',
          tool_name: 'shell_command',
          permission_level: 'elevated',
          created_at: '2026-05-01T12:00:01Z'
        },
        {
          request_id: 'approval-created-newer',
          status: 'pending',
          tool_name: 'request_user_input',
          permission_level: 'standard',
          created_at: '2026-05-01T12:00:10Z'
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('approval-created-newer')
    expect(wrapper.text()).toContain('request_user_input')
    expect(wrapper.text()).not.toContain('shell_command · approval-created-older')
  })

  it('continues comparing created_at when pending approvals have the same updated_at', async () => {
    seedPlan({
      approval_requests: [
        {
          request_id: 'approval-same-updated-first',
          status: 'pending',
          tool_name: 'shell_command',
          permission_level: 'elevated',
          updated_at: '2026-05-01T12:00:10Z',
          created_at: '2026-05-01T12:00:01Z'
        },
        {
          request_id: 'approval-same-updated-second',
          status: 'pending',
          tool_name: 'request_user_input',
          permission_level: 'standard',
          updated_at: '2026-05-01T12:00:10Z',
          created_at: '2026-05-01T12:00:09Z'
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('approval-same-updated-second')
    expect(wrapper.text()).toContain('request_user_input')
    expect(wrapper.text()).not.toContain('shell_command · approval-same-updated-first')
  })

  it('falls back to timestamp when updated_at and created_at are unavailable for pending approvals', async () => {
    seedPlan({
      approval_requests: [
        {
          request_id: 'approval-timestamp-older',
          status: 'pending',
          tool_name: 'shell_command',
          permission_level: 'elevated',
          timestamp: '2026-05-01T12:00:01Z'
        },
        {
          request_id: 'approval-timestamp-newer',
          status: 'pending',
          tool_name: 'request_user_input',
          permission_level: 'standard',
          timestamp: '2026-05-01T12:00:10Z'
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('approval-timestamp-newer')
    expect(wrapper.text()).toContain('request_user_input')
    expect(wrapper.text()).not.toContain('shell_command · approval-timestamp-older')
  })

  it('continues comparing timestamp when pending approvals have the same updated_at and created_at', async () => {
    seedPlan({
      approval_requests: [
        {
          request_id: 'approval-same-created-first',
          status: 'pending',
          tool_name: 'shell_command',
          permission_level: 'elevated',
          updated_at: '2026-05-01T12:00:10Z',
          created_at: '2026-05-01T12:00:02Z',
          timestamp: '2026-05-01T12:00:03Z'
        },
        {
          request_id: 'approval-same-created-second',
          status: 'pending',
          tool_name: 'request_user_input',
          permission_level: 'standard',
          updated_at: '2026-05-01T12:00:10Z',
          created_at: '2026-05-01T12:00:02Z',
          timestamp: '2026-05-01T12:00:09Z'
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('approval-same-created-second')
    expect(wrapper.text()).toContain('request_user_input')
    expect(wrapper.text()).not.toContain('shell_command · approval-same-created-first')
  })

  it('falls back to later list order when pending approval times are equal or missing', async () => {
    seedPlan({
      approval_requests: [
        {
          request_id: 'approval-same-time-first',
          status: 'pending',
          tool_name: 'shell_command',
          permission_level: 'elevated',
          timestamp: '2026-05-01T12:00:10Z'
        },
        {
          request_id: 'approval-same-time-second',
          status: 'pending',
          tool_name: 'request_user_input',
          permission_level: 'standard',
          timestamp: '2026-05-01T12:00:10Z'
        },
        {
          request_id: 'approval-no-time-third',
          status: 'pending',
          tool_name: 'list_mcp_resources',
          permission_level: 'standard'
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('approval-same-time-second')
    expect(wrapper.text()).toContain('request_user_input')
    expect(wrapper.text()).not.toContain('shell_command · approval-same-time-first')

    seedPlan({
      approval_requests: [
        {
          request_id: 'approval-no-time-first',
          status: 'pending',
          tool_name: 'shell_command',
          permission_level: 'elevated'
        },
        {
          request_id: 'approval-no-time-second',
          status: 'pending',
          tool_name: 'request_user_input',
          permission_level: 'standard'
        }
      ]
    })

    const missingTimeWrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(missingTimeWrapper.text()).toContain('approval-no-time-second')
    expect(missingTimeWrapper.text()).toContain('request_user_input')
    expect(missingTimeWrapper.text()).not.toContain('shell_command · approval-no-time-first')
  })

  it('does not render current run card for an empty scheduler run shell', async () => {
    seedPlan({
      scheduler_run: {},
      approval_requests: []
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(wrapper.text()).not.toContain('当前执行实例')
    expect(wrapper.text()).toContain('待处理审批')
    expect(wrapper.text()).toContain('0 个待处理')
  })

  it('sorts overview cards by latest update time', async () => {
    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const overviewCardLabels = wrapper
      .findAllComponents({ name: 'GovernanceTimelineOverviewCards' })
      .at(0)
      .findAll('.governance-overview-card .summary-label')
      .map(item => item.text())

    expect(overviewCardLabels).toEqual([
      'Runtime',
      'Framework Adapter',
      'Learning',
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

    const hookCard = wrapper.findAllComponents({ name: 'GovernanceTimelineOverviewCards' }).at(0).findAll('.governance-overview-card').find(item => item.text().includes('Hook'))
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

  it('renders recent governance snapshot commands from local storage', async () => {
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
        copiedAt: '2026-05-20T10:00:00Z',
      },
    ]))

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('最近治理快照命令')
    expect(wrapper.text()).toContain('/snapshot RUNT-BOOT-321')
    expect(wrapper.text()).toContain('Embedded Runtime Bootstrap 更新')
    expect(wrapper.text()).toContain('workspace_mode=memory_only · runtime=memory_preview')
  })

  it('applies filter when summary cards are clicked', async () => {
    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const permissionSummaryCard = wrapper.findComponent({ name: 'GovernanceTimelineSummaryActionCards' }).findAll('button').find(item => item.text().includes('最近一次权限结果'))
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

    const mcpSummaryCard = wrapper.findComponent({ name: 'GovernanceTimelineSummaryActionCards' }).findAll('button').find(item => item.text().includes('最近一次 MCP 结果'))
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

    const hookSummaryCard = wrapper.findComponent({ name: 'GovernanceTimelineSummaryActionCards' }).findAll('button').find(item => item.text().includes('最近一次 Hook 结果'))
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

    const learningSummaryCard = wrapper.findComponent({ name: 'GovernanceTimelineSummaryActionCards' }).findAll('button').find(item => item.text().includes('最近一次 Learning 结果'))
    expect(learningSummaryCard).toBeTruthy()
    await learningSummaryCard.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('当前筛选')
    expect(wrapper.text()).toContain('Learning')
    expect(wrapper.find('.timeline-list').text()).toContain('Learning `LRN-1` 已应用历史版本')
    expect(wrapper.find('.timeline-list').text()).not.toContain('MCP 服务 `filesystem` 已完成 Probe')
  })

  it('supports Framework Adapter pilot summary card navigation', async () => {
    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const frameworkPilotCard = wrapper.findComponent({ name: 'GovernanceTimelineFrameworkAdapterCards' }).findAll('button').find(item => item.text().includes('最近一次 LocalFakeFramework Pilot'))
    expect(frameworkPilotCard).toBeTruthy()
    await frameworkPilotCard.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('当前筛选')
    expect(wrapper.text()).toContain('Framework Adapter')
    expect(wrapper.find('.timeline-list').text()).toContain('Local fake adapter processed: 请生成一份运行时巡检计划摘要')
    expect(wrapper.find('.timeline-list').text()).not.toContain('Framework adapter `LangGraph` precheck completed')
    expect(wrapper.find('.timeline-list').text()).toContain('引用 FRAM-FRAMEWORK_A-321-20260501120013')
  })

  it('supports Framework Adapter precheck summary card navigation', async () => {
    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const frameworkPrecheckCard = wrapper.findComponent({ name: 'GovernanceTimelineFrameworkAdapterCards' }).findAll('button').find(item => item.text().includes('最近一次 LangGraph Precheck'))
    expect(frameworkPrecheckCard).toBeTruthy()
    await frameworkPrecheckCard.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('当前筛选')
    expect(wrapper.text()).toContain('Framework Adapter')
    expect(wrapper.find('.timeline-list').text()).toContain('Framework adapter `LangGraph` precheck completed')
    expect(wrapper.find('.timeline-list').text()).not.toContain('Local fake adapter processed: 请生成一份运行时巡检计划摘要')
    expect(wrapper.find('.timeline-list').text()).toContain('引用 FRAM-PRECHECK-321-20260501120014')
  })

  it('supports Framework Adapter external pilot summary card navigation', async () => {
    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const frameworkExternalPilotCard = wrapper.findComponent({ name: 'GovernanceTimelineFrameworkAdapterCards' }).findAll('button').find(item => item.text().includes('最近一次 LangGraph External Pilot'))
    expect(frameworkExternalPilotCard).toBeTruthy()
    await frameworkExternalPilotCard.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('当前筛选')
    expect(wrapper.text()).toContain('Framework Adapter')
    expect(wrapper.find('.timeline-list').text()).toContain('Framework Adapter 外部执行失败')
    expect(wrapper.find('.timeline-list').text()).toContain('连通性错误 (connectivity_error)')
    expect(wrapper.find('.timeline-list').text()).not.toContain('Framework adapter `LangGraph` precheck completed')
    expect(wrapper.find('.timeline-list').text()).toContain('引用 FRAM-EXT-ERR-321-20260501120016')
  })

  it('supports Framework Adapter external pilot failure diagnostic summary card navigation', async () => {
    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const frameworkExternalFailureCard = wrapper.findComponent({ name: 'GovernanceTimelineFrameworkAdapterCards' }).findAll('button').find(item => item.text().includes('最近一次 LangGraph External Pilot 失败诊断'))
    expect(frameworkExternalFailureCard).toBeTruthy()
    await frameworkExternalFailureCard.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('当前筛选')
    expect(wrapper.text()).toContain('Framework Adapter')
    expect(wrapper.find('.timeline-list').text()).toContain('Framework Adapter 外部执行失败')
    expect(wrapper.find('.timeline-list').text()).toContain('协议错误 (protocol_error)')
    expect(wrapper.find('.timeline-list').text()).toContain('transport probe did not provide assistant identity evidence')
    expect(wrapper.find('.timeline-list').text()).toContain('引用 FRAM-EXT-DIAG-321-20260501120017')
  })

  it('supports Framework Adapter external pilot failure diagnostic snapshot command copy', async () => {
    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    clipboardWriteTextMock.mockClear()
    const diagnosticCopyButton = wrapper.findComponent({ name: 'GovernanceTimelineFrameworkAdapterCards' }).findAll('button').find(item => item.text().includes('复制快照命令'))
    expect(diagnosticCopyButton).toBeTruthy()
    await diagnosticCopyButton.trigger('click')
    await flushPromises()

    expect(clipboardWriteTextMock).toHaveBeenCalledWith('/snapshot FRAM-EXT-DIAG-321-20260501120017')
    expect(wrapper.text()).toContain('已复制命令')
    expect(wrapper.text()).toContain('最近治理快照命令')
    expect(wrapper.text()).toContain('最近复制：')
    expect(wrapper.text()).toContain('Framework Adapter 外部执行失败诊断')
    expect(wrapper.text()).toContain('协议错误 (protocol_error)')
    expect(wrapper.text()).toContain('/snapshot FRAM-EXT-DIAG-321-20260501120017')
  })

  it('supports Framework Adapter external pilot failure diagnostic runtime navigation', async () => {
    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const diagnosticOpenButton = wrapper.findComponent({ name: 'GovernanceTimelineFrameworkAdapterCards' }).findAll('button').find(item => item.text().includes('打开运行时面板'))
    expect(diagnosticOpenButton).toBeTruthy()
    await diagnosticOpenButton.trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/settings?tab=advanced')
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

    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('快照ID: FRAM-EXT-ERR-321-20260501120016'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('生成时间: 2026-05-01T12:00:16Z'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('治理视图: Hook / 仅告警'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('事件范围: 1 / 4'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('后端引用: framework_adapter / framework_adapter_external_error'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('governance_filter=hook'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('governance_severity=warning'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('tab=advanced'))
    expect(wrapper.text()).toContain('已复制视图')
  })

  it('includes main_chat history search when copying current view', async () => {
    routeQuery.tab = 'advanced'
    routeQuery.governance_filter = 'main_chat'
    getMainChatQueryHistoryMock.mockResolvedValue({
      data: {
        recording_state: 'recorded',
        items: [
          {
            query_id: 'manual-chat-3',
            latest_stage: 'review',
            latest_summary: 'Main chat review 3',
            latest_timestamp: '2026-05-01T12:00:21Z',
            latest_snapshot_id: 'QUER-REVIEW-3',
            stage_counts: { review: 1 },
            last_success_stage: 'review',
            last_warning_stage: '',
            recording_state: 'recorded'
          }
        ],
        page: 1,
        page_size: 5,
        total_items: 1,
        has_more: false,
        next_cursor: '',
        reason: ''
      }
    })
    seedPlan({
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:21Z',
          source: 'query_control',
          event_type: 'query_control_review',
          severity: 'info',
          summary: 'Main chat review 3',
          detail: 'phase=review',
          payload: {
            channel: 'main_chat',
            stage: 'review',
            query_id: 'manual-chat-3',
          }
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const searchInput = wrapper.find('.main-chat-history-search-input')
    await searchInput.setValue('review')
    await flushPromises()

    clipboardWriteTextMock.mockClear()
    const copyViewButton = wrapper.findAll('button').find(item => item.text().includes('复制当前视图'))
    expect(copyViewButton).toBeTruthy()
    await copyViewButton.trigger('click')
    await flushPromises()

    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('History 搜索: review'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('governance_query_search=review'))
  })

  it('includes main_chat history page when copying current view after load more', async () => {
    routeQuery.tab = 'advanced'
    routeQuery.governance_filter = 'main_chat'
    getMainChatQueryHistoryMock
      .mockResolvedValueOnce({
        data: {
          recording_state: 'recorded',
          items: [
            {
              query_id: 'manual-chat-2',
              latest_stage: 'final_output',
              latest_summary: 'Main chat final output 2',
              latest_timestamp: '2026-05-01T12:00:20Z',
              latest_snapshot_id: 'QUER-FINAL-2',
              stage_counts: { final_output: 1 },
              last_success_stage: 'final_output',
              last_warning_stage: '',
              recording_state: 'recorded'
            }
          ],
          page: 1,
          page_size: 5,
          total_items: 2,
          has_more: true,
          next_cursor: '2026-05-01T12:00:20Z|manual-chat-2',
          reason: ''
        }
      })
      .mockResolvedValueOnce({
        data: {
          recording_state: 'recorded',
          items: [
            {
              query_id: 'manual-chat-1',
              latest_stage: 'planning',
              latest_summary: 'Main chat planning 1',
              latest_timestamp: '2026-05-01T12:00:19Z',
              latest_snapshot_id: 'QUER-PLAN-1',
              stage_counts: { planning: 1 },
              last_success_stage: 'planning',
              last_warning_stage: '',
              recording_state: 'recorded'
            }
          ],
          page: 2,
          page_size: 5,
          total_items: 2,
          has_more: false,
          next_cursor: '',
          reason: ''
        }
      })
    seedPlan({
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:20Z',
          source: 'query_control',
          event_type: 'query_control_final_output',
          severity: 'info',
          summary: 'Main chat final output 2',
          detail: 'phase=final_output',
          payload: {
            channel: 'main_chat',
            stage: 'final_output',
            query_id: 'manual-chat-2',
          }
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const loadMoreButton = wrapper.findAll('button').find(item => item.text().includes('加载更多'))
    await loadMoreButton.trigger('click')
    await flushPromises()

    clipboardWriteTextMock.mockClear()
    const copyViewButton = wrapper.findAll('button').find(item => item.text().includes('复制当前视图'))
    await copyViewButton.trigger('click')
    await flushPromises()

    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('History 页: 2'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('governance_query_page=2'))
  })

  it('supports route-driven filter and payload expansion', async () => {
    routeQuery.governance_filter = 'mcp'
    seedPlan({
      audit_trail: [],
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:11Z',
          source: 'mcp',
          event_type: 'mcp_server_probed',
          severity: 'success',
          summary: 'MCP 服务 `filesystem` 已完成 Probe',
          detail: 'server=filesystem status=ok',
          payload: {
            server_name: 'filesystem',
            status: 'ok',
            dedupe_key: 'mcp_server_probed:321:filesystem:ok'
          }
        }
      ]
    })

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

    const copyDedupeKeyButton = wrapper.findAll('button').find(item => item.text().includes('复制幂等键'))
    expect(copyDedupeKeyButton).toBeTruthy()
    await copyDedupeKeyButton.trigger('click')
    await flushPromises()

    expect(clipboardWriteTextMock).toHaveBeenCalledWith('mcp_server_probed:321:filesystem:ok')
    expect(wrapper.text()).toContain('已复制幂等键')
  })

  it('supports route-driven runtime contract warning filter', async () => {
    routeQuery.governance_filter = 'runtime_contract'
    routeQuery.governance_severity = 'warning'
    seedPlan({
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:18Z',
          source: 'runtime_contract',
          event_type: 'runtime_contract_gate_degraded',
          severity: 'warning',
          summary: 'Runtime contract gate degraded',
          detail: 'failed_check_count=1',
          payload: {
            snapshot_ref: {
              snapshot_id: 'RCON-GATE-321-20260501120018',
              generated_at: '2026-05-01T12:00:18Z',
              conversation_id: 321,
              source: 'runtime_contract',
              event_type: 'runtime_contract_gate_degraded'
            },
            overall_status: 'degraded',
            failed_check_count: 1,
            check_name: 'adapter_health_status',
            runtime_contract_summary: {
              missing_payload_count: 2,
              approval_replay_coverage: {
                event_payload_sample: false,
                observed_status_kinds: ['approval_created', 'approval_resolved']
              },
              approval_lifecycle_recovery_coverage: {
                alignment_smoke: true,
                contract_version: 'phase-ii-approval-lifecycle-recovery-v1',
                replayed_submission_status: 'replayed',
                ignored_submission_status: 'ignored',
                resolved_recovery_reason: 'already_resolved'
              },
              approved_tool_execution_coverage: {
                bridge_smoke: true,
                contract_version: 'phase-ii-runtime-approved-tool-execution-v1',
                approved_tool_call_count: 1
              },
              sdk_tool_runtime_execution_coverage: {
                bridge_smoke: true,
                contract_version: 'phase-ii-sdk-tool-runtime-execution-v1',
                approved_tool_call_count: 1
              },
              embedded_sdk_persistence_coverage: {
                persistence_smoke: true,
                contract_version: 'phase-ii-embedded-sdk-persistence-v1',
                durable_cross_process_candidate: true
              },
              worker_ownership_store_mode_coverage: {
                mode_smoke: true,
                contract_version: 'phase-ii-worker-ownership-store-mode-v1',
                default_mode: 'memory_only'
              },
              child_executor_promotion_gate_coverage: {
                gate_smoke: true,
                contract_version: 'phase-ii-child-executor-promotion-gate-v1',
                gate_status: 'blocked'
              },
              child_executor_execution_prerequisites_coverage: {
                prerequisites_smoke: true,
                contract_version: 'phase-ii-child-executor-execution-prerequisites-v1',
                ready: false
              },
              child_executor_dispatch_coverage: {
                dispatch_smoke: true,
                contract_version: 'phase-ii-child-executor-dispatch-v1',
                dispatch_ready: false
              },
              child_executor_dispatcher_coverage: {
                dispatcher_smoke: true,
                contract_version: 'phase-ii-child-executor-dispatcher-v1',
                default_status: 'blocked'
              },
              subagent_lane_query_detail_coverage: {
                detail_smoke: true,
                contract_version: 'phase-h-subagent-lane-query-detail-v1',
                recording_state: 'recorded',
                stage_count: 2,
                recent_event_count: 2
              },
              recovery_retry_evidence_coverage: {
                retry_smoke: true,
                contract_version: 'phase-ii-recovery-retry-protocol-v1',
                retry_status: 'exhausted'
              },
              recovery_retry_scheduler_coverage: {
                scheduler_smoke: true,
                contract_version: 'phase-ii-recovery-retry-scheduler-v1',
                default_status: 'disabled'
              },
              durable_recovery_loader_coverage: {
                loader_smoke: true,
                contract_version: 'phase-ii-durable-recovery-loader-v1',
                loader_status: 'ready'
              },
              checkpoint_resume_cursor_coverage: {
                cursor_smoke: true,
                contract_version: 'phase-ii-durable-checkpoint-resume-v1',
                checkpoint_status: 'ready',
                resume_cursor_status: 'ready'
              }
            }
          }
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('当前筛选')
    expect(wrapper.text()).toContain('Runtime Contract')
    expect(wrapper.text()).toContain('仅告警')
    expect(wrapper.find('.timeline-list').text()).toContain('Runtime contract gate degraded')
    expect(wrapper.find('.timeline-list').text()).toContain('failed_check_count=1')
    expect(wrapper.find('.timeline-list').text()).toContain('runtime_contract=degraded · failed=1 · missing_payloads=2 · approval_replay=missing · approval_lifecycle=covered · approved_tool=covered · sdk_tool=covered · embedded_persistence=covered · worker_ownership=covered · child_executor_gate=covered · child_executor_prerequisites=covered · child_executor_dispatch=covered · child_executor_dispatcher=covered · subagent_detail=covered · recovery_retry=covered · recovery_retry_scheduler=covered · durable_loader=covered · checkpoint_cursor=covered')
    expect(wrapper.find('.timeline-list').text()).not.toContain('Framework adapter `LangGraph` external pilot failed')
  })

  it('supports route-driven main_chat query control filter', async () => {
    routeQuery.governance_filter = 'main_chat'
    getMainChatQueryHistoryMock.mockResolvedValue({
      data: {
        recording_state: 'recorded',
        items: [
          {
            query_id: 'manual-chat-1',
            latest_stage: 'planning',
            latest_summary: 'Main chat planning',
            latest_timestamp: '2026-05-01T12:00:19Z',
            latest_snapshot_id: 'QUER-PLAN-321-20260501120019',
            stage_counts: { planning: 1 },
            last_success_stage: 'planning',
            last_warning_stage: '',
            recording_state: 'recorded'
          }
        ],
        page: 1,
        page_size: 5,
        total_items: 1,
        has_more: false,
        next_cursor: '',
        reason: ''
      }
    })
    seedPlan({
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:19Z',
          source: 'query_control',
          event_type: 'query_control_planning',
          severity: 'info',
          summary: 'Main chat planning',
          detail: 'phase=planning',
          payload: {
            channel: 'main_chat',
            stage: 'planning',
            query_id: 'manual-chat-1',
            snapshot_ref: {
              snapshot_id: 'QUER-PLAN-321-20260501120019',
              generated_at: '2026-05-01T12:00:19Z',
              conversation_id: 321,
              source: 'query_control',
              event_type: 'query_control_planning'
            }
          }
        },
        {
          timestamp: '2026-05-01T12:00:20Z',
          source: 'mcp',
          event_type: 'mcp_server_probed',
          severity: 'info',
          summary: 'MCP 服务 `filesystem` 已完成 Probe',
          detail: 'status=ok',
          payload: {
            server_name: 'filesystem',
            status: 'ok'
          }
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('当前筛选')
    expect(wrapper.text()).toContain('Main Chat')
    expect(wrapper.text()).toContain('Main Chat Query Workspace')
    expect(wrapper.text()).toContain('Main Chat Query History')
    expect(wrapper.text()).toContain('已加载 1 / 总计 1')
    expect(wrapper.text()).toContain('当前页 1')
    expect(wrapper.text()).toContain('manual-chat-1')
    expect(wrapper.find('.main-chat-history-panel').exists()).toBe(true)
    expect(wrapper.find('.main-chat-query-workspace').exists()).toBe(true)
    expect(wrapper.find('.main-chat-history-item.active').exists()).toBe(false)
    expect(wrapper.find('.timeline-list').text()).toContain('Main chat planning')
    expect(wrapper.find('.timeline-list').text()).not.toContain('MCP 服务 `filesystem` 已完成 Probe')
    expect(getMainChatQueryHistoryMock).toHaveBeenCalledWith({
      conversation_id: 321,
      page: 1,
      page_size: 5
    })
  })

  it('restores main_chat query history search from route state', async () => {
    routeQuery.governance_filter = 'main_chat'
    routeQuery.governance_query_search = 'review'
    getMainChatQueryHistoryMock.mockResolvedValue({
      data: {
        recording_state: 'recorded',
        items: [
          {
            query_id: 'manual-chat-3',
            latest_stage: 'review',
            latest_summary: 'Main chat review 3',
            latest_timestamp: '2026-05-01T12:00:21Z',
            latest_snapshot_id: 'QUER-REVIEW-3',
            stage_counts: { review: 1 },
            last_success_stage: 'review',
            last_warning_stage: '',
            recording_state: 'recorded'
          },
          {
            query_id: 'manual-chat-2',
            latest_stage: 'final_output',
            latest_summary: 'Main chat final output 2',
            latest_timestamp: '2026-05-01T12:00:20Z',
            latest_snapshot_id: 'QUER-FINAL-2',
            stage_counts: { final_output: 1 },
            last_success_stage: 'final_output',
            last_warning_stage: '',
            recording_state: 'recorded'
          }
        ],
        page: 1,
        page_size: 5,
        total_items: 2,
        has_more: false,
        next_cursor: '',
        reason: ''
      }
    })
    seedPlan({
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:21Z',
          source: 'query_control',
          event_type: 'query_control_review',
          severity: 'info',
          summary: 'Main chat review 3',
          detail: 'phase=review',
          payload: {
            channel: 'main_chat',
            stage: 'review',
            query_id: 'manual-chat-3',
          }
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const searchInput = wrapper.find('.main-chat-history-search-input')
    expect(searchInput.element.value).toBe('review')
    expect(wrapper.text()).toContain('manual-chat-3')
    expect(wrapper.text()).not.toContain('manual-chat-2')
  })

  it('restores main_chat query history page from route state', async () => {
    routeQuery.governance_filter = 'main_chat'
    routeQuery.governance_query_page = '2'
    getMainChatQueryHistoryMock
      .mockResolvedValueOnce({
        data: {
          recording_state: 'recorded',
          items: [
            {
              query_id: 'manual-chat-2',
              latest_stage: 'final_output',
              latest_summary: 'Main chat final output 2',
              latest_timestamp: '2026-05-01T12:00:20Z',
              latest_snapshot_id: 'QUER-FINAL-2',
              stage_counts: { final_output: 1 },
              last_success_stage: 'final_output',
              last_warning_stage: '',
              recording_state: 'recorded'
            }
          ],
          page: 1,
          page_size: 5,
          total_items: 2,
          has_more: true,
          next_cursor: '2026-05-01T12:00:20Z|manual-chat-2',
          reason: ''
        }
      })
      .mockResolvedValueOnce({
        data: {
          recording_state: 'recorded',
          items: [
            {
              query_id: 'manual-chat-1',
              latest_stage: 'planning',
              latest_summary: 'Main chat planning 1',
              latest_timestamp: '2026-05-01T12:00:19Z',
              latest_snapshot_id: 'QUER-PLAN-1',
              stage_counts: { planning: 1 },
              last_success_stage: 'planning',
              last_warning_stage: '',
              recording_state: 'recorded'
            }
          ],
          page: 2,
          page_size: 5,
          total_items: 2,
          has_more: false,
          next_cursor: '',
          reason: ''
        }
      })
    seedPlan({
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:20Z',
          source: 'query_control',
          event_type: 'query_control_final_output',
          severity: 'info',
          summary: 'Main chat final output 2',
          detail: 'phase=final_output',
          payload: {
            channel: 'main_chat',
            stage: 'final_output',
            query_id: 'manual-chat-2',
          }
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(getMainChatQueryHistoryMock).toHaveBeenNthCalledWith(1, {
      conversation_id: 321,
      page: 1,
      page_size: 5
    })
    expect(getMainChatQueryHistoryMock).toHaveBeenNthCalledWith(2, {
      conversation_id: 321,
      page: 2,
      page_size: 5
    })
  })

  it('supports route-driven main_chat query id filter', async () => {
    routeQuery.governance_filter = 'main_chat'
    routeQuery.governance_query_id = 'manual-chat-2'
    getMainChatQueryHistoryMock.mockResolvedValue({
      data: {
        recording_state: 'recorded',
        items: [
          {
            query_id: 'manual-chat-2',
            latest_stage: 'final_output',
            latest_summary: 'Main chat final output 2',
            latest_timestamp: '2026-05-01T12:00:20Z',
            latest_snapshot_id: 'QUER-FINAL-321-20260501120020',
            stage_counts: { final_output: 1 },
            last_success_stage: 'final_output',
            last_warning_stage: '',
            recording_state: 'recorded'
          }
        ],
        page: 1,
        page_size: 5,
        total_items: 1,
        has_more: false,
        next_cursor: '',
        reason: ''
      }
    })
    getMainChatQueryDetailMock.mockResolvedValue({
      data: {
        query_id: 'manual-chat-2',
        recording_state: 'recorded',
        latest_stage: 'final_output',
        latest_summary: 'Main chat final output 2',
        latest_snapshot_id: 'QUER-FINAL-321-20260501120020',
        latest_warning_summary: '',
        stage_chain: ['planning', 'final_output'],
        dedupe_keys: ['query_control:main_chat:planning:321:manual-chat-2'],
        recent_events: [
          {
            timestamp: '2026-05-01T12:00:19Z',
            stage: 'planning',
            summary: 'Main chat planning 1',
            severity: 'info',
            snapshot_id: '',
            dedupe_key: 'query_control:main_chat:planning:321:manual-chat-2'
          },
          {
            timestamp: '2026-05-01T12:00:20Z',
            stage: 'final_output',
            summary: 'Main chat final output 2',
            severity: 'info',
            snapshot_id: 'QUER-FINAL-321-20260501120020',
            dedupe_key: 'query_control:main_chat:final_output:321:manual-chat-2'
          }
        ],
        stage_count: 2,
        warning_count: 0,
        event_count: 2,
        reason: ''
      }
    })
    seedPlan({
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:19Z',
          source: 'query_control',
          event_type: 'query_control_planning',
          severity: 'info',
          summary: 'Main chat planning 1',
          detail: 'phase=planning',
          payload: {
            channel: 'main_chat',
            stage: 'planning',
            query_id: 'manual-chat-1',
          }
        },
        {
          timestamp: '2026-05-01T12:00:20Z',
          source: 'query_control',
          event_type: 'query_control_final_output',
          severity: 'info',
          summary: 'Main chat final output 2',
          detail: 'phase=final_output',
          payload: {
            channel: 'main_chat',
            stage: 'final_output',
            query_id: 'manual-chat-2',
          }
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('Query 聚焦')
    expect(wrapper.text()).toContain('Query 摘要')
    expect(wrapper.text()).toContain('Query Detail')
    expect(wrapper.text()).toContain('final_output')
    expect(wrapper.text()).toContain('阶段 2 · 告警 0')
    expect(wrapper.text()).toContain('manual-chat-2')
    expect(wrapper.text()).toContain('QUER-FINAL-321-20260501120020')
    expect(wrapper.text()).toContain('最近事件')
    expect(wrapper.find('.main-chat-history-item.active').text()).toContain('manual-chat-2')
    expect(wrapper.find('.timeline-list').text()).toContain('Main chat final output 2')
    expect(wrapper.find('.timeline-list').text()).not.toContain('Main chat planning 1')
    expect(getMainChatQueryDetailMock).toHaveBeenCalledWith({
      conversation_id: 321,
      query_id: 'manual-chat-2'
    })
  })

  it('supports focusing query stage from query detail stage chain', async () => {
    routeQuery.governance_filter = 'main_chat'
    routeQuery.governance_query_id = 'manual-chat-2'
    getMainChatQueryHistoryMock.mockResolvedValue({
      data: {
        recording_state: 'recorded',
        items: [
          {
            query_id: 'manual-chat-2',
            latest_stage: 'final_output',
            latest_summary: 'Main chat final output 2',
            latest_timestamp: '2026-05-01T12:00:20Z',
            latest_snapshot_id: 'QUER-FINAL-321-20260501120020',
            stage_counts: { final_output: 1, planning: 1 },
            last_success_stage: 'final_output',
            last_warning_stage: '',
            recording_state: 'recorded'
          }
        ],
        page: 1,
        page_size: 5,
        total_items: 1,
        has_more: false,
        next_cursor: '',
        reason: ''
      }
    })
    getMainChatQueryDetailMock.mockResolvedValue({
      data: {
        query_id: 'manual-chat-2',
        recording_state: 'recorded',
        latest_stage: 'final_output',
        latest_summary: 'Main chat final output 2',
        latest_snapshot_id: 'QUER-FINAL-321-20260501120020',
        latest_warning_summary: '',
        stage_chain: ['planning', 'final_output'],
        dedupe_keys: ['query_control:main_chat:planning:321:manual-chat-2'],
        recent_events: [
          {
            timestamp: '2026-05-01T12:00:19Z',
            stage: 'planning',
            summary: 'Main chat planning 1',
            severity: 'info',
            snapshot_id: '',
            dedupe_key: 'query_control:main_chat:planning:321:manual-chat-2'
          },
          {
            timestamp: '2026-05-01T12:00:20Z',
            stage: 'final_output',
            summary: 'Main chat final output 2',
            severity: 'info',
            snapshot_id: 'QUER-FINAL-321-20260501120020',
            dedupe_key: 'query_control:main_chat:final_output:321:manual-chat-2'
          }
        ],
        stage_count: 2,
        warning_count: 0,
        event_count: 2,
        reason: ''
      }
    })
    seedPlan({
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:19Z',
          source: 'query_control',
          event_type: 'query_control_planning',
          severity: 'info',
          summary: 'Main chat planning 1',
          detail: 'phase=planning',
          payload: {
            channel: 'main_chat',
            stage: 'planning',
            query_id: 'manual-chat-2',
          }
        },
        {
          timestamp: '2026-05-01T12:00:20Z',
          source: 'query_control',
          event_type: 'query_control_final_output',
          severity: 'info',
          summary: 'Main chat final output 2',
          detail: 'phase=final_output',
          payload: {
            channel: 'main_chat',
            stage: 'final_output',
            query_id: 'manual-chat-2',
          }
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const planningChip = wrapper.findAll('.query-stage-chip').find(item => item.text().includes('planning'))
    expect(planningChip).toBeTruthy()

    await planningChip.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('阶段聚焦')
    expect(wrapper.find('.main-chat-history-context').text()).toContain('manual-chat-2 / planning')
    expect(wrapper.find('.main-chat-history-item.stage-focused').exists()).toBe(true)
    expect(wrapper.find('.main-chat-history-stage-tag.active').text()).toContain('planning 1')
    expect(wrapper.find('.timeline-list').text()).toContain('Main chat planning 1')
    expect(wrapper.find('.timeline-list').text()).not.toContain('Main chat final output 2')
  })

  it('supports focusing query stage from query detail recent events', async () => {
    routeQuery.governance_filter = 'main_chat'
    routeQuery.governance_query_id = 'manual-chat-2'
    getMainChatQueryHistoryMock.mockResolvedValue({
      data: {
        recording_state: 'recorded',
        items: [
          {
            query_id: 'manual-chat-2',
            latest_stage: 'final_output',
            latest_summary: 'Main chat final output 2',
            latest_timestamp: '2026-05-01T12:00:20Z',
            latest_snapshot_id: 'QUER-FINAL-321-20260501120020',
            stage_counts: { final_output: 1, planning: 1 },
            last_success_stage: 'final_output',
            last_warning_stage: '',
            recording_state: 'recorded'
          }
        ],
        page: 1,
        page_size: 5,
        total_items: 1,
        has_more: false,
        next_cursor: '',
        reason: ''
      }
    })
    getMainChatQueryDetailMock.mockResolvedValue({
      data: {
        query_id: 'manual-chat-2',
        recording_state: 'recorded',
        latest_stage: 'final_output',
        latest_summary: 'Main chat final output 2',
        latest_snapshot_id: 'QUER-FINAL-321-20260501120020',
        latest_warning_summary: '',
        stage_chain: ['planning', 'final_output'],
        dedupe_keys: ['query_control:main_chat:planning:321:manual-chat-2'],
        recent_events: [
          {
            timestamp: '2026-05-01T12:00:19Z',
            stage: 'planning',
            summary: 'Main chat planning 1',
            severity: 'info',
            snapshot_id: '',
            dedupe_key: 'query_control:main_chat:planning:321:manual-chat-2'
          },
          {
            timestamp: '2026-05-01T12:00:20Z',
            stage: 'final_output',
            summary: 'Main chat final output 2',
            severity: 'info',
            snapshot_id: 'QUER-FINAL-321-20260501120020',
            dedupe_key: 'query_control:main_chat:final_output:321:manual-chat-2'
          }
        ],
        stage_count: 2,
        warning_count: 0,
        event_count: 2,
        reason: ''
      }
    })
    seedPlan({
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:19Z',
          source: 'query_control',
          event_type: 'query_control_planning',
          severity: 'info',
          summary: 'Main chat planning 1',
          detail: 'phase=planning',
          payload: {
            channel: 'main_chat',
            stage: 'planning',
            query_id: 'manual-chat-2',
          }
        },
        {
          timestamp: '2026-05-01T12:00:20Z',
          source: 'query_control',
          event_type: 'query_control_final_output',
          severity: 'info',
          summary: 'Main chat final output 2',
          detail: 'phase=final_output',
          payload: {
            channel: 'main_chat',
            stage: 'final_output',
            query_id: 'manual-chat-2',
          }
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const planningEventLink = wrapper.findAll('.query-detail-event-link').find(item => item.text().includes('Main chat planning 1'))
    expect(planningEventLink).toBeTruthy()

    await planningEventLink.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('阶段聚焦')
    expect(wrapper.find('.timeline-list').text()).toContain('Main chat planning 1')
    expect(wrapper.find('.timeline-list').text()).not.toContain('Main chat final output 2')
  })

  it('supports focusing query stage directly from history stage tags', async () => {
    routeQuery.governance_filter = 'main_chat'
    getMainChatQueryHistoryMock.mockResolvedValue({
      data: {
        recording_state: 'recorded',
        items: [
          {
            query_id: 'manual-chat-2',
            latest_stage: 'final_output',
            latest_summary: 'Main chat final output 2',
            latest_timestamp: '2026-05-01T12:00:20Z',
            latest_snapshot_id: 'QUER-FINAL-321-20260501120020',
            stage_counts: { final_output: 1, planning: 1 },
            last_success_stage: 'final_output',
            last_warning_stage: '',
            recording_state: 'recorded'
          }
        ],
        page: 1,
        page_size: 5,
        total_items: 1,
        has_more: false,
        next_cursor: '',
        reason: ''
      }
    })
    getMainChatQueryDetailMock.mockResolvedValue({
      data: {
        query_id: 'manual-chat-2',
        recording_state: 'recorded',
        latest_stage: 'final_output',
        latest_summary: 'Main chat final output 2',
        latest_snapshot_id: 'QUER-FINAL-321-20260501120020',
        latest_warning_summary: '',
        stage_chain: ['planning', 'final_output'],
        dedupe_keys: ['query_control:main_chat:planning:321:manual-chat-2'],
        recent_events: [
          {
            timestamp: '2026-05-01T12:00:19Z',
            stage: 'planning',
            summary: 'Main chat planning 1',
            severity: 'info',
            snapshot_id: '',
            dedupe_key: 'query_control:main_chat:planning:321:manual-chat-2'
          },
          {
            timestamp: '2026-05-01T12:00:20Z',
            stage: 'final_output',
            summary: 'Main chat final output 2',
            severity: 'info',
            snapshot_id: 'QUER-FINAL-321-20260501120020',
            dedupe_key: 'query_control:main_chat:final_output:321:manual-chat-2'
          }
        ],
        stage_count: 2,
        warning_count: 0,
        event_count: 2,
        reason: ''
      }
    })
    seedPlan({
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:19Z',
          source: 'query_control',
          event_type: 'query_control_planning',
          severity: 'info',
          summary: 'Main chat planning 1',
          detail: 'phase=planning',
          payload: {
            channel: 'main_chat',
            stage: 'planning',
            query_id: 'manual-chat-2',
          }
        },
        {
          timestamp: '2026-05-01T12:00:20Z',
          source: 'query_control',
          event_type: 'query_control_final_output',
          severity: 'info',
          summary: 'Main chat final output 2',
          detail: 'phase=final_output',
          payload: {
            channel: 'main_chat',
            stage: 'final_output',
            query_id: 'manual-chat-2',
          }
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const planningTag = wrapper.findAll('.main-chat-history-stage-tag').find(item => item.text().includes('planning 1'))
    expect(planningTag).toBeTruthy()

    await planningTag.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Query 聚焦')
    expect(wrapper.text()).toContain('阶段聚焦')
    expect(wrapper.find('.main-chat-history-context').text()).toContain('manual-chat-2 / planning')
    expect(wrapper.find('.timeline-list').text()).toContain('Main chat planning 1')
    expect(wrapper.find('.timeline-list').text()).not.toContain('Main chat final output 2')
  })

  it('supports clicking main_chat history item to enter query drill-down', async () => {
    routeQuery.governance_filter = 'main_chat'
    getMainChatQueryHistoryMock.mockResolvedValue({
      data: {
        recording_state: 'recorded',
        items: [
          {
            query_id: 'manual-chat-1',
            latest_stage: 'planning',
            latest_summary: 'Main chat planning 1',
            latest_timestamp: '2026-05-01T12:00:19Z',
            latest_snapshot_id: 'QUER-PLAN-321-20260501120019',
            stage_counts: { planning: 1 },
            last_success_stage: 'planning',
            last_warning_stage: '',
            recording_state: 'recorded'
          },
          {
            query_id: 'manual-chat-2',
            latest_stage: 'final_output',
            latest_summary: 'Main chat final output 2',
            latest_timestamp: '2026-05-01T12:00:20Z',
            latest_snapshot_id: 'QUER-FINAL-321-20260501120020',
            stage_counts: { final_output: 1 },
            last_success_stage: 'final_output',
            last_warning_stage: '',
            recording_state: 'recorded'
          }
        ],
        page: 1,
        page_size: 5,
        total_items: 2,
        has_more: false,
        next_cursor: '',
        reason: ''
      }
    })
    getMainChatQueryDetailMock.mockResolvedValue({
      data: {
        query_id: 'manual-chat-2',
        recording_state: 'recorded',
        latest_stage: 'final_output',
        latest_summary: 'Main chat final output 2',
        latest_snapshot_id: 'QUER-FINAL-321-20260501120020',
        latest_warning_summary: '',
        stage_chain: ['planning', 'final_output'],
        dedupe_keys: ['query_control:main_chat:planning:321:manual-chat-2'],
        recent_events: [
          {
            timestamp: '2026-05-01T12:00:20Z',
            stage: 'final_output',
            summary: 'Main chat final output 2',
            severity: 'info',
            snapshot_id: 'QUER-FINAL-321-20260501120020',
            dedupe_key: 'query_control:main_chat:final_output:321:manual-chat-2'
          }
        ],
        stage_count: 2,
        warning_count: 0,
        event_count: 1,
        reason: ''
      }
    })
    seedPlan({
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:19Z',
          source: 'query_control',
          event_type: 'query_control_planning',
          severity: 'info',
          summary: 'Main chat planning 1',
          detail: 'phase=planning',
          payload: {
            channel: 'main_chat',
            stage: 'planning',
            query_id: 'manual-chat-1',
          }
        },
        {
          timestamp: '2026-05-01T12:00:20Z',
          source: 'query_control',
          event_type: 'query_control_final_output',
          severity: 'info',
          summary: 'Main chat final output 2',
          detail: 'phase=final_output',
          payload: {
            channel: 'main_chat',
            stage: 'final_output',
            query_id: 'manual-chat-2',
          }
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const historyButton = wrapper.findAll('.main-chat-history-entry').find(item => item.text().includes('manual-chat-2'))
    expect(historyButton).toBeTruthy()

    await historyButton.trigger('click')
    await flushPromises()

    expect(getMainChatQueryDetailMock).toHaveBeenCalledWith({
      conversation_id: 321,
      query_id: 'manual-chat-2'
    })
    expect(wrapper.text()).toContain('Query Detail')
    expect(wrapper.text()).toContain('Main Chat Query Workspace')
    expect(wrapper.find('.main-chat-history-item.active').text()).toContain('manual-chat-2')
  })

  it('supports filtering loaded main_chat history items locally', async () => {
    routeQuery.governance_filter = 'main_chat'
    getMainChatQueryHistoryMock.mockResolvedValue({
      data: {
        recording_state: 'recorded',
        items: [
          {
            query_id: 'manual-chat-1',
            latest_stage: 'planning',
            latest_summary: 'Main chat planning 1',
            latest_timestamp: '2026-05-01T12:00:19Z',
            latest_snapshot_id: 'QUER-PLAN-321-20260501120019',
            stage_counts: { planning: 1 },
            last_success_stage: 'planning',
            last_warning_stage: '',
            recording_state: 'recorded'
          },
          {
            query_id: 'manual-chat-2',
            latest_stage: 'final_output',
            latest_summary: 'Main chat final output 2',
            latest_timestamp: '2026-05-01T12:00:20Z',
            latest_snapshot_id: 'QUER-FINAL-321-20260501120020',
            stage_counts: { final_output: 1 },
            last_success_stage: 'final_output',
            last_warning_stage: '',
            recording_state: 'recorded'
          }
        ],
        page: 1,
        page_size: 5,
        total_items: 2,
        has_more: false,
        next_cursor: '',
        reason: ''
      }
    })
    seedPlan({
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:19Z',
          source: 'query_control',
          event_type: 'query_control_planning',
          severity: 'info',
          summary: 'Main chat planning 1',
          detail: 'phase=planning',
          payload: {
            channel: 'main_chat',
            stage: 'planning',
            query_id: 'manual-chat-1',
          }
        },
        {
          timestamp: '2026-05-01T12:00:20Z',
          source: 'query_control',
          event_type: 'query_control_final_output',
          severity: 'info',
          summary: 'Main chat final output 2',
          detail: 'phase=final_output',
          payload: {
            channel: 'main_chat',
            stage: 'final_output',
            query_id: 'manual-chat-2',
          }
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const searchInput = wrapper.find('.main-chat-history-search-input')
    expect(searchInput.exists()).toBe(true)

    await searchInput.setValue('final_output')
    await flushPromises()

    const historyPanelText = wrapper.find('.main-chat-history-panel').text()
    expect(historyPanelText).toContain('manual-chat-2')
    expect(historyPanelText).not.toContain('manual-chat-1')
    expect(getMainChatQueryHistoryMock).toHaveBeenCalledTimes(1)
  })

  it('clears main_chat history search from panel action', async () => {
    routeQuery.governance_filter = 'main_chat'
    getMainChatQueryHistoryMock.mockResolvedValue({
      data: {
        recording_state: 'recorded',
        items: [
          {
            query_id: 'manual-chat-1',
            latest_stage: 'planning',
            latest_summary: 'Main chat planning 1',
            latest_timestamp: '2026-05-01T12:00:19Z',
            latest_snapshot_id: 'QUER-PLAN-321-20260501120019',
            stage_counts: { planning: 1 },
            last_success_stage: 'planning',
            last_warning_stage: '',
            recording_state: 'recorded'
          },
          {
            query_id: 'manual-chat-2',
            latest_stage: 'final_output',
            latest_summary: 'Main chat final output 2',
            latest_timestamp: '2026-05-01T12:00:20Z',
            latest_snapshot_id: 'QUER-FINAL-321-20260501120020',
            stage_counts: { final_output: 1 },
            last_success_stage: 'final_output',
            last_warning_stage: '',
            recording_state: 'recorded'
          }
        ],
        page: 1,
        page_size: 5,
        total_items: 2,
        has_more: false,
        next_cursor: '',
        reason: ''
      }
    })
    seedPlan({
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:19Z',
          source: 'query_control',
          event_type: 'query_control_planning',
          severity: 'info',
          summary: 'Main chat planning 1',
          detail: 'phase=planning',
          payload: {
            channel: 'main_chat',
            stage: 'planning',
            query_id: 'manual-chat-1',
          }
        },
        {
          timestamp: '2026-05-01T12:00:20Z',
          source: 'query_control',
          event_type: 'query_control_final_output',
          severity: 'info',
          summary: 'Main chat final output 2',
          detail: 'phase=final_output',
          payload: {
            channel: 'main_chat',
            stage: 'final_output',
            query_id: 'manual-chat-2',
          }
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const searchInput = wrapper.find('.main-chat-history-search-input')
    await searchInput.setValue('final_output')
    await flushPromises()

    expect(wrapper.find('.main-chat-history-panel').text()).not.toContain('manual-chat-1')

    const clearSearchButton = wrapper.findAll('button').find(item => item.text().includes('清除搜索'))
    expect(clearSearchButton).toBeTruthy()
    await clearSearchButton.trigger('click')
    await flushPromises()

    expect(wrapper.find('.main-chat-history-search-input').element.value).toBe('')
    expect(wrapper.find('.main-chat-history-panel').text()).toContain('manual-chat-1')
  })

  it('loads more main_chat query history items inside governance timeline', async () => {
    routeQuery.governance_filter = 'main_chat'
    getMainChatQueryHistoryMock
      .mockResolvedValueOnce({
        data: {
          recording_state: 'recorded',
          items: [
            {
              query_id: 'manual-chat-2',
              latest_stage: 'final_output',
              latest_summary: 'Main chat final output 2',
              latest_timestamp: '2026-05-01T12:00:20Z',
              latest_snapshot_id: 'QUER-FINAL-321-20260501120020',
              stage_counts: { final_output: 1 },
              last_success_stage: 'final_output',
              last_warning_stage: '',
              recording_state: 'recorded'
            }
          ],
          page: 1,
          page_size: 5,
          total_items: 2,
          has_more: true,
          next_cursor: '2026-05-01T12:00:20Z|manual-chat-2',
          reason: ''
        }
      })
      .mockResolvedValueOnce({
        data: {
          recording_state: 'recorded',
          items: [
            {
              query_id: 'manual-chat-1',
              latest_stage: 'planning',
              latest_summary: 'Main chat planning 1',
              latest_timestamp: '2026-05-01T12:00:19Z',
              latest_snapshot_id: 'QUER-PLAN-321-20260501120019',
              stage_counts: { planning: 1 },
              last_success_stage: 'planning',
              last_warning_stage: '',
              recording_state: 'recorded'
            }
          ],
          page: 2,
          page_size: 5,
          total_items: 2,
          has_more: false,
          next_cursor: '',
          reason: ''
        }
      })
    seedPlan({
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:19Z',
          source: 'query_control',
          event_type: 'query_control_planning',
          severity: 'info',
          summary: 'Main chat planning 1',
          detail: 'phase=planning',
          payload: {
            channel: 'main_chat',
            stage: 'planning',
            query_id: 'manual-chat-1',
          }
        },
        {
          timestamp: '2026-05-01T12:00:20Z',
          source: 'query_control',
          event_type: 'query_control_final_output',
          severity: 'info',
          summary: 'Main chat final output 2',
          detail: 'phase=final_output',
          payload: {
            channel: 'main_chat',
            stage: 'final_output',
            query_id: 'manual-chat-2',
          }
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const loadMoreButton = wrapper.findAll('button').find(item => item.text().includes('加载更多'))
    expect(loadMoreButton).toBeTruthy()

    await loadMoreButton.trigger('click')
    await flushPromises()

    expect(getMainChatQueryHistoryMock).toHaveBeenCalledWith({
      conversation_id: 321,
      page: 2,
      page_size: 5
    })
    expect(wrapper.text()).toContain('Main chat planning 1')
  })

  it('supports focusing query from a main_chat timeline event', async () => {
    routeQuery.governance_filter = 'main_chat'
    getMainChatQueryHistoryMock.mockResolvedValue({
      data: {
        recording_state: 'recorded',
        items: [
          {
            query_id: 'manual-chat-2',
            latest_stage: 'final_output',
            latest_summary: 'Main chat final output 2',
            latest_timestamp: '2026-05-01T12:00:20Z',
            latest_snapshot_id: 'QUER-FINAL-321-20260501120020',
            stage_counts: { final_output: 1 },
            last_success_stage: 'final_output',
            last_warning_stage: '',
            recording_state: 'recorded'
          }
        ],
        page: 1,
        page_size: 5,
        total_items: 1,
        has_more: false,
        next_cursor: '',
        reason: ''
      }
    })
    getMainChatQueryDetailMock.mockResolvedValue({
      data: {
        query_id: 'manual-chat-2',
        recording_state: 'recorded',
        latest_stage: 'final_output',
        latest_summary: 'Main chat final output 2',
        latest_snapshot_id: 'QUER-FINAL-321-20260501120020',
        latest_warning_summary: '',
        stage_chain: ['planning', 'final_output'],
        dedupe_keys: ['query_control:main_chat:planning:321:manual-chat-2'],
        recent_events: [
          {
            timestamp: '2026-05-01T12:00:20Z',
            stage: 'final_output',
            summary: 'Main chat final output 2',
            severity: 'info',
            snapshot_id: 'QUER-FINAL-321-20260501120020',
            dedupe_key: 'query_control:main_chat:final_output:321:manual-chat-2'
          }
        ],
        stage_count: 2,
        warning_count: 0,
        event_count: 1,
        reason: ''
      }
    })
    seedPlan({
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:20Z',
          source: 'query_control',
          event_type: 'query_control_final_output',
          severity: 'info',
          summary: 'Main chat final output 2',
          detail: 'phase=final_output',
          payload: {
            channel: 'main_chat',
            stage: 'final_output',
            query_id: 'manual-chat-2',
          }
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const focusQueryButton = wrapper.findAll('button').find(item => item.text().includes('聚焦 Query'))
    expect(focusQueryButton).toBeTruthy()

    await focusQueryButton.trigger('click')
    await flushPromises()

    expect(getMainChatQueryDetailMock).toHaveBeenCalledWith({
      conversation_id: 321,
      query_id: 'manual-chat-2'
    })
    expect(wrapper.text()).toContain('Query Detail')
    expect(wrapper.find('.main-chat-history-item.active').text()).toContain('manual-chat-2')
  })

  it('shows main_chat history error state inside governance timeline', async () => {
    routeQuery.governance_filter = 'main_chat'
    getMainChatQueryHistoryMock.mockRejectedValueOnce(new Error('history request failed'))
    seedPlan({
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:19Z',
          source: 'query_control',
          event_type: 'query_control_planning',
          severity: 'info',
          summary: 'Main chat planning 1',
          detail: 'phase=planning',
          payload: {
            channel: 'main_chat',
            stage: 'planning',
            query_id: 'manual-chat-1',
          }
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('Main Chat Query History')
    expect(wrapper.text()).toContain('Query history 加载失败')
    expect(wrapper.text()).toContain('history request failed')
    expect(wrapper.find('.main-chat-history-panel').exists()).toBe(true)
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
    expect(wrapper.text()).toContain('最近治理快照命令')
    expect(wrapper.text()).toContain('最近复制：')
    expect(wrapper.text()).toContain('MCP Probe 完成')
    expect(wrapper.text()).toContain('status=ok')
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
    const severityFocusLabel = wrapper.find('.severity-focus-label')
    expect(severityFocusLabel.exists()).toBe(true)
    expect(severityFocusLabel.text()).toBe('仅告警')
    expect(severityFocusLabel.attributes('title')).toBe('warning')
    expect(severityFocusLabel.attributes('aria-label')).toBe('风险模式 仅告警')
    expect(wrapper.text()).not.toContain('自动聚焦')
    expect(wrapper.find('.timeline-list').text()).toContain('Doctor `capability_gap` 门禁未通过')
    expect(wrapper.find('.timeline-list').text()).toContain('Hook 已阻断高风险工具调用')
    expect(wrapper.find('.timeline-list').text()).not.toContain('调度器已完成结果合并')
    expect(wrapper.find('.timeline-list').text()).not.toContain('MCP 服务 `filesystem` 已完成 Probe')
  })

  it('supports route-driven framework adapter error type filtering', async () => {
    routeQuery.governance_filter = 'framework_adapter'
    routeQuery.governance_severity = 'warning'
    routeQuery.governance_error_type = 'protocol_error'

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('错误类型')
    expect(wrapper.text()).toContain('协议错误 (protocol_error)')
    const filterFocusLabel = wrapper.find('.filter-focus-label')
    expect(filterFocusLabel.exists()).toBe(true)
    expect(filterFocusLabel.text()).toBe('Framework Adapter')
    expect(filterFocusLabel.attributes('title')).toBe('framework_adapter')
    expect(filterFocusLabel.attributes('aria-label')).toBe('当前筛选 Framework Adapter')
    expect(wrapper.find('.timeline-list').text()).toContain('协议错误 (protocol_error)')
    expect(wrapper.find('.timeline-list').text()).not.toContain('连通性错误 (connectivity_error)')
    const errorTypeFocusLabel = wrapper.find('.framework-error-type-focus-label')
    expect(errorTypeFocusLabel.exists()).toBe(true)
    expect(errorTypeFocusLabel.text()).toBe('协议错误 (protocol_error)')
    expect(errorTypeFocusLabel.attributes('title')).toBe('protocol_error')
    expect(errorTypeFocusLabel.attributes('aria-label')).toBe('错误类型 协议错误 (protocol_error)')
    const clearErrorTypeButton = wrapper.findAll('button').find(item => item.text().includes('清除错误类型'))
    expect(clearErrorTypeButton).toBeTruthy()
    expect(clearErrorTypeButton.attributes('title')).toBe('protocol_error')
    expect(clearErrorTypeButton.attributes('aria-label')).toBe('清除错误类型 协议错误 (protocol_error)')

    clipboardWriteTextMock.mockClear()
    const copyViewButton = wrapper.findAll('button').find(item => item.text().includes('复制当前视图'))
    expect(copyViewButton).toBeTruthy()
    await copyViewButton.trigger('click')
    await flushPromises()

    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('governance_error_type=protocol_error'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('错误类型: 协议错误 (protocol_error)'))
  })

  it('supports route-driven dedupe key filtering and copied view links', async () => {
    routeQuery.governance_filter = 'framework_adapter'
    routeQuery.governance_dedupe_key = 'framework_adapter_external_error:321:langgraph_draft:connectivity_error:connect failed'
    seedPlan({
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:16Z',
          source: 'framework_adapter',
          event_type: 'framework_adapter_external_error',
          severity: 'warning',
          summary: 'Framework adapter `LangGraph` external pilot failed',
          detail: 'connect failed',
          payload: {
            adapter_id: 'langgraph_draft',
            framework_name: 'LangGraph',
            error_type: 'connectivity_error',
            detail: 'connect failed',
            dedupe_key: 'framework_adapter_external_error:321:langgraph_draft:connectivity_error:connect failed'
          }
        },
        {
          timestamp: '2026-05-01T12:00:17Z',
          source: 'framework_adapter',
          event_type: 'framework_adapter_external_error',
          severity: 'warning',
          summary: 'Framework adapter `LangGraph` external pilot failed',
          detail: 'transport probe failed',
          payload: {
            adapter_id: 'langgraph_draft',
            framework_name: 'LangGraph',
            error_type: 'protocol_error',
            detail: 'transport probe failed',
            dedupe_key: 'framework_adapter_external_error:321:langgraph_draft:protocol_error:transport probe failed'
          }
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('幂等键')
    expect(wrapper.text()).toContain('匹配事件 1 / 2')
    expect(wrapper.text()).toContain('connect failed')
    expect(wrapper.find('.timeline-list').text()).toContain('连通性错误 (connectivity_error)')
    expect(wrapper.find('.timeline-list').text()).not.toContain('协议错误 (protocol_error)')
    const dedupeFocusPreview = wrapper.find('.dedupe-focus-preview')
    expect(dedupeFocusPreview.exists()).toBe(true)
    expect(dedupeFocusPreview.attributes('title')).toBe('framework_adapter_external_error:321:langgraph_draft:connectivity_error:connect failed')
    expect(dedupeFocusPreview.attributes('aria-label')).toBe('幂等键聚焦 framework_adapter_external_error:321:langgraph_draft:connectivity_error:connect failed')
    const dedupeMatchCount = wrapper.find('.dedupe-focus-match-count')
    expect(dedupeMatchCount.exists()).toBe(true)
    expect(dedupeMatchCount.text()).toBe('匹配事件 1 / 2')
    expect(dedupeMatchCount.attributes('aria-label')).toBe('幂等键匹配事件 1 / 2')

    clipboardWriteTextMock.mockClear()
    const copyViewButton = wrapper.findAll('button').find(item => item.text().includes('复制当前视图'))
    expect(copyViewButton).toBeTruthy()
    await copyViewButton.trigger('click')
    await flushPromises()

    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('governance_dedupe_key=framework_adapter_external_error%3A321%3Alanggraph_draft%3Aconnectivity_error%3Aconnect+failed'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('幂等键: framework_adapter_external_error:321:langgraph_draft:connectivity_error:connect failed'))
    expect(clipboardWriteTextMock).toHaveBeenCalledWith(expect.stringContaining('幂等键匹配: 匹配事件 1 / 2'))
  })

  it('copies active route-driven dedupe key from the summary focus card', async () => {
    routeQuery.governance_filter = 'framework_adapter'
    routeQuery.governance_dedupe_key = 'framework_adapter_external_error:321:langgraph_draft:connectivity_error:connect failed'
    seedPlan({
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:16Z',
          source: 'framework_adapter',
          event_type: 'framework_adapter_external_error',
          severity: 'warning',
          summary: 'Framework adapter `LangGraph` external pilot failed',
          detail: 'connect failed',
          payload: {
            adapter_id: 'langgraph_draft',
            framework_name: 'LangGraph',
            error_type: 'connectivity_error',
            detail: 'connect failed',
            dedupe_key: 'framework_adapter_external_error:321:langgraph_draft:connectivity_error:connect failed'
          }
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    clipboardWriteTextMock.mockClear()
    const summaryCopyButton = wrapper.findAll('button').find(item => item.text().includes('复制当前幂等键'))
    expect(summaryCopyButton).toBeTruthy()
    expect(summaryCopyButton.attributes('title')).toBe('framework_adapter_external_error:321:langgraph_draft:connectivity_error:connect failed')
    expect(summaryCopyButton.attributes('aria-label')).toBe('复制当前幂等键 framework_adapter_external_error:321:langgraph_draft:connectivity_error:connect failed')
    const summaryClearButton = wrapper.findAll('button').find(item => item.text().includes('清除幂等键'))
    expect(summaryClearButton).toBeTruthy()
    expect(summaryClearButton.attributes('title')).toBe('framework_adapter_external_error:321:langgraph_draft:connectivity_error:connect failed')
    expect(summaryClearButton.attributes('aria-label')).toBe('清除幂等键 framework_adapter_external_error:321:langgraph_draft:connectivity_error:connect failed')

    await summaryCopyButton.trigger('click')
    await flushPromises()

    expect(clipboardWriteTextMock).toHaveBeenCalledWith('framework_adapter_external_error:321:langgraph_draft:connectivity_error:connect failed')
    expect(wrapper.text()).toContain('已复制当前幂等键')
    const copiedSummaryCopyButton = wrapper.findAll('button').find(item => item.text().includes('已复制当前幂等键'))
    expect(copiedSummaryCopyButton.attributes('aria-label')).toBe('已复制当前幂等键 framework_adapter_external_error:321:langgraph_draft:connectivity_error:connect failed')
  })

  it('resets active dedupe key copied state when focusing another dedupe key', async () => {
    routeQuery.governance_filter = 'framework_adapter'
    routeQuery.governance_dedupe_key = 'framework_adapter_external_error:321:langgraph_draft:connectivity_error:connect failed'
    seedPlan({
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:16Z',
          source: 'framework_adapter',
          event_type: 'framework_adapter_external_error',
          severity: 'warning',
          summary: 'Framework adapter `LangGraph` external pilot failed',
          detail: 'connect failed',
          payload: {
            adapter_id: 'langgraph_draft',
            framework_name: 'LangGraph',
            error_type: 'connectivity_error',
            detail: 'connect failed',
            dedupe_key: 'framework_adapter_external_error:321:langgraph_draft:connectivity_error:connect failed'
          }
        },
        {
          timestamp: '2026-05-01T12:00:17Z',
          source: 'framework_adapter',
          event_type: 'framework_adapter_external_error',
          severity: 'warning',
          summary: 'Framework adapter `LangGraph` external pilot failed',
          detail: 'transport probe failed',
          payload: {
            adapter_id: 'langgraph_draft',
            framework_name: 'LangGraph',
            error_type: 'protocol_error',
            detail: 'transport probe failed',
            dedupe_key: 'framework_adapter_external_error:321:langgraph_draft:protocol_error:transport probe failed'
          }
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const summaryCopyButton = wrapper.findAll('button').find(item => item.text().includes('复制当前幂等键'))
    expect(summaryCopyButton).toBeTruthy()
    await summaryCopyButton.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('已复制当前幂等键')

    const clearButton = wrapper.findAll('button').find(item => item.text().includes('清除幂等键'))
    expect(clearButton).toBeTruthy()
    await clearButton.trigger('click')
    await flushPromises()

    const focusButtons = wrapper.findAll('button').filter(item => item.text().includes('聚焦幂等键'))
    expect(focusButtons.length).toBeGreaterThan(0)
    await focusButtons[0].trigger('click')
    await flushPromises()

    expect(wrapper.text()).not.toContain('已复制当前幂等键')
    expect(wrapper.text()).toContain('复制当前幂等键')
  })

  it('focuses timeline by dedupe key from an event card action', async () => {
    routeQuery.governance_filter = 'framework_adapter'
    seedPlan({
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:16Z',
          source: 'framework_adapter',
          event_type: 'framework_adapter_external_error',
          severity: 'warning',
          summary: 'Framework adapter `LangGraph` external pilot failed',
          detail: 'connect failed',
          payload: {
            adapter_id: 'langgraph_draft',
            framework_name: 'LangGraph',
            error_type: 'connectivity_error',
            detail: 'connect failed',
            dedupe_key: 'framework_adapter_external_error:321:langgraph_draft:connectivity_error:connect failed'
          }
        },
        {
          timestamp: '2026-05-01T12:00:17Z',
          source: 'framework_adapter',
          event_type: 'framework_adapter_external_error',
          severity: 'warning',
          summary: 'Framework adapter `LangGraph` external pilot failed',
          detail: 'transport probe failed',
          payload: {
            adapter_id: 'langgraph_draft',
            framework_name: 'LangGraph',
            error_type: 'protocol_error',
            detail: 'transport probe failed',
            dedupe_key: 'framework_adapter_external_error:321:langgraph_draft:protocol_error:transport probe failed'
          }
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(wrapper.find('.timeline-list').text()).toContain('连通性错误 (connectivity_error)')
    expect(wrapper.find('.timeline-list').text()).toContain('协议错误 (protocol_error)')

    const focusButtons = wrapper.findAll('button').filter(item => item.text().includes('聚焦幂等键'))
    expect(focusButtons.length).toBeGreaterThan(0)
    await focusButtons[0].trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('幂等键聚焦')
    expect(wrapper.text()).toContain('已聚焦幂等键')
    expect(wrapper.find('.timeline-list').text()).toContain('协议错误 (protocol_error)')
    expect(wrapper.find('.timeline-list').text()).not.toContain('连通性错误 (connectivity_error)')
    expect(replaceMock).toHaveBeenCalledWith({
      query: expect.objectContaining({
        governance_filter: 'framework_adapter',
        governance_dedupe_key: 'framework_adapter_external_error:321:langgraph_draft:protocol_error:transport probe failed'
      })
    })
  })

  it('clears route-driven dedupe key focus without dropping domain focus', async () => {
    routeQuery.governance_filter = 'framework_adapter'
    routeQuery.governance_dedupe_key = 'framework_adapter_external_error:321:langgraph_draft:connectivity_error:connect failed'
    seedPlan({
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:16Z',
          source: 'framework_adapter',
          event_type: 'framework_adapter_external_error',
          severity: 'warning',
          summary: 'Framework adapter `LangGraph` external pilot failed',
          detail: 'connect failed',
          payload: {
            adapter_id: 'langgraph_draft',
            framework_name: 'LangGraph',
            error_type: 'connectivity_error',
            detail: 'connect failed',
            dedupe_key: 'framework_adapter_external_error:321:langgraph_draft:connectivity_error:connect failed'
          }
        },
        {
          timestamp: '2026-05-01T12:00:17Z',
          source: 'framework_adapter',
          event_type: 'framework_adapter_external_error',
          severity: 'warning',
          summary: 'Framework adapter `LangGraph` external pilot failed',
          detail: 'transport probe failed',
          payload: {
            adapter_id: 'langgraph_draft',
            framework_name: 'LangGraph',
            error_type: 'protocol_error',
            detail: 'transport probe failed',
            dedupe_key: 'framework_adapter_external_error:321:langgraph_draft:protocol_error:transport probe failed'
          }
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(wrapper.find('.timeline-list').text()).toContain('连通性错误 (connectivity_error)')
    expect(wrapper.find('.timeline-list').text()).not.toContain('协议错误 (protocol_error)')

    const clearButton = wrapper.findAll('button').find(item => item.text().includes('清除幂等键'))
    expect(clearButton).toBeTruthy()

    await clearButton.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Framework Adapter')
    expect(wrapper.find('.timeline-list').text()).toContain('连通性错误 (connectivity_error)')
    expect(wrapper.find('.timeline-list').text()).toContain('协议错误 (protocol_error)')
    expect(replaceMock).toHaveBeenCalledWith({
      query: expect.not.objectContaining({
        governance_dedupe_key: expect.anything()
      })
    })
  })

  it('explains empty route-driven dedupe key focus and allows clearing it', async () => {
    routeQuery.governance_filter = 'framework_adapter'
    routeQuery.governance_dedupe_key = 'framework_adapter_external_error:321:langgraph_draft:missing_error:stale-link'
    seedPlan({
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:16Z',
          source: 'framework_adapter',
          event_type: 'framework_adapter_external_error',
          severity: 'warning',
          summary: 'Framework adapter `LangGraph` external pilot failed',
          detail: 'connect failed',
          payload: {
            adapter_id: 'langgraph_draft',
            framework_name: 'LangGraph',
            error_type: 'connectivity_error',
            detail: 'connect failed',
            dedupe_key: 'framework_adapter_external_error:321:langgraph_draft:connectivity_error:connect failed'
          }
        }
      ]
    })

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    expect(wrapper.find('.timeline-list').text()).toContain('当前幂等键没有匹配到治理事件')
    expect(wrapper.find('.timeline-list').text()).toContain('stale-link')
    expect(wrapper.find('.timeline-list').text()).not.toContain('连通性错误 (connectivity_error)')
    const emptyDedupeKey = wrapper.find('.timeline-empty-dedupe-key')
    expect(emptyDedupeKey.exists()).toBe(true)
    expect(emptyDedupeKey.attributes('title')).toBe('framework_adapter_external_error:321:langgraph_draft:missing_error:stale-link')
    expect(emptyDedupeKey.attributes('aria-label')).toBe('当前幂等键 framework_adapter_external_error:321:langgraph_draft:missing_error:stale-link')

    const clearButton = wrapper.findAll('button').find(item => item.text().includes('清除幂等键聚焦'))
    expect(clearButton).toBeTruthy()
    expect(clearButton.attributes('title')).toBe('framework_adapter_external_error:321:langgraph_draft:missing_error:stale-link')
    expect(clearButton.attributes('aria-label')).toBe('清除幂等键聚焦 framework_adapter_external_error:321:langgraph_draft:missing_error:stale-link')

    await clearButton.trigger('click')
    await flushPromises()

    expect(wrapper.find('.timeline-list').text()).toContain('连通性错误 (connectivity_error)')
    expect(replaceMock).toHaveBeenCalledWith({
      query: expect.not.objectContaining({
        governance_dedupe_key: expect.anything()
      })
    })
  })

  it('clears framework adapter error type filter without dropping domain severity focus', async () => {
    routeQuery.governance_filter = 'framework_adapter'
    routeQuery.governance_severity = 'warning'
    routeQuery.governance_error_type = 'protocol_error'

    const wrapper = mount(GovernanceTimelinePanel, {
      global: {
        plugins: [pinia]
      }
    })

    await flushPromises()

    const clearButton = wrapper.findAll('button').find(item => item.text().includes('清除错误类型'))
    expect(clearButton).toBeTruthy()

    await clearButton.trigger('click')
    await flushPromises()

    expect(wrapper.text()).not.toContain('错误类型')
    expect(wrapper.text()).toContain('Framework Adapter')
    expect(wrapper.text()).toContain('仅告警')
    expect(wrapper.find('.timeline-list').text()).toContain('协议错误 (protocol_error)')
    expect(wrapper.find('.timeline-list').text()).toContain('连通性错误 (connectivity_error)')
    expect(replaceMock).toHaveBeenCalledWith({
      query: expect.not.objectContaining({
        governance_error_type: expect.anything()
      })
    })
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
