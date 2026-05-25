import { normalizeText } from './governanceValueUtils'

export function buildGovernanceViewUrl(options = {}) {
  const {
    locationHref = 'http://localhost/',
    routeQuery = {},
    activeFilter = 'all',
    activeSeverity = 'all',
    activeFrameworkAdapterErrorType = '',
    activeDedupeKey = '',
    activeQueryId = '',
    activeQueryStage = '',
    activeQuerySearch = '',
    activeQueryHistoryPage = 1,
    activeSnapshotId = '',
  } = options

  const baseUrl = new URL(locationHref)
  baseUrl.search = ''
  for (const [key, rawValue] of Object.entries(routeQuery || {})) {
    if (
      key === 'governance_filter' ||
      key === 'governance_severity' ||
      key === 'governance_error_type' ||
      key === 'governance_dedupe_key' ||
      key === 'governance_query_id' ||
      key === 'governance_query_stage' ||
      key === 'governance_query_search' ||
      key === 'governance_query_page' ||
      key === 'governance_snapshot'
    ) {
      continue
    }
    const value = Array.isArray(rawValue) ? rawValue[0] : rawValue
    if (value === undefined || value === null || value === '') {
      continue
    }
    baseUrl.searchParams.set(key, String(value))
  }
  if (activeFilter && activeFilter !== 'all') {
    baseUrl.searchParams.set('governance_filter', activeFilter)
  }
  if (activeSeverity && activeSeverity !== 'all') {
    baseUrl.searchParams.set('governance_severity', activeSeverity)
  }
  if (activeFilter === 'framework_adapter' && activeFrameworkAdapterErrorType) {
    baseUrl.searchParams.set('governance_error_type', activeFrameworkAdapterErrorType)
  }
  if (activeDedupeKey) {
    baseUrl.searchParams.set('governance_dedupe_key', activeDedupeKey)
  }
  if (activeQueryId) {
    baseUrl.searchParams.set('governance_query_id', activeQueryId)
  }
  if (activeQueryStage) {
    baseUrl.searchParams.set('governance_query_stage', activeQueryStage)
  }
  if (activeQuerySearch) {
    baseUrl.searchParams.set('governance_query_search', activeQuerySearch)
  }
  if (Number(activeQueryHistoryPage || 1) > 1) {
    baseUrl.searchParams.set('governance_query_page', String(activeQueryHistoryPage))
  }
  if (activeSnapshotId) {
    baseUrl.searchParams.set('governance_snapshot', activeSnapshotId)
  }
  return baseUrl.toString()
}

export function inferSnapshotCommandDomain(snapshotRef, fallbackDomain = '', inferTimelineDomain = () => '') {
  const sourceDomain = inferTimelineDomain(snapshotRef?.event_type, snapshotRef?.source, snapshotRef)
  if (['mcp', 'permission', 'governance', 'learning'].includes(sourceDomain)) {
    return sourceDomain
  }
  const normalizedFallback = normalizeText(fallbackDomain).toLowerCase()
  if (['mcp', 'permission', 'governance', 'learning'].includes(normalizedFallback)) {
    return normalizedFallback
  }
  return ''
}

export function buildGovernanceViewSnapshotId(timestamp, options = {}) {
  const {
    activeFilter = 'all',
    activeSeverity = 'all',
    filteredTimeline = [],
  } = options
  const latestEntry = Array.isArray(filteredTimeline) ? filteredTimeline[0] : null
  const domainKey = String(activeFilter || 'all').slice(0, 4).toUpperCase()
  const severityKey = String(activeSeverity || 'all').slice(0, 4).toUpperCase()
  const eventKey = String(latestEntry?.title || 'timeline')
    .replace(/\s+/g, '')
    .slice(0, 8)
    .toUpperCase()
  const timeKey = String(timestamp || '')
    .replace(/[-:TZ.]/g, '')
    .slice(0, 12)
  return `${domainKey}-${severityKey}-${eventKey || 'TIMELINE'}-${timeKey || 'NA'}`
}

export function buildGovernanceViewSnapshot(options = {}) {
  const {
    currentSnapshotRef = null,
    activeFilterLabel = '全部',
    activeSeverityLabel = '全部事件',
    filteredTimeline = [],
    scopedTimeline = [],
    activeFrameworkAdapterErrorTypeLabel = '',
    activeDedupeKey = '',
    activeDedupeKeyMatchLabel = '',
    activeQueryId = '',
    currentQueryOverview = null,
    activeQueryStage = '',
    activeQuerySearch = '',
    activeQueryHistoryPage = 1,
    autoFocusNotice = '',
    currentViewUrl = '',
  } = options

  const snapshotTimestamp = currentSnapshotRef?.generated_at || new Date().toISOString()
  const snapshotId = currentSnapshotRef?.snapshot_id || buildGovernanceViewSnapshotId(snapshotTimestamp, options)
  const lines = [
    `快照ID: ${snapshotId}`,
    `生成时间: ${snapshotTimestamp}`,
    `治理视图: ${activeFilterLabel} / ${activeSeverityLabel}`,
    `事件范围: ${Array.isArray(filteredTimeline) ? filteredTimeline.length : 0} / ${Array.isArray(scopedTimeline) ? scopedTimeline.length : 0}`,
  ]
  if (activeFrameworkAdapterErrorTypeLabel) {
    lines.push(`错误类型: ${activeFrameworkAdapterErrorTypeLabel}`)
  }
  if (activeDedupeKey) {
    lines.push(`幂等键: ${activeDedupeKey}`)
    lines.push(`幂等键匹配: ${activeDedupeKeyMatchLabel}`)
  }
  if (activeQueryId && currentQueryOverview) {
    lines.push(`Query: ${activeQueryId}`)
    lines.push(`Query 阶段: ${currentQueryOverview.latestStage || '-'}`)
    lines.push(`Query 告警数: ${currentQueryOverview.warningCount}`)
  }
  if (activeQueryStage) {
    lines.push(`阶段聚焦: ${activeQueryStage}`)
  }
  if (activeQuerySearch) {
    lines.push(`History 搜索: ${activeQuerySearch}`)
  }
  if (Number(activeQueryHistoryPage || 1) > 1) {
    lines.push(`History 页: ${activeQueryHistoryPage}`)
  }
  if (autoFocusNotice) {
    lines.push(`聚焦原因: ${autoFocusNotice}`)
  }
  if (currentSnapshotRef?.source || currentSnapshotRef?.event_type) {
    lines.push(`后端引用: ${currentSnapshotRef.source || '-'} / ${currentSnapshotRef.event_type || '-'}`)
  }
  lines.push(`链接: ${currentViewUrl}`)
  return lines.join('\n')
}

export function buildCurrentGovernanceViewSnapshot(options = {}) {
  const {
    locationHref = 'http://localhost/',
    routeQuery = {},
    activeFilter = 'all',
    activeSeverity = 'all',
    activeFrameworkAdapterErrorType = '',
    activeDedupeKey = '',
    activeQueryId = '',
    activeQueryStage = '',
    activeQuerySearch = '',
    activeQueryHistoryPage = 1,
    activeSnapshotId = '',
    currentSnapshotRef = null,
    activeFilterLabel = '全部',
    activeSeverityLabel = '全部事件',
    filteredTimeline = [],
    scopedTimeline = [],
    activeFrameworkAdapterErrorTypeLabel = '',
    activeDedupeKeyMatchLabel = '',
    currentQueryOverview = null,
    autoFocusNotice = '',
  } = options

  const currentViewUrl = buildGovernanceViewUrl({
    locationHref,
    routeQuery,
    activeFilter,
    activeSeverity,
    activeFrameworkAdapterErrorType,
    activeDedupeKey,
    activeQueryId,
    activeQueryStage,
    activeQuerySearch,
    activeQueryHistoryPage,
    activeSnapshotId,
  })

  return buildGovernanceViewSnapshot({
    currentSnapshotRef,
    activeFilterLabel,
    activeSeverityLabel,
    filteredTimeline,
    scopedTimeline,
    activeFrameworkAdapterErrorTypeLabel,
    activeDedupeKey,
    activeDedupeKeyMatchLabel,
    activeQueryId,
    currentQueryOverview,
    activeQueryStage,
    activeQuerySearch,
    activeQueryHistoryPage,
    autoFocusNotice,
    currentViewUrl,
  })
}
