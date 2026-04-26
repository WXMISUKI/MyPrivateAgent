import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/',
    redirect: '/chat'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('../views/ChatView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/learnings',
    name: 'Learnings',
    component: () => import('../views/LearningsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/skills',
    name: 'Skills',
    component: () => import('../views/SkillsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/SettingsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/search',
    name: 'Search',
    component: () => import('../views/SearchView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/feedback-analytics',
    name: 'FeedbackAnalytics',
    component: () => import('../views/FeedbackAnalyticsView.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

let authCheckPromise = null

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  if (!authStore.isInitialized) {
    if (!authCheckPromise) {
      authCheckPromise = authStore.checkAuth()
    }
    await authCheckPromise
    authCheckPromise = null
  }

  if (to.meta.requiresAuth) {
    if (!authStore.isAuthenticated) {
      next('/login')
      return
    }
  }

  if (to.path === '/login') {
    if (authStore.isAuthenticated) {
      next('/chat')
      return
    }
  }

  next()
})

export default router
