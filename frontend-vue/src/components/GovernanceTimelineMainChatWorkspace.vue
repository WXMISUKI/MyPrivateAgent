<template>
  <div
    v-if="activeFilter === 'main_chat' || currentQueryDetail"
    class="main-chat-query-workspace"
  >
    <div class="main-chat-query-workspace-head">
      <div>
        <h3>Main Chat Query Workspace</h3>
        <p class="muted">把 query history、query detail 与阶段聚焦放在同一工作区，减少在治理视图里来回跳转。</p>
      </div>
    </div>

    <div class="main-chat-query-workspace-grid">
      <MainChatQueryHistoryPanel
        v-if="activeFilter === 'main_chat'"
        :history="mainChatQueryHistory"
        :loading="mainChatQueryHistoryLoading"
        :error="mainChatQueryHistoryError"
        :search="mainChatHistorySearch"
        :status-text="mainChatHistoryStatusText"
        :context-label="mainChatHistoryContextLabel"
        :active-query-id="activeQueryId"
        :active-stage="activeQueryStage"
        :filtered-items="filteredMainChatQueryHistoryItems"
        :is-stage-focused="isHistoryStageFocused"
        :format-stage-tags="formatHistoryStageTags"
        :format-snapshot-time="formatSnapshotTime"
        @update:search="$emit('update:search', $event)"
        @clear-search="$emit('clear-search')"
        @refresh="$emit('refresh')"
        @retry="$emit('retry')"
        @select-query="$emit('select-query', $event)"
        @select-stage="$emit('select-stage', $event)"
        @clear-query="$emit('clear-query')"
        @clear-stage="$emit('clear-stage')"
        @load-more="$emit('load-more')"
      />

      <MainChatQueryDetailPanel
        v-if="currentQueryDetail"
        :detail="currentQueryDetail"
        :active-stage="activeQueryStage"
        @focus-stage="$emit('focus-stage', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import MainChatQueryHistoryPanel from './MainChatQueryHistoryPanel.vue'
import MainChatQueryDetailPanel from './MainChatQueryDetailPanel.vue'

defineProps({
  activeFilter: {
    type: String,
    default: '',
  },
  currentQueryDetail: {
    type: Object,
    default: null,
  },
  mainChatQueryHistory: {
    type: Object,
    required: true,
  },
  mainChatQueryHistoryLoading: {
    type: Boolean,
    default: false,
  },
  mainChatQueryHistoryError: {
    type: String,
    default: '',
  },
  mainChatHistorySearch: {
    type: String,
    default: '',
  },
  mainChatHistoryStatusText: {
    type: String,
    default: '',
  },
  mainChatHistoryContextLabel: {
    type: String,
    default: '',
  },
  activeQueryId: {
    type: String,
    default: '',
  },
  activeQueryStage: {
    type: String,
    default: '',
  },
  filteredMainChatQueryHistoryItems: {
    type: Array,
    default: () => [],
  },
  isHistoryStageFocused: {
    type: Function,
    required: true,
  },
  formatHistoryStageTags: {
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
  'focus-stage',
])
</script>

