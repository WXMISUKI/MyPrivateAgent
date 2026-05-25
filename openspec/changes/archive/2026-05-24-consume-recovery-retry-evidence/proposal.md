## Why

Recovery operation records already allow compact retry evidence, and the recovery audit summary already counts retry fields when present. The remaining gap is that retry classification and read-model consumption are not explicit enough to serve as a stable production-hardening step before automatic retry execution.

## What Changes

- Add a focused retry evidence builder/classifier for recovery reasons.
- Ensure retry evidence can classify retryable, terminal, and exhausted states without adding a parallel event model.
- Extend recovery audit summary/read model tests so retry status and terminal reason are observable from operation history.
- Keep retry execution disabled for this slice.
- Non-goals:
  - Do not add background retry scheduling.
  - Do not automatically re-run recovery entrypoints.
  - Do not bypass worker ownership validation.
  - Do not introduce a new retry table, trace event model, or frontend-only retry derivation.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `recovery-retry-protocol`: clarify that retry evidence MUST be classifiable and consumable before retry execution exists.
- `recovery-audit-hardening`: require audit summary to expose retry status distribution and latest terminal retry reason from compact operation evidence.
- `runtime-surface-recovery-operation-read-model`: require `run_recovery` to preserve retry summary evidence without exposing executable internals.

## Impact

- Backend recovery operation evidence:
  - `backend/agent_framework/recovery_operations.py`
- Runtime Surface recovery read model:
  - `backend/services/runtime_surface_builders.py`
  - `backend/services/runtime_surface_service.py`
- Tests:
  - `tests/agent_framework/test_recovery_retry_protocol.py`
  - `tests/agent_framework/test_recovery_audit_summary.py`
  - `tests/agent_framework/test_runtime_surface_service.py`
- Docs:
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`

