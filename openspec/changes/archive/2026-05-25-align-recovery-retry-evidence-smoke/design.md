## Design

### Retry Evidence Semantics

The classifier remains the source of truth:

- retryable transient reasons before max attempts produce `status = retryable`, `retryable = true`, `terminal = false`
- terminal reasons produce `status = terminal`, `retryable = false`, `terminal = true`
- any attempt at or above `max_attempts` produces `status = exhausted`, `terminal = true`, and preserves the idempotency key

The smoke check for explicit retry evidence should not require `retryable = true` when it deliberately exercises a fail-closed recovery path with `workspace_backend_not_durable`.

### Quality Gate Semantics

`recovery_retry_evidence_coverage.retry_smoke` should be true when:

- the smoke check succeeded
- contract version, attempt number, max attempts, status, terminal flag, recovery reason, and idempotency key evidence are present and coherent
- `retry.status = exhausted`
- `terminal = true`

It should not require `retryable = true` for the fail-closed smoke sample.

### Non-Goals

- Do not add automatic retry scheduling.
- Do not add `workspace_backend_not_durable` to retryable reasons.
- Do not change `RecoveryRetryScheduler` execution behavior.
