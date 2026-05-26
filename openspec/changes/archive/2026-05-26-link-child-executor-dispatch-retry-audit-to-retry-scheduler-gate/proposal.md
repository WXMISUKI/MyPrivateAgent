# Link Child Executor Dispatch Retry Audit To Retry Scheduler Gate

## Summary

Add a side-effect-free handoff gate between child executor dispatch retry audit evidence and the existing opt-in recovery retry scheduler posture.

The change does not schedule retries, start workers, enable background retry execution, merge child results, or change SDK defaults. It makes the missing boundary machine-readable: a retryable child executor dispatch result may be audit-ready, but it is not scheduler-ready unless scheduler binding, idempotency, audit, and production/default constraints are explicit.

## Motivation

Child executor dispatch now has:

- sandbox dispatch-ready opt-in contract evidence
- dispatcher result handoff evidence
- retry audit posture for success, retryable, terminal, and blocked results

The remaining gap is that `retry_policy_status = retryable` can still be misread as retry scheduling authorization. A dedicated retry scheduler handoff gate keeps the retry audit layer separate from scheduler execution.

## Goals

- Expose a machine-readable `child_executor_dispatch_retry_scheduler_handoff` contract.
- Preserve default blocked posture and `will_schedule_retry = false`.
- Prove retryable child dispatch failures can be recognized without scheduling retry work.
- Fail closed when idempotency, audit evidence, retry scheduler binding, or retryable policy evidence is missing.
- Add runtime smoke, Quality Gate, Runtime Contract Gate, Snapshot, and docs coverage.

## Non-Goals

- Do not enable automatic retry scheduling.
- Do not start a background scheduler.
- Do not invoke `RecoveryRetryScheduler` for child executor dispatch retries by default.
- Do not start child executor workers or sandbox runtimes.
- Do not execute parent merge or recovery retry.
- Do not change API endpoints or SDK default behavior.
