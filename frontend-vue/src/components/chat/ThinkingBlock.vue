<template>
  <div class="thinking-block" :class="{ expanded: isExpanded, generating: isGenerating }">
    <!-- 折叠头部 -->
    <div class="thinking-header" @click="$emit('toggle')">
      <div class="thinking-header-left">
        <div class="thinking-icon-wrapper" :class="{ spinning: isGenerating }">
          <svg v-if="isGenerating" class="thinking-spinner" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="60 40" />
          </svg>
          <svg v-else class="thinking-check" viewBox="0 0 24 24" fill="none">
            <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" />
          </svg>
        </div>
        <span class="thinking-label">
          {{ isGenerating ? '思考中...' : '已深度思考' }}
        </span>
      </div>
      <div class="thinking-header-right">
        <span v-if="duration" class="thinking-duration">耗时 {{ duration }}</span>
        <svg class="thinking-chevron" :class="{ rotated: isExpanded }" viewBox="0 0 24 24" fill="none">
          <path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
    </div>

    <!-- 展开内容 -->
    <div class="thinking-body-wrapper" :class="{ visible: isExpanded }">
      <div class="thinking-body">
        <div class="thinking-content" ref="contentRef">
          <slot />
        </div>
        <div v-if="isGenerating" class="thinking-cursor"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  isExpanded: { type: Boolean, default: false },
  isGenerating: { type: Boolean, default: false },
  duration: { type: String, default: '' },
})

defineEmits(['toggle'])

const contentRef = ref(null)

// 流式内容时自动滚动到底部
watch(() => props.isGenerating, async () => {
  if (props.isExpanded && contentRef.value) {
    await nextTick()
    contentRef.value.scrollTop = contentRef.value.scrollHeight
  }
})
</script>

<style scoped>
.thinking-block {
  border: 1px solid var(--border-primary);
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 12px;
  background: var(--bg-surface);
  transition: border-color 0.2s;
}

.thinking-block.generating {
  border-color: rgba(99, 102, 241, 0.3);
}

.thinking-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  user-select: none;
  transition: background 0.15s;
}

.thinking-header:hover {
  background: var(--bg-elevated);
}

.thinking-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.thinking-icon-wrapper {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
}

.thinking-spinner {
  width: 20px;
  height: 20px;
  animation: spin 1s linear infinite;
}

.thinking-check {
  width: 20px;
  height: 20px;
  color: #22c55e;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.thinking-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
}

.thinking-header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.thinking-duration {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.thinking-chevron {
  width: 16px;
  height: 16px;
  color: var(--text-tertiary);
  transition: transform 0.2s;
}

.thinking-chevron.rotated {
  transform: rotate(180deg);
}

.thinking-body-wrapper {
  max-height: 0;
  opacity: 0;
  overflow: hidden;
  transition: max-height 0.3s ease, opacity 0.2s ease;
}

.thinking-body-wrapper.visible {
  max-height: 500px;
  opacity: 1;
}

.thinking-body {
  border-top: 1px solid var(--border-primary);
  padding: 16px;
  position: relative;
}

.thinking-content {
  max-height: 400px;
  overflow-y: auto;
  font-size: 0.875rem;
  line-height: 1.7;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
}

.thinking-content::-webkit-scrollbar {
  width: 4px;
}

.thinking-content::-webkit-scrollbar-track {
  background: transparent;
}

.thinking-content::-webkit-scrollbar-thumb {
  background: var(--border-primary);
  border-radius: 2px;
}

.thinking-cursor {
  display: inline-block;
  width: 2px;
  height: 16px;
  background: var(--primary);
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>
