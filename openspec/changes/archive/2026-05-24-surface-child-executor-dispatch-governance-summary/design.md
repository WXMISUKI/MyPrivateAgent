# Design

## Scope

This slice only changes the Governance Timeline read-side summary for `runtime_contract_gate_degraded` payloads. Backend Runtime Contract Gate already normalizes `runtime_contract_summary.child_executor_dispatch_coverage`.

## Summary Label

`frontend-vue/src/services/governanceFormatting.js` should read:

- `payload.runtime_contract_summary.overall_status`
- `payload.runtime_contract_summary.child_executor_dispatch_coverage.dispatch_smoke`

The formatter should append:

```text
child_executor_dispatch=<covered|missing|unknown>
```

Rules:

- `overall_status = unknown` means `child_executor_dispatch=unknown`.
- `dispatch_smoke = true` means `child_executor_dispatch=covered`.
- Missing, malformed, or false dispatch coverage means `child_executor_dispatch=missing` when status is not unknown.

## Non-Goals

- Do not change dispatch readiness.
- Do not change `will_dispatch` semantics.
- Do not start workers or mutate child runs.
