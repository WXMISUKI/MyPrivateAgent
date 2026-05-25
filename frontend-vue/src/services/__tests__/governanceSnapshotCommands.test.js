import { describe, expect, it } from 'vitest'

import {
  buildRecentSnapshotCommandDisplay,
  buildRecentSnapshotCommandsHelp,
} from '../governanceSnapshotCommands'

describe('governanceSnapshotCommands', () => {
  it('builds a shared display model for recent snapshot commands', () => {
    const display = buildRecentSnapshotCommandDisplay({
      commandText: '/snapshot RUNT-BOOT-321',
      commandName: 'snapshot',
      action: 'open_snapshot',
      params: ['RUNT-BOOT-321'],
      domain: 'runtime_control',
      snapshotId: 'RUNT-BOOT-321',
      eventLabel: 'Embedded Runtime Bootstrap 更新',
      summary: 'workspace_mode=memory_only · runtime=memory_preview',
      copiedAt: '2026-05-20T10:00:00Z',
    })

    expect(display.descriptionText).toBe('最近治理快照 · Embedded Runtime Bootstrap 更新 · RUNT-BOOT-321 · workspace_mode=memory_only · runtime=memory_preview')
    expect(display.helpLineText).toBe('/snapshot - /snapshot RUNT-BOOT-321 · 事件 Embedded Runtime Bootstrap 更新 · 快照 RUNT-BOOT-321 · 摘要 workspace_mode=memory_only · runtime=memory_preview')
    expect(display.params).toEqual(['RUNT-BOOT-321'])
  })

  it('renders recent snapshot help text from stored commands', () => {
    localStorage.setItem('governance_recent_snapshot_commands', JSON.stringify([
      {
        commandText: '/mcp snapshot MCP-REF-1',
        commandName: 'mcp',
        action: 'open_mcp',
        params: ['snapshot', 'MCP-REF-1'],
        domain: 'mcp',
        snapshotId: 'MCP-REF-1',
        eventLabel: 'MCP Probe 完成',
        summary: 'status=ok',
        copiedAt: '2026-05-03T10:00:00Z',
      },
    ]))

    expect(buildRecentSnapshotCommandsHelp(3)).toContain('事件 MCP Probe 完成')
    expect(buildRecentSnapshotCommandsHelp(3)).toContain('摘要 status=ok')

    localStorage.removeItem('governance_recent_snapshot_commands')
  })
})
