<template>
  <div
    v-if="failure"
    class="contract-block runtime-detail-block adapter-pilot-result"
  >
    <h4>{{ failureHeading }}</h4>
    <div class="catalog-tags remediation-status-tags">
      <span class="capability-pill">
        错误: {{ errorTag }}
      </span>
    </div>
    <ul>
      <li><code>error_type</code>: {{ failure.error_type || '-' }}</li>
      <li><code>snapshot_id</code>: {{ failure.snapshot_id || '-' }}</li>
      <li><code>失败总数</code>: {{ failureCount }}</li>
      <li><code>统计窗口</code>: {{ failureWindow }}</li>
      <li><code>样本数</code>: {{ failureSampleSize }}</li>
      <li><code>错误分布</code>: {{ failureDistribution }}</li>
      <li><code>错误详情</code>: {{ errorDetail }}</li>
    </ul>
    <div
      v-if="distributionEntries.length"
      class="catalog-tags remediation-status-tags"
    >
      <button
        v-for="entry in distributionEntries"
        :key="`failure-dist-${entry.errorType}`"
        type="button"
        class="secondary-btn inline-filter-btn"
        :class="{ active: entry.errorType === activeErrorType }"
        @click="$emit('open-failure-type', entry.errorType)"
      >
        {{ entry.label }} {{ entry.count }}
      </button>
    </div>
    <p class="provider-meta adapter-result-meta">{{ identityLine }}</p>
    <button
      v-if="failure.snapshot_id"
      class="secondary-btn recent-copy-btn"
      @click="$emit('open-snapshot', failure.snapshot_id)"
    >
      查看时间线
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  failure: {
    type: Object,
    default: null,
  },
  counts: {
    type: Object,
    default: null,
  },
  activeErrorType: {
    type: String,
    default: '',
  },
})

defineEmits(['open-snapshot', 'open-failure-type'])

const failureHeading = computed(() => {
  const identity = getFrameworkAdapterIdentity(props.failure)
  return ['最近一次', identity.displayName, 'External Pilot 失败'].filter(Boolean).join(' ')
})

const errorTag = computed(() => formatAdapterExternalPilotErrorTag(props.failure))
const errorDetail = computed(() => formatAdapterExternalPilotErrorDetail(props.failure))
const identityLine = computed(() => formatFrameworkAdapterIdentityLine(props.failure))
const failureCount = computed(() => formatAdapterExternalPilotFailureCount(props.counts))
const failureWindow = computed(() => formatAdapterExternalPilotFailureWindow(props.counts))
const failureSampleSize = computed(() => formatAdapterExternalPilotFailureSampleSize(props.counts))
const failureDistribution = computed(() => formatAdapterExternalPilotFailureDistribution(props.counts))
const distributionEntries = computed(() => buildAdapterExternalPilotFailureDistributionEntries(props.counts))

function normalizeContractObject(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return {}
  }
  return value
}

function formatAdapterExternalPilotErrorLabel(errorType) {
  const normalized = String(errorType || '').trim()
  const labelMap = {
    configuration_error: '配置错误',
    connectivity_error: '连通性错误',
    authentication_error: '鉴权错误',
    protocol_error: '协议错误',
    upstream_runtime_error: '上游运行时错误',
    request_failed: '请求失败'
  }
  return labelMap[normalized] || normalized || ''
}

function formatAdapterExternalPilotErrorTag(result) {
  const payload = normalizeContractObject(result)
  const errorType = String(payload.error_type || '').trim()
  if (!errorType) {
    return ''
  }
  const label = formatAdapterExternalPilotErrorLabel(errorType)
  if (label === errorType) {
    return label
  }
  return `${label} (${errorType})`
}

function formatAdapterExternalPilotErrorDetail(result) {
  const payload = normalizeContractObject(result)
  return String(payload.error_detail || payload.detail || '').trim() || '-'
}

function getFrameworkAdapterIdentity(result) {
  const payload = normalizeContractObject(result)
  const frameworkName = String(payload.framework_name || payload.display_name || '').trim()
  const adapterId = String(payload.adapter_id || '').trim()
  return {
    frameworkName,
    adapterId,
    displayName: frameworkName || adapterId || 'Framework Adapter'
  }
}

function formatFrameworkAdapterIdentityLine(result) {
  const identity = getFrameworkAdapterIdentity(result)
  if (identity.frameworkName && identity.adapterId) {
    return `adapter_id: ${identity.adapterId}`
  }
  if (identity.adapterId) {
    return `adapter_id: ${identity.adapterId}`
  }
  if (identity.frameworkName) {
    return `framework: ${identity.frameworkName}`
  }
  return ''
}

function formatAdapterExternalPilotFailureCount(value) {
  const counts = normalizeContractObject(value)
  const total = Number(counts.total || 0)
  return Number.isFinite(total) && total > 0 ? String(total) : '-'
}

function formatAdapterExternalPilotFailureWindow(value) {
  const counts = normalizeContractObject(value)
  const windowScope = String(counts.window_scope || '').trim()
  const labelMap = {
    recent_plan_items: '最近 PlanItem',
  }
  return labelMap[windowScope] || windowScope || '-'
}

function formatAdapterExternalPilotFailureSampleSize(value) {
  const counts = normalizeContractObject(value)
  const sampleSize = Number(counts.sample_size || 0)
  return Number.isFinite(sampleSize) && sampleSize > 0 ? String(sampleSize) : '-'
}

function formatAdapterExternalPilotFailureDistribution(value) {
  const entries = buildAdapterExternalPilotFailureDistributionEntries(value)
    .map(entry => `${entry.label} ${entry.count}`)
  return entries.length ? entries.join(' · ') : '-'
}

function buildAdapterExternalPilotFailureDistributionEntries(value) {
  const counts = normalizeContractObject(value)
  const byErrorType = normalizeContractObject(counts.by_error_type)
  return Object.entries(byErrorType)
    .map(([errorType, rawCount]) => {
      const count = Number(rawCount || 0)
      const label = formatAdapterExternalPilotErrorLabel(errorType)
      if (!label || !Number.isFinite(count) || count <= 0) {
        return null
      }
      return {
        errorType: String(errorType || '').trim(),
        label,
        count,
      }
    })
    .filter(Boolean)
}
</script>

<style scoped>
.contract-block {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
  padding: var(--space-md);
}

.runtime-detail-block {
  margin-top: var(--space-lg);
}

.adapter-pilot-result {
  margin-top: var(--space-sm);
}

.contract-block h4 {
  margin-bottom: var(--space-sm);
  color: var(--text-primary);
}

.contract-block ul {
  margin: 0;
  padding-left: 1rem;
  color: var(--text-secondary);
}

.contract-block li + li {
  margin-top: 6px;
}

.catalog-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  margin-top: var(--space-sm);
}

.capability-pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(59, 130, 246, 0.12);
  color: var(--text-secondary);
  font-size: 0.8rem;
}

.provider-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-top: var(--space-xs);
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.secondary-btn {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-color);
  background: var(--bg-elevated);
  color: var(--text-primary);
  border-radius: var(--radius-md);
  cursor: pointer;
}

.inline-filter-btn.active {
  border-color: rgba(37, 99, 235, 0.45);
  background: rgba(37, 99, 235, 0.12);
  color: #1d4ed8;
}

.recent-copy-btn {
  flex-shrink: 0;
}
</style>
