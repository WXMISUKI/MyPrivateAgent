# Design

## Scope

This slice only changes the Governance Timeline read-side summary for `runtime_contract_gate_degraded` payloads. Backend Runtime Contract Gate already normalizes `runtime_contract_summary.embedded_sdk_persistence_coverage`.

## Summary Label

`frontend-vue/src/services/governanceFormatting.js` should read:

- `payload.runtime_contract_summary.overall_status`
- `payload.runtime_contract_summary.embedded_sdk_persistence_coverage.persistence_smoke`

The formatter should append one compact fragment:

```text
embedded_persistence=<covered|missing|unknown>
```

Rules:

- `overall_status = unknown` means `embedded_persistence=unknown`.
- `persistence_smoke = true` means `embedded_persistence=covered`.
- Missing, malformed, or false embedded persistence coverage means `embedded_persistence=missing` when status is not unknown.

## Non-Goals

- Do not change Embedded SDK workspace persistence behavior.
- Do not alter quality gate or Runtime Contract Gate backend normalization.
- Do not change trace fingerprints or dedupe keys.
