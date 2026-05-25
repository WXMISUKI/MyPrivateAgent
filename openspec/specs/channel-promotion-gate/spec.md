# Channel Promotion Gate Specification

## Purpose

本规格定义 `MyPrivateAgent` 中 **channel 从 readiness 到 recent summary / query detail / query history / query workspace 的推广门槛**。  
它不替代 `query-run-read-model` 或 `query-workspace-generalization`，而是回答：

- 一个 channel 进入下一层 query 能力之前必须满足什么
- 什么时候必须停止继续推进
- 如何避免因为局部 momentum 直接越级扩展

本规格应与以下文档共同阅读：

- `openspec/specs/query-run-read-model/spec.md`
- `openspec/specs/query-workspace-generalization/spec.md`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`

## Requirements

### Requirement: Promotion Gate by Layer

系统 SHALL 按层推进 channel 的 query 能力，不得跳级扩展。

#### Scenario: Layer Order

- **WHEN** 团队评估某个 channel 的 query 推广
- **THEN** 系统 SHALL 按顺序判断：
  1. readiness
  2. `recent summary`
  3. `query detail`
  4. `query history`
  5. `query workspace`
- **AND** 不得因为某层局部实现顺手，就跳过中间层

### Requirement: Readiness Checklist

系统在允许某个 channel 进入下一层前，SHALL 先完成正式 checklist 判断。

#### Scenario: Readiness Before Summary

- **WHEN** 某个 channel 想进入 `recent summary`
- **THEN** 系统 SHALL 至少确认：
  - 稳定 `query_id`
  - latest-stage 归纳语义
  - 可读 summary
  - 前端不需要本地猜 query 身份

#### Scenario: Readiness Before Detail

- **WHEN** 某个 channel 想进入 `query detail`
- **THEN** 系统 SHALL 至少确认：
  - dedicated detail contract
  - 稳定 stage chain 或等价 lifecycle 明细
  - 单 query 视角与执行日志视角分离

### Requirement: Stop Condition for Over-Promotion

系统 SHALL 在尚未满足 readiness 时，明确阻止继续推进更深层能力。

#### Scenario: Over-Promotion Block

- **WHEN** 某个 channel 仅通过了 `recent summary` readiness
- **THEN** 系统 SHALL 阻止其直接进入 `query history / query workspace`
- **AND** 团队应单独立项评估更深层能力

### Requirement: Canonical Evaluation Record

每次 channel 推广判断，SHALL 有正式记录，而不是只存在于对话中。

#### Scenario: Evaluation Record

- **WHEN** 团队完成某个 channel 的 readiness 评估
- **THEN** 系统 SHALL 将结果写入 canonical spec、roadmap 或正式 change
- **AND** 后续讨论应优先引用该记录

### Requirement: Current Reference Samples

当前 `subagent_lane` 与 `external_adapter` SHALL 作为 promotion gate 模板样例。

#### Scenario: subagent_lane Sample

- **WHEN** 团队需要一个通过 `recent summary` readiness 的内部样例
- **THEN** 系统 SHALL 优先参考 `subagent_lane`

#### Scenario: external_adapter Sample

- **WHEN** 团队需要一个通过 `recent summary` readiness 但默认不立即推进实现的样例
- **THEN** 系统 SHALL 优先参考 `external_adapter`

### Requirement: Implementation Resume Decision MUST Be Recorded

系统 SHALL 在恢复任何 channel 级实现前记录 implementation resume decision，避免 channel promotion 只存在于对话或局部 momentum 中。

#### Scenario: Resume decision allows implementation

- **WHEN** 团队决定恢复某个 channel 的实现
- **THEN** promotion record SHALL include channel, current layer, target layer, readiness evidence, blockers, decision, next allowed action, and explicit non-goals
- **AND** decision SHALL identify the shallowest eligible target layer
- **AND** implementation SHALL NOT include deeper query layers than the recorded target layer

#### Scenario: Resume decision blocks implementation

- **WHEN** readiness evidence is incomplete or blockers remain
- **THEN** promotion record SHALL set decision to blocked or spec_only
- **AND** next allowed action SHALL be a spec, architecture, or readiness-check slice rather than a new channel feature implementation
