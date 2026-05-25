# runtime-contract-summary-nested-snapshot

## Summary

`runtime_contract_summary.subagent_lane_query_detail_coverage` is now produced by smoke, quality gate, Runtime Contract Gate, degraded traces, and Governance Timeline formatting. The remaining backend gap is the snapshot guard: `RuntimeContractSnapshotService` currently treats `runtime_contract_summary` as one stable field, so a future profile refactor could silently drop the nested coverage object without degrading the snapshot.

This change hardens the backend snapshot contract by making key `runtime_contract_summary` nested fields explicit stable paths.

## Scope

- Backend contract snapshot guard only.
- Focused tests for runtime contract snapshot degradation and healthy shape.
- Runtime contract docs / roadmap notes.

## Non-Goals

- No new smoke check.
- No frontend behavior change.
- No database migration.
