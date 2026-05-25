## Why

`AgentHarnessFacade` is still a preview developer surface. It can delegate to
`EmbeddedAgentRuntimeSDK.execute_run(...)`, but tool registration and default
tool execution still rely on ad hoc callables.

To move the embedded harness toward v1, the facade needs a minimal bridge into
the existing `ToolSpec` / `ToolRuntimeService` layer while preserving the rule
that runtime state, events, approvals and recovery stay owned by the SDK.

## What Changes

- Add a facade-level `register_tool(...)` method backed by `ToolSpec`.
- Allow registered facade tools to be executed by `execute(...)` without passing
  a custom `tool_executor` every time.
- Emit tool action/observation metadata through the existing SDK event stream
  and run `tool_history`, instead of creating a second runtime trace model.
- Expose the new method and v1 posture in the `agent_harness_facade` contract.

## Non-Goals

- Do not migrate to LangGraph / OpenHands / Goose / Aider.
- Do not add sandbox isolation, retry policy, timeout enforcement or async tool
  dispatch in this change.
- Do not bypass `EmbeddedAgentRuntimeSDK` for events, approvals or recovery.
