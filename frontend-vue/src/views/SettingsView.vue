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

        <ProviderConfigPanel />

        <div class="tab-footer">
          <button @click="saveSettings" class="save-btn">保存设置</button>
        </div>
      </div>

      <!-- 高级 Tab -->
      <div v-if="activeTab === 'advanced'" class="tab-panel">
        <RuntimeSurfacePanel />
        <CapabilityGapSummaryPanel />
        <McpManagementPanel />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSettingsStore } from '../stores/settings'
import { useAuthStore } from '../stores/auth'
import McpManagementPanel from '../components/McpManagementPanel.vue'
import CapabilityGapSummaryPanel from '../components/CapabilityGapSummaryPanel.vue'
import RuntimeSurfacePanel from '../components/RuntimeSurfacePanel.vue'
import ProviderConfigPanel from '../components/ProviderConfigPanel.vue'
import { runtimeSurfaceApi } from '../api'

const emit = defineEmits(['close', 'theme-changed'])
const router = useRouter()
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

onMounted(async () => {
  currentTheme.value = settingsStore.theme || 'dark'
  defaultModel.value = settingsStore.defaultModel || 'doubao'
  temperature.value = settingsStore.temperature || 0.7
  maxContextLength.value = settingsStore.maxContextLength || 8192
  autoSave.value = settingsStore.autoSave ?? true
  username.value = authStore.user?.username || '用户'
  isDemoGuestMode.value = authStore.authMode === 'demo_guest'

  try {
    const response = await runtimeSurfaceApi.getProfile()
    availableModels.value = Array.isArray(response.data?.models) ? response.data.models : []
    if (!availableModels.value.find(item => item.name === defaultModel.value)) {
      defaultModel.value = response.data?.default_model || availableModels.value.find(item => item.is_default)?.name || availableModels.value[0]?.name || 'doubao'
    }
  } catch (error) {
    console.error('Failed to load runtime models in settings:', error)
    availableModels.value = [{ name: 'doubao', display_name: '豆包 (火山引擎)' }]
  }
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
  settingsStore.setDefaultModel(defaultModel.value)
  settingsStore.setTemperature(parseFloat(temperature.value))
  settingsStore.setMaxContextLength(parseInt(maxContextLength.value))
  settingsStore.setAutoSave(autoSave.value)
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
</style>
