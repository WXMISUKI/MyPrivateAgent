# ii2-runtime-approved-tool-execution-bridge

## Summary

Close the approved-tool execution loop for facade + ToolRuntimeService integration.

## Motivation

`AgentHarnessFacade` can now map runtime-service `ask / high_risk` tools into SDK approval requests. However, after approval is granted, the continuation resumes through the same default runtime-service executor. Without an approved execution context, `ToolRuntimeService.execute_tool(...)` will apply the same `permission_level_gate_v1` again and return `approval_required` instead of executing the tool.

The backend needs a narrow, auditable bridge: approval blocks first execution, then a consumed approval allows exactly the continuation execution path to proceed.

## Scope

- Add an approved policy override contract to `ToolRuntimeService.execute_tool(...)`.
- Mark SDK tool-continuation resume with an approved execution context.
- Pass that context from `AgentHarnessFacade` default runtime-service executor.
- Ensure `ask / high_risk` tools execute only after approval, while `deny` tools remain blocked.

## Non-Goals

- Do not bypass `deny`.
- Do not create approval requests in ToolRuntimeService.
- Do not implement a broad token service or database migration.
