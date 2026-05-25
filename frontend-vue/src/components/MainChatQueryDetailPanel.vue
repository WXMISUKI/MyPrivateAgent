<template>
  <div class="contract-block query-detail-block">
    <h4>Query Detail</h4>
    <div class="query-detail-metadata">
      <span class="muted">layer: {{ detail.readModelLayer || '-' }}</span>
      <span class="muted">source: {{ detail.sourceChannel || '-' }}</span>
      <span class="muted">identity: {{ detail.identityKind || '-' }}</span>
    </div>
    <div class="query-detail-grid">
      <div>
        <div class="summary-label">阶段链</div>
        <div v-if="detail.stageChain.length" class="query-detail-stage-chain">
          <button
            v-for="stage in detail.stageChain"
            :key="stage"
            type="button"
            class="query-stage-chip"
            :class="{ active: activeStage === stage }"
            @click="$emit('focus-stage', stage)"
          >
            {{ stage }}
          </button>
        </div>
        <div v-else class="query-detail-value">暂无阶段链</div>
      </div>
      <div>
        <div class="summary-label">最近快照</div>
        <div class="query-detail-value">{{ detail.latestSnapshotId || '-' }}</div>
      </div>
      <div>
        <div class="summary-label">幂等键数量</div>
        <div class="query-detail-value">{{ detail.dedupeKeyCount }}</div>
      </div>
      <div>
        <div class="summary-label">最近告警</div>
        <div class="query-detail-value">{{ detail.latestWarningSummary || '无告警' }}</div>
      </div>
    </div>
    <div class="query-detail-events">
      <div class="summary-label">最近事件</div>
      <ul>
        <li v-if="!detail.recentEvents.length">暂无事件摘要</li>
        <li v-for="event in detail.recentEvents" :key="`${event.timestamp}-${event.stage}-${event.summary}`">
          <button
            type="button"
            class="query-detail-event-link"
            @click="$emit('focus-stage', event.stage)"
          >
            <code>{{ event.stage || '-' }}</code> · {{ event.summary || '无摘要' }} · {{ event.severity || 'info' }}
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
defineProps({
  detail: {
    type: Object,
    required: true,
  },
  activeStage: {
    type: String,
    default: '',
  },
})

defineEmits(['focus-stage'])
</script>

<style scoped>
.query-detail-block {
  margin-bottom: var(--space-lg);
  padding: var(--space-md);
}

.query-detail-metadata {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
  font-size: 0.76rem;
}

.query-detail-grid {
  display: grid;
  gap: var(--space-md);
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.query-detail-value {
  margin-top: 4px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.query-detail-stage-chain {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  margin-top: 4px;
}

.query-stage-chip,
.query-detail-event-link {
  border: 1px solid var(--border-color);
  background: var(--bg-elevated);
  color: var(--text-secondary);
  border-radius: var(--radius-md);
  cursor: pointer;
}

.query-stage-chip {
  padding: 4px 10px;
  font-size: 0.76rem;
}

.query-stage-chip.active {
  border-color: var(--border-primary);
  background: rgba(15, 118, 110, 0.08);
  color: var(--text-primary);
}

.query-detail-event-link {
  padding: 4px 8px;
  text-align: left;
}
</style>
