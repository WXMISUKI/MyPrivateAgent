<template>
  <div v-if="hasDebugContent" class="runtime-debug-panel">
    <button class="debug-header" type="button" @click="collapsed = !collapsed">
      <span class="debug-icon">🧭</span>
      <span class="debug-title">运行调试信息</span>
      <span class="debug-toggle">{{ collapsed ? '展开' : '收起' }}</span>
    </button>

    <template v-if="!collapsed">
    <div v-if="runtimeKnowledge" class="debug-section">
      <div class="section-title">Runtime Knowledge</div>
      <div class="meta-line">
        <span>scope: {{ runtimeKnowledge.scope || 'global' }}</span>
        <span>prompts: {{ runtimeKnowledge.promptCount || 0 }}</span>
        <span>practices: {{ runtimeKnowledge.practiceCount || 0 }}</span>
      </div>
      <div v-if="runtimeKnowledge.selectedItems?.length" class="chips">
        <span
          v-for="item in runtimeKnowledge.selectedItems"
          :key="`${item.type}-${item.id}`"
          class="chip chip-selected"
        >
          {{ item.type }} / {{ item.id }} / {{ item.level }}
        </span>
      </div>
      <div v-if="runtimeKnowledge.skippedItems?.length" class="chips">
        <span
          v-for="item in runtimeKnowledge.skippedItems"
          :key="`${item.type}-${item.id}-skipped`"
          class="chip chip-skipped"
        >
          {{ item.id }}: {{ item.reason }}
        </span>
      </div>
    </div>

    <div v-if="toolExecution" class="debug-section">
      <div class="section-title">Tool Execution</div>
      <div class="meta-line">
        <span>source: {{ toolExecution.result_source || 'tool' }}</span>
        <span>cache: {{ toolExecution.cache_hit ? 'hit' : 'miss' }}</span>
        <span v-if="toolExecution.duration_ms !== null && toolExecution.duration_ms !== undefined">
          duration: {{ formatDuration(toolExecution.duration_ms) }}
        </span>
        <span v-if="toolExecution.status">status: {{ toolExecution.status }}</span>
      </div>
    </div>
    </template>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  runtimeKnowledge: {
    type: Object,
    default: null
  },
  toolExecution: {
    type: Object,
    default: null
  }
})

const hasDebugContent = computed(() => {
  return !!props.runtimeKnowledge || !!props.toolExecution
})

const collapsed = ref(true)

function formatDuration(value) {
  const numeric = Number(value)
  if (Number.isNaN(numeric)) return '-'
  return `${numeric.toFixed(numeric >= 10 ? 0 : 2)} ms`
}
</script>

<style scoped>
.runtime-debug-panel {
  margin-top: var(--space-sm);
  padding: var(--space-md);
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(59, 130, 246, 0.06) 100%);
}

.debug-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  justify-content: space-between;
  margin-bottom: var(--space-sm);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  width: 100%;
  border: none;
  background: transparent;
  padding: 0;
  cursor: pointer;
  text-align: left;
}

.debug-toggle {
  font-size: 12px;
  color: var(--text-tertiary);
}

.debug-section + .debug-section {
  margin-top: var(--space-sm);
  padding-top: var(--space-sm);
  border-top: 1px solid rgba(148, 163, 184, 0.15);
}

.section-title {
  margin-bottom: var(--space-xs);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.meta-line {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  font-size: var(--text-sm);
  color: var(--text-primary);
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  margin-top: var(--space-sm);
}

.chip {
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: 12px;
  line-height: 1.5;
}

.chip-selected {
  background: rgba(34, 197, 94, 0.15);
  color: #86efac;
}

.chip-skipped {
  background: rgba(245, 158, 11, 0.12);
  color: #fcd34d;
}
</style>
