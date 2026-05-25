# Design

## Scope

This slice only changes the Governance Timeline read-side summary for `runtime_contract_gate_degraded` payloads. Backend Runtime Contract Gate already normalizes `runtime_contract_summary.approved_tool_execution_coverage`, and degraded trace payloads already include the normalized coverage.

## Summary Label

`frontend-vue/src/services/governanceFormatting.js` should read:

- `payload.runtime_contract_summary.overall_status`
- `payload.runtime_contract_summary.approved_tool_execution_coverage.bridge_smoke`

The formatter should append one compact fragment:

```text
approved_tool=<covered|missing|unknown>
```

Rules:

- `overall_status = unknown` means `approved_tool=unknown`.
- `bridge_smoke = true` means `approved_tool=covered`.
- Missing, malformed, or false approved tool coverage means `approved_tool=missing` when status is not unknown.

## Non-Goals

- Do not change approved tool continuation execution behavior.
- Do not alter approval replay, lifecycle recovery, or ToolRuntime bridge semantics.
- Do not change Runtime Contract Gate backend normalization, trace fingerprints, or dedupe keys.
