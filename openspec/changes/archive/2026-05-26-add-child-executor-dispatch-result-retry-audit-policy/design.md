## Context

The dispatcher stack now has a clear pre-dispatch and post-dispatch sequence:

- Dispatch contract decides whether real dispatch is allowed.
- Attempt handoff validates sandbox attempt envelope readiness.
- Opt-in dispatcher invokes an injected backend adapter only when explicitly enabled.
- Result handoff normalizes compact backend result and audit references.

The next gap is retry interpretation. Backend result evidence can include `retryable`, `error_code`, or blocked reason, but consumers do not yet have a named policy that says whether the result is retry-audit-ready, terminal, or eligible for a future retry scheduler. Without that policy, future consumers may treat `retryable=true` as a command to schedule retries.

## Goals / Non-Goals

**Goals:**

- Add `build_child_executor_dispatch_result_retry_audit_policy_contract(...)`.
- Classify result handoff into `not_required`, `retryable`, `terminal`, or `blocked`.
- Require idempotency and audit evidence before a retryable result can be marked audit-ready.
- Keep `retry_scheduled = false` and `will_retry = false` everywhere in this slice.
- Add smoke/gate/snapshot coverage for success/no-retry, retryable failure, and terminal failure.

**Non-Goals:**

- Do not execute retries.
- Do not add a retry scheduler, backoff clock, durable queue, or background worker.
- Do not merge child output into parent state.
- Do not turn sandbox backend coverage into production dispatch authorization.

## Decisions

1. Retry audit policy is nested under result handoff.

   Rationale: retryability is a property of the result handoff, not a separate dispatcher execution path.

2. Retryable status requires compact audit and idempotency evidence.

   Rationale: future retry execution must be dedupe-safe and explainable. A bare `retryable=true` flag is not enough.

3. Terminal status is explicit.

   Rationale: malformed payloads, unsafe payloads, policy-denied dispatch, and schema failures should be machine-readable as terminal unless a future policy explicitly reclassifies them.

## Risks / Trade-offs

- [Risk] More nested coverage fields increase fixture churn. -> Mitigation: add only stable summary fields to required snapshot guard.
- [Risk] Retryable evidence may be mistaken for a scheduled retry. -> Mitigation: expose `retry_scheduled = false`, `will_retry = false`, and `scheduler_required = true`.
