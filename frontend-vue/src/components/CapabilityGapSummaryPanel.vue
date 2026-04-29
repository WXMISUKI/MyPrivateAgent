<template>
  <section class="settings-section gap-panel">
    <div class="section-head">
      <div>
        <h2>能力缺口统计</h2>
        <p class="section-desc">用于盘点当前框架最常缺的能力类型，帮助后续决定补工具、Skill 还是 MCP。这里反映的是框架治理缺口，不是单次回答质量评分。</p>
      </div>
      <button class="secondary-btn" :disabled="loading" @click="loadSummary">
        {{ loading ? '刷新中...' : '刷新统计' }}
      </button>
    </div>

    <p v-if="error" class="inline-error">{{ error }}</p>
    <p v-if="bulkOperationResult" class="inline-info">{{ bulkOperationResult }}</p>

    <div v-if="bulkOperationHistory.length" class="panel-card">
      <div class="card-head">
        <h3>批量操作审计</h3>
        <button class="secondary-btn" @click="clearBulkOperationHistory">清空记录</button>
      </div>
      <div class="mini-list">
        <div v-for="item in bulkOperationHistory" :key="item.id" class="gap-item">
          <strong>{{ item.time }} · {{ formatEscalationType(item.recommendationType) }}</strong>
          <div class="gap-count">成功 {{ item.successCount }}，失败 {{ item.failureCount }}</div>
          <div v-if="item.failedActions.length" class="gap-count">失败动作：{{ item.failedActions.join('、') }}</div>
          <div class="gap-count">负责人：{{ item.updatedBy || 'runtime-panel' }} · 备注：{{ item.note || '无' }}</div>
        </div>
      </div>
    </div>

    <div class="filter-grid">
      <label class="field-block">
        <span>时间窗口</span>
        <select v-model="selectedWindowDays" class="field-select">
          <option value="7">近 7 天</option>
          <option value="14">近 14 天</option>
          <option value="30">近 30 天</option>
          <option value="0">全部</option>
        </select>
      </label>
      <label class="field-block">
        <span>缺口类型</span>
        <select v-model="selectedMissingPart" class="field-select">
          <option value="">全部</option>
          <option v-for="part in availableMissingParts" :key="part" :value="part">
            {{ formatPart(part) }}
          </option>
        </select>
      </label>
      <label class="field-block">
        <span>关键词筛选</span>
        <input v-model.trim="keyword" type="text" class="field-input" placeholder="例如：舟山 / 交通 / 攻略" />
      </label>
      <label class="field-block">
        <span>复合任务模板</span>
        <select v-model="selectedProfile" class="field-select">
          <option value="">全部</option>
          <option v-for="profile in availableProfiles" :key="profile" :value="profile">
            {{ formatProfile(profile) }}
          </option>
        </select>
      </label>
      <label class="field-block">
        <span>收尾阶段</span>
        <select v-model="selectedCompletionStage" class="field-select">
          <option value="">全部</option>
          <option v-for="stage in availableCompletionStages" :key="stage" :value="stage">
            {{ formatStage(stage) }}
          </option>
        </select>
      </label>
      <label class="field-block">
        <span>错误类型</span>
        <select v-model="selectedErrorCategory" class="field-select">
          <option value="">全部</option>
          <option v-for="category in availableErrorCategories" :key="category" :value="category">
            {{ formatErrorCategory(category) }}
          </option>
        </select>
      </label>
      <label class="field-block">
        <span>Hook 事件</span>
        <select v-model="selectedHookEventType" class="field-select">
          <option value="">全部</option>
          <option v-for="eventType in availableHookEventTypes" :key="eventType" :value="eventType">
            {{ formatHookEventType(eventType) }}
          </option>
        </select>
      </label>
      <label class="field-block">
        <span>Subagent 角色</span>
        <select v-model="selectedSubagentRole" class="field-select">
          <option value="">全部</option>
          <option v-for="role in availableSubagentRoles" :key="role" :value="role">
            {{ formatSubagentRole(role) }}
          </option>
        </select>
      </label>
      <label class="field-block">
        <span>Provider</span>
        <select v-model="selectedProvider" class="field-select">
          <option value="">全部</option>
          <option v-for="provider in availableProviders" :key="provider" :value="provider">
            {{ provider }}
          </option>
        </select>
      </label>
      <label class="field-block">
        <span>模型</span>
        <select v-model="selectedModelName" class="field-select">
          <option value="">全部</option>
          <option v-for="model in availableModels" :key="model" :value="model">
            {{ model }}
          </option>
        </select>
      </label>
      <div class="filter-actions">
        <button class="secondary-btn" :disabled="loading" @click="loadSummary">
          {{ loading ? '筛选中...' : '应用筛选' }}
        </button>
      </div>
    </div>

    <div v-if="summary" class="summary-grid">
      <div class="summary-card">
        <span class="summary-label">缺口事件数</span>
        <strong>{{ summary.total_gap_events || 0 }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">缺口类型数</span>
        <strong>{{ (summary.top_missing_parts || []).length }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">未闭环动作</span>
        <strong>{{ summary.non_closed_action_count ?? computedNonClosedActionCount }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">当前筛选</span>
        <strong>{{ activeFilterLabel }}</strong>
      </div>
    </div>

    <div v-if="summary?.top_missing_parts?.length" class="panel-card">
      <div class="card-head">
        <h3>高频缺口</h3>
        <span class="muted">按近期 run trace 聚合</span>
      </div>
      <div class="gap-list">
        <div v-for="item in summary.top_missing_parts" :key="item.name" class="gap-item">
          <strong>{{ formatPart(item.name) }}</strong>
          <span class="gap-count">{{ item.count }} 次</span>
        </div>
      </div>
    </div>

    <div v-if="summary?.top_profiles?.length || summary?.top_completion_stages?.length || summary?.top_error_categories?.length || summary?.top_hook_event_types?.length || summary?.top_subagent_roles?.length || summary?.top_providers?.length || summary?.top_models?.length" class="panel-card">
      <div class="card-head">
        <h3>治理维度</h3>
        <span class="muted">按任务模板 / 收尾阶段 / 错误类型 / Hook / Subagent 聚合</span>
      </div>
      <div class="governance-grid">
        <div v-if="summary?.top_profiles?.length">
          <h4>复合任务模板</h4>
          <div class="mini-list">
            <div v-for="item in summary.top_profiles" :key="item.name" class="gap-item">
              <strong>{{ formatProfile(item.name) }}</strong>
              <span class="gap-count">{{ item.count }} 次</span>
            </div>
          </div>
        </div>
        <div v-if="summary?.top_completion_stages?.length">
          <h4>收尾阶段</h4>
          <div class="mini-list">
            <div v-for="item in summary.top_completion_stages" :key="item.name" class="gap-item">
              <strong>{{ formatStage(item.name) }}</strong>
              <span class="gap-count">{{ item.count }} 次</span>
            </div>
          </div>
        </div>
        <div v-if="summary?.top_error_categories?.length">
          <h4>工具/Provider 错误</h4>
          <div class="mini-list">
            <div v-for="item in summary.top_error_categories" :key="item.name" class="gap-item">
              <strong>{{ formatErrorCategory(item.name) }}</strong>
              <span class="gap-count">{{ item.count }} 次</span>
            </div>
          </div>
        </div>
        <div v-if="summary?.top_hook_event_types?.length">
          <h4>Hook 治理事件</h4>
          <div class="mini-list">
            <div v-for="item in summary.top_hook_event_types" :key="item.name" class="gap-item">
              <strong>{{ formatHookEventType(item.name) }}</strong>
              <span class="gap-count">{{ item.count }} 次</span>
            </div>
          </div>
        </div>
        <div v-if="summary?.top_subagent_roles?.length">
          <h4>Subagent 角色负载</h4>
          <div class="mini-list">
            <div v-for="item in summary.top_subagent_roles" :key="item.name" class="gap-item">
              <strong>{{ formatSubagentRole(item.name) }}</strong>
              <span class="gap-count">{{ item.count }} 次</span>
            </div>
          </div>
        </div>
        <div v-if="summary?.top_providers?.length">
          <h4>Provider 分布</h4>
          <div class="mini-list">
            <div v-for="item in summary.top_providers" :key="item.name" class="gap-item">
              <strong>{{ item.name }}</strong>
              <span class="gap-count">{{ item.count }} 次</span>
            </div>
          </div>
        </div>
        <div v-if="summary?.top_models?.length">
          <h4>模型分布</h4>
          <div class="mini-list">
            <div v-for="item in summary.top_models" :key="item.name" class="gap-item">
              <strong>{{ item.name }}</strong>
              <span class="gap-count">{{ item.count }} 次</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="summary?.trend_by_day?.length || summary?.provider_model_pairs?.length || summary?.profile_provider_model_pairs?.length" class="panel-card">
      <div class="card-head">
        <h3>趋势与对比</h3>
        <span class="muted">按日期趋势与 Provider-模型组合聚合</span>
      </div>
      <div v-if="summary?.window_comparison?.window_days" class="summary-grid">
        <div class="summary-card">
          <span class="summary-label">本窗口事件</span>
          <strong>{{ summary.window_comparison.current_count ?? 0 }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">上窗口事件</span>
          <strong>{{ summary.window_comparison.previous_count ?? 0 }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">环比变化</span>
          <strong>{{ formatDelta(summary.window_comparison.delta_count, summary.window_comparison.delta_ratio) }}</strong>
        </div>
      </div>
      <div class="governance-grid">
        <div v-if="summary?.trend_by_day?.length">
          <h4>按日缺口趋势</h4>
          <div class="mini-list">
            <div v-for="item in summary.trend_by_day" :key="item.date" class="gap-item">
              <strong>{{ item.date }}</strong>
              <span class="gap-count">{{ item.count }} 次</span>
            </div>
          </div>
        </div>
        <div v-if="summary?.provider_model_pairs?.length">
          <h4>Provider-模型对比</h4>
          <div class="mini-list">
            <div v-for="item in summary.provider_model_pairs" :key="`${item.provider}-${item.model}`" class="gap-item">
              <strong>{{ item.provider }} / {{ item.model }}</strong>
              <span class="gap-count">{{ item.count }} 次</span>
            </div>
          </div>
        </div>
        <div v-if="summary?.profile_provider_model_pairs?.length">
          <h4>模板-Provider-模型对比</h4>
          <div class="mini-list">
            <div v-for="item in summary.profile_provider_model_pairs" :key="`${item.profile}-${item.provider}-${item.model}`" class="gap-item">
              <strong>{{ formatProfile(item.profile) }} / {{ item.provider }} / {{ item.model }}</strong>
              <span class="gap-count">{{ item.count }} 次</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="summary?.top_regression_risk_models?.length" class="panel-card">
      <div class="card-head">
        <h3>Top 回归风险模型</h3>
        <span class="muted">按当前窗口较上窗口缺口增量排序</span>
      </div>
      <div class="mini-list">
        <div
          v-for="item in summary.top_regression_risk_models"
          :key="`${item.provider}-${item.model}`"
          class="gap-item"
        >
          <strong>{{ item.provider }} / {{ item.model }}</strong>
          <span class="gap-count">
            当前 {{ item.current_count }}，上期 {{ item.previous_count }}，Δ {{ item.delta_count }}（{{ formatRisk(item.risk_level) }}）
          </span>
        </div>
      </div>
    </div>

    <div v-if="summary?.benchmark_health" class="panel-card">
      <div class="card-head">
        <h3>回归健康度</h3>
        <span class="muted">阶段六：执行链关键断言自动评测</span>
      </div>
      <div class="summary-grid">
        <div class="summary-card">
          <span class="summary-label">健康分</span>
          <strong>{{ summary.benchmark_health.score ?? 0 }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">门禁状态</span>
          <strong>{{ summary.benchmark_health.gate_passed ? '通过' : '未通过' }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">断言通过</span>
          <strong>{{ summary.benchmark_health.passed_assertions ?? 0 }} / {{ summary.benchmark_health.total_assertions ?? 0 }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">覆盖案例</span>
          <strong>{{ summary.benchmark_health.total_cases ?? 0 }}</strong>
        </div>
      </div>
      <div class="mini-list">
        <div class="gap-item">
          <strong>门禁阈值</strong>
          <span class="gap-count">
            {{ summary.benchmark_health.threshold_score ?? 0 }} 分
          </span>
        </div>
        <div class="gap-item">
          <strong>模板覆盖</strong>
          <span class="gap-count">
            已覆盖 {{ (summary.benchmark_health.covered_profiles || []).join(', ') || '无' }}
            <template v-if="(summary.benchmark_health.missing_profiles || []).length">
              · 缺失 {{ summary.benchmark_health.missing_profiles.join(', ') }}
            </template>
          </span>
        </div>
        <div class="gap-item">
          <strong>固定用例覆盖</strong>
          <span class="gap-count">
            {{ summary.benchmark_health.benchmark_catalog_matched ?? 0 }} / {{ summary.benchmark_health.benchmark_catalog_total ?? 0 }}
            （{{ formatPercent(summary.benchmark_health.benchmark_catalog_coverage_ratio) }}，
            阈值 {{ formatPercent(summary.benchmark_health.benchmark_catalog_coverage_threshold) }}）
          </span>
        </div>
      </div>
      <div v-if="summary?.benchmark_health?.assertions?.length" class="mini-list">
        <div v-for="item in summary.benchmark_health.assertions" :key="item.id" class="gap-item">
          <strong>{{ item.label }}</strong>
          <span class="gap-count">
            {{ item.passed ? '通过' : '未通过' }} · 检查 {{ item.checked }} · 失败 {{ item.failed }}
          </span>
        </div>
      </div>
      <div v-if="summary?.benchmark_health?.scenario_coverage?.length" class="mini-list">
        <div class="gap-item" v-for="item in summary.benchmark_health.scenario_coverage" :key="item.scenario">
          <strong>场景 {{ item.scenario }}</strong>
          <span class="gap-count">{{ item.matched }} / {{ item.total }}（{{ formatPercent(item.ratio) }}）</span>
        </div>
      </div>
      <div v-if="summary?.benchmark_health?.benchmark_catalog_unmatched?.length" class="mini-list">
        <div class="gap-item" v-for="item in summary.benchmark_health.benchmark_catalog_unmatched" :key="item.id">
          <strong>{{ item.id }} · {{ item.scenario }}</strong>
          <span class="gap-count">{{ item.reason || '未匹配' }}</span>
          <span v-if="item.remediation" class="gap-count">建议：{{ item.remediation }}</span>
          <span v-if="item.remediation_action_id" class="gap-count">
            动作ID：{{ item.remediation_action_id }}
          </span>
        </div>
      </div>
      <div v-if="summary?.benchmark_health?.action_playbook" class="mini-list">
        <div class="gap-item" v-for="(action, actionId) in summary.benchmark_health.action_playbook" :key="actionId">
          <strong>{{ actionId }} · {{ action.title }}</strong>
          <span class="gap-count">{{ action.description }}</span>
        </div>
      </div>
    </div>

    <div v-if="summary?.escalation_recommendations?.length" class="panel-card">
      <div class="card-head">
        <h3>门禁升级建议</h3>
        <span class="muted">doctor 门禁失败后的优先整改路径</span>
      </div>
      <div class="mini-list">
        <div v-for="item in summary.escalation_recommendations" :key="`${item.type}-${item.severity}`" class="gap-item">
          <strong>{{ formatEscalationType(item.type) }}（{{ formatEscalationSeverity(item.severity) }}）</strong>
          <div class="gap-count">{{ item.message }}</div>
          <div v-if="resolveRecommendationActions(item).length" class="remediation-status-row">
            <input
              v-model.trim="bulkRemediationInputs[item.type].updated_by"
              type="text"
              class="field-input remediation-inline-input"
              placeholder="负责人（updated_by）"
            />
            <input
              v-model.trim="bulkRemediationInputs[item.type].note"
              type="text"
              class="field-input remediation-inline-input"
              placeholder="备注（note）"
            />
            <button
              class="secondary-btn"
              @click="promoteRecommendationActions(item)"
            >
              批量标记进行中
            </button>
          </div>
          <div v-if="resolveRecommendationActions(item).length" class="remediation-status-row">
            <button
              v-for="actionId in resolveRecommendationActions(item)"
              :key="`promote-${item.type}-${actionId}`"
              class="secondary-btn"
              @click="promoteActionToInProgress(actionId)"
            >
              标记进行中：{{ actionId }}
            </button>
          </div>
          <div v-if="item.blocked_actions?.length" class="gap-count">
            阻塞动作：{{ item.blocked_actions.join('、') }}
          </div>
          <div v-if="item.missing_profiles?.length" class="gap-count">
            缺失模板：{{ item.missing_profiles.map(formatProfile).join('、') }}
          </div>
          <ul v-if="item.next_steps?.length" class="suggestion-list escalation-steps">
            <li v-for="step in item.next_steps" :key="step">{{ step }}</li>
          </ul>
        </div>
      </div>
    </div>

    <div v-if="groupedRemediationTargets.length" class="panel-card">
      <div class="card-head">
        <h3>整改入口（可分派）</h3>
        <span class="muted">按 owner / module 聚合</span>
      </div>
      <div class="summary-grid remediation-summary-grid">
        <div class="summary-card">
          <span class="summary-label">Open</span>
          <strong>{{ remediationStatusCounts.open || 0 }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">In Progress</span>
          <strong>{{ remediationStatusCounts.in_progress || 0 }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">Blocked</span>
          <strong>{{ remediationStatusCounts.blocked || 0 }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">Done</span>
          <strong>{{ remediationStatusCounts.done || 0 }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">Verified</span>
          <strong>{{ remediationStatusCounts.verified || 0 }}</strong>
        </div>
      </div>
      <div v-if="summary?.remediation_progress" class="summary-grid remediation-summary-grid">
        <div class="summary-card">
          <span class="summary-label">最近有进展</span>
          <strong>{{ summary.remediation_progress.recent_progress_count || 0 }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">长期阻塞</span>
          <strong>{{ summary.remediation_progress.long_blocked_count || 0 }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">待启动</span>
          <strong>{{ summary.remediation_progress.pending_start_count || 0 }}</strong>
        </div>
      </div>
      <div class="filter-grid remediation-filter-grid">
        <label class="field-block">
          <span>整改状态</span>
          <select v-model="selectedRemediationStatus" class="field-select">
            <option value="">全部</option>
            <option value="open">open</option>
            <option value="in_progress">in_progress</option>
            <option value="blocked">blocked</option>
            <option value="done">done</option>
            <option value="verified">verified</option>
          </select>
        </label>
        <label class="field-block checkbox-inline">
          <input v-model="onlyNonClosedActions" type="checkbox" />
          <span>只看未闭环（open/in_progress/blocked）</span>
        </label>
      </div>
      <div v-if="summary?.remediation_progress" class="governance-grid">
        <div v-if="summary.remediation_progress.recent_progress?.length">
          <h4>最近 {{ summary.remediation_progress.window_days }} 天有进展</h4>
          <div class="mini-list">
            <div v-for="item in summary.remediation_progress.recent_progress" :key="`recent-${item.action_id}`" class="gap-item">
              <strong>{{ item.action_id }} · {{ item.playbook_title || '未命名动作' }}</strong>
              <span class="gap-count">{{ formatOwner(item.owner) }} / {{ item.module || '未标注模块' }} · {{ item.status }} · {{ item.updated_at || '无时间' }}</span>
            </div>
          </div>
        </div>
        <div v-if="summary.remediation_progress.long_blocked?.length">
          <h4>长期阻塞（>30天）</h4>
          <div class="mini-list">
            <div v-for="item in summary.remediation_progress.long_blocked" :key="`blocked-${item.action_id}`" class="gap-item">
              <strong>{{ item.action_id }} · {{ item.playbook_title || '未命名动作' }}</strong>
              <span class="gap-count">{{ formatOwner(item.owner) }} / {{ item.module || '未标注模块' }} · {{ item.updated_at || '无时间' }}</span>
            </div>
          </div>
        </div>
        <div v-if="summary.remediation_progress.pending_start?.length">
          <h4>待启动动作</h4>
          <div class="mini-list">
            <div v-for="item in summary.remediation_progress.pending_start" :key="`open-${item.action_id}`" class="gap-item">
              <strong>{{ item.action_id }} · {{ item.playbook_title || '未命名动作' }}</strong>
              <span class="gap-count">{{ formatOwner(item.owner) }} / {{ item.module || '未标注模块' }}</span>
            </div>
          </div>
        </div>
      </div>
      <div class="mini-list">
        <div v-for="group in groupedRemediationTargets" :key="`${group.owner}-${group.module}`" class="gap-item remediation-group">
          <strong>{{ formatOwner(group.owner) }} / {{ group.module || '未标注模块' }}</strong>
          <span class="gap-count">动作 {{ group.actionCount }} · 待处理案例 {{ group.caseCount }}</span>
          <div class="mini-list remediation-actions">
            <div v-for="target in group.targets" :key="target.action_id" class="gap-item">
              <strong>{{ target.action_id }} · {{ target.playbook_title || '未命名动作' }}</strong>
              <div class="remediation-status-row">
                <select class="field-select remediation-status-select" :value="target.status || 'open'" @change="onChangeRemediationStatus(target, $event)">
                  <option value="open">open</option>
                  <option value="in_progress">in_progress</option>
                  <option value="blocked">blocked</option>
                  <option value="done">done</option>
                  <option value="verified">verified</option>
                </select>
                <span class="gap-count" v-if="target.status_detail?.updated_by">by {{ target.status_detail.updated_by }}</span>
              </div>
              <span class="gap-count">建议文件：{{ (target.files || []).join('、') || '未标注' }}</span>
              <span class="gap-count" v-if="target.status_detail?.note">备注：{{ target.status_detail.note }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="summary?.suggested_investments?.length" class="panel-card">
      <div class="card-head">
        <h3>建议补强方向</h3>
      </div>
      <ul class="suggestion-list">
        <li v-for="item in summary.suggested_investments" :key="item">{{ item }}</li>
      </ul>
    </div>

    <div v-if="summary?.recent_examples?.length" class="panel-card">
      <div class="card-head">
        <h3>近期案例</h3>
      </div>
      <div class="example-list">
        <div v-for="example in summary.recent_examples" :key="`${example.plan_item_id}-${example.timestamp}`" class="example-item">
          <div class="example-title">{{ example.title }}</div>
          <div class="example-meta">缺口：{{ (example.missing_parts || []).map(formatPart).join('、') || '未标注' }}</div>
          <div v-if="example.detail" class="example-detail">{{ example.detail }}</div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { capabilityGapApi } from '../api'

const STORAGE_KEYS = {
  auditHistory: 'cap_gap_bulk_audit_history',
  localStatusMap: 'cap_gap_local_status_map',
  cachedSummary: 'cap_gap_cached_summary'
}

const summary = ref(null)
const loading = ref(false)
const error = ref('')
const selectedMissingPart = ref('')
const keyword = ref('')
const selectedProfile = ref('')
const selectedCompletionStage = ref('')
const selectedErrorCategory = ref('')
const selectedHookEventType = ref('')
const selectedSubagentRole = ref('')
const selectedProvider = ref('')
const selectedModelName = ref('')
const selectedWindowDays = ref('7')
const selectedRemediationStatus = ref('')
const onlyNonClosedActions = ref(false)
const bulkRemediationInputs = ref({})
const bulkOperationResult = ref('')
const bulkOperationHistory = ref([])
const localStatusMap = ref({})

const partLabelMap = {
  weather: '天气',
  transport: '交通',
  play: '游玩/行程'
}

const profileLabelMap = {
  travel_planning: '旅行规划',
  research_compare: '研究/对比',
  planning: '任务规划'
}

const stageLabelMap = {
  retry: '补查',
  boundary_fallback: '边界收尾',
  timeout_fallback: '超时收尾',
  finalized: '最终收尾'
}

const errorCategoryLabelMap = {
  provider_timeout: 'Provider 超时',
  provider_connection: 'Provider 连接失败',
  provider_network: 'Provider 网络错误',
  provider_rate_limit: 'Provider 限流',
  provider_unavailable: 'Provider 不可用',
  tool_validation: '工具参数校验失败',
  missing_tool: '缺少工具',
  unknown_error: '未知错误'
}

const hookEventTypeLabelMap = {
  pre_tool_use_blocked: 'PreToolUse 阻断'
}

const subagentRoleLabelMap = {
  planner: 'planner',
  researcher: 'researcher',
  executor: 'executor',
  backend: 'backend',
  frontend: 'frontend',
  qa: 'qa',
  docs: 'docs'
}

const escalationTypeLabelMap = {
  open_action_overflow: '未闭环动作超阈值',
  long_blocked_overflow: '长期阻塞动作超阈值',
  benchmark_profile_gap: '基准模板覆盖不足'
}

const escalationSeverityLabelMap = {
  high: '高优先级',
  medium: '中优先级',
  low: '低优先级'
}

const ownerLabelMap = {
  'agent-core': 'Agent Core',
  'agent-governance': 'Agent Governance',
  'runtime-governance': 'Runtime Governance',
  planning: 'Planning',
  tooling: 'Tooling',
  'qa-governance': 'QA Governance'
}

const availableMissingParts = computed(() => summary.value?.available_missing_parts || [])
const availableProfiles = computed(() => summary.value?.available_profiles || [])
const availableCompletionStages = computed(() => summary.value?.available_completion_stages || [])
const availableErrorCategories = computed(() => summary.value?.available_error_categories || [])
const availableHookEventTypes = computed(() => summary.value?.available_hook_event_types || [])
const availableSubagentRoles = computed(() => summary.value?.available_subagent_roles || [])
const availableProviders = computed(() => summary.value?.available_providers || [])
const availableModels = computed(() => summary.value?.available_models || [])
const groupedRemediationTargets = computed(() => {
  const targets = summary.value?.remediation_targets || []
  const pendingActions = summary.value?.pending_actions || []
  const selectedStatus = String(selectedRemediationStatus.value || '').trim()
  const groupMap = new Map()
  for (const target of targets) {
    const targetStatus = String(target?.status || 'open').trim()
    if (selectedStatus && selectedStatus !== targetStatus) {
      continue
    }
    if (onlyNonClosedActions.value && !['open', 'in_progress', 'blocked'].includes(targetStatus)) {
      continue
    }
    const owner = String(target?.owner || '').trim() || 'unassigned'
    const moduleName = String(target?.module || '').trim() || 'unassigned'
    const key = `${owner}::${moduleName}`
    if (!groupMap.has(key)) {
      groupMap.set(key, { owner, module: moduleName, targets: [], actionCount: 0, caseCount: 0 })
    }
    const group = groupMap.get(key)
    group.targets.push(target)
    group.actionCount += 1
    group.caseCount += pendingActions.filter(
      action => String(action?.action_id || '').trim() === String(target?.action_id || '').trim()
    ).length
  }
  return Array.from(groupMap.values()).sort((a, b) => b.caseCount - a.caseCount || b.actionCount - a.actionCount)
})
const remediationStatusCounts = computed(() => {
  if (summary.value?.remediation_status_counts) {
    return summary.value.remediation_status_counts
  }
  const counters = { open: 0, in_progress: 0, blocked: 0, done: 0, verified: 0 }
  for (const item of summary.value?.remediation_targets || []) {
    const status = String(item?.status || 'open').trim()
    if (!(status in counters)) {
      counters[status] = 0
    }
    counters[status] += 1
  }
  return counters
})
const computedNonClosedActionCount = computed(() => {
  const counters = remediationStatusCounts.value || {}
  return Number(counters.open || 0) + Number(counters.in_progress || 0) + Number(counters.blocked || 0)
})
const activeFilterLabel = computed(() => {
  const labels = []
  if (selectedMissingPart.value) {
    labels.push(formatPart(selectedMissingPart.value))
  }
  if (keyword.value) {
    labels.push(`关键词: ${keyword.value}`)
  }
  if (selectedProfile.value) {
    labels.push(`模板: ${formatProfile(selectedProfile.value)}`)
  }
  if (selectedCompletionStage.value) {
    labels.push(`阶段: ${formatStage(selectedCompletionStage.value)}`)
  }
  if (selectedErrorCategory.value) {
    labels.push(`错误: ${formatErrorCategory(selectedErrorCategory.value)}`)
  }
  if (selectedHookEventType.value) {
    labels.push(`Hook: ${formatHookEventType(selectedHookEventType.value)}`)
  }
  if (selectedSubagentRole.value) {
    labels.push(`Subagent: ${formatSubagentRole(selectedSubagentRole.value)}`)
  }
  if (selectedProvider.value) {
    labels.push(`Provider: ${selectedProvider.value}`)
  }
  if (selectedModelName.value) {
    labels.push(`模型: ${selectedModelName.value}`)
  }
  if (selectedWindowDays.value && selectedWindowDays.value !== '0') {
    labels.push(`窗口: ${selectedWindowDays.value}天`)
  }
  return labels.length ? labels.join(' / ') : '未筛选'
})

function formatPart(name) {
  return partLabelMap[name] || name
}

function formatProfile(name) {
  return profileLabelMap[name] || name
}

function formatStage(name) {
  return stageLabelMap[name] || name
}

function formatErrorCategory(name) {
  return errorCategoryLabelMap[name] || name
}

function formatHookEventType(name) {
  return hookEventTypeLabelMap[name] || name
}

function formatSubagentRole(name) {
  return subagentRoleLabelMap[name] || name
}

function formatOwner(name) {
  return ownerLabelMap[name] || name
}

function formatEscalationType(name) {
  return escalationTypeLabelMap[name] || name
}

function formatEscalationSeverity(name) {
  return escalationSeverityLabelMap[name] || name
}

function formatDelta(deltaCount, deltaRatio) {
  const delta = Number(deltaCount || 0)
  const ratio = typeof deltaRatio === 'number' ? `${(deltaRatio * 100).toFixed(1)}%` : 'N/A'
  const sign = delta > 0 ? '+' : ''
  return `${sign}${delta} / ${ratio}`
}

function formatRisk(level) {
  if (level === 'high') return '高风险'
  if (level === 'medium') return '中风险'
  return '稳定'
}

function formatPercent(value) {
  const number = Number(value || 0)
  return `${(number * 100).toFixed(1)}%`
}

async function loadSummary() {
  loading.value = true
  error.value = ''
  bulkOperationResult.value = ''
  try {
    const response = await capabilityGapApi.getSummary({
      limit: 100,
      missing_part: selectedMissingPart.value || undefined,
      keyword: keyword.value || undefined,
      profile: selectedProfile.value || undefined,
      completion_stage: selectedCompletionStage.value || undefined,
      error_category: selectedErrorCategory.value || undefined,
      hook_event_type: selectedHookEventType.value || undefined,
      subagent_role: selectedSubagentRole.value || undefined,
      provider: selectedProvider.value || undefined,
      model_name: selectedModelName.value || undefined,
      window_days: Number(selectedWindowDays.value || 0) || undefined
    })
    summary.value = applyLocalRemediationState(response.data || null)
    persistJson(STORAGE_KEYS.cachedSummary, summary.value)
    syncBulkRemediationInputs()
  } catch (err) {
    const cachedSummary = readJson(STORAGE_KEYS.cachedSummary, null)
    if (cachedSummary) {
      summary.value = applyLocalRemediationState(cachedSummary)
      error.value = '后端不可用，已切换到本地缓存视图。'
      syncBulkRemediationInputs()
    } else {
      error.value = err?.response?.data?.detail || err?.message || '加载能力缺口统计失败'
    }
  } finally {
    loading.value = false
  }
}

function syncBulkRemediationInputs() {
  const next = {}
  for (const item of summary.value?.escalation_recommendations || []) {
    const key = String(item?.type || '').trim()
    if (!key) continue
    next[key] = bulkRemediationInputs.value[key] || { updated_by: 'runtime-panel', note: '' }
  }
  bulkRemediationInputs.value = next
}

async function onChangeRemediationStatus(target, event) {
  const nextStatus = String(event?.target?.value || '').trim()
  if (!nextStatus || !target?.action_id) {
    return
  }
  try {
    await capabilityGapApi.updateRemediationStatus(target.action_id, {
      status: nextStatus,
      owner: target.owner || undefined,
      module: target.module || undefined,
      updated_by: 'runtime-panel'
    })
    await loadSummary()
  } catch (err) {
    applyLocalStatusUpdate(target.action_id, {
      status: nextStatus,
      owner: target?.owner || undefined,
      module: target?.module || undefined,
      updated_by: 'runtime-panel'
    })
    summary.value = applyLocalRemediationState(summary.value)
    error.value = '后端不可用，已使用本地状态更新。'
  }
}

function resolveRecommendationActions(item) {
  if (!item || !item.type) return []
  if (Array.isArray(item.blocked_actions) && item.blocked_actions.length) {
    return item.blocked_actions
  }
  if (item.type === 'open_action_overflow') {
    return (summary.value?.remediation_targets || [])
      .filter(target => ['open', 'blocked'].includes(String(target?.status || 'open').trim()))
      .map(target => String(target?.action_id || '').trim())
      .filter(Boolean)
  }
  if (item.type === 'benchmark_profile_gap') {
    return (summary.value?.remediation_targets || [])
      .filter(target => String(target?.action_id || '').trim() === 'expand_profile_benchmark_samples')
      .map(target => String(target?.action_id || '').trim())
      .filter(Boolean)
  }
  return []
}

async function promoteActionToInProgress(actionId) {
  if (!actionId) return
  const target = (summary.value?.remediation_targets || []).find(
    item => String(item?.action_id || '').trim() === String(actionId).trim()
  )
  try {
    await capabilityGapApi.updateRemediationStatus(actionId, {
      status: 'in_progress',
      owner: target?.owner || undefined,
      module: target?.module || undefined,
      updated_by: 'runtime-panel'
    })
    await loadSummary()
  } catch (err) {
    applyLocalStatusUpdate(actionId, {
      status: 'in_progress',
      owner: target?.owner || undefined,
      module: target?.module || undefined,
      updated_by: 'runtime-panel'
    })
    summary.value = applyLocalRemediationState(summary.value)
    error.value = '后端不可用，已使用本地状态更新。'
  }
}

async function promoteRecommendationActions(item) {
  const actionIds = resolveRecommendationActions(item)
  if (!actionIds.length) return
  const actionLabel = actionIds.join('、')
  const confirmed = window.confirm(`将以下动作批量标记为 in_progress：\n${actionLabel}\n\n是否继续？`)
  if (!confirmed) return
  const input = bulkRemediationInputs.value[String(item?.type || '').trim()] || {}
  const updatedBy = String(input.updated_by || '').trim() || 'runtime-panel'
  const note = String(input.note || '').trim()
  let successCount = 0
  const failedActions = []
  try {
    for (const actionId of actionIds) {
      const target = (summary.value?.remediation_targets || []).find(
        current => String(current?.action_id || '').trim() === String(actionId).trim()
      )
      try {
        await capabilityGapApi.updateRemediationStatus(actionId, {
          status: 'in_progress',
          owner: target?.owner || undefined,
          module: target?.module || undefined,
          note: note || undefined,
          updated_by: updatedBy
        })
        successCount += 1
      } catch (_err) {
        applyLocalStatusUpdate(actionId, {
          status: 'in_progress',
          owner: target?.owner || undefined,
          module: target?.module || undefined,
          note: note || undefined,
          updated_by: updatedBy
        })
        failedActions.push(actionId)
      }
    }
    await loadSummary()
    bulkOperationResult.value = failedActions.length
      ? `批量更新完成：成功 ${successCount} 条，失败 ${failedActions.length} 条（${failedActions.join('、')}）。`
      : `批量更新完成：成功 ${successCount} 条。`
    bulkOperationHistory.value.unshift({
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      time: new Date().toLocaleString(),
      recommendationType: String(item?.type || '').trim(),
      successCount,
      failureCount: failedActions.length,
      failedActions,
      updatedBy,
      note
    })
    bulkOperationHistory.value = bulkOperationHistory.value.slice(0, 20)
    persistJson(STORAGE_KEYS.auditHistory, bulkOperationHistory.value)
  } catch (err) {
    error.value = err?.response?.data?.detail || err?.message || '批量更新整改状态失败'
  }
}

function clearBulkOperationHistory() {
  bulkOperationHistory.value = []
  persistJson(STORAGE_KEYS.auditHistory, bulkOperationHistory.value)
}

function readJson(key, fallbackValue) {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return fallbackValue
    return JSON.parse(raw)
  } catch (_err) {
    return fallbackValue
  }
}

function persistJson(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch (_err) {
    // ignore localStorage write failure
  }
}

function applyLocalStatusUpdate(actionId, patch) {
  if (!actionId) return
  localStatusMap.value[String(actionId).trim()] = {
    ...(localStatusMap.value[String(actionId).trim()] || {}),
    action_id: String(actionId).trim(),
    updated_at: new Date().toISOString(),
    ...patch
  }
  persistJson(STORAGE_KEYS.localStatusMap, localStatusMap.value)
}

function applyLocalRemediationState(currentSummary) {
  if (!currentSummary || !Array.isArray(currentSummary.remediation_targets)) {
    return currentSummary
  }
  const data = JSON.parse(JSON.stringify(currentSummary))
  const counters = { open: 0, in_progress: 0, blocked: 0, done: 0, verified: 0 }
  for (const target of data.remediation_targets) {
    const actionId = String(target?.action_id || '').trim()
    const localState = localStatusMap.value[actionId]
    if (localState) {
      target.status = String(localState.status || target.status || 'open')
      target.status_detail = {
        ...(target.status_detail || {}),
        ...localState
      }
    }
    const status = String(target?.status || 'open').trim()
    if (!(status in counters)) counters[status] = 0
    counters[status] += 1
  }
  data.remediation_status_counts = counters
  data.non_closed_action_count =
    Number(counters.open || 0) + Number(counters.in_progress || 0) + Number(counters.blocked || 0)
  return data
}

onMounted(loadSummary)
onMounted(() => {
  bulkOperationHistory.value = readJson(STORAGE_KEYS.auditHistory, [])
  localStatusMap.value = readJson(STORAGE_KEYS.localStatusMap, {})
  if (!summary.value) {
    const cached = readJson(STORAGE_KEYS.cachedSummary, null)
    if (cached) {
      summary.value = applyLocalRemediationState(cached)
      syncBulkRemediationInputs()
    }
  }
})
</script>

<style scoped>
.gap-panel {
  width: 100%;
}

.filter-grid {
  display: grid;
  gap: var(--space-md);
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  margin: 0 0 var(--space-lg);
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.field-select,
.field-input {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.filter-actions {
  display: flex;
  align-items: flex-end;
}

.section-head,
.card-head,
.gap-item {
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

.summary-grid {
  display: grid;
  gap: var(--space-md);
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  margin-bottom: var(--space-lg);
}

.summary-card,
.panel-card,
.example-item,
.gap-item {
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

.gap-list,
.example-list,
.suggestion-list,
.mini-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.remediation-group {
  align-items: flex-start;
}

.remediation-actions {
  width: 100%;
  margin-top: var(--space-sm);
}

.remediation-status-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin: var(--space-xs) 0;
}

.remediation-status-select {
  max-width: 200px;
}

.remediation-inline-input {
  min-width: 180px;
}

.remediation-summary-grid {
  margin-bottom: var(--space-md);
}

.remediation-filter-grid {
  margin-bottom: var(--space-md);
}

.checkbox-inline {
  flex-direction: row;
  align-items: center;
  gap: var(--space-sm);
  margin-top: 1.6rem;
}

.escalation-steps {
  margin-top: var(--space-xs);
}

.governance-grid {
  display: grid;
  gap: var(--space-lg);
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  margin-top: var(--space-md);
}

.gap-item,
.example-item {
  padding: var(--space-md);
}

.gap-count,
.example-meta {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.example-title {
  font-weight: 600;
  color: var(--text-primary);
}

.example-detail {
  margin-top: var(--space-xs);
  color: var(--text-secondary);
  line-height: 1.5;
  white-space: pre-wrap;
}

.secondary-btn {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-color);
  background: var(--bg-elevated);
  color: var(--text-primary);
  border-radius: var(--radius-md);
  cursor: pointer;
}

.inline-error {
  color: #dc2626;
  margin: var(--space-sm) 0;
}

.inline-info {
  color: var(--text-secondary);
  margin: var(--space-sm) 0;
}
</style>
