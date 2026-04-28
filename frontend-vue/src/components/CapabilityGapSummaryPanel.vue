<template>
  <section class="settings-section gap-panel">
    <div class="section-head">
      <div>
        <h2>能力缺口统计</h2>
        <p class="section-desc">用于盘点当前框架最常缺的能力类型，帮助后续决定补工具、Skill 还是 MCP。这里反映的是框架治理缺口，不是单次回答质量评分。</p>
      </div>
      <button class="secondary-btn" :disabled="loading" @click="loadSummary">
        {{ loading ? '刷新中...' : '刷新统计' }}
      </button>
    </div>

    <p v-if="error" class="inline-error">{{ error }}</p>

    <div class="filter-grid">
      <label class="field-block">
        <span>缺口类型</span>
        <select v-model="selectedMissingPart" class="field-select">
          <option value="">全部</option>
          <option v-for="part in availableMissingParts" :key="part" :value="part">
            {{ formatPart(part) }}
          </option>
        </select>
      </label>
      <label class="field-block">
        <span>关键词筛选</span>
        <input v-model.trim="keyword" type="text" class="field-input" placeholder="例如：舟山 / 交通 / 攻略" />
      </label>
      <label class="field-block">
        <span>复合任务模板</span>
        <select v-model="selectedProfile" class="field-select">
          <option value="">全部</option>
          <option v-for="profile in availableProfiles" :key="profile" :value="profile">
            {{ formatProfile(profile) }}
          </option>
        </select>
      </label>
      <label class="field-block">
        <span>收尾阶段</span>
        <select v-model="selectedCompletionStage" class="field-select">
          <option value="">全部</option>
          <option v-for="stage in availableCompletionStages" :key="stage" :value="stage">
            {{ formatStage(stage) }}
          </option>
        </select>
      </label>
      <label class="field-block">
        <span>错误类型</span>
        <select v-model="selectedErrorCategory" class="field-select">
          <option value="">全部</option>
          <option v-for="category in availableErrorCategories" :key="category" :value="category">
            {{ formatErrorCategory(category) }}
          </option>
        </select>
      </label>
      <div class="filter-actions">
        <button class="secondary-btn" :disabled="loading" @click="loadSummary">
          {{ loading ? '筛选中...' : '应用筛选' }}
        </button>
      </div>
    </div>

    <div v-if="summary" class="summary-grid">
      <div class="summary-card">
        <span class="summary-label">缺口事件数</span>
        <strong>{{ summary.total_gap_events || 0 }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">缺口类型数</span>
        <strong>{{ (summary.top_missing_parts || []).length }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">当前筛选</span>
        <strong>{{ activeFilterLabel }}</strong>
      </div>
    </div>

    <div v-if="summary?.top_missing_parts?.length" class="panel-card">
      <div class="card-head">
        <h3>高频缺口</h3>
        <span class="muted">按近期 run trace 聚合</span>
      </div>
      <div class="gap-list">
        <div v-for="item in summary.top_missing_parts" :key="item.name" class="gap-item">
          <strong>{{ formatPart(item.name) }}</strong>
          <span class="gap-count">{{ item.count }} 次</span>
        </div>
      </div>
    </div>

    <div v-if="summary?.top_profiles?.length || summary?.top_completion_stages?.length || summary?.top_error_categories?.length" class="panel-card">
      <div class="card-head">
        <h3>治理维度</h3>
        <span class="muted">按任务模板 / 收尾阶段 / 错误类型聚合</span>
      </div>
      <div class="governance-grid">
        <div v-if="summary?.top_profiles?.length">
          <h4>复合任务模板</h4>
          <div class="mini-list">
            <div v-for="item in summary.top_profiles" :key="item.name" class="gap-item">
              <strong>{{ formatProfile(item.name) }}</strong>
              <span class="gap-count">{{ item.count }} 次</span>
            </div>
          </div>
        </div>
        <div v-if="summary?.top_completion_stages?.length">
          <h4>收尾阶段</h4>
          <div class="mini-list">
            <div v-for="item in summary.top_completion_stages" :key="item.name" class="gap-item">
              <strong>{{ formatStage(item.name) }}</strong>
              <span class="gap-count">{{ item.count }} 次</span>
            </div>
          </div>
        </div>
        <div v-if="summary?.top_error_categories?.length">
          <h4>工具/Provider 错误</h4>
          <div class="mini-list">
            <div v-for="item in summary.top_error_categories" :key="item.name" class="gap-item">
              <strong>{{ formatErrorCategory(item.name) }}</strong>
              <span class="gap-count">{{ item.count }} 次</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="summary?.suggested_investments?.length" class="panel-card">
      <div class="card-head">
        <h3>建议补强方向</h3>
      </div>
      <ul class="suggestion-list">
        <li v-for="item in summary.suggested_investments" :key="item">{{ item }}</li>
      </ul>
    </div>

    <div v-if="summary?.recent_examples?.length" class="panel-card">
      <div class="card-head">
        <h3>近期案例</h3>
      </div>
      <div class="example-list">
        <div v-for="example in summary.recent_examples" :key="`${example.plan_item_id}-${example.timestamp}`" class="example-item">
          <div class="example-title">{{ example.title }}</div>
          <div class="example-meta">缺口：{{ (example.missing_parts || []).map(formatPart).join('、') || '未标注' }}</div>
          <div v-if="example.detail" class="example-detail">{{ example.detail }}</div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { capabilityGapApi } from '../api'

const summary = ref(null)
const loading = ref(false)
const error = ref('')
const selectedMissingPart = ref('')
const keyword = ref('')
const selectedProfile = ref('')
const selectedCompletionStage = ref('')
const selectedErrorCategory = ref('')

const partLabelMap = {
  weather: '天气',
  transport: '交通',
  play: '游玩/行程'
}

const profileLabelMap = {
  travel_planning: '旅行规划',
  research_compare: '研究/对比',
  planning: '任务规划'
}

const stageLabelMap = {
  retry: '补查',
  boundary_fallback: '边界收尾',
  timeout_fallback: '超时收尾',
  finalized: '最终收尾'
}

const errorCategoryLabelMap = {
  provider_timeout: 'Provider 超时',
  provider_connection: 'Provider 连接失败',
  provider_network: 'Provider 网络错误',
  provider_rate_limit: 'Provider 限流',
  provider_unavailable: 'Provider 不可用',
  tool_validation: '工具参数校验失败',
  missing_tool: '缺少工具',
  unknown_error: '未知错误'
}

const availableMissingParts = computed(() => summary.value?.available_missing_parts || [])
const availableProfiles = computed(() => summary.value?.available_profiles || [])
const availableCompletionStages = computed(() => summary.value?.available_completion_stages || [])
const availableErrorCategories = computed(() => summary.value?.available_error_categories || [])
const activeFilterLabel = computed(() => {
  const labels = []
  if (selectedMissingPart.value) {
    labels.push(formatPart(selectedMissingPart.value))
  }
  if (keyword.value) {
    labels.push(`关键词: ${keyword.value}`)
  }
  if (selectedProfile.value) {
    labels.push(`模板: ${formatProfile(selectedProfile.value)}`)
  }
  if (selectedCompletionStage.value) {
    labels.push(`阶段: ${formatStage(selectedCompletionStage.value)}`)
  }
  if (selectedErrorCategory.value) {
    labels.push(`错误: ${formatErrorCategory(selectedErrorCategory.value)}`)
  }
  return labels.length ? labels.join(' / ') : '未筛选'
})

function formatPart(name) {
  return partLabelMap[name] || name
}

function formatProfile(name) {
  return profileLabelMap[name] || name
}

function formatStage(name) {
  return stageLabelMap[name] || name
}

function formatErrorCategory(name) {
  return errorCategoryLabelMap[name] || name
}

async function loadSummary() {
  loading.value = true
  error.value = ''
  try {
    const response = await capabilityGapApi.getSummary({
      limit: 100,
      missing_part: selectedMissingPart.value || undefined,
      keyword: keyword.value || undefined,
      profile: selectedProfile.value || undefined,
      completion_stage: selectedCompletionStage.value || undefined,
      error_category: selectedErrorCategory.value || undefined
    })
    summary.value = response.data || null
  } catch (err) {
    error.value = err?.response?.data?.detail || err?.message || '加载能力缺口统计失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadSummary)
</script>

<style scoped>
.gap-panel {
  width: 100%;
}

.filter-grid {
  display: grid;
  gap: var(--space-md);
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  margin: 0 0 var(--space-lg);
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.field-select,
.field-input {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.filter-actions {
  display: flex;
  align-items: flex-end;
}

.section-head,
.card-head,
.gap-item {
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

.summary-grid {
  display: grid;
  gap: var(--space-md);
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  margin-bottom: var(--space-lg);
}

.summary-card,
.panel-card,
.example-item,
.gap-item {
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

.gap-list,
.example-list,
.suggestion-list,
.mini-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.governance-grid {
  display: grid;
  gap: var(--space-lg);
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  margin-top: var(--space-md);
}

.gap-item,
.example-item {
  padding: var(--space-md);
}

.gap-count,
.example-meta {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.example-title {
  font-weight: 600;
  color: var(--text-primary);
}

.example-detail {
  margin-top: var(--space-xs);
  color: var(--text-secondary);
  line-height: 1.5;
  white-space: pre-wrap;
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
