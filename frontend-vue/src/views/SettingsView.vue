<template>
  <div class="settings-container">
    <div class="settings-header">
      <div class="header-row">
        <button @click="goBack" class="back-btn">
          <span>←</span> 返回
        </button>
        <h1>设置</h1>
      </div>
    </div>

    <div class="settings-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="tab-btn"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="settings-content">
      <!-- 通用 Tab -->
      <div v-if="activeTab === 'general'" class="tab-panel">
        <section class="settings-section">
          <h2>外观</h2>
          <div class="setting-item">
            <div class="setting-info">
              <label>主题</label>
              <span class="setting-desc">选择浅色或深色主题</span>
            </div>
            <div class="theme-switcher">
              <button :class="{ active: currentTheme === 'light' }" @click="setTheme('light')">浅色</button>
              <button :class="{ active: currentTheme === 'dark' }" @click="setTheme('dark')">深色</button>
            </div>
          </div>
        </section>

        <section class="settings-section">
          <h2>对话</h2>
          <div class="setting-item">
            <div class="setting-info">
              <label>温度参数</label>
              <span class="setting-desc">控制输出的随机性，值越高越有创意</span>
            </div>
            <div class="range-control">
              <input type="range" v-model="temperature" min="0" max="1" step="0.1" class="setting-range" />
              <span class="range-value">{{ temperature }}</span>
            </div>
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <label>最大上下文长度</label>
              <span class="setting-desc">单次对话的最大 token 数</span>
            </div>
            <select v-model="maxContextLength" class="setting-select">
              <option value="4096">4,096</option>
              <option value="8192">8,192</option>
              <option value="16384">16,384</option>
              <option value="32768">32,768</option>
            </select>
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <label>自动保存对话</label>
              <span class="setting-desc">自动保存对话历史到本地</span>
            </div>
            <label class="toggle-switch">
              <input type="checkbox" v-model="autoSave" />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </section>

        <section class="settings-section">
          <h2>账户</h2>
          <div class="setting-item">
            <div class="setting-info">
              <label>{{ isDemoGuestMode ? '当前身份' : '用户名' }}</label>
              <span class="setting-desc">{{ username }}</span>
            </div>
            <div class="mode-badge" :class="{ demo: isDemoGuestMode, business: !isDemoGuestMode }">
              {{ isDemoGuestMode ? 'Demo' : 'Business' }}
            </div>
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <label>{{ isDemoGuestMode ? '重置会话' : '退出登录' }}</label>
              <span class="setting-desc">{{ isDemoGuestMode ? '清除当前 Demo 会话数据' : '退出当前账户' }}</span>
            </div>
            <button @click="handleLogout" class="logout-btn">
              {{ isDemoGuestMode ? '重置' : '退出' }}
            </button>
          </div>
        </section>

        <div class="tab-footer">
          <button @click="saveSettings" class="save-btn">保存设置</button>
        </div>
      </div>

      <!-- 模型与 Provider Tab -->
      <div v-if="activeTab === 'model'" class="tab-panel">
        <section class="settings-section">
          <h2>默认模型</h2>
          <div class="setting-item">
            <div class="setting-info">
              <label>对话模型</label>
              <span class="setting-desc">新对话默认使用的模型，可在聊天页随时切换</span>
            </div>
            <select v-model="defaultModel" class="setting-select">
              <option v-for="model in availableModels" :key="model.name" :value="model.name">
                {{ model.display_name }}
              </option>
            </select>
          </div>
        </section>

        <section class="settings-section">
          <h2>Provider Failover 看板</h2>
          <div class="setting-item">
            <div class="setting-info">
              <label>统计窗口</label>
              <span class="setting-desc">观察不同时间窗口下的 provider 自动切换情况</span>
            </div>
            <select v-model="failoverWindowDays" class="setting-select" @change="loadFailoverAnalytics">
              <option :value="7">近 7 天</option>
              <option :value="14">近 14 天</option>
              <option :value="30">近 30 天</option>
            </select>
          </div>
          <div class="failover-board" v-if="failoverAnalytics">
            <div class="failover-metric">
              <span class="metric-label">切换率</span>
              <span class="metric-value" :class="`risk-${failoverRiskLevel}`">{{ formatPercent(failoverAnalytics.switch_rate) }}</span>
            </div>
            <div class="failover-metric">
              <span class="metric-label">切换子任务</span>
              <span class="metric-value">{{ failoverAnalytics.switched_children }}/{{ failoverAnalytics.total_children }}</span>
            </div>
            <div class="failover-metric">
              <span class="metric-label">总切换次数</span>
              <span class="metric-value">{{ failoverAnalytics.total_switches }}</span>
            </div>
            <div class="failover-metric">
              <span class="metric-label">风险级别</span>
              <span class="metric-value" :class="`risk-${failoverRiskLevel}`">{{ failoverRiskText }}</span>
            </div>
          </div>
          <div class="setting-item threshold-item">
            <div class="setting-info">
              <label>风险阈值配置</label>
              <span class="setting-desc">切换率超过中风险阈值标黄，超过高风险阈值标红</span>
            </div>
            <div class="threshold-controls">
              <label class="threshold-label">
                中风险
                <input v-model.number="mediumRiskThresholdPercent" type="number" min="1" max="99" class="threshold-input" />
                <span>%</span>
              </label>
              <label class="threshold-label">
                高风险
                <input v-model.number="highRiskThresholdPercent" type="number" min="1" max="99" class="threshold-input" />
                <span>%</span>
              </label>
            </div>
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <label>静默运行告警</label>
              <span class="setting-desc">开启后聊天页不显示 failover 风险横幅，仅在设置页查看</span>
            </div>
            <label class="toggle-switch">
              <input type="checkbox" v-model="muteHealthAlerts" />
              <span class="toggle-slider"></span>
            </label>
          </div>
          <div v-if="failoverAnalytics" class="failover-alert" :class="`risk-${failoverRiskLevel}`">
            {{ failoverAlertText }}
          </div>
          <div v-if="healthFailoverLevel" class="failover-health" :class="`risk-${healthFailoverLevel}`">
            {{ healthFailoverText }}
          </div>
          <div v-if="healthUpdatedAtText" class="health-updated-at">
            健康数据更新时间：{{ healthUpdatedAtText }}
          </div>
          <div class="failover-list" v-if="failoverAnalytics?.top_provider_failover_pairs?.length">
            <div class="list-title">Top Failover 路径</div>
            <div v-for="item in failoverAnalytics.top_provider_failover_pairs" :key="item.name" class="list-row">
              <span>{{ item.name }}</span>
              <span>{{ item.count }}</span>
            </div>
          </div>
        </section>

        <ProviderConfigPanel />
        <CapabilityProviderDiagnosticsPanel />

        <div class="tab-footer">
          <button @click="saveSettings" class="save-btn">保存设置</button>
        </div>
      </div>

      <!-- 高级 Tab -->
      <div v-if="activeTab === 'advanced'" class="tab-panel">
        <DoctorPanel />
        <GovernanceTimelinePanel />
        <RuntimeSurfacePanel />
        <CapabilityGapSummaryPanel />
        <McpManagementPanel />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useSettingsStore } from '../stores/settings'
import { useAuthStore } from '../stores/auth'
import DoctorPanel from '../components/DoctorPanel.vue'
import GovernanceTimelinePanel from '../components/GovernanceTimelinePanel.vue'
import McpManagementPanel from '../components/McpManagementPanel.vue'
import CapabilityGapSummaryPanel from '../components/CapabilityGapSummaryPanel.vue'
import RuntimeSurfacePanel from '../components/RuntimeSurfacePanel.vue'
import ProviderConfigPanel from '../components/ProviderConfigPanel.vue'
import CapabilityProviderDiagnosticsPanel from '../components/CapabilityProviderDiagnosticsPanel.vue'
import { healthApi, providerApi, runtimeSurfaceApi } from '../api'

const emit = defineEmits(['close', 'theme-changed'])
const router = useRouter()
const route = useRoute()
const settingsStore = useSettingsStore()
const authStore = useAuthStore()

const activeTab = ref('general')
const tabs = [
  { id: 'general', label: '通用' },
  { id: 'model', label: '模型与 Provider' },
  { id: 'advanced', label: '高级' },
]

const currentTheme = ref('dark')
const defaultModel = ref('doubao')
const temperature = ref(0.7)
const maxContextLength = ref(8192)
const autoSave = ref(true)
const username = ref('')
const availableModels = ref([])
const isDemoGuestMode = ref(false)
const failoverWindowDays = ref(7)
const failoverAnalytics = ref(null)
const mediumRiskThresholdPercent = ref(20)
const highRiskThresholdPercent = ref(40)
const healthFailover = ref(null)
const muteHealthAlerts = ref(false)
const healthUpdatedAt = ref(null)
let healthPollTimer = null

onMounted(async () => {
  const tabQuery = String(route.query.tab || '').trim().toLowerCase()
  if (tabs.some(item => item.id === tabQuery)) {
    activeTab.value = tabQuery
  }
  currentTheme.value = settingsStore.theme || 'dark'
  defaultModel.value = settingsStore.defaultModel || 'doubao'
  temperature.value = settingsStore.temperature || 0.7
  maxContextLength.value = settingsStore.maxContextLength || 8192
  autoSave.value = settingsStore.autoSave ?? true
  username.value = authStore.user?.username || '用户'
  isDemoGuestMode.value = authStore.authMode === 'demo_guest'
  mediumRiskThresholdPercent.value = Math.round(Number(settingsStore.failoverMediumThreshold || 0.2) * 100)
  highRiskThresholdPercent.value = Math.round(Number(settingsStore.failoverHighThreshold || 0.4) * 100)
  muteHealthAlerts.value = Boolean(settingsStore.muteHealthAlerts)

  try {
    const response = await runtimeSurfaceApi.getProfile()
    availableModels.value = Array.isArray(response.data?.models) ? response.data.models : []
    const profileThresholds = response.data?.failover_thresholds || response.data?.config_layers?.effective?.failover_thresholds
    if (profileThresholds) {
      const medium = Number(profileThresholds.medium)
      const high = Number(profileThresholds.high)
      if (Number.isFinite(medium) && medium > 0 && medium < 1) {
        mediumRiskThresholdPercent.value = Math.round(medium * 100)
      }
      if (Number.isFinite(high) && high > 0 && high < 1) {
        highRiskThresholdPercent.value = Math.round(high * 100)
      }
    }
    if (!availableModels.value.find(item => item.name === defaultModel.value)) {
      defaultModel.value = response.data?.default_model || availableModels.value.find(item => item.is_default)?.name || availableModels.value[0]?.name || 'doubao'
    }
  } catch (error) {
    console.error('Failed to load runtime models in settings:', error)
    availableModels.value = [{ name: 'doubao', display_name: '豆包 (火山引擎)' }]
  }
  await loadFailoverAnalytics()
  await loadHealthFailover()
})

function setTheme(theme) {
  currentTheme.value = theme
  settingsStore.setTheme(theme)
  emit('theme-changed', theme)
}

function goBack() {
  router.push('/chat')
}

function saveSettings() {
  let medium = Number(mediumRiskThresholdPercent.value || 20)
  let high = Number(highRiskThresholdPercent.value || 40)
  medium = Math.min(Math.max(medium, 1), 99)
  high = Math.min(Math.max(high, 1), 99)
  if (high <= medium) {
    high = Math.min(99, medium + 1)
  }
  mediumRiskThresholdPercent.value = medium
  highRiskThresholdPercent.value = high

  settingsStore.setDefaultModel(defaultModel.value)
  settingsStore.setTemperature(parseFloat(temperature.value))
  settingsStore.setMaxContextLength(parseInt(maxContextLength.value))
  settingsStore.setAutoSave(autoSave.value)
  settingsStore.setFailoverMediumThreshold(medium / 100)
  settingsStore.setFailoverHighThreshold(high / 100)
  settingsStore.setMuteHealthAlerts(Boolean(muteHealthAlerts.value))
  runtimeSurfaceApi.updateProfile({
    default_model: defaultModel.value,
    failover_thresholds: {
      medium: medium / 100,
      high: high / 100
    }
  }).catch((error) => {
    console.error('Failed to persist runtime profile settings:', error)
  })
  router.push('/chat')
}

async function handleLogout() {
  await authStore.logout()
  if (isDemoGuestMode.value) {
    await authStore.loginGuest()
    router.push('/chat')
    return
  }
  router.push('/login')
}

async function loadFailoverAnalytics() {
  try {
    const response = await providerApi.getFailoverAnalytics({
      window_days: failoverWindowDays.value,
      limit: 1000
    })
    failoverAnalytics.value = response.data
  } catch (error) {
    console.error('Failed to load failover analytics:', error)
    failoverAnalytics.value = null
  }
}

async function loadHealthFailover() {
  try {
    const response = await healthApi.getHealth()
    healthFailover.value = response.data?.failover || null
    healthUpdatedAt.value = Date.now()
  } catch (error) {
    console.error('Failed to load health failover status:', error)
    healthFailover.value = null
  }
}

function formatPercent(value) {
  return `${((Number(value || 0)) * 100).toFixed(1)}%`
}

const failoverRiskLevel = computed(() => {
  const rate = Number(failoverAnalytics.value?.switch_rate || 0)
  const medium = Math.min(Math.max(Number(mediumRiskThresholdPercent.value || 20), 1), 99) / 100
  const high = Math.min(Math.max(Number(highRiskThresholdPercent.value || 40), 1), 99) / 100
  if (rate > Math.max(high, medium + 0.01)) return 'high'
  if (rate > medium) return 'medium'
  return 'low'
})

const failoverRiskText = computed(() => {
  if (failoverRiskLevel.value === 'high') return '高风险'
  if (failoverRiskLevel.value === 'medium') return '中风险'
  return '低风险'
})

const failoverAlertText = computed(() => {
  const rate = Number(failoverAnalytics.value?.switch_rate || 0)
  const rateText = formatPercent(rate)
  if (failoverRiskLevel.value === 'high') {
    return `当前切换率 ${rateText}，已超过高风险阈值。建议优先排查首选 Provider 稳定性与超时配置。`
  }
  if (failoverRiskLevel.value === 'medium') {
    return `当前切换率 ${rateText}，处于中风险区间。建议检查高频 failover 路径并优化模型路由。`
  }
  return `当前切换率 ${rateText}，处于可接受范围。`
})

const healthFailoverLevel = computed(() => {
  const level = String(healthFailover.value?.alert_level || '').trim().toLowerCase()
  if (level === 'high' || level === 'medium' || level === 'low') return level
  return ''
})

const healthFailoverText = computed(() => {
  if (!healthFailoverLevel.value) return ''
  if (healthFailoverLevel.value === 'high') return '运行健康告警：Failover 高风险'
  if (healthFailoverLevel.value === 'medium') return '运行健康告警：Failover 中风险'
  return '运行健康状态：Failover 低风险'
})

const healthUpdatedAtText = computed(() => {
  if (!healthUpdatedAt.value) return ''
  const date = new Date(healthUpdatedAt.value)
  const hh = String(date.getHours()).padStart(2, '0')
  const mm = String(date.getMinutes()).padStart(2, '0')
  const ss = String(date.getSeconds()).padStart(2, '0')
  return `${hh}:${mm}:${ss}`
})

onMounted(() => {
  healthPollTimer = setInterval(() => {
    loadHealthFailover()
  }, 60000)
})

onUnmounted(() => {
  if (healthPollTimer) {
    clearInterval(healthPollTimer)
    healthPollTimer = null
  }
})
</script>

<style scoped>
.settings-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  overflow: hidden;
}

.settings-header {
  padding: var(--space-lg) var(--space-xl) 0;
}

.header-row {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: 6px 12px;
  font-size: 0.875rem;
  color: var(--text-secondary);
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn:hover {
  color: var(--text-primary);
  border-color: var(--primary);
}

.settings-header h1 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
}

.settings-tabs {
  display: flex;
  gap: 2px;
  padding: var(--space-md) var(--space-xl) 0;
  border-bottom: 1px solid var(--border-color);
}

.tab-btn {
  padding: 10px 20px;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: -1px;
}

.tab-btn:hover {
  color: var(--text-primary);
}

.tab-btn.active {
  color: var(--primary);
  border-bottom-color: var(--primary);
}

.settings-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-lg) var(--space-xl);
}

.tab-panel {
  max-width: 680px;
}

.settings-section {
  margin-bottom: var(--space-xl);
}

.settings-section h2 {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-sm);
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 0;
  border-bottom: 1px solid var(--border-color);
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.setting-info label {
  font-weight: 500;
  font-size: 0.9rem;
  color: var(--text-primary);
}

.setting-desc {
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

.theme-switcher {
  display: flex;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: 3px;
}

.theme-switcher button {
  padding: 6px 16px;
  font-size: 0.8rem;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
}

.theme-switcher button.active {
  color: var(--text-primary);
  background: var(--bg-primary);
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.setting-select {
  padding: 6px 12px;
  font-size: 0.875rem;
  color: var(--text-primary);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  min-width: 140px;
  cursor: pointer;
}

.range-control {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.setting-range {
  width: 120px;
  accent-color: var(--primary);
}

.range-value {
  min-width: 32px;
  text-align: right;
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-family: monospace;
}

.toggle-switch {
  position: relative;
  width: 44px;
  height: 22px;
  display: inline-block;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0; left: 0; right: 0; bottom: 0;
  background: var(--bg-elevated, #555);
  border-radius: 22px;
  transition: 0.3s;
}

.toggle-slider::before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 3px;
  bottom: 3px;
  background: white;
  border-radius: 50%;
  transition: 0.3s;
}

.toggle-switch input:checked + .toggle-slider {
  background: var(--primary);
}

.toggle-switch input:checked + .toggle-slider::before {
  transform: translateX(22px);
}

.mode-badge {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.mode-badge.demo {
  background: rgba(34, 197, 94, 0.12);
  color: #22c55e;
}

.mode-badge.business {
  background: rgba(245, 158, 11, 0.12);
  color: #f59e0b;
}

.logout-btn {
  padding: 6px 16px;
  font-size: 0.8rem;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.15);
}

.tab-footer {
  padding-top: var(--space-lg);
  margin-top: var(--space-md);
  border-top: 1px solid var(--border-color);
}

.save-btn {
  padding: 10px 28px;
  font-size: 0.9rem;
  font-weight: 600;
  color: white;
  background: var(--primary);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}

.save-btn:hover {
  opacity: 0.9;
}

.failover-board {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 12px;
}

.failover-metric {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-label {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.metric-value {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
}

.metric-value.risk-low {
  color: #22c55e;
}

.metric-value.risk-medium {
  color: #f59e0b;
}

.metric-value.risk-high {
  color: #ef4444;
}

.failover-list {
  margin-top: 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  padding: 10px 12px;
}

.list-title {
  font-size: 0.8rem;
  color: var(--text-tertiary);
  margin-bottom: 8px;
}

.list-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.82rem;
  color: var(--text-secondary);
  padding: 3px 0;
}

.threshold-item {
  align-items: flex-start;
}

.threshold-controls {
  display: flex;
  gap: 12px;
}

.threshold-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.threshold-input {
  width: 64px;
  padding: 4px 8px;
  font-size: 0.85rem;
  color: var(--text-primary);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
}

.failover-alert {
  margin-top: 10px;
  border-radius: var(--radius-md);
  padding: 10px 12px;
  font-size: 0.82rem;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-secondary);
}

.failover-alert.risk-medium {
  border-color: rgba(245, 158, 11, 0.4);
  background: rgba(245, 158, 11, 0.08);
  color: #b45309;
}

.failover-alert.risk-high {
  border-color: rgba(239, 68, 68, 0.45);
  background: rgba(239, 68, 68, 0.08);
  color: #b91c1c;
}

.failover-health {
  margin-top: 10px;
  border-radius: var(--radius-md);
  padding: 10px 12px;
  font-size: 0.82rem;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-secondary);
}

.failover-health.risk-medium {
  border-color: rgba(245, 158, 11, 0.4);
  background: rgba(245, 158, 11, 0.08);
  color: #b45309;
}

.failover-health.risk-high {
  border-color: rgba(239, 68, 68, 0.45);
  background: rgba(239, 68, 68, 0.08);
  color: #b91c1c;
}

.health-updated-at {
  margin-top: 8px;
  font-size: 0.75rem;
  color: var(--text-tertiary);
}
</style>
