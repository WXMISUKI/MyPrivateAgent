export function normalizeText(value) {
  return String(value || '').trim()
}

export function normalizeObject(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return {}
  }
  return value
}

export function normalizePayload(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return null
  }
  return payload
}

export function normalizeSnapshotRef(snapshotRef) {
  if (!snapshotRef || typeof snapshotRef !== 'object' || Array.isArray(snapshotRef)) {
    return null
  }
  const snapshotId = normalizeText(snapshotRef.snapshot_id)
  if (!snapshotId) {
    return null
  }
  return {
    snapshot_id: snapshotId,
    generated_at: normalizeText(snapshotRef.generated_at),
    conversation_id: snapshotRef.conversation_id ?? null,
    source: normalizeText(snapshotRef.source),
    event_type: normalizeText(snapshotRef.event_type),
  }
}

export function toTimestamp(value) {
  const date = new Date(value || '')
  return Number.isNaN(date.getTime()) ? 0 : date.getTime()
}

export function formatPayloadJson(payload) {
  try {
    return JSON.stringify(payload || {}, null, 2)
  } catch (_err) {
    return '{}'
  }
}

export function hasPayload(entry) {
  return Boolean(entry?.payload && Object.keys(entry.payload).length)
}

export function entrySnapshotRef(entry) {
  return normalizeSnapshotRef(entry?.payload?.snapshot_ref)
}

export function getTimelineDedupeKey(entry) {
  return normalizeText(entry?.payload?.dedupe_key)
}

export function getTimelineQueryId(entry) {
  return normalizeText(entry?.payload?.query_id)
}
