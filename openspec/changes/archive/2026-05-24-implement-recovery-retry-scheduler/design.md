# Design

## Boundary

The scheduler is opt-in and uses the existing recovery operation contract as the source of truth. It must not treat arbitrary SDK failures as retryable without classifier evidence.

## Required Flow

1. Read retry policy from `recovery_operation_contract.retry_policy`.
2. Classify the previous operation result using existing retry evidence helper.
3. Stop on terminal or exhausted status.
4. Schedule next attempt with bounded backoff.
5. Execute only the approved recovery entrypoint.
6. Record compact retry attempt evidence and dedupe/idempotency keys.

## Failure Mode

Scheduler errors must fail closed for the retry attempt while leaving the original recovery operation audit intact.

## Non-Goals

- No global job queue requirement in the first slice.
- No retry of non-recovery tool execution.
- No retry without operation idempotency evidence.
