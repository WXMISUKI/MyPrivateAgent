<template>
  <div class="chat-container">
    <div class="chat-header">
      <div class="model-selector">
        <select v-model="selectedModel" @change="handleModelChange" class="model-select">
          <option v-for="model in availableModels" :key="model.name" :value="model.name">
            {{ model.display_name }}
          </option>
        </select>
      </div>
    </div>

    <div class="chat-messages" ref="messagesContainer">
      <div v-if="messages.length === 0 && !isLoading" class="empty-state">
        <div class="empty-icon">💬</div>
        <h2>开始新对话</h2>
        <p>输入消息与 AI 助手开始对话</p>
      </div>

      <div
        v-for="(msg, index) in messages"
        :key="msg.id || index"
        class="message-wrapper"
        :class="msg.role"
      >
        <div class="message-avatar">
          <span v-if="msg.role === 'user'">👤</span>
          <span v-else>🤖</span>
        </div>

        <div class="message-content">
          <div v-if="msg.role === 'assistant' && msg.isGenerating" class="generating-indicator">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
          </div>

          <div v-if="msg.role === 'assistant' && msg.thinking" class="thinking-box">
            <div class="thinking-header" @click="toggleThinking(msg.id || index)">
              <span class="thinking-icon">🧠</span>
              <span class="thinking-label">思考过程</span>
              <span class="thinking-toggle">{{ expandedThinking[msg.id || index] ? '▼' : '▶' }}</span>
            </div>
            <div v-show="expandedThinking[msg.id || index]" class="thinking-content">
              <pre>{{ msg.thinking }}</pre>
            </div>
          </div>

          <div class="message-text" v-html="renderMarkdown(msg.content)"></div>

          <div v-if="msg.role === 'assistant'" class="message-actions">
            <button @click="copyMessage(msg.content)" class="action-btn" title="复制">
              <span>📋</span>
            </button>
            <button @click="regenerateMessage(index)" class="action-btn" title="重新生成">
              <span>🔄</span>
            </button>
          </div>

          <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
        </div>
      </div>
    </div>

    <div class="chat-input-area">
      <div class="input-container">
        <textarea
          v-model="inputMessage"
          @keydown.enter.exact.prevent="handleSend"
          @keydown.shift.enter="handleNewLine"
          placeholder="输入消息..."
          rows="1"
          ref="textareaRef"
          :disabled="isLoading"
        ></textarea>
        <button
          class="send-btn"
          @click="handleSend"
          :disabled="!inputMessage.trim() || isLoading"
        >
          <span>↑</span>
        </button>
      </div>
      <div class="input-hints">
        <span>Enter 发送</span>
        <span>Shift + Enter 换行</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import { useConversationStore } from '../stores/conversation'
import axios from 'axios'

const conversationStore = useConversationStore()

const messagesContainer = ref(null)
const textareaRef = ref(null)
const inputMessage = ref('')
const expandedThinking = ref({})
const selectedModel = ref('doubao')
const availableModels = ref([
  { name: 'doubao', display_name: '豆包 (火山引擎)' },
  { name: 'deepseek-r1:7b', display_name: 'DeepSeek R1 7B' },
  { name: 'llama3.1', display_name: 'Llama 3.1' },
  { name: 'llava', display_name: 'LLaVA' }
])

const isLoading = computed(() => conversationStore.isLoading)

const messages = computed(() => {
  const conv = conversationStore.currentConversation
  return conv?.messages || []
})

const currentModelName = computed(() => {
  const conv = conversationStore.currentConversation
  return conv?.modelName || 'doubao'
})

watch(currentModelName, (newModel) => {
  if (newModel && newModel !== selectedModel.value) {
    selectedModel.value = newModel
  }
}, { immediate: true })

marked.setOptions({
  highlight: function(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true
})

function renderMarkdown(content) {
  if (!content) return ''
  const str = Array.isArray(content) ? content.join('') : String(content || '')
  return marked(str)
}

function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function toggleThinking(key) {
  expandedThinking.value[key] = !expandedThinking.value[key]
}

function copyMessage(content) {
  navigator.clipboard.writeText(content)
}

async function regenerateMessage(index) {
  if (isLoading.value) return

  const userMessage = messages.value[index - 1]
  if (!userMessage || userMessage.role !== 'user') return

  messages.value.splice(index, 2)

  await handleSendMessage(userMessage.content)
}

function handleModelChange() {
  console.log('Model changed to:', selectedModel.value)
  if (conversationStore.currentConversation) {
    conversationStore.currentConversation.modelName = selectedModel.value
    conversationStore.updateConversation(conversationStore.currentConversation.id, { modelName: selectedModel.value })
  }
}

async function handleSendMessage(content) {
  const userMessage = {
    role: 'user',
    content: content,
    timestamp: Date.now()
  }

  await conversationStore.addMessage(userMessage)
  inputMessage.value = ''

  nextTick(() => {
    if (textareaRef.value) {
      textareaRef.value.style.height = 'auto'
    }
  })

  try {
    await conversationStore.sendMessage(content, selectedModel.value)
  } finally {
    scrollToBottom()
  }
}

async function handleSend(e) {
  if (!inputMessage.value.trim() || isLoading.value) return
  await handleSendMessage(inputMessage.value.trim())
}

function handleNewLine(e) {
  // Allow default behavior for shift+enter
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

function autoResizeTextarea() {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = Math.min(textareaRef.value.scrollHeight, 120) + 'px'
  }
}

watch(inputMessage, () => {
  nextTick(autoResizeTextarea)
})

onMounted(async () => {
  scrollToBottom()

  try {
    const response = await axios.get('/api/models')
    if (response.data && Array.isArray(response.data)) {
      availableModels.value = response.data
    }
  } catch (error) {
    console.error('Failed to load models:', error)
  }
})

watch(() => messages.value.length, () => {
  scrollToBottom()
})
</script>

<style scoped>
.chat-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
}

.chat-header {
  display: flex;
  justify-content: center;
  padding: var(--space-sm) var(--space-lg);
  border-bottom: 1px solid var(--border-primary);
  background: var(--bg-secondary);
}

.model-selector {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.model-select {
  padding: var(--space-xs) var(--space-md);
  font-size: var(--text-sm);
  color: var(--text-primary);
  background: var(--bg-surface);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  cursor: pointer;
  outline: none;
  min-width: 150px;
}

.model-select:focus {
  border-color: var(--primary);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: var(--space-lg);
}

.empty-state h2 {
  font-size: 1.5rem;
  color: var(--text-primary);
  margin-bottom: var(--space-sm);
}

.message-wrapper {
  display: flex;
  gap: var(--space-md);
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
  animation: fadeInUp 0.3s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-wrapper.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  background: var(--bg-elevated);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.user .message-avatar {
  background: var(--primary);
}

.message-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  min-width: 0;
}

.message-text {
  padding: var(--space-md);
  border-radius: var(--radius-lg);
  background: var(--bg-surface);
  color: var(--text-primary);
  line-height: 1.6;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.message-text :deep(pre) {
  background: var(--bg-elevated);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  overflow-x: auto;
  margin: var(--space-sm) 0;
}

.message-text :deep(code) {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.9em;
}

.message-text :deep(p:not(:last-child)) {
  margin-bottom: var(--space-sm);
}

.message-text :deep(ul),
.message-text :deep(ol) {
  margin: var(--space-sm) 0;
  padding-left: var(--space-lg);
}

.message-text :deep(a) {
  color: var(--primary);
}

.user .message-text {
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  color: white;
}

.assistant .message-text {
  background: var(--bg-elevated);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
}

.message-actions {
  display: flex;
  gap: var(--space-sm);
  opacity: 0;
  transition: opacity 0.2s;
}

.message-wrapper:hover .message-actions {
  opacity: 1;
}

.action-btn {
  padding: var(--space-xs);
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
  opacity: 0.6;
  transition: opacity 0.2s, transform 0.2s;
}

.action-btn:hover {
  opacity: 1;
  transform: scale(1.1);
}

.message-time {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.thinking-box {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  overflow: hidden;
  margin-bottom: var(--space-sm);
  border: 1px solid var(--border-primary);
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  cursor: pointer;
  user-select: none;
  background: var(--bg-tertiary);
  transition: background 0.2s;
}

.thinking-header:hover {
  background: var(--border-primary);
}

.thinking-icon {
  font-size: 1rem;
}

.thinking-label {
  flex: 1;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.thinking-toggle {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.thinking-content {
  padding: var(--space-md);
}

.thinking-content pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-family: inherit;
  margin: 0;
}

.generating-indicator {
  display: flex;
  gap: var(--space-xs);
  padding: var(--space-sm);
}

.generating-indicator .loading-dot {
  width: 6px;
  height: 6px;
}

.loading {
  opacity: 0.7;
}

.loading-indicator {
  display: flex;
  gap: var(--space-xs);
  padding: var(--space-md);
}

.loading-dot {
  width: 8px;
  height: 8px;
  background: var(--primary);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dot:nth-child(1) { animation-delay: -0.32s; }
.loading-dot:nth-child(2) { animation-delay: -0.16s; }
.loading-dot:nth-child(3) { animation-delay: 0s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.loading-text {
  font-size: 0.875rem;
  color: var(--text-tertiary);
}

.chat-input-area {
  padding: var(--space-md) var(--space-lg);
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-primary);
}

.input-container {
  display: flex;
  gap: var(--space-sm);
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-sm);
  border: 1px solid var(--border-primary);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-container:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.input-container textarea {
  flex: 1;
  padding: var(--space-sm) var(--space-md);
  font-size: 1rem;
  color: var(--text-primary);
  background: transparent;
  border: none;
  outline: none;
  resize: none;
  max-height: 120px;
  font-family: inherit;
  line-height: 1.5;
}

.input-container textarea::placeholder {
  color: var(--text-tertiary);
}

.input-container textarea:disabled {
  opacity: 0.6;
}

.send-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--primary);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  transition: all 0.2s;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  background: var(--primary-hover);
  transform: scale(1.05);
}

.send-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-hints {
  display: flex;
  gap: var(--space-lg);
  margin-top: var(--space-sm);
  font-size: 0.75rem;
  color: var(--text-tertiary);
  justify-content: center;
}
</style>
