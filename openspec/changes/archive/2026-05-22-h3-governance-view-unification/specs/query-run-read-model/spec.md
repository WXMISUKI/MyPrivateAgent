## MODIFIED Requirements

### Requirement: Shared Contract Interpretation

前端多个治理视图对同一 query detail contract 的解释 SHALL 保持一致，并且其术语应与 Runtime Core 的正式定义对齐。

#### Scenario: Runtime Surface and Governance Timeline

- **WHEN** `RuntimeSurfacePanel` 与 `GovernanceTimelinePanel` 同时消费 `main_chat_query_detail`
- **THEN** 它们 SHALL 共享同一份 contract normalization 逻辑
- **AND** 不得各自维护一套字段解释规则
- **AND** 所使用的 `query / run / child run / approval / trace / audit` 术语 SHALL 与 Runtime Core 术语收口保持一致
- **AND** route-driven focus、snapshot focus 与 stage focus 的语义 SHALL 在两个治理视图中保持一致
