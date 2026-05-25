import { getCurrentInstance, onUnmounted, ref } from 'vue'
import { hasPayload } from '../services/governanceValueUtils'

function createResetScheduler(targetRef, nextValue, timeoutMs = 1500) {
  let timer = null

  function schedule() {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
    timer = setTimeout(() => {
      targetRef.value = nextValue
      timer = null
    }, timeoutMs)
  }

  function reset() {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
    targetRef.value = nextValue
  }

  function dispose() {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
  }

  return { schedule, reset, dispose }
}

export function useGovernanceTimelineClipboard(options = {}) {
  const {
    error = ref(''),
    copiedPayloadKey = ref(''),
    copiedDedupeKey = ref(''),
    copiedActiveDedupeKey = ref(false),
    copiedSnapshotKey = ref(''),
    copiedCommandTarget = ref(''),
    copiedViewLink = ref(false),
    recentCopiedCommandText = ref(''),
    hasPayload: hasPayloadFn = hasPayload,
    formatPayloadJson = () => '{}',
    entrySnapshotRef = () => null,
    buildSnapshotCommandDescriptor = () => null,
    persistRecentSnapshotCommand = () => {},
    inferSnapshotCommandDomain = () => '',
    buildCurrentViewSnapshot = () => '',
    openRuntimeSurface = () => {},
    getActiveDedupeKey = () => '',
    getCurrentSnapshotRef = () => null,
    getActiveFilter = () => 'all',
    writeTextToClipboard = async () => {},
  } = options

  const payloadReset = createResetScheduler(copiedPayloadKey, '')
  const dedupeReset = createResetScheduler(copiedDedupeKey, '')
  const activeDedupeReset = createResetScheduler(copiedActiveDedupeKey, false)
  const snapshotReset = createResetScheduler(copiedSnapshotKey, '')
  const commandReset = createResetScheduler(copiedCommandTarget, '')
  const viewReset = createResetScheduler(copiedViewLink, false)

  async function copyFrameworkAdapterRemediationCommand(commandText) {
    const text = String(commandText || '').trim()
    if (!text) {
      return
    }
    try {
      await writeTextToClipboard(text)
      recentCopiedCommandText.value = text
      copiedCommandTarget.value = 'framework-remediation'
      error.value = ''
      commandReset.schedule()
    } catch (_err) {
      copiedCommandTarget.value = ''
      error.value = '当前环境不支持复制修复命令'
    }
  }

  async function copyPayload(entry) {
    if (!hasPayloadFn(entry)) {
      return
    }
    try {
      await writeTextToClipboard(formatPayloadJson(entry.payload))
      copiedPayloadKey.value = entry.key
      error.value = ''
      payloadReset.schedule()
    } catch (_err) {
      copiedPayloadKey.value = ''
      error.value = '当前环境不支持复制 Payload'
    }
  }

  async function copyDedupeKey(entry) {
    const dedupeKey = String(entry?.payload?.dedupe_key || '').trim()
    if (!dedupeKey) {
      return
    }
    try {
      await writeTextToClipboard(dedupeKey)
      copiedDedupeKey.value = entry.key
      error.value = ''
      dedupeReset.schedule()
    } catch (_err) {
      copiedDedupeKey.value = ''
      error.value = '当前环境不支持复制幂等键'
    }
  }

  async function copyActiveDedupeKey() {
    const activeDedupeKey = getActiveDedupeKey()
    if (!activeDedupeKey) {
      return
    }
    try {
      await writeTextToClipboard(activeDedupeKey)
      copiedActiveDedupeKey.value = true
      error.value = ''
      activeDedupeReset.schedule()
    } catch (_err) {
      copiedActiveDedupeKey.value = false
      error.value = '当前环境不支持复制幂等键'
    }
  }

  async function copySnapshotRef(entry) {
    const snapshotRef = entrySnapshotRef(entry)
    if (!snapshotRef) {
      return
    }
    try {
      await writeTextToClipboard([
        `快照ID: ${snapshotRef.snapshot_id}`,
        `生成时间: ${snapshotRef.generated_at || '-'}`,
        `来源: ${snapshotRef.source || '-'} / ${snapshotRef.event_type || '-'}`,
        `会话: ${snapshotRef.conversation_id ?? '-'}`,
      ].join('\n'))
      copiedSnapshotKey.value = entry.key
      error.value = ''
      snapshotReset.schedule()
    } catch (_err) {
      copiedSnapshotKey.value = ''
      error.value = '当前环境不支持复制治理引用'
    }
  }

  async function copySnapshotCommand(entry) {
    const snapshotRef = entrySnapshotRef(entry)
    if (!snapshotRef) {
      return
    }
    try {
      const descriptor = buildSnapshotCommandDescriptor(snapshotRef.snapshot_id, entry?.domain, {
        eventType: entry?.title,
        eventLabel: entry?.title,
        summary: entry?.content || entry?.payloadSummary || entry?.detail || '',
      })
      if (!descriptor) {
        return
      }
      await writeTextToClipboard(descriptor.commandText)
      persistRecentSnapshotCommand(descriptor)
      recentCopiedCommandText.value = descriptor.commandText
      copiedCommandTarget.value = entry.key
      error.value = ''
      commandReset.schedule()
    } catch (_err) {
      copiedCommandTarget.value = ''
      error.value = '当前环境不支持复制快照命令'
    }
  }

  async function copyCurrentSnapshotCommand() {
    const currentSnapshotRef = getCurrentSnapshotRef()
    if (!currentSnapshotRef) {
      return
    }
    try {
      const currentDomain = inferSnapshotCommandDomain(currentSnapshotRef, getActiveFilter())
      const descriptor = buildSnapshotCommandDescriptor(currentSnapshotRef.snapshot_id, currentDomain, {
        eventType: currentSnapshotRef.event_type,
        summary: '',
      })
      if (!descriptor) {
        return
      }
      await writeTextToClipboard(descriptor.commandText)
      persistRecentSnapshotCommand(descriptor)
      recentCopiedCommandText.value = descriptor.commandText
      copiedCommandTarget.value = 'view'
      error.value = ''
      commandReset.schedule()
    } catch (_err) {
      copiedCommandTarget.value = ''
      error.value = '当前环境不支持复制快照命令'
    }
  }

  async function copyCurrentView() {
    const snapshotText = buildCurrentViewSnapshot()
    if (!snapshotText) {
      return
    }
    try {
      await writeTextToClipboard(snapshotText)
      copiedViewLink.value = true
      error.value = ''
      viewReset.schedule()
    } catch (_err) {
      copiedViewLink.value = false
      error.value = '当前环境不支持复制治理视图'
    }
  }

  function openRuntimeSurfacePanel() {
    openRuntimeSurface()
  }

  function resetCopiedActiveDedupeKey() {
    activeDedupeReset.reset()
  }

  function clearClipboardState() {
    payloadReset.dispose()
    dedupeReset.dispose()
    activeDedupeReset.dispose()
    snapshotReset.dispose()
    commandReset.dispose()
    viewReset.dispose()
    recentCopiedCommandText.value = ''
  }

  if (getCurrentInstance()) {
    onUnmounted(clearClipboardState)
  }

  return {
    copyFrameworkAdapterRemediationCommand,
    copyPayload,
    copyDedupeKey,
    copyActiveDedupeKey,
    copySnapshotRef,
    copySnapshotCommand,
    copyCurrentSnapshotCommand,
    copyCurrentView,
    openRuntimeSurfacePanel,
    resetCopiedActiveDedupeKey,
    clearClipboardState,
    writeTextToClipboard,
  }
}
