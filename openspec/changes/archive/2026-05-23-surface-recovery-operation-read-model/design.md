## Overview

上一刀的 SDK operation evidence 已经存在于 run metadata 与 `recovery_failed_closed` event 中，但 Runtime Surface 的 `run_recovery` 仍只暴露 checkpoint、resume cursor、continuation 和 entrypoints。为了让治理消费方稳定读取恢复操作审计，本变更把 operation evidence 提升到 read model 层。

## Read Model Shape

`run_recovery` 新增：

- `recovery_operation_boundary`: SDK 支持的 auditable entrypoints 与 worker ownership boundary。
- `latest_recovery_operation`: 最近一次恢复操作证据；无记录时为空对象。
- `recovery_operation_history`: 最多保留最近 20 条 compact operation evidence。
- `recovery_operation_count`: history 条数。

operation evidence 只保留 compact 字段：

- `contract_version`
- `operation_id`
- `run_id`
- `entrypoint`
- `operation_status`
- `recovery_reason`
- `blocked_reason`
- `checkpoint_id`
- `resume_cursor_id`
- `continuation_ref`
- `workspace_backend`
- `persistence_posture`
- `worker_ownership`
- `recorded_at`

## Data Flow

1. SDK 在 `probe_run_recovery()` 中把 run metadata 里的 `latest_recovery_operation / recovery_operations` 放入 probe result。
2. `RuntimeRecoveryContractBuilder` 从 probe 归一化这些字段。
3. `RuntimeSurfaceService.get_run_recovery()` 继续复用 builder，不直接拼字段。

## Non-Goals

- 不新增 UI。
- 不改 quality gate summary。
- 不实现 worker lease 或 cross-instance ownership。
- 不复制 executable callable、provider client、handler 或 active stream iterator。

## Validation

- Focused Runtime Surface builder/service tests。
- Focused SDK recovery test，确保 probe result 暴露 operation evidence。
- OpenSpec strict validation。
