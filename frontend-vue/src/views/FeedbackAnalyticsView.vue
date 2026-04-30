<template>
  <div class="feedback-analytics-container">
    <div class="analytics-header">
      <div class="header-row">
        <button @click="goBack" class="back-btn">
          <span>←</span> 返回
        </button>
        <h1>📊 反馈分析</h1>
      </div>
      <p class="subtitle">按 scope / prompt / practice 评估反馈表现，辅助知识治理与回滚。</p>
    </div>

    <div class="controls-row">
      <label class="control-item">
        <span>统计窗口</span>
        <select v-model.number="windowDays">
          <option :value="7">7 天</option>
          <option :value="14">14 天</option>
          <option :value="30">30 天</option>
          <option :value="60">60 天</option>
        </select>
      </label>
      <label class="control-item">
        <span>候选最小样本</span>
        <select v-model.number="minSamplesForCandidate">
          <option :value="2">2</option>
          <option :value="3">3</option>
          <option :value="5">5</option>
        </select>
      </label>
      <button class="refresh-btn" :disabled="loading" @click="fetchAnalytics">
        {{ loading ? '刷新中...' : '刷新' }}
      </button>
    </div>

    <div v-if="errorMessage" class="error-banner">{{ errorMessage }}</div>

    <div class="summary-cards">
      <div class="summary-card">
        <div class="label">总反馈</div>
        <div class="value">{{ analytics.total_feedback || 0 }}</div>
      </div>
      <div class="summary-card">
        <div class="label">正反馈</div>
        <div class="value positive">{{ analytics.positive_count || 0 }}</div>
      </div>
      <div class="summary-card">
        <div class="label">负反馈</div>
        <div class="value negative">{{ analytics.negative_count || 0 }}</div>
      </div>
      <div class="summary-card">
        <div class="label">负反馈率</div>
        <div class="value">{{ formatRate(analytics.negative_rate) }}</div>
      </div>
    </div>

    <div class="analytics-grid">
      <section class="panel">
        <h2>回滚候选</h2>
        <div v-if="rollbackCandidates.length === 0" class="empty-text">暂无满足阈值的候选。</div>
        <table v-else class="analytics-table">
          <thead>
            <tr>
              <th>类型</th>
              <th>Key</th>
              <th>总数</th>
              <th>负反馈</th>
              <th>负反馈率</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in rollbackCandidates" :key="`${item.kind}:${item.key}`">
              <td>{{ item.kind }}</td>
              <td>{{ item.key }}</td>
              <td>{{ item.total }}</td>
              <td>{{ item.negative }}</td>
              <td>{{ formatRate(item.negative_rate) }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="panel">
        <h2>Scope 维度</h2>
        <table class="analytics-table">
          <thead>
            <tr>
              <th>Scope</th>
              <th>总数</th>
              <th>负反馈</th>
              <th>负反馈率</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in scopeStats" :key="item.key">
              <td>{{ item.key }}</td>
              <td>{{ item.total }}</td>
              <td>{{ item.negative }}</td>
              <td>{{ formatRate(item.negative_rate) }}</td>
            </tr>
            <tr v-if="scopeStats.length === 0">
              <td colspan="4" class="empty-text">暂无数据</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="panel">
        <h2>Prompt 维度</h2>
        <table class="analytics-table">
          <thead>
            <tr>
              <th>Prompt Key</th>
              <th>总数</th>
              <th>负反馈</th>
              <th>负反馈率</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in promptStats" :key="item.key">
              <td>{{ item.key }}</td>
              <td>{{ item.total }}</td>
              <td>{{ item.negative }}</td>
              <td>{{ formatRate(item.negative_rate) }}</td>
            </tr>
            <tr v-if="promptStats.length === 0">
              <td colspan="4" class="empty-text">暂无数据</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="panel">
        <h2>Practice 维度</h2>
        <table class="analytics-table">
          <thead>
            <tr>
              <th>Practice ID</th>
              <th>总数</th>
              <th>负反馈</th>
              <th>负反馈率</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in practiceStats" :key="item.key">
              <td>{{ item.key }}</td>
              <td>{{ item.total }}</td>
              <td>{{ item.negative }}</td>
              <td>{{ formatRate(item.negative_rate) }}</td>
            </tr>
            <tr v-if="practiceStats.length === 0">
              <td colspan="4" class="empty-text">暂无数据</td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { buildApiUrl } from '../config/apiBase'

const router = useRouter()

const loading = ref(false)
const errorMessage = ref('')
const windowDays = ref(30)
const minSamplesForCandidate = ref(2)
const analytics = ref({
  total_feedback: 0,
  positive_count: 0,
  negative_count: 0,
  neutral_count: 0,
  negative_rate: 0,
  scope_stats: [],
  prompt_stats: [],
  practice_stats: [],
  rollback_candidates: []
})

const scopeStats = computed(() => analytics.value.scope_stats || [])
const promptStats = computed(() => analytics.value.prompt_stats || [])
const practiceStats = computed(() => analytics.value.practice_stats || [])
const rollbackCandidates = computed(() => analytics.value.rollback_candidates || [])

function getAuthHeaders() {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function goBack() {
  router.push('/chat')
}

function formatRate(value) {
  const numeric = Number(value)
  if (Number.isNaN(numeric)) return '-'
  return `${(numeric * 100).toFixed(1)}%`
}

async function fetchAnalytics() {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await axios.get(buildApiUrl('/conversations/analytics/feedback'), {
      params: {
        days: windowDays.value,
        min_samples_for_candidate: minSamplesForCandidate.value
      },
      headers: getAuthHeaders()
    })
    analytics.value = response.data || analytics.value
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || '加载反馈分析失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchAnalytics()
})
</script>

<style scoped>
.feedback-analytics-container {
  width: 100%;
  height: 100%;
  padding: var(--space-xl);
  overflow-y: auto;
  background: var(--bg-primary);
}

.analytics-header {
  margin-bottom: var(--space-lg);
}

.header-row {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  background: var(--bg-surface);
  color: var(--text-secondary);
  cursor: pointer;
}

.back-btn:hover {
  color: var(--text-primary);
  border-color: var(--primary);
}

.subtitle {
  color: var(--text-secondary);
  margin-top: var(--space-xs);
}

.controls-row {
  display: flex;
  gap: var(--space-md);
  align-items: flex-end;
  flex-wrap: wrap;
  margin-bottom: var(--space-lg);
}

.control-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.control-item select {
  min-width: 110px;
  padding: 8px 10px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-primary);
  background: var(--bg-surface);
  color: var(--text-primary);
}

.refresh-btn {
  padding: 8px 14px;
  border-radius: var(--radius-md);
  border: 1px solid rgba(34, 197, 94, 0.45);
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
  cursor: pointer;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-banner {
  margin-bottom: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  border: 1px solid rgba(239, 68, 68, 0.4);
  border-radius: var(--radius-md);
  background: rgba(239, 68, 68, 0.08);
  color: #f87171;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.summary-card {
  padding: var(--space-md);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  background: var(--bg-surface);
}

.summary-card .label {
  color: var(--text-secondary);
  font-size: 0.8rem;
}

.summary-card .value {
  margin-top: 6px;
  font-size: 1.4rem;
  font-weight: 700;
}

.summary-card .value.positive {
  color: #22c55e;
}

.summary-card .value.negative {
  color: #f97316;
}

.analytics-grid {
  display: grid;
  gap: var(--space-md);
}

.panel {
  padding: var(--space-md);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
  background: var(--bg-surface);
}

.panel h2 {
  margin: 0 0 var(--space-sm);
  font-size: 1rem;
}

.analytics-table {
  width: 100%;
  border-collapse: collapse;
}

.analytics-table th,
.analytics-table td {
  padding: 8px 10px;
  text-align: left;
  border-bottom: 1px solid var(--border-primary);
  font-size: 0.85rem;
}

.analytics-table th {
  color: var(--text-secondary);
  font-weight: 600;
}

.empty-text {
  color: var(--text-tertiary);
  text-align: center;
}
</style>
