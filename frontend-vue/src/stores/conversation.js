import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import storage from '../services/storage'

export const useConversationStore = defineStore('conversation', () => {
  const conversations = ref([])
  const activeId = ref(null)
  const searchQuery = ref('')
  const isLoading = ref(false)

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
    console.log('[Conversation] activeId:', activeId.value, 'type:', typeof activeId.value)
    if (conversations.value.length > 0) {
      console.log('[Conversation] First conv id:', conversations.value[0].id, 'type:', typeof conversations.value[0].id)
      console.log('[Conversation] First conv messages:', conversations.value[0].messages?.length)
    }

    // Find current conversation
    const found = conversations.value.find(c => String(c.id) === String(activeId.value))
    console.log('[Conversation] Found conversation:', found ? 'yes' : 'no', found?.id)
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

  async function sendMessage(content, model = null) {
    if (!currentConversation.value) {
      createConversation()
    }

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
        message: content
      }
      if (model) {
        requestData.model_name = model
      }

      const xhr = new XMLHttpRequest()
      xhr.open('POST', '/api/chat', true)
      xhr.setRequestHeader('Content-Type', 'application/json')
      const token = localStorage.getItem('token')
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`)
      }

      xhr.timeout = 300000

      let fullContent = ''
      let thinkingContent = ''
      let responseConversationId = null
      let jsonBuffer = ''
      let lastProcessedIndex = 0

      xhr.onprogress = (event) => {
        if (xhr.readyState === 3) {
          const responseText = xhr.responseText
          const newData = responseText.slice(lastProcessedIndex)
          lastProcessedIndex = responseText.length

          const lines = newData.split('\n')
          for (let i = 0; i < lines.length; i++) {
            const line = lines[i]
            if (line.startsWith('data: ')) {
              jsonBuffer += line.slice(6)
              console.log('[Stream] Received:', line.slice(6).substring(0, 100))

              try {
                const data = JSON.parse(jsonBuffer)
                jsonBuffer = ''

                console.log('[Stream] Parsed:', data.type, 'content length:', (data.content || '').length)

                if (data.type === 'conversation_id') {
                  responseConversationId = data.conversation_id
                  console.log('[Stream] Got conversation_id:', responseConversationId)
                  if (currentConversation.value && String(currentConversation.value.id).startsWith('local_')) {
                    currentConversation.value.id = responseConversationId
                    activeId.value = responseConversationId
                  }
                } else if (data.type === 'reasoning') {
                  thinkingContent += data.content || ''
                  const updatedMsg = { ...assistantMessage, thinking: thinkingContent }
                  const msgIndex = currentConversation.value.messages.findIndex(m => m.id === assistantMessage.id)
                  if (msgIndex !== -1) {
                    currentConversation.value.messages[msgIndex] = updatedMsg
                  }
                  assistantMessage.thinking = thinkingContent
                  console.log('[Stream] Thinking:', thinkingContent.substring(0, 50))
                } else if (data.type === 'content' || data.type === 'answer') {
                  const contentStr = data.content || data.answer || ''
                  fullContent += contentStr
                  const updatedMsg = { ...assistantMessage, content: fullContent }
                  const msgIndex = currentConversation.value.messages.findIndex(m => m.id === assistantMessage.id)
                  if (msgIndex !== -1) {
                    currentConversation.value.messages[msgIndex] = updatedMsg
                  }
                  assistantMessage.content = fullContent
                  console.log('[Stream] Content:', fullContent.substring(0, 50))
                } else if (data.type === 'done') {
                  if (data.content !== undefined) {
                    fullContent = data.content
                  }
                  if (data.reasoning_content) {
                    thinkingContent = data.reasoning_content
                  }
                  const updatedMsg = { 
                    ...assistantMessage, 
                    content: fullContent,
                    thinking: thinkingContent,
                    isGenerating: false
                  }
                  const msgIndex = currentConversation.value.messages.findIndex(m => m.id === assistantMessage.id)
                  if (msgIndex !== -1) {
                    currentConversation.value.messages[msgIndex] = updatedMsg
                  }
                  assistantMessage.content = fullContent
                  assistantMessage.thinking = thinkingContent
                  assistantMessage.isGenerating = false
                  console.log('[Stream] Done! Full content length:', fullContent.length)
                }
              } catch (e) {
                // JSON不完整，继续缓冲
              }
            }
          }
        }
      }

      xhr.onload = () => {
        isLoading.value = false
        if (xhr.status >= 200 && xhr.status < 300) {
          const finalMsg = { 
            ...assistantMessage, 
            content: String(fullContent || ''),
            thinking: '',
            isGenerating: false,
            timestamp: Date.now()
          }
          const msgIndex = currentConversation.value.messages.findIndex(m => m.id === assistantMessage.id)
          if (msgIndex !== -1) {
            currentConversation.value.messages[msgIndex] = finalMsg
          }
          currentConversation.value.updatedAt = Date.now()
          saveToStorage()
          resolve(finalMsg)
        } else {
          let errorContent = '发生错误，请稍后重试'
          try {
            const errorData = JSON.parse(xhr.responseText)
            errorContent = errorData.detail || errorContent
          } catch (e) {
            // use default error content
          }
          const errorMsg = {
            ...assistantMessage,
            content: errorContent,
            thinking: '',
            isGenerating: false
          }
          const msgIndex = currentConversation.value.messages.findIndex(m => m.id === assistantMessage.id)
          if (msgIndex !== -1) {
            currentConversation.value.messages[msgIndex] = errorMsg
          }
          saveToStorage()
          reject(new Error(errorContent))
        }
      }

      xhr.onerror = () => {
        isLoading.value = false
        const errorMsg = {
          ...assistantMessage,
          content: '网络错误，请检查连接',
          thinking: '',
          isGenerating: false
        }
        const msgIndex = currentConversation.value.messages.findIndex(m => m.id === assistantMessage.id)
        if (msgIndex !== -1) {
          currentConversation.value.messages[msgIndex] = errorMsg
        }
        saveToStorage()
        reject(new Error('Network error'))
      }

      xhr.ontimeout = () => {
        isLoading.value = false
        const errorMsg = {
          ...assistantMessage,
          content: '请求超时，请稍后重试',
          thinking: '',
          isGenerating: false
        }
        const msgIndex = currentConversation.value.messages.findIndex(m => m.id === assistantMessage.id)
        if (msgIndex !== -1) {
          currentConversation.value.messages[msgIndex] = errorMsg
        }
        saveToStorage()
        reject(new Error('Timeout'))
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
    updateConversation,
    clearCurrentMessages,
    exportConversations,
    importConversations
  }
})
