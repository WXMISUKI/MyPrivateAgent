<template>
  <div class="chat-messages">
    <div v-if="messages.length === 0 && !isLoading" class="empty-state">
      <div class="empty-icon">💬</div>
      <h2>开始新对话</h2>
      <p>输入消息与 AI 助手开始对话</p>
      <div class="command-hints">
        <p>输入 <kbd>/</kbd> 打开快捷命令</p>
      </div>
    </div>

    <ChatMessageItem
      v-for="(msg, index) in messages"
      :key="msg.id || index"
      :message="msg"
      :index="index"
      :expanded-thinking="expandedThinking"
      :feedback-reasons="feedbackReasons"
      :is-feedback-submitting="isFeedbackSubmitting(msg, index)"
      :is-negative-panel-open="isNegativePanelOpen(msg, index)"
      :selected-reasons="feedbackReasonSelections[messageKey(msg, index)] || []"
      :feedback-comment="feedbackCommentFor(msg, index)"
      :feedback-error="feedbackErrorFor(msg, index)"
      @toggle-thinking="(key) => emit('toggle-thinking', key)"
      @abort-generation="emit('abort-generation')"
      @copy-message="(content) => emit('copy-message', content)"
      @regenerate-message="(msgIndex) => emit('regenerate-message', msgIndex)"
      @quick-feedback="(message, msgIndex, feedbackType) => emit('quick-feedback', message, msgIndex, feedbackType)"
      @open-negative-feedback="(message, msgIndex) => emit('open-negative-feedback', message, msgIndex)"
      @toggle-feedback-reason="(message, msgIndex, reasonId) => emit('toggle-feedback-reason', message, msgIndex, reasonId)"
      @update-feedback-comment="(message, msgIndex, value) => emit('update-feedback-comment', message, msgIndex, value)"
      @submit-negative-feedback="(message, msgIndex) => emit('submit-negative-feedback', message, msgIndex)"
      @close-negative-feedback="emit('close-negative-feedback')"
    />
  </div>
</template>

<script setup>
import { defineAsyncComponent } from 'vue'

const ChatMessageItem = defineAsyncComponent(() => import('./ChatMessageItem.vue'))

defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  expandedThinking: {
    type: Object,
    default: () => ({})
  },
  feedbackReasons: {
    type: Array,
    default: () => []
  },
  feedbackReasonSelections: {
    type: Object,
    default: () => ({})
  },
  isFeedbackSubmitting: {
    type: Function,
    required: true
  },
  isNegativePanelOpen: {
    type: Function,
    required: true
  },
  feedbackCommentFor: {
    type: Function,
    required: true
  },
  feedbackErrorFor: {
    type: Function,
    required: true
  },
  messageKey: {
    type: Function,
    required: true
  }
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
</script>

<style scoped>
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

.command-hints {
  margin-top: var(--space-lg);
}

.command-hints p {
  font-size: 0.875rem;
  color: var(--text-tertiary);
}

.command-hints kbd {
  padding: 4px 8px;
  background: var(--bg-surface);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-size: 0.875rem;
}
</style>
