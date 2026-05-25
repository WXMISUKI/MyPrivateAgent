import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import storage from '../services/storage'
import { createStreamingEventParser, normalizeAgentEvent } from '../services/agentEvents'
import { usePlannerStore } from './planner'
import { useSettingsStore } from './settings'
import axios from 'axios'
import { buildApiUrl } from '../config/apiBase'

export const useConversationStore = defineStore('conversation', () => {
  const plannerStore = usePlannerStore()
  const settingsStore = useSettingsStore()
  const conversations = ref([])
  const activeId = ref(null)
  const searchQuery = ref('')
  const isLoading = ref(false)

  let currentRequestHandle = null
  let lastDataTimestamp = null
  let timeoutCheckInterval = null
  const STREAM_TIMEOUT_MS = 60000

  const feedbackReasons = [
    { id: 'irrelevant', label: '回答与问题无关' },
    { id: 'incorrect', label: '内容不正确' },
    { id: 'incomplete', label: '信息不完整' },
    { id: 'not_helpful', label: '不够实用' },
    { id: 'format_issue', label: '格式不符合预期' },
    { id: 'other', label: '其他问题' }
  ]

  function getAuthHeaders() {
    const token = localStorage.getItem('token')
    if (!token) {
      return {}
    }
    return {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  }

  function buildMainChatExecutionContext(currentModel) {
    if (!settingsStore.enableMainChatRuntimeTrace) {
      return null
    }
    return {
      run_id: `manual-chat-${Date.now()}`,
      run_kind: 'chat',
      enable_main_chat_query_control_timeline: true,
      ...(currentModel ? { agent_id: `chat-ui-${currentModel}` } : {})
    }
  }

  function applyAssistantRenderMetadata(message, event) {
    if (event.render_mode) {
      message.renderMode = event.render_mode
    }
    if (event.card) {
      message.cardData = event.card
    }
    if (event.card_schema) {
      message.cardSchema = event.card_schema
    }
    if (message.renderMode === 'structured_card' && !message.cardData) {
      message.renderMode = 'plain_text'
    }
  }

  function applyAssistantDebugMetadata(message, event) {
    if (event.tool_execution) {
      message.toolExecution = { ...event.tool_execution }
    } else if (event.cache_hit !== null || event.duration_ms !== null || event.result_source || event.status) {
      message.toolExecution = {
        cache_hit: event.cache_hit ?? false,
        duration_ms: event.duration_ms ?? null,
        result_source: event.result_source || '',
        status: event.status || ''
      }
    }

    if (event.type === 'status' && event.status_kind === 'runtime_knowledge') {
      message.runtimeKnowledge = {
        scope: event.scope || 'global',
        promptCount: event.prompt_count || 0,
        practiceCount: event.practice_count || 0,
        selectedItems: Array.isArray(event.selected_items) ? event.selected_items : [],
        skippedItems: Array.isArray(event.skipped_items) ? event.skipped_items : []
      }
    }

    if (event.completion_check) {
      message.completionCheck = { ...event.completion_check }
    }
    if (event.framework_notice !== undefined) {
      message.frameworkNotice = Boolean(event.framework_notice)
    }
  }

  function applyExecutionProgress(message, event) {
    if (event.type !== 'status' || event.status_kind !== 'execution_progress') {
      return
    }
    const content = String(event.content || '').trim()
    if (!content) {
      return
    }
    message.executionProgress = Array.isArray(message.executionProgress) ? [...message.executionProgress] : []
    const phase = event.phase || ''
    const duplicate = message.executionProgress.find(
      item => item.phase === phase && item.content === content
    )
    if (duplicate) {
      return
    }
    message.executionProgress.push({
      phase,
      content,
      timestamp: Date.now()
    })
  }

  function applyMessageFeedback(message, feedback) {
    if (!feedback) {
      return
    }
    message.feedback = {
      type: feedback.feedback_type || feedback.type || '',
      score: feedback.score ?? null,
      comment: feedback.comment || '',
      runtime_artifact_id: feedback.runtime_artifact_id || null,
      runtime_scope: feedback.runtime_scope || null,
      selected_items: Array.isArray(feedback.selected_items) ? feedback.selected_items : [],
      stop_reason: feedback.stop_reason || '',
      created_learning_id: feedback.created_learning_id || null,
      metadata: feedback.feedback_metadata || null
    }
  }

  function upsertToolCall(message, event, status = 'completed') {
    message.toolCalls = message.toolCalls || []
    const toolCall = message.toolCalls.find(t => t.name === event.name && t.status === 'pending')
    const execution = event.tool_execution || {
      cache_hit: event.cache_hit ?? false,
      duration_ms: event.duration_ms ?? null,
      result_source: event.result_source || '',
      status: event.status || ''
    }

    if (toolCall) {
      toolCall.status = status
      toolCall.result = event.result
      toolCall.toolSpec = event.tool_spec || null
      toolCall.cardData = event.card || null
      toolCall.cardSchema = event.card_schema || ''
      toolCall.execution = execution
    } else {
      message.toolCalls.push({
        id: `tool_${Date.now()}`,
        name: event.name,
        status,
        result: event.result,
        toolSpec: event.tool_spec || null,
        cardData: event.card || null,
        cardSchema: event.card_schema || '',
        execution
      })
    }
  }

  const currentConversation = computed(() => {
    if (!activeId.value && conversations.value.length > 0) {
      return conversations.value[0]
    }
    return conversations.value.find(c => String(c.id) === String(activeId.value)) || null
  })

  const groupedConversations = computed(() => {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const yesterday = new Date(today - 24 * 60 * 60 * 1000)
    const weekAgo = new Date(today - 7 * 24 * 60 * 60 * 1000)

    const groups = {
      today: { label: '今天', conversations: [] },
      yesterday: { label: '昨天', conversations: [] },
      week: { label: '本周', conversations: [] },
      older: { label: '更早', conversations: [] }
    }

    let filtered = conversations.value

    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      filtered = conversations.value.filter(c =>
        c.title.toLowerCase().includes(query) ||
        c.messages.some(m => m.content.toLowerCase().includes(query))
      )
    }

    filtered.forEach(conv => {
      const date = new Date(conv.updatedAt)
      if (date >= today) {
        groups.today.conversations.push(conv)
      } else if (date >= yesterday) {
        groups.yesterday.conversations.push(conv)
      } else if (date >= weekAgo) {
        groups.week.conversations.push(conv)
      } else {
        groups.older.conversations.push(conv)
      }
    })

    return Object.values(groups).filter(g => g.conversations.length > 0)
  })

  function saveToStorage() {
    try {
      storage.saveConversations(conversations.value)
      storage.setActiveId(activeId.value)
      console.log('[Storage] Saved:', conversations.value.length, 'conversations, activeId:', activeId.value)
    } catch (error) {
      console.error('[Storage] Save failed:', error)
    }
  }

  function loadFromStorage() {
    const loaded = storage.loadConversations()
    conversations.value = loaded.map(conv => ({
      ...conv,
      messages: conv.messages || [],
      createdAt: conv.createdAt || Date.now(),
      updatedAt: conv.updatedAt || Date.now()
    }))
    const savedActiveId = storage.getActiveId()
    if (savedActiveId) {
      activeId.value = savedActiveId
    }
    console.log('[Conversation] Loaded from storage:', conversations.value.length, 'conversations')
  }

  function loadConversations() {
    loadFromStorage()
  }

  function createConversation(title = '新对话') {
    const newConv = {
      id: `local_${Date.now()}`,
      title: title,
      modelName: 'doubao',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now()
    }
    conversations.value.unshift(newConv)
    activeId.value = newConv.id
    saveToStorage()
    return newConv
  }

  async function deleteConversation(id) {
    conversations.value = conversations.value.filter(c => c.id !== id)
    if (activeId.value === id) {
      activeId.value = conversations.value[0]?.id || null
    }
    saveToStorage()
  }

  function setActiveConversation(id) {
    activeId.value = id
    saveToStorage()
  }

  function setSearchQuery(query) {
    searchQuery.value = query
  }

  async function submitMessageFeedback({
    messageId = null,
    feedbackType,
    score = null,
    comment = '',
    selectedReasons = []
  } = {}) {
    if (!currentConversation.value) {
      throw new Error('当前没有活动会话')
    }

    const conversationId = Number(currentConversation.value.id)
    if (!Number.isFinite(conversationId)) {
      throw new Error('会话尚未同步，暂不可提交反馈')
    }

    if (!['positive', 'negative', 'neutral'].includes(feedbackType)) {
      throw new Error('feedback_type 无效')
    }

    const payload = {
      feedback_type: feedbackType,
      score: score ?? null,
      comment: comment ? comment.trim() : null
    }

    if (Array.isArray(selectedReasons) && selectedReasons.length > 0) {
      payload.selected_reasons = selectedReasons.map(reason => String(reason).trim()).filter(Boolean)
    }

    if (messageId) {
      const normalizedMessageId = Number(messageId)
      if (Number.isFinite(normalizedMessageId)) {
        payload.message_id = normalizedMessageId
      }
    }

    try {
      const response = await axios.post(
        buildApiUrl(`/conversations/${conversationId}/feedback`),
        payload,
        {
          headers: getAuthHeaders()
        }
      )

      const msgIndex = currentConversation.value.messages.findIndex(m => m.id === messageId)
      if (msgIndex !== -1) {
        const currentMessage = currentConversation.value.messages[msgIndex]
        const updatedMessage = {
          ...currentMessage
        }
        applyMessageFeedback(updatedMessage, response.data)
        currentConversation.value.messages.splice(msgIndex, 1, updatedMessage)
        saveToStorage()
      }

      return response.data
    } catch (error) {
      console.error('[Feedback] 提交失败:', error)
      throw error
    }
  }

  async function addMessage(message) {
    if (!currentConversation.value) {
      createConversation()
    }

    currentConversation.value.messages.push(message)
    currentConversation.value.updatedAt = Date.now()

    if (message.role === 'user' && currentConversation.value.title === '新对话') {
      const title = message.content.substring(0, 30) + (message.content.length > 30 ? '...' : '')
      currentConversation.value.title = title
    }

    saveToStorage()
  }

  function abortCurrentRequest(reason = 'user') {
    if (currentRequestHandle && typeof currentRequestHandle.abort === 'function') {
      console.log('[Stream] Aborting previous request')
      currentRequestHandle._abortReason = reason
      currentRequestHandle.abort()
      currentRequestHandle = null
    }
    stopTimeoutCheck()
    isLoading.value = false
  }

  function stopTimeoutCheck() {
    if (timeoutCheckInterval) {
      clearInterval(timeoutCheckInterval)
      timeoutCheckInterval = null
    }
    lastDataTimestamp = null
  }

  function startTimeoutCheck(msgId, updateCallback) {
    lastDataTimestamp = Date.now()
    timeoutCheckInterval = setInterval(() => {
      if (lastDataTimestamp && Date.now() - lastDataTimestamp > STREAM_TIMEOUT_MS) {
        console.log('[Stream] Timeout detected, forcing completion')
        stopTimeoutCheck()
        if (currentRequestHandle && typeof currentRequestHandle.abort === 'function') {
          currentRequestHandle._abortReason = 'timeout'
          currentRequestHandle.abort()
        }
        updateCallback({ type: 'timeout' })
      }
    }, 5000)
  }

  async function sendMessage(content, model = null) {
    abortCurrentRequest()

    if (!currentConversation.value) {
      createConversation()
    }

    const currentModel = model || currentConversation.value?.modelName || 'doubao'
    if (model && currentConversation.value) {
      currentConversation.value.modelName = model
    }

    isLoading.value = true

    const assistantMessage = {
      id: `local_${Date.now()}`,
      role: 'assistant',
      content: '',
      thinking: '',
      timestamp: Date.now(),
      isGenerating: true
    }
    currentConversation.value.messages.push(assistantMessage)
    saveToStorage()

    return new Promise((resolve, reject) => {
      const requestData = {
        message: content,
        model_name: currentModel
      }
      const executionContext = buildMainChatExecutionContext(currentModel)
      if (executionContext) {
        requestData.execution_context = executionContext
      }

      const xhr = new XMLHttpRequest()
      xhr.open('POST', buildApiUrl('/chat'), true)
      xhr.setRequestHeader('Content-Type', 'application/json')
      const token = localStorage.getItem('token')
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`)
      }

      xhr.timeout = 300000
      currentRequestHandle = xhr

      let fullContent = ''
      let thinkingContent = ''
      let isCompleted = false

      const finalizeMessage = (finalContent, finalThinking, isError = false, lookupMessageId = assistantMessage.id) => {
        if (isCompleted) return
        isCompleted = true
        isLoading.value = false

        const msgIndex = currentConversation.value.messages.findIndex(m => m.id === lookupMessageId)
        const finalMsg = {
          ...assistantMessage,
          content: String(finalContent || ''),
          thinking: finalThinking || '',
          isGenerating: false,
          isToolCalling: false,
          timestamp: Date.now()
        }
        Object.assign(assistantMessage, finalMsg)
        if (msgIndex !== -1) {
          if (finalMsg.renderMode === 'structured_card' && !finalMsg.cardData) {
            finalMsg.renderMode = 'plain_text'
          }
          currentConversation.value.messages.splice(msgIndex, 1, finalMsg)
        }
        currentConversation.value.updatedAt = Date.now()
        saveToStorage()
        stopTimeoutCheck()
        currentRequestHandle = null
      }

      const handleStreamData = (data) => {
        const event = normalizeAgentEvent(data)
        lastDataTimestamp = Date.now()

        if (event.type === 'conversation_id') {
          console.log('[Stream] Got conversation_id:', event.conversation_id)
          if (currentConversation.value && String(currentConversation.value.id).startsWith('local_')) {
            currentConversation.value.id = event.conversation_id
            activeId.value = event.conversation_id
          }
        } else if (event.type === 'reasoning') {
          thinkingContent += event.content || ''
          assistantMessage.thinking = thinkingContent
          const msgIndex = currentConversation.value.messages.findIndex(m => m.id === assistantMessage.id)
          if (msgIndex !== -1) {
            currentConversation.value.messages.splice(msgIndex, 1, { ...assistantMessage })
          }
        } else if (event.type === 'content' || event.type === 'answer') {
          const contentStr = event.content || event.answer || ''
          fullContent += contentStr
          assistantMessage.content = fullContent
          assistantMessage.isGenerating = true
          applyAssistantRenderMetadata(assistantMessage, event)
          applyAssistantDebugMetadata(assistantMessage, event)
          const msgIndex = currentConversation.value.messages.findIndex(m => m.id === assistantMessage.id)
          if (msgIndex !== -1) {
            currentConversation.value.messages.splice(msgIndex, 1, { ...assistantMessage })
          }
        } else if (event.type === 'status' && event.status_kind === 'runtime_knowledge') {
          applyAssistantDebugMetadata(assistantMessage, event)
          applyExecutionProgress(assistantMessage, event)
          const msgIndex = currentConversation.value.messages.findIndex(m => m.id === assistantMessage.id)
          if (msgIndex !== -1) {
            currentConversation.value.messages.splice(msgIndex, 1, { ...assistantMessage })
          }
        } else if (event.type === 'status' && event.status_kind === 'execution_progress') {
          applyExecutionProgress(assistantMessage, event)
          const msgIndex = currentConversation.value.messages.findIndex(m => m.id === assistantMessage.id)
          if (msgIndex !== -1) {
            currentConversation.value.messages.splice(msgIndex, 1, { ...assistantMessage })
          }
        } else if (event.type === 'tool_call_start') {
          console.log('[Stream] Tool call start:', event.count)
          assistantMessage.toolCalls = assistantMessage.toolCalls || []
          assistantMessage.isToolCalling = true
          const msgIndex = currentConversation.value.messages.findIndex(m => m.id === assistantMessage.id)
          if (msgIndex !== -1) {
            currentConversation.value.messages.splice(msgIndex, 1, { ...assistantMessage })
          }
        } else if (event.type === 'tool_permission_required') {
          console.log('[Stream] Tool permission required:', event.name)
          const toolCall = {
            id: `tool_${Date.now()}`,
            name: event.name,
            args: event.args,
            status: 'pending',
            result: null
          }
          assistantMessage.toolCalls = assistantMessage.toolCalls || []
          assistantMessage.toolCalls.push(toolCall)
          assistantMessage.isToolCalling = false
          const msgIndex = currentConversation.value.messages.findIndex(m => m.id === assistantMessage.id)
          if (msgIndex !== -1) {
            currentConversation.value.messages.splice(msgIndex, 1, { ...assistantMessage })
          }
        } else if (event.type === 'tool_denied') {
          console.log('[Stream] Tool denied:', event.name)
          assistantMessage.isToolCalling = false
          const msgIndex = currentConversation.value.messages.findIndex(m => m.id === assistantMessage.id)
          if (msgIndex !== -1) {
            currentConversation.value.messages.splice(msgIndex, 1, { ...assistantMessage })
          }
        } else if (event.type === 'tool_result') {
          console.log('[Stream] Tool result:', event.name, event.result)
          upsertToolCall(assistantMessage, event, 'completed')
          assistantMessage.isToolCalling = false
          const msgIndex = currentConversation.value.messages.findIndex(m => m.id === assistantMessage.id)
          if (msgIndex !== -1) {
            currentConversation.value.messages.splice(msgIndex, 1, { ...assistantMessage })
          }
        } else if (event.type === 'plan_updated') {
          if (event.plan) {
            plannerStore.upsertPlan(event.plan)
          }
        } else if (event.type === 'done') {
          const finalContent = event.content !== undefined ? event.content : fullContent
          const finalThinking = event.reasoning_content || thinkingContent
          const lookupMessageId = assistantMessage.id
          const resolvedMessageId = Number(event.message_id)
          if (Number.isFinite(resolvedMessageId)) {
            assistantMessage.id = resolvedMessageId
          }
          applyAssistantRenderMetadata(assistantMessage, event)
          applyAssistantDebugMetadata(assistantMessage, event)
          finalizeMessage(finalContent, finalThinking, false, lookupMessageId)
          resolve(assistantMessage)
        } else if (event.type === 'error') {
          const errorContent = event.error || event.content || fullContent || '发生错误，请稍后重试'
          finalizeMessage(errorContent, '', true)
          resolve(assistantMessage)
        } else if (event.type === 'timeout') {
          finalizeMessage(fullContent || '生成超时，请尝试重新生成', thinkingContent)
          resolve(assistantMessage)
        }
      }
      const eventParser = createStreamingEventParser(handleStreamData)

      startTimeoutCheck(assistantMessage.id, handleStreamData)

      xhr.onprogress = () => {
        if (xhr.readyState === 3) {
          eventParser.processResponseText(xhr.responseText)
        }
      }

      xhr.onload = () => {
        eventParser.flush(xhr.responseText)
        stopTimeoutCheck()
        isLoading.value = false

        if (xhr.status >= 200 && xhr.status < 300) {
          if (!isCompleted) {
            finalizeMessage(fullContent || '', thinkingContent)
            resolve(assistantMessage)
          }
        } else if (xhr.status === 0) {
          if (!isCompleted) {
            finalizeMessage(fullContent || '请求被中断', thinkingContent)
            resolve(assistantMessage)
          }
        } else {
          let errorContent = '发生错误，请稍后重试'
          try {
            const errorData = JSON.parse(xhr.responseText)
            errorContent = errorData.detail || errorContent
          } catch (e) {
          }
          if (!isCompleted) {
            finalizeMessage(errorContent, '', true)
            resolve(assistantMessage)
          }
        }
        currentRequestHandle = null
      }

      xhr.onerror = () => {
        stopTimeoutCheck()
        isLoading.value = false
        if (!isCompleted) {
          finalizeMessage('网络错误，请检查连接', '', true)
          resolve(assistantMessage)
        }
        currentRequestHandle = null
      }

      xhr.ontimeout = () => {
        stopTimeoutCheck()
        isLoading.value = false
        if (!isCompleted) {
          finalizeMessage('请求超时，请稍后重试', '', true)
          resolve(assistantMessage)
        }
        currentRequestHandle = null
      }

      xhr.onabort = () => {
        stopTimeoutCheck()
        isLoading.value = false
        if (!isCompleted) {
          const abortReason = xhr._abortReason || 'user'
          const abortMessage = abortReason === 'timeout'
            ? (fullContent || '生成超时，请稍后重试')
            : (fullContent || '已停止生成')
          finalizeMessage(abortMessage, thinkingContent)
          resolve(assistantMessage)
        }
        currentRequestHandle = null
      }

      xhr.send(JSON.stringify(requestData))
    })
  }

  function updateConversation(id, data) {
    const conv = conversations.value.find(c => c.id === id)
    if (conv) {
      Object.assign(conv, data)
      saveToStorage()
    }
  }

  function clearCurrentMessages() {
    if (currentConversation.value) {
      currentConversation.value.messages = []
      saveToStorage()
    }
  }

  async function regenerateMessage(userMessageContent) {
    abortCurrentRequest()

    if (!currentConversation.value) return Promise.reject('No active conversation')

    const currentModel = currentConversation.value.modelName || 'doubao'

    isLoading.value = true

    const assistantMessage = {
      id: `local_${Date.now()}`,
      role: 'assistant',
      content: '',
      thinking: '',
      timestamp: Date.now(),
      isGenerating: true
    }
    currentConversation.value.messages.push(assistantMessage)
    saveToStorage()

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open('POST', buildApiUrl('/chat'), true)
      xhr.setRequestHeader('Content-Type', 'application/json')
      const token = localStorage.getItem('token')
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`)
      }

      xhr.timeout = 300000
      currentRequestHandle = xhr

      let fullContent = ''
      let thinkingContent = ''
      let isCompleted = false

      const finalizeMessage = (finalContent, finalThinking, isError = false, lookupMessageId = assistantMessage.id) => {
        if (isCompleted) return
        isCompleted = true
        isLoading.value = false

        const msgIndex = currentConversation.value.messages.findIndex(m => m.id === lookupMessageId)
        const finalMsg = {
          ...assistantMessage,
          content: String(finalContent || ''),
          thinking: finalThinking || '',
          isGenerating: false,
          isToolCalling: false,
          timestamp: Date.now()
        }
        Object.assign(assistantMessage, finalMsg)
        if (msgIndex !== -1) {
          if (finalMsg.renderMode === 'structured_card' && !finalMsg.cardData) {
            finalMsg.renderMode = 'plain_text'
          }
          currentConversation.value.messages.splice(msgIndex, 1, finalMsg)
        }
        currentConversation.value.updatedAt = Date.now()
        saveToStorage()
        stopTimeoutCheck()
        currentRequestHandle = null
      }

      const handleStreamData = (data) => {
        const event = normalizeAgentEvent(data)
        lastDataTimestamp = Date.now()

        if (event.type === 'reasoning') {
          thinkingContent += event.content || ''
          assistantMessage.thinking = thinkingContent
          const msgIndex = currentConversation.value.messages.findIndex(m => m.id === assistantMessage.id)
          if (msgIndex !== -1) {
            currentConversation.value.messages.splice(msgIndex, 1, { ...assistantMessage })
          }
        } else if (event.type === 'content' || event.type === 'answer') {
          const contentStr = event.content || event.answer || ''
          fullContent += contentStr
          assistantMessage.content = fullContent
          assistantMessage.isGenerating = true
          applyAssistantRenderMetadata(assistantMessage, event)
          applyAssistantDebugMetadata(assistantMessage, event)
          const msgIndex = currentConversation.value.messages.findIndex(m => m.id === assistantMessage.id)
          if (msgIndex !== -1) {
            currentConversation.value.messages.splice(msgIndex, 1, { ...assistantMessage })
          }
        } else if (event.type === 'status' && event.status_kind === 'runtime_knowledge') {
          applyAssistantDebugMetadata(assistantMessage, event)
          applyExecutionProgress(assistantMessage, event)
          const msgIndex = currentConversation.value.messages.findIndex(m => m.id === assistantMessage.id)
          if (msgIndex !== -1) {
            currentConversation.value.messages.splice(msgIndex, 1, { ...assistantMessage })
          }
        } else if (event.type === 'status' && event.status_kind === 'execution_progress') {
          applyExecutionProgress(assistantMessage, event)
          const msgIndex = currentConversation.value.messages.findIndex(m => m.id === assistantMessage.id)
          if (msgIndex !== -1) {
            currentConversation.value.messages.splice(msgIndex, 1, { ...assistantMessage })
          }
        } else if (event.type === 'tool_call_start') {
          assistantMessage.toolCalls = assistantMessage.toolCalls || []
          assistantMessage.isToolCalling = true
          const msgIndex = currentConversation.value.messages.findIndex(m => m.id === assistantMessage.id)
          if (msgIndex !== -1) {
            currentConversation.value.messages.splice(msgIndex, 1, { ...assistantMessage })
          }
        } else if (event.type === 'tool_result') {
          upsertToolCall(assistantMessage, event, 'completed')
          assistantMessage.isToolCalling = false
          const msgIndex = currentConversation.value.messages.findIndex(m => m.id === assistantMessage.id)
          if (msgIndex !== -1) {
            currentConversation.value.messages.splice(msgIndex, 1, { ...assistantMessage })
          }
        } else if (event.type === 'plan_updated') {
          if (event.plan) {
            plannerStore.upsertPlan(event.plan)
          }
        } else if (event.type === 'done') {
          const lookupMessageId = assistantMessage.id
          const resolvedMessageId = Number(event.message_id)
          if (Number.isFinite(resolvedMessageId)) {
            assistantMessage.id = resolvedMessageId
          }
          if (event.content !== undefined) {
            fullContent = event.content
          }
          if (event.reasoning_content) {
            thinkingContent = event.reasoning_content
          }
          applyAssistantRenderMetadata(assistantMessage, event)
          applyAssistantDebugMetadata(assistantMessage, event)
          finalizeMessage(fullContent, thinkingContent, false, lookupMessageId)
          resolve(assistantMessage)
        } else if (event.type === 'error') {
          const errorContent = event.error || event.content || fullContent || '重新生成失败，请稍后重试'
          finalizeMessage(errorContent, '', true)
          resolve(assistantMessage)
        } else if (event.type === 'timeout') {
          finalizeMessage(fullContent || '生成超时，请尝试重新生成', thinkingContent)
          resolve(assistantMessage)
        }
      }
      const eventParser = createStreamingEventParser(handleStreamData)

      startTimeoutCheck(assistantMessage.id, handleStreamData)

      xhr.onprogress = () => {
        if (xhr.readyState === 3) {
          eventParser.processResponseText(xhr.responseText)
        }
      }

      xhr.onload = () => {
        eventParser.flush(xhr.responseText)
        stopTimeoutCheck()
        isLoading.value = false

        if (xhr.status >= 200 && xhr.status < 300) {
          if (!isCompleted) {
            finalizeMessage(fullContent || '', thinkingContent)
          }
          resolve(assistantMessage)
        } else if (xhr.status === 0) {
          if (!isCompleted) {
            finalizeMessage(fullContent || '请求被中断', thinkingContent)
            resolve(assistantMessage)
          }
        } else {
          let errorContent = '重新生成失败，请稍后重试'
          try {
            const errorData = JSON.parse(xhr.responseText)
            errorContent = errorData.detail || errorContent
          } catch (e) {
            // use default
          }
          finalizeMessage(errorContent, '', true)
          resolve(assistantMessage)
        }
        currentRequestHandle = null
      }

      xhr.onerror = () => {
        stopTimeoutCheck()
        isLoading.value = false
        if (!isCompleted) {
          finalizeMessage('网络错误，请检查连接', '', true)
          resolve(assistantMessage)
        }
        currentRequestHandle = null
      }

      xhr.ontimeout = () => {
        stopTimeoutCheck()
        isLoading.value = false
        if (!isCompleted) {
          finalizeMessage('请求超时，请稍后重试', '', true)
          resolve(assistantMessage)
        }
        currentRequestHandle = null
      }

      xhr.onabort = () => {
        stopTimeoutCheck()
        isLoading.value = false
        if (!isCompleted) {
          const abortReason = xhr._abortReason || 'user'
          const abortMessage = abortReason === 'timeout'
            ? (fullContent || '生成超时，请稍后重试')
            : (fullContent || '已停止生成')
          finalizeMessage(abortMessage, thinkingContent)
          resolve(assistantMessage)
        }
        currentRequestHandle = null
      }

      const requestData = {
        message: userMessageContent,
        model_name: currentModel
      }
      const executionContext = buildMainChatExecutionContext(currentModel)
      if (executionContext) {
        requestData.execution_context = executionContext
      }
      xhr.send(JSON.stringify(requestData))
    })
  }

  function removeAssistantMessage(messageId) {
    if (!currentConversation.value) return
    const msgIndex = currentConversation.value.messages.findIndex(m => m.id === messageId)
    if (msgIndex !== -1) {
      currentConversation.value.messages.splice(msgIndex, 1)
      saveToStorage()
    }
  }

  function exportConversations() {
    return storage.exportData()
  }

  function importConversations(data) {
    return storage.importData(data)
  }

  watch(conversations, () => {
    saveToStorage()
  }, { deep: true })

  return {
    conversations,
    activeId,
    searchQuery,
    isLoading,
    currentConversation,
    groupedConversations,
    loadConversations,
    createConversation,
    deleteConversation,
    setActiveConversation,
    setSearchQuery,
    addMessage,
    sendMessage,
    regenerateMessage,
    removeAssistantMessage,
    submitMessageFeedback,
    feedbackReasons,
    abortCurrentRequest,
    updateConversation,
    clearCurrentMessages,
    exportConversations,
    importConversations
  }
})
