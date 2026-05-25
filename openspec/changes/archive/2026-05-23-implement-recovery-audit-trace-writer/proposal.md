## Why

`run_recovery.recovery_audit_summary` 已经能从 operation history 派生治理摘要，但 `recovery-audit-hardening` 还要求 recovery operation 与治理 trace 能建立 compact、幂等的关联。当前如果治理台想审计某次 recovery operation，只能读取 SDK metadata 或 Runtime Surface read model，缺少可复用的 trace writer。

本变更收口对象：新增最小 `RecoveryAuditTimelineService`，把一条 compact recovery operation evidence 写入 Runtime Trace，并用 operation-level dedupe key 保证重复写入不会污染治理时间线。

非目标：本变更不自动接入 SDK 恢复主流程、不写 audit 表、不改变 recovery operation record shape、不新增前端展示、不实现 retry execution 或 worker lease validation。

## What Changes

- 新增 `backend/services/recovery_audit_timeline_service.py`。
- 支持 `record_operation(...)`，从 compact recovery operation 构建 trace payload。
- payload 包含 `operation_id / run_id / entrypoint / operation_status / recovery_reason / dedupe_key`，并保留 retry/ownership 的紧凑摘要。
- 命中相同 dedupe key 时跳过 trace 写入并返回 machine-readable dedupe result。
- 补 focused tests 覆盖写入、去重、无 trace service、非可执行 payload。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `recovery-audit-hardening`: trace correlation 与 idempotent audit writer 从规格推进到最小实现。

## Impact

- Affected code: `backend/services/recovery_audit_timeline_service.py`。
- Affected tests: 新增 focused recovery audit timeline service tests。
- Affected docs: `docs/architecture/runtime_contracts.md`、`docs/roadmap/next_phase_hardening.md`、`docs/test_manual.md`。
