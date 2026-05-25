import { describe, expect, it } from 'vitest'

import {
  buildApprovalOverview,
  buildCurrentRunOverview,
  compareApprovalRecency,
  isPendingApprovalStatus,
  pickLatestApprovalRequest,
} from '../governanceTimelineSummary'

describe('governanceTimelineSummary', () => {
  const toTimestamp = value => new Date(value).getTime()

  it('builds current run overview from scheduler run context', () => {
    expect(buildCurrentRunOverview({
      run_id: 'sched-run-01',
      run_kind: 'scheduler',
      state: 'running',
      active_children: 1,
      approval_request_count: 2,
    }, { traceCount: 4 })).toEqual({
      id: 'sched-run-01',
      summary: 'scheduler · running',
      notice: 'Trace 4 · 活跃子任务 1 · 审批 2',
    })

    expect(buildCurrentRunOverview({}, { traceCount: 0 })).toBeNull()
  })

  it('picks latest approval request by updated_at created_at timestamp and list order', () => {
    const requests = [
      {
        request_id: 'older',
        status: 'pending',
        updated_at: '2026-05-01T12:00:01Z',
      },
      {
        request_id: 'newer',
        status: 'pending',
        updated_at: '2026-05-01T12:00:10Z',
      },
    ]
    expect(pickLatestApprovalRequest(requests, toTimestamp)?.request_id).toBe('newer')

    expect(compareApprovalRecency(
      { created_at: '2026-05-01T12:00:10Z' },
      0,
      { created_at: '2026-05-01T12:00:01Z' },
      1,
      toTimestamp
    )).toBeGreaterThan(0)

    expect(compareApprovalRecency(
      { updated_at: '2026-05-01T12:00:10Z', created_at: '2026-05-01T12:00:02Z', timestamp: '2026-05-01T12:00:09Z' },
      1,
      { updated_at: '2026-05-01T12:00:10Z', created_at: '2026-05-01T12:00:02Z', timestamp: '2026-05-01T12:00:03Z' },
      0,
      toTimestamp
    )).toBeGreaterThan(0)

    expect(compareApprovalRecency(
      { timestamp: '2026-05-01T12:00:10Z' },
      1,
      { timestamp: '2026-05-01T12:00:10Z' },
      0,
      toTimestamp
    )).toBeGreaterThan(0)
  })

  it('builds approval overview from pending and latest requests', () => {
    const overview = buildApprovalOverview([
      {
        request_id: 'approval-1',
        status: 'approved',
        tool_name: 'shell_command',
      },
      {
        request_id: 'approval-2',
        status: 'pending',
        tool_name: 'mcp_filesystem_read',
        permission_level: 'standard',
        updated_at: '2026-05-01T12:00:10Z',
      },
    ], {
      currentRunOverview: { id: 'sched-run-01' },
      toTimestamp,
    })

    expect(overview).toEqual({
      pendingLabel: '1 个待处理',
      primaryDetail: 'mcp_filesystem_read · approval-2',
      secondaryDetail: 'standard · sched-run-01',
    })
  })

  it('recognizes pending approval statuses', () => {
    expect(isPendingApprovalStatus('pending')).toBe(true)
    expect(isPendingApprovalStatus('waiting_approval')).toBe(true)
    expect(isPendingApprovalStatus('approved')).toBe(false)
  })
})
