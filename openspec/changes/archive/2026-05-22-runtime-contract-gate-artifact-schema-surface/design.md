# Design

`RuntimeContractGateService.build_runtime_contract()` will include:

```json
{
  "runtime_contract_artifact_schema": {
    "contract_version": "phase-f-runtime-contract-artifact-schema-v1",
    "overall_status": "healthy|degraded|unknown",
    "summary_required_fields": ["..."],
    "summary_missing_fields": ["..."]
  }
}
```

Selection rule:

- Prefer the first object `runtime_contract_artifact_schema` found under report steps.
- If missing or malformed but contract checks exist, derive a guard from the normalized `runtime_contract_summary`.
- If the whole report is missing or contract checks are missing, return `overall_status = unknown` with stable required fields.

This mirrors the current summary extraction pattern and keeps old quality gate artifacts readable.
