import { computed, getCurrentInstance, onUnmounted, ref } from 'vue'
import {
  buildRecentSnapshotCommandDisplay,
  loadRecentSnapshotCommands,
  persistRecentSnapshotCommand,
} from '../services/governanceSnapshotCommands'
import { writeTextToClipboard as defaultWriteTextToClipboard } from '../services/governanceClipboard'

export function useRecentSnapshotCommands() {
  const recentSnapshotCommands = ref(loadRecentSnapshotCommands())
  const copiedCommandText = ref('')
  let copiedCommandResetTimer = null

  const copiedCommandDisplay = computed(() => {
    const matched = recentSnapshotCommands.value.find(item => item.commandText === copiedCommandText.value)
    return matched ? buildRecentSnapshotCommandDisplay(matched) : null
  })

  function refreshRecentSnapshotCommands() {
    recentSnapshotCommands.value = loadRecentSnapshotCommands()
  }

  function clearCopiedRecentSnapshotCommand() {
    if (copiedCommandResetTimer) {
      clearTimeout(copiedCommandResetTimer)
      copiedCommandResetTimer = null
    }
    copiedCommandText.value = ''
  }

  function markRecentSnapshotCommandCopied(commandText, timeoutMs = 1800) {
    const text = String(commandText || '').trim()
    if (!text) {
      clearCopiedRecentSnapshotCommand()
      return null
    }
    copiedCommandText.value = text
    if (copiedCommandResetTimer) {
      clearTimeout(copiedCommandResetTimer)
    }
    copiedCommandResetTimer = setTimeout(() => {
      copiedCommandText.value = ''
      copiedCommandResetTimer = null
    }, timeoutMs)
    return copiedCommandDisplay.value
  }

  function recordRecentSnapshotCommand(descriptor) {
    persistRecentSnapshotCommand(descriptor)
    refreshRecentSnapshotCommands()
    return descriptor
  }

  async function copyRecentSnapshotCommand(commandOrItem, options = {}) {
    const text = String(commandOrItem?.commandText || commandOrItem || '').trim()
    const writeText = options.writeTextToClipboard || defaultWriteTextToClipboard
    if (!text) {
      return false
    }
    try {
      await writeText(text)
      markRecentSnapshotCommandCopied(text, options.timeoutMs)
      options.onSuccess?.(text)
      return true
    } catch (error) {
      options.onError?.(error, text)
      return false
    }
  }

  if (getCurrentInstance()) {
    onUnmounted(() => {
      clearCopiedRecentSnapshotCommand()
    })
  }

  return {
    recentSnapshotCommands,
    copiedCommandText,
    copiedCommandDisplay,
    refreshRecentSnapshotCommands,
    recordRecentSnapshotCommand,
    markRecentSnapshotCommandCopied,
    copyRecentSnapshotCommand,
    clearCopiedRecentSnapshotCommand,
  }
}
