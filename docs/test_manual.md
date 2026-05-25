# MyPrivateAgent 测试手册

## 1. 目标

这份手册用于后续按固定顺序验证当前智能体 demo 的：

- 可启动性
- 前后端主链路可用性
- 聊天流式稳定性
- Planner / MCP / Skill 等框架能力的展示可用性
- 异常态与停止态是否能平稳收尾

建议每次合并前、对外演示前、以及重要重构后，都至少跑一遍这里的最小用例集。

## 2. 测试范围分层

### 2.1 L0 启动与环境层

目标：

- 能启动
- 默认 SQLite 模式可用
- 核心接口在线

### 2.2 L1 主链路层

目标：

- 登录
- 创建会话
- 发消息
- 流式返回
- 停止生成
- 空响应兜底
- 错误态收尾

### 2.3 L2 框架展示层

目标：

- Planner 可展示
- Tool Call 可展示
- MCP 管理页可展示
- Skill 管理页可展示

### 2.4 L3 回归层

目标：

- 前端自动化通过
- 关键后端 smoke 通过

### 2.5 L4 Framework Adapter 治理层

目标：

- `LocalFakeFrameworkAdapter` pilot 可触发
- `LangGraphDraftAdapter` precheck 可触发
- `LangGraphDraftAdapter` external pilot 可触发
- doctor / health / timeline 可看到 readiness 与 remediation
- Runtime Surface / Governance Timeline 的治理动作可闭环

## 3. 执行顺序

### 3.1 后端 smoke

```powershell
cd D:\AI\AIcode\MyPrivateAgent\backend
python scripts/doctor.py
python scripts/smoke_check.py
python scripts/auth_session_smoke.py
python scripts/chat_stream_smoke.py
python scripts/chat_empty_response_smoke.py
python scripts/chat_error_event_smoke.py
python scripts/chat_stop_generation_smoke.py
```

### 3.2 前端健康告警最小 E2E（本地）

在仓库根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File backend/scripts/frontend_health_alert_smoke.ps1
```

通过标准：
- `src/components/__tests__/RuntimeSurfacePanel.test.js` 通过（runtime contract snapshot 与 adapter health 展示）
- `src/components/__tests__/ChatView.test.js` 通过（高风险横幅与静默开关）
- `src/components/__tests__/SettingsView.test.js` 通过（阈值告警与健康更新时间）

### 3.3 一键质量门禁（后端 + 前端）

在仓库根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File backend/scripts/quality_gate_smoke.ps1 -CondaEnv myenv
```

门禁覆盖：
- 后端基础健康与模型目录 smoke
- 后端鉴权/会话 smoke
- 多智能体策略 smoke
- 多 Provider failover smoke
- Runtime contract / adapter pilot smoke
- 治理相关回归单测：
  - `tests.agent_framework.test_doctor_script`
  - `tests.agent_framework.test_health_router`
  - `tests.agent_framework.test_runtime_contract_smoke`
  - `tests.agent_framework.test_runtime_surface_config_service`
- 基于隔离基线数据的治理 smoke：
  - `backend/scripts/capability_gap_governance_smoke.py`
- 前端健康告警 smoke

通过标准：

- 输出 `PASS: quality_gate_smoke`
- 中间任一步失败都会中断，并返回非零退出码
- `quality_gate_report.py` 会从 `quality_gate_smoke.ps1` 的混合 stdout 中抽取 Runtime Contract Checks，并在 `runtime_contract_summary` 中汇总整体状态、失败数、payload 缺口数、approval replay/ignored 样本覆盖情况与 approval lifecycle recovery alignment 覆盖情况
- `quality_gate_report.py` 生成 `runtime_contract_summary` 时，`embedded_sdk_event_payloads.missing_payload_count` 的异常值不应导致报告生成失败，应按 `0` 归一化
- `quality_gate_report.py` 与 Runtime Contract Gate 遇到非 list 的 `observed_status_kinds` 时，应按空列表处理，不应把字符串拆成字符集合或中断 Runtime Profile 读取
- `quality_gate_report.py` 渲染 Runtime Contract Summary 表格时，如果 `approval_replay_coverage` 是非对象值，应按缺失处理并显示 coverage 为 `no`
- `quality_gate_report.py` 与 Runtime Contract Gate 读取 `approval_replay_coverage.event_payload_sample` 时应 fail-closed；字符串 `"false"` 应显示为未覆盖
- `runtime_contract_smoke.py` 输出中应包含 `approval_lifecycle_recovery_alignment` check，且 `replayed_submission_status = replayed`、`ignored_submission_status = ignored`、`resolved_recovery_reason = already_resolved`
- `quality_gate_report.py` 与 Runtime Contract Gate 应将上述 check 汇总为 `runtime_contract_summary.approval_lifecycle_recovery_coverage.alignment_smoke = true`
- `quality_gate_report.py` 的 Markdown summary 中 `Approval Lifecycle Recovery` 列应按 replayed/ignored/already_resolved 三个证据字段判定；证据不匹配时应显示 `no`
- Runtime Contract Gate 与 degraded trace 对 `approval_lifecycle_recovery_coverage` 应 fail-closed：如果 replayed/ignored/recovery reason 任一证据字段不匹配，即使 `alignment_smoke` 原值为 true，归一化后也应为 false
- `runtime_contract_smoke.py` 输出中应包含 `runtime_approved_tool_execution_bridge` check，且 `approved_tool_call_count = 1`、`approved_policy_original_status = approval_required`、`approved_policy_override_status = approved`、`deny_override_status = policy_denied`
- `runtime_contract_smoke.py` 输出中应包含 `sdk_tool_runtime_execution_bridge` check，且 `auto_tool_call_count = 1`、`auto_tool_history_count = 1`、`approved_tool_call_count = 1`、`approved_policy_original_status = approval_required`、`approved_policy_override_status = approved`、`deny_override_status = policy_denied`、`deny_tool_call_count = 0`
- `runtime_contract_smoke.py` 输出中应包含 `durable_checkpoint_resume_cursor` check，且 `checkpoint_status = ready`、`checkpoint_kind = approval_waiting`、`cursor_status = ready`、`cursor_entrypoint = submit_approval.approved`、`cursor_recovery_reason = ready_via_registry`
- `quality_gate_report.py` 与 Runtime Contract Gate 应将上述 check 汇总为 `runtime_contract_summary.checkpoint_resume_cursor_coverage.cursor_smoke = true`；旧报告、缺失 check 或证据字段不匹配时应 fail-closed 为 `false`
- `RuntimeContractSnapshotService` 应守护 `runtime_contract_summary.checkpoint_resume_cursor_coverage` 与 `runtime_contract_summary.checkpoint_resume_cursor_coverage.cursor_smoke`
- `runtime_contract_smoke.py` 输出中应包含 `embedded_sdk_persistence_posture` check，且 `memory_posture = memory_preview`、`durable_posture = durable_ready`、`degraded_posture = durable_degraded`、`durable_cross_process_candidate = true`
- `quality_gate_report.py` 与 Runtime Contract Gate 应将上述 check 汇总为 `runtime_contract_summary.embedded_sdk_persistence_coverage.persistence_smoke = true`；旧报告、缺失 check 或证据字段不匹配时应 fail-closed 为 `false`
- `RuntimeContractSnapshotService` 应守护 `runtime_contract_summary.embedded_sdk_persistence_coverage` 与 `runtime_contract_summary.embedded_sdk_persistence_coverage.persistence_smoke`
- Embedded SDK approval lifecycle trace adapter 应保持 opt-in：未配置 recorder 时，`approval_resolved / approval_replayed / approval_ignored / recovery_failed_closed` 仍只进入 SDK event stream，不应影响审批结果
- 配置 `SdkApprovalLifecycleTimelineService` 或等价 recorder 时，approval lifecycle trace payload 应保持 compact，并通过 `dedupe_key` 避免 replay/ignored 重复污染 Runtime Trace
- recorder 抛错或 trace service 不可用时，SDK 应 fail-open，approval decision、recovery reason 与 event stream 均不得改变
- Embedded SDK contract 应暴露 `recovery_operation_contract`，其中 `entrypoints = submit_approval.approved / resume_run.continue_loop`，`worker_ownership.implemented = false`
- Recovery retry policy contract 应暴露在 `recovery_operation_contract.retry_policy`，其中 `implemented = false`、`evidence_supported = true`，并包含 `max_attempts / backoff_strategy / retryable_reasons / terminal_reasons`
- `build_recovery_operation_record(...)` 未传入 retry evidence 时不应输出 `retry` 字段；传入 retry evidence 时应输出 compact `retry.attempt_number / retry.max_attempts / retry.previous_operation_id / retry.idempotency_key / retry.status`，且不得携带 callable、handler、provider client 或 active stream iterator
- `RecoveryRetryScheduler` 默认必须 disabled：未显式启用时只能返回 retry decision 和 idempotency evidence，不得自动调用 `submit_approval` 或 `resume_run`
- 显式启用 `RecoveryRetryScheduler` 时，只能重试 `submit_approval.approved / resume_run.continue_loop` recovery entrypoint；terminal 或 exhausted retry evidence 必须阻断执行，成功或 fail-closed 的 retry attempt 都必须进入 compact recovery operation history
- Worker ownership focused tests 应覆盖 in-memory `claim_run / heartbeat / validate_ownership`：首个 worker claim 成功、活跃 lease 阻断其它 worker、heartbeat 延长过期时间且 fencing token 不变、过期 lease 可被更高 fencing token 替换、stale fencing token fail-closed
- `build_recovery_operation_record(...)` 未传入 ownership evidence 时应继续输出 `worker_ownership.implemented = false`；传入 compact ownership evidence 时应输出 `implemented = true`、`worker_id / lease_id / fencing_token / lease_status`，且不得携带 callable、handler、provider client 或 active stream iterator
- `EmbeddedAgentRuntimeSDK` 显式注入 `worker_ownership_store` 且 persisted recovery descriptor 携带 `worker_ownership` evidence 时，registry-backed `submit_approval(..., "approved")` / `resume_run(..., continue_loop=True)` 应先校验 lease/fencing；valid evidence 可恢复并记录 `lease_status = validated`，stale fencing 必须 fail-closed 且不得执行 recovered continuation
- recovery entry 自动 claim 应保持显式 opt-in：默认不 claim，只沿用 descriptor ownership evidence；启用 `worker_ownership_auto_claim_enabled` 并注入 ownership store 后，registry-backed recovery 应在执行 continuation 前 claim run lease，并在 `latest_recovery_operation.worker_ownership` 中记录 compact `worker_id / lease_id / fencing_token / lease_status`
- `EmbeddedRuntimeFactory.build_runtime_contract()` 应暴露 `worker_ownership` dependency contract：`available / adapter_kind / durable / enforcement_mode / operations / fail_closed_reasons`；默认 in-memory adapter 的 `durable` 必须是 `false`，且 `enforcement_mode = opt_in_descriptor_evidence`
- `EmbeddedRuntimeFactory.build_runtime_contract()` 应暴露 `worker_ownership.operational_readiness`：默认 memory/fallback 为 `preview_or_degraded`，strict SQL 可为 `production_ready`，并稳定输出 `recovery_entry_claim_mode / vendor_lock_posture / migration_checklist / rollout_checklist`
- durable workspace + registry reattach 成功时，`submit_approval(..., "approved")` 与 `resume_run(..., continue_loop=True)` 返回的 run metadata 应包含 `latest_recovery_operation.operation_status = recovered`，并保留 compact `continuation_ref / workspace_backend / persistence_posture`
- fail-closed recovery 时，`recovery_failed_closed` event 应携带 `recovery_operation.operation_status = blocked`，且不得包含 callable、handler、provider client 或 active stream iterator
- Runtime Surface `run_recovery` 应暴露 `recovery_operation_boundary / latest_recovery_operation / recovery_operation_history / recovery_operation_count`；registry-backed recovery 后，`latest_recovery_operation.operation_status = recovered`，且 read model 不应包含 callable、handler、provider client 或 active stream iterator
- Runtime Surface `run_recovery.recovery_audit_summary` 应从 bounded operation history 派生，包含 latest status / latest entrypoint / latest reason / status counts / retry counts / ownership status / terminal status；无 operation history 时也应稳定输出 `operation_count = 0`
- `RecoveryAuditTimelineService.record_operation(...)` 应把 compact recovery operation 写入 Runtime Trace，payload 至少包含 `operation_id / run_id / entrypoint / operation_status / recovery_reason / dedupe_key`；同一 dedupe key 已存在时应跳过写入并返回 `dedupe_source = persisted_trace`；trace service 不可用时应 fail-open
- `EmbeddedRunWorkspaceStore.describe_backend()` 与 Runtime Surface 的 `workspace_backend` 应包含 `state_contract`，并明确 durable state kinds 与 runtime-only state kinds
- Runtime Surface 的 `embedded_runtime_boundaries.persistence_interface` 与 `default_runtime_recovery.persistence_interface` 应暴露同一套 posture 语言：`memory_preview / durable_ready / durable_degraded`
- `EmbeddedAgentRuntimeSDK.probe_run_recovery()` 应输出 `checkpoint` 与 `resume_cursor`；durable workspace + registry binding 时应返回 `checkpoint.status = ready`、`resume_cursor.cursor_status = ready`、`resume_cursor.entrypoint = submit_approval.approved`
- `EmbeddedAgentRuntimeSDK.probe_run_recovery()` 应输出 `durable_recovery_loader`：ready 路径必须来自 durable workspace + registry binding，缺 run snapshot、未注册 binding、resolved approval state 或 persisted descriptor 中出现 `handler / callable / tool_executor / reflector / reviewer / fallback_handler` 等 callable-like payload 时必须 fail-closed
- 当 workspace backend 非 durable、fallback 激活、registry binding 缺失或 approval 已 resolved 时，`checkpoint/resume_cursor` 应分别进入 `blocked` 或 `stale`，不得仅凭 `persistence_posture = durable_ready` 或 continuation descriptor 存在推断为可恢复
- `AgentHarnessFacade.register_tool()` 应能注册 ToolSpec 元数据与本地 handler；未显式传入 `tool_executor` 时，`execute()` 应通过 SDK 事件流记录 `tool_call_started / tool_result`，并在 `tool_history.execution` 中包含 action / observation metadata
- `ToolRuntimeService.execute_tool()` 应返回 `phase-ii-tool-runtime-execution-v1` envelope；有效参数返回 `status = ok`，缺少 required args、primitive type 不匹配、enum 越界或 object required 缺失时返回 `status = validation_failed` 且不得调用工具实现
- `ToolRuntimeService.execute_tool()` 应先执行 `permission_level_gate_v1`：`auto` 允许执行并写入 `execution.policy_decision.status = allowed`，`ask / high_risk` 返回 `status = approval_required` 且不得调用工具实现，`deny` 返回 `status = policy_denied` 且不得调用工具实现
- `ToolRuntimeService.evaluate_tool_policy()` 应返回同一套 `permission_level_gate_v1` decision，且不得调用工具实现；`AgentHarnessFacade.execute()` 在 ToolRuntimeService 接线下应把 registry ToolSpec 的 `ask / high_risk / deny` 映射成 SDK 审批或拒绝，而不是产生普通 `tool_result`
- `AgentHarnessFacade` + `ToolRuntimeService` 的 `ask / high_risk` 工具在 approval approved 后应恢复执行一次，并在 `execution.policy_decision` 中记录 approved override；`deny` 工具即使带 approved override 也不得执行
- `runtime_contract_smoke.py` 应用一条独立 smoke check 覆盖上述 approved runtime-service tool execution bridge，避免该行为只停留在单元测试中
- `ToolRuntimeService.execute_tool(..., execution_options={"max_attempts": 2})` 应在瞬时异常恢复后返回 `retry.status = recovered`；持续失败时返回 `retry.status = exhausted`
- `ToolRuntimeService.execute_tool(..., execution_options={"timeout_seconds": ...})` 在同步调用耗时超过阈值时应返回 `status = timeout` 与 `timeout.status = exceeded`；该语义是 post-call elapsed check，不代表线程级强杀
- `QueryControlEventMapperService.build_record_payload()` 处理 `tool_result` 时应输出 compact `tool_runtime_observation`，包含 policy / schema / retry / timeout 状态，但不得复制完整工具 result 文本
- `quality_gate_report.py` 遇到非对象 Runtime Contract check 时不应中断报告生成或 Markdown 渲染；这些原始项可保留在 `structured_output`，但不应进入 `contract_checks` 或表格
- `quality_gate_report.py` 遇到非对象 `runtime_contract_summary` 时不应中断 Markdown 渲染，也不应把该值写入 Runtime Contract Summary 表格
- `quality_gate_report.py` 遇到非对象 step 时不应中断 Markdown 渲染，也不应把该值写入主表、失败列表或 runtime contract 表格
- `quality_gate_report.py` 遇到非 list 的 `steps / failed_steps` 时不应中断 Markdown 渲染，应按空列表处理
- `quality_gate_report.py` 遇到缺少 `name / passed / exit_code / duration_seconds` 的 object step 时不应中断 Markdown 渲染，应以空值或 `FAIL` fallback 展示
- `quality_gate_report.py` 遇到缺少 `passed / step_count / failed_steps / steps` 的旧报告时不应中断 Markdown 渲染；`step_count` 可从有效 steps 推导，`passed` 缺失时显示 `FAIL`
- `quality_gate_report.py` 遇到缺少顶层 `failed_steps` 的旧报告时，应从有效 steps 中 `passed = false` 的项推导失败列表，避免摘要失败数与主表冲突
- `quality_gate_report.py` 渲染 `passed` 状态时应 fail-closed；字符串 `"false"` 不应被渲染为 PASS
- `quality_gate_report.py` 渲染 Markdown summary 时，step/check/failure reason 或 runtime contract summary 字段中的 `|` 与换行不应破坏 Runtime Contract Checks / Summary 表格结构
- `/api/runtime-profile.runtime_contract_gate` 会透出 `runtime_contract_summary`，Runtime Surface 的 `Contract Gate` 卡片应能直接展示 payload 缺口和 approval replay/ignored 覆盖状态
- 如果质量门禁报告或 contract checks 缺失，`runtime_contract_summary.overall_status` 应显示 `unknown`，不应误显示为 `degraded` 或 `approval_replay=missing`
- 如果质量门禁报告中的 `steps / contract_checks` 是非 list 类型，Runtime Contract Gate 应按空列表处理，Runtime Profile 不应因 artifact 类型漂移报错
- 如果质量门禁报告中的 `runtime_contract_summary` 或 `contract_checks` 计数字段不可解析或为负数，后端应回退到推导值或 `None`，Runtime Profile 不应因 artifact 脏字段报错
- `quality_gate_report.py` 的 `runtime_contract_summary.approved_tool_execution_coverage` 应来自 `runtime_approved_tool_execution_bridge` check；缺失、旧报告或非对象 check 应显示 `bridge_smoke=false`
- `quality_gate_report.py` 的 `runtime_contract_summary.sdk_tool_runtime_execution_coverage` 应来自 `sdk_tool_runtime_execution_bridge` check；缺失、旧报告或证据字段不匹配时应显示 `bridge_smoke=false`
- Runtime Contract Gate 应归一化 `approved_tool_execution_coverage`，让 Runtime Profile 消费方无需扫描 raw `contract_checks` 即可判断 approved tool bridge 是否被 smoke 覆盖
- Runtime Contract Gate 应归一化 `sdk_tool_runtime_execution_coverage`，让 Runtime Profile 消费方无需扫描 raw `contract_checks` 即可判断 SDK 直连 ToolRuntime bridge 是否被 smoke 覆盖
- `quality_gate_report.py` 的 `runtime_contract_summary.subagent_lane_query_detail_coverage` 应来自 `subagent_lane_query_detail` check；缺失、旧报告或非对象 check 应显示 `detail_smoke=false`
- Runtime Contract Gate 应归一化 `subagent_lane_query_detail_coverage`，让 Runtime Profile 消费方无需扫描 raw `contract_checks` 即可判断 subagent lane query detail 是否被 smoke 覆盖
- 当 `runtime_contract_gate.overall_status = degraded` 且请求携带治理上下文时，写入的 `runtime_contract_gate_degraded` trace payload 应包含 `runtime_contract_summary`，且 fingerprint 会随 summary 关键字段变化而变化
- `runtime_contract_gate_degraded` trace detail 应包含 `approval_lifecycle=<covered|missing|unknown>`，其中 summary 缺失时为 `unknown`，coverage 未通过时为 `missing`
- 当 `approved_tool_execution_coverage.bridge_smoke` 从 `false` 变为 `true` 时，`runtime_contract_gate_degraded` 应生成新的 fingerprint / dedupe key 并允许写入新的治理 trace
- `runtime_contract_gate_degraded.payload.runtime_contract_summary` 应保留并归一化 `sdk_tool_runtime_execution_coverage / embedded_sdk_persistence_coverage / worker_ownership_store_mode_coverage / child_executor_promotion_gate_coverage / child_executor_execution_prerequisites_coverage / child_executor_dispatch_coverage / subagent_lane_query_detail_coverage / durable_recovery_loader_coverage`，缺失或证据不完整时对应 smoke flag 应为 `false`
- `runtime_contract_gate_degraded.detail` 应包含 `approved_tool / sdk_tool / embedded_persistence / worker_ownership / child_executor_gate / child_executor_prerequisites / child_executor_dispatch / subagent_detail / durable_loader` 等紧凑覆盖标签
- 当 `recovery_retry_evidence_coverage.retry_smoke` 从 `false` 变为 `true` 时，`runtime_contract_gate_degraded` 应生成新的 fingerprint / dedupe key 并允许写入新的治理 trace；trace detail 应包含 `recovery_retry=<covered|missing|unknown>`
- 当 `subagent_lane_query_detail_coverage.detail_smoke` 从 `false` 变为 `true` 时，`runtime_contract_gate_degraded` 应生成新的 fingerprint / dedupe key 并允许写入新的治理 trace
- Governance Timeline 的 runtime contract warning 事件卡片应展示 `runtime_contract=<status> / missing_payloads=<n> / approval_replay=<covered|missing|unknown> / approval_lifecycle=<covered|missing|unknown> / approved_tool=<covered|missing|unknown> / sdk_tool=<covered|missing|unknown> / embedded_persistence=<covered|missing|unknown> / worker_ownership=<covered|missing|unknown> / child_executor_gate=<covered|missing|unknown> / child_executor_prerequisites=<covered|missing|unknown> / child_executor_dispatch=<covered|missing|unknown> / child_executor_dispatcher=<covered|missing|unknown> / subagent_detail=<covered|missing|unknown> / recovery_retry=<covered|missing|unknown> / recovery_retry_scheduler=<covered|missing|unknown> / durable_loader=<covered|missing|unknown> / checkpoint_cursor=<covered|missing|unknown>` 摘要，不需要展开 Payload 才能判断门禁退化原因

### Child Executor Dispatcher Smoke

- 默认构造 `ChildExecutorDispatcher` 时应保持 `enabled = false`，即使传入 ready `child_executor_dispatch_contract` 也不会调用 backend adapter，并返回 `blocked_reason = dispatcher_disabled`。
- 显式 `enabled = true` 但 dispatch contract blocked 时应返回 `blocked_reason = dispatch_contract_not_ready`，并记录 compact audit evidence。
- 只有显式 enabled、`dispatch_ready = true` 且 backend adapter 已注册时，dispatcher 才会调用 adapter；adapter 异常或返回非对象结果时必须 fail-closed。
- `runtime_contract_smoke.py` / `quality_gate_report.py` / Runtime Contract Gate / snapshot guard 应共同暴露并守护 `child_executor_dispatcher_coverage.dispatcher_smoke`。
- Sandbox worker backend adapter contract 应保持 opt-in：默认 backend registry 仍为 relationship-only，`embedded_sdk_worker.dispatch_ready = false`；只有 sandbox adapter contract、sandbox/resource/audit/idempotency guard evidence 均完整时，sandbox backend 才可作为 dispatch-ready candidate。Dispatcher 遇到 unsafe payload、非对象结果或缺少 compact attempt envelope 字段时必须 fail-closed。
- `/api/runtime-profile/subagent-lane-query-detail-readiness` 应只返回 detail readiness 门禁字段；即使 ready，也不应返回 `recent_events / history_items / workspace` 状态
- `/api/runtime-profile/subagent-lane-query-detail?query_id=<id>` 应返回指定 `subagent_lane` query 的 `stage_chain / recent_events / latest_stage / latest_summary`，但不应返回 history pagination 或 workspace 状态
- `runtime_contract_smoke.py` 输出中应包含 `subagent_lane_query_detail` check，且 `contract_version = phase-h-subagent-lane-query-detail-v1`、`recording_state = recorded`、`stage_count >= 2`、`recent_event_count >= 2`

### 3.4 Runtime Contract Smoke

```powershell
python backend/scripts/runtime_contract_smoke.py
```

通过标准：
- `/api/runtime-profile` 返回 `contract_snapshot.overall_status = healthy`
- `POST /api/runtime-framework-adapters/pilot-run` 成功返回最小事件流
- Embedded SDK 事件样本通过 payload contract 校验，包含审批已决后的 `approval_replayed / approval_ignored` 治理事件
- `embedded_sdk_event_payloads` 检查输出 `observed_status_kinds`，用于质量门禁报告判断 approval replay/ignored 样本是否被覆盖
- `embedded_sdk_persistence_posture` 检查输出 memory、durable-ready、durable-degraded 三类 posture 证据，用于质量门禁报告判断 SDK persistence interface 是否被 gate 覆盖
- `subagent_lane_query_detail` 检查输出 dedicated detail coverage 字段，用于质量门禁报告判断 subagent lane query detail 是否被 gate 覆盖
- 输出 JSON 中 `status = ok`

### 3.5 Phase D Framework Adapter 专项验证

建议在运行前确认以下开关：

```powershell
$env:ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER="true"
$env:ENABLE_LANGGRAPH_DRAFT_ADAPTER="true"
```

如果要验证 `runtime_disabled -> ready` 相关分支，可按需补充：

```powershell
$env:LANGGRAPH_RUNTIME_ENDPOINT="http://localhost:8000/mock-langgraph"
$env:LANGGRAPH_ASSISTANT_ID="draft-assistant"
```

如果要验证真实 external pilot 骨架，可继续补充：

```powershell
$env:ENABLE_LANGGRAPH_RUNTIME_EXECUTION="true"
$env:ENABLE_LANGGRAPH_EXTERNAL_PILOT="true"
```

建议按以下顺序执行：

1. 运行 `python backend/scripts/doctor.py`
2. 打开设置页高级标签中的 `Runtime Surface`
3. 在 `local_fake_framework` 上执行 `运行 Pilot`
4. 在 `langgraph_draft` 上执行 `运行预检`
5. 当 `langgraph_draft` 进入 `ready` 后，执行 `运行 External Pilot`
6. 打开 `Governance Timeline` 查看：
   - `最近一次 LocalFakeFramework Pilot`
   - `最近一次 LangGraph Precheck`
   - `最近一次 LangGraph External Pilot`
   - `最近一次 LangGraph External Pilot 失败诊断`
   - `最近一次 LangGraph 修复建议`

通过标准：

- `Runtime Surface` 能展示 adapter health 扩展字段
- `Pilot` 返回 `run_id / event_count / snapshot_id / final_output`
- `Precheck` 返回 `ready / configuration_status / execution_mode / snapshot_id`
- `External Pilot` 返回 `status / snapshot_id / final_output`
- `External Pilot` 失败时返回 `error_type / detail`
- `External Pilot` 在 preflight 阶段能明确区分：
  - `protocol_error`：probe 未返回 assistant identity evidence 或 evidence 形状非法
  - `configuration_error`：upstream 不识别当前 assistant identity，或 identity 回传不匹配
- `Health / Doctor / doctor.py` 中的 `checks.framework_adapters.latest_external_pilot_failure`
  - 能看到最近一次 external pilot 失败分类、adapter 身份、错误详情与 `snapshot_ref`
- `Health / Doctor / doctor.py` 中的 `checks.framework_adapters.external_pilot_failure_counts`
  - 能看到最近一段时间的 external pilot 失败总数与 `error_type` 分布
- `Runtime Surface`
  - 能直接看到“最近一次 LangGraph External Pilot 失败”摘要、失败总数、错误分布与跳转入口
  - 可点击某个 `error_type` 分布项，直接跳到对应的治理时间线告警视图
- `Governance Timeline` 能看到 `framework_adapter_precheck_completed`
- `Governance Timeline` 能看到 `framework_adapter_external_pilot_completed`
- `Governance Timeline` 能看到 `framework_adapter_external_error`
- `Governance Timeline` 能看到 `最近一次 LangGraph External Pilot 失败诊断`
  - 该卡来源于 `doctor_run_completed.payload.framework_adapters.latest_external_pilot_failure`
  - 该卡支持展示失败总数与 `error_type` 分布
  - 该卡支持直接 `打开运行时面板`
  - 该卡支持直接 `复制快照命令`
  - 支持通过 `governance_error_type` 路由参数只查看指定 `error_type` 的 external pilot 告警
  - 支持在前端直接清除 `error_type` 过滤，且保留当前 `framework_adapter / warning` 视图
- `Doctor` 或 timeline 中能看到 `framework_adapters.remediation_actions`

### 3.6 前端回归

```powershell
cd D:\AI\AIcode\MyPrivateAgent\frontend-vue
npm test
npm run build
```

## 4. 测试用例

### TC-001 启动自检

- 目标：确认 demo 默认环境可运行
- 前置条件：已安装 Python 依赖
- 步骤：运行 `python scripts/doctor.py`
- 预期结果：
  - 输出 `ok` 或等价通过状态
  - 显示当前为 `sqlite` 或本地默认模式
  - 无阻断级错误

### TC-002 基础健康检查

- 目标：确认后端基础路由可访问
- 前置条件：后端依赖已安装
- 步骤：运行 `python scripts/smoke_check.py`
- 预期结果：
  - 健康检查通过
  - 基础 API 可返回成功

### TC-003 游客登录与会话链路

- 目标：确认登录和会话基础能力可用
- 前置条件：后端可启动
- 步骤：运行 `python scripts/auth_session_smoke.py`
- 预期结果：
  - 游客登录成功
  - `/api/auth/me` 正常
  - 可创建会话
  - 会话列表和详情可返回

### TC-004 聊天正常流式输出

- 目标：确认 SSE 主链路可用
- 前置条件：后端可启动
- 步骤：运行 `python scripts/chat_stream_smoke.py`
- 预期结果：
  - 返回 `conversation_id`
  - 返回至少一段 `content`
  - 返回 `done`

### TC-005 聊天空响应兜底

- 目标：确认上游空响应不会让前端卡死
- 前置条件：后端可启动
- 步骤：运行 `python scripts/chat_empty_response_smoke.py`
- 预期结果：
  - 返回兜底文案
  - 最终返回 `done`

### TC-006 聊天错误事件收尾

- 目标：确认上游报错时链路可以正常收尾
- 前置条件：后端可启动
- 步骤：运行 `python scripts/chat_error_event_smoke.py`
- 预期结果：
  - 返回 `error` 事件
  - 前端展示链路不会永久停在生成中

### TC-007 停止生成

- 目标：确认“停止生成”按钮链路真实可用
- 前置条件：
  - 前端 `npm test` 环境可运行
  - 聊天页已打开
- 步骤：
  1. 发起一条会进入生成态的消息
  2. 点击消息上的“停止生成”
  3. 或运行 `python scripts/chat_stop_generation_smoke.py`
- 预期结果：
  - 当前请求被中断
  - assistant 消息结束生成态
  - 展示“已停止生成”或已生成片段
  - 页面不再保持 loading

### TC-008 前端最小自动化

- 目标：确认主界面关键行为未回归
- 前置条件：Node.js 环境可用
- 步骤：运行 `npm test`
- 预期结果：
  - 所有测试通过
  - 至少覆盖：
    - 消息流式渲染
    - 命令面板
    - 反馈提交
    - 停止生成

### TC-009 前端生产构建

- 目标：确认前端可产出构建包
- 前置条件：Node.js 环境可用
- 步骤：运行 `npm run build`
- 预期结果：
  - 构建成功
  - 无阻断级错误

### TC-010 Planner 展示

- 目标：确认 Todo/Planner 面板可展示
- 前置条件：前后端已启动
- 步骤：
  1. 进入聊天页
  2. 输入目标
  3. 点击“为当前目标生成计划”
- 预期结果：
  - 右侧出现计划
  - 计划项状态可切换
  - 时间线 / run trace 可展示

### TC-011 MCP 管理面板

- 目标：确认 MCP 管理入口可用
- 前置条件：前后端已启动
- 步骤：
  1. 打开设置页
  2. 查看 MCP server 列表
  3. 尝试新增或探测一个 server
- 预期结果：
  - 页面正常渲染
  - 列表、catalog、probe/handshake 按钮可操作

### TC-012 Skill 管理页

- 目标：确认 Skill 资产管理页可展示
- 前置条件：前后端已启动
- 步骤：
  1. 打开 Skill 管理页
  2. 查看已存在技能
  3. 尝试执行启停或读取
- 预期结果：
  - 页面正常渲染
  - 基本管理动作可用

### TC-013 Runtime Profile 与 Adapter Health

- 目标：确认 runtime profile 已正确暴露 contract snapshot 与 framework adapter readiness
- 前置条件：
  - 后端已启动
  - `ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER=true`
  - `ENABLE_LANGGRAPH_DRAFT_ADAPTER=true`
- 步骤：
  1. 运行 `python backend/scripts/runtime_contract_smoke.py`
  2. 或调用 `GET /api/runtime-profile`
- 预期结果：
  - `contract_snapshot.overall_status = healthy`
  - `adapter_health.adapters` 中包含 `local_fake_framework`
  - `adapter_health.adapters` 中包含 `langgraph_draft`
  - `langgraph_draft` 返回 `configuration_status / execution_mode / missing_packages / missing_env`

### TC-014 LocalFakeFramework Pilot

- 目标：确认本地 fake adapter 的 pilot 能通过平台治理链路闭环
- 前置条件：
  - 后端已启动
  - `ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER=true`
  - 前端设置页可访问
- 步骤：
  1. 打开 `Runtime Surface`
  2. 在 `local_fake_framework` 卡片点击 `运行 Pilot`
  3. 记录返回的 `snapshot_id`
  4. 点击 `查看时间线`
- 预期结果：
  - 面板显示 `最近 LocalFakeFramework Pilot`
  - 显示 `状态: 已完成`
  - 显示 `输出: 已产生`
  - 可看到 `run_id / event_count / snapshot_id / final_output`
  - 时间线中可聚焦到该次 pilot 快照

### TC-015 LangGraph Draft Precheck

- 目标：确认 draft adapter 只做 readiness 预检，不误入真实执行链
- 前置条件：
  - 后端已启动
  - `ENABLE_LANGGRAPH_DRAFT_ADAPTER=true`
  - 前端设置页可访问
- 步骤：
  1. 打开 `Runtime Surface`
  2. 在 `langgraph_draft` 卡片点击 `运行预检`
  3. 记录返回的 `snapshot_id`
  4. 点击 `查看时间线`
- 预期结果：
  - 面板显示 `最近 LangGraph Precheck`
  - 显示 `状态: 缺包`、`缺环境变量`、`运行时开关未启用` 或 `已就绪` 中的一种
  - 显示 `就绪度: 未就绪` 或 `就绪度: 已就绪`
  - 显示 `configuration_status / execution_mode / snapshot_id / 阻塞原因`
  - 时间线中出现 `Framework Adapter 预检完成`

### TC-016 LangGraph External Pilot

- 目标：确认 draft adapter 在 ready 且 external pilot 开关开启时，可以走真实外部执行骨架
- 前置条件：
  - 后端已启动
  - `ENABLE_LANGGRAPH_DRAFT_ADAPTER=true`
  - `ENABLE_LANGGRAPH_RUNTIME_EXECUTION=true`
  - `ENABLE_LANGGRAPH_EXTERNAL_PILOT=true`
  - `LANGGRAPH_RUNTIME_ENDPOINT` 已配置
  - `LANGGRAPH_ASSISTANT_ID` 已配置
  - 前端设置页可访问
- 步骤：
  1. 打开 `Runtime Surface`
  2. 确认 `langgraph_draft` 显示 `config: 已就绪`
  3. 点击 `运行 External Pilot`
  4. 记录返回的 `snapshot_id`
  5. 点击 `查看时间线`
- 预期结果：
  - 面板显示 `最近 LangGraph External Pilot`
  - 显示 `status / snapshot_id`
  - 成功时显示 `final_output`
  - 失败时显示 `error_type / detail`
  - 时间线中出现 `Framework Adapter 外部执行完成` 或 `Framework Adapter 外部执行失败`

### TC-016A LangGraph External Pilot 成功路径

- 目标：确认 external pilot 在 assistant identity 与 probe 证据都合法时可以成功执行
- 前置条件：
  - 满足 `TC-016` 所有前置条件
  - 上游 probe 能返回 assistant identity evidence，且与当前 `LANGGRAPH_ASSISTANT_ID` 一致
- 步骤：
  1. 打开 `Runtime Surface`
  2. 在 `langgraph_draft` 上点击 `运行 External Pilot`
  3. 记录 `snapshot_id`
  4. 打开 `Governance Timeline`
- 预期结果：
  - 结果卡显示 `最近 LangGraph External Pilot`
  - 显示 `status / snapshot_id / final_output`
  - 时间线中出现 `Framework Adapter 外部执行完成`

### TC-016B LangGraph External Pilot 缺少 Assistant Evidence

- 目标：确认 probe 未返回 assistant identity evidence 时，平台会稳定归类为 `protocol_error`
- 前置条件：
  - 满足 `TC-016` 所有前置条件
  - 上游 probe 只返回 reachability 成功，但不返回 `assistant_exists / assistant_id / assistants[]`
- 步骤：
  1. 打开 `Runtime Surface`
  2. 在 `langgraph_draft` 上点击 `运行 External Pilot`
  3. 记录失败结果与 `snapshot_id`
  4. 打开 `Governance Timeline`
- 预期结果：
  - 结果卡显示 `错误: 协议错误 (protocol_error)`
  - 详情体现 probe 缺少 assistant identity evidence
  - 时间线中出现 `Framework Adapter 外部执行失败`
  - 时间线摘要卡出现 `最近一次 LangGraph External Pilot 失败诊断`

### TC-016C LangGraph External Pilot Assistant Identity 不存在

- 目标：确认 upstream 明确不识别当前 assistant identity 时，平台会稳定归类为 `configuration_error`
- 前置条件：
  - 满足 `TC-016` 所有前置条件
  - 上游 probe 明确返回当前 assistant identity 不存在，或返回了与请求不匹配的 identity
- 步骤：
  1. 打开 `Runtime Surface`
  2. 在 `langgraph_draft` 上点击 `运行 External Pilot`
  3. 记录失败结果与 `snapshot_id`
  4. 打开 `Governance Timeline`
- 预期结果：
  - 结果卡显示 `错误: 配置错误 (configuration_error)`
  - 详情体现 assistant identity 不被上游识别，或 identity 回传不匹配
  - 时间线中出现 `Framework Adapter 外部执行失败`
  - 时间线摘要卡出现 `最近一次 LangGraph External Pilot 失败诊断`

### TC-017 Doctor Remediation 与治理时间线

- 目标：确认 framework adapter 的 remediation 建议能进入 doctor 与治理时间线
- 前置条件：
  - 后端已启动
  - `ENABLE_LANGGRAPH_DRAFT_ADAPTER=true`
  - 当前存在至少一个 readiness 阻塞项
- 步骤：
  1. 运行 `python backend/scripts/doctor.py`
  2. 打开 `Governance Timeline`
  3. 查看 `最近一次 LangGraph 修复建议`
  4. 点击 `复制修复命令`
  5. 点击 `打开运行时面板`
- 预期结果：
  - doctor 输出中存在 `framework_adapters`
  - `framework_adapters.remediation_actions[*].framework_name = LangGraph`
  - 时间线中出现 `最近一次 LangGraph 修复建议`
  - 卡片可显示 `状态: 缺包 / 缺环境变量 / 运行时未启用`
  - 可复制修复命令草案并跳转到 `Runtime Surface`

## 5. 建议验收顺序

建议按下面顺序做人工验收：

1. `TC-001 ~ TC-003`
2. `TC-004 ~ TC-007`
3. `TC-008 ~ TC-009`
4. `TC-010 ~ TC-012`
5. `TC-013 ~ TC-017`

## 6. 结果记录模板

每次测试可按下面模板记录：

```md
测试日期：
测试人：
版本/分支：

- TC-001：通过 / 失败
- TC-002：通过 / 失败
- TC-003：通过 / 失败
- TC-004：通过 / 失败
- TC-005：通过 / 失败
- TC-006：通过 / 失败
- TC-007：通过 / 失败
- TC-008：通过 / 失败
- TC-009：通过 / 失败
- TC-010：通过 / 失败
- TC-011：通过 / 失败
- TC-012：通过 / 失败
- TC-013：通过 / 失败
- TC-014：通过 / 失败
- TC-015：通过 / 失败
- TC-016：通过 / 失败
- TC-017：通过 / 失败

问题记录：
- 
```
