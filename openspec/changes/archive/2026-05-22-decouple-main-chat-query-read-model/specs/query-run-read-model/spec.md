## ADDED Requirements

### Requirement: main_chat Query Detail Dedicated Endpoint

系统 SHALL 提供 dedicated endpoint，用于读取 `main_chat` 的 query 级治理详情，而不是强依赖 `runtime-profile` 聚合接口。

#### Scenario: Query Detail Read

- **WHEN** 调用方已知 `conversation_id` 与 `query_id`
- **THEN** 系统 SHALL 返回 `main_chat_query_detail` 对应的 query 级 read model
- **AND** 返回字段至少包含 `query_id`、`recording_state`、`stage_chain`、`recent_events`、`latest_stage`、`latest_summary`

#### Scenario: Missing Query

- **WHEN** `query_id` 缺失或未命中
- **THEN** 系统 SHALL 返回可解释的空态 contract
- **AND** 不得返回前端无法区分的模糊空对象

### Requirement: Shared Query Detail Interpretation

前端不同治理面板对同一 `main_chat_query_detail` contract 的解释 SHALL 保持一致。

#### Scenario: Runtime Surface and Governance Timeline

- **WHEN** `RuntimeSurfacePanel` 与 `GovernanceTimelinePanel` 同时消费 query detail
- **THEN** 它们 SHALL 共享同一份 contract normalization 逻辑
- **AND** 不得各自维护一套字段归一化规则

### Requirement: Progressive Decoupling from runtime-profile

`runtime-profile` 可以继续内嵌 `main_chat_query_detail` 以保持兼容，但 dedicated endpoint SHALL 成为 query detail 的主扩展边界。

#### Scenario: Future Query History Expansion

- **WHEN** 后续扩展 `recent_queries` 分页或 query 历史接口
- **THEN** 设计 SHALL 继续沿 dedicated read model 扩展
- **AND** 不得重新把 query 历史复杂度主要推回 `runtime-profile`
