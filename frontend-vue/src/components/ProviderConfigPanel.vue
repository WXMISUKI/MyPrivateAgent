<template>
  <section class="settings-section">
    <h2>Provider 配置</h2>
    <p class="section-desc">管理模型服务商的连接配置。修改后需要保存才会生效。</p>

    <div v-if="loading" class="loading-hint">加载中...</div>

    <div v-for="provider in providers" :key="provider.name" class="provider-card">
      <div class="provider-header">
        <span class="provider-name">{{ provider.display_name }}</span>
        <span class="provider-badge" :class="provider.configured ? 'configured' : 'unconfigured'">
          {{ provider.configured ? '已配置' : '未配置' }}
        </span>
        <span v-if="provider.config_source" class="source-tag">{{ provider.config_source }}</span>
        <span v-if="provider._testResult" class="status-dot" :class="provider._testResult.status" :title="provider._testResult.message"></span>
      </div>

      <div class="provider-fields">
        <div v-if="provider.requires_api_key" class="field-row">
          <label>API Key</label>
          <div v-if="!provider._editing" class="field-display">
            <span class="masked-value">{{ provider.api_key_masked || '未配置' }}</span>
            <button class="edit-btn" @click="provider._editing = true" type="button">修改</button>
          </div>
          <div v-else class="input-group">
            <input
              :type="provider._showKey ? 'text' : 'password'"
              v-model="provider._editApiKey"
              placeholder="输入新的 API Key"
              class="field-input"
            />
            <button class="icon-btn" @click="provider._showKey = !provider._showKey" type="button">
              {{ provider._showKey ? '隐藏' : '显示' }}
            </button>
            <button class="icon-btn" @click="provider._editing = false; provider._editApiKey = ''" type="button">取消</button>
          </div>
        </div>

        <div class="field-row">
          <label>Base URL</label>
          <input
            type="text"
            v-model="provider._editBaseUrl"
            :placeholder="provider.base_url"
            class="field-input"
          />
        </div>
        <div v-if="provider.requires_api_key" class="field-row">
          <label>模型名称</label>
          <input
            type="text"
            v-model="provider._editModelName"
            :placeholder="provider.model_name || '如 doubao-seed-2-0-mini-260215'"
            class="field-input"
          />
          <span class="field-hint">当前生效: {{ provider.model_name || '默认' }}</span>
        </div>
      </div>

      <div class="provider-actions">
        <button class="action-btn test-btn" @click="testProvider(provider)" :disabled="provider._testing">
          {{ provider._testing ? '测试中...' : '测试连接' }}
        </button>
        <button class="action-btn save-btn" @click="saveProvider(provider)" :disabled="provider._saving">
          {{ provider._saving ? '保存中...' : '保存' }}
        </button>
      </div>
      <div v-if="provider._testResult" class="test-result" :class="provider._testResult.status">
        <span class="test-icon">{{ provider._testResult.status === 'ok' ? '✓' : provider._testResult.status === 'warning' ? '⚠' : '✗' }}</span>
        {{ provider._testResult.message }}
        <span v-if="provider._testResult.latency_ms" class="latency">({{ provider._testResult.latency_ms }}ms)</span>
      </div>

      <div v-if="provider._saveMessage" class="save-message" :class="provider._saveStatus">
        {{ provider._saveMessage }}
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { providerApi } from '../api'

const providers = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const response = await providerApi.list()
    providers.value = (response.data || []).map(p => ({
      ...p,
      _editApiKey: '',
      _editBaseUrl: p.base_url || '',
      _editModelName: p.model_name || '',
      _showKey: false,
      _editing: false,
      _testing: false,
      _saving: false,
      _testResult: null,
      _saveMessage: '',
      _saveStatus: '',
    }))
    // 自动测试已配置的 provider
    for (const p of providers.value) {
      if (p.configured) {
        testProvider(p)
      }
    }
  } catch (e) {
    console.error('Failed to load providers:', e)
  } finally {
    loading.value = false
  }
})

async function testProvider(provider) {
  provider._testing = true
  provider._testResult = null
  try {
    const response = await providerApi.test(provider.name)
    provider._testResult = response.data
  } catch (e) {
    provider._testResult = { status: 'error', message: '请求失败: ' + (e.message || '未知错误') }
  } finally {
    provider._testing = false
  }
}
async function saveProvider(provider) {
  const payload = {}
  if (provider._editApiKey.trim()) {
    payload.api_key = provider._editApiKey.trim()
  }
  if (provider._editBaseUrl.trim()) {
    payload.base_url = provider._editBaseUrl.trim()
  }
  if (provider._editModelName.trim() && provider._editModelName.trim() !== provider.model_name) {
    payload.model_name = provider._editModelName.trim()
  }
  if (!payload.api_key && !payload.base_url && !payload.model_name) {
    provider._saveMessage = '没有需要保存的修改'
    provider._saveStatus = 'warning'
    setTimeout(() => { provider._saveMessage = '' }, 3000)
    return
  }

  provider._saving = true
  provider._saveMessage = ''
  try {
    await providerApi.update(provider.name, payload)
    provider._saveMessage = '保存成功'
    provider._saveStatus = 'ok'
    provider._editing = false
    provider.config_source = 'local_override'
    provider.configured = true
    if (payload.api_key) {
      const k = payload.api_key
      provider.api_key_masked = k.length > 8 ? k.slice(0, 4) + '****' + k.slice(-4) : '****'
      provider._editApiKey = ''
    }
    if (payload.base_url) {
      provider.base_url = payload.base_url
      provider._editBaseUrl = ''
    }
    if (payload.model_name) {
      provider.model_name = payload.model_name
    }
  } catch (e) {
    provider._saveMessage = '保存失败: ' + (e.response?.data?.detail || e.message)
    provider._saveStatus = 'error'
  } finally {
    provider._saving = false
    setTimeout(() => { provider._saveMessage = '' }, 5000)
  }
}
</script>
<style scoped>
.section-desc {
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin-bottom: var(--space-md);
}

.loading-hint {
  color: var(--text-secondary);
  padding: var(--space-md);
}

.provider-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  margin-bottom: var(--space-md);
}

.provider-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.provider-name {
  font-weight: 600;
  font-size: 1rem;
}

.provider-badge {
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.provider-badge.configured {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.provider-badge.unconfigured {
  background: rgba(234, 179, 8, 0.15);
  color: #eab308;
}

.source-tag {
  font-size: 0.7rem;
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
  padding: 1px 6px;
  border-radius: var(--radius-sm);
}
.provider-fields {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.field-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-row label {
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.input-group {
  display: flex;
  gap: var(--space-xs);
}

.field-input {
  flex: 1;
  padding: 6px 10px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 0.875rem;
  font-family: monospace;
}

.field-input:focus {
  outline: none;
  border-color: var(--primary);
}

.icon-btn {
  padding: 4px 8px;
  font-size: 0.75rem;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  white-space: nowrap;
}

.provider-actions {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}
.action-btn {
  padding: 6px 14px;
  font-size: 0.8rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  border: 1px solid var(--border-color);
  transition: all 0.2s;
}

.test-btn {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.test-btn:hover:not(:disabled) {
  border-color: var(--primary);
}

.save-btn {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

.save-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.test-result {
  font-size: 0.8rem;
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-xs);
}

.test-result.ok {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.test-result.warning {
  background: rgba(234, 179, 8, 0.1);
  color: #eab308;
}

.test-result.error {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.test-icon {
  font-weight: bold;
  margin-right: 4px;
}

.latency {
  opacity: 0.7;
  font-size: 0.75rem;
}

.save-message {
  font-size: 0.8rem;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
}

.save-message.ok {
  color: #22c55e;
}

.save-message.warning {
  color: #eab308;
}

.save-message.error {
  color: #ef4444;
}

.field-display {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.masked-value {
  font-family: monospace;
  font-size: 0.875rem;
  color: var(--text-secondary);
  background: var(--bg-primary);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
}

.edit-btn {
  padding: 3px 10px;
  font-size: 0.75rem;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--primary);
  cursor: pointer;
}

.edit-btn:hover {
  border-color: var(--primary);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  margin-left: auto;
}

.status-dot.ok {
  background: #22c55e;
  box-shadow: 0 0 4px rgba(34, 197, 94, 0.5);
}

.status-dot.warning {
  background: #eab308;
}

.status-dot.error {
  background: #ef4444;
}

.field-hint {
  font-size: 0.7rem;
  color: var(--text-tertiary);
  margin-top: 2px;
}
</style>
