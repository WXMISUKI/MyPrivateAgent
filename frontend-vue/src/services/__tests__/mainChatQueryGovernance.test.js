import { describe, expect, it } from 'vitest'

import {
  buildCurrentQueryDetail,
  buildCurrentQueryOverview,
  buildHistoryStageTags,
  buildMainChatHistoryContextLabel,
  buildMainChatHistoryStatus,
  filterMainChatHistoryItems,
  isHistoryStageFocused,
} from '../mainChatQueryGovernance'
import {
  buildMainChatQueryDetailContract,
  buildMainChatQueryHistoryContract,
} from '../governanceViewInterpretation'

describe('mainChatQueryGovernance', () => {
  it('builds history status and context labels', () => {
    expect(buildMainChatHistoryStatus({ items: [], recordingState: 'recorded', totalItems: 2, page: 3 }, false, '')).toBe('共 2 条 · 第 3 页')
    expect(buildMainChatHistoryStatus({ items: [] }, true, '')).toBe('正在读取最近记录')
    expect(buildMainChatHistoryStatus({ items: [] }, false, 'failed')).toBe('加载失败')

    expect(buildMainChatHistoryContextLabel('manual-chat-2', 'planning')).toBe('当前聚焦：manual-chat-2 / planning')
    expect(buildMainChatHistoryContextLabel('manual-chat-2', '')).toBe('当前聚焦：manual-chat-2')
  })

  it('filters history items and derives stage tags', () => {
    const items = [
      { queryId: 'manual-chat-1', latestStage: 'planning', latestSummary: 'Plan', latestSnapshotId: 'S1' },
      { queryId: 'manual-chat-2', latestStage: 'final_output', latestSummary: 'Done', latestSnapshotId: 'S2' },
    ]
    expect(filterMainChatHistoryItems(items, 'final_output')).toEqual([items[1]])

    const tags = buildHistoryStageTags(
      { queryId: 'manual-chat-2', stageCounts: { planning: 1, final_output: 2 } },
      'manual-chat-2',
      'planning'
    )
    expect(tags[0]).toEqual({ key: 'final_output', label: 'final_output 2', active: false })
    expect(tags[1]).toEqual({ key: 'planning', label: 'planning 1', active: true })
    expect(isHistoryStageFocused({ queryId: 'manual-chat-2', stageCounts: { planning: 1 } }, 'manual-chat-2', 'planning')).toBe(true)
  })

  it('derives query overview and detail from timeline entries', () => {
    const entries = [
      {
        timestamp: '2026-05-01T12:00:20Z',
        title: 'query_control_final_output',
        content: 'Main chat final output 2',
        severity: 'info',
        payload: {
          stage: 'final_output',
          dedupe_key: 'dedupe-final',
          snapshot_ref: { snapshot_id: 'S2' },
        },
      },
      {
        timestamp: '2026-05-01T12:00:19Z',
        title: 'query_control_planning',
        content: 'Main chat planning 1',
        severity: 'warning',
        payload: {
          stage: 'planning',
          dedupe_key: 'dedupe-plan',
          snapshot_ref: { snapshot_id: 'S1' },
        },
      }
    ]

    const overview = buildCurrentQueryOverview(null, 'manual-chat-2', entries, entry => entry?.payload?.snapshot_ref || null)
    expect(overview).toMatchObject({
      queryId: 'manual-chat-2',
      latestStage: 'final_output',
      latestSnapshotId: 'S2',
      stageCount: 2,
      warningCount: 1,
    })

    const detail = buildCurrentQueryDetail(null, 'manual-chat-2', entries, {
      entrySnapshotRef: entry => entry?.payload?.snapshot_ref || null,
      getTimelineDedupeKey: entry => entry?.payload?.dedupe_key || '',
      toTimestamp: value => new Date(value).getTime(),
    })
    expect(detail.stageChain).toEqual(['planning', 'final_output'])
    expect(detail.dedupeKeyCount).toBe(2)
    expect(detail.latestWarningSummary).toBe('query_control_planning')
    expect(detail.recentEvents[0].stage).toBe('planning')
    expect(detail.latestStage).toBe('final_output')
    expect(detail.latestSummary).toBe('query_control_final_output')
    expect(detail.stageCount).toBe(2)
    expect(detail.warningCount).toBe(1)
    expect(detail.eventCount).toBe(2)
    expect(detail.reason).toBe('')
  })

  it('exposes shared query read model defaults through the consolidated helper', () => {
    expect(buildMainChatQueryDetailContract(null)).toEqual({
      connected: false,
      readModelLayer: '',
      sourceChannel: '',
      identityKind: '',
      queryId: '',
      associatedRunIds: [],
      recordingState: 'unavailable',
      stageChain: [],
      dedupeKeys: [],
      dedupeKeyCount: 0,
      recentEvents: [],
      latestSnapshotId: '',
      latestWarningSummary: '',
      latestStage: '',
      latestSummary: '',
      stageCount: 0,
      warningCount: 0,
      eventCount: 0,
      recentEventCount: 0,
      reason: '',
    })

    expect(buildMainChatQueryHistoryContract(null)).toEqual({
      connected: false,
      readModelLayer: '',
      sourceChannel: '',
      identityKind: '',
      paginationMode: '',
      recordingState: 'unavailable',
      items: [],
      page: 1,
      pageSize: 20,
      totalItems: 0,
      hasMore: false,
      nextCursor: '',
      reason: '',
    })
  })

  it('preserves read model metadata when normalizing shared query contracts', () => {
    const detail = buildMainChatQueryDetailContract({
      read_model_layer: 'query_detail',
      source_channel: 'main_chat',
      identity_kind: 'query_id',
      query_id: 'manual-chat-1',
      associated_run_ids: ['run-1', 'run-2'],
      recording_state: 'recorded',
      latest_stage: 'planning',
      latest_summary: 'Main chat planning',
      stage_chain: ['planning'],
      recent_events: [],
      dedupe_keys: [],
      latest_snapshot_id: 'S1',
      stage_count: 1,
      warning_count: 0,
      event_count: 1,
      recent_event_count: 0,
      reason: '',
    })

    expect(detail.readModelLayer).toBe('query_detail')
    expect(detail.sourceChannel).toBe('main_chat')
    expect(detail.identityKind).toBe('query_id')
    expect(detail.queryId).toBe('manual-chat-1')
    expect(detail.associatedRunIds).toEqual(['run-1', 'run-2'])

    const history = buildMainChatQueryHistoryContract({
      read_model_layer: 'query_history',
      source_channel: 'main_chat',
      identity_kind: 'query_id',
      pagination_mode: 'page_plus_cursor',
      recording_state: 'recorded',
      items: [
        {
          read_model_layer: 'recent_summary',
          source_channel: 'main_chat',
          identity_kind: 'query_id',
          query_id: 'manual-chat-1',
          latest_stage: 'planning',
        },
      ],
      page: 1,
      page_size: 20,
      total_items: 0,
      has_more: false,
      next_cursor: '',
      reason: '',
    })

    expect(history.readModelLayer).toBe('query_history')
    expect(history.sourceChannel).toBe('main_chat')
    expect(history.identityKind).toBe('query_id')
    expect(history.paginationMode).toBe('page_plus_cursor')
    expect(history.items[0].readModelLayer).toBe('recent_summary')
    expect(history.items[0].sourceChannel).toBe('main_chat')
    expect(history.items[0].identityKind).toBe('query_id')
  })
})
