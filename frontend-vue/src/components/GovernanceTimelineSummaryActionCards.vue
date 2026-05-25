<template>
  <div class="summary-action-stack">
    <button
      v-if="lastDoctorOutcome"
      type="button"
      class="panel-card summary-action-card doctor-state-card"
      :class="[`doctor-${lastDoctorOutcome.severity}`, { active: activeFilter === 'doctor' }]"
      @click="emit('filter', 'doctor')"
    >
      <div class="card-head">
        <h3>最近一次 Doctor 结果</h3>
        <span class="muted">{{ formatAuditTime(lastDoctorOutcome.timestamp) }}</span>
      </div>
      <div class="doctor-outcome-row">
        <strong>{{ lastDoctorOutcome.title }}</strong>
        <span>{{ lastDoctorOutcome.detail || '无附加信息' }}</span>
      </div>
    </button>

    <button
      v-if="lastPermissionOutcome"
      type="button"
      class="panel-card summary-action-card permission-state-card"
      :class="[`permission-${lastPermissionOutcome.severity}`, { active: activeFilter === 'permission' }]"
      @click="emit('filter', 'permission')"
    >
      <div class="card-head">
        <h3>最近一次权限结果</h3>
        <span class="muted">{{ formatAuditTime(lastPermissionOutcome.timestamp) }}</span>
      </div>
      <div class="doctor-outcome-row">
        <strong>{{ lastPermissionOutcome.title }}</strong>
        <span>{{ lastPermissionOutcome.content || '无附加信息' }}</span>
      </div>
    </button>

    <button
      v-if="lastMcpOutcome"
      type="button"
      class="panel-card summary-action-card mcp-state-card"
      :class="[`mcp-${lastMcpOutcome.severity}`, { active: activeFilter === 'mcp' }]"
      @click="emit('filter', 'mcp')"
    >
      <div class="card-head">
        <h3>最近一次 MCP 结果</h3>
        <span class="muted">{{ formatAuditTime(lastMcpOutcome.timestamp) }}</span>
      </div>
      <div class="doctor-outcome-row">
        <strong>{{ lastMcpOutcome.title }}</strong>
        <span>{{ lastMcpOutcome.content || lastMcpOutcome.detail || '无附加信息' }}</span>
      </div>
    </button>

    <button
      v-if="lastGovernanceOutcome"
      type="button"
      class="panel-card summary-action-card governance-state-card"
      :class="[`governance-${lastGovernanceOutcome.severity}`, { active: activeFilter === 'governance' }]"
      @click="emit('filter', 'governance')"
    >
      <div class="card-head">
        <h3>最近一次整改结果</h3>
        <span class="muted">{{ formatAuditTime(lastGovernanceOutcome.timestamp) }}</span>
      </div>
      <div class="doctor-outcome-row">
        <strong>{{ lastGovernanceOutcome.title }}</strong>
        <span>{{ lastGovernanceOutcome.content || lastGovernanceOutcome.detail || '无附加信息' }}</span>
      </div>
    </button>

    <button
      v-if="lastSchedulerOutcome"
      type="button"
      class="panel-card summary-action-card scheduler-state-card"
      :class="[`scheduler-${lastSchedulerOutcome.severity}`, { active: activeFilter === 'scheduler' }]"
      @click="emit('filter', 'scheduler')"
    >
      <div class="card-head">
        <h3>最近一次调度结果</h3>
        <span class="muted">{{ formatAuditTime(lastSchedulerOutcome.timestamp) }}</span>
      </div>
      <div class="doctor-outcome-row">
        <strong>{{ lastSchedulerOutcome.title }}</strong>
        <span>{{ lastSchedulerOutcome.content || lastSchedulerOutcome.detail || '无附加信息' }}</span>
      </div>
    </button>

    <button
      v-if="lastHookOutcome"
      type="button"
      class="panel-card summary-action-card hook-state-card"
      :class="[`hook-${lastHookOutcome.severity}`, { active: activeFilter === 'hook' }]"
      @click="emit('filter', 'hook')"
    >
      <div class="card-head">
        <h3>最近一次 Hook 结果</h3>
        <span class="muted">{{ formatAuditTime(lastHookOutcome.timestamp) }}</span>
      </div>
      <div class="doctor-outcome-row">
        <strong>{{ lastHookOutcome.title }}</strong>
        <span>{{ lastHookOutcome.content || lastHookOutcome.detail || '无附加信息' }}</span>
      </div>
    </button>

    <button
      v-if="lastLearningOutcome"
      type="button"
      class="panel-card summary-action-card learning-state-card"
      :class="[`learning-${lastLearningOutcome.severity}`, { active: activeFilter === 'learning' }]"
      @click="emit('filter', 'learning')"
    >
      <div class="card-head">
        <h3>最近一次 Learning 结果</h3>
        <span class="muted">{{ formatAuditTime(lastLearningOutcome.timestamp) }}</span>
      </div>
      <div class="doctor-outcome-row">
        <strong>{{ lastLearningOutcome.title }}</strong>
        <span>{{ lastLearningOutcome.content || lastLearningOutcome.detail || '无附加信息' }}</span>
      </div>
    </button>

    <button
      v-if="lastRuntimeOutcome"
      type="button"
      class="panel-card summary-action-card runtime-state-card"
      :class="[`runtime-${lastRuntimeOutcome.severity}`, { active: activeFilter === 'runtime' }]"
      @click="emit('filter', 'runtime')"
    >
      <div class="card-head">
        <h3>最近一次 Runtime 结果</h3>
        <span class="muted">{{ formatAuditTime(lastRuntimeOutcome.timestamp) }}</span>
      </div>
      <div class="doctor-outcome-row">
        <strong>{{ lastRuntimeOutcome.title }}</strong>
        <span>{{ lastRuntimeOutcome.content || lastRuntimeOutcome.detail || '无附加信息' }}</span>
      </div>
      <span v-if="lastRuntimeOutcome.sourceLabel" class="muted">{{ lastRuntimeOutcome.sourceLabel }}</span>
    </button>
  </div>
</template>

<script setup>
defineOptions({
  name: 'GovernanceTimelineSummaryActionCards',
})

defineProps({
  activeFilter: {
    type: String,
    default: '',
  },
  lastDoctorOutcome: {
    type: Object,
    default: null,
  },
  lastPermissionOutcome: {
    type: Object,
    default: null,
  },
  lastMcpOutcome: {
    type: Object,
    default: null,
  },
  lastGovernanceOutcome: {
    type: Object,
    default: null,
  },
  lastSchedulerOutcome: {
    type: Object,
    default: null,
  },
  lastHookOutcome: {
    type: Object,
    default: null,
  },
  lastLearningOutcome: {
    type: Object,
    default: null,
  },
  lastRuntimeOutcome: {
    type: Object,
    default: null,
  },
  formatAuditTime: {
    type: Function,
    required: true,
  },
})

const emit = defineEmits(['filter'])
</script>
