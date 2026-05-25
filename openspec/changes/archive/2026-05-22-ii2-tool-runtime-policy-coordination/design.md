# Design

## Contract

`ToolRuntimeService.execute_tool(...)` will evaluate registered tool permission before schema validation and invocation.

Returned envelopes include:

```json
{
  "execution": {
    "policy_decision": {
      "status": "allowed | approval_required | denied",
      "allowed": true,
      "requires_approval": false,
      "permission_level": "auto",
      "reason_code": "permission_level_auto_allowed",
      "policy": "permission_level_gate_v1"
    }
  }
}
```

## Mapping

- `auto`, empty, or unknown low-risk levels -> `allowed`
- `ask`, `high_risk` -> `approval_required`
- `deny`, `denied` -> `denied`

ToolSpec metadata wins over BaseTool metadata when both are available, because `ToolSpec` is the typed capability contract surfaced to the runtime.

## Blocking Semantics

Policy blocking happens before schema validation. The service must not validate or invoke a tool that is not currently executable, because approval and denial are governance gates, not data-shape failures.

For blocked execution:

- `approval_required`: envelope status and observation status are `approval_required`
- `deny`: envelope status is `policy_denied`, policy decision status is `denied`, observation status is `policy_denied`
- schema/retry/timeout metadata are `skipped`

## Integration Boundary

`ToolRuntimeService` does not create approval requests. Callers such as `EmbeddedAgentRuntimeSDK`, `AgentHarnessFacade`, and execution-loop policy adapters can consume the `approval_required` result and hand it to `ApprovalEngineService`.
