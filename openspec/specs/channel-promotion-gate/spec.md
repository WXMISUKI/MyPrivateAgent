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

### Requirement: Promotion Record MUST Precede Implementation Resume

The system SHALL require a canonical promotion record before any channel resumes implementation for a deeper query read-model layer.

#### Scenario: Resume decision is recorded

- **WHEN** the team decides to resume implementation for a channel query capability
- **THEN** the promotion record MUST include channel, current layer, target layer, readiness evidence, blockers, decision, next allowed action, and explicit non-goals
- **AND** the target layer MUST be the shallowest eligible layer for that channel
- **AND** implementation MUST NOT include deeper query layers than the recorded target layer

#### Scenario: Missing record blocks implementation

- **WHEN** a channel implementation would add recent summary, query detail, query history, or query workspace behavior
- **AND** no canonical promotion record exists for that target layer
- **THEN** the next allowed action MUST be a spec, architecture, or readiness-check slice
- **AND** the implementation MUST NOT proceed by copying the `main_chat` product shell

### Requirement: Current Channel Promotion Decisions MUST Be Canonical

The system SHALL preserve the current promotion decisions for `main_chat`, `subagent_lane`, and `external_adapter` as canonical Phase I records.

#### Scenario: main_chat remains canonical baseline

- **WHEN** the team evaluates query workspace generalization
- **THEN** the promotion record MUST treat `main_chat` as the canonical `query_workspace` baseline
- **AND** further `main_chat` work MUST be justified as boundary clarification or explicit value, not default local expansion

#### Scenario: subagent_lane blocks deeper promotion by default

- **WHEN** the team evaluates `subagent_lane`
- **THEN** the promotion record MUST treat its current allowed layer as no deeper than its recorded dedicated detail capability
- **AND** query history or query workspace promotion MUST require a separate decision
- **AND** the non-goals MUST block copying `main_chat` history or workspace behavior into `subagent_lane`

#### Scenario: external_adapter remains spec-only until explicitly resumed

- **WHEN** the team evaluates `external_adapter`
- **THEN** the promotion record MUST treat it as a `recent summary` candidate with implementation paused by default
- **AND** the next allowed action MUST remain a recorded resume decision or readiness-check slice unless implementation is explicitly approved
- **AND** it MUST NOT advance to query detail, query history, or query workspace without first landing real recent summary evidence

### Requirement: Promotion Records MUST Preserve Shared Recent Summary Boundaries

The system SHALL preserve the current recent summary abstraction decision while keeping channel-specific builders.

#### Scenario: Shared fields are recorded without generic assembler

- **WHEN** a channel is evaluated for `recent summary`
- **THEN** the promotion record MUST identify the shared field set as `query_id`, `latest_stage`, `latest_summary`, `latest_timestamp`, and `recording_state`
- **AND** optional fields MAY include `latest_snapshot_id`, `last_success_stage`, and `last_warning_stage`
- **AND** the record MUST NOT require a generic recent summary assembler before a third real channel sample exists

### Requirement: external_adapter Resume Decision MUST Target Recent Summary Only

The channel promotion gate MUST record that `external_adapter` implementation may resume only for the `recent_summary` layer until a separate decision promotes it further.

#### Scenario: Recent summary implementation is allowed

- **WHEN** `external_adapter_recent_summary` is implemented from Query Control trace evidence
- **THEN** the promotion gate MAY report `recent_summary_status = recorded`
- **AND** `external_adapter` MUST remain blocked for `query_detail`, `query_history`, and `query_workspace`

#### Scenario: Deeper layers remain blocked

- **WHEN** `external_adapter` recent summary evidence exists
- **THEN** the promotion gate MUST NOT treat it as a dedicated detail contract
- **AND** it MUST keep `ready_for_detail = false` until a separate detail readiness decision exists
