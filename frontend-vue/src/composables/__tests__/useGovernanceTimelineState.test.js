import { describe, expect, it, vi } from 'vitest'
import { effectScope, nextTick, reactive, ref } from 'vue'

import { useGovernanceTimelineState } from '../useGovernanceTimelineState'

describe('useGovernanceTimelineState', () => {
  it('hydrates state from route query and syncs updates back to route', async () => {
    const route = reactive({
      query: {
        governance_filter: 'main_chat',
        governance_severity: 'warning',
        governance_snapshot: 'SNAP-1',
        governance_error_type: 'protocol_error',
        governance_dedupe_key: 'dedupe-1',
        governance_query_id: 'query-1',
        governance_query_stage: 'planning',
      },
    })
    const replace = vi.fn(() => Promise.resolve())

    const scope = effectScope()
    const state = scope.run(() => useGovernanceTimelineState({
      route,
      router: { replace },
      timelineFilters: ref([{ key: 'all' }, { key: 'main_chat' }, { key: 'framework_adapter' }]),
      severityFilters: ref([{ key: 'all' }, { key: 'warning' }]),
      combinedTimeline: ref([]),
      governanceOverviewCards: ref([]),
      recommendedFocusFilter: ref('all'),
      recommendedFocusSignature: ref(''),
      entrySnapshotRef: entry => entry?.payload?.snapshot_ref || null,
      getTimelineDedupeKey: entry => entry?.payload?.dedupe_key || '',
      getTimelineQueryId: entry => entry?.payload?.query_id || '',
      normalizeText: value => String(value || '').trim(),
    }))

    expect(state.activeFilter.value).toBe('main_chat')
    expect(state.activeSeverity.value).toBe('warning')
    expect(state.activeSnapshotId.value).toBe('SNAP-1')
    expect(state.activeFrameworkAdapterErrorType.value).toBe('protocol_error')
    expect(state.activeDedupeKey.value).toBe('dedupe-1')
    expect(state.activeQueryId.value).toBe('query-1')
    expect(state.activeQueryStage.value).toBe('planning')

    state.activeQueryStage.value = 'final_output'
    await nextTick()

    expect(replace).toHaveBeenCalledWith({
      query: expect.objectContaining({
        governance_query_stage: 'final_output',
      }),
    })
    scope.stop()
  })

  it('supports filter and focus actions with state cleanup', async () => {
    const route = reactive({ query: {} })
    const replace = vi.fn(() => Promise.resolve())
    const timelineFilters = ref([{ key: 'all' }, { key: 'main_chat' }, { key: 'framework_adapter' }])
    const combinedTimeline = ref([
      {
        domain: 'framework_adapter',
        payload: {
          snapshot_ref: { snapshot_id: 'SNAP-2' },
        },
      },
    ])
    const onActiveDedupeKeyChanged = vi.fn()

    const scope = effectScope()
    const state = scope.run(() => useGovernanceTimelineState({
      route,
      router: { replace },
      timelineFilters,
      severityFilters: ref([{ key: 'all' }, { key: 'warning' }]),
      combinedTimeline,
      governanceOverviewCards: ref([{ key: 'framework_adapter', warningCount: 2 }]),
      recommendedFocusFilter: ref('framework_adapter'),
      recommendedFocusSignature: ref('sig-1'),
      entrySnapshotRef: entry => entry?.payload?.snapshot_ref || null,
      getTimelineDedupeKey: entry => entry?.payload?.dedupe_key || '',
      getTimelineQueryId: entry => entry?.payload?.query_id || '',
      normalizeText: value => String(value || '').trim(),
      onActiveDedupeKeyChanged,
    }))

    state.activeFrameworkAdapterErrorType.value = 'protocol_error'
    state.activeDedupeKey.value = 'dedupe-2'
    state.focusTimelineEntry({
      domain: 'framework_adapter',
      payload: { snapshot_ref: { snapshot_id: 'SNAP-2' } },
    }, 'framework_adapter')
    await nextTick()

    expect(state.activeFilter.value).toBe('framework_adapter')
    expect(state.activeSeverity.value).toBe('all')
    expect(state.activeFrameworkAdapterErrorType.value).toBe('')
    expect(state.activeDedupeKey.value).toBe('')
    expect(state.activeSnapshotId.value).toBe('SNAP-2')

    state.focusQueryId({
      domain: 'main_chat',
      payload: {
        query_id: 'query-2',
        stage: 'planning',
      },
    })
    await nextTick()
    expect(state.activeFilter.value).toBe('main_chat')
    expect(state.activeQueryId.value).toBe('query-2')
    expect(state.activeQueryStage.value).toBe('planning')

    state.focusDedupeKey({
      payload: {
        dedupe_key: 'dedupe-3',
      },
    })
    await nextTick()
    expect(state.activeDedupeKey.value).toBe('dedupe-3')
    expect(onActiveDedupeKeyChanged).toHaveBeenCalled()

    state.applyWarningFocus('framework_adapter')
    await nextTick()
    expect(state.activeSeverity.value).toBe('warning')
    scope.stop()
  })

  it('keeps state valid when route options or snapshots drift', async () => {
    const route = reactive({ query: {} })
    const replace = vi.fn(() => Promise.resolve())
    const timelineFilters = ref([{ key: 'all' }, { key: 'framework_adapter' }])
    const combinedTimeline = ref([
      { payload: { snapshot_ref: { snapshot_id: 'SNAP-1' } } },
    ])
    const recommendedFocusSignature = ref('sig-1')

    const scope = effectScope()
    const state = scope.run(() => useGovernanceTimelineState({
      route,
      router: { replace },
      timelineFilters,
      severityFilters: ref([{ key: 'all' }, { key: 'warning' }]),
      combinedTimeline,
      governanceOverviewCards: ref([{ key: 'framework_adapter', warningCount: 1 }]),
      recommendedFocusFilter: ref('framework_adapter'),
      recommendedFocusSignature,
      entrySnapshotRef: entry => entry?.payload?.snapshot_ref || null,
      getTimelineDedupeKey: entry => entry?.payload?.dedupe_key || '',
      getTimelineQueryId: entry => entry?.payload?.query_id || '',
      normalizeText: value => String(value || '').trim(),
    }))

    state.activeFilter.value = 'framework_adapter'
    state.activeFrameworkAdapterErrorType.value = 'protocol_error'
    state.activeSnapshotId.value = 'UNKNOWN'
    await nextTick()

    expect(state.activeSnapshotId.value).toBe('')

    timelineFilters.value = [{ key: 'all' }]
    await nextTick()
    expect(state.activeFilter.value).toBe('all')
    expect(state.activeFrameworkAdapterErrorType.value).toBe('')

    timelineFilters.value = [{ key: 'all' }, { key: 'framework_adapter' }]
    state.activeFilter.value = 'all'
    route.query = {}
    recommendedFocusSignature.value = 'sig-2'
    await nextTick()
    expect(state.activeFilter.value).toBe('framework_adapter')
    expect(state.lastAutoFocusSignature.value).toBe('sig-2')
    scope.stop()
  })
})
