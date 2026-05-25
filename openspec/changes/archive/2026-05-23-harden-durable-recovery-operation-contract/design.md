## Overview

本变更把恢复能力从“可探测 checkpoint/cursor”推进到“可审计 operation”。现有 `probe_run_recovery()` 已能说明某个 run 是否具备 descriptor、durable workspace、registry binding 和 resume cursor；但生产排障还需要知道某一次实际恢复入口调用是否尝试过、被什么 gate 阻断、成功是否来自 persisted descriptor reattachment。

设计选择：在 Embedded SDK 内部构建 compact recovery operation record，并把它放进 probe boundary、成功恢复 metadata、fail-closed event payload。该 record 只携带稳定标识和状态证据，不复制 executable continuation。

## Recovery Operation Record

字段：

- `contract_version`: `phase-ii-durable-recovery-operation-v1`
- `operation_id`: 单次尝试 id，用于审计追踪
- `run_id`
- `entrypoint`: `submit_approval.approved` 或 `resume_run.continue_loop`
- `operation_status`: `attempted / recovered / blocked / failed`
- `recovery_reason` 与 `blocked_reason`
- `checkpoint_id` 与 `resume_cursor_id`
- `continuation_ref`: continuation kind、continuation id、descriptor present、binding ids
- `workspace_backend`: compact backend kind / durability / fallback status
- `persistence_posture`
- `worker_ownership`: 明确 `implemented = false`，原因是本切片不实现 lease / cross-instance ownership

## Recording Points

- `probe_run_recovery()` 返回 `recovery_operation_boundary`，让消费者知道当前 SDK 支持哪些 operation evidence，以及 worker lease 仍未实现。
- `_resume_tool_continuation()` 从 persisted descriptor + registry reattachment 成功恢复后，记录 `submit_approval.approved` 的 `recovered` operation。
- `_continue_observing_loop()` 从 persisted descriptor + registry reattachment 成功恢复后，记录 `resume_run.continue_loop` 的 `recovered` operation。
- `_fail_closed_recovery()` 记录 `blocked` operation，并把 operation 放入 `recovery_failed_closed` event payload。

## Non-Goals

- 不实现跨进程 worker lease 或抢占控制。
- 不引入外部队列、分布式锁或 remote executor。
- 不改变 approval immutability、checkpoint、resume cursor、registry reattachment 的现有判断语义。
- 不把 callable、handler、provider client、stream iterator、raw tool result 正文写入 operation payload。

## Validation

- OpenSpec strict validation。
- Focused unittest 覆盖：
  - SDK contract 暴露 recovery operation boundary。
  - 跨进程 registry reattachment 成功时记录 `recovered` operation。
  - fail-closed recovery event 携带 `blocked` operation。
