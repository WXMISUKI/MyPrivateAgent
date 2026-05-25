# Design

## Scope

This slice only changes the Governance Timeline read-side summary for `runtime_contract_gate_degraded` payloads. Backend trace payloads already include normalized `runtime_contract_summary.recovery_retry_evidence_coverage`, and backend trace detail already includes a compact retry label.

## Summary Label

`frontend-vue/src/services/governanceFormatting.js` should read:

- `payload.runtime_contract_summary.overall_status`
- `payload.runtime_contract_summary.recovery_retry_evidence_coverage.retry_smoke`

The formatter should append one compact fragment:

```text
recovery_retry=<covered|missing|unknown>
```

Rules:

- `overall_status = unknown` means `recovery_retry=unknown`.
- `retry_smoke = true` means `recovery_retry=covered`.
- Missing, malformed, or false retry coverage means `recovery_retry=missing` when status is not unknown.

## Non-Goals

- Do not implement automatic retry execution or scheduling.
- Do not alter `retry_policy.implemented = false`.
- Do not change Runtime Contract Gate backend normalization, trace fingerprints, or dedupe keys.
