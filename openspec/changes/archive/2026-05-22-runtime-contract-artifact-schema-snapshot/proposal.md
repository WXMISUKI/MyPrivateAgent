# runtime-contract-artifact-schema-snapshot

## Summary

Runtime Contract Gate now exposes `runtime_contract_artifact_schema`, but Runtime Contract Snapshot still does not guard that field. This leaves one remaining gap in the backend contract chain: Runtime Profile could drop the schema guard after Gate exposure and snapshot would remain healthy.

This change adds snapshot-level stable field protection for `runtime_contract_gate.runtime_contract_artifact_schema`.

## Scope

- Extend `RuntimeContractSnapshotService` required paths for `runtime_contract_gate`.
- Add focused snapshot tests.
- Update runtime contract docs and roadmap notes.

## Non-Goals

- No changes to quality gate artifact generation.
- No frontend behavior change.
- No database migration.
