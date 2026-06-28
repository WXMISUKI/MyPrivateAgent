import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

const apiMocks = vi.hoisted(() => ({
  workflowLabApi: {
    list: vi.fn(),
    get: vi.fn(),
    getExample: vi.fn(),
    invokeExample: vi.fn()
  }
}))

vi.mock('../../api', () => ({
  workflowLabApi: apiMocks.workflowLabApi
}))

import WorkflowLabView from '../WorkflowLabView.vue'

describe('WorkflowLabView', () => {
  beforeEach(() => {
    apiMocks.workflowLabApi.list.mockReset()
    apiMocks.workflowLabApi.get.mockReset()
    apiMocks.workflowLabApi.getExample.mockReset()
    apiMocks.workflowLabApi.invokeExample.mockReset()
  })

  it('lists workflows, loads detail, and replays an example through the lab contract', async () => {
    apiMocks.workflowLabApi.list.mockResolvedValue({
      data: {
        total_workflows: 1,
        ready_workflows: 1,
        invalid_workflows: 0,
        workflows: [{
          workflow_id: 'szzg_agent_encapsulation_route',
          name: 'SZZG Agent Encapsulation Route',
          status: 'active',
          capability_id: 'coze.workflow.szzg_agent_encapsulation_route',
          readiness: { status: 'ready' },
          owner: { primary: 'szzg-owner@example.com' },
          launch_evidence: { status: 'present', path: 'docs/integration/demo', decision: 'go' }
        }]
      }
    })
    apiMocks.workflowLabApi.get.mockResolvedValue({
      data: {
        workflow_id: 'szzg_agent_encapsulation_route',
        name: 'SZZG Agent Encapsulation Route',
        status: 'active',
        version: '0.1.0',
        capability_id: 'coze.workflow.szzg_agent_encapsulation_route',
        owner: { primary: 'szzg-owner@example.com' },
        governance: { permission_level: 'medium', trace_required: true, approval_required: false, allowed_callers: ['runtime'] },
        input_schema: { type: 'object', required: ['user_input'] },
        output_schema: { type: 'object', required: ['command'] },
        prompts: {
          system: { path: 'prompts/system.md', exists: true },
          task: { path: 'prompts/task.md', exists: true }
        },
        acceptance: {
          examples: [{ id: 'route_agent_single_match', path: 'examples/route_agent_single_match.json', expected_path: 'examples/route_agent_single_match_expected.json' }]
        },
        dependency_mapping: {
          status: 'ready',
          reason: 'ok',
          items: [{
            kind: 'runtime_capability',
            source: 'http.request',
            target_capability_id: 'http.request',
            status: 'ready'
          }]
        },
        launch_evidence: { status: 'present', path: 'docs/integration/demo', decision: 'go' }
      }
    })
    apiMocks.workflowLabApi.getExample.mockResolvedValue({
      data: {
        contract_version: 'coze-workflow-lab-v1',
        workflow_id: 'szzg_agent_encapsulation_route',
        example_id: 'route_agent_single_match',
        input: { payload: { user_input: '打开代码调试助手' } },
        expected: { payload: { command: 'route_agent', params: ['ROUTE://agent_detail?id=7'], message: '我马上为你打开代码调试助手智能体' } }
      }
    })
    apiMocks.workflowLabApi.invokeExample.mockResolvedValue({
      data: {
        contract_version: 'coze-workflow-lab-v1',
        workflow_id: 'szzg_agent_encapsulation_route',
        capability_id: 'coze.workflow.szzg_agent_encapsulation_route',
        example_id: 'route_agent_single_match',
        status: 'completed',
        run_id: 'run_123',
        result: {
          command: 'route_agent',
          params: ['ROUTE://agent_detail?id=7'],
          message: '我马上为你打开代码调试助手智能体'
        },
        expected_comparison: {
          status: 'match',
          diff: []
        },
        trace_summary: {
          workflow_version: '0.1.0',
          delegated_to_capability_runtime: true
        }
      }
    })

    const wrapper = mount(WorkflowLabView)
    await flushPromises()
    await flushPromises()

    expect(wrapper.text()).toContain('Workflow Lab')
    expect(wrapper.text()).toContain('Verification Runbook')
    expect(wrapper.text()).toContain('coze_workflow_lab_verification_runbook.md')
    expect(wrapper.text()).toContain('SZZG Agent Encapsulation Route')
    expect(wrapper.text()).toContain('http.request')
    expect(wrapper.text()).toContain('route_agent_single_match')

    const replayButton = wrapper.findAll('button').find(button => button.text().includes('回放示例'))
    expect(replayButton).toBeTruthy()
    await replayButton.trigger('click')
    await flushPromises()

    expect(apiMocks.workflowLabApi.invokeExample).toHaveBeenCalledWith('szzg_agent_encapsulation_route', 'route_agent_single_match')
    expect(wrapper.text()).toContain('run_123')
    expect(wrapper.text()).toContain('match')
  })
})
