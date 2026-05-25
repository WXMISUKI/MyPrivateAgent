# runtime-contract-trace-lifecycle-detail

## Summary

`runtime_contract_gate_degraded` trace payload now carries normalized `approval_lifecycle_recovery_coverage`, but the trace `detail` remains only `failed_check_count=<n>`. Backend governance consumers that display compact trace detail cannot see whether approval lifecycle recovery alignment is covered without expanding the payload.

This change adds a compact approval lifecycle recovery signal to the backend trace detail.

## Scope

- Add `approval_lifecycle=<covered|missing|unknown>` to `runtime_contract_gate_degraded` trace detail.
- Keep the signal derived from normalized `runtime_contract_summary.approval_lifecycle_recovery_coverage`.
- Add focused health router tests.
- Update runtime contract docs and manual test notes.

## Non-Goals

- No frontend change.
- No new API endpoint.
- No change to trace payload shape beyond existing fields.
