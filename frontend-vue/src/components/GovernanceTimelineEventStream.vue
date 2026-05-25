<template>
  <div class="panel-card">
    <div class="card-head">
      <h3>统一事件流</h3>
      <span class="muted">最近 {{ filteredTimeline.length }} / {{ scopedTimeline.length }} 条</span>
    </div>
    <GovernanceTimelineFilters
      :active-severity="activeSeverity"
      :active-filter="activeFilter"
      :severity-filters="severityFilters"
      :timeline-filters="timelineFilters"
      @update:active-severity="emit('update:active-severity', $event)"
      @update:active-filter="emit('update:active-filter', $event)"
    />
    <div class="timeline-list">
      <div v-if="activeDedupeKey && !filteredTimeline.length" class="timeline-empty-state">
        <strong>当前幂等键没有匹配到治理事件</strong>
        <span
          class="timeline-empty-dedupe-key"
          :title="activeDedupeKey"
          :aria-label="`当前幂等键 ${activeDedupeKey}`"
        >
          {{ activeDedupeKey }}
        </span>
        <button
          type="button"
          class="payload-toggle-btn"
          :title="activeDedupeKey"
          :aria-label="activeDedupeKeyEmptyClearLabel"
          @click="emit('clear-dedupe-key')"
        >
          清除幂等键聚焦
        </button>
      </div>
      <GovernanceTimelineEventCard
        v-for="entry in filteredTimeline"
        :key="entry.key"
        :entry="entry"
        :snapshot-ref="entrySnapshotRef(entry)"
        :highlighted="isSnapshotHighlighted(entry)"
        :has-payload="hasPayload(entry)"
        :payload-expanded="isPayloadExpanded(entry.key)"
        :payload-json="formatPayloadJson(entry.payload)"
        :copied-snapshot="copiedSnapshotKey === entry.key"
        :copied-command="copiedCommandTarget === entry.key"
        :copied-payload="copiedPayloadKey === entry.key"
        :copied-dedupe-key="copiedDedupeKey === entry.key"
        :focused-dedupe-key="activeDedupeKey === getTimelineDedupeKey(entry)"
        :focused-query-id="activeQueryId === getTimelineQueryId(entry)"
        :formatted-time="formatAuditTime(entry.timestamp)"
        @toggle-payload="emit('toggle-payload', $event)"
        @copy-snapshot-ref="emit('copy-snapshot-ref', $event)"
        @copy-snapshot-command="emit('copy-snapshot-command', $event)"
        @copy-payload="emit('copy-payload', $event)"
        @copy-dedupe-key="emit('copy-dedupe-key', $event)"
        @focus-dedupe-key="emit('focus-dedupe-key', $event)"
        @focus-query-id="emit('focus-query-id', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import GovernanceTimelineEventCard from './GovernanceTimelineEventCard.vue'
import GovernanceTimelineFilters from './GovernanceTimelineFilters.vue'

defineOptions({
  name: 'GovernanceTimelineEventStream',
})

defineProps({
  filteredTimeline: {
    type: Array,
    default: () => [],
  },
  scopedTimeline: {
    type: Array,
    default: () => [],
  },
  activeFilter: {
    type: String,
    default: '',
  },
  activeSeverity: {
    type: String,
    default: '',
  },
  activeDedupeKey: {
    type: String,
    default: '',
  },
  activeDedupeKeyEmptyClearLabel: {
    type: String,
    default: '',
  },
  copiedSnapshotKey: {
    type: String,
    default: '',
  },
  copiedCommandTarget: {
    type: String,
    default: '',
  },
  copiedPayloadKey: {
    type: String,
    default: '',
  },
  copiedDedupeKey: {
    type: String,
    default: '',
  },
  activeQueryId: {
    type: String,
    default: '',
  },
  severityFilters: {
    type: Array,
    default: () => [],
  },
  timelineFilters: {
    type: Array,
    default: () => [],
  },
  formatAuditTime: {
    type: Function,
    required: true,
  },
  formatPayloadJson: {
    type: Function,
    required: true,
  },
  entrySnapshotRef: {
    type: Function,
    required: true,
  },
  isSnapshotHighlighted: {
    type: Function,
    required: true,
  },
  hasPayload: {
    type: Function,
    required: true,
  },
  isPayloadExpanded: {
    type: Function,
    required: true,
  },
  getTimelineDedupeKey: {
    type: Function,
    required: true,
  },
  getTimelineQueryId: {
    type: Function,
    required: true,
  },
})

const emit = defineEmits([
  'update:active-severity',
  'update:active-filter',
  'toggle-payload',
  'copy-snapshot-ref',
  'copy-snapshot-command',
  'copy-payload',
  'copy-dedupe-key',
  'focus-dedupe-key',
  'focus-query-id',
  'clear-dedupe-key',
])
</script>
