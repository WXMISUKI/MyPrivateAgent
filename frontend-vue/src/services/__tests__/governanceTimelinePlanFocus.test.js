import { describe, expect, it } from 'vitest'

import {
  getLatestGovernanceTimestamp,
  isGovernanceDomain,
  pickGovernanceFocusItem,
} from '../governanceTimelinePlanFocus'

describe('governanceTimelinePlanFocus', () => {
  const toTimestamp = value => new Date(value).getTime()
  const normalizePayload = payload => (payload && typeof payload === 'object' && !Array.isArray(payload) ? payload : null)
  const inferTimelineDomain = (eventType, source) => {
    if (source) {
      return source
    }
    if (String(eventType || '').startsWith('doctor')) {
      return 'doctor'
    }
    return 'other'
  }

  it('recognizes governance domains', () => {
    expect(isGovernanceDomain('doctor')).toBe(true)
    expect(isGovernanceDomain('main_chat')).toBe(true)
    expect(isGovernanceDomain('other')).toBe(false)
  })

  it('computes latest governance timestamp from trace and audit entries', () => {
    const item = {
      audit_trail: [
        {
          timestamp: '2026-05-01T12:00:01Z',
          event_type: 'doctor_run_started',
          payload: {},
        },
      ],
      run_trace: [
        {
          timestamp: '2026-05-01T12:00:10Z',
          source: 'mcp',
          event_type: 'mcp_server_probed',
          payload: {},
        },
        {
          timestamp: '2026-05-01T12:00:20Z',
          source: 'other',
          event_type: 'custom_event',
          payload: {},
        },
      ],
    }

    expect(getLatestGovernanceTimestamp(item, {
      inferTimelineDomain,
      normalizePayload,
      toTimestamp,
    })).toBe(toTimestamp('2026-05-01T12:00:10Z'))
  })

  it('prefers items with governance trace and falls back by active or in progress state', () => {
    const planWithTrace = {
      active_item_id: 2,
      items: [
        { id: 1, title: 'older', status: 'completed', run_trace: [{ timestamp: '2026-05-01T12:00:01Z', source: 'doctor', event_type: 'doctor_run_started', payload: {} }] },
        { id: 2, title: 'latest', status: 'in_progress', run_trace: [{ timestamp: '2026-05-01T12:00:10Z', source: 'mcp', event_type: 'mcp_server_probed', payload: {} }] },
      ],
    }

    expect(pickGovernanceFocusItem(planWithTrace, {
      getLatestGovernanceTimestamp: item => getLatestGovernanceTimestamp(item, {
        inferTimelineDomain,
        normalizePayload,
        toTimestamp,
      }),
    })?.id).toBe(2)

    expect(pickGovernanceFocusItem({
      active_item_id: 5,
      items: [
        { id: 3, title: 'first', status: 'todo' },
        { id: 5, title: 'active', status: 'todo' },
      ],
    })?.id).toBe(5)

    expect(pickGovernanceFocusItem({
      items: [
        { id: 7, title: 'todo', status: 'todo' },
        { id: 8, title: 'doing', status: 'in_progress' },
      ],
    })?.id).toBe(8)
  })
})
