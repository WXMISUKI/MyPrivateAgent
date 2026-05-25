import { normalizeText, toTimestamp } from './governanceValueUtils'

export function compareApprovalRecency(leftRequest, leftIndex, rightRequest, rightIndex, toTimestampFn = toTimestamp) {
  const fields = ['updated_at', 'created_at', 'timestamp']
  for (const field of fields) {
    const leftValue = normalizeText(leftRequest?.[field])
    const rightValue = normalizeText(rightRequest?.[field])
    const leftHasValue = Boolean(leftValue)
    const rightHasValue = Boolean(rightValue)

    if (!leftHasValue && !rightHasValue) {
      continue
    }

    if (leftHasValue && rightHasValue) {
      const delta = toTimestampFn(leftValue) - toTimestampFn(rightValue)
      if (delta !== 0) {
        return delta
      }
      continue
    }

    return leftHasValue ? 1 : -1
  }

  return leftIndex - rightIndex
}

export function pickLatestApprovalRequest(requests, toTimestampFn = toTimestamp) {
  if (!Array.isArray(requests) || requests.length === 0) {
    return null
  }

  return requests.reduce((latest, current, index) => {
    if (!latest) {
      return { request: current, index }
    }

    return compareApprovalRecency(current, index, latest.request, latest.index, toTimestampFn) > 0
      ? { request: current, index }
      : latest
  }, null)?.request || null
}

export function isPendingApprovalStatus(value) {
  const status = normalizeText(value).toLowerCase()
  return ['pending', 'created', 'requested', 'waiting', 'waiting_approval'].includes(status)
}

export function buildCurrentRunOverview(run, options = {}) {
  const {
    traceCount = 0,
    normalizeText: normalizeTextFn = normalizeText,
  } = options

  if (!run || typeof run !== 'object' || Array.isArray(run)) {
    return null
  }

  const runId = normalizeTextFn(run.run_id || run.scheduler_run_id)
  const runKind = normalizeTextFn(run.run_kind)
  const status = normalizeTextFn(run.state || run.status)
  const activeChildren = Number(run.active_children || 0)
  const approvalCount = Number(run.approval_request_count || 0)
  const parentRunId = normalizeTextFn(run.parent_run_id)
  const childRunId = normalizeTextFn(run.child_run_id)

  const hasConcreteRunContext = Boolean(
    runId ||
    status ||
    parentRunId ||
    childRunId ||
    activeChildren > 0 ||
    approvalCount > 0
  )

  if (!hasConcreteRunContext) {
    return null
  }

  const noticeParts = []
  if (traceCount > 0) {
    noticeParts.push(`Trace ${traceCount}`)
  }
  if (activeChildren > 0) {
    noticeParts.push(`活跃子任务 ${activeChildren}`)
  }
  if (approvalCount > 0) {
    noticeParts.push(`审批 ${approvalCount}`)
  }

  return {
    id: runId || '未分配',
    summary: [runKind, status].filter(Boolean).join(' · ') || '等待运行时状态回填',
    notice: noticeParts.join(' · ') || '当前 Run 暂无附加上下文',
  }
}

export function buildApprovalOverview(approvalRequests, options = {}) {
  const {
    currentRunOverview = null,
    normalizeText: normalizeTextFn = normalizeText,
    toTimestamp = toTimestamp,
  } = options

  const requests = Array.isArray(approvalRequests) ? approvalRequests : []
  const pendingRequests = requests.filter(item => isPendingApprovalStatus(item?.status))
  const latestPending = pickLatestApprovalRequest(pendingRequests, toTimestamp)
  const latestRequest = latestPending || pickLatestApprovalRequest(requests, toTimestamp)
  const requestId = normalizeTextFn(latestPending?.request_id || latestRequest?.request_id)
  const toolName = normalizeTextFn(latestPending?.tool_name || latestRequest?.tool_name)
  const permissionLevel = normalizeTextFn(latestPending?.permission_level || latestRequest?.permission_level)

  return {
    pendingLabel: `${pendingRequests.length} 个待处理`,
    primaryDetail: latestPending
      ? [toolName || 'unknown_tool', requestId || '未命名审批'].filter(Boolean).join(' · ')
      : '当前没有待处理审批',
    secondaryDetail: latestPending
      ? [permissionLevel || '未标注级别', currentRunOverview?.id || '未关联 Run'].filter(Boolean).join(' · ')
      : (latestRequest ? `最近审批状态 ${normalizeTextFn(latestRequest.status) || '-'}` : '当前没有审批请求'),
  }
}
