<template>
  <section class="settings-section governance-timeline-panel">
    <div class="section-head">
      <div>
        <h2>治理时间线</h2>
        <p class="section-desc">聚合当前会话的 doctor、scheduler、permission 等治理事件，便于快速复盘最近一次框架动作。</p>
      </div>
      <div class="section-actions">
        <button class="secondary-btn" :disabled="!currentSnapshotRef" @click="copyCurrentSnapshotCommand">
          {{ copiedCommandTarget === 'view' ? '已复制命令' : '复制快照命令' }}
        </button>
        <button class="secondary-btn" :disabled="!currentConversationId" @click="copyCurrentView">
          {{ copiedViewLink ? '已复制视图' : '复制当前视图' }}
        </button>
        <button class="secondary-btn" :disabled="loading || !currentConversationId" @click="loadTimeline">
          {{ loading ? '刷新中...' : '刷新时间线' }}
        </button>
      </div>
    </div>

    <p v-if="error" class="inline-error">{{ error }}</p>
    <p v-else-if="!currentConversationId" class="empty-hint">当前没有可追踪的持久化会话，治理时间线将在会话落库后可见。</p>
    <p v-else-if="!currentPlan" class="empty-hint">当前会话尚未建立计划上下文，暂时没有可展示的治理时间线。</p>

    <template v-else-if="focusItem">
      <GovernanceTimelineFocusSummaryGrid
        :current-plan-objective-label="currentPlanObjectiveLabel"
        :focus-item-title-label="focusItemTitleLabel"
        :audit-count="auditCount"
        :trace-count="traceCount"
        :current-run-overview="currentRunOverview"
        :approval-overview="approvalOverview"
        :active-filter="activeFilter"
        :active-filter-label="activeFilterLabel"
        :active-severity="activeSeverity"
        :active-severity-label="activeSeverityLabel"
        :active-framework-adapter-error-type="activeFrameworkAdapterErrorType"
        :active-framework-adapter-error-type-label="activeFrameworkAdapterErrorTypeLabel"
        :active-framework-adapter-error-type-clear-label="activeFrameworkAdapterErrorTypeClearLabel"
        :active-dedupe-key="activeDedupeKey"
        :active-dedupe-key-preview="activeDedupeKeyPreview"
        :active-dedupe-key-match-label="activeDedupeKeyMatchLabel"
        :active-dedupe-key-match-aria-label="activeDedupeKeyMatchAriaLabel"
        :active-dedupe-key-copy-label="activeDedupeKeyCopyLabel"
        :active-dedupe-key-clear-label="activeDedupeKeyClearLabel"
        :copied-active-dedupe-key="copiedActiveDedupeKey"
        :active-query-id="activeQueryId"
        :active-query-stage="activeQueryStage"
        :current-query-overview="currentQueryOverview"
        :main-chat-query-history="mainChatQueryHistory"
        :current-snapshot-id="currentSnapshotId"
        :current-snapshot-generated-at="currentSnapshotGeneratedAt"
        :active-snapshot-label="activeSnapshotLabel"
        :active-snapshot-notice="activeSnapshotNotice"
        :format-snapshot-time="formatSnapshotTime"
        @clear-framework-adapter-error-type="clearFrameworkAdapterErrorTypeFilter"
        @copy-active-dedupe-key="copyActiveDedupeKey"
        @clear-dedupe-key="clearDedupeKeyFilter"
        @clear-query="clearQueryIdFilter"
        @clear-stage="clearQueryStageFilter"
      />

      <GovernanceTimelineMainChatWorkspace
        :active-filter="activeFilter"
        :current-query-detail="currentQueryDetail"
        :main-chat-query-history="mainChatQueryHistory"
        :main-chat-query-history-loading="mainChatQueryHistoryLoading"
        :main-chat-query-history-error="mainChatQueryHistoryError"
        :main-chat-history-search="mainChatHistorySearch"
        :main-chat-history-status-text="mainChatHistoryStatusText"
        :main-chat-history-context-label="mainChatHistoryContextLabel"
        :active-query-id="activeQueryId"
        :active-query-stage="activeQueryStage"
        :filtered-main-chat-query-history-items="filteredMainChatQueryHistoryItems"
        :is-history-stage-focused="isHistoryStageFocused"
        :format-history-stage-tags="formatHistoryStageTags"
        :format-snapshot-time="formatSnapshotTime"
        @update:search="mainChatHistorySearch = $event"
        @clear-search="mainChatHistorySearch = ''"
        @refresh="loadMainChatQueryHistory()"
        @retry="loadMainChatQueryHistory()"
        @select-query="activeQueryId = $event"
        @select-stage="focusHistoryQueryStage($event.queryId, $event.stage)"
        @clear-query="clearQueryIdFilter"
        @clear-stage="clearQueryStageFilter"
        @load-more="loadMoreMainChatQueryHistory"
        @focus-stage="focusQueryStage"
      />

      <GovernanceTimelineOverviewCards
        :cards="governanceOverviewCards"
        :active-filter="activeFilter"
        :active-severity="activeSeverity"
        :format-severity-badge="formatSeverityBadge"
        :format-audit-time="formatAuditTime"
        @select-card="applyFilter"
        @focus-warning="applyWarningFocus"
      />

      <div v-if="autoFocusNotice" class="governance-focus-notice">
        <strong>自动聚焦</strong>
        <span>{{ autoFocusNotice }}</span>
      </div>

      <GovernanceRecentSnapshotCommandsCard
        :items="recentSnapshotCommands"
        :copied-command-text="recentCopiedCommandText"
        :copied-command-display="recentCopiedCommandDisplay"
        @copy-command="copyRecentSnapshotCommand"
      />

      <GovernanceTimelineSummaryActionCards
        :active-filter="activeFilter"
        :last-doctor-outcome="lastDoctorOutcome"
        :last-permission-outcome="lastPermissionOutcome"
        :last-mcp-outcome="lastMcpOutcome"
        :last-governance-outcome="lastGovernanceOutcome"
        :last-scheduler-outcome="lastSchedulerOutcome"
        :last-hook-outcome="lastHookOutcome"
        :last-learning-outcome="lastLearningOutcome"
        :last-runtime-outcome="lastRuntimeOutcome"
        :format-audit-time="formatAuditTime"
        @filter="applyFilter"
      />

      <GovernanceTimelineFrameworkAdapterCards
        :copied-command-target="copiedCommandTarget"
        :last-framework-adapter-pilot-outcome="lastFrameworkAdapterPilotOutcome"
        :last-framework-adapter-precheck-outcome="lastFrameworkAdapterPrecheckOutcome"
        :last-framework-adapter-external-pilot-outcome="lastFrameworkAdapterExternalPilotOutcome"
        :last-framework-adapter-external-failure-diagnostic="lastFrameworkAdapterExternalFailureDiagnostic"
        :format-audit-time="formatAuditTime"
        :format-framework-adapter-summary-heading="formatFrameworkAdapterSummaryHeading"
        :format-framework-adapter-identity-line="formatFrameworkAdapterIdentityLine"
        :format-framework-adapter-failure-count="formatFrameworkAdapterFailureCount"
        :format-framework-adapter-failure-distribution="formatFrameworkAdapterFailureDistribution"
        :format-framework-adapter-failure-window="formatFrameworkAdapterFailureWindow"
        :format-framework-adapter-failure-sample-size="formatFrameworkAdapterFailureSampleSize"
        :is-summary-outcome-active="isSummaryOutcomeActive"
        @focus-entry="focusTimelineEntry"
        @open-runtime-surface="openRuntimeSurfacePanel"
        @copy-snapshot-command="copySnapshotCommand"
      />

      <GovernanceTimelineFrameworkAdapterRemediationCard
        :remediation="lastFrameworkAdapterRemediation"
        :active-filter="activeFilter"
        :copied-command-target="copiedCommandTarget"
        :format-audit-time="formatAuditTime"
        :format-framework-adapter-remediation-heading="formatFrameworkAdapterRemediationHeading"
        :format-framework-adapter-remediation-identity-line="formatFrameworkAdapterRemediationIdentityLine"
        :format-framework-adapter-remediation-action="formatFrameworkAdapterRemediationAction"
        @focus="applyFilter"
        @open-runtime-surface="openRuntimeSurfacePanel"
        @copy-command="copyFrameworkAdapterRemediationCommand"
      />

      <GovernanceTimelineEventStream
        :filtered-timeline="filteredTimeline"
        :scoped-timeline="scopedTimeline"
        :active-filter="activeFilter"
        :active-severity="activeSeverity"
        :active-dedupe-key="activeDedupeKey"
        :active-dedupe-key-empty-clear-label="activeDedupeKeyEmptyClearLabel"
        :copied-snapshot-key="copiedSnapshotKey"
        :copied-command-target="copiedCommandTarget"
        :copied-payload-key="copiedPayloadKey"
        :copied-dedupe-key="copiedDedupeKey"
        :active-query-id="activeQueryId"
        :severity-filters="severityFilters"
        :timeline-filters="timelineFilters"
        :format-audit-time="formatAuditTime"
        :format-payload-json="formatPayloadJson"
        :entry-snapshot-ref="entrySnapshotRef"
        :is-snapshot-highlighted="isSnapshotHighlighted"
        :has-payload="hasPayload"
        :is-payload-expanded="isPayloadExpanded"
        :get-timeline-dedupe-key="getTimelineDedupeKey"
        :get-timeline-query-id="getTimelineQueryId"
        @update:active-filter="activeFilter = $event"
        @update:active-severity="activeSeverity = $event"
        @toggle-payload="togglePayload($event.key)"
        @copy-snapshot-ref="copySnapshotRef"
        @copy-snapshot-command="copySnapshotCommand"
        @copy-payload="copyPayload"
        @copy-dedupe-key="copyDedupeKey"
        @focus-dedupe-key="focusDedupeKey"
        @focus-query-id="focusQueryId"
        @clear-dedupe-key="clearDedupeKeyFilter"
      />
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useConversationStore } from '../stores/conversation'
import { usePlannerStore } from '../stores/planner'
import { runtimeSurfaceApi } from '../api'
import { buildSnapshotCommandDescriptor } from '../services/governanceSnapshotCommands'
import {
  entrySnapshotRef,
  formatPayloadJson,
  getTimelineDedupeKey,
  getTimelineQueryId,
  hasPayload,
  normalizePayload,
  normalizeSnapshotRef,
  normalizeText,
  toTimestamp,
} from '../services/governanceValueUtils'
import {
  buildCurrentQueryDetail,
  buildCurrentQueryOverview,
  buildHistoryStageTags,
  buildMainChatHistoryContextLabel,
  buildMainChatHistoryStatus,
  buildMainChatQueryDetailContract,
  buildMainChatQueryHistoryContract,
  filterMainChatHistoryItems,
  isHistoryStageFocused as checkHistoryStageFocused,
  inferSnapshotCommandDomain,
} from '../services/governanceViewInterpretation'
import {
  getLatestGovernanceTimestamp,
  pickGovernanceFocusItem,
} from '../services/governanceTimelinePlanFocus'
import {
  buildApprovalOverview,
  buildCurrentRunOverview,
} from '../services/governanceTimelineSummary'
import {
  formatAuditTime,
  formatSeverityBadge,
  formatSnapshotTime,
  getSeverityRank,
  truncateMiddle,
} from '../services/governanceTimelineDisplay'
import {
  buildActiveSnapshotNotice,
  buildCombinedTimeline,
  buildCurrentSnapshotRef,
  buildDedupeCandidateTimeline,
  buildGovernanceTimelineOutcomes,
  buildGovernanceOverviewCards,
  buildRecommendedFocusFilter,
  buildRecommendedFocusSignature,
  buildSeverityFilters,
  buildTimelineFilters,
  buildAutoFocusNotice,
  filterTimelineEntries,
  scopeTimelineBySeverity,
} from '../services/governanceTimelineView'
import {
  buildCurrentGovernanceViewSnapshot,
} from '../services/governanceTimelineSnapshotView'
import { writeTextToClipboard } from '../services/governanceClipboard'
import {
  formatAuditEvent,
  formatPayloadSummary,
  formatTimelineDomain,
  formatTraceSource,
  inferTimelineDomain,
  normalizeSeverity,
  stringifyPayloadValue,
} from '../services/governanceFormatting'
import {
  buildFrameworkAdapterRemediationCommand,
  buildFrameworkAdapterRemediationStatusTags,
  formatFrameworkAdapterDisplayName,
  formatFrameworkAdapterExternalErrorDetail,
  formatFrameworkAdapterExternalErrorLabel,
  formatFrameworkAdapterExternalErrorTag,
  formatFrameworkAdapterFailureCount,
  formatFrameworkAdapterFailureDistribution,
  formatFrameworkAdapterFailureSampleSize,
  formatFrameworkAdapterFailureWindow,
  formatFrameworkAdapterIdentityLine,
  formatFrameworkAdapterRemediationAction,
  formatFrameworkAdapterRemediationContent,
  formatFrameworkAdapterRemediationHeading,
  formatFrameworkAdapterRemediationIdentityLine,
  formatFrameworkAdapterSummaryHeading,
  getFrameworkAdapterExternalErrorType,
} from '../services/frameworkAdapterGovernance'
import GovernanceRecentSnapshotCommandsCard from './GovernanceRecentSnapshotCommandsCard.vue'
import GovernanceTimelineFocusSummaryGrid from './GovernanceTimelineFocusSummaryGrid.vue'
import GovernanceTimelineMainChatWorkspace from './GovernanceTimelineMainChatWorkspace.vue'
import GovernanceTimelineOverviewCards from './GovernanceTimelineOverviewCards.vue'
import GovernanceTimelineFrameworkAdapterRemediationCard from './GovernanceTimelineFrameworkAdapterRemediationCard.vue'
import GovernanceTimelineSummaryActionCards from './GovernanceTimelineSummaryActionCards.vue'
import GovernanceTimelineFrameworkAdapterCards from './GovernanceTimelineFrameworkAdapterCards.vue'
import GovernanceTimelineEventStream from './GovernanceTimelineEventStream.vue'
import { useRecentSnapshotCommands } from '../composables/useRecentSnapshotCommands'
import { useGovernanceTimelineState } from '../composables/useGovernanceTimelineState'
import { useGovernanceTimelineClipboard } from '../composables/useGovernanceTimelineClipboard'

const router = useRouter()
const route = useRoute()
const conversationStore = useConversationStore()
const plannerStore = usePlannerStore()
const {
  recentSnapshotCommands,
  copiedCommandText: recentCopiedCommandText,
  copiedCommandDisplay: recentCopiedCommandDisplay,
  refreshRecentSnapshotCommands,
  recordRecentSnapshotCommand,
  copyRecentSnapshotCommand,
} = useRecentSnapshotCommands()
const loading = ref(false)
const error = ref('')
const activeFilter = ref('all')
const activeSeverity = ref('all')
const activeSnapshotId = ref('')
const activeFrameworkAdapterErrorType = ref('')
const activeDedupeKey = ref('')
const activeQueryId = ref('')
const activeQueryStage = ref('')
const expandedPayloadKeys = ref({})
const copiedPayloadKey = ref('')
const copiedDedupeKey = ref('')
const copiedActiveDedupeKey = ref(false)
const copiedSnapshotKey = ref('')
const copiedCommandTarget = ref('')
const copiedViewLink = ref(false)
const lastAutoFocusSignature = ref('')
const queryDetailContract = ref(null)
const mainChatQueryHistory = ref(buildMainChatQueryHistoryContract())
const mainChatQueryHistoryLoading = ref(false)
const mainChatQueryHistoryError = ref('')
const mainChatHistorySearch = ref('')
const activeMainChatHistoryPage = ref(1)

const currentConversationId = computed(() => {
  const id = Number(conversationStore.currentConversation?.id)
  return Number.isFinite(id) ? id : null
})

const currentPlan = computed(() => plannerStore.currentPlan)

const currentPlanObjectiveLabel = computed(() => currentPlan.value?.objective || '-')

const focusItem = computed(() => pickGovernanceFocusItem(currentPlan.value, {
  getLatestGovernanceTimestamp: item => getLatestGovernanceTimestamp(item, {
    inferTimelineDomain,
    normalizePayload,
    toTimestamp,
  }),
}))

const focusItemTitleLabel = computed(() => focusItem.value?.title || '-')

const auditCount = computed(() => (focusItem.value?.audit_trail || []).length)
const traceCount = computed(() => (focusItem.value?.run_trace || []).length)
const mainChatHistoryStatusText = computed(() => buildMainChatHistoryStatus(
  mainChatQueryHistory.value,
  mainChatQueryHistoryLoading.value,
  mainChatQueryHistoryError.value
))
const filteredMainChatQueryHistoryItems = computed(() => filterMainChatHistoryItems(
  mainChatQueryHistory.value.items,
  mainChatHistorySearch.value
))
const mainChatHistoryContextLabel = computed(() => buildMainChatHistoryContextLabel(
  activeQueryId.value,
  activeQueryStage.value
))
const currentRunOverview = computed(() => buildCurrentRunOverview(focusItem.value?.scheduler_run, {
  traceCount: traceCount.value,
  normalizeText,
}))

const approvalOverview = computed(() => buildApprovalOverview(focusItem.value?.approval_requests, {
  currentRunOverview: currentRunOverview.value,
  normalizeText,
  toTimestamp,
}))

const combinedTimeline = computed(() => buildCombinedTimeline(focusItem.value, {
  normalizePayload,
  inferTimelineDomain,
  formatTimelineDomain,
  normalizeSeverity,
  formatAuditEvent,
  formatPayloadSummary,
  formatTraceSource,
  formatFrameworkAdapterExternalErrorTag,
  formatFrameworkAdapterExternalErrorDetail,
  normalizeSnapshotRef,
  toTimestamp,
  normalizeText,
}))

const severityFilters = computed(() => buildSeverityFilters(combinedTimeline.value))

const scopedTimeline = computed(() => scopeTimelineBySeverity(combinedTimeline.value, activeSeverity.value))

const timelineFilters = computed(() => buildTimelineFilters(scopedTimeline.value, formatTimelineDomain))

const dedupeCandidateTimeline = computed(() => buildDedupeCandidateTimeline(scopedTimeline.value, {
  activeFilter: activeFilter.value,
  activeQueryId: activeQueryId.value,
  activeQueryStage: activeQueryStage.value,
  activeFrameworkAdapterErrorType: activeFrameworkAdapterErrorType.value,
  getTimelineQueryId,
  getFrameworkAdapterExternalErrorType,
}))

const filteredTimeline = computed(() => filterTimelineEntries(scopedTimeline.value, {
  activeFilter: activeFilter.value,
  activeQueryId: activeQueryId.value,
  activeQueryStage: activeQueryStage.value,
  activeFrameworkAdapterErrorType: activeFrameworkAdapterErrorType.value,
  activeDedupeKey: activeDedupeKey.value,
  activeSnapshotId: activeSnapshotId.value,
  getTimelineQueryId,
  getTimelineDedupeKey,
  entrySnapshotRef,
  getFrameworkAdapterExternalErrorType,
}))

const activeFilterLabel = computed(() => {
  const matched = timelineFilters.value.find(item => item.key === activeFilter.value)
  return matched?.label || '全部'
})

const activeSeverityLabel = computed(() => {
  const matched = severityFilters.value.find(item => item.key === activeSeverity.value)
  return matched?.label || '全部事件'
})

const activeFrameworkAdapterErrorTypeLabel = computed(() => {
  if (!activeFrameworkAdapterErrorType.value) {
    return ''
  }
  const label = formatFrameworkAdapterExternalErrorLabel(activeFrameworkAdapterErrorType.value)
  if (!label) {
    return ''
  }
  return label === activeFrameworkAdapterErrorType.value
    ? label
    : `${label} (${activeFrameworkAdapterErrorType.value})`
})

const activeFrameworkAdapterErrorTypeClearLabel = computed(() => {
  if (!activeFrameworkAdapterErrorTypeLabel.value) {
    return ''
  }
  return `清除错误类型 ${activeFrameworkAdapterErrorTypeLabel.value}`
})

const activeDedupeKeyPreview = computed(() => truncateMiddle(activeDedupeKey.value, 88))

const activeDedupeKeyCopyLabel = computed(() => {
  const prefix = copiedActiveDedupeKey.value ? '已复制当前幂等键' : '复制当前幂等键'
  return `${prefix} ${activeDedupeKey.value}`
})

const activeDedupeKeyClearLabel = computed(() => `清除幂等键 ${activeDedupeKey.value}`)

const activeDedupeKeyEmptyClearLabel = computed(() => `清除幂等键聚焦 ${activeDedupeKey.value}`)

const activeDedupeKeyMatchLabel = computed(() => {
  if (!activeDedupeKey.value) {
    return ''
  }
  return `匹配事件 ${filteredTimeline.value.length} / ${dedupeCandidateTimeline.value.length}`
})

const activeDedupeKeyMatchAriaLabel = computed(() => activeDedupeKeyMatchLabel.value
  ? `幂等键${activeDedupeKeyMatchLabel.value}`
  : ''
)

const activeQueryEntries = computed(() => {
  if (!activeQueryId.value) {
    return []
  }
  return dedupeCandidateTimeline.value.filter(entry => getTimelineQueryId(entry) === activeQueryId.value)
})

const currentQueryOverview = computed(() => {
  return buildCurrentQueryOverview(
    queryDetailContract.value,
    activeQueryId.value,
    activeQueryEntries.value,
    entrySnapshotRef
  )
})

const currentQueryDetail = computed(() => {
  return buildCurrentQueryDetail(
    queryDetailContract.value,
    activeQueryId.value,
    activeQueryEntries.value,
    {
      entrySnapshotRef,
      getTimelineDedupeKey,
      toTimestamp,
    }
  )
})

const currentSnapshotRef = computed(() => buildCurrentSnapshotRef(
  filteredTimeline.value,
  scopedTimeline.value,
  combinedTimeline.value,
  entrySnapshotRef
))

const currentSnapshotId = computed(() => currentSnapshotRef.value?.snapshot_id || '本地待生成')
const currentSnapshotGeneratedAt = computed(() => currentSnapshotRef.value?.generated_at || '')
const activeSnapshotLabel = computed(() => activeSnapshotId.value || '未指定')
const activeSnapshotNotice = computed(() => buildActiveSnapshotNotice(
  activeSnapshotId.value,
  combinedTimeline.value,
  entrySnapshotRef
))

const governanceOverviewCards = computed(() => buildGovernanceOverviewCards(
  combinedTimeline.value,
  timelineFilters.value,
  {
    formatTimelineDomain,
    toTimestamp,
    getSeverityRank,
  }
))

const recommendedFocusFilter = computed(() => buildRecommendedFocusFilter(
  lastDoctorOutcome.value,
  formatAuditEvent('doctor_gate_failed'),
  governanceOverviewCards.value
))

const recommendedFocusSignature = computed(() => buildRecommendedFocusSignature(
  focusItem.value,
  recommendedFocusFilter.value,
  lastDoctorOutcome.value
))

const autoFocusNotice = computed(() => buildAutoFocusNotice({
  recommendedFocusSignature: recommendedFocusSignature.value,
  routeGovernanceFilter: route.query.governance_filter,
  lastAutoFocusSignature: lastAutoFocusSignature.value,
  activeFilter: activeFilter.value,
  recommendedFocusFilter: recommendedFocusFilter.value,
  governanceOverviewCards: governanceOverviewCards.value,
}))

const governanceTimelineOutcomes = computed(() => buildGovernanceTimelineOutcomes(combinedTimeline.value, {
  formatAuditEvent,
  normalizeText,
  formatFrameworkAdapterDisplayName,
  buildFrameworkAdapterRemediationStatusTags,
  formatFrameworkAdapterRemediationContent,
  buildFrameworkAdapterRemediationCommand,
}))

const lastDoctorOutcome = computed(() => governanceTimelineOutcomes.value.lastDoctorOutcome)
const lastPermissionOutcome = computed(() => governanceTimelineOutcomes.value.lastPermissionOutcome)
const lastMcpOutcome = computed(() => governanceTimelineOutcomes.value.lastMcpOutcome)
const lastGovernanceOutcome = computed(() => governanceTimelineOutcomes.value.lastGovernanceOutcome)
const lastSchedulerOutcome = computed(() => governanceTimelineOutcomes.value.lastSchedulerOutcome)
const lastHookOutcome = computed(() => governanceTimelineOutcomes.value.lastHookOutcome)
const lastLearningOutcome = computed(() => governanceTimelineOutcomes.value.lastLearningOutcome)
const lastRuntimeOutcome = computed(() => governanceTimelineOutcomes.value.lastRuntimeOutcome)
const lastFrameworkAdapterPilotOutcome = computed(() => governanceTimelineOutcomes.value.lastFrameworkAdapterPilotOutcome)
const lastFrameworkAdapterPrecheckOutcome = computed(() => governanceTimelineOutcomes.value.lastFrameworkAdapterPrecheckOutcome)
const lastFrameworkAdapterExternalPilotOutcome = computed(() => governanceTimelineOutcomes.value.lastFrameworkAdapterExternalPilotOutcome)
const lastFrameworkAdapterExternalFailureDiagnostic = computed(() => governanceTimelineOutcomes.value.lastFrameworkAdapterExternalFailureDiagnostic)
const lastFrameworkAdapterRemediation = computed(() => governanceTimelineOutcomes.value.lastFrameworkAdapterRemediation)

const {
  copyFrameworkAdapterRemediationCommand,
  copyPayload,
  copyDedupeKey,
  copyActiveDedupeKey,
  copySnapshotRef,
  copySnapshotCommand,
  copyCurrentSnapshotCommand,
  copyCurrentView,
  openRuntimeSurfacePanel,
  resetCopiedActiveDedupeKey,
} = useGovernanceTimelineClipboard({
  error,
  copiedPayloadKey,
  copiedDedupeKey,
  copiedActiveDedupeKey,
  copiedSnapshotKey,
  copiedCommandTarget,
  copiedViewLink,
  recentCopiedCommandText,
  hasPayload,
  formatPayloadJson,
  entrySnapshotRef,
  buildSnapshotCommandDescriptor,
  persistRecentSnapshotCommand: recordRecentSnapshotCommand,
  inferSnapshotCommandDomain: (snapshotRef, fallbackDomain) => inferSnapshotCommandDomain(snapshotRef, fallbackDomain, inferTimelineDomain),
  buildCurrentViewSnapshot: () => buildCurrentGovernanceViewSnapshot({
    locationHref: globalThis.location?.href || 'http://localhost/',
    routeQuery: route.query || {},
    currentSnapshotRef: currentSnapshotRef.value,
    activeFilter: activeFilter.value,
    activeSeverity: activeSeverity.value,
    activeFilterLabel: activeFilterLabel.value,
    activeSeverityLabel: activeSeverityLabel.value,
    filteredTimeline: filteredTimeline.value,
    scopedTimeline: scopedTimeline.value,
    activeFrameworkAdapterErrorType: activeFrameworkAdapterErrorType.value,
    activeFrameworkAdapterErrorTypeLabel: activeFrameworkAdapterErrorTypeLabel.value,
    activeDedupeKey: activeDedupeKey.value,
    activeDedupeKeyMatchLabel: activeDedupeKeyMatchLabel.value,
    activeQueryId: activeQueryId.value,
    currentQueryOverview: currentQueryOverview.value,
    activeQueryStage: activeQueryStage.value,
    activeQuerySearch: mainChatHistorySearch.value,
    activeQueryHistoryPage: activeMainChatHistoryPage.value,
    autoFocusNotice: autoFocusNotice.value,
    activeSnapshotId: activeSnapshotId.value,
  }),
  openRuntimeSurface: () => router.push('/settings?tab=advanced'),
  getActiveDedupeKey: () => activeDedupeKey.value,
  getCurrentSnapshotRef: () => currentSnapshotRef.value,
  getActiveFilter: () => activeFilter.value,
  writeTextToClipboard,
})

const {
  applyFilter,
  focusTimelineEntry,
  applyWarningFocus,
  clearFrameworkAdapterErrorTypeFilter,
  clearDedupeKeyFilter,
  clearQueryIdFilter,
  clearQueryStageFilter,
  focusDedupeKey,
  focusQueryId,
  focusQueryStage,
  focusHistoryQueryStage,
} = useGovernanceTimelineState({
  activeFilter,
  activeSeverity,
  activeSnapshotId,
  activeFrameworkAdapterErrorType,
  activeDedupeKey,
  activeQueryId,
  activeQueryStage,
  lastAutoFocusSignature,
  route,
  router,
  timelineFilters,
  severityFilters,
  combinedTimeline,
  governanceOverviewCards,
  recommendedFocusFilter,
  recommendedFocusSignature,
  entrySnapshotRef,
  getTimelineDedupeKey,
  getTimelineQueryId,
  normalizeText,
  onActiveDedupeKeyChanged: resetCopiedActiveDedupeKey,
})

async function loadTimeline() {
  if (!currentConversationId.value) return
  loading.value = true
  error.value = ''
  try {
    await plannerStore.loadPlans({ conversationId: currentConversationId.value })
    await loadMainChatQueryDetail()
    await loadMainChatQueryHistory()
  } catch (err) {
    error.value = err?.response?.data?.detail || err?.message || '加载治理时间线失败'
  } finally {
    loading.value = false
  }
}

async function loadMainChatQueryHistory(targetPage = activeMainChatHistoryPage.value, append = false) {
  if (!currentConversationId.value || activeFilter.value !== 'main_chat') {
    mainChatQueryHistory.value = buildMainChatQueryHistoryContract()
    mainChatQueryHistoryError.value = ''
    return
  }
  const normalizedTargetPage = Math.max(1, Number(targetPage || 1))
  mainChatQueryHistoryError.value = ''
  mainChatQueryHistoryLoading.value = true
  try {
    if (append) {
      const response = await runtimeSurfaceApi.getMainChatQueryHistory({
        conversation_id: currentConversationId.value,
        page: normalizedTargetPage,
        page_size: 5,
      })
      const normalized = buildMainChatQueryHistoryContract(response?.data)
      mainChatQueryHistory.value = {
        ...normalized,
        items: [...mainChatQueryHistory.value.items, ...normalized.items],
      }
      return
    }
    let accumulatedHistory = buildMainChatQueryHistoryContract()
    for (let page = 1; page <= normalizedTargetPage; page += 1) {
      const response = await runtimeSurfaceApi.getMainChatQueryHistory({
        conversation_id: currentConversationId.value,
        page,
        page_size: 5,
      })
      const normalized = buildMainChatQueryHistoryContract(response?.data)
      accumulatedHistory = page === 1
        ? normalized
        : {
          ...normalized,
          items: [...accumulatedHistory.items, ...normalized.items],
        }
      if (!normalized.hasMore) {
        break
      }
    }
    mainChatQueryHistory.value = accumulatedHistory
  } catch (requestError) {
    mainChatQueryHistory.value = buildMainChatQueryHistoryContract()
    mainChatQueryHistoryError.value = requestError?.response?.data?.detail || requestError?.message || '加载 query history 失败'
  } finally {
    mainChatQueryHistoryLoading.value = false
  }
}

async function loadMoreMainChatQueryHistory() {
  if (!mainChatQueryHistory.value.hasMore || mainChatQueryHistoryLoading.value) {
    return
  }
  const nextPage = Number(activeMainChatHistoryPage.value || 1) + 1
  activeMainChatHistoryPage.value = nextPage
  await loadMainChatQueryHistory(nextPage, true)
}

async function loadMainChatQueryDetail() {
  if (!currentConversationId.value || !activeQueryId.value) {
    queryDetailContract.value = null
    return
  }
  try {
    const response = await runtimeSurfaceApi.getMainChatQueryDetail({
      conversation_id: currentConversationId.value,
      query_id: activeQueryId.value,
    })
    queryDetailContract.value = buildMainChatQueryDetailContract(response?.data)
  } catch (_error) {
    queryDetailContract.value = null
  }
}

function isSnapshotHighlighted(entry) {
  if (!activeSnapshotId.value) {
    return false
  }
  return entrySnapshotRef(entry)?.snapshot_id === activeSnapshotId.value
}

function isPayloadExpanded(entryKey) {
  return Boolean(expandedPayloadKeys.value[entryKey])
}

function togglePayload(entryKey) {
  expandedPayloadKeys.value = {
    ...expandedPayloadKeys.value,
    [entryKey]: !expandedPayloadKeys.value[entryKey],
  }
}

function isSummaryOutcomeActive(entry, filterKey) {
  if (activeFilter.value !== filterKey) {
    return false
  }
  const snapshotId = entrySnapshotRef(entry)?.snapshot_id
  if (!snapshotId) {
    return !activeSnapshotId.value
  }
  return activeSnapshotId.value === snapshotId
}

function isHistoryStageFocused(query) {
  return checkHistoryStageFocused(query, activeQueryId.value, activeQueryStage.value)
}

function formatHistoryStageTags(query) {
  return buildHistoryStageTags(query, activeQueryId.value, activeQueryStage.value)
}

watch([activeQueryId, currentConversationId], async () => {
  await loadMainChatQueryDetail()
})

watch([activeFilter, currentConversationId], async ([filterValue]) => {
  if (filterValue !== 'main_chat') {
    mainChatQueryHistory.value = buildMainChatQueryHistoryContract()
    mainChatQueryHistoryError.value = ''
    mainChatHistorySearch.value = ''
    activeMainChatHistoryPage.value = 1
    return
  }
  await loadMainChatQueryHistory(activeMainChatHistoryPage.value)
})

watch(
  () => route.query.governance_query_search,
  (value) => {
    mainChatHistorySearch.value = normalizeText(value)
  },
  { immediate: true }
)

watch(mainChatHistorySearch, (value) => {
  const currentSearch = String(route.query.governance_query_search || '').trim()
  const normalizedNextSearch = normalizeText(value)
  if (currentSearch === normalizedNextSearch) {
    return
  }
  const nextQuery = {
    ...route.query,
  }
  if (!normalizedNextSearch) {
    delete nextQuery.governance_query_search
  } else {
    nextQuery.governance_query_search = normalizedNextSearch
  }
  router.replace({ query: nextQuery }).catch(() => {})
})

watch(
  () => route.query.governance_query_page,
  async (value) => {
    const parsed = Number(value)
    const nextPage = Number.isFinite(parsed) && parsed > 0 ? parsed : 1
    if (activeMainChatHistoryPage.value === nextPage) {
      return
    }
    activeMainChatHistoryPage.value = nextPage
    if (activeFilter.value === 'main_chat' && currentConversationId.value) {
      await loadMainChatQueryHistory(nextPage)
    }
  },
  { immediate: true }
)

watch(activeMainChatHistoryPage, (value) => {
  const currentPage = Number(route.query.governance_query_page || 1)
  const normalizedNextPage = Math.max(1, Number(value || 1))
  if (currentPage === normalizedNextPage) {
    return
  }
  const nextQuery = {
    ...route.query,
  }
  if (normalizedNextPage <= 1) {
    delete nextQuery.governance_query_page
  } else {
    nextQuery.governance_query_page = String(normalizedNextPage)
  }
  router.replace({ query: nextQuery }).catch(() => {})
})

watch(currentConversationId, async (value, previous) => {
  if (value && value !== previous) {
    lastAutoFocusSignature.value = ''
    await loadTimeline()
  }
}, { immediate: false })

onMounted(async () => {
  refreshRecentSnapshotCommands()
  await loadTimeline()
})
onUnmounted(() => {
  resetCopiedActiveDedupeKey()
})
</script>

<style scoped>
.governance-timeline-panel {
  width: 100%;
}

.section-head,
.card-head,
.doctor-outcome-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
}

.section-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.section-desc,
.muted,
.empty-hint {
  color: var(--text-tertiary);
  font-size: 0.875rem;
}

.empty-hint,
.inline-error {
  margin: var(--space-sm) 0;
}

.panel-card {
  border: 1px solid var(--border-color);
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
}

.governance-overview-grid {
  margin-bottom: var(--space-lg);
}

.main-chat-query-workspace {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.main-chat-query-workspace-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-md);
}

.main-chat-query-workspace-grid {
  display: grid;
  gap: var(--space-md);
  grid-template-columns: minmax(320px, 1.2fr) minmax(260px, 0.8fr);
  align-items: start;
}

.governance-overview-card {
  padding: var(--space-md);
  gap: var(--space-sm);
  text-align: left;
}

.overview-card-main {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-xs);
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.overview-card-actions {
  display: flex;
  justify-content: flex-end;
}

.overview-risk-btn {
  padding: 4px 10px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: rgba(249, 115, 22, 0.08);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.76rem;
}

.overview-risk-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.overview-risk-btn.active {
  border-color: rgba(249, 115, 22, 0.45);
  background: rgba(249, 115, 22, 0.16);
  color: var(--text-primary);
}

.overview-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-sm);
}

.overview-severity-badge {
  font-size: 0.68rem;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid transparent;
}

.overview-severity-badge.severity-warning {
  color: #c2410c;
  border-color: rgba(249, 115, 22, 0.35);
  background: rgba(249, 115, 22, 0.12);
}

.overview-severity-badge.severity-success {
  color: #15803d;
  border-color: rgba(34, 197, 94, 0.3);
  background: rgba(34, 197, 94, 0.12);
}

.overview-severity-badge.severity-info {
  color: var(--text-secondary);
  border-color: var(--border-color);
  background: rgba(148, 163, 184, 0.08);
}

.governance-overview-card.active {
  border-width: 2px;
  border-color: var(--border-primary);
  background: rgba(15, 118, 110, 0.08);
}

.governance-overview-card.severity-warning {
  border-color: rgba(249, 115, 22, 0.35);
}

.governance-overview-card.severity-success {
  border-color: rgba(34, 197, 94, 0.28);
}

.overview-card-title {
  margin-top: 2px;
  color: var(--text-primary);
  font-size: 0.84rem;
  line-height: 1.4;
}

.overview-card-metrics {
  color: var(--text-secondary);
  font-size: 0.76rem;
}

.overview-card-time {
  color: var(--text-tertiary);
  font-size: 0.74rem;
}

@media (max-width: 980px) {
  .main-chat-query-workspace-grid {
    grid-template-columns: 1fr;
  }
}

.governance-focus-notice {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
  padding: var(--space-sm) var(--space-md);
  border: 1px solid rgba(249, 115, 22, 0.25);
  border-radius: var(--radius-md);
  background: rgba(249, 115, 22, 0.08);
  color: var(--text-secondary);
  font-size: 0.84rem;
}

.panel-card {
  padding: var(--space-lg);
  margin-bottom: var(--space-lg);
}

.doctor-state-card.doctor-warning {
  border-color: rgba(249, 115, 22, 0.35);
  background: rgba(249, 115, 22, 0.06);
}

.doctor-state-card.doctor-success {
  border-color: rgba(34, 197, 94, 0.3);
  background: rgba(34, 197, 94, 0.06);
}

.summary-action-card {
  width: 100%;
  text-align: left;
  cursor: pointer;
}

.summary-action-main {
  width: 100%;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.summary-action-card.active {
  border-width: 2px;
}

.permission-state-card.permission-warning {
  border-color: rgba(245, 158, 11, 0.35);
  background: rgba(245, 158, 11, 0.06);
}

.permission-state-card.permission-success {
  border-color: rgba(14, 165, 233, 0.35);
  background: rgba(14, 165, 233, 0.06);
}

.mcp-state-card.mcp-info,
.mcp-state-card.mcp-success {
  border-color: rgba(59, 130, 246, 0.35);
  background: rgba(59, 130, 246, 0.06);
}

.governance-state-card.governance-info,
.governance-state-card.governance-success {
  border-color: rgba(16, 185, 129, 0.35);
  background: rgba(16, 185, 129, 0.06);
}

.scheduler-state-card.scheduler-success,
.scheduler-state-card.scheduler-info {
  border-color: rgba(168, 85, 247, 0.32);
  background: rgba(168, 85, 247, 0.06);
}

.hook-state-card.hook-warning,
.hook-state-card.hook-info {
  border-color: rgba(245, 158, 11, 0.35);
  background: rgba(245, 158, 11, 0.06);
}

.runtime-state-card.runtime-info,
.runtime-state-card.runtime-success {
  border-color: rgba(100, 116, 139, 0.35);
  background: rgba(100, 116, 139, 0.08);
}

.learning-state-card.learning-info,
.learning-state-card.learning-success {
  border-color: rgba(16, 185, 129, 0.35);
  background: rgba(16, 185, 129, 0.08);
}

.doctor-outcome-row {
  margin-top: var(--space-md);
  align-items: flex-start;
}

.timeline-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.timeline-empty-state {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  padding: var(--space-md);
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-lg);
  background: var(--bg-elevated);
  color: var(--text-secondary);
  word-break: break-all;
}

.timeline-empty-state strong {
  color: var(--text-primary);
}

.timeline-empty-state .payload-toggle-btn {
  align-self: flex-start;
  margin-top: var(--space-xs);
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

.secondary-btn {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-color);
  background: var(--bg-elevated);
  color: var(--text-primary);
  border-radius: var(--radius-md);
  cursor: pointer;
}

.inline-error {
  color: #dc2626;
}
</style>
