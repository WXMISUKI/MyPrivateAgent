# Design

## Runtime Contract Summary Normalization

`backend/routers/health.py` already normalizes Runtime Contract Gate summaries before writing degraded traces and building fingerprints. This change extends that normalization with:

```json
{
  "approved_tool_execution_coverage": {
    "bridge_smoke": true,
    "approved_tool_call_count": 1,
    "approved_policy_original_status": "approval_required",
    "approved_policy_override_status": "approved",
    "deny_override_status": "policy_denied",
    "deny_tool_call_count": 0
  }
}
```

## Fingerprint Semantics

The degraded trace fingerprint already hashes the normalized `runtime_contract_summary`. By adding approved tool coverage to that normalized summary, dedupe keys change when:

- bridge smoke coverage appears or disappears;
- approved tool call count changes;
- original / override / deny status changes;
- deny tool call count changes.

## Fail-Closed Rules

- Missing summary -> coverage defaults to uncovered.
- Non-object `approved_tool_execution_coverage` -> coverage defaults to uncovered.
- Numeric fields are non-negative integers or `0`.
- String fields are compact strings.

## External References

- LangGraph-style checkpoint/resume semantics inform the need for stable machine-readable runtime reasons, but no graph orchestration is introduced.
- OpenHands-style action/observation separation informs why tool approval bridge coverage must be traceable, but no sandbox runtime is introduced in this change.
