<template>
  <div class="summary-action-stack">
    <button
      v-if="lastFrameworkAdapterPilotOutcome"
      type="button"
      class="panel-card summary-action-card framework-adapter-state-card"
      :class="[`framework-adapter-${lastFrameworkAdapterPilotOutcome.severity}`, { active: isSummaryOutcomeActive(lastFrameworkAdapterPilotOutcome, 'framework_adapter') }]"
      @click="emit('focus-entry', lastFrameworkAdapterPilotOutcome, 'framework_adapter')"
    >
      <div class="card-head">
        <h3>{{ formatFrameworkAdapterSummaryHeading(lastFrameworkAdapterPilotOutcome, 'Pilot') }}</h3>
        <span class="muted">{{ formatAuditTime(lastFrameworkAdapterPilotOutcome.timestamp) }}</span>
      </div>
      <div class="doctor-outcome-row">
        <strong>{{ lastFrameworkAdapterPilotOutcome.title }}</strong>
        <span>{{ lastFrameworkAdapterPilotOutcome.content || lastFrameworkAdapterPilotOutcome.detail || '无附加信息' }}</span>
      </div>
      <span class="muted">{{ formatFrameworkAdapterIdentityLine(lastFrameworkAdapterPilotOutcome) }}</span>
    </button>

    <button
      v-if="lastFrameworkAdapterPrecheckOutcome"
      type="button"
      class="panel-card summary-action-card framework-adapter-state-card"
      :class="[`framework-adapter-${lastFrameworkAdapterPrecheckOutcome.severity}`, { active: isSummaryOutcomeActive(lastFrameworkAdapterPrecheckOutcome, 'framework_adapter') }]"
      @click="emit('focus-entry', lastFrameworkAdapterPrecheckOutcome, 'framework_adapter')"
    >
      <div class="card-head">
        <h3>{{ formatFrameworkAdapterSummaryHeading(lastFrameworkAdapterPrecheckOutcome, 'Precheck') }}</h3>
        <span class="muted">{{ formatAuditTime(lastFrameworkAdapterPrecheckOutcome.timestamp) }}</span>
      </div>
      <div class="doctor-outcome-row">
        <strong>{{ lastFrameworkAdapterPrecheckOutcome.title }}</strong>
        <span>{{ lastFrameworkAdapterPrecheckOutcome.content || lastFrameworkAdapterPrecheckOutcome.detail || '无附加信息' }}</span>
      </div>
      <span class="muted">{{ formatFrameworkAdapterIdentityLine(lastFrameworkAdapterPrecheckOutcome) }}</span>
    </button>

    <button
      v-if="lastFrameworkAdapterExternalPilotOutcome"
      type="button"
      class="panel-card summary-action-card framework-adapter-state-card"
      :class="[`framework-adapter-${lastFrameworkAdapterExternalPilotOutcome.severity}`, { active: isSummaryOutcomeActive(lastFrameworkAdapterExternalPilotOutcome, 'framework_adapter') }]"
      @click="emit('focus-entry', lastFrameworkAdapterExternalPilotOutcome, 'framework_adapter')"
    >
      <div class="card-head">
        <h3>{{ formatFrameworkAdapterSummaryHeading(lastFrameworkAdapterExternalPilotOutcome, 'External Pilot') }}</h3>
        <span class="muted">{{ formatAuditTime(lastFrameworkAdapterExternalPilotOutcome.timestamp) }}</span>
      </div>
      <div class="doctor-outcome-row">
        <strong>{{ lastFrameworkAdapterExternalPilotOutcome.title }}</strong>
        <span>{{ lastFrameworkAdapterExternalPilotOutcome.content || lastFrameworkAdapterExternalPilotOutcome.detail || '无附加信息' }}</span>
      </div>
      <span class="muted">{{ formatFrameworkAdapterIdentityLine(lastFrameworkAdapterExternalPilotOutcome) }}</span>
    </button>

    <div
      v-if="lastFrameworkAdapterExternalFailureDiagnostic"
      class="panel-card summary-action-card framework-adapter-state-card framework-adapter-diagnostic-card"
      :class="[`framework-adapter-${lastFrameworkAdapterExternalFailureDiagnostic.severity}`, { active: isSummaryOutcomeActive(lastFrameworkAdapterExternalFailureDiagnostic, 'framework_adapter') }]"
    >
      <button
        type="button"
        class="summary-action-main"
        @click="emit('focus-entry', lastFrameworkAdapterExternalFailureDiagnostic, 'framework_adapter')"
      >
        <div class="card-head">
          <h3>{{ formatFrameworkAdapterSummaryHeading(lastFrameworkAdapterExternalFailureDiagnostic, 'External Pilot 失败诊断') }}</h3>
          <span class="muted">{{ formatAuditTime(lastFrameworkAdapterExternalFailureDiagnostic.timestamp) }}</span>
        </div>
        <div class="doctor-outcome-row">
          <strong>{{ lastFrameworkAdapterExternalFailureDiagnostic.title }}</strong>
          <span>{{ lastFrameworkAdapterExternalFailureDiagnostic.content || lastFrameworkAdapterExternalFailureDiagnostic.detail || '无附加信息' }}</span>
        </div>
        <span class="muted">{{ formatFrameworkAdapterIdentityLine(lastFrameworkAdapterExternalFailureDiagnostic) }}</span>
        <div
          v-if="formatFrameworkAdapterFailureCount(lastFrameworkAdapterExternalFailureDiagnostic) || formatFrameworkAdapterFailureDistribution(lastFrameworkAdapterExternalFailureDiagnostic)"
          class="catalog-tags remediation-status-tags"
        >
          <span
            v-if="formatFrameworkAdapterFailureCount(lastFrameworkAdapterExternalFailureDiagnostic)"
            class="capability-pill"
          >
            失败总数: {{ formatFrameworkAdapterFailureCount(lastFrameworkAdapterExternalFailureDiagnostic) }}
          </span>
          <span
            v-if="formatFrameworkAdapterFailureWindow(lastFrameworkAdapterExternalFailureDiagnostic)"
            class="capability-pill"
          >
            统计窗口: {{ formatFrameworkAdapterFailureWindow(lastFrameworkAdapterExternalFailureDiagnostic) }}
          </span>
          <span
            v-if="formatFrameworkAdapterFailureSampleSize(lastFrameworkAdapterExternalFailureDiagnostic)"
            class="capability-pill"
          >
            样本数: {{ formatFrameworkAdapterFailureSampleSize(lastFrameworkAdapterExternalFailureDiagnostic) }}
          </span>
          <span
            v-if="formatFrameworkAdapterFailureDistribution(lastFrameworkAdapterExternalFailureDiagnostic)"
            class="capability-pill"
          >
            错误分布: {{ formatFrameworkAdapterFailureDistribution(lastFrameworkAdapterExternalFailureDiagnostic) }}
          </span>
        </div>
      </button>
      <div class="overview-card-actions remediation-card-actions diagnostic-card-actions">
        <button
          type="button"
          class="overview-risk-btn"
          @click.stop="emit('open-runtime-surface')"
        >
          打开运行时面板
        </button>
        <button
          type="button"
          class="overview-risk-btn"
          @click.stop="emit('copy-snapshot-command', lastFrameworkAdapterExternalFailureDiagnostic)"
        >
          {{ copiedCommandTarget === lastFrameworkAdapterExternalFailureDiagnostic.key ? '已复制命令' : '复制快照命令' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineOptions({
  name: 'GovernanceTimelineFrameworkAdapterCards',
})

defineProps({
  copiedCommandTarget: {
    type: String,
    default: '',
  },
  lastFrameworkAdapterPilotOutcome: {
    type: Object,
    default: null,
  },
  lastFrameworkAdapterPrecheckOutcome: {
    type: Object,
    default: null,
  },
  lastFrameworkAdapterExternalPilotOutcome: {
    type: Object,
    default: null,
  },
  lastFrameworkAdapterExternalFailureDiagnostic: {
    type: Object,
    default: null,
  },
  formatAuditTime: {
    type: Function,
    required: true,
  },
  formatFrameworkAdapterSummaryHeading: {
    type: Function,
    required: true,
  },
  formatFrameworkAdapterIdentityLine: {
    type: Function,
    required: true,
  },
  formatFrameworkAdapterFailureCount: {
    type: Function,
    required: true,
  },
  formatFrameworkAdapterFailureDistribution: {
    type: Function,
    required: true,
  },
  formatFrameworkAdapterFailureWindow: {
    type: Function,
    required: true,
  },
  formatFrameworkAdapterFailureSampleSize: {
    type: Function,
    required: true,
  },
  isSummaryOutcomeActive: {
    type: Function,
    required: true,
  },
})

const emit = defineEmits(['focus-entry', 'open-runtime-surface', 'copy-snapshot-command'])
</script>
