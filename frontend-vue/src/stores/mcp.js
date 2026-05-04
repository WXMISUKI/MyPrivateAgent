import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { mcpApi } from '../api'

export const useMcpStore = defineStore('mcp', () => {
  const servers = ref([])
  const catalog = ref({ total_servers: 0, enabled_servers: 0, capabilities: [] })
  const isLoading = ref(false)
  const isSubmitting = ref(false)
  const error = ref('')
  const probeResults = ref({})
  const handshakeResults = ref({})
  const toolCallResults = ref({})
  const actionStates = ref({})

  const enabledServers = computed(() => servers.value.filter((item) => item.enabled))

  function setActionState(key, value) {
    actionStates.value = {
      ...actionStates.value,
      [key]: Boolean(value)
    }
  }

  function parseApiError(err, fallback = '请求失败，请稍后重试') {
    return err?.response?.data?.detail || err?.message || fallback
  }

  async function loadServers() {
    isLoading.value = true
    error.value = ''
    try {
      const response = await mcpApi.listServers()
      servers.value = Array.isArray(response.data) ? response.data : []
    } catch (err) {
      error.value = parseApiError(err, '加载 MCP 服务失败')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function loadCatalog() {
    try {
      const response = await mcpApi.getCatalog()
      catalog.value = response.data || { total_servers: 0, enabled_servers: 0, capabilities: [] }
    } catch (err) {
      error.value = parseApiError(err, '加载 MCP 能力目录失败')
      throw err
    }
  }

  async function refreshAll() {
    await Promise.all([loadServers(), loadCatalog()])
  }

  async function createServer(payload, options = {}) {
    isSubmitting.value = true
    error.value = ''
    try {
      const response = await mcpApi.createServer(payload, options)
      await refreshAll()
      return response.data
    } catch (err) {
      error.value = parseApiError(err, '创建 MCP 服务失败')
      throw err
    } finally {
      isSubmitting.value = false
    }
  }

  async function updateServer(serverName, payload, options = {}) {
    isSubmitting.value = true
    error.value = ''
    try {
      const response = await mcpApi.updateServer(serverName, payload, options)
      await refreshAll()
      return response.data
    } catch (err) {
      error.value = parseApiError(err, '更新 MCP 服务失败')
      throw err
    } finally {
      isSubmitting.value = false
    }
  }

  async function deleteServer(serverName, options = {}) {
    setActionState(`delete:${serverName}`, true)
    error.value = ''
    try {
      const response = await mcpApi.deleteServer(serverName, options)
      const nextProbeResults = { ...probeResults.value }
      const nextHandshakeResults = { ...handshakeResults.value }
      const nextToolCallResults = { ...toolCallResults.value }
      delete nextProbeResults[serverName]
      delete nextHandshakeResults[serverName]
      delete nextToolCallResults[serverName]
      probeResults.value = nextProbeResults
      handshakeResults.value = nextHandshakeResults
      toolCallResults.value = nextToolCallResults
      await refreshAll()
      return response.data
    } catch (err) {
      error.value = parseApiError(err, '删除 MCP 服务失败')
      throw err
    } finally {
      setActionState(`delete:${serverName}`, false)
    }
  }

  async function setServerEnabled(serverName, enabled, options = {}) {
    setActionState(`enable:${serverName}`, true)
    error.value = ''
    try {
      let response
      if (enabled) {
        response = await mcpApi.enableServer(serverName, options)
      } else {
        response = await mcpApi.disableServer(serverName, options)
      }
      await refreshAll()
      return response?.data
    } catch (err) {
      error.value = parseApiError(err, '更新 MCP 服务状态失败')
      throw err
    } finally {
      setActionState(`enable:${serverName}`, false)
    }
  }

  async function probeServer(serverName, options = {}) {
    setActionState(`probe:${serverName}`, true)
    error.value = ''
    try {
      const response = await mcpApi.probeServer(serverName, options)
      probeResults.value = {
        ...probeResults.value,
        [serverName]: response.data
      }
      return response.data
    } catch (err) {
      error.value = parseApiError(err, '探测 MCP 服务失败')
      throw err
    } finally {
      setActionState(`probe:${serverName}`, false)
    }
  }

  async function handshakeServer(serverName, options = {}) {
    setActionState(`handshake:${serverName}`, true)
    error.value = ''
    try {
      const response = await mcpApi.handshakeServer(serverName, options)
      handshakeResults.value = {
        ...handshakeResults.value,
        [serverName]: response.data
      }
      return response.data
    } catch (err) {
      error.value = parseApiError(err, '握手 MCP 服务失败')
      throw err
    } finally {
      setActionState(`handshake:${serverName}`, false)
    }
  }

  async function callTool(serverName, toolName, argumentsPayload = {}, options = {}) {
    const actionKey = `call:${serverName}:${toolName}`
    setActionState(actionKey, true)
    error.value = ''
    try {
      const response = await mcpApi.callTool(serverName, toolName, argumentsPayload, options)
      toolCallResults.value = {
        ...toolCallResults.value,
        [serverName]: response.data
      }
      return response.data
    } catch (err) {
      error.value = parseApiError(err, '调用 MCP 工具失败')
      throw err
    } finally {
      setActionState(actionKey, false)
    }
  }

  return {
    servers,
    catalog,
    isLoading,
    isSubmitting,
    error,
    probeResults,
    handshakeResults,
    toolCallResults,
    actionStates,
    enabledServers,
    loadServers,
    loadCatalog,
    refreshAll,
    createServer,
    updateServer,
    deleteServer,
    setServerEnabled,
    probeServer,
    handshakeServer,
    callTool
  }
})
