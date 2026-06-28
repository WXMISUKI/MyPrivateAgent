<template>
  <div class="app-container" :data-theme="theme">
    <div v-if="isLoading" class="loading-screen">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <template v-else-if="isAuthenticated || isDemoGuestMode">
      <AppHeader
        :theme="theme"
        :username="username"
        @toggle-theme="toggleTheme"
        @toggle-sidebar="toggleSidebar"
        @logout="handleLogout"
      />

      <div class="app-body">
        <AppSidebar
          :conversations="conversations"
          :active-conversation-id="activeConversationId"
          :collapsed="sidebarCollapsed"
          @new-chat="createNewChat"
          @select-conversation="selectConversation"
          @delete-conversation="deleteConversation"
          @open-learnings="goToLearnings"
          @open-workflow-lab="goToWorkflowLab"
          @open-feedback-analytics="goToFeedbackAnalytics"
          @open-skills="goToSkills"
          @open-settings="goToSettings"
        />

        <main class="main-view" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
          <router-view
            :key="activeConversationId"
            @update-conversation="updateCurrentConversation"
          />
        </main>
      </div>
    </template>

    <template v-else>
      <router-view />
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from './components/AppHeader.vue'
import AppSidebar from './components/AppSidebar.vue'
import { useConversationStore } from './stores/conversation'
import { useAuthStore } from './stores/auth'
import { useSettingsStore } from './stores/settings'

const router = useRouter()
const conversationStore = useConversationStore()
const authStore = useAuthStore()
const settingsStore = useSettingsStore()

const theme = ref('dark')
const username = ref('用户')
const sidebarCollapsed = ref(false)
const isLoading = ref(true)

const isAuthenticated = computed(() => authStore.isAuthenticated)
const isDemoGuestMode = computed(() => authStore.authMode === 'demo_guest')
const activeConversationId = computed(() => conversationStore.activeId)
const conversations = computed(() => conversationStore.conversations)

onMounted(async () => {
  const savedTheme = localStorage.getItem('theme') || 'dark'
  theme.value = savedTheme
  document.documentElement.setAttribute('data-theme', savedTheme)

  if (authStore.isAuthenticated && authStore.user) {
    username.value = authStore.user.username || '用户'
  }

  conversationStore.loadConversations()
  console.log('[App] Conversations loaded, count:', conversationStore.conversations.length)

  isLoading.value = false
})

watch(() => authStore.isAuthenticated, (isAuth) => {
  if (!isAuth && !isDemoGuestMode.value) {
    router.push('/login')
  }
})

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  localStorage.setItem('theme', theme.value)
  document.documentElement.setAttribute('data-theme', theme.value)
  settingsStore.setTheme(theme.value)
}

function handleThemeChange(newTheme) {
  theme.value = newTheme
}

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

async function createNewChat() {
  await conversationStore.createConversation()
  router.push('/chat')
}

function selectConversation(id) {
  conversationStore.setActiveConversation(id)
  router.push('/chat')
}

async function deleteConversation(id) {
  await conversationStore.deleteConversation(id)
}

function updateCurrentConversation(data) {
  conversationStore.updateConversation(activeConversationId.value, data)
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

function goToLearnings() {
  router.push('/learnings')
}

function goToWorkflowLab() {
  router.push('/workflow-lab')
}

function goToSkills() {
  router.push('/skills')
}

function goToSettings() {
  router.push('/settings')
}

function goToFeedbackAnalytics() {
  router.push('/feedback-analytics')
}
</script>

<style scoped>
.app-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  overflow: hidden;
}

.loading-screen {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  color: var(--text-secondary);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-color);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.app-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.main-view {
  flex: 1;
  overflow: hidden;
  transition: margin-left 0.3s ease;
}

.main-view:not(.sidebar-collapsed) {
  margin-left: 0;
}

@media (max-width: 768px) {
  .main-view {
    margin-left: 0 !important;
  }
}
</style>
