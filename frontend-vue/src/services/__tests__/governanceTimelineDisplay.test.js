import { describe, expect, it } from 'vitest'

import {
  formatAuditTime,
  formatSeverityBadge,
  formatSnapshotTime,
  getSeverityRank,
  truncateMiddle,
} from '../governanceTimelineDisplay'

describe('governanceTimelineDisplay', () => {
  it('formats severity badges and ranks', () => {
    expect(formatSeverityBadge('warning')).toBe('Warn')
    expect(formatSeverityBadge('success')).toBe('OK')
    expect(formatSeverityBadge('info')).toBe('Info')
    expect(getSeverityRank('warning')).toBe(3)
    expect(getSeverityRank('success')).toBe(2)
    expect(getSeverityRank('info')).toBe(1)
  })

  it('truncates long text in the middle', () => {
    expect(truncateMiddle('abc')).toBe('abc')
    expect(truncateMiddle('abcdefghijklmnopqrstuvwxyz', 20)).toBe('abcdefghijkl...opqrstuvwxyz')
  })

  it('formats audit and snapshot time values', () => {
    expect(formatAuditTime('2026-05-01T12:00:05Z')).toMatch(/^\d{2}:\d{2}:\d{2}$/)
    expect(formatAuditTime('not-a-date')).toBe('not-a-date')
    expect(formatSnapshotTime('2026-05-01T12:00:05Z')).toMatch(/^\d+\/\d+\/\d+ \d{2}:\d{2}:\d{2}$/)
    expect(formatSnapshotTime('')).toBe('--')
  })
})
