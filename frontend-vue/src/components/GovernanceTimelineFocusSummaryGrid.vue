<template>
  <div class="summary-grid">
    <div class="summary-card">
      <span class="summary-label">当前计划</span>
      <strong
        class="plan-objective-label"
        :title="currentPlanObjectiveLabel"
        :aria-label="`当前计划 ${currentPlanObjectiveLabel}`"
      >
        {{ currentPlanObjectiveLabel }}
      </strong>
    </div>
    <div class="summary-card">
      <span class="summary-label">聚焦步骤</span>
      <strong
        class="focus-step-label"
        :title="focusItemTitleLabel"
        :aria-label="`聚焦步骤 ${focusItemTitleLabel}`"
      >
        {{ focusItemTitleLabel }}
      </strong>
    </div>
    <div class="summary-card">
      <span class="summary-label">审计事件</span>
      <strong
        class="audit-count-label"
        :title="String(auditCount)"
        :aria-label="`审计事件 ${auditCount}`"
      >
        {{ auditCount }}
      </strong>
    </div>
    <div class="summary-card">
      <span class="summary-label">运行 Trace</span>
      <strong
        class="trace-count-label"
        :title="String(traceCount)"
        :aria-label="`运行 Trace ${traceCount}`"
      >
        {{ traceCount }}
      </strong>
    </div>
    <div v-if="currentRunOverview" class="summary-card">
      <span class="summary-label">当前执行实例</span>
      <strong>{{ currentRunOverview.id }}</strong>
      <span class="muted">{{ currentRunOverview.summary }}</span>
      <span class="muted">{{ currentRunOverview.notice }}</span>
    </div>
    <div class="summary-card">
      <span class="summary-label">待处理审批</span>
      <strong>{{ approvalOverview.pendingLabel }}</strong>
      <span class="muted">{{ approvalOverview.primaryDetail }}</span>
      <span class="muted">{{ approvalOverview.secondaryDetail }}</span>
    </div>
    <div class="summary-card">
      <span class="summary-label">当前筛选</span>
      <strong
        class="filter-focus-label"
        :title="activeFilter"
        :aria-label="`当前筛选 ${activeFilterLabel}`"
      >
        {{ activeFilterLabel }}
      </strong>
    </div>
    <div class="summary-card">
      <span class="summary-label">风险模式</span>
      <strong
        class="severity-focus-label"
        :title="activeSeverity"
        :aria-label="`风险模式 ${activeSeverityLabel}`"
      >
        {{ activeSeverityLabel }}
      </strong>
    </div>
    <div v-if="activeFrameworkAdapterErrorTypeLabel" class="summary-card summary-card-dismissible">
      <span class="summary-label">错误类型</span>
      <strong
        class="framework-error-type-focus-label"
        :title="activeFrameworkAdapterErrorType"
        :aria-label="`错误类型 ${activeFrameworkAdapterErrorTypeLabel}`"
      >
        {{ activeFrameworkAdapterErrorTypeLabel }}
      </strong>
      <button
        type="button"
        class="payload-toggle-btn compact-dismiss-btn"
        :title="activeFrameworkAdapterErrorType"
        :aria-label="activeFrameworkAdapterErrorTypeClearLabel"
        @click="emit('clear-framework-adapter-error-type')"
      >
        清除错误类型
      </button>
    </div>
    <div v-if="activeDedupeKey" class="summary-card summary-card-dismissible">
      <span class="summary-label">幂等键聚焦</span>
      <strong
        class="dedupe-focus-preview"
        :title="activeDedupeKey"
        :aria-label="`幂等键聚焦 ${activeDedupeKey}`"
      >
        {{ activeDedupeKeyPreview }}
      </strong>
      <span
        class="muted dedupe-focus-match-count"
        :aria-label="activeDedupeKeyMatchAriaLabel"
      >
        {{ activeDedupeKeyMatchLabel }}
      </span>
      <button
        type="button"
        class="payload-toggle-btn compact-dismiss-btn"
        :title="activeDedupeKey"
        :aria-label="activeDedupeKeyCopyLabel"
        @click="emit('copy-active-dedupe-key')"
      >
        {{ copiedActiveDedupeKey ? '已复制当前幂等键' : '复制当前幂等键' }}
      </button>
      <button
        type="button"
        class="payload-toggle-btn compact-dismiss-btn"
        :title="activeDedupeKey"
        :aria-label="activeDedupeKeyClearLabel"
        @click="emit('clear-dedupe-key')"
      >
        清除幂等键
      </button>
    </div>
    <div v-if="activeQueryId" class="summary-card summary-card-dismissible">
      <span class="summary-label">Query 聚焦</span>
      <strong
        class="dedupe-focus-preview"
        :title="activeQueryId"
        :aria-label="`Query 聚焦 ${activeQueryId}`"
      >
        {{ activeQueryId }}
      </strong>
      <button
        type="button"
        class="payload-toggle-btn compact-dismiss-btn"
        :title="activeQueryId"
        :aria-label="`清除 Query ${activeQueryId}`"
        @click="emit('clear-query')"
      >
        清除 Query
      </button>
    </div>
    <div v-if="activeQueryStage" class="summary-card summary-card-dismissible">
      <span class="summary-label">阶段聚焦</span>
      <strong
        class="dedupe-focus-preview"
        :title="activeQueryStage"
        :aria-label="`阶段聚焦 ${activeQueryStage}`"
      >
        {{ activeQueryStage }}
      </strong>
      <button
        type="button"
        class="payload-toggle-btn compact-dismiss-btn"
        :title="activeQueryStage"
        :aria-label="`清除阶段 ${activeQueryStage}`"
        @click="emit('clear-stage')"
      >
        清除阶段
      </button>
    </div>
    <div v-if="currentQueryOverview" class="summary-card">
      <span class="summary-label">Query 摘要</span>
      <strong>{{ currentQueryOverview.latestStage || '-' }}</strong>
      <span class="muted">
        {{ `阶段 ${currentQueryOverview.stageCount} · 告警 ${currentQueryOverview.warningCount}` }}
      </span>
      <span class="muted">{{ currentQueryOverview.latestSnapshotId || currentQueryOverview.latestSummary || '无最近摘要' }}</span>
    </div>
    <div v-if="activeFilter === 'main_chat'" class="summary-card main-chat-history-summary-card">
      <span class="summary-label">Main Chat Query History</span>
      <strong>{{ mainChatQueryHistory.totalItems || 0 }}</strong>
      <span class="muted">
        {{ mainChatQueryHistory.recordingState === 'recorded' ? `page ${mainChatQueryHistory.page} · size ${mainChatQueryHistory.pageSize}` : (mainChatQueryHistory.reason || '暂无 history') }}
      </span>
    </div>
    <div class="summary-card">
      <span class="summary-label">治理快照</span>
      <strong>{{ currentSnapshotId }}</strong>
      <span class="muted">{{ currentSnapshotGeneratedAt ? formatSnapshotTime(currentSnapshotGeneratedAt) : '等待后端引用' }}</span>
    </div>
    <div class="summary-card">
      <span class="summary-label">快照聚焦</span>
      <strong>{{ activeSnapshotLabel }}</strong>
      <span class="muted">{{ activeSnapshotNotice }}</span>
    </div>
  </div>
</template>

<script setup>
defineOptions({
  name: 'GovernanceTimelineFocusSummaryGrid',
})

defineProps({
  currentPlanObjectiveLabel: {
    type: String,
    default: '-',
  },
  focusItemTitleLabel: {
    type: String,
    default: '-',
  },
  auditCount: {
    type: Number,
    default: 0,
  },
  traceCount: {
    type: Number,
    default: 0,
  },
  currentRunOverview: {
    type: Object,
    default: null,
  },
  approvalOverview: {
    type: Object,
    required: true,
  },
  activeFilter: {
    type: String,
    default: '',
  },
  activeFilterLabel: {
    type: String,
    default: '',
  },
  activeSeverity: {
    type: String,
    default: '',
  },
  activeSeverityLabel: {
    type: String,
    default: '',
  },
  activeFrameworkAdapterErrorType: {
    type: String,
    default: '',
  },
  activeFrameworkAdapterErrorTypeLabel: {
    type: String,
    default: '',
  },
  activeFrameworkAdapterErrorTypeClearLabel: {
    type: String,
    default: '',
  },
  activeDedupeKey: {
    type: String,
    default: '',
  },
  activeDedupeKeyPreview: {
    type: String,
    default: '',
  },
  activeDedupeKeyMatchLabel: {
    type: String,
    default: '',
  },
  activeDedupeKeyMatchAriaLabel: {
    type: String,
    default: '',
  },
  activeDedupeKeyCopyLabel: {
    type: String,
    default: '',
  },
  activeDedupeKeyClearLabel: {
    type: String,
    default: '',
  },
  copiedActiveDedupeKey: {
    type: Boolean,
    default: false,
  },
  activeQueryId: {
    type: String,
    default: '',
  },
  activeQueryStage: {
    type: String,
    default: '',
  },
  currentQueryOverview: {
    type: Object,
    default: null,
  },
  mainChatQueryHistory: {
    type: Object,
    required: true,
  },
  currentSnapshotId: {
    type: String,
    default: '',
  },
  currentSnapshotGeneratedAt: {
    type: String,
    default: '',
  },
  activeSnapshotLabel: {
    type: String,
    default: '',
  },
  activeSnapshotNotice: {
    type: String,
    default: '',
  },
  formatSnapshotTime: {
    type: Function,
    required: true,
  },
})

const emit = defineEmits([
  'clear-framework-adapter-error-type',
  'copy-active-dedupe-key',
  'clear-dedupe-key',
  'clear-query',
  'clear-stage',
])
</script>

<style scoped>
.summary-grid {
  display: grid;
  gap: var(--space-md);
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  margin-bottom: var(--space-lg);
}

.summary-card {
  border: 1px solid var(--border-color);
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.summary-card-dismissible {
  align-items: flex-start;
}

.summary-label {
  font-size: 0.8rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.muted {
  color: var(--text-tertiary);
  font-size: 0.875rem;
}

.compact-dismiss-btn {
  margin-top: 0.2rem;
}

.main-chat-history-summary-card {
  justify-content: center;
}
</style>
