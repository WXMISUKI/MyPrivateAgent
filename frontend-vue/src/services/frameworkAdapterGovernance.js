import { normalizePayload, normalizeText } from './governanceValueUtils'

export function formatFrameworkAdapterExternalErrorLabel(errorType) {
  const labelMap = {
    configuration_error: '配置错误',
    connectivity_error: '连通性错误',
    authentication_error: '鉴权错误',
    protocol_error: '协议错误',
    upstream_runtime_error: '上游运行时错误',
    request_failed: '请求失败',
  }
  const normalizedErrorType = normalizeText(errorType)
  return labelMap[normalizedErrorType] || normalizedErrorType
}

export function formatFrameworkAdapterExternalErrorTag(payload) {
  const data = normalizePayload(payload) || {}
  const errorType = normalizeText(data.error_type)
  if (!errorType) {
    return ''
  }
  const label = formatFrameworkAdapterExternalErrorLabel(errorType)
  return label === errorType ? label : `${label} (${errorType})`
}

export function formatFrameworkAdapterExternalErrorDetail(payload) {
  const data = normalizePayload(payload) || {}
  return normalizeText(data.detail)
}

export function formatFrameworkAdapterFailureCount(entry) {
  const counts = normalizePayload(entry?.payload?.external_pilot_failure_counts)
  const total = Number(counts?.total)
  if (!Number.isFinite(total) || total <= 0) {
    return ''
  }
  return String(total)
}

export function formatFrameworkAdapterFailureWindow(entry) {
  const counts = normalizePayload(entry?.payload?.external_pilot_failure_counts)
  const windowScope = normalizeText(counts?.window_scope)
  const labelMap = {
    recent_plan_items: '最近 PlanItem',
  }
  return labelMap[windowScope] || windowScope
}

export function formatFrameworkAdapterFailureSampleSize(entry) {
  const counts = normalizePayload(entry?.payload?.external_pilot_failure_counts)
  const sampleSize = Number(counts?.sample_size)
  if (!Number.isFinite(sampleSize) || sampleSize <= 0) {
    return ''
  }
  return String(sampleSize)
}

export function formatFrameworkAdapterFailureDistribution(entry) {
  const counts = normalizePayload(entry?.payload?.external_pilot_failure_counts)
  const distribution = normalizePayload(counts?.by_error_type)
  if (!distribution) {
    return ''
  }
  const fragments = Object.entries(distribution)
    .map(([errorType, count]) => {
      const numericCount = Number(count)
      if (!Number.isFinite(numericCount) || numericCount <= 0) {
        return ''
      }
      const label = formatFrameworkAdapterExternalErrorLabel(errorType)
      return `${label} ${numericCount}`
    })
    .filter(Boolean)
  return fragments.join(' · ')
}

function formatFrameworkAdapterRemediationStatus(actionType) {
  const labelMap = {
    install_package: '缺包',
    configure_env: '缺环境变量',
    enable_runtime_execution: '运行时未启用',
  }
  return labelMap[normalizeText(actionType)] || ''
}

export function buildFrameworkAdapterRemediationStatusTags(remediationActions) {
  if (!Array.isArray(remediationActions) || remediationActions.length === 0) {
    return []
  }
  const tags = []
  for (const action of remediationActions) {
    const label = formatFrameworkAdapterRemediationStatus(action?.type)
    if (label && !tags.includes(label)) {
      tags.push(label)
    }
  }
  return tags
}

export function formatFrameworkAdapterRemediationContent(displayName, actionCount, statusTags) {
  const normalizedDisplayName = normalizeText(displayName) || 'Framework Adapter'
  const summary = Array.isArray(statusTags) && statusTags.length
    ? statusTags.join(' / ')
    : `${actionCount} 条修复建议`
  return `${normalizedDisplayName} · ${summary}`
}

export function formatFrameworkAdapterDisplayName(frameworkName, adapterId) {
  const normalizedFrameworkName = normalizeText(frameworkName)
  const normalizedAdapterId = normalizeText(adapterId)
  if (normalizedFrameworkName) {
    return normalizedFrameworkName
  }
  const adapterLabelMap = {
    local_fake_framework: 'LocalFakeFramework',
    langgraph_draft: 'LangGraph',
    tool_registry: 'Tool Registry',
    mcp_runtime: 'MCP Runtime',
  }
  return adapterLabelMap[normalizedAdapterId] || normalizedAdapterId || 'Framework Adapter'
}

function getFrameworkAdapterIdentity(entry) {
  const data = normalizePayload(entry?.payload) || {}
  const frameworkName = normalizeText(data.framework_name)
  const adapterId = normalizeText(data.adapter_id)
  return {
    frameworkName,
    adapterId,
    displayName: formatFrameworkAdapterDisplayName(frameworkName, adapterId),
  }
}

function getFrameworkAdapterRemediationIdentity(remediation) {
  const remediationActions = Array.isArray(remediation?.remediationActions)
    ? remediation.remediationActions
    : []
  const frameworkName = remediationActions
    .map(item => normalizeText(item?.framework_name))
    .find(Boolean)
  const adapterId = normalizeText(remediation?.adapterId) || remediationActions
    .map(item => normalizeText(item?.adapter_id))
    .find(Boolean)
  return {
    frameworkName,
    adapterId,
    displayName: formatFrameworkAdapterDisplayName(frameworkName, adapterId),
  }
}

export function formatFrameworkAdapterSummaryHeading(entry, suffix) {
  const identity = getFrameworkAdapterIdentity(entry)
  const normalizedSuffix = normalizeText(suffix)
  return ['最近一次', identity.displayName, normalizedSuffix].filter(Boolean).join(' ')
}

export function formatFrameworkAdapterIdentityLine(entry) {
  const identity = getFrameworkAdapterIdentity(entry)
  if (identity.adapterId) {
    return `adapter_id: ${identity.adapterId}`
  }
  if (identity.frameworkName) {
    return `framework: ${identity.frameworkName}`
  }
  return ''
}

export function formatFrameworkAdapterRemediationHeading(remediation) {
  const identity = getFrameworkAdapterRemediationIdentity(remediation)
  return ['最近一次', identity.displayName || 'Framework Adapter', '修复建议'].filter(Boolean).join(' ')
}

export function formatFrameworkAdapterRemediationIdentityLine(remediation) {
  const identity = getFrameworkAdapterRemediationIdentity(remediation)
  return identity.adapterId ? `adapter_id: ${identity.adapterId}` : ''
}

export function formatFrameworkAdapterRemediationAction(action) {
  const data = normalizePayload(action) || {}
  const fragments = [
    normalizeText(data.adapter_id),
    normalizeText(data.type),
    normalizeText(data.message),
  ].filter(Boolean)
  return fragments.join(' · ') || 'framework_adapter_remediation'
}

export function buildFrameworkAdapterRemediationCommand(remediationActions) {
  if (!Array.isArray(remediationActions) || remediationActions.length === 0) {
    return ''
  }
  const installPackages = new Set()
  const requiredEnv = new Set()
  let needsRuntimeEnable = false

  for (const action of remediationActions) {
    const data = normalizePayload(action) || {}
    const actionType = normalizeText(data.type)
    if (actionType === 'install_package') {
      for (const item of data.packages || []) {
        const packageName = normalizeText(item)
        if (packageName) {
          installPackages.add(packageName)
        }
      }
    }
    if (actionType === 'configure_env') {
      for (const item of data.env || []) {
        const envName = normalizeText(item)
        if (envName) {
          requiredEnv.add(envName)
        }
      }
    }
    if (actionType === 'enable_runtime_execution') {
      needsRuntimeEnable = true
    }
  }

  const commands = []
  if (installPackages.size) {
    commands.push(`pip install ${[...installPackages].join(' ')}`)
  }
  for (const envName of requiredEnv) {
    commands.push(`${envName}=<value>`)
  }
  if (needsRuntimeEnable || requiredEnv.size || installPackages.size) {
    commands.push('ENABLE_LANGGRAPH_RUNTIME_EXECUTION=true')
  }
  return commands.join('\n')
}

export function getFrameworkAdapterExternalErrorType(entry) {
  if (entry?.domain !== 'framework_adapter') {
    return ''
  }
  return normalizeText(entry?.payload?.error_type)
}
