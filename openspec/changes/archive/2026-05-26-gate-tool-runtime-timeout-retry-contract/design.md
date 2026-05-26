# Design

This slice treats ToolRuntime timeout/retry as contract evidence rather than new execution behavior.

The smoke check should exercise three existing paths:

1. A flaky tool succeeds on the second attempt and reports `retry.status = recovered`.
2. A flaky tool exhausts retries and reports `retry.status = exhausted`.
3. A slow synchronous tool returns after `timeout_seconds` and reports `status = timeout` plus `timeout.status = exceeded`.

The check also reads `ToolRuntimeService.build_runtime_contract().execution_adapter` so Quality Gate can prove the declared posture remains `sync_exception_retry` and `post_call_elapsed_check`.

Runtime Contract Summary should expose a compact coverage object:

```json
{
  "tool_runtime_timeout_retry_coverage": {
    "timeout_retry_smoke": true,
    "retry_policy": "sync_exception_retry",
    "timeout_enforcement": "post_call_elapsed_check"
  }
}
```

The coverage is deliberately separate from `sdk_tool_runtime_execution_coverage`: SDK bridge coverage proves facade/SDK integration, while this coverage proves ToolRuntime's own execution adapter metadata.
