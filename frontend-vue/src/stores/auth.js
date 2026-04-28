import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const API_BASE_URL = '/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || '')
  const isAuthenticated = ref(false)
  const isInitialized = ref(false)
  const authMode = ref('demo_guest')
  const runtimeProfile = ref(null)

  const isLoggedIn = computed(() => isAuthenticated.value && !!token.value)
  const isDemoGuestMode = computed(() => authMode.value === 'demo_guest')

  async function ensureRuntimeProfile() {
    if (runtimeProfile.value) {
      return runtimeProfile.value
    }
    try {
      const response = await axios.get(`${API_BASE_URL}/runtime-profile`)
      runtimeProfile.value = response.data
      authMode.value = response.data?.auth_mode || 'demo_guest'
    } catch (error) {
      console.error('[Auth] failed to load runtime profile:', error.response?.data || error.message)
      runtimeProfile.value = { auth_mode: 'demo_guest' }
      authMode.value = 'demo_guest'
    }
    return runtimeProfile.value
  }

  async function hydrateCurrentUser(activeToken) {
    const response = await axios.get(`${API_BASE_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${activeToken}` }
    })
    user.value = response.data
    isAuthenticated.value = true
    return true
  }

  async function loginGuest() {
    try {
      const guestResponse = await axios.post(`${API_BASE_URL}/auth/guest`)
      const receivedToken = guestResponse.data?.access_token
      if (!receivedToken) {
        return false
      }
      token.value = receivedToken
      localStorage.setItem('token', receivedToken)
      await hydrateCurrentUser(receivedToken)
      return true
    } catch (error) {
      console.error('[Auth] guest login failed:', error.response?.data || error.message)
      token.value = ''
      localStorage.removeItem('token')
      isAuthenticated.value = false
      user.value = null
      return false
    }
  }

  async function checkAuth() {
    await ensureRuntimeProfile()
    console.log('[Auth] checkAuth called, current token:', token.value ? token.value.substring(0, 20) + '...' : 'empty')
    if (!token.value) {
      if (isDemoGuestMode.value) {
        const guestOk = await loginGuest()
        isInitialized.value = true
        return guestOk
      }
      console.log('[Auth] No token, setting isAuthenticated to false')
      isAuthenticated.value = false
      isInitialized.value = true
      return false
    }

    try {
      console.log('[Auth] Fetching /auth/me with token:', token.value.substring(0, 20) + '...')
      await hydrateCurrentUser(token.value)
    } catch (error) {
      console.error('[Auth] checkAuth failed:', error.response?.status, error.response?.data)
      token.value = ''
      localStorage.removeItem('token')
      user.value = null
      if (isDemoGuestMode.value) {
        const guestOk = await loginGuest()
        isInitialized.value = true
        return guestOk
      }
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
      await hydrateCurrentUser(receivedToken)

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
    authMode,
    runtimeProfile,
    isLoggedIn,
    isDemoGuestMode,
    ensureRuntimeProfile,
    checkAuth,
    loginGuest,
    login,
    logout,
    getAuthHeaders,
    setToken,
    setUser
  }
})
