<template>
  <div class="workflow-lab">
    <header class="lab-hero">
      <div>
        <p class="eyebrow">Coze Migration</p>
        <h1>Workflow Lab</h1>
        <p class="subtitle">
          这里是迁移后的工作流检视、依赖映射和示例回放入口。它只读展示工作流合同，不会影响默认聊天或 Provider 设置。
        </p>
      </div>
      <div class="hero-stats" v-if="summary">
        <div class="stat-card">
          <span class="stat-label">总数</span>
          <strong>{{ summary.total_workflows }}</strong>
        </div>
        <div class="stat-card">
          <span class="stat-label">Ready</span>
          <strong>{{ summary.ready_workflows }}</strong>
        </div>
        <div class="stat-card">
          <span class="stat-label">Blocked</span>
          <strong>{{ summary.invalid_workflows }}</strong>
        </div>
      </div>
    </header>

    <div class="lab-shell">
      <aside class="workflow-list-panel">
        <div class="panel-header">
          <h2>已注册工作流</h2>
          <button class="ghost-btn" type="button" @click="reload">刷新</button>
        </div>
        <div v-if="loadError" class="error-banner">{{ loadError }}</div>
        <button
          v-for="workflow in workflows"
          :key="workflow.workflow_id"
          type="button"
          class="workflow-card"
          :class="{ active: workflow.workflow_id === selectedWorkflowId }"
          @click="selectWorkflow(workflow.workflow_id)"
        >
          <div class="workflow-card-top">
            <strong>{{ workflow.name }}</strong>
            <span class="status-pill" :class="statusClass(workflow.readiness?.status)">
              {{ workflow.readiness?.status || 'unknown' }}
            </span>
          </div>
          <div class="workflow-meta">
            <span>{{ workflow.workflow_id }}</span>
            <span>{{ workflow.capability_id || '-' }}</span>
          </div>
          <div class="workflow-meta">
            <span>Owner: {{ workflow.owner?.primary || '-' }}</span>
            <span>Evidence: {{ workflow.launch_evidence?.status || 'missing' }}</span>
          </div>
        </button>
      </aside>

      <main class="detail-panel" v-if="selectedDetail">
        <section class="detail-hero">
          <div>
            <p class="eyebrow">Workflow Detail</p>
            <h2>{{ selectedDetail.name }}</h2>
            <p class="subtitle">{{ selectedDetail.metadata?.business_owner || selectedDetail.owner?.primary || '-' }}</p>
          </div>
          <div class="detail-badges">
            <span class="status-pill" :class="statusClass(selectedDetail.status)">{{ selectedDetail.status }}</span>
            <span class="status-pill" :class="statusClass(selectedDetail.readiness?.status)">{{ selectedDetail.readiness?.status }}</span>
          </div>
        </section>

        <section class="detail-grid">
          <div class="detail-card">
            <h3>Contract</h3>
            <dl>
              <div><dt>Workflow</dt><dd>{{ selectedDetail.workflow_id }}</dd></div>
              <div><dt>Capability</dt><dd>{{ selectedDetail.capability_id }}</dd></div>
              <div><dt>Version</dt><dd>{{ selectedDetail.version }}</dd></div>
              <div><dt>Launch Evidence</dt><dd>{{ selectedDetail.launch_evidence?.path || 'missing' }}</dd></div>
            </dl>
          </div>

          <div class="detail-card">
            <h3>Governance</h3>
            <dl>
              <div><dt>Permission</dt><dd>{{ selectedDetail.governance?.permission_level || '-' }}</dd></div>
              <div><dt>Trace</dt><dd>{{ selectedDetail.governance?.trace_required ? 'required' : 'optional' }}</dd></div>
              <div><dt>Approval</dt><dd>{{ selectedDetail.governance?.approval_required ? 'required' : 'not required' }}</dd></div>
              <div><dt>Calls</dt><dd>{{ (selectedDetail.governance?.allowed_callers || []).join(', ') || '-' }}</dd></div>
            </dl>
          </div>
        </section>

        <section class="detail-card">
          <div class="section-header">
            <h3>Input Schema</h3>
            <span class="mono">{{ selectedDetail.input_schema?.type || '-' }}</span>
          </div>
          <pre>{{ prettyJson(selectedDetail.input_schema) }}</pre>
        </section>

        <section class="detail-card">
          <div class="section-header">
            <h3>Output Schema</h3>
            <span class="mono">{{ selectedDetail.output_schema?.type || '-' }}</span>
          </div>
          <pre>{{ prettyJson(selectedDetail.output_schema) }}</pre>
        </section>

        <section class="detail-card">
          <div class="section-header">
            <h3>Dependency Mapping</h3>
            <span class="status-pill" :class="statusClass(selectedDetail.dependency_mapping?.status)">
              {{ selectedDetail.dependency_mapping?.status || 'unknown' }}
            </span>
          </div>
          <p class="section-note">{{ selectedDetail.dependency_mapping?.reason }}</p>
          <div class="dependency-list">
            <article v-for="item in selectedDetail.dependency_mapping?.items || []" :key="`${item.kind}-${item.source}`" class="dependency-item">
              <div class="dependency-top">
                <strong>{{ item.kind }}</strong>
                <span class="status-pill" :class="statusClass(item.status)">{{ item.status }}</span>
              </div>
              <div class="dependency-meta">source: {{ item.source }}</div>
              <div class="dependency-meta">target: {{ item.target_capability_id || '-' }}</div>
              <div class="dependency-meta" v-if="item.provider_id">provider: {{ item.provider_id }}</div>
              <div class="dependency-meta" v-if="item.onboarding_path">onboarding: {{ item.onboarding_path }}</div>
              <div class="dependency-meta" v-if="item.blocker">blocker: {{ item.blocker }}</div>
              <div class="dependency-meta" v-if="item.provider_readiness">provider readiness: {{ item.provider_readiness.configuration_status }}</div>
            </article>
          </div>
        </section>

        <section class="detail-card">
          <div class="section-header">
            <h3>Acceptance Examples</h3>
            <span class="mono">{{ selectedDetail.acceptance?.examples?.length || 0 }}</span>
          </div>
          <div class="example-grid">
            <button
              v-for="example in selectedDetail.acceptance?.examples || []"
              :key="example.id"
              type="button"
              class="example-card"
              :class="{ active: activeExampleId === example.id }"
              @click="selectExample(example.id)"
            >
              <strong>{{ example.id }}</strong>
              <span>{{ example.path }}</span>
              <span>{{ example.expected_path }}</span>
            </button>
          </div>
        </section>

        <section class="detail-card">
          <div class="section-header">
            <h3>Replay</h3>
            <button class="ghost-btn" type="button" :disabled="!activeExampleId || isReplaying" @click="replayActiveExample">
              {{ isReplaying ? '回放中...' : '回放示例' }}
            </button>
          </div>
          <div v-if="examplePayload" class="replay-split">
            <div>
              <h4>Input</h4>
              <pre>{{ prettyJson(examplePayload.input?.payload || examplePayload.input) }}</pre>
            </div>
            <div>
              <h4>Expected</h4>
              <pre>{{ prettyJson(examplePayload.expected?.payload || examplePayload.expected) }}</pre>
            </div>
          </div>
          <div v-if="replayResult" class="replay-result">
            <div class="section-header compact">
              <strong>Result</strong>
              <span class="status-pill" :class="statusClass(replayResult.status)">{{ replayResult.status }}</span>
            </div>
            <p class="section-note">run_id: {{ replayResult.run_id || '-' }} · capability: {{ replayResult.capability_id }}</p>
            <pre>{{ prettyJson(replayResult) }}</pre>
          </div>
        </section>

        <section class="detail-card">
          <h3>Prompts</h3>
          <div class="prompt-grid">
            <div v-for="(prompt, key) in selectedDetail.prompts || {}" :key="key" class="prompt-item">
              <strong>{{ key }}</strong>
              <span>{{ prompt.path }}</span>
              <span class="status-pill" :class="prompt.exists ? 'ready' : 'blocked'">
                {{ prompt.exists ? 'exists' : 'missing' }}
              </span>
            </div>
          </div>
        </section>
      </main>

      <main v-else class="detail-panel empty">
        <div class="empty-card">
          <h2>未选择工作流</h2>
          <p>请从左侧列表选择一个已注册的 Coze 工作流。</p>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { workflowLabApi } from '../api'

const summary = ref(null)
const workflows = ref([])
const selectedWorkflowId = ref('')
const selectedDetail = ref(null)
const activeExampleId = ref('')
const examplePayload = ref(null)
const replayResult = ref(null)
const loadError = ref('')
const isReplaying = ref(false)

onMounted(async () => {
  await reload()
})

watch(selectedWorkflowId, async (workflowId) => {
  if (!workflowId) return
  await loadDetail(workflowId)
})

async function reload() {
  loadError.value = ''
  try {
    const response = await workflowLabApi.list()
    summary.value = response.data
    workflows.value = Array.isArray(response.data?.workflows) ? response.data.workflows : []
    if (!selectedWorkflowId.value && workflows.value.length > 0) {
      selectedWorkflowId.value = workflows.value[0].workflow_id
    } else if (selectedWorkflowId.value && !workflows.value.some(item => item.workflow_id === selectedWorkflowId.value)) {
      selectedWorkflowId.value = workflows.value[0]?.workflow_id || ''
    }
  } catch (error) {
    loadError.value = error?.response?.data?.detail || error?.message || '加载 Workflow Lab 失败'
    workflows.value = []
    summary.value = null
    selectedDetail.value = null
  } finally {
  }
}

async function loadDetail(workflowId) {
  try {
    const response = await workflowLabApi.get(workflowId)
    selectedDetail.value = response.data
    activeExampleId.value = response.data?.acceptance?.examples?.[0]?.id || ''
    replayResult.value = null
    examplePayload.value = null
    if (activeExampleId.value) {
      await loadExample(workflowId, activeExampleId.value)
    }
  } catch (error) {
    loadError.value = error?.response?.data?.detail || error?.message || '加载工作流详情失败'
    selectedDetail.value = null
  }
}

async function loadExample(workflowId, exampleId) {
  try {
    const response = await workflowLabApi.getExample(workflowId, exampleId)
    examplePayload.value = response.data
  } catch (error) {
    examplePayload.value = {
      input: { error: error?.response?.data?.detail || error?.message || '加载失败' },
      expected: { error: error?.response?.data?.detail || error?.message || '加载失败' }
    }
  }
}

function selectWorkflow(workflowId) {
  selectedWorkflowId.value = workflowId
}

function selectExample(exampleId) {
  activeExampleId.value = exampleId
  replayResult.value = null
  if (selectedWorkflowId.value) {
    loadExample(selectedWorkflowId.value, exampleId)
  }
}

async function replayActiveExample() {
  if (!selectedWorkflowId.value || !activeExampleId.value) return
  isReplaying.value = true
  replayResult.value = null
  try {
    const response = await workflowLabApi.invokeExample(selectedWorkflowId.value, activeExampleId.value)
    replayResult.value = response.data
  } catch (error) {
    replayResult.value = error?.response?.data || {
      status: 'error',
      error: {
        message: error?.message || '回放失败'
      }
    }
  } finally {
    isReplaying.value = false
  }
}

function prettyJson(value) {
  if (value === undefined || value === null) {
    return '-'
  }
  try {
    return JSON.stringify(value, null, 2)
  } catch (error) {
    return String(value)
  }
}

function statusClass(status) {
  const normalized = String(status || '').toLowerCase()
  if (['ready', 'active', 'completed', 'match', 'present', 'configured'].includes(normalized)) return 'ready'
  if (['blocked', 'invalid', 'mismatch', 'missing', 'unconfigured', 'review'].includes(normalized)) return 'blocked'
  if (['draft', 'declared'].includes(normalized)) return 'draft'
  return 'unknown'
}
</script>

<style scoped>
.workflow-lab {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, rgba(79, 70, 229, 0.18), transparent 28%),
    radial-gradient(circle at top right, rgba(16, 185, 129, 0.12), transparent 24%),
    var(--bg-primary);
}

.lab-hero {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px 12px;
  border-bottom: 1px solid var(--border-primary);
}

.eyebrow {
  margin: 0 0 6px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 0.72rem;
  color: var(--text-tertiary);
}

.lab-hero h1,
.detail-hero h2,
.empty-card h2 {
  margin: 0;
  color: var(--text-primary);
}

.subtitle {
  margin: 8px 0 0;
  max-width: 780px;
  color: var(--text-secondary);
  line-height: 1.6;
  font-size: 0.92rem;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(92px, 1fr));
  gap: 10px;
  align-self: end;
}

.stat-card,
.workflow-card,
.detail-card,
.empty-card {
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  background: rgba(10, 14, 26, 0.72);
  backdrop-filter: blur(10px);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.18);
}

.stat-card {
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 0.72rem;
  color: var(--text-tertiary);
}

.stat-card strong {
  font-size: 1.25rem;
  color: var(--text-primary);
}

.lab-shell {
  flex: 1;
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  min-height: 0;
  overflow: hidden;
}

.workflow-list-panel {
  padding: 16px;
  border-right: 1px solid var(--border-primary);
  overflow-y: auto;
}

.panel-header,
.section-header,
.workflow-card-top,
.dependency-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.panel-header h2,
.detail-card h3 {
  margin: 0;
  color: var(--text-primary);
}

.ghost-btn {
  border: 1px solid var(--border-primary);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-primary);
  border-radius: var(--radius-md);
  padding: 8px 12px;
  cursor: pointer;
}

.ghost-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-banner {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  color: #fecaca;
  border: 1px solid rgba(248, 113, 113, 0.4);
  background: rgba(127, 29, 29, 0.25);
}

.workflow-card {
  width: 100%;
  margin-top: 12px;
  padding: 14px;
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.workflow-card:hover,
.workflow-card.active {
  transform: translateY(-1px);
  border-color: rgba(99, 102, 241, 0.45);
  box-shadow: 0 16px 34px rgba(0, 0, 0, 0.24);
}

.workflow-meta,
.dependency-meta,
.section-note {
  color: var(--text-tertiary);
  font-size: 0.8rem;
}

.workflow-meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-top: 8px;
}

.detail-panel {
  padding: 16px;
  overflow-y: auto;
  min-width: 0;
}

.detail-panel.empty {
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-card {
  max-width: 520px;
  padding: 28px;
  text-align: center;
}

.detail-hero {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.detail-badges {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 14px;
}

.detail-card {
  padding: 14px;
  margin-bottom: 14px;
}

.detail-card dl {
  margin: 12px 0 0;
}

.detail-card dl > div {
  display: grid;
  grid-template-columns: 140px minmax(0, 1fr);
  gap: 10px;
  padding: 6px 0;
}

.detail-card dt {
  color: var(--text-tertiary);
  font-size: 0.78rem;
}

.detail-card dd {
  margin: 0;
  color: var(--text-primary);
  word-break: break-all;
}

.detail-card pre {
  margin: 10px 0 0;
  padding: 12px;
  border-radius: var(--radius-md);
  background: rgba(0, 0, 0, 0.22);
  color: #dbeafe;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.8rem;
  line-height: 1.5;
}

.prompt-grid,
.example-grid,
.dependency-list {
  display: grid;
  gap: 10px;
  margin-top: 10px;
}

.prompt-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.prompt-item,
.dependency-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-primary);
  background: rgba(255, 255, 255, 0.03);
}

.example-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.example-card {
  text-align: left;
  padding: 12px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-primary);
  background: rgba(255, 255, 255, 0.03);
  color: inherit;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.example-card.active,
.example-card:hover {
  border-color: rgba(99, 102, 241, 0.45);
}

.replay-split {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.replay-result {
  margin-top: 12px;
}

.section-header.compact {
  margin-bottom: 6px;
}

.mono {
  font-family: monospace;
  color: var(--text-tertiary);
  font-size: 0.8rem;
}

.status-pill {
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  border: 1px solid transparent;
}

.status-pill.ready {
  color: #86efac;
  background: rgba(34, 197, 94, 0.1);
  border-color: rgba(34, 197, 94, 0.24);
}

.status-pill.blocked {
  color: #fca5a5;
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.24);
}

.status-pill.draft,
.status-pill.unknown {
  color: #cbd5e1;
  background: rgba(148, 163, 184, 0.08);
  border-color: rgba(148, 163, 184, 0.2);
}

@media (max-width: 1100px) {
  .lab-shell {
    grid-template-columns: 1fr;
  }

  .workflow-list-panel {
    border-right: none;
    border-bottom: 1px solid var(--border-primary);
  }
}

@media (max-width: 860px) {
  .lab-hero,
  .detail-hero,
  .detail-grid,
  .replay-split,
  .prompt-grid,
  .example-grid {
    grid-template-columns: 1fr;
    display: grid;
  }

  .lab-hero {
    display: grid;
  }

  .hero-stats {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    align-self: stretch;
  }
}
</style>
