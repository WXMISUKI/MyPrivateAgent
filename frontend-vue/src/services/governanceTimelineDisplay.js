import { normalizeText } from './governanceValueUtils'

export function truncateMiddle(value, maxLength = 88) {
  const text = normalizeText(value)
  if (text.length <= maxLength) {
    return text
  }
  const edgeLength = Math.max(12, Math.floor((maxLength - 3) / 2))
  return `${text.slice(0, edgeLength)}...${text.slice(-edgeLength)}`
}

export function getSeverityRank(severity) {
  const ranks = {
    warning: 3,
    success: 2,
    info: 1,
  }
  return Number(ranks[normalizeText(severity) || 'info'] || 0)
}

export function formatSeverityBadge(severity) {
  const value = normalizeText(severity) || 'info'
  if (value === 'warning') return 'Warn'
  if (value === 'success') return 'OK'
  return 'Info'
}

export function formatAuditTime(value) {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`
}

export function formatSnapshotTime(value) {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return `${date.toLocaleDateString()} ${formatAuditTime(value)}`
}
