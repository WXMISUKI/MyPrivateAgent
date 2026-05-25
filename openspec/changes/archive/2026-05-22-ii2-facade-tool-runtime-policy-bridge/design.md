# Design

## ToolRuntimeService Policy Probe

Add `evaluate_tool_policy(tool_name)` as a public, side-effect-free method. It returns the same `permission_level_gate_v1` decision shape as `execute_tool(...)`, but does not validate arguments or invoke tools.

## Facade Bridge

When `AgentHarnessFacade.execute(...)` has a `ToolRuntimeService`, it wraps any supplied `tool_policy`.

The wrapper:

1. Runs the caller policy.
2. Normalizes the decision to a dict.
3. If the decision status is `allowed` and has a `tool_name`, probes `ToolRuntimeService.evaluate_tool_policy(tool_name)`.
4. If the probe says `approval_required`, returns an execution-loop `approval_required` decision with metadata copied from the runtime policy decision.
5. If the probe says `denied`, returns a `denied` decision with metadata copied from the runtime policy decision.
6. Otherwise returns the original policy result.

This keeps approval creation inside `EmbeddedAgentRuntimeSDK._create_loop_tool_approval_if_required(...)`.

## Behavior

The bridge is intentionally before execution. It must prevent `ToolRuntimeService.execute_tool(...)` from being called for `ask`, `high_risk`, or `deny` tools when the facade has enough policy context.
