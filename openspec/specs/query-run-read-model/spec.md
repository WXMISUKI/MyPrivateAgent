# Query / Run Read Model Specification

## Purpose

本规格定义 `MyPrivateAgent` 当前与 `query / run` 治理视图相关的主规格真源。  
它不负责描述所有 Runtime Core 行为，而是重点约束：

- `query_id` 与 `run_id` 的语义边界
- `main_chat` 的 query 级 read model
- dedicated endpoint 与 `runtime-profile` 的职责分层
- 前端治理视图对 query detail contract 的一致消费方式
- query history / query workspace 的扩展边界

本规格应与以下文档共同阅读：

- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`
- `.specify/memory/constitution.md`
## Requirements
### Requirement: Query and Run Are Distinct First-Class Objects
系统 SHALL 保持 `query` 与 `run` 的语义边界清晰，并将其定义与 `runtime-core-terms-model` 对齐，不得把两者视为同一个对象的不同叫法。

#### Scenario: Governance Lifecycle

- **WHEN** 讨论用户请求从输入到最终输出的完整治理观察生命周期
- **THEN** 系统 SHALL 使用 `query / query_id`
- **AND** 不得把 `run_id` 作为 query 的正式替代主键

#### Scenario: Runtime Execution Instance

- **WHEN** 讨论执行实例、状态机、tool/approval/adapter 的运行实体
- **THEN** 系统 SHALL 使用 `run / run_id`
- **AND** 不得把 `query_id` 退化成执行实例主键

#### Scenario: Query detail is not a run alias

- **WHEN** 任何治理视图展示单个请求的完整生命周期详情
- **THEN** `query_id` SHALL 作为详情主键
- **AND** `run_id` 只能作为关联执行实例字段出现，不能反过来替代 query 语义

### Requirement: main_chat Query Detail Formal Contract

系统 SHALL 为 `main_chat` 提供正式 query 级 read model，而不是长期依赖前端从通用 timeline 临时推导。

#### Scenario: Query Detail Read

- **WHEN** 调用方已知 `conversation_id` 与 `query_id`
- **THEN** 系统 SHALL 返回 `main_chat_query_detail` 对应的 query 级 read model
- **AND** 返回字段至少包含：
  - `query_id`
  - `recording_state`
  - `stage_chain`
  - `recent_events`
  - `latest_stage`
  - `latest_summary`
  - `stage_count`
  - `warning_count`
  - `event_count`
  - `read_model_layer`
  - `source_channel`
  - `identity_kind`

#### Scenario: Missing Query

- **WHEN** `query_id` 缺失或未命中
- **THEN** 系统 SHALL 返回可解释的空态 contract
- **AND** 不得返回前端无法区分的模糊空对象

### Requirement: Dedicated Query Detail Endpoint

系统 SHALL 提供 dedicated endpoint 读取 query 级详情，以避免 `runtime-profile` 持续膨胀。

#### Scenario: Dedicated Endpoint

- **WHEN** 前端或治理面板只需要 `main_chat` 的 query detail
- **THEN** 系统 SHALL 优先允许通过 dedicated endpoint 读取
- **AND** dedicated endpoint SHALL 作为后续 query read model 扩展的主边界

#### Scenario: runtime-profile Compatibility

- **WHEN** 现有面板仍需要通过 `runtime-profile` 获取 query detail
- **THEN** 系统 MAY 继续在 `runtime-profile` 中保留兼容字段
- **BUT** 这不应阻止 dedicated endpoint 成为主扩展路径

### Requirement: Shared Contract Interpretation

前端多个治理视图对同一 query detail contract 的解释 SHALL 保持一致，并且其术语应与 Runtime Core 的正式定义对齐。

#### Scenario: Runtime Surface and Governance Timeline

- **WHEN** `RuntimeSurfacePanel` 与 `GovernanceTimelinePanel` 同时消费 `main_chat_query_detail`
- **THEN** 它们 SHALL 共享同一份 contract normalization 逻辑
- **AND** 不得各自维护一套字段解释规则
- **AND** 所使用的 `query / run / child run / approval / trace / audit` 术语 SHALL 与 Runtime Core 术语收口保持一致

### Requirement: Progressive History Expansion

系统 SHALL 允许后续平滑扩展 query 历史接口，而不破坏现有 query detail 与 recent summaries 边界。

#### Scenario: recent_queries Summary

- **WHEN** 调用方只需要最近若干次 query 摘要
- **THEN** 系统 SHALL 继续通过 `main_chat_trace_overview.recent_queries` 暴露 lightweight summary list
- **AND** 该 list 应保持后向兼容

#### Scenario: Future Pagination

- **WHEN** 后续扩展 `recent_queries` 分页或更完整历史接口
- **THEN** 设计 SHALL 继续沿 query read model 扩展
- **AND** 不得把 query 历史复杂度主要重新推回前端本地推导

### Requirement: Query History Read Model

系统 SHALL 为 `main_chat` 的 query summary history 保留 dedicated read model 扩展边界。

#### Scenario: History Browse Beyond Recent Summaries

- **WHEN** 调用方需要读取超出 `recent_queries` 范围的 query 历史摘要
- **THEN** 系统 SHALL 提供独立于 `recent_queries` 与 `main_chat_query_detail` 的 history 读取边界
- **AND** 不得要求前端从通用 timeline 本地重建长历史列表

#### Scenario: Pagination-Friendly Evolution

- **WHEN** 后续实现 dedicated query history endpoint
- **THEN** contract SHALL 支持分页或 cursor 扩展
- **AND** history item 字段应尽量与现有 `recent_queries` 做兼容映射

### Requirement: subagent_lane Recent Summary Trial

系统 SHALL 只为 `subagent_lane` 提供 `recent summary` 层的轻量试点，并且 MUST NOT 在该试点内越级进入更深层 query 模型。

#### Scenario: Summary Trial

- **WHEN** 团队对 `subagent_lane` 开启 query 模式轻量试点
- **THEN** 系统 SHALL 只提供 `recent summary` 所需的最小字段
- **AND** 不得在同一试点中同时引入 detail/history/workspace 能力

#### Scenario: Field Scope

- **WHEN** 系统为 `subagent_lane` 聚合 recent summaries
- **THEN** 字段 SHALL 优先限制在：
  - `query_id`
  - `latest_stage`
  - `latest_summary`
  - `latest_timestamp`
  - `recording_state`

### Requirement: No Premature Promotion Beyond Summary

在 dedicated detail contract 稳定前，系统 MUST NOT 将 `subagent_lane` 推进到 `query detail / query history / query workspace`。

#### Scenario: Trial Guardrail

- **WHEN** 试点仍处于 `recent summary` 阶段
- **THEN** 系统 SHALL 阻止把最近事件列表、stage chain、dedupe keys、history pagination 或 workspace 交互一并纳入
- **AND** 团队应将这些能力留到后续单独 change 评估

### Requirement: Query Workspace Boundary

系统 MUST 明确区分 `recent summary`、`query detail`、`query history`、`query workspace` 四层能力，不得把它们混成单一概念。

#### Scenario: Recent Summary

- **WHEN** 调用方只需要最近若干次 query 的轻摘要
- **THEN** 系统 SHALL 使用 `recent summary` 层
- **AND** 不得让该层承担长历史分页职责

#### Scenario: Query Detail

- **WHEN** 调用方需要某个 `query_id` 的完整生命周期详情
- **THEN** 系统 SHALL 使用 `query detail` 层
- **AND** 不得让该层承担跨多个 query 的历史浏览职责

#### Scenario: Query History

- **WHEN** 调用方需要浏览跨多个 query 的历史摘要
- **THEN** 系统 SHALL 使用 `query history` 层
- **AND** 不得要求前端从通用 timeline 本地重建长历史列表

#### Scenario: Query Workspace

- **WHEN** 调用方需要在同一治理工作区内联动 history、detail、focus、search、page restore
- **THEN** 系统 SHALL 将其视为 `query workspace` 层
- **AND** 该层默认依赖下层 read model，而不是重新定义 query 语义

### Requirement: Promotion Rules from main_chat

系统 MUST 明确哪些 `main_chat` 能力可推广为通用 query 模式，哪些当前仍保留为 `main_chat` 专用。

#### Scenario: Directly Promotable Layers

- **WHEN** 某项能力属于 `recent summary`、`query detail` 或 `query history` 的 contract/read model 分层
- **THEN** 系统 MAY 将其视为可推广候选模式

#### Scenario: main_chat-specific Workspace

- **WHEN** 某项能力高度依赖 `main_chat` 当前前端体验与使用路径
- **THEN** 系统 SHALL 暂时将其保留为 `main_chat` 专用
- **AND** 不得在未做边界评估前直接扩展到其他 channel

### Requirement: Preconditions for Multi-Channel Expansion

系统在将 query history/workspace 扩展到其他 channel 之前，MUST 先满足统一前置条件。

#### Scenario: Expansion Readiness

- **WHEN** 某个非 `main_chat` channel 想复用 query detail 或 query history 模式
- **THEN** 它 SHALL 先具备稳定 `query_id`
- **AND** 已具备 dedicated query detail contract
- **AND** 已具备统一 lifecycle stage 映射
- **AND** 不需要前端从通用 timeline 本地重建 query 模型

### Requirement: Channel Promotion Order

系统在把 query 能力从 `main_chat` 推广到其他 channel 时，MUST 遵循由浅到深的扩展顺序。

#### Scenario: Promotion Sequence

- **WHEN** 团队准备把 query 模式推广到新的 channel
- **THEN** 系统 SHALL 优先评估 `recent summary`
- **AND** 只有在 dedicated query detail contract 稳定后，才评估 `query detail`
- **AND** `query history / query workspace` 默认应最后评估，不得直接跳级扩展

### Requirement: subagent_lane Current Boundary

当前 `subagent_lane` MUST 只被视为 `recent summary / query detail` 的候选评估对象，不得直接视为完整 query history/workspace 的实现候选。

#### Scenario: subagent_lane Promotion

- **WHEN** 团队评估 `subagent_lane`
- **THEN** 系统 SHALL 先判断其是否满足 `recent summary` 前置条件
- **AND** 在 dedicated detail contract 稳定前，不得直接扩展到 `query history / query workspace`

#### Scenario: subagent_lane Readiness Checklist

- **WHEN** 团队准备让 `subagent_lane` 进入 `recent summary`
- **THEN** 系统 SHALL 先确认其已具备稳定 `query_id`
- **AND** 已具备 latest-stage 归纳语义
- **AND** 前端不需要从原始 timeline 本地猜测 query 身份

#### Scenario: subagent_lane Current Evaluation Result

- **WHEN** 基于当前实现评估 `subagent_lane`
- **THEN** 系统 SHALL 将其视为已通过 `recent summary` readiness
- **AND** 在 dedicated detail contract 稳定前，仍不得进入 `query detail / query history / query workspace`

### Requirement: external_adapter Current Boundary

当前 `external_adapter` MUST 只被视为 `recent summary / query detail` 的候选评估对象，不得直接视为完整 query history/workspace 的实现候选。

#### Scenario: external_adapter Promotion

- **WHEN** 团队评估 `external_adapter`
- **THEN** 系统 SHALL 先判断其是否满足 `recent summary` 前置条件
- **AND** 在 dedicated detail contract 稳定前，不得直接扩展到 `query history / query workspace`

#### Scenario: external_adapter Readiness Checklist

- **WHEN** 团队准备让 `external_adapter` 进入 `recent summary`
- **THEN** 系统 SHALL 先确认其已具备稳定 `query_id`
- **AND** output / error / reasoning 已可稳定压缩成 summary
- **AND** 前端不需要追加 framework-specific 解释逻辑才能消费

#### Scenario: external_adapter Current Evaluation Result

- **WHEN** 基于当前实现评估 `external_adapter`
- **THEN** 系统 SHALL 将其视为已通过 `recent summary` readiness
- **AND** 在 dedicated detail contract 稳定前，仍不得进入 `query detail / query history / query workspace`

### Requirement: external_adapter Recent Summary Read Model

The system MUST provide `external_adapter_recent_summary` as a dedicated recent summary read model built from Query Control trace events for the `external_adapter` channel.

#### Scenario: Runtime Surface exposes recorded external adapter summary

- **WHEN** Query Control trace events exist with `channel = external_adapter`
- **THEN** Runtime Surface MUST expose `external_adapter_recent_summary`
- **AND** the contract MUST include `contract_version`, `connected`, `recording_state`, `items`, `latest_query_id`, `latest_stage`, `latest_summary`, `latest_timestamp`, `total_items`, and `reason`
- **AND** each item MUST use the shared recent summary field set: `query_id`, `latest_stage`, `latest_summary`, `latest_timestamp`, and `recording_state`

#### Scenario: No external adapter records remain a safe summary state

- **WHEN** no Query Control trace events exist for `external_adapter`
- **THEN** the contract MUST return `recording_state = no_records`
- **AND** it MUST NOT synthesize query identity from framework-specific payloads

#### Scenario: external_adapter summary does not imply deeper read models

- **WHEN** `external_adapter_recent_summary` is recorded
- **THEN** the system MUST NOT expose external adapter query detail, query history, or query workspace behavior as part of this change
