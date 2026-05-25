import { normalizePayload, normalizeText, toTimestamp } from './governanceValueUtils'

export function isGovernanceDomain(domain) {
  return [
    'doctor',
    'permission',
    'mcp',
    'governance',
    'scheduler',
    'hook',
    'runtime',
    'main_chat',
    'learning',
    'framework_adapter',
  ].includes(normalizeText(domain))
}

export function getLatestGovernanceTimestamp(item, options = {}) {
  const {
    inferTimelineDomain = () => '',
    normalizePayload: normalizePayloadFn = normalizePayload,
    toTimestamp: toTimestampFn = toTimestamp,
  } = options

  const traces = item?.run_trace || []
  const audits = item?.audit_trail || []
  const traceMax = traces.reduce((currentMax, entry) => {
    const domain = inferTimelineDomain(entry?.event_type, entry?.source, normalizePayloadFn(entry?.payload))
    if (!isGovernanceDomain(domain)) {
      return currentMax
    }
    return Math.max(currentMax, toTimestampFn(entry?.timestamp))
  }, 0)
  const auditMax = audits.reduce((currentMax, entry) => {
    const domain = inferTimelineDomain(entry?.event_type, '', normalizePayloadFn(entry?.payload))
    if (!isGovernanceDomain(domain)) {
      return currentMax
    }
    return Math.max(currentMax, toTimestampFn(entry?.timestamp))
  }, 0)
  return Math.max(traceMax, auditMax)
}

export function pickGovernanceFocusItem(plan, options = {}) {
  const { getLatestGovernanceTimestamp: getLatestGovernanceTimestampFn = () => 0 } = options
  const items = Array.isArray(plan?.items) ? plan.items : []
  if (!items.length) {
    return null
  }

  const withGovernanceTrace = [...items]
    .sort((left, right) => getLatestGovernanceTimestampFn(right) - getLatestGovernanceTimestampFn(left))
    .find(item => getLatestGovernanceTimestampFn(item) > 0)

  if (withGovernanceTrace) {
    return withGovernanceTrace
  }

  return (
    items.find(item => item.id === plan?.active_item_id) ||
    items.find(item => item.status === 'in_progress') ||
    items[0]
  )
}
