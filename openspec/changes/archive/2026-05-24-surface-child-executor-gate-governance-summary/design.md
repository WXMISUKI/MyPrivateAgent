# Design

## Scope

This slice only changes the Governance Timeline read-side summary for `runtime_contract_gate_degraded` payloads. Backend Runtime Contract Gate already normalizes `runtime_contract_summary.child_executor_promotion_gate_coverage`.

## Summary Label

`frontend-vue/src/services/governanceFormatting.js` should read:

- `payload.runtime_contract_summary.overall_status`
- `payload.runtime_contract_summary.child_executor_promotion_gate_coverage.gate_smoke`

The formatter should append one compact fragment:

```text
child_executor_gate=<covered|missing|unknown>
```

Rules:

- `overall_status = unknown` means `child_executor_gate=unknown`.
- `gate_smoke = true` means `child_executor_gate=covered`.
- Missing, malformed, or false child executor promotion gate coverage means `child_executor_gate=missing` when status is not unknown.

## Non-Goals

- Do not change child executor promotion gate policy or blockers.
- Do not enable real child executor dispatch.
- Do not alter quality gate or Runtime Contract Gate backend normalization.
- Do not change trace fingerprints or dedupe keys.
