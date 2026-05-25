<template>
  <div
    v-if="remediation"
    class="panel-card summary-action-card framework-adapter-remediation-card"
    :class="[`framework-adapter-${remediation.severity}`, { active: activeFilter === 'doctor' }]"
    @click="emit('focus', 'doctor')"
  >
    <div class="card-head">
      <h3>{{ formatFrameworkAdapterRemediationHeading(remediation) }}</h3>
      <span class="muted">{{ formatAuditTime(remediation.timestamp) }}</span>
    </div>
    <div class="doctor-outcome-row">
      <strong>{{ remediation.title }}</strong>
      <span>{{ remediation.content || '无附加信息' }}</span>
    </div>
    <span class="muted">{{ formatFrameworkAdapterRemediationIdentityLine(remediation) }}</span>
    <div v-if="remediation.statusTags.length" class="catalog-tags remediation-status-tags">
      <span
        v-for="tag in remediation.statusTags"
        :key="`framework-remediation-status-${tag}`"
        class="capability-pill"
      >
        状态: {{ tag }}
      </span>
    </div>
    <div v-if="remediation.remediationActions.length" class="catalog-tags remediation-action-tags">
      <span
        v-for="action in remediation.remediationActions"
        :key="`${action.adapter_id || 'framework'}-${action.type || 'remediation'}-${action.message || 'item'}`"
        class="capability-pill"
      >
        {{ formatFrameworkAdapterRemediationAction(action) }}
      </span>
    </div>
    <div class="overview-card-actions remediation-card-actions">
      <button
        type="button"
        class="overview-risk-btn"
        @click.stop="emit('open-runtime-surface')"
      >
        打开运行时面板
      </button>
      <button
        v-if="remediation.commandText"
        type="button"
        class="overview-risk-btn"
        @click.stop="emit('copy-command', remediation.commandText)"
      >
        {{ copiedCommandTarget === 'framework-remediation' ? '已复制命令' : '复制修复命令' }}
      </button>
    </div>
  </div>
</template>

<script setup>
defineOptions({
  name: 'GovernanceTimelineFrameworkAdapterRemediationCard',
})

defineProps({
  remediation: {
    type: Object,
    default: null,
  },
  activeFilter: {
    type: String,
    default: '',
  },
  copiedCommandTarget: {
    type: String,
    default: '',
  },
  formatAuditTime: {
    type: Function,
    required: true,
  },
  formatFrameworkAdapterRemediationHeading: {
    type: Function,
    required: true,
  },
  formatFrameworkAdapterRemediationIdentityLine: {
    type: Function,
    required: true,
  },
  formatFrameworkAdapterRemediationAction: {
    type: Function,
    required: true,
  },
})

const emit = defineEmits(['focus', 'open-runtime-surface', 'copy-command'])
</script>
