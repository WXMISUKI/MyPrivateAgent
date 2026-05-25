# Design

## Scope

This slice only changes the Governance Timeline read-side summary for `runtime_contract_gate_degraded` payloads. Backend Runtime Contract Gate already normalizes `runtime_contract_summary.sdk_tool_runtime_execution_coverage`.

## Summary Label

`frontend-vue/src/services/governanceFormatting.js` should read:

- `payload.runtime_contract_summary.overall_status`
- `payload.runtime_contract_summary.sdk_tool_runtime_execution_coverage.bridge_smoke`

The formatter should append one compact fragment:

```text
sdk_tool=<covered|missing|unknown>
```

Rules:

- `overall_status = unknown` means `sdk_tool=unknown`.
- `bridge_smoke = true` means `sdk_tool=covered`.
- Missing, malformed, or false SDK tool coverage means `sdk_tool=missing` when status is not unknown.

## Non-Goals

- Do not change SDK direct ToolRuntime execution behavior.
- Do not alter quality gate or Runtime Contract Gate backend normalization.
- Do not change trace fingerprints or dedupe keys.
