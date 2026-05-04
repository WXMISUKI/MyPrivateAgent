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
        <div class="stat-value">{{ stats.reviewedLearnings }}</div>
        <div class="stat-label">已审核</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ formatQualityScore(stats.averageQualityScore) }}</div>
        <div class="stat-label">平均质量</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.disabledLearnings }}</div>
        <div class="stat-label">已禁用</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.rolledBackLearnings }}</div>
        <div class="stat-label">已回滚</div>
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
        <option value="in_progress">进行中</option>
        <option value="resolved">已解决</option>
        <option value="promoted">已提升</option>
        <option value="promoted_to_skill">已提升到技能</option>
        <option value="disabled">已禁用</option>
        <option value="rolled_back">已回滚</option>
      </select>
      <select v-model="filterCategory" class="filter-select">
        <option value="">全部分类</option>
        <option value="correction">纠正</option>
        <option value="insight">洞察</option>
        <option value="knowledge_gap">知识差距</option>
        <option value="best_practice">最佳实践</option>
      </select>
      <select v-model="reviewStatusFilter" class="filter-select">
        <option value="">全部审核</option>
        <option value="unreviewed">未审核</option>
        <option value="approved">已通过</option>
        <option value="needs_changes">需修改</option>
        <option value="rejected">已拒绝</option>
      </select>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索..."
        class="search-input"
      />
      <input
        v-model="sourceFilter"
        type="text"
        placeholder="来源，如 user_feedback"
        class="search-input narrow-input"
      />
      <input
        v-model="patternKeyFilter"
        type="text"
        placeholder="Pattern Key"
        class="search-input narrow-input"
      />
      <input
        v-model="tagFilter"
        type="text"
        placeholder="Tag，如 prompt:xxx"
        class="search-input narrow-input"
      />
      <input
        v-model="learningIdFilter"
        type="text"
        placeholder="Learning ID"
        class="search-input narrow-input"
      />
      <button @click="refreshData" class="refresh-btn" :disabled="loading">
        🔄
      </button>
      <button @click="clearFilters" class="clear-btn" type="button">
        清除筛选
      </button>
    </div>

  <div v-if="activeFilterLabels.length" class="active-filter-bar">
      <span class="active-filter-title">当前钻取</span>
      <span
        v-for="item in activeFilterLabels"
        :key="item"
        class="active-filter-chip"
      >
        {{ item }}
      </span>
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
        <div v-if="item.pattern_key" class="learning-pattern">
          Pattern: {{ item.pattern_key }}
        </div>
        <div v-if="Array.isArray(item.tags) && item.tags.length" class="learning-tags">
          <span
            v-for="tag in item.tags.slice(0, 8)"
            :key="`${item.learning_id || item.error_id || item.feature_id}-${tag}`"
            class="learning-tag"
          >
            {{ tag }}
          </span>
        </div>

        <div v-if="item.latest_review" class="learning-review-summary">
          <span>审核: {{ item.latest_review.review_status }}</span>
          <span v-if="item.latest_review.quality_score !== null && item.latest_review.quality_score !== undefined">
            质量: {{ item.latest_review.quality_score }}/5
          </span>
          <span v-if="item.latest_review.reviewer">审核人: {{ item.latest_review.reviewer }}</span>
        </div>

        <div v-if="item.learning_id" class="learning-governance-summary">
          <span class="learning-history-count">历史版本: {{ item.history_count || 0 }}</span>
          <button
            class="history-toggle-btn"
            type="button"
            @click="toggleLearningHistory(item.learning_id)"
          >
            {{ isHistoryExpanded(item.learning_id) ? '收起历史' : '查看历史' }}
          </button>
        </div>

        <div
          v-if="Array.isArray(item.conflict_flags) && item.conflict_flags.length"
          class="learning-conflicts"
        >
          <span
            v-for="flag in item.conflict_flags"
            :key="`${item.learning_id}-${flag}`"
            class="learning-conflict-chip"
          >
            {{ formatConflictFlag(flag) }}
          </span>
        </div>

        <div
          v-if="item.conflict_context && Array.isArray(item.conflict_context.duplicate_learning_ids) && item.conflict_context.duplicate_learning_ids.length"
          class="learning-duplicate-actions"
        >
          <span class="duplicate-actions-label">重复候选:</span>
          <button
            v-for="candidateId in item.conflict_context.duplicate_learning_ids"
            :key="`${item.learning_id}-duplicate-${candidateId}`"
            class="duplicate-merge-btn"
            type="button"
            :disabled="isDuplicateMergeBusy(item.learning_id, candidateId)"
            @click="mergeDuplicateLearning(item.learning_id, candidateId)"
          >
            {{ isDuplicateMergeBusy(item.learning_id, candidateId) ? `合并中 ${candidateId}...` : `合并 ${candidateId}` }}
          </button>
        </div>

        <div v-if="item.learning_id" class="learning-actions">
          <button
            v-if="item.status !== 'disabled' && item.status !== 'rolled_back'"
            class="learning-action-btn"
            type="button"
            :disabled="isActionBusy(item.learning_id, 'disable')"
            @click="runLearningAction(item.learning_id, 'disable')"
          >
            禁用
          </button>
          <button
            v-if="item.status === 'disabled' || item.status === 'rolled_back'"
            class="learning-action-btn"
            type="button"
            :disabled="isActionBusy(item.learning_id, 'restore')"
            @click="runLearningAction(item.learning_id, 'restore')"
          >
            恢复
          </button>
          <button
            v-if="item.status !== 'promoted' && item.status !== 'promoted_to_skill'"
            class="learning-action-btn"
            type="button"
            :disabled="isActionBusy(item.learning_id, 'promote')"
            @click="runLearningAction(item.learning_id, 'promote', { promote_to: 'CLAUDE.md' })"
          >
            提升
          </button>
          <button
            v-if="item.status === 'promoted' || item.status === 'promoted_to_skill'"
            class="learning-action-btn"
            type="button"
            :disabled="isActionBusy(item.learning_id, 'rollback')"
            @click="runLearningAction(item.learning_id, 'rollback')"
          >
            回滚
          </button>
        </div>

        <div v-if="item.learning_id" class="learning-review-box">
          <div class="review-box-title">人工审核</div>
          <div class="review-box-row">
            <select
              class="review-select"
              :value="getReviewDraft(item.learning_id).review_status"
              @change="updateReviewDraft(item.learning_id, 'review_status', $event.target.value)"
            >
              <option value="approved">通过</option>
              <option value="needs_changes">需修改</option>
              <option value="rejected">拒绝</option>
            </select>
            <select
              class="review-select"
              :value="getReviewDraft(item.learning_id).quality_score"
              @change="updateReviewDraft(item.learning_id, 'quality_score', $event.target.value)"
            >
              <option v-for="score in [1, 2, 3, 4, 5]" :key="`score-${score}`" :value="String(score)">
                {{ score }}/5
              </option>
            </select>
            <input
              class="review-input"
              type="text"
              placeholder="审核备注"
              :value="getReviewDraft(item.learning_id).review_note"
              @input="updateReviewDraft(item.learning_id, 'review_note', $event.target.value)"
            />
            <button
              class="review-submit-btn"
              type="button"
              :disabled="isReviewBusy(item.learning_id)"
              @click="submitLearningReview(item.learning_id)"
            >
              {{ isReviewBusy(item.learning_id) ? '提交中...' : '提交审核' }}
            </button>
          </div>
        </div>

        <div v-if="item.learning_id && isHistoryExpanded(item.learning_id)" class="learning-history-box">
          <div class="history-box-title">版本历史</div>
          <div v-if="isHistoryBusy(item.learning_id)" class="history-loading">
            加载中...
          </div>
          <div v-else-if="getLearningHistory(item.learning_id).length" class="history-entry-list">
            <div
              v-for="entry in getLearningHistory(item.learning_id).slice(0, 6)"
              :key="entry.version_id"
              class="history-entry"
            >
              <div class="history-entry-header">
                <span class="history-entry-type">{{ entry.event_type }}</span>
                <span class="history-entry-date">{{ formatDateTime(entry.created_at) }}</span>
              </div>
              <div class="history-entry-summary">{{ entry.summary }}</div>
              <div v-if="entry.change_note" class="history-entry-note">
                {{ entry.change_note }}
              </div>
              <div v-if="entry.snapshot_ref && entry.snapshot_ref.snapshot_id" class="history-entry-snapshot">
                快照: {{ entry.snapshot_ref.snapshot_id }}
              </div>
              <div class="history-entry-actions">
                <button
                  class="history-entry-btn"
                  type="button"
                  :disabled="isCompareBusy(item.learning_id, entry.version_id)"
                  @click="compareHistoryVersion(item.learning_id, entry.version_id)"
                >
                  {{ isCompareBusy(item.learning_id, entry.version_id) ? '对比中...' : '对比当前' }}
                </button>
              </div>
            </div>
          </div>
          <div v-else class="history-empty">
            暂无历史
          </div>

          <div
            v-if="getHistoryCompareResult(item.learning_id)"
            class="history-compare-box"
          >
            <div class="history-compare-title-row">
              <div class="history-compare-title">
                版本对比 {{ getHistoryCompareResult(item.learning_id).base_label }} -> {{ getHistoryCompareResult(item.learning_id).target_label }}
              </div>
              <button
                v-if="getHistoryCompareResult(item.learning_id).base_label"
                class="apply-version-btn"
                type="button"
                :disabled="isApplyVersionBusy(item.learning_id, getHistoryCompareResult(item.learning_id).base_label)"
                @click="applyHistoryVersion(item.learning_id, getHistoryCompareResult(item.learning_id).base_label)"
              >
                {{ isApplyVersionBusy(item.learning_id, getHistoryCompareResult(item.learning_id).base_label) ? '应用中...' : '应用此版本' }}
              </button>
              <button
                v-if="getHistoryCompareResult(item.learning_id).base_label"
                class="apply-version-btn secondary"
                type="button"
                :disabled="isApplySelectedVersionBusy(item.learning_id, getHistoryCompareResult(item.learning_id).base_label)"
                @click="applySelectedHistoryVersion(item.learning_id, getHistoryCompareResult(item.learning_id).base_label)"
              >
                {{ isApplySelectedVersionBusy(item.learning_id, getHistoryCompareResult(item.learning_id).base_label) ? '应用中...' : '应用已选字段' }}
              </button>
            </div>
            <div v-if="getHistoryCompareResult(item.learning_id).has_changes" class="history-compare-list">
              <div
                v-for="change in getHistoryCompareResult(item.learning_id).changed_fields"
                :key="`${item.learning_id}-${change.field}`"
                class="history-compare-item"
              >
                <label class="history-compare-field">
                  <input
                    type="checkbox"
                    :checked="isCompareFieldSelected(item.learning_id, change.field)"
                    @change="toggleCompareField(item.learning_id, change.field, $event.target.checked)"
                  />
                  <span>{{ formatCompareField(change.field) }}</span>
                </label>
                <div class="history-compare-values">
                  <span class="history-compare-before">旧: {{ change.before || '-' }}</span>
                  <span class="history-compare-after">新: {{ change.after || '-' }}</span>
                </div>
              </div>
            </div>
            <div v-else class="history-empty">
              当前版本与所选版本无差异
            </div>
          </div>
        </div>
      </div>

      <div v-if="actionMessage" class="action-banner">
        {{ actionMessage }}
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { buildApiUrl } from '../config/apiBase'
import { useConversationStore } from '../stores/conversation'

const router = useRouter()
const route = useRoute()
const conversationStore = useConversationStore()

function getAuthHeaders() {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

const currentConversationId = computed(() => {
  const id = Number(conversationStore.currentConversation?.id)
  return Number.isFinite(id) ? id : null
})

function withConversationId(payload = {}) {
  return currentConversationId.value ? { ...payload, conversation_id: currentConversationId.value } : { ...payload }
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
const reviewStatusFilter = ref('')
const searchQuery = ref('')
const sourceFilter = ref('')
const patternKeyFilter = ref('')
const tagFilter = ref('')
const learningIdFilter = ref('')

const stats = ref({
  totalLearnings: 0,
  pendingLearnings: 0,
  resolvedLearnings: 0,
  reviewedLearnings: 0,
  averageQualityScore: null,
  disabledLearnings: 0,
  rolledBackLearnings: 0,
  totalErrors: 0
})

const learnings = ref([])
const errors = ref([])
const features = ref([])
const actionState = ref({ learningId: '', action: '' })
const actionMessage = ref('')
const reviewDrafts = ref({})
const reviewState = ref({ learningId: '', submitting: false })
const learningHistories = ref({})
const historyState = ref({ learningId: '', loading: false })
const expandedHistoryIds = ref({})
const compareState = ref({ learningId: '', versionId: '', loading: false })
const historyCompareResults = ref({})
const compareFieldSelections = ref({})
const duplicateMergeState = ref({ learningId: '', sourceLearningId: '', loading: false })
const applyVersionState = ref({ learningId: '', versionId: '', loading: false })
const applySelectedVersionState = ref({ learningId: '', versionId: '', loading: false })

const currentItems = computed(() => {
  switch (activeTab.value) {
    case 'learnings': return learnings.value
    case 'errors': return errors.value
    case 'features': return features.value
    default: return []
  }
})

const isLearningsTab = computed(() => activeTab.value === 'learnings')

const filteredItems = computed(() => {
  return currentItems.value.filter(item => {
    const matchStatus = !filterStatus.value || item.status === filterStatus.value
    const matchCategory = !filterCategory.value || item.category === filterCategory.value || item.area === filterCategory.value
    const latestReviewStatus = String(item.latest_review?.review_status || '').trim().toLowerCase()
    const matchReviewStatus = !isLearningsTab.value || !reviewStatusFilter.value ||
      (reviewStatusFilter.value === 'unreviewed'
        ? !latestReviewStatus
        : latestReviewStatus === reviewStatusFilter.value.trim().toLowerCase())
    const normalizedSource = String(item.source || '').trim().toLowerCase()
    const normalizedPatternKey = String(item.pattern_key || '').trim().toLowerCase()
    const normalizedLearningId = String(item.learning_id || '').trim().toLowerCase()
    const normalizedTagFilter = tagFilter.value.trim().toLowerCase()
    const tags = Array.isArray(item.tags) ? item.tags.map(tag => String(tag || '').trim().toLowerCase()) : []
    const matchSource = !isLearningsTab.value || !sourceFilter.value || normalizedSource === sourceFilter.value.trim().toLowerCase()
    const matchPatternKey = !isLearningsTab.value || !patternKeyFilter.value || normalizedPatternKey.includes(patternKeyFilter.value.trim().toLowerCase())
    const matchTag = !isLearningsTab.value || !normalizedTagFilter || tags.some(tag => tag.includes(normalizedTagFilter))
    const matchLearningId = !isLearningsTab.value || !learningIdFilter.value || normalizedLearningId === learningIdFilter.value.trim().toLowerCase()
    const searchLower = searchQuery.value.toLowerCase()
    const matchSearch = !searchQuery.value ||
      (item.summary || '').toLowerCase().includes(searchLower) ||
      (item.details || '').toLowerCase().includes(searchLower) ||
      (item.requested_capability || '').toLowerCase().includes(searchLower) ||
      (item.pattern_key || '').toLowerCase().includes(searchLower) ||
      (item.learning_id || '').toLowerCase().includes(searchLower) ||
      (item.latest_review?.review_note || '').toLowerCase().includes(searchLower) ||
      tags.some(tag => tag.includes(searchLower))
    return matchStatus && matchCategory && matchReviewStatus && matchSource && matchPatternKey && matchTag && matchLearningId && matchSearch
  })
})

const activeFilterLabels = computed(() => {
  const labels = []
  if (filterStatus.value) labels.push(`状态: ${filterStatus.value}`)
  if (filterCategory.value) labels.push(`分类: ${filterCategory.value}`)
  if (reviewStatusFilter.value) labels.push(`审核: ${reviewStatusFilter.value}`)
  if (searchQuery.value) labels.push(`搜索: ${searchQuery.value}`)
  if (sourceFilter.value) labels.push(`来源: ${sourceFilter.value}`)
  if (patternKeyFilter.value) labels.push(`Pattern: ${patternKeyFilter.value}`)
  if (tagFilter.value) labels.push(`Tag: ${tagFilter.value}`)
  if (learningIdFilter.value) labels.push(`Learning: ${learningIdFilter.value}`)
  return labels
})

function readQueryValue(value) {
  if (Array.isArray(value)) {
    return String(value[0] || '').trim()
  }
  return String(value || '').trim()
}

function syncFiltersFromRoute(query = route.query) {
  const nextTab = readQueryValue(query.tab)
  activeTab.value = tabs.some(item => item.value === nextTab) ? nextTab : 'learnings'
  filterStatus.value = readQueryValue(query.status)
  filterCategory.value = readQueryValue(query.category)
  reviewStatusFilter.value = readQueryValue(query.review_status)
  searchQuery.value = readQueryValue(query.search || query.q)
  sourceFilter.value = readQueryValue(query.source)
  patternKeyFilter.value = readQueryValue(query.pattern_key)
  tagFilter.value = readQueryValue(query.tag)
  learningIdFilter.value = readQueryValue(query.learning_id)
}

function clearFilters() {
  router.push('/learnings?tab=learnings')
}

async function fetchStats() {
  try {
    const response = await axios.get(buildApiUrl('/learnings/stats'), { headers: getAuthHeaders() })
    stats.value = {
      totalLearnings: response.data.total_learnings,
      pendingLearnings: response.data.pending_learnings,
      resolvedLearnings: response.data.resolved_learnings,
      reviewedLearnings: response.data.reviewed_learnings || 0,
      averageQualityScore: response.data.average_quality_score ?? null,
      disabledLearnings: response.data.disabled_learnings || 0,
      rolledBackLearnings: response.data.rolled_back_learnings || 0,
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

function formatDateTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatQualityScore(value) {
  const numeric = Number(value)
  if (Number.isNaN(numeric)) return '-'
  return numeric.toFixed(1)
}

function formatConflictFlag(flag) {
  const normalized = String(flag || '').trim()
  const mapping = {
    review_needs_changes: '审核需修改',
    review_rejected: '审核已拒绝',
    duplicate_pattern_key: '重复模式',
    promotion_without_approved_review: '提升未通过审核'
  }
  return mapping[normalized] || normalized
}

function formatCompareField(field) {
  const mapping = {
    status: '状态',
    summary: '摘要',
    details: '详情',
    suggested_action: '建议动作',
    tags: '标签',
    promoted_to: '提升目标',
    source: '来源',
    pattern_key: 'Pattern',
    category: '分类',
    priority: '优先级',
    area: '区域',
    review_status: '审核状态',
    quality_score: '质量分'
  }
  return mapping[String(field || '').trim()] || field
}

function isActionBusy(learningId, action) {
  return actionState.value.learningId === learningId && actionState.value.action === action
}

function getReviewDraft(learningId) {
  const key = String(learningId || '').trim()
  if (!key) {
    return { review_status: 'approved', quality_score: '4', review_note: '' }
  }
  if (!reviewDrafts.value[key]) {
    reviewDrafts.value[key] = {
      review_status: 'approved',
      quality_score: '4',
      review_note: ''
    }
  }
  return reviewDrafts.value[key]
}

function updateReviewDraft(learningId, field, value) {
  const draft = getReviewDraft(learningId)
  const nextValue = field === 'quality_score' ? String(value || '4') : String(value || '')
  reviewDrafts.value[String(learningId || '').trim()] = {
    ...draft,
    [field]: nextValue
  }
}

function isReviewBusy(learningId) {
  return reviewState.value.learningId === learningId && reviewState.value.submitting
}

function isHistoryExpanded(learningId) {
  return Boolean(expandedHistoryIds.value[String(learningId || '').trim()])
}

function isHistoryBusy(learningId) {
  return historyState.value.learningId === learningId && historyState.value.loading
}

function getLearningHistory(learningId) {
  return learningHistories.value[String(learningId || '').trim()] || []
}

function getHistoryCompareResult(learningId) {
  return historyCompareResults.value[String(learningId || '').trim()] || null
}

function isCompareBusy(learningId, versionId) {
  return compareState.value.learningId === learningId && compareState.value.versionId === versionId && compareState.value.loading
}

function isDuplicateMergeBusy(learningId, sourceLearningId) {
  return duplicateMergeState.value.learningId === learningId
    && duplicateMergeState.value.sourceLearningId === sourceLearningId
    && duplicateMergeState.value.loading
}

function isApplyVersionBusy(learningId, versionId) {
  return applyVersionState.value.learningId === learningId
    && applyVersionState.value.versionId === versionId
    && applyVersionState.value.loading
}

function isApplySelectedVersionBusy(learningId, versionId) {
  return applySelectedVersionState.value.learningId === learningId
    && applySelectedVersionState.value.versionId === versionId
    && applySelectedVersionState.value.loading
}

function getCompareSelectionKey(learningId) {
  return String(learningId || '').trim()
}

function getCompareSelectedFields(learningId) {
  return compareFieldSelections.value[getCompareSelectionKey(learningId)] || []
}

function isCompareFieldSelected(learningId, field) {
  return getCompareSelectedFields(learningId).includes(String(field || '').trim())
}

function setCompareSelectedFields(learningId, fields) {
  const key = getCompareSelectionKey(learningId)
  compareFieldSelections.value = {
    ...compareFieldSelections.value,
    [key]: Array.from(new Set((fields || []).map(item => String(item || '').trim()).filter(Boolean)))
  }
}

function toggleCompareField(learningId, field, checked) {
  const key = getCompareSelectionKey(learningId)
  const nextFields = new Set(getCompareSelectedFields(learningId))
  const normalizedField = String(field || '').trim()
  if (!normalizedField) return
  if (checked) {
    nextFields.add(normalizedField)
  } else {
    nextFields.delete(normalizedField)
  }
  compareFieldSelections.value = {
    ...compareFieldSelections.value,
    [key]: Array.from(nextFields)
  }
}

async function fetchLearningHistory(learningId) {
  const normalizedLearningId = String(learningId || '').trim()
  if (!normalizedLearningId) return
  if (learningHistories.value[normalizedLearningId]) return
  historyState.value = { learningId: normalizedLearningId, loading: true }
  try {
    const response = await axios.get(
      buildApiUrl(`/learnings/${encodeURIComponent(normalizedLearningId)}/history`),
      { headers: getAuthHeaders() }
    )
    learningHistories.value = {
      ...learningHistories.value,
      [normalizedLearningId]: Array.isArray(response.data) ? response.data : []
    }
  } catch (error) {
    actionMessage.value = error?.response?.data?.detail || '加载学习历史失败'
  } finally {
    historyState.value = { learningId: '', loading: false }
  }
}

async function toggleLearningHistory(learningId) {
  const normalizedLearningId = String(learningId || '').trim()
  if (!normalizedLearningId) return
  const nextExpanded = !isHistoryExpanded(normalizedLearningId)
  expandedHistoryIds.value = {
    ...expandedHistoryIds.value,
    [normalizedLearningId]: nextExpanded
  }
  if (nextExpanded) {
    await fetchLearningHistory(normalizedLearningId)
  }
}

async function compareHistoryVersion(learningId, versionId) {
  const normalizedLearningId = String(learningId || '').trim()
  const normalizedVersionId = String(versionId || '').trim()
  if (!normalizedLearningId || !normalizedVersionId) return
  compareState.value = { learningId: normalizedLearningId, versionId: normalizedVersionId, loading: true }
  try {
    const response = await axios.get(
      buildApiUrl(`/learnings/${encodeURIComponent(normalizedLearningId)}/compare?base_version_id=${encodeURIComponent(normalizedVersionId)}`),
      { headers: getAuthHeaders() }
    )
    historyCompareResults.value = {
      ...historyCompareResults.value,
      [normalizedLearningId]: response.data || null
    }
    const changedFields = Array.isArray(response.data?.changed_fields)
      ? response.data.changed_fields.map(item => item.field).filter(Boolean)
      : []
    setCompareSelectedFields(normalizedLearningId, changedFields)
  } catch (error) {
    actionMessage.value = error?.response?.data?.detail || '学习版本对比失败'
  } finally {
    compareState.value = { learningId: '', versionId: '', loading: false }
  }
}

async function mergeDuplicateLearning(learningId, sourceLearningId) {
  const normalizedLearningId = String(learningId || '').trim()
  const normalizedSourceLearningId = String(sourceLearningId || '').trim()
  if (!normalizedLearningId || !normalizedSourceLearningId) return
  duplicateMergeState.value = {
    learningId: normalizedLearningId,
    sourceLearningId: normalizedSourceLearningId,
    loading: true
  }
  actionMessage.value = ''
  try {
    const response = await axios.post(
      buildApiUrl(`/learnings/${encodeURIComponent(normalizedLearningId)}/merge-duplicate`),
      withConversationId({
        source_learning_id: normalizedSourceLearningId,
        note: '前端合并重复模式'
      }),
      { headers: getAuthHeaders() }
    )
    const snapshotId = response?.data?.snapshot_ref?.snapshot_id
    actionMessage.value = snapshotId
      ? `学习 ${normalizedLearningId} 已合并重复项 ${normalizedSourceLearningId} (${snapshotId})`
      : `学习 ${normalizedLearningId} 已合并重复项 ${normalizedSourceLearningId}`
    await refreshData()
    const nextHistories = { ...learningHistories.value }
    delete nextHistories[normalizedLearningId]
    learningHistories.value = nextHistories
  } catch (error) {
    actionMessage.value = error?.response?.data?.detail || '合并重复学习失败'
  } finally {
    duplicateMergeState.value = { learningId: '', sourceLearningId: '', loading: false }
  }
}

async function applyHistoryVersion(learningId, versionId) {
  const normalizedLearningId = String(learningId || '').trim()
  const normalizedVersionId = String(versionId || '').trim()
  if (!normalizedLearningId || !normalizedVersionId) return
  applyVersionState.value = {
    learningId: normalizedLearningId,
    versionId: normalizedVersionId,
    loading: true
  }
  actionMessage.value = ''
  try {
    const response = await axios.post(
      buildApiUrl(`/learnings/${encodeURIComponent(normalizedLearningId)}/apply-version`),
      withConversationId({
        version_id: normalizedVersionId,
        note: '前端应用历史版本'
      }),
      { headers: getAuthHeaders() }
    )
    const snapshotId = response?.data?.snapshot_ref?.snapshot_id
    actionMessage.value = snapshotId
      ? `学习 ${normalizedLearningId} 已应用版本 ${normalizedVersionId} (${snapshotId})`
      : `学习 ${normalizedLearningId} 已应用版本 ${normalizedVersionId}`
    await refreshData()
    const nextHistories = { ...learningHistories.value }
    delete nextHistories[normalizedLearningId]
    learningHistories.value = nextHistories
    historyCompareResults.value = {
      ...historyCompareResults.value,
      [normalizedLearningId]: null
    }
    compareFieldSelections.value = {
      ...compareFieldSelections.value,
      [normalizedLearningId]: []
    }
  } catch (error) {
    actionMessage.value = error?.response?.data?.detail || '应用学习版本失败'
  } finally {
    applyVersionState.value = { learningId: '', versionId: '', loading: false }
  }
}

async function applySelectedHistoryVersion(learningId, versionId) {
  const normalizedLearningId = String(learningId || '').trim()
  const normalizedVersionId = String(versionId || '').trim()
  if (!normalizedLearningId || !normalizedVersionId) return
  const selectedFields = getCompareSelectedFields(normalizedLearningId)
  if (!selectedFields.length) {
    actionMessage.value = '请至少选择一个字段再应用'
    return
  }
  applySelectedVersionState.value = {
    learningId: normalizedLearningId,
    versionId: normalizedVersionId,
    loading: true
  }
  actionMessage.value = ''
  try {
    const response = await axios.post(
      buildApiUrl(`/learnings/${encodeURIComponent(normalizedLearningId)}/apply-version`),
      withConversationId({
        version_id: normalizedVersionId,
        fields: selectedFields,
        note: '前端应用选定字段'
      }),
      { headers: getAuthHeaders() }
    )
    const snapshotId = response?.data?.snapshot_ref?.snapshot_id
    actionMessage.value = snapshotId
      ? `学习 ${normalizedLearningId} 已应用选定字段 (${snapshotId})`
      : `学习 ${normalizedLearningId} 已应用选定字段`
    await refreshData()
    const nextHistories = { ...learningHistories.value }
    delete nextHistories[normalizedLearningId]
    learningHistories.value = nextHistories
    historyCompareResults.value = {
      ...historyCompareResults.value,
      [normalizedLearningId]: null
    }
    compareFieldSelections.value = {
      ...compareFieldSelections.value,
      [normalizedLearningId]: []
    }
  } catch (error) {
    actionMessage.value = error?.response?.data?.detail || '应用学习选定字段失败'
  } finally {
    applySelectedVersionState.value = { learningId: '', versionId: '', loading: false }
  }
}

async function runLearningAction(learningId, action, payload = {}) {
  const normalizedLearningId = String(learningId || '').trim()
  if (!normalizedLearningId) return
  actionState.value = { learningId: normalizedLearningId, action }
  actionMessage.value = ''
  try {
    const response = await axios.post(
      buildApiUrl(`/learnings/${encodeURIComponent(normalizedLearningId)}/${action}`),
      withConversationId(payload),
      { headers: getAuthHeaders() }
    )
    const snapshotId = response?.data?.snapshot_ref?.snapshot_id
    actionMessage.value = snapshotId
      ? `学习 ${normalizedLearningId} 已执行 ${action} (${snapshotId})`
      : `学习 ${normalizedLearningId} 已执行 ${action}`
    await refreshData()
  } catch (error) {
    actionMessage.value = error?.response?.data?.detail || `学习治理动作执行失败: ${action}`
  } finally {
    actionState.value = { learningId: '', action: '' }
  }
}

async function submitLearningReview(learningId) {
  const normalizedLearningId = String(learningId || '').trim()
  if (!normalizedLearningId) return
  const draft = getReviewDraft(normalizedLearningId)
  reviewState.value = { learningId: normalizedLearningId, submitting: true }
  actionMessage.value = ''
  try {
    const response = await axios.post(
      buildApiUrl(`/learnings/${encodeURIComponent(normalizedLearningId)}/review`),
      withConversationId({
        review_status: draft.review_status,
        quality_score: Number(draft.quality_score),
        review_note: draft.review_note
      }),
      { headers: getAuthHeaders() }
    )
    const snapshotId = response?.data?.snapshot_ref?.snapshot_id
    actionMessage.value = snapshotId
      ? `学习 ${normalizedLearningId} 已提交审核 (${snapshotId})`
      : `学习 ${normalizedLearningId} 已提交审核`
    await refreshData()
  } catch (error) {
    actionMessage.value = error?.response?.data?.detail || '提交审核失败'
  } finally {
    reviewState.value = { learningId: '', submitting: false }
  }
}

onMounted(() => {
  refreshData()
})

watch(() => route.query, syncFiltersFromRoute, { immediate: true, deep: true })
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

.narrow-input {
  flex: 0 1 220px;
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

.clear-btn {
  padding: var(--space-sm) var(--space-md);
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: var(--radius-md);
  color: var(--primary);
  cursor: pointer;
}

.active-filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: var(--space-lg);
  padding: var(--space-sm) var(--space-md);
  border: 1px solid rgba(99, 102, 241, 0.16);
  border-radius: var(--radius-md);
  background: rgba(99, 102, 241, 0.06);
}

.active-filter-title {
  color: var(--text-secondary);
  font-size: 0.8rem;
}

.active-filter-chip {
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(99, 102, 241, 0.14);
  color: var(--text-primary);
  font-size: 0.75rem;
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
.status-in_progress { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
.status-resolved { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
.status-promoted { background: rgba(99, 102, 241, 0.15); color: #6366f1; }
.status-promoted_to_skill { background: rgba(168, 85, 247, 0.15); color: #a855f7; }
.status-disabled { background: rgba(148, 163, 184, 0.18); color: #94a3b8; }
.status-rolled_back { background: rgba(239, 68, 68, 0.15); color: #ef4444; }

.learning-source {
  margin-top: var(--space-sm);
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.learning-pattern {
  margin-top: 6px;
  font-size: 0.75rem;
  color: var(--text-tertiary);
  font-family: monospace;
}

.learning-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.learning-tag {
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(59, 130, 246, 0.14);
  color: var(--text-secondary);
  font-size: 0.72rem;
}

.learning-review-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 8px;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.learning-governance-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  margin-top: 8px;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.history-toggle-btn {
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid rgba(99, 102, 241, 0.22);
  background: rgba(99, 102, 241, 0.08);
  color: var(--primary);
  font-size: 0.75rem;
  cursor: pointer;
}

.learning-conflicts {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.learning-conflict-chip {
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
  font-size: 0.72rem;
}

.learning-duplicate-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  margin-top: 8px;
}

.duplicate-actions-label {
  font-size: 0.72rem;
  color: var(--text-secondary);
}

.duplicate-merge-btn {
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid rgba(249, 115, 22, 0.24);
  background: rgba(249, 115, 22, 0.08);
  color: #f97316;
  font-size: 0.72rem;
  cursor: pointer;
}

.learning-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: var(--space-sm);
}

.learning-action-btn {
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  border: 1px solid rgba(99, 102, 241, 0.25);
  background: rgba(99, 102, 241, 0.1);
  color: var(--primary);
  font-size: 0.75rem;
  cursor: pointer;
}

.learning-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-banner {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid rgba(34, 197, 94, 0.28);
  border-radius: var(--radius-md);
  background: rgba(34, 197, 94, 0.08);
  color: #22c55e;
  margin: var(--space-sm) 0;
}

.learning-review-box {
  margin-top: var(--space-sm);
  padding: var(--space-sm);
  border: 1px solid rgba(99, 102, 241, 0.18);
  border-radius: var(--radius-md);
  background: rgba(99, 102, 241, 0.05);
}

.review-box-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.review-box-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.review-select,
.review-input {
  min-width: 120px;
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
  background: var(--bg-surface);
  color: var(--text-primary);
  font-size: 0.8rem;
}

.review-input {
  flex: 1;
  min-width: 180px;
}

.review-submit-btn {
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  border: 1px solid rgba(99, 102, 241, 0.25);
  background: rgba(99, 102, 241, 0.1);
  color: var(--primary);
  font-size: 0.8rem;
  cursor: pointer;
}

.review-submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.learning-history-box {
  margin-top: var(--space-sm);
  padding: var(--space-sm);
  border: 1px solid rgba(99, 102, 241, 0.18);
  border-radius: var(--radius-md);
  background: rgba(99, 102, 241, 0.04);
}

.history-box-title {
  margin-bottom: 8px;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-primary);
}

.history-entry-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-entry {
  padding: 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
  background: var(--bg-surface);
}

.history-entry-header {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 0.72rem;
  color: var(--text-secondary);
}

.history-entry-type {
  color: var(--primary);
  font-weight: 600;
}

.history-entry-summary {
  font-size: 0.82rem;
  color: var(--text-primary);
}

.history-entry-note,
.history-loading,
.history-empty {
  margin-top: 4px;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.history-entry-snapshot {
  margin-top: 4px;
  font-size: 0.72rem;
  color: var(--text-tertiary);
  font-family: monospace;
}

.history-entry-actions {
  margin-top: 6px;
}

.history-entry-btn {
  padding: 3px 8px;
  border-radius: 999px;
  border: 1px solid rgba(99, 102, 241, 0.22);
  background: rgba(99, 102, 241, 0.08);
  color: var(--primary);
  font-size: 0.72rem;
  cursor: pointer;
}

.history-compare-box {
  margin-top: var(--space-sm);
  padding: var(--space-sm);
  border: 1px solid rgba(99, 102, 241, 0.18);
  border-radius: var(--radius-md);
  background: rgba(99, 102, 241, 0.05);
}

.history-compare-title {
  margin-bottom: 8px;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-primary);
}

.history-compare-title-row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.apply-version-btn {
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid rgba(16, 185, 129, 0.22);
  background: rgba(16, 185, 129, 0.08);
  color: #10b981;
  font-size: 0.72rem;
  cursor: pointer;
}

.apply-version-btn.secondary {
  border-color: rgba(99, 102, 241, 0.22);
  background: rgba(99, 102, 241, 0.08);
  color: var(--primary);
}

.apply-version-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.history-compare-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-compare-item {
  padding: 8px;
  border-radius: var(--radius-sm);
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
}

.history-compare-field {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--primary);
}

.history-compare-values {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 0.75rem;
  color: var(--text-secondary);
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
