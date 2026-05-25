## ADDED Requirements

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
