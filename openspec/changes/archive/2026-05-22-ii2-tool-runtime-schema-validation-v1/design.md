## Design

`ToolRuntimeService._validate_tool_args(...)` remains the single validation
point before invocation.

Supported schema forms:

```python
parameters = {
    "case_id": {"type": "string", "required": True},
    "mode": {"type": "string", "enum": ["quick", "deep"]},
    "filters": {
        "type": "object",
        "required": ["level"],
        "properties": {
            "level": {"type": "string"}
        }
    }
}
```

Returned metadata:

```json
{
  "status": "failed",
  "missing_required": ["case_id"],
  "invalid_types": [{"path": "case_id", "expected": "string", "actual": "integer"}],
  "invalid_enum": [{"path": "mode", "allowed": ["quick", "deep"], "actual": "other"}]
}
```

Validation is fail-closed for supported schema keys and permissive for
unsupported keys. This keeps v1 predictable without pretending to be complete
JSON Schema.
