<template>
  <div class="provider-card">
    <div class="provider-title-row">
      <strong>{{ adapter.display_name || adapter.adapter_id }}</strong>
      <span class="status-badge" :class="{ online: adapter.status === 'healthy', offline: adapter.status !== 'healthy' }">
        {{ adapter.status || 'unknown' }}
      </span>
    </div>
    <p class="provider-meta">
      <code>{{ adapter.adapter_id }}</code>
      <span>{{ adapter.adapter_type || '-' }}</span>
    </p>
    <p class="provider-endpoint">{{ adapter.detail || '-' }}</p>
    <div class="catalog-tags">
      <span class="capability-pill">config: {{ formatConfigurationStatusTag(adapter.configuration_status) }}</span>
      <span class="capability-pill">mode: {{ formatExecutionModeTag(adapter.execution_mode) }}</span>
      <span class="capability-pill">pkg: {{ formatPackageStateTag(adapter.package_installed) }}</span>
      <span class="capability-pill">runtime: {{ formatRuntimeEnabledTag(adapter.runtime_enabled) }}</span>
    </div>
    <div v-if="(adapter.required_packages || []).length" class="catalog-tags">
      <span
        v-for="packageName in adapter.required_packages || []"
        :key="`${adapter.adapter_id}-pkg-${packageName}`"
        class="capability-pill"
      >
        依赖包: {{ packageName }}
      </span>
    </div>
    <div v-if="(adapter.missing_packages || []).length" class="catalog-tags">
      <span
        v-for="packageName in adapter.missing_packages || []"
        :key="`${adapter.adapter_id}-missing-pkg-${packageName}`"
        class="capability-pill"
      >
        缺失依赖包: {{ packageName }}
      </span>
    </div>
    <div v-if="(adapter.required_env || []).length" class="catalog-tags">
      <span
        v-for="envName in adapter.required_env || []"
        :key="`${adapter.adapter_id}-${envName}`"
        class="capability-pill"
      >
        环境变量: {{ envName }}
      </span>
    </div>
    <div v-if="(adapter.missing_env || []).length" class="catalog-tags">
      <span
        v-for="envName in adapter.missing_env || []"
        :key="`${adapter.adapter_id}-missing-${envName}`"
        class="capability-pill"
      >
        缺失环境变量: {{ envName }}
      </span>
    </div>
    <p v-if="adapter.execution_block_reason" class="provider-endpoint adapter-block-reason">
      阻塞原因: {{ formatExecutionBlockReason(adapter.execution_block_reason) }}
    </p>
    <div v-if="canRunAdapterPrecheck(adapter)" class="adapter-pilot-actions">
      <button
        class="secondary-btn"
        :disabled="adapterPrecheckRunning"
        @click="$emit('run-precheck', adapter)"
      >
        {{ adapterPrecheckRunning ? '预检中...' : '运行预检' }}
      </button>
      <small class="summary-note">
        {{ formatAdapterPrecheckHint(adapter) }}
      </small>
    </div>
    <AdapterPilotResultCard
      v-if="showPrecheckResult"
      :result="adapterPrecheckResult"
      variant="precheck"
      :copied-command-text="copiedCommandText"
      @open-snapshot="$emit('open-snapshot', $event)"
      @copy-command="$emit('copy-command', $event)"
    />
    <div v-if="canRunAdapterExternalPilot(adapter)" class="adapter-pilot-actions">
      <button
        class="secondary-btn"
        :disabled="adapterExternalPilotRunning"
        @click="$emit('run-external-pilot', adapter)"
      >
        {{ adapterExternalPilotRunning ? 'External Pilot 运行中...' : '运行 External Pilot' }}
      </button>
      <small class="summary-note">
        调用 LangGraph 外部执行骨架，验证 request / stream / output / trace 链路。
      </small>
    </div>
    <AdapterPilotResultCard
      v-if="showExternalPilotResult"
      :result="adapterExternalPilotResult"
      variant="external"
      :copied-command-text="copiedCommandText"
      @open-snapshot="$emit('open-snapshot', $event)"
      @copy-command="$emit('copy-command', $event)"
    />
    <div v-if="canRunAdapterPilot(adapter)" class="adapter-pilot-actions">
      <button
        class="secondary-btn"
        :disabled="adapterPilotRunning"
        @click="$emit('run-pilot', adapter)"
      >
        {{ adapterPilotRunning ? 'Pilot 运行中...' : '运行 Pilot' }}
      </button>
      <small class="summary-note">调用本地 fake adapter，验证 trace / audit / output 闭环。</small>
    </div>
    <AdapterPilotResultCard
      v-if="showPilotResult"
      :result="adapterPilotResult"
      variant="local"
      :copied-command-text="copiedCommandText"
      @open-snapshot="$emit('open-snapshot', $event)"
      @copy-command="$emit('copy-command', $event)"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AdapterPilotResultCard from './AdapterPilotResultCard.vue'

const props = defineProps({
  adapter: {
    type: Object,
    required: true,
  },
  adapterPrecheckRunning: {
    type: Boolean,
    default: false,
  },
  adapterExternalPilotRunning: {
    type: Boolean,
    default: false,
  },
  adapterPilotRunning: {
    type: Boolean,
    default: false,
  },
  adapterPrecheckResult: {
    type: Object,
    default: null,
  },
  adapterExternalPilotResult: {
    type: Object,
    default: null,
  },
  adapterPilotResult: {
    type: Object,
    default: null,
  },
  copiedCommandText: {
    type: String,
    default: '',
  },
})

defineEmits([
  'run-precheck',
  'run-external-pilot',
  'run-pilot',
  'open-snapshot',
  'copy-command',
])

const showPrecheckResult = computed(() => isResultForCurrentAdapter(props.adapterPrecheckResult))
const showExternalPilotResult = computed(() => isResultForCurrentAdapter(props.adapterExternalPilotResult))
const showPilotResult = computed(() => isResultForCurrentAdapter(props.adapterPilotResult))

function isResultForCurrentAdapter(result) {
  return Boolean(result && result.adapter_id === props.adapter.adapter_id)
}

function normalizeContractObject(value) {
  return value && typeof value === 'object' ? value : {}
}

function canRunAdapterPilot(adapter) {
  return adapter?.adapter_id === 'local_fake_framework' && adapter?.status === 'healthy'
}

function canRunAdapterPrecheck(adapter) {
  return adapter?.adapter_type === 'agent_framework' && adapter?.adapter_id !== 'local_fake_framework'
}

function canRunAdapterExternalPilot(adapter) {
  return adapter?.adapter_id === 'langgraph_draft'
    && adapter?.status === 'healthy'
    && adapter?.configuration_status === 'ready'
    && adapter?.package_installed !== false
    && adapter?.runtime_enabled !== false
}

function formatConfigurationStatusLabel(value) {
  const normalized = String(value || '').trim()
  const labelMap = {
    ready: '已就绪',
    missing_package: '缺包',
    missing_env: '缺环境变量',
    runtime_disabled: '运行时开关未启用',
  }
  return labelMap[normalized] || normalized || 'unknown'
}

function formatConfigurationStatusTag(value) {
  return formatConfigurationStatusLabel(value)
}

function formatExecutionModeLabel(value) {
  const normalized = String(value || '').trim()
  const labelMap = {
    internal_registry: '内部注册表',
    internal_runtime: '内部运行时',
    draft_external_runtime: '外部草稿运行时',
    local_fake_pilot: '本地假运行 Pilot',
    placeholder: '占位模式',
  }
  return labelMap[normalized] || normalized || 'unknown'
}

function formatExecutionModeTag(value) {
  return formatExecutionModeLabel(value)
}

function formatPackageStateTag(value) {
  return value ? '已安装' : '缺失'
}

function formatRuntimeEnabledTag(value) {
  return value ? '已启用' : '未启用'
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

function formatAdapterPrecheckHint(adapter) {
  const payload = normalizeContractObject(adapter)
  const configurationStatus = String(payload.configuration_status || '').trim()
  if (configurationStatus === 'missing_package') {
    return '当前缺包，建议先安装依赖，再执行预检确认 env / runtime 开关状态。'
  }
  if (configurationStatus === 'missing_env') {
    return '当前缺环境变量，建议先补齐配置，再执行预检确认 readiness。'
  }
  if (configurationStatus === 'runtime_disabled') {
    return '当前运行时执行开关未启用，可先执行预检确认配置是否已就绪。'
  }
  if (configurationStatus === 'ready') {
    return '当前已就绪，可执行预检确认 readiness，不进入真实执行链。'
  }
  const statusLabel = formatConfigurationStatusLabel(configurationStatus)
  if (statusLabel && statusLabel !== 'unknown') {
    return `当前${statusLabel}，可先执行预检确认 package / env / runtime 开关状态。`
  }
  return '只校验 package / env / runtime 开关，不进入真实执行链。'
}
</script>

<style scoped>
.provider-card {
  border: 1px solid var(--border-color);
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
}

.provider-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
}

.provider-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-top: var(--space-xs);
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.provider-endpoint {
  margin: var(--space-sm) 0;
  color: var(--text-tertiary);
  word-break: break-all;
  font-size: 0.875rem;
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

.status-badge {
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 0.75rem;
  border: 1px solid var(--border-color);
}

.status-badge.online {
  background: rgba(34, 197, 94, 0.14);
  color: #15803d;
}

.status-badge.offline {
  background: rgba(245, 158, 11, 0.14);
  color: #b45309;
}

.secondary-btn {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-color);
  background: var(--bg-elevated);
  color: var(--text-primary);
  border-radius: var(--radius-md);
  cursor: pointer;
}

.summary-note {
  color: var(--text-tertiary);
  line-height: 1.4;
}

.adapter-pilot-actions {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  margin-top: var(--space-sm);
}

.adapter-block-reason {
  margin-top: var(--space-sm);
}
</style>
