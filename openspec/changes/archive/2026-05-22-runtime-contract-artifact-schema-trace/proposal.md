# runtime-contract-artifact-schema-trace

## Summary

Runtime Contract Gate now exposes `runtime_contract_artifact_schema`, and Runtime Contract Snapshot guards it. The remaining trace gap is that degraded runtime contract governance traces still carry only `runtime_contract_summary`; artifact schema guard changes are not part of the trace payload or dedupe fingerprint.

This change adds normalized artifact schema guard data to `runtime_contract_gate_degraded` trace payloads and fingerprints.

## Scope

- Normalize `runtime_contract_artifact_schema` in `backend/routers/health.py`.
- Include it in degraded trace payload and fingerprint.
- Add focused health router tests.
- Update docs and roadmap notes.

## Non-Goals

- No frontend formatting change in this slice.
- No quality gate report changes.
- No database migration.
