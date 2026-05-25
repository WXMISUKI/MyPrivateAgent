# Design

`EmbeddedAgentRuntimeSDK.execute_run(...)` will derive effective loop callables:

1. If a caller passes `tool_executor`, preserve existing behavior.
2. If no `tool_executor` is passed but a `tool_policy` is present, wrap the policy with ToolRuntimeService policy probing.
3. If the original policy returns `allowed`, ask `ToolRuntimeService.evaluate_tool_policy(tool_name)` for the registered permission decision.
4. Convert `approval_required` and `denied` back into the existing execution loop decision contract so SDK approval lifecycle and fail-closed handling remain the owner.
5. Capture the final tool decision and use a ToolRuntimeService-backed executor to call `execute_tool(...)`.
6. When approval continuation resumes, pass the existing `approved_tool_execution` marker as `execution_options.policy_override` so `ask / high_risk` tools can execute after approval while `deny` remains blocked by ToolRuntimeService.

This mirrors the facade path but keeps the implementation in SDK helpers so SDK-only callers get the same runtime behavior.
