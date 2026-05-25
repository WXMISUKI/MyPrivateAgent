import { normalizeText, toTimestamp } from './governanceValueUtils'

export function buildMainChatHistoryStatus(history, loading, error) {
  if (error) {
    return '加载失败'
  }
  if (loading && !history?.items?.length) {
    return '正在读取最近记录'
  }
  if (history?.recordingState === 'recorded') {
    return `共 ${history.totalItems || 0} 条 · 第 ${history.page || 1} 页`
  }
  return history?.reason || '暂无 history'
}

export function filterMainChatHistoryItems(items, keyword) {
  const normalizedKeyword = normalizeText(keyword).toLowerCase()
  if (!normalizedKeyword) {
    return Array.isArray(items) ? items : []
  }
  return (Array.isArray(items) ? items : []).filter((item) => {
    return [
      item?.queryId,
      item?.latestStage,
      item?.latestSummary,
      item?.latestSnapshotId,
    ].some(value => normalizeText(value).toLowerCase().includes(normalizedKeyword))
  })
}

export function buildMainChatHistoryContextLabel(activeQueryId, activeQueryStage) {
  const queryId = normalizeText(activeQueryId)
  const stage = normalizeText(activeQueryStage)
  if (!queryId && !stage) {
    return ''
  }
  if (queryId && stage) {
    return `当前聚焦：${queryId} / ${stage}`
  }
  if (queryId) {
    return `当前聚焦：${queryId}`
  }
  return `当前阶段：${stage}`
}

export function buildHistoryStageTags(query, activeQueryId, activeQueryStage) {
  const stageCounts = query?.stageCounts && typeof query.stageCounts === 'object'
    ? query.stageCounts
    : {}
  return Object.entries(stageCounts)
    .filter(([stage]) => normalizeText(stage))
    .sort((left, right) => String(left[0]).localeCompare(String(right[0])))
    .map(([stage, count]) => ({
      key: stage,
      label: `${stage} ${Number(count || 0)}`,
      active: normalizeText(activeQueryId) === normalizeText(query?.queryId) && normalizeText(activeQueryStage) === stage,
    }))
}

export function isHistoryStageFocused(query, activeQueryId, activeQueryStage) {
  const queryId = normalizeText(activeQueryId)
  const stage = normalizeText(activeQueryStage)
  if (!queryId || !stage) {
    return false
  }
  return queryId === normalizeText(query?.queryId) && Boolean(query?.stageCounts?.[stage])
}

export function buildCurrentQueryOverview(queryDetailContract, activeQueryId, entries, entrySnapshotRef) {
  if (queryDetailContract?.connected) {
    return {
      queryId: queryDetailContract.queryId,
      latestStage: queryDetailContract.latestStage,
      latestSummary: queryDetailContract.latestSummary,
      latestSnapshotId: queryDetailContract.latestSnapshotId,
      stageCount: queryDetailContract.stageCount,
      warningCount: queryDetailContract.warningCount,
    }
  }
  const queryId = normalizeText(activeQueryId)
  if (!queryId) {
    return null
  }
  if (!entries.length) {
    return {
      queryId,
      latestStage: '',
      latestSummary: '',
      latestSnapshotId: '',
      stageCount: 0,
      warningCount: 0,
    }
  }
  const latest = entries[0]
  const stageSet = new Set(entries.map(entry => normalizeText(entry?.payload?.stage)).filter(Boolean))
  return {
    queryId,
    latestStage: normalizeText(latest?.payload?.stage),
    latestSummary: normalizeText(latest?.title || latest?.content),
    latestSnapshotId: entrySnapshotRef(latest)?.snapshot_id || '',
    stageCount: stageSet.size,
    warningCount: entries.filter(entry => entry.severity === 'warning').length,
  }
}

export function buildCurrentQueryDetail(queryDetailContract, activeQueryId, entries, options = {}) {
  const { entrySnapshotRef = () => null, getTimelineDedupeKey = () => '', toTimestamp: toTimestampFn = toTimestamp } = options
  if (queryDetailContract?.connected) {
    return queryDetailContract
  }
  const queryId = normalizeText(activeQueryId)
  if (!queryId) {
    return null
  }
  if (!entries.length) {
    return {
      queryId,
      stageChain: [],
      latestSnapshotId: '',
      dedupeKeyCount: 0,
      latestWarningSummary: '',
      recentEvents: [],
      latestStage: '',
      latestSummary: '',
      stageCount: 0,
      warningCount: 0,
      eventCount: 0,
      reason: '',
    }
  }

  const orderedEntries = [...entries].sort((left, right) => toTimestampFn(left.timestamp) - toTimestampFn(right.timestamp))
  const stageChain = []
  const dedupeKeys = new Set()
  let latestSnapshotId = ''
  let latestWarningSummary = ''
  const latestEntry = entries[0]
  let warningCount = 0

  for (const entry of orderedEntries) {
    const stage = normalizeText(entry?.payload?.stage)
    if (stage && stageChain[stageChain.length - 1] !== stage) {
      stageChain.push(stage)
    }
    const dedupeKey = getTimelineDedupeKey(entry)
    if (dedupeKey) {
      dedupeKeys.add(dedupeKey)
    }
    const snapshotId = entrySnapshotRef(entry)?.snapshot_id || ''
    if (snapshotId) {
      latestSnapshotId = snapshotId
    }
    if (entry.severity === 'warning') {
      latestWarningSummary = normalizeText(entry.title || entry.content)
      warningCount += 1
    }
  }

  return {
    queryId,
    stageChain,
    latestSnapshotId,
    dedupeKeyCount: dedupeKeys.size,
    latestWarningSummary,
    latestStage: normalizeText(latestEntry?.payload?.stage),
    latestSummary: normalizeText(latestEntry?.title || latestEntry?.content),
    stageCount: stageChain.length,
    warningCount,
    eventCount: orderedEntries.length,
    reason: '',
    recentEvents: orderedEntries.map(entry => ({
      timestamp: normalizeText(entry?.timestamp),
      stage: normalizeText(entry?.payload?.stage),
      summary: normalizeText(entry?.title || entry?.content),
      severity: normalizeText(entry?.severity) || 'info',
      snapshotId: entrySnapshotRef(entry)?.snapshot_id || '',
      dedupeKey: getTimelineDedupeKey(entry),
    })),
  }
}
