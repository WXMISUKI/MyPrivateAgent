import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { getApiBaseUrl } from '../config/apiBase'

const API_BASE_URL = getApiBaseUrl()

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

      const errorBody = error.response?.data?.error
      if (errorBody) {
        const message = errorBody.message || '请求失败'
        const code = errorBody.code || 'UNKNOWN'
        console.error(`[API Error] ${code}: ${message} (request_id: ${errorBody.request_id || '-'})`)
      } else if (error.code === 'ECONNABORTED') {
        console.error('[API Error] 请求超时，请检查网络连接')
      } else if (!error.response) {
        console.error('[API Error] 网络连接失败，请检查后端服务是否运行')
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

export const runtimeSurfaceApi = {
  getProfile(params = {}) {
    return api.get('/runtime-profile', { params })
  },

  getMainChatQueryDetail(params = {}) {
    return api.get('/runtime-profile/main-chat-query-detail', { params })
  },

  getMainChatQueryHistory(params = {}) {
    return api.get('/runtime-profile/main-chat-query-history', { params })
  },

  getSubagentLaneRecentSummary(params = {}) {
    return api.get('/runtime-profile/subagent-lane-recent-summary', { params })
  },

  getChildExecutorOutputReplay(params = {}) {
    return api.get('/runtime-profile/child-executor-output-replay', { params })
  },

  getChildExecutorOutputSummary(params = {}) {
    return api.get('/runtime-profile/child-executor-output-summary', { params })
  },

  getChildExecutorMergedSemantics(params = {}) {
    return api.get('/runtime-profile/child-executor-merged-semantics', { params })
  },

  updateProfile(payload) {
    return api.patch('/runtime-profile', payload)
  },

  updateEmbeddedRuntimeBootstrap(payload) {
    return api.patch('/runtime-profile/embedded-runtime-bootstrap', payload)
  },

  precheckFrameworkAdapter(payload) {
    return api.post('/runtime-framework-adapters/precheck', payload)
  },

  runFrameworkAdapterPilot(payload) {
    return api.post('/runtime-framework-adapters/pilot-run', payload)
  },

  runExternalFrameworkAdapterPilot(payload) {
    return api.post('/runtime-framework-adapters/external-pilot', payload)
  }
}

export const capabilityGapApi = {
  getSummary(params = {}) {
    return api.get('/capability-gaps', { params })
  },

  getRemediationStatuses() {
    return api.get('/remediation-status')
  },

  updateRemediationStatus(actionId, payload = {}) {
    return api.patch(`/remediation-status/${encodeURIComponent(actionId)}`, payload)
  }
}

export const healthApi = {
  getHealth() {
    return api.get('/health')
  }
}

export const doctorApi = {
  getReport(params = {}) {
    return api.get('/doctor', { params })
  }
}

export const providerApi = {
  list() {
    return api.get('/providers')
  },

  update(providerName, payload) {
    return api.patch(`/providers/${encodeURIComponent(providerName)}`, payload)
  },

  test(providerName) {
    return api.post(`/providers/${encodeURIComponent(providerName)}/test`)
  },

  getFailoverAnalytics(params = {}) {
    return api.get('/failover-analytics', { params })
  }
}

// Legacy /api/voice compatibility wrapper. New voice surfaces should prefer
// capabilityApi with voice.tts.edge and voice.asr.vosk.
export const voiceApi = {
  getCapabilities() {
    return api.get('/voice/capabilities')
  },

  synthesizeSpeech(payload) {
    return api.post('/voice/tts', payload, { responseType: 'blob' })
  },

  transcribeAudio(file, params = {}) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/voice/asr', formData, {
      params,
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}

export const capabilityApi = {
  list() {
    return api.get('/capabilities')
  },

  get(capabilityId) {
    return api.get(`/capabilities/${encodeURIComponent(capabilityId)}`)
  },

  health(capabilityId) {
    return api.get(`/capabilities/${encodeURIComponent(capabilityId)}/health`)
  },

  heartbeat() {
    return api.get('/capabilities/heartbeat')
  },

  test(capabilityId, payload = {}) {
    return api.post(`/capabilities/${encodeURIComponent(capabilityId)}/test`, payload)
  },

  invoke(capabilityId, payload = {}) {
    return api.post(`/capabilities/${encodeURIComponent(capabilityId)}/invoke`, payload)
  }
}

export const documentArtifactApi = {
  list(params = {}) {
    return api.get('/document-artifacts', { params })
  },

  get(artifactId) {
    return api.get(`/document-artifacts/${encodeURIComponent(artifactId)}`)
  },

  persist(payload = {}) {
    return api.post('/document-artifacts', payload)
  }
}

export const documentIngestionApi = {
  list(params = {}) {
    return api.get('/document-ingestions', { params })
  },

  get(ingestId) {
    return api.get(`/document-ingestions/${encodeURIComponent(ingestId)}`)
  },

  getResult(ingestId) {
    return api.get(`/document-ingestions/${encodeURIComponent(ingestId)}/result`)
  },

  submit(payload = {}) {
    return api.post('/document-ingestions', payload)
  }
}

export const mcpApi = {
  listServers() {
    return api.get('/mcp/servers')
  },

  createServer(payload, params = {}) {
    return api.post('/mcp/servers', payload, { params })
  },

  updateServer(serverName, payload, params = {}) {
    return api.patch(`/mcp/servers/${serverName}`, payload, { params })
  },

  deleteServer(serverName, params = {}) {
    return api.delete(`/mcp/servers/${serverName}`, { params })
  },

  enableServer(serverName, params = {}) {
    return api.post(`/mcp/servers/${serverName}/enable`, null, { params })
  },

  disableServer(serverName, params = {}) {
    return api.post(`/mcp/servers/${serverName}/disable`, null, { params })
  },

  getCatalog() {
    return api.get('/mcp/catalog')
  },

  probeServer(serverName, params = {}) {
    return api.post(`/mcp/servers/${serverName}/probe`, null, { params })
  },

  handshakeServer(serverName, params = {}) {
    return api.post(`/mcp/servers/${serverName}/handshake`, null, { params })
  },

  callTool(serverName, toolName, argumentsPayload = {}, params = {}) {
    return api.post(`/mcp/servers/${serverName}/tools/${toolName}/call`, {
      arguments: argumentsPayload
    }, { params })
  }
}

export const commandApi = {
  list() {
    return api.get('/commands')
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
