<template>
  <section class="settings-section">
    <div class="section-header">
      <div>
        <h2>能力 Provider 测试</h2>
        <p class="section-desc">查看统一能力注册、外部服务心跳，并执行短链路能力测试。</p>
      </div>
      <button class="action-btn" type="button" @click="loadDiagnostics" :disabled="loading">
        {{ loading ? '刷新中...' : '刷新' }}
      </button>
    </div>

    <div v-if="loadError" class="test-result error">{{ loadError }}</div>

    <div class="heartbeat-list">
      <div v-for="provider in heartbeatProviders" :key="provider.provider_id + provider.base_url" class="provider-card compact">
        <div class="provider-header">
          <span class="provider-name">{{ provider.provider_id || 'local' }}</span>
          <span class="provider-badge" :class="statusClass(provider.status)">{{ provider.status || 'unknown' }}</span>
          <span class="source-tag">{{ provider.base_url || 'local' }}</span>
        </div>
        <div v-if="provider.reason" class="field-hint">{{ provider.reason }}</div>
      </div>
    </div>

    <div v-if="loading" class="loading-hint">加载中...</div>

    <div v-for="capability in capabilities" :key="capability.capability_id" class="provider-card">
      <div class="provider-header">
        <span class="provider-name">{{ capability.capability_id }}</span>
        <span class="provider-badge" :class="statusClass(capability.status)">{{ capability.status || 'unknown' }}</span>
        <span class="source-tag">{{ capability.kind }} / {{ capability.transport }}</span>
      </div>
      <div class="capability-meta">
        <span>Provider: {{ capability.provider }}</span>
        <span v-if="capability.reason">Reason: {{ capability.reason }}</span>
      </div>

      <div v-if="capability.kind === 'asr'" class="field-row">
        <label>ASR PCM 文件（可选）</label>
        <input class="field-input" type="file" accept="audio/*,.pcm" @change="event => handleAsrFile(capability.capability_id, event)" />
        <span class="field-hint">不上传文件时只执行 health-only readiness 测试。</span>
      </div>

      <div class="provider-actions">
        <button
          class="action-btn test-btn"
          data-test="capability-test"
          type="button"
          @click="runCapabilityTest(capability)"
          :disabled="testing[capability.capability_id]"
        >
          {{ testing[capability.capability_id] ? '测试中...' : '测试能力' }}
        </button>
      </div>

      <div
        v-if="testResults[capability.capability_id]"
        class="test-result"
        :class="testResults[capability.capability_id].ok ? 'ok' : 'error'"
      >
        <span>{{ testResults[capability.capability_id].ok ? '测试通过' : '测试失败' }}</span>
        <span v-if="testResults[capability.capability_id].latency_ms !== undefined">
          ({{ testResults[capability.capability_id].latency_ms }}ms)
        </span>
        <pre>{{ formatResult(testResults[capability.capability_id]) }}</pre>
        <audio v-if="audioUrls[capability.capability_id]" :src="audioUrls[capability.capability_id]" controls />
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { capabilityApi } from '../api'

const capabilities = ref([])
const heartbeat = ref(null)
const loading = ref(false)
const loadError = ref('')
const testing = reactive({})
const testResults = reactive({})
const audioUrls = reactive({})
const asrFiles = reactive({})

const heartbeatProviders = computed(() => heartbeat.value?.providers || [])

onMounted(() => {
  loadDiagnostics()
})

onBeforeUnmount(() => {
  Object.values(audioUrls).forEach(url => URL.revokeObjectURL(url))
})

async function loadDiagnostics() {
  loading.value = true
  loadError.value = ''
  try {
    const [capabilitiesResponse, heartbeatResponse] = await Promise.all([
      capabilityApi.list(),
      capabilityApi.heartbeat()
    ])
    capabilities.value = capabilitiesResponse.data?.capabilities || []
    heartbeat.value = heartbeatResponse.data || null
  } catch (error) {
    loadError.value = '能力诊断加载失败: ' + (error.response?.data?.error?.message || error.message || '未知错误')
  } finally {
    loading.value = false
  }
}

async function runCapabilityTest(capability) {
  const capabilityId = capability.capability_id
  testing[capabilityId] = true
  testResults[capabilityId] = null
  clearAudioUrl(capabilityId)
  try {
    const payload = await buildTestPayload(capability)
    const response = await capabilityApi.test(capabilityId, { payload, mode: 'default' })
    testResults[capabilityId] = response.data
    attachAudioUrl(capabilityId, response.data?.result_summary)
  } catch (error) {
    testResults[capabilityId] = {
      ok: false,
      error: error.response?.data?.error || error.response?.data || {
        code: 'CAPABILITY_TEST_REQUEST_FAILED',
        message: error.message || '请求失败'
      }
    }
  } finally {
    testing[capabilityId] = false
  }
}

async function buildTestPayload(capability) {
  if (capability.kind !== 'asr' || !asrFiles[capability.capability_id]) {
    return {}
  }
  const file = asrFiles[capability.capability_id]
  const audioBase64 = await readFileAsBase64(file)
  return {
    audio_base64: audioBase64,
    media_type: file.type || 'audio/pcm;rate=16000;channels=1;format=s16le',
    language: 'zh-cn'
  }
}

function handleAsrFile(capabilityId, event) {
  const file = event.target.files?.[0]
  if (file) {
    asrFiles[capabilityId] = file
  }
}

function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const value = String(reader.result || '')
      resolve(value.includes(',') ? value.split(',').pop() : value)
    }
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })
}

function attachAudioUrl(capabilityId, summary = {}) {
  const audioBase64 = summary.audio_base64
  if (!audioBase64) return
  const mediaType = summary.media_type || 'audio/mpeg'
  const bytes = Uint8Array.from(atob(audioBase64), char => char.charCodeAt(0))
  const blob = new Blob([bytes], { type: mediaType })
  audioUrls[capabilityId] = URL.createObjectURL(blob)
}

function clearAudioUrl(capabilityId) {
  if (audioUrls[capabilityId]) {
    URL.revokeObjectURL(audioUrls[capabilityId])
    delete audioUrls[capabilityId]
  }
}

function formatResult(result) {
  return JSON.stringify(result.result_summary || result.error || result, null, 2)
}

function statusClass(status) {
  if (['ok', 'ready'].includes(status)) return 'configured'
  if (['disabled', 'unconfigured', 'missing_dependency', 'unreachable'].includes(status)) return 'unconfigured'
  return 'error'
}
</script>

<style scoped>
.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-md);
}

.section-desc {
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin: 4px 0 var(--space-md);
}

.heartbeat-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.provider-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  margin-bottom: var(--space-md);
}

.provider-card.compact {
  margin-bottom: 0;
}

.provider-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
  margin-bottom: var(--space-sm);
}

.provider-name {
  font-weight: 600;
}

.provider-badge,
.source-tag {
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.provider-badge.configured {
  color: #22c55e;
  background: rgba(34, 197, 94, 0.15);
}

.provider-badge.unconfigured {
  color: #eab308;
  background: rgba(234, 179, 8, 0.15);
}

.provider-badge.error {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.15);
}

.source-tag {
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
}

.capability-meta,
.field-hint,
.loading-hint {
  color: var(--text-secondary);
  font-size: 0.8rem;
}

.capability-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: var(--space-sm);
}

.provider-actions {
  display: flex;
  gap: var(--space-sm);
  margin: var(--space-sm) 0;
}

.action-btn {
  padding: 6px 14px;
  font-size: 0.8rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  border: 1px solid var(--border-color);
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.action-btn:hover:not(:disabled) {
  border-color: var(--primary);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.field-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: var(--space-sm);
}

.field-input {
  padding: 6px 10px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
}

.test-result {
  font-size: 0.8rem;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
}

.test-result.ok {
  color: #22c55e;
  background: rgba(34, 197, 94, 0.1);
}

.test-result.error {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

pre {
  overflow: auto;
  max-height: 180px;
  margin: 8px 0;
  color: var(--text-primary);
  white-space: pre-wrap;
}

audio {
  width: 100%;
  margin-top: 8px;
}
</style>
