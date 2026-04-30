<template>
  <div class="chat-messages">
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
</style>
