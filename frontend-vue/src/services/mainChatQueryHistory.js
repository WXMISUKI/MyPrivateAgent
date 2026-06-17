import { normalizeObject, normalizeText } from './governanceValueUtils'

export function normalizeMainChatQueryHistoryContract(value) {
  const contract = normalizeObject(value)
  if (!Object.keys(contract).length) {
    return {
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
    }
  }

  return {
    connected: true,
    readModelLayer: normalizeText(contract.read_model_layer),
    sourceChannel: normalizeText(contract.source_channel),
    identityKind: normalizeText(contract.identity_kind),
    paginationMode: normalizeText(contract.pagination_mode),
    recordingState: normalizeText(contract.recording_state) || 'unavailable',
    items: Array.isArray(contract.items)
      ? contract.items.map((item) => ({
        readModelLayer: normalizeText(item?.read_model_layer),
        sourceChannel: normalizeText(item?.source_channel),
        identityKind: normalizeText(item?.identity_kind),
        queryId: normalizeText(item?.query_id),
        latestStage: normalizeText(item?.latest_stage),
        latestSummary: normalizeText(item?.latest_summary),
        latestTimestamp: normalizeText(item?.latest_timestamp),
        latestSnapshotId: normalizeText(item?.latest_snapshot_id),
        stageCounts: normalizeObject(item?.stage_counts),
        lastSuccessStage: normalizeText(item?.last_success_stage),
        lastWarningStage: normalizeText(item?.last_warning_stage),
        recordingState: normalizeText(item?.recording_state) || 'recorded',
      })).filter((item) => item.queryId)
      : [],
    page: Number(contract.page || 1),
    pageSize: Number(contract.page_size || 20),
    totalItems: Number(contract.total_items || 0),
    hasMore: Boolean(contract.has_more),
    nextCursor: normalizeText(contract.next_cursor),
    reason: normalizeText(contract.reason),
  }
}
