<template>
  <header class="app-header">
    <div class="header-left">
      <button class="menu-btn" @click="$emit('toggle-sidebar')">
        <span class="icon">☰</span>
      </button>
    </div>

    <div class="header-center">
      <div class="search-box" @click="navigateToSearch">
        <span class="search-icon">🔍</span>
        <input
          type="text"
          v-model="searchQuery"
          placeholder="搜索会话..."
          @keydown.enter="navigateToSearch"
        />
      </div>
    </div>

    <div class="header-right">
      <button class="header-btn" @click="$emit('toggle-theme')" :title="theme === 'dark' ? '切换到亮色' : '切换到暗色'">
        <span class="icon">{{ theme === 'dark' ? '☀️' : '🌙' }}</span>
      </button>
      <div class="user-menu" ref="userMenuRef">
        <button class="user-btn" @click="showUserMenu = !showUserMenu">
          <span class="avatar">👤</span>
          <span class="username">{{ username }}</span>
        </button>
        <div v-if="showUserMenu" class="user-dropdown">
          <button @click="$emit('logout')">退出登录</button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

defineProps({
  theme: {
    type: String,
    default: 'dark'
  },
  username: {
    type: String,
    default: '用户'
  }
})

defineEmits(['toggle-sidebar', 'toggle-theme', 'logout'])

const searchQuery = ref('')
const showUserMenu = ref(false)

function navigateToSearch() {
  router.push({ path: '/search', query: searchQuery.value ? { q: searchQuery.value } : {} })
}

const userMenuRef = ref(null)

function handleClickOutside(e) {
  if (userMenuRef.value && !userMenuRef.value.contains(e.target)) {
    showUserMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.app-header {
  height: var(--header-height);
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-primary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-md);
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.menu-btn,
.header-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}

.menu-btn:hover,
.header-btn:hover {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.menu-btn .icon,
.header-btn .icon {
  font-size: 18px;
}

.header-center {
  flex: 1;
  max-width: 400px;
  margin: 0 var(--space-lg);
}

.search-box {
  position: relative;
  width: 100%;
}

.search-icon {
  position: absolute;
  left: var(--space-md);
  top: 50%;
  transform: translateY(-50%);
  font-size: 14px;
  color: var(--text-tertiary);
}

.search-box input {
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  padding-left: 40px;
  background-color: var(--bg-tertiary);
  border: 1px solid transparent;
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  color: var(--text-primary);
  transition: all var(--transition-fast);
}

.search-box input:focus {
  border-color: var(--primary);
  background-color: var(--bg-surface);
}

.search-box input::placeholder {
  color: var(--text-tertiary);
}

.user-menu {
  position: relative;
}

.user-btn {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}

.user-btn:hover {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.avatar {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-full);
  font-size: 14px;
}

.username {
  font-size: var(--text-sm);
  font-weight: 500;
}

.user-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: var(--space-xs);
  background-color: var(--bg-surface);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  min-width: 120px;
  z-index: var(--z-dropdown);
  animation: fadeIn 0.15s ease;
}

.user-dropdown button {
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  text-align: left;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}

.user-dropdown button:hover {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}
</style>
