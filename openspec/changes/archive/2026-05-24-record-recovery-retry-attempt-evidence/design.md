## Overview

This slice turns retry evidence from a reusable classifier into evidence emitted by real SDK recovery gates. The implementation should stay deliberately narrow: only explicit caller-provided retry metadata is recorded; the SDK must not start a retry loop on its own.

The work follows the current recovery contract boundary:

- recovery attempts remain `recovery_operation` records
- retry details live under the existing compact `retry` field
- `run_recovery.recovery_audit_summary` remains the read-side consumer
- trace writing remains opt-in and fail-open

## Next Direction Backlog

1. `record-recovery-retry-attempt-evidence`
   - Record explicit retry attempt evidence at SDK recovery gates.
   - Verify Runtime Surface recovery audit summary consumes the evidence.
   - Do not implement scheduling or automatic retry loops.

2. `gate-child-executor-promotion-quality`
   - Add quality-gate/smoke coverage for the already exposed child executor promotion gate.
   - Verify blocked vs allowed evidence is fail-closed and summarized in runtime contract summary.
   - Do not promote `delegate_run(...)` into a real executor yet.

3. `harden-parent-merge-state-sections`
   - Strengthen parent merge state surface sections and summary invariants.
   - Keep the existing `merged_sections` shape as the source of truth.
   - Do not add new UI-only merge interpretations.

## Contract Shape

SDK recovery gates should accept optional retry attempt metadata in a small, explicit shape:

- `attempt_number`
- `previous_operation_id`
- `idempotency_key`
- optional `max_attempts`

The SDK should pass this through `build_recovery_retry_evidence(...)` with the actual blocked recovery reason. The resulting payload is attached to the existing recovery operation record as `retry`.

If no retry metadata is supplied, current behavior must remain unchanged and operation records may omit `retry`.

## Error And Safety Behavior

- Retry evidence construction must not execute recovery by itself.
- Terminal reasons remain terminal.
- Exhausted retry evidence remains terminal and fail-closed.
- Non-retryable unknown reasons should not become automatic retries.
- Existing blocked recovery exceptions should still surface as they do today.
- Retry evidence must not contain handler/callable/provider/iterator internals.

## Testing Strategy

Focused tests should cover:

- `resume_run(..., continue_loop=True)` fail-closed path records retry evidence when retry metadata is supplied.
- `submit_approval(..., approved)` fail-closed path records retry evidence when retry metadata is supplied.
- `run_recovery.recovery_audit_summary` reports latest retry status and terminal reason from SDK-produced evidence.
- Existing recovery paths without retry metadata remain compatible.

