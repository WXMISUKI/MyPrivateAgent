<template>
  <div v-if="items.length" class="panel-card">
    <div class="card-head">
      <h3>最近治理快照命令</h3>
      <span class="muted">最近从治理时间线复制的 slash command，可直接复用</span>
    </div>
    <div class="recent-command-list">
      <div
        v-for="item in items"
        :key="`${item.snapshotId}-${item.copiedAt}`"
        class="recent-command-item"
      >
        <div class="recent-command-main">
          <div class="recent-command-text"><code>{{ item.commandText }}</code></div>
          <div class="recent-command-meta">
            <span v-if="item.domain">域: {{ item.domain }}</span>
            <span>快照: {{ item.snapshotId }}</span>
            <span v-if="item.eventLabel">事件: {{ item.eventLabel }}</span>
            <span v-if="item.copiedAt">复制于: {{ formatCopiedAt(item.copiedAt) }}</span>
          </div>
          <div v-if="item.summary" class="recent-command-summary">{{ item.summary }}</div>
        </div>
        <button class="secondary-btn recent-copy-btn" @click="$emit('copy-command', item)">
          {{ copiedCommandText === item.commandText ? '已复制' : '复制命令' }}
        </button>
      </div>
    </div>
    <p v-if="copiedCommandText" class="recent-command-note">
      最近复制：
      <span v-if="copiedCommandDisplay?.eventLabel">{{ copiedCommandDisplay.eventLabel }}</span>
      <span v-if="copiedCommandDisplay?.summary"> · {{ copiedCommandDisplay.summary }}</span>
      <code>{{ copiedCommandText }}</code>
    </p>
  </div>
</template>

<script setup>
defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  copiedCommandText: {
    type: String,
    default: '',
  },
  copiedCommandDisplay: {
    type: Object,
    default: null,
  },
})

defineEmits(['copy-command'])

function formatCopiedAt(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value || '-'
  }
  return date.toLocaleString()
}
</script>

<style scoped>
.panel-card {
  padding: var(--space-lg);
  margin-bottom: var(--space-lg);
  border: 1px solid var(--border-color);
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
}

.muted {
  color: var(--text-tertiary);
  font-size: 0.875rem;
}

.recent-command-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.recent-command-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  padding: var(--space-md);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
}

.recent-command-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.recent-command-text {
  color: var(--text-primary);
  word-break: break-all;
}

.recent-command-summary {
  color: var(--text-secondary);
  font-size: 0.84rem;
  line-height: 1.45;
}

.recent-command-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  color: var(--text-tertiary);
  font-size: 0.8rem;
}

.recent-copy-btn {
  flex-shrink: 0;
}

.recent-command-note {
  margin-top: var(--space-sm);
  color: var(--text-tertiary);
  font-size: 0.82rem;
}

.secondary-btn {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-color);
  background: var(--bg-elevated);
  color: var(--text-primary);
  border-radius: var(--radius-md);
  cursor: pointer;
}
</style>
