<template>
  <section class="settings-section">
    <div class="section-header">
      <div>
        <h2>Provider Ops</h2>
        <p class="section-desc">查看 Provider 的只读运营姿态，不执行配置写入、路由切换或运行时推广。</p>
      </div>
      <button class="action-btn" type="button" @click="loadProviderOps" :disabled="loading">
        {{ loading ? '刷新中...' : '刷新' }}
      </button>
    </div>

    <div v-if="loadError" class="test-result error">{{ loadError }}</div>
    <div v-if="loading && !providers.length" class="loading-hint">加载中...</div>

    <div v-if="summary.total" class="ops-summary">
      <div class="summary-metric">
        <span class="metric-label">总 Provider</span>
        <span class="metric-value">{{ summary.total }}</span>
      </div>
      <div class="summary-metric">
        <span class="metric-label">Ready</span>
        <span class="metric-value status-ready">{{ summary.ready }}</span>
      </div>
      <div class="summary-metric">
        <span class="metric-label">Review</span>
        <span class="metric-value status-review">{{ summary.review }}</span>
      </div>
      <div class="summary-metric">
        <span class="metric-label">Blocked</span>
        <span class="metric-value status-blocked">{{ summary.blocked }}</span>
      </div>
      <div class="summary-metric">
        <span class="metric-label">Unconfigured</span>
        <span class="metric-value status-unconfigured">{{ summary.unconfigured }}</span>
      </div>
    </div>

    <div v-for="provider in providers" :key="provider.provider_id" class="provider-card">
      <div class="provider-header">
        <span class="provider-name">{{ provider.display_name || provider.provider_id }}</span>
        <span class="provider-badge" :class="statusClass(provider.overall_status)">
          {{ provider.overall_status || 'unknown' }}
        </span>
      </div>

      <div class="provider-grid">
        <div class="meta-block">
          <span class="meta-label">Credential</span>
          <span class="provider-badge" :class="statusClass(provider.credential_posture)">
            {{ provider.credential_posture }}
          </span>
        </div>
        <div class="meta-block">
          <span class="meta-label">Quota</span>
          <span class="provider-badge" :class="statusClass(provider.quota_posture)">
            {{ provider.quota_posture }}
          </span>
        </div>
        <div class="meta-block">
          <span class="meta-label">Rate Limit</span>
          <span class="provider-badge" :class="statusClass(provider.rate_limit_posture)">
            {{ provider.rate_limit_posture }}
          </span>
        </div>
        <div class="meta-block">
          <span class="meta-label">Cost</span>
          <span class="provider-badge" :class="statusClass(provider.cost_posture)">
            {{ provider.cost_posture }}
          </span>
        </div>
        <div class="meta-block">
          <span class="meta-label">SLA</span>
          <span class="provider-badge" :class="statusClass(provider.sla_posture)">
            {{ provider.sla_posture }}
          </span>
        </div>
        <div class="meta-block">
          <span class="meta-label">Fallback</span>
          <span class="provider-badge" :class="statusClass(provider.fallback_posture)">
            {{ provider.fallback_posture }}
          </span>
        </div>
      </div>

      <div class="ops-detail">
        <span class="field-hint">reason: {{ provider.reason || '-' }}</span>
        <span class="field-hint">next_action: {{ provider.next_action || '-' }}</span>
        <span class="mono-value" v-if="provider.base_url">{{ provider.base_url }}</span>
      </div>
    </div>

    <div v-if="!loading && !providers.length && !loadError" class="loading-hint">
      当前没有可展示的 Provider Ops 数据。
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { providerApi } from '../api'

const loading = ref(false)
const loadError = ref('')
const providers = ref([])
const summary = ref({
  total: 0,
  ready: 0,
  review: 0,
  blocked: 0,
  unconfigured: 0
})

onMounted(() => {
  loadProviderOps()
})

async function loadProviderOps() {
  loading.value = true
  loadError.value = ''
  try {
    const response = await providerApi.getProviderOps()
    providers.value = Array.isArray(response.data?.providers) ? response.data.providers : []
    summary.value = {
      total: Number(response.data?.summary?.total || 0),
      ready: Number(response.data?.summary?.ready || 0),
      review: Number(response.data?.summary?.review || 0),
      blocked: Number(response.data?.summary?.blocked || 0),
      unconfigured: Number(response.data?.summary?.unconfigured || 0)
    }
  } catch (error) {
    providers.value = []
    summary.value = { total: 0, ready: 0, review: 0, blocked: 0, unconfigured: 0 }
    loadError.value = error.response?.data?.error?.message || error.message || 'Provider Ops 加载失败'
  } finally {
    loading.value = false
  }
}

function statusClass(status) {
  const normalized = String(status || 'unknown').trim().toLowerCase()
  if (['ready', 'configured', 'not_required'].includes(normalized)) return 'configured'
  if (['review', 'unknown'].includes(normalized)) return 'unknown'
  if (['blocked', 'unconfigured'].includes(normalized)) return 'error'
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
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

.action-btn {
  padding: 0.5rem 0.85rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  background: var(--color-surface-elevated);
  color: var(--color-text-primary);
  cursor: pointer;
}

.ops-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.summary-metric,
.meta-block {
  padding: 0.75rem;
  border-radius: 12px;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.metric-label,
.meta-label {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
}

.metric-value {
  font-size: 1.1rem;
  font-weight: 700;
}

.provider-card {
  border: 1px solid var(--color-border);
  background: var(--color-surface-elevated);
  border-radius: 16px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.provider-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.9rem;
}

.provider-name {
  font-weight: 700;
}

.provider-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.75rem;
}

.provider-badge {
  width: fit-content;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
}

.configured,
.status-ready {
  background: rgba(44, 130, 87, 0.12);
  color: #2c8257;
}

.unknown,
.status-review {
  background: rgba(180, 132, 29, 0.14);
  color: #b4841d;
}

.error,
.status-blocked,
.status-unconfigured {
  background: rgba(184, 54, 54, 0.14);
  color: #b83636;
}

.ops-detail {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-top: 0.9rem;
}

.mono-value {
  font-family: 'Cascadia Code', 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  word-break: break-all;
}
</style>
