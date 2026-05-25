# Phase G Agent Runtime Reference Alignment

> 目标读者：继续维护 `MyPrivateAgent` 通用智能体底座的开发者、评审者、后续垂域智能体接入方。

## 1. 阶段定位

Phase F 已经把 Runtime Contract Gate、Quality Gate Report、Governance Timeline 幂等过滤和可观测细节打到较深。继续在前端治理台做小幅展示增强，边际收益开始下降。

Phase G 的目标是参考已下载的 Claude Code 相关项目，把后续重点从“治理台展示”切回“智能体运行时主干”：

- Query / execution control plane
- Tool runtime contract
- Prompt / context assembler
- Self-improvement ledger
- Subagent / worktree lane
- Provider stream adapter
- Feature gate

本阶段不迁移到任何外部框架，不复制反编译项目源码，只复用成熟设计思想和 contract 边界。

## 2. 参考项目结论

### 2.1 `D:\AI\AIcode\claude-code`

可借鉴：

- QueryEngine / query loop 把用户输入、模型流、工具调用和 turn state 放在统一控制面。
- Tool registry 以 `name / schema / call / render` 固定工具边界。
- Context assembler 独立拼装 CLAUDE.md、memory、git 状态、日期和系统上下文。
- Provider adapter 把不同供应商输出转换为统一事件流。
- Feature flag 保护实验能力，避免半成品进入主路径。

约束：

- 该项目包含逆向/反编译背景，只作为架构参考，不直接复制源码。

### 2.2 `D:\AI\AIcode\learn-claude-code`

可借鉴：

- 用 Agent Loop、Tools、Planning、Context Management、Permissions、Hooks、Memory、Prompt Construction、Tasks、Teams、Worktree、MCP 作为系统拆解清单。
- 用数据结构驱动设计，而不是先堆 UI。
- 以阶段化文档控制工程节奏，避免能力扩张失控。

### 2.3 `D:\AI\AIcode\self-improving-agent`

可借鉴：

- 把失败、用户纠正、能力缺口沉淀为一等记录。
- 将命令失败归入 errors，将用户纠正归入 learnings，将缺失能力归入 feature requests。
- 重要经验可晋升到 AGENTS.md、docs、system prompt、best practice 或 skill。

本仓库已有 `Learning / Error / FeatureRequest` 数据模型和 learnings API，因此 Phase G 不新增第二套文件账本，而是把现有学习治理体系正式暴露为 Runtime Surface contract。

## 3. 本轮落地：Self-Improvement Ledger Contract

新增运行时 contract：

```json
{
  "contract_version": "phase-g-self-improvement-ledger-v1",
  "overall_status": "ready",
  "record_types": ["learning", "error", "feature_request"],
  "tracked_sources": ["conversation", "error", "user_feedback", "quality_gate", "runtime_contract"],
  "promotion_targets": ["AGENTS.md", "docs", "system_prompt", "best_practice", "skill"],
  "governance_states": ["pending", "in_progress", "resolved", "promoted", "promoted_to_skill", "disabled", "rolled_back"],
  "quality_controls": ["review", "version_history", "duplicate_merge", "rollback", "restore"],
  "runtime_surface_enabled": true
}
```

新增文件：

- `backend/services/self_improvement_ledger_service.py`

修改文件：

- `backend/services/runtime_surface_service.py`
- `backend/services/runtime_contract_snapshot_service.py`
- `tests/agent_framework/test_runtime_surface_service.py`
- `tests/agent_framework/test_runtime_contract_snapshot_service.py`

## 4. Contract 维护约束

- `self_improvement_ledger` 是能力契约，不直接暴露数据库行。
- Runtime Surface 只暴露可消费摘要和稳定枚举。
- 真实统计值后续可以接入 `LearningManager.get_statistics(...)`，但不能让前端直接依赖内部 ORM。
- 新增 record type、promotion target、quality control 时必须同步 snapshot guard 和测试。
- 任何自我改进记录进入治理台前，都必须能追溯来源和治理状态。

## 5. 下一步建议

### G-2：Self-Improvement Ledger Health Summary

把当前 contract 从静态能力描述推进到健康摘要：

- pending learning count
- pending error count
- pending feature request count
- reviewed learning count
- average quality score
- duplicate/conflict count

建议通过独立 service 读取统计，不把数据库会话塞进 `RuntimeSurfaceService` 构造函数。

实施状态：已完成第一刀。

本轮新增：

- `SelfImprovementLedgerService.build_runtime_contract(db=...)` 支持在传入数据库会话时生成 `health_summary`。
- `GET /api/runtime-profile` 会在真实 Health Router 中把当前 `db` 传给 Runtime Surface，使前端治理台可直接消费自我改进健康摘要。
- 为兼容现有测试 stub 和外部调用方，Health Router 增加 `_get_runtime_profile_with_optional_db(...)`，仅当目标 service 支持 `db` 参数时才传入。
- `RuntimeContractSnapshotService` 已把 `self_improvement_ledger.health_summary` 纳入稳定字段守护。

当前 `health_summary` 字段：

```json
{
  "total_learning_count": 0,
  "pending_learning_count": 0,
  "resolved_learning_count": 0,
  "promoted_learning_count": 0,
  "disabled_learning_count": 0,
  "rolled_back_learning_count": 0,
  "reviewed_learning_count": 0,
  "average_learning_quality_score": null,
  "total_error_count": 0,
  "pending_error_count": 0,
  "total_feature_request_count": 0,
  "pending_feature_request_count": 0,
  "attention_items": []
}
```

`overall_status` 语义：

- `ready`：当前没有需要优先处理的 pending learning / error / feature request。
- `attention_required`：存在 pending error、pending learning 或 pending feature request。

### G-3：Self-Improvement Governance Timeline Adapter

把以下事件统一写入 Governance Timeline：

- learning created
- error recorded
- feature request recorded
- learning reviewed
- learning promoted
- learning rollback / restore
- duplicate merged

已有 learnings router 局部写入 timeline，下一步应抽成 adapter seam，避免每个 endpoint 手写事件。

实施状态：已完成第一刀。

本轮新增：

- `backend/services/self_improvement_timeline_service.py`
- `SelfImprovementTimelineService.record_learning_event(...)`
- `get_self_improvement_timeline_service()`
- `tests/agent_framework/test_self_improvement_timeline_service.py`
- `tests/agent_framework/test_learnings_timeline_adapter.py`

当前行为：

- 统一构建 `snapshot_ref`，来源固定为 `learning`。
- 统一把 `learning_id / conversation_id / snapshot_ref` 写入 payload。
- 当 `conversation_id` 存在时，同时写入 run trace 和 audit。
- 当 `conversation_id` 缺失时，只返回 snapshot_ref，不写 trace / audit，保持原 router helper 行为。
- `backend/routers/learnings.py::_record_learning_timeline(...)` 现在只是兼容 wrapper，实际写入逻辑下沉到 service。

后续建议：

- 前端 Governance Timeline 可以继续消费 `source = learning`，不需要关心后端 router 或 service 来源。

### G-3B：Error / Feature Request Timeline Adapter

实施状态：已完成。

本轮新增：

- `SelfImprovementTimelineService.record_error_event(...)`
- `SelfImprovementTimelineService.record_feature_request_event(...)`
- `tests/agent_framework/test_error_feature_timeline_adapter.py`

本轮修改：

- `ErrorCreate / ErrorUpdate` 新增可选 `conversation_id`。
- `FeatureRequestCreate / FeatureRequestUpdate` 新增可选 `conversation_id`。
- `ErrorResponse / FeatureRequestResponse` 新增可选 `snapshot_ref` 和 `timeline_recording`。
- `/api/learnings/errors` 创建错误时写入 `error_recorded`。
- `/api/learnings/errors/{error_id}` 更新错误时写入 `error_updated`。
- `/api/learnings/features` 创建功能请求时写入 `feature_request_recorded`。
- `/api/learnings/{feature_id}` 更新功能请求时写入 `feature_request_updated`。

兼容性：

- 不传 `conversation_id` 时仍会返回 `snapshot_ref`，但不会写 trace / audit。
- 旧响应字段保持不变，新增字段均为可选字段。
- 前端 Governance Timeline 可通过 `source = error` 和 `source = feature_request` 区分自我改进事件来源。

### G-3C：Self-Improvement Timeline Dedupe Key

实施状态：已完成。

本轮新增：

- `SelfImprovementTimelineService` 会为 learning / error / feature request 事件自动生成稳定 `dedupe_key`。
- 默认格式：`{source}:{event_type}:{conversation_id}:{entity_id}`。
- 当 `conversation_id` 缺失时，conversation 段使用 `NA`。
- 调用方显式传入 `payload.dedupe_key` 时优先保留显式值。
- `dedupe_key` 会同时进入 trace payload 和 `timeline_recording` 返回值。

示例：

```text
learning:learning_promoted:321:LRN-1
error:error_recorded:321:ERR-20260516-ABC
feature_request:feature_request_updated:321:FEAT-20260516-XYZ
```

边界说明：

- 本刀只生成和透出 `dedupe_key`。
- 是否基于 `dedupe_key` 做幂等写入，需要下一刀结合业务审计需求决定。

### G-3D：Self-Improvement Timeline Dedupe Write Guard

实施状态：已完成。

本轮新增：

- `SelfImprovementTimelineService` 在写 trace / audit 前，会通过 `trace_service.has_runtime_trace_dedupe_key(...)` 检查同一 `dedupe_key` 是否已经存在。
- 如已存在，返回 `trace_written = false`、`audit_written = false`、`dedupe_source = persisted_trace`。
- 如 trace service 不支持 `has_runtime_trace_dedupe_key(...)`，保持原行为，继续写 trace / audit。
- 如 `conversation_id` 缺失，保持原行为，只返回 `snapshot_ref` 和 `dedupe_key`，不写 trace / audit。

保守启用条件：

- 仅在 `conversation_id` 存在时做幂等查询。
- 仅当当前 trace service 显式提供 `has_runtime_trace_dedupe_key(...)` 时启用。
- 不引入进程内全局集合，避免跨测试或跨实例状态污染。

返回示例：

```json
{
  "trace_written": false,
  "audit_written": false,
  "conversation_id": 321,
  "snapshot_ref": {"source": "error", "event_type": "error_recorded"},
  "dedupe_key": "error:error_recorded:321:ERR-1",
  "dedupe_source": "persisted_trace"
}
```

### G-4：Query Control Plane Design

基于当前 `ExecutionLoopController`、`EmbeddedAgentRuntimeSDK` 和 `AgentHarnessFacade`，整理正式的请求生命周期：

```text
user_input -> context_assembly -> planning -> model_stream -> tool_decision -> tool_execution -> observation -> review -> final_output
```

目标是让主 chat、SDK、external adapter、subagent lane 都能对齐同一套事件语义。

实施状态：已完成第一刀。

本轮新增：

- `backend/services/query_control_plane_service.py`
- `QueryControlPlaneService.build_runtime_contract()`
- `get_query_control_plane_service()`
- `tests/agent_framework/test_query_control_plane_service.py`

Runtime Surface 新增 contract：

```json
{
  "contract_version": "phase-g-query-control-plane-v1",
  "overall_status": "design_ready",
  "lifecycle_stages": [
    "input_received",
    "context_assembly",
    "planning",
    "model_stream",
    "tool_decision",
    "tool_execution",
    "observation",
    "review",
    "final_output"
  ],
  "execution_channels": [
    "main_chat",
    "embedded_sdk",
    "external_adapter",
    "subagent_lane"
  ]
}
```

Contract guard：

- `RuntimeSurfaceService.get_runtime_profile(...)` 已暴露 `query_control_plane`。
- `RuntimeContractSnapshotService` 已守护 `query_control_plane` 的稳定字段。
- 当前 contract count 从 8 增加到 9。

边界说明：

- 本刀只建立控制面 contract，不重写 `chat_service.py`。
- `overall_status = design_ready` 表示生命周期边界已固定，但主 chat、SDK、external adapter、subagent lane 尚未全部接入统一 trace event。
- 后续接线必须逐步做，避免一次性重构主执行链。

下一步建议：

- G-4B：为 Query Control Plane 增加 timeline adapter，先能记录 `input_received / context_assembly / planning` 三个低风险事件。
- G-4C：把 Embedded SDK / ExecutionLoopController 的状态事件映射到 `query_control_plane.required_trace_events`。
- G-4D：再评估主 chat 是否接入同一控制面事件，而不是直接改 chat 主流程。

### G-4B：Query Control Timeline Adapter

实施状态：已完成第一刀。

本轮新增：

- `backend/services/query_control_timeline_service.py`
- `QueryControlTimelineService.record_stage(...)`
- `get_query_control_timeline_service()`
- `tests/agent_framework/test_query_control_timeline_service.py`

当前行为：

- 统一用 `source = query_control` 记录请求生命周期事件。
- 事件类型固定为 `query_control_{stage}`，例如 `query_control_input_received`、`query_control_context_assembly`、`query_control_planning`。
- `stage` 必须来自 `QueryControlPlaneService.build_runtime_contract()["lifecycle_stages"]`。
- `channel` 必须来自 `QueryControlPlaneService.build_runtime_contract()["execution_channels"]`。
- trace / audit payload 统一包含 `channel / stage / query_id / conversation_id / snapshot_ref / dedupe_key`。
- 默认 `dedupe_key` 格式为 `query_control:{channel}:{stage}:{conversation_id}:{query_id}`。
- 当 `conversation_id` 缺失时，conversation 段使用 `NA`，并只返回 `snapshot_ref` 与 `dedupe_key`，不写 trace / audit。
- 当 trace service 支持 `has_runtime_trace_dedupe_key(...)` 且 persisted trace 已存在同 key 时，跳过重复写入并返回 `dedupe_source = persisted_trace`。

边界说明：

- 本刀只新增 adapter seam，不修改 `chat_service.py` 主执行链。
- 当前最适合先接入 `input_received / context_assembly / planning` 这类低风险阶段。
- 后续 Embedded SDK、ExecutionLoopController、external adapter、subagent lane 应优先通过该 adapter 对齐统一生命周期语义。

### G-4C：Embedded SDK Query Lifecycle Mapping

实施状态：已完成第一刀。

本轮新增：

- `backend/services/query_control_event_mapper_service.py`
- `QueryControlEventMapperService.map_embedded_sdk_event(...)`
- `QueryControlEventMapperService.build_record_payload(...)`
- `tests/agent_framework/test_query_control_event_mapper_service.py`

本轮修改：

- `EmbeddedAgentRuntimeSDK` 新增可选 `query_control_db`、`query_control_event_mapper`、`query_control_timeline_service` 注入点。
- SDK `_append_event(...)` 会在保留原事件流后，尝试把可识别事件映射到 Query Control timeline。
- 默认未传 `query_control_db` 时不启用持久 timeline 写入，保持原 in-process SDK 行为。
- Query Control recorder 故障时 SDK fail-open，不阻断 create / execute / approval / resume 主流程，并把失败摘要写入 `run.metadata.query_control_recording_failures`。

当前映射：

```text
run_created -> input_received
execution_loop_step: planning -> planning
execution_loop_step: generating -> model_stream
tool_permission_required -> tool_decision
tool_call_started -> tool_execution
tool_result -> observation
execution_loop_reviewed -> review
execution_loop_done -> final_output
```

边界说明：

- 本刀没有修改 `ExecutionLoopController` 状态机。
- 本刀没有修改 `chat_service.py` 主执行链。
- 映射层只消费现有 SDK 事件，不创建第二套执行语义。
- `build_record_payload(...)` 只保留源事件身份字段，不把完整 event body 写入 query timeline，避免 payload 膨胀。

### G-4E：External Adapter Pilot Query Lifecycle Mapping

实施状态：已完成第一刀。

本轮新增：

- `QueryControlEventMapperService.map_external_adapter_event(...)`
- `FrameworkAdapterRuntimeService` 可选 `query_control_event_mapper` 与 `query_control_timeline_service` 注入点。

当前映射：

```text
framework_adapter_status -> model_stream
framework_adapter_reasoning -> planning
framework_adapter_output -> final_output
framework_adapter_external_error -> final_output
```

当前行为：

- 仅当调用方显式注入 `query_control_timeline_service` 且传入 `db` 时，external pilot 才会写 Query Control timeline。
- 默认 external pilot 行为保持不变，只写原有 framework adapter trace / audit。
- recorder 成功时，返回 `query_control_recordings`。
- recorder 失败时，external pilot fail-open，返回 `query_control_recording_failures`，不影响 pilot `status` 和原有 snapshot。

边界说明：

- 本刀不直接把 LangGraph draft external pilot 接入主 chat。
- 本刀只复用 external pilot 已有事件，不新增外部框架协议。
- `external_adapter` 通道目前只覆盖受控 pilot，不表示所有外部 framework adapter 均已进入生产执行链。

### G-4F：Subagent Lane Query Lifecycle Mapping

实施状态：已完成第一刀。

本轮新增：

- `QueryControlEventMapperService.map_subagent_event(...)`
- `SubagentRuntimeService.record_query_control_events(...)`

本轮修改：

- `EmbeddedAgentRuntimeSDK` 的 Query Control recorder 会先尝试 embedded SDK 映射，未命中时再尝试 subagent lane 映射。
- `delegate_run(...)` 写入父 run 的 `child_run_created` 事件时，可在显式注入 Query Control recorder 后记录 `subagent_lane / input_received`。
- `SubagentRuntimeService` 新增可选 `query_control_event_mapper` 与 `query_control_timeline_service` 注入点。

当前映射：

```text
child_run_created -> input_received
subagent_spawned -> planning
subagent_collected -> observation
subagent_merged -> final_output
```

当前行为：

- SDK delegate 路径沿用 G-4C 的显式 `query_control_db` + `query_control_timeline_service` 注入方式。
- 传统 subagent spawn / collect / merge 协议通过 `SubagentRuntimeService.record_query_control_events(...)` 显式记录。
- 未注入 recorder 或未传 `db` 时不写 Query Control timeline。
- recorder 失败时 fail-open，返回 `failures`，不影响 subagent 协议事件生成。

边界说明：

- 本刀不实现真实并行 child executor。
- 本刀不改 scheduler 主流程，只提供统一 helper，后续 scheduler/orchestrator 可显式调用。
- `subagent_lane` 当前表示 child run / pseudo-subagent 协议对齐 Query Control 生命周期，不代表已经具备完整 fan-out / fan-in 执行器。

### G-4G：Scheduler Fan-out Subagent Query Control Wiring

实施状态：已完成第一刀。

本轮修改：

- `backend/services/chat_service.py`
- `stream_scheduled_orchestrator_events(...)` 在 scheduler fan-out 路径中显式调用 `SubagentRuntimeService.record_query_control_events(...)`。
- 新增 `_get_subagent_runtime_service()`，使 subagent runtime service 入口可测试、可替换。
- 新增 `_record_subagent_query_control_event(...)` 小 helper，避免 scheduler 主流程直接拼 Query Control timeline payload。

当前接线：

```text
child spawn event -> subagent_lane / planning
child collect event -> subagent_lane / observation
scheduler merge completion -> synthetic subagent_merged -> subagent_lane / final_output
```

边界说明：

- 本刀没有改变前端输出 contract，外部仍看到原有 `subagent_spawned`、`subagent_collected`、`scheduler_merged`。
- `subagent_merged` 在 scheduler fan-out 路径中只作为 Query Control 内部记录事件使用，不额外向前端输出。
- recorder fail-open 仍由 `SubagentRuntimeService.record_query_control_events(...)` 负责。
- 本刀不触碰主 chat 的普通对话路径。

### G-4H：Main Chat Core Query Lifecycle Read-Only Mapping Design

实施状态：`G-4H-1` 与 `G-4H-2` 第一刀已完成。

目标：

- 为 `main_chat` 通道补齐 Query Control Plane 的核心执行生命周期映射。
- 先让主 chat 进入统一 runtime 语言，再决定是否接入持久 Query Control timeline。
- 保持第一刀为只读设计，不改变前端 SSE 输出 contract，不重构 chat 主流程。

本轮范围：

- 只覆盖主 chat 的核心执行生命周期：

```text
input_received
planning
model_stream
tool_decision
tool_execution
observation
review
final_output
```

- 只讨论现有主 chat 事件如何映射到统一 lifecycle stage。
- 不在本刀中默认开启 `main_chat` 的 timeline 持久写入。

建议映射：

```text
incoming user chat request -> main_chat / input_received
reasoning -> main_chat / planning
content (streaming body) -> main_chat / model_stream
tool_permission_required -> main_chat / tool_decision
tool_result -> main_chat / observation
execution_progress (completion retry / boundary fallback / completion finalized related review signal) -> main_chat / review
done -> main_chat / final_output
```

映射取舍：

- `tool_result` 第一刀先映射到 `observation`，把它视为工具结果回流后的观察信号，而不是先拆成执行开始与执行结果两段。
- `tool_execution` stage 暂不强行从现有主 chat 事件中补造；后续若补 `tool_call_started` 或等价运行时事件，再提升到更细粒度映射。
- `reasoning` 先作为 `planning`，避免把现有流式 reasoning 直接等同于完整 `review` 或 `model_stream`。

明确不纳入：

- `approval_created`
- `approval_resolved`
- `tool_denied`
- framework adapter 专属事件
- scheduler / subagent lane 相关事件
- 纯治理 trace event
- `capability_profile` / `memory_layers` 这类说明性初始化状态

边界说明：

- 第一刀建议新增 `main_chat` 专用 mapper / helper，不让 `chat_service.py` 直接拼 Query Control payload。
- 第一刀只做映射规则与 helper，可测试、可替换。
- 第一刀不改变前端看到的 `reasoning / content / tool_result / done` 等事件名与事件体。
- 若后续接持久 timeline，必须保持 `opt-in + fail-open`，不能因为治理记录失败阻断主 chat。
- 第二刀再评估审批 / 治理事件是否作为补充通道信号纳入，而不是现在与主执行线混合设计。

本轮实现：

- `backend/services/query_control_event_mapper_service.py`
- 新增 `map_main_chat_event(...)`，把 `main_chat` 核心事件映射到 Query Control lifecycle stage。
- `backend/services/main_chat_query_control_service.py`
- 新增 `MainChatQueryControlService.record_query_control_events(...)`，复用现有 timeline recorder 模式，按 `recordings / failures` 返回结果。
- `backend/services/chat_service.py`
- 新增 `_record_main_chat_query_control_event(...)`，通过 `execution_context.enable_main_chat_query_control_timeline` 控制是否启用 recorder。
- 在 `collect_orchestrator_response(...)` 与 `stream_orchestrator_events(...)` 中，对输入种子事件与后续流式事件进行受控 Query Control 记录。
- 对计划驱动的 handoff / scheduler execution context 显式补 `enable_main_chat_query_control_timeline = True`，普通 chat 路径仍不默认落治理 timeline。

当前接线：

```text
plan-driven main chat input seed -> main_chat / input_received
reasoning -> main_chat / planning
content -> main_chat / model_stream
tool_permission_required -> main_chat / tool_decision
tool_result -> main_chat / observation
execution_progress (selected review phases) -> main_chat / review
done (non approval wait) -> main_chat / final_output
```

当前约束：

- `main_chat` timeline recorder 当前仍是 `opt-in + fail-open`，只在受控 execution context 中启用。
- 普通 chat 请求若没有显式 execution context 开关，不会默认写入 Query Control timeline。
- `approval_created / approval_resolved / tool_denied` 等治理事件仍不并入 `main_chat` 核心执行映射。

G-4H-3：

- `backend/schemas.py`
- `ChatRequest` 已新增类型化的 `execution_context` 专家入口，允许普通 chat 请求显式传入受控运行时上下文。
- 当前 request-level contract 固定字段：

```text
run_id
run_kind
agent_role
agent_id
enable_main_chat_query_control_timeline
```

- request-level `execution_context` 当前采用白名单模型，不接受未知字段，避免普通 chat 接口退化成任意 runtime metadata 注入口。
- `backend/routers/chat.py`
- 普通 `/api/chat` 与 `/api/chat/non-stream` 现已把 request-level `execution_context` 与计划系统生成的 runtime execution context 合并。
- 合并策略为“runtime execution context 优先，请求上下文只做补充”，避免用户手工字段覆盖计划驱动的真实运行时标识。
- 因此，普通 chat 现在也可以通过显式传入：

```json
{
  "execution_context": {
    "run_id": "manual-chat-1",
    "enable_main_chat_query_control_timeline": true
  }
}
```

启用 `main_chat` Query Control timeline recorder；若不传该开关，默认行为不变。

G-4H-4：

- `frontend-vue/src/stores/settings.js`
- 新增本地持久化开关 `enableMainChatRuntimeTrace`，作为聊天页专家模式的前端单一状态源。
- `frontend-vue/src/stores/conversation.js`
- `sendMessage(...)` 与 `regenerateMessage(...)` 现会在该开关启用时，自动向 `/api/chat` 透传类型化 `execution_context`：

```json
{
  "run_id": "manual-chat-<timestamp>",
  "run_kind": "chat",
  "agent_id": "chat-ui-<model>",
  "enable_main_chat_query_control_timeline": true
}
```

- `frontend-vue/src/views/ChatView.vue`
- 聊天页 header 已新增 `Runtime Trace / 专家模式` 轻量开关，并在输入提示区展示“已附加 main_chat runtime trace 上下文”提示。
- 当前策略仍是显式 opt-in；关闭开关时，前端不会向普通 chat 请求附加 `execution_context`。

G-4H-5：

- `frontend-vue/src/components/RuntimeSurfacePanel.vue`
- Runtime Surface 已新增 `Main Chat Trace` 卡片，与聊天页复用同一个 `settingsStore.enableMainChatRuntimeTrace` 状态源。
- 该卡片会展示当前状态、入口类型，并提供统一开关，避免调试入口只散落在 ChatView。
- 当前统一策略：
  - ChatView 负责“就地切换与即时提示”
  - Runtime Surface 负责“全局查看与统一设置”
  - 两者都不会改变默认普通 chat 行为，除非用户显式启用专家开关

G-4H-7：

- `backend/services/runtime_surface_service.py`
- Runtime profile 已新增 `main_chat_trace_overview` contract，用于暴露最近一次 `main_chat` Query Control 记录状态。
- 当前 contract 重点字段：

```text
recording_state
trace_event_count
latest_stage
latest_query_id
latest_summary
latest_timestamp
latest_snapshot_id
reason
```

- 当前 `recording_state` 语义：
  - `recorded`: 已找到最近一次 `main_chat` Query Control trace
  - `no_records`: 已解析到 runtime target，但还没有 `main_chat` Query Control 记录
  - `unavailable`: 当前无法解析 runtime target 或缺少 db / 运行时上下文
- `frontend-vue/src/components/RuntimeSurfacePanel.vue`
- `Main Chat Trace` 卡片已新增“最近写入”摘要与“最近一次 main_chat trace”详情块，能够直接显示最近 `query_id / snapshot_id / stage / timestamp`。
- 因此当前前端已经不只是“开关已开”，还能看到“最近一次是否真的写进去了”。

G-4H-8：

- `backend/services/runtime_surface_service.py`
- `governance_overview` 已新增 `main_chat` 子合同，直接复用 `main_chat_trace_overview` 的最近写入状态与摘要字段。
- `frontend-vue/src/components/RuntimeSurfacePanel.vue`
- `治理总览合同` 现已直接展示 `Main Chat Trace` 概览卡与详情块，不再要求用户必须切到独立卡片才能看到最近写入状态。
- 因此当前 `main_chat` trace 状态已经进入统一治理总览语义：
  - 顶部独立卡片负责“配置与最近一次详情”
  - 治理总览卡负责“run / approval / audit / main_chat”并列概览

G-4H-9：

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- 治理时间线现在会把 `source = query_control` 且 `payload.channel = main_chat` 的 trace 识别为独立 `main_chat` domain。
- 这意味着：
  - `governance_filter=main_chat` 已可直接生效
  - 时间线 domain 筛选、overview cards、route-driven filter 复用现有机制即可覆盖 `main_chat`
- 当前实现保持最小侵入：
  - 不改后端事件格式
  - 不新增新的 trace source
  - 只在前端 domain 识别阶段把 `payload.channel` 提升为一等过滤维度

G-4H-10：

- `backend/services/runtime_surface_service.py`
- `main_chat_trace_overview` 与 `governance_overview.main_chat` 已新增结构化阶段指标：

```text
stage_counts
last_success_stage
last_warning_stage
```

- 当前语义：
  - `stage_counts`: 最近 `main_chat` Query Control trace 的 stage 分布
  - `last_success_stage`: 最近一条非 warning `main_chat` stage
  - `last_warning_stage`: 最近一条 warning `main_chat` stage
- `frontend-vue/src/components/RuntimeSurfacePanel.vue`
- `Main Chat Trace` 独立卡片与 `治理总览合同` 当前都已展示阶段化概览，不再只显示 latest trace。
- 因此当前治理面板已经能同时回答三类问题：
  - 最近一次写到哪一步了
  - 累计各 stage 出现了多少次
  - 最近一次成功阶段 / 最近一次告警阶段分别是什么

G-4H-11：

- `backend/services/runtime_surface_service.py`
- `main_chat_trace_overview` 与 `governance_overview.main_chat` 已新增 `recent_queries`，用于暴露最近 N 次 `query_id` 摘要列表。
- 当前每条 query 摘要最小字段：

```text
query_id
latest_stage
latest_summary
latest_timestamp
latest_snapshot_id
stage_counts
last_success_stage
last_warning_stage
recording_state
```

- `frontend-vue/src/components/RuntimeSurfacePanel.vue`
- `Main Chat Trace` 独立卡片与 `治理总览合同` 都已展示最近 query 列表。
- 因此当前我们已经不只看到“当前 item 的聚合结果”，还能看到最近几次 `main_chat` query 的连续摘要视角。

G-4H-12：

- `frontend-vue/src/components/RuntimeSurfacePanel.vue`
- 最近 `query_id` 摘要列表已升级为可点击 drill-down，点击后可直接跳转到：

```text
/settings?tab=advanced&governance_filter=main_chat&governance_query_id=<query_id>
```

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- 已新增 `governance_query_id` 路由态与过滤链路，可把当前治理时间线收束到单个 `query_id`。
- 当前 `Query 聚焦` 视图会额外展示一个轻量 `Query 摘要` 卡，至少包含：

```text
latestStage
stageCount
warningCount
latestSnapshotId
```

- 因此当前 `main_chat` 已经具备从摘要列表进入 `query_id` 级时间线的最小闭环。

G-4H-13：

- `frontend-vue/src/components/GovernanceTimelinePanel.vue`
- 当前 `query_id` drill-down 已进一步升级为专门的 `Query Detail` 面板，不再只依赖通用时间线列表。
- 当前 `Query Detail` 面板会集中展示：

```text
stageChain
latestSnapshotId
dedupeKeyCount
latestWarningSummary
```

- 因此当前单个 `query_id` 视角已经具备“摘要 + 时间线 + 结构化详情”三层信息，而不是只靠 route 过滤后的事件列表。

G-4H-14：

- `backend/services/runtime_surface_service.py`
- `runtime-profile` 已支持可选 `query_id` 上下文，并新增正式 `main_chat_query_detail` contract。
- 当前后端 contract 重点字段：

```text
query_id
recording_state
stage_chain
dedupe_keys
latest_snapshot_id
latest_warning_summary
latest_stage
event_count
reason
```

- `frontend-vue/src/components/RuntimeSurfacePanel.vue`
- Runtime Surface 当前已优先消费后端 `main_chat_query_detail` contract，而不再只依赖前端临时推导。
- 因此当前 query 级详情已经开始从“前端推导逻辑”收口为“后端正式 contract + 前端展示”模式。
- `main_chat_query_history` 与 `main_chat_query_detail` 已共同构成 `main_chat` query 级 read model 的稳定边界；非 `main_chat` channel 的历史扩展不属于当前 Phase G 收口范围，后续若需要应单独立项。
- H-1 收口决策已同步写入 `docs/architecture/runtime_contracts.md` 与 `docs/architecture/current_architecture.md`，Runtime Core 的正式术语以 `query / run / child_run / scheduler_run / approval / artifact / trace / audit` 为准；其中 `child_display_id` 已被明确记为正式 display field，默认优先等于 `child_run_id`，用于 Runtime Surface、审批对象、query-control payload、adapter timeline 与 server serialization 的统一稳定展示标识。

## 6. 验证

已执行：

```powershell
python -m unittest tests.agent_framework.test_query_control_plane_service tests.agent_framework.test_runtime_contract_snapshot_service tests.agent_framework.test_runtime_surface_service tests.agent_framework.test_health_router -v
```

结果：

- `Ran 33 tests`
- `OK`

本轮补充验证：

```powershell
python -m unittest tests.agent_framework.test_main_chat_query_control_service tests.agent_framework.test_query_control_event_mapper_service tests.agent_framework.test_chat_service.ChatServiceTests tests.agent_framework.test_chat_service.RuntimeTraceTests -v
```

结果：

- `Ran 38 tests`
- `OK`

本轮接口层补充验证：

```powershell
python -m unittest tests.agent_framework.test_main_chat_query_control_service tests.agent_framework.test_chat_service.ChatServiceTests tests.agent_framework.test_chat_service.RuntimeTraceTests tests.agent_framework.test_query_control_event_mapper_service -v
```

结果：

- `Ran 39 tests`
- `OK`

本轮 contract 类型化补充验证：

```powershell
python -m unittest tests.agent_framework.test_schemas_chat_request tests.agent_framework.test_main_chat_query_control_service tests.agent_framework.test_chat_service.ChatServiceTests tests.agent_framework.test_chat_service.RuntimeTraceTests tests.agent_framework.test_query_control_event_mapper_service -v
```

结果：

- `Ran 41 tests`
- `OK`

前端补充验证：

```powershell
cd frontend-vue
npm test -- --run src/stores/__tests__/conversation.test.js src/components/__tests__/ChatView.test.js
```

结果：

- `2` 个测试文件通过
- `23` 个测试通过

前端统一入口补充验证：

```powershell
cd frontend-vue
npm test -- --run src/stores/__tests__/conversation.test.js src/components/__tests__/ChatView.test.js src/components/__tests__/RuntimeSurfacePanel.test.js
```

结果：

- `3` 个测试文件通过
- `49` 个测试通过

后端 trace overview 补充验证：

```powershell
python - <<'PY'
import sys, types, unittest
sys.modules.setdefault('dotenv', types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None))
from tests.agent_framework import test_runtime_surface_service
suite = unittest.defaultTestLoader.loadTestsFromModule(test_runtime_surface_service)
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
PY
```

结果：

- `4` 个测试通过
- `OK`

治理总览联动补充验证：

```powershell
cd frontend-vue
npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js
```

结果：

- `1` 个测试文件通过
- `26` 个测试通过

治理时间线 main_chat 过滤补充验证：

```powershell
cd frontend-vue
npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- `1` 个测试文件通过
- `46` 个测试通过

阶段化概览补充验证：

```powershell
cd frontend-vue
npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js
```

结果：

- `1` 个测试文件通过
- `26` 个测试通过

最近 query 摘要补充验证：

```powershell
cd frontend-vue
npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js
```

结果：

- `1` 个测试文件通过
- `26` 个测试通过

query_id drill-down 补充验证：

```powershell
cd frontend-vue
npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- `2` 个测试文件通过
- `74` 个测试通过

Query Detail 面板补充验证：

```powershell
cd frontend-vue
npm test -- --run src/components/__tests__/GovernanceTimelinePanel.test.js
```

结果：

- `1` 个测试文件通过
- `47` 个测试通过

query detail contract 补充验证：

```powershell
cd frontend-vue
npm test -- --run src/components/__tests__/RuntimeSurfacePanel.test.js
```

结果：

- `1` 个测试文件通过
- `28` 个测试通过
