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
        <div v-if="provider.circuit_breaker" class="breaker-meta">
          <span class="source-tag">circuit: {{ provider.circuit_breaker.state || 'unknown' }}</span>
          <span class="field-hint">failures: {{ provider.circuit_breaker.failure_count ?? 0 }}</span>
          <span v-if="provider.circuit_breaker.retry_after_seconds !== undefined" class="field-hint">
            retry in {{ formatRetryAfter(provider.circuit_breaker.retry_after_seconds) }}s
          </span>
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
        <input class="field-input" type="file" accept=".pcm,.raw,application/octet-stream" @change="event => handleAsrFile(capability.capability_id, event)" />
        <span class="field-hint">仅支持 16kHz / mono / PCM s16le；不上传文件时只执行 health-only readiness 测试。</span>
      </div>

      <div v-if="capability.kind === 'ocr'" class="field-row">
        <label>OCR 文件（图片/PDF）</label>
        <input class="field-input" type="file" accept=".png,.jpg,.jpeg,.pdf,image/png,image/jpeg,application/pdf" @change="event => handleOcrFile(capability.capability_id, event)" />
        <label class="inline-check">
          <input type="checkbox" :checked="ocrVisualize[capability.capability_id] === true" @change="event => setOcrVisualize(capability.capability_id, event)" />
          返回可视化（visualize）
        </label>
        <span class="field-hint">建议先用小图测试。图片自动映射为 image/*，PDF 映射为 application/pdf。</span>
      </div>

      <div v-if="capability.kind === 'layout'" class="field-row">
        <label>Layout 文件（图片/PDF）</label>
        <input class="field-input" type="file" accept=".png,.jpg,.jpeg,.pdf,image/png,image/jpeg,application/pdf" @change="event => handleLayoutFile(capability.capability_id, event)" />
        <label>输出格式（output_format）</label>
        <select class="field-input" :value="layoutOutputFormat[capability.capability_id] || 'markdown'" @change="event => setLayoutOutputFormat(capability.capability_id, event)">
          <option value="markdown">markdown</option>
          <option value="json">json</option>
        </select>
        <label class="inline-check">
          <input type="checkbox" :checked="layoutIncludeTables[capability.capability_id] !== false" @change="event => setLayoutIncludeTables(capability.capability_id, event)" />
          包含表格（include_tables）
        </label>
        <label class="inline-check">
          <input type="checkbox" :checked="layoutIncludeLayout[capability.capability_id] !== false" @change="event => setLayoutIncludeLayout(capability.capability_id, event)" />
          包含版面（include_layout）
        </label>
        <label>最大页数（max_pages，可选）</label>
        <input class="field-input" type="number" min="1" step="1" :value="layoutMaxPages[capability.capability_id] || ''" @input="event => setLayoutMaxPages(capability.capability_id, event)" placeholder="例如 10" />
        <span class="field-hint">默认输出 markdown，参数会透传到 layout provider。</span>
      </div>
      <div v-if="capability.kind === 'vlm'" class="field-row">
        <label>VLM 文件（图片/PDF）</label>
        <input class="field-input" type="file" accept=".png,.jpg,.jpeg,.pdf,image/png,image/jpeg,application/pdf" @change="event => handleVlmFile(capability.capability_id, event)" />
        <label>任务（task）</label>
        <select class="field-input" :value="vlmTasks[capability.capability_id] || 'summarize'" @change="event => setVlmTask(capability.capability_id, event)">
          <option value="summarize">summarize</option>
          <option value="extract_fields">extract_fields</option>
          <option value="chart_understanding">chart_understanding</option>
          <option value="qa">qa</option>
        </select>
        <label>问题（question，可选）</label>
        <input class="field-input" type="text" :value="vlmQuestions[capability.capability_id] || ''" @input="event => setVlmQuestion(capability.capability_id, event)" placeholder="例如：请总结合同关键条款" />
        <label>最大页数（max_pages，可选）</label>
        <input class="field-input" type="number" min="1" step="1" :value="vlmMaxPages[capability.capability_id] || ''" @input="event => setVlmMaxPages(capability.capability_id, event)" placeholder="例如 5" />
        <template v-if="capability.capability_id === 'document.vlm.parse.async'">
          <label>任务 ID（job_id，用于查询）</label>
          <input class="field-input" type="text" :value="vlmJobIds[capability.capability_id] || ''" @input="event => setVlmJobId(capability.capability_id, event)" placeholder="例如 job_20260601_001" />
        </template>
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
        <button
          v-if="capability.kind === 'ocr'"
          class="action-btn test-btn"
          data-test="ocr-invoke"
          type="button"
          @click="runOcrInvoke(capability)"
          :disabled="testing[capability.capability_id]"
        >
          {{ testing[capability.capability_id] ? '测试中...' : '测试 OCR' }}
        </button>
        <button
          v-if="capability.kind === 'layout'"
          class="action-btn test-btn"
          data-test="layout-invoke"
          type="button"
          @click="runLayoutInvoke(capability)"
          :disabled="testing[capability.capability_id]"
        >
          {{ testing[capability.capability_id] ? '测试中...' : '测试 Layout' }}
        </button>
        <button
          v-if="capability.kind === 'vlm' && capability.capability_id !== 'document.vlm.parse.async'"
          class="action-btn test-btn"
          data-test="vlm-invoke"
          type="button"
          @click="runVlmInvoke(capability)"
          :disabled="testing[capability.capability_id]"
        >
          {{ testing[capability.capability_id] ? '测试中...' : '测试 VLM' }}
        </button>
        <button
          v-if="capability.kind === 'vlm' && capability.capability_id === 'document.vlm.parse.async'"
          class="action-btn test-btn"
          data-test="vlm-async-submit"
          type="button"
          @click="runVlmAsyncSubmit(capability)"
          :disabled="testing[capability.capability_id]"
        >
          {{ testing[capability.capability_id] ? '测试中...' : '提交 VLM 任务' }}
        </button>
        <button
          v-if="capability.kind === 'vlm' && capability.capability_id === 'document.vlm.parse.async'"
          class="action-btn test-btn"
          data-test="vlm-async-status"
          type="button"
          @click="runVlmAsyncStatus(capability)"
          :disabled="testing[capability.capability_id]"
        >
          {{ testing[capability.capability_id] ? '测试中...' : '查询任务状态' }}
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
        <template v-if="capability.kind === 'ocr' && ocrResultView(testResults[capability.capability_id])">
          <div class="ocr-summary">
            <span>文本长度: {{ ocrResultView(testResults[capability.capability_id]).text.length }}</span>
            <span>页面数: {{ ocrResultView(testResults[capability.capability_id]).pages.length }}</span>
            <span>Blocks: {{ ocrResultView(testResults[capability.capability_id]).blocks.length }}</span>
          </div>
          <div v-if="ocrResultView(testResults[capability.capability_id]).warnings.length" class="ocr-warning-list">
            <span
              v-for="(warning, idx) in ocrResultView(testResults[capability.capability_id]).warnings"
              :key="'ocr-warning-' + idx"
              class="field-hint"
            >
              warning: {{ warning }}
            </span>
          </div>
          <details class="ocr-section" open>
            <summary>文本结果</summary>
            <pre>{{ ocrResultView(testResults[capability.capability_id]).text || '(empty)' }}</pre>
          </details>
          <details class="ocr-section">
            <summary>Blocks / 置信度</summary>
            <pre>{{ formatOcrBlocks(ocrResultView(testResults[capability.capability_id]).blocks) }}</pre>
          </details>
          <details class="ocr-section">
            <summary>Pages</summary>
            <pre>{{ formatJson(ocrResultView(testResults[capability.capability_id]).pages) }}</pre>
          </details>
          <details class="ocr-section">
            <summary>Raw JSON</summary>
            <pre>{{ formatJson(ocrResultView(testResults[capability.capability_id]).raw) }}</pre>
          </details>
        </template>
        <template v-else-if="capability.kind === 'layout' && layoutResultView(testResults[capability.capability_id])">
          <div class="ocr-summary">
            <span>Markdown 长度: {{ layoutResultView(testResults[capability.capability_id]).markdown.length }}</span>
            <span>Elements: {{ layoutResultView(testResults[capability.capability_id]).elements.length }}</span>
            <span>Tables: {{ layoutResultView(testResults[capability.capability_id]).tables.length }}</span>
          </div>
          <div v-if="layoutResultView(testResults[capability.capability_id]).warnings.length" class="ocr-warning-list">
            <span
              v-for="(warning, idx) in layoutResultView(testResults[capability.capability_id]).warnings"
              :key="'layout-warning-' + idx"
              class="field-hint"
            >
              warning: {{ warning }}
            </span>
          </div>
          <details class="ocr-section" open>
            <summary>Markdown</summary>
            <pre>{{ layoutResultView(testResults[capability.capability_id]).markdown || '(empty)' }}</pre>
          </details>
          <div class="provider-actions">
            <button class="action-btn test-btn" type="button" @click="copyLayoutMarkdown(layoutResultView(testResults[capability.capability_id]).markdown)">
              复制 Markdown
            </button>
            <button class="action-btn test-btn" type="button" @click="downloadLayoutResult(capability.capability_id, layoutResultView(testResults[capability.capability_id]))">
              导出 JSON
            </button>
          </div>
          <details class="ocr-section">
            <summary>Elements</summary>
            <pre>{{ formatJson(layoutResultView(testResults[capability.capability_id]).elements) }}</pre>
          </details>
          <details class="ocr-section">
            <summary>Tables</summary>
            <pre>{{ formatJson(layoutResultView(testResults[capability.capability_id]).tables) }}</pre>
          </details>
          <details class="ocr-section">
            <summary>Pages</summary>
            <pre>{{ formatJson(layoutResultView(testResults[capability.capability_id]).pages) }}</pre>
          </details>
          <details class="ocr-section">
            <summary>Raw JSON</summary>
            <pre>{{ formatJson(layoutResultView(testResults[capability.capability_id]).raw) }}</pre>
          </details>
        </template>
        <template v-else-if="capability.capability_id === 'document.vlm.parse.async' && vlmAsyncResultView(testResults[capability.capability_id])">
          <div class="ocr-summary">
            <span>Job: {{ vlmAsyncResultView(testResults[capability.capability_id]).job_id || '(missing)' }}</span>
            <span>Status: {{ vlmAsyncResultView(testResults[capability.capability_id]).status }}</span>
            <span>Progress: {{ vlmAsyncResultView(testResults[capability.capability_id]).progress }}</span>
          </div>
          <div v-if="vlmAsyncResultView(testResults[capability.capability_id]).warnings.length" class="ocr-warning-list">
            <span
              v-for="(warning, idx) in vlmAsyncResultView(testResults[capability.capability_id]).warnings"
              :key="'vlm-async-warning-' + idx"
              class="field-hint"
            >
              warning: {{ warning }}
            </span>
          </div>
          <details class="ocr-section" open>
            <summary>Async Result</summary>
            <pre>{{ formatJson(vlmAsyncResultView(testResults[capability.capability_id]).result) }}</pre>
          </details>
          <details class="ocr-section">
            <summary>Async Error</summary>
            <pre>{{ formatJson(vlmAsyncResultView(testResults[capability.capability_id]).error) }}</pre>
          </details>
          <details class="ocr-section">
            <summary>Raw JSON</summary>
            <pre>{{ formatJson(vlmAsyncResultView(testResults[capability.capability_id]).raw) }}</pre>
          </details>
        </template>
        <template v-else-if="capability.kind === 'vlm' && vlmResultView(testResults[capability.capability_id])">
          <div class="ocr-summary">
            <span>Summary 长度: {{ vlmResultView(testResults[capability.capability_id]).summary.length }}</span>
            <span>Sections: {{ vlmResultView(testResults[capability.capability_id]).sections.length }}</span>
            <span>Evidence: {{ vlmResultView(testResults[capability.capability_id]).evidence.length }}</span>
          </div>
          <div v-if="vlmResultView(testResults[capability.capability_id]).warnings.length" class="ocr-warning-list">
            <span
              v-for="(warning, idx) in vlmResultView(testResults[capability.capability_id]).warnings"
              :key="'vlm-warning-' + idx"
              class="field-hint"
            >
              warning: {{ warning }}
            </span>
          </div>
          <details class="ocr-section" open>
            <summary>Summary</summary>
            <pre>{{ vlmResultView(testResults[capability.capability_id]).summary || '(empty)' }}</pre>
          </details>
          <details class="ocr-section">
            <summary>Sections</summary>
            <pre>{{ formatJson(vlmResultView(testResults[capability.capability_id]).sections) }}</pre>
          </details>
          <details class="ocr-section">
            <summary>Answers</summary>
            <pre>{{ formatJson(vlmResultView(testResults[capability.capability_id]).answers) }}</pre>
          </details>
          <details class="ocr-section">
            <summary>Raw JSON</summary>
            <pre>{{ formatJson(vlmResultView(testResults[capability.capability_id]).raw) }}</pre>
          </details>
        </template>
        <pre v-else>{{ formatResult(testResults[capability.capability_id]) }}</pre>
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
const ocrFiles = reactive({})
const ocrVisualize = reactive({})
const layoutFiles = reactive({})
const layoutIncludeTables = reactive({})
const layoutIncludeLayout = reactive({})
const layoutOutputFormat = reactive({})
const layoutMaxPages = reactive({})
const vlmFiles = reactive({})
const vlmTasks = reactive({})
const vlmQuestions = reactive({})
const vlmMaxPages = reactive({})
const vlmJobIds = reactive({})

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

async function runOcrInvoke(capability) {
  const capabilityId = capability.capability_id
  testing[capabilityId] = true
  testResults[capabilityId] = null
  try {
    const payload = await buildOcrInvokePayload(capabilityId)
    const response = await capabilityApi.invoke(capabilityId, payload)
    testResults[capabilityId] = response.data
  } catch (error) {
    testResults[capabilityId] = {
      ok: false,
      error: error.response?.data?.error || error.response?.data || {
        code: 'OCR_INVOKE_REQUEST_FAILED',
        message: error.message || '请求失败'
      }
    }
  } finally {
    testing[capabilityId] = false
  }
}

async function runLayoutInvoke(capability) {
  const capabilityId = capability.capability_id
  testing[capabilityId] = true
  testResults[capabilityId] = null
  try {
    const payload = await buildLayoutInvokePayload(capabilityId)
    const response = await capabilityApi.invoke(capabilityId, payload)
    testResults[capabilityId] = response.data
  } catch (error) {
    testResults[capabilityId] = {
      ok: false,
      error: error.response?.data?.error || error.response?.data || {
        code: 'LAYOUT_INVOKE_REQUEST_FAILED',
        message: error.message || '请求失败'
      }
    }
  } finally {
    testing[capabilityId] = false
  }
}

async function runVlmInvoke(capability) {
  const capabilityId = capability.capability_id
  testing[capabilityId] = true
  testResults[capabilityId] = null
  try {
    const payload = await buildVlmInvokePayload(capabilityId)
    const response = await capabilityApi.invoke(capabilityId, payload)
    testResults[capabilityId] = response.data
  } catch (error) {
    testResults[capabilityId] = {
      ok: false,
      error: error.response?.data?.error || error.response?.data || {
        code: 'VLM_INVOKE_REQUEST_FAILED',
        message: error.message || '请求失败'
      }
    }
  } finally {
    testing[capabilityId] = false
  }
}

async function runVlmAsyncSubmit(capability) {
  const capabilityId = capability.capability_id
  testing[capabilityId] = true
  testResults[capabilityId] = null
  try {
    const payload = await buildVlmInvokePayload(capabilityId, 'submit')
    const response = await capabilityApi.invoke(capabilityId, payload)
    testResults[capabilityId] = response.data
    if (response.data?.ok && response.data?.result?.job_id) {
      vlmJobIds[capabilityId] = String(response.data.result.job_id)
    }
  } catch (error) {
    testResults[capabilityId] = {
      ok: false,
      error: error.response?.data?.error || error.response?.data || {
        code: 'VLM_ASYNC_SUBMIT_REQUEST_FAILED',
        message: error.message || '请求失败'
      }
    }
  } finally {
    testing[capabilityId] = false
  }
}

async function runVlmAsyncStatus(capability) {
  const capabilityId = capability.capability_id
  testing[capabilityId] = true
  testResults[capabilityId] = null
  try {
    const payload = await buildVlmInvokePayload(capabilityId, 'status')
    const response = await capabilityApi.invoke(capabilityId, payload)
    testResults[capabilityId] = response.data
  } catch (error) {
    testResults[capabilityId] = {
      ok: false,
      error: error.response?.data?.error || error.response?.data || {
        code: 'VLM_ASYNC_STATUS_REQUEST_FAILED',
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
  const mediaType = resolveAsrMediaType(file)
  if (!isSupportedAsrMediaType(mediaType)) {
    throw new Error('ASR 测试仅支持 16kHz / mono / PCM s16le 文件，请先将 MP3/WAV/WebM 转为 raw PCM。')
  }
  const audioBase64 = await readFileAsBase64(file)
  return {
    audio_base64: audioBase64,
    media_type: mediaType,
    language: 'zh-cn'
  }
}

function handleAsrFile(capabilityId, event) {
  const file = event.target.files?.[0]
  if (file) {
    asrFiles[capabilityId] = file
    return
  }
  delete asrFiles[capabilityId]
}

function handleOcrFile(capabilityId, event) {
  const file = event.target.files?.[0]
  if (file) {
    ocrFiles[capabilityId] = file
    return
  }
  delete ocrFiles[capabilityId]
}

function setOcrVisualize(capabilityId, event) {
  ocrVisualize[capabilityId] = Boolean(event.target.checked)
}

function handleLayoutFile(capabilityId, event) {
  const file = event.target.files?.[0]
  if (file) {
    layoutFiles[capabilityId] = file
    return
  }
  delete layoutFiles[capabilityId]
}

function setLayoutIncludeTables(capabilityId, event) {
  layoutIncludeTables[capabilityId] = Boolean(event.target.checked)
}

function setLayoutIncludeLayout(capabilityId, event) {
  layoutIncludeLayout[capabilityId] = Boolean(event.target.checked)
}

function setLayoutOutputFormat(capabilityId, event) {
  layoutOutputFormat[capabilityId] = String(event.target.value || 'markdown')
}

function setLayoutMaxPages(capabilityId, event) {
  const value = String(event.target.value || '').trim()
  layoutMaxPages[capabilityId] = value
}

function handleVlmFile(capabilityId, event) {
  const file = event.target.files?.[0]
  if (file) {
    vlmFiles[capabilityId] = file
    return
  }
  delete vlmFiles[capabilityId]
}

function setVlmTask(capabilityId, event) {
  vlmTasks[capabilityId] = String(event.target.value || 'summarize')
}

function setVlmQuestion(capabilityId, event) {
  vlmQuestions[capabilityId] = String(event.target.value || '')
}

function setVlmMaxPages(capabilityId, event) {
  vlmMaxPages[capabilityId] = String(event.target.value || '').trim()
}

function setVlmJobId(capabilityId, event) {
  vlmJobIds[capabilityId] = String(event.target.value || '').trim()
}

function resolveAsrMediaType(file) {
  if (!file.type || file.name?.toLowerCase().endsWith('.pcm') || file.name?.toLowerCase().endsWith('.raw')) {
    return 'audio/pcm;rate=16000;channels=1;format=s16le'
  }
  return file.type
}

function isSupportedAsrMediaType(mediaType) {
  const value = String(mediaType || '').toLowerCase()
  return value.startsWith('audio/pcm') || value === 'application/octet-stream'
}

function readFileAsBase64(file) {
  if (file && typeof file.arrayBuffer === 'function') {
    return file.arrayBuffer().then(buffer => {
      const bytes = new Uint8Array(buffer)
      let binary = ''
      for (let i = 0; i < bytes.length; i += 1) {
        binary += String.fromCharCode(bytes[i])
      }
      return btoa(binary)
    })
  }
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

async function buildOcrInvokePayload(capabilityId) {
  const file = ocrFiles[capabilityId]
  if (!file) {
    throw new Error('请先选择 OCR 文件（png/jpg/pdf）')
  }
  const mediaType = resolveOcrMediaType(file)
  const fileBase64 = await readFileAsBase64(file)
  return {
    file_base64: fileBase64,
    media_type: mediaType,
    filename: file.name,
    visualize: ocrVisualize[capabilityId] === true
  }
}

function resolveOcrMediaType(file) {
  const name = String(file.name || '').toLowerCase()
  if (name.endsWith('.pdf')) return 'application/pdf'
  if (name.endsWith('.png')) return 'image/png'
  if (name.endsWith('.jpg') || name.endsWith('.jpeg')) return 'image/jpeg'
  if (file.type) return file.type
  return 'application/octet-stream'
}

async function buildLayoutInvokePayload(capabilityId) {
  const file = layoutFiles[capabilityId]
  if (!file) {
    throw new Error('请先选择 Layout 文件（png/jpg/pdf）')
  }
  const mediaType = resolveOcrMediaType(file)
  const fileBase64 = await readFileAsBase64(file)
  return {
    file_base64: fileBase64,
    media_type: mediaType,
    filename: file.name,
    output_format: layoutOutputFormat[capabilityId] || 'markdown',
    include_tables: layoutIncludeTables[capabilityId] !== false,
    include_layout: layoutIncludeLayout[capabilityId] !== false,
    max_pages: toPositiveInteger(layoutMaxPages[capabilityId])
  }
}

async function buildVlmInvokePayload(capabilityId, operation = 'submit') {
  if (operation === 'status') {
    const jobId = String(vlmJobIds[capabilityId] || '').trim()
    if (!jobId) {
      throw new Error('请先输入任务 ID（job_id）')
    }
    return {
      operation: 'status',
      job_id: jobId
    }
  }
  const file = vlmFiles[capabilityId]
  if (!file) {
    throw new Error('请先选择 VLM 文件（png/jpg/pdf）')
  }
  const mediaType = resolveOcrMediaType(file)
  const fileBase64 = await readFileAsBase64(file)
  return {
    operation: 'submit',
    file_base64: fileBase64,
    media_type: mediaType,
    filename: file.name,
    task: vlmTasks[capabilityId] || 'summarize',
    question: String(vlmQuestions[capabilityId] || ''),
    max_pages: toPositiveInteger(vlmMaxPages[capabilityId])
  }
}

function toPositiveInteger(value) {
  if (value === undefined || value === null || value === '') {
    return undefined
  }
  const numeric = Number.parseInt(String(value), 10)
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return undefined
  }
  return numeric
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

function formatJson(value) {
  return JSON.stringify(value ?? {}, null, 2)
}

function ocrResultView(result) {
  if (!result || !result.ok) return null
  const payload = typeof result.result === 'object' && result.result ? result.result : null
  if (!payload) return null
  return {
    text: String(payload.text || ''),
    pages: Array.isArray(payload.pages) ? payload.pages : [],
    blocks: Array.isArray(payload.blocks) ? payload.blocks : [],
    warnings: Array.isArray(payload.warnings) ? payload.warnings.map(item => String(item)) : [],
    raw: typeof payload.raw === 'object' && payload.raw ? payload.raw : {}
  }
}

function layoutResultView(result) {
  if (!result || !result.ok) return null
  const payload = typeof result.result === 'object' && result.result ? result.result : null
  if (!payload) return null
  return {
    markdown: String(payload.markdown || ''),
    elements: Array.isArray(payload.elements) ? payload.elements : [],
    tables: Array.isArray(payload.tables) ? payload.tables : [],
    pages: Array.isArray(payload.pages) ? payload.pages : [],
    warnings: Array.isArray(payload.warnings) ? payload.warnings.map(item => String(item)) : [],
    raw: typeof payload.raw === 'object' && payload.raw ? payload.raw : {}
  }
}

function vlmResultView(result) {
  if (!result || !result.ok) return null
  const payload = typeof result.result === 'object' && result.result ? result.result : null
  if (!payload) return null
  return {
    summary: String(payload.summary || ''),
    sections: Array.isArray(payload.sections) ? payload.sections : [],
    answers: Array.isArray(payload.answers) ? payload.answers : [],
    evidence: Array.isArray(payload.evidence) ? payload.evidence : [],
    warnings: Array.isArray(payload.warnings) ? payload.warnings.map(item => String(item)) : [],
    raw: typeof payload.raw === 'object' && payload.raw ? payload.raw : {}
  }
}

function vlmAsyncResultView(result) {
  if (!result || !result.ok) return null
  const payload = typeof result.result === 'object' && result.result ? result.result : null
  if (!payload) return null
  return {
    job_id: String(payload.job_id || ''),
    status: String(payload.status || 'unknown'),
    progress: payload.progress ?? 0,
    result: typeof payload.result === 'object' && payload.result ? payload.result : {},
    error: typeof payload.error === 'object' && payload.error ? payload.error : {},
    warnings: Array.isArray(payload.warnings) ? payload.warnings.map(item => String(item)) : [],
    raw: typeof payload.raw === 'object' && payload.raw ? payload.raw : {}
  }
}

async function copyLayoutMarkdown(markdown) {
  const value = String(markdown || '')
  if (!value || !navigator?.clipboard?.writeText) {
    return
  }
  await navigator.clipboard.writeText(value)
}

function downloadLayoutResult(capabilityId, result) {
  const payload = JSON.stringify(result || {}, null, 2)
  const blob = new Blob([payload], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${capabilityId.replace(/[^\w.-]/g, '_')}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function formatOcrBlocks(blocks) {
  if (!Array.isArray(blocks) || blocks.length === 0) {
    return '(empty)'
  }
  return blocks
    .map((block, idx) => {
      const confidence = block?.confidence === null || block?.confidence === undefined ? '-' : block.confidence
      const bbox = Array.isArray(block?.bbox) ? JSON.stringify(block.bbox) : '-'
      const text = String(block?.text || '').trim() || '(empty)'
      return `${idx + 1}. conf=${confidence} bbox=${bbox}\n${text}`
    })
    .join('\n\n')
}

function statusClass(status) {
  if (['ok', 'ready'].includes(status)) return 'configured'
  if (['disabled', 'unconfigured', 'missing_dependency', 'unreachable'].includes(status)) return 'unconfigured'
  return 'error'
}

function formatRetryAfter(value) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric) || numeric < 0) return '0.00'
  return numeric.toFixed(2)
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

.breaker-meta {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
  margin-bottom: 4px;
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

.inline-check {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  color: var(--text-secondary);
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

.ocr-summary {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-top: 8px;
  color: var(--text-primary);
}

.ocr-warning-list {
  display: flex;
  flex-direction: column;
  margin-top: 8px;
}

.ocr-section {
  margin-top: 8px;
}

.ocr-section > summary {
  cursor: pointer;
  color: var(--text-primary);
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
