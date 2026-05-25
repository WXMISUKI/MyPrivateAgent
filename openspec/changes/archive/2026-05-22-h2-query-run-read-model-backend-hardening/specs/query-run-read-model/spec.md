## MODIFIED Requirements

### Requirement: Query and Run Are Distinct First-Class Objects
系统 SHALL 保持 `query` 与 `run` 的语义边界清晰，不得把两者视为同一个对象的不同叫法。

#### Scenario: Governance Lifecycle

- **WHEN** 讨论用户请求从输入到最终输出的完整治理观察生命周期
- **THEN** 系统 SHALL 使用 `query / query_id`
- **AND** 不得把 `run_id` 作为 query 的正式替代主键

#### Scenario: Runtime Execution Instance

- **WHEN** 讨论执行实例、状态机、tool/approval/adapter 的运行实体
- **THEN** 系统 SHALL 使用 `run / run_id`
- **AND** 不得把 `query_id` 退化成执行实例主键

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
