<template>
  <section class="settings-section runtime-panel">
    <div class="section-head">
      <div>
        <h2>运行时能力面</h2>
        <p class="section-desc">查看当前 demo 模式、provider、模型目录，以及框架当前可暴露的运行时表面。</p>
      </div>
      <button class="secondary-btn" :disabled="loading" @click="loadProfile">
        {{ loading ? '刷新中...' : '刷新运行时信息' }}
      </button>
    </div>

    <p v-if="error" class="inline-error">{{ error }}</p>

    <div v-if="profile" class="summary-grid">
      <div class="summary-card">
        <span class="summary-label">运行模式</span>
        <strong>{{ profile.agent_mode || 'general_demo' }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">鉴权模式</span>
        <strong>{{ profile.auth_mode || 'demo_guest' }}</strong>
        <small class="summary-note">{{ authModeDescription }}</small>
      </div>
      <div class="summary-card">
        <span class="summary-label">默认模型</span>
        <strong>{{ profile.default_model || '-' }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">Provider 数量</span>
        <strong>{{ providers.length }}</strong>
      </div>
    </div>

    <div v-if="capabilityContract" class="panel-card">
      <div class="card-head">
        <h3>主智能体能力合同</h3>
        <span class="muted">用于约束通用智能体的身份、执行原则与能力边界</span>
      </div>
      <p class="contract-summary">{{ capabilityContract.identity_summary }}</p>

      <div class="contract-grid">
        <div class="contract-block">
          <h4>执行原则</h4>
          <ul>
            <li v-for="item in capabilityContract.operating_principles || []" :key="item">{{ item }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>当前可用能力</h4>
          <ul>
            <li v-for="item in capabilityContract.available_capabilities || []" :key="item">{{ item }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>当前受限能力</h4>
          <ul>
            <li v-for="item in capabilityContract.limited_capabilities || []" :key="item">{{ item }}</li>
          </ul>
        </div>
      </div>
    </div>

    <div v-if="memoryContract" class="panel-card">
      <div class="card-head">
        <h3>分层记忆 / 指令系统</h3>
        <span class="muted">对齐成熟智能体的长期规则层，区分通用底座、项目规则和本地实验规则</span>
      </div>
      <div class="config-layer-grid">
        <div class="contract-block">
          <h4>启用状态</h4>
          <ul>
            <li><code>active</code>: {{ memoryContract.active ? '已启用' : '未启用' }}</li>
            <li><code>layer_order</code>: {{ (memoryContract.layer_order || []).join(', ') || '-' }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>已加载层</h4>
          <ul v-if="(memoryContract.loaded_layers || []).length">
            <li v-for="layer in memoryContract.loaded_layers || []" :key="`${layer.name}-${layer.path}`">
              <strong>{{ layer.name }}</strong>
              <span class="path-line">{{ layer.path }}</span>
            </li>
          </ul>
          <p v-else class="empty-hint">当前未检测到任何分层记忆文件，主智能体仅按内置身份与能力合同运行。</p>
        </div>
        <div class="contract-block">
          <h4>预留层</h4>
          <ul v-if="(memoryContract.missing_layers || []).length">
            <li v-for="layer in memoryContract.missing_layers || []" :key="`${layer.name}-${layer.path}`">
              <strong>{{ layer.name }}</strong>
              <span class="path-line">{{ layer.path }}</span>
            </li>
          </ul>
          <p v-else class="empty-hint">当前所有预留层都已存在。</p>
        </div>
      </div>
    </div>

    <div v-if="subagentContract" class="panel-card">
      <div class="card-head">
        <h3>Subagent 注册能力面</h3>
        <span class="muted">角色化子智能体注册信息：描述、工具范围、模型偏好、触发条件</span>
      </div>
      <p class="section-desc">当前注册子智能体：{{ subagentContract.total_profiles || 0 }}</p>
      <div class="provider-grid">
        <div v-for="item in subagentContract.profiles || []" :key="item.name" class="provider-card">
          <div class="provider-title-row">
            <strong>{{ item.name }}</strong>
            <span class="status-badge online">registered</span>
          </div>
          <p class="provider-meta">{{ item.description }}</p>
          <p class="provider-endpoint">context_policy: {{ item.context_policy || '-' }}</p>
          <p class="provider-endpoint">allowed_tools: {{ (item.allowed_tools || []).join(', ') || '-' }}</p>
          <p class="provider-endpoint">preferred_models: {{ (item.preferred_models || []).join(', ') || '-' }}</p>
          <p class="provider-endpoint">triggers: {{ (item.trigger_conditions || []).join(', ') || '-' }}</p>
        </div>
      </div>
    </div>

    <div v-if="hookContract" class="panel-card">
      <div class="card-head">
        <h3>Hooks / Permission 治理层</h3>
        <span class="muted">工具与收尾链路的框架治理钩子</span>
      </div>
      <div class="config-layer-grid">
        <div class="contract-block">
          <h4>已启用 Hook</h4>
          <ul>
            <li v-for="item in hookContract.enabled_hooks || []" :key="item"><code>{{ item }}</code></li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>高风险工具关键字</h4>
          <ul>
            <li v-for="item in hookContract.high_risk_tool_keywords || []" :key="item"><code>{{ item }}</code></li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>治理模型</h4>
          <ul>
            <li><code>{{ hookContract.governance_model || '-' }}</code></li>
          </ul>
        </div>
      </div>
    </div>

    <div v-if="configLayers" class="panel-card">
      <div class="card-head">
        <h3>配置分层</h3>
        <span class="muted">区分默认值、可编辑本地覆写和当前生效值，便于后续对齐企业级 settings surface</span>
      </div>
      <div class="config-layer-grid">
        <div class="contract-block">
          <h4>默认值（.env / 后端默认）</h4>
          <ul>
            <li><code>auth_mode</code>: {{ configLayers.defaults?.auth_mode || '-' }}</li>
            <li><code>default_model</code>: {{ configLayers.defaults?.default_model || '-' }}</li>
            <li><code>enabled_providers</code>: {{ formatProviderConfig(configLayers.defaults?.enabled_providers) }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>本地覆写（runtime_surface.json）</h4>
          <ul>
            <li><code>path</code>: {{ configLayers.override_path || '-' }}</li>
            <li><code>auth_mode</code>: {{ configLayers.overrides?.auth_mode || '未覆写' }}</li>
            <li><code>default_model</code>: {{ configLayers.overrides?.default_model || '未覆写' }}</li>
            <li><code>enabled_providers</code>: {{ formatProviderConfig(configLayers.overrides?.enabled_providers, true) }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>当前生效值</h4>
          <ul>
            <li><code>auth_mode</code>: {{ configLayers.effective?.auth_mode || '-' }}</li>
            <li><code>default_model</code>: {{ configLayers.effective?.default_model || '-' }}</li>
            <li><code>enabled_providers</code>: {{ formatProviderConfig(configLayers.provider_resolution?.enabled_provider_ids || []) }}</li>
            <li><code>editable_keys</code>: {{ (configLayers.editable_keys || []).join(', ') || '-' }}</li>
          </ul>
        </div>
      </div>
    </div>

    <div v-if="profile" class="panel-card">
      <div class="card-head">
        <h3>最小运行时配置</h3>
        <span class="muted">仅开放对 demo 安全的配置项：默认模型与鉴权模式</span>
      </div>
      <div class="editable-grid">
        <label class="field-block">
          <span>默认模型</span>
          <select v-model="editableDefaultModel" class="field-select">
            <option v-for="model in models" :key="model.name" :value="model.name">
              {{ model.display_name || model.name }}
            </option>
          </select>
        </label>
        <label class="field-block">
          <span>鉴权模式</span>
          <select v-model="editableAuthMode" class="field-select">
            <option value="demo_guest">demo_guest</option>
            <option value="business_auth">business_auth</option>
          </select>
        </label>
      </div>
      <div class="provider-toggle-grid">
        <label v-for="provider in providers" :key="provider.provider_id" class="provider-toggle">
          <input
            :checked="editableEnabledProviders.includes(provider.provider_id)"
            type="checkbox"
            @change="toggleProvider(provider.provider_id, $event.target.checked)"
          />
          <div>
            <strong>{{ provider.display_name }}</strong>
            <div class="provider-toggle-meta">
              <span><code>{{ provider.provider_id }}</code></span>
              <span>{{ provider.enabled_source === 'override' ? '本地覆写' : '默认全启用' }}</span>
            </div>
          </div>
        </label>
      </div>
      <div class="edit-actions">
        <button class="secondary-btn" :disabled="saving" @click="saveProfile">
          {{ saving ? '保存中...' : '保存运行时配置' }}
        </button>
        <span v-if="saveMessage" class="save-message">{{ saveMessage }}</span>
      </div>
      <p class="muted helper-text">说明：provider 启停属于本地运行时治理面。若未显式覆写 provider 列表，则默认视为“全部启用”。</p>
    </div>

    <div v-if="models.length" class="panel-card">
      <div class="card-head">
        <h3>模型目录</h3>
        <span class="muted">由后端动态下发，不再写死在前端</span>
      </div>
      <div class="model-list">
        <div v-for="model in models" :key="model.name" class="model-item">
          <div class="model-title-row">
            <strong>{{ model.display_name || model.name }}</strong>
            <span class="status-badge" :class="{ online: model.available, offline: !model.available }">
              {{ model.available ? 'available' : 'unavailable' }}
            </span>
          </div>
          <div class="model-meta">
            <span><code>{{ model.name }}</code></span>
            <span>{{ model.provider_label || model.provider }}</span>
            <span>{{ model.type }}</span>
            <span v-if="model.has_reasoning">reasoning</span>
            <span v-if="model.is_default">default</span>
          </div>
          <div class="model-submeta">
            <span v-if="model.name !== model.actual_model">alias_of: {{ model.actual_model }}</span>
            <span v-if="model.actual_model">actual: {{ model.actual_model }}</span>
            <span v-if="model.base_url">base_url: {{ model.base_url }}</span>
            <span v-if="model.source">source: {{ model.source }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="providers.length" class="panel-card">
      <div class="card-head">
        <h3>Provider 目录</h3>
        <span class="muted">用于后续接入更多云模型、本地模型和 OpenAI 兼容接口</span>
      </div>
      <div class="provider-grid">
        <div v-for="provider in providers" :key="provider.provider_id" class="provider-card">
          <div class="provider-title-row">
            <strong>{{ provider.display_name }}</strong>
            <span class="status-badge" :class="{ online: provider.configured, offline: !provider.configured }">
              {{ provider.configured ? 'configured' : 'not configured' }}
            </span>
          </div>
          <p class="provider-meta">
            <code>{{ provider.provider_id }}</code>
            <span>{{ provider.type }}</span>
            <span>{{ provider.enabled ? 'enabled' : 'disabled' }}</span>
            <span>{{ provider.enabled_source === 'override' ? 'override' : 'default' }}</span>
            <span>configured_models: {{ provider.configured_model_count || 0 }}</span>
            <span>available_models: {{ provider.available_model_count || 0 }}</span>
            <span>total_models: {{ provider.total_model_count || 0 }}</span>
          </p>
          <p v-if="provider.base_url" class="provider-endpoint">{{ provider.base_url }}</p>
          <p v-if="provider.model_sources?.length" class="provider-endpoint">sources: {{ provider.model_sources.join(', ') }}</p>
          <p v-if="provider.actual_models?.length" class="provider-endpoint">actual_models: {{ provider.actual_models.join(', ') }}</p>
          <div class="catalog-tags">
            <span v-for="modelName in provider.models || []" :key="`${provider.provider_id}-${modelName}`" class="capability-pill">
              {{ modelName }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { runtimeSurfaceApi } from '../api'

const profile = ref(null)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const saveMessage = ref('')
const editableAuthMode = ref('demo_guest')
const editableDefaultModel = ref('')
const editableEnabledProviders = ref([])

const models = computed(() => profile.value?.models || [])
const providers = computed(() => profile.value?.providers || [])
const capabilityContract = computed(() => profile.value?.capability_contract || null)
const memoryContract = computed(() => profile.value?.memory_contract || null)
const subagentContract = computed(() => profile.value?.subagent_contract || null)
const hookContract = computed(() => profile.value?.hook_contract || null)
const configLayers = computed(() => profile.value?.config_layers || null)
const authModeDescription = computed(() => {
  const contract = profile.value?.auth_mode_contract || {}
  return profile.value?.auth_mode === 'business_auth'
    ? (contract.business_auth_description || '')
    : (contract.demo_guest_description || '')
})

async function loadProfile() {
  loading.value = true
  error.value = ''
  try {
    const response = await runtimeSurfaceApi.getProfile()
    profile.value = response.data || null
    editableAuthMode.value = profile.value?.auth_mode || 'demo_guest'
    editableDefaultModel.value = profile.value?.default_model || models.value[0]?.name || ''
    editableEnabledProviders.value = [...(profile.value?.config_layers?.provider_resolution?.enabled_provider_ids || [])]
  } catch (err) {
    error.value = err?.response?.data?.detail || err?.message || '加载运行时信息失败'
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  if (!editableDefaultModel.value) {
    saveMessage.value = '请先选择默认模型'
    return
  }
  saving.value = true
  error.value = ''
  saveMessage.value = ''
  try {
    const response = await runtimeSurfaceApi.updateProfile({
      auth_mode: editableAuthMode.value,
      default_model: editableDefaultModel.value,
      enabled_providers: editableEnabledProviders.value
    })
    profile.value = response.data || null
    editableAuthMode.value = profile.value?.auth_mode || editableAuthMode.value
    editableDefaultModel.value = profile.value?.default_model || editableDefaultModel.value
    editableEnabledProviders.value = [...(profile.value?.config_layers?.provider_resolution?.enabled_provider_ids || editableEnabledProviders.value)]
    saveMessage.value = '运行时配置已保存'
  } catch (err) {
    error.value = err?.response?.data?.detail || err?.message || '保存运行时信息失败'
  } finally {
    saving.value = false
  }
}

function toggleProvider(providerId, checked) {
  const current = new Set(editableEnabledProviders.value)
  if (checked) {
    current.add(providerId)
  } else {
    current.delete(providerId)
  }
  editableEnabledProviders.value = [...current]
}

function formatProviderConfig(value, isOverride = false) {
  if (!Array.isArray(value) || value.length === 0) {
    return isOverride ? '未覆写（沿用默认全启用）' : '全部启用'
  }
  return value.join(', ')
}

onMounted(loadProfile)
</script>

<style scoped>
.runtime-panel {
  width: 100%;
}

.section-head,
.card-head,
.model-title-row,
.provider-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
}

.section-desc,
.muted {
  color: var(--text-tertiary);
  font-size: 0.875rem;
}

.path-line {
  display: block;
  color: var(--text-tertiary);
  font-size: 0.82rem;
  word-break: break-all;
}

.editable-grid {
  display: grid;
  gap: var(--space-md);
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  margin-top: var(--space-md);
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.field-select {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.edit-actions {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-top: var(--space-md);
}

.provider-toggle-grid {
  display: grid;
  gap: var(--space-sm);
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  margin-top: var(--space-lg);
}

.provider-toggle {
  display: flex;
  gap: var(--space-sm);
  align-items: flex-start;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
  padding: var(--space-md);
}

.provider-toggle-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 0.8rem;
}

.save-message {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.summary-grid,
.provider-grid {
  display: grid;
  gap: var(--space-md);
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  margin-bottom: var(--space-lg);
}

.contract-summary {
  margin-top: var(--space-md);
  color: var(--text-secondary);
  line-height: 1.7;
}

.contract-grid {
  display: grid;
  gap: var(--space-md);
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  margin-top: var(--space-lg);
}

.contract-block {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
  padding: var(--space-md);
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

.summary-card,
.provider-card,
.panel-card,
.model-item {
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

.summary-note {
  color: var(--text-tertiary);
  line-height: 1.4;
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

.model-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  margin-top: var(--space-md);
}

.model-item,
.provider-card {
  padding: var(--space-md);
}

.model-meta,
.model-submeta,
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

.inline-error {
  color: #dc2626;
  margin: var(--space-sm) 0;
}
</style>
