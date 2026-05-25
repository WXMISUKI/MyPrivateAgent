# implement-recovery-retry-scheduler

## Why

Recovery retry currently has policy and compact attempt evidence, but no automatic retry execution or scheduler. Production recovery needs a controlled scheduler that respects idempotency, terminal reasons, max attempts, backoff, and auditability.

## What Changes

- Add an opt-in recovery retry scheduler.
- Reuse `recovery_operation_contract.retry_policy` and `build_recovery_retry_evidence(...)`.
- Record retry attempts through existing recovery operation history and audit trace patterns.
- Add runtime contract smoke/quality gate evidence.

## Impact

- 收口对象：backend recovery scheduler service, SDK recovery gate integration, recovery audit, runtime contract smoke, quality gate docs/specs.
- 非目标：不新增第二套 retry event model；不默认开启自动 retry；不重试 terminal recovery reasons。
