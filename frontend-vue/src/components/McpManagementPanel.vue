<template>
  <section class="settings-section mcp-panel">
    <div class="section-head">
      <div>
        <h2>MCP 服务管理</h2>
        <p class="section-desc">集中管理 server、capability、握手状态与工具调试入口。</p>
      </div>
      <button class="secondary-btn" :disabled="mcpStore.isLoading" @click="refreshData">
        {{ mcpStore.isLoading ? '刷新中...' : '刷新数据' }}
      </button>
    </div>

    <div class="catalog-grid">
      <div class="catalog-card">
        <span class="catalog-label">总服务数</span>
        <strong>{{ mcpStore.catalog.total_servers || 0 }}</strong>
      </div>
      <div class="catalog-card">
        <span class="catalog-label">启用服务</span>
        <strong>{{ mcpStore.catalog.enabled_servers || 0 }}</strong>
      </div>
      <div class="catalog-card catalog-card-wide">
        <span class="catalog-label">Capability 目录</span>
        <div v-if="catalogEntries.length" class="catalog-tags">
          <span v-for="item in catalogEntries" :key="item.capability" class="capability-pill">
            {{ item.capability }} · {{ item.server_names.length }}
          </span>
        </div>
        <span v-else class="muted">暂无能力目录</span>
      </div>
    </div>

    <div class="panel-grid">
      <div class="panel-card">
        <div class="card-head">
          <h3>新增 / 更新服务</h3>
          <span class="muted">支持 stdio 与 http</span>
        </div>

        <div class="form-grid">
          <label class="field">
            <span>服务名</span>
            <input v-model.trim="form.name" type="text" placeholder="filesystem" />
          </label>
          <label class="field">
            <span>展示名</span>
            <input v-model.trim="form.display_name" type="text" placeholder="Filesystem MCP" />
          </label>
          <label class="field">
            <span>传输方式</span>
            <select v-model="form.transport">
              <option value="stdio">stdio</option>
              <option value="http">http</option>
            </select>
          </label>
          <label class="field">
            <span>Capability 列表</span>
            <input v-model.trim="form.capabilitiesText" type="text" placeholder="filesystem.read, search.query" />
          </label>
          <label v-if="form.transport === 'stdio'" class="field field-span-2">
            <span>命令</span>
            <input v-model.trim="form.command" type="text" placeholder="cmd" />
          </label>
          <label v-if="form.transport === 'stdio'" class="field field-span-2">
            <span>参数</span>
            <input v-model.trim="form.argsText" type="text" placeholder="/c, python, server.py" />
          </label>
          <label v-if="form.transport === 'http'" class="field field-span-2">
            <span>URL</span>
            <input v-model.trim="form.url" type="text" placeholder="http://localhost:9001/mcp" />
          </label>
          <label class="field field-span-2">
            <span>描述</span>
            <textarea v-model.trim="form.description" rows="3" placeholder="说明该 MCP server 的职责与边界"></textarea>
          </label>
          <label class="field field-span-2">
            <span>metadata JSON</span>
            <textarea
              v-model="form.metadataJson"
              rows="5"
              placeholder='{"timeout_seconds": 15, "capability_tools": {"filesystem.read": "read_file"}}'
            ></textarea>
          </label>
        </div>

        <p v-if="formError" class="inline-error">{{ formError }}</p>

        <div class="form-actions">
          <button class="primary-btn" :disabled="mcpStore.isSubmitting" @click="submitForm">
            {{ mcpStore.isSubmitting ? '提交中...' : (editingServerName ? '更新服务' : '创建服务') }}
          </button>
          <button class="secondary-btn" :disabled="mcpStore.isSubmitting" @click="resetForm">
            重置
          </button>
        </div>
      </div>

      <div class="panel-card">
        <div class="card-head">
          <h3>服务列表</h3>
          <span class="muted">用于 probe / handshake / tool call</span>
        </div>

        <p v-if="mcpStore.error" class="inline-error">{{ mcpStore.error }}</p>
        <p v-if="!servers.length && !mcpStore.isLoading" class="empty-state">暂无 MCP 服务配置</p>

        <div v-for="server in servers" :key="server.name" class="server-card">
          <div class="server-head">
            <div>
              <div class="server-title-row">
                <h4>{{ server.display_name }}</h4>
                <span class="status-badge" :class="{ online: server.enabled, offline: !server.enabled }">
                  {{ server.enabled ? 'enabled' : 'disabled' }}
                </span>
              </div>
              <p class="server-meta">
                <code>{{ server.name }}</code>
                <span>{{ server.transport }}</span>
              </p>
            </div>
            <div class="server-actions">
              <button class="secondary-btn" @click="startEdit(server)">编辑</button>
              <button
                class="secondary-btn"
                :disabled="Boolean(mcpStore.actionStates[`enable:${server.name}`])"
                @click="toggleEnabled(server)"
              >
                {{ server.enabled ? '停用' : '启用' }}
              </button>
              <button
                class="danger-btn"
                :disabled="Boolean(mcpStore.actionStates[`delete:${server.name}`])"
                @click="removeServer(server.name)"
              >
                删除
              </button>
            </div>
          </div>

          <p v-if="server.description" class="server-description">{{ server.description }}</p>

          <div class="server-details">
            <div>
              <span class="detail-label">Capabilities</span>
              <div class="catalog-tags">
                <span
                  v-for="capability in server.capabilities || []"
                  :key="capability"
                  class="capability-pill"
                >
                  {{ capability }}
                </span>
                <span v-if="!(server.capabilities || []).length" class="muted">未配置</span>
              </div>
            </div>
            <div>
              <span class="detail-label">Endpoint</span>
              <code v-if="server.transport === 'stdio'">{{ server.command }} {{ (server.args || []).join(' ') }}</code>
              <code v-else>{{ server.url }}</code>
            </div>
          </div>

          <div class="diagnostic-actions">
            <button
              class="secondary-btn"
              :disabled="Boolean(mcpStore.actionStates[`probe:${server.name}`])"
              @click="runProbe(server.name)"
            >
              {{ mcpStore.actionStates[`probe:${server.name}`] ? '探测中...' : 'Probe' }}
            </button>
            <button
              class="secondary-btn"
              :disabled="Boolean(mcpStore.actionStates[`handshake:${server.name}`])"
              @click="runHandshake(server.name)"
            >
              {{ mcpStore.actionStates[`handshake:${server.name}`] ? '握手中...' : 'Handshake' }}
            </button>
          </div>

          <div v-if="mcpStore.probeResults[server.name]" class="diagnostic-box">
            <strong>Probe</strong>
            <pre>{{ formatJson(mcpStore.probeResults[server.name]) }}</pre>
          </div>

          <div v-if="mcpStore.handshakeResults[server.name]" class="diagnostic-box">
            <strong>Handshake</strong>
            <pre>{{ formatJson(mcpStore.handshakeResults[server.name]) }}</pre>

            <div class="tool-call-block">
              <label class="field">
                <span>工具名</span>
                <input
                  v-model.trim="toolDrafts[server.name].toolName"
                  type="text"
                  placeholder="read_file"
                />
              </label>
              <label class="field">
                <span>arguments JSON</span>
                <textarea
                  v-model="toolDrafts[server.name].argumentsJson"
                  rows="4"
                  placeholder='{"path":"README.md"}'
                ></textarea>
              </label>
              <p v-if="toolDrafts[server.name].error" class="inline-error">{{ toolDrafts[server.name].error }}</p>
              <button
                class="primary-btn"
                :disabled="Boolean(mcpStore.actionStates[`call:${server.name}:${toolDrafts[server.name].toolName || ''}`])"
                @click="runToolCall(server.name)"
              >
                执行 tools/call
              </button>
            </div>
          </div>

          <div v-if="mcpStore.toolCallResults[server.name]" class="diagnostic-box">
            <strong>Tool Call Result</strong>
            <pre>{{ formatJson(mcpStore.toolCallResults[server.name]) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive } from 'vue'
import { useMcpStore } from '../stores/mcp'

const mcpStore = useMcpStore()

const form = reactive({
  name: '',
  display_name: '',
  transport: 'stdio',
  command: '',
  argsText: '',
  url: '',
  description: '',
  capabilitiesText: '',
  metadataJson: '{}'
})
const toolDrafts = reactive({})
const state = reactive({
  editingServerName: '',
  formError: ''
})

const servers = computed(() => mcpStore.servers || [])
const catalogEntries = computed(() => mcpStore.catalog?.capabilities || [])
const editingServerName = computed(() => state.editingServerName)
const formError = computed(() => state.formError)

onMounted(async () => {
  await refreshData()
})

function ensureToolDraft(serverName) {
  if (!toolDrafts[serverName]) {
    toolDrafts[serverName] = {
      toolName: '',
      argumentsJson: '{}',
      error: ''
    }
  }
  return toolDrafts[serverName]
}

function resetForm() {
  form.name = ''
  form.display_name = ''
  form.transport = 'stdio'
  form.command = ''
  form.argsText = ''
  form.url = ''
  form.description = ''
  form.capabilitiesText = ''
  form.metadataJson = '{}'
  state.formError = ''
  state.editingServerName = ''
}

function startEdit(server) {
  state.editingServerName = server.name
  form.name = server.name
  form.display_name = server.display_name
  form.transport = server.transport
  form.command = server.command || ''
  form.argsText = (server.args || []).join(', ')
  form.url = server.url || ''
  form.description = server.description || ''
  form.capabilitiesText = (server.capabilities || []).join(', ')
  form.metadataJson = JSON.stringify(server.metadata || {}, null, 2)
  state.formError = ''
}

function normalizeTextList(value) {
  return String(value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function parseMetadata() {
  const raw = String(form.metadataJson || '').trim()
  if (!raw) return {}
  try {
    const parsed = JSON.parse(raw)
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      return parsed
    }
    throw new Error('metadata 必须是 JSON 对象')
  } catch (error) {
    throw new Error(error?.message || 'metadata JSON 无效')
  }
}

function buildPayload() {
  const metadata = parseMetadata()
  const payload = {
    name: form.name,
    display_name: form.display_name,
    transport: form.transport,
    command: form.transport === 'stdio' ? form.command : null,
    args: form.transport === 'stdio' ? normalizeTextList(form.argsText) : [],
    url: form.transport === 'http' ? form.url : null,
    enabled: true,
    description: form.description || null,
    capabilities: normalizeTextList(form.capabilitiesText),
    tags: [],
    metadata
  }
  return payload
}

async function submitForm() {
  state.formError = ''
  try {
    const payload = buildPayload()
    if (!payload.name || !payload.display_name) {
      state.formError = '服务名和展示名不能为空'
      return
    }
    if (payload.transport === 'stdio' && !payload.command) {
      state.formError = 'stdio 模式必须填写命令'
      return
    }
    if (payload.transport === 'http' && !payload.url) {
      state.formError = 'http 模式必须填写 URL'
      return
    }

    if (editingServerName.value) {
      await mcpStore.updateServer(editingServerName.value, payload)
    } else {
      await mcpStore.createServer(payload)
    }
    resetForm()
  } catch (error) {
    state.formError = error?.response?.data?.detail || error?.message || '提交失败'
  }
}

async function refreshData() {
  try {
    await mcpStore.refreshAll()
    servers.value.forEach((server) => {
      const draft = ensureToolDraft(server.name)
      const handshake = mcpStore.handshakeResults[server.name]
      if (!draft.toolName && handshake?.tools?.length) {
        draft.toolName = handshake.tools[0].name || ''
      }
    })
  } catch (error) {
    console.error('[MCP] Refresh failed:', error)
  }
}

async function toggleEnabled(server) {
  await mcpStore.setServerEnabled(server.name, !server.enabled)
}

async function removeServer(serverName) {
  await mcpStore.deleteServer(serverName)
}

async function runProbe(serverName) {
  await mcpStore.probeServer(serverName)
}

async function runHandshake(serverName) {
  const result = await mcpStore.handshakeServer(serverName)
  const draft = ensureToolDraft(serverName)
  if (!draft.toolName && result?.tools?.length) {
    draft.toolName = result.tools[0].name || ''
  }
}

async function runToolCall(serverName) {
  const draft = ensureToolDraft(serverName)
  draft.error = ''
  if (!draft.toolName) {
    draft.error = '请先填写工具名'
    return
  }

  let argumentsPayload = {}
  try {
    argumentsPayload = draft.argumentsJson?.trim() ? JSON.parse(draft.argumentsJson) : {}
  } catch (error) {
    draft.error = 'arguments JSON 格式无效'
    return
  }

  await mcpStore.callTool(serverName, draft.toolName, argumentsPayload)
}

function formatJson(value) {
  return JSON.stringify(value || {}, null, 2)
}
</script>

<style scoped>
.mcp-panel {
  max-width: 1100px;
}

.section-head,
.card-head,
.server-head,
.server-title-row,
.server-actions,
.diagnostic-actions,
.form-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-sm);
}

.section-desc,
.muted,
.server-meta,
.server-description,
.detail-label {
  color: var(--text-secondary);
}

.section-desc {
  margin-top: var(--space-xs);
}

.catalog-grid,
.panel-grid,
.form-grid {
  display: grid;
  gap: var(--space-md);
}

.catalog-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin: var(--space-lg) 0;
}

.catalog-card,
.panel-card,
.server-card,
.diagnostic-box {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
}

.catalog-card {
  padding: var(--space-md);
}

.catalog-card strong {
  display: block;
  margin-top: var(--space-sm);
  font-size: 1.5rem;
  color: var(--text-primary);
}

.catalog-card-wide {
  grid-column: span 1;
}

.catalog-label,
.detail-label {
  display: block;
  margin-bottom: var(--space-xs);
  font-size: 0.875rem;
}

.catalog-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.capability-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.35rem 0.6rem;
  font-size: 0.75rem;
  color: var(--text-primary);
  background: var(--bg-elevated);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-full);
}

.panel-grid {
  grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
}

.panel-card {
  padding: var(--space-lg);
}

.form-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: var(--space-md);
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.field-span-2 {
  grid-column: span 2;
}

.field input,
.field select,
.field textarea {
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  color: var(--text-primary);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
}

.field textarea {
  resize: vertical;
  min-height: 90px;
}

.primary-btn,
.secondary-btn,
.danger-btn {
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
}

.primary-btn {
  color: white;
  background: var(--primary);
}

.secondary-btn {
  color: var(--text-primary);
  background: var(--bg-elevated);
  border-color: var(--border-primary);
}

.danger-btn {
  color: var(--error);
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.35);
}

.primary-btn:disabled,
.secondary-btn:disabled,
.danger-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.inline-error {
  margin-top: var(--space-sm);
  color: var(--error);
  white-space: pre-wrap;
}

.empty-state {
  margin-top: var(--space-md);
  color: var(--text-secondary);
}

.server-card {
  padding: var(--space-md);
  margin-top: var(--space-md);
}

.server-title-row h4 {
  font-size: 1rem;
  color: var(--text-primary);
}

.server-meta {
  display: flex;
  gap: var(--space-sm);
  margin-top: 0.2rem;
  font-size: 0.85rem;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.55rem;
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  text-transform: uppercase;
}

.status-badge.online {
  color: #0f766e;
  background: rgba(20, 184, 166, 0.16);
}

.status-badge.offline {
  color: #9f1239;
  background: rgba(244, 63, 94, 0.12);
}

.server-description {
  margin: var(--space-sm) 0;
}

.server-details {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
}

.diagnostic-actions {
  justify-content: flex-start;
  margin-top: var(--space-md);
}

.diagnostic-box {
  margin-top: var(--space-md);
  padding: var(--space-md);
}

.diagnostic-box pre {
  margin-top: var(--space-sm);
  padding: var(--space-sm);
  overflow-x: auto;
  color: var(--text-primary);
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.tool-call-block {
  margin-top: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

@media (max-width: 960px) {
  .catalog-grid,
  .panel-grid,
  .form-grid {
    grid-template-columns: 1fr;
  }

  .field-span-2,
  .catalog-card-wide {
    grid-column: span 1;
  }

  .section-head,
  .card-head,
  .server-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .server-actions {
    width: 100%;
    flex-wrap: wrap;
  }
}
</style>
