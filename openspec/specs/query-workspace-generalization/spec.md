# Query Workspace Generalization Specification

## Purpose

本规格定义 `MyPrivateAgent` 中与 **query workspace 通用化** 相关的长期真源。  
它不替代 `query-run-read-model`，而是在其之上回答：

- 什么能力属于 `query workspace`
- 哪些能力当前可以从 `main_chat` 提升为通用模式
- 哪些能力当前仍必须保持 channel-specific
- 多 channel 扩展时应遵循什么顺序与前置条件

本规格应与以下文档共同阅读：

- `openspec/specs/query-run-read-model/spec.md`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`
- `.specify/memory/constitution.md`

## Requirements

### Requirement: Query Workspace Depends on Read Model Layers

系统 SHALL 将 `query workspace` 视为建立在 `recent summary / query detail / query history` 之上的交互层，而不是重新定义 query 语义的独立模型。

#### Scenario: Workspace Composition

- **WHEN** 系统提供 query workspace
- **THEN** 它 SHALL 依赖现有 read model 层
- **AND** 不得绕过 read model 直接从原始 timeline 重建主语义

### Requirement: main_chat as Canonical Baseline

当前 `main_chat` SHALL 作为通用化判断的基准线，因为它是唯一完整实现 query workspace 能力的 channel。

#### Scenario: Baseline Selection

- **WHEN** 团队讨论 query workspace 通用化
- **THEN** 系统 SHALL 以 `main_chat` 当前实现作为 canonical baseline
- **AND** 不得以尚未成熟的 channel 替代其作为基准

### Requirement: Promotion by Layer, Not by Product Shell

系统在推广 query 能力时，SHALL 按层逐步推进，而不是直接复制某个 channel 的产品壳。

#### Scenario: Layered Promotion

- **WHEN** 团队准备把 query 能力推广到新的 channel
- **THEN** 系统 SHALL 先评估 `recent summary`
- **AND** 只有在 dedicated detail contract 稳定后，才评估 `query detail`
- **AND** `query history / query workspace` 默认应最后评估

### Requirement: Channel-Specific Guardrail

系统 SHALL 在高层边界未明确前，阻止把 `main_chat` 的专项交互体验直接外推到其他 channel。

#### Scenario: Guardrail

- **WHEN** 某个 channel 仅通过了 `recent summary` readiness
- **THEN** 系统 SHALL 阻止其直接进入 `query history / query workspace`
- **AND** 团队应单独立项评估更深层能力

### Requirement: subagent_lane Current Promotion Level

当前 `subagent_lane` SHALL 被视为已具备 `recent summary` 候选资格，但仍不进入更深层 query 模式。

#### Scenario: subagent_lane Current State

- **WHEN** 团队评估 `subagent_lane`
- **THEN** 系统 SHALL 将其视为 `recent summary` 试点候选
- **AND** 在 dedicated detail contract 稳定前，不得进入 `query detail / query history / query workspace`

### Requirement: external_adapter Current Promotion Level

当前 `external_adapter` SHALL 被视为已具备 `recent summary` 候选资格，但仍不进入更深层 query 模式。

#### Scenario: external_adapter Current State

- **WHEN** 团队评估 `external_adapter`
- **THEN** 系统 SHALL 将其视为 `recent summary` 试点候选
- **AND** 在 dedicated detail contract 稳定前，不得进入 `query detail / query history / query workspace`

### Requirement: Canonical Stop Condition for main_chat Expansion

当 `main_chat` 已形成完整 query workspace 雏形后，系统 SHALL 优先转向边界收口，而不是继续默认深挖局部体验。

#### Scenario: Stop Condition

- **WHEN** `main_chat` 已具备 recent summary、query detail、query history、workspace 雏形
- **THEN** 团队 SHALL 优先回到高层边界判断
- **AND** 只有在存在明确价值时，才继续做局部体验增强

### Requirement: Phase I Exit Gate

当团队进入 `Phase I` 后，系统 SHALL 明确什么时候允许恢复新的 channel 实现，什么时候应继续停留在规格/架构层。

#### Scenario: Resume Implementation

- **WHEN** 同时满足以下条件：
  - 高层真源稳定
  - channel promotion gate 有正式记录
  - recent summary 抽象判断已有明确当前结论
  - 下一步实现目标从该 channel 当前允许的最浅层开始
  - 本次实现明确列出不会越级推进的非目标
- **THEN** 团队 MAY 恢复新的 channel 级实现
- **AND** 恢复时应优先从最浅层、最小试点开始
- **AND** 不得在同一 change 中顺手推广到更深层 query 能力

#### Scenario: Stay in Spec Layer

- **WHEN** 存在以下任一情况：
  - 新增 channel 的推广顺序还在摇摆
  - canonical spec 之间仍有冲突
  - 团队对 channel-specific / generic 的边界还没统一
  - channel promotion gate 尚未记录当前层级与下一允许动作
  - 下一步实现会同时触碰 detail/history/workspace 多层能力
- **THEN** 团队 SHALL 继续停留在规格/架构层
- **AND** 不得默认恢复新的 channel 实现

### Requirement: Query Workspace Generalization MUST Use Promotion Records

The system SHALL use channel promotion records as the gate between high-level query workspace generalization and channel-specific implementation.

#### Scenario: Generalization stays at boundary layer

- **WHEN** Phase I high-level truth sources are stable
- **AND** a channel lacks a promotion record for the desired implementation layer
- **THEN** the team MUST continue with specification, architecture, or readiness-check work
- **AND** it MUST NOT resume channel-specific implementation by default

#### Scenario: Implementation resumes from the shallowest eligible layer

- **WHEN** a promotion record allows channel-specific implementation
- **THEN** the implementation MUST begin at the recorded target layer
- **AND** it MUST preserve explicit non-goals for deeper layers
- **AND** it MUST NOT expand from recent summary into detail, history, or workspace in the same change unless the record explicitly allows each layer

### Requirement: external_adapter Recent Summary MUST Not Promote Workspace

The query workspace generalization layer MUST treat `external_adapter_recent_summary` as a shallow pilot and not as a query workspace promotion.

#### Scenario: external_adapter stays below query detail

- **WHEN** external adapter recent summary is recorded
- **THEN** query workspace generalization MUST continue to classify `external_adapter` below `query_detail`
- **AND** it MUST require a separate OpenSpec change before external adapter query detail, query history, or query workspace can be implemented

### Requirement: Phase I Exit Line MUST Prefer Boundary Closure Over Channel Parity

The query workspace generalization phase SHALL close when promotion boundaries are stable, even if non-`main_chat` channels have not reached full workspace parity.

#### Scenario: Phase I exits without channel parity

- **WHEN** `main_chat` is the canonical workspace baseline
- **AND** `subagent_lane` and `external_adapter` each have explicit blocked deeper layers
- **AND** recent summary abstraction has a recorded current decision
- **THEN** Phase I MAY be closed
- **AND** the team MUST NOT require every channel to reach query workspace before moving to Phase II

#### Scenario: Phase II becomes default next phase

- **WHEN** Phase I is closed
- **THEN** the default next project planning frame MUST move to Phase II runtime-core implementation and delivery-surface slimming
- **AND** new channel workspace implementation MUST require a future promotion decision change
