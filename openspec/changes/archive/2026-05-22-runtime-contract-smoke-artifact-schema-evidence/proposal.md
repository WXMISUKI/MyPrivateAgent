# runtime-contract-smoke-artifact-schema-evidence

## Summary

Runtime Contract Gate now exposes `runtime_contract_artifact_schema`, Snapshot guards it, and degraded governance traces include it. The smoke check still only reports `contract_snapshot_status`, so quality gate artifacts do not directly show whether the Runtime Profile included the artifact schema guard.

This change adds artifact schema evidence fields to the `runtime_profile_contract_snapshot` smoke check.

## Scope

- Add artifact schema status / missing field evidence to `runtime_contract_smoke.py`.
- Add focused runtime smoke tests.
- Update runtime contract docs and roadmap notes.

## Non-Goals

- No new endpoint.
- No Runtime Contract Gate behavior change.
- No frontend change.
