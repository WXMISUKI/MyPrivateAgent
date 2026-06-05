# 当前架构总览

> 本文记录 `MyPrivateAgent` 当前事实，不记录历史推演。历史实施过程见 `docs/change/`。

## 1. 当前定位

`MyPrivateAgent` 当前应被视为一个 **企业内部通用智能体底座**，而不是单一聊天 Demo，也不是直接绑定某个外部 agent 框架的业务应用。

当前推荐路线仍是：

- 自研 Runtime Core：掌握 run、event、approval、trace、audit、memory、skill、tool 等核心对象。
- 外部框架 Adapter：LangGraph / DeepAgents / CrewAI / Hermes / Manus 风格能力只作为可替换执行引擎或设计参考。
- 最小治理台并行：前端只承担观察、诊断、回放、调试，不承载业务领域逻辑。
- 双形态交付：核心能力可作为 embedded SDK 嵌入，也可通过标准服务接口对外暴露。

## 2. 四层结构

### Runtime Core

负责智能体执行的核心状态与事件。

主要落点：

- `backend/agent_framework/runtime.py`
- `backend/agent_framework/events.py`
- `backend/services/scheduler_runtime_entities.py`
- `backend/services/scheduler_runtime_contract.py`
- `backend/services/scheduler_runtime_store.py`
- `backend/services/run_trace_service.py`

当前核心对象：

- `AgentRunContext`
- `AgentState`
- `AgentRunKind`
- `AgentEvent`
- `SchedulerRuntimeRepository`
- run trace / audit trail

当前术语收口重点：

  - `query`：一个用户请求的完整运行生命周期，不等于单条 message、单次 completion 或局部 tool call
  - `run`：一次具体执行实例，是 Runtime Core 的主执行体，属于 query 生命周期中的执行体
- `child run`：从 parent run 派生出的下级执行体，不等于长期 teammate
- `scheduler run`：围绕某个 plan item 组织 fan-out / fan-in 的调度主运行
- `approval`：正式可回放的权限/治理决策对象
- `artifact`：运行过程产出的可引用结果对象
- `trace`：面向运行回放的执行证据流
- `audit`：面向治理记账的稳定事件流

当前首要命名收口判断：

- `child_run_id`：Runtime Core 正式术语
- `child_execution_id`：scheduler/runtime repository 兼容键
- `child_display_id`：对外展示层的稳定子运行标识，应优先等于 `child_run_id`

当前对象模型收口原则：

  - `query` 是用户请求的完整生命周期，不等于单条 message、单次 completion，也不等于局部 tool call。
- `run` 是一次具体执行实例，是 query 生命周期中的执行体，不等于长期 work goal。
- `scheduler run` 是调度层围绕 plan item 组织 fan-out / fan-in 的主运行，不等于 query 主键。
- `approval` 是正式可回放的治理决策对象，不是临时 warning 或 UI 状态。
- `artifact` 是运行过程产出的可引用结果对象，不是任意 payload 的别名。
- `trace` 是执行证据流，`audit` 是治理记账流，两者并列但不互相复制。
- `durable state` 是跨进程/跨刷新仍应被系统正式理解的状态，`runtime state` 只在当前执行窗口内有效。
- `control plane` 负责决定如何执行，`execution plane` 负责真正做事。

### Capability Layer

负责工具、MCP、Skill、Memory、Command、外部框架 adapter 的统一接入。

主要落点：

- `backend/services/tool_runtime_service.py`
- `backend/services/mcp_runtime_service.py`
- `backend/services/skill_runtime_service.py`
- `backend/services/agent_memory_service.py`
- `backend/services/command_registry_service.py`
- `backend/agent_framework/framework_adapter_spi/`
- `backend/agent_framework/framework_adapters.py`

当前关键 seam：

- `ToolRuntimeService.build_runtime_contract()`
- `ToolRuntimeService.build_adapter_health_contract()`
- `AgentFrameworkAdapter`
- `FrameworkAdapterRegistry`
- `EmbeddedAgentRuntimeSDK` preview contract

### Governance Layer

负责审批、策略、审计、诊断、回放和可观测性。

主要落点：

- `backend/services/approval_engine_service.py`
- `backend/services/policy_engine_service.py`
- `backend/services/runtime_contract_snapshot_service.py`
- `backend/services/framework_adapter_diagnostics_service.py`
- `backend/services/framework_adapter_timeline_service.py`
- `backend/scripts/doctor.py`
- `backend/routers/health.py`

当前治理能力：

- runtime contract snapshot guard
- framework adapter precheck
- external pilot timeline recording
- external pilot failure counts
- doctor / health 一致诊断
- remediation actions 展示

### Delivery Layer

负责向业务项目、前端治理台和外部系统交付底座能力。

主要落点：

- `backend/routers/`
- `backend/services/runtime_surface_service.py`
- `backend/agent_framework/harness.py`
- `backend/agent_framework/sdk.py`
- `frontend-vue/src/components/RuntimeSurfacePanel.vue`
- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- `frontend-vue/src/components/AdapterHealthCard.vue`
- `frontend-vue/src/components/AdapterPilotResultCard.vue`
- `frontend-vue/src/components/AdapterExternalPilotFailureSummary.vue`

当前交付形态：

- FastAPI service API
- Runtime Surface 管理/诊断接口
- Governance Timeline 回放入口
- Agent Harness Facade preview contract
- Embedded SDK draft contract
- Vue 最小治理台

## 3. 当前已收口能力

- Runtime Core 已具备状态机、事件、trace、audit、approval 的基本一等对象边界。
- Capability Layer 已具备 tool / MCP / skill / memory / command / framework adapter 的运行时契约。
- Framework Adapter 已完成 SPI 拆分，并保留 `backend.agent_framework.framework_adapters` 作为兼容 facade。
- LangGraph draft adapter 已具备 readiness、precheck、external pilot、request / event / output translator、错误分类和治理时间线记录。
- Agent Harness Facade 已提供 `create_agent()`、`run()`、`stream()`、`approve()`、`resume()`、`delegate()`、`create_artifact()`、`list_artifacts()`、`execute()` 的最小开发者入口，并复用 Embedded SDK、Runtime Core 与 ApprovalEngine。
- Embedded SDK 已具备嵌入式运行时最小闭环：`create_run`、`stream_events`、`submit_approval`、`resume_run`、`delegate_run`、`create_artifact`、`list_artifacts`、`execute_run`、`register_tool` 可用，并复用 Runtime Core 与 ApprovalEngine；tool policy 触发 `approval_required` 时会创建正式 `ApprovalRequestState`，审批通过后可消费 tool continuation 恢复原 tool execution，并可通过显式 `continue_loop=True` 接回后续 observing / finalizing / done；run metadata 会记录 `tool_approval_continuation` 与 `loop_continuation` 的 pending / consumed / discarded 状态，artifact 可通过可注入 `ArtifactStore` 进入持久化边界。
- Embedded SDK 现在已具备 workspace store、continuation registry、persistence interface 与 recovery probe 第一刀；`memory_preview / durable_ready / durable_degraded` 用于描述 storage posture，单个 run 是否可恢复仍由 descriptor、checkpoint/cursor、approval state 与 registry binding gate 决定。
- Embedded SDK 现在已新增 durable recovery operation contract；`submit_approval(..., "approved")` 与 `resume_run(..., continue_loop=True)` 的实际恢复尝试会记录 compact operation evidence，包括 operation id、entrypoint、status、reason、checkpoint/cursor ref、workspace posture 和 worker ownership boundary。该证据只用于生产排障和治理审计，不表示已实现 worker lease。
- Embedded SDK approval lifecycle 已可通过显式 recorder 进入 Runtime Trace；该 adapter 只记录 `approval_resolved / approval_replayed / approval_ignored / recovery_failed_closed` 的 compact governance evidence，并保持 opt-in + fail-open。
- Execution Loop 已具备 `ExecutionLoopController` 最小 seam，可驱动 run 经过 planning / generating / tool_calling / waiting_approval / observing / finalizing / done，并写入统一状态事件；同时支持可插拔 tool policy、tool executor、reflector、reviewer 与 fallback handler，形成可审计 permission / act / reflection / review / degradation gate；tool policy `denied` 会 fail-closed，不会继续执行工具。
- Tool Policy Adapter 已提供 `build_policy_engine_tool_policy(...)`，可把 `PolicyEngineService.evaluate_tool_use()` 的结果转换成 `ExecutionToolDecision`，用于 harness loop 的 `allowed / approval_required / denied` 统一语义。
- Health API 与 doctor CLI 已通过 `FrameworkAdapterDiagnosticsService` 统一 external pilot 失败统计口径。
- Runtime Surface 前端已拆出 adapter failure summary、adapter health card、pilot result card。
- Runtime Surface 与 Governance Timeline 已通过 `frontend-vue/src/services/governanceViewInterpretation.js` 共享 query/history/snapshot 的治理解释入口，route focus 仍然只是观察态，不是持久对象模型。
- `query workspace` 的高层通用化边界已单独提升为 canonical spec：`openspec/specs/query-workspace-generalization/spec.md`；当前 `main_chat` 仍是唯一完整 baseline，`subagent_lane / external_adapter` 只停留在 `recent summary` 试点或 readiness 阶段。
- 当前阶段推荐的工作模式已从“继续扩某个单一 channel 的局部体验”切换为“先收口通用边界，再决定是否继续扩 channel”；也就是说，`main_chat` 更像通用模式基准线，而不是默认继续加功能的主线。
- Main chat 已具备 `ChatContextPackingService` 输入装配边界：模型请求会在运行时系统层之后注入同一 `conversation_id` 的持久化最近历史，并在历史超出窗口或预算时用确定性早期摘要收口；该能力只影响主聊天模型输入，不改变 Runtime Surface / Governance Timeline payload，也不替代长期记忆检索。
- Main chat 现在具备 durable compact 边界：`ConversationSummary` 保存手动压缩后的会话摘要、覆盖消息数和最后覆盖消息 id；用户可通过 `/compact` 或会话 compact API 主动生成摘要，后续模型输入优先使用持久化摘要加摘要之后的新消息，原始 `messages` 仍保留用于审计、展示和搜索。
- Domain agent grounded answer 现在具备最小 promotion gate：`DomainAgentGroundedAnswerPromotionService` 会把 provider trial、grounding decision、PromptOps、MemoryOps 与 multi-turn eval evidence 聚合成 `go / review / blocked`，用于判断是否可以进入 repo-side grounded answer trial；该 gate 不调用 provider、不生成 answer、不写 source binding、不改变默认 `/api/chat` retrieval injection，GraphRAG 仍单独 gated。

## 4. 当前仍在路上的能力

- `AgentHarnessFacade` 当前仍是 preview；它已覆盖 run / stream / approve / resume / delegate / create_artifact / list_artifacts / execute / register_tool，并已开始复用 ToolRuntimeService bridge，但还不是完整稳定 SDK 产品面。
- Embedded SDK 已完成持久化姿态、workspace store、continuation descriptor、registry reattach、checkpoint/cursor、recovery operation evidence 和 approval lifecycle trace adapter 第一刀；但完整 durable continuation recovery、跨进程执行所有权、失败重试恢复和 worker lease 仍是后续阶段。
- ToolRuntimeService 已具备最小 execution adapter、permission gate、lightweight schema validation、retry 与 elapsed timeout metadata；完整远程 registry、沙箱隔离、worker 级硬超时和多租户权限模型仍应进入后续阶段。
- 真实并行 subagent executor 仍未完整落地；当前 child run / child executor 能力已经具备 preflight、promotion gate、record/stub/execution skeleton 与 merge semantics，但还不等于成熟 worker runtime。
- Runtime Surface 后端仍是聚合层，后续可继续拆出 contract assembler。
- Governance Timeline 前端仍偏大，已拆出 filter 与 event card，后续应继续拆 remediation card、snapshot command card。
- 外部框架 adapter 当前只把 LangGraph 作为 pilot 骨架，不应直接接入主 chat 路径。

## 5. 架构约束

- 不要把垂域业务直接写进 Runtime Core。
- 不要让业务项目直接依赖某个外部框架语义。
- 不要绕过 adapter SPI 直接在业务里调用 LangGraph / CrewAI 等运行时。
- 不要让前端治理台承担领域判断逻辑。
- `docs/change` 只作为历史审计日志；新接入者应先读 `docs/architecture/`。

## 6. 推荐阅读顺序

1. `docs/architecture/current_architecture.md`
2. `docs/architecture/runtime_contracts.md`
3. `openspec/specs/query-workspace-generalization/spec.md`
4. `docs/architecture/reference_project_mapping.md`
5. `docs/architecture/extension_points.md`
6. `docs/roadmap/next_phase_hardening.md`
7. `docs/change/2026-05-13-phase-e-architecture-hardening-plan.md`
