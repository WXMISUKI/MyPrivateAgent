<template>
  <div class="governance-timeline-filters">
    <div class="filter-chip-row severity-chip-row">
      <button
        v-for="option in severityFilters"
        :key="option.key"
        class="filter-chip severity-chip"
        :class="{ active: activeSeverity === option.key }"
        @click="$emit('update:activeSeverity', option.key)"
      >
        {{ option.label }} · {{ option.count }}
      </button>
    </div>
    <div class="filter-chip-row">
      <button
        v-for="filter in timelineFilters"
        :key="filter.key"
        class="filter-chip"
        :class="{ active: activeFilter === filter.key }"
        @click="$emit('update:activeFilter', filter.key)"
      >
        {{ filter.label }} · {{ filter.count }}
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  severityFilters: {
    type: Array,
    default: () => [],
  },
  timelineFilters: {
    type: Array,
    default: () => [],
  },
  activeSeverity: {
    type: String,
    default: 'all',
  },
  activeFilter: {
    type: String,
    default: 'all',
  },
})

defineEmits(['update:activeSeverity', 'update:activeFilter'])
</script>

<style scoped>
.filter-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.filter-chip {
  font-size: 0.74rem;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  cursor: pointer;
}

.filter-chip.active {
  color: var(--text-primary);
  border-color: var(--border-primary);
  background: rgba(15, 118, 110, 0.12);
}
</style>
