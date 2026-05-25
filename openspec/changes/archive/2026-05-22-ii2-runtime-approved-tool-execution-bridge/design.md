# Design

## Approved Execution Context

During `_resume_tool_continuation(...)`, the SDK temporarily marks the `run_context.metadata` with:

```json
{
  "approved_tool_execution": {
    "approval_request_id": "apr_...",
    "decision": "approved",
    "source": "embedded_sdk_tool_continuation"
  }
}
```

The marker only exists while the stored tool executor is being called.

## Facade Runtime-Service Executor

`AgentHarnessFacade` passes the marker into `ToolRuntimeService.execute_tool(...)` as:

```json
{
  "policy_override": {
    "status": "approved",
    "approval_request_id": "apr_...",
    "source": "embedded_sdk_tool_continuation"
  }
}
```

## ToolRuntimeService Behavior

If the normal permission-level decision is `approval_required` and `policy_override.status` is `approved`, the service allows execution and records the original gated decision plus override metadata in `execution.policy_decision`.

`denied` decisions are never overridden.
