# Design

## Summary Shape

`runtime_contract_summary` gains:

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

The field is derived from the `runtime_approved_tool_execution_bridge` smoke check.

## Fail-Closed Rules

- Missing check -> `bridge_smoke = false`
- Non-object summary field -> recompute from checks
- Numeric fields are non-negative ints or `0`
- String fields are normalized strings

## Markdown

The Runtime Contract Summary table adds an `Approved Tool Bridge` column with `yes` / `no`.
