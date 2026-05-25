## Overview

这是一刀 opt-in trace writer。它与 `SdkApprovalLifecycleTimelineService`、`QueryControlTimelineService` 的思路一致：服务可被 SDK、Runtime Surface 或后续治理任务显式调用，但默认不改变现有 recovery 执行路径。

## Module Shape

新增 `backend/services/recovery_audit_timeline_service.py`：

- `RECOVERY_AUDIT_TRACE_SOURCE = "recovery_audit"`
- `RECOVERY_AUDIT_TRACE_EVENT_TYPE = "recovery_operation_recorded"`
- `RecoveryAuditTimelineService`
- `get_recovery_audit_timeline_service(db=None)`

`RecoveryAuditTimelineService.record_operation(...)` 参数：

- `operation`
- `user_id=None`
- `conversation_id=None`
- `run_id=None`
- `db=None`

## Payload Shape

Trace payload 至少包含：

- `contract_version = phase-ii-recovery-audit-trace-v1`
- `source = recovery_audit`
- `operation_id`
- `run_id`
- `entrypoint`
- `operation_status`
- `recovery_reason`
- `blocked_reason`
- `dedupe_key`
- `retry_status`
- `ownership_implemented`
- `ownership_status`

不复制 callable、handler、provider client、active stream iterator，也不复制完整 operation history。

## Dedupe

dedupe key:

`recovery_audit:<run_id>:<operation_id>`

如果 operation id 缺失，回退到：

`recovery_audit:<run_id>:<entrypoint>:<operation_status>:<recovery_reason>`

命中 `has_runtime_trace_dedupe_key(...)` 时返回：

- `trace_written = false`
- `dedupe_source = persisted_trace`
- `dedupe_key`

## Non-Goals

- No automatic SDK integration.
- No audit table write.
- No retry execution.
- No worker lease validation.
- No frontend change.

## Validation

- Focused unit tests for payload compaction, trace append, dedupe skip, trace service unavailable。
- Existing recovery-focused tests if needed。
- OpenSpec strict validation。
