<template>
  <div class="panel-card main-chat-history-panel">
    <div class="card-head main-chat-history-head">
      <div>
        <h3>Main Chat Query History</h3>
        <span class="muted">
          {{ statusText }}
        </span>
        <div v-if="contextLabel" class="main-chat-history-context">
          {{ contextLabel }}
        </div>
      </div>
      <div class="main-chat-history-toolbar">
        <input
          :value="search"
          type="text"
          class="main-chat-history-search-input"
          placeholder="筛选 query / stage / summary"
          @input="$emit('update:search', $event.target.value)"
        >
        <button
          v-if="search"
          type="button"
          class="payload-toggle-btn"
          @click="$emit('clear-search')"
        >
          清除搜索
        </button>
        <button
          type="button"
          class="secondary-btn"
          :disabled="loading"
          @click="$emit('refresh')"
        >
          {{ loading && !history.items.length ? '加载中...' : '刷新 History' }}
        </button>
      </div>
    </div>

    <div class="main-chat-history-metrics">
      <span class="history-metric-chip">已加载 {{ history.items.length }} / 总计 {{ history.totalItems || 0 }}</span>
      <span class="history-metric-chip">当前页 {{ history.page || 1 }}</span>
      <span class="history-metric-chip">layer {{ history.readModelLayer || '-' }}</span>
      <span class="history-metric-chip">source {{ history.sourceChannel || '-' }}</span>
      <span v-if="activeQueryId" class="history-metric-chip active">Query {{ activeQueryId }}</span>
      <span v-if="activeStage" class="history-metric-chip active">阶段 {{ activeStage }}</span>
      <button
        v-if="activeQueryId"
        type="button"
        class="payload-toggle-btn"
        @click="$emit('clear-query')"
      >
        清除 Query
      </button>
      <button
        v-if="activeStage"
        type="button"
        class="payload-toggle-btn"
        @click="$emit('clear-stage')"
      >
        清除阶段
      </button>
    </div>

    <div v-if="error" class="timeline-empty-state main-chat-history-state">
      <strong>Query history 加载失败</strong>
      <span>{{ error }}</span>
      <button
        type="button"
        class="payload-toggle-btn"
        @click="$emit('retry')"
      >
        重试
      </button>
    </div>

    <div
      v-else-if="loading && !history.items.length"
      class="timeline-empty-state main-chat-history-state"
    >
      <strong>正在加载 Query History</strong>
      <span>正在读取 main_chat 域下最近的 query 控制记录。</span>
    </div>

    <div
      v-else-if="!history.items.length"
      class="timeline-empty-state main-chat-history-state"
    >
      <strong>暂无 Query History</strong>
      <span>{{ history.reason || '当前 main_chat 域还没有可浏览的 query history。' }}</span>
    </div>

    <div
      v-else-if="search && !filteredItems.length"
      class="timeline-empty-state main-chat-history-state"
    >
      <strong>当前筛选没有匹配到 Query History</strong>
      <span>{{ `筛选词：${search}` }}</span>
    </div>

    <template v-else>
      <ul class="main-chat-history-list">
        <li
          v-for="query in filteredItems"
          :key="`${query.queryId}-${query.latestTimestamp}`"
          class="main-chat-history-item"
          :class="{
            active: activeQueryId === query.queryId,
            'stage-focused': isStageFocused(query),
          }"
        >
          <button
            type="button"
            class="main-chat-history-entry"
            :aria-pressed="activeQueryId === query.queryId ? 'true' : 'false'"
            @click="$emit('select-query', query.queryId)"
          >
            <div class="main-chat-history-entry-head">
              <code>{{ query.queryId }}</code>
              <span class="main-chat-history-stage">{{ query.latestStage || '-' }}</span>
            </div>
            <span class="main-chat-history-summary">{{ query.latestSummary || '无摘要' }}</span>
            <span class="muted main-chat-history-meta">
              {{ query.latestSnapshotId || formatSnapshotTime(query.latestTimestamp) || '无最近快照' }}
            </span>
          </button>
          <div class="main-chat-history-stage-tags">
            <button
              v-for="tag in formatStageTags(query)"
              :key="`${query.queryId}-${tag.key}`"
              type="button"
              class="main-chat-history-stage-tag"
              :class="{ active: tag.active }"
              @click="$emit('select-stage', { queryId: query.queryId, stage: tag.key })"
            >
              {{ tag.label }}
            </button>
          </div>
        </li>
      </ul>
      <div class="main-chat-history-actions">
        <button
          type="button"
          class="secondary-btn history-load-more-btn"
          :disabled="loading || !history.hasMore"
          @click="$emit('load-more')"
        >
          {{ loading ? '加载中...' : (history.hasMore ? '加载更多' : '已加载完成') }}
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
defineProps({
  history: {
    type: Object,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: '',
  },
  search: {
    type: String,
    default: '',
  },
  statusText: {
    type: String,
    default: '',
  },
  contextLabel: {
    type: String,
    default: '',
  },
  activeQueryId: {
    type: String,
    default: '',
  },
  activeStage: {
    type: String,
    default: '',
  },
  filteredItems: {
    type: Array,
    default: () => [],
  },
  isStageFocused: {
    type: Function,
    required: true,
  },
  formatStageTags: {
    type: Function,
    required: true,
  },
  formatSnapshotTime: {
    type: Function,
    required: true,
  },
})

defineEmits([
  'update:search',
  'clear-search',
  'refresh',
  'retry',
  'select-query',
  'select-stage',
  'clear-query',
  'clear-stage',
  'load-more',
])
</script>

<style scoped>
.main-chat-history-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.main-chat-history-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-md);
}

.main-chat-history-toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.main-chat-history-search-input {
  min-width: 240px;
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.main-chat-history-context {
  margin-top: 6px;
  color: var(--text-secondary);
  font-size: 0.78rem;
}

.main-chat-history-metrics {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.history-metric-chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border: 1px solid var(--border-color);
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.08);
  color: var(--text-secondary);
  font-size: 0.76rem;
}

.history-metric-chip.active {
  border-color: var(--border-primary);
  background: rgba(15, 118, 110, 0.12);
  color: var(--text-primary);
}

.main-chat-history-state {
  margin-top: 0;
}

.main-chat-history-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin: 0;
  padding: 0;
}

.main-chat-history-item {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
}

.main-chat-history-item.active {
  border-color: var(--border-primary);
  background: rgba(15, 118, 110, 0.08);
}

.main-chat-history-item.stage-focused {
  box-shadow: inset 0 0 0 1px rgba(15, 118, 110, 0.2);
}

.main-chat-history-entry {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  padding: var(--space-md);
  border: 0;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.main-chat-history-entry-head {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-sm);
}

.main-chat-history-stage {
  flex-shrink: 0;
  font-size: 0.76rem;
  padding: 2px 8px;
  border: 1px solid var(--border-color);
  border-radius: 999px;
  color: var(--text-secondary);
}

.main-chat-history-summary {
  color: var(--text-primary);
  line-height: 1.5;
}

.main-chat-history-meta {
  word-break: break-all;
}

.main-chat-history-stage-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 0 var(--space-md) var(--space-md);
}

.main-chat-history-stage-tag {
  font-size: 0.72rem;
  padding: 2px 8px;
  border: 1px solid var(--border-color);
  border-radius: 999px;
  color: var(--text-tertiary);
  background: rgba(148, 163, 184, 0.08);
  cursor: pointer;
}

.main-chat-history-stage-tag.active {
  border-color: var(--border-primary);
  color: var(--text-primary);
  background: rgba(15, 118, 110, 0.12);
}

.main-chat-history-actions {
  display: flex;
  justify-content: flex-end;
}
</style>
