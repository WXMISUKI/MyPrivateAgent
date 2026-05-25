## Overview

这是一刀最小 retry evidence contract。它只声明 retry policy 和 operation-level retry evidence，不做自动调度或执行循环。这样后续实现失败重试恢复时，可以直接复用同一 operation record，而不是重新发明 retry 事件模型。

## Module Shape

继续使用 `backend/agent_framework/recovery_operations.py`：

- `build_recovery_retry_policy_contract()`
- `is_recovery_reason_retryable(reason)`
- `build_recovery_retry_evidence(...)`
- `_compact_recovery_retry_payload(...)`

`build_recovery_operation_contract()` 增加 `retry_policy`：

- `implemented = false`
- `evidence_supported = true`
- `max_attempts`
- `backoff_strategy`
- `retryable_reasons`
- `terminal_reasons`

`build_recovery_operation_record(...)` 增加可选 `retry` 参数。传入时只保留 compact 字段；未传入时不添加 retry 字段，避免改变已有 operation payload 的默认外观。

## Semantics

- Retry policy 必须显式声明，不依赖调用方隐式循环。
- Retry evidence 必须包含 `attempt_number / max_attempts / previous_operation_id / idempotency_key / status / retryable`。
- `missing_registered_binding / denied / already_resolved / stale_worker_fencing_token / worker_ownership_lost` 属于 terminal reason。
- `transient_workspace_unavailable / workspace_backend_fallback_active / workspace_backend_unavailable` 属于 retryable reason。
- Retry evidence 只表示重试审计/协议状态，不授予执行权限，也不绕过 worker ownership。

## Non-Goals

- No automatic retry scheduler.
- No backoff timer.
- No SDK recovery loop.
- No frontend changes.
- No durable retry queue.

## Validation

- Focused tests for retry policy, retryable/terminal classification, retry evidence compaction, default payload compatibility.
- Existing SDK and Runtime Surface tests to guard compatibility.
- OpenSpec strict validation.
