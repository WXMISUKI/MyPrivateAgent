import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const API_BASE_URL = '/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || '')
  const isAuthenticated = ref(false)
  const isInitialized = ref(false)

  const isLoggedIn = computed(() => isAuthenticated.value && !!token.value)

  async function checkAuth() {
    console.log('[Auth] checkAuth called, current token:', token.value ? token.value.substring(0, 20) + '...' : 'empty')
    if (!token.value) {
      console.log('[Auth] No token, setting isAuthenticated to false')
      isAuthenticated.value = false
      isInitialized.value = true
      return false
    }

    try {
      console.log('[Auth] Fetching /auth/me with token:', token.value.substring(0, 20) + '...')
      const response = await axios.get(`${API_BASE_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token.value}` }
      })
      console.log('[Auth] /auth/me response:', response.data)
      user.value = response.data
      isAuthenticated.value = true
    } catch (error) {
      console.error('[Auth] checkAuth failed:', error.response?.status, error.response?.data)
      token.value = ''
      localStorage.removeItem('token')
      isAuthenticated.value = false
    }

    isInitialized.value = true
    return isAuthenticated.value
  }

  async function login(username, password) {
    try {
      const loginResponse = await axios.post(`${API_BASE_URL}/auth/login`, {
        username,
        password
      }, {
        headers: { 'Content-Type': 'application/json' }
      })

      console.log('[Auth] Login response:', loginResponse.data)

      const receivedToken = loginResponse.data.access_token
      if (!receivedToken) {
        console.error('[Auth] No access_token in response')
        return false
      }

      token.value = receivedToken
      localStorage.setItem('token', receivedToken)
      isAuthenticated.value = true

      console.log('[Auth] Token saved, fetching user info...')

      const userResponse = await axios.get(`${API_BASE_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${receivedToken}` }
      })
      user.value = userResponse.data

      console.log('[Auth] Login successful, user:', user.value)
      return true
    } catch (error) {
      console.error('Login failed:', error.response?.data || error.message)
      return false
    }
  }

  async function logout() {
    try {
      await axios.post(`${API_BASE_URL}/auth/logout`, {}, {
        headers: { Authorization: `Bearer ${token.value}` }
      })
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      token.value = ''
      user.value = null
      isAuthenticated.value = false
      localStorage.removeItem('token')
    }
  }

  function getAuthHeaders() {
    const headers = {
      Authorization: `Bearer ${token.value}`
    }
    console.log('[Auth] getAuthHeaders called, token:', token.value ? token.value.substring(0, 20) + '...' : 'empty')
    return headers
  }

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('token', newToken)
    isAuthenticated.value = true
  }

  function setUser(newUser) {
    user.value = newUser
  }

  return {
    user,
    token,
    isAuthenticated,
    isInitialized,
    isLoggedIn,
    checkAuth,
    login,
    logout,
    getAuthHeaders,
    setToken,
    setUser
  }
})
