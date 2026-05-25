# ii2-facade-tool-runtime-policy-bridge

## Summary

Bridge the new `ToolRuntimeService` permission-level policy coordination into `AgentHarnessFacade.execute(...)`.

## Motivation

`ToolRuntimeService.execute_tool(...)` now returns `approval_required` or `policy_denied` before invocation for non-auto tools. `AgentHarnessFacade` still depends on the execution-loop `tool_policy` to pause before tool execution. If the caller supplies an `allowed` policy while the registry ToolSpec says `ask`, the facade can still reach the tool executor path and treat the runtime-service response like a normal tool result.

The facade should consume the runtime-service policy decision before execution, so the SDK keeps owning approval request creation and denied-run semantics.

## Scope

- Expose a lightweight public policy probe on `ToolRuntimeService`.
- Wrap facade `tool_policy` when the facade has a `ToolRuntimeService`.
- Map runtime-service policy decisions into execution-loop statuses:
  - `allowed` remains `allowed`
  - `approval_required` pauses through SDK approval lifecycle
  - `denied` fails closed through execution-loop denied semantics
- Preserve local handler behavior unless the caller explicitly routes the tool through runtime-service metadata.

## Non-Goals

- Do not create approval requests in `ToolRuntimeService`.
- Do not change `ApprovalEngineService` state machine.
- Do not add frontend changes.
