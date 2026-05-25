# runtime-contract-gate-artifact-schema-surface

## Summary

`quality_gate_report.py` now emits `runtime_contract_artifact_schema`, but Runtime Contract Gate does not expose it through the backend runtime profile contract. Consumers still need to open the raw quality gate artifact to know whether `runtime_contract_summary` itself satisfied the schema guard.

This change surfaces the artifact schema guard from `RuntimeContractGateService`.

## Scope

- Read and normalize `runtime_contract_artifact_schema` from quality gate report steps.
- Return a fail-closed schema guard when the report is missing, malformed, or old.
- Add focused backend tests.
- Update runtime contract docs and roadmap notes.

## Non-Goals

- No frontend rendering change in this slice.
- No new smoke check.
- No database migration.
