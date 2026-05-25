function normalizeText(value) {
  return String(value || '').trim()
}

function normalizeObject(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return {}
  }
  return value
}

export function normalizeSubagentLaneRecentSummaryContract(value) {
  const contract = normalizeObject(value)
  if (!Object.keys(contract).length) {
    return {
      connected: false,
      recordingState: 'unavailable',
      items: [],
      latestQueryId: '',
      latestStage: '',
      latestSummary: '',
      latestTimestamp: '',
      totalItems: 0,
      reason: '',
    }
  }

  return {
    connected: true,
    recordingState: normalizeText(contract.recording_state) || 'unavailable',
    items: Array.isArray(contract.items)
      ? contract.items.map((item) => ({
        queryId: normalizeText(item?.query_id),
        latestStage: normalizeText(item?.latest_stage),
        latestSummary: normalizeText(item?.latest_summary),
        latestTimestamp: normalizeText(item?.latest_timestamp),
        latestSnapshotId: normalizeText(item?.latest_snapshot_id),
        lastSuccessStage: normalizeText(item?.last_success_stage),
        lastWarningStage: normalizeText(item?.last_warning_stage),
        recordingState: normalizeText(item?.recording_state) || 'recorded',
      })).filter((item) => item.queryId)
      : [],
    latestQueryId: normalizeText(contract.latest_query_id),
    latestStage: normalizeText(contract.latest_stage),
    latestSummary: normalizeText(contract.latest_summary),
    latestTimestamp: normalizeText(contract.latest_timestamp),
    totalItems: Number(contract.total_items || 0),
    reason: normalizeText(contract.reason),
  }
}
