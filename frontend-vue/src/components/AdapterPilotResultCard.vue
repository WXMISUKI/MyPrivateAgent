<template>
  <div
    v-if="result"
    class="contract-block runtime-detail-block adapter-pilot-result"
  >
    <h4>{{ heading }}</h4>
    <div class="catalog-tags remediation-status-tags">
      <span class="capability-pill">
        状态: {{ statusTag }}
      </span>
      <span class="capability-pill">
        {{ secondaryLabel }}: {{ secondaryTag }}
      </span>
    </div>
    <ul>
      <template v-if="variant === 'precheck'">
        <li><code>ready</code>: {{ result.ready ? 'true' : 'false' }}</li>
        <li><code>configuration_status</code>: {{ formatConfigurationStatusDetail(result.configuration_status) }}</li>
        <li><code>execution_mode</code>: {{ formatExecutionModeDetail(result.execution_mode) }}</li>
        <li><code>snapshot_id</code>: {{ result.snapshot_id || '-' }}</li>
        <li>{{ formatExecutionBlockReasonDetail(result.execution_block_reason || result.detail) }}</li>
      </template>
      <template v-else-if="variant === 'external'">
        <li><code>adapter_id</code>: {{ result.adapter_id || '-' }}</li>
        <li><code>status</code>: {{ result.status || '-' }}</li>
        <li><code>snapshot_id</code>: {{ result.snapshot_id || '-' }}</li>
        <li v-if="result.error_type"><code>错误</code>: {{ formatAdapterExternalPilotErrorTag(result) }}</li>
        <li v-if="result.error_detail"><code>错误详情</code>: {{ formatAdapterExternalPilotErrorDetail(result) }}</li>
        <li v-else>{{ result.final_output || '-' }}</li>
      </template>
      <template v-else>
        <li><code>run_id</code>: {{ result.run_id || '-' }}</li>
        <li><code>event_count</code>: {{ result.event_count || 0 }}</li>
        <li><code>snapshot_id</code>: {{ result.snapshot_id || '-' }}</li>
        <li>{{ result.final_output || '-' }}</li>
      </template>
    </ul>
    <p class="provider-meta adapter-result-meta">{{ identityLine }}</p>
    <button
      v-if="result.snapshot_id"
      class="secondary-btn recent-copy-btn"
      @click="$emit('open-snapshot', result.snapshot_id)"
    >
      查看时间线
    </button>
    <button
      v-if="copyCommand"
      class="secondary-btn recent-copy-btn"
      @click="$emit('copy-command', copyCommand)"
    >
      {{ copiedCommandText === copyCommand ? '已复制命令' : copyLabel }}
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  result: {
    type: Object,
    default: null,
  },
  variant: {
    type: String,
    default: 'local',
    validator: value => ['precheck', 'external', 'local'].includes(value),
  },
  copiedCommandText: {
    type: String,
    default: '',
  },
})

defineEmits(['open-snapshot', 'copy-command'])

const heading = computed(() => {
  const suffixMap = {
    precheck: 'Precheck',
    external: 'External Pilot',
    local: 'Pilot',
  }
  return formatFrameworkAdapterResultHeading(props.result, suffixMap[props.variant] || 'Pilot')
})

const statusTag = computed(() => {
  if (props.variant === 'precheck') {
    return formatAdapterPrecheckStatusTag(props.result?.configuration_status)
  }
  if (props.variant === 'external') {
    return formatAdapterExternalPilotStatusTag(props.result)
  }
  return formatAdapterPilotStatusTag(props.result)
})

const secondaryLabel = computed(() => props.variant === 'precheck' ? '就绪度' : '输出')
const secondaryTag = computed(() => {
  if (props.variant === 'precheck') {
    return props.result?.ready ? '已就绪' : '未就绪'
  }
  if (props.variant === 'external') {
    return formatAdapterExternalPilotOutputTag(props.result?.final_output)
  }
  return formatAdapterPilotOutputTag(props.result?.final_output)
})

const copyCommand = computed(() => {
  if (props.variant === 'precheck') {
    return String(props.result?.remediation_command || '').trim()
  }
  return String(props.result?.snapshot_command || '').trim()
})

const copyLabel = computed(() => props.variant === 'precheck' ? '复制修复命令' : '复制快照命令')
const identityLine = computed(() => formatFrameworkAdapterIdentityLine(props.result))

function normalizeContractObject(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return {}
  }
  return value
}

function formatConfigurationStatusLabel(value) {
  const normalized = String(value || '').trim()
  const labelMap = {
    ready: '就绪',
    not_configured: '未配置',
    missing_package: '缺包',
    missing_env: '缺环境变量',
    runtime_disabled: '运行时未启用',
    unavailable: '不可用',
    error: '异常',
  }
  return labelMap[normalized] || normalized || 'unknown'
}

function formatConfigurationStatusDetail(value) {
  const normalized = String(value || '').trim()
  const label = formatConfigurationStatusLabel(normalized)
  if (!normalized || label === normalized) {
    return label
  }
  return `${label} (${normalized})`
}

function formatExecutionModeLabel(value) {
  const normalized = String(value || '').trim()
  const labelMap = {
    internal_registry: '内置注册表',
    internal_runtime: '内置运行时',
    placeholder: '占位',
    local_fake_pilot: '本地 Pilot',
    draft_external_runtime: '外部草稿运行时',
  }
  return labelMap[normalized] || normalized || 'unknown'
}

function formatExecutionModeDetail(value) {
  const normalized = String(value || '').trim()
  const label = formatExecutionModeLabel(normalized)
  if (!normalized || label === normalized) {
    return label
  }
  return `${label} (${normalized})`
}

function formatExecutionBlockReasonLabel(value) {
  const normalized = String(value || '').trim()
  if (!normalized) {
    return ''
  }
  if (normalized === 'missing required package: langgraph') {
    return '缺少必需依赖包'
  }
  if (normalized.startsWith('missing required env:')) {
    return '缺少必需环境变量'
  }
  if (normalized === 'runtime execution is not enabled') {
    return '运行时执行开关未启用'
  }
  if (normalized.includes('runtime execution is not enabled')) {
    return '运行时执行未启用'
  }
  return normalized
}

function formatExecutionBlockReason(value) {
  const normalized = String(value || '').trim()
  if (!normalized) {
    return ''
  }
  const label = formatExecutionBlockReasonLabel(normalized)
  if (label === normalized) {
    return label
  }
  return `${label} (${normalized})`
}

function formatExecutionBlockReasonDetail(value) {
  return formatExecutionBlockReason(value) || '-'
}

function formatAdapterPrecheckStatusTag(value) {
  return formatConfigurationStatusLabel(value) || 'unknown'
}

function formatAdapterPilotStatusTag(result) {
  const payload = normalizeContractObject(result)
  return payload.run_id ? '已完成' : 'unknown'
}

function formatAdapterPilotOutputTag(value) {
  return String(value || '').trim() ? '已产生' : '无内容'
}

function formatAdapterExternalPilotStatusTag(result) {
  const status = String(normalizeContractObject(result).status || '').trim()
  const labelMap = {
    ok: '已完成',
    success: '已完成',
    completed: '已完成',
    failed: '失败',
    error: '失败',
  }
  return labelMap[status] || status || 'unknown'
}

function formatAdapterExternalPilotOutputTag(value) {
  return String(value || '').trim() ? '已产生' : '无内容'
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

function formatFrameworkAdapterResultHeading(result, suffix) {
  const identity = getFrameworkAdapterIdentity(result)
  return ['最近', identity.displayName, String(suffix || '').trim()].filter(Boolean).join(' ')
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

.recent-copy-btn {
  flex-shrink: 0;
}
</style>
