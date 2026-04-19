<template>
  <div class="settings-container">
    <div class="settings-header">
      <h1>⚙️ 设置</h1>
      <p class="subtitle">配置您的个人偏好</p>
    </div>

    <div class="settings-sections">
      <section class="settings-section">
        <h2>外观</h2>
        <div class="setting-item">
          <div class="setting-info">
            <label>主题</label>
            <span class="setting-desc">选择浅色或深色主题</span>
          </div>
          <div class="theme-switcher">
            <button
              :class="{ active: currentTheme === 'light' }"
              @click="setTheme('light')"
            >
              ☀️ 浅色
            </button>
            <button
              :class="{ active: currentTheme === 'dark' }"
              @click="setTheme('dark')"
            >
              🌙 深色
            </button>
          </div>
        </div>
      </section>

      <section class="settings-section">
        <h2>模型设置</h2>
        <div class="setting-item">
          <div class="setting-info">
            <label>默认模型</label>
            <span class="setting-desc">选择默认使用的 AI 模型</span>
          </div>
          <select v-model="defaultModel" class="setting-select">
            <option value="gpt-4">GPT-4</option>
            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            <option value="claude-3">Claude 3</option>
            <option value="deepseek">DeepSeek</option>
          </select>
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <label>温度参数</label>
            <span class="setting-desc">控制输出的随机性 (0-1)</span>
          </div>
          <input
            type="range"
            v-model="temperature"
            min="0"
            max="1"
            step="0.1"
            class="setting-range"
          />
          <span class="range-value">{{ temperature }}</span>
        </div>
      </section>

      <section class="settings-section">
        <h2>对话设置</h2>
        <div class="setting-item">
          <div class="setting-info">
            <label>最大上下文长度</label>
            <span class="setting-desc">控制单次对话的最大 token 数</span>
          </div>
          <select v-model="maxContextLength" class="setting-select">
            <option value="4096">4096 tokens</option>
            <option value="8192">8192 tokens</option>
            <option value="16384">16384 tokens</option>
            <option value="32768">32768 tokens</option>
          </select>
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <label>自动保存对话</label>
            <span class="setting-desc">自动保存对话历史</span>
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
            <label>用户名</label>
            <span class="setting-desc">{{ username }}</span>
          </div>
        </div>

        <div class="setting-item">
          <button @click="handleLogout" class="logout-btn">
            退出登录
          </button>
        </div>
      </section>
    </div>

    <div class="settings-footer">
      <button @click="saveSettings" class="save-btn">
        保存设置
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSettingsStore } from '../stores/settings'
import { useAuthStore } from '../stores/auth'

const emit = defineEmits(['close', 'theme-changed'])
const router = useRouter()
const settingsStore = useSettingsStore()
const authStore = useAuthStore()

const currentTheme = ref('dark')
const defaultModel = ref('gpt-4')
const temperature = ref(0.7)
const maxContextLength = ref(8192)
const autoSave = ref(true)
const username = ref('')

onMounted(() => {
  currentTheme.value = settingsStore.theme || 'dark'
  defaultModel.value = settingsStore.defaultModel || 'gpt-4'
  temperature.value = settingsStore.temperature || 0.7
  maxContextLength.value = settingsStore.maxContextLength || 8192
  autoSave.value = settingsStore.autoSave ?? true
  username.value = authStore.user?.username || '用户'
})

function setTheme(theme) {
  currentTheme.value = theme
  settingsStore.setTheme(theme)
  emit('theme-changed', theme)
}

function saveSettings() {
  settingsStore.setDefaultModel(defaultModel.value)
  settingsStore.setTemperature(parseFloat(temperature.value))
  settingsStore.setMaxContextLength(parseInt(maxContextLength.value))
  settingsStore.setAutoSave(autoSave.value)
  emit('close')
}

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.settings-container {
  width: 100%;
  height: 100%;
  padding: var(--space-xl);
  overflow-y: auto;
  background: var(--bg-primary);
}

.settings-header {
  margin-bottom: var(--space-xl);
}

.settings-header h1 {
  font-size: 1.75rem;
  color: var(--text-primary);
  margin-bottom: var(--space-sm);
}

.subtitle {
  color: var(--text-secondary);
}

.settings-sections {
  display: flex;
  flex-direction: column;
  gap: var(--space-xl);
  max-width: 700px;
}

.settings-section h2 {
  font-size: 1rem;
  color: var(--text-secondary);
  margin-bottom: var(--space-md);
  padding-bottom: var(--space-sm);
  border-bottom: 1px solid var(--border-color);
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) 0;
  border-bottom: 1px solid var(--border-color);
}

.setting-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.setting-info label {
  font-weight: 500;
  color: var(--text-primary);
}

.setting-desc {
  font-size: 0.875rem;
  color: var(--text-tertiary);
}

.theme-switcher {
  display: flex;
  gap: var(--space-sm);
  background: var(--bg-surface);
  padding: var(--space-xs);
  border-radius: var(--radius-md);
}

.theme-switcher button {
  padding: var(--space-sm) var(--space-md);
  font-size: 0.875rem;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
}

.theme-switcher button.active {
  color: var(--text-primary);
  background: var(--bg-elevated);
}

.setting-select {
  padding: var(--space-sm) var(--space-md);
  font-size: 0.875rem;
  color: var(--text-primary);
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  min-width: 150px;
}

.setting-range {
  width: 150px;
  accent-color: var(--primary);
}

.range-value {
  min-width: 40px;
  text-align: right;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.toggle-switch {
  position: relative;
  width: 48px;
  height: 24px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg-elevated);
  border-radius: var(--radius-full);
  transition: 0.3s;
}

.toggle-slider::before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
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
  transform: translateX(24px);
}

.logout-btn {
  padding: var(--space-sm) var(--space-lg);
  font-size: 0.875rem;
  color: var(--error);
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid var(--error);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.2);
}

.settings-footer {
  margin-top: var(--space-xl);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--border-color);
}

.save-btn {
  padding: var(--space-md) var(--space-xl);
  font-size: 1rem;
  font-weight: 600;
  color: white;
  background: var(--primary);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}

.save-btn:hover {
  background: var(--primary-hover);
}
</style>
