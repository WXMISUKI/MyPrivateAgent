<template>
  <div class="learnings-container">
    <div class="learnings-header">
      <div class="header-row">
        <button @click="goBack" class="back-btn">
          <span>←</span> 返回
        </button>
        <h1>🧠 学习记录</h1>
      </div>
      <p class="subtitle">查看 AI 从对话中学到的内容</p>
    </div>

    <div class="learnings-stats">
      <div class="stat-card">
        <div class="stat-value">{{ stats.totalLearnings }}</div>
        <div class="stat-label">总学习条目</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.pendingLearnings }}</div>
        <div class="stat-label">待处理</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.resolvedLearnings }}</div>
        <div class="stat-label">已解决</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.totalErrors }}</div>
        <div class="stat-label">错误记录</div>
      </div>
    </div>

    <div class="learnings-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        :class="['tab-btn', { active: activeTab === tab.value }]"
        @click="activeTab = tab.value"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="learnings-filters">
      <select v-model="filterStatus" class="filter-select">
        <option value="">全部状态</option>
        <option value="pending">待处理</option>
        <option value="resolved">已解决</option>
        <option value="promoted">已提升</option>
      </select>
      <select v-model="filterCategory" class="filter-select">
        <option value="">全部分类</option>
        <option value="correction">纠正</option>
        <option value="insight">洞察</option>
        <option value="knowledge_gap">知识差距</option>
        <option value="best_practice">最佳实践</option>
      </select>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索..."
        class="search-input"
      />
      <button @click="refreshData" class="refresh-btn" :disabled="loading">
        🔄
      </button>
    </div>

    <div class="learnings-list">
      <div
        v-for="item in filteredItems"
        :key="item.learning_id || item.error_id || item.feature_id"
        class="learning-item"
      >
        <div class="learning-header">
          <span class="learning-id">{{ item.learning_id || item.error_id || item.feature_id }}</span>
          <span :class="['learning-priority', `priority-${item.priority}`]">
            {{ item.priority }}
          </span>
        </div>

        <div class="learning-summary">{{ item.summary || item.requested_capability }}</div>

        <div v-if="item.details" class="learning-details">
          {{ item.details }}
        </div>

        <div v-if="item.suggested_action" class="learning-action">
          <strong>建议:</strong> {{ item.suggested_action }}
        </div>

        <div class="learning-meta">
          <span class="learning-category">{{ item.category || item.area }}</span>
          <span class="learning-status" :class="`status-${item.status}`">
            {{ item.status }}
          </span>
          <span class="learning-date">{{ formatDate(item.created_at) }}</span>
        </div>

        <div v-if="item.source" class="learning-source">
          来源: {{ item.source }}
        </div>
      </div>

      <div v-if="filteredItems.length === 0 && !loading" class="empty-state">
        <p>暂无记录</p>
      </div>

      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { buildApiUrl } from '../config/apiBase'

const router = useRouter()

function getAuthHeaders() {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function goBack() {
  router.push('/chat')
}

const loading = ref(false)
const activeTab = ref('learnings')
const tabs = [
  { label: '学习记录', value: 'learnings' },
  { label: '错误记录', value: 'errors' },
  { label: '功能请求', value: 'features' }
]

const filterStatus = ref('')
const filterCategory = ref('')
const searchQuery = ref('')

const stats = ref({
  totalLearnings: 0,
  pendingLearnings: 0,
  resolvedLearnings: 0,
  totalErrors: 0
})

const learnings = ref([])
const errors = ref([])
const features = ref([])

const currentItems = computed(() => {
  switch (activeTab.value) {
    case 'learnings': return learnings.value
    case 'errors': return errors.value
    case 'features': return features.value
    default: return []
  }
})

const filteredItems = computed(() => {
  return currentItems.value.filter(item => {
    const matchStatus = !filterStatus.value || item.status === filterStatus.value
    const matchCategory = !filterCategory.value || item.category === filterCategory.value || item.area === filterCategory.value
    const searchLower = searchQuery.value.toLowerCase()
    const matchSearch = !searchQuery.value ||
      (item.summary || '').toLowerCase().includes(searchLower) ||
      (item.details || '').toLowerCase().includes(searchLower) ||
      (item.requested_capability || '').toLowerCase().includes(searchLower)
    return matchStatus && matchCategory && matchSearch
  })
})

async function fetchStats() {
  try {
    const response = await axios.get(buildApiUrl('/learnings/stats'), { headers: getAuthHeaders() })
    stats.value = {
      totalLearnings: response.data.total_learnings,
      pendingLearnings: response.data.pending_learnings,
      resolvedLearnings: response.data.resolved_learnings,
      totalErrors: response.data.total_errors
    }
  } catch (error) {
    console.error('[Learnings] Failed to fetch stats:', error)
  }
}

async function fetchLearnings() {
  try {
    loading.value = true
    const response = await axios.get(buildApiUrl('/learnings'), { headers: getAuthHeaders() })
    learnings.value = response.data
  } catch (error) {
    console.error('[Learnings] Failed to fetch learnings:', error)
  } finally {
    loading.value = false
  }
}

async function fetchErrors() {
  try {
    loading.value = true
    const response = await axios.get(buildApiUrl('/learnings/errors'), { headers: getAuthHeaders() })
    errors.value = response.data
  } catch (error) {
    console.error('[Learnings] Failed to fetch errors:', error)
  } finally {
    loading.value = false
  }
}

async function fetchFeatures() {
  try {
    loading.value = true
    const response = await axios.get(buildApiUrl('/learnings/features'), { headers: getAuthHeaders() })
    features.value = response.data
  } catch (error) {
    console.error('[Learnings] Failed to fetch features:', error)
  } finally {
    loading.value = false
  }
}

async function refreshData() {
  await fetchStats()
  await Promise.all([
    fetchLearnings(),
    fetchErrors(),
    fetchFeatures()
  ])
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.learnings-container {
  width: 100%;
  height: 100%;
  padding: var(--space-xl);
  overflow-y: auto;
  background: var(--bg-primary);
}

.learnings-header {
  margin-bottom: var(--space-xl);
}

.header-row {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn:hover {
  color: var(--text-primary);
  border-color: var(--primary);
}

.learnings-header h1 {
  font-size: 1.75rem;
  color: var(--text-primary);
  margin-bottom: var(--space-sm);
}

.subtitle {
  color: var(--text-secondary);
}

.learnings-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--space-md);
  margin-bottom: var(--space-xl);
}

.stat-card {
  padding: var(--space-lg);
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  text-align: center;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--primary);
  margin-bottom: var(--space-xs);
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.learnings-tabs {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
  border-bottom: 1px solid var(--border-color);
  padding-bottom: var(--space-sm);
}

.tab-btn {
  padding: var(--space-sm) var(--space-lg);
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--radius-md);
  transition: all 0.2s;
}

.tab-btn:hover {
  color: var(--text-primary);
  background: var(--bg-surface);
}

.tab-btn.active {
  color: var(--primary);
  background: var(--bg-surface);
  font-weight: 600;
}

.learnings-filters {
  display: flex;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
  flex-wrap: wrap;
}

.filter-select {
  padding: var(--space-sm) var(--space-md);
  font-size: 0.875rem;
  color: var(--text-primary);
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  outline: none;
  min-width: 120px;
}

.filter-select:focus {
  border-color: var(--primary);
}

.search-input {
  flex: 1;
  min-width: 200px;
  padding: var(--space-sm) var(--space-md);
  font-size: 0.875rem;
  color: var(--text-primary);
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  outline: none;
}

.search-input:focus {
  border-color: var(--primary);
}

.refresh-btn {
  padding: var(--space-sm);
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: transform 0.2s;
}

.refresh-btn:hover {
  transform: rotate(180deg);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.learnings-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.learning-item {
  padding: var(--space-lg);
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  transition: transform 0.2s, box-shadow 0.2s;
}

.learning-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px -10px rgba(0, 0, 0, 0.3);
}

.learning-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
}

.learning-id {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  font-family: monospace;
}

.learning-priority {
  padding: var(--space-xs) var(--space-sm);
  font-size: 0.75rem;
  border-radius: var(--radius-sm);
  text-transform: uppercase;
}

.priority-low { background: rgba(107, 114, 128, 0.2); color: #6b7280; }
.priority-medium { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
.priority-high { background: rgba(249, 115, 22, 0.2); color: #f97316; }
.priority-critical { background: rgba(239, 68, 68, 0.2); color: #ef4444; }

.learning-summary {
  color: var(--text-primary);
  line-height: 1.6;
  margin-bottom: var(--space-sm);
  font-weight: 500;
}

.learning-details {
  color: var(--text-secondary);
  font-size: 0.875rem;
  line-height: 1.5;
  margin-bottom: var(--space-sm);
  padding: var(--space-sm);
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
}

.learning-action {
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin-bottom: var(--space-sm);
}

.learning-meta {
  display: flex;
  gap: var(--space-md);
  align-items: center;
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.learning-category {
  padding: var(--space-xs) var(--space-sm);
  background: rgba(99, 102, 241, 0.15);
  color: var(--primary);
  border-radius: var(--radius-sm);
  text-transform: capitalize;
}

.learning-status {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  text-transform: capitalize;
}

.status-pending { background: rgba(249, 115, 22, 0.15); color: #f97316; }
.status-resolved { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
.status-promoted { background: rgba(99, 102, 241, 0.15); color: #6366f1; }
.status-in_progress { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }

.learning-source {
  margin-top: var(--space-sm);
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.empty-state,
.loading-state {
  text-align: center;
  padding: var(--space-2xl);
  color: var(--text-secondary);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-color);
  border-top-color: var(--primary);
  border-radius: 50%;
  margin: 0 auto var(--space-md);
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
