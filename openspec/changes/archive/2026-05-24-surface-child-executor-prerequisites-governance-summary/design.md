# Design

## Scope

This slice only changes the Governance Timeline read-side summary for `runtime_contract_gate_degraded` payloads. Backend Runtime Contract Gate already normalizes `runtime_contract_summary.child_executor_execution_prerequisites_coverage`.

## Summary Label

`frontend-vue/src/services/governanceFormatting.js` should read:

- `payload.runtime_contract_summary.overall_status`
- `payload.runtime_contract_summary.child_executor_execution_prerequisites_coverage.prerequisites_smoke`

The formatter should append one compact fragment:

```text
child_executor_prerequisites=<covered|missing|unknown>
```

Rules:

- `overall_status = unknown` means `child_executor_prerequisites=unknown`.
- `prerequisites_smoke = true` means `child_executor_prerequisites=covered`.
- Missing, malformed, or false prerequisites coverage means `child_executor_prerequisites=missing` when status is not unknown.

## Non-Goals

- Do not change child executor prerequisites policy or blockers.
- Do not enable real child executor dispatch.
- Do not alter quality gate or Runtime Contract Gate backend normalization.
