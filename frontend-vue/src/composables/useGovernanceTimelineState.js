import { ref, watch } from 'vue'
import {
  entrySnapshotRef,
  getTimelineDedupeKey,
  getTimelineQueryId,
  normalizeText,
} from '../services/governanceValueUtils'

export function useGovernanceTimelineState(options = {}) {
  const {
    activeFilter = ref('all'),
    activeSeverity = ref('all'),
    activeSnapshotId = ref(''),
    activeFrameworkAdapterErrorType = ref(''),
    activeDedupeKey = ref(''),
    activeQueryId = ref(''),
    activeQueryStage = ref(''),
    lastAutoFocusSignature = ref(''),
    route,
    router,
    timelineFilters,
    severityFilters,
    combinedTimeline,
    governanceOverviewCards,
    recommendedFocusFilter,
    recommendedFocusSignature,
    entrySnapshotRef: entrySnapshotRefFn = entrySnapshotRef,
    getTimelineDedupeKey: getTimelineDedupeKeyFn = getTimelineDedupeKey,
    getTimelineQueryId: getTimelineQueryIdFn = getTimelineQueryId,
    normalizeText: normalizeTextFn = normalizeText,
    onActiveDedupeKeyChanged = () => {},
  } = options

  function replaceRouteQuery(patch = {}) {
    const nextQuery = { ...route.query }
    for (const [key, value] of Object.entries(patch)) {
      if (value === undefined || value === null || value === '' || value === 'all') {
        delete nextQuery[key]
      } else {
        nextQuery[key] = value
      }
    }
    router.replace({ query: nextQuery }).catch(() => {})
  }

  function syncFilterToRoute(nextFilter) {
    const currentFilter = String(route.query.governance_filter || 'all').trim() || 'all'
    if (currentFilter === nextFilter) return
    replaceRouteQuery({ governance_filter: nextFilter === 'all' ? '' : nextFilter })
  }

  function syncSeverityToRoute(nextSeverity) {
    const currentSeverity = String(route.query.governance_severity || 'all').trim() || 'all'
    if (currentSeverity === nextSeverity) return
    replaceRouteQuery({ governance_severity: nextSeverity === 'all' ? '' : nextSeverity })
  }

  function syncSnapshotToRoute(nextSnapshotId) {
    const currentSnapshot = String(route.query.governance_snapshot || '').trim()
    if (currentSnapshot === String(nextSnapshotId || '').trim()) return
    replaceRouteQuery({ governance_snapshot: nextSnapshotId })
  }

  function syncFrameworkAdapterErrorTypeToRoute(nextErrorType) {
    const currentErrorType = String(route.query.governance_error_type || '').trim()
    const normalizedNextErrorType = String(nextErrorType || '').trim()
    if (currentErrorType === normalizedNextErrorType) return
    replaceRouteQuery({ governance_error_type: normalizedNextErrorType })
  }

  function syncDedupeKeyToRoute(nextDedupeKey) {
    const currentDedupeKey = String(route.query.governance_dedupe_key || '').trim()
    const normalizedNextDedupeKey = String(nextDedupeKey || '').trim()
    if (currentDedupeKey === normalizedNextDedupeKey) return
    replaceRouteQuery({ governance_dedupe_key: normalizedNextDedupeKey })
  }

  function syncQueryIdToRoute(nextQueryId) {
    const currentQueryId = String(route.query.governance_query_id || '').trim()
    const normalizedNextQueryId = String(nextQueryId || '').trim()
    if (currentQueryId === normalizedNextQueryId) return
    replaceRouteQuery({ governance_query_id: normalizedNextQueryId })
  }

  function syncQueryStageToRoute(nextQueryStage) {
    const currentQueryStage = String(route.query.governance_query_stage || '').trim()
    const normalizedNextQueryStage = String(nextQueryStage || '').trim()
    if (currentQueryStage === normalizedNextQueryStage) return
    replaceRouteQuery({ governance_query_stage: normalizedNextQueryStage })
  }

  function applyFilter(filterKey) {
    const nextFilter = String(filterKey || 'all').trim() || 'all'
    activeFilter.value = timelineFilters.value.some(item => item.key === nextFilter) ? nextFilter : 'all'
  }

  function focusTimelineEntry(entry, filterKey = 'all') {
    activeSeverity.value = 'all'
    activeFrameworkAdapterErrorType.value = ''
    activeDedupeKey.value = ''
    applyFilter(filterKey)
    activeSnapshotId.value = entrySnapshotRefFn(entry)?.snapshot_id || ''
  }

  function applyWarningFocus(filterKey) {
    const nextFilter = String(filterKey || 'all').trim() || 'all'
    const matchedCard = governanceOverviewCards.value.find(card => card.key === nextFilter)
    if (!matchedCard || matchedCard.warningCount <= 0) {
      return
    }
    activeSeverity.value = 'warning'
    if (nextFilter !== 'framework_adapter') {
      activeFrameworkAdapterErrorType.value = ''
    }
    activeDedupeKey.value = ''
    applyFilter(nextFilter)
  }

  function clearFrameworkAdapterErrorTypeFilter() {
    activeFrameworkAdapterErrorType.value = ''
  }

  function clearDedupeKeyFilter() {
    activeDedupeKey.value = ''
  }

  function clearQueryIdFilter() {
    activeQueryId.value = ''
    activeQueryStage.value = ''
  }

  function clearQueryStageFilter() {
    activeQueryStage.value = ''
  }

  function focusDedupeKey(entry) {
    const dedupeKey = getTimelineDedupeKeyFn(entry)
    if (!dedupeKey) {
      return
    }
    activeDedupeKey.value = dedupeKey
  }

  function focusQueryId(entry) {
    const queryId = getTimelineQueryIdFn(entry)
    if (!queryId) {
      return
    }
    if (entry?.domain === 'main_chat' && activeFilter.value !== 'main_chat') {
      activeFilter.value = 'main_chat'
    }
    activeQueryId.value = queryId
    activeQueryStage.value = normalizeTextFn(entry?.payload?.stage)
  }

  function focusQueryStage(stage) {
    const normalizedStage = normalizeTextFn(stage)
    if (!normalizedStage) {
      return
    }
    activeQueryStage.value = normalizedStage
  }

  function focusHistoryQueryStage(queryId, stage) {
    const normalizedQueryId = normalizeTextFn(queryId)
    const normalizedStage = normalizeTextFn(stage)
    if (!normalizedQueryId || !normalizedStage) {
      return
    }
    activeQueryId.value = normalizedQueryId
    activeQueryStage.value = normalizedStage
  }

  watch(
    () => route.query.governance_filter,
    (value) => {
      const nextValue = String(value || 'all').trim() || 'all'
      activeFilter.value = timelineFilters.value.some(item => item.key === nextValue) ? nextValue : 'all'
    },
    { immediate: true }
  )

  watch(
    () => route.query.governance_severity,
    (value) => {
      const nextValue = String(value || 'all').trim() || 'all'
      activeSeverity.value = severityFilters.value.some(item => item.key === nextValue) ? nextValue : 'all'
    },
    { immediate: true }
  )

  watch(
    () => route.query.governance_snapshot,
    (value) => {
      activeSnapshotId.value = String(value || '').trim()
    },
    { immediate: true }
  )

  watch(
    () => route.query.governance_error_type,
    (value) => {
      activeFrameworkAdapterErrorType.value = normalizeTextFn(value)
    },
    { immediate: true }
  )

  watch(
    () => route.query.governance_dedupe_key,
    (value) => {
      activeDedupeKey.value = normalizeTextFn(value)
    },
    { immediate: true }
  )

  watch(
    () => route.query.governance_query_id,
    (value) => {
      activeQueryId.value = normalizeTextFn(value)
    },
    { immediate: true }
  )

  watch(
    () => route.query.governance_query_stage,
    (value) => {
      activeQueryStage.value = normalizeTextFn(value)
    },
    { immediate: true }
  )

  watch(activeFilter, (value) => {
    syncFilterToRoute(value)
  })

  watch(activeSeverity, (value) => {
    syncSeverityToRoute(value)
  })

  watch(activeSnapshotId, (value) => {
    syncSnapshotToRoute(value)
  })

  watch(activeFrameworkAdapterErrorType, (value) => {
    syncFrameworkAdapterErrorTypeToRoute(value)
  })

  watch(activeDedupeKey, (value, previous) => {
    if (value !== previous) {
      onActiveDedupeKeyChanged()
    }
    syncDedupeKeyToRoute(value)
  })

  watch(activeQueryId, (value) => {
    syncQueryIdToRoute(value)
  })

  watch(activeQueryStage, (value) => {
    syncQueryStageToRoute(value)
  })

  watch([timelineFilters, activeFilter], ([filters, currentFilter]) => {
    if (!filters.some(item => item.key === currentFilter)) {
      activeFilter.value = 'all'
    }
    if (currentFilter !== 'framework_adapter' && activeFrameworkAdapterErrorType.value) {
      activeFrameworkAdapterErrorType.value = ''
    }
  })

  watch([combinedTimeline, activeSnapshotId], ([timeline, snapshotId]) => {
    if (!snapshotId) {
      return
    }
    if (!timeline.some(entry => entrySnapshotRefFn(entry)?.snapshot_id === snapshotId)) {
      activeSnapshotId.value = ''
    }
  })

  watch(
    [recommendedFocusSignature, () => route.query.governance_filter, () => route.query.governance_snapshot, activeFilter],
    ([signature, routeFilter, routeSnapshot, currentFilter]) => {
      if (!signature || routeFilter || routeSnapshot) {
        return
      }
      if (currentFilter !== 'all' || lastAutoFocusSignature.value === signature) {
        return
      }
      lastAutoFocusSignature.value = signature
      applyFilter(recommendedFocusFilter.value)
    },
    { immediate: true }
  )

  return {
    activeFilter,
    activeSeverity,
    activeSnapshotId,
    activeFrameworkAdapterErrorType,
    activeDedupeKey,
    activeQueryId,
    activeQueryStage,
    lastAutoFocusSignature,
    applyFilter,
    focusTimelineEntry,
    applyWarningFocus,
    clearFrameworkAdapterErrorTypeFilter,
    clearDedupeKeyFilter,
    clearQueryIdFilter,
    clearQueryStageFilter,
    focusDedupeKey,
    focusQueryId,
    focusQueryStage,
    focusHistoryQueryStage,
  }
}
