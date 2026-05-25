const STORAGE_KEY = 'governance_recent_snapshot_commands'
const MAX_RECENT_COMMANDS = 5

const DOMAIN_COMMAND_MAP = {
  mcp: 'mcp',
  permission: 'permissions',
  governance: 'gaps',
}

const ACTION_MAP = {
  snapshot: 'open_snapshot',
  mcp: 'open_mcp',
  permissions: 'open_permissions',
  gaps: 'open_gaps',
}

function normalizeDomain(domain) {
  return String(domain || '').trim().toLowerCase()
}

export function buildSnapshotCommandDescriptor(snapshotId, domain = '', metadata = {}) {
  const normalizedSnapshotId = String(snapshotId || '').trim()
  const normalizedDomain = normalizeDomain(domain)
  if (!normalizedSnapshotId) {
    return null
  }
  const commandName = DOMAIN_COMMAND_MAP[normalizedDomain] || 'snapshot'
  const params = commandName === 'snapshot'
    ? [normalizedSnapshotId]
    : ['snapshot', normalizedSnapshotId]
  return {
    commandName,
    action: ACTION_MAP[commandName] || 'open_snapshot',
    params,
    domain: normalizedDomain,
    snapshotId: normalizedSnapshotId,
    commandText: `/${commandName} ${params.join(' ')}`.trim(),
    eventType: String(metadata?.eventType || '').trim(),
    eventLabel: String(metadata?.eventLabel || '').trim(),
    summary: String(metadata?.summary || '').trim(),
  }
}

export function persistRecentSnapshotCommand(descriptor) {
  if (!descriptor?.commandText || !descriptor?.snapshotId) {
    return
  }
  const nextEntry = {
    commandText: descriptor.commandText,
    commandName: descriptor.commandName,
    action: descriptor.action,
    params: Array.isArray(descriptor.params) ? descriptor.params : [],
    domain: descriptor.domain || '',
    snapshotId: descriptor.snapshotId,
    eventType: String(descriptor.eventType || '').trim(),
    eventLabel: String(descriptor.eventLabel || '').trim(),
    summary: String(descriptor.summary || '').trim(),
    copiedAt: new Date().toISOString(),
  }
  const currentEntries = loadRecentSnapshotCommands()
  const dedupedEntries = currentEntries.filter(item => item.commandText !== nextEntry.commandText)
  const nextEntries = [nextEntry, ...dedupedEntries].slice(0, MAX_RECENT_COMMANDS)
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(nextEntries))
  } catch (_err) {
    // ignore storage failure
  }
}

export function loadRecentSnapshotCommands() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return []
    }
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) {
      return []
    }
    return parsed
      .map(item => ({
        commandText: String(item?.commandText || '').trim(),
        commandName: String(item?.commandName || '').trim(),
        action: String(item?.action || '').trim(),
        params: Array.isArray(item?.params) ? item.params.map(value => String(value || '').trim()).filter(Boolean) : [],
        domain: String(item?.domain || '').trim(),
        snapshotId: String(item?.snapshotId || '').trim(),
        eventType: String(item?.eventType || '').trim(),
        eventLabel: String(item?.eventLabel || '').trim(),
        summary: String(item?.summary || '').trim(),
        copiedAt: String(item?.copiedAt || '').trim(),
      }))
      .filter(item => item.commandText && item.commandName && item.snapshotId)
      .slice(0, MAX_RECENT_COMMANDS)
  } catch (_err) {
    return []
  }
}

export function buildRecentSnapshotCommandDisplay(item) {
  const domain = String(item?.domain || '').trim()
  const snapshotId = String(item?.snapshotId || '').trim()
  const eventLabel = String(item?.eventLabel || '').trim()
  const summary = String(item?.summary || '').trim()
  const copiedAt = String(item?.copiedAt || '').trim()
  const commandText = String(item?.commandText || '').trim()
  const commandName = String(item?.commandName || '').trim()
  const action = String(item?.action || '').trim()
  const params = Array.isArray(item?.params) ? item.params.map(value => String(value || '').trim()).filter(Boolean) : []
  const descriptionFragments = ['最近治理快照']
  if (eventLabel) {
    descriptionFragments.push(eventLabel)
  }
  if (snapshotId) {
    descriptionFragments.push(snapshotId)
  }
  if (summary) {
    descriptionFragments.push(summary)
  }
  const helpFragments = [`/${commandName || 'snapshot'} - ${commandText || '-'}`]
  if (eventLabel) {
    helpFragments.push(`事件 ${eventLabel}`)
  }
  if (snapshotId) {
    helpFragments.push(`快照 ${snapshotId}`)
  }
  if (summary) {
    helpFragments.push(`摘要 ${summary}`)
  }
  return {
    domain,
    snapshotId,
    eventLabel,
    summary,
    copiedAt,
    commandText,
    commandName,
    action,
    params,
    descriptionText: descriptionFragments.join(' · '),
    helpLineText: helpFragments.join(' · '),
    searchText: [
      commandText,
      commandName,
      domain,
      snapshotId,
      eventLabel,
      summary,
    ].filter(Boolean).join(' '),
  }
}

export function buildRecentSnapshotCommandsHelp(limit = 3) {
  const recentEntries = loadRecentSnapshotCommands().slice(0, Math.max(1, Number(limit) || 3))
  if (!recentEntries.length) {
    return ''
  }
  const lines = recentEntries.map(item => buildRecentSnapshotCommandDisplay(item).helpLineText)
  return ['最近治理快照命令:', ...lines].join('\n')
}
