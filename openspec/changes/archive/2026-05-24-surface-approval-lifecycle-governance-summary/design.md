# Design

## Scope

This slice only changes the Governance Timeline read-side summary for `runtime_contract_gate_degraded` payloads. Backend Runtime Contract Gate already normalizes `runtime_contract_summary.approval_lifecycle_recovery_coverage`, and degraded trace detail already exposes `approval_lifecycle=<covered|missing|unknown>`.

## Summary Label

`frontend-vue/src/services/governanceFormatting.js` should read:

- `payload.runtime_contract_summary.overall_status`
- `payload.runtime_contract_summary.approval_lifecycle_recovery_coverage.alignment_smoke`

The formatter should append one compact fragment:

```text
approval_lifecycle=<covered|missing|unknown>
```

Rules:

- `overall_status = unknown` means `approval_lifecycle=unknown`.
- `alignment_smoke = true` means `approval_lifecycle=covered`.
- Missing, malformed, or false lifecycle coverage means `approval_lifecycle=missing` when status is not unknown.

## Non-Goals

- Do not change SDK approval lifecycle recovery behavior.
- Do not alter approval replay or ignored/replayed reason validation.
- Do not change Runtime Contract Gate backend normalization, trace fingerprints, or dedupe keys.
