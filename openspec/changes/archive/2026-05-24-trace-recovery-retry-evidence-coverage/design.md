# Design

## Approach
Follow the existing degraded trace pattern for `approval_lifecycle_recovery_coverage`, `checkpoint_resume_cursor_coverage`, approved tool coverage, subagent detail coverage, and artifact schema guard.

1. Extend `backend/routers/health.py` summary normalization with `recovery_retry_evidence_coverage`.
2. Fail closed when retry coverage is missing, malformed, or contradictory.
3. Include normalized coverage in the trace payload that feeds fingerprint generation.
4. Add a compact `recovery_retry=<covered|missing|unknown>` detail label.
5. Verify with focused health router tests that changed retry coverage writes a distinct trace.

## Coverage Shape
The trace payload should preserve:

- `retry_smoke`
- `contract_version`
- `attempt_number`
- `max_attempts`
- `retry_status`
- `retryable`
- `terminal`
- `recovery_reason`
- `idempotency_key_present`

`retry_smoke` is true only for the same bounded exhausted fail-closed evidence accepted by Runtime Contract Gate:

- `contract_version = phase-ii-recovery-retry-protocol-v1`
- `attempt_number = 3`
- `max_attempts = 3`
- `retry_status = exhausted`
- `retryable = true`
- `terminal = true`
- `recovery_reason = workspace_backend_not_durable`
- `idempotency_key_present = true`

## Trace Detail
When the raw summary is absent or not an object, the label is `unknown`.
When normalized retry coverage is present and `retry_smoke = true`, the label is `covered`.
Otherwise, the label is `missing`.
