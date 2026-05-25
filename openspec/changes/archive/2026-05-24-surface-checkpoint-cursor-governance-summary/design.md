# Design

## Scope

This slice only changes the Governance Timeline read-side summary for `runtime_contract_gate_degraded` payloads. Backend Runtime Contract Gate already normalizes `runtime_contract_summary.checkpoint_resume_cursor_coverage`, and degraded trace detail already exposes `checkpoint_cursor=<covered|missing|unknown>`.

## Summary Label

`frontend-vue/src/services/governanceFormatting.js` should read:

- `payload.runtime_contract_summary.overall_status`
- `payload.runtime_contract_summary.checkpoint_resume_cursor_coverage.cursor_smoke`

The formatter should append one compact fragment:

```text
checkpoint_cursor=<covered|missing|unknown>
```

Rules:

- `overall_status = unknown` means `checkpoint_cursor=unknown`.
- `cursor_smoke = true` means `checkpoint_cursor=covered`.
- Missing, malformed, or false cursor coverage means `checkpoint_cursor=missing` when status is not unknown.

## Non-Goals

- Do not change SDK recovery probe behavior.
- Do not alter checkpoint or resume cursor backend contracts.
- Do not change Runtime Contract Gate backend normalization, trace fingerprints, or dedupe keys.
