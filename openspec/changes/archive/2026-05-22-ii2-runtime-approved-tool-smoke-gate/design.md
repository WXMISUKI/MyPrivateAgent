# Design

## Smoke Check

Add `runtime_approved_tool_execution_bridge` to `runtime_contract_smoke.py`.

The check uses an in-memory `ToolRegistry`, `ToolRuntimeService`, `EmbeddedAgentRuntimeSDK`, and `AgentHarnessFacade`.

It validates:

- `ask` runtime tool initially returns a pending approval request through SDK.
- approving the request executes the underlying tool exactly once.
- tool history includes `execution.policy_decision.status = allowed`.
- `execution.policy_decision.original_status = approval_required`.
- `execution.policy_decision.override.status = approved`.
- `deny` runtime tool remains `policy_denied` even with an approved override.

## Output

The smoke check returns compact machine-readable fields for quality gate summaries and debugging:

- `ask_approval_status`
- `approved_tool_call_count`
- `approved_policy_status`
- `approved_policy_original_status`
- `approved_policy_override_status`
- `deny_override_status`
- `deny_tool_call_count`
