import { describe, expect, it } from 'vitest'

import {
  buildFrameworkAdapterRemediationCommand,
  buildFrameworkAdapterRemediationStatusTags,
  formatFrameworkAdapterDisplayName,
  formatFrameworkAdapterExternalErrorDetail,
  formatFrameworkAdapterExternalErrorLabel,
  formatFrameworkAdapterExternalErrorTag,
  formatFrameworkAdapterFailureCount,
  formatFrameworkAdapterFailureDistribution,
  formatFrameworkAdapterFailureSampleSize,
  formatFrameworkAdapterFailureWindow,
  formatFrameworkAdapterIdentityLine,
  formatFrameworkAdapterRemediationAction,
  formatFrameworkAdapterRemediationContent,
  formatFrameworkAdapterRemediationHeading,
  formatFrameworkAdapterRemediationIdentityLine,
  formatFrameworkAdapterSummaryHeading,
  getFrameworkAdapterExternalErrorType,
} from '../frameworkAdapterGovernance'

describe('frameworkAdapterGovernance', () => {
  it('formats external error labels and failure metrics', () => {
    expect(formatFrameworkAdapterExternalErrorLabel('protocol_error')).toBe('协议错误')
    expect(formatFrameworkAdapterExternalErrorTag({ error_type: 'protocol_error' })).toBe('协议错误 (protocol_error)')
    expect(formatFrameworkAdapterExternalErrorDetail({ detail: 'transport probe failed' })).toBe('transport probe failed')

    const entry = {
      payload: {
        external_pilot_failure_counts: {
          total: 4,
          window_scope: 'recent_plan_items',
          sample_size: 50,
          by_error_type: {
            protocol_error: 3,
            connectivity_error: 1,
          },
        },
      },
    }
    expect(formatFrameworkAdapterFailureCount(entry)).toBe('4')
    expect(formatFrameworkAdapterFailureWindow(entry)).toBe('最近 PlanItem')
    expect(formatFrameworkAdapterFailureSampleSize(entry)).toBe('50')
    expect(formatFrameworkAdapterFailureDistribution(entry)).toBe('协议错误 3 · 连通性错误 1')
  })

  it('formats adapter identity and summary headings', () => {
    const entry = {
      payload: {
        framework_name: '',
        adapter_id: 'langgraph_draft',
      },
    }
    expect(formatFrameworkAdapterDisplayName('', 'langgraph_draft')).toBe('LangGraph')
    expect(formatFrameworkAdapterSummaryHeading(entry, 'Pilot')).toBe('最近一次 LangGraph Pilot')
    expect(formatFrameworkAdapterIdentityLine(entry)).toBe('adapter_id: langgraph_draft')
  })

  it('formats remediation summaries and commands', () => {
    const remediationActions = [
      {
        adapter_id: 'langgraph_draft',
        type: 'install_package',
        message: '安装缺失依赖包',
        packages: ['langgraph'],
      },
      {
        adapter_id: 'langgraph_draft',
        type: 'configure_env',
        message: '补齐运行时环境变量',
        env: ['LANGGRAPH_RUNTIME_ENDPOINT', 'LANGGRAPH_ASSISTANT_ID'],
      },
      {
        adapter_id: 'langgraph_draft',
        type: 'enable_runtime_execution',
        message: '启用运行时执行',
      },
    ]

    expect(formatFrameworkAdapterRemediationAction(remediationActions[0])).toBe('langgraph_draft · install_package · 安装缺失依赖包')
    expect(buildFrameworkAdapterRemediationStatusTags(remediationActions)).toEqual(['缺包', '缺环境变量', '运行时未启用'])
    expect(formatFrameworkAdapterRemediationContent('LangGraph', 3, ['缺包', '缺环境变量'])).toBe('LangGraph · 缺包 / 缺环境变量')
    expect(formatFrameworkAdapterRemediationHeading({
      adapterId: 'langgraph_draft',
      remediationActions,
    })).toBe('最近一次 LangGraph 修复建议')
    expect(formatFrameworkAdapterRemediationIdentityLine({
      adapterId: 'langgraph_draft',
      remediationActions,
    })).toBe('adapter_id: langgraph_draft')
    expect(buildFrameworkAdapterRemediationCommand(remediationActions)).toBe([
      'pip install langgraph',
      'LANGGRAPH_RUNTIME_ENDPOINT=<value>',
      'LANGGRAPH_ASSISTANT_ID=<value>',
      'ENABLE_LANGGRAPH_RUNTIME_EXECUTION=true',
    ].join('\n'))
  })

  it('derives framework adapter error type from timeline entry', () => {
    expect(getFrameworkAdapterExternalErrorType({
      domain: 'framework_adapter',
      payload: { error_type: 'protocol_error' },
    })).toBe('protocol_error')
    expect(getFrameworkAdapterExternalErrorType({
      domain: 'mcp',
      payload: { error_type: 'protocol_error' },
    })).toBe('')
  })
})
