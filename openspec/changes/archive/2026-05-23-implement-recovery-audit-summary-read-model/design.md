## Overview

这是一刀 read-side aggregation。它不新增 SDK event，不写 trace，不调度 retry，只把已有 `recovery_operation_history` 归纳成治理面可以直接消费的 summary。

## Module Shape

在 `backend/services/runtime_surface_builders.py` 的 `RuntimeRecoveryContractBuilder` 中新增：

- `build_recovery_audit_summary(operations)`
- `_count_by_field(operations, field)`
- `_latest_terminal_reason(operations)`

`build_run_recovery_contract(...)` 在规范化 `latest_recovery_operation` 和 `recovery_operation_history` 后，新增：

- `recovery_audit_summary`

## Summary Fields

`recovery_audit_summary` 至少包含：

- `contract_version`
- `operation_count`
- `latest_status`
- `latest_entrypoint`
- `latest_reason`
- `status_counts`
- `entrypoint_counts`
- `reason_counts`
- `retry_count`
- `retry_status_counts`
- `latest_retry_status`
- `ownership_implemented`
- `latest_ownership_status`
- `terminal`
- `latest_terminal_reason`
- `authorization_source = false`

## Semantics

- Summary 必须从 compact operation evidence 派生。
- `blocked / failed` 被视为 terminal candidate；如果 operation 的 retry status 是 `terminal / exhausted`，也视为 terminal。
- ownership 字段只作为 audit evidence，不能作为 lease validation 真源。
- 无 operation history 时也输出稳定 empty summary，避免前端自行判断字段缺失。

## Non-Goals

- No governance trace writer.
- No audit dedupe adapter.
- No retry execution.
- No worker lease validation.
- No frontend changes.

## Validation

- Focused builder tests for empty summary、recovered summary、retry/terminal/failure distribution、ownership evidence summary。
- Existing SDK and Runtime Surface tests to guard compatibility。
- OpenSpec strict validation。
