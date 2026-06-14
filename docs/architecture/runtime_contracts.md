# Runtime Contracts

> 本文记录当前运行时契约入口。契约字段以代码为准，本文只记录稳定边界和维护约束。

## 0. 项目定位与外部框架边界

MyPrivateAgent 的正式定位是企业级 `Agent Runtime Control Plane`，不是 LangGraph、CrewAI、Qwen-Agent、OpenAI Agents SDK、DeerFlow、Agno 等外部 Agent 框架的替代实现。

外部框架在本项目中的位置是可插拔执行引擎或 adapter candidate：

- 它们可以提供 agent workflow、handoff、多 agent 协作、tool execution、tracing、planning 等执行层能力。
- 它们不能直接替代本项目的 Runtime Core、Tool Runtime、Query Control、Runtime Contract Gate、Governance Timeline、审计、权限和业务系统集成语义。
- 任何外部框架接入都必须通过 framework adapter 把原生事件、工具、run、失败、审批和 handoff 映射为本地稳定 contract。
- 前端治理台和 Runtime Surface 优先消费本地 runtime/governance contract，不直接依赖 framework-native raw payload。

后续若新增或推广外部框架 adapter，必须先通过 OpenSpec 记录 adapter 边界、生命周期映射、promotion gate、非目标与验证方式；默认不得直接进入主 chat 执行链。

## 1. Contract 聚合入口

Runtime Surface 的当前聚合入口是：

- `backend/services/runtime_surface_service.py`
- `RuntimeSurfaceService.get_runtime_profile()`

该方法向前端治理台暴露以下主要 contract：

- `runtime_core`
- `governance_overview`
- `domain_agent_registry`
- `rag_source_registry`
- `knowledge_graph_registry`
- `tool_runtime`
- `mcp_runtime`
- `adapter_health`
- `capability_contract`
- `skill_contract`
- `memory_contract`
- `subagent_contract`
- `hook_contract`
- `command_contract`
- `runtime_contract_gate`
- `self_improvement_ledger`
- `query_control_plane`
- `contract_snapshot`
- `config_layers`

`domain_agent_registry` 由 `backend/services/domain_agent_registry_service.py` 构建，只读扫描 `backend/domain_agents/*/agent.yaml` 或 `agent.yml`。它用于暴露垂域 agent 身份、角色、能力和治理边界，不导入垂域代码，不自动注册工具、Skill、MCP 或 RAG，也不参与 chat 执行路由。

`domain_agent_registry` 还会保留每个 agent 的规范化 `grounding_policy` 及其 `grounding_policy_status` 只读状态块，用于在默认 chat 检索注入之前向治理消费者展示策略、兼容输入和可见性 readiness。这个状态块是描述性的，不是执行授权源。

`rag_source_registry` 与 `knowledge_graph_registry` 同样由 `DomainAgentRegistryService` 从 `capabilities.rag_sources` 和 `capabilities.graph_sources` 派生。它们只表达“哪个垂域 agent 允许看哪些知识源/图谱”，不创建索引、不上传文档、不编辑 ontology，也不自动把检索结果注入主 chat。外部知识执行由 capability runtime 的 `knowledge.rag.retrieve` 和 `knowledge.graph.query` 代理到 `unifiedKnowledgeProvider`。

`unifiedKnowledgeProvider` 的 capability health / heartbeat 当前会暴露 compact `governance_readiness`，用于说明 provider 是否配置、显式 RAG 是否可用、source catalog 是否 degraded，以及 `graph_query` / default chat grounding 为什么仍保持 `gated`。该 readiness 只读、fail-open，不执行 GraphRAG、不创建 source binding、不启用 `/api/chat` 检索注入，也不改变答案策略。

Domain-agent grounded-answer promotion gate 当前会优先消费 `provider_evidence.governance_readiness`：`rag_retrieve.status = ready` 可作为文档 RAG trial 的 provider readiness，`source_catalog.status = degraded` 会进入 review，`overall_status = unreachable` 会 blocked，`graph_query.status = gated` 会继续阻止 graph grounded-answer trial。该消费仍然 side-effect-free，不调用 provider。

Domain-agent grounded-answer trial surface 当前会把 promotion gate 的 provider readiness 结果提升为顶层 compact `provider_readiness` 摘要，包含 provider 状态、RAG/source catalog/Graph/default chat grounding posture、provider/graph blockers、warnings 与 promotion boundary。该摘要只保留 caller-supplied readiness 的治理解释，不复制 raw provider payload，不调用 provider，不生成答案，也不改变默认 chat 行为。

Grounded-answer package dry-run 当前会从 trial report 继续保留 compact `provider_readiness`，让后续 composition trial 或治理消费者可以读取同一份 provider readiness 摘要。package 仍只构造未来答案路径的输入包，不重新裁决 readiness，不调用 provider/model/chat，不执行 GraphRAG，也不创建 source binding、memory、audit 或 trace 状态。

当前运行时作用域契约补充：

- `runtime-profile` 当前已支持显式 run scope 输入（`run_id / parent_run_id / child_run_id / scheduler_run_id`）；当上游已知当前作用域时，后端应优先采信显式 scope，而不是依赖前端推导。
- `governance_overview.run` 当前已成为 parent overview 的后端真源；`child_merge_intent / child_merge_entities / child_merge_conclusion` 不再只由前端从 child merged semantics 反向拼装。
- `governance_overview.run` 与 `runtime_core` 当前已同步暴露 `child_merge_section_source / child_merge_section_ids / child_merge_section_counts`，作为 parent-facing merge overview 的稳定 section evidence；前端无需再调用 dedicated merged semantics read model 来反推 count provenance。
- `runtime_contract_gate` 当前会从最近一次 `quality-gate-report.json` 读取 Runtime Contract Checks，并稳定暴露 `runtime_contract_summary`。该 summary 汇总 `overall_status / check_count / failed_check_count / missing_payload_count / approval_replay_coverage / approval_lifecycle_recovery_coverage / approved_tool_execution_coverage / sdk_tool_runtime_execution_coverage / tool_runtime_timeout_retry_coverage / checkpoint_resume_cursor_coverage / embedded_sdk_persistence_coverage / worker_ownership_store_mode_coverage / recovery_retry_evidence_coverage / recovery_retry_scheduler_coverage / durable_recovery_loader_coverage / continuation_descriptor_lifecycle_coverage / loader_execution_handoff_coverage / recovery_audit_operation_history_coverage / production_recovery_registry_checkpoint_policy_coverage / child_executor_promotion_gate_coverage / child_executor_execution_prerequisites_coverage / child_executor_dispatch_coverage / child_executor_dispatcher_coverage / child_executor_dispatch_result_handoff_coverage / child_executor_dispatch_result_retry_audit_coverage / child_executor_dispatch_retry_scheduler_handoff_coverage / child_executor_sandbox_backend_binding_coverage / child_executor_sandbox_backend_coverage / subagent_lane_query_detail_coverage`，供 Runtime Surface、Governance Timeline 和 CI artifact 消费方直接读取。
- `quality_gate_report.py` 在生成 `runtime_contract_summary` 时也必须按 fail-closed 方式读取 `embedded_sdk_event_payloads.missing_payload_count`；脏值或负数应按 `0` 处理，保证 quality gate artifact 本身可生成。
- `quality_gate_report.py` 抽取与渲染 `contract_checks` 时只把 object check 纳入 summary/table 计算；非对象项应保留在 `structured_output` 原始证据里，但不应进入 `contract_checks`、Markdown 表格或拖垮 summary 生成。
- `quality_gate_report.py` 渲染 Markdown summary 时只接受 object `runtime_contract_summary`；旧报告或手工报告中的非对象 summary 不应进入 `Runtime Contract Summary` 表格，也不应中断 summary 渲染。
- `quality_gate_report.py` 渲染旧报告或手工报告时只接受 object step；非对象 step 不应进入主表、失败列表、Runtime Contract Checks 或 Runtime Contract Summary 表格。
- `quality_gate_report.py` 渲染旧报告或手工报告时只接受 list 形态的 `steps / failed_steps`；非 list 顶层字段应按空列表处理，不应中断 Markdown summary 生成。
- `quality_gate_report.py` 渲染 object step 时应容忍 `name / passed / exit_code / duration_seconds` 缺失；缺失字段应以空值或 `FAIL` fallback 展示，不应中断 Markdown summary 生成。
- `quality_gate_report.py` 渲染旧报告或手工报告时应容忍顶层 `passed / step_count / failed_steps / steps` 缺失；`step_count` 缺失时应从有效 object steps 推导，`passed` 缺失时按 `FAIL` 展示。
- `quality_gate_report.py` 渲染旧报告或手工报告时，如果顶层 `failed_steps` 缺失，应从有效 object steps 中 `passed = false` 的项推导失败列表，避免 Markdown summary 显示失败数为 0 但主表存在失败 step。
- `quality_gate_report.py` 渲染 `passed` 状态时应 fail-closed 归一化；只有布尔 `true` 或明确的 `true/pass/passed/ok/yes/1` 字符串可显示 PASS，字符串 `false` 等其他值必须显示 FAIL。
- `quality_gate_report.py` 渲染 Markdown 表格时必须转义 `|` 并折叠换行，避免 step/check/failure reason 或 summary 字段中的自由文本破坏 `Runtime Contract Checks` / `Runtime Contract Summary` 表格结构。
- `quality_gate_report.py` 生成 runtime contract step 时必须写入 `runtime_contract_artifact_schema`，用于声明 `runtime_contract_summary` 关键字段是否完整；该 guard 至少守护 `subagent_lane_query_detail_coverage.detail_smoke`，并在 Markdown summary 的 `Runtime Contract Artifact Schema` 表格中展示缺失字段。
- 当质量门禁报告缺失或报告中没有 `contract_checks` 时，`runtime_contract_gate.overall_status` 与 `runtime_contract_summary.overall_status` 都必须保持 `unknown`；这表示“无法判断”，不应被前端或审计链误解释为 `degraded`。
- Runtime Contract Gate 读取质量门禁 artifact 时必须暴露 `runtime_contract_artifact_schema`；新报告优先读取 artifact 自带 guard，旧报告应从归一化后的 `runtime_contract_summary` 派生 guard，报告缺失或 checks 缺失时 guard 状态为 `unknown`。
- Runtime Contract Gate 读取 `quality-gate-report.json` 时只接受 list 形态的 `steps / contract_checks` 和 object check；非 list 或非 object artifact 字段应按空处理并返回 `contract_checks_missing`，不应拖垮 Runtime Profile。
- `quality_gate_report.py` 与 Runtime Contract Gate 读取 `observed_status_kinds` 时只接受 list；字符串、数字等非 list 值应按空列表处理，避免把字符串拆成字符集合或让 Runtime Profile 读取失败。
- `RuntimeContractSnapshotService` 必须守护 `runtime_contract_gate.runtime_contract_summary` 的关键嵌套字段，包括 `overall_status / check_count / failed_check_count / missing_payload_count / approval_replay_coverage / approval_lifecycle_recovery_coverage / approval_lifecycle_recovery_coverage.alignment_smoke / approved_tool_execution_coverage / sdk_tool_runtime_execution_coverage / sdk_tool_runtime_execution_coverage.bridge_smoke / tool_runtime_timeout_retry_coverage / tool_runtime_timeout_retry_coverage.timeout_retry_smoke / checkpoint_resume_cursor_coverage / checkpoint_resume_cursor_coverage.cursor_smoke / embedded_sdk_persistence_coverage / embedded_sdk_persistence_coverage.persistence_smoke / worker_ownership_store_mode_coverage / worker_ownership_store_mode_coverage.mode_smoke / recovery_retry_evidence_coverage / recovery_retry_evidence_coverage.retry_smoke / recovery_retry_scheduler_coverage / recovery_retry_scheduler_coverage.scheduler_smoke / durable_recovery_loader_coverage / durable_recovery_loader_coverage.loader_smoke / continuation_descriptor_lifecycle_coverage / continuation_descriptor_lifecycle_coverage.lifecycle_smoke / loader_execution_handoff_coverage / loader_execution_handoff_coverage.handoff_smoke / recovery_audit_operation_history_coverage / recovery_audit_operation_history_coverage.audit_smoke / production_recovery_registry_checkpoint_policy_coverage / production_recovery_registry_checkpoint_policy_coverage.policy_smoke / child_executor_promotion_gate_coverage / child_executor_promotion_gate_coverage.gate_smoke / child_executor_execution_prerequisites_coverage / child_executor_execution_prerequisites_coverage.prerequisites_smoke / child_executor_execution_prerequisites_coverage.context_budget_policy_status / child_executor_execution_prerequisites_coverage.context_budget_policy_missing_sections / child_executor_execution_prerequisites_coverage.opt_in_context_budget_policy_ready / child_executor_execution_prerequisites_coverage.merge_handoff_status / child_executor_execution_prerequisites_coverage.merge_handoff_missing_sections / child_executor_execution_prerequisites_coverage.opt_in_merge_handoff_ready / child_executor_dispatch_coverage / child_executor_dispatch_coverage.dispatch_smoke / child_executor_dispatch_coverage.dispatch_attempt_handoff_status / child_executor_dispatch_coverage.opt_in_dispatch_attempt_handoff_ready / child_executor_dispatch_coverage.opt_in_attempt_validation_ready / child_executor_dispatch_coverage.opt_in_ready_dispatch_status / child_executor_dispatch_coverage.opt_in_ready_dispatch_ready / child_executor_dispatch_coverage.opt_in_ready_handoff_ready / child_executor_dispatch_coverage.opt_in_ready_will_dispatch / child_executor_dispatcher_coverage / child_executor_dispatcher_coverage.dispatcher_smoke / child_executor_dispatch_result_handoff_coverage / child_executor_dispatch_result_handoff_coverage.result_handoff_smoke / child_executor_dispatch_result_handoff_coverage.ready_handoff_status / child_executor_dispatch_result_handoff_coverage.malformed_handoff_status / child_executor_dispatch_result_retry_audit_coverage / child_executor_dispatch_result_retry_audit_coverage.retry_audit_smoke / child_executor_dispatch_result_retry_audit_coverage.retryable_retry_policy_status / child_executor_dispatch_result_retry_audit_coverage.missing_idempotency_status / child_executor_dispatch_retry_scheduler_handoff_coverage / child_executor_dispatch_retry_scheduler_handoff_coverage.handoff_smoke / child_executor_dispatch_retry_scheduler_handoff_coverage.default_status / child_executor_dispatch_retry_scheduler_handoff_coverage.bound_status / child_executor_sandbox_backend_binding_coverage / child_executor_sandbox_backend_binding_coverage.binding_smoke / child_executor_sandbox_backend_binding_coverage.ready_status / child_executor_sandbox_backend_binding_coverage.missing_callable_status / child_executor_sandbox_backend_coverage / child_executor_sandbox_backend_coverage.sandbox_backend_smoke / child_executor_sandbox_backend_coverage.execution_seam_supported / child_executor_sandbox_backend_coverage.execution_completed_status / child_executor_sandbox_backend_coverage.execution_missing_idempotency_status / child_executor_sandbox_backend_coverage.execution_handler_failure_status / subagent_lane_query_detail_coverage / subagent_lane_query_detail_coverage.detail_smoke`；任一字段缺失时 snapshot 应退化为 `degraded`。`child_executor_dispatch_contract` 作为顶层 dispatch boundary 也必须进入 snapshot stable field guard，避免 Runtime Profile 保留旧 shell 但丢失 dispatch readiness 与 attempt handoff 证据。
- `RuntimeContractSnapshotService` 必须守护 `runtime_contract_gate.runtime_contract_artifact_schema` 及其 `contract_version / overall_status / summary_required_fields / summary_missing_fields`，避免 Runtime Profile 保留 gate 外壳但丢失 artifact schema guard。
- `quality_gate_report.py` 渲染 Runtime Contract Summary 表格时只接受 object `approval_replay_coverage`；非 object 值应按缺失处理并显示 coverage 为 `no`，不应中断 Markdown summary 生成。
- `approval_replay_coverage.event_payload_sample` 必须 fail-closed 读取；只有布尔 `true` 或明确真值字符串 `true/ok/yes/1` 可视为覆盖，字符串 `"false"` 等脏值必须显示为未覆盖。
- Runtime recovery approval kernel 使用 `recovery_reason` 作为后端稳定路由码；resolved approval 的 `submit_approval/approved` entrypoint 必须返回 `recovery_reason = already_resolved`，`blocked_reason = approval_already_resolved` 仅作为兼容诊断字段保留。
- Embedded SDK approval lifecycle trace adapter 当前是 opt-in governance recorder；只记录 `approval_resolved / approval_replayed / approval_ignored / recovery_failed_closed` 四类 SDK lifecycle evidence，并且不得改变 approval immutability、recovery reason 或 SDK event stream 结果。
- `SdkApprovalLifecycleTimelineService` 写入 Runtime Trace 时必须使用 compact payload：允许包含 `run_id / conversation_id / user_id / approval_request_id / status_kind / decision / approval_status / original_decision / attempted_decision / submission_status / recovery_reason / blocked_reason / dedupe_key`，不得复制 executable continuation callable、handler、provider client 或 active stream iterator。
- SDK approval lifecycle trace 写入必须 fail-open；recorder 不存在、trace service 不可用、dedupe 命中或 recorder 抛错时，SDK 主流程仍以本地 event stream 和 approval state machine 为真源。
- Runtime recovery 当前暴露 `checkpoint` 与 `resume_cursor` 两层机器可读 contract；`checkpoint` 表达 durable workspace 是否形成可恢复点，`resume_cursor` 表达下一次允许尝试的恢复入口。两者都不得包含 Python callable、active stream iterator 或 provider client。
- `checkpoint.status` 至少包含 `ready / blocked / missing / stale`；`resume_cursor.cursor_status` 至少包含 `ready / blocked / missing / stale`。resolved approval 应返回 stale/state-gated cursor，denied approval 的 cursor `recovery_reason` 必须是 `denied`，不能被后续 approved 反向恢复。
- `DurableRecoveryLoader` 是 SDK recovery probe 的 durable candidate 重建边界：它只读取 durable workspace 中的 run snapshot、event log、approval snapshot、continuation descriptors 与 recovery operation history，并只通过 `EmbeddedContinuationRegistry` 的 binding id 判断能否 reattach；它不执行恢复、不反序列化 callable，也不绕过 checkpoint/resume cursor、worker ownership 或 retry policy。
- `probe_run_recovery(run_id)` 必须暴露 `durable_recovery_loader` evidence。ready candidate 应包含 `contract_version = phase-ii-durable-recovery-loader-v1`、`status = ready`、`recovery_reason = ready_via_registry`、binding evidence 与 `descriptor_lifecycle`；缺 run snapshot、缺 registry binding、resolved approval state 或 callable-like descriptor payload 必须 fail-closed。
- continuation descriptor lifecycle governance 当前已落地为 compact classifier：状态词表为 `created / bound / ready / stale / resolved / unsafe`，`ready` 只表示 descriptor 与 registry binding 可重挂，`bound` 表示存在 binding identity 但未完全解析，`stale` 表示审批/运行等待点已过期，`unsafe` 表示 callable-like payload 或 runtime-only state 进入 descriptor 并必须 fail-closed。该 classifier 不执行恢复、不反序列化 callable，也不等价于 production default recovery authorization。
- durable loader execution handoff policy 当前已落地为 compact fail-closed policy：默认 handoff 返回 `blocked / explicit_handoff_required / will_execute=false`，显式 handoff 但缺 recovery executor binding 时返回 `blocked / recovery_executor_not_bound / will_execute=false`。该 policy 只定义 loader candidate 到未来 executor 的交接边界，不执行恢复、不反序列化 callable，也不表示 production default recovery 已启用。
- recovery audit production readiness 当前已落地为 compact governance evidence：`recovery_audit_production_readiness` 会证明 operation history、audit summary、opt-in timeline writer 与 idempotent trace dedupe 可用，并显式声明 `authorization_source = false`。`persistence_interface.production_recovery_gate` 可将 `recovery_audit_operation_history` 标记为 ready，但 production recovery 仍会因 registry/checkpoint policy、worker ownership gate 与 rollout 缺口保持 blocked。
- production recovery registry/checkpoint policy 当前已落地为 compact side-effect-free evidence：`production_recovery_registry_checkpoint_policy` 会证明 registry binding identity、registry resolution、checkpoint contract、resume cursor contract 与 stale/resolved fail-closed policy 可用，并显式声明 `authorization_source = false`。`persistence_interface.production_recovery_gate` 可将 `registry_binding_resolution` 与 `checkpoint_resume_cursor_gate` 标记为 ready，但 production recovery 仍会因 worker ownership gate 与 rollout 缺口保持 blocked。
- Embedded SDK 当前还暴露 `recovery_operation_contract`，用于描述实际恢复尝试的操作级审计包络。该 contract 支持 `submit_approval.approved` 与 `resume_run.continue_loop` 两个 auditable entrypoint，operation status 至少包含 `attempted / recovered / blocked / failed`。
- `recovery_operation_contract.retry_policy` 当前声明 retry evidence contract 已可用，但 `implemented = false` 表示自动 retry execution / scheduler 尚未实现。该 policy 至少暴露 `max_attempts / backoff_strategy / retryable_reasons / terminal_reasons`，供后续 retry 执行器复用。
- `build_recovery_retry_evidence(...)` 当前是 recovery retry evidence 的专用 classifier：terminal reasons 会输出 `status = terminal`，retryable transient reason 在未耗尽时输出 `status = retryable`，达到 `attempt_number >= max_attempts` 时输出 `status = exhausted / terminal = true`。该 helper 只生成 compact evidence，不执行自动 retry。
- `RecoveryRetryScheduler` 是显式 opt-in retry 执行边界：默认 `enabled = false` 时只返回 `status = disabled` 决策，不执行恢复入口；显式启用后才会读取 latest recovery operation、复用 retry policy/classifier、生成 `idempotency_key`，并只调用 `submit_approval.approved` 或 `resume_run.continue_loop` 这类 recovery entrypoint。
- 生产级自动 retry 必须先通过 `recovery-retry-production-scheduler-gate`：`build_recovery_retry_production_scheduler_gate_contract()` 当前会输出 machine-readable `overall_status / sections / missing_sections / next_allowed_action / non_goals`。durable scheduling state、确定性 idempotency/dedupe、backoff clock、worker ownership 与 recovery audit timeline 任一缺失时，gate 必须 `overall_status = blocked`，且 `production_automatic_retry=True` 的调度请求必须 fail-closed 为 `production_scheduler_gate_blocked`，不得启用后台或默认自动 retry。
- `EmbeddedAgentRuntimeSDK.schedule_recovery_retry(...)` 是 SDK 级 opt-in 入口；成功恢复与 fail-closed 恢复都必须把 compact retry attempt evidence 写入 recovery operation history，且可通过显式 `audit_recorder` 进入 Recovery Audit Timeline。
- `submit_approval(..., retry_attempt=...)` 与 `resume_run(..., continue_loop=True, retry_attempt=...)` 当前可在显式 retry attempt metadata 存在时，把 SDK recovery gate 的 blocked / fail-closed 结果记录为 compact `recovery_operation.retry` evidence；未传入 retry metadata 时继续省略 `retry` 字段。该能力仍不表示 SDK 已具备自动 retry scheduler。
- `backend/agent_framework/recovery_operations.py` 是 recovery operation contract 与 operation record construction 的专用 Module；`EmbeddedAgentRuntimeSDK` 只负责决定何时记录 operation、何时写 metadata/event，不应重新内联 payload 构造细节。
- `recovery_operation` payload 必须保持 compact：允许包含 `operation_id / run_id / entrypoint / operation_status / recovery_reason / blocked_reason / checkpoint_id / resume_cursor_id / continuation_ref / workspace_backend / persistence_posture / worker_ownership / recorded_at`，不得复制 executable continuation callable、handler、provider client、active stream iterator 或完整工具结果正文。
- 当 recovery operation record 显式传入 retry evidence 时，可携带 compact `retry.attempt_number / retry.max_attempts / retry.previous_operation_id / retry.idempotency_key / retry.status / retryable / terminal`；未传入时默认不输出 `retry` 字段，既有恢复消费方不应被迫处理空 retry 外壳。
- `worker_ownership.implemented = false` 仍是默认生产边界事实：未传入 ownership evidence 时，recovery operation 只能说明恢复尝试已审计，不能说明 worker lease、跨实例所有权或抢占控制已经生效。
- `backend/agent_framework/worker_ownership.py` 当前提供 worker ownership seam：默认 `InMemoryRuntimeWorkerOwnershipStore` 仍用于本地预览，新增 `SQLAlchemyRuntimeWorkerOwnershipStore` 可作为显式注入的 durable adapter，二者共享 `claim_run / heartbeat / validate_ownership / get_lease` 与 `lease_id / fencing_token / lease_expires_at` compact evidence。
- `SQLAlchemyRuntimeWorkerOwnershipStore` 会把 ownership lease 持久化到 `runtime_worker_ownership_leases`，并报告 `adapter_kind = sqlalchemy`、`durable = true`。该能力表示 SQL-backed lease/fencing 已可用于跨 store instance 的 ownership evidence，不等同于已经启用数据库 vendor 专用分布式锁或后台自动续租。
- `WORKER_OWNERSHIP_STORE_MODE` 是默认 worker ownership store 的显式装配开关，支持 `memory_only / prefer_sql_with_fallback / strict_sql`。默认值仍是 `memory_only`；`strict_sql` 初始化失败必须 fail closed，`prefer_sql_with_fallback` 可回退到 in-memory 并在 ownership contract 中保留 fallback evidence。
- 当 recovery operation record 显式传入 worker ownership evidence 时，`worker_ownership.implemented = true` 可携带 `worker_id / lease_id / fencing_token / lease_status` 等 compact 字段；payload 仍不得复制 callable、handler、provider client、active stream iterator 或 worker 内部执行对象。
- `EmbeddedAgentRuntimeSDK` 当前支持 opt-in `worker_ownership_store`。只有调用方显式注入 ownership store 且 persisted recovery descriptor 提供 `worker_ownership` evidence 时，SDK 才会在 registry-backed recovery 执行前校验 lease/fencing；校验失败会 fail-closed 并写入 blocked recovery operation。未注入 store 时默认行为保持 `worker_ownership.implemented = false`。
- recovery entry 自动 claim 必须显式启用：默认 `worker_ownership_auto_claim_enabled = false` 时，SDK 仍只使用 descriptor 中已有的 ownership evidence；启用后才会在 registry-backed recovery entrypoint 执行前调用 ownership store claim，并把 compact lease evidence 写入 recovery operation。
- `EmbeddedRuntimeDependencies` 当前已把 `worker_ownership_store` 纳入默认 dependency bundle；`EmbeddedRuntimeFactory.build_runtime_contract()` 会暴露 `worker_ownership.available / adapter_kind / durable / enforcement_mode / operations / fail_closed_reasons / operational_readiness`，并在 `default_runtime_profile` 中暴露 `worker_ownership_store_mode / worker_ownership_store_mode_source`。该依赖默认是 in-memory 且 `durable = false`，只表示 SDK 已有 opt-in ownership gate seam，不表示具备生产分布式锁。
- `worker_ownership.operational_readiness` 是生产启用前的机器可读 checklist：默认 memory/fallback posture 必须是 `readiness_status = preview_or_degraded`，strict SQL posture 可报告 `production_ready`，但 `vendor_lock_posture = sql_row_lease_fencing` 仍明确它是 SQL row lease/fencing，不是 vendor 专用 distributed lock。生产启用前还必须确认 `runtime_worker_ownership_leases` migration、heartbeat renewal、stale fencing fail-closed 与 recovery-entry auto-claim 决策。
- `worker_ownership.renewal_supervisor` 是后台续租 supervisor 的只读 readiness contract 与显式 opt-in seam：当前暴露 `contract_version / overall_status / supervisor_enabled_by_default / policy / missing_sections / next_allowed_action / non_goals`，其中 policy 会说明 `renew_once_supported / owner_identity_required / ttl_interval_policy_ready / controlled_lifecycle_supported / starts_by_default / active / last_renewal_status / stop_supported / failure_fail_closed / lease_loss_fail_closed`。`WorkerOwnershipRenewalSupervisor.renew_once(...)` 只在调用方显式传入 run/worker/lease/fencing evidence 时执行一次 validate + heartbeat；`start(...) / stop(...) / status()` 提供受控 lifecycle，但只有调用方显式 start 才会启动可停止的续租循环，构造时默认 inactive，且默认不启用生产后台 supervisor。
- `worker_ownership.production_rollout` 是生产 rollout 操作化的只读 readiness contract：当前暴露 `contract_version / overall_status / production_rollout_confirmed / checklist / operationalization / missing_sections / next_allowed_action / non_goals`。`operationalization` 会进一步解释 `rollout_mode / required_artifacts / missing_artifacts / rollback_plan_status / fallback_policy_status / renewal_lifecycle_verification_status / auto_claim_decision_status`，并嵌入 `confirmation_decision` 决策记录；该 decision 还会嵌入 `input_source`，说明 rollout confirmation 来源于 config、ops decision record、deployment artifact、change ticket 或 manual approval metadata 的哪一类证据，并透出 source kind、decision id、approver、approval time、target store mode、rollback/fallback/renewal/auto-claim references 与 missing sections。该层只说明 strict mode rollout、fallback policy、migration、renewal lifecycle verification、stale fencing、auto-claim decision、audit evidence、rollback plan、显式 rollout confirmation 与 confirmation input source 缺口，不修改部署状态、不启用生产 ownership。
- `worker_ownership.auto_claim_entrypoint_allowlist` 是恢复入口自动 claim 的只读 allowlist contract：当前默认将 `submit_approval.approved / resume_run.continue_loop` 作为允许被显式 auto-claim policy 考虑的 entrypoints，并暴露 `contract_version / overall_status / allowed_entrypoints / required_entrypoints / missing_entrypoints / default_auto_claim_enabled / requires_production_gate_ready / non_goals`。该 contract ready 只表示 allowlist 已定义，不调用 `claim_run`，不启用默认 auto-claim。
- `worker_ownership.explicit_auto_claim_enablement_gate` 是恢复入口自动 claim 的显式启用只读 gate：当前暴露 `contract_version / overall_status / will_auto_claim / requested_entrypoint / allowed_entrypoints / missing_sections / blocked_reason / policy / next_allowed_action / non_goals`。只有显式 runtime config、production gate ready、durable ownership、descriptor fallback、idempotency/audit evidence、lease validation、rollout auto-claim decision 与 allowlisted entrypoint 全部满足时，才允许 `will_auto_claim = true`；默认保持 blocked，不调用 `claim_run`。
- `worker_ownership.auto_claim_policy` 是恢复入口自动 claim 的只读 policy contract：当前暴露 `contract_version / overall_status / auto_claim_enabled_by_default / policy / missing_sections / next_allowed_action / non_goals`，只解释显式配置、production gate ready 要求、durable ownership、descriptor evidence fallback、idempotency/audit evidence、entrypoint allowlist 与 lease validation 缺口；`policy.entrypoint_allowlist` 会嵌入 allowlist contract，`policy.enablement_gate` 会嵌入 explicit auto-claim enablement gate。默认 allowlist 可为 ready，但 policy 仍因显式配置、production gate、idempotency/audit evidence、rollout auto-claim decision 和 default enablement 缺口保持 blocked，不调用 `claim_run`，不改变 SDK recovery entrypoint 执行。
- `worker_ownership.ownership_audit` 是 ownership audit evidence 的只读 readiness contract：当前暴露 `contract_version / overall_status / authorization_source / evidence / missing_sections / next_allowed_action / non_goals`，只解释 compact ownership evidence、operation history、recovery operation link、timeline writer 与 idempotent dedupe 缺口；`authorization_source` 必须保持 false，audit evidence 不能替代 lease validation 或 recovery execution authorization。
- `worker_ownership.vendor_lock_semantics` 是 vendor-specific distributed lock readiness 的只读 contract：当前暴露 `contract_version / overall_status / production_lock_allowed / current_posture / policy / missing_sections / next_allowed_action / non_goals`，只解释 lock adapter、lock scope、fencing guarantee、failover semantics、TTL/renewal semantics、stale owner cleanup 与 production allowment 缺口；`policy.adapter_contract` 会以 side-effect-free seam 方式暴露 adapter kind、target backend、scope、fencing、TTL/renewal、failover、stale cleanup、acquire/renew/release/probe capability 与 production allowment evidence，默认 blocked 且不执行 acquire/renew/release/probe；当 adapter 指向 PostgreSQL advisory lock 时，`adapter_contract.backend_probe` 会暴露 PostgreSQL probe contract version / status / advisory lock family / lock key derivation / lock scope / fencing binding / TTL-renewal / failover / stale cleanup / probe safety / executes_probe / missing sections，默认 blocked 且不连接 PostgreSQL、不执行 advisory lock SQL；`backend_probe.execution_seam` 现在会进一步暴露 PostgreSQL advisory lock opt-in execution seam 的 contract version / status / executor binding / probe-acquire-renew-release one-shot support / lock-key derivation / default enablement / production allowment / missing sections。`PostgresAdvisoryLockExecutionSeam` 只有调用方显式注入 executor 时才会生成并执行 probe/acquire/renew/release envelope，构造时不连接数据库、不启动后台循环；缺 executor、缺 run/worker/fencing evidence 或 executor 拒绝都会 fail-closed，且 opt-in 执行 evidence 不等于 production default ownership 授权。`policy.target_decision` 还会以只读方式暴露 vendor lock target backend、adapter kind、scope、fencing、TTL/renewal、failover、stale cleanup 与 production allowment 决策证据，且 `target_decision.input_source` 会解释该 target decision 来自 config、ops decision record、rollout artifact 还是 manual approval metadata。strict SQL 的 `sql_row_lease_fencing` 必须继续显示为当前 posture，但 `sql_row_lease_is_vendor_lock = false` 且 adapter contract / backend probe / execution seam / target decision / input source 都不得把 SQL row lease 视作 vendor lock。
- `worker_ownership.production_default_enablement_input_source` 是默认生产启用请求的只读来源 contract：当前暴露 `contract_version / overall_status / input_source_kind / request_id / requested_by / requested_at / target_store_mode / rollout_artifact / vendor_lock_decision_id / renewal_lifecycle_reference / auto_claim_decision_reference / audit_evidence_reference / rollback_plan_reference / fallback_policy_reference / missing_sections / next_allowed_action / non_goals`。默认 blocked；只有 config、ops decision record、rollout artifact 或 manual approval 这类来源携带 request、approval、strict SQL 目标模式、rollout artifact、vendor lock decision、renewal lifecycle、auto-claim decision、audit、rollback 和 fallback evidence 时才可 ready，但 ready 也只是描述性证据。
- `worker_ownership.postgres_rollout_artifact_consumer` 是 PostgreSQL advisory lock rollout artifact / runtime config 的只读 consumer：当前暴露 `contract_version / overall_status / source_kind / artifact_id / approved_by / approved_at / target_store_mode / target_backend / lock_adapter_kind / rollout_artifact / vendor_lock_decision_id / renewal_lifecycle_reference / auto_claim_decision_reference / audit_evidence_reference / rollback_plan_reference / fallback_policy_reference / postgres_execution_seam_status / enablement_input_source / will_enable_production_default / executes_advisory_lock / missing_sections`。默认 blocked 且不读取文件、不拉取远程 config、不连接 PostgreSQL、不执行 advisory lock SQL；完整 artifact 加 ready 的 opt-in execution seam 只会生成 ready 的 nested `production_default_enablement_input_source` 证据，仍不会打开 production default ownership。
- `worker_ownership.production_enablement_strategy` 是默认生产启用的只读策略 contract：当前暴露 `contract_version / overall_status / required_sections / blocking_sections / production_default_enabled_requested / production_default_allowed / input_source / policy / next_allowed_action / non_goals`。只有所有必需 section ready、显式请求 production default enablement 且 input source ready 时，才允许 `fail_closed_default_decision` ready；默认仍 blocked。
- `worker_ownership.production_enablement_runtime_config_consumer` 是生产启用 runtime config 的只读 consumer：当前可把 caller-owned `runtime_config / rollout_artifact / ops_decision_record / manual_approval` metadata 标准化为 nested `production_default_enablement_input_source` 与 `production_gate_composition_dry_run` evidence，并暴露 source kind、config id、approval、strict SQL target、PostgreSQL advisory lock adapter、rollout artifact、vendor lock decision、renewal lifecycle、auto-claim decision、audit、rollback/fallback references、missing sections 与 non-execution flags。默认 blocked；完整 config 加 ready dry-run 只会让 consumer evidence ready，仍固定 `will_enable_production_default = false / executes_lock = false / starts_background_worker = false / runs_recovery_auto_claim = false`，不读取文件、不拉取远程 config、不修改环境、不解除 durable recovery blocker。
- `EmbeddedRuntimeFactory` 当前已支持显式 `worker_ownership_production_enablement_config` 输入，并通过 `worker_ownership.production_enablement_runtime_config_consumer` 暴露 factory-built evidence；`RuntimeSurfaceService` 只会从已物化的 runtime surface effective config 中传入本地 dict，不读取远端配置、文件或 secret store。该 binding 只证明 Runtime Profile/Factory 装配路径可观测，不代表 production default ownership、advisory lock execution、background renewal 或 recovery auto-claim 已启用。
- `worker_ownership.production_gate` 是 worker ownership 默认生产启用的 fail-closed gate：当前会暴露 `contract_version / overall_status / production_default_enabled / sections / missing_sections / next_allowed_action / non_goals`。即使 strict SQL adapter 已具备 durable row lease/fencing，只要 vendor lock semantics、后台 renewal supervisor、rollout checklist、recovery-entry auto-claim policy、audit evidence 或 fail-closed default decision 缺失，gate 仍必须 `overall_status = blocked`，且不得把 worker ownership 作为默认生产执行授权。`vendor_lock_semantics` section 必须携带 vendor lock status / missing sections / current posture / sql row lease posture / adapter / scope / fencing / failover / TTL-renewal / stale cleanup / production allowment evidence，并额外携带 vendor lock adapter contract version / status / kind / target backend / scope / fencing / TTL-renewal / failover / stale cleanup / acquire-renew-release-probe support / missing sections / SQL-row-lease-not-vendor-lock / production allowment evidence，PostgreSQL probe contract version / status / executes flag / missing sections 以及 PostgreSQL execution seam contract version / status / executor bound / one-shot operation support / default enablement / production allowment / missing sections，vendor lock target decision contract version / status / recorded flag / backend / adapter kind / scope / fencing / TTL-renewal / failover / stale cleanup / missing sections / SQL-row-lease-not-vendor-lock / production allowment evidence，以及 target decision input source contract version / status / source kind / decision id / approver / approval time / backend / adapter kind / rollout artifact / config key / manual approval reference / missing sections / SQL-row-lease-not-vendor-lock evidence；`heartbeat_renewal_supervisor` section 必须携带 renewal supervisor status / missing sections / supervisor default flag / renew-once support / owner identity requirement / TTL-interval policy readiness / controlled lifecycle support / starts-by-default / active / last renewal / stop support / failure fail-closed / lease-loss fail-closed evidence；`rollout_checklist` section 必须携带 rollout readiness status / missing sections / production rollout flag / strict-mode rollout / fallback policy / migration / stale fencing / rollback plan / rollout operationalization status / rollout mode / missing artifacts / fallback policy status / renewal lifecycle verification status / auto-claim decision status，以及 rollout confirmation decision contract version / status / recorded flag / decision id / approver / approval time / target store mode / missing sections evidence，并额外携带 rollout confirmation input source contract version / status / source kind / decision id / approver / approval time / target store mode / rollback/fallback/renewal/auto-claim references / missing sections / SQL-row-lease-not-rollout-authority evidence；`recovery_entry_auto_claim_policy` section 必须携带 auto-claim policy status / missing sections / default flag / descriptor fallback / gate readiness / allowlist / lease validation evidence，并额外暴露 auto-claim entrypoint allowlist contract version / status / allowed entrypoints / missing entrypoints / default auto-claim flag / production gate requirement，以及 explicit auto-claim enablement gate version / status / will-auto-claim / requested entrypoint / missing sections / blocked reason；`ownership_audit_evidence` section 必须携带 audit status / missing sections / compact evidence / operation history / recovery operation link / timeline writer / idempotent dedupe / authorization-source evidence；`fail_closed_default_decision` section 必须携带 enablement strategy status / blocking sections / requested flag / allowed flag、enablement input source contract version / status / source kind / request id / requester / requested time / target store mode / rollout artifact / vendor lock decision / renewal lifecycle / auto-claim decision / audit / rollback / fallback references / missing sections、explicit enablement requirement / all-required-sections readiness / SQL row lease not default authority evidence；该 gate 现在会作为 compact evidence 联动进入 `persistence_interface.production_recovery_gate.sections[name=worker_ownership_production_gate]`，但只作为阻断证据，不授权 durable recovery 执行。
- `probe_run_recovery(run_id)` 必须返回 `recovery_operation_boundary`，让恢复消费方知道哪些入口具备 operation evidence，以及 worker ownership 仍是后续边界。
- 当 `submit_approval(..., "approved")` 或 `resume_run(..., continue_loop=True)` 通过 persisted descriptor + registry reattachment 成功恢复时，run metadata 必须写入 `latest_recovery_operation.operation_status = recovered`；当实际恢复尝试 fail-closed 时，`recovery_failed_closed` event 必须携带 `recovery_operation.operation_status = blocked`。
- `runtime_contract_smoke.py` 必须输出 `approval_lifecycle_recovery_alignment` check，证明 approved replay、denied reversal ignored 与 resolved approval recovery gate 使用同一套 machine-readable reason。
- `runtime_contract_smoke.py` 必须输出 `durable_checkpoint_resume_cursor` check，证明 durable checkpoint 与 resume cursor 可从真实 SDK recovery probe 中派生，且 ready 状态必须同时满足 `checkpoint.status = ready`、`checkpoint_kind = approval_waiting`、`resume_cursor.cursor_status = ready`、`entrypoint = submit_approval.approved`、`recovery_reason = ready_via_registry`。
- `runtime_contract_smoke.py` 必须输出 `durable_recovery_loader` check，证明 durable loader 能产出 ready registry-backed candidate，并覆盖 missing run snapshot、unresolved binding、stale approval state 与 unsafe descriptor 的 fail-closed reason；Quality Gate / Runtime Contract Gate / Snapshot 必须归一化并守护 `runtime_contract_summary.durable_recovery_loader_coverage.loader_smoke`、`runtime_contract_summary.continuation_descriptor_lifecycle_coverage.lifecycle_smoke` 与 `runtime_contract_summary.loader_execution_handoff_coverage.handoff_smoke`。
- `runtime_contract_smoke.py` 必须输出 `embedded_sdk_persistence_posture` check，证明 `memory_preview / durable_ready / durable_degraded` 三类 SDK persistence posture 都由 workspace backend description 派生，而不是由构造参数或前端展示逻辑推断。
- `runtime_contract_smoke.py` 的 `embedded_sdk_persistence_posture` check 还必须输出 durable workspace production recovery gate evidence，证明 `durable_ready` 仍不等同于默认生产跨进程恢复授权；该 evidence 必须包含 linked worker ownership gate status / missing sections / production default flag，证明 ownership gate blocked 会让 durable recovery gate 保持 blocked。Quality Gate 与 Runtime Contract Gate 必须把该证据归一化进 `runtime_contract_summary.embedded_sdk_persistence_coverage`，旧报告或缺字段应 fail-closed 为未覆盖。
- `quality_gate_report.py` 与 Runtime Contract Gate 必须从 `approval_lifecycle_recovery_alignment` check 推导 `runtime_contract_summary.approval_lifecycle_recovery_coverage`；check 缺失、非对象或旧报告应 fail-closed 为 `alignment_smoke = false`，而不是让消费者自行扫描 raw checks。
- `quality_gate_report.py` 与 Runtime Contract Gate 必须从 `durable_checkpoint_resume_cursor` check 推导 `runtime_contract_summary.checkpoint_resume_cursor_coverage`；check 缺失、非对象或旧报告应 fail-closed 为 `cursor_smoke = false`。
- `quality_gate_report.py` 与 Runtime Contract Gate 必须从 `embedded_sdk_persistence_posture` check 推导 `runtime_contract_summary.embedded_sdk_persistence_coverage`；check 缺失、非对象或证据不完整时应 fail-closed 为 `persistence_smoke = false`。
- `runtime_contract_smoke.py` 必须输出 `worker_ownership_store_mode` check，证明默认 `memory_only`、默认 in-memory 非 durable、`WORKER_OWNERSHIP_STORE_MODE` 进入 configurable / hot-reloadable bootstrap knobs，并覆盖 `strict_sql` 与 `prefer_sql_with_fallback` 的模式证据；该 check 还必须包含 operational readiness evidence，确认 memory/fallback 非 production-ready、strict SQL production-ready、vendor lock posture 与 migration checklist 机器可读。
- `runtime_contract_smoke.py` 的 `worker_ownership_store_mode` check 还必须输出 production gate evidence，证明 strict SQL row lease/fencing 仍因 `vendor_lock_semantics / heartbeat_renewal_supervisor / rollout_checklist / recovery_entry_auto_claim_policy / ownership_audit_evidence / fail_closed_default_decision` 等缺口保持 production default disabled；该 evidence 必须包含 vendor lock contract version / status / missing sections / current posture / SQL row lease posture / adapter / scope / fencing / failover / TTL-renewal / stale cleanup / production allowment evidence，vendor lock adapter contract version / status / kind / target backend / scope / fencing / TTL-renewal / failover / stale cleanup / acquire-renew-release-probe support / missing sections / SQL-row-lease-not-vendor-lock / production allowment evidence，PostgreSQL probe evidence 与 PostgreSQL advisory lock execution seam evidence，证明默认无 executor 时 blocked 且不执行 SQL、显式注入 executor 时只产生 opt-in probe/acquire envelope 且仍不允许 production lock，PostgreSQL rollout artifact consumer evidence、PostgreSQL vendor lock target artifact binding evidence、PostgreSQL vendor lock semantics binding evidence 与 PostgreSQL vendor lock production gate wiring decision evidence，证明 rollout artifact 可被只读映射为 target decision input / target decision，并进一步形成 vendor lock semantics candidate；ready semantics candidate 可被显式批准为 future production gate input，但 wiring decision 仍不执行 advisory lock SQL、不会启用 production lock、不会更新默认 production gate，worker ownership production gate composition dry-run evidence，证明所有 required production evidence 可被组合成 ready dry-run，但 dry-run 仍不会启用 production default、不会执行 lock、不会启动 background worker、不会运行 recovery auto-claim，vendor lock target decision contract version / status / recorded flag / backend / adapter kind / scope / fencing / TTL-renewal / failover / stale cleanup / missing sections / SQL-row-lease-not-vendor-lock / production allowment evidence，renewal supervisor contract version / status / missing sections / supervisor default flag / renew-once supported / owner identity required / TTL-interval policy ready / controlled lifecycle / starts-by-default / active / last renewal / stop support / failure fail-closed / lease-loss fail-closed / one-shot renewal status / stale fencing blocked / explicit start-stop lifecycle evidence，rollout readiness contract version / status / missing sections / production rollout flag / migration / stale fencing / rollback plan / rollout operationalization / rollout mode / missing artifacts / fallback policy / renewal lifecycle verification / auto-claim decision evidence，rollout confirmation decision evidence 与 rollout confirmation input source evidence，auto-claim policy contract version / status / missing sections / default flag / descriptor fallback / lease validation / entrypoint allowlist evidence，auto-claim entrypoint allowlist contract version / status / allowed entrypoints / missing entrypoints / default auto-claim flag / production gate requirement evidence，explicit auto-claim enablement gate version / status / will-auto-claim / requested entrypoint / missing sections / blocked reason evidence，ownership audit contract version / status / missing sections / compact evidence / operation history / recovery operation link / timeline writer / idempotent dedupe / authorization-source evidence，以及 enablement strategy contract version / status / blocking sections / requested flag / allowed flag / explicit enablement requirement / all-required-sections readiness / fail-closed posture / SQL-row-lease-not-default-authority evidence。Quality Gate 与 Runtime Contract Gate 必须把该证据归一化进 `runtime_contract_summary.worker_ownership_store_mode_coverage`，旧报告或缺字段应 fail-closed 为未覆盖。
- `quality_gate_report.py` 与 Runtime Contract Gate 必须从 `worker_ownership_store_mode` check 推导 `runtime_contract_summary.worker_ownership_store_mode_coverage`；check 缺失、非对象或证据不完整时应 fail-closed 为 `mode_smoke = false`。
- `runtime_contract_smoke.py` 必须输出 `recovery_retry_evidence` check，证明显式 retry attempt metadata 会在 SDK fail-closed recovery path 中形成 compact retry evidence；该 check 只验证 audit/quality-gate evidence，不执行自动 retry scheduler。当前 fail-closed smoke 样本可使用 `workspace_backend_not_durable` 这类非 retryable reason，只要 exhausted evidence 保留 attempt bounds、`terminal = true`、recovery reason 与 idempotency key 即可视为覆盖。
- `quality_gate_report.py` 与 Runtime Contract Gate 必须从 `recovery_retry_evidence` check 推导 `runtime_contract_summary.recovery_retry_evidence_coverage`；check 缺失、非对象、旧报告或证据不完整时应 fail-closed 为 `retry_smoke = false`。
- `runtime_contract_smoke.py` 必须输出 `recovery_retry_scheduler` check，证明 retry scheduler 默认保持 disabled 且显式 enabled 后只执行受支持的 recovery entrypoint；Quality Gate / Runtime Contract Gate / Snapshot 必须归一化并守护 `runtime_contract_summary.recovery_retry_scheduler_coverage.scheduler_smoke`。
- `runtime_contract_smoke.py` 必须输出 `child_executor_promotion_gate` check，证明默认 child executor promotion gate 仍保持 relationship-only blocked 决策且证据机器可读；`quality_gate_report.py` 与 Runtime Contract Gate 必须从该 check 推导 `runtime_contract_summary.child_executor_promotion_gate_coverage`，缺失、非对象或证据不完整时应 fail-closed 为 `gate_smoke = false`。
- `child_executor_promotion_gate` 必须嵌套暴露 `child_executor_execution_prerequisites`，用于说明真实 child executor 启动前仍缺哪些 execution prerequisites。该 contract 至少包含 `contract_version / overall_status / ready / requirements / missing_requirements / recommended_next_step`，并且默认必须保持 `overall_status = blocked`、`ready = false`、relationship seam preserved。
- `runtime_contract_smoke.py` 的 `child_executor_promotion_gate` check 必须同时输出 execution prerequisite evidence；`quality_gate_report.py` 与 Runtime Contract Gate 必须从该 check 推导 `runtime_contract_summary.child_executor_execution_prerequisites_coverage`，缺失、非对象或证据不完整时应 fail-closed 为 `prerequisites_smoke = false`。
- `child_executor_sandbox_backend_binding` 当前是 sandbox worker backend 到 dispatcher backend adapter 的显式绑定 gate：它区分 adapter contract ready、explicit executor opt-in ready、dispatcher backend adapter callable 三层证据。默认缺显式 binding 或缺 callable adapter 时必须保持 blocked；ready binding 仍只表示 dispatcher 具备可调用 adapter 边界，不启动 worker、不写队列、不合并结果。
- `runtime_contract_smoke.py` 必须输出 `child_executor_sandbox_backend_binding` check，覆盖默认 blocked、缺 dispatcher callable adapter、显式 opt-in ready 三条路径；`quality_gate_report.py` 与 Runtime Contract Gate 必须从该 check 推导 `runtime_contract_summary.child_executor_sandbox_backend_binding_coverage`，缺失、非对象或证据不完整时应 fail-closed 为 `binding_smoke = false`。
- `runtime_contract_smoke.py` 必须输出 `child_executor_dispatch_contract` check，证明默认 dispatch boundary 仍保持 blocked、`dispatch_ready = false`、`will_dispatch = false`，且 backend dispatch readiness blocker 机器可读；该 check 还必须覆盖 opt-in sandbox dispatch-ready contract、默认 handoff blocked、opt-in sandbox attempt envelope-ready、missing idempotency fail-closed、unsafe payload guard fail-closed evidence。`quality_gate_report.py` 与 Runtime Contract Gate 必须从该 check 推导 `runtime_contract_summary.child_executor_dispatch_coverage`，其中 `opt_in_ready_dispatch_status = ready`、`opt_in_ready_dispatch_ready = true`、`opt_in_ready_handoff_ready = true`、`opt_in_ready_will_dispatch = false` 表示只读 dispatch contract 已可解释 sandbox-ready 条件，但不会启动 worker；缺失、非对象或证据不完整时应 fail-closed 为 `dispatch_smoke = false`。
- `runtime_contract_smoke.py` 必须输出 `child_executor_dispatcher` check，证明真实 dispatcher 默认 disabled、不调用 backend，且只有显式 enabled 加 ready dispatch contract 时才进入 backend adapter；`quality_gate_report.py` 与 Runtime Contract Gate 必须从该 check 推导 `runtime_contract_summary.child_executor_dispatcher_coverage`，缺失、非对象或证据不完整时应 fail-closed 为 `dispatcher_smoke = false`。
- `runtime_contract_smoke.py` 必须输出 `child_executor_dispatch_result_handoff` check，证明 dispatcher 后置 result handoff 能覆盖 ready sandbox result、default blocked result 与 malformed result fail-closed；`quality_gate_report.py` 与 Runtime Contract Gate 必须从该 check 推导 `runtime_contract_summary.child_executor_dispatch_result_handoff_coverage`，缺失、非对象或证据不完整时应 fail-closed 为 `result_handoff_smoke = false`。该 coverage 只说明 compact result audit handoff 健康，不表示 parent merge、retry scheduling、默认 worker 或生产 dispatch 已启用。
- `runtime_contract_smoke.py` 必须输出 `child_executor_dispatch_result_retry_audit_policy` check，证明 dispatch result retry audit policy 能覆盖 success/no-retry、retryable failure、terminal failure 与 missing-idempotency fail-closed；`quality_gate_report.py` 与 Runtime Contract Gate 必须从该 check 推导 `runtime_contract_summary.child_executor_dispatch_result_retry_audit_coverage`，缺失、非对象或证据不完整时应 fail-closed 为 `retry_audit_smoke = false`。该 coverage 只说明 retry posture/audit/idempotency evidence 健康，不表示 retry 已调度、worker 已启动或 production dispatch 已授权。
- `runtime_contract_smoke.py` 必须输出 `child_executor_dispatch_retry_scheduler_handoff` check，证明 retryable dispatch result audit evidence 在缺 scheduler binding 时仍 blocked，缺 idempotency / audit evidence 时 fail-closed，terminal result 不可进入 scheduler handoff，显式 bound handoff 也保持 `will_schedule_retry = false`。`quality_gate_report.py` 与 Runtime Contract Gate 必须从该 check 推导 `runtime_contract_summary.child_executor_dispatch_retry_scheduler_handoff_coverage`，缺失、非对象或证据不完整时应 fail-closed 为 `handoff_smoke = false`。该 coverage 只说明 retry audit evidence 到未来 scheduler 的 handoff gate 健康，不调度 retry、不启动 worker、不默认启用 retry scheduler。
- `runtime_contract_smoke.py` 必须输出 `child_executor_sandbox_backend` check，证明 sandbox worker backend adapter 的 ready contract、missing guard fail-closed、unsafe payload fail-closed、compact attempt envelope、backend invocation count 与 opt-in `SandboxChildExecutorBackend` execution seam 已进入门禁覆盖；`quality_gate_report.py`、Runtime Contract Gate、health trace normalization 与 Snapshot 必须从该 check 推导并守护 `runtime_contract_summary.child_executor_sandbox_backend_coverage.sandbox_backend_smoke` 以及 `execution_seam_supported / execution_completed_status / execution_missing_idempotency_status / execution_handler_failure_status`。该 coverage 只说明 adapter gate 与显式 seam evidence 健康，不表示默认启用 worker、queue、sandbox runtime、远端 executor、parent merge、retry scheduling 或 production dispatch authorization。
- `child_executor_backend_registry` 当前是 child executor backend readiness 的后端真源。默认 registry 至少暴露 `embedded_sdk_worker` 作为 known candidate，但 `dispatch_ready = false`、`dispatch_mode = not_implemented`，因此它只满足“backend id 可识别”，不表示真实 child executor dispatch 已可用。
- `child_executor_dispatch_contract` 当前是 child executor 真正执行前的最终 side-effect-free 边界。它读取 promotion gate、execution prerequisites、backend registry、sandbox backend binding、sandbox execution seam 与 payload/idempotency guard。默认保持 `overall_status = blocked`、`dispatch_ready = false`、`will_dispatch = false`，避免消费方把 `promotion_gate.allowed = true` 误解释为已经可以启动真实 worker。显式 opt-in 且 sandbox seam/payload/idempotency 全 ready 时，该 contract 可以报告 `overall_status = ready`、`dispatch_ready = true` 与 `sandbox_dispatch_ready_opt_in = true`，但 `will_dispatch` 仍必须为 `false`，且不会调用 backend adapter。其嵌套 `child_executor_dispatch_attempt_handoff` 只验证 dispatch attempt envelope handoff 是否可构造；真实调用仍必须经过显式 enabled 的 `ChildExecutorDispatcher` 与注入 backend adapter。
- `child_executor_execution_prerequisites` 现在要求 `explicit_executor_binding_opt_in`：payload 或 metadata 中的显式 opt-in 只能把 record-only relationship binding 升级为可测试的 skeleton execution 前置证据，不能代表默认 worker dispatch、queue、sandbox runtime 或远端 executor 已启用。`child_executor_dispatch_contract` 也会暴露 explicit binding status/source/backend evidence；缺失 opt-in 时必须把 `explicit_executor_binding_opt_in` 放入 blockers，并保持 `will_dispatch = false`。
- Runtime Surface 或 SDK 测试如果要断言已执行 child output merge 语义（例如 `risk_review` parent merge state），fixture 必须显式提供 `explicit_executor_binding_opt_in = true`；缺失 opt-in 的 blocked merge 不能被治理读模型误当成已执行 child semantics。
- `child_executor_context_budget_policy` 现在作为 `child_context_budget_defined` 的只读 evidence 进入 preflight 与 execution prerequisites：只有 `payload/metadata.child_context_budget`、`context_budget` 或 `scheduler_policy.max_turns/timeout_seconds` 中存在可归一化的正向 bounded limit 时才 ready；空对象、无界策略或缺失来源必须 fail-closed，并在 quality gate 中暴露 `context_budget_policy_status / context_budget_policy_missing_sections / opt_in_context_budget_policy_ready`。
- `child_result_merge_handoff_contract` 现在作为 `child_result_merge_semantics_defined` 的只读 evidence 进入 preflight 与 execution prerequisites：只有 `append_summary / role_sections` 或可归一化到这些策略的 `result_merge_policy` 才 ready；缺失来源、空策略或未知策略必须 fail-closed，并在 quality gate 中暴露 `merge_handoff_status / merge_handoff_missing_sections / opt_in_merge_handoff_ready`。该 contract 只描述 parent merge handoff expectations，不执行 parent merge，也不授权 worker dispatch。
- `child_executor_sandbox_worker_backend` 当前定义真实 child executor dispatch 前的 sandbox backend adapter contract seam，并提供显式 opt-in `SandboxChildExecutorBackend` execution seam：backend 必须暴露 adapter contract、sandbox/resource/audit/idempotency guard evidence，并返回 compact dispatch attempt envelope。缺 guard、unsafe payload、missing child/idempotency field、malformed attempt output 或 adapter/executor exception 都必须 fail-closed；默认 registry 仍保持 relationship-only，不会启动 worker、queue 或 sandbox runtime。
- `ChildExecutorDispatcher` 是 `child_executor_dispatch_contract` 后面的 opt-in execution boundary。默认构造保持 disabled 并记录 blocked audit evidence；只有显式启用、dispatch contract ready、且 backend adapter 已注册时才会调用 adapter，adapter 异常、unsafe sandbox payload 或结果非法都 fail-closed。attempt handoff readiness 只是 dispatcher 前置证据，不会自动启动 worker。其返回的 `dispatch_result_handoff` 是后置 compact audit handoff evidence，只说明 output/audit refs 与 schema guard 可解释，不执行 parent merge、不调度 retry，也不授权默认生产 dispatch。
- `quality_gate_report.py` 渲染 Runtime Contract Summary 表格时，`Approval Lifecycle Recovery` 列必须按 `replayed / ignored / already_resolved` 三个证据字段重新判定；不能只读取 `alignment_smoke` 原始布尔值。
- Runtime Contract Gate 与 degraded trace 归一化 `approval_lifecycle_recovery_coverage` 时必须重新校验 `replayed_submission_status = replayed`、`ignored_submission_status = ignored`、`resolved_recovery_reason = already_resolved`；即使 artifact 声称 `alignment_smoke = true`，证据字段不一致也必须 fail-closed 为 `false`。
- `runtime_contract_smoke.py` 必须输出 `runtime_approved_tool_execution_bridge` check，证明 facade + ToolRuntimeService 的 `ask / high_risk` 工具在 SDK approval approved 后可恢复执行一次，并证明 `deny` 工具不能被 approved override 绕过。
- `runtime_contract_smoke.py` 还必须输出 `sdk_tool_runtime_execution_bridge` check，证明 SDK 直连 `register_tool -> execute_run(tool_policy) -> ToolRuntimeService` 能覆盖 `auto / ask-approved / deny` 三条路径；`quality_gate_report.py` 与 Runtime Contract Gate 必须从该 check 推导 `runtime_contract_summary.sdk_tool_runtime_execution_coverage`，缺失或证据不匹配时 fail-closed 为 `bridge_smoke = false`。
- `runtime_contract_smoke.py` 必须输出 `tool_runtime_timeout_retry` check，证明 ToolRuntimeService 自身的 synchronous exception retry 与 post-call elapsed timeout metadata 保持可观测：一次 transient error recovery 必须输出 `retry.status = recovered / attempt_count = 2`，持续失败必须输出 `retry.status = exhausted / attempt_count = 2`，同步调用超过 `timeout_seconds` 必须输出 `status = timeout` 与 `timeout.status = exceeded`。该 check 只证明 metadata 与边界，不声明 hard cancellation、sandbox execution 或 worker-level timeout enforcement；`quality_gate_report.py` 与 Runtime Contract Gate 必须从该 check 推导 `runtime_contract_summary.tool_runtime_timeout_retry_coverage`，缺失或证据不匹配时 fail-closed 为 `timeout_retry_smoke = false`。
- `runtime_contract_smoke.py` 的 `runtime_profile_contract_snapshot` check 必须携带 `runtime_contract_artifact_schema_status / runtime_contract_artifact_schema_missing_field_count / runtime_contract_artifact_schema_missing_fields`，让 quality gate artifact 可直接看到 Runtime Profile 中 artifact schema guard 的证据。
- `quality_gate_report.py` 与 Runtime Contract Gate 必须从 `runtime_approved_tool_execution_bridge` check 推导 `runtime_contract_summary.approved_tool_execution_coverage`；check 缺失、非对象或旧报告应 fail-closed 为 `bridge_smoke = false`，而不是让消费者自行扫描 raw checks。
- `runtime_contract_smoke.py` 必须输出 `subagent_lane_query_detail` check，证明 dedicated subagent lane query detail contract 已进入 smoke gate；`quality_gate_report.py` 与 Runtime Contract Gate 必须从该 check 推导 `runtime_contract_summary.subagent_lane_query_detail_coverage`，缺失时 fail-closed 为 `detail_smoke = false`。
- `EmbeddedRunWorkspaceStore.describe_backend()` 必须暴露 `state_contract`，明确 durable state kinds 与 runtime-only state kinds；SQLAlchemy 与 in-memory backend 使用同一份状态词表，但只有 durable 且未 fallback 的 backend 才能作为跨进程恢复候选。
- `state_contract.durable_state_kinds` 当前至少包含 `run_snapshot / event_log / approval_snapshot / tool_continuation_descriptor / loop_continuation_descriptor / artifact_ref / child_executor_output`；`runtime_only_state_kinds` 当前至少包含 `executable_continuation_callable / python_function_binding / temporary_stream_cursor / in_process_event_iterator`。
- `embedded_sdk_persistence_interface` 是 SDK / Facade / Runtime Surface 判断默认持久化姿态的机器可读 contract；它只描述 storage capability，不描述某个 run 是否已经可恢复。
- `persistence_interface.persistence_posture` 当前至少包含 `memory_preview / durable_ready / durable_degraded`：内存 backend 固定是 `memory_preview`，durable 且未 fallback 才是 `durable_ready`，durable 配置但 fallback 激活必须是 `durable_degraded`。
- `persistence_interface.cross_process_candidate` 只能表示当前 backend 有资格成为跨进程恢复候选；单个 run 仍必须通过 descriptor、checkpoint、resume cursor、approval state 与 registry binding gate，不能因为 `durable_ready` 直接跳过恢复检查。
- `persistence_interface.production_recovery_gate` 是 durable workspace 默认跨进程恢复启用前的 fail-closed gate：当前暴露 `contract_version / overall_status / production_default_enabled / sections / missing_sections / next_allowed_action / non_goals`。descriptor lifecycle governance、registry binding policy、checkpoint/resume cursor gate、recovery audit 与 loader execution handoff policy 已可标记为 ready；即使 backend 为 `durable_ready`，只要 worker ownership production gate 或 rollout 缺失，gate 仍必须 `overall_status = blocked`，且不得默认执行跨进程恢复。`worker_ownership_production_gate` section 必须保留 ownership gate 的 compact blocker evidence，包括 `worker_ownership_gate_status / worker_ownership_missing_sections / worker_ownership_production_default_enabled`。
- `persistence_interface.cross_process_block_reason` 当前至少包含 `workspace_backend_not_durable / workspace_backend_fallback_active`；该字段是持久化姿态 blocker，不替代 `probe_run_recovery(...).reason`。
- 当报告中的 `runtime_contract_summary` 计数字段不可解析或为负数时，后端会回退到 `contract_checks` 推导出的 summary，并让 summary 状态跟随该推导结果，避免出现 gate 与 summary 状态互相矛盾。
- `contract_checks[*].missing_payload_count / checked_event_count` 同样按非负整数读取；不可解析或为负数时归一为 `None`，summary fallback 会按 `0` 处理，避免单个脏 check 字段拖垮整个 Runtime Profile。
- `runtime_contract_gate_degraded` 治理 trace payload 会携带规范化后的 `runtime_contract_summary`，其 fingerprint / dedupe key 也会纳入 summary 关键字段；payload 缺口数、approval replay 覆盖状态或 approved tool bridge 覆盖状态变化时，应记录为新的治理信号。
- `runtime_contract_gate_degraded.detail` 必须包含 `approval_lifecycle=<covered|missing|unknown>`、`approved_tool=<covered|missing|unknown>`、`sdk_tool=<covered|missing|unknown>`、`embedded_persistence=<covered|missing|unknown>`、`worker_ownership=<covered|missing|unknown>`、`child_executor_gate=<covered|missing|unknown>`、`child_executor_prerequisites=<covered|missing|unknown>`、`child_executor_dispatch=<covered|missing|unknown>` 与 `subagent_detail=<covered|missing|unknown>`，从归一化后的 runtime contract summary coverage 派生；这些字段只是紧凑排障摘要，payload 仍是事实来源。
- `runtime_contract_gate_degraded.detail` 必须包含 `checkpoint_cursor=<covered|missing|unknown>`，从归一化后的 `checkpoint_resume_cursor_coverage` 派生；coverage 变化必须进入 fingerprint / dedupe key。
- `runtime_contract_gate_degraded.detail` 必须包含 `recovery_retry=<covered|missing|unknown>`，从归一化后的 `recovery_retry_evidence_coverage` 派生；该字段只说明显式 retry evidence 是否被门禁覆盖，不表示自动 retry scheduler 已实现。
- `runtime_contract_gate_degraded.detail` 必须包含 `recovery_retry_scheduler=<covered|missing|unknown>`、`durable_loader=<covered|missing|unknown>`、`child_executor_dispatcher=<covered|missing|unknown>`、`child_executor_result_handoff=<covered|missing|unknown>` 与 `child_executor_retry_audit=<covered|missing|unknown>`，分别从归一化后的 `recovery_retry_scheduler_coverage`、`durable_recovery_loader_coverage`、`child_executor_dispatcher_coverage`、`child_executor_dispatch_result_handoff_coverage` 与 `child_executor_dispatch_result_retry_audit_coverage` 派生；这些字段说明 opt-in scheduler、durable recovery loader、dispatcher 边界、dispatch result handoff 与 retry audit policy 是否进入门禁覆盖。
- `runtime_contract_gate_degraded.payload.runtime_contract_summary.approval_lifecycle_recovery_coverage` 必须由后端 trace 入口归一化后写入；缺失或非对象字段应按 `alignment_smoke = false` 处理，确保审批生命周期恢复对齐状态进入 fingerprint / dedupe key。
- `runtime_contract_gate_degraded.payload.runtime_contract_summary.approved_tool_execution_coverage` 必须由后端 trace 入口归一化后写入；缺失或非对象字段应按 `bridge_smoke = false` 处理，确保 Governance Timeline 与 dedupe key 看到的是同一份机器可读状态。
- `runtime_contract_gate_degraded.payload.runtime_contract_summary.sdk_tool_runtime_execution_coverage / embedded_sdk_persistence_coverage / worker_ownership_store_mode_coverage / child_executor_promotion_gate_coverage / child_executor_execution_prerequisites_coverage / child_executor_dispatch_coverage / child_executor_sandbox_backend_binding_coverage / subagent_lane_query_detail_coverage` 必须由后端 trace 入口归一化后写入；缺失、非对象或证据不完整时应按对应 smoke flag 为 `false` 处理，并纳入 fingerprint / dedupe key。
- Runtime Contract Gate degraded trace detail 必须包含 `child_executor_sandbox_binding=<covered|missing|unknown>`，该信号只表示 sandbox backend binding coverage 已进入治理证据，不表示真实 child executor production dispatch 已启用。
- `runtime_contract_gate_degraded.payload.runtime_contract_summary.recovery_retry_evidence_coverage` 必须由后端 trace 入口归一化后写入；缺失、非对象或证据不完整时应按 `retry_smoke = false` 处理，并纳入 fingerprint / dedupe key，确保 recovery retry evidence coverage 变化会形成新的治理信号。
- `runtime_contract_gate_degraded.payload.runtime_contract_summary.recovery_retry_scheduler_coverage` 必须由后端 trace 入口归一化后写入；缺失、非对象或证据不完整时应按 `scheduler_smoke = false` 处理，并纳入 fingerprint / dedupe key。
- `runtime_contract_gate_degraded.payload.runtime_contract_summary.durable_recovery_loader_coverage` 必须由后端 trace 入口归一化后写入；缺失、非对象或证据不完整时应按 `loader_smoke = false` 处理，并纳入 fingerprint / dedupe key。
- `runtime_contract_gate_degraded.payload.runtime_contract_summary.child_executor_dispatcher_coverage` 必须由后端 trace 入口归一化后写入；缺失、非对象或证据不完整时应按 `dispatcher_smoke = false` 处理，并纳入 fingerprint / dedupe key。
- `runtime_contract_gate_degraded.payload.runtime_contract_summary.child_executor_dispatch_result_handoff_coverage` 必须由后端 trace 入口归一化后写入；缺失、非对象或证据不完整时应按 `result_handoff_smoke = false` 处理，并纳入 fingerprint / dedupe key，确保 result handoff coverage 变化会形成新的治理信号。
- `runtime_contract_gate_degraded.payload.runtime_contract_summary.child_executor_dispatch_result_retry_audit_coverage` 必须由后端 trace 入口归一化后写入；缺失、非对象或证据不完整时应按 `retry_audit_smoke = false` 处理，并纳入 fingerprint / dedupe key，确保 retry audit coverage 变化会形成新的治理信号。
- `runtime_contract_gate_degraded.payload.runtime_contract_summary.child_executor_sandbox_backend_coverage` 必须由后端 trace 入口归一化后写入；缺失、非对象或 adapter / execution seam 证据不完整时应按 `sandbox_backend_smoke = false` 处理，并纳入 fingerprint / dedupe key，确保 sandbox adapter gate 或 opt-in execution seam coverage 变化会形成新的治理信号。
- `runtime_contract_gate_degraded.payload.runtime_contract_summary.subagent_lane_query_detail_coverage` 必须由后端 trace 入口归一化后写入；缺失或非对象字段应按 `detail_smoke = false`、计数字段为 `0` 处理，并纳入 fingerprint / dedupe key，确保 subagent detail smoke coverage 变化会形成新的治理信号。
- `runtime_contract_gate_degraded.payload.runtime_contract_artifact_schema` 必须由后端 trace 入口归一化后写入；schema guard 的状态或缺失字段变化必须纳入 fingerprint / dedupe key，确保 quality gate artifact schema 漂移会形成新的治理信号。
- Governance Timeline 的 runtime contract warning 摘要必须展示 `approval_lifecycle=<covered|missing|unknown>`、`approved_tool=<covered|missing|unknown>`、`sdk_tool=<covered|missing|unknown>`、`embedded_persistence=<covered|missing|unknown>`、`worker_ownership=<covered|missing|unknown>`、`child_executor_gate=<covered|missing|unknown>`、`child_executor_prerequisites=<covered|missing|unknown>`、`child_executor_dispatch=<covered|missing|unknown>`、`child_executor_dispatcher=<covered|missing|unknown>`、`subagent_detail=<covered|missing|unknown>`、`recovery_retry=<covered|missing|unknown>`、`recovery_retry_scheduler=<covered|missing|unknown>`、`durable_loader=<covered|missing|unknown>` 与 `checkpoint_cursor=<covered|missing|unknown>`，让排查者不用展开 Payload 也能判断 approval lifecycle recovery、approved tool continuation、SDK direct ToolRuntime bridge、Embedded SDK persistence、worker ownership store mode、child executor promotion gate、child executor execution prerequisites、child executor dispatch boundary、opt-in dispatcher、`subagent_lane_query_detail`、显式 retry evidence、retry scheduler、durable recovery loader 和 checkpoint/resume cursor 是否被 smoke/gate 覆盖。

维护约束：

- 新增 contract 时必须补 `contract_version`。
- 破坏性字段变化必须同步 `runtime_contract_snapshot_service.py`。
- 前端治理台只能消费 contract，不应反向定义后端 contract。

## 2. Runtime Core Contract

主要来源：

- `backend/agent_framework/runtime.py`
- `backend/agent_framework/events.py`
- `backend/services/runtime_core_contract_builder.py::RuntimeCoreContractBuilder`
- `backend/services/runtime_surface_service.py::_build_runtime_core_contract` 兼容 wrapper

核心语义：

- `AgentRunContext` 是执行上下文。
- `AgentState` 是统一状态机。
- `AgentEvent` 是统一事件包络。
- `run_id / parent_run_id / child_run_id / scheduler_run_id` 用于串联主运行、子运行、调度运行和治理回放。
- 当外层消费方只需要稳定子执行展示标识时，应优先消费统一字段 `child_display_id`，而不是自行再写 `child_run_id || child_execution_id`。

### 2.1 Runtime Core 术语收口

当前阶段最容易漂移的不是字段名本身，而是这些字段背后的对象语义。后续新增 contract、治理视图或 adapter 时，应优先沿下面这组定义收口，而不是各处自行发明近义词。这组定义与 `query-run-core-terms-alignment` 保持一致。

#### Query

是什么：

- `query` 是“完成一个用户请求所需的整段运行过程”。
- 它可以跨多个 runtime 事件、多个 tool 调用、多个 approval、多个 subagent/proxy lifecycle。
- 在 Query Control 里，`query_id` 是把这一整段生命周期串起来的治理观察主键。

不是什么：

- 不是单条 message。
- 不是单次 model completion。
- 不是某个 tool call 的局部 id。

#### Run

是什么：

- `run` 是一次具体执行单元的运行实例。
- 它有状态机，有事件流，有 run metadata，有 approval / artifact / trace 依附关系。
- `run_id` 是 Runtime Core 的主执行标识。

不是什么：

- 不是长期 work goal。
- 不是 planner item 本身。
- 不是 query 的全部生命周期，只是 query 生命周期中的一个执行体。

#### Child Run

是什么：

- `child run` 是从 parent run 派生出来的下级执行单元。
- 它保留执行级关系，重点表达“谁派生了谁”，而不是团队组织关系。
- 在 SDK / subagent / scheduler fan-out 里，它是对 delegated execution 的统一抽象。

不是什么：

- 不是长期 teammate。
- 不是 scheduler group 的别名。
- 不是普通 message thread。

#### Scheduler Run

是什么：

- `scheduler run` 是调度层围绕某个 plan item 组织 fan-out / fan-in 执行时的主运行标识。
- `scheduler_run_id` 用于把 child execution、merge、approval、trace 回放关联到同一调度上下文。

不是什么：

- 不是 child run。
- 不是 query 的通用 id。
- 不是 planner plan 的持久主键。

#### Approval

是什么：

- `approval` 是正式可回放的权限/治理决策对象。
- 它至少应回答：谁请求、请求什么、当前状态、何时处理、处理结果。
- `approval_request_id` 是治理与恢复执行之间的稳定桥接点。
- 当审批对象绑定到某个 child run 时，也应稳定保留 `child_run_id / child_display_id`，避免审批卡、治理时间线和恢复入口各自重建子执行身份。

不是什么：

- 不是一条临时 warning 文案。
- 不是 tool policy 的内部布尔值。
- 不是前端按钮状态。

#### Artifact

是什么：

- `artifact` 是运行过程产出的可引用结果对象。
- 它可以是 reasoning trace、structured card、持久化文件引用、治理快照等。
- 它强调“可引用、可回放、可挂接”，而不强调具体展示方式。
- `snapshot_ref` 是 artifact 或事件的引用包装，不是 artifact 本体。

不是什么：

- 不是普通 response text 的别名。
- 不是所有 payload 都自动算 artifact。

#### Trace

是什么：

- `trace` 是面向运行回放的时间序列事件。
- 它描述发生了什么、在哪个 runtime scope 下发生、为何重要。
- 它偏执行观察面，是 run/query 生命周期的第一层证据。

不是什么：

- 不是 audit 的同义词。
- 不是 summary card。
- 不是数据库 ORM 行直接透出。

#### Audit

是什么：

- `audit` 是面向治理/合规/变更记录的事件流。
- 它重点记录“什么动作被正式记账”，而不是所有运行细节。
- 它偏治理记账面，通常比 trace 更少、更稳定、更强调可解释性。

不是什么：

- 不是原始 trace 的完整复制。
- 不是纯 UI 提示。

#### Durable State vs Runtime State

是什么：

- durable state：跨进程、跨刷新、跨会话仍有意义的状态，例如 plan、approval record、persisted trace、contract snapshot。
- runtime state：只在当前执行窗口内有效的状态，例如 in-memory continuation、当前 active stream、pending tool execution descriptor。

不是什么：

- 不是“数据库里的都算 durable、内存里的都算 runtime”这么粗糙。
- 判断标准应是“离开当前执行上下文后，这个状态是否仍应被系统正式理解和消费”。

#### Control Plane vs Execution Plane

是什么：

- control plane：负责决定如何执行，例如 lifecycle stage、policy、approval、query channel、route filter、governance read model。
- execution plane：负责真正做事，例如 model generation、tool execution、adapter stream、subagent run、scheduler merge。

不是什么：

- control plane 不是所有 metadata 的垃圾桶。
- execution plane 也不应直接承载治理解释逻辑。

### 2.2 术语到字段/展示对照

下表不是完整字段清单，而是当前最容易漂移、且最值得统一的核心对象对照。后续如果新增字段或视图，应优先判断它属于哪一行，而不是先发明新名词。

| 术语 | 当前后端 contract / 字段 | 当前前端主要展示位置 | 当前判断 |
|---|---|---|---|
| `query` | `query_control` payload 中的 `query_id`；`main_chat_trace_overview.latest_query_id`；`main_chat_trace_overview.recent_queries[*].query_id`；`main_chat_query_detail.query_id`；`main_chat_query_detail.read_model_layer`；`main_chat_query_detail.source_channel`；`main_chat_query_detail.identity_kind` | `RuntimeSurfacePanel` 的 `Main Chat Trace`、`Recent Queries`、`Query Detail Contract`；`GovernanceTimelinePanel` 的 `Query 聚焦 / Query 摘要 / Query Detail` | 主语义已收口为“用户请求生命周期”，且 query detail 现在已显式自描述其 read model 层级与来源通道，仍需防止把 `run_id` 当成 `query_id` 的替代品 |
| `run` | `runtime_core.run_id`；`governance_overview.run.run_id`；trace scope 中的 `run_id` | `RuntimeSurfacePanel` 的 `Runtime Core 合同 / 治理总览合同`；`GovernanceTimelinePanel` 的当前 Run 卡 | 主执行实例语义已基本稳定，但前端仍偶尔用“当前 Run / 调度 Run”混称 |
| `child run` | `runtime_core.child_run_id`；trace scope 中的 `child_run_id`；scheduler child execution payload 中的 `child_run_id / child_execution_id`；展示消费面的 `child_display_id` | `RuntimeSurfacePanel` 的 `Runtime Core 合同`；`GovernanceTimelinePanel` 当前 Run 与 trace payload | 主执行语义以 `child_run_id` 为准；如消费方只需要稳定展示标识，应优先读取 `child_display_id`，不要继续在外层重写 fallback |
| `scheduler run` | `runtime_core.scheduler_run_id`；`governance_overview.run.scheduler_run_id`；scheduler trace scope 中的 `scheduler_run_id` | `RuntimeSurfacePanel` 的 `Runtime Core 合同 / 治理总览合同`；`GovernanceTimelinePanel` 当前 Run 卡 | 已稳定表达调度主运行，但仍需避免在普通 `main_chat` 语境里误当作 query 主键 |
| `approval` | `approval_request_id`；`governance_overview.approval.latest_request`；SDK `approval_created / approval_resolved / approval_replayed / approval_ignored.required_payload` | `RuntimeSurfacePanel` 的治理总览审批卡；`GovernanceTimelinePanel` 的待处理审批卡与 permission 域 timeline | 主语义稳定，是正式治理决策对象，不建议再用临时 status 替代 |
| `artifact` | SDK `create_artifact / list_artifacts`；run metadata artifact 引用；治理快照 `snapshot_ref` | `RuntimeSurfacePanel` 的 snapshot_id / recent snapshot command；`GovernanceTimelinePanel` 的引用快照与复制命令 | 仍偏散，`artifact` 与 `snapshot_ref` 关系需要后续进一步明确 |
| `trace` | `run_trace`；`latest_trace_event`；`query_control_*` trace events | `RuntimeSurfacePanel` 的 `latest_trace_event`、`main_chat_trace_overview`；`GovernanceTimelinePanel` 主列表 | 作为执行证据流已稳定，但前端列表里仍会混 trace 与 audit 结果，需要靠 domain/label 区分 |
| `audit` | `audit_trail`；`governance_overview.audit.latest_event`；`query_control_*` audit events | `RuntimeSurfacePanel` 的治理总览审计卡；`GovernanceTimelinePanel` 主列表 | 主语义稳定，但“trace 与 audit 是否并列或复制”仍应持续约束 |
| `durable state` | `plan`、`approval record`、persisted trace、contract snapshot、runtime surface profile contract | `RuntimeSurfacePanel`、`GovernanceTimelinePanel`、`PlannerPanel` | 仍需要在文档里反复强调，不然容易把临时前端 state 当成 durable 事实 |
| `runtime state` | in-memory continuation、active stream、临时 execution_context、前端当前 filter/query focus | `ChatView`、`GovernanceTimelinePanel` route state、SDK metadata descriptor | 仍是高漂移区，尤其前端 route/query state 容易被误认为后端持久事实 |

当前最值得继续收口的漂移点：

- `query_id` 与 `run_id` 在 `main_chat` 语境下仍容易被混用。
- `child_run_id` 与 `child_execution_id` 当前仍是双名并存。
- `artifact` 与 `snapshot_ref` 的关系还没有形成单一正式表述。
- 前端 route state 的 `governance_query_id / governance_dedupe_key / governance_snapshot` 仍需持续提醒：它们是观察焦点，不是 durable runtime 对象。

### 2.3 漂移点优先级判断

当前不建议把所有漂移点并行处理。按“收益 / 风险 / 改动面 / 后续影响面”综合判断，建议优先级固定为：

#### P1：`child_run_id` vs `child_execution_id`

为什么最高：

- 这是当前最明确的“双名并存”问题，而且已经横跨数据库、scheduler runtime、chat service、前端展示和测试。
- 它不是纯文案问题，而是同一对象在不同层被两套名字同时承载。
- 如果继续拖着不收口，后续 `run / child run / scheduler run` 的对象模型会持续混乱。

当前事实：

- 数据模型层两者同时存在：
  - `backend/models.py`
  - `backend/services/scheduler_runtime_entities.py`
  - `backend/services/scheduler_runtime_sql_repository.py`
- 运行时/展示层也同时消费两者：
  - `backend/services/scheduler_service.py`
  - `backend/services/chat_service.py`
  - `frontend-vue/src/components/PlannerPanel.vue`
  - `frontend-vue/src/components/RuntimeSurfacePanel.vue`

建议策略：

- 先明确谁是一等术语、谁是兼容字段。
- 当前更适合把 `child_run_id` 作为 Runtime Core 正式术语，把 `child_execution_id` 视为 scheduler/runtime repository 兼容层或实现细节。

### 2.4 `child_run_id` 最小收口方案

这一节不是立刻要求改代码，而是先把后续收口决策补成一份“不会反复摇摆”的最小方案。

#### 当前判断

- `child_run_id` 应作为 Runtime Core 正式术语。
- `child_execution_id` 应视为 scheduler fan-out / runtime repository / 持久化兼容层的实现键。
- `child_display_id` 应作为外层展示、治理摘要和跨消费面复制链路的统一稳定字段；默认优先等于 `child_run_id`，必要时才回退 `child_execution_id`。

#### 为什么这样定

- 数据模型中 `child_run_id` 已经是唯一索引、显式命名为 run：
  - `backend/models.py::ChildRunRecord.child_run_id`
- `child_execution_id` 当前更多承担“某次 scheduler 拆分出来的执行槽位标识”角色：
  - `backend/models.py::ChildRunRecord.child_execution_id`
  - `backend/services/scheduler_runtime_entities.py::ChildRunState.child_execution_id`
- 前端治理和运行时 contract 语义更接近 `child run`，而不是 `child execution slot`：
  - `frontend-vue/src/components/RuntimeSurfacePanel.vue`
  - `frontend-vue/src/components/GovernanceTimelinePanel.vue`

#### 规范化规则

**正式术语层：**

- 在架构文档、runtime contract、治理面板、Runtime Surface、query/read model 中，统一使用 `child_run_id`。

**兼容/实现层：**

- 在 scheduler runtime repository、数据库唯一约束、历史 metadata、fan-out child 列表里，允许继续保留 `child_execution_id`。
- 但它应被解释为“child run 的调度执行槽位键”，而不是与 `child_run_id` 平级的一等运行时对象名。

#### 字段使用规则

- 当一个字段表示“运行时执行对象身份”时，优先用 `child_run_id`。
- 当一个字段表示“scheduler 内部拆分槽位/兼容历史持久化键”时，保留 `child_execution_id`。
- 新增 API、contract、前端展示字段时，不再新增第三套近义词。

#### 建议的后续代码收口顺序

1. 文档与 contract 文案统一：
   - 先把前后端文档、Runtime Surface 文案、治理面板提示统一成 `child run`。
2. 后端 contract 输出统一：
   - 在外发 contract 中把 `child_run_id` 作为主字段。
   - `child_execution_id` 如需保留，降级为兼容字段或 metadata。
   - 如调用方只需要稳定展示标识，优先提供单一字段（例如 `child_display_id`），避免继续在外层重复写优先级判断。
   - `child_display_id` 当前已进入 runtime surface、scheduler child execution、subagent/query-control 事件、framework adapter timeline、approval request 与 server serialization；新增 contract 时不应再遗漏这条统一键。
3. scheduler/runtime repository 内部兼容保留：
   - 不急着删库字段，不做破坏性迁移。
4. 最后再评估数据库迁移：
   - 只有当外层 contract 和前端展示都稳定后，再考虑是否弱化或淘汰 `child_execution_id`。

#### 当前不建议做的事

- 不建议立刻删除数据库里的 `child_execution_id`。
- 不建议当前阶段同时重构 scheduler/runtime store/前端所有消费点。
- 不建议在 contract 还没统一前先做字段迁移。

#### 这一步完成的标准

- 后续讨论里，提到运行时子执行对象时默认说 `child run`，不再说“child execution”。
- 新增 contract / UI / read model 时，默认主字段是 `child_run_id`。
- `child_execution_id` 被明确约束在兼容层和实现层，而不是继续向外扩散。
- 外层展示若只需要一个稳定 id，应优先消费统一字段，而不是自己再写 `child_run_id || child_execution_id`。
- 当前 `child_display_id` 已被视为正式 display field，而不是前端临时派生字段；如果某条 contract 仍缺它，应视为收口缺口，而不是消费层自行兜底。

#### P2：`query_id` vs `run_id`

为什么第二：

- 它的影响面也很大，但这里并不是简单重名，而是两个对象本来就语义不同。
- 当前文档和 contract 已经开始区分，只是 `main_chat` 语境下仍容易被误读。
- 所以它更像“需要继续明确边界”的问题，而不是“同一对象双名并存”的问题。

当前事实：

- `query_id` 已主要收口在 Query Control / `main_chat` 观察面：
  - `query_control` payload
  - `main_chat_trace_overview`
  - `main_chat_query_detail`
  - `governance_query_id`
- `run_id` 仍主要属于 Runtime Core 执行体：
  - `runtime_core.run_id`
  - `governance_overview.run.run_id`
  - scheduler / approval / adapter runtime scope

建议策略：

- 先通过文档、contract、前端文案继续压实“query 是生命周期、run 是执行实例”的边界。
- 在真正需要 query-level 专用接口之前，不建议急着大改底层字段。

### 2.5 `query_id` 最小收口方案

这一节的目标不是让 `query_id` 与 `run_id` 互相替代，而是防止它们在外层 contract、文案和治理视图里被误当成同一个东西。

#### 当前判断

- `query_id` 应作为 Query Control / 治理观察生命周期主键。
- `run_id` 应继续作为 Runtime Core 执行实例主键。

#### 为什么这样定

- `query_id` 当前主要服务于 `main_chat` / Query Control 观察面：
  - `query_control` payload
  - `main_chat_trace_overview.latest_query_id`
  - `main_chat_trace_overview.recent_queries[*].query_id`
  - `main_chat_query_detail.query_id`
  - `governance_query_id`
- `run_id` 当前主要服务于执行实例与运行时作用域：
  - `runtime_core.run_id`
  - `governance_overview.run.run_id`
  - scheduler / approval / adapter runtime scope

#### 规范化规则

**正式术语层：**

- 当讨论“一个用户请求从输入到最终结果的完整治理观察生命周期”时，用 `query / query_id`。
- 当讨论“一个具体执行实例、状态机、tool/approval/adapter 运行实体”时，用 `run / run_id`。

**展示层：**

- Runtime Surface 中：
  - `Runtime Core 合同`
  - `治理总览合同 / 治理 Run`
  - `当前 Run`
  默认属于 `run` 视角。
- Runtime Surface / Governance Timeline 中：
  - `Main Chat Trace`
  - `Recent Queries`
  - `Query Detail Contract`
  - `Query 聚焦 / Query 摘要 / Query Detail`
  默认属于 `query` 视角。

**兼容/实现层：**

- 允许某些内部 helper 暂时从 `run_id / scheduler_run_id / child_run_id` fallback 生成 `query_id`，但这属于实现兜底，不应反向定义术语。
- 如果外层 contract 已显式给出 `query_id`，前端和文案不应再把它叫成 `run`。

#### 当前最值得先收口的点

- `backend/services/chat_service.py::_record_main_chat_query_control_event(...)`
  - 当前 `query_id` 仍通过 `run_id / scheduler_run_id / child_run_id` fallback 取值，应在文档中明确这是实现兜底。
- `frontend-vue/src/components/RuntimeSurfacePanel.vue`
  - `Runtime Core` 与 `Main Chat Trace` 已分区，但外层文案仍需要持续避免 `Run / Query` 混称。
- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
  - 当前 `当前 Run` 与 `Query 聚焦 / Query Detail` 两套视角已经存在，应继续保持命名边界，不再回退成模糊表述。

#### 当前不建议做的事

- 不建议把所有 `query_id` 强行改成与 `run_id` 一一绑定。
- 不建议把 Query Control 的 query 语义退化成 run 语义。
- 不建议在正式 query 级接口还没成形前，先做大规模底层字段重构。

#### 这一步完成的标准

- 后续讨论里，提到治理观察主键时默认说 `query_id`，提到执行实例时默认说 `run_id`。
- Runtime Surface 与 Governance Timeline 的外层文案不再把 `Run` 与 `Query` 混称。
- query 级 read model 不再继续依赖 `run_id` 作为外显主标识。

### 2.6 Query Workspace 通用化边界

当前在高层设计上，应把 query 能力分成四层，而不是把所有治理浏览能力混成同一个概念：

1. `recent summary`
2. `query detail`
3. `query history`
4. `query workspace`

当前正式判断：

- `main_chat` 是唯一完整实现了四层能力的 channel，应作为当前 canonical baseline。
- `subagent_lane` 已具备 recent summary 与 dedicated query detail evidence，但仍不得默认推进到 `query history / query workspace`。
- `external_adapter` 已具备 `external_adapter_recent_summary` 轻量 evidence；在 dedicated detail readiness 另行立项前，不得推进到 `query detail / query history / query workspace`。
- 在 promotion record 显式允许前，非 `main_chat` channel 都不应进入：
  - `query detail`
  - `query history`
  - `query workspace`

维护约束：

- Query 能力推广必须按层推进，不能直接复制某个 channel 的产品壳。
- `recent summary` 是多 channel 最先允许推广的层；`query history / query workspace` 默认应最后评估。
- 如果某个 channel 还需要前端从通用 timeline 本地重建 query 模型，就说明它还不具备进入更深层 query 能力的资格。
- 恢复任何 channel 级实现前，必须先有 promotion record：至少记录 `channel / current_layer / target_layer / readiness_evidence / blockers / decision / next_allowed_action / non_goals`。
- 当前 promotion decisions：
  - `main_chat`: `query_workspace` baseline；后续工作必须证明是在做边界澄清或明确价值增强，而不是默认继续深挖局部体验。
  - `subagent_lane`: 允许停在已记录的 detail 能力；history/workspace 必须另开 promotion decision，且不得复制 `main_chat` 壳。
  - `external_adapter`: 允许停在已记录的 `recent_summary` 能力；detail/history/workspace 必须另开 promotion decision，且不得复制 `main_chat` 或 `subagent_lane` 的更深层壳。
- `recent summary` 当前继续保持 channel-specific builder，但共享字段口径固定为 `query_id / latest_stage / latest_summary / latest_timestamp / recording_state`；`latest_snapshot_id / last_success_stage / last_warning_stage` 只作为可选字段，不要求提前抽通用 assembler。
- Phase I 的完成线是 promotion boundary 收束，不是所有 channel 达到 workspace parity；当前默认下一阶段进入 Phase II runtime-core implementation / delivery-surface slimming，新的 channel 深层能力必须通过 future reopen decision。
- 当前若讨论“哪些能力能从 `main_chat` 提升为通用模式”，优先以 `openspec/specs/query-workspace-generalization/spec.md` 为真源，而不是重新从局部 UI 或 change log 推断。

#### P3：`artifact` vs `snapshot_ref`

为什么放第三：

- 当前它的歧义主要集中在治理快照、artifact store、tool artifact 三条线之间的概念关系。
- 但相比前两个，它还没有形成高频的双名混用或明显执行风险。
- 更适合在 Runtime Core / Query Read Model 再稳一点后，作为能力层与交付层的接口清理再收口。

当前事实：

- `artifact` 主要落在 SDK / Harness / ArtifactStore / tool result envelope
- `snapshot_ref` 主要落在治理 timeline / doctor / query control / external adapter 回放

建议策略：

- 先保持两者并存，但明确：`snapshot_ref` 偏治理引用；`artifact` 偏运行产物引用。
- 等 query/run 术语稳定后，再评估是否需要统一成更高层的 reference model。

状态机当前包含：

- `init`
- `planning`
- `generating`
- `tool_calling`
- `waiting_approval`
- `waiting_permission`
- `observing`
- `merging`
- `finalizing`
- `done`
- `failed`
- `aborted`

维护约束：

- 状态迁移必须通过 `AgentRunContext.transition_to()`。
- 新状态必须补合法迁移表和测试。
- 事件输出必须保留 `payload`，同时兼容扁平字段。

## 3. Governance Overview Contract

主要来源：

- `backend/services/runtime_surface_service.py::_build_governance_overview_contract`
- `backend/services/approval_engine_service.py`
- `backend/services/policy_engine_service.py`
- `backend/services/run_trace_service.py`

当前覆盖：

- run 概览
- approval 概览
- audit 概览
- 审批对象当前也应保持最小 runtime scope 身份字段一致性：至少包括 `run_id / parent_run_id / child_run_id / child_display_id / scheduler_run_id`。

维护约束：

- approval、audit、trace 只应该暴露摘要或引用，不应把内部数据库对象直接透出。
- 新增治理事件时应能被 Governance Timeline 回放。
- 当 approval、trace、adapter timeline 或 server serialization 需要暴露 child 身份时，优先直接透出 `child_display_id`，不要把 fallback 逻辑下放给前端或审计消费者。

## 4. Tool Runtime Contract

主要来源：

- `backend/services/tool_runtime_service.py`

当前字段类别：

- 工具总量
- base tool 数量
- LangChain tool 数量
- ToolSpec 数量
- MCP capability 数量
- 高风险工具数量
- tool registry 状态
- MCP registry 状态
- tools 列表
- mcp capabilities 列表

维护约束：

- 工具风险等级应在后端归一化，前端只展示。
- 新工具需要明确 permission level、risk level、schema 状态。

## 5. Adapter Health Contract

主要来源：

- `backend/services/tool_runtime_service.py::build_adapter_health_contract`
- `backend/agent_framework/framework_adapter_spi/registry.py`
- `backend/services/framework_adapter_diagnostics_service.py`

当前覆盖：

- internal tool registry
- MCP runtime
- external framework adapters
- latest external pilot failure
- external pilot failure counts

关键统计字段：

- `window_scope`
- `sample_size`
- `by_error_type`

维护约束：

- health API、doctor CLI、Runtime Surface 必须使用同一套诊断 seam。
- 失败统计必须说明窗口，不允许展示成全量历史。
- adapter readiness 与 runtime execution gate 必须分开表达。

## 6. Framework Adapter Runtime Contract

主要来源：

- `backend/agent_framework/framework_adapter_spi/base.py`
- `backend/agent_framework/framework_adapter_spi/health.py`
- `backend/agent_framework/framework_adapter_spi/registry.py`
- `backend/services/framework_adapter_runtime_service.py`
- `backend/services/framework_adapter_external_pilot_service.py`

核心接口：

- `health_check()`
- `can_execute()`
- `translate_input()`
- `stream_events()`
- `translate_output()`
- `FrameworkAdapterRuntimeService.build_adapter_authoring_checklist(...)`

当前 adapter：

- `NoopFrameworkAdapter`
- `LocalFakeFrameworkAdapter`
- `LangGraphDraftAdapter`

维护约束：

- `framework_adapters.py` 是 public facade，不应删除。
- 新外部框架优先新增 adapter，不要把逻辑写进 Runtime Surface。
- external pilot 只能走受控 pilot 路径，不应直接进入主 chat 路径。
- `build_adapter_authoring_checklist(...)` 当前是 side-effect-free authoring / promotion review contract：它读取 adapter registry 与 precheck evidence，返回 identity、lifecycle mapping、readiness checks、governance timeline、promotion gate、non-goals 与 conservative `promotion_review`。该 checklist 不执行 adapter、不调用外部 framework、不写 trace/audit、不注册 tool、不启动 worker，且 `default_chat_entry` 必须保持 `disabled`。

## 7. Embedded SDK Contract

主要来源：

- `backend/agent_framework/sdk.py`
- `backend/services/command_registry_service.py`

当前状态：

- `build_embedded_sdk_contract()` 已作为 contract 暴露。
- `create_run`、`stream_events`、`submit_approval`、`resume_run`、`delegate_run`、`create_artifact`、`list_artifacts`、`execute_run`、`register_tool` 已进入 preview。
- `register_tool` 现在是 SDK 到 `ToolRuntimeService` 的薄桥接：SDK 不创建第二套工具运行时，只把 `ToolSpec` 元数据和可选 executable handler 注册进配置的 tool runtime registry。
- `execute_run` 在未显式传入 `tool_executor` 且提供了 `tool_policy` 时，可默认使用 `ToolRuntimeService` 执行已注册工具；`ask / high_risk / deny` 权限仍先通过 SDK policy decision 进入 approval / fail-closed 生命周期。
- `event_status_kinds` 已暴露 SDK 预览事件面，包含 run、approval、execution_loop、tool、continuation 等核心 status_kind 与关键 `required_payload`。
- reviewer / fallback 事件已进入 `event_status_kinds.required_payload` 守护：`execution_loop_reviewed` 与 `execution_loop_review_rejected` 必须携带 `review / loop_step`，`execution_loop_fallback_applied` 与 `execution_loop_failed` 必须携带 `fallback / error / loop_step`。
- contract 还会显式暴露 `volatile_runtime_state`、`persistence_seams`、`recovery_entrypoints` 与 `delegate_preflight`，把 Phase II 的恢复边界和 child executor 前置判断收口成代码真源。

当前方法：

- `create_run`：创建内存态 `AgentRunContext`，写入 `run_created` 事件。
- `stream_events`：读取 SDK 内存态 run 的事件流。
- `submit_approval`：处理 SDK 创建的 approval request，并写入 `approval_resolved` 与状态迁移事件；显式传入 `approved` 且 tool continuation descriptor 可恢复时，会继续消费 approved tool continuation。已 resolved 的 approval 不允许反向改写：同决策重放返回 `approval_submission.status = replayed`，反向提交返回 `approval_submission.status = ignored`，并分别写入 `approval_replayed / approval_ignored`。
- `ApprovalEngineService.submit_approval_decision(...)` 是 approval 生命周期状态机的服务层入口；SDK 可以编排 continuation 与事件，但不应重新实现 `pending / accepted / replayed / ignored` 的判定规则。
- `resume_run`：默认仅允许从 `observing` 恢复到下一次 `generating` iteration，并写入 `run_resumed` 与状态迁移事件；显式传入 `continue_loop=True` 时，会从 `observing` 接回后续 `observing -> finalizing -> done` loop continuation。
- `recovery_entrypoints`：除 `cross_process_ready` 之外，还会显式标注 `requires_durable_workspace` 与 `requires_registry_bindings`。当前 `submit_approval + approved` 与 `resume_run + continue_loop` 都进入条件式跨进程恢复成熟度，也就是仅当 workspace backend durable 且 continuation binding 可由 registry 解析时，才允许把 persisted descriptor 重挂为 executable continuation。
- `delegate_run`：在已存在的 parent run 下创建 child run，并在父事件流写入 `child_run_created`；同时返回并持久化 `child_executor_preflight`，明确当前仍只是 relationship seam。
- `child_executor_preflight`：独立 child executor preflight contract，用于表达 promotion readiness、binding blockers、next step、workspace backend 状态与 gate 结果。
- `child_executor_promotion_gate`：独立 child executor promotion gate contract，用于表达最终是否允许从 relationship seam 升格为真实 child executor；前端与治理台应直接消费该决策，不重算 allow/deny。
- `child_executor_execution_prerequisites`：嵌套在 promotion gate 下的 execution readiness contract，用于表达真实 child executor 启动前的 binding、context budget、merge contract、worker backend、recovery boundary 与 gate allowed 前置条件。它只做 side-effect-free 判断，不创建 child run、不启动 executor。
- `child_executor_backend_registry`：side-effect-free backend capability registry，用于区分“backend id 已知”与“backend dispatch ready”。新增 executor backend 时应先进入该 registry，再由 preflight/prerequisites 消费其 compact evidence。
- `child_executor_dispatch_contract`：side-effect-free dispatch boundary，用于表达当前是否具备真实 child executor dispatch 条件。它不会启动 executor；即使 opt-in sandbox dispatch contract 已 ready，`will_dispatch` 仍为 `false`，并嵌套 `child_executor_dispatch_attempt_handoff` 来说明 sandbox attempt envelope validation、unsafe payload guard、audit/idempotency handoff 证据。真实 dispatcher 必须作为后续显式 opt-in boundary 接入；dispatcher 返回的 `dispatch_result_handoff` 则描述 adapter result 的 compact audit handoff，不代表 parent merge 或 retry execution。
- `create_artifact`：为 run 创建 artifact 引用，写入 run metadata，并在 run 事件流写入 `artifact_created`；如 SDK 注入 `ArtifactStore`，则优先通过 store 创建 artifact。
- `list_artifacts`：按 run 回放已关联 artifact，优先用 SDK artifact index 补全详情。
- `execute_run`：通过 `ExecutionLoopController` 驱动 run 进入最小 harness loop，并把状态事件追加到 SDK 事件流；可选接收 tool policy、tool executor、reflector、reviewer、fallback handler callable，作为 permission、act、observing 后反思、finalizing 质量门禁与降级 seam。若没有传入 `tool_executor`，SDK 会使用 ToolRuntimeService 作为默认 tool executor bridge，并在执行前复用 ToolRuntimeService policy probe，把 `ask / high_risk` 映射为 approval request、把 `deny` 映射为 `tool_policy_denied`。
- `register_tool`：注册 `ToolSpec` 元数据；当传入 handler 时，会把 handler 包装成 ToolRuntimeService 可执行的 registry tool。返回值包含 `tool_registry_bridge`、`handler_registered` 与 compact `runtime_contract`，用于治理和 smoke 读取。
- `runtime_dependencies / runtime_factory`：默认 embedded runtime 的依赖与构造入口。`workspace_store / continuation_registry` 已开始通过 `EmbeddedRuntimeDependencies / EmbeddedRuntimeFactory` 统一注入，避免 SDK、Facade、Runtime Surface 各自拼默认 runtime。

当前易失状态边界：

- `_runs`
- `_events`
- `_approvals`
- `_artifacts`
- `_tool_continuations`
- `_loop_continuations`

这些状态当前都仍是 in-process memory runtime 的一部分，不应被误解为 durable storage。

Phase II 当前推荐先抽出的持久化 / 恢复 seam：

- run workspace persistence boundary
- tool approval continuation descriptor boundary
- loop continuation descriptor boundary
- artifact persistence boundary（继续优先复用 `ArtifactStore`）

当前恢复边界判断：

- `resume_run(...)` 当前只在内存态 `run_context` 与 continuation descriptor 仍可用时成立。
- `submit_approval(..., "approved")` 当前可以消费 approved tool continuation；`resume_run(..., continue_loop=True)` 当前可以消费 `loop_continuation` 接回 `observing -> finalizing -> done`。两者都已经进入条件式跨进程恢复边界，但仍显式依赖 durable workspace 与可解析的 registry binding。
- `delegate_run(...)` 当前只创建 child run 与事件关系，不代表已经进入真实 child executor。

Phase II 当前前置判断：

- 只有当 continuation descriptor 已进入稳定 persistence seam，才允许把 `submit_approval(..., "approved")` 与 `resume_run(..., continue_loop=True)` 进一步讨论为跨进程恢复入口。
- 只有当 child run 的恢复边界、上下文预算和结果 merge 语义已明确，才允许把 `delegate_run(...)` 提升为真实 child executor 起点。
- 在上述前置条件满足前，`submit_approval(..., "approved")` 与 `resume_run(..., continue_loop=True)` 都应按 fail-closed recovery seam 理解，只有满足 durable workspace 与 registry binding 条件时才允许跨进程重挂 executable continuation；`delegate_run(...)` 仍应被理解为 object relationship seam。
- `delegate_preflight` 默认仍以 `relationship_only` 输出，但现在已开始按 payload/metadata 实际评估 `child_context_budget_defined / child_result_merge_semantics_defined / worker_runtime_backend_selected`；当 promotion requirements 全部满足时，可升级为 `promotion_candidate`，但这仍不代表真实 child executor 已落地。
- `child_executor_preflight` 已从附属边界信息升级为独立 read model，并同时挂在 `runtime_profile` 与 `governance_overview.child_executor_preflight`；前端与治理台应直接读取该 contract，而不是继续从多个 helper 反推 promotion readiness。
- `child_executor_promotion_gate` 当前已作为独立 backend truth source 挂在 `runtime_profile` 与 `governance_overview.child_executor_promotion_gate`；它负责收口最终 `allowed / blocked`、`failure_reason / blockers / executor_path / recommended_next_step`，不由前端、Facade 或 call site 自行重建。
- `child_executor_execution_prerequisites` 当前已作为 promotion gate 的嵌套证据进入 `runtime_profile.child_executor_promotion_gate` 与 `governance_overview.child_executor_promotion_gate`；它负责回答“真实 executor 启动前还缺什么”，不代表 executor 已经启动。
- `child_executor_backend_registry` 当前已暴露在 `build_embedded_sdk_contract()`、`runtime_profile.child_executor_backend_registry` 与 `embedded_runtime_boundaries.child_executor_backend_registry`；preflight 的 `worker_runtime_backend_selected` 现在通过 registry lookup 记录 known/unknown evidence，execution prerequisites 再用 `dispatch_ready` 形成 `worker_backend_dispatch_ready` blocker。
- `child_executor_dispatch_contract` 当前已暴露在 `build_embedded_sdk_contract()`、`runtime_profile.child_executor_dispatch_contract`、`embedded_runtime_boundaries.child_executor_dispatch_contract` 与 `governance_overview.child_executor_dispatch_contract`；它把 gate/prerequisites/backend registry 的结论收成最终 dispatch boundary，并暴露 `child_executor_dispatch_attempt_handoff`，默认阻断真实 dispatch。
- `run_recovery` 当前也已进入 dedicated runtime surface read model；它复用 `probe_run_recovery(run_id)` 的 machine-readable recovery 结果，统一返回 `recoverable / approval_request / tool_continuation / loop_continuation / recovery_capabilities / recovery_entrypoints / workspace_backend / reason`，供治理台、排障链和后续恢复实现共用。
- `run_recovery.recovery_capabilities` 是恢复摘要层，当前至少表达 `recovery_mode`（如 `unavailable / in_process / registry_backed`）以及 `requires_durable_workspace / requires_registry_bindings`，外层消费方应优先读取这层摘要，而不是每次都从 tool/loop continuation 明细自行归纳恢复能力。
- 默认 SDK、默认 facade 与 Runtime Surface 当前已开始共享同一默认 runtime factory；后续若要提升默认可恢复 runtime 的成熟度，应优先沿 `runtime_dependencies / runtime_factory` 调整，而不是分别修改三处默认构造。
- `embedded_runtime_factory` 当前也已进入 command runtime contract；它是“默认 runtime 是什么”的后端真源，至少会表达 `default_runtime_profile / default_recovery_capabilities / workspace_backend / continuation_registry / recovery_capabilities / factory_methods`，供垂域项目和排障链路直接读取。
- `embedded_runtime_factory.default_recovery_capabilities` 是默认恢复能力概览层，当前与 `run_recovery.recovery_capabilities`、`bootstrap_recovery_validation.recovery_capabilities` 共享同一套摘要语义，调用方应优先用它判断默认 runtime 更接近 `registry_backed` 还是 `unavailable`，再决定是否继续下钻 validation 或单 run 明细。
- `embedded_runtime_factory` 现也已进入 `runtime_profile` 主画像；后续如果要判断“默认 runtime 是否更偏 demo 还是更偏 durable/recoverable”，应优先读取这份 contract，而不是分别查看环境变量、workspace backend 和零散 helper。
- `runtime_profile` 顶层当前还提供 `default_runtime_recovery` 轻量摘要层，用于把 `default_recovery_capabilities / default_recovery_expectation / default_runtime_profile.recovery_posture` 收口成一个更直接的默认恢复 posture 真源。它不会触发真实 bootstrap validation，只负责主画像级默认恢复概览；当前还会提供 `recovery_entrypoints`，表达默认 runtime 对 `submit_approval + approved / resume_run + default / resume_run + continue_loop` 这些入口的能力预期。
- `governance_overview.default_runtime_recovery` 是上述默认恢复摘要在治理总览里的只读投影，便于治理面直接并排展示默认恢复预期，不必回到 profile 顶层二次取值。
- `governance_overview` 当前还会提供 `recovery_alignment_summary`，把 `default_runtime_recovery.recovery_entrypoints` 与 `run_recovery.recovery_entrypoints` 收口成 expected vs current 的统一对比摘要，供治理面直接读取一致性结果，而不是逐项手工比较入口。
- `default_runtime_profile` 当前不仅给出结果值，也会给出来源与策略字段，例如 `db_mode_source / embedded_workspace_store_mode_source / workspace_strategy_rule / durable_by_default / recommended_bootstrap`，用于解释“为什么默认运行时是当前模式”。 
- `default_runtime_profile` 现也会声明 `configurable_bootstrap_knobs`，用于明确哪些 runtime bootstrap 开关是当前允许的正式配置输入，而不是让调用方自行猜测或依赖未声明环境变量。
- `default_runtime_profile` 当前还会显式声明 `hot_reloadable_bootstrap_knobs / restart_required_bootstrap_knobs`，用于区分哪些 bootstrap 变更支持当前进程热切换，哪些仍应被视为需要重新启动 runtime。
- `embedded_runtime_bootstrap` 当前已作为 dedicated runtime surface contract 与 `/api/runtime-profile/embedded-runtime-bootstrap` 接口存在；新增默认运行时消费方时，应优先读取这份 contract，而不是直接耦合 command contract 或 service 内部 factory helper。
- `embedded_runtime_bootstrap` 现也已有 dedicated 更新入口 `/api/runtime-profile/embedded-runtime-bootstrap`（PATCH）；当前仅允许通过该入口正式更新 `embedded_workspace_store_mode`，并在当前进程里重新同步默认 workspace/runtime factory。
- `embedded_runtime_bootstrap` 的 dedicated 更新结果当前还会返回 `post_update_verification`，用于明确这次热切换前后的 `default_runtime_mode / recovery_posture / workspace_backend_kind` 是否真的发生变化，避免调用方只能手工比对合同字段。
- `embedded_runtime_bootstrap` 当前还会返回 `bootstrap_recovery_validation`，它会按当前 bootstrap 模式临时构造 writer/reader runtime 依赖并实际执行一次 recovery probe，用真实 `recoverable / recovery_reason / workspace_backend / recovery_capabilities / recovery_entrypoints` 结果验证默认恢复合同是否与模式描述一致。
- `bootstrap_recovery_validation.recovery_capabilities` 与 `run_recovery.recovery_capabilities` 共享同一层恢复摘要语义，当前至少表达 `recovery_mode`（如 `unavailable / in_process / registry_backed`）以及 `requires_durable_workspace / requires_registry_bindings`；默认 runtime 验证与单 run 恢复能力说明不应再各自发明第二套语言。
- `embedded_runtime_bootstrap` 当前还会提供顶层 `recovery_alignment_summary`，把 `default_runtime_recovery.recovery_entrypoints` 与 `bootstrap_recovery_validation.recovery_entrypoints` 收口成 expected vs actual 的统一对比摘要，供控制面直接判断默认恢复预期与真实 bootstrap 样本是否一致。
- `PATCH /api/runtime-profile/embedded-runtime-bootstrap` 在提供 `conversation_id` 时，还会追加 `embedded_runtime_bootstrap_updated` 治理 trace/audit 事件，把默认 runtime 策略热切换正式纳入 runtime control plane 审计链。
- `post_update_verification` 当前不仅返回前后值，也会直接给出布尔判断：`runtime_mode_changed / recovery_posture_changed / workspace_backend_changed / durable_capability_changed`，用于让调用方以 machine-readable 方式判断此次 bootstrap 热切换的实际影响。
- `post_update_verification` 现也会返回 `previous_default_recovery_expectation / current_default_recovery_expectation`，用于让调用方直接比较默认恢复能力合同本身，而不只依赖拆散后的派生布尔字段。
- child executor output 当前已不再只保留 `result_type / conclusion`，而是会稳定携带 `entities / focus_points / action_items`，并进入 replay record 与 compact summary。
- Runtime Surface child executor 读模型当前也已正式消费 `latest_merged_semantics`，包括 `intent_label` 与最小 `merge_behavior`，避免这层语义只停留在 SDK 内部 contract。
- `parent merged semantics` 当前已额外提升为 dedicated read model，可独立于 child artifact summary 被 Runtime Surface 消费；后续 parent 侧其他治理/执行视图不应继续从 child summary 间接取值。
- dedicated merged semantics read model 现已进一步暴露 `intent_catalog_version / supported_intents / merged_sections`，用于稳定 child intent taxonomy 与 parent merge sections。
- dedicated merged semantics read model 的 `merged_sections` 现在会为 list section 暴露 `section_kind = list / item_count`，为 latest conclusion 暴露 `section_kind = text / text_length`；`parent_state_surface` 同步暴露 `section_source / section_ids / section_counts`，让 parent overview 消费方不再从 section payload 临时反推 count。
- dedicated merged semantics read model 现也暴露 `parent_state_surface`，作为 parent overview 的最小消费面；它用于表达“当前 parent 已吸收了什么 child merge 状态”，而不是替代 replay 或 child artifact summary。
- parent overview 的最小消费面已进一步下沉到 `governance_overview.run`；Runtime Surface 的 `Run Overview` 现在应优先读取该后端 contract，而不是继续从 child merged semantics read model 反推 `child_merge_*` 字段。
- child output merge 当前已开始进入正式 contract：parent merge 不再只看 `merge_strategy` 字符串，而会按 `intent_label` 选择最小 merge behavior（如 `append_dedup / replace_latest / summary_only`）。
- SDK 与 Facade 现已提供独立 preflight 评估入口，可在不创建 child run 的前提下返回 `executor_binding_status / executor_binding_blockers / recommended_next_step`，供后续正式执行前 gate 复用。
- gate 与 preflight 当前职责已分离：preflight 负责原子 readiness 检查，promotion gate 负责最终升格决策；新增消费方时应优先读取 gate，而不是从 preflight 自行拼 allow/deny。
- execution prerequisites 当前职责是 gate 内的执行前置条件证据：它把 preflight requirement checks 与 promotion gate allowed 归一成稳定 `requirements / missing_requirements`，供 smoke、quality gate 和治理消费者读取。
- backend registry 当前职责是 worker backend 候选目录：它可以让 skeleton handoff 继续识别 `embedded_sdk_worker`，但真实 dispatch 仍由 `worker_backend_dispatch_ready` 阻断，避免把 skeleton output/merge 能力误读成生产 child executor。

维护约束：

- SDK 实现必须复用 Runtime Core 和 Governance seam。
- SDK 不能绕过 approval / policy / trace。
- SDK 当前为 in-process memory runtime，不承诺跨进程持久化。
- 在 Phase II 持久化 seam 收口完成前，任何新能力都不应默认依赖 `_runs / _events / _approvals / _tool_continuations / _loop_continuations` 的进程内存在性。
- 治理台和审计服务应优先读取 `event_status_kinds` 判断可消费事件，不要在前端硬编码猜测运行时事件面。
- `RuntimeContractSnapshotService` 会检查 `command_contract.embedded_sdk.event_status_kinds`，事件契约缺失时 contract snapshot 应退化为 degraded；同时会校验关键必需 `status_kind`：`approval_created`、`approval_resolved`、`approval_replayed`、`approval_ignored`、`execution_loop_done`、`loop_continuation_registered`、`loop_continuation_consumed`、`loop_continuation_discarded`。
- `RuntimeContractSnapshotService` 也会校验上述关键事件的 `required_payload`：例如 `approval_created` 必须声明 `approval_request_id / approval_request`，`approval_resolved` 必须声明 `approval_request_id / approval_request / decision`，`approval_replayed / approval_ignored` 必须声明 `approval_request_id / approval_request / original_decision / attempted_decision`，`execution_loop_done` 必须声明 `run / completed_steps`，continuation 生命周期事件必须声明 `loop_continuation`。reviewer / fallback 事件消费者应同样通过 `event_status_kinds` 与 `validate_embedded_sdk_event_payloads(...)` 判断 payload 完整性，不在前端或 adapter 中硬编码事件形状。
- `validate_embedded_sdk_event_payloads(...)` 可用于校验真实 SDK 事件样本是否满足 `event_status_kinds.required_payload`，适合 adapter pilot、治理台健康检查复用；当前 `runtime_contract_smoke` 已把该检查作为 `embedded_sdk_event_payloads` 门禁项。
- 默认运行时相关依赖不应继续由外部调用方在多个入口各自 new singleton；新增默认构造路径时，应优先复用 `EmbeddedRuntimeFactory`。

参考对标约束：

- `D:\AI\AIcode\learn-claude-code` 应优先作为 Runtime Harness 的概念分层与术语校正参考，尤其用于 loop、recovery、runtime task、subagent、teammate 边界的判断。
- `D:\AI\AIcode\claude-code` 应优先作为真实控制面机制参考，尤其用于 backend abstraction、in-process runner、permission sync、reconnection、teammate lifecycle。
- 外部参考只能提供模式与分层，不直接覆盖本项目的 Runtime Core / Governance / Approval / Query-Run Read Model 语义。
- 后续 `child executor / worker runtime / multi-process recovery` 相关变更，应明确引用具体参考切面，而不是笼统宣称“参考某仓库实现”。

## 8. Agent Harness Facade Contract

主要来源：

- `backend/agent_framework/harness.py`
- `backend/services/command_registry_service.py`

当前状态：

- `build_agent_harness_facade_contract()` 已作为 command runtime contract 的一部分暴露。
- `create_agent()` 是面向垂域项目的高层入口。
- `AgentHarnessFacade.run()`、`stream()`、`approve()`、`resume()`、`delegate()`、`create_artifact()`、`list_artifacts()`、`register_tool()`、`execute()` 已进入 preview。
- Facade contract 现同步暴露 `delegate_preflight`，供垂域接入方在 facade 层直接读取“当前不是 child executor”的正式判断。
- `create_agent()` 当前也已支持 `runtime_dependencies / runtime_factory`；若未显式传入 SDK，会优先通过默认 factory 构造共享依赖下的 embedded runtime。
- Facade contract 当前已暴露 `facade_runtime_posture = embedded_harness_v1_candidate`、`tool_registry_bridge` 与 `default_tool_executor`，表示它已经具备最小 ToolSpec 注册与本地工具执行 bridge，但 Runtime Core、事件、审批和 recovery 仍由 Embedded SDK 负责。

当前方法：

- `run`：归一化业务输入，填充 agent 默认模型、用户、会话、run kind，并通过 `EmbeddedAgentRuntimeSDK.create_run()` 创建运行。
- `stream`：代理 `EmbeddedAgentRuntimeSDK.stream_events()`，不重新实现事件存储。
- `approve`：代理 `EmbeddedAgentRuntimeSDK.submit_approval()`，不绕过 ApprovalEngine 语义。
- `resume`：代理 `EmbeddedAgentRuntimeSDK.resume_run()`，不直接跳过 Runtime Core 状态机。
- `delegate`：代理 `EmbeddedAgentRuntimeSDK.delegate_run()`，只创建 child run 对象和事件关系，不执行真实并行任务。
- `create_artifact`：代理 `EmbeddedAgentRuntimeSDK.create_artifact()`，只创建可审计 artifact 引用；持久化由可注入 `ArtifactStore` 负责，Facade 不直接写真实文件系统。
- `list_artifacts`：代理 `EmbeddedAgentRuntimeSDK.list_artifacts()`，为治理台和 replay 提供按 run 查询入口。
- `register_tool`：注册 `ToolSpec` 元数据与可选本地 handler；若注入了 `ToolRuntimeService`，会同步写入其底层 tool registry 的 ToolSpec 元数据，但不会创建第二套 runtime state。
- `execute`：代理 `EmbeddedAgentRuntimeSDK.execute_run()`，只进入最小状态循环；可透传 tool policy / tool executor / reflector / reviewer / fallback handler callable。当调用方未显式传入 `tool_executor` 且 facade 已注册本地工具 handler 时，facade 会构造最小默认 executor，并把 action / observation metadata 放入 SDK-owned `tool_result.execution` 与 `run.tool_history`。

Phase II 当前边界说明：

- Harness 仍建立在 Embedded SDK 的内存态恢复能力之上，尚未对外承诺 durable workspace。
- `resume()` 的真实恢复能力上限受 SDK continuation persistence seam 约束。
- `delegate()` 当前仍是 child run object relationship seam，不应被上层误读为真实多智能体执行器。
- Facade 当前已同步暴露 `evaluate_delegate_gate(...)`，供垂域项目在不创建 child run 的前提下读取 promotion gate 结果。
- 若未来要把 `delegate()` 升级成真实 child executor 入口，应先复用既有 promotion gate，而不是直接在 facade 层加行为。
- 若未来要把 `delegate()` 升级成真实 child executor 入口，还必须保证 child output merge behavior 已稳定，而不是继续依赖 ad hoc metadata 拼接。
- `register_tool()` 当前只覆盖 ToolSpec 元数据和同步本地 callable handler；超时、retry、沙箱、schema validation 与真实远程 tool backend 仍应继续落到 ToolRuntimeService / PolicyEngine / ExecutionLoop seam。
- `ToolRuntimeService.execute_tool(...)` 当前提供最小同步执行 adapter：解析 registry tool、先做 `permission_level_gate_v1` policy coordination，再做 lightweight schema v1 校验，并返回 `phase-ii-tool-runtime-execution-v1` envelope。Facade 在没有显式 `tool_executor` 且没有本地 handler 时，可以通过该 adapter 执行工具，但事件和 `tool_history` 仍由 SDK 记录。
- `ToolRuntimeService.build_runtime_contract().execution_adapter` 当前明确 `schema_validation = lightweight_schema_v1`、`schema_validation_keywords = required / type / enum / object.required`、`policy_coordination = permission_level_gate_v1`、`policy_decision_statuses = allowed / approval_required / denied`、`timeout_enforcement = post_call_elapsed_check`、`retry_policy = sync_exception_retry`。这里的 schema validation 不是完整 JSON Schema；policy coordination 只给出执行前机器可读 gate，不创建 approval request；timeout 是同步调用返回后的 elapsed gate，不会强杀正在运行的工具；retry 只重试工具实现异常，不重试策略拦截、参数校验失败或工具不存在。
- `ToolRuntimeService.execute_tool(..., execution_options={max_attempts, timeout_seconds})` 会在 `execution.retry` 与 `execution.timeout` 中输出机器可读元数据。`retry.status` 至少包含 `not_needed / recovered / exhausted / skipped`；`timeout.status` 至少包含 `not_configured / not_exceeded / exceeded / skipped`。
- `ToolRuntimeService.execute_tool(...)` 会在 `execution.policy_decision` 中输出 `status / allowed / requires_approval / permission_level / reason_code / policy`；`ask` 和 `high_risk` 返回 `status = approval_required` 且不调用工具实现，`deny` 返回 `status = policy_denied` 且不调用工具实现。
- `ToolRuntimeService.evaluate_tool_policy(tool_name)` 是无副作用 policy probe，只读取 registry tool / ToolSpec 并返回同一套 `permission_level_gate_v1` decision，不做 schema validation，也不调用工具实现。`AgentHarnessFacade` 会在已有 `tool_policy` 返回 `allowed` 时调用该 probe；若 probe 返回 `approval_required / denied`，facade 会把它改写成 execution-loop 可识别的审批/拒绝决策，让 SDK 继续负责 approval request、continuation 和审计事件。
- 审批通过后的恢复执行通过 `execution_options.policy_override.status = approved` 显式进入 `ToolRuntimeService.execute_tool(...)`；该 override 只允许原始 policy decision 为 `approval_required` 的工具继续执行，并在 `execution.policy_decision` 中保留 `original_status / original_reason_code / override`。`deny` 仍不可被 approved override 绕过。
- `runtime_contract_smoke` 的 `runtime_approved_tool_execution_bridge` check 会覆盖这条 approved override 链：初次 `ask` 生成 pending approval，approved 后工具调用次数为 1，`execution.policy_decision.original_status = approval_required` 且 `override.status = approved`；同一 check 也验证 `deny + approved override` 仍返回 `policy_denied`。
- `runtime_contract_smoke` 的 `sdk_tool_runtime_execution_bridge` check 会覆盖 SDK 直连 ToolRuntimeService 链：`auto` 工具直接进入 `tool_history`，`ask` 工具先进入 SDK approval lifecycle 并在 approved 后执行一次，`deny` 工具在调用 handler 前 fail-closed。

II-1 第一刀当前已完成：

- SDK 当前易失状态边界已明确，不再默认把 `_runs / _events / _approvals / _tool_continuations / _loop_continuations` 误当成 durable workspace。
- `tool_approval_continuation / loop_continuation` descriptor 已有统一 helper，便于后续 persistence seam 继续外提。
- `submit_approval(..., "approved")` 与 `resume_run(..., continue_loop=True)` 的当前恢复上限已明确：两者都属于条件式跨进程恢复 seam，只有在 durable workspace 与 registry binding 可解析时才允许跨进程重挂 executable continuation。
- `delegate_run(...)` 的当前上限已明确：仅限 child run relationship seam。
- `EmbeddedRunWorkspaceStore` seam 已落地，当前可统一承接 run snapshot / events / approvals / continuation descriptors 的读写边界。
- SDK 已支持从 `workspace_store` 回填 run snapshot / events / approval snapshot；但 persisted continuation descriptor 仍只代表“可恢复信息存在”，不代表 executable continuation 已可跨进程恢复。
- 已新增 `probe_run_recovery(run_id)` 作为正式 recovery probe seam，会返回 `recoverable / unrecoverable`、`recovery_reason`、descriptor/executable availability，并把 probe 结果写回 metadata 与 persisted continuation descriptor。
- `probe_run_recovery(run_id)` 当前还会直接返回入口级 `recovery_entrypoints` 摘要，至少覆盖 `submit_approval + approved`、`resume_run + default`、`resume_run + continue_loop` 的 `available / blocked_reason / recovery_reason / approval_status`，外层消费方不应再从 approval、tool/loop continuation 明细自行反推入口是否可用。
- 其中 `default_runtime_recovery.recovery_entrypoints` 表达的是默认 runtime 的能力预期；`run_recovery.recovery_entrypoints` 与 `bootstrap_recovery_validation.recovery_entrypoints` 表达的是当前 run 或真实 bootstrap probe 的即时结果，因此会额外受到当前 approval 与 `run_state` 等状态门禁影响。例如已 resolved approval 会以 `approval_already_resolved` 阻断 `submit_approval + approved`，普通非等待审批 run 则可能因 `run_not_waiting_approval` 被即时阻断，即使默认 runtime 仍具备跨进程恢复能力。
- `recovery_alignment_summary` 当前会把入口对比结果统一归一为 `aligned / state_gated / mismatch`：其中 `state_gated` 明确表示当前 run 或 probe 样本受 `run_not_*`、`approval_already_resolved` 这类状态门禁影响，不应误判为默认恢复能力本身发生偏离；只有真正的能力不一致才应落到 `mismatch`。
- `submit_approval(..., "approved")` 与 `resume_run(..., continue_loop=True)` 在仅有 persisted continuation descriptor、但无 executable continuation 时，会统一按 `missing_executable_continuation` fail-closed，并写入 `recovery_failed_closed` status event。
- 已新增可注入 `EmbeddedContinuationRegistry` seam；当 continuation descriptor 持有稳定 binding id，且当前 SDK 能从 registry 解析到 binding 时，SDK 可以在新进程里把 persisted descriptor 重新挂接成 executable continuation。
- tool continuation 与 loop continuation descriptor 当前都支持持久化 binding identity，供 `probe_run_recovery()` 与实际 recovery 共享同一套 resolver 逻辑。
- `EmbeddedContinuationRegistry` 当前已支持标准 binding catalog 输出；SDK 可通过 `list_continuation_bindings()` 暴露只读 binding 清单，供排障、预检和后续执行器前置校验使用。
- child executor merge 当前已支持最小 intent-aware merged semantics：`child_executor_merged_semantics` 会写入 parent metadata，并与 replay / summary 保持一致。
- 当前前端消费面仍保持只读展示，不在 UI 侧二次解释 merge 行为；`intent_label / merge_behavior` 仍以后端 contract 为真源。
- `child_executor_output_summary` 与 `child_executor_merged_semantics` 当前职责已分离：前者面向 child output artifact 摘要，后者面向 parent merge 结果解释；新增 parent merge 消费方时应优先复用后者。
- `merged_sections` 当前最小固定为 `merged_entities / merged_focus / merged_actions / latest_conclusion`；后续若新增 parent merge section，必须先更新 contract、测试和消费面，而不是在前端临时拼装。
- `parent_state_surface.section_counts` 必须与 `merged_sections` 保持一致：entities/focus/actions 使用对应 list section 的 `item_count`，latest conclusion 使用 text section 的 `text_length`。该 surface 只作为 read model 摘要，不改变 child output replay 或真实执行语义。
- `parent_state_surface` 当前最小固定为 `intent_label / entity_count / focus_count / action_count / primary_entities / latest_conclusion`；它适合作为 Runtime Surface 或后续治理总览的 parent-facing 概览层。

II-1 第一刀当前未做：

- 还没有完整 persistent workspace。
- 还没有跨进程 continuation 恢复。
- 还没有真实 child executor。
- 还没有多进程 / 多实例恢复协调器。

维护约束：

- Facade 不能成为第二套 Runtime Core。
- Facade 新能力必须先映射到底层 SDK / Runtime Core / Governance seam。
- Facade 工具执行 trace 必须复用 SDK 事件流与 `tool_history`；不允许新增独立 trace store。
- 垂域业务可以依赖 Facade，但不应直接依赖 scheduler store 或外部框架 adapter 内部结构。

## 9. Execution Loop Contract

主要来源：

- `backend/agent_framework/execution_loop.py`
- `backend/agent_framework/runtime.py`
- `backend/agent_framework/events.py`

当前状态：

- `ExecutionLoopController` 已进入 preview。
- 当前仅提供最小状态循环：`planning -> generating -> observing -> finalizing -> done`。
- 每个步骤写入 state event 与 `execution_loop_step` status event。
- 完成时写入 `done` event，`status_kind = execution_loop_done`。
- 可选 tool policy 在 `generating` 后、tool executor 前执行；返回 `approval_required` 时，run 进入 `waiting_approval`，写入 `tool_permission_required` event，并停止 loop；SDK 会把该暂停点转成正式 `ApprovalRequestState`，写入 `approval_request_id / approval_request` 并追加 `approval_created` event。
- tool policy 返回 `denied` 时，run 必须 fail-closed：进入 `failed`，`stop_reason = tool_policy_denied`，写入 `tool_permission_denied` error event，并停止后续 tool executor / done event。
- 可选 tool executor 在 tool policy 允许后执行，结果会进入 `tool_calling` 状态，写入 `tool_call_start` / `tool_result` event，并记录到 `run.tool_history`。
- 当 `execute_run` 因 `approval_required` 暂停且传入了 tool executor 时，SDK 会登记内存态 tool continuation；`submit_approval(..., "approved")` 会消费该 continuation，写入 `tool_approval_continued`、`tool_call_start`、`tool_result`，并转回 `observing`。
- `submit_approval(..., "denied")` 会丢弃 pending tool continuation，避免同一审批后续被重复提交时恢复已拒绝工具。
- 审批生命周期采用已决不可反写规则：`denied -> approved` 与 `approved -> denied` 都不会修改原审批结果，也不会再次消费或恢复 continuation；调用方应读取 `approval_submission.status / reason / original_decision / attempted_decision` 做机器可读判断。
- 当上一次 `execute_run` 保存了 reflector / reviewer / fallback handler continuation，调用 `resume_run(..., continue_loop=True)` 可从 `observing` 继续执行后续 `observing / finalizing / done`，不会重新进入 `generating` 或再次触发 tool executor。
- `run.metadata.tool_approval_continuation` 与 `run.metadata.loop_continuation` 是当前内存态 continuation 的可观测 descriptor；状态值包括 `pending`、`consumed`、`discarded`，用于治理台、审计和排障展示。
- continuation 生命周期会写入标准 status event：`loop_continuation_registered`、`loop_continuation_consumed`、`loop_continuation_discarded`，事件 payload 携带 descriptor 快照，供 Governance Timeline / Audit 回放。
- `probe_run_recovery(run_id)` 会写入 `recovery_probe_evaluated` status event；当恢复尝试被阻断时，SDK 会写入 `recovery_failed_closed` status event。两类事件都必须携带 machine-readable `recovery` payload，便于治理台和排障链路直接解释当前恢复状态。
- Runtime Surface 当前已提供 dedicated `run_recovery` 读模型与 `/api/runtime-profile/run-recovery` 接口；新增恢复消费方时应优先复用该 contract，而不是直接从 SDK 内部 metadata 或测试样本手工拼装恢复判断。
- `run_recovery` 读模型必须原样透出 SDK recovery probe 的 `checkpoint` 与 `resume_cursor`；Governance Overview 中的 `run_recovery` 摘要也应保留这两个字段，避免前端或审计消费者从 continuation descriptor 自行推断恢复状态。
- `run_recovery` 读模型还必须透出 `recovery_operation_boundary / latest_recovery_operation / recovery_operation_history / recovery_operation_count`，作为恢复操作审计的正式消费入口；治理台和垂域项目不应直接扫描 SDK metadata 或事件样本来重建该 read model。
- `run_recovery.latest_recovery_operation` 与 `run_recovery.recovery_operation_history` 必须只保留 compact operation evidence，不得暴露 callable、handler、provider client 或 active stream iterator。`recovery_operation_history` 当前最多保留最近 20 条。
- `run_recovery.recovery_audit_summary` 是 recovery operation history 的读侧审计摘要，至少包含 latest status / latest entrypoint / latest reason / status counts / entrypoint counts / reason counts / retry counts / retry status counts / latest retry status / latest retry terminal reason / ownership status / terminal status。该 summary 只作为治理证据，不是 worker lease validation、retry execution 或执行授权来源。
- `RecoveryAuditTimelineService` 是 opt-in recovery operation trace writer：调用方显式传入 compact recovery operation 时，它会写入 `source = recovery_audit`、`event_type = recovery_operation_recorded` 的 Runtime Trace，并用 `recovery_audit:<run_id>:<operation_id>` 作为 dedupe key。该 writer 不自动接入 SDK recovery 主流程，写入失败或 trace service 不可用时必须 fail-open。
- SDK worker ownership auto-claim 现在分为三层：默认 descriptor-evidence-only、旧的显式 `worker_ownership_auto_claim_enabled` opt-in claim seam、以及新增的 `worker_ownership_auto_claim_gate_enforced` opt-in enforcement seam。开启 gate enforcement 时，SDK 会先读取 explicit auto-claim enablement gate；production gate、durable ownership、idempotency/audit、rollout decision 或 entrypoint allowlist 任一不满足时，不调用 `claim_run`，并在 `recovery_failed_closed.recovery_operation.worker_ownership.auto_claim_enablement_gate` 保留 nested blocked evidence。该 seam 不代表默认 production ownership 或默认 recovery auto-claim 已启用。
- Runtime contract smoke、Quality Gate、Runtime Contract Gate 与 Snapshot 当前已守护 `runtime_contract_summary.recovery_audit_operation_history_coverage.audit_smoke`。该覆盖只证明 recovery audit operation history/readiness evidence 可读，不代表 recovery executor、worker lease validation 或默认跨进程恢复已经启用。
- Runtime contract smoke、Quality Gate、Runtime Contract Gate 与 Snapshot 当前已守护 `runtime_contract_summary.production_recovery_registry_checkpoint_policy_coverage.policy_smoke`。该覆盖只证明 registry/checkpoint production policy 可读，不代表 recovery executor、worker lease validation 或默认跨进程恢复已经启用。
- 当前 recovery reason 至少包含：`descriptor_missing`、`ready_in_process`、`ready_via_registry`、`missing_registered_binding`、`missing_executable_continuation`、`workspace_backend_not_durable`、`workspace_backend_fallback_active`。其中：
  - `ready_via_registry` 表示当前进程虽然没有原始内存态 continuation，但 registry 已能把 binding 重挂为 executable continuation；
  - `missing_registered_binding` 表示 descriptor 已提供 binding identity，但当前 registry 无法解析，因此仍必须 fail-closed；
  - `missing_executable_continuation` 表示 persisted continuation descriptor 已存在，但既没有原始内存态 continuation，也没有足够 binding identity 完成重挂，不能误判为跨进程恢复已完成。
  - `workspace_backend_not_durable` 表示当前 `workspace_store` 只提供内存态 descriptor 保存，不应误判为真正的跨进程恢复来源。
  - `workspace_backend_fallback_active` 表示 SQL workspace backend 已退回到内存 fallback，当前恢复结果只能视为降级态，不应误判为 durable cross-process recovery。
- continuation binding catalog 只暴露描述信息，例如 `binding_id / binding_kind / handler_name / metadata`，不暴露可执行 handler 本身；它表达的是“已注册 binding 能力面”，不是执行成功承诺。
- `build_policy_engine_tool_policy(...)` 可把 `PolicyEngineService.evaluate_tool_use()` 结果转为 `ExecutionToolDecision`，作为 PolicyEngine 与 Execution Loop 之间的标准 adapter seam。
- 可选 reflector 在 `observing` 后执行，结果写入 `metadata.execution_reflections` 与 `execution_loop_reflected` event。
- reflector 返回 `status = revise` 且未超过 `max_iterations` 时，写入 `execution_loop_revision_requested`，并回到 `generating` 开启下一轮 iteration。
- 可选 reviewer 在 `finalizing` 阶段执行，结果写入 `metadata.execution_review` 与 `execution_loop_reviewed` event。
- reviewer 返回 `status = rejected` 时，默认把 run 转为 `failed`，写入 `execution_loop_review_rejected` error event，并停止后续 done event。
- reviewer 或后续 callable 抛错时，默认 fail-closed：run 转为 `failed`，`stop_reason = loop_exception`，写入 `execution_loop_failed` error event。
- 可选 fallback handler 可把异常转为 `ExecutionFallbackResult(status = handled)`，写入 `metadata.execution_fallback` 与 `execution_loop_fallback_applied` event，然后继续后续 loop。

维护约束：

- Execution Loop 只负责循环状态和事件包络。
- 真实 LLM 生成、企业 tool registry、ToolRuntimeService、LLM reflector/reviewer、降级、子智能体执行器应作为后续 step / policy / adapter 挂接到该 seam。
- tool policy / executor seam 只表达 permission 与 act 阶段结果；当前已具备正式 `ApprovalRequestState` 创建、审批提交入口、内存态 approved continuation 恢复和可观测 continuation descriptor，但还不代表已经具备跨进程 continuation 持久化、完整工具注册、权限 UI 或沙箱执行。
- 降级默认不能静默吞错；任何 fallback 都必须写入 metadata 与事件流。
- 不允许在 Facade 中绕开 `ExecutionLoopController` 直接拼接执行循环。

## 10. Self-Improvement Ledger Contract

主要来源：

- `backend/services/self_improvement_ledger_service.py`
- `backend/services/runtime_surface_service.py`
- `backend/models.py`
- `backend/routers/learnings.py`

当前状态：

- `self_improvement_ledger` 已作为 Runtime Surface contract 暴露。
- 当前 contract 描述学习、错误、功能请求三类自我改进记录。
- 当前 contract 明确可追踪来源：conversation、error、user_feedback、quality_gate、runtime_contract。
- 当前 contract 明确晋升目标：AGENTS.md、docs、system_prompt、best_practice、skill。
- 当前 contract 明确质量控制：review、version_history、duplicate_merge、rollback、restore。
- 当前 contract 暴露 `health_summary`，汇总 pending learning、pending error、pending feature request、reviewed learning 和平均质量分。
- `SelfImprovementTimelineService` 已统一承接 learning、error、feature request 治理事件的 trace / audit 写入。
- self-improvement timeline payload 已统一包含 `dedupe_key`，格式为 `{source}:{event_type}:{conversation_id}:{entity_id}`。

维护约束：

- 该 contract 只暴露能力边界和稳定枚举，不直接暴露 ORM 行。
- 新增 record type、tracked source、promotion target、quality control 或 health summary 字段时，必须同步 `RuntimeContractSnapshotService` 和测试。
- 自我改进记录进入治理台前，必须带来源、状态和可回放上下文。
- 健康统计必须通过 service 汇总，不应让前端直接拼数据库语义。
- router endpoint 不应直接拼 Governance Timeline payload；应通过 self-improvement timeline adapter 写入。
- 创建或更新 error / feature request 时，如调用方希望治理台可回放，应传入 `conversation_id`。
- `dedupe_key` 已用于 self-improvement timeline 写入幂等；当 `RunTraceService.has_runtime_trace_dedupe_key(...)` 命中 persisted trace 时，应跳过重复 trace / audit 写入并返回 `dedupe_source = persisted_trace`。
- 幂等查询只应依赖持久化 trace，不应引入进程内全局集合，避免跨实例状态漂移。

## 11. Query Control Plane Contract

主要来源：

- `backend/services/query_control_plane_service.py`
- `backend/services/query_control_event_mapper_service.py`
- `backend/services/query_control_timeline_service.py`
- `backend/services/runtime_surface_service.py`
- `backend/services/runtime_contract_snapshot_service.py`

当前状态：

- `query_control_plane` 已作为 Runtime Surface contract 暴露。
- 当前 contract 固定请求生命周期：input_received、context_assembly、planning、model_stream、tool_decision、tool_execution、observation、review、final_output。
- 当前 contract 固定执行通道：main_chat、embedded_sdk、external_adapter、subagent_lane。
- 当前 contract 只表达控制面边界，尚不表示所有执行通道都已接入统一 trace event。
- `QueryControlTimelineService` 已提供统一 timeline adapter，可把生命周期阶段写入 trace / audit。
- Query Control timeline 使用 `source = query_control`，事件类型为 `query_control_{stage}`。
- Query Control timeline payload 固定包含 `channel / stage / query_id / conversation_id / snapshot_ref / dedupe_key`。
- Query Control timeline 默认 `dedupe_key` 格式为 `query_control:{channel}:{stage}:{conversation_id}:{query_id}`。
- `QueryControlEventMapperService` 已把 Embedded SDK 现有事件映射到 Query Control lifecycle。
- `QueryControlEventMapperService.build_record_payload(...)` 会为 `tool_result` 事件提取 compact `tool_runtime_observation`，包含 `tool_name / status / executor / policy_status / policy_permission_level / policy_reason_code / schema_validation_status / retry_status / retry_attempt_count / retry_max_attempts / timeout_status / timeout_seconds / timeout_enforcement`，但不会复制完整 result 文本、card 或任意 raw execution blob。

## 12. PromptOps Versioned Prompt Contract

主要来源：

- `backend/models.py` 的 `SystemPrompt`
- `backend/services/promptops_contract_service.py`
- `backend/routers/learnings.py`

当前状态：

- `promptops-versioned-prompt-v1` 是现有 prompt 记录之上的只读兼容合同。
- `GET /api/learnings/prompts/contract` 暴露 PromptOps registry，包含 `prompt_count`、`active_prompt_count`、`behavior_boundary` 和归一化后的 prompt contracts。
- 旧 prompt 默认映射为 `version = "1"`。
- `is_active = true` 默认映射为 `status = active`；`is_active = false` 默认映射为 `status = archived`。
- `{{variable_name}}` 模板占位符会被提取到 `variables_schema.properties` 和 `variables_schema.required`。
- tag 前缀可携带轻量治理元数据：
  - `version:<value>`
  - `status:draft|review|active|archived`
  - `owner:<id>`
  - `grounding_policy:<id>`
  - `eval_set:<id>`
  - `approval:not_required|pending|approved|rejected`
  - `rollout:<mode>`
  - `rollback_target:<version>`

维护约束：

- 该合同当前是 `visibility_only`，不改变 `/api/chat`、`RuntimeLearningService` 或 `PromptInjector` 的默认注入行为。
- Prompt 激活、审批、灰度、回滚执行必须等待后续 eval-backed promotion change。
- 新增 PromptOps 字段时，应优先保持向后兼容；旧 prompt 记录不能因为缺少版本 tag 而失效。
- 该阶段不引入 prompt version 表、Prompt Studio UI 或多轮 eval runner。

## 13. Agent MemoryOps Lifecycle Contract

主要来源：

- `backend/services/agent_memory_service.py`
- `backend/services/chat_context_compact_service.py`
- `backend/services/chat_context_packing_service.py`
- `backend/services/memoryops_contract_service.py`
- `backend/routers/memory.py`

当前状态：

- `agent-memoryops-lifecycle-v1` 是现有 memory/summary 能力之上的只读生命周期合同。
- `GET /api/admin/memoryops/contract` 暴露 MemoryOps registry。
- `AgentMemoryService` 的分层指令记忆映射为 `kind = runtime_instruction_memory`。
- 传入 `conversation_id` 且存在 durable compact summary 时，最新摘要映射为 `kind = conversation_summary`。
- `hot_session_state` 和 `long_term_memory` 当前只报告 posture，不表示已存在专用 MemoryOps 存储。
- `retrieved_knowledge_evidence` 当前报告 `promotion_mode = explicit_only`，检索片段不会默认写入长期记忆。
- registry 的 `behavior_boundary.mode = visibility_only`，并显式声明未改变 chat context packing、prompt injection 和 retrieval behavior。

维护约束：

- MemoryOps registry 不得创建、删除、提升、过期、注入或检索任何 memory entry。
- 自动长期记忆写入、冲突处理、TTL 执行、隐私删除、向量记忆库都必须另开 change。
- Conversation summary 的 audit source 仍是原始 `messages` 表；MemoryOps 只解释摘要生命周期，不替代原始会话记录。
- 后续多轮 eval 可以引用该合同的 kind/status/source/scope/injection_trace 字段，但不得把当前 visibility-only registry 当作行为 enforcement。

## 14. Multi-turn Agent Evaluation Gate

主要来源：

- `backend/services/multiturn_eval_gate_service.py`
- `docs/evals/multiturn/*.json`

当前状态：

- `multiturn-agent-evaluation-gate-v1` 是 deterministic contract check，不调用真实 LLM。
- scenario 文件包含 `id / title / turns / evidence / assertions`，其中 `evidence` 应使用 Grounding Policy、PromptOps、MemoryOps、tool 和 response behavior 的稳定字段。
- 当前样例覆盖：
  - `grounding_required_no_evidence`
  - `prompt_version_visibility`
  - `memory_summary_boundary`
- eval report 固定输出 `overall_status / scenario_count / status_counts / results / behavior_boundary`。
- scenario status 固定为 `passed / failed / skipped / blocked`。
- malformed scenario 不抛给 runtime consumer，而是返回 `blocked` 和机器可读 reason。

维护约束：

- Eval gate 当前只验证合同证据，不生成答案、不调用 `/api/chat`、不执行 tool、不访问 external provider。
- 默认 chat retrieval injection、prompt rollout、memory injection promotion 仍必须等 representative scenarios 通过后再另开 behavior promotion change。
- 后续如果加入 live model eval 或 LLM-as-judge，必须另开 change，并保留当前 deterministic scenario report 的后向兼容字段。
- `EmbeddedAgentRuntimeSDK` 可通过显式注入 `query_control_db` 和 timeline service 启用 query lifecycle 持久记录。
- `QueryControlEventMapperService` 已把 external adapter pilot 事件映射到 Query Control lifecycle。
- `FrameworkAdapterRuntimeService` 可通过显式注入 query control timeline service 启用 external adapter pilot 的 query lifecycle 持久记录。
- `QueryControlEventMapperService` 已把 subagent lane 事件映射到 Query Control lifecycle。
- `EmbeddedAgentRuntimeSDK.delegate_run(...)` 可在显式启用 Query Control recorder 后记录 `child_run_created -> input_received`。
- `SubagentRuntimeService.record_query_control_events(...)` 可把 `subagent_spawned / subagent_collected / subagent_merged` 写入 Query Control timeline。
- `stream_scheduled_orchestrator_events(...)` 已在 scheduler fan-out 路径中显式调用 subagent Query Control helper，记录 spawn、collect 与 merge 生命周期。
- `QueryControlEventMapperService.map_main_chat_event(...)` 已完成 `main_chat` 核心执行生命周期映射第一刀。
- `MainChatQueryControlService.record_query_control_events(...)` 已提供 `main_chat` 的 timeline recorder，并通过 execution context 开关保持 `opt-in + fail-open`。

维护约束：

- 新增或删除 lifecycle stage 必须同步 `RuntimeContractSnapshotService` 和测试。
- 主 chat、SDK、external adapter、subagent lane 后续接线时，应优先映射到该生命周期，而不是各自发明事件名。
- provider adapter、tool runtime、reviewer、timeline 只能作为边界挂接点，不应把执行细节塞进 Runtime Surface。
- Query Control 的 `tool_runtime_observation` 只允许作为 read-model 摘要，不应替代 SDK event 或 ToolRuntimeService execution envelope 原始真源。
- 写入 Query Control timeline 前必须校验 stage 和 channel 来自 Query Control Plane contract。
- Query Control timeline 幂等应优先依赖 persisted trace 的 `dedupe_key`，不应引入进程内全局集合。
- Embedded SDK 的 query lifecycle 记录必须是 fail-open，不能因为治理记录失败中断 SDK 主流程。
- External adapter pilot 的 query lifecycle 记录也必须是 opt-in 和 fail-open，不能因为治理记录失败中断受控 pilot。
- Subagent lane 的 query lifecycle 记录必须是 opt-in 和 fail-open，不能因为治理记录失败中断 child run 创建或 pseudo-subagent 协议。
- Scheduler fan-out 的 `subagent_merged` 目前是内部 Query Control 记录事件，不改变前端可见的 `scheduler_merged` 输出 contract。
- `main_chat` 第一刀应优先覆盖核心执行生命周期；审批、治理和通道专属事件不应在未收敛边界前直接混入主执行线映射。
- `main_chat` 当前只在受控 execution context 中开启 Query Control timeline recorder；普通 chat 路径不默认写入治理 timeline。
- 普通 chat 若需显式启用 `main_chat` timeline recorder，可通过 request-level `execution_context` 传入 gate；runtime execution context 与 request context 合并时以 runtime 字段优先。
- `ChatRequest.execution_context` 当前已收敛为白名单型输入 contract，不应接受任意扩展字段；新增专家入口字段时应同步 schema、测试与文档。
- 前端聊天页当前已有受控的专家模式开关；若开关关闭，客户端不应默认向 `/api/chat` 注入 `execution_context`。
- Runtime Surface 当前也已复用同一专家模式状态源；前端不应出现多个相互独立的 main chat trace 开关。
- Runtime Surface 当前已暴露 `main_chat_trace_overview`，用于区分“开关已开”与“最近一次 trace 已写入”；状态枚举新增时应同步前端展示与测试。
- `governance_overview.main_chat` 当前已复用 `main_chat_trace_overview` 的摘要字段；若后续字段扩展，应保持两者语义一致，避免一个显示 recorded、另一个仍显示 unavailable。
- Governance Timeline 当前以前端 domain 识别方式支持 `main_chat` 过滤；若后续新增其他 query control channel，应明确决定是否也提升为一等治理 domain。
- `main_chat_trace_overview` 当前已暴露 `stage_counts / last_success_stage / last_warning_stage`；若后续引入 error/failure 专用 stage，应同步修正这些字段的判定语义。
- `main_chat_trace_overview.recent_queries` 当前提供最近 N 次 `query_id` 摘要列表；若后续扩展为分页/完整历史，应保持现有列表字段的后向兼容。
- `main_chat_query_detail` 当前已在 contract 内显式携带 `read_model_layer / source_channel / identity_kind`，用于让 Runtime Surface 与 Governance Timeline 共享同一份自描述 read model 解释语义；`associated_run_ids` 只表示该 query 生命周期关联到的执行实例集合，不替代 `query_id` 作为 detail 主身份。
- Runtime Surface、Governance Timeline、Query Detail 与 Query History 面板当前已轻量展示 query read model metadata；后续前端扩展这些视图时，应继续消费 shared interpretation 结果，不要直接从原始 payload 重新拼 metadata。
- `main_chat_query_history` 当前已作为 dedicated history read model 暴露于 `/api/runtime-profile/main-chat-query-history`；其职责是提供分页/长历史摘要，不替代 `recent_queries` 或单 query `main_chat_query_detail`。
- `RuntimeSurfaceService.get_runtime_profile()` 当前已拆出独立 profile assembler；顶层 profile shell 位于 `backend/services/runtime_surface_profile_assembler.py::RuntimeSurfaceProfileAssembler`，profile request context / runtime scope / recovery target 推导位于 `backend/services/runtime_surface_profile_context.py::RuntimeSurfaceProfileContextAssembler`，`runtime_core` shell 与 scoped overlay 位于 `backend/services/runtime_core_contract_builder.py::RuntimeCoreContractBuilder`，`governance_overview.run` run-state assembly 位于 `backend/services/governance_overview_run_state_builder.py::GovernanceOverviewRunStateBuilder`，模型/提供方聚合已进一步下沉到 `ProviderCatalogBuilder`。后续新增 profile 组装能力时，应优先延续 concern-specific builder 边界，而不是继续把逻辑堆回 service 主方法或 assembler 主流程。
- `GovernanceTimelinePanel` 当前已把 `main_chat` workspace 下沉为独立子组件；后续继续瘦身治理面板时，应优先沿 summary/action/workspace 这种区域边界拆分，而不是重新把所有治理逻辑堆回主面板。
- `GovernanceTimelinePanel` 当前已把 `main_chat` 的查询历史与查询详情收口为独立 `Main Chat Query Workspace` 子组件；后续继续瘦身时，应优先沿 summary / action / workspace 的边界继续拆分，而不是把工作区逻辑重新堆回主面板。
- `GovernanceTimelinePanel` 当前已把治理 overview、基础 summary-action、Framework Adapter 专题卡和 remediation 卡下沉为独立子组件；后续若继续拆分，应优先保持 `GovernanceTimelineEventStream` 为主事件流主干，不建议再把事件流拆成更多互相重叠的小卡片。
- 当前前端已支持 `governance_query_id` 路由态；若后续后端提供 query 级专用接口，应保持与现有 route-driven drill-down 兼容，而不是强行替换。
- 当前 `Query Detail` 已优先消费 dedicated contract；若后续 query 级视图继续复杂化，应继续优先扩 dedicated read model，而不是回到前端本地推导。
- `main_chat_query_detail` 当前已作为后端正式 contract 暴露；若后续 query 级详情继续扩展，应优先扩这个 contract，而不是重新把复杂度推回前端。
- `main_chat_query_detail` 当前已同时支持内嵌在 `/api/runtime-profile` 中返回，以及通过 dedicated endpoint `/api/runtime-profile/main-chat-query-detail` 单独读取；后续若继续解耦 query 级 read model，应优先沿 dedicated endpoint 扩展。
- `main_chat_query_history` 当前采用 page/page_size + next_cursor 的兼容形态；后续若改为更强 cursor 模式，应保持现有 item 字段集合的兼容映射。
- 前端若需要解释 `main_chat_query_detail` 或 `main_chat_query_history`，应尽量共享同一份 contract helper；当前 `frontend-vue/src/services/governanceViewInterpretation.js` 已作为 `RuntimeSurfacePanel` 与 `GovernanceTimelinePanel` 的共同解释入口，避免两边各自维护字段归一化逻辑。涉及 `associated_run_ids` 这类 query/run 边界字段时，也必须通过该共享解释入口保持“query 是生命周期、run 是执行实例”的语义。
- 若后续扩展 `subagent_lane recent summary` 或其他 channel 的 query 只读模型，也应优先复用 shared interpretation facade，而不是为每个 channel 再发明一套独立前端解释逻辑。
- `main_chat_query_history` 当前是 `main_chat` 专用 read model；非 `main_chat` channel 若要扩展历史能力，应另行立项，不得默认复用当前治理面板语义。
- `subagent_lane_recent_summary` 当前已作为轻量试点 contract 暴露于 `/api/runtime-profile/subagent-lane-recent-summary`；其职责仅限 `recent summary` 候选验证，不得越级承担 detail/history/workspace 语义。
- `external_adapter_recent_summary` 当前已作为第二个非 `main_chat` 轻量试点 contract 暴露于 `/api/runtime-profile/external-adapter-recent-summary`；它只读取 Query Control trace 中 `channel = external_adapter` 的 compact lifecycle evidence，并输出共享 recent summary 字段集合，不从 framework-specific payload 推导 query 身份，也不表示 external adapter 已具备 query detail/history/workspace。
- `subagent_lane_query_detail_readiness` 当前作为后端门禁 contract 暴露于 `/api/runtime-profile/subagent-lane-query-detail-readiness`；它只回答 `subagent_lane` 是否具备进入 dedicated query detail contract 的前置条件，不返回 `recent_events / history_items / workspace` 状态。
- `channel_promotion_gate` 当前作为后端推广门禁 contract 暴露于 `/api/runtime-profile/channel-promotion-gate`；它统一汇总 `main_chat / subagent_lane / external_adapter` 的层级、阻断层和证据，供 Runtime Surface、治理诊断与 spec 收口直接消费。
- 恢复任何新的 channel 级实现前，必须先有 implementation resume decision：记录 channel、当前层级、目标层级、readiness evidence、blockers、decision、next allowed action 与 explicit non-goals。若缺少该记录，或目标会越级触碰 detail/history/workspace 多层能力，应继续停留在规格/架构层。
- `subagent_lane_query_detail` 当前已作为单 query dedicated contract 暴露于 `/api/runtime-profile/subagent-lane-query-detail`；其职责是展示指定 `query_id` 的 subagent lane lifecycle detail，不替代 child executor output replay/summary/merged semantics，也不得承担 history/workspace 语义。
- `subagent_lane_query_detail` 已进入 runtime contract smoke 与 quality gate summary；消费者应优先读取 `runtime_contract_summary.subagent_lane_query_detail_coverage` 判断该 contract 是否被门禁覆盖，而不是自行扫描 smoke stdout。
- `GovernanceTimelinePanel` 当前的治理历史工作区已按 `main_chat` 收口完成；后续应优先维护现有 query/history/detail 三层边界，而不是继续增加新的 channel 级展示分支。
- mapper payload 只能保留源事件身份和关键摘要，不应把完整事件体复制进 timeline。
- 当前 `overall_status = design_ready`，后续通道接线完成后才能提升状态。

## 12. Child Executor Dispatch Retry Scheduler Binding Gate

主要来源：

- `backend/agent_framework/child_executor_dispatcher.py`
- `backend/scripts/runtime_contract_smoke.py`
- `backend/scripts/quality_gate_report.py`
- `backend/services/runtime_contract_gate_service.py`
- `backend/services/runtime_contract_snapshot_service.py`

当前状态：

- `child_executor_dispatch_retry_scheduler_binding_gate` 已作为只读 binding gate 暴露，承接 dispatch retry scheduler handoff evidence 与显式 scheduler binding decision。
- 默认无显式 binding decision 时保持 `overall_status = blocked`，并在 `missing_sections` 中报告 `scheduler_binding_decision`。
- 即使 handoff evidence、scheduler contract、production scheduler gate、idempotency/dedupe、audit timeline、worker ownership 与 bounded attempts 都齐备，也只允许报告 `ready`，仍保持 `will_schedule_retry = false`。
- Runtime smoke、Quality Gate summary、Runtime Contract Gate、health trace normalization 与 Snapshot 已纳入 `child_executor_dispatch_retry_scheduler_binding_gate_coverage`。

维护约束：

- 该 gate 只能表达是否具备把 retryable dispatch result 交给 retry scheduler 的机器可读前置证据，不得实际调度 retry。
- `ready` 不等于 production scheduling authorization；生产调度仍需后续显式 change 接线。
- 新增 binding source、scheduler gate 字段或执行语义前，必须同步 OpenSpec、runtime smoke、Quality Gate summary、Runtime Contract Gate 和 Snapshot。
- 缺失 handoff、audit/idempotency、worker ownership、bounded attempts 或 production scheduler gate evidence 时必须 fail closed。

## 13. Child Executor Dispatch Retry Scheduler Execution Authorization Dry-Run

主要来源：

- `backend/agent_framework/child_executor_dispatcher.py`
- `backend/scripts/runtime_contract_smoke.py`
- `backend/scripts/quality_gate_report.py`
- `backend/services/runtime_contract_gate_service.py`
- `backend/services/runtime_contract_snapshot_service.py`

当前状态：

- `child_executor_dispatch_retry_scheduler_execution_authorization` 已作为只读 dry-run gate 暴露在 retry scheduler binding gate 下，用于说明 binding gate evidence 是否足以进入未来 scheduler execution authorization review。
- 默认没有显式 execution authorization request 时保持 `overall_status = blocked`，并在 `missing_sections` 中报告 `execution_authorization_request`。
- 只有 binding gate、显式授权来源、scheduler contract、production scheduler gate、durable schedule state、idempotency/dedupe、audit timeline、worker ownership 与 bounded attempts 都齐备时，dry-run 才可报告 `ready`。
- 即使 dry-run 报告 `ready`，仍固定 `will_schedule_retry = false` 与 `retry_scheduled = false`，不写 schedule state、不启动 worker、不默认启用 retry scheduler。
- Runtime smoke、Quality Gate summary、Runtime Contract Gate、health trace normalization 与 Snapshot 已纳入 `child_executor_dispatch_retry_scheduler_execution_authorization_coverage`。

维护约束：

- 不得从 binding gate ready 自动推导 production scheduler execution authorization。
- 缺失 production scheduler gate、durable schedule state、idempotency/dedupe、audit timeline、worker ownership 或 bounded attempts evidence 时必须 fail closed。
- 新增实际 scheduler execution、durable schedule writer 或 worker retry loop 前，必须另开显式 OpenSpec change，并同步 runtime smoke、Quality Gate summary、Runtime Contract Gate、health trace normalization 与 Snapshot。
- `ready` 只代表授权审查 evidence dry-run ready，不代表 retry 已调度、worker 已启动或默认 scheduler 已启用。

## 14. Contract Snapshot

主要来源：

- `backend/services/runtime_contract_snapshot_service.py`

用途：

- 防止 Runtime Surface contract 静默漂移。
- 给治理台和后续垂域接入方提供稳定 contract 指纹。

维护约束：

- 新增重要 contract 时同步 snapshot whitelist。
- 删除字段前先确认前端与测试是否仍消费。
- 任何 contract version 变化都应写入 `docs/change`。
