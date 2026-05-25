import { normalizeText } from './governanceValueUtils'

export function normalizeMainChatQueryDetailContract(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return null
  }
  if (!Object.keys(value).length) {
    return null
  }

  return {
    connected: true,
    readModelLayer: normalizeText(value.read_model_layer),
    sourceChannel: normalizeText(value.source_channel),
    identityKind: normalizeText(value.identity_kind),
    queryId: normalizeText(value.query_id),
    latestStage: normalizeText(value.latest_stage),
    latestSummary: normalizeText(value.latest_summary),
    latestSnapshotId: normalizeText(value.latest_snapshot_id),
    latestWarningSummary: normalizeText(value.latest_warning_summary),
    stageChain: Array.isArray(value.stage_chain) ? value.stage_chain.map(item => normalizeText(item)).filter(Boolean) : [],
    dedupeKeys: Array.isArray(value.dedupe_keys) ? value.dedupe_keys.map(item => normalizeText(item)).filter(Boolean) : [],
    recentEvents: Array.isArray(value.recent_events) ? value.recent_events.map(item => ({
      timestamp: normalizeText(item?.timestamp),
      stage: normalizeText(item?.stage),
      summary: normalizeText(item?.summary),
      severity: normalizeText(item?.severity) || 'info',
      snapshotId: normalizeText(item?.snapshot_id),
      dedupeKey: normalizeText(item?.dedupe_key),
    })) : [],
    dedupeKeyCount: Number(value.dedupe_key_count ?? (Array.isArray(value.dedupe_keys) ? value.dedupe_keys.length : 0)),
    stageCount: Number(value.stage_count || 0),
    warningCount: Number(value.warning_count || 0),
    eventCount: Number(value.event_count || 0),
    recentEventCount: Number(value.recent_event_count ?? (Array.isArray(value.recent_events) ? value.recent_events.length : 0)),
    recordingState: normalizeText(value.recording_state) || 'unavailable',
    reason: normalizeText(value.reason),
  }
}
