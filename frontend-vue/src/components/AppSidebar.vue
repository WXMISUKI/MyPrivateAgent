<template>
  <div class="app-layout">
    <aside class="sidebar" :class="{ collapsed: collapsed }">
      <div class="sidebar-header">
        <button class="new-chat-btn" @click="$emit('new-chat')">
          <span class="icon">+</span>
          <span class="text">新建对话</span>
        </button>
      </div>

      <div class="conversation-list">
        <div v-if="conversations.length === 0" class="empty-conversations">
          <p>暂无对话记录</p>
        </div>

        <div
          v-for="group in conversationGroups"
          :key="group.label"
          class="conversation-group"
        >
          <div class="group-label">{{ group.label }}</div>
          <div
            v-for="conv in group.conversations"
            :key="conv.id"
            class="conversation-item"
            :class="{ active: activeConversationId === conv.id }"
            @click="$emit('select-conversation', conv.id)"
            @mouseenter="hoveredConv = conv.id"
            @mouseleave="hoveredConv = null"
          >
            <div class="conv-content">
              <span class="conv-icon">💬</span>
              <span class="conv-title truncate">{{ conv.title }}</span>
            </div>
            <button
              v-if="hoveredConv === conv.id"
              class="conv-delete-btn"
              @click.stop="handleDelete(conv.id)"
              title="删除对话"
            >
              🗑️
            </button>
          </div>
        </div>
      </div>

      <div class="sidebar-footer">
        <button class="footer-btn" @click="$emit('open-learnings')">
          <span class="icon">🧠</span>
          <span class="text">学习记录</span>
        </button>
        <button class="footer-btn" @click="$emit('open-workflow-lab')">
          <span class="icon">🧪</span>
          <span class="text">Workflow Lab</span>
        </button>
        <button class="footer-btn" @click="$emit('open-feedback-analytics')">
          <span class="icon">📊</span>
          <span class="text">反馈分析</span>
        </button>
        <button class="footer-btn" @click="$emit('open-skills')">
          <span class="icon">🛠️</span>
          <span class="text">Skills</span>
        </button>
        <button class="footer-btn" @click="$emit('open-settings')">
          <span class="icon">⚙️</span>
          <span class="text">设置</span>
        </button>
      </div>
    </aside>

    <main class="main-content">
      <slot />
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  conversations: {
    type: Array,
    default: () => []
  },
  activeConversationId: {
    type: [Number, String],
    default: null
  },
  collapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'new-chat',
  'select-conversation',
  'open-learnings',
  'open-workflow-lab',
  'open-feedback-analytics',
  'open-skills',
  'open-settings',
  'delete-conversation'
])

const hoveredConv = ref(null)

const conversationGroups = computed(() => {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)
  const weekAgo = new Date(today - 7 * 86400000)

  const groups = {
    today: { label: '今天', conversations: [] },
    yesterday: { label: '昨天', conversations: [] },
    week: { label: '本周', conversations: [] },
    older: { label: '更早', conversations: [] }
  }

  props.conversations.forEach(conv => {
    const date = new Date(conv.updatedAt)
    if (date >= today) {
      groups.today.conversations.push(conv)
    } else if (date >= yesterday) {
      groups.yesterday.conversations.push(conv)
    } else if (date >= weekAgo) {
      groups.week.conversations.push(conv)
    } else {
      groups.older.conversations.push(conv)
    }
  })

  return Object.values(groups).filter(g => g.conversations.length > 0)
})

function formatTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${hours}:${minutes}`
}

function handleDelete(convId) {
  if (confirm('确定要删除这个对话吗？')) {
    emit('delete-conversation', convId)
  }
}
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.sidebar {
  width: var(--sidebar-width);
  background-color: var(--bg-secondary);
  border-right: 1px solid var(--border-primary);
  display: flex;
  flex-direction: column;
  transition: width var(--transition-normal);
}

.sidebar.collapsed {
  width: var(--sidebar-collapsed-width);
}

.sidebar.collapsed .text,
.sidebar.collapsed .conv-title,
.sidebar.collapsed .conv-time,
.sidebar.collapsed .group-label {
  display: none;
}

.sidebar-header {
  padding: var(--space-md);
  border-bottom: 1px solid var(--border-primary);
}

.new-chat-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background-color: var(--primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.new-chat-btn:hover {
  background-color: var(--primary-hover);
  transform: translateY(-1px);
}

.new-chat-btn:active {
  transform: translateY(0);
}

.new-chat-btn .icon {
  font-size: 18px;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-sm);
}

.empty-conversations {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100px;
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}

.conversation-group {
  margin-bottom: var(--space-md);
}

.group-label {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  padding: var(--space-xs) var(--space-sm);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.conversation-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  margin-bottom: 2px;
}

.conversation-item:hover {
  background-color: var(--bg-tertiary);
}

.conversation-item.active {
  background-color: var(--bg-tertiary);
  border-left: 3px solid var(--primary);
  padding-left: calc(var(--space-md) - 3px);
}

.conv-content {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex: 1;
  min-width: 0;
}

.conv-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.conv-title {
  font-size: var(--text-sm);
  color: var(--text-primary);
  flex: 1;
  min-width: 0;
}

.conv-time {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  flex-shrink: 0;
  margin-left: var(--space-sm);
}

.conv-delete-btn {
  padding: 4px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 12px;
  opacity: 0.6;
  transition: all var(--transition-fast);
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.conv-delete-btn:hover {
  opacity: 1;
  background-color: var(--error-bg);
  transform: scale(1.1);
}

.sidebar-footer {
  padding: var(--space-md);
  border-top: 1px solid var(--border-primary);
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.footer-btn {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  background: none;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
  font-size: var(--text-sm);
}

.footer-btn:hover {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.footer-btn .icon {
  font-size: 16px;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 完全收缩样式 - 只显示图标 */
.sidebar.collapsed {
  width: var(--sidebar-collapsed-width);
}

.sidebar.collapsed .sidebar-header {
  padding: var(--space-sm);
  display: flex;
  justify-content: center;
}

.sidebar.collapsed .new-chat-btn {
  width: 40px;
  height: 40px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.sidebar.collapsed .new-chat-btn .icon {
  font-size: 20px;
}

.sidebar.collapsed .new-chat-btn .text {
  display: none;
}

.sidebar.collapsed .conversation-list {
  display: none;
}

.sidebar.collapsed .sidebar-footer {
  padding: var(--space-sm);
  align-items: center;
}

.sidebar.collapsed .footer-btn {
  width: 40px;
  height: 40px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  margin: 0 auto;
}

.sidebar.collapsed .footer-btn .icon {
  font-size: 18px;
}

.sidebar.collapsed .footer-btn .text {
  display: none;
}
</style>
