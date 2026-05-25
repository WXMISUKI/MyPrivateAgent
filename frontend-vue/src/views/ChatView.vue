<template>
  <div class="chat-container">
    <div class="chat-header">
      <div class="chat-header-controls">
      <div class="model-selector" ref="modelSelectorRef">
        <button class="model-trigger" @click="modelDropdownOpen = !modelDropdownOpen">
          <span class="model-name">{{ currentModelDisplay }}</span>
          <span class="model-provider" v-if="currentModelProvider">{{ currentModelProvider }}</span>
          <span class="dropdown-arrow">{{ modelDropdownOpen ? '▲' : '▼' }}</span>
        </button>
        <div v-if="modelDropdownOpen" class="model-dropdown">
          <div
            v-for="model in availableModels"
            :key="model.name"
            class="model-option"
            :class="{ active: selectedModel === model.name, unavailable: model.available === false }"
            @click="selectModel(model)"
          >
            <span class="option-dot" :class="{ online: model.available !== false }"></span>
            <div class="option-info">
              <span class="option-name">{{ model.display_name }}</span>
              <span class="option-provider">{{ model.provider_label || model.provider || '' }}</span>
            </div>
          </div>
        </div>
      </div>
        <label class="runtime-trace-toggle" :class="{ active: settingsStore.enableMainChatRuntimeTrace }">
          <input
            type="checkbox"
            :checked="settingsStore.enableMainChatRuntimeTrace"
            @change="settingsStore.setEnableMainChatRuntimeTrace($event.target.checked)"
          >
          <span class="toggle-label">Runtime Trace</span>
          <span class="toggle-hint">专家模式</span>
        </label>
      </div>
      <button v-if="showPlannerConsole" class="planner-toggle-btn" @click="plannerCollapsed = !plannerCollapsed">
        {{ plannerCollapsed ? '打开 Planner' : '隐藏 Planner' }}
      </button>
    </div>
    <div v-if="healthAlertLevel" class="chat-health-alert" :class="`risk-${healthAlertLevel}`">
      {{ healthAlertText }}
      <span v-if="healthUpdatedAt" class="alert-updated-at">更新时间 {{ new Date(healthUpdatedAt).toLocaleTimeString() }}</span>
    </div>

    <div class="chat-body">
      <div class="chat-main">
        <div v-if="!messages.length && !isLoading" class="empty-state">
          <div class="empty-icon">💬</div>
          <h2 class="empty-title">开始新对话</h2>
          <p class="empty-desc">输入你的问题，我会尽力帮助你。支持多轮对话、工具调用和计划执行。</p>
          <div class="empty-hints">
            <button class="hint-chip" @click="inputMessage = '你好，你能帮我做什么？'">你能帮我做什么？</button>
            <button class="hint-chip" @click="inputMessage = '今天天气怎么样？'">查询天气</button>
            <button class="hint-chip" @click="inputMessage = '帮我制定一个学习计划'">制定计划</button>
          </div>
        </div>
        <MessageList
          v-else
          ref="messagesContainer"
          :messages="messages"
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
            <span v-if="settingsStore.enableMainChatRuntimeTrace">
              已附加 main_chat runtime trace 上下文
            </span>
            <span v-if="showPlannerConsole && latestPlannerPolicyHint">
              当前策略 Provider: {{ latestPlannerPolicyHint.selected_provider }} ({{ latestPlannerPolicyHint.reason }})
            </span>
            <span v-if="showPlannerConsole && latestPlannerRouteSummary">
              路由落点: {{ latestPlannerRouteSummary.providerName }} / {{ latestPlannerRouteSummary.modelName }} · 切换{{ latestPlannerRouteSummary.totalSwitches }}次
            </span>
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
import { ref, computed, watch, nextTick, onMounted, onUnmounted, defineAsyncComponent } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useConversationStore } from '../stores/conversation'
import { usePlannerStore } from '../stores/planner'
import { useAuthStore } from '../stores/auth'
import { useSettingsStore } from '../stores/settings'
import axios from 'axios'
import { buildApiUrl } from '../config/apiBase'
import { healthApi } from '../api'
import { buildRecentSnapshotCommandsHelp } from '../services/governanceSnapshotCommands'

const CommandPalette = defineAsyncComponent(() => import('../components/CommandPalette.vue'))
const MessageList = defineAsyncComponent(() => import('../components/chat/MessageList.vue'))
const PlannerPanel = defineAsyncComponent(() => import('../components/PlannerPanel.vue'))
import { parseCommand } from '../services/commands'

const router = useRouter()
const route = useRoute()
const conversationStore = useConversationStore()
const plannerStore = usePlannerStore()
const authStore = useAuthStore()
const settingsStore = useSettingsStore()

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
const modelDropdownOpen = ref(false)
const modelSelectorRef = ref(null)
const healthFailover = ref(null)
const healthUpdatedAt = ref(null)
let healthPollTimer = null

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

const currentModelDisplay = computed(() => {
  const model = availableModels.value.find(m => m.name === selectedModel.value)
  return model?.display_name || selectedModel.value
})

const currentModelProvider = computed(() => {
  const model = availableModels.value.find(m => m.name === selectedModel.value)
  return model?.provider_label || model?.provider || ''
})

const latestPlannerPolicyHint = computed(() => {
  const items = currentPlan.value?.items || []
  const activeItem = items.find(item => item.status === 'in_progress') || items[0]
  const traces = [...(activeItem?.run_trace || [])].reverse()
  const policyTrace = traces.find(entry => entry?.source === 'policy' && entry?.event_type === 'subagent_policy_selected')
  return policyTrace?.payload?.provider_hint || null
})

const latestPlannerRouteSummary = computed(() => {
  const items = currentPlan.value?.items || []
  const activeItem = items.find(item => item.status === 'in_progress') || items[0]
  const children = activeItem?.child_executions || []
  if (!children.length) return null
  const switched = children.filter(child => Number(child.provider_switch_count || 0) > 0)
  const totalSwitches = switched.reduce((sum, child) => sum + Number(child.provider_switch_count || 0), 0)
  const latest = [...children].reverse().find(child => child.provider_name || child.model_name) || children[0]
  if (!latest) return null
  return {
    totalSwitches,
    providerName: latest.provider_name || 'unknown',
    modelName: latest.model_name || 'unknown',
    switchedChildren: switched.length
  }
})

const healthAlertLevel = computed(() => {
  if (settingsStore.muteHealthAlerts) return ''
  const level = String(healthFailover.value?.alert_level || '').trim().toLowerCase()
  if (level === 'high' || level === 'medium') return level
  return ''
})

const healthAlertText = computed(() => {
  if (healthAlertLevel.value === 'high') return '系统告警：Provider Failover 高风险，请优先检查上游模型服务稳定性。'
  if (healthAlertLevel.value === 'medium') return '系统提醒：Provider Failover 中风险，建议关注近期路由切换。'
  return ''
})

function selectModel(model) {
  if (model.available === false) return
  selectedModel.value = model.name
  modelDropdownOpen.value = false
  handleModelChange()
}

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

function normalizeCommandExecution(request) {
  if (request?.command) {
    return {
      command: request.command,
      params: Array.isArray(request.params) ? request.params : []
    }
  }
  return {
    command: request,
    params: []
  }
}

function resolveDoctorMode(params = []) {
  const mode = String(params[0] || '').trim().toLowerCase()
  if (mode === 'governance' || mode === 'gaps' || mode === 'gate') {
    return 'governance'
  }
  return 'startup'
}

function resolveDoctorSeverity(params = []) {
  const hint = params.map(item => String(item || '').trim().toLowerCase())
  return hint.includes('warning') ? 'warning' : 'all'
}

function resolveGovernanceSeverity(params = []) {
  const mode = String(params[0] || '').trim().toLowerCase()
  return mode === 'warning' ? 'warning' : 'all'
}

function resolveSnapshotId(params = []) {
  const first = String(params[0] || '').trim().toLowerCase()
  if (first === 'snapshot') {
    return String(params[1] || '').trim()
  }
  return ''
}

function resolveDirectSnapshotId(params = []) {
  const first = String(params[0] || '').trim()
  if (!first) {
    return ''
  }
  if (first.toLowerCase() === 'snapshot') {
    return String(params[1] || '').trim()
  }
  return first
}

function buildGovernanceRoute(domain, params = []) {
  const query = new URLSearchParams({
    tab: 'advanced',
    governance_filter: domain,
  })
  const snapshotId = resolveSnapshotId(params)
  if (snapshotId) {
    query.set('governance_snapshot', snapshotId)
  }
  const severity = resolveGovernanceSeverity(params)
  if (severity === 'warning' && !snapshotId) {
    query.set('governance_severity', 'warning')
  }
  return `/settings?${query.toString()}`
}

function handleCommandExecute(request) {
  const { command, params } = normalizeCommandExecution(request)
  console.log('[Command] Executing:', command.action, params)

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

    case 'open_planner':
      showPlannerConsole.value = true
      break

    case 'open_gaps':
      router.push(buildGovernanceRoute('governance', params))
      break

    case 'open_permissions':
      router.push(buildGovernanceRoute('permission', params))
      break

    case 'open_mcp':
      router.push(buildGovernanceRoute('mcp', params))
      break

    case 'open_memory':
      router.push('/settings?tab=advanced')
      break

    case 'open_snapshot':
      {
        const snapshotId = resolveDirectSnapshotId(params)
        if (!snapshotId) {
          router.push('/settings?tab=advanced')
          break
        }
        router.push(`/settings?tab=advanced&governance_snapshot=${encodeURIComponent(snapshotId)}`)
      }
      break

    case 'open_model':
      if (params.length > 0) {
        const requestedModel = String(params[0] || '').trim()
        const targetModel = availableModels.value.find(model => String(model.name || '').toLowerCase() === requestedModel.toLowerCase())
        if (targetModel) {
          selectModel(targetModel)
          break
        }
      }
      router.push('/settings?tab=model')
      break

    case 'run_doctor':
      {
        const query = new URLSearchParams({
          tab: 'advanced',
          doctor: resolveDoctorMode(params),
        })
        if (resolveDoctorSeverity(params) === 'warning') {
          query.set('governance_severity', 'warning')
        }
        router.push(`/settings?${query.toString()}`)
      }
      break

    case 'open_search':
      if (params.length > 0) {
        router.push(`/search?q=${encodeURIComponent(params.join(' '))}`)
        break
      }
      router.push('/search')
      break

    case 'show_help':
      inputMessage.value = buildHelpMessage()
      break
  }
}

function buildHelpMessage() {
  const baseLines = [
    '/help 可用命令:',
    '/new - 新建对话',
    '/clear - 清空对话',
    '/search <query> - 搜索会话',
    '/export - 导出对话',
    '/skills - Skills管理',
    '/learnings - 学习记录',
    '/feedback - 反馈分析',
    '/settings - 设置',
    '/plan - 打开计划',
    '/gaps <all|warning|snapshot <id>> - 查看整改治理',
    '/memory - 查看记忆',
    '/mcp <all|warning|snapshot <id>> - 查看MCP治理',
    '/permissions <all|warning|snapshot <id>> - 查看权限治理',
    '/snapshot <id> - 打开治理快照定位视图',
    '/model <name> - 切换模型',
    '/doctor <startup|governance> [warning] - 运行检查'
  ]
  const recentHelp = buildRecentSnapshotCommandsHelp(3)
  if (recentHelp) {
    baseLines.push('', recentHelp)
  }
  return baseLines.join('\n')
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
    if (parsed && !parsed.error) {
      handleCommandExecute(parsed)
      if (parsed.command?.action !== 'show_help') {
        inputMessage.value = ''
      }
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

async function loadHealthAlert() {
  try {
    const response = await healthApi.getHealth()
    healthFailover.value = response.data?.failover || null
    healthUpdatedAt.value = Date.now()
  } catch (error) {
    console.error('Failed to load health alert:', error)
    healthFailover.value = null
  }
}

watch(inputMessage, () => {
  nextTick(autoResizeTextarea)
})

onMounted(async () => {
  scrollToBottom()

  document.addEventListener('click', (e) => {
    if (modelSelectorRef.value && !modelSelectorRef.value.contains(e.target)) {
      modelDropdownOpen.value = false
    }
  })

  try {
    const response = await axios.get(buildApiUrl('/models'))
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

  await loadHealthAlert()
  healthPollTimer = setInterval(() => {
    loadHealthAlert()
  }, 60000)

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

onUnmounted(() => {
  if (healthPollTimer) {
    clearInterval(healthPollTimer)
    healthPollTimer = null
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

.chat-header-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.chat-body {
  flex: 1;
  display: flex;
  min-height: 0;
}

.chat-health-alert {
  margin: 8px var(--space-lg) 0;
  border-radius: var(--radius-md);
  padding: 8px 10px;
  font-size: 0.8rem;
  border: 1px solid var(--border-primary);
  background: var(--bg-secondary);
  color: var(--text-secondary);
}

.chat-health-alert.risk-medium {
  border-color: rgba(245, 158, 11, 0.45);
  background: rgba(245, 158, 11, 0.1);
  color: #b45309;
}

.chat-health-alert.risk-high {
  border-color: rgba(239, 68, 68, 0.45);
  background: rgba(239, 68, 68, 0.1);
  color: #b91c1c;
}

.alert-updated-at {
  margin-left: 10px;
  font-size: 0.72rem;
  opacity: 0.8;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.model-selector {
  position: relative;
}

.runtime-trace-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  background: var(--bg-surface);
  color: var(--text-secondary);
  font-size: 0.8rem;
  cursor: pointer;
}

.runtime-trace-toggle.active {
  border-color: rgba(16, 185, 129, 0.45);
  background: rgba(16, 185, 129, 0.08);
  color: #047857;
}

.runtime-trace-toggle input {
  margin: 0;
}

.toggle-label {
  font-weight: 600;
  color: var(--text-primary);
}

.toggle-hint {
  font-size: 0.72rem;
  color: var(--text-tertiary);
}

.model-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--bg-surface);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}

.model-trigger:hover {
  border-color: var(--primary);
}

.model-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
}

.model-provider {
  font-size: 0.7rem;
  color: var(--text-tertiary);
  padding: 1px 6px;
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
}

.dropdown-arrow {
  font-size: 0.6rem;
  color: var(--text-tertiary);
  margin-left: 2px;
}

.model-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  min-width: 240px;
  background: var(--bg-surface);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  z-index: 100;
  max-height: 300px;
  overflow-y: auto;
}

.model-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  cursor: pointer;
  transition: background 0.15s;
}

.model-option:hover {
  background: var(--bg-secondary);
}

.model-option.active {
  background: rgba(var(--primary-rgb, 99, 102, 241), 0.1);
}

.model-option.unavailable {
  opacity: 0.4;
  cursor: not-allowed;
}

.option-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #6b7280;
  flex-shrink: 0;
}

.option-dot.online {
  background: #22c55e;
}

.option-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.option-name {
  font-size: 0.875rem;
  color: var(--text-primary);
}

.option-provider {
  font-size: 0.7rem;
  color: var(--text-tertiary);
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

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
  padding: var(--space-xl);
}

.empty-icon {
  font-size: 3rem;
  opacity: 0.5;
}

.empty-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.empty-desc {
  font-size: 0.875rem;
  text-align: center;
  max-width: 400px;
  line-height: 1.5;
}

.empty-hints {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
  justify-content: center;
}

.hint-chip {
  padding: 8px 16px;
  font-size: 0.8rem;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.2s;
}

.hint-chip:hover {
  color: var(--primary);
  border-color: var(--primary);
  background: rgba(var(--primary-rgb, 99, 102, 241), 0.08);
}
</style>
