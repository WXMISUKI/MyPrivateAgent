## Overview

这是一刀 opt-in SDK recovery gate。它不改变默认恢复行为，也不自动 claim lease；调用方需要显式提供 ownership store 和 ownership evidence，SDK 才会在恢复执行前验证 lease/fencing。

## Module Shape

修改 `backend/agent_framework/sdk.py`：

- `EmbeddedAgentRuntimeSDK.__init__(..., worker_ownership_store=None)`
- `_validate_recovery_worker_ownership(...)`
- `_record_recovery_operation(..., worker_ownership=None)`
- `_build_recovery_operation_record(..., worker_ownership=None)`

恢复路径：

- `_resume_tool_continuation(...)` 在 registry reattach 成功后，若 descriptor 或 recovery metadata 中提供 `worker_ownership` evidence，则先校验。
- `_continue_observing_loop(...)` 同理。
- 校验失败时调用 `_fail_closed_recovery(...)`，但 recovery reason 使用 ownership gate reason，例如 `stale_worker_fencing_token` 或 `worker_ownership_lost`。

## Semantics

- 未配置 worker ownership store：默认不启用 gate，operation 仍输出 `worker_ownership.implemented=false`。
- 配置 store 但未提供 ownership evidence：不启用 gate，保持兼容。
- 配置 store 且提供 ownership evidence：必须校验 `run_id / worker_id / lease_id / fencing_token`。
- gate 通过：operation record 携带 validated ownership evidence。
- gate 失败：operation record `operation_status = blocked`，`recovery_reason` 使用 ownership reason，且恢复执行不得继续。

## Non-Goals

- No SQL lease store.
- No automatic claim/heartbeat.
- No distributed lock.
- No retry execution.
- No frontend change.

## Validation

- Focused SDK tests for valid ownership evidence, stale fencing fail-closed, default compatibility.
- Existing SDK/Runtime Surface tests to guard recovery behavior.
- OpenSpec strict validation.
