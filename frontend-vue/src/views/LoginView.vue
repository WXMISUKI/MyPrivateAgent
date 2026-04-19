<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1 class="app-title">MyPrivateAgent</h1>
        <p class="app-subtitle">智能助手</p>
      </div>

      <form @submit.prevent class="login-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input
            id="username"
            v-model="username"
            type="text"
            placeholder="请输入用户名"
            required
            autocomplete="username"
          />
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="请输入密码"
            required
            autocomplete="current-password"
          />
        </div>

        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <div v-if="successMessage" class="success-message">
          {{ successMessage }}
        </div>

        <button type="button" class="login-btn" :disabled="loading" @click="handleLogin">
          <span v-if="loading" class="loading-spinner"></span>
          <span v-else>{{ isRegistering ? '注 册' : '登 录' }}</span>
        </button>

        <div class="auth-switch">
          <button type="button" @click="toggleAuthMode" class="switch-btn">
            {{ isRegistering ? '已有账号？登录' : '没有账号？注册' }}
          </button>
        </div>

        <div class="divider">
          <span>或</span>
        </div>

        <button type="button" class="guest-btn" :disabled="loading" @click="handleGuestLogin">
          <span v-if="loading" class="loading-spinner"></span>
          <span v-else>游客登录</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const errorMessage = ref('')
const successMessage = ref('')
const loading = ref(false)
const isRegistering = ref(false)

const API_BASE_URL = '/api'

async function handleLogin() {
  console.log('[Login] handleLogin called, username:', username.value)
  errorMessage.value = ''
  successMessage.value = ''
  loading.value = true

  try {
    console.log('[Login] Calling authStore.login...')
    const success = await authStore.login(username.value, password.value)
    console.log('[Login] authStore.login returned:', success)
    if (success) {
      console.log('[Login] Success, navigating to /chat')
      router.push('/chat')
    } else {
      errorMessage.value = '用户名或密码错误'
    }
  } catch (error) {
    console.error('[Login] Error:', error)
    errorMessage.value = '登录失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  errorMessage.value = ''
  successMessage.value = ''
  loading.value = true

  try {
    await axios.post(`${API_BASE_URL}/auth/register`, {
      username: username.value,
      password: password.value
    })
    successMessage.value = '注册成功，请登录'
    isRegistering.value = false
  } catch (error) {
    if (error.response?.data?.detail) {
      errorMessage.value = error.response.data.detail
    } else {
      errorMessage.value = '注册失败，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}

function toggleAuthMode() {
  isRegistering.value = !isRegistering.value
  errorMessage.value = ''
  successMessage.value = ''
}

async function handleGuestLogin() {
  console.log('[Login] Guest login called')
  errorMessage.value = ''
  successMessage.value = ''
  loading.value = true

  try {
    const response = await axios.post(`${API_BASE_URL}/auth/guest`)
    console.log('[Login] Guest response:', response.data)

    const token = response.data.access_token
    localStorage.setItem('token', token)

    const userResponse = await axios.get(`${API_BASE_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    console.log('[Login] Guest user info:', userResponse.data)

    authStore.setToken(token)
    authStore.setUser(userResponse.data)

    console.log('[Login] Guest success, navigating to /chat')
    router.push('/chat')
  } catch (error) {
    console.error('[Login] Guest error:', error)
    errorMessage.value = '游客登录失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: var(--space-2xl);
  background: var(--bg-surface);
  border-radius: var(--radius-xl);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.login-header {
  text-align: center;
  margin-bottom: var(--space-xl);
}

.app-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: var(--space-sm);
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.app-subtitle {
  font-size: 1rem;
  color: var(--text-secondary);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-group input {
  padding: var(--space-md);
  font-size: 1rem;
  color: var(--text-primary);
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  transition: all 0.2s ease;
}

.form-group input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
}

.error-message {
  padding: var(--space-md);
  font-size: 0.875rem;
  color: var(--error);
  background: rgba(239, 68, 68, 0.1);
  border-radius: var(--radius-md);
  text-align: center;
}

.login-btn {
  padding: var(--space-md) var(--space-lg);
  font-size: 1rem;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px -10px rgba(99, 102, 241, 0.5);
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.success-message {
  padding: var(--space-md);
  font-size: 0.875rem;
  color: #22c55e;
  background: rgba(34, 197, 94, 0.1);
  border-radius: var(--radius-md);
  text-align: center;
}

.auth-switch {
  text-align: center;
  margin-top: var(--space-md);
}

.switch-btn {
  background: none;
  border: none;
  color: var(--primary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: color 0.2s;
}

.switch-btn:hover {
  color: var(--primary-hover);
  text-decoration: underline;
}

.divider {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border-color);
}

.guest-btn {
  padding: var(--space-md) var(--space-lg);
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
}

.guest-btn:hover:not(:disabled) {
  background: var(--bg-surface);
  border-color: var(--primary);
}

.guest-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
</style>
