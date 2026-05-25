<template>
  <div v-if="cards.length" class="summary-grid governance-overview-grid">
    <div
      v-for="card in cards"
      :key="card.key"
      class="summary-card governance-overview-card"
      :class="[{ active: activeFilter === card.key }, `severity-${card.severity || 'info'}`]"
    >
      <button type="button" class="overview-card-main" @click="emit('select-card', card.key)">
        <div class="overview-card-head">
          <span class="summary-label">{{ card.label }}</span>
          <span class="overview-severity-badge" :class="`severity-${card.severity || 'info'}`">
            {{ formatSeverityBadge(card.severity) }}
          </span>
        </div>
        <strong>{{ card.count }}</strong>
        <span class="overview-card-metrics">总事件 {{ card.count }} · 告警 {{ card.warningCount }}</span>
        <span class="overview-card-title">{{ card.latestTitle || '无最近事件' }}</span>
        <span class="overview-card-time">{{ formatAuditTime(card.latestTimestamp) }}</span>
      </button>
      <div class="overview-card-actions">
        <button
          type="button"
          class="overview-risk-btn"
          :class="{ active: activeFilter === card.key && activeSeverity === 'warning' }"
          :disabled="card.warningCount === 0"
          @click="emit('focus-warning', card.key)"
        >
          {{ card.warningCount > 0 ? `仅告警 · ${card.warningCount}` : '无告警' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineOptions({
  name: 'GovernanceTimelineOverviewCards',
})

defineProps({
  cards: {
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
  formatSeverityBadge: {
    type: Function,
    required: true,
  },
  formatAuditTime: {
    type: Function,
    required: true,
  },
})

const emit = defineEmits(['select-card', 'focus-warning'])
</script>
