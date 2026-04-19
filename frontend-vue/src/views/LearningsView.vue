<template>
  <div class="learnings-container">
    <div class="learnings-header">
      <h1>🧠 学习记录</h1>
      <p class="subtitle">查看 AI 从对话中学到的内容</p>
    </div>

    <div class="learnings-stats">
      <div class="stat-card">
        <div class="stat-value">{{ stats.totalLearnings }}</div>
        <div class="stat-label">总学习条目</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.thisWeek }}</div>
        <div class="stat-label">本周新增</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.categories }}</div>
        <div class="stat-label">知识分类</div>
      </div>
    </div>

    <div class="learnings-filters">
      <select v-model="filterCategory" class="filter-select">
        <option value="">全部分类</option>
        <option value="code">代码</option>
        <option value="concept">概念</option>
        <option value="preference">偏好</option>
      </select>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索学习记录..."
        class="search-input"
      />
    </div>

    <div class="learnings-list">
      <div
        v-for="item in filteredLearnings"
        :key="item.id"
        class="learning-item"
      >
        <div class="learning-category">{{ item.category }}</div>
        <div class="learning-content">{{ item.content }}</div>
        <div class="learning-meta">
          <span class="learning-date">{{ formatDate(item.createdAt) }}</span>
          <span class="learning-source">来源: {{ item.source }}</span>
        </div>
      </div>

      <div v-if="filteredLearnings.length === 0" class="empty-state">
        <p>暂无学习记录</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const filterCategory = ref('')
const searchQuery = ref('')

const stats = ref({
  totalLearnings: 0,
  thisWeek: 0,
  categories: 0
})

const learnings = ref([])

const filteredLearnings = computed(() => {
  return learnings.value.filter(item => {
    const matchCategory = !filterCategory.value || item.category === filterCategory.value
    const matchSearch = !searchQuery.value || item.content.toLowerCase().includes(searchQuery.value.toLowerCase())
    return matchCategory && matchSearch
  })
})

function formatDate(timestamp) {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleDateString('zh-CN')
}
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
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-lg);
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
  margin-bottom: var(--space-sm);
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.learnings-filters {
  display: flex;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.filter-select,
.search-input {
  padding: var(--space-sm) var(--space-md);
  font-size: 0.875rem;
  color: var(--text-primary);
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  outline: none;
}

.filter-select:focus,
.search-input:focus {
  border-color: var(--primary);
}

.filter-select {
  min-width: 150px;
}

.search-input {
  flex: 1;
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

.learning-category {
  display: inline-block;
  padding: var(--space-xs) var(--space-sm);
  font-size: 0.75rem;
  color: var(--primary-light);
  background: rgba(99, 102, 241, 0.15);
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-sm);
}

.learning-content {
  color: var(--text-primary);
  line-height: 1.6;
  margin-bottom: var(--space-md);
}

.learning-meta {
  display: flex;
  gap: var(--space-lg);
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.empty-state {
  text-align: center;
  padding: var(--space-2xl);
  color: var(--text-secondary);
}
</style>
