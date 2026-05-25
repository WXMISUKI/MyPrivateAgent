# runtime-contract-approval-lifecycle-coverage-strictness

## Summary

`approval_lifecycle_recovery_coverage` is now exposed through Quality Gate, Runtime Contract Gate, Snapshot, and degraded trace payloads. The next hardening step is to make the coverage flag fail-closed: consumers must not trust `alignment_smoke = true` when the replayed / ignored / recovery reason fields disagree with the approval lifecycle contract.

## Scope

- Recompute approval lifecycle coverage from its machine-readable fields during normalization.
- Apply the same strict normalization in Runtime Contract Gate and health degraded trace payloads.
- Add focused tests for malformed or inconsistent coverage objects.
- Update runtime contract docs and roadmap notes.

## Non-Goals

- No new contract fields.
- No approval state-machine behavior change.
- No frontend change.
