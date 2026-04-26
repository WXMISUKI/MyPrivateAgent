<template>
  <div class="message-wrapper" :class="message.role">
    <div class="message-avatar">
      <span v-if="message.role === 'user'">👤</span>
      <span v-else>🤖</span>
    </div>

    <div class="message-content">
      <div v-if="message.role === 'assistant' && message.isGenerating" class="generating-indicator">
        <div class="loading-dot"></div>
        <div class="loading-dot"></div>
        <div class="loading-dot"></div>
        <button class="thinking-stop inline-stop" @click.stop="onAbortGeneration">
          停止生成
        </button>
      </div>

      <div v-if="message.role === 'assistant' && message.thinking" class="thinking-box">
        <div class="thinking-header" @click="onToggleThinking">
          <span class="thinking-icon">🧠</span>
          <span class="thinking-label">思考过程</span>
          <span class="thinking-toggle">
            <span class="toggle-arrow" :class="{ expanded: isThinkingExpanded }">▼</span>
            <button v-if="message.isGenerating" class="thinking-stop" @click.stop="onAbortGeneration">
              ⏹
            </button>
          </span>
        </div>
        <div class="thinking-content" :class="{ collapsed: !isThinkingExpanded }">
          <MessageTextRenderer :content="message.thinking" class="thinking-body" />
        </div>
      </div>

      <div v-if="message.toolCalls && message.toolCalls.length > 0" class="tool-calls-box">
        <div class="tool-calls-header">
          <span class="tool-icon">🔧</span>
          <span class="tool-label">工具调用</span>
          <span class="tool-count">{{ message.toolCalls.length }}</span>
        </div>
        <div class="tool-calls-list">
          <div
            v-for="(tool, tIdx) in message.toolCalls"
            :key="tool.id || tIdx"
            class="tool-call-item"
            :class="{ 'executing': tool.status === 'pending', 'completed': tool.status === 'completed', 'denied': tool.status === 'denied' }"
          >
            <div class="tool-call-header">
              <span class="tool-name">{{ tool.name }}</span>
              <span class="tool-status">
                <span v-if="tool.status === 'pending'" class="status-executing">⏳ 执行中</span>
                <span v-else-if="tool.status === 'completed'" class="status-done">✅</span>
                <span v-else-if="tool.status === 'denied'" class="status-denied">❌</span>
              </span>
            </div>
            <div v-if="tool.args && Object.keys(tool.args).length > 0" class="tool-args">
              <span class="args-label">参数:</span>
              <code class="args-code">{{ JSON.stringify(tool.args) }}</code>
            </div>
            <div v-if="tool.execution" class="tool-execution-meta">
              <span>source: {{ tool.execution.result_source || 'tool' }}</span>
              <span>cache: {{ tool.execution.cache_hit ? 'hit' : 'miss' }}</span>
              <span v-if="tool.execution.duration_ms !== null && tool.execution.duration_ms !== undefined">
                duration: {{ formatDuration(tool.execution.duration_ms) }}
              </span>
            </div>
            <div v-if="hasStructuredCard(tool.cardData, tool.cardSchema)" class="tool-card-wrapper">
              <AgentStructuredCard :card="tool.cardData" :card-schema="tool.cardSchema" compact />
            </div>
            <div v-if="tool.result" class="tool-result">
              <span class="result-label">结果:</span>
              <span v-if="!hasStructuredCard(tool.cardData, tool.cardSchema)" class="result-text">{{ tool.result }}</span>
              <span v-else class="result-text muted">已生成结构化天气卡片</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="hasStructuredCard(message.cardData, message.cardSchema)">
        <AgentStructuredCard :card="message.cardData" :card-schema="message.cardSchema" />
      </div>

      <AgentRuntimeDebugPanel
        v-if="message.role === 'assistant' && (message.runtimeKnowledge || message.toolExecution)"
        :runtime-knowledge="message.runtimeKnowledge"
        :tool-execution="message.toolExecution"
      />

      <MessageTextRenderer
        v-if="hasVisibleMessageText"
        :content="message.content"
        :render-mode="message.renderMode"
        :card-data="message.cardData"
        :card-schema="message.cardSchema"
        class="message-text"
      />

      <div v-if="message.role === 'assistant'" class="message-actions">
        <button @click="onCopyMessage" class="action-btn" title="复制">
          <span>📋</span>
        </button>
        <button @click="onRegenerateMessage" class="action-btn" title="重新生成">
          <span>🔄</span>
        </button>
        <button
          @click="onQuickFeedback('positive')"
          class="action-btn"
          :class="{ active: message.feedback?.type === 'positive' }"
          :disabled="isFeedbackSubmitting"
          title="有帮助"
        >
          <span>👍</span>
        </button>
        <button
          @click="onOpenNegativeFeedback"
          class="action-btn"
          :class="{ active: message.feedback?.type === 'negative' || isNegativePanelOpen }"
          :disabled="isFeedbackSubmitting"
          title="不满意"
        >
          <span>👎</span>
        </button>
      </div>

      <div v-if="message.role === 'assistant' && message.feedback" class="feedback-result" :class="`feedback-${message.feedback.type}`">
        <span>反馈已记录：{{ formatFeedbackType(message.feedback.type) }}</span>
        <span v-if="message.feedback.runtime_scope">scope: {{ message.feedback.runtime_scope }}</span>
        <span v-if="message.feedback.created_learning_id">learning: {{ message.feedback.created_learning_id }}</span>
        <span v-if="feedbackReasonLabels.length">
          原因: {{ feedbackReasonLabels.join('、') }}
        </span>
      </div>

      <div v-if="isNegativePanelOpen" class="feedback-panel">
        <div class="feedback-panel-title">选择点踩原因（可多选）</div>
        <label
          v-for="reason in feedbackReasons"
          :key="reason.id"
          class="feedback-reason-item"
        >
          <input
            type="checkbox"
            :checked="isFeedbackReasonChecked(reason.id)"
            @change="onToggleFeedbackReason(reason.id)"
          >
          <span>{{ reason.label }}</span>
        </label>
        <textarea
          class="feedback-comment"
          placeholder="补充说明（可选）"
          :value="feedbackComment"
          @input="onUpdateFeedbackComment"
        />
        <div v-if="feedbackError" class="feedback-error">{{ feedbackError }}</div>
        <div class="feedback-panel-actions">
          <button
            class="feedback-submit-btn"
            :disabled="isFeedbackSubmitting"
            @click="onSubmitNegativeFeedback"
          >
            {{ isFeedbackSubmitting ? '提交中...' : '提交反馈' }}
          </button>
          <button class="feedback-cancel-btn" :disabled="isFeedbackSubmitting" @click="onCloseNegativeFeedback">
            取消
          </button>
        </div>
      </div>

      <div class="message-time">{{ formatTime(message.timestamp) }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed, defineAsyncComponent } from 'vue'
import { hasStructuredCardSchema } from '../cards/registry'

const MessageTextRenderer = defineAsyncComponent(() => import('./MessageTextRenderer.vue'))
const AgentRuntimeDebugPanel = defineAsyncComponent(() => import('../AgentRuntimeDebugPanel.vue'))
const AgentStructuredCard = defineAsyncComponent(() => import('../cards/AgentStructuredCard.vue'))

const props = defineProps({
  message: {
    type: Object,
    required: true
  },
  index: {
    type: Number,
    required: true
  },
  expandedThinking: {
    type: Object,
    default: () => ({})
  },
  feedbackReasons: {
    type: Array,
    default: () => []
  },
  isFeedbackSubmitting: {
    type: Boolean,
    default: false
  },
  isNegativePanelOpen: {
    type: Boolean,
    default: false
  },
  selectedReasons: {
    type: Array,
    default: () => []
  },
  feedbackComment: {
    type: String,
    default: ''
  },
  feedbackError: {
    type: String,
    default: ''
  },
})

const emit = defineEmits([
  'toggle-thinking',
  'abort-generation',
  'copy-message',
  'regenerate-message',
  'quick-feedback',
  'open-negative-feedback',
  'toggle-feedback-reason',
  'update-feedback-comment',
  'submit-negative-feedback',
  'close-negative-feedback'
])

const messageKey = computed(() => {
  return String(props.message?.id ?? `assistant_${props.index}`)
})

const isThinkingExpanded = computed(() => {
  return !!props.expandedThinking[messageKey.value]
})

const hasVisibleMessageText = computed(() => {
  if (!props.message) return false
  if (props.message.renderMode === 'structured_card' && hasStructuredCard(props.message.cardData, props.message.cardSchema)) {
    return false
  }
  return !!String(props.message.content || '').trim()
})

function hasStructuredCard(cardData, cardSchema) {
  return !!cardData && hasStructuredCardSchema(cardSchema, cardData)
}

const feedbackReasonLabels = computed(() => {
  const reasonIds = props.message?.feedback?.metadata?.selected_reasons
  if (!Array.isArray(reasonIds) || reasonIds.length === 0) {
    return []
  }
  const reasonMap = new Map(props.feedbackReasons.map(item => [item.id, item.label]))
  return reasonIds.map(item => reasonMap.get(item) || String(item))
})

function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function formatDuration(value) {
  const numeric = Number(value)
  if (Number.isNaN(numeric)) return '-'
  return `${numeric.toFixed(numeric >= 10 ? 0 : 2)} ms`
}

function formatFeedbackType(type) {
  if (type === 'positive') return '点赞'
  if (type === 'negative') return '点踩'
  return '中性反馈'
}

function isFeedbackReasonChecked(reasonId) {
  return (props.selectedReasons || []).includes(reasonId)
}

function onToggleThinking() {
  emit('toggle-thinking', messageKey.value)
}

function onAbortGeneration() {
  emit('abort-generation')
}

function onCopyMessage() {
  emit('copy-message', props.message.content)
}

function onRegenerateMessage() {
  emit('regenerate-message', props.index)
}

function onQuickFeedback(type) {
  emit('quick-feedback', props.message, props.index, type)
}

function onOpenNegativeFeedback() {
  emit('open-negative-feedback', props.message, props.index)
}

function onCloseNegativeFeedback() {
  emit('close-negative-feedback')
}

function onToggleFeedbackReason(reasonId) {
  emit('toggle-feedback-reason', props.message, props.index, reasonId)
}

function onUpdateFeedbackComment(event) {
  emit('update-feedback-comment', props.message, props.index, event.target.value)
}

function onSubmitNegativeFeedback() {
  emit('submit-negative-feedback', props.message, props.index)
}
</script>

<style scoped>
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

.action-btn.active {
  opacity: 1;
  transform: scale(1.05);
}

.action-btn:disabled {
  cursor: not-allowed;
  opacity: 0.4;
}

.feedback-result {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  font-size: 0.75rem;
  line-height: 1.4;
  color: var(--text-secondary);
}

.feedback-result.feedback-positive {
  color: #22c55e;
}

.feedback-result.feedback-negative {
  color: #f97316;
}

.feedback-panel {
  margin-top: var(--space-xs);
  padding: var(--space-sm);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
}

.feedback-panel-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-xs);
}

.feedback-reason-item {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.feedback-comment {
  width: 100%;
  margin-top: var(--space-xs);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 0.8rem;
  line-height: 1.4;
  min-height: 58px;
  resize: vertical;
  padding: 6px 8px;
}

.feedback-error {
  margin-top: 4px;
  color: var(--error);
  font-size: 0.75rem;
}

.feedback-panel-actions {
  margin-top: var(--space-xs);
  display: flex;
  gap: var(--space-xs);
}

.feedback-submit-btn,
.feedback-cancel-btn {
  border: 1px solid var(--border-primary);
  background: var(--bg-surface);
  color: var(--text-primary);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  padding: 4px 10px;
  cursor: pointer;
}

.feedback-submit-btn {
  border-color: rgba(249, 115, 22, 0.45);
}

.feedback-submit-btn:disabled,
.feedback-cancel-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.message-time {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.thinking-box {
  background: var(--thinking-bg);
  border-radius: var(--radius-lg);
  overflow: hidden;
  margin-bottom: var(--space-sm);
  border: 1px solid var(--thinking-border);
  transition: all var(--transition-normal);
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  cursor: pointer;
  user-select: none;
  background: var(--thinking-header-bg);
  transition: background var(--transition-fast);
}

.thinking-header:hover {
  background: var(--thinking-header-hover);
}

.thinking-icon {
  font-size: 1rem;
}

.thinking-label {
  flex: 1;
  font-size: 0.875rem;
  color: var(--thinking-text);
  font-weight: 500;
}

.thinking-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.toggle-arrow {
  font-size: 0.7rem;
  color: var(--text-tertiary);
  transition: transform var(--transition-normal);
  display: inline-block;
}

.toggle-arrow.expanded {
  transform: rotate(180deg);
}

.thinking-stop {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.8rem;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  color: var(--error);
  opacity: 0.8;
  transition: all var(--transition-fast);
}

.thinking-stop.inline-stop {
  margin-left: var(--space-sm);
  border: 1px solid var(--error);
  padding: 4px 8px;
}

.thinking-stop:hover {
  opacity: 1;
  background: var(--error-bg);
}

.thinking-content {
  max-height: 400px;
  overflow: hidden;
  transition: max-height var(--transition-normal), opacity var(--transition-normal);
}

.thinking-content.collapsed {
  max-height: 0;
  opacity: 0;
}

.thinking-body {
  padding: var(--space-md);
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.7;
  border-top: 1px solid var(--thinking-border);
}

.thinking-body :deep(pre) {
  background: var(--bg-elevated);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  overflow-x: auto;
  margin: var(--space-sm) 0;
  font-size: 0.8rem;
}

.thinking-body :deep(code) {
  font-family: var(--font-mono);
  font-size: 0.85em;
}

.thinking-body :deep(p:not(:last-child)) {
  margin-bottom: var(--space-sm);
}

.thinking-body :deep(ul),
.thinking-body :deep(ol) {
  margin: var(--space-sm) 0;
  padding-left: var(--space-lg);
}

.tool-calls-box {
  background: var(--tool-bg);
  border: 1px solid var(--tool-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  margin-bottom: var(--space-sm);
}

.tool-calls-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--tool-header-bg);
  border-bottom: 1px solid var(--tool-border);
}

.tool-icon {
  font-size: 1rem;
}

.tool-label {
  flex: 1;
  font-size: 0.875rem;
  color: var(--tool-text);
  font-weight: 500;
}

.tool-count {
  background: var(--tool-badge-bg);
  color: var(--tool-text);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 500;
}

.tool-calls-list {
  padding: var(--space-sm);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.tool-call-item {
  background: var(--bg-surface);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  padding: var(--space-sm);
  transition: all var(--transition-fast);
}

.tool-call-item.executing {
  border-color: var(--warning);
  background: var(--warning-bg);
}

.tool-call-item.completed {
  border-color: var(--success);
}

.tool-call-item.denied {
  border-color: var(--error);
  opacity: 0.7;
}

.tool-call-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-xs);
}

.tool-name {
  font-weight: 500;
  color: var(--text-primary);
  font-size: 0.875rem;
}

.tool-status {
  font-size: 0.875rem;
}

.status-executing {
  color: var(--warning);
}

.status-done {
  color: var(--success);
}

.status-denied {
  color: var(--error);
}

.tool-args {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-top: var(--space-xs);
}

.tool-execution-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-top: var(--space-xs);
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.args-label {
  color: var(--text-tertiary);
  margin-right: var(--space-xs);
}

.args-code {
  background: var(--bg-elevated);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 0.75rem;
}

.tool-result {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-top: var(--space-xs);
  padding-top: var(--space-xs);
  border-top: 1px dashed var(--border-primary);
}

.result-label {
  color: var(--text-tertiary);
  margin-right: var(--space-xs);
}

.result-text {
  color: var(--text-secondary);
  word-break: break-word;
}

.result-text.muted {
  color: var(--text-tertiary);
}

.tool-card-wrapper {
  margin-top: var(--space-sm);
}

.generating-indicator {
  display: flex;
  gap: var(--space-xs);
  padding: var(--space-sm);
}

.generating-indicator .loading-dot {
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
</style>
