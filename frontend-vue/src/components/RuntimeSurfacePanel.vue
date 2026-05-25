<template>
  <section class="settings-section runtime-panel">
    <div class="section-head">
      <div>
        <h2>运行时能力面</h2>
        <p class="section-desc">查看当前 demo 模式、provider、模型目录，以及框架当前可暴露的运行时表面。</p>
      </div>
      <button class="secondary-btn" :disabled="loading" @click="loadProfile">
        {{ loading ? '刷新中...' : '刷新运行时信息' }}
      </button>
    </div>

    <p v-if="error" class="inline-error">{{ error }}</p>

    <div v-if="profile" class="summary-grid">
      <div class="summary-card">
        <span class="summary-label">运行模式</span>
        <strong>{{ profile.agent_mode || 'general_demo' }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">鉴权模式</span>
        <strong>{{ profile.auth_mode || 'demo_guest' }}</strong>
        <small class="summary-note">{{ authModeDescription }}</small>
      </div>
      <div class="summary-card">
        <span class="summary-label">默认模型</span>
        <strong>{{ profile.default_model || '-' }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">Provider 数量</span>
        <strong>{{ providers.length }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">契约门禁</span>
        <strong>{{ runtimeContractGate.overall_status || '-' }}</strong>
        <small class="summary-note">failed checks: {{ runtimeContractGate.failed_check_count }}</small>
        <button
          v-if="runtimeContractGate.failed_check_count > 0"
          class="secondary-btn summary-action-btn"
          @click="openRuntimeContractGateTimeline"
        >
          查看治理事件
        </button>
      </div>
    </div>

    <div v-if="profile" class="panel-card">
      <div class="card-head">
        <h3>Main Chat Trace</h3>
        <span class="muted">统一控制聊天页专家模式的 main_chat Query Control 透传开关</span>
      </div>
      <div class="summary-grid runtime-contract-grid">
        <div class="summary-card">
          <span class="summary-label">当前状态</span>
          <strong>{{ settingsStore.enableMainChatRuntimeTrace ? 'enabled' : 'disabled' }}</strong>
          <small class="summary-note">
            {{ settingsStore.enableMainChatRuntimeTrace ? '普通 chat 会附加受控 execution_context' : '默认用户路径不附加 execution_context' }}
          </small>
        </div>
        <div class="summary-card">
          <span class="summary-label">入口类型</span>
          <strong>expert toggle</strong>
          <small class="summary-note">ChatView 与 Runtime Surface 共用同一设置源</small>
        </div>
        <div class="summary-card">
          <span class="summary-label">最近写入</span>
          <strong>{{ mainChatTraceOverview.recordingState }}</strong>
          <small class="summary-note">
            {{ mainChatTraceOverview.latestStage ? `stage: ${mainChatTraceOverview.latestStage}` : (mainChatTraceOverview.reason || '暂无 main_chat trace') }}
          </small>
        </div>
        <div class="summary-card">
          <span class="summary-label">最后成功阶段</span>
          <strong>{{ mainChatTraceOverview.lastSuccessStage || '-' }}</strong>
          <small class="summary-note">最近告警阶段 {{ mainChatTraceOverview.lastWarningStage || '-' }}</small>
        </div>
      </div>
      <label class="trace-toggle-row" :class="{ active: settingsStore.enableMainChatRuntimeTrace }">
        <input
          type="checkbox"
          :checked="settingsStore.enableMainChatRuntimeTrace"
          @change="settingsStore.setEnableMainChatRuntimeTrace($event.target.checked)"
        >
        <span class="trace-toggle-copy">
          <strong>启用 Main Chat Runtime Trace</strong>
          <small>打开后，聊天请求会透传受控 execution_context，用于 main_chat Query Control timeline 观测。</small>
        </span>
      </label>
      <div class="trace-status-grid">
        <div class="contract-block">
          <h4>最近一次 main_chat trace</h4>
          <ul>
            <li><code>query_id</code>: {{ mainChatTraceOverview.latestQueryId || '-' }}</li>
            <li><code>snapshot_id</code>: {{ mainChatTraceOverview.latestSnapshotId || '-' }}</li>
            <li><code>timestamp</code>: {{ mainChatTraceOverview.latestTimestamp || '-' }}</li>
            <li>{{ mainChatTraceOverview.latestSummary || mainChatTraceOverview.latestDetail || mainChatTraceOverview.reason || '暂无写入记录' }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>阶段分布</h4>
          <ul>
            <li v-if="!mainChatTraceOverview.stageEntries.length">暂无阶段统计</li>
            <li v-for="entry in mainChatTraceOverview.stageEntries" :key="entry.stage">
              <code>{{ entry.stage }}</code>: {{ entry.count }}
            </li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>最近 Query</h4>
          <ul>
            <li v-if="!mainChatTraceOverview.recentQueries.length">暂无 query 历史</li>
            <li v-for="query in mainChatTraceOverview.recentQueries" :key="query.queryId">
              <button type="button" class="link-btn" @click="openMainChatQueryTimeline(query.queryId)">
                <code>{{ query.queryId }}</code>
              </button>
              · {{ query.latestStage || '-' }} · {{ query.latestSummary || '无摘要' }}
            </li>
          </ul>
        </div>
      </div>
      <div class="trace-status-grid">
        <div class="contract-block">
          <h4>Query History Contract</h4>
          <ul>
            <li><code>state</code>: {{ mainChatQueryHistory.recordingState || 'unavailable' }}</li>
            <li><code>page</code>: {{ mainChatQueryHistory.page }}</li>
            <li><code>page_size</code>: {{ mainChatQueryHistory.pageSize }}</li>
            <li><code>total_items</code>: {{ mainChatQueryHistory.totalItems }}</li>
            <li><code>next_cursor</code>: {{ mainChatQueryHistory.nextCursor || '-' }}</li>
            <li>{{ mainChatQueryHistory.reason || 'query history 已就绪' }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <div class="card-head">
            <h4>Query History Items</h4>
            <button
              type="button"
              class="secondary-btn"
              :disabled="mainChatQueryHistoryLoading || !mainChatQueryHistory.hasMore"
              @click="loadMoreMainChatQueryHistory"
            >
              {{ mainChatQueryHistoryLoading ? '加载中...' : (mainChatQueryHistory.hasMore ? '加载更多' : '已加载完成') }}
            </button>
          </div>
          <ul>
            <li v-if="!mainChatQueryHistory.items.length">暂无 query history</li>
            <li v-for="query in mainChatQueryHistory.items" :key="`${query.queryId}-${query.latestTimestamp}`">
              <button type="button" class="link-btn" @click="openMainChatQueryTimeline(query.queryId)">
                <code>{{ query.queryId }}</code>
              </button>
              · {{ query.latestStage || '-' }} · {{ query.latestSummary || '无摘要' }}
            </li>
          </ul>
        </div>
      </div>
      <div v-if="mainChatQueryDetail.connected || activeMainChatQueryId" class="trace-status-grid">
        <div class="contract-block">
          <h4>Query Detail Contract</h4>
          <div class="model-meta">
            <span><code>layer</code>: {{ mainChatQueryDetail.readModelLayer || '-' }}</span>
            <span><code>source</code>: {{ mainChatQueryDetail.sourceChannel || '-' }}</span>
            <span><code>identity</code>: {{ mainChatQueryDetail.identityKind || '-' }}</span>
          </div>
          <ul>
            <li><code>query_id</code>: {{ mainChatQueryDetail.queryId || activeMainChatQueryId || '-' }}</li>
            <li><code>state</code>: {{ mainChatQueryDetail.recordingState || 'unavailable' }}</li>
            <li><code>latest_stage</code>: {{ mainChatQueryDetail.latestStage || '-' }}</li>
            <li><code>stage_count</code>: {{ mainChatQueryDetail.stageCount }}</li>
            <li><code>warning_count</code>: {{ mainChatQueryDetail.warningCount }}</li>
            <li><code>snapshot_id</code>: {{ mainChatQueryDetail.latestSnapshotId || '-' }}</li>
            <li>{{ mainChatQueryDetail.latestSummary || '无最近摘要' }}</li>
            <li>{{ mainChatQueryDetail.latestWarningSummary || mainChatQueryDetail.reason || '无最近告警' }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>Query Stage Chain</h4>
          <ul>
            <li v-if="!mainChatQueryDetail.stageChain.length">暂无阶段链</li>
            <li v-for="stage in mainChatQueryDetail.stageChain" :key="stage">
              <code>{{ stage }}</code>
            </li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>Query Recent Events</h4>
          <ul>
            <li v-if="!mainChatQueryDetail.recentEvents.length">暂无事件摘要</li>
            <li v-for="event in mainChatQueryDetail.recentEvents" :key="`${event.timestamp}-${event.stage}-${event.summary}`">
              <code>{{ event.stage || '-' }}</code> · {{ event.summary || '无摘要' }} · {{ event.severity || 'info' }}
            </li>
          </ul>
        </div>
      </div>
    </div>

    <div v-if="profile" class="panel-card">
      <div class="card-head">
        <h3>Runtime Core 合同</h3>
        <span class="muted">{{ runtimeCore.connected ? 'Phase A 对齐：把当前 run 的核心上下文支点直接暴露到运行时面板' : 'Phase A 对齐：当前前端已预留 runtime core 卡位' }}</span>
      </div>
      <p v-if="!runtimeCore.connected" class="contract-placeholder">等待后端接入 runtime_core contract</p>
      <div class="summary-grid runtime-contract-grid">
        <div class="summary-card">
          <span class="summary-label">执行实例 run_id</span>
          <strong>{{ runtimeCore.run_id || '-' }}</strong>
          <small class="summary-note">{{ formatInlinePair(runtimeCore.run_kind, runtimeCore.status) }}</small>
        </div>
        <div class="summary-card">
          <span class="summary-label">parent / child</span>
          <strong>{{ runtimeCore.parent_run_id || '-' }}</strong>
          <small class="summary-note">child: {{ runtimeCore.child_run_id || '-' }}</small>
        </div>
        <div class="summary-card">
          <span class="summary-label">scheduler_run_id</span>
          <strong>{{ runtimeCore.scheduler_run_id || '-' }}</strong>
          <small class="summary-note">trace_count: {{ runtimeCore.trace_count ?? 0 }}</small>
        </div>
      </div>
      <div v-if="runtimeCore.latest_trace_event" class="contract-block runtime-detail-block">
        <h4>最近 Trace</h4>
        <ul>
          <li><code>{{ runtimeCore.latest_trace_event.event_type || '-' }}</code></li>
          <li>{{ runtimeCore.latest_trace_event.summary || '无摘要' }}</li>
          <li>{{ runtimeCore.latest_trace_event.detail || '无 detail' }}</li>
        </ul>
      </div>
      <div v-if="runtimeCore.child_merge_intent || runtimeCore.child_merge_entities.length || runtimeCore.child_merge_conclusion" class="contract-block runtime-detail-block">
        <h4>Parent Merge State</h4>
        <ul>
          <li><code>child_merge_intent</code>: {{ runtimeCore.child_merge_intent || '-' }}</li>
          <li><code>child_merge_entities</code>: {{ runtimeCore.child_merge_entities.length ? runtimeCore.child_merge_entities.join('、') : '-' }}</li>
          <li><code>child_merge_entity_count</code>: {{ runtimeCore.child_merge_entity_count ?? 0 }}</li>
          <li><code>child_merge_focus_count</code>: {{ runtimeCore.child_merge_focus_count ?? 0 }}</li>
          <li><code>child_merge_action_count</code>: {{ runtimeCore.child_merge_action_count ?? 0 }}</li>
          <li><code>child_merge_primary_entities</code>: {{ runtimeCore.child_merge_primary_entities.length ? runtimeCore.child_merge_primary_entities.join('、') : '-' }}</li>
          <li><code>child_merge_conclusion</code>: {{ runtimeCore.child_merge_conclusion || '-' }}</li>
        </ul>
      </div>
      <div v-if="runRecovery.available" class="contract-block runtime-detail-block">
        <h4>Run Recovery</h4>
        <ul>
          <li><code>recoverable</code>: {{ runRecovery.recoverable ? 'true' : 'false' }}</li>
          <li><code>run_state</code>: {{ runRecovery.run_state || '-' }}</li>
          <li><code>tool_recovery_reason</code>: {{ runRecovery.toolContinuation.recoveryReason || '-' }}</li>
          <li><code>loop_recovery_reason</code>: {{ runRecovery.loopContinuation.recoveryReason || '-' }}</li>
          <li><code>workspace_backend</code>: {{ runRecovery.workspaceBackend.backendKind || '-' }}</li>
          <li><code>backend_durable</code>: {{ runRecovery.workspaceBackend.durable ? 'true' : 'false' }}</li>
          <li><code>fallback_active</code>: {{ runRecovery.workspaceBackend.fallbackActive ? 'true' : 'false' }}</li>
          <li><code>reason</code>: {{ runRecovery.reason || '-' }}</li>
        </ul>
      </div>
    </div>

    <div v-if="profile" class="panel-card">
      <div class="card-head">
        <h3>治理总览合同</h3>
        <span class="muted">{{ governanceOverview.connected ? 'Phase A 对齐：最小展示 run / approval / audit overview contract' : 'Phase A 对齐：当前前端已预留 governance overview 卡位' }}</span>
      </div>
      <p v-if="!governanceOverview.connected" class="contract-placeholder">等待后端接入 governance_overview contract</p>
      <div class="summary-grid runtime-contract-grid">
        <div class="summary-card">
          <span class="summary-label">治理执行实例</span>
          <strong>{{ governanceOverview.run?.run_id || '-' }}</strong>
          <small class="summary-note">{{ formatInlinePair(governanceOverview.run?.run_kind, governanceOverview.run?.status) }}</small>
        </div>
        <div class="summary-card">
          <span class="summary-label">待处理审批</span>
          <strong>{{ `${governanceOverview.approval?.pending_count || 0} 个待处理` }}</strong>
          <small class="summary-note">总审批 {{ governanceOverview.approval?.request_count || 0 }}</small>
        </div>
        <div class="summary-card">
          <span class="summary-label">审计事件</span>
          <strong>{{ governanceOverview.audit?.event_count || 0 }}</strong>
          <small class="summary-note">{{ governanceOverview.audit?.latest_event?.summary || '暂无最近审计事件' }}</small>
        </div>
        <div class="summary-card">
          <span class="summary-label">治理 Query</span>
          <strong>{{ governanceOverview.main_chat?.recordingState || 'unavailable' }}</strong>
          <small class="summary-note">
            {{ governanceOverview.main_chat?.latestStage ? `stage: ${governanceOverview.main_chat.latestStage}` : (governanceOverview.main_chat?.reason || '暂无 main_chat trace') }}
          </small>
        </div>
        <div class="summary-card">
          <span class="summary-label">Main Chat 最后成功</span>
          <strong>{{ governanceOverview.main_chat?.lastSuccessStage || '-' }}</strong>
          <small class="summary-note">最近告警阶段 {{ governanceOverview.main_chat?.lastWarningStage || '-' }}</small>
        </div>
      </div>
      <div class="contract-grid">
        <div class="contract-block">
          <h4>Run Overview</h4>
          <ul>
            <li><code>scheduler_run_id</code>: {{ governanceOverview.run?.scheduler_run_id || '-' }}</li>
            <li><code>child_run_id</code>: {{ governanceOverview.run?.child_run_id || '-' }}</li>
            <li><code>latest_trace</code>: {{ governanceOverview.run?.latest_trace_event?.summary || '-' }}</li>
            <li><code>child_merge_intent</code>: {{ governanceOverview.run?.childMergeIntent || '-' }}</li>
            <li><code>child_merge_entities</code>: {{ governanceOverview.run?.childMergeEntities?.length ? governanceOverview.run.childMergeEntities.join('、') : '-' }}</li>
            <li><code>child_merge_entity_count</code>: {{ governanceOverview.run?.childMergeEntityCount ?? 0 }}</li>
            <li><code>child_merge_focus_count</code>: {{ governanceOverview.run?.childMergeFocusCount ?? 0 }}</li>
            <li><code>child_merge_action_count</code>: {{ governanceOverview.run?.childMergeActionCount ?? 0 }}</li>
            <li><code>child_merge_primary_entities</code>: {{ governanceOverview.run?.childMergePrimaryEntities?.length ? governanceOverview.run.childMergePrimaryEntities.join('、') : '-' }}</li>
            <li><code>child_merge_conclusion</code>: {{ governanceOverview.run?.childMergeConclusion || '-' }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>Run Recovery</h4>
          <ul>
            <li><code>recoverable</code>: {{ governanceOverview.runRecovery?.recoverable ? 'true' : 'false' }}</li>
            <li><code>run_state</code>: {{ governanceOverview.runRecovery?.runState || '-' }}</li>
            <li><code>tool_recovery_reason</code>: {{ governanceOverview.runRecovery?.toolContinuation?.recoveryReason || '-' }}</li>
            <li><code>loop_recovery_reason</code>: {{ governanceOverview.runRecovery?.loopContinuation?.recoveryReason || '-' }}</li>
            <li><code>workspace_backend</code>: {{ governanceOverview.runRecovery?.workspaceBackend?.backendKind || '-' }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>Child Executor Preflight</h4>
          <ul>
            <li><code>status</code>: {{ governanceOverview.childExecutorPreflight?.status || '-' }}</li>
            <li><code>promotion_ready</code>: {{ governanceOverview.childExecutorPreflight?.promotionReady ? 'true' : 'false' }}</li>
            <li><code>executor_binding_status</code>: {{ governanceOverview.childExecutorPreflight?.executorBindingStatus || '-' }}</li>
            <li><code>recommended_next_step</code>: {{ governanceOverview.childExecutorPreflight?.recommendedNextStep || '-' }}</li>
            <li><code>gate_status</code>: {{ governanceOverview.childExecutorPreflight?.gateStatus || '-' }}</li>
            <li><code>gate_allowed</code>: {{ governanceOverview.childExecutorPreflight?.gateAllowed ? 'true' : 'false' }}</li>
            <li><code>workspace_backend</code>: {{ governanceOverview.childExecutorPreflight?.workspaceBackend?.backend_kind || '-' }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>Child Executor Promotion Gate</h4>
          <ul>
            <li><code>gate_status</code>: {{ governanceOverview.childExecutorPromotionGate?.gateStatus || '-' }}</li>
            <li><code>allowed</code>: {{ governanceOverview.childExecutorPromotionGate?.allowed ? 'true' : 'false' }}</li>
            <li><code>executor_path</code>: {{ governanceOverview.childExecutorPromotionGate?.executorPath || '-' }}</li>
            <li><code>recommended_next_step</code>: {{ governanceOverview.childExecutorPromotionGate?.recommendedNextStep || '-' }}</li>
            <li><code>failure_reason</code>: {{ governanceOverview.childExecutorPromotionGate?.failureReason || '-' }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>Approval Overview</h4>
          <ul>
            <li><code>request_id</code>: {{ governanceOverview.approval?.latest_request?.request_id || '-' }}</li>
            <li><code>tool_name</code>: {{ governanceOverview.approval?.latest_request?.tool_name || '-' }}</li>
            <li><code>permission_level</code>: {{ governanceOverview.approval?.latest_request?.permission_level || '-' }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>Audit Overview</h4>
          <ul>
            <li><code>latest_event</code>: {{ governanceOverview.audit?.latest_event?.event_type || '-' }}</li>
            <li>{{ governanceOverview.audit?.latest_event?.summary || '-' }}</li>
            <li>{{ governanceOverview.audit?.latest_event?.detail || '-' }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>Main Chat Trace</h4>
          <ul>
            <li><code>query_id</code>: {{ governanceOverview.main_chat?.latestQueryId || '-' }}</li>
            <li><code>snapshot_id</code>: {{ governanceOverview.main_chat?.latestSnapshotId || '-' }}</li>
            <li><code>state</code>: {{ governanceOverview.main_chat?.recordingState || 'unavailable' }}</li>
            <li>{{ governanceOverview.main_chat?.latestSummary || governanceOverview.main_chat?.reason || '-' }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>Main Chat Recent Queries</h4>
          <ul>
            <li v-if="!governanceOverview.main_chat?.recentQueries?.length">暂无 query 历史</li>
            <li v-for="query in governanceOverview.main_chat?.recentQueries || []" :key="query.queryId">
              <button type="button" class="link-btn" @click="openMainChatQueryTimeline(query.queryId)">
                <code>{{ query.queryId }}</code>
              </button>
              · {{ query.latestStage || '-' }} · {{ query.latestSummary || '无摘要' }}
            </li>
          </ul>
        </div>
      </div>
    </div>

    <div v-if="profile" class="panel-card">
      <div class="card-head">
        <h3>Tool Runtime 合同</h3>
        <span class="muted">{{ toolRuntime.connected ? toolRuntime.contract_version : 'Phase B 对齐：当前前端已预留 tool runtime 卡位' }}</span>
      </div>
      <p v-if="!toolRuntime.connected" class="contract-placeholder">等待后端接入 tool_runtime contract</p>
      <div class="summary-grid runtime-contract-grid">
        <div class="summary-card">
          <span class="summary-label">工具总数</span>
          <strong>{{ toolRuntime.total_tools }}</strong>
          <small class="summary-note">spec: {{ toolRuntime.tool_spec_count }}</small>
        </div>
        <div class="summary-card">
          <span class="summary-label">LangChain 工具</span>
          <strong>{{ toolRuntime.langchain_tool_count }}</strong>
          <small class="summary-note">base: {{ toolRuntime.base_tool_count }}</small>
        </div>
        <div class="summary-card">
          <span class="summary-label">MCP capability</span>
          <strong>{{ toolRuntime.mcp_capability_count }}</strong>
          <small class="summary-note">doubao defs: {{ toolRuntime.doubao_definition_count }}</small>
        </div>
        <div class="summary-card">
          <span class="summary-label">高风险工具</span>
          <strong>{{ toolRuntime.high_risk_tool_count }}</strong>
          <small class="summary-note">需审批或高风险策略命中</small>
        </div>
      </div>
      <div v-if="toolRuntime.tools.length" class="catalog-tags">
        <span v-for="tool in toolRuntime.tools.slice(0, 8)" :key="tool.name" class="capability-pill">
          {{ tool.name }} · {{ tool.risk_level || 'normal' }}
        </span>
      </div>
    </div>

    <div v-if="profile" class="panel-card">
      <div class="card-head">
        <h3>MCP Runtime 合同</h3>
        <span class="muted">{{ mcpRuntime.connected ? mcpRuntime.contract_version : 'Phase B-3 对齐：当前前端已预留 mcp runtime 卡位' }}</span>
      </div>
      <p v-if="!mcpRuntime.connected" class="contract-placeholder">等待后端接入 mcp_runtime contract</p>
      <div class="summary-grid runtime-contract-grid">
        <div class="summary-card">
          <span class="summary-label">overall_status</span>
          <strong>{{ mcpRuntime.overall_status || '-' }}</strong>
          <small class="summary-note">capabilities: {{ mcpRuntime.capability_count }}</small>
        </div>
        <div class="summary-card">
          <span class="summary-label">enabled_servers</span>
          <strong>{{ mcpRuntime.enabled_servers }}</strong>
          <small class="summary-note">MCP server 可用入口</small>
        </div>
      </div>
      <div class="provider-grid">
        <div v-for="component in mcpRuntime.components" :key="component.component_id" class="provider-card">
          <div class="provider-title-row">
            <strong>{{ component.display_name || component.component_id }}</strong>
            <span class="status-badge" :class="{ online: component.status === 'healthy', offline: component.status !== 'healthy' }">
              {{ component.status || 'unknown' }}
            </span>
          </div>
          <p class="provider-meta"><code>{{ component.component_id }}</code></p>
          <p class="provider-endpoint">{{ component.detail || '-' }}</p>
        </div>
      </div>
    </div>

    <div v-if="profile" class="panel-card">
      <div class="card-head">
        <h3>Adapter Health</h3>
        <span class="muted">{{ adapterHealth.connected ? adapterHealth.contract_version : 'Phase B 对齐：当前前端已预留 adapter health 卡位' }}</span>
      </div>
      <p v-if="!adapterHealth.connected" class="contract-placeholder">等待后端接入 adapter_health contract</p>
      <div class="summary-grid runtime-contract-grid">
        <div class="summary-card">
          <span class="summary-label">overall_status</span>
          <strong>{{ adapterHealth.overall_status || '-' }}</strong>
          <small class="summary-note">adapters: {{ adapterHealth.adapter_count }}</small>
        </div>
        <div class="summary-card">
          <span class="summary-label">unavailable</span>
          <strong>{{ adapterHealth.unavailable_count }}</strong>
          <small class="summary-note">不可用 adapter 数</small>
        </div>
      </div>
      <AdapterExternalPilotFailureSummary
        :failure="adapterHealth.latest_external_pilot_failure"
        :counts="adapterHealth.external_pilot_failure_counts"
        :active-error-type="activeAdapterFailureType"
        @open-snapshot="openAdapterPilotSnapshot"
        @open-failure-type="openAdapterFailureTypeTimeline"
      />
      <div class="provider-grid">
        <AdapterHealthCard
          v-for="adapter in adapterHealth.adapters"
          :key="adapter.adapter_id"
          :adapter="adapter"
          :adapter-precheck-running="adapterPrecheckRunning"
          :adapter-external-pilot-running="adapterExternalPilotRunning"
          :adapter-pilot-running="adapterPilotRunning"
          :adapter-precheck-result="adapterPrecheckResult"
          :adapter-external-pilot-result="adapterExternalPilotResult"
          :adapter-pilot-result="adapterPilotResult"
          :copied-command-text="copiedSnapshotCommandText"
          @run-precheck="runAdapterPrecheck"
          @run-external-pilot="runAdapterExternalPilot"
          @run-pilot="runAdapterPilot"
          @open-snapshot="openAdapterPilotSnapshot"
          @copy-command="copySnapshotCommand"
        />
      </div>
    </div>

    <div v-if="profile" class="panel-card">
      <div class="card-head">
        <h3>Contract Snapshot</h3>
        <span class="muted">{{ contractSnapshot.connected ? contractSnapshot.contract_version : 'Phase C-1 对齐：当前前端已预留 contract snapshot 卡位' }}</span>
      </div>
      <p v-if="!contractSnapshot.connected" class="contract-placeholder">等待后端接入 contract_snapshot</p>
      <div class="summary-grid runtime-contract-grid">
        <div class="summary-card">
          <span class="summary-label">overall_status</span>
          <strong>{{ contractSnapshot.overall_status || '-' }}</strong>
          <small class="summary-note">contracts: {{ contractSnapshot.contract_count }}</small>
        </div>
        <div class="summary-card">
          <span class="summary-label">missing contracts</span>
          <strong>{{ contractSnapshot.missing_contract_count }}</strong>
          <small class="summary-note">missing contracts: {{ contractSnapshot.missing_contract_count }}</small>
        </div>
        <div class="summary-card">
          <span class="summary-label">missing fields</span>
          <strong>{{ contractSnapshot.missing_field_count }}</strong>
          <small class="summary-note">missing fields: {{ contractSnapshot.missing_field_count }}</small>
        </div>
      </div>
      <div class="contract-block runtime-detail-block">
        <h4>Snapshot Fingerprint</h4>
        <ul>
          <li><code>{{ contractSnapshot.fingerprint || '-' }}</code></li>
        </ul>
      </div>
      <div class="provider-grid">
        <div v-for="contract in contractSnapshot.contracts" :key="contract.contract_name" class="provider-card">
          <div class="provider-title-row">
            <strong>{{ contract.contract_name }}</strong>
            <span class="status-badge" :class="{ online: contract.status === 'healthy', offline: contract.status !== 'healthy' }">
              {{ contract.status || 'unknown' }}
            </span>
          </div>
          <p class="provider-meta">
            <code>{{ contract.version || '-' }}</code>
            <span>fields: {{ contract.field_count || 0 }}</span>
          </p>
          <p class="provider-endpoint">fingerprint: {{ contract.fingerprint || '-' }}</p>
          <div v-if="(contract.missing_fields || []).length" class="catalog-tags">
            <span v-for="field in contract.missing_fields || []" :key="`${contract.contract_name}-${field}`" class="capability-pill">
              missing: {{ field }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="profile" class="panel-card">
      <div class="card-head">
        <h3>Contract Gate</h3>
        <span class="muted">{{ runtimeContractGate.connected ? runtimeContractGate.contract_version : 'Phase F-20 对齐：当前前端已预留 contract gate 卡位' }}</span>
      </div>
      <p v-if="!runtimeContractGate.connected" class="contract-placeholder">等待后端接入 runtime_contract_gate</p>
      <div class="summary-grid runtime-contract-grid">
        <div class="summary-card">
          <span class="summary-label">overall_status</span>
          <strong>{{ runtimeContractGate.overall_status || '-' }}</strong>
          <small class="summary-note">checks: {{ runtimeContractGate.check_count }}</small>
        </div>
        <div class="summary-card">
          <span class="summary-label">failed checks</span>
          <strong>{{ runtimeContractGate.failed_check_count }}</strong>
          <small class="summary-note">failed checks: {{ runtimeContractGate.failed_check_count }}</small>
        </div>
        <div class="summary-card">
          <span class="summary-label">report</span>
          <strong>{{ runtimeContractGate.available ? 'available' : 'unknown' }}</strong>
          <small class="summary-note">{{ runtimeContractGate.report_path || '-' }}</small>
        </div>
      </div>
      <div class="contract-block runtime-detail-block">
        <h4>Quality Gate Source</h4>
        <ul>
          <li><code>generated_at</code>: {{ runtimeContractGate.generated_at || '-' }}</li>
          <li><code>report_path</code>: {{ runtimeContractGate.report_path || '-' }}</li>
          <li><code>failure_reason</code>: {{ runtimeContractGate.failure_reason || '-' }}</li>
        </ul>
      </div>
      <div class="contract-block runtime-detail-block">
        <h4>Runtime Contract Summary</h4>
        <ul>
          <li><code>overall_status</code>: {{ runtimeContractGate.summary.overall_status || '-' }}</li>
          <li><code>missing_payload_count</code>: {{ runtimeContractGate.summary.missing_payload_count }}</li>
          <li><code>approval replay coverage</code>: {{ runtimeContractGate.summary.approvalReplayCovered ? 'covered' : 'missing' }}</li>
        </ul>
        <div class="catalog-tags">
          <span
            v-for="statusKind in runtimeContractGate.summary.observedStatusKinds"
            :key="`runtime-contract-summary-${statusKind}`"
            class="capability-pill"
          >
            {{ statusKind }}
          </span>
        </div>
      </div>
      <div class="provider-grid">
        <div v-for="check in runtimeContractGate.checks" :key="`${check.step}-${check.name}`" class="provider-card">
          <div class="provider-title-row">
            <strong>{{ check.name || '-' }}</strong>
            <span class="status-badge" :class="{ online: check.ok, offline: !check.ok }">
              {{ check.ok ? 'passed' : 'failed' }}
            </span>
          </div>
          <p class="provider-meta">
            <code>{{ check.step || '-' }}</code>
            <span v-if="check.status_code">status: {{ check.status_code }}</span>
          </p>
          <p class="provider-endpoint">{{ check.failure_reason || 'quality gate check passed' }}</p>
          <p
            v-if="check.backend_kind || check.tool_recovery_reason || check.loop_recovery_reason"
            class="provider-endpoint"
          >
            {{ check.backend_kind ? `backend: ${check.backend_kind}` : '' }}
            <span v-if="check.backend_mode"> · mode: {{ check.backend_mode }}</span>
            <span v-if="check.tool_recovery_reason"> · tool: {{ check.tool_recovery_reason }}</span>
            <span v-if="check.loop_recovery_reason"> · loop: {{ check.loop_recovery_reason }}</span>
            <span v-if="check.resumed_state"> · resumed: {{ check.resumed_state }}</span>
          </p>
          <div class="catalog-tags">
            <span v-if="check.contract_snapshot_status" class="capability-pill">snapshot: {{ check.contract_snapshot_status }}</span>
            <span v-if="check.adapter_health_status" class="capability-pill">adapter: {{ check.adapter_health_status }}</span>
            <span class="capability-pill">events: {{ check.checked_event_count }}</span>
            <span class="capability-pill">missing payloads: {{ check.missing_payload_count }}</span>
            <span v-if="check.backend_kind" class="capability-pill">backend: {{ check.backend_kind }}</span>
            <span v-if="check.backend_mode" class="capability-pill">mode: {{ check.backend_mode }}</span>
            <span v-if="check.probe_recoverable !== ''" class="capability-pill">recoverable: {{ check.probe_recoverable }}</span>
            <span v-if="check.fallback_active !== ''" class="capability-pill">fallback: {{ check.fallback_active }}</span>
            <span
              v-for="statusKind in check.observed_status_kinds"
              :key="`${check.step}-${check.name}-${statusKind}`"
              class="capability-pill"
            >
              {{ statusKind }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="capabilityContract" class="panel-card">
      <div class="card-head">
        <h3>主智能体能力合同</h3>
        <span class="muted">用于约束通用智能体的身份、执行原则与能力边界</span>
      </div>
      <p class="contract-summary">{{ capabilityContract.identity_summary }}</p>

      <div class="contract-grid">
        <div class="contract-block">
          <h4>执行原则</h4>
          <ul>
            <li v-for="item in capabilityContract.operating_principles || []" :key="item">{{ item }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>当前可用能力</h4>
          <ul>
            <li v-for="item in capabilityContract.available_capabilities || []" :key="item">{{ item }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>当前受限能力</h4>
          <ul>
            <li v-for="item in capabilityContract.limited_capabilities || []" :key="item">{{ item }}</li>
          </ul>
        </div>
      </div>
    </div>

    <div v-if="profile" class="panel-card">
      <div class="card-head">
        <h3>SkillDefinition 合同</h3>
        <span class="muted">{{ skillContract.connected ? skillContract.contract_version : 'Phase B-4 对齐：当前前端已预留 skill definition 卡位' }}</span>
      </div>
      <p v-if="!skillContract.connected" class="contract-placeholder">等待后端接入 skill_contract</p>
      <div class="summary-grid runtime-contract-grid">
        <div class="summary-card">
          <span class="summary-label">definitions</span>
          <strong>{{ skillContract.total_definitions }}</strong>
          <small class="summary-note">可治理 SkillDefinition 数</small>
        </div>
      </div>
      <div class="provider-grid">
        <div v-for="definition in skillContract.definitions" :key="definition.skill_id || definition.name" class="provider-card">
          <div class="provider-title-row">
            <strong>{{ definition.name || '-' }}</strong>
            <span class="status-badge online">{{ definition.scope || 'chat' }}</span>
          </div>
          <p class="provider-meta">
            <code>skill_id: {{ definition.skill_id || '-' }}</code>
            <span>version: {{ definition.version || '-' }}</span>
          </p>
          <p class="provider-endpoint">selection_reason: {{ definition.selection_reason || '-' }}</p>
          <div class="catalog-tags">
            <span v-for="capability in definition.required_capabilities || []" :key="`${definition.skill_id}-${capability}`" class="capability-pill">
              {{ capability }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="memoryContract" class="panel-card">
      <div class="card-head">
        <h3>MemoryEntry 合同</h3>
        <span class="muted">对齐成熟智能体的长期规则层，区分通用底座、项目规则和本地实验规则</span>
      </div>
      <p v-if="!memoryContract.connected" class="contract-placeholder">等待后端接入 memory_contract</p>
      <div class="config-layer-grid">
        <div class="contract-block">
          <h4>启用状态</h4>
          <ul>
            <li><code>contract_version</code>: {{ memoryContract.contract_version || '-' }}</li>
            <li><code>active</code>: {{ memoryContract.active ? '已启用' : '未启用' }}</li>
            <li><code>layer_order</code>: {{ (memoryContract.layer_order || []).join(', ') || '-' }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>已加载层</h4>
          <ul v-if="(memoryContract.loaded_layers || []).length">
            <li v-for="layer in memoryContract.loaded_layers || []" :key="`${layer.name}-${layer.path}`">
              <strong>{{ layer.name }}</strong>
              <span class="path-line">{{ layer.path }}</span>
            </li>
          </ul>
          <p v-else class="empty-hint">当前未检测到任何分层记忆文件，主智能体仅按内置身份与能力合同运行。</p>
        </div>
        <div class="contract-block">
          <h4>预留层</h4>
          <ul v-if="(memoryContract.missing_layers || []).length">
            <li v-for="layer in memoryContract.missing_layers || []" :key="`${layer.name}-${layer.path}`">
              <strong>{{ layer.name }}</strong>
              <span class="path-line">{{ layer.path }}</span>
            </li>
          </ul>
          <p v-else class="empty-hint">当前所有预留层都已存在。</p>
        </div>
      </div>
      <div v-if="(memoryContract.memory_entries || []).length" class="provider-grid">
        <div v-for="entry in memoryContract.memory_entries || []" :key="entry.memory_id" class="provider-card">
          <div class="provider-title-row">
            <strong>{{ entry.memory_id }}</strong>
            <span class="status-badge online">{{ entry.scope || '-' }}</span>
          </div>
          <p class="provider-meta">
            <code>{{ entry.source || '-' }}</code>
            <span>confidence: {{ entry.confidence ?? '-' }}</span>
          </p>
          <p class="provider-endpoint">retrieval_reason: {{ entry.retrieval_reason || '-' }}</p>
        </div>
      </div>
    </div>

    <div v-if="subagentContract" class="panel-card">
      <div class="card-head">
        <h3>Subagent 注册能力面</h3>
        <span class="muted">角色化子智能体注册信息：描述、工具范围、模型偏好、触发条件</span>
      </div>
      <p class="section-desc">当前注册子智能体：{{ subagentContract.total_profiles || 0 }}</p>
      <div class="trace-status-grid">
        <div class="contract-block">
          <h4>Subagent Lane Recent Summary</h4>
          <ul>
            <li><code>state</code>: {{ subagentLaneRecentSummary.recordingState || 'unavailable' }}</li>
            <li><code>total_items</code>: {{ subagentLaneRecentSummary.totalItems || 0 }}</li>
            <li><code>latest_query_id</code>: {{ subagentLaneRecentSummary.latestQueryId || '-' }}</li>
            <li><code>latest_stage</code>: {{ subagentLaneRecentSummary.latestStage || '-' }}</li>
            <li>{{ subagentLaneRecentSummary.latestSummary || subagentLaneRecentSummary.reason || 'subagent recent summary 未就绪' }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>Recent Summary Items</h4>
          <ul>
            <li v-if="!subagentLaneRecentSummary.items.length">暂无 subagent recent summary</li>
            <li v-for="item in subagentLaneRecentSummary.items" :key="`${item.queryId}-${item.latestTimestamp}`">
              <code>{{ item.queryId }}</code> · {{ item.latestStage || '-' }} · {{ item.latestSummary || '无摘要' }}
            </li>
          </ul>
        </div>
      </div>
      <div class="provider-grid">
        <div v-for="item in subagentContract.profiles || []" :key="item.name" class="provider-card">
          <div class="provider-title-row">
            <strong>{{ item.name }}</strong>
            <span class="status-badge online">registered</span>
          </div>
          <p class="provider-meta">{{ item.description }}</p>
          <p class="provider-endpoint">context_policy: {{ item.context_policy || '-' }}</p>
          <p class="provider-endpoint">allowed_tools: {{ (item.allowed_tools || []).join(', ') || '-' }}</p>
          <p class="provider-endpoint">preferred_models: {{ (item.preferred_models || []).join(', ') || '-' }}</p>
          <p class="provider-endpoint">triggers: {{ (item.trigger_conditions || []).join(', ') || '-' }}</p>
        </div>
      </div>
    </div>

    <div v-if="hookContract" class="panel-card">
      <div class="card-head">
        <h3>Hooks / Permission 治理层</h3>
        <span class="muted">工具与收尾链路的框架治理钩子</span>
      </div>
      <div class="config-layer-grid">
        <div class="contract-block">
          <h4>已启用 Hook</h4>
          <ul>
            <li v-for="item in hookContract.enabled_hooks || []" :key="item"><code>{{ item }}</code></li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>高风险工具关键字</h4>
          <ul>
            <li v-for="item in hookContract.high_risk_tool_keywords || []" :key="item"><code>{{ item }}</code></li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>治理模型</h4>
          <ul>
            <li><code>{{ hookContract.governance_model || '-' }}</code></li>
          </ul>
        </div>
      </div>
    </div>

    <div v-if="commandContract" class="panel-card">
      <div class="card-head">
        <h3>Slash Command 层</h3>
        <span class="muted">{{ commandContract.contract_version || '框架级命令入口，统一暴露 doctor / plan / gaps / permissions / mcp / memory / model' }}</span>
      </div>
      <div class="config-layer-grid">
        <div class="contract-block">
          <h4>命令统计</h4>
          <ul>
            <li><code>total_commands</code>: {{ commandContract.total_commands || 0 }}</li>
            <li><code>framework_commands</code>: {{ (commandContract.framework_commands || []).length }}</li>
            <li><code>governance_commands</code>: {{ (commandContract.governance_commands || []).length }}</li>
            <li><code>command_definitions</code>: {{ (commandContract.command_definitions || []).length }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>框架命令</h4>
          <ul>
            <li v-for="item in commandContract.framework_commands || []" :key="item.id">
              <code>/{{ item.name }}</code> - {{ item.description }}
            </li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>Embedded SDK</h4>
          <ul>
            <li><code>{{ commandContract.embedded_sdk?.contract_version || '-' }}</code></li>
            <li v-for="item in commandContract.embedded_sdk?.methods || []" :key="item.method">
              <code>{{ item.method }}</code> - {{ item.stability || 'draft' }}
            </li>
          </ul>
        </div>
      </div>
      <div v-if="(commandContract.command_definitions || []).length" class="provider-grid">
        <div v-for="definition in commandContract.command_definitions || []" :key="definition.command_id || definition.name" class="provider-card">
          <div class="provider-title-row">
            <strong>CommandDefinition · {{ definition.name || '-' }}</strong>
            <span class="status-badge online">{{ definition.permission_level || 'read' }}</span>
          </div>
          <p class="provider-meta">
            <code>{{ definition.command_id || '-' }}</code>
            <span>{{ definition.execution_handler || '-' }}</span>
          </p>
          <div class="catalog-tags">
            <span v-for="capability in definition.required_capabilities || []" :key="`${definition.command_id}-${capability}`" class="capability-pill">
              {{ capability }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="embeddedRuntimeBoundaries.connected" class="panel-card">
      <div class="card-head">
        <h3>Embedded Runtime Boundaries</h3>
        <span class="muted">{{ embeddedRuntimeBoundaries.contract_version || 'Phase II：把 Embedded SDK / Harness 的 persistence、recovery 与 delegate preflight 收口成独立读模型' }}</span>
      </div>
      <div class="config-layer-grid">
        <div class="contract-block">
          <h4>Delegate Preflight</h4>
          <ul>
            <li><code>status</code>: {{ embeddedRuntimeBoundaries.delegate_preflight_status || '-' }}</li>
            <li><code>real_child_executor_ready</code>: {{ embeddedRuntimeBoundaries.real_child_executor_ready ? 'true' : 'false' }}</li>
            <li><code>facade_status</code>: {{ embeddedRuntimeBoundaries.facade_delegate_preflight_status || '-' }}</li>
            <li><code>executor_binding_status</code>: {{ embeddedRuntimeBoundaries.delegate_executor_binding_status || '-' }}</li>
            <li><code>next_step</code>: {{ embeddedRuntimeBoundaries.delegate_recommended_next_step || '-' }}</li>
            <li><code>gate_status</code>: {{ embeddedRuntimeBoundaries.delegate_gate_status || '-' }}</li>
            <li><code>route_status</code>: {{ embeddedRuntimeBoundaries.delegate_route_status || '-' }}</li>
            <li><code>binding_status</code>: {{ embeddedRuntimeBoundaries.delegate_binding_status || '-' }}</li>
            <li><code>stub_status</code>: {{ embeddedRuntimeBoundaries.delegate_stub_status || '-' }}</li>
            <li><code>execution_status</code>: {{ embeddedRuntimeBoundaries.delegate_execution_status || '-' }}</li>
            <li><code>merge_status</code>: {{ embeddedRuntimeBoundaries.delegate_merge_status || '-' }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>Volatile Runtime State</h4>
          <ul>
            <li v-if="!embeddedRuntimeBoundaries.volatile_runtime_state.length">暂无 volatile state 定义</li>
            <li v-for="item in embeddedRuntimeBoundaries.volatile_runtime_state" :key="item">
              <code>{{ item }}</code>
            </li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>Persistence Seams</h4>
          <ul>
            <li v-if="!embeddedRuntimeBoundaries.persistence_seams.length">暂无 persistence seam</li>
            <li v-for="item in embeddedRuntimeBoundaries.persistence_seams" :key="item">
              <code>{{ item }}</code>
            </li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>Workspace Backend</h4>
          <ul>
            <li><code>backend_kind</code>: {{ embeddedRuntimeBoundaries.workspace_backend.backend_kind || '-' }}</li>
            <li><code>backend_mode</code>: {{ embeddedRuntimeBoundaries.workspace_backend.backend_mode || '-' }}</li>
            <li><code>durable</code>: {{ embeddedRuntimeBoundaries.workspace_backend.durable ? 'true' : 'false' }}</li>
            <li><code>operation_fallback_allowed</code>: {{ embeddedRuntimeBoundaries.workspace_backend.operation_fallback_allowed ? 'true' : 'false' }}</li>
            <li><code>fallback_active</code>: {{ embeddedRuntimeBoundaries.workspace_backend.fallback_active ? 'true' : 'false' }}</li>
            <li>{{ embeddedRuntimeBoundaries.workspace_backend.fallback_reason || embeddedRuntimeBoundaries.workspace_backend.last_error || 'workspace backend 正常' }}</li>
          </ul>
        </div>
      </div>
      <div class="provider-grid">
        <div class="provider-card">
          <div class="provider-title-row">
            <strong>Recovery Entrypoints</strong>
            <span class="status-badge" :class="{ online: embeddedRuntimeBoundaries.recovery_entrypoints.length, offline: !embeddedRuntimeBoundaries.recovery_entrypoints.length }">
              {{ embeddedRuntimeBoundaries.recovery_entrypoints.length || 0 }}
            </span>
          </div>
          <ul>
            <li v-if="!embeddedRuntimeBoundaries.recovery_entrypoints.length">暂无 recovery 入口</li>
            <li v-for="entry in embeddedRuntimeBoundaries.recovery_entrypoints" :key="`${entry.method}-${entry.mode || 'default'}`">
              <code>{{ entry.method }}</code>
              <span v-if="entry.mode"> · {{ entry.mode }}</span>
              <span v-if="entry.recovery_scope"> · {{ entry.recovery_scope }}</span>
            </li>
          </ul>
        </div>
        <div class="provider-card">
          <div class="provider-title-row">
            <strong>Promotion Requirements</strong>
            <span class="status-badge offline">{{ embeddedRuntimeBoundaries.delegate_promotion_requirements.length }}</span>
          </div>
          <ul>
            <li v-if="!embeddedRuntimeBoundaries.delegate_promotion_requirements.length">暂无 promotion requirements</li>
            <li v-for="item in embeddedRuntimeBoundaries.delegate_promotion_requirements" :key="item">
              <code>{{ item }}</code>
            </li>
          </ul>
        </div>
        <div class="provider-card">
          <div class="provider-title-row">
            <strong>Executor Binding Blockers</strong>
            <span class="status-badge offline">{{ embeddedRuntimeBoundaries.delegate_executor_binding_blockers.length }}</span>
          </div>
          <ul>
            <li v-if="!embeddedRuntimeBoundaries.delegate_executor_binding_blockers.length">暂无 executor binding blockers</li>
            <li v-for="item in embeddedRuntimeBoundaries.delegate_executor_binding_blockers" :key="item">
              <code>{{ item }}</code>
            </li>
          </ul>
        </div>
        <div class="provider-card">
          <div class="provider-title-row">
            <strong>Routing Seam</strong>
            <span class="status-badge" :class="{ online: embeddedRuntimeBoundaries.delegate_route_status === 'routed', offline: embeddedRuntimeBoundaries.delegate_route_status !== 'routed' }">
              {{ embeddedRuntimeBoundaries.delegate_route_status || '-' }}
            </span>
          </div>
          <ul>
            <li><code>executor_path</code>: {{ embeddedRuntimeBoundaries.delegate_route_executor_path || '-' }}</li>
            <li><code>route_reason</code>: {{ embeddedRuntimeBoundaries.delegate_route_reason || '-' }}</li>
            <li><code>recommended_action</code>: {{ embeddedRuntimeBoundaries.delegate_route_recommended_action || '-' }}</li>
          </ul>
        </div>
        <div class="provider-card">
          <div class="provider-title-row">
            <strong>Binding Seam</strong>
            <span class="status-badge" :class="{ online: embeddedRuntimeBoundaries.delegate_binding_status === 'bound', offline: embeddedRuntimeBoundaries.delegate_binding_status !== 'bound' }">
              {{ embeddedRuntimeBoundaries.delegate_binding_status || '-' }}
            </span>
          </div>
          <ul>
            <li><code>binding_id</code>: {{ embeddedRuntimeBoundaries.delegate_binding_id || '-' }}</li>
            <li><code>binding_reason</code>: {{ embeddedRuntimeBoundaries.delegate_binding_reason || '-' }}</li>
            <li><code>recommended_action</code>: {{ embeddedRuntimeBoundaries.delegate_binding_recommended_action || '-' }}</li>
          </ul>
        </div>
        <div class="provider-card">
          <div class="provider-title-row">
            <strong>Executor Stub</strong>
            <span class="status-badge" :class="{ online: embeddedRuntimeBoundaries.delegate_stub_status === 'recorded', offline: embeddedRuntimeBoundaries.delegate_stub_status !== 'recorded' }">
              {{ embeddedRuntimeBoundaries.delegate_stub_status || '-' }}
            </span>
          </div>
          <ul>
            <li><code>binding_id</code>: {{ embeddedRuntimeBoundaries.delegate_stub_binding_id || '-' }}</li>
            <li><code>executor_path</code>: {{ embeddedRuntimeBoundaries.delegate_stub_executor_path || '-' }}</li>
            <li><code>stub_reason</code>: {{ embeddedRuntimeBoundaries.delegate_stub_reason || '-' }}</li>
            <li><code>recommended_action</code>: {{ embeddedRuntimeBoundaries.delegate_stub_recommended_action || '-' }}</li>
          </ul>
        </div>
        <div class="provider-card">
          <div class="provider-title-row">
            <strong>Executor Skeleton</strong>
            <span class="status-badge" :class="{ online: embeddedRuntimeBoundaries.delegate_execution_status === 'executed', offline: embeddedRuntimeBoundaries.delegate_execution_status !== 'executed' }">
              {{ embeddedRuntimeBoundaries.delegate_execution_status || '-' }}
            </span>
          </div>
          <ul>
            <li><code>binding_id</code>: {{ embeddedRuntimeBoundaries.delegate_execution_binding_id || '-' }}</li>
            <li><code>executor_path</code>: {{ embeddedRuntimeBoundaries.delegate_execution_executor_path || '-' }}</li>
            <li><code>execution_mode</code>: {{ embeddedRuntimeBoundaries.delegate_execution_mode || '-' }}</li>
            <li><code>output_summary</code>: {{ embeddedRuntimeBoundaries.delegate_execution_output_summary || '-' }}</li>
            <li><code>output_text</code>: {{ embeddedRuntimeBoundaries.delegate_execution_output_text || '-' }}</li>
            <li><code>artifact_id</code>: {{ embeddedRuntimeBoundaries.delegate_execution_output_envelope.artifactId || '-' }}</li>
            <li><code>merge_hint</code>: {{ embeddedRuntimeBoundaries.delegate_execution_output_envelope.mergeHint || '-' }}</li>
            <li><code>merge_ready</code>: {{ embeddedRuntimeBoundaries.delegate_execution_output_envelope.mergeReady ? 'true' : 'false' }}</li>
            <li><code>section_count</code>: {{ embeddedRuntimeBoundaries.delegate_execution_output_envelope.sectionCount || 0 }}</li>
            <li><code>recommended_action</code>: {{ embeddedRuntimeBoundaries.delegate_execution_recommended_action || '-' }}</li>
          </ul>
        </div>
        <div class="provider-card">
          <div class="provider-title-row">
            <strong>Parent Merge</strong>
            <span class="status-badge" :class="{ online: embeddedRuntimeBoundaries.delegate_merge_status === 'merged', offline: embeddedRuntimeBoundaries.delegate_merge_status !== 'merged' }">
              {{ embeddedRuntimeBoundaries.delegate_merge_status || '-' }}
            </span>
          </div>
          <ul>
            <li><code>merge_ready</code>: {{ embeddedRuntimeBoundaries.delegate_merge_ready ? 'true' : 'false' }}</li>
            <li><code>merge_strategy</code>: {{ embeddedRuntimeBoundaries.delegate_merge_strategy || '-' }}</li>
            <li><code>merged_summary</code>: {{ embeddedRuntimeBoundaries.delegate_merged_summary || '-' }}</li>
            <li><code>artifact_id</code>: {{ embeddedRuntimeBoundaries.delegate_merge_artifact_ref.artifactId || '-' }}</li>
            <li><code>section_count</code>: {{ embeddedRuntimeBoundaries.delegate_merge_section_count || 0 }}</li>
          </ul>
        </div>
        <ChildExecutorOutputWorkspace
          :replay="childExecutorOutputReplay"
          :summary="childExecutorOutputSummary"
          :merged-semantics="childExecutorMergedSemantics"
        />
        <div class="provider-card">
          <div class="provider-title-row">
            <strong>Current Non-Goals</strong>
            <span class="status-badge offline">{{ embeddedRuntimeBoundaries.delegate_non_goals.length }}</span>
          </div>
          <ul>
            <li v-if="!embeddedRuntimeBoundaries.delegate_non_goals.length">暂无 non-goals</li>
            <li v-for="item in embeddedRuntimeBoundaries.delegate_non_goals" :key="item">
              <code>{{ item }}</code>
            </li>
          </ul>
        </div>
        <div class="provider-card">
          <div class="provider-title-row">
            <strong>Current Scope</strong>
            <span class="status-badge online">{{ embeddedRuntimeBoundaries.delegate_current_scope.length }}</span>
          </div>
          <ul>
            <li v-if="!embeddedRuntimeBoundaries.delegate_current_scope.length">暂无 current scope</li>
            <li v-for="item in embeddedRuntimeBoundaries.delegate_current_scope" :key="item">
              <code>{{ item }}</code>
            </li>
          </ul>
        </div>
        <div class="provider-card">
          <div class="provider-title-row">
            <strong>Approved Reference Slices</strong>
            <span class="status-badge online">{{ embeddedRuntimeBoundaries.approved_reference_slices.length }}</span>
          </div>
          <div v-if="!embeddedRuntimeBoundaries.approved_reference_slices.length" class="reference-slice-empty">
            暂无 reference slices
          </div>
          <div
            v-for="entry in embeddedRuntimeBoundaries.approved_reference_slices"
            :key="`${entry.source}-${entry.role}`"
            class="reference-slice-card"
          >
            <div class="provider-title-row">
              <strong><code>{{ entry.source || '-' }}</code></strong>
              <span class="status-badge online">{{ entry.role_label || entry.role || '-' }}</span>
            </div>
            <p class="provider-meta">
              <span v-if="entry.role_description">{{ entry.role_description }}</span>
              <span>参考切面数: {{ entry.slices?.length || 0 }}</span>
            </p>
            <ul class="reference-slice-list">
              <li v-for="slice in entry.slices || []" :key="`${entry.source}-${slice}`">
                <code>{{ slice }}</code>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <GovernanceRecentSnapshotCommandsCard
      :items="recentSnapshotCommands"
      :copied-command-text="copiedSnapshotCommandText"
      :copied-command-display="copiedSnapshotCommandDisplay"
      @copy-command="copySnapshotCommand"
    />

    <div v-if="configLayers" class="panel-card">
      <div class="card-head">
        <h3>配置分层</h3>
        <span class="muted">区分默认值、可编辑本地覆写和当前生效值，便于后续对齐企业级 settings surface</span>
      </div>
      <div class="config-layer-grid">
        <div class="contract-block">
          <h4>默认值（.env / 后端默认）</h4>
          <ul>
            <li><code>auth_mode</code>: {{ configLayers.defaults?.auth_mode || '-' }}</li>
            <li><code>default_model</code>: {{ configLayers.defaults?.default_model || '-' }}</li>
            <li><code>enabled_providers</code>: {{ formatProviderConfig(configLayers.defaults?.enabled_providers) }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>本地覆写（runtime_surface.json）</h4>
          <ul>
            <li><code>path</code>: {{ configLayers.override_path || '-' }}</li>
            <li><code>auth_mode</code>: {{ configLayers.overrides?.auth_mode || '未覆写' }}</li>
            <li><code>default_model</code>: {{ configLayers.overrides?.default_model || '未覆写' }}</li>
            <li><code>enabled_providers</code>: {{ formatProviderConfig(configLayers.overrides?.enabled_providers, true) }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>当前生效值</h4>
          <ul>
            <li><code>auth_mode</code>: {{ configLayers.effective?.auth_mode || '-' }}</li>
            <li><code>default_model</code>: {{ configLayers.effective?.default_model || '-' }}</li>
            <li><code>enabled_providers</code>: {{ formatProviderConfig(configLayers.provider_resolution?.enabled_provider_ids || []) }}</li>
            <li><code>editable_keys</code>: {{ (configLayers.editable_keys || []).join(', ') || '-' }}</li>
          </ul>
        </div>
      </div>
    </div>

    <div v-if="profile" class="panel-card">
      <div class="card-head">
        <h3>最小运行时配置</h3>
        <span class="muted">仅开放对 demo 安全的配置项：默认模型与鉴权模式</span>
      </div>
      <div class="editable-grid">
        <label class="field-block">
          <span>默认模型</span>
          <select v-model="editableDefaultModel" class="field-select">
            <option v-for="model in models" :key="model.name" :value="model.name">
              {{ model.display_name || model.name }}
            </option>
          </select>
        </label>
        <label class="field-block">
          <span>鉴权模式</span>
          <select v-model="editableAuthMode" class="field-select">
            <option value="demo_guest">demo_guest</option>
            <option value="business_auth">business_auth</option>
          </select>
        </label>
      </div>
      <div class="provider-toggle-grid">
        <label v-for="provider in providers" :key="provider.provider_id" class="provider-toggle">
          <input
            :checked="editableEnabledProviders.includes(provider.provider_id)"
            type="checkbox"
            @change="toggleProvider(provider.provider_id, $event.target.checked)"
          />
          <div>
            <strong>{{ provider.display_name }}</strong>
            <div class="provider-toggle-meta">
              <span><code>{{ provider.provider_id }}</code></span>
              <span>{{ provider.enabled_source === 'override' ? '本地覆写' : '默认全启用' }}</span>
            </div>
          </div>
        </label>
      </div>
      <div class="edit-actions">
        <button class="secondary-btn" :disabled="saving" @click="saveProfile">
          {{ saving ? '保存中...' : '保存运行时配置' }}
        </button>
        <span v-if="saveMessage" class="save-message">{{ saveMessage }}</span>
      </div>
      <p class="muted helper-text">说明：provider 启停属于本地运行时治理面。若未显式覆写 provider 列表，则默认视为“全部启用”。</p>
    </div>

    <div v-if="embeddedRuntimeBootstrap.connected" class="panel-card">
      <div class="card-head">
        <h3>Embedded Runtime Bootstrap</h3>
        <span class="muted">{{ embeddedRuntimeBootstrap.contractVersion || '默认 runtime bootstrap 控制面' }}</span>
      </div>
      <div class="summary-grid runtime-contract-grid">
        <div class="summary-card">
          <span class="summary-label">当前 workspace mode</span>
          <strong>{{ embeddedRuntimeBootstrap.defaultRuntimeProfile.embedded_workspace_store_mode || '-' }}</strong>
          <small class="summary-note">{{ embeddedRuntimeBootstrap.defaultRuntimeProfile.default_runtime_mode || '-' }}</small>
        </div>
        <div class="summary-card">
          <span class="summary-label">恢复姿态</span>
          <strong>{{ embeddedRuntimeBootstrap.defaultRuntimeProfile.recovery_posture || '-' }}</strong>
          <small class="summary-note">backend: {{ embeddedRuntimeBootstrap.workspaceBackend.backend_kind || '-' }}</small>
        </div>
        <div class="summary-card">
          <span class="summary-label">真实校验</span>
          <strong>{{ embeddedRuntimeBootstrap.bootstrapRecoveryValidation.validation_status || '-' }}</strong>
          <small class="summary-note">
            {{ embeddedRuntimeBootstrap.bootstrapRecoveryValidation.workspace_backend_mode || embeddedRuntimeBootstrap.workspaceBackend.backend_mode || '-' }}
          </small>
        </div>
        <div class="summary-card">
          <span class="summary-label">最近治理快照</span>
          <strong>{{ embeddedRuntimeBootstrapUpdateResult.timelineSnapshotId || '-' }}</strong>
          <small class="summary-note">{{ embeddedRuntimeBootstrapUpdateResult.timelineEventLabel || '未产生新的 runtime control 事件' }}</small>
        </div>
      </div>
      <div class="editable-grid">
        <label class="field-block">
          <span>embedded_workspace_store_mode</span>
          <select
            v-model="editableEmbeddedWorkspaceStoreMode"
            class="field-select"
            data-testid="embedded-runtime-bootstrap-mode"
          >
            <option value="memory_only">memory_only</option>
            <option value="prefer_sql_with_fallback">prefer_sql_with_fallback</option>
            <option value="strict_sql">strict_sql</option>
          </select>
        </label>
      </div>
      <div class="edit-actions">
        <button
          class="secondary-btn"
          :disabled="bootstrapSaving"
          data-testid="embedded-runtime-bootstrap-save"
          @click="saveEmbeddedRuntimeBootstrap"
        >
          {{ bootstrapSaving ? '切换中...' : '应用 Bootstrap 切换' }}
        </button>
        <span v-if="bootstrapSaveMessage" class="save-message">{{ bootstrapSaveMessage }}</span>
      </div>
      <div class="trace-status-grid">
        <div class="contract-block">
          <h4>Bootstrap Recovery Validation</h4>
          <ul>
            <li><code>validation_status</code>: {{ embeddedRuntimeBootstrap.bootstrapRecoveryValidation.validation_status || '-' }}</li>
            <li><code>actual_recoverable</code>: {{ embeddedRuntimeBootstrap.bootstrapRecoveryValidation.actual_recoverable ? 'true' : 'false' }}</li>
            <li><code>expected_recoverable</code>: {{ embeddedRuntimeBootstrap.bootstrapRecoveryValidation.expected_recoverable ? 'true' : 'false' }}</li>
            <li><code>tool_recovery_reason</code>: {{ embeddedRuntimeBootstrap.bootstrapRecoveryValidation.tool_recovery_reason || '-' }}</li>
            <li><code>loop_recovery_reason</code>: {{ embeddedRuntimeBootstrap.bootstrapRecoveryValidation.loop_recovery_reason || '-' }}</li>
          </ul>
        </div>
        <div class="contract-block">
          <h4>Latest Bootstrap Update</h4>
          <ul>
            <li><code>update_status</code>: {{ embeddedRuntimeBootstrapUpdateResult.updateStatus || '-' }}</li>
            <li><code>runtime_mode</code>: {{ embeddedRuntimeBootstrapUpdateResult.currentRuntimeMode || '-' }}</li>
            <li><code>recovery_posture</code>: {{ embeddedRuntimeBootstrapUpdateResult.currentRecoveryPosture || '-' }}</li>
            <li><code>workspace_backend</code>: {{ embeddedRuntimeBootstrapUpdateResult.currentWorkspaceBackendMode || '-' }}</li>
            <li><code>snapshot_id</code>: {{ embeddedRuntimeBootstrapUpdateResult.timelineSnapshotId || '-' }}</li>
            <li><code>summary</code>: {{ embeddedRuntimeBootstrapUpdateResult.summary || '-' }}</li>
          </ul>
        </div>
      </div>
      <p class="muted helper-text">说明：这条切换会走 dedicated bootstrap control plane；当前有会话上下文时，会同时写入 runtime control 治理事件。</p>
    </div>

    <div v-if="models.length" class="panel-card">
      <div class="card-head">
        <h3>模型目录</h3>
        <span class="muted">由后端动态下发，不再写死在前端</span>
      </div>
      <div class="model-list">
        <div v-for="model in models" :key="model.name" class="model-item">
          <div class="model-title-row">
            <strong>{{ model.display_name || model.name }}</strong>
            <span class="status-badge" :class="{ online: model.available, offline: !model.available }">
              {{ model.available ? 'available' : 'unavailable' }}
            </span>
          </div>
          <div class="model-meta">
            <span><code>{{ model.name }}</code></span>
            <span>{{ model.provider_label || model.provider }}</span>
            <span>{{ model.type }}</span>
            <span v-if="model.has_reasoning">reasoning</span>
            <span v-if="model.is_default">default</span>
          </div>
          <div class="model-submeta">
            <span v-if="model.name !== model.actual_model">alias_of: {{ model.actual_model }}</span>
            <span v-if="model.actual_model">actual: {{ model.actual_model }}</span>
            <span v-if="model.base_url">base_url: {{ model.base_url }}</span>
            <span v-if="model.source">source: {{ model.source }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="providers.length" class="panel-card">
      <div class="card-head">
        <h3>Provider 目录</h3>
        <span class="muted">用于后续接入更多云模型、本地模型和 OpenAI 兼容接口</span>
      </div>
      <div class="provider-grid">
        <div v-for="provider in providers" :key="provider.provider_id" class="provider-card">
          <div class="provider-title-row">
            <strong>{{ provider.display_name }}</strong>
            <span class="status-badge" :class="{ online: provider.configured, offline: !provider.configured }">
              {{ provider.configured ? 'configured' : 'not configured' }}
            </span>
          </div>
          <p class="provider-meta">
            <code>{{ provider.provider_id }}</code>
            <span>{{ provider.type }}</span>
            <span>{{ provider.enabled ? 'enabled' : 'disabled' }}</span>
            <span>{{ provider.enabled_source === 'override' ? 'override' : 'default' }}</span>
            <span>configured_models: {{ provider.configured_model_count || 0 }}</span>
            <span>available_models: {{ provider.available_model_count || 0 }}</span>
            <span>total_models: {{ provider.total_model_count || 0 }}</span>
          </p>
          <p v-if="provider.base_url" class="provider-endpoint">{{ provider.base_url }}</p>
          <p v-if="provider.model_sources?.length" class="provider-endpoint">sources: {{ provider.model_sources.join(', ') }}</p>
          <p v-if="provider.actual_models?.length" class="provider-endpoint">actual_models: {{ provider.actual_models.join(', ') }}</p>
          <div class="catalog-tags">
            <span v-for="modelName in provider.models || []" :key="`${provider.provider_id}-${modelName}`" class="capability-pill">
              {{ modelName }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { runtimeSurfaceApi } from '../api'
import AdapterExternalPilotFailureSummary from './AdapterExternalPilotFailureSummary.vue'
import AdapterHealthCard from './AdapterHealthCard.vue'
import ChildExecutorOutputWorkspace from './ChildExecutorOutputWorkspace.vue'
import GovernanceRecentSnapshotCommandsCard from './GovernanceRecentSnapshotCommandsCard.vue'
import {
  buildMainChatQueryDetailContract,
  buildMainChatQueryHistoryContract,
} from '../services/governanceViewInterpretation'
import { buildSnapshotCommandDescriptor } from '../services/governanceSnapshotCommands'
import { formatAuditEvent, formatEmbeddedRuntimeBootstrapSummary } from '../services/governanceFormatting'
import { normalizeSubagentLaneRecentSummaryContract } from '../services/subagentLaneRecentSummary'
import { useRecentSnapshotCommands } from '../composables/useRecentSnapshotCommands'
import { useConversationStore } from '../stores/conversation'
import { usePlannerStore } from '../stores/planner'
import { useSettingsStore } from '../stores/settings'

const router = useRouter()
const route = useRoute()
const profile = ref(null)
const loading = ref(false)
const saving = ref(false)
const bootstrapSaving = ref(false)
const error = ref('')
const saveMessage = ref('')
const bootstrapSaveMessage = ref('')
const adapterPilotRunning = ref(false)
const adapterPilotResult = ref(null)
const adapterPrecheckRunning = ref(false)
const adapterPrecheckResult = ref(null)
const adapterExternalPilotRunning = ref(false)
const adapterExternalPilotResult = ref(null)
const mainChatQueryHistory = ref(buildMainChatQueryHistoryContract())
const mainChatQueryHistoryLoading = ref(false)
const subagentLaneRecentSummary = ref(normalizeSubagentLaneRecentSummaryContract())
const childExecutorOutputReplay = ref(buildChildExecutorOutputReplayContract())
const childExecutorOutputSummary = ref(buildChildExecutorOutputSummaryContract())
const childExecutorMergedSemantics = ref(buildChildExecutorMergedSemanticsContract())
const editableAuthMode = ref('demo_guest')
const editableDefaultModel = ref('')
const editableEnabledProviders = ref([])
const editableEmbeddedWorkspaceStoreMode = ref('strict_sql')
const embeddedRuntimeBootstrapUpdateResult = ref(buildEmbeddedRuntimeBootstrapUpdateResult())
const conversationStore = useConversationStore()
const plannerStore = usePlannerStore()
const settingsStore = useSettingsStore()
const {
  recentSnapshotCommands,
  copiedCommandText: copiedSnapshotCommandText,
  copiedCommandDisplay: copiedSnapshotCommandDisplay,
  refreshRecentSnapshotCommands,
  recordRecentSnapshotCommand,
  copyRecentSnapshotCommand,
} = useRecentSnapshotCommands()

const models = computed(() => profile.value?.models || [])
const providers = computed(() => profile.value?.providers || [])
const currentConversationId = computed(() => normalizeNumericId(conversationStore.currentConversation?.id))
const currentPlanId = computed(() => normalizeNumericId(plannerStore.currentPlan?.id))
const currentPlanItemId = computed(() => normalizeNumericId(plannerStore.currentPlan?.active_item_id))
const activeMainChatQueryId = computed(() => String(route.query?.governance_query_id || '').trim())
const runtimeCore = computed(() => buildRuntimeCoreContract(profile.value?.runtime_core))
const runRecovery = computed(() => buildRunRecoveryContract(profile.value?.run_recovery))
const governanceOverview = computed(() => buildGovernanceOverviewContract(profile.value?.governance_overview))
const mainChatTraceOverview = computed(() => buildMainChatTraceOverview(profile.value?.main_chat_trace_overview))
const mainChatQueryDetail = computed(() => buildMainChatQueryDetailContract(profile.value?.main_chat_query_detail))
const toolRuntime = computed(() => buildToolRuntimeContract(profile.value?.tool_runtime))
const mcpRuntime = computed(() => buildMcpRuntimeContract(profile.value?.mcp_runtime))
const adapterHealth = computed(() => buildAdapterHealthContract(profile.value?.adapter_health))
const activeAdapterFailureType = computed(() => {
  const filter = String(route.query?.governance_filter || '').trim()
  const severity = String(route.query?.governance_severity || '').trim()
  if (filter !== 'framework_adapter' || severity !== 'warning') {
    return ''
  }
  return String(route.query?.governance_error_type || '').trim()
})
const contractSnapshot = computed(() => buildContractSnapshot(profile.value?.contract_snapshot))
const runtimeContractGate = computed(() => buildRuntimeContractGate(profile.value?.runtime_contract_gate))
const capabilityContract = computed(() => profile.value?.capability_contract || null)
const skillContract = computed(() => buildSkillContract(profile.value?.skill_contract))
const memoryContract = computed(() => buildMemoryContract(profile.value?.memory_contract))
const subagentContract = computed(() => profile.value?.subagent_contract || null)
const hookContract = computed(() => profile.value?.hook_contract || null)
const commandContract = computed(() => profile.value?.command_contract || null)
const embeddedRuntimeBootstrap = computed(() => buildEmbeddedRuntimeBootstrapContract(profile.value?.embedded_runtime_bootstrap))
const embeddedRuntimeBoundaries = computed(() => buildEmbeddedRuntimeBoundariesContract(profile.value?.embedded_runtime_boundaries))
const currentParentRunId = computed(() => String(runtimeCore.value?.run_id || '').trim())
const configLayers = computed(() => profile.value?.config_layers || null)
const authModeDescription = computed(() => {
  const contract = profile.value?.auth_mode_contract || {}
  return profile.value?.auth_mode === 'business_auth'
    ? (contract.business_auth_description || '')
    : (contract.demo_guest_description || '')
})

async function loadProfile() {
  loading.value = true
  error.value = ''
  try {
    const response = await runtimeSurfaceApi.getProfile(buildRuntimeProfileContextParams())
    profile.value = response.data || null
    editableAuthMode.value = profile.value?.auth_mode || 'demo_guest'
    editableDefaultModel.value = profile.value?.default_model || models.value[0]?.name || ''
    editableEnabledProviders.value = [...(profile.value?.config_layers?.provider_resolution?.enabled_provider_ids || [])]
    editableEmbeddedWorkspaceStoreMode.value = profile.value?.embedded_runtime_bootstrap?.default_runtime_profile?.embedded_workspace_store_mode || 'strict_sql'
    await loadMainChatQueryHistory()
    await loadSubagentLaneRecentSummary()
    await loadChildExecutorOutputReplay()
    await loadChildExecutorOutputSummary()
    await loadChildExecutorMergedSemantics()
  } catch (err) {
    error.value = err?.response?.data?.detail || err?.message || '加载运行时信息失败'
  } finally {
    loading.value = false
  }
}

async function loadSubagentLaneRecentSummary() {
  if (currentConversationId.value === null) {
    subagentLaneRecentSummary.value = normalizeSubagentLaneRecentSummaryContract()
    return
  }
  try {
    const response = await runtimeSurfaceApi.getSubagentLaneRecentSummary({
      conversation_id: currentConversationId.value,
      ...(currentPlanId.value !== null ? { plan_id: currentPlanId.value } : {}),
      ...(currentPlanItemId.value !== null ? { item_id: currentPlanItemId.value } : {}),
    })
    subagentLaneRecentSummary.value = normalizeSubagentLaneRecentSummaryContract(response.data)
  } catch (_err) {
    subagentLaneRecentSummary.value = normalizeSubagentLaneRecentSummaryContract()
  }
}

async function loadChildExecutorOutputReplay() {
  const parentRunId = currentParentRunId.value
  if (!parentRunId) {
    childExecutorOutputReplay.value = buildChildExecutorOutputReplayContract()
    return
  }
  try {
    const response = await runtimeSurfaceApi.getChildExecutorOutputReplay({
      parent_run_id: parentRunId
    })
    childExecutorOutputReplay.value = buildChildExecutorOutputReplayContract(response.data)
  } catch (_err) {
    childExecutorOutputReplay.value = buildChildExecutorOutputReplayContract()
  }
}

async function loadChildExecutorOutputSummary() {
  const parentRunId = currentParentRunId.value
  if (!parentRunId) {
    childExecutorOutputSummary.value = buildChildExecutorOutputSummaryContract()
    return
  }
  try {
    const response = await runtimeSurfaceApi.getChildExecutorOutputSummary({
      parent_run_id: parentRunId
    })
    childExecutorOutputSummary.value = buildChildExecutorOutputSummaryContract(response.data)
  } catch (_err) {
    childExecutorOutputSummary.value = buildChildExecutorOutputSummaryContract()
  }
}

async function loadChildExecutorMergedSemantics() {
  const parentRunId = currentParentRunId.value
  if (!parentRunId) {
    childExecutorMergedSemantics.value = buildChildExecutorMergedSemanticsContract()
    return
  }
  try {
    const response = await runtimeSurfaceApi.getChildExecutorMergedSemantics({
      parent_run_id: parentRunId
    })
    childExecutorMergedSemantics.value = buildChildExecutorMergedSemanticsContract(response.data)
  } catch (_err) {
    childExecutorMergedSemantics.value = buildChildExecutorMergedSemanticsContract()
  }
}

function buildRuntimeProfileContextParams() {
  return {
    ...(currentConversationId.value !== null ? { conversation_id: currentConversationId.value } : {}),
    ...(currentPlanId.value !== null ? { plan_id: currentPlanId.value } : {}),
    ...(currentPlanItemId.value !== null ? { item_id: currentPlanItemId.value } : {}),
    ...(activeMainChatQueryId.value ? { query_id: activeMainChatQueryId.value } : {}),
    ...(String(route.query?.run_id || '').trim() ? { run_id: String(route.query.run_id).trim() } : {}),
    ...(String(route.query?.parent_run_id || '').trim() ? { parent_run_id: String(route.query.parent_run_id).trim() } : {}),
    ...(String(route.query?.child_run_id || '').trim() ? { child_run_id: String(route.query.child_run_id).trim() } : {}),
    ...(String(route.query?.scheduler_run_id || '').trim() ? { scheduler_run_id: String(route.query.scheduler_run_id).trim() } : {}),
  }
}

async function loadMainChatQueryHistory(page = 1, append = false) {
  if (currentConversationId.value === null) {
    mainChatQueryHistory.value = buildMainChatQueryHistoryContract()
    return
  }
  mainChatQueryHistoryLoading.value = true
  try {
    const response = await runtimeSurfaceApi.getMainChatQueryHistory({
      conversation_id: currentConversationId.value,
      ...(currentPlanId.value !== null ? { plan_id: currentPlanId.value } : {}),
      ...(currentPlanItemId.value !== null ? { item_id: currentPlanItemId.value } : {}),
      page,
      page_size: 5,
    })
    const normalized = buildMainChatQueryHistoryContract(response.data)
    mainChatQueryHistory.value = append
      ? {
        ...normalized,
        items: [...mainChatQueryHistory.value.items, ...normalized.items],
      }
      : normalized
  } catch (_err) {
    if (!append) {
      mainChatQueryHistory.value = buildMainChatQueryHistoryContract()
    }
  } finally {
    mainChatQueryHistoryLoading.value = false
  }
}

async function loadMoreMainChatQueryHistory() {
  if (!mainChatQueryHistory.value.hasMore || mainChatQueryHistoryLoading.value) {
    return
  }
  const nextPage = Number(mainChatQueryHistory.value.page || 1) + 1
  await loadMainChatQueryHistory(nextPage, true)
}

async function saveProfile() {
  if (!editableDefaultModel.value) {
    saveMessage.value = '请先选择默认模型'
    return
  }
  saving.value = true
  error.value = ''
  saveMessage.value = ''
  try {
    const response = await runtimeSurfaceApi.updateProfile({
      auth_mode: editableAuthMode.value,
      default_model: editableDefaultModel.value,
      enabled_providers: editableEnabledProviders.value
    })
    profile.value = response.data || null
    editableAuthMode.value = profile.value?.auth_mode || editableAuthMode.value
    editableDefaultModel.value = profile.value?.default_model || editableDefaultModel.value
    editableEnabledProviders.value = [...(profile.value?.config_layers?.provider_resolution?.enabled_provider_ids || editableEnabledProviders.value)]
    saveMessage.value = '运行时配置已保存'
  } catch (err) {
    error.value = err?.response?.data?.detail || err?.message || '保存运行时信息失败'
  } finally {
    saving.value = false
  }
}

async function saveEmbeddedRuntimeBootstrap() {
  if (!editableEmbeddedWorkspaceStoreMode.value) {
    bootstrapSaveMessage.value = '请先选择 workspace mode'
    return
  }
  bootstrapSaving.value = true
  error.value = ''
  bootstrapSaveMessage.value = ''
  try {
    const payload = {
      embedded_workspace_store_mode: editableEmbeddedWorkspaceStoreMode.value,
      ...(currentConversationId.value !== null ? { conversation_id: currentConversationId.value } : {}),
    }
    const response = await runtimeSurfaceApi.updateEmbeddedRuntimeBootstrap(payload)
    const data = normalizeContractObject(response.data)
    embeddedRuntimeBootstrapUpdateResult.value = buildEmbeddedRuntimeBootstrapUpdateResult(data)
    const snapshotId = String(data.timeline_recording?.snapshot_ref?.snapshot_id || '').trim()
    if (snapshotId) {
      const defaultRuntimeProfile = normalizeContractObject(data.default_runtime_profile)
      const bootstrapRecoveryValidation = normalizeContractObject(data.bootstrap_recovery_validation)
      const snapshotDescriptor = buildSnapshotCommandDescriptor(snapshotId, 'runtime_control', {
        eventType: String(data.timeline_recording?.snapshot_ref?.event_type || '').trim(),
        eventLabel: formatAuditEvent(String(data.timeline_recording?.snapshot_ref?.event_type || '').trim()),
        summary: formatEmbeddedRuntimeBootstrapSummary({
          requested_embedded_workspace_store_mode: String(
            data.requested_embedded_workspace_store_mode ||
            defaultRuntimeProfile.embedded_workspace_store_mode ||
            ''
          ).trim(),
          current_runtime_mode: String(data.post_update_verification?.current_runtime_mode || '').trim(),
          current_recovery_posture: String(data.post_update_verification?.current_recovery_posture || '').trim(),
          current_workspace_backend_mode: String(data.post_update_verification?.current_workspace_backend_mode || '').trim(),
          bootstrap_recovery_validation_status: String(bootstrapRecoveryValidation.validation_status || '').trim(),
        }),
      })
      recordRecentSnapshotCommand(snapshotDescriptor)
    }
    bootstrapSaveMessage.value = data.timeline_recording?.snapshot_ref?.snapshot_id
      ? `Bootstrap 已切换并写入治理快照 ${data.timeline_recording.snapshot_ref.snapshot_id}`
      : 'Bootstrap 已切换'
    await loadProfile()
    if (currentConversationId.value !== null) {
      await plannerStore.loadPlans({ conversationId: currentConversationId.value })
    }
  } catch (err) {
    error.value = err?.response?.data?.detail || err?.message || '更新 embedded runtime bootstrap 失败'
  } finally {
    bootstrapSaving.value = false
  }
}

async function runAdapterPrecheck(adapter) {
  const adapterId = String(adapter?.adapter_id || '').trim()
  if (!adapterId) return

  adapterPrecheckRunning.value = true
  error.value = ''
  try {
    const conversationId = currentConversationId.value
    const planId = currentPlanId.value
    const planItemId = currentPlanItemId.value
    const response = await runtimeSurfaceApi.precheckFrameworkAdapter({
      adapter_id: adapterId,
      conversation_id: conversationId,
      execution_context: {
        run_kind: 'framework_adapter_precheck',
        ...(planId !== null ? { plan_id: planId } : {}),
        ...(planItemId !== null ? { plan_item_id: planItemId } : {}),
      }
    })
    const data = response.data || {}
    adapterPrecheckResult.value = {
      adapter_id: data.adapter_id || adapterId,
      display_name: data.framework_name || adapter?.display_name || adapterId,
      framework_name: data.framework_name || adapter?.framework_name || adapter?.display_name || '',
      ready: Boolean(data.ready),
      configuration_status: data.configuration_status || '',
      execution_mode: data.execution_mode || '',
      execution_block_reason: data.execution_block_reason || '',
      detail: data.detail || '',
      snapshot_id: String(data.timeline_recording?.snapshot_ref?.snapshot_id || '').trim(),
      remediation_command: buildAdapterRemediationCommand(data),
    }
    if (conversationId !== null) {
      await plannerStore.loadPlans({ conversationId })
    }
    await loadProfile()
  } catch (err) {
    error.value = err?.response?.data?.error?.message || err?.response?.data?.detail || err?.message || '运行 adapter 预检失败'
  } finally {
    adapterPrecheckRunning.value = false
  }
}

async function runAdapterExternalPilot(adapter) {
  const adapterId = String(adapter?.adapter_id || '').trim()
  if (!adapterId) return

  adapterExternalPilotRunning.value = true
  error.value = ''
  try {
    const conversationId = currentConversationId.value
    const planId = currentPlanId.value
    const planItemId = currentPlanItemId.value
    const response = await runtimeSurfaceApi.runExternalFrameworkAdapterPilot({
      adapter_id: adapterId,
      run_id: `ui-external-pilot-${Date.now()}`,
      messages: [{ role: 'user', content: '请执行 LangGraph external pilot 并返回运行时巡检结果' }],
      conversation_id: conversationId,
      execution_context: {
        run_kind: 'framework_adapter_external_pilot',
        ...(planId !== null ? { plan_id: planId } : {}),
        ...(planItemId !== null ? { plan_item_id: planItemId } : {})
      }
    })
    const data = response.data || {}
    const snapshotId = String(data.snapshot_ref?.snapshot_id || '').trim()
    const snapshotDescriptor = snapshotId
      ? buildSnapshotCommandDescriptor(snapshotId, 'framework_adapter')
      : null
    if (snapshotDescriptor) {
      recordRecentSnapshotCommand(snapshotDescriptor)
    }
    adapterExternalPilotResult.value = {
      adapter_id: data.adapter_id || adapterId,
      display_name: data.framework_name || adapter?.display_name || adapterId,
      framework_name: data.framework_name || adapter?.framework_name || adapter?.display_name || '',
      status: data.status || 'ok',
      error_type: data.error?.error_type || '',
      error_detail: data.error?.detail || '',
      detail: data.error?.detail || data.detail || '',
      final_output: data.final_output || '',
      snapshot_id: snapshotId,
      snapshot_command: snapshotDescriptor?.commandText || ''
    }
    if (conversationId !== null) {
      await plannerStore.loadPlans({ conversationId })
    }
    await loadProfile()
  } catch (err) {
    const errorBody = err?.response?.data?.error || {}
    const detail = errorBody.message || err?.response?.data?.detail || err?.message || '运行 adapter external pilot 失败'
    adapterExternalPilotResult.value = {
      adapter_id: adapterId,
      display_name: adapter?.display_name || adapterId,
      framework_name: adapter?.framework_name || adapter?.display_name || '',
      status: 'failed',
      error_type: errorBody.code || errorBody.error_type || 'request_failed',
      error_detail: detail,
      detail,
      final_output: '',
      snapshot_id: '',
      snapshot_command: ''
    }
    error.value = detail
  } finally {
    adapterExternalPilotRunning.value = false
  }
}

async function runAdapterPilot(adapter) {
  const adapterId = String(adapter?.adapter_id || '').trim()
  if (!adapterId) return

  adapterPilotRunning.value = true
  error.value = ''
  try {
    const conversationId = currentConversationId.value
    const planId = currentPlanId.value
    const planItemId = currentPlanItemId.value
    const response = await runtimeSurfaceApi.runFrameworkAdapterPilot({
      adapter_id: adapterId,
      run_id: `ui-pilot-${Date.now()}`,
      messages: [{ role: 'user', content: '请生成一份运行时巡检计划摘要' }],
      conversation_id: conversationId,
      execution_context: {
        run_kind: 'framework_adapter',
        ...(planId !== null ? { plan_id: planId } : {}),
        ...(planItemId !== null ? { plan_item_id: planItemId } : {})
      }
    })
    const data = response.data || {}
    const snapshotId = String(data.snapshot_ref?.snapshot_id || '').trim()
    const snapshotDescriptor = snapshotId
      ? buildSnapshotCommandDescriptor(snapshotId, 'framework_adapter')
      : null
    if (snapshotDescriptor) {
      recordRecentSnapshotCommand(snapshotDescriptor)
    }
    adapterPilotResult.value = {
      adapter_id: data.adapter_id || adapterId,
      display_name: data.framework_name || adapter?.display_name || adapterId,
      framework_name: data.framework_name || adapter?.framework_name || adapter?.display_name || '',
      run_id: data.run_id || '',
      event_count: Array.isArray(data.events) ? data.events.length : 0,
      final_output: data.final_output || '',
      snapshot_id: snapshotId,
      snapshot_command: snapshotDescriptor?.commandText || ''
    }
    if (conversationId !== null) {
      await plannerStore.loadPlans({ conversationId })
    }
    await loadProfile()
  } catch (err) {
    error.value = err?.response?.data?.error?.message || err?.response?.data?.detail || err?.message || '运行 adapter pilot 失败'
  } finally {
    adapterPilotRunning.value = false
  }
}

function toggleProvider(providerId, checked) {
  const current = new Set(editableEnabledProviders.value)
  if (checked) {
    current.add(providerId)
  } else {
    current.delete(providerId)
  }
  editableEnabledProviders.value = [...current]
}

function formatProviderConfig(value, isOverride = false) {
  if (!Array.isArray(value) || value.length === 0) {
    return isOverride ? '未覆写（沿用默认全启用）' : '全部启用'
  }
  return value.join(', ')
}

function buildAdapterRemediationCommand(result) {
  const payload = normalizeContractObject(result)
  const commands = []
  const missingPackages = Array.isArray(payload.missing_packages) ? payload.missing_packages : []
  const missingEnv = Array.isArray(payload.missing_env) ? payload.missing_env : []
  if (missingPackages.length) {
    commands.push(`pip install ${missingPackages.join(' ')}`)
  }
  for (const envName of missingEnv) {
    commands.push(`${envName}=<value>`)
  }
  if (missingPackages.length || missingEnv.length || payload.configuration_status === 'runtime_disabled') {
    commands.push('ENABLE_LANGGRAPH_RUNTIME_EXECUTION=true')
  }
  return commands.join('\n')
}

function openAdapterPilotSnapshot(snapshotId) {
  const normalizedSnapshotId = String(snapshotId || '').trim()
  if (!normalizedSnapshotId) {
    return
  }
  router.push(`/settings?tab=advanced&governance_snapshot=${encodeURIComponent(normalizedSnapshotId)}`)
}

function openAdapterFailureTypeTimeline(errorType) {
  const normalizedErrorType = String(errorType || '').trim()
  if (!normalizedErrorType) {
    return
  }
  router.push(
    `/settings?tab=advanced&governance_filter=framework_adapter&governance_severity=warning&governance_error_type=${encodeURIComponent(normalizedErrorType)}`
  )
}

function openRuntimeContractGateTimeline() {
  router.push('/settings?tab=advanced&governance_filter=runtime_contract&governance_severity=warning')
}

function openMainChatQueryTimeline(queryId) {
  const normalizedQueryId = String(queryId || '').trim()
  if (!normalizedQueryId) {
    return
  }
  router.push(`/settings?tab=advanced&governance_filter=main_chat&governance_query_id=${encodeURIComponent(normalizedQueryId)}`)
}

function normalizeNumericId(value) {
  const normalized = Number(value)
  return Number.isFinite(normalized) ? normalized : null
}

function normalizeContractObject(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return {}
  }
  return value
}

function buildRuntimeCoreContract(value) {
  const contract = normalizeContractObject(value)
  return {
    connected: Object.keys(contract).length > 0,
    run_id: contract.run_id || '',
    parent_run_id: contract.parent_run_id || '',
    child_run_id: contract.child_run_id || '',
    scheduler_run_id: contract.scheduler_run_id || '',
    run_kind: contract.run_kind || '',
    status: contract.status || '',
    trace_count: Number(contract.trace_count || 0),
    latest_trace_event: normalizeNestedContract(contract.latest_trace_event),
    child_merge_intent: contract.child_merge_intent || '',
    child_merge_entities: Array.isArray(contract.child_merge_entities) ? contract.child_merge_entities : [],
    child_merge_entity_count: Number(contract.child_merge_entity_count || 0),
    child_merge_focus_count: Number(contract.child_merge_focus_count || 0),
    child_merge_action_count: Number(contract.child_merge_action_count || 0),
    child_merge_primary_entities: Array.isArray(contract.child_merge_primary_entities) ? contract.child_merge_primary_entities : [],
    child_merge_conclusion: contract.child_merge_conclusion || '',
  }
}

function buildRunRecoveryContract(value) {
  const contract = normalizeContractObject(value)
  const toolContinuation = normalizeContractObject(contract.tool_continuation)
  const loopContinuation = normalizeContractObject(contract.loop_continuation)
  const workspaceBackend = normalizeContractObject(contract.workspace_backend)
  return {
    available: Object.keys(contract).length > 0 && Boolean(contract.available),
    contractVersion: contract.contract_version || '',
    run_id: contract.run_id || '',
    run_state: contract.run_state || '',
    recoverable: Boolean(contract.recoverable),
    reason: contract.reason || '',
    toolContinuation: {
      recoveryStatus: toolContinuation.recovery_status || '',
      recoveryReason: toolContinuation.recovery_reason || '',
      descriptorPresent: Boolean(toolContinuation.descriptor_present),
      executableAvailable: Boolean(toolContinuation.executable_available),
    },
    loopContinuation: {
      recoveryStatus: loopContinuation.recovery_status || '',
      recoveryReason: loopContinuation.recovery_reason || '',
      descriptorPresent: Boolean(loopContinuation.descriptor_present),
      executableAvailable: Boolean(loopContinuation.executable_available),
    },
    workspaceBackend: {
      backendKind: workspaceBackend.backend_kind || '',
      durable: Boolean(workspaceBackend.durable),
      fallbackActive: Boolean(workspaceBackend.fallback_active),
      fallbackReason: workspaceBackend.fallback_reason || '',
    }
  }
}

function buildEmbeddedRuntimeBootstrapContract(value) {
  const contract = normalizeContractObject(value)
  const defaultRuntimeProfile = normalizeContractObject(contract.default_runtime_profile)
  const workspaceBackend = normalizeContractObject(contract.workspace_backend)
  const bootstrapRecoveryValidation = normalizeContractObject(contract.bootstrap_recovery_validation)
  return {
    connected: Object.keys(contract).length > 0,
    contractVersion: contract.contract_version || '',
    runtimeBackend: contract.runtime_backend || '',
    defaultRuntimeProfile: {
      db_mode: defaultRuntimeProfile.db_mode || '',
      embedded_workspace_store_mode: defaultRuntimeProfile.embedded_workspace_store_mode || '',
      default_runtime_mode: defaultRuntimeProfile.default_runtime_mode || '',
      recovery_posture: defaultRuntimeProfile.recovery_posture || '',
      recommended_bootstrap: defaultRuntimeProfile.recommended_bootstrap || '',
    },
    workspaceBackend: {
      backend_kind: workspaceBackend.backend_kind || '',
      backend_mode: workspaceBackend.backend_mode || '',
      durable: Boolean(workspaceBackend.durable),
      fallback_active: Boolean(workspaceBackend.fallback_active),
      fallback_reason: workspaceBackend.fallback_reason || '',
      last_error: workspaceBackend.last_error || '',
    },
    bootstrapRecoveryValidation: {
      contract_version: bootstrapRecoveryValidation.contract_version || '',
      validation_status: bootstrapRecoveryValidation.validation_status || '',
      actual_recoverable: Boolean(bootstrapRecoveryValidation.actual_recoverable),
      expected_recoverable: Boolean(bootstrapRecoveryValidation.expected_recoverable),
      workspace_backend_kind: bootstrapRecoveryValidation.workspace_backend_kind || '',
      workspace_backend_mode: bootstrapRecoveryValidation.workspace_backend_mode || '',
      tool_recovery_reason: bootstrapRecoveryValidation.tool_recovery_reason || '',
      loop_recovery_reason: bootstrapRecoveryValidation.loop_recovery_reason || '',
    }
  }
}

function buildEmbeddedRuntimeBootstrapUpdateResult(value) {
  const contract = normalizeContractObject(value)
  const defaultRuntimeProfile = normalizeContractObject(contract.default_runtime_profile)
  const bootstrapRecoveryValidation = normalizeContractObject(contract.bootstrap_recovery_validation)
  const postUpdateVerification = normalizeContractObject(contract.post_update_verification)
  const timelineRecording = normalizeContractObject(contract.timeline_recording)
  const snapshotRef = normalizeContractObject(timelineRecording.snapshot_ref)
  const summaryPayload = {
    requested_embedded_workspace_store_mode: String(
      contract.requested_embedded_workspace_store_mode ||
      defaultRuntimeProfile.embedded_workspace_store_mode ||
      ''
    ).trim(),
    current_runtime_mode: String(postUpdateVerification.current_runtime_mode || '').trim(),
    current_recovery_posture: String(postUpdateVerification.current_recovery_posture || '').trim(),
    current_workspace_backend_mode: String(postUpdateVerification.current_workspace_backend_mode || '').trim(),
    bootstrap_recovery_validation_status: String(bootstrapRecoveryValidation.validation_status || '').trim(),
  }
  return {
    updateStatus: String(contract.update_status || '').trim(),
    currentRuntimeMode: String(postUpdateVerification.current_runtime_mode || '').trim(),
    currentRecoveryPosture: String(postUpdateVerification.current_recovery_posture || '').trim(),
    currentWorkspaceBackendMode: String(postUpdateVerification.current_workspace_backend_mode || '').trim(),
    timelineSnapshotId: String(snapshotRef.snapshot_id || '').trim(),
    timelineEventType: String(snapshotRef.event_type || '').trim(),
    timelineEventLabel: formatAuditEvent(String(snapshotRef.event_type || '').trim()),
    summary: formatEmbeddedRuntimeBootstrapSummary(summaryPayload),
  }
}

function buildEmbeddedRuntimeBoundariesContract(value) {
  const contract = normalizeContractObject(value)
  return {
    connected: Object.keys(contract).length > 0,
    contract_version: contract.contract_version || '',
    volatile_runtime_state: Array.isArray(contract.volatile_runtime_state) ? contract.volatile_runtime_state : [],
    persistence_seams: Array.isArray(contract.persistence_seams) ? contract.persistence_seams : [],
    recovery_entrypoints: Array.isArray(contract.recovery_entrypoints)
      ? contract.recovery_entrypoints.map(entry => ({
        method: entry?.method || '',
        mode: entry?.mode || '',
        recovery_scope: entry?.recovery_scope || ''
      }))
      : [],
    delegate_preflight_status: contract.delegate_preflight_status || '',
    facade_delegate_preflight_status: contract.facade_delegate_preflight_status || '',
    real_child_executor_ready: Boolean(contract.real_child_executor_ready),
    delegate_executor_binding_status: contract.delegate_executor_binding_status || '',
    delegate_executor_binding_blockers: Array.isArray(contract.delegate_executor_binding_blockers) ? contract.delegate_executor_binding_blockers : [],
    delegate_recommended_next_step: contract.delegate_recommended_next_step || '',
    delegate_gate_status: contract.delegate_gate_status || '',
    delegate_gate_allowed: Boolean(contract.delegate_gate_allowed),
    delegate_gate_failure_reason: contract.delegate_gate_failure_reason || '',
    delegate_route_status: contract.delegate_route_status || '',
    delegate_route_executor_path: contract.delegate_route_executor_path || '',
    delegate_route_reason: contract.delegate_route_reason || '',
    delegate_route_recommended_action: contract.delegate_route_recommended_action || '',
    delegate_binding_status: contract.delegate_binding_status || '',
    delegate_binding_id: contract.delegate_binding_id || '',
    delegate_binding_reason: contract.delegate_binding_reason || '',
    delegate_binding_recommended_action: contract.delegate_binding_recommended_action || '',
    delegate_stub_status: contract.delegate_stub_status || '',
    delegate_stub_binding_id: contract.delegate_stub_binding_id || '',
    delegate_stub_executor_path: contract.delegate_stub_executor_path || '',
    delegate_stub_reason: contract.delegate_stub_reason || '',
    delegate_stub_recommended_action: contract.delegate_stub_recommended_action || '',
    delegate_execution_status: contract.delegate_execution_status || '',
    delegate_execution_binding_id: contract.delegate_execution_binding_id || '',
    delegate_execution_executor_path: contract.delegate_execution_executor_path || '',
    delegate_execution_mode: contract.delegate_execution_mode || '',
    delegate_execution_output_summary: contract.delegate_execution_output_summary || '',
    delegate_execution_reason: contract.delegate_execution_reason || '',
    delegate_execution_output_text: contract.delegate_execution_output_text || '',
    delegate_execution_output_envelope: {
      artifactId: contract.delegate_execution_output_envelope?.artifact_ref?.artifact_id || '',
      uri: contract.delegate_execution_output_envelope?.artifact_ref?.uri || '',
      mergeHint: contract.delegate_execution_output_envelope?.merge_hint || '',
      mergeReady: Boolean(contract.delegate_execution_output_envelope?.merge_ready),
      sectionCount: Array.isArray(contract.delegate_execution_output_envelope?.sections) ? contract.delegate_execution_output_envelope.sections.length : 0,
    },
    delegate_execution_recommended_action: contract.delegate_execution_recommended_action || '',
    delegate_merge_status: contract.delegate_merge_status || '',
    delegate_merge_ready: Boolean(contract.delegate_merge_ready),
    delegate_merge_reason: contract.delegate_merge_reason || '',
    delegate_merge_strategy: contract.delegate_merge_strategy || '',
    delegate_merged_summary: contract.delegate_merged_summary || '',
    delegate_merged_output: contract.delegate_merged_output || '',
    delegate_merge_artifact_ref: {
      artifactId: contract.delegate_merge_artifact_ref?.artifact_id || '',
      uri: contract.delegate_merge_artifact_ref?.uri || '',
    },
    delegate_merge_section_count: Number(contract.delegate_merge_section_count || 0),
    delegate_replay_record_count: Number(contract.delegate_replay_record_count || 0),
    delegate_replay_records: Array.isArray(contract.delegate_replay_records)
      ? contract.delegate_replay_records.map(record => ({
        binding_id: record?.binding_id || '',
        execution_status: record?.execution_status || '',
        executor_path: record?.executor_path || '',
        merge_status: record?.merge_status || '',
      }))
      : [],
    delegate_artifact_summary: {
      recordCount: Number(contract.delegate_artifact_summary?.record_count || 0),
      latestArtifactId: contract.delegate_artifact_summary?.latest_artifact_id || '',
      latestMergeStrategy: contract.delegate_artifact_summary?.latest_merge_strategy || '',
      latestResultType: contract.delegate_artifact_summary?.latest_result_type || '',
      latestConclusion: contract.delegate_artifact_summary?.latest_conclusion || '',
      latestMergedSummary: contract.delegate_artifact_summary?.latest_merged_summary || '',
      latestMergedOutput: contract.delegate_artifact_summary?.latest_merged_output || '',
      artifactIds: Array.isArray(contract.delegate_artifact_summary?.artifact_ids) ? contract.delegate_artifact_summary.artifact_ids : [],
      mergeStrategies: Array.isArray(contract.delegate_artifact_summary?.merge_strategies) ? contract.delegate_artifact_summary.merge_strategies : [],
      resultTypes: Array.isArray(contract.delegate_artifact_summary?.result_types) ? contract.delegate_artifact_summary.result_types : [],
    },
    delegate_current_scope: Array.isArray(contract.delegate_current_scope) ? contract.delegate_current_scope : [],
    delegate_promotion_requirements: Array.isArray(contract.delegate_promotion_requirements) ? contract.delegate_promotion_requirements : [],
    delegate_non_goals: Array.isArray(contract.delegate_non_goals) ? contract.delegate_non_goals : [],
    workspace_backend: {
      backend_kind: contract.workspace_backend?.backend_kind || '',
      backend_mode: contract.workspace_backend?.backend_mode || '',
      durable: Boolean(contract.workspace_backend?.durable),
      operation_fallback_allowed: Boolean(contract.workspace_backend?.operation_fallback_allowed),
      fallback_active: Boolean(contract.workspace_backend?.fallback_active),
      fallback_reason: contract.workspace_backend?.fallback_reason || '',
      last_error: contract.workspace_backend?.last_error || '',
    },
    approved_reference_slices: Array.isArray(contract.approved_reference_slices)
      ? contract.approved_reference_slices.map(entry => ({
        source: entry?.source || '',
        role: entry?.role || '',
        role_label: describeReferenceRole(entry?.role).label,
        role_description: describeReferenceRole(entry?.role).description,
        slices: Array.isArray(entry?.slices) ? entry.slices : [],
      }))
      : [],
  }
}

function describeReferenceRole(role) {
  const normalizedRole = String(role || '').trim()
  if (normalizedRole === 'conceptual_reference') {
    return {
      label: '概念分层参考',
      description: '用于校正运行时术语、恢复语义和任务分层边界，不直接照搬产品壳。'
    }
  }
  if (normalizedRole === 'control_plane_reference') {
    return {
      label: '控制面机制参考',
      description: '用于参考执行后端、权限同步、重连与 runner lifecycle 等真实控制面机制。'
    }
  }
  return {
    label: normalizedRole || '-',
    description: ''
  }
}

function buildGovernanceOverviewContract(value) {
  const contract = normalizeContractObject(value)
  const runContract = normalizeContractObject(contract.run)
  const runRecoveryContract = normalizeContractObject(contract.run_recovery)
  const childExecutorPreflightContract = normalizeContractObject(contract.child_executor_preflight)
  const childExecutorPromotionGateContract = normalizeContractObject(contract.child_executor_promotion_gate)
  return {
    connected: Object.keys(contract).length > 0,
    run: {
      ...buildRuntimeCoreContract(runContract),
      childMergeIntent: String(runContract.child_merge_intent || '').trim(),
      childMergeEntities: Array.isArray(runContract.child_merge_entities) ? runContract.child_merge_entities : [],
      childMergeEntityCount: Number(runContract.child_merge_entity_count || 0),
      childMergeFocusCount: Number(runContract.child_merge_focus_count || 0),
      childMergeActionCount: Number(runContract.child_merge_action_count || 0),
      childMergePrimaryEntities: Array.isArray(runContract.child_merge_primary_entities) ? runContract.child_merge_primary_entities : [],
      childMergeConclusion: String(runContract.child_merge_conclusion || '').trim(),
    },
    runRecovery: buildRunRecoveryContract(runRecoveryContract),
    childExecutorPreflight: {
      contractVersion: childExecutorPreflightContract.contract_version || '',
      status: childExecutorPreflightContract.status || '',
      promotionReady: Boolean(childExecutorPreflightContract.promotion_ready),
      realChildExecutorReady: Boolean(childExecutorPreflightContract.real_child_executor_ready),
      executorBindingStatus: childExecutorPreflightContract.executor_binding_status || '',
      executorBindingBlockers: Array.isArray(childExecutorPreflightContract.executor_binding_blockers)
        ? childExecutorPreflightContract.executor_binding_blockers
        : [],
      recommendedNextStep: childExecutorPreflightContract.recommended_next_step || '',
      gateStatus: childExecutorPreflightContract.delegate_gate_status || '',
      gateAllowed: Boolean(childExecutorPreflightContract.delegate_gate_allowed),
      gateFailureReason: childExecutorPreflightContract.delegate_gate_failure_reason || '',
      promotionRequirements: Array.isArray(childExecutorPreflightContract.delegate_promotion_requirements)
        ? childExecutorPreflightContract.delegate_promotion_requirements
        : [],
      missingRequirements: Array.isArray(childExecutorPreflightContract.delegate_missing_requirements)
        ? childExecutorPreflightContract.delegate_missing_requirements
        : [],
      nonGoals: Array.isArray(childExecutorPreflightContract.delegate_non_goals)
        ? childExecutorPreflightContract.delegate_non_goals
        : [],
      currentScope: Array.isArray(childExecutorPreflightContract.delegate_current_scope)
        ? childExecutorPreflightContract.delegate_current_scope
        : [],
      workspaceBackend: normalizeContractObject(childExecutorPreflightContract.workspace_backend),
    },
    childExecutorPromotionGate: {
      contractVersion: childExecutorPromotionGateContract.contract_version || '',
      gateStatus: childExecutorPromotionGateContract.gate_status || '',
      allowed: Boolean(childExecutorPromotionGateContract.allowed),
      failureReason: childExecutorPromotionGateContract.failure_reason || '',
      executorPath: childExecutorPromotionGateContract.executor_path || '',
      recommendedNextStep: childExecutorPromotionGateContract.recommended_next_step || '',
      blockers: Array.isArray(childExecutorPromotionGateContract.blockers) ? childExecutorPromotionGateContract.blockers : [],
      checkedAt: childExecutorPromotionGateContract.checked_at || '',
    },
    approval: {
      request_count: Number(contract.approval?.request_count || 0),
      pending_count: Number(contract.approval?.pending_count || 0),
      latest_request: normalizeNestedContract(contract.approval?.latest_request),
    },
    audit: {
      event_count: Number(contract.audit?.event_count || 0),
      latest_event: normalizeNestedContract(contract.audit?.latest_event),
    },
    main_chat: buildMainChatTraceOverview(contract.main_chat),
  }
}

function buildToolRuntimeContract(value) {
  const contract = normalizeContractObject(value)
  return {
    connected: Object.keys(contract).length > 0,
    contract_version: contract.contract_version || '',
    total_tools: Number(contract.total_tools || 0),
    base_tool_count: Number(contract.base_tool_count || 0),
    langchain_tool_count: Number(contract.langchain_tool_count || 0),
    tool_spec_count: Number(contract.tool_spec_count || 0),
    doubao_definition_count: Number(contract.doubao_definition_count || 0),
    mcp_capability_count: Number(contract.mcp_capability_count || 0),
    high_risk_tool_count: Number(contract.high_risk_tool_count || 0),
    tools: Array.isArray(contract.tools) ? contract.tools : [],
  }
}

function buildMcpRuntimeContract(value) {
  const contract = normalizeContractObject(value)
  return {
    connected: Object.keys(contract).length > 0,
    contract_version: contract.contract_version || '',
    overall_status: contract.overall_status || '',
    capability_count: Number(contract.capability_count || 0),
    enabled_servers: Number(contract.enabled_servers || 0),
    components: Array.isArray(contract.components) ? contract.components : [],
  }
}

function buildAdapterHealthContract(value) {
  const contract = normalizeContractObject(value)
  const latestExternalPilotFailure = normalizeContractObject(contract.latest_external_pilot_failure)
  const externalPilotFailureCounts = normalizeContractObject(contract.external_pilot_failure_counts)
  return {
    connected: Object.keys(contract).length > 0,
    contract_version: contract.contract_version || '',
    overall_status: contract.overall_status || '',
    adapter_count: Number(contract.adapter_count || 0),
    unavailable_count: Number(contract.unavailable_count || 0),
    external_pilot_failure_counts: Object.keys(externalPilotFailureCounts).length
      ? {
        total: Number(externalPilotFailureCounts.total || 0),
        window_scope: String(externalPilotFailureCounts.window_scope || '').trim(),
        sample_size: Number(externalPilotFailureCounts.sample_size || 0),
        by_error_type: normalizeContractObject(externalPilotFailureCounts.by_error_type)
      }
      : null,
    latest_external_pilot_failure: Object.keys(latestExternalPilotFailure).length
      ? {
        ...latestExternalPilotFailure,
        error_type: String(latestExternalPilotFailure.error_type || '').trim(),
        detail: String(latestExternalPilotFailure.detail || latestExternalPilotFailure.error_detail || '').trim(),
        snapshot_id: String(latestExternalPilotFailure.snapshot_ref?.snapshot_id || '').trim(),
      }
      : null,
    adapters: Array.isArray(contract.adapters)
      ? contract.adapters.map(adapter => ({
        ...normalizeContractObject(adapter),
        required_env: Array.isArray(adapter?.required_env) ? adapter.required_env : [],
        missing_env: Array.isArray(adapter?.missing_env) ? adapter.missing_env : [],
        required_packages: Array.isArray(adapter?.required_packages) ? adapter.required_packages : [],
        missing_packages: Array.isArray(adapter?.missing_packages) ? adapter.missing_packages : [],
        package_installed: Boolean(adapter?.package_installed),
        runtime_enabled: Boolean(adapter?.runtime_enabled),
        configuration_status: String(adapter?.configuration_status || '').trim(),
        execution_mode: String(adapter?.execution_mode || '').trim(),
        execution_block_reason: String(adapter?.execution_block_reason || '').trim(),
      }))
      : [],
  }
}

function buildContractSnapshot(value) {
  const contract = normalizeContractObject(value)
  return {
    connected: Object.keys(contract).length > 0,
    contract_version: contract.contract_version || '',
    overall_status: contract.overall_status || '',
    contract_count: Number(contract.contract_count || 0),
    missing_contract_count: Number(contract.missing_contract_count || 0),
    missing_field_count: Number(contract.missing_field_count || 0),
    fingerprint: contract.fingerprint || '',
    contracts: Array.isArray(contract.contracts) ? contract.contracts : [],
  }
}

function buildRuntimeContractGate(value) {
  const contract = normalizeContractObject(value)
  const summary = normalizeContractObject(contract.runtime_contract_summary)
  const coverage = normalizeContractObject(summary.approval_replay_coverage)
  return {
    connected: Object.keys(contract).length > 0,
    contract_version: contract.contract_version || '',
    available: Boolean(contract.available),
    overall_status: contract.overall_status || '',
    generated_at: contract.generated_at || '',
    report_path: contract.report_path || '',
    check_count: Number(contract.check_count || 0),
    failed_check_count: Number(contract.failed_check_count || 0),
    failure_reason: contract.failure_reason || '',
    summary: {
      overall_status: String(summary.overall_status || '').trim(),
      check_count: Number(summary.check_count || 0),
      failed_check_count: Number(summary.failed_check_count || 0),
      missing_payload_count: Number(summary.missing_payload_count || 0),
      approvalReplayCovered: Boolean(coverage.event_payload_sample),
      observedStatusKinds: Array.isArray(coverage.observed_status_kinds)
        ? coverage.observed_status_kinds.map(item => String(item || '').trim()).filter(Boolean)
        : [],
    },
    checks: Array.isArray(contract.checks)
      ? contract.checks.map(check => ({
        ...normalizeContractObject(check),
        step: String(check?.step || '').trim(),
        name: String(check?.name || '').trim(),
        ok: Boolean(check?.ok),
        failure_reason: String(check?.failure_reason || '').trim(),
        status_code: check?.status_code || '',
        contract_snapshot_status: String(check?.contract_snapshot_status || '').trim(),
        adapter_health_status: String(check?.adapter_health_status || '').trim(),
        missing_payload_count: Number(check?.missing_payload_count || 0),
        checked_event_count: Number(check?.checked_event_count || 0),
        backend_kind: String(check?.backend_kind || '').trim(),
        backend_mode: String(check?.backend_mode || '').trim(),
        observed_status_kinds: Array.isArray(check?.observed_status_kinds)
          ? check.observed_status_kinds.map(item => String(item || '').trim()).filter(Boolean)
          : [],
        fallback_active: typeof check?.fallback_active === 'boolean' ? String(check.fallback_active) : '',
        probe_recoverable: typeof check?.probe_recoverable === 'boolean' ? String(check.probe_recoverable) : '',
        tool_recovery_reason: String(check?.tool_recovery_reason || '').trim(),
        loop_recovery_reason: String(check?.loop_recovery_reason || '').trim(),
        resumed_state: String(check?.resumed_state || '').trim(),
        approved_state: String(check?.approved_state || '').trim(),
      }))
      : [],
  }
}

function buildMainChatTraceOverview(value) {
  const contract = normalizeContractObject(value)
  const stageCounts = normalizeContractObject(contract.stage_counts)
  const recentQueries = Array.isArray(contract.recent_queries)
    ? contract.recent_queries.map(item => ({
      queryId: String(item?.query_id || '').trim(),
      latestStage: String(item?.latest_stage || '').trim(),
      latestSummary: String(item?.latest_summary || '').trim(),
      latestTimestamp: String(item?.latest_timestamp || '').trim(),
      latestSnapshotId: String(item?.latest_snapshot_id || '').trim(),
      stageCounts: normalizeContractObject(item?.stage_counts),
      lastSuccessStage: String(item?.last_success_stage || '').trim(),
      lastWarningStage: String(item?.last_warning_stage || '').trim(),
      recordingState: String(item?.recording_state || 'recorded').trim() || 'recorded',
    })).filter(item => item.queryId)
    : []
  return {
    connected: Object.keys(contract).length > 0,
    hasRuntimeTarget: Boolean(contract.has_runtime_target),
    traceEventCount: Number(contract.trace_event_count || 0),
    stageCounts,
    stageEntries: Object.entries(stageCounts)
      .map(([stage, count]) => ({ stage: String(stage || '').trim(), count: Number(count || 0) }))
      .filter(entry => entry.stage),
    lastSuccessStage: String(contract.last_success_stage || '').trim(),
    lastWarningStage: String(contract.last_warning_stage || '').trim(),
    latestStage: String(contract.latest_stage || '').trim(),
    latestQueryId: String(contract.latest_query_id || '').trim(),
    latestSummary: String(contract.latest_summary || '').trim(),
    latestDetail: String(contract.latest_detail || '').trim(),
    latestTimestamp: String(contract.latest_timestamp || '').trim(),
    latestSnapshotId: String(contract.latest_snapshot_id || '').trim(),
    reason: String(contract.reason || '').trim(),
    recordingState: String(contract.recording_state || 'unavailable').trim() || 'unavailable',
    recentQueries,
  }
}

function buildChildExecutorOutputReplayContract(value = {}) {
  const contract = normalizeContractObject(value)
  return {
    contractVersion: contract.contract_version || '',
    parentRunId: contract.parent_run_id || '',
    recordCount: Number(contract.record_count || 0),
    records: Array.isArray(contract.records)
      ? contract.records.map(record => ({
        bindingId: record?.binding_id || '',
        executionStatus: record?.execution_status || '',
        executorPath: record?.executor_path || '',
        mergeStatus: record?.merge_status || '',
        mergeStrategy: record?.merge_strategy || '',
        mergedSummary: record?.merged_summary || '',
        artifactId: record?.artifact_id || '',
      }))
      : [],
    latestMergedSummary: contract.latest_merged_summary || '',
    latestMergedOutput: contract.latest_merged_output || '',
  }
}

function buildChildExecutorOutputSummaryContract(value = {}) {
  const contract = normalizeContractObject(value)
  const latestMergedSemantics = normalizeContractObject(contract.latest_merged_semantics)
  const mergeBehavior = normalizeContractObject(latestMergedSemantics.merge_behavior)
  return {
    contractVersion: contract.contract_version || '',
    parentRunId: contract.parent_run_id || '',
    recordCount: Number(contract.record_count || 0),
    latestArtifactId: contract.latest_artifact_id || '',
    latestMergeStrategy: contract.latest_merge_strategy || '',
    latestResultType: contract.latest_result_type || '',
    latestConclusion: contract.latest_conclusion || '',
    latestMergedSummary: contract.latest_merged_summary || '',
    latestMergedOutput: contract.latest_merged_output || '',
    latestEntities: Array.isArray(contract.latest_entities) ? contract.latest_entities : [],
    latestFocusPoints: Array.isArray(contract.latest_focus_points) ? contract.latest_focus_points : [],
    latestActionItems: Array.isArray(contract.latest_action_items) ? contract.latest_action_items : [],
    artifactIds: Array.isArray(contract.artifact_ids) ? contract.artifact_ids : [],
    mergeStrategies: Array.isArray(contract.merge_strategies) ? contract.merge_strategies : [],
    resultTypes: Array.isArray(contract.result_types) ? contract.result_types : [],
    entitySets: Array.isArray(contract.entity_sets) ? contract.entity_sets : [],
    latestMergedSemantics: {
      intentLabel: latestMergedSemantics.intent_label || '',
      entities: Array.isArray(latestMergedSemantics.entities) ? latestMergedSemantics.entities : [],
      focusPoints: Array.isArray(latestMergedSemantics.focus_points) ? latestMergedSemantics.focus_points : [],
      actionItems: Array.isArray(latestMergedSemantics.action_items) ? latestMergedSemantics.action_items : [],
      mergeBehavior: {
        entities: mergeBehavior.entities || '',
        focusPoints: mergeBehavior.focus_points || '',
        actionItems: mergeBehavior.action_items || '',
      },
    },
  }
}

function buildChildExecutorMergedSemanticsContract(value = {}) {
  const contract = normalizeContractObject(value)
  const mergeBehavior = normalizeContractObject(contract.merge_behavior)
  const mergedSections = normalizeContractObject(contract.merged_sections)
  const parentStateSurface = normalizeContractObject(contract.parent_state_surface)
  const mergedEntitiesSection = normalizeContractObject(mergedSections.merged_entities)
  const mergedFocusSection = normalizeContractObject(mergedSections.merged_focus)
  const mergedActionsSection = normalizeContractObject(mergedSections.merged_actions)
  const latestConclusionSection = normalizeContractObject(mergedSections.latest_conclusion)
  return {
    contractVersion: contract.contract_version || '',
    parentRunId: contract.parent_run_id || '',
    recordCount: Number(contract.record_count || 0),
    available: Boolean(contract.available),
    intentCatalogVersion: contract.intent_catalog_version || '',
    supportedIntents: Array.isArray(contract.supported_intents) ? contract.supported_intents : [],
    intentLabel: contract.intent_label || '',
    entities: Array.isArray(contract.entities) ? contract.entities : [],
    focusPoints: Array.isArray(contract.focus_points) ? contract.focus_points : [],
    actionItems: Array.isArray(contract.action_items) ? contract.action_items : [],
    latestMergedSummary: contract.latest_merged_summary || '',
    latestMergedOutput: contract.latest_merged_output || '',
    latestMergeStrategy: contract.latest_merge_strategy || '',
    latestResultType: contract.latest_result_type || '',
    mergeBehavior: {
      entities: mergeBehavior.entities || '',
      focusPoints: mergeBehavior.focus_points || '',
      actionItems: mergeBehavior.action_items || '',
    },
    mergedSections: {
      mergedEntities: {
        sectionId: mergedEntitiesSection.section_id || '',
        title: mergedEntitiesSection.title || '',
        mergeMode: mergedEntitiesSection.merge_mode || '',
        items: Array.isArray(mergedEntitiesSection.items) ? mergedEntitiesSection.items : [],
      },
      mergedFocus: {
        sectionId: mergedFocusSection.section_id || '',
        title: mergedFocusSection.title || '',
        mergeMode: mergedFocusSection.merge_mode || '',
        items: Array.isArray(mergedFocusSection.items) ? mergedFocusSection.items : [],
      },
      mergedActions: {
        sectionId: mergedActionsSection.section_id || '',
        title: mergedActionsSection.title || '',
        mergeMode: mergedActionsSection.merge_mode || '',
        items: Array.isArray(mergedActionsSection.items) ? mergedActionsSection.items : [],
      },
      latestConclusion: {
        sectionId: latestConclusionSection.section_id || '',
        title: latestConclusionSection.title || '',
        mergeMode: latestConclusionSection.merge_mode || '',
        text: latestConclusionSection.text || '',
      },
    },
    parentStateSurface: {
      intentLabel: parentStateSurface.intent_label || '',
      entityCount: Number(parentStateSurface.entity_count || 0),
      focusCount: Number(parentStateSurface.focus_count || 0),
      actionCount: Number(parentStateSurface.action_count || 0),
      primaryEntities: Array.isArray(parentStateSurface.primary_entities) ? parentStateSurface.primary_entities : [],
      latestConclusion: parentStateSurface.latest_conclusion || '',
    },
  }
}

function buildSkillContract(value) {
  const contract = normalizeContractObject(value)
  return {
    connected: Object.keys(contract).length > 0,
    contract_version: contract.contract_version || '',
    total_definitions: Number(contract.total_definitions || 0),
    definitions: Array.isArray(contract.definitions) ? contract.definitions : [],
  }
}

function buildMemoryContract(value) {
  const contract = normalizeContractObject(value)
  return {
    connected: Object.keys(contract).length > 0,
    contract_version: contract.contract_version || '',
    active: Boolean(contract.active),
    loaded_layers: Array.isArray(contract.loaded_layers) ? contract.loaded_layers : [],
    missing_layers: Array.isArray(contract.missing_layers) ? contract.missing_layers : [],
    memory_entries: Array.isArray(contract.memory_entries) ? contract.memory_entries : [],
    layer_order: Array.isArray(contract.layer_order) ? contract.layer_order : [],
  }
}

function normalizeNestedContract(value) {
  const contract = normalizeContractObject(value)
  return Object.keys(contract).length ? contract : null
}

function formatInlinePair(left, right) {
  const items = [left, right]
    .map(item => String(item || '').trim())
    .filter(Boolean)
  return items.join(' · ') || '-'
}

async function copySnapshotCommand(commandOrItem) {
  await copyRecentSnapshotCommand(commandOrItem)
}

onMounted(async () => {
  await loadProfile()
  refreshRecentSnapshotCommands()
})
</script>

<style scoped>
.runtime-panel {
  width: 100%;
}

.section-head,
.card-head,
.model-title-row,
.provider-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
}

.section-desc,
.muted {
  color: var(--text-tertiary);
  font-size: 0.875rem;
}

.path-line {
  display: block;
  color: var(--text-tertiary);
  font-size: 0.82rem;
  word-break: break-all;
}

.editable-grid {
  display: grid;
  gap: var(--space-md);
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  margin-top: var(--space-md);
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.field-select {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.edit-actions {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-top: var(--space-md);
}

.provider-toggle-grid {
  display: grid;
  gap: var(--space-sm);
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  margin-top: var(--space-lg);
}

.provider-toggle {
  display: flex;
  gap: var(--space-sm);
  align-items: flex-start;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
  padding: var(--space-md);
}

.trace-toggle-row {
  display: flex;
  gap: var(--space-sm);
  align-items: flex-start;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
  padding: var(--space-md);
  cursor: pointer;
}

.trace-toggle-row.active {
  border-color: rgba(16, 185, 129, 0.45);
  background: rgba(16, 185, 129, 0.08);
}

.trace-toggle-row input {
  margin-top: 2px;
}

.trace-toggle-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.trace-toggle-copy strong {
  color: var(--text-primary);
}

.trace-toggle-copy small {
  color: var(--text-secondary);
  line-height: 1.45;
}

.link-btn {
  padding: 0;
  border: none;
  background: transparent;
  color: var(--primary);
  cursor: pointer;
}

.link-btn:hover {
  text-decoration: underline;
}

.reference-slice-empty {
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.reference-slice-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  padding-top: var(--space-sm);
  margin-top: var(--space-sm);
  border-top: 1px solid rgba(148, 163, 184, 0.18);
}

.reference-slice-list {
  margin: 0;
  padding-left: 1rem;
}

.reference-slice-list li + li {
  margin-top: 4px;
}

.provider-toggle-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 0.8rem;
}

.save-message {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.summary-grid,
.provider-grid {
  display: grid;
  gap: var(--space-md);
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  margin-bottom: var(--space-lg);
}

.contract-summary {
  margin-top: var(--space-md);
  color: var(--text-secondary);
  line-height: 1.7;
}

.contract-grid {
  display: grid;
  gap: var(--space-md);
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  margin-top: var(--space-lg);
}

.runtime-contract-grid {
  margin-bottom: 0;
}

.contract-block {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
  padding: var(--space-md);
}

.runtime-detail-block {
  margin-top: var(--space-lg);
}

.contract-placeholder {
  margin-top: var(--space-md);
  color: var(--text-tertiary);
  font-size: 0.84rem;
}

.contract-block h4 {
  margin-bottom: var(--space-sm);
  color: var(--text-primary);
}

.contract-block ul {
  margin: 0;
  padding-left: 1rem;
  color: var(--text-secondary);
}

.contract-block li + li {
  margin-top: 6px;
}

.summary-card,
.provider-card,
.panel-card,
.model-item {
  border: 1px solid var(--border-color);
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
}

.summary-card {
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.summary-note {
  color: var(--text-tertiary);
  line-height: 1.4;
}

.summary-label {
  font-size: 0.8rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.panel-card {
  padding: var(--space-lg);
  margin-bottom: var(--space-lg);
}

.model-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  margin-top: var(--space-md);
}

.model-item,
.provider-card {
  padding: var(--space-md);
}

.model-meta,
.model-submeta,
.provider-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-top: var(--space-xs);
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.provider-endpoint {
  margin: var(--space-sm) 0;
  color: var(--text-tertiary);
  word-break: break-all;
  font-size: 0.875rem;
}

.catalog-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  margin-top: var(--space-sm);
}

.capability-pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(59, 130, 246, 0.12);
  color: var(--text-secondary);
  font-size: 0.8rem;
}

.status-badge {
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 0.75rem;
  border: 1px solid var(--border-color);
}

.status-badge.online {
  background: rgba(34, 197, 94, 0.14);
  color: #15803d;
}

.status-badge.offline {
  background: rgba(245, 158, 11, 0.14);
  color: #b45309;
}

.secondary-btn {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-color);
  background: var(--bg-elevated);
  color: var(--text-primary);
  border-radius: var(--radius-md);
  cursor: pointer;
}

.inline-filter-btn.active {
  border-color: rgba(37, 99, 235, 0.45);
  background: rgba(37, 99, 235, 0.12);
  color: #1d4ed8;
}

.summary-action-btn {
  margin-top: var(--space-sm);
  align-self: flex-start;
}


.adapter-pilot-result {
  margin-top: var(--space-sm);
}

.inline-error {
  color: #dc2626;
  margin: var(--space-sm) 0;
}
</style>
