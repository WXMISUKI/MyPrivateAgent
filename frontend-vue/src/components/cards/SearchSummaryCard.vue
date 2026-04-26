<template>
  <div class="search-summary-card">
    <div class="search-summary-header">
      <div class="search-summary-label">搜索摘要</div>
      <div class="search-status" :class="card.status">{{ statusText }}</div>
    </div>

    <div class="search-query">{{ card.query }}</div>
    <div v-if="metaItems.length" class="search-meta-row">
      <span
        v-for="item in metaItems"
        :key="item.label"
        class="search-meta-pill"
      >
        {{ item.label }}
      </span>
    </div>
    <div class="search-summary-text">{{ card.summary }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  card: {
    type: Object,
    required: true
  }
})

const statusText = computed(() => {
  if (props.card.status === 'not_found') return '未命中'
  if (props.card.status === 'error') return '异常'
  return '结果'
})

const metaItems = computed(() => {
  const items = []

  if (props.card.source_label) {
    items.push({ label: `来源：${props.card.source_label}` })
  }

  if (typeof props.card.source_count === 'number') {
    items.push({ label: `来源数：${props.card.source_count}` })
  }

  return items
})
</script>

<style scoped>
.search-summary-card {
  margin-bottom: var(--space-sm);
  padding: var(--space-md);
  border-radius: var(--radius-lg);
  border: 1px solid rgba(99, 102, 241, 0.18);
  background:
    linear-gradient(145deg, rgba(30, 41, 59, 0.82), rgba(51, 65, 85, 0.96)),
    radial-gradient(circle at top right, rgba(129, 140, 248, 0.24), transparent 38%);
  color: #f8fafc;
}

.search-summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-sm);
}

.search-summary-label {
  font-size: 0.8rem;
  color: #cbd5e1;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.search-status {
  padding: 3px 8px;
  border-radius: var(--radius-full);
  font-size: 0.74rem;
  font-weight: 600;
  background: rgba(129, 140, 248, 0.18);
  color: #e0e7ff;
}

.search-status.not_found {
  background: rgba(245, 158, 11, 0.16);
  color: #fde68a;
}

.search-status.error {
  background: rgba(239, 68, 68, 0.18);
  color: #fecaca;
}

.search-query {
  margin-top: var(--space-sm);
  font-size: 1rem;
  font-weight: 700;
  color: #ffffff;
}

.search-meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.search-meta-pill {
  padding: 4px 10px;
  border-radius: var(--radius-full);
  background: rgba(191, 219, 254, 0.14);
  color: #bfdbfe;
  font-size: 0.76rem;
  line-height: 1;
}

.search-summary-text {
  margin-top: var(--space-sm);
  font-size: 0.88rem;
  line-height: 1.6;
  color: #dbeafe;
}
</style>
