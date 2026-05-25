## Why

Recovery retry evidence is now classifiable and visible in `run_recovery`, but the real SDK recovery entrypoints still only record first-attempt operation evidence. This leaves retry readiness observable in tests and helpers, but not yet grounded in the recovery gates that production consumers will inspect.

This change makes the next recovery slice concrete: record compact retry-attempt evidence from the SDK recovery gates when a retry attempt is explicitly requested, while keeping automatic retry execution out of scope.

## What Changes

- Add SDK recovery gate support for explicit retry attempt evidence on `submit_approval(..., approved)` and `resume_run(..., continue_loop=True)` blocked recovery paths.
- Reuse the existing `build_recovery_retry_evidence(...)` classifier and recovery operation record shape instead of introducing a parallel retry event model.
- Ensure retry attempt evidence is compact, bounded, and non-executable.
- Ensure `run_recovery.recovery_audit_summary` can consume retry evidence produced by real SDK recovery gates.
- Update docs and focused tests to record the next ordered hardening directions:
  - first: recovery gate retry attempt evidence
  - next: child executor promotion gate quality/smoke coverage
  - next: parent merge state surface section hardening
- Non-goals:
  - No automatic retry scheduler.
  - No background retry worker.
  - No database vendor lock semantics.
  - No true child executor execution path.
  - No new retry event table or parallel retry timeline model.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `recovery-retry-protocol`: recovery retry attempts must be recordable by SDK recovery gates as compact operation evidence.
- `durable-recovery-operation-contract`: recovery operation records produced by SDK recovery gates must preserve retry attempt evidence when explicitly supplied.
- `runtime-surface-recovery-operation-read-model`: `run_recovery` must expose retry evidence produced by SDK recovery gates through existing operation history and audit summary fields.
- `recovery-audit-hardening`: recovery audit summaries must treat SDK-gate retry evidence the same as helper-built operation evidence.

## Impact

- Backend code:
  - `backend/agent_framework/sdk.py`
  - `backend/agent_framework/recovery_operations.py`
  - runtime recovery read-model builders if normalization gaps appear
- Tests:
  - focused Embedded SDK recovery tests
  - recovery retry protocol / audit summary tests as needed
- Docs/specs:
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
  - modified OpenSpec capabilities listed above

