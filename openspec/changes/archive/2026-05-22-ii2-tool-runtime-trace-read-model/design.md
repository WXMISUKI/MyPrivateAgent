## Design

`QueryControlEventMapperService.build_record_payload(...)` keeps its identity
payload but gains a compact tool summary when the source event is a tool result.

Input sources:

- Top-level flattened SDK event fields.
- Nested `payload` fields.

Output:

```json
{
  "tool_runtime_observation": {
    "tool_name": "risk_lookup",
    "status": "timeout",
    "executor": "tool_runtime_service",
    "schema_validation_status": "passed",
    "retry_status": "recovered",
    "retry_attempt_count": 2,
    "timeout_status": "exceeded",
    "timeout_seconds": 0.1
  }
}
```

The summary is intentionally small and deterministic. It should not include
full tool result text, large card payloads, or arbitrary raw execution blobs.

## Contract Surface

`QueryControlPlaneService.build_runtime_contract()` will expose
`tool_runtime_observation_payload = compact_status_summary` under
`adapter_boundaries.tool_runtime`.
