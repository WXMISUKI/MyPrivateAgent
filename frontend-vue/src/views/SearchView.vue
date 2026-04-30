<template>
  <div class="search-container">
    <div class="search-header">
      <div class="header-row">
        <button @click="goBack" class="back-btn">
          <span>←</span> 返回
        </button>
        <h1>🔍 搜索会话</h1>
      </div>
      <p class="subtitle">搜索您的对话历史</p>
    </div>

    <div class="search-input-wrapper">
      <input
        v-model="searchQuery"
        type="text"
        class="search-input"
        placeholder="输入搜索关键词..."
        @keydown.enter="performSearch"
        ref="searchInputRef"
      />
      <button @click="performSearch" class="search-btn">搜索</button>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <span>搜索中...</span>
    </div>

    <div v-else-if="searchQuery && results.length === 0" class="empty-state">
      <div class="empty-icon">🔍</div>
      <p>未找到与 "{{ searchQuery }}" 相关的会话</p>
    </div>

    <div v-else-if="!searchQuery" class="empty-state">
      <div class="empty-icon">💬</div>
      <p>输入关键词开始搜索</p>
    </div>

    <div v-else class="results-container">
      <div class="results-count">
        找到 {{ results.length }} 个相关会话
      </div>

      <div class="conversation-results">
        <div
          v-for="conv in results"
          :key="conv.id"
          class="conversation-item"
          @click="openConversation(conv.id)"
        >
          <div class="conversation-info">
            <h3 class="conversation-title">{{ conv.title }}</h3>
            <div class="conversation-meta">
              <span class="model-tag">{{ conv.model_name }}</span>
              <span class="date">{{ formatDate(conv.updated_at) }}</span>
            </div>
          </div>
          <button class="open-btn">打开</button>
        </div>
      </div>

      <div v-if="messageResults.length > 0" class="message-results">
        <h3 class="results-section-title">匹配的消息</h3>
        <div
          v-for="msg in messageResults"
          :key="msg.id"
          class="message-item"
          @click="openConversation(msg.conversation_id)"
        >
          <div class="message-header">
            <span :class="['role-badge', msg.role]">
              {{ msg.role === 'user' ? '用户' : 'AI' }}
            </span>
            <span class="conv-title">{{ msg.conversation_title }}</span>
            <span class="date">{{ formatDate(msg.created_at) }}</span>
          </div>
          <div class="message-preview" v-html="highlightSearch(msg.content)"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'
import { buildApiUrl } from '../config/apiBase'

const router = useRouter()
const authStore = useAuthStore()

const searchQuery = ref('')
const results = ref([])
const messageResults = ref([])
const loading = ref(false)
const searchInputRef = ref(null)

onMounted(() => {
  nextTick(() => {
    searchInputRef.value?.focus()
  })
})

function goBack() {
  router.push('/chat')
}

async function performSearch() {
  if (!searchQuery.value.trim()) return

  loading.value = true
  try {
    const headers = authStore.getAuthHeaders()

    const [convResponse, msgResponse] = await Promise.all([
      axios.get(buildApiUrl(`/conversations/search?q=${encodeURIComponent(searchQuery.value)}`), { headers }),
      axios.get(buildApiUrl(`/conversations/search/messages?q=${encodeURIComponent(searchQuery.value)}`), { headers })
    ])

    results.value = convResponse.data
    messageResults.value = msgResponse.data
  } catch (error) {
    console.error('[Search] Failed to search:', error)
    results.value = []
    messageResults.value = []
  } finally {
    loading.value = false
  }
}

function openConversation(convId) {
  router.push(`/chat?conversation=${convId}`)
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function highlightSearch(text) {
  if (!text || !searchQuery.value) return text
  const regex = new RegExp(`(${searchQuery.value})`, 'gi')
  return text.replace(regex, '<mark>$1</mark>')
}
</script>

<style scoped>
.search-container {
  width: 100%;
  height: 100%;
  padding: var(--space-xl);
  overflow-y: auto;
  background: var(--bg-primary);
}

.search-header {
  margin-bottom: var(--space-xl);
}

.header-row {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-sm);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  font-size: 0.875rem;
  color: var(--text-secondary);
  background: var(--bg-surface);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn:hover {
  color: var(--text-primary);
  background: var(--bg-elevated);
  border-color: var(--primary);
}

.search-header h1 {
  font-size: 1.75rem;
  color: var(--text-primary);
}

.subtitle {
  color: var(--text-secondary);
}

.search-input-wrapper {
  display: flex;
  gap: var(--space-md);
  margin-bottom: var(--space-xl);
  max-width: 700px;
}

.search-input {
  flex: 1;
  padding: var(--space-md) var(--space-lg);
  font-size: 1rem;
  color: var(--text-primary);
  background: var(--bg-surface);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.search-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.search-input::placeholder {
  color: var(--text-tertiary);
}

.search-btn {
  padding: var(--space-md) var(--space-xl);
  font-size: 1rem;
  font-weight: 600;
  color: white;
  background: var(--primary);
  border: none;
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.2s;
}

.search-btn:hover {
  background: var(--primary-hover);
}

.loading-state {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  color: var(--text-secondary);
  padding: var(--space-xl);
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--border-primary);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl);
  color: var(--text-secondary);
  text-align: center;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: var(--space-md);
}

.results-container {
  max-width: 700px;
}

.results-count {
  font-size: 0.875rem;
  color: var(--text-tertiary);
  margin-bottom: var(--space-lg);
}

.conversation-results {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  margin-bottom: var(--space-xl);
}

.conversation-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) var(--space-lg);
  background: var(--bg-surface);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.2s;
}

.conversation-item:hover {
  background: var(--bg-elevated);
  border-color: var(--primary);
}

.conversation-title {
  font-size: 1rem;
  color: var(--text-primary);
  margin-bottom: var(--space-xs);
}

.conversation-meta {
  display: flex;
  gap: var(--space-md);
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.model-tag {
  padding: 2px 8px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
}

.open-btn {
  padding: var(--space-xs) var(--space-md);
  font-size: 0.875rem;
  color: var(--primary);
  background: transparent;
  border: 1px solid var(--primary);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}

.open-btn:hover {
  background: var(--primary);
  color: white;
}

.message-results {
  border-top: 1px solid var(--border-primary);
  padding-top: var(--space-lg);
}

.results-section-title {
  font-size: 1rem;
  color: var(--text-secondary);
  margin-bottom: var(--space-md);
}

.message-item {
  padding: var(--space-md);
  background: var(--bg-surface);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-sm);
  cursor: pointer;
  transition: all 0.2s;
}

.message-item:hover {
  background: var(--bg-elevated);
  border-color: var(--primary);
}

.message-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
  font-size: 0.75rem;
}

.role-badge {
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-weight: 500;
}

.role-badge.user {
  background: var(--primary);
  color: white;
}

.role-badge.assistant {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.conv-title {
  flex: 1;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.message-preview {
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.message-preview :deep(mark) {
  background: rgba(255, 193, 7, 0.3);
  color: inherit;
  padding: 0 2px;
  border-radius: 2px;
}
</style>
