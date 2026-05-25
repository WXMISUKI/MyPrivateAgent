# quality-gate-artifact-schema-guard

## Summary

`quality_gate_report.py` now builds `contract_checks` and `runtime_contract_summary` from runtime smoke output, but the artifact does not explicitly state whether the generated summary still contains the stable nested fields expected by Runtime Contract Gate and Runtime Contract Snapshot. A future report refactor could keep checks while silently dropping a summary coverage field.

This change adds a small machine-readable `runtime_contract_artifact_schema` guard to quality gate runtime contract steps.

## Scope

- Add schema guard metadata to runtime contract quality gate steps.
- Render the schema guard in Markdown summary.
- Add focused backend tests.
- Update runtime contract docs and roadmap notes.

## Non-Goals

- No new runtime smoke check.
- No change to Runtime Contract Gate API.
- No frontend behavior change.
