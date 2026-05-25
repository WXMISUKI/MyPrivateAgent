# runtime-contract-approval-lifecycle-summary

## Summary

`runtime_contract_smoke.py` already emits `approval_lifecycle_recovery_alignment`, proving replayed approvals, ignored reverse submissions, and resolved recovery reason alignment. The Quality Gate `runtime_contract_summary` still only exposes the older `approval_replay_coverage` payload sample, so downstream Runtime Contract Gate and Snapshot consumers cannot read lifecycle/recovery alignment as a first-class summary field.

This change promotes approval lifecycle recovery alignment into the backend runtime contract summary.

## Scope

- Add `approval_lifecycle_recovery_coverage` to quality gate runtime contract summary.
- Normalize and expose the coverage through `RuntimeContractGateService`.
- Guard the new summary field through `RuntimeContractSnapshotService` and artifact schema required fields.
- Update focused backend tests and runtime contract docs.

## Non-Goals

- No approval state-machine behavior change.
- No frontend change.
- No database migration.
