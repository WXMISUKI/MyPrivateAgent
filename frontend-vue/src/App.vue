<template>
  <div class="app-container" :data-theme="theme">
    <div v-if="isLoading" class="loading-screen">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <template v-else-if="isAuthenticated">
      <AppHeader
        :theme="theme"
        :username="username"
        @toggle-theme="toggleTheme"
        @toggle-sidebar="toggleSidebar"
        @search="handleSearch"
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
          @open-learnings="showLearnings = true"
          @open-settings="showSettings = true"
        />

        <main class="main-view" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
          <router-view
            :key="activeConversationId"
            @update-conversation="updateCurrentConversation"
          />
        </main>
      </div>

      <LearningsModal
        v-if="showLearnings"
        @close="showLearnings = false"
      />

      <SettingsModal
        v-if="showSettings"
        @close="showSettings = false"
        @theme-changed="handleThemeChange"
      />
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
import LearningsModal from './views/LearningsView.vue'
import SettingsModal from './views/SettingsView.vue'
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
const showLearnings = ref(false)
const showSettings = ref(false)
const searchQuery = ref('')
const isLoading = ref(true)

const isAuthenticated = computed(() => authStore.isAuthenticated)
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
  if (!isAuth) {
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

function handleSearch(query) {
  searchQuery.value = query
  conversationStore.setSearchQuery(query)
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
  router.push('/login')
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
