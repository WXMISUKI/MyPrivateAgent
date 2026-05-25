## Design

The new smoke check should prove the SDK direct bridge using real code:

1. Construct a `ToolRuntimeService` with a local test registry.
2. Construct `EmbeddedAgentRuntimeSDK(tool_runtime_service=...)`.
3. Register an executable `ToolSpec` through `sdk.register_tool(...)`.
4. Execute a run without a custom `tool_executor`.
5. Verify auto permission calls the handler exactly once and records ToolRuntime execution metadata in SDK `tool_history`.
6. Verify `ask` permission pauses into SDK approval lifecycle and executes once after `submit_approval(..., "approved")`.
7. Verify `deny` permission fails closed before invoking the handler.

The existing `runtime_approved_tool_execution_bridge` check remains Facade-focused. The new check should use a distinct name, `sdk_tool_runtime_execution_bridge`, so quality gate summaries can distinguish the SDK direct path from the Facade path.

## Quality Gate Summary

`quality_gate_report.py` and `RuntimeContractGateService` should normalize the new check into:

```json
{
  "sdk_tool_runtime_execution_coverage": {
    "bridge_smoke": true,
    "auto_tool_call_count": 1,
    "approved_tool_call_count": 1,
    "approved_policy_original_status": "approval_required",
    "approved_policy_override_status": "approved",
    "deny_override_status": "policy_denied",
    "deny_tool_call_count": 0
  }
}
```

Missing, malformed, or failed check evidence must fail closed as `bridge_smoke = false`.

## Contract Boundaries

- The smoke check validates quality gate coverage, not new SDK behavior.
- Unit tests for SDK behavior remain the primary behavioral tests.
- Runtime Profile should consume the normalized summary from the quality gate artifact, not re-run tool execution.
