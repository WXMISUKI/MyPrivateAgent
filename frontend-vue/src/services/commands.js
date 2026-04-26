export const commands = [
  {
    id: 'new',
    name: 'new',
    description: '开始一个新对话',
    icon: '➕',
    action: 'new_conversation'
  },
  {
    id: 'clear',
    name: 'clear',
    description: '清空当前对话',
    icon: '🗑️',
    action: 'clear_conversation'
  },
  {
    id: 'export',
    name: 'export',
    description: '导出当前对话',
    icon: '📤',
    action: 'export_conversation'
  },
  {
    id: 'skills',
    name: 'skills',
    description: '打开 Skills 管理页面',
    icon: '🧠',
    action: 'open_skills'
  },
  {
    id: 'learnings',
    name: 'learnings',
    description: '打开学习记录页面',
    icon: '📚',
    action: 'open_learnings'
  },
  {
    id: 'feedback',
    name: 'feedback',
    description: '打开反馈分析页面',
    icon: '📊',
    action: 'open_feedback_analytics'
  },
  {
    id: 'settings',
    name: 'settings',
    description: '打开设置页面',
    icon: '⚙️',
    action: 'open_settings'
  },
  {
    id: 'search',
    name: 'search',
    description: '搜索会话历史',
    icon: '🔍',
    action: 'open_search'
  },
  {
    id: 'help',
    name: 'help',
    description: '显示帮助信息',
    icon: '❓',
    action: 'show_help'
  }
]

export function parseCommand(input) {
  const trimmed = input.trim()
  if (!trimmed.startsWith('/')) {
    return null
  }

  const parts = trimmed.slice(1).split(/\s+/)
  const commandId = parts[0].toLowerCase()
  const params = parts.slice(1)

  const command = commands.find(c => c.name === commandId)
  if (!command) {
    return { error: 'unknown_command', commandId }
  }

  return {
    command,
    params
  }
}

export function filterCommands(query) {
  if (!query) return commands
  const lower = query.toLowerCase()
  return commands.filter(cmd =>
    cmd.name.toLowerCase().includes(lower) ||
    cmd.description.toLowerCase().includes(lower)
  )
}

export function getCommandById(id) {
  return commands.find(c => c.id === id)
}
