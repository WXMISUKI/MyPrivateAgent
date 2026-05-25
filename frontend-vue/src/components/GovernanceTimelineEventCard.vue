<template>
  <div
    class="timeline-item"
    :class="[`severity-${entry.severity}`, { highlighted }]"
  >
    <div class="timeline-top">
      <span class="timeline-badges">
        <span class="timeline-kind">{{ entry.kindLabel }}</span>
        <span v-if="entry.domainLabel" class="timeline-source">{{ entry.domainLabel }}</span>
        <span v-if="entry.sourceLabel" class="timeline-source">{{ entry.sourceLabel }}</span>
        <span class="timeline-event">{{ entry.title }}</span>
      </span>
      <span class="timeline-time">{{ formattedTime }}</span>
    </div>
    <div class="timeline-content">{{ entry.content }}</div>
    <div v-if="entry.detail" class="timeline-detail">{{ entry.detail }}</div>
    <div v-if="snapshotRef" class="timeline-snapshot-ref">
      引用 {{ snapshotRef.snapshot_id }}
    </div>
    <div
      v-if="dedupeKeyPreview"
      class="timeline-dedupe-key"
      :title="dedupeKey"
      :aria-label="`幂等键 ${dedupeKey}`"
    >
      幂等键 {{ dedupeKeyPreview }}
    </div>
    <div v-if="entry.payloadSummary" class="timeline-payload-summary">{{ entry.payloadSummary }}</div>
    <div
      v-if="queryId"
      class="timeline-query-id"
      :title="queryId"
      :aria-label="`Query ${queryId}`"
    >
      Query {{ queryId }}
    </div>
    <div v-if="hasPayload" class="timeline-payload-actions">
      <button class="payload-toggle-btn" @click="$emit('toggle-payload', entry)">
        {{ payloadExpanded ? '收起 Payload' : '展开 Payload' }}
      </button>
      <button v-if="snapshotRef" class="payload-toggle-btn" @click="$emit('copy-snapshot-ref', entry)">
        {{ copiedSnapshot ? '已复制引用' : '复制引用' }}
      </button>
      <button v-if="snapshotRef" class="payload-toggle-btn" @click="$emit('copy-snapshot-command', entry)">
        {{ copiedCommand ? '已复制命令' : '复制命令' }}
      </button>
      <button class="payload-toggle-btn" @click="$emit('copy-payload', entry)">
        {{ copiedPayload ? '已复制 Payload' : '复制 Payload' }}
      </button>
      <button
        v-if="queryId"
        class="payload-toggle-btn"
        :title="queryId"
        :aria-label="queryFocusButtonLabel"
        :disabled="focusedQueryId"
        @click="$emit('focus-query-id', entry)"
      >
        {{ focusedQueryId ? '已聚焦 Query' : '聚焦 Query' }}
      </button>
      <button
        v-if="dedupeKey"
        class="payload-toggle-btn"
        :title="dedupeKey"
        :aria-label="dedupeCopyButtonLabel"
        @click="$emit('copy-dedupe-key', entry)"
      >
        {{ copiedDedupeKey ? '已复制幂等键' : '复制幂等键' }}
      </button>
      <button
        v-if="dedupeKey"
        class="payload-toggle-btn"
        :title="dedupeKey"
        :aria-label="dedupeFocusButtonLabel"
        :disabled="focusedDedupeKey"
        @click="$emit('focus-dedupe-key', entry)"
      >
        {{ focusedDedupeKey ? '已聚焦幂等键' : '聚焦幂等键' }}
      </button>
    </div>
    <pre v-if="hasPayload && payloadExpanded" class="timeline-payload-json">{{ payloadJson }}</pre>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  entry: {
    type: Object,
    required: true,
  },
  snapshotRef: {
    type: Object,
    default: null,
  },
  highlighted: {
    type: Boolean,
    default: false,
  },
  hasPayload: {
    type: Boolean,
    default: false,
  },
  payloadExpanded: {
    type: Boolean,
    default: false,
  },
  payloadJson: {
    type: String,
    default: '',
  },
  copiedSnapshot: {
    type: Boolean,
    default: false,
  },
  copiedCommand: {
    type: Boolean,
    default: false,
  },
  copiedPayload: {
    type: Boolean,
    default: false,
  },
  copiedDedupeKey: {
    type: Boolean,
    default: false,
  },
  focusedDedupeKey: {
    type: Boolean,
    default: false,
  },
  focusedQueryId: {
    type: Boolean,
    default: false,
  },
  formattedTime: {
    type: String,
    default: '',
  },
})

const dedupeKey = computed(() => String(props.entry?.payload?.dedupe_key || '').trim())
const queryId = computed(() => String(props.entry?.payload?.query_id || '').trim())

const dedupeKeyPreview = computed(() => {
  const rawKey = dedupeKey.value
  if (!rawKey) return ''
  return truncateMiddle(rawKey, 96)
})

const dedupeFocusButtonLabel = computed(() => {
  const prefix = props.focusedDedupeKey ? '已聚焦幂等键' : '聚焦幂等键'
  return `${prefix} ${dedupeKey.value}`
})

const dedupeCopyButtonLabel = computed(() => {
  const prefix = props.copiedDedupeKey ? '已复制幂等键' : '复制幂等键'
  return `${prefix} ${dedupeKey.value}`
})

const queryFocusButtonLabel = computed(() => {
  const prefix = props.focusedQueryId ? '已聚焦 Query' : '聚焦 Query'
  return `${prefix} ${queryId.value}`
})

function truncateMiddle(value, maxLength = 96) {
  const text = String(value || '').trim()
  if (text.length <= maxLength) {
    return text
  }
  const prefixLength = 56
  const suffixLength = Math.max(16, maxLength - prefixLength - 3)
  return `${text.slice(0, prefixLength)}...${text.slice(-suffixLength)}`
}

defineEmits([
  'toggle-payload',
  'copy-snapshot-ref',
  'copy-snapshot-command',
  'copy-payload',
  'copy-dedupe-key',
  'focus-dedupe-key',
  'focus-query-id',
])
</script>

<style scoped>
.timeline-item {
  border: 1px solid var(--border-color);
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
  border-left: 3px solid rgba(148, 163, 184, 0.25);
}

.timeline-item.severity-warning {
  border-left-color: rgba(249, 115, 22, 0.45);
}

.timeline-item.severity-success {
  border-left-color: rgba(34, 197, 94, 0.45);
}

.timeline-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
}

.timeline-badges {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.timeline-kind,
.timeline-source,
.timeline-event {
  font-size: 0.74rem;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
}

.timeline-event {
  color: var(--text-primary);
}

.timeline-time {
  font-size: 0.72rem;
  color: var(--text-tertiary);
}

.timeline-content {
  margin-top: 6px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.timeline-detail {
  margin-top: 4px;
  color: var(--text-tertiary);
  font-size: 0.82rem;
  line-height: 1.5;
  white-space: pre-wrap;
}

.timeline-payload-summary {
  margin-top: 6px;
  color: var(--text-secondary);
  font-size: 0.78rem;
  line-height: 1.5;
}

.timeline-snapshot-ref {
  margin-top: 6px;
  color: var(--text-tertiary);
  font-size: 0.76rem;
  line-height: 1.5;
}

.timeline-dedupe-key {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  margin-top: 6px;
  padding: 3px 8px;
  border: 1px solid rgba(59, 130, 246, 0.22);
  border-radius: 999px;
  background: rgba(59, 130, 246, 0.08);
  color: var(--text-tertiary);
  font-size: 0.72rem;
  line-height: 1.4;
  overflow-wrap: anywhere;
}

.timeline-query-id {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  margin-top: 6px;
  padding: 3px 8px;
  border: 1px solid rgba(15, 118, 110, 0.22);
  border-radius: 999px;
  background: rgba(15, 118, 110, 0.08);
  color: var(--text-tertiary);
  font-size: 0.72rem;
  line-height: 1.4;
  overflow-wrap: anywhere;
}

.timeline-payload-actions {
  margin-top: 8px;
}

.payload-toggle-btn {
  padding: 4px 10px;
  border: 1px solid var(--border-color);
  background: var(--bg-elevated);
  color: var(--text-secondary);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 0.76rem;
}

.timeline-payload-json {
  margin-top: 8px;
  padding: var(--space-sm);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-secondary);
  overflow-x: auto;
  font-size: 0.78rem;
  line-height: 1.5;
}
</style>
