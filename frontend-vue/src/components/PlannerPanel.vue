<template>
  <aside class="planner-panel" :class="{ collapsed }">
    <div class="planner-header">
      <div>
        <div class="planner-eyebrow">Planner</div>
        <h3>执行清单</h3>
      </div>
      <button class="collapse-btn" @click="$emit('toggle-collapse')">
        {{ collapsed ? '展开' : '收起' }}
      </button>
    </div>

    <template v-if="!collapsed">
      <div class="planner-toolbar">
        <button
          class="toolbar-btn primary"
          :disabled="isGenerating || !draftObjective.trim()"
          @click="onGenerate"
        >
          {{ isGenerating ? '生成中...' : '生成计划' }}
        </button>
        <button
          class="toolbar-btn"
          :disabled="!draftObjective.trim()"
          @click="onCreateManual"
        >
          新建空计划
        </button>
      </div>

      <textarea
        :value="draftObjective"
        class="objective-input"
        rows="4"
        placeholder="输入当前目标，例如：完善多智能体 planner/todo 能力并补齐前后端展示。"
        @input="$emit('update:draft-objective', $event.target.value)"
      ></textarea>

      <div v-if="errorMessage" class="planner-error">{{ errorMessage }}</div>

      <div v-if="plan" class="plan-card">
        <div class="plan-meta">
          <span class="status-badge" :class="`status-${plan.status}`">{{ formatStatus(plan.status) }}</span>
          <span class="summary">{{ plan.summary || '暂无摘要' }}</span>
        </div>
        <div class="plan-objective">{{ plan.objective }}</div>
        <div class="progress-row">
          <span>完成 {{ plan.progress?.completed || 0 }}/{{ plan.progress?.total || 0 }}</span>
          <span v-if="activeItemTitle">当前执行：{{ activeItemTitle }}</span>
        </div>

        <div class="items-list">
          <div v-for="item in plan.items || []" :key="item.id" class="plan-item" :class="`status-${item.status}`">
            <button class="item-status-btn" @click="onCycleStatus(item)" :title="formatStatus(item.status)">
              {{ statusSymbol(item.status) }}
            </button>
            <div class="item-body">
              <div class="item-title-row">
                <span class="item-order">{{ item.step_order }}.</span>
                <input
                  class="item-title-input"
                  :value="item.title"
                  @change="onRenameItem(item, $event.target.value)"
                />
              </div>
              <div class="assignment-row">
                <select class="assignment-select" :value="item.agent_role || 'general'" @change="onUpdateAgentRole(item, $event.target.value)">
                  <option value="general">主智能体</option>
                  <option value="planner">规划子智能体</option>
                  <option value="frontend">前端子智能体</option>
                  <option value="backend">后端子智能体</option>
                  <option value="qa">测试子智能体</option>
                  <option value="docs">文档子智能体</option>
                </select>
                <select class="assignment-select" :value="item.handoff_status || 'unassigned'" @change="onUpdateHandoffStatus(item, $event.target.value)">
                  <option value="unassigned">未分派</option>
                  <option value="ready">待交接</option>
                  <option value="handed_off">已交接</option>
                  <option value="executing">执行中</option>
                  <option value="merged">已合并</option>
                </select>
              </div>
              <div class="assignment-meta">
                <span>负责人：{{ item.owner || '未指定' }}</span>
                <span>Agent ID：{{ item.agent_id || '待分配' }}</span>
              </div>
              <div v-if="item.merge_summary || (item.child_executions && item.child_executions.length)" class="scheduler-block">
                <div class="scheduler-header">
                  <span class="scheduler-title">调度状态</span>
                  <span
                    v-if="item.merge_summary?.merge_status"
                    class="scheduler-badge"
                    :class="`merge-${item.merge_summary.merge_status}`"
                  >
                    {{ formatMergeStatus(item.merge_summary.merge_status) }}
                  </span>
                </div>
                <div class="scheduler-meta">
                  <span>子执行：{{ item.merge_summary?.child_count ?? item.child_executions?.length ?? 0 }}</span>
                  <span v-if="item.merge_summary?.merge_strategy">合并策略：{{ item.merge_summary.merge_strategy }}</span>
                </div>
                <div v-if="item.child_executions && item.child_executions.length" class="child-execution-list">
                  <div
                    v-for="child in item.child_executions"
                    :key="child.child_execution_id || child.agent_id"
                    class="child-execution-item"
                    :class="`child-${child.status}`"
                  >
                    <div class="child-title-row">
                      <span class="child-role">{{ formatAgentRole(child.agent_role) }}</span>
                      <span class="child-status">{{ formatChildStatus(child.status) }}</span>
                    </div>
                    <div class="child-meta">Agent：{{ child.agent_id || '待分配' }}</div>
                    <div v-if="child.summary" class="child-summary">{{ child.summary }}</div>
                    <div v-else-if="child.error" class="child-error">{{ child.error }}</div>
                  </div>
                </div>
              <div v-if="item.merge_summary?.merged_output" class="merge-output">
                  {{ item.merge_summary.merged_output }}
                </div>
              </div>
              <div v-if="item.audit_trail && item.audit_trail.length" class="timeline-block">
                <div class="timeline-header">
                  <span class="timeline-title">执行时间线</span>
                  <span class="timeline-count">{{ item.audit_trail.length }} 条</span>
                </div>
                <div class="timeline-list">
                  <div
                    v-for="(entry, entryIndex) in orderedAuditTrail(item.audit_trail)"
                    :key="`${entry.timestamp || 'na'}-${entry.event_type || 'unknown'}-${entryIndex}`"
                    class="timeline-item"
                  >
                    <div class="timeline-top">
                      <span class="timeline-event">{{ formatAuditEvent(entry.event_type) }}</span>
                      <span class="timeline-time">{{ formatAuditTime(entry.timestamp) }}</span>
                    </div>
                    <div class="timeline-content">{{ entry.content || '无说明' }}</div>
                  </div>
                </div>
              </div>
              <div v-if="item.run_trace && item.run_trace.length" class="trace-block">
                <div class="timeline-header">
                  <span class="timeline-title">运行 Trace</span>
                  <span class="timeline-count">{{ item.run_trace.length }} 条</span>
                </div>
                <div class="trace-list">
                  <div
                    v-for="(entry, entryIndex) in orderedRunTrace(item.run_trace)"
                    :key="`${entry.timestamp || 'na'}-${entry.source || 'runtime'}-${entry.event_type || 'unknown'}-${entryIndex}`"
                    class="trace-item"
                    :class="`trace-${entry.severity || 'info'}`"
                  >
                    <div class="timeline-top">
                      <span class="trace-badges">
                        <span class="trace-source">{{ formatTraceSource(entry.source) }}</span>
                        <span class="trace-event">{{ formatAuditEvent(entry.event_type) }}</span>
                      </span>
                      <span class="timeline-time">{{ formatAuditTime(entry.timestamp) }}</span>
                    </div>
                    <div class="timeline-content">{{ entry.summary || '无摘要' }}</div>
                    <div v-if="entry.detail" class="trace-detail">{{ entry.detail }}</div>
                  </div>
                </div>
              </div>
              <textarea
                class="item-details-input"
                rows="2"
                :value="item.details || ''"
                placeholder="补充该步骤的执行说明"
                @change="onUpdateDetails(item, $event.target.value)"
              ></textarea>
            </div>
            <button class="item-delete-btn" @click="onDeleteItem(item)">删除</button>
          </div>
        </div>

        <div class="add-item-row">
          <input
            :value="newItemTitle"
            class="add-item-input"
            placeholder="新增一个步骤..."
            @input="$emit('update:new-item-title', $event.target.value)"
            @keydown.enter.prevent="onAddItem"
          />
          <button class="toolbar-btn" :disabled="!newItemTitle.trim()" @click="onAddItem">添加</button>
        </div>
      </div>

      <div v-else class="planner-empty">
        <div class="empty-title">还没有执行计划</div>
        <div class="empty-text">先写下当前目标，再生成 Todo。这个面板会作为后续多智能体编排和任务合并的基础。</div>
      </div>
    </template>
  </aside>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  collapsed: {
    type: Boolean,
    default: false
  },
  plan: {
    type: Object,
    default: null
  },
  draftObjective: {
    type: String,
    default: ''
  },
  newItemTitle: {
    type: String,
    default: ''
  },
  isGenerating: {
    type: Boolean,
    default: false
  },
  errorMessage: {
    type: String,
    default: ''
  }
})

const emit = defineEmits([
  'toggle-collapse',
  'generate-plan',
  'create-manual-plan',
  'update:draft-objective',
  'update:new-item-title',
  'update-item-status',
  'rename-item',
  'update-item-details',
  'update-item-agent-role',
  'update-item-handoff-status',
  'delete-item',
  'add-item'
])

const activeItemTitle = computed(() => {
  return props.plan?.items?.find(item => item.status === 'in_progress')?.title || ''
})

function onGenerate() {
  emit('generate-plan')
}

function onCreateManual() {
  emit('create-manual-plan')
}

function onCycleStatus(item) {
  const nextStatusMap = {
    pending: 'in_progress',
    in_progress: 'completed',
    completed: 'pending',
    blocked: 'pending',
    cancelled: 'pending'
  }
  emit('update-item-status', item, nextStatusMap[item.status] || 'pending')
}

function onRenameItem(item, title) {
  emit('rename-item', item, title)
}

function onUpdateDetails(item, details) {
  emit('update-item-details', item, details)
}

function onUpdateAgentRole(item, agentRole) {
  emit('update-item-agent-role', item, agentRole)
}

function onUpdateHandoffStatus(item, handoffStatus) {
  emit('update-item-handoff-status', item, handoffStatus)
}

function onDeleteItem(item) {
  emit('delete-item', item)
}

function onAddItem() {
  emit('add-item')
}

function formatStatus(status) {
  const labelMap = {
    pending: '待开始',
    in_progress: '进行中',
    completed: '已完成',
    blocked: '已阻塞',
    cancelled: '已取消'
  }
  return labelMap[status] || status
}

function statusSymbol(status) {
  const symbolMap = {
    pending: '○',
    in_progress: '◐',
    completed: '●',
    blocked: '!',
    cancelled: '×'
  }
  return symbolMap[status] || '○'
}

function formatMergeStatus(status) {
  const labelMap = {
    pending: '待合并',
    incomplete: '待完成',
    completed: '已合并',
    partial_failed: '部分失败',
    failed: '合并失败'
  }
  return labelMap[status] || status
}

function formatChildStatus(status) {
  const labelMap = {
    queued: '排队中',
    running: '执行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return labelMap[status] || status
}

function formatAgentRole(role) {
  const labelMap = {
    planner: '规划',
    frontend: '前端',
    backend: '后端',
    qa: '测试',
    docs: '文档',
    general: '主智能体'
  }
  return labelMap[role] || role || '未指定'
}

function orderedAuditTrail(entries) {
  return [...(entries || [])].slice().reverse()
}

function orderedRunTrace(entries) {
  return [...(entries || [])].slice().reverse()
}

function formatAuditEvent(eventType) {
  const labelMap = {
    scheduler_fanout_prepared: '已拆分',
    scheduler_execution_started: '开始执行',
    child_running: '子执行启动',
    child_completed: '子执行完成',
    child_failed: '子执行失败',
    child_retrying: '子执行重试',
    child_cancelled: '子执行取消',
    scheduler_cancelled: '调度取消',
    scheduler_merged: '结果合并'
  }
  return labelMap[eventType] || eventType || '未知事件'
}

function formatAuditTime(value) {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`
}

function formatTraceSource(source) {
  const labelMap = {
    scheduler: 'Scheduler',
    subagent: 'Subagent',
    capability: 'Capability',
    tool: 'Tool',
    mcp: 'MCP',
    learning: 'Learning'
  }
  return labelMap[source] || source || 'Runtime'
}
</script>

<style scoped>
.planner-panel {
  width: 340px;
  border-left: 1px solid var(--border-primary);
  background:
    linear-gradient(180deg, rgba(26, 31, 46, 0.98), rgba(18, 22, 34, 0.98)),
    radial-gradient(circle at top right, rgba(72, 187, 120, 0.12), transparent 36%);
  display: flex;
  flex-direction: column;
  padding: var(--space-md);
  gap: var(--space-md);
  overflow: hidden;
}

.planner-panel.collapsed {
  width: 88px;
}

.planner-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-sm);
}

.planner-eyebrow {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #7dd3a7;
}

.planner-header h3 {
  margin: 4px 0 0;
  font-size: 1rem;
}

.collapse-btn,
.toolbar-btn,
.item-delete-btn {
  border: 1px solid var(--border-primary);
  background: var(--bg-surface);
  color: var(--text-primary);
  border-radius: var(--radius-md);
  cursor: pointer;
}

.collapse-btn {
  padding: 6px 10px;
  font-size: 0.75rem;
}

.planner-toolbar,
.add-item-row {
  display: flex;
  gap: var(--space-sm);
}

.toolbar-btn {
  padding: 8px 12px;
  font-size: 0.8rem;
}

.toolbar-btn.primary {
  background: #1f7a4f;
  border-color: #2aa364;
}

.toolbar-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.objective-input,
.add-item-input,
.item-title-input,
.item-details-input {
  width: 100%;
  border: 1px solid var(--border-primary);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-primary);
  border-radius: var(--radius-md);
  outline: none;
}

.objective-input,
.item-details-input {
  resize: vertical;
  padding: 10px 12px;
}

.add-item-input,
.item-title-input {
  padding: 8px 10px;
}

.planner-error {
  padding: 10px 12px;
  border-radius: var(--radius-md);
  background: rgba(220, 38, 38, 0.14);
  color: #fca5a5;
  font-size: 0.8rem;
}

.plan-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  min-height: 0;
}

.plan-meta,
.progress-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-sm);
  font-size: 0.78rem;
  color: var(--text-secondary);
}

.status-badge {
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 0.72rem;
}

.status-badge.status-pending { background: rgba(148, 163, 184, 0.16); }
.status-badge.status-in_progress { background: rgba(59, 130, 246, 0.18); color: #93c5fd; }
.status-badge.status-completed { background: rgba(34, 197, 94, 0.18); color: #86efac; }
.status-badge.status-blocked { background: rgba(249, 115, 22, 0.18); color: #fdba74; }
.status-badge.status-cancelled { background: rgba(239, 68, 68, 0.18); color: #fca5a5; }

.plan-objective {
  font-size: 0.9rem;
  line-height: 1.5;
  color: var(--text-primary);
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  overflow: auto;
  min-height: 0;
}

.plan-item {
  display: grid;
  grid-template-columns: 32px 1fr auto;
  gap: var(--space-sm);
  padding: 10px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.03);
}

.plan-item.status-in_progress {
  border-color: rgba(96, 165, 250, 0.4);
  box-shadow: inset 0 0 0 1px rgba(96, 165, 250, 0.22);
}

.plan-item.status-completed {
  opacity: 0.78;
}

.item-status-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid var(--border-primary);
  background: transparent;
  color: var(--text-primary);
  cursor: pointer;
}

.item-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.assignment-row,
.assignment-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.assignment-select {
  flex: 1;
  min-width: 120px;
  padding: 6px 8px;
  border: 1px solid var(--border-primary);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-primary);
  border-radius: var(--radius-md);
  outline: none;
}

.assignment-meta {
  font-size: 0.74rem;
  color: var(--text-secondary);
  justify-content: space-between;
}

.scheduler-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.035);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.scheduler-header,
.scheduler-meta,
.child-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.scheduler-title {
  font-size: 0.76rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.scheduler-badge {
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 0.7rem;
}

.scheduler-badge.merge-completed {
  background: rgba(34, 197, 94, 0.18);
  color: #86efac;
}

.scheduler-badge.merge-partial_failed {
  background: rgba(249, 115, 22, 0.18);
  color: #fdba74;
}

.scheduler-badge.merge-failed {
  background: rgba(239, 68, 68, 0.18);
  color: #fca5a5;
}

.scheduler-badge.merge-pending,
.scheduler-badge.merge-incomplete {
  background: rgba(148, 163, 184, 0.16);
  color: #cbd5e1;
}

.scheduler-meta,
.child-meta {
  font-size: 0.74rem;
  color: var(--text-secondary);
}

.child-execution-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.child-execution-item {
  padding: 8px 10px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.child-execution-item.child-running {
  border-color: rgba(96, 165, 250, 0.35);
}

.child-execution-item.child-completed {
  border-color: rgba(34, 197, 94, 0.26);
}

.child-execution-item.child-failed {
  border-color: rgba(249, 115, 22, 0.32);
}

.child-role,
.child-status {
  font-size: 0.76rem;
}

.child-summary,
.child-error,
.merge-output {
  white-space: pre-wrap;
  line-height: 1.5;
  font-size: 0.8rem;
}

.child-summary,
.merge-output {
  color: var(--text-primary);
}

.child-error {
  color: #fdba74;
}

.merge-output {
  padding-top: 4px;
  border-top: 1px dashed rgba(255, 255, 255, 0.08);
}

.timeline-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.timeline-header,
.timeline-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.timeline-title {
  font-size: 0.76rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.timeline-count,
.timeline-time {
  font-size: 0.72rem;
  color: var(--text-tertiary);
}

.timeline-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 180px;
  overflow: auto;
}

.timeline-item {
  padding: 8px 10px;
  border-left: 2px solid rgba(125, 211, 167, 0.35);
  background: rgba(255, 255, 255, 0.02);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
}

.timeline-event {
  font-size: 0.76rem;
  color: var(--text-primary);
}

.timeline-content {
  margin-top: 4px;
  line-height: 1.5;
  font-size: 0.78rem;
  color: var(--text-secondary);
}

.trace-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.trace-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 180px;
  overflow: auto;
}

.trace-item {
  padding: 8px 10px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.02);
  border-left: 2px solid rgba(148, 163, 184, 0.32);
}

.trace-item.trace-success {
  border-left-color: rgba(34, 197, 94, 0.45);
}

.trace-item.trace-warning {
  border-left-color: rgba(249, 115, 22, 0.45);
}

.trace-item.trace-error {
  border-left-color: rgba(239, 68, 68, 0.45);
}

.trace-badges {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.trace-source,
.trace-event {
  font-size: 0.72rem;
  padding: 2px 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
}

.trace-detail {
  margin-top: 4px;
  white-space: pre-wrap;
  line-height: 1.5;
  font-size: 0.76rem;
  color: var(--text-tertiary);
}

.item-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.item-order {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.item-delete-btn {
  align-self: start;
  padding: 6px 8px;
  font-size: 0.75rem;
}

.planner-empty {
  padding: 18px 14px;
  border: 1px dashed rgba(255, 255, 255, 0.12);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.02);
}

.empty-title {
  font-size: 0.92rem;
  margin-bottom: 6px;
}

.empty-text {
  font-size: 0.8rem;
  line-height: 1.6;
  color: var(--text-secondary);
}

@media (max-width: 1100px) {
  .planner-panel {
    width: 100%;
    border-left: none;
    border-top: 1px solid var(--border-primary);
  }
}
</style>
