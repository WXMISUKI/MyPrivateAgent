## ADDED Requirements

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
