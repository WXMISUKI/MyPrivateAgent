<template>
  <section class="settings-section doctor-panel">
    <div class="section-head">
      <div>
        <h2>Doctor</h2>
        <p class="section-desc">直接运行框架诊断与治理门禁，不必离开工作台。</p>
      </div>
    </div>

    <div class="doctor-toolbar">
      <button class="secondary-btn" :disabled="loading" @click="runStartupDoctor">
        {{ loading && mode === 'startup' ? '执行中...' : '运行 Startup Doctor' }}
      </button>
      <button class="secondary-btn" :disabled="loading" @click="runGovernanceDoctor">
        {{ loading && mode === 'governance' ? '执行中...' : '运行 Governance Gate' }}
      </button>
    </div>

    <p v-if="error" class="inline-error">{{ error }}</p>

    <div v-if="latestSnapshotRef" class="panel-card snapshot-card">
      <div class="card-head">
        <h3>最近治理快照</h3>
        <button class="secondary-btn" @click="openSnapshotTimeline">查看时间线</button>
      </div>
      <div class="doctor-summary-grid">
        <div class="summary-card">
          <span class="summary-label">快照 ID</span>
          <strong>{{ latestSnapshotRef.snapshot_id }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">来源</span>
          <strong>{{ latestSnapshotRef.source || '-' }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">事件</span>
          <strong>{{ latestSnapshotRef.event_type || '-' }}</strong>
        </div>
      </div>
    </div>

    <div v-if="report" class="panel-card">
      <div class="card-head">
        <h3>最近一次诊断</h3>
        <span class="muted">scope: {{ report.scope || '-' }} · exit_code: {{ report.exit_code ?? '-' }}</span>
      </div>

      <div class="doctor-summary-grid">
        <div class="summary-card">
          <span class="summary-label">状态</span>
          <strong>{{ report.status || (report.gate_passed ? 'ok' : 'warn') }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">门禁</span>
          <strong>{{ report.gate_passed === undefined ? '-' : (report.gate_passed ? '通过' : '未通过') }}</strong>
        </div>
        <div v-if="report.score !== undefined" class="summary-card">
          <span class="summary-label">分数</span>
          <strong>{{ report.score }}</strong>
        </div>
        <div v-if="report.non_closed_action_count !== undefined" class="summary-card">
          <span class="summary-label">未闭环动作</span>
          <strong>{{ report.non_closed_action_count }}</strong>
        </div>
      </div>

      <div v-if="report.summary" class="doctor-json">
        <pre>{{ formatJson(report.summary) }}</pre>
      </div>

      <div v-if="report.escalation_recommendations?.length" class="doctor-list">
        <div class="list-title">升级建议</div>
        <div v-for="item in report.escalation_recommendations" :key="item.type" class="list-row doctor-row">
          <strong>{{ item.type }}</strong>
          <span>{{ item.message }}</span>
        </div>
      </div>

      <div v-if="report.pending_actions?.length" class="doctor-list">
        <div class="list-title">待整改动作</div>
        <div v-for="item in report.pending_actions.slice(0, 5)" :key="`${item.case_id}-${item.action_id}`" class="list-row doctor-row">
          <strong>{{ item.action_id }}</strong>
          <span>{{ item.reason }}</span>
        </div>
      </div>

      <details class="doctor-raw">
        <summary>查看完整结果 JSON</summary>
        <pre>{{ formatJson(report) }}</pre>
      </details>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { doctorApi } from '../api'
import { useConversationStore } from '../stores/conversation'
import { usePlannerStore } from '../stores/planner'

const router = useRouter()
const route = useRoute()
const conversationStore = useConversationStore()
const plannerStore = usePlannerStore()
const loading = ref(false)
const error = ref('')
const report = ref(null)
const mode = ref('startup')
const latestSnapshotRef = ref(null)
const currentConversationId = computed(() => {
  const id = Number(conversationStore.currentConversation?.id)
  return Number.isFinite(id) ? id : null
})

function formatJson(value) {
  return JSON.stringify(value || {}, null, 2)
}

function normalizeSnapshotRef(snapshotRef) {
  if (!snapshotRef || typeof snapshotRef !== 'object') {
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

function extractLatestSnapshotFromPlan() {
  const items = plannerStore.currentPlan?.items || []
  for (const item of items) {
    for (const entry of item.run_trace || []) {
      const snapshotRef = normalizeSnapshotRef(entry?.payload?.snapshot_ref)
      if (snapshotRef) {
        return snapshotRef
      }
    }
  }
  return null
}

function resolveLatestSnapshot(responseData) {
  return (
    normalizeSnapshotRef(responseData?.timeline_recording?.snapshot_ref) ||
    extractLatestSnapshotFromPlan()
  )
}

async function loadDoctor(params, targetMode) {
  loading.value = true
  error.value = ''
  mode.value = targetMode
  try {
    const requestParams = {
      ...params
    }
    if (currentConversationId.value !== null) {
      requestParams.conversation_id = currentConversationId.value
    }
    const response = await doctorApi.getReport(requestParams)
    report.value = response.data || null
    if (currentConversationId.value !== null) {
      try {
        await plannerStore.loadPlans({ conversationId: currentConversationId.value })
      } catch (refreshError) {
        console.warn('[DoctorPanel] 刷新 Planner 失败', refreshError)
      }
    }
    latestSnapshotRef.value = resolveLatestSnapshot(response.data || null)
  } catch (err) {
    latestSnapshotRef.value = null
    error.value = err?.response?.data?.detail || err?.message || 'Doctor 执行失败'
  } finally {
    loading.value = false
  }
}

function openSnapshotTimeline() {
  if (!latestSnapshotRef.value?.snapshot_id) {
    return
  }
  router.push(`/settings?tab=advanced&governance_snapshot=${encodeURIComponent(latestSnapshotRef.value.snapshot_id)}`)
}

async function runStartupDoctor() {
  await loadDoctor({}, 'startup')
}

async function runGovernanceDoctor() {
  await loadDoctor({
    capability_gaps: true,
    window_days: 14,
    limit: 200,
    max_open_actions: 10,
    max_long_blocked_actions: 0
  }, 'governance')
}

onMounted(async () => {
  const doctorMode = String(route.query.doctor || '').trim().toLowerCase()
  if (doctorMode === 'governance') {
    await runGovernanceDoctor()
    return
  }
  if (doctorMode === 'startup') {
    await runStartupDoctor()
  }
})
</script>
