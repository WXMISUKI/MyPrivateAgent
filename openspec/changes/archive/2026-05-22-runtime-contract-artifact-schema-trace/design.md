# Design

Extend the existing `runtime_contract_gate_degraded` trace normalization path. It already normalizes `runtime_contract_summary`; artifact schema should follow the same fail-closed pattern.

Normalized shape:

```json
{
  "contract_version": "phase-f-runtime-contract-artifact-schema-v1",
  "overall_status": "healthy|degraded|unknown|",
  "summary_required_fields": ["..."],
  "summary_missing_fields": ["..."]
}
```

The normalized artifact schema will be included in:

- `_build_runtime_contract_gate_trace_fingerprint(...)`
- `runtime_contract_gate_degraded.payload.runtime_contract_artifact_schema`

When missing or malformed, the field should still appear with empty/default values so governance consumers get a stable contract.
