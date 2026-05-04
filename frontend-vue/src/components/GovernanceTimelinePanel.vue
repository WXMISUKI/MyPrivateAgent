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
      <div class="summary-grid">
        <div class="summary-card">
          <span class="summary-label">当前计划</span>
          <strong>{{ currentPlan.objective || '-' }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">聚焦步骤</span>
          <strong>{{ focusItem.title || '-' }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">审计事件</span>
          <strong>{{ auditCount }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">运行 Trace</span>
          <strong>{{ traceCount }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">当前筛选</span>
          <strong>{{ activeFilterLabel }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">风险模式</span>
          <strong>{{ activeSeverityLabel }}</strong>
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

      <div v-if="governanceOverviewCards.length" class="summary-grid governance-overview-grid">
        <div
          v-for="card in governanceOverviewCards"
          :key="card.key"
          class="summary-card governance-overview-card"
          :class="[{ active: activeFilter === card.key }, `severity-${card.severity || 'info'}`]"
        >
          <button type="button" class="overview-card-main" @click="applyFilter(card.key)">
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
              @click="applyWarningFocus(card.key)"
            >
              {{ card.warningCount > 0 ? `仅告警 · ${card.warningCount}` : '无告警' }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="autoFocusNotice" class="governance-focus-notice">
        <strong>自动聚焦</strong>
        <span>{{ autoFocusNotice }}</span>
      </div>

      <div v-if="recentCopiedCommandText" class="governance-command-notice">
        <strong>最近复制命令</strong>
        <code>{{ recentCopiedCommandText }}</code>
      </div>

      <button
        v-if="lastDoctorOutcome"
        type="button"
        class="panel-card summary-action-card doctor-state-card"
        :class="[`doctor-${lastDoctorOutcome.severity}`, { active: activeFilter === 'doctor' }]"
        @click="applyFilter('doctor')"
      >
        <div class="card-head">
          <h3>最近一次 Doctor 结果</h3>
          <span class="muted">{{ formatAuditTime(lastDoctorOutcome.timestamp) }}</span>
        </div>
        <div class="doctor-outcome-row">
          <strong>{{ lastDoctorOutcome.title }}</strong>
          <span>{{ lastDoctorOutcome.detail || '无附加信息' }}</span>
        </div>
      </button>

      <button
        v-if="lastPermissionOutcome"
        type="button"
        class="panel-card summary-action-card permission-state-card"
        :class="[`permission-${lastPermissionOutcome.severity}`, { active: activeFilter === 'permission' }]"
        @click="applyFilter('permission')"
      >
        <div class="card-head">
          <h3>最近一次权限结果</h3>
          <span class="muted">{{ formatAuditTime(lastPermissionOutcome.timestamp) }}</span>
        </div>
        <div class="doctor-outcome-row">
          <strong>{{ lastPermissionOutcome.title }}</strong>
          <span>{{ lastPermissionOutcome.content || '无附加信息' }}</span>
        </div>
      </button>

      <button
        v-if="lastMcpOutcome"
        type="button"
        class="panel-card summary-action-card mcp-state-card"
        :class="[`mcp-${lastMcpOutcome.severity}`, { active: activeFilter === 'mcp' }]"
        @click="applyFilter('mcp')"
      >
        <div class="card-head">
          <h3>最近一次 MCP 结果</h3>
          <span class="muted">{{ formatAuditTime(lastMcpOutcome.timestamp) }}</span>
        </div>
        <div class="doctor-outcome-row">
          <strong>{{ lastMcpOutcome.title }}</strong>
          <span>{{ lastMcpOutcome.content || lastMcpOutcome.detail || '无附加信息' }}</span>
        </div>
      </button>

      <button
        v-if="lastGovernanceOutcome"
        type="button"
        class="panel-card summary-action-card governance-state-card"
        :class="[`governance-${lastGovernanceOutcome.severity}`, { active: activeFilter === 'governance' }]"
        @click="applyFilter('governance')"
      >
        <div class="card-head">
          <h3>最近一次整改结果</h3>
          <span class="muted">{{ formatAuditTime(lastGovernanceOutcome.timestamp) }}</span>
        </div>
        <div class="doctor-outcome-row">
          <strong>{{ lastGovernanceOutcome.title }}</strong>
          <span>{{ lastGovernanceOutcome.content || lastGovernanceOutcome.detail || '无附加信息' }}</span>
        </div>
      </button>

      <button
        v-if="lastSchedulerOutcome"
        type="button"
        class="panel-card summary-action-card scheduler-state-card"
        :class="[`scheduler-${lastSchedulerOutcome.severity}`, { active: activeFilter === 'scheduler' }]"
        @click="applyFilter('scheduler')"
      >
        <div class="card-head">
          <h3>最近一次调度结果</h3>
          <span class="muted">{{ formatAuditTime(lastSchedulerOutcome.timestamp) }}</span>
        </div>
        <div class="doctor-outcome-row">
          <strong>{{ lastSchedulerOutcome.title }}</strong>
          <span>{{ lastSchedulerOutcome.content || lastSchedulerOutcome.detail || '无附加信息' }}</span>
        </div>
      </button>

      <button
        v-if="lastHookOutcome"
        type="button"
        class="panel-card summary-action-card hook-state-card"
        :class="[`hook-${lastHookOutcome.severity}`, { active: activeFilter === 'hook' }]"
        @click="applyFilter('hook')"
      >
        <div class="card-head">
          <h3>最近一次 Hook 结果</h3>
          <span class="muted">{{ formatAuditTime(lastHookOutcome.timestamp) }}</span>
        </div>
        <div class="doctor-outcome-row">
          <strong>{{ lastHookOutcome.title }}</strong>
          <span>{{ lastHookOutcome.content || lastHookOutcome.detail || '无附加信息' }}</span>
        </div>
      </button>

        <button
        v-if="lastLearningOutcome"
        type="button"
        class="panel-card summary-action-card learning-state-card"
        :class="[`learning-${lastLearningOutcome.severity}`, { active: activeFilter === 'learning' }]"
        @click="applyFilter('learning')"
      >
        <div class="card-head">
          <h3>最近一次 Learning 结果</h3>
          <span class="muted">{{ formatAuditTime(lastLearningOutcome.timestamp) }}</span>
        </div>
        <div class="doctor-outcome-row">
          <strong>{{ lastLearningOutcome.title }}</strong>
          <span>{{ lastLearningOutcome.content || lastLearningOutcome.detail || '无附加信息' }}</span>
        </div>
      </button>

      <button
        v-if="lastRuntimeOutcome"
        type="button"
        class="panel-card summary-action-card runtime-state-card"
        :class="[`runtime-${lastRuntimeOutcome.severity}`, { active: activeFilter === 'runtime' }]"
        @click="applyFilter('runtime')"
      >
        <div class="card-head">
          <h3>最近一次 Runtime 结果</h3>
          <span class="muted">{{ formatAuditTime(lastRuntimeOutcome.timestamp) }}</span>
        </div>
        <div class="doctor-outcome-row">
          <strong>{{ lastRuntimeOutcome.title }}</strong>
          <span>{{ lastRuntimeOutcome.content || lastRuntimeOutcome.detail || '无附加信息' }}</span>
        </div>
      </button>

      <div class="panel-card">
        <div class="card-head">
          <h3>统一事件流</h3>
          <span class="muted">最近 {{ filteredTimeline.length }} / {{ scopedTimeline.length }} 条</span>
        </div>
        <div class="filter-chip-row severity-chip-row">
          <button
            v-for="option in severityFilters"
            :key="option.key"
            class="filter-chip severity-chip"
            :class="{ active: activeSeverity === option.key }"
            @click="activeSeverity = option.key"
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
            @click="activeFilter = filter.key"
          >
            {{ filter.label }} · {{ filter.count }}
          </button>
        </div>
        <div class="timeline-list">
          <div
            v-for="entry in filteredTimeline"
            :key="entry.key"
            class="timeline-item"
            :class="[`severity-${entry.severity}`, { highlighted: isSnapshotHighlighted(entry) }]"
          >
            <div class="timeline-top">
              <span class="timeline-badges">
                <span class="timeline-kind">{{ entry.kindLabel }}</span>
                <span v-if="entry.domainLabel" class="timeline-source">{{ entry.domainLabel }}</span>
                <span v-if="entry.sourceLabel" class="timeline-source">{{ entry.sourceLabel }}</span>
                <span class="timeline-event">{{ entry.title }}</span>
              </span>
              <span class="timeline-time">{{ formatAuditTime(entry.timestamp) }}</span>
            </div>
            <div class="timeline-content">{{ entry.content }}</div>
            <div v-if="entry.detail" class="timeline-detail">{{ entry.detail }}</div>
            <div v-if="entrySnapshotRef(entry)" class="timeline-snapshot-ref">
              引用 {{ entrySnapshotRef(entry)?.snapshot_id }}
            </div>
            <div v-if="entry.payloadSummary" class="timeline-payload-summary">{{ entry.payloadSummary }}</div>
            <div v-if="hasPayload(entry)" class="timeline-payload-actions">
              <button class="payload-toggle-btn" @click="togglePayload(entry.key)">
                {{ isPayloadExpanded(entry.key) ? '收起 Payload' : '展开 Payload' }}
              </button>
              <button v-if="entrySnapshotRef(entry)" class="payload-toggle-btn" @click="copySnapshotRef(entry)">
                {{ copiedSnapshotKey === entry.key ? '已复制引用' : '复制引用' }}
              </button>
              <button v-if="entrySnapshotRef(entry)" class="payload-toggle-btn" @click="copySnapshotCommand(entry)">
                {{ copiedCommandTarget === entry.key ? '已复制命令' : '复制命令' }}
              </button>
              <button class="payload-toggle-btn" @click="copyPayload(entry)">
                {{ copiedPayloadKey === entry.key ? '已复制 Payload' : '复制 Payload' }}
              </button>
            </div>
            <pre v-if="hasPayload(entry) && isPayloadExpanded(entry.key)" class="timeline-payload-json">{{ formatPayloadJson(entry.payload) }}</pre>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useConversationStore } from '../stores/conversation'
import { usePlannerStore } from '../stores/planner'
import { buildSnapshotCommandDescriptor, persistRecentSnapshotCommand } from '../services/governanceSnapshotCommands'

const router = useRouter()
const route = useRoute()
const conversationStore = useConversationStore()
const plannerStore = usePlannerStore()
const loading = ref(false)
const error = ref('')
const activeFilter = ref('all')
const activeSeverity = ref('all')
const activeSnapshotId = ref('')
const expandedPayloadKeys = ref({})
const copiedPayloadKey = ref('')
const copiedSnapshotKey = ref('')
const copiedCommandTarget = ref('')
const copiedViewLink = ref(false)
const recentCopiedCommandText = ref('')
const lastAutoFocusSignature = ref('')
let copiedPayloadResetTimer = null
let copiedSnapshotResetTimer = null
let copiedCommandResetTimer = null
let copiedViewResetTimer = null

const currentConversationId = computed(() => {
  const id = Number(conversationStore.currentConversation?.id)
  return Number.isFinite(id) ? id : null
})

const currentPlan = computed(() => plannerStore.currentPlan)

const focusItem = computed(() => {
  const items = currentPlan.value?.items || []
  if (!items.length) return null

  const withGovernanceTrace = [...items].sort((left, right) => {
    return getLatestGovernanceTimestamp(right) - getLatestGovernanceTimestamp(left)
  }).find(item => getLatestGovernanceTimestamp(item) > 0)
  if (withGovernanceTrace) {
    return withGovernanceTrace
  }

  return (
    items.find(item => item.id === currentPlan.value?.active_item_id) ||
    items.find(item => item.status === 'in_progress') ||
    items[0]
  )
})

const auditCount = computed(() => (focusItem.value?.audit_trail || []).length)
const traceCount = computed(() => (focusItem.value?.run_trace || []).length)

const combinedTimeline = computed(() => {
  if (!focusItem.value) return []
  const auditEntries = (focusItem.value.audit_trail || []).map((entry, index) => ({
    key: `audit-${entry.timestamp || 'na'}-${entry.event_type || 'unknown'}-${index}`,
    timestamp: entry.timestamp,
    kind: 'audit',
    kindLabel: 'Audit',
    domain: inferTimelineDomain(entry.event_type, ''),
    domainLabel: formatTimelineDomain(inferTimelineDomain(entry.event_type, '')),
    sourceLabel: '',
    severity: normalizeSeverity(entry.event_type),
    title: formatAuditEvent(entry.event_type),
    content: entry.content || '无说明',
    detail: '',
    payload: normalizePayload(entry.payload),
    payloadSummary: formatPayloadSummary(entry.payload),
  }))
  const traceEntries = (focusItem.value.run_trace || []).map((entry, index) => ({
    key: `trace-${entry.timestamp || 'na'}-${entry.source || 'runtime'}-${entry.event_type || 'unknown'}-${index}`,
    timestamp: entry.timestamp,
    kind: 'trace',
    kindLabel: 'Trace',
    domain: inferTimelineDomain(entry.event_type, entry.source),
    domainLabel: formatTimelineDomain(inferTimelineDomain(entry.event_type, entry.source)),
    sourceLabel: formatTraceSource(entry.source),
    severity: entry.severity || 'info',
    title: formatAuditEvent(entry.event_type),
    content: entry.summary || '无摘要',
    detail: entry.detail || '',
    payload: normalizePayload(entry.payload),
    payloadSummary: formatPayloadSummary(entry.payload),
  }))
  return [...traceEntries, ...auditEntries]
    .sort((left, right) => toTimestamp(right.timestamp) - toTimestamp(left.timestamp))
    .slice(0, 20)
})

const severityFilters = computed(() => {
  const warningCount = combinedTimeline.value.filter(entry => entry.severity === 'warning').length
  return [
    { key: 'all', label: '全部事件', count: combinedTimeline.value.length },
    { key: 'warning', label: '仅告警', count: warningCount },
  ]
})

const scopedTimeline = computed(() => {
  if (activeSeverity.value === 'warning') {
    return combinedTimeline.value.filter(entry => entry.severity === 'warning')
  }
  return combinedTimeline.value
})

const timelineFilters = computed(() => {
  const counters = new Map()
  for (const entry of scopedTimeline.value) {
    const key = String(entry.domain || 'other').trim() || 'other'
    counters.set(key, Number(counters.get(key) || 0) + 1)
  }
  const orderedKeys = ['all', 'doctor', 'permission', 'mcp', 'governance', 'scheduler', 'hook', 'runtime', 'learning', 'other']
  return orderedKeys
    .filter(key => key === 'all' || counters.has(key))
    .map(key => ({
      key,
      label: key === 'all' ? '全部' : formatTimelineDomain(key),
      count: key === 'all'
        ? scopedTimeline.value.length
        : Number(counters.get(key) || 0),
    }))
})

const filteredTimeline = computed(() => {
  const domainScoped = activeFilter.value === 'all'
    ? scopedTimeline.value
    : scopedTimeline.value.filter(entry => entry.domain === activeFilter.value)
  if (!activeSnapshotId.value) {
    return domainScoped
  }
  const snapshotMatched = domainScoped.filter(entry => entrySnapshotRef(entry)?.snapshot_id === activeSnapshotId.value)
  return snapshotMatched.length ? snapshotMatched : domainScoped
})

const activeFilterLabel = computed(() => {
  const matched = timelineFilters.value.find(item => item.key === activeFilter.value)
  return matched?.label || '全部'
})

const activeSeverityLabel = computed(() => {
  const matched = severityFilters.value.find(item => item.key === activeSeverity.value)
  return matched?.label || '全部事件'
})

const currentSnapshotRef = computed(() => {
  const candidates = [
    ...filteredTimeline.value,
    ...scopedTimeline.value,
    ...combinedTimeline.value,
  ]
  for (const entry of candidates) {
    const snapshotRef = normalizeSnapshotRef(entry?.payload?.snapshot_ref)
    if (snapshotRef) {
      return snapshotRef
    }
  }
  return null
})

const currentSnapshotId = computed(() => currentSnapshotRef.value?.snapshot_id || '本地待生成')
const currentSnapshotGeneratedAt = computed(() => currentSnapshotRef.value?.generated_at || '')
const activeSnapshotLabel = computed(() => activeSnapshotId.value || '未指定')
const activeSnapshotNotice = computed(() => {
  if (!activeSnapshotId.value) {
    return '当前展示的是常规治理视图'
  }
  const matched = combinedTimeline.value.find(entry => entrySnapshotRef(entry)?.snapshot_id === activeSnapshotId.value)
  if (!matched) {
    return '当前会话未找到对应快照，已回退到常规治理视图'
  }
  return `已聚焦到 ${matched.title}`
})

const governanceOverviewCards = computed(() => {
  const order = ['doctor', 'permission', 'mcp', 'governance', 'scheduler', 'hook', 'runtime', 'learning']
  const countMap = new Map(timelineFilters.value.map(item => [item.key, item.count]))
  const latestByDomain = new Map()
  const warningCountByDomain = new Map()
  for (const entry of combinedTimeline.value) {
    if (!latestByDomain.has(entry.domain)) {
      latestByDomain.set(entry.domain, entry)
    }
    if (entry.severity === 'warning') {
      warningCountByDomain.set(entry.domain, Number(warningCountByDomain.get(entry.domain) || 0) + 1)
    }
  }
  return order
    .filter(key => Number(countMap.get(key) || 0) > 0)
    .map(key => ({
      key,
      label: formatTimelineDomain(key),
      count: Number(countMap.get(key) || 0),
      warningCount: Number(warningCountByDomain.get(key) || 0),
      severity: latestByDomain.get(key)?.severity || 'info',
      latestTitle: latestByDomain.get(key)?.title || '',
      latestTimestamp: latestByDomain.get(key)?.timestamp || '',
      sortIndex: order.indexOf(key),
    }))
    .sort((left, right) => {
      const timestampDelta = toTimestamp(right.latestTimestamp) - toTimestamp(left.latestTimestamp)
      if (timestampDelta !== 0) {
        return timestampDelta
      }
      const severityDelta = getSeverityRank(right.severity) - getSeverityRank(left.severity)
      if (severityDelta !== 0) {
        return severityDelta
      }
      return left.sortIndex - right.sortIndex
    })
})

const recommendedFocusFilter = computed(() => {
  if (!lastDoctorOutcome.value || lastDoctorOutcome.value.title !== formatAuditEvent('doctor_gate_failed')) {
    return 'all'
  }
  const highestRiskDomain = governanceOverviewCards.value.find(card => card.key !== 'doctor' && card.severity === 'warning')
  if (highestRiskDomain) {
    return highestRiskDomain.key
  }
  return 'doctor'
})

const recommendedFocusSignature = computed(() => {
  if (!focusItem.value || recommendedFocusFilter.value === 'all') {
    return ''
  }
  return [
    focusItem.value.id || 'na',
    lastDoctorOutcome.value?.timestamp || 'na',
    recommendedFocusFilter.value,
  ].join(':')
})

const autoFocusNotice = computed(() => {
  if (!recommendedFocusSignature.value || route.query.governance_filter) {
    return ''
  }
  if (lastAutoFocusSignature.value !== recommendedFocusSignature.value) {
    return ''
  }
  if (activeFilter.value !== recommendedFocusFilter.value) {
    return ''
  }
  const matchedCard = governanceOverviewCards.value.find(card => card.key === recommendedFocusFilter.value)
  if (!matchedCard) {
    return ''
  }
  if (recommendedFocusFilter.value === 'doctor') {
    return '因 Doctor 门禁失败，当前默认聚焦到 Doctor 域。'
  }
  return `因 Doctor 门禁失败，当前默认聚焦到 ${matchedCard.label} 风险域，共 ${matchedCard.warningCount} 条告警。`
})

const lastDoctorOutcome = computed(() => {
  const entry = combinedTimeline.value.find(item =>
    item.domain === 'doctor' && item.kind === 'trace' && (
      item.title === formatAuditEvent('doctor_gate_failed') ||
      item.title === formatAuditEvent('doctor_run_completed')
    )
  )
  if (!entry) return null
  return entry
})

const lastPermissionOutcome = computed(() => {
  return combinedTimeline.value.find(item =>
    item.domain === 'permission' && (
      item.title === formatAuditEvent('permission_approved') ||
      item.title === formatAuditEvent('permission_denied') ||
      item.title === formatAuditEvent('tool_permission_required')
    )
  ) || null
})

const lastMcpOutcome = computed(() => {
  return combinedTimeline.value.find(item =>
    item.domain === 'mcp' && (
      item.title === formatAuditEvent('mcp_tool_call_completed') ||
      item.title === formatAuditEvent('mcp_server_handshake_completed') ||
      item.title === formatAuditEvent('mcp_server_probed') ||
      item.title === formatAuditEvent('mcp_server_created') ||
      item.title === formatAuditEvent('mcp_server_updated')
    )
  ) || null
})

const lastGovernanceOutcome = computed(() => {
  return combinedTimeline.value.find(item =>
    item.domain === 'governance' && item.title === formatAuditEvent('remediation_status_updated')
  ) || null
})

const lastSchedulerOutcome = computed(() => {
  return combinedTimeline.value.find(item =>
    item.domain === 'scheduler' && (
      item.title === formatAuditEvent('scheduler_merged') ||
      item.title === formatAuditEvent('scheduler_execution_started') ||
      item.title === formatAuditEvent('child_completed') ||
      item.title === formatAuditEvent('child_failed')
    )
  ) || null
})

const lastHookOutcome = computed(() => {
  return combinedTimeline.value.find(item =>
    item.domain === 'hook' && (
      item.title === formatAuditEvent('pre_tool_use_blocked') ||
      item.title.includes('Hook')
    )
  ) || null
})

const lastLearningOutcome = computed(() => {
  return combinedTimeline.value.find(item =>
    item.domain === 'learning' && (
      item.title === formatAuditEvent('learning_version_applied') ||
      item.title.includes('Learning')
    )
  ) || null
})

const lastRuntimeOutcome = computed(() => {
  return combinedTimeline.value.find(item =>
    item.domain === 'runtime' && (
      item.title === formatAuditEvent('agent_state_changed') ||
      item.title.includes('运行时')
    )
  ) || null
})

async function loadTimeline() {
  if (!currentConversationId.value) return
  loading.value = true
  error.value = ''
  try {
    await plannerStore.loadPlans({ conversationId: currentConversationId.value })
  } catch (err) {
    error.value = err?.response?.data?.detail || err?.message || '加载治理时间线失败'
  } finally {
    loading.value = false
  }
}

function normalizePayload(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return null
  }
  return payload
}

function normalizeSnapshotRef(snapshotRef) {
  if (!snapshotRef || typeof snapshotRef !== 'object' || Array.isArray(snapshotRef)) {
    return null
  }
  const snapshotId = String(snapshotRef.snapshot_id || '').trim()
  if (!snapshotId) {
    return null
  }
  return {
    snapshot_id: snapshotId,
    generated_at: String(snapshotRef.generated_at || '').trim(),
    conversation_id: snapshotRef.conversation_id ?? null,
    source: String(snapshotRef.source || '').trim(),
    event_type: String(snapshotRef.event_type || '').trim(),
  }
}

function toTimestamp(value) {
  const date = new Date(value || '')
  return Number.isNaN(date.getTime()) ? 0 : date.getTime()
}

function getLatestGovernanceTimestamp(item) {
  const traces = item?.run_trace || []
  const audits = item?.audit_trail || []
  const traceMax = traces.reduce((currentMax, entry) => {
    const domain = inferTimelineDomain(entry?.event_type, entry?.source)
    if (!isGovernanceDomain(domain)) {
      return currentMax
    }
    return Math.max(currentMax, toTimestamp(entry?.timestamp))
  }, 0)
  const auditMax = audits.reduce((currentMax, entry) => {
    const domain = inferTimelineDomain(entry?.event_type, '')
    if (!isGovernanceDomain(domain)) {
      return currentMax
    }
    return Math.max(currentMax, toTimestamp(entry?.timestamp))
  }, 0)
  return Math.max(traceMax, auditMax)
}

function isGovernanceDomain(domain) {
  return ['doctor', 'permission', 'mcp', 'governance', 'scheduler', 'hook', 'runtime', 'learning'].includes(String(domain || '').trim())
}

function normalizeSeverity(eventType) {
  if (eventType === 'doctor_gate_failed') return 'warning'
  if (String(eventType || '').includes('failed') || String(eventType || '').includes('blocked')) return 'warning'
  if (String(eventType || '').includes('denied')) return 'warning'
  if (
    String(eventType || '').includes('approved') ||
    String(eventType || '').includes('completed') ||
    String(eventType || '').includes('updated') ||
    String(eventType || '').includes('enabled')
  ) return 'success'
  return 'info'
}

function getSeverityRank(severity) {
  const ranks = {
    warning: 3,
    success: 2,
    info: 1,
  }
  return Number(ranks[String(severity || 'info').trim()] || 0)
}

function formatAuditEvent(eventType) {
  const labelMap = {
    doctor_run_started: 'Doctor 启动',
    doctor_run_completed: 'Doctor 完成',
    doctor_gate_failed: 'Doctor 门禁失败',
    scheduler_fanout_prepared: '调度拆分',
    scheduler_execution_started: '调度启动',
    scheduler_merged: '结果合并',
    scheduler_cancelled: '调度取消',
    child_running: '子执行启动',
    child_completed: '子执行完成',
    child_failed: '子执行失败',
    child_retrying: '子执行重试',
    child_cancelled: '子执行取消',
    permission_approved: '权限批准',
    permission_denied: '权限拒绝',
    tool_permission_required: '等待工具授权',
    remediation_status_updated: '整改状态更新',
    mcp_server_created: 'MCP 服务创建',
    mcp_server_updated: 'MCP 服务更新',
    mcp_server_deleted: 'MCP 服务删除',
    mcp_server_enabled: 'MCP 服务启用',
    mcp_server_disabled: 'MCP 服务停用',
    mcp_server_probed: 'MCP Probe 完成',
    mcp_server_handshake_completed: 'MCP Handshake 完成',
    mcp_tool_call_completed: 'MCP 工具调用完成',
    pre_tool_use_blocked: 'Hook 阻断',
    agent_state_changed: '运行时状态迁移',
    learning_version_applied: 'Learning 版本应用',
  }
  return labelMap[eventType] || eventType || '未知事件'
}

function inferTimelineDomain(eventType, source) {
  const sourceText = String(source || '').trim()
  if (sourceText) {
    if (['doctor', 'permission', 'mcp', 'governance', 'scheduler', 'hook', 'runtime'].includes(sourceText)) {
      return sourceText
    }
  }
  const eventText = String(eventType || '').trim()
  if (eventText.startsWith('doctor_')) return 'doctor'
  if (eventText.startsWith('permission_') || eventText === 'tool_permission_required') return 'permission'
  if (eventText.startsWith('mcp_')) return 'mcp'
  if (eventText.startsWith('learning_')) return 'learning'
  if (eventText.startsWith('scheduler_') || eventText.startsWith('child_')) return 'scheduler'
  if (eventText.startsWith('remediation_')) return 'governance'
  if (eventText.includes('hook') || eventText === 'pre_tool_use_blocked') return 'hook'
  if (eventText.startsWith('agent_state_') || eventText.startsWith('runtime_')) return 'runtime'
  return 'other'
}

function formatTimelineDomain(domain) {
  const labelMap = {
    doctor: 'Doctor',
    permission: 'Permission',
    mcp: 'MCP',
    governance: 'Governance',
    scheduler: 'Scheduler',
    hook: 'Hook',
    runtime: 'Runtime',
    learning: 'Learning',
    other: 'Other',
  }
  return labelMap[domain] || domain || 'Other'
}

function formatSeverityBadge(severity) {
  const value = String(severity || 'info').trim()
  if (value === 'warning') return 'Warn'
  if (value === 'success') return 'OK'
  return 'Info'
}

function formatPayloadSummary(payload) {
  const data = normalizePayload(payload)
  if (!data) return ''
  const priorityKeys = [
    'action_id',
    'status',
    'server_name',
    'tool_name',
    'request_id',
    'scope',
    'exit_code',
    'gate_passed',
  ]
  const fragments = []
  for (const key of priorityKeys) {
    if (data[key] === undefined || data[key] === null || data[key] === '') {
      continue
    }
    fragments.push(`${key}=${stringifyPayloadValue(data[key])}`)
  }
  return fragments.slice(0, 4).join(' | ')
}

function stringifyPayloadValue(value) {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value)
  }
  if (Array.isArray(value)) {
    return value.join(', ')
  }
  try {
    return JSON.stringify(value)
  } catch (_err) {
    return String(value)
  }
}

function formatPayloadJson(payload) {
  try {
    return JSON.stringify(payload || {}, null, 2)
  } catch (_err) {
    return '{}'
  }
}

function hasPayload(entry) {
  return Boolean(entry?.payload && Object.keys(entry.payload).length)
}

function entrySnapshotRef(entry) {
  return normalizeSnapshotRef(entry?.payload?.snapshot_ref)
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

function applyFilter(filterKey) {
  const nextFilter = String(filterKey || 'all').trim() || 'all'
  activeFilter.value = timelineFilters.value.some(item => item.key === nextFilter) ? nextFilter : 'all'
}

function applyWarningFocus(filterKey) {
  const nextFilter = String(filterKey || 'all').trim() || 'all'
  const matchedCard = governanceOverviewCards.value.find(card => card.key === nextFilter)
  if (!matchedCard || matchedCard.warningCount <= 0) {
    return
  }
  activeSeverity.value = 'warning'
  applyFilter(nextFilter)
}

async function copyPayload(entry) {
  if (!hasPayload(entry)) {
    return
  }
  const text = formatPayloadJson(entry.payload)
  try {
    await writeTextToClipboard(text)
    copiedPayloadKey.value = entry.key
    error.value = ''
    scheduleCopiedPayloadReset()
  } catch (_err) {
    copiedPayloadKey.value = ''
    error.value = '当前环境不支持复制 Payload'
  }
}

async function copySnapshotRef(entry) {
  const snapshotRef = entrySnapshotRef(entry)
  if (!snapshotRef) {
    return
  }
  try {
    await writeTextToClipboard([
      `快照ID: ${snapshotRef.snapshot_id}`,
      `生成时间: ${snapshotRef.generated_at || '-'}`,
      `来源: ${snapshotRef.source || '-'} / ${snapshotRef.event_type || '-'}`,
      `会话: ${snapshotRef.conversation_id ?? '-'}`,
    ].join('\n'))
    copiedSnapshotKey.value = entry.key
    error.value = ''
    scheduleCopiedSnapshotReset()
  } catch (_err) {
    copiedSnapshotKey.value = ''
    error.value = '当前环境不支持复制治理引用'
  }
}

async function copySnapshotCommand(entry) {
  const snapshotRef = entrySnapshotRef(entry)
  if (!snapshotRef) {
    return
  }
  try {
    const descriptor = buildSnapshotCommandDescriptor(snapshotRef.snapshot_id, entry?.domain)
    if (!descriptor) {
      return
    }
    await writeTextToClipboard(descriptor.commandText)
    persistRecentSnapshotCommand(descriptor)
    recentCopiedCommandText.value = descriptor.commandText
    copiedCommandTarget.value = entry.key
    error.value = ''
    scheduleCopiedCommandReset()
  } catch (_err) {
    copiedCommandTarget.value = ''
    error.value = '当前环境不支持复制快照命令'
  }
}

async function copyCurrentSnapshotCommand() {
  if (!currentSnapshotRef.value) {
    return
  }
  try {
    const currentDomain = inferSnapshotCommandDomain(currentSnapshotRef.value, activeFilter.value)
    const descriptor = buildSnapshotCommandDescriptor(currentSnapshotRef.value.snapshot_id, currentDomain)
    if (!descriptor) {
      return
    }
    await writeTextToClipboard(descriptor.commandText)
    persistRecentSnapshotCommand(descriptor)
    recentCopiedCommandText.value = descriptor.commandText
    copiedCommandTarget.value = 'view'
    error.value = ''
    scheduleCopiedCommandReset()
  } catch (_err) {
    copiedCommandTarget.value = ''
    error.value = '当前环境不支持复制快照命令'
  }
}

async function copyCurrentView() {
  if (!currentConversationId.value) {
    return
  }
  try {
    await writeTextToClipboard(buildCurrentViewSnapshot())
    copiedViewLink.value = true
    error.value = ''
    scheduleCopiedViewReset()
  } catch (_err) {
    copiedViewLink.value = false
    error.value = '当前环境不支持复制治理视图'
  }
}

function scheduleCopiedPayloadReset() {
  if (copiedPayloadResetTimer) {
    clearTimeout(copiedPayloadResetTimer)
    copiedPayloadResetTimer = null
  }
  copiedPayloadResetTimer = setTimeout(() => {
    copiedPayloadKey.value = ''
    copiedPayloadResetTimer = null
  }, 1500)
}

function scheduleCopiedSnapshotReset() {
  if (copiedSnapshotResetTimer) {
    clearTimeout(copiedSnapshotResetTimer)
    copiedSnapshotResetTimer = null
  }
  copiedSnapshotResetTimer = setTimeout(() => {
    copiedSnapshotKey.value = ''
    copiedSnapshotResetTimer = null
  }, 1500)
}

function scheduleCopiedCommandReset() {
  if (copiedCommandResetTimer) {
    clearTimeout(copiedCommandResetTimer)
    copiedCommandResetTimer = null
  }
  copiedCommandResetTimer = setTimeout(() => {
    copiedCommandTarget.value = ''
    copiedCommandResetTimer = null
  }, 1500)
}

async function writeTextToClipboard(text) {
  if (globalThis.navigator?.clipboard?.writeText) {
    await globalThis.navigator.clipboard.writeText(text)
    return
  }
  if (typeof document === 'undefined' || typeof document.createElement !== 'function') {
    throw new Error('clipboard unavailable')
  }
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.setAttribute('readonly', 'readonly')
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  textarea.style.pointerEvents = 'none'
  document.body.appendChild(textarea)
  textarea.focus()
  textarea.select()
  try {
    if (typeof document.execCommand !== 'function' || !document.execCommand('copy')) {
      throw new Error('execCommand copy failed')
    }
  } finally {
    document.body.removeChild(textarea)
  }
}

function buildCurrentViewUrl() {
  const baseUrl = new URL(globalThis.location?.href || 'http://localhost/')
  baseUrl.search = ''
  for (const [key, rawValue] of Object.entries(route.query || {})) {
    if (key === 'governance_filter' || key === 'governance_severity') {
      continue
    }
    const value = Array.isArray(rawValue) ? rawValue[0] : rawValue
    if (value === undefined || value === null || value === '') {
      continue
    }
    baseUrl.searchParams.set(key, String(value))
  }
  if (activeFilter.value && activeFilter.value !== 'all') {
    baseUrl.searchParams.set('governance_filter', activeFilter.value)
  }
  if (activeSeverity.value && activeSeverity.value !== 'all') {
    baseUrl.searchParams.set('governance_severity', activeSeverity.value)
  }
  if (activeSnapshotId.value) {
    baseUrl.searchParams.set('governance_snapshot', activeSnapshotId.value)
  }
  return baseUrl.toString()
}

function buildCurrentViewSnapshot() {
  const snapshotTimestamp = currentSnapshotRef.value?.generated_at || new Date().toISOString()
  const snapshotId = currentSnapshotRef.value?.snapshot_id || buildViewSnapshotId(snapshotTimestamp)
  const lines = [
    `快照ID: ${snapshotId}`,
    `生成时间: ${snapshotTimestamp}`,
    `治理视图: ${activeFilterLabel.value} / ${activeSeverityLabel.value}`,
    `事件范围: ${filteredTimeline.value.length} / ${scopedTimeline.value.length}`,
  ]
  if (autoFocusNotice.value) {
    lines.push(`聚焦原因: ${autoFocusNotice.value}`)
  }
  if (currentSnapshotRef.value?.source || currentSnapshotRef.value?.event_type) {
    lines.push(`后端引用: ${currentSnapshotRef.value.source || '-'} / ${currentSnapshotRef.value.event_type || '-'}`)
  }
  lines.push(`链接: ${buildCurrentViewUrl()}`)
  return lines.join('\n')
}

function inferSnapshotCommandDomain(snapshotRef, fallbackDomain = '') {
  const sourceDomain = inferTimelineDomain(snapshotRef?.event_type, snapshotRef?.source)
  if (['mcp', 'permission', 'governance', 'learning'].includes(sourceDomain)) {
    return sourceDomain
  }
  if (['mcp', 'permission', 'governance', 'learning'].includes(String(fallbackDomain || '').trim().toLowerCase())) {
    return String(fallbackDomain || '').trim().toLowerCase()
  }
  return ''
}

function buildViewSnapshotId(timestamp) {
  const latestEntry = filteredTimeline.value[0]
  const domainKey = String(activeFilter.value || 'all').slice(0, 4).toUpperCase()
  const severityKey = String(activeSeverity.value || 'all').slice(0, 4).toUpperCase()
  const eventKey = String(latestEntry?.title || 'timeline')
    .replace(/\s+/g, '')
    .slice(0, 8)
    .toUpperCase()
  const timeKey = String(timestamp || '')
    .replace(/[-:TZ.]/g, '')
    .slice(0, 12)
  return `${domainKey}-${severityKey}-${eventKey || 'TIMELINE'}-${timeKey || 'NA'}`
}

function scheduleCopiedViewReset() {
  if (copiedViewResetTimer) {
    clearTimeout(copiedViewResetTimer)
    copiedViewResetTimer = null
  }
  copiedViewResetTimer = setTimeout(() => {
    copiedViewLink.value = false
    copiedViewResetTimer = null
  }, 1500)
}

function syncFilterToRoute(nextFilter) {
  const currentFilter = String(route.query.governance_filter || 'all').trim() || 'all'
  if (currentFilter === nextFilter) {
    return
  }
  const nextQuery = {
    ...route.query,
  }
  if (!nextFilter || nextFilter === 'all') {
    delete nextQuery.governance_filter
  } else {
    nextQuery.governance_filter = nextFilter
  }
  router.replace({ query: nextQuery }).catch(() => {})
}

function syncSeverityToRoute(nextSeverity) {
  const currentSeverity = String(route.query.governance_severity || 'all').trim() || 'all'
  if (currentSeverity === nextSeverity) {
    return
  }
  const nextQuery = {
    ...route.query,
  }
  if (!nextSeverity || nextSeverity === 'all') {
    delete nextQuery.governance_severity
  } else {
    nextQuery.governance_severity = nextSeverity
  }
  router.replace({ query: nextQuery }).catch(() => {})
}

function syncSnapshotToRoute(nextSnapshotId) {
  const currentSnapshot = String(route.query.governance_snapshot || '').trim()
  if (currentSnapshot === String(nextSnapshotId || '').trim()) {
    return
  }
  const nextQuery = {
    ...route.query,
  }
  if (!nextSnapshotId) {
    delete nextQuery.governance_snapshot
  } else {
    nextQuery.governance_snapshot = nextSnapshotId
  }
  router.replace({ query: nextQuery }).catch(() => {})
}

function formatTraceSource(source) {
  const labelMap = {
    doctor: 'Doctor',
    scheduler: 'Scheduler',
    subagent: 'Subagent',
    permission: 'Permission',
    hook: 'Hook',
    tool: 'Tool',
    mcp: 'MCP',
    runtime: 'Runtime',
    policy: 'Policy',
    skill: 'Skill',
    agent: 'Agent',
  }
  return labelMap[source] || source || ''
}

function formatAuditTime(value) {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`
}

function formatSnapshotTime(value) {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return `${date.toLocaleDateString()} ${formatAuditTime(value)}`
}

watch(
  () => route.query.governance_filter,
  (value) => {
    const nextValue = String(value || 'all').trim() || 'all'
    activeFilter.value = timelineFilters.value.some(item => item.key === nextValue) ? nextValue : 'all'
  },
  { immediate: true }
)

watch(
  () => route.query.governance_severity,
  (value) => {
    const nextValue = String(value || 'all').trim() || 'all'
    activeSeverity.value = severityFilters.value.some(item => item.key === nextValue) ? nextValue : 'all'
  },
  { immediate: true }
)

watch(
  () => route.query.governance_snapshot,
  (value) => {
    activeSnapshotId.value = String(value || '').trim()
  },
  { immediate: true }
)

watch(activeFilter, (value) => {
  syncFilterToRoute(value)
})

watch(activeSeverity, (value) => {
  syncSeverityToRoute(value)
})

watch(activeSnapshotId, (value) => {
  syncSnapshotToRoute(value)
})

watch([timelineFilters, activeFilter], ([filters, currentFilter]) => {
  if (!filters.some(item => item.key === currentFilter)) {
    activeFilter.value = 'all'
  }
})

watch([combinedTimeline, activeSnapshotId], ([timeline, snapshotId]) => {
  if (!snapshotId) {
    return
  }
  if (!timeline.some(entry => entrySnapshotRef(entry)?.snapshot_id === snapshotId)) {
    activeSnapshotId.value = ''
  }
})

watch(
  [recommendedFocusSignature, () => route.query.governance_filter, () => route.query.governance_snapshot, activeFilter],
  ([signature, routeFilter, routeSnapshot, currentFilter]) => {
    if (!signature || routeFilter || routeSnapshot) {
      return
    }
    if (currentFilter !== 'all' || lastAutoFocusSignature.value === signature) {
      return
    }
    lastAutoFocusSignature.value = signature
    applyFilter(recommendedFocusFilter.value)
  },
  { immediate: true }
)

watch(currentConversationId, async (value, previous) => {
  if (value && value !== previous) {
    lastAutoFocusSignature.value = ''
    await loadTimeline()
  }
}, { immediate: false })

onMounted(loadTimeline)
onUnmounted(() => {
  if (copiedPayloadResetTimer) {
    clearTimeout(copiedPayloadResetTimer)
    copiedPayloadResetTimer = null
  }
  if (copiedSnapshotResetTimer) {
    clearTimeout(copiedSnapshotResetTimer)
    copiedSnapshotResetTimer = null
  }
  if (copiedCommandResetTimer) {
    clearTimeout(copiedCommandResetTimer)
    copiedCommandResetTimer = null
  }
  if (copiedViewResetTimer) {
    clearTimeout(copiedViewResetTimer)
    copiedViewResetTimer = null
  }
  recentCopiedCommandText.value = ''
})
</script>

<style scoped>
.governance-timeline-panel {
  width: 100%;
}

.section-head,
.card-head,
.timeline-top,
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

.summary-grid {
  display: grid;
  gap: var(--space-md);
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  margin-bottom: var(--space-lg);
}

.summary-card,
.panel-card,
.timeline-item {
  border: 1px solid var(--border-color);
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
}

.summary-card {
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.governance-overview-grid {
  margin-bottom: var(--space-lg);
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

.governance-command-notice {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
  padding: var(--space-sm) var(--space-md);
  border: 1px solid rgba(59, 130, 246, 0.24);
  border-radius: var(--radius-md);
  background: rgba(59, 130, 246, 0.08);
  color: var(--text-secondary);
  font-size: 0.84rem;
}

.governance-command-notice code {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.08);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.summary-label {
  font-size: 0.8rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
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

.filter-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.timeline-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.timeline-item {
  padding: var(--space-md);
  border-left: 3px solid rgba(148, 163, 184, 0.25);
}

.timeline-item.severity-warning {
  border-left-color: rgba(249, 115, 22, 0.45);
}

.timeline-item.severity-success {
  border-left-color: rgba(34, 197, 94, 0.45);
}

.timeline-badges {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.filter-chip,
.timeline-kind,
.timeline-source,
.timeline-event {
  font-size: 0.74rem;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
}

.timeline-event {
  color: var(--text-primary);
}

.filter-chip {
  border: 1px solid var(--border-color);
  cursor: pointer;
}

.filter-chip.active {
  color: var(--text-primary);
  border-color: var(--border-primary);
  background: rgba(15, 118, 110, 0.12);
}

.timeline-time {
  font-size: 0.72rem;
  color: var(--text-tertiary);
}

.timeline-content {
  margin-top: 6px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.timeline-detail {
  margin-top: 4px;
  color: var(--text-tertiary);
  font-size: 0.82rem;
  line-height: 1.5;
  white-space: pre-wrap;
}

.timeline-payload-summary {
  margin-top: 6px;
  color: var(--text-secondary);
  font-size: 0.78rem;
  line-height: 1.5;
}

.timeline-snapshot-ref {
  margin-top: 6px;
  color: var(--text-tertiary);
  font-size: 0.76rem;
  line-height: 1.5;
}

.timeline-payload-actions {
  margin-top: 8px;
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

.timeline-payload-json {
  margin-top: 8px;
  padding: var(--space-sm);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-secondary);
  overflow-x: auto;
  font-size: 0.78rem;
  line-height: 1.5;
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
