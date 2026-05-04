export const localCommands = [
  {
    id: 'new',
    name: 'new',
    description: '开始一个新对话',
    icon: '➕',
    action: 'new_conversation',
    category: 'conversation'
  },
  {
    id: 'clear',
    name: 'clear',
    description: '清空当前对话',
    icon: '🗑️',
    action: 'clear_conversation',
    category: 'conversation'
  },
  {
    id: 'export',
    name: 'export',
    description: '导出当前对话',
    icon: '📤',
    action: 'export_conversation',
    category: 'conversation'
  },
  {
    id: 'skills',
    name: 'skills',
    description: '打开 Skills 管理页面',
    icon: '🧠',
    action: 'open_skills',
    category: 'governance'
  },
  {
    id: 'learnings',
    name: 'learnings',
    description: '打开学习记录页面',
    icon: '📚',
    action: 'open_learnings',
    category: 'governance'
  },
  {
    id: 'feedback',
    name: 'feedback',
    description: '打开反馈分析页面',
    icon: '📊',
    action: 'open_feedback_analytics',
    category: 'governance'
  },
  {
    id: 'settings',
    name: 'settings',
    description: '打开设置页面',
    icon: '⚙️',
    action: 'open_settings',
    category: 'governance'
  },
  {
    id: 'search',
    name: 'search',
    description: '搜索会话历史',
    icon: '🔍',
    action: 'open_search',
    category: 'conversation',
    hasParam: true,
    paramHint: '/search <query>'
  },
  {
    id: 'help',
    name: 'help',
    description: '显示帮助信息',
    icon: '❓',
    action: 'show_help',
    category: 'system'
  },
  {
    id: 'doctor',
    name: 'doctor',
    description: '运行框架健康检查或治理门禁',
    icon: '🩺',
    action: 'run_doctor',
    category: 'framework',
    hasParam: true,
    paramHint: '/doctor <startup|governance> [warning]'
  },
  {
    id: 'snapshot',
    name: 'snapshot',
    description: '按快照 ID 打开治理时间线定位视图',
    icon: '🧷',
    action: 'open_snapshot',
    category: 'framework',
    hasParam: true,
    paramHint: '/snapshot <snapshot_id>'
  },
  {
    id: 'plan',
    name: 'plan',
    description: '打开计划与调度面板',
    icon: '🗂️',
    action: 'open_planner',
    category: 'framework'
  },
  {
    id: 'gaps',
    name: 'gaps',
    description: '查看能力缺口治理面板',
    icon: '🧭',
    action: 'open_gaps',
    category: 'framework',
    hasParam: true,
    paramHint: '/gaps <all|warning|snapshot <id>>'
  },
  {
    id: 'permissions',
    name: 'permissions',
    description: '查看权限治理面板',
    icon: '🔐',
    action: 'open_permissions',
    category: 'framework',
    hasParam: true,
    paramHint: '/permissions <all|warning|snapshot <id>>'
  },
  {
    id: 'mcp',
    name: 'mcp',
    description: '查看 MCP 注册与连接状态',
    icon: '🔌',
    action: 'open_mcp',
    category: 'framework',
    hasParam: true,
    paramHint: '/mcp <all|warning|snapshot <id>>'
  },
  {
    id: 'memory',
    name: 'memory',
    description: '查看分层记忆与指令面',
    icon: '🧩',
    action: 'open_memory',
    category: 'framework'
  },
  {
    id: 'model',
    name: 'model',
    description: '切换当前模型或打开模型设置',
    icon: '🧠',
    action: 'open_model',
    category: 'framework',
    hasParam: true,
    paramHint: '/model <name>'
  }
]

export function parseCommand(input) {
  const trimmed = String(input || '').trim()
  if (!trimmed.startsWith('/')) {
    return null
  }

  const parts = trimmed.slice(1).split(/\s+/).filter(Boolean)
  const commandId = String(parts[0] || '').toLowerCase()
  const params = parts.slice(1)

  const command = localCommands.find(c => c.name === commandId)
  if (!command) {
    return { error: 'unknown_command', commandId }
  }

  return {
    command,
    params
  }
}

export function filterCommands(query) {
  if (!query) return localCommands
  const lower = query.toLowerCase()
  return localCommands.filter(cmd =>
    cmd.name.toLowerCase().includes(lower) ||
    cmd.description.toLowerCase().includes(lower)
  )
}

export function getCommandById(id) {
  return localCommands.find(c => c.id === id)
}
