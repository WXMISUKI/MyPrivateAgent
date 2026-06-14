<template>
  <section class="settings-section">
    <div class="section-header">
      <div>
        <h2>外接 Provider 接入</h2>
        <p class="section-desc">查看已知外接项目的接入清单与当前管理面状态。</p>
      </div>
      <button class="action-btn" type="button" @click="loadProviderOnboarding" :disabled="loading">
        {{ loading ? '刷新中...' : '刷新' }}
      </button>
    </div>

    <div v-if="loadError" class="test-result error">{{ loadError }}</div>
    <div v-if="loading && !entries.length" class="loading-hint">加载中...</div>

    <div v-for="entry in entries" :key="entry.onboarding_id" class="provider-card">
      <div class="provider-header">
        <span class="provider-name">{{ entry.provider_id }}</span>
        <span class="provider-badge" :class="statusClass(liveProvider(entry)?.overall_status)">
          {{ liveProvider(entry)?.overall_status || 'not_registered' }}
        </span>
        <span class="source-tag">{{ entry.kind }}</span>
      </div>

      <div class="provider-grid">
        <div class="meta-block">
          <span class="meta-label">Default URL</span>
          <span class="mono-value">{{ entry.default_base_url || '-' }}</span>
        </div>
        <div class="meta-block">
          <span class="meta-label">Env</span>
          <span class="mono-value">{{ entry.env?.enable_var || '-' }}</span>
          <span class="mono-value">{{ entry.env?.base_url_var || '-' }}</span>
        </div>
        <div class="meta-block">
          <span class="meta-label">Capabilities</span>
          <span class="tag-list">
            <span v-for="capabilityId in entry.capability_ids || []" :key="capabilityId" class="source-tag">
              {{ capabilityId }}
            </span>
          </span>
        </div>
      </div>

      <div class="readiness-row">
        <span class="meta-label">Readiness</span>
        <span class="provider-badge" :class="readinessClass(readinessFor(entry)?.configuration_status)">
          {{ readinessFor(entry)?.configuration_status || 'unknown' }}
        </span>
        <span class="field-hint">{{ readinessFor(entry)?.recommended_action || 'inspect_provider_readiness_before_use' }}</span>
      </div>

      <div class="check-list" v-if="readinessFor(entry)?.checks?.length">
        <div v-for="check in readinessFor(entry).checks" :key="check.id + (check.env_var || '')" class="check-row">
          <span>{{ check.id }}</span>
          <span class="provider-badge" :class="checkClass(check.status)">{{ check.status }}</span>
          <span class="field-hint">{{ check.env_var || check.path || check.reason || '' }}</span>
        </div>
      </div>

      <div class="live-summary" v-if="liveProvider(entry)">
        <div class="summary-line">
          <span>configured: {{ liveProvider(entry).configured ? 'yes' : 'no' }}</span>
          <span>enabled: {{ liveProvider(entry).enabled ? 'yes' : 'no' }}</span>
          <span v-if="liveProvider(entry).base_url" class="mono-value">{{ liveProvider(entry).base_url }}</span>
        </div>
        <div class="check-list" v-if="liveProvider(entry).capabilities?.length">
          <div v-for="capability in liveProvider(entry).capabilities" :key="capability.capability_id" class="check-row">
            <span>{{ capability.capability_id }}</span>
            <span class="provider-badge" :class="statusClass(capability.status)">{{ capability.status || 'unknown' }}</span>
            <span class="field-hint">{{ capability.invocation_boundary || 'explicit_only' }}</span>
          </div>
        </div>
      </div>
      <div v-else class="test-result warning">当前 service-provider 管理列表中未注册该 Provider。</div>

      <div class="path-list">
        <span v-if="entry.management?.service_provider_detail" class="mono-value">
          {{ entry.management.service_provider_detail }}
        </span>
        <span v-if="entry.management?.service_provider_evidence_preview" class="mono-value">
          {{ entry.management.service_provider_evidence_preview }}
        </span>
        <span v-for="doc in entry.docs || []" :key="doc" class="field-hint">{{ doc }}</span>
      </div>

      <details v-if="boundaryEntries(entry).length || liveBoundaryEntries(entry).length" class="boundary-details">
        <summary>Boundaries</summary>
        <div class="boundary-list">
          <span v-for="item in boundaryEntries(entry)" :key="'entry-' + item.key" class="field-hint">
            {{ item.key }}: {{ item.value }}
          </span>
          <span v-for="item in liveBoundaryEntries(entry)" :key="'live-' + item.key" class="field-hint">
            {{ item.key }}: {{ item.value }}
          </span>
        </div>
      </details>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { providerOnboardingApi, serviceProviderApi } from '../api'

const entries = ref([])
const readinessById = ref({})
const serviceProviders = ref([])
const loading = ref(false)
const loadError = ref('')

const serviceProviderById = computed(() => {
  const index = {}
  for (const provider of serviceProviders.value) {
    if (provider?.provider_id) {
      index[provider.provider_id] = provider
    }
  }
  return index
})

onMounted(() => {
  loadProviderOnboarding()
})

async function loadProviderOnboarding() {
  loading.value = true
  loadError.value = ''
  try {
    const [onboardingResponse, providersResponse] = await Promise.all([
      providerOnboardingApi.list(),
      serviceProviderApi.list()
    ])
    entries.value = Array.isArray(onboardingResponse.data?.entries)
      ? onboardingResponse.data.entries
      : []
    serviceProviders.value = Array.isArray(providersResponse.data?.providers)
      ? providersResponse.data.providers
      : []
    await loadReadiness(entries.value)
  } catch (error) {
    loadError.value = error.response?.data?.error?.message || error.message || 'Provider 接入信息加载失败'
  } finally {
    loading.value = false
  }
}

async function loadReadiness(items) {
  const pairs = await Promise.all(items.map(async entry => {
    try {
      const response = await providerOnboardingApi.readiness(entry.onboarding_id)
      return [entry.onboarding_id, response.data]
    } catch (error) {
      return [entry.onboarding_id, {
        onboarding_id: entry.onboarding_id,
        configuration_status: 'unknown',
        recommended_action: 'inspect_provider_readiness_before_use',
        checks: [{
          id: 'readiness_request',
          status: 'unknown',
          reason: error.message || 'readiness request failed'
        }]
      }]
    }
  }))
  readinessById.value = Object.fromEntries(pairs)
}

function readinessFor(entry) {
  return readinessById.value[entry.onboarding_id] || null
}

function liveProvider(entry) {
  return serviceProviderById.value[entry.provider_id] || null
}

function boundaryEntries(entry) {
  return objectEntries(entry.boundaries)
}

function liveBoundaryEntries(entry) {
  return objectEntries(liveProvider(entry)?.boundaries)
}

function objectEntries(value) {
  if (!value || typeof value !== 'object') return []
  return Object.entries(value).map(([key, itemValue]) => ({ key, value: itemValue }))
}

function readinessClass(status) {
  if (status === 'configured') return 'configured'
  if (status === 'unconfigured') return 'unconfigured'
  return 'unknown'
}

function checkClass(status) {
  if (['present', 'probe_required', 'optional'].includes(status)) return 'configured'
  if (status === 'missing') return 'unconfigured'
  return 'unknown'
}

function statusClass(status) {
  if (status === 'ready') return 'configured'
  if (['unconfigured', 'disabled', 'gated', 'review', 'not_registered'].includes(status)) return 'unconfigured'
  if (['blocked', 'unreachable'].includes(status)) return 'error'
  return 'unknown'
}
</script>

<style scoped>
.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-md);
}

.section-desc,
.field-hint,
.loading-hint {
  color: var(--text-secondary);
  font-size: 0.8rem;
}

.section-desc {
  margin: 4px 0 var(--space-md);
}

.provider-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  margin-bottom: var(--space-md);
}

.provider-header,
.readiness-row,
.summary-line {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.provider-header {
  margin-bottom: var(--space-sm);
}

.provider-name {
  font-weight: 600;
}

.provider-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.meta-block,
.path-list,
.boundary-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-label {
  color: var(--text-tertiary);
  font-size: 0.75rem;
}

.mono-value {
  color: var(--text-secondary);
  font-family: monospace;
  font-size: 0.78rem;
  overflow-wrap: anywhere;
}

.tag-list {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.provider-badge,
.source-tag {
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.provider-badge.configured {
  color: #22c55e;
  background: rgba(34, 197, 94, 0.15);
}

.provider-badge.unconfigured {
  color: #eab308;
  background: rgba(234, 179, 8, 0.15);
}

.provider-badge.error {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.15);
}

.provider-badge.unknown,
.source-tag {
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
}

.check-list {
  margin-top: var(--space-sm);
  border-top: 1px solid var(--border-color);
}

.check-row {
  display: grid;
  grid-template-columns: minmax(110px, 1fr) auto minmax(160px, 2fr);
  gap: var(--space-sm);
  align-items: center;
  padding: 6px 0;
  font-size: 0.8rem;
  color: var(--text-primary);
}

.live-summary,
.path-list,
.boundary-details {
  margin-top: var(--space-sm);
}

.boundary-details > summary {
  cursor: pointer;
  color: var(--text-primary);
  font-size: 0.8rem;
}

.action-btn {
  padding: 6px 14px;
  font-size: 0.8rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  border: 1px solid var(--border-color);
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.action-btn:hover:not(:disabled) {
  border-color: var(--primary);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.test-result {
  font-size: 0.8rem;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-sm);
}

.test-result.error {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.test-result.warning {
  color: #eab308;
  background: rgba(234, 179, 8, 0.1);
}
</style>
