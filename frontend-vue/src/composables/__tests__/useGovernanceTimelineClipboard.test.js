import { beforeEach, describe, expect, it, vi } from 'vitest'
import { effectScope, ref } from 'vue'

import { useGovernanceTimelineClipboard } from '../useGovernanceTimelineClipboard'

describe('useGovernanceTimelineClipboard', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  it('copies current view and resets copied state on timer', async () => {
    const writeTextToClipboard = vi.fn().mockResolvedValue(undefined)
    const scope = effectScope()
    const state = scope.run(() => useGovernanceTimelineClipboard({
      error: ref(''),
      copiedViewLink: ref(false),
      recentCopiedCommandText: ref(''),
      buildCurrentViewSnapshot: () => '快照ID: TEST-1',
      writeTextToClipboard,
    }))

    await state.copyCurrentView()
    expect(writeTextToClipboard).toHaveBeenCalledWith('快照ID: TEST-1')
    expect(state).toBeTruthy()

    vi.advanceTimersByTime(1500)
    scope.stop()
  })

  it('copies snapshot command and tracks recent command text', async () => {
    const writeTextToClipboard = vi.fn().mockResolvedValue(undefined)
    const persistRecentSnapshotCommand = vi.fn()
    const copiedCommandTarget = ref('')
    const recentCopiedCommandText = ref('')
    const scope = effectScope()
    const state = scope.run(() => useGovernanceTimelineClipboard({
      error: ref(''),
      copiedCommandTarget,
      recentCopiedCommandText,
      entrySnapshotRef: entry => entry?.payload?.snapshot_ref || null,
      buildSnapshotCommandDescriptor: snapshotId => ({ commandText: `/snapshot ${snapshotId}` }),
      persistRecentSnapshotCommand,
      writeTextToClipboard,
    }))

    await state.copySnapshotCommand({
      key: 'entry-1',
      payload: {
        snapshot_ref: {
          snapshot_id: 'SNAP-1',
        },
      },
    })

    expect(writeTextToClipboard).toHaveBeenCalledWith('/snapshot SNAP-1')
    expect(persistRecentSnapshotCommand).toHaveBeenCalledWith(expect.objectContaining({ commandText: '/snapshot SNAP-1' }))
    expect(copiedCommandTarget.value).toBe('entry-1')
    expect(recentCopiedCommandText.value).toBe('/snapshot SNAP-1')

    vi.advanceTimersByTime(1500)
    expect(copiedCommandTarget.value).toBe('')
    scope.stop()
  })

  it('resets active dedupe copied state when requested', async () => {
    const writeTextToClipboard = vi.fn().mockResolvedValue(undefined)
    const copiedActiveDedupeKey = ref(false)
    const scope = effectScope()
    const state = scope.run(() => useGovernanceTimelineClipboard({
      error: ref(''),
      copiedActiveDedupeKey,
      getActiveDedupeKey: () => 'dedupe-1',
      writeTextToClipboard,
    }))

    await state.copyActiveDedupeKey()
    expect(copiedActiveDedupeKey.value).toBe(true)

    state.resetCopiedActiveDedupeKey()
    expect(copiedActiveDedupeKey.value).toBe(false)
    scope.stop()
  })

  it('opens runtime surface through injected action', () => {
    const openRuntimeSurface = vi.fn()
    const scope = effectScope()
    const state = scope.run(() => useGovernanceTimelineClipboard({
      error: ref(''),
      openRuntimeSurface,
    }))

    state.openRuntimeSurfacePanel()
    expect(openRuntimeSurface).toHaveBeenCalledTimes(1)
    scope.stop()
  })
})
