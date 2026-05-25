<template>
  <Teleport to="body">
    <div v-if="visible" class="command-palette-overlay" @click="close">
      <div class="command-palette" @click.stop>
        <div class="command-input-wrapper">
          <span class="command-icon">/</span>
          <input
            ref="inputRef"
            v-model="query"
            type="text"
            class="command-input"
            placeholder="输入命令..."
            @keydown.enter="executeCommand"
            @keydown.escape="close"
            @keydown.up.prevent="navigateUp"
            @keydown.down.prevent="navigateDown"
          />
          <span v-if="selectedCommand" class="command-hint">
            {{ selectedCommand.description }}
          </span>
        </div>

        <div v-if="filteredCommands.length > 0" class="command-list">
          <div v-if="filteredRecentCommands.length > 0" class="command-section">
            <div class="command-section-title">最近治理快照</div>
            <div
              v-for="(cmd, index) in filteredRecentCommands"
              :key="cmd.id"
              class="command-item"
              :class="{ active: index === activeIndex }"
              @click="executeCommandItem(cmd)"
              @mouseenter="activeIndex = index"
            >
              <span class="command-item-icon">{{ cmd.icon }}</span>
              <div class="command-item-content">
                <div class="command-item-name-row">
                  <span class="command-item-name">{{ cmd.display_name || `/${cmd.name}` }}</span>
                  <span class="command-item-badge">最近</span>
                </div>
                <span class="command-item-desc">{{ cmd.description }}</span>
              </div>
              <span v-if="cmd.has_param || cmd.hasParam" class="command-param-hint">
                {{ cmd.param_hint || cmd.paramHint }}
              </span>
            </div>
          </div>

          <div v-if="filteredRecentCommands.length > 0 && filteredBaseCommands.length > 0" class="command-section-divider"></div>

          <div v-if="filteredBaseCommands.length > 0" class="command-section">
            <div class="command-section-title">全部命令</div>
            <div
              v-for="(cmd, index) in filteredBaseCommands"
              :key="cmd.id"
              class="command-item"
              :class="{ active: index + filteredRecentCommands.length === activeIndex }"
              @click="executeCommandItem(cmd)"
              @mouseenter="activeIndex = index + filteredRecentCommands.length"
            >
              <span class="command-item-icon">{{ cmd.icon }}</span>
              <div class="command-item-content">
                <span class="command-item-name">{{ cmd.display_name || `/${cmd.name}` }}</span>
                <span class="command-item-desc">{{ cmd.description }}</span>
              </div>
              <span v-if="cmd.has_param || cmd.hasParam" class="command-param-hint">
                {{ cmd.param_hint || cmd.paramHint }}
              </span>
            </div>
          </div>
        </div>

        <div v-else-if="query && !selectedCommand" class="command-empty">
          <span>未找到命令: /{{ query }}</span>
        </div>

        <div class="command-footer">
          <span class="footer-hint">
            <kbd>↑↓</kbd> 选择
            <kbd>Enter</kbd> 执行
            <kbd>Esc</kbd> 关闭
          </span>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { localCommands, parseCommand } from '../services/commands'
import { commandApi } from '../api'
import { buildRecentSnapshotCommandDisplay, loadRecentSnapshotCommands } from '../services/governanceSnapshotCommands'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'execute'])

const inputRef = ref(null)
const query = ref('')
const activeIndex = ref(0)
const baseCommands = ref([...localCommands])
const recentCommands = ref([])

const filteredRecentCommands = computed(() => {
  if (!query.value) return recentCommands.value
  const lower = query.value.toLowerCase()
  return recentCommands.value.filter(cmd =>
    (cmd.search_text || '').toLowerCase().includes(lower) ||
    (cmd.name || '').toLowerCase().includes(lower) ||
    (cmd.description || '').toLowerCase().includes(lower) ||
    (cmd.display_name || '').toLowerCase().includes(lower) ||
    (cmd.command_text || '').toLowerCase().includes(lower)
  )
})

const filteredBaseCommands = computed(() => {
  if (!query.value) return baseCommands.value
  const lower = query.value.toLowerCase()
  return baseCommands.value.filter(cmd =>
    (cmd.name || '').toLowerCase().includes(lower) ||
    (cmd.description || '').toLowerCase().includes(lower) ||
    (cmd.display_name || '').toLowerCase().includes(lower) ||
    (cmd.command_text || '').toLowerCase().includes(lower)
  )
})

const filteredCommands = computed(() => {
  return [
    ...filteredRecentCommands.value,
    ...filteredBaseCommands.value
  ]
})

const selectedCommand = computed(() => {
  if (filteredCommands.value.length > 0 && activeIndex.value >= 0) {
    return filteredCommands.value[activeIndex.value]
  }
  return null
})

watch(() => props.visible, (newVal) => {
  if (newVal) {
    query.value = ''
    activeIndex.value = 0
    hydrateRecentCommands()
    nextTick(() => {
      inputRef.value?.focus()
    })
  }
})

watch(query, () => {
  activeIndex.value = 0
})

onMounted(async () => {
  hydrateRecentCommands()
  try {
    const response = await commandApi.list()
    if (Array.isArray(response.data) && response.data.length > 0) {
      baseCommands.value = response.data.map(cmd => ({
        ...cmd,
        has_param: Boolean(cmd.has_param || cmd.hasParam),
        param_hint: cmd.param_hint || cmd.paramHint || ''
      }))
    }
  } catch (error) {
    console.warn('[CommandPalette] 使用本地命令集', error)
  }
})

function navigateUp() {
  if (activeIndex.value > 0) {
    activeIndex.value--
  }
}

function navigateDown() {
  if (activeIndex.value < filteredCommands.value.length - 1) {
    activeIndex.value++
  }
}

function executeCommand() {
  const parsed = parseCommand('/' + query.value)
  if (parsed && !parsed.error) {
    emit('execute', parsed)
    close()
  } else if (selectedCommand.value) {
    executeCommandItem(selectedCommand.value)
  } else if (parsed && parsed.error === 'unknown_command') {
    close()
  }
}

function executeCommandItem(cmd) {
  if (Array.isArray(cmd.presetParams)) {
    emit('execute', {
      command: cmd,
      params: [...cmd.presetParams]
    })
    close()
    return
  }
  emit('execute', cmd)
  close()
}

function hydrateRecentCommands() {
  recentCommands.value = loadRecentSnapshotCommands().map(item => {
    const display = buildRecentSnapshotCommandDisplay(item)
    return {
      id: `recent-${display.snapshotId}`,
      name: display.commandName,
      display_name: display.commandText,
      command_text: display.commandText,
      description: display.descriptionText,
      icon: '🧷',
      action: display.action,
      category: 'recent',
      hasParam: true,
      paramHint: display.commandText,
      presetParams: display.params,
      search_text: display.searchText,
    }
  })
}

function close() {
  query.value = ''
  activeIndex.value = 0
  emit('close')
}
</script>

<style scoped>
.command-palette-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 15vh;
  z-index: 10000;
  animation: fadeIn 0.15s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.command-palette {
  width: 560px;
  max-width: 90vw;
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  animation: slideDown 0.2s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.command-input-wrapper {
  display: flex;
  align-items: center;
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--border-primary);
  gap: var(--space-sm);
}

.command-icon {
  font-size: 1.25rem;
  color: var(--text-tertiary);
  font-weight: 600;
}

.command-input {
  flex: 1;
  font-size: 1rem;
  color: var(--text-primary);
  background: transparent;
  border: none;
  outline: none;
  font-family: inherit;
}

.command-input::placeholder {
  color: var(--text-tertiary);
}

.command-hint {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  white-space: nowrap;
}

.command-list {
  max-height: 320px;
  overflow-y: auto;
  padding: var(--space-sm);
}

.command-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.command-section-title {
  padding: 8px 12px 4px;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.command-section-divider {
  height: 1px;
  margin: 8px 12px;
  background: var(--border-primary);
}

.command-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.15s;
}

.command-item:hover,
.command-item.active {
  background: var(--bg-elevated);
}

.command-item-icon {
  font-size: 1.25rem;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.command-item-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.command-item-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.command-item-name {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-primary);
  font-family: 'Consolas', monospace;
}

.command-item-desc {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.command-item-badge {
  font-size: 0.65rem;
  color: var(--text-accent);
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  background: rgba(59, 130, 246, 0.12);
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.command-param-hint {
  font-size: 0.7rem;
  color: var(--text-tertiary);
  padding: 2px 6px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  font-family: monospace;
}

.command-empty {
  padding: var(--space-lg);
  text-align: center;
  color: var(--text-tertiary);
  font-size: 0.875rem;
}

.command-footer {
  padding: var(--space-sm) var(--space-lg);
  border-top: 1px solid var(--border-primary);
  background: var(--bg-tertiary);
}

.footer-hint {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  display: flex;
  gap: var(--space-md);
}

.footer-hint kbd {
  padding: 2px 6px;
  background: var(--bg-surface);
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-size: 0.7rem;
  border: 1px solid var(--border-primary);
}
</style>
