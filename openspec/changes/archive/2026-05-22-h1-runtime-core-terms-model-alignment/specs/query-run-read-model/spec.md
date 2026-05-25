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

### Requirement: Shared Contract Interpretation

前端多个治理视图对同一 query detail contract 的解释 SHALL 保持一致，并且其术语应与 Runtime Core 的正式定义对齐。

#### Scenario: Runtime Surface and Governance Timeline

- **WHEN** `RuntimeSurfacePanel` 与 `GovernanceTimelinePanel` 同时消费 `main_chat_query_detail`
- **THEN** 它们 SHALL 共享同一份 contract normalization 逻辑
- **AND** 不得各自维护一套字段解释规则
- **AND** 所使用的 `query / run / child run / approval / trace / audit` 术语 SHALL 与 Runtime Core 术语收口保持一致
