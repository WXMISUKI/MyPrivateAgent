# ii2-tool-runtime-policy-coordination

## Summary

Close the next backend runtime gap by moving basic tool permission coordination into `ToolRuntimeService.execute_tool(...)`.

The execution adapter already owns the action/observation envelope, schema validation, timeout, retry, and trace read model. It now needs to fail closed before validation/invocation when the registered tool is not auto-executable.

## Motivation

`ExecutionLoopController` and `PolicyEngineService` already use the machine-readable statuses `allowed`, `approval_required`, and `denied`. `ToolRuntimeService` currently exposes `permission_level` and high-risk counts, but execution still proceeds unless the caller supplies an outer policy callable. That leaves the tool runtime adapter with an incomplete governance boundary.

## Scope

- Add a permission-level policy gate inside `ToolRuntimeService.execute_tool(...)`.
- Normalize `auto`, `ask`, `high_risk`, and `deny` permission levels into the existing execution-loop statuses.
- Return a compact `execution.policy_decision` object in every execution envelope.
- Block `ask` / `high_risk` tools as `approval_required` without invoking the tool.
- Block `deny` tools as `policy_denied` without invoking the tool.
- Keep ApprovalEngine as the owner of approval request creation and lifecycle.

## Non-Goals

- Do not create approval requests directly in `ToolRuntimeService`.
- Do not replace `PolicyEngineService` or execution-loop tool policies.
- Do not introduce external framework adapters or database migrations.
