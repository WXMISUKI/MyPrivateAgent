# Design

## Boundary

This change defines production readiness for automatic retry scheduling. It does not implement a background scheduler, durable queue, or default retry execution.

## Current State

The current runtime already has:

- retry policy and retry evidence classifier
- compact retry evidence on explicit recovery attempts
- `RecoveryRetryScheduler` as an explicit opt-in seam
- recovery operation history and audit summary
- optional `RecoveryAuditTimelineService`
- opt-in worker ownership validation

The missing production decision is whether automatic retry may run without a caller manually invoking the scheduler.

## Production Gate

Automatic retry may be enabled only when all gate sections are ready:

- durable scheduling state
- deterministic idempotency/dedupe key
- monotonic backoff schedule
- terminal reason classifier
- worker ownership validation or explicit ownership bypass denial
- recovery audit timeline integration
- supported recovery entrypoint allowlist
- bounded attempt limit
- fail-closed execution decision

If any section is missing, the runtime remains in explicit opt-in mode.

## Data Shape

The production gate should be machine-readable:

- `contract_version`
- `overall_status`
- `automatic_retry_enabled_by_default`
- `sections`
- `missing_sections`
- `next_allowed_action`
- `non_goals`

## Failure Mode

The scheduler must fail closed before executing retry when production gate evidence is missing. Audit writing remains fail-open only after the recovery operation evidence is safely recorded; audit failure must not create duplicate retry execution.
