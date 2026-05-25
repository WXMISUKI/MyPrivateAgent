import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { useRecentSnapshotCommands } from '../useRecentSnapshotCommands'

describe('useRecentSnapshotCommands', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('persists and refreshes recent snapshot commands', () => {
    const state = useRecentSnapshotCommands()

    state.recordRecentSnapshotCommand({
      commandText: '/mcp snapshot MCP-REF-1',
      commandName: 'mcp',
      action: 'open_mcp',
      params: ['snapshot', 'MCP-REF-1'],
      domain: 'mcp',
      snapshotId: 'MCP-REF-1',
      eventLabel: 'MCP Probe 完成',
      summary: 'status=ok',
    })

    expect(state.recentSnapshotCommands.value).toEqual([
      expect.objectContaining({
        commandText: '/mcp snapshot MCP-REF-1',
        snapshotId: 'MCP-REF-1',
        eventLabel: 'MCP Probe 完成',
        summary: 'status=ok',
      }),
    ])
  })

  it('exposes copied command display and clears it after timeout', async () => {
    const state = useRecentSnapshotCommands()
    state.recordRecentSnapshotCommand({
      commandText: '/snapshot RUNT-BOOT-1',
      commandName: 'snapshot',
      action: 'open_snapshot',
      params: ['RUNT-BOOT-1'],
      domain: 'runtime_control',
      snapshotId: 'RUNT-BOOT-1',
      eventLabel: 'Embedded Runtime Bootstrap 更新',
      summary: 'workspace_mode=memory_only',
    })

    state.markRecentSnapshotCommandCopied('/snapshot RUNT-BOOT-1')
    await nextTick()

    expect(state.copiedCommandText.value).toBe('/snapshot RUNT-BOOT-1')
    expect(state.copiedCommandDisplay.value).toEqual(expect.objectContaining({
      eventLabel: 'Embedded Runtime Bootstrap 更新',
      summary: 'workspace_mode=memory_only',
      commandText: '/snapshot RUNT-BOOT-1',
    }))

    vi.advanceTimersByTime(1800)
    await nextTick()

    expect(state.copiedCommandText.value).toBe('')
    expect(state.copiedCommandDisplay.value).toBeNull()
  })

  it('copies a recent snapshot command through injected clipboard writer', async () => {
    const writeTextToClipboard = vi.fn().mockResolvedValue()
    const state = useRecentSnapshotCommands()
    state.recordRecentSnapshotCommand({
      commandText: '/mcp snapshot MCP-REF-1',
      commandName: 'mcp',
      action: 'open_mcp',
      params: ['snapshot', 'MCP-REF-1'],
      domain: 'mcp',
      snapshotId: 'MCP-REF-1',
      eventLabel: 'MCP Probe 完成',
      summary: 'status=ok',
    })

    const copied = await state.copyRecentSnapshotCommand(
      state.recentSnapshotCommands.value[0],
      { writeTextToClipboard }
    )

    expect(copied).toBe(true)
    expect(writeTextToClipboard).toHaveBeenCalledWith('/mcp snapshot MCP-REF-1')
    expect(state.copiedCommandText.value).toBe('/mcp snapshot MCP-REF-1')
    expect(state.copiedCommandDisplay.value).toEqual(expect.objectContaining({
      eventLabel: 'MCP Probe 完成',
      summary: 'status=ok',
    }))
  })
})
