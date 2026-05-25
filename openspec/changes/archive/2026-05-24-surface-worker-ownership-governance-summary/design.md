# Design

## Scope

This slice only changes the Governance Timeline read-side summary for `runtime_contract_gate_degraded` payloads. Backend Runtime Contract Gate already normalizes `runtime_contract_summary.worker_ownership_store_mode_coverage`.

## Summary Label

`frontend-vue/src/services/governanceFormatting.js` should read:

- `payload.runtime_contract_summary.overall_status`
- `payload.runtime_contract_summary.worker_ownership_store_mode_coverage.mode_smoke`

The formatter should append one compact fragment:

```text
worker_ownership=<covered|missing|unknown>
```

Rules:

- `overall_status = unknown` means `worker_ownership=unknown`.
- `mode_smoke = true` means `worker_ownership=covered`.
- Missing, malformed, or false worker ownership store mode coverage means `worker_ownership=missing` when status is not unknown.

## Non-Goals

- Do not change worker ownership store mode, lease, fencing, or recovery enforcement behavior.
- Do not alter quality gate or Runtime Contract Gate backend normalization.
- Do not change trace fingerprints or dedupe keys.
