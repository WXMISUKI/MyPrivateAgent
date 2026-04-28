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
      <button v-if="showPlannerConsole" class="planner-toggle-btn" @click="plannerCollapsed = !plannerCollapsed">
        {{ plannerCollapsed ? '打开 Planner' : '隐藏 Planner' }}
      </button>
    </div>

    <div class="chat-body">
      <div class="chat-main">
        <MessageList
          ref="messagesContainer"
          :messages="messages"
          :is-loading="isLoading"
          :expanded-thinking="expandedThinking"
          :feedback-reasons="feedbackReasons"
          :feedback-reason-selections="feedbackReasonSelections"
          :is-feedback-submitting="isFeedbackSubmitting"
          :is-negative-panel-open="isNegativePanelOpen"
          :feedback-comment-for="feedbackCommentFor"
          :feedback-error-for="feedbackErrorFor"
          :message-key="messageKey"
          @toggle-thinking="toggleThinking"
          @abort-generation="abortGeneration"
          @copy-message="copyMessage"
          @regenerate-message="regenerateMessage"
          @quick-feedback="submitQuickFeedback"
          @open-negative-feedback="openNegativeFeedback"
          @toggle-feedback-reason="toggleFeedbackReason"
          @update-feedback-comment="updateFeedbackComment"
          @submit-negative-feedback="submitNegativeFeedback"
          @close-negative-feedback="closeNegativeFeedback"
        />

        <div class="chat-input-area">
          <div class="input-container">
            <textarea
              v-model="inputMessage"
              @keydown.enter.exact.prevent="handleSend"
              @keydown.shift.enter="handleNewLine"
              @keydown="handleKeyDown"
              placeholder="输入消息，或输入 / 打开快捷命令..."
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
            <span>/ 快捷命令</span>
            <button
              v-if="showPlannerConsole"
              class="inline-plan-btn"
              :disabled="plannerStore.isGenerating || !plannerDraftObjective.trim()"
              @click="generatePlanFromDraft"
            >
              {{ plannerStore.isGenerating ? '生成计划中...' : '为当前目标生成计划' }}
            </button>
          </div>
        </div>
      </div>

      <PlannerPanel
        v-if="showPlannerConsole"
        :collapsed="plannerCollapsed"
        :plan="currentPlan"
        :draft-objective="plannerDraftObjective"
        :new-item-title="newPlanItemTitle"
        :is-generating="plannerStore.isGenerating"
        :error-message="plannerError"
        @toggle-collapse="plannerCollapsed = !plannerCollapsed"
        @update:draft-objective="plannerDraftObjective = $event"
        @update:new-item-title="newPlanItemTitle = $event"
        @generate-plan="generatePlanFromDraft"
        @create-manual-plan="createManualPlan"
        @update-item-status="updatePlanItemStatus"
        @rename-item="renamePlanItem"
        @update-item-details="updatePlanItemDetails"
        @update-item-agent-role="updatePlanItemAgentRole"
        @update-item-handoff-status="updatePlanItemHandoffStatus"
        @delete-item="deletePlanItem"
        @add-item="addPlanItem"
      />
    </div>

    <CommandPalette
      :visible="showCommandPalette"
      @close="showCommandPalette = false"
      @execute="handleCommandExecute"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, defineAsyncComponent } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useConversationStore } from '../stores/conversation'
import { usePlannerStore } from '../stores/planner'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'

const CommandPalette = defineAsyncComponent(() => import('../components/CommandPalette.vue'))
const MessageList = defineAsyncComponent(() => import('../components/chat/MessageList.vue'))
const PlannerPanel = defineAsyncComponent(() => import('../components/PlannerPanel.vue'))
import { parseCommand } from '../services/commands'

const router = useRouter()
const route = useRoute()
const conversationStore = useConversationStore()
const plannerStore = usePlannerStore()
const authStore = useAuthStore()

const messagesContainer = ref(null)
const textareaRef = ref(null)
const inputMessage = ref('')
const expandedThinking = ref({})
const selectedModel = ref('doubao')
const showCommandPalette = ref(false)
const plannerCollapsed = ref(false)
const plannerDraftObjective = ref('')
const newPlanItemTitle = ref('')
const plannerError = ref('')
const availableModels = ref([])

const isLoading = computed(() => conversationStore.isLoading)
const feedbackReasons = computed(() => conversationStore.feedbackReasons || [])
const negativeFeedbackTarget = ref('')
const feedbackSubmittingKey = ref('')
const feedbackReasonSelections = ref({})
const feedbackCommentDrafts = ref({})
const feedbackErrorByKey = ref({})

const messages = computed(() => {
  const conv = conversationStore.currentConversation
  return conv?.messages || []
})

const currentPlan = computed(() => plannerStore.currentPlan)
const showPlannerConsole = computed(() => {
  const queryFlag = String(route.query.planner || '').trim() === '1'
  const localFlag = localStorage.getItem('myprivateagent.showPlannerConsole') === '1'
  return queryFlag || localFlag
})
const currentConversationId = computed(() => {
  const conv = conversationStore.currentConversation
  const normalizedId = Number(conv?.id)
  return Number.isFinite(normalizedId) ? normalizedId : null
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

function messageKey(message, index) {
  return String(message?.id ?? `assistant_${index}`)
}

function isFeedbackSubmitting(message, index) {
  return feedbackSubmittingKey.value === messageKey(message, index)
}

function isNegativePanelOpen(message, index) {
  return negativeFeedbackTarget.value === messageKey(message, index)
}

function closeNegativeFeedback() {
  negativeFeedbackTarget.value = ''
}

function openNegativeFeedback(message, index) {
  const key = messageKey(message, index)
  negativeFeedbackTarget.value = key
  feedbackErrorByKey.value[key] = ''
  feedbackReasonSelections.value[key] = []
  feedbackCommentDrafts.value[key] = ''
  if (message?.feedback?.type === 'negative') {
    const selectedReasons = message?.feedback?.metadata?.selected_reasons
    if (Array.isArray(selectedReasons)) {
      feedbackReasonSelections.value[key] = [...selectedReasons]
    }
    feedbackCommentDrafts.value[key] = message?.feedback?.comment || ''
  }
}

function toggleFeedbackReason(message, index, reasonId) {
  const key = messageKey(message, index)
  const selected = [...(feedbackReasonSelections.value[key] || [])]
  const existingIndex = selected.indexOf(reasonId)
  if (existingIndex === -1) {
    selected.push(reasonId)
  } else {
    selected.splice(existingIndex, 1)
  }
  feedbackReasonSelections.value[key] = selected
}

function updateFeedbackComment(message, index, value) {
  const key = messageKey(message, index)
  feedbackCommentDrafts.value[key] = value || ''
}

function feedbackCommentFor(message, index) {
  const key = messageKey(message, index)
  return feedbackCommentDrafts.value[key] || ''
}

function feedbackErrorFor(message, index) {
  return feedbackErrorByKey.value[messageKey(message, index)] || ''
}

async function submitFeedbackForMessage(message, index, feedbackType, selectedReasons = [], comment = '') {
  if (!message) return
  const key = messageKey(message, index)
  feedbackSubmittingKey.value = key
  feedbackErrorByKey.value[key] = ''

  try {
    await conversationStore.submitMessageFeedback({
      messageId: message.id || null,
      feedbackType,
      score: feedbackType === 'positive' ? 5 : feedbackType === 'negative' ? 1 : null,
      comment,
      selectedReasons
    })
    closeNegativeFeedback()
  } catch (error) {
    feedbackErrorByKey.value[key] = error?.response?.data?.detail || '反馈提交失败，请稍后重试'
  } finally {
    feedbackSubmittingKey.value = ''
  }
}

async function submitQuickFeedback(message, index, feedbackType) {
  await submitFeedbackForMessage(message, index, feedbackType, [])
}

async function submitNegativeFeedback(message, index) {
  const key = messageKey(message, index)
  await submitFeedbackForMessage(
    message,
    index,
    'negative',
    feedbackReasonSelections.value[key] || [],
    feedbackCommentFor(message, index)
  )
}

function toggleThinking(key) {
  expandedThinking.value[key] = !expandedThinking.value[key]
}

function abortGeneration() {
  conversationStore.abortCurrentRequest()
}

function copyMessage(content) {
  navigator.clipboard.writeText(content)
}

async function regenerateMessage(index) {
  if (isLoading.value) return

  const userMessage = messages.value[index - 1]
  if (!userMessage || userMessage.role !== 'user') return

  const aiMessage = messages.value[index]
  if (!aiMessage || aiMessage.role !== 'assistant') return

  const aiMessageId = aiMessage.id

  // Remove only the AI message at this index (keep user message)
  conversationStore.removeAssistantMessage(aiMessageId)

  // Call store's regenerateMessage to re-generate AI response
  try {
    await conversationStore.regenerateMessage(userMessage.content)
  } catch (error) {
    console.error('[Chat] Regenerate failed:', error)
  }

  scrollToBottom()
}

function handleModelChange() {
  console.log('Model changed to:', selectedModel.value)
  if (conversationStore.currentConversation) {
    conversationStore.currentConversation.modelName = selectedModel.value
    conversationStore.updateConversation(conversationStore.currentConversation.id, { modelName: selectedModel.value })
  }
}

function handleKeyDown(e) {
  if (e.key === '/') {
    const textarea = e.target
    const cursorPos = textarea.selectionStart
    const textBeforeCursor = inputMessage.value.substring(0, cursorPos)

    if (textBeforeCursor === '' || textBeforeCursor.endsWith(' ') || textBeforeCursor.endsWith('\n')) {
      e.preventDefault()
      showCommandPalette.value = true
    }
  }
}

function handleCommandExecute(command) {
  console.log('[Command] Executing:', command.action)

  switch (command.action) {
    case 'new_conversation':
      conversationStore.createConversation()
      inputMessage.value = ''
      break

    case 'clear_conversation':
      if (conversationStore.currentConversation) {
        conversationStore.clearCurrentMessages()
      }
      break

    case 'export_conversation':
      exportConversation()
      break

    case 'open_skills':
      router.push('/skills')
      break

    case 'open_learnings':
      router.push('/learnings')
      break

    case 'open_feedback_analytics':
      router.push('/feedback-analytics')
      break

    case 'open_settings':
      router.push('/settings')
      break

    case 'open_search':
      router.push('/search')
      break

    case 'show_help':
      inputMessage.value = '/help 可用命令:\n/new - 新建对话\n/clear - 清空对话\n/search - 搜索会话\n/export - 导出对话\n/skills - Skills管理\n/learnings - 学习记录\n/feedback - 反馈分析\n/settings - 设置'
      break
  }
}

async function refreshPlans() {
  try {
    await plannerStore.loadPlans({
      conversationId: currentConversationId.value
    })
  } catch (error) {
    console.error('[Planner] Load failed:', error)
  }
}

async function generatePlanFromDraft() {
  if (!plannerDraftObjective.value.trim()) return
  plannerError.value = ''

  try {
    await plannerStore.generatePlan({
      objective: plannerDraftObjective.value.trim(),
      conversationId: currentConversationId.value
    })
    newPlanItemTitle.value = ''
  } catch (error) {
    plannerError.value = error?.response?.data?.detail || '生成计划失败，请稍后重试'
  }
}

async function createManualPlan() {
  if (!plannerDraftObjective.value.trim()) return
  plannerError.value = ''

  try {
    await plannerStore.createPlan({
      objective: plannerDraftObjective.value.trim(),
      conversationId: currentConversationId.value
    })
    newPlanItemTitle.value = ''
  } catch (error) {
    plannerError.value = error?.response?.data?.detail || '创建计划失败，请稍后重试'
  }
}

async function addPlanItem() {
  if (!currentPlan.value || !newPlanItemTitle.value.trim()) return
  plannerError.value = ''

  try {
    await plannerStore.addPlanItem(currentPlan.value.id, {
      title: newPlanItemTitle.value.trim(),
      details: '',
      status: 'pending'
    })
    newPlanItemTitle.value = ''
  } catch (error) {
    plannerError.value = error?.response?.data?.detail || '添加计划项失败'
  }
}

async function updatePlanItemStatus(item, status) {
  if (!currentPlan.value || !item) return
  plannerError.value = ''

  try {
    await plannerStore.updatePlanItem(currentPlan.value.id, item.id, { status })
  } catch (error) {
    plannerError.value = error?.response?.data?.detail || '更新计划状态失败'
  }
}

async function renamePlanItem(item, title) {
  if (!currentPlan.value || !item || !String(title || '').trim()) return
  plannerError.value = ''

  try {
    await plannerStore.updatePlanItem(currentPlan.value.id, item.id, { title: String(title).trim() })
  } catch (error) {
    plannerError.value = error?.response?.data?.detail || '更新标题失败'
  }
}

async function updatePlanItemDetails(item, details) {
  if (!currentPlan.value || !item) return
  plannerError.value = ''

  try {
    await plannerStore.updatePlanItem(currentPlan.value.id, item.id, { details: String(details || '').trim() })
  } catch (error) {
    plannerError.value = error?.response?.data?.detail || '更新说明失败'
  }
}

async function updatePlanItemAgentRole(item, agentRole) {
  if (!currentPlan.value || !item) return
  plannerError.value = ''

  const ownerMap = {
    general: '主智能体',
    planner: '规划子智能体',
    frontend: '前端子智能体',
    backend: '后端子智能体',
    qa: '测试子智能体',
    docs: '文档子智能体'
  }

  try {
    await plannerStore.updatePlanItem(currentPlan.value.id, item.id, {
      agent_role: agentRole,
      owner: ownerMap[agentRole] || '主智能体',
      handoff_status: agentRole === 'general' ? 'unassigned' : (item.handoff_status || 'ready')
    })
  } catch (error) {
    plannerError.value = error?.response?.data?.detail || '更新执行角色失败'
  }
}

async function updatePlanItemHandoffStatus(item, handoffStatus) {
  if (!currentPlan.value || !item) return
  plannerError.value = ''

  try {
    await plannerStore.updatePlanItem(currentPlan.value.id, item.id, {
      handoff_status: handoffStatus
    })
  } catch (error) {
    plannerError.value = error?.response?.data?.detail || '更新交接状态失败'
  }
}

async function deletePlanItem(item) {
  if (!currentPlan.value || !item) return
  plannerError.value = ''

  try {
    await plannerStore.deletePlanItem(currentPlan.value.id, item.id)
  } catch (error) {
    plannerError.value = error?.response?.data?.detail || '删除计划项失败'
  }
}

function exportConversation() {
  const conv = conversationStore.currentConversation
  if (!conv || conv.messages.length === 0) {
    alert('没有对话可导出')
    return
  }

  const exportData = {
    title: conv.title || '未命名对话',
    model: conv.modelName,
    exportedAt: new Date().toISOString(),
    messages: conv.messages.map(m => ({
      role: m.role,
      content: m.content,
      timestamp: new Date(m.timestamp).toISOString()
    }))
  }

  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `conversation_${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
}

async function handleSendMessage(content) {
  const parsed = parseCommand(content)
  if (parsed) {
    if (parsed.error === 'unknown_command') {
      alert(`未知命令: /${parsed.commandId}`)
      return
    }
  }

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

  if (inputMessage.value.trim().startsWith('/')) {
    const parsed = parseCommand(inputMessage.value.trim())
    if (parsed && !parsed.command.hasParam) {
      handleCommandExecute(parsed.command)
      inputMessage.value = ''
      return
    }
  }

  await handleSendMessage(inputMessage.value.trim())
}

function handleNewLine(e) {
  // Allow default behavior for shift+enter
}

function scrollToBottom() {
  nextTick(() => {
    const container = messagesContainer.value?.$el || messagesContainer.value
    if (container) {
      container.scrollTop = container.scrollHeight
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
      const defaultModel = response.data.find(model => model.is_default)?.name
      if (!conversationStore.currentConversation && defaultModel) {
        selectedModel.value = defaultModel
      }
    }
  } catch (error) {
    console.error('Failed to load models:', error)
  }

  if (authStore.runtimeProfile?.default_model && !conversationStore.currentConversation) {
    selectedModel.value = authStore.runtimeProfile.default_model
  }

  plannerDraftObjective.value = inputMessage.value.trim()
  if (showPlannerConsole.value) {
    await refreshPlans()
  }
})

watch(() => messages.value.length, () => {
  scrollToBottom()
})

watch(currentConversationId, async () => {
  if (showPlannerConsole.value) {
    await refreshPlans()
  }
}, { immediate: false })

watch(inputMessage, (value) => {
  if (!currentPlan.value) {
    plannerDraftObjective.value = value.trim()
  }
})
</script>

<style scoped>
.chat-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-sm) var(--space-lg);
  border-bottom: 1px solid var(--border-primary);
  background: var(--bg-secondary);
}

.chat-body {
  flex: 1;
  display: flex;
  min-height: 0;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.model-selector {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.planner-toggle-btn,
.inline-plan-btn {
  border: 1px solid var(--border-primary);
  background: var(--bg-surface);
  color: var(--text-primary);
  border-radius: var(--radius-md);
  cursor: pointer;
}

.planner-toggle-btn {
  padding: var(--space-xs) var(--space-md);
  font-size: var(--text-sm);
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
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-lg);
  margin-top: var(--space-sm);
  font-size: 0.75rem;
  color: var(--text-tertiary);
  justify-content: center;
}

.inline-plan-btn {
  padding: 6px 10px;
  font-size: 0.75rem;
}

@media (max-width: 1100px) {
  .chat-body {
    flex-direction: column;
  }
}
</style>
