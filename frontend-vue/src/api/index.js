import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const API_BASE_URL = '/api'

function createAxiosInstance() {
  const authStore = useAuthStore()
  const instance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 300000
  })

  instance.interceptors.request.use(
    config => {
      if (authStore.token) {
        config.headers.Authorization = `Bearer ${authStore.token}`
      }
      return config
    },
    error => Promise.reject(error)
  )

  instance.interceptors.response.use(
    response => response,
    error => {
      if (error.response?.status === 401) {
        authStore.logout()
      }
      return Promise.reject(error)
    }
  )

  return instance
}

const api = createAxiosInstance()

export const chatApi = {
  sendMessage(message, conversationId = null) {
    return api.post('/chat', { message, conversation_id: conversationId })
  },

  regenerateMessage(messageIndex) {
    return api.post('/chat/regenerate', { message_index: messageIndex })
  },

  abortStream() {
    return api.post('/chat/abort')
  }
}

export const conversationApi = {
  getConversations() {
    return api.get('/conversations')
  },

  createConversation(title) {
    return api.post('/conversations', { title })
  },

  updateConversation(id, data) {
    return api.put(`/conversations/${id}`, data)
  },

  deleteConversation(id) {
    return api.delete(`/conversations/${id}`)
  },

  getConversation(id) {
    return api.get(`/conversations/${id}`)
  }
}

export const authApi = {
  login(username, password) {
    return api.post('/auth/login', { username, password })
  },

  logout() {
    return api.post('/auth/logout')
  },

  verify() {
    return api.get('/auth/verify')
  }
}

export const settingsApi = {
  getSettings() {
    return api.get('/settings')
  },

  updateSettings(settings) {
    return api.put('/settings', settings)
  }
}

export const learningsApi = {
  getLearnings(params) {
    return api.get('/learnings', { params })
  },

  addLearning(content, category, source) {
    return api.post('/learnings', { content, category, source })
  },

  deleteLearning(id) {
    return api.delete(`/learnings/${id}`)
  }
}

export default api
