## Why

`runtime_contract_smoke.py` currently emits `recovery_retry_evidence.ok = false` for an exhausted retry attempt whose recovery reason is `workspace_backend_not_durable`. The retry classifier correctly reports `retryable = false`, while the smoke and quality-gate summary still expect exhausted evidence to be retryable.

This creates a quality gate failure even though the current canonical retry policy says exhausted status only proves terminal retry evidence and idempotency preservation, not that every exhausted reason must be retryable.

## What Changes

- Align the recovery retry evidence smoke with the classifier contract.
- Treat exhausted retry evidence as covered when it preserves attempt bounds, terminal state, recovery reason, and idempotency key.
- Keep terminal/non-retryable reasons from being scheduled automatically.
- Update Quality Gate and Runtime Contract Gate normalization to match the same semantics.
- Sync runtime docs and canonical spec language where needed.

## Capabilities

### Modified Capabilities

- `recovery-retry-protocol`: Clarifies that smoke coverage may use a fail-closed non-retryable recovery reason as long as it proves terminal/exhausted compact evidence.
- `runtime-contract-trace-recovery-retry-evidence`: Keeps degraded trace coverage tied to normalized `retry_smoke`.

## Impact

- Affected backend paths: `backend/scripts/runtime_contract_smoke.py`, `backend/scripts/quality_gate_report.py`, `backend/services/runtime_contract_gate_service.py`.
- Affected docs/specs: `openspec/specs/recovery-retry-protocol/spec.md`, `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`.
- Non-goals: no automatic retry scheduler changes, no retrying non-retryable blockers, no worker ownership bypass, no new recovery entrypoint.
