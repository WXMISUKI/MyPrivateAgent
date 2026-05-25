## Why

`AgentHarnessFacade.register_tool(...)` can now execute a local handler, but the
next backend convergence point is `ToolRuntimeService`. Without an execution
adapter, facade execution still has two meanings: local callable execution and
tool runtime contract discovery.

This change makes `ToolRuntimeService` the default backend execution seam for
registered tools while keeping `EmbeddedAgentRuntimeSDK` as the owner of run
state, events, approvals and recovery.

## What Changes

- Add `ToolRuntimeService.execute_tool(...)` as a minimal synchronous execution
  adapter over the existing tool registry.
- Return a standard action/observation execution envelope.
- Add minimal argument validation from the registered tool parameter metadata.
- Let `AgentHarnessFacade.execute(...)` use `ToolRuntimeService.execute_tool(...)`
  when no explicit executor is supplied and no local handler is registered.

## Non-Goals

- Do not introduce async queue execution, sandbox isolation, full JSON Schema
  validation, timeout enforcement or retry execution in this change.
- Do not move runtime trace storage into `ToolRuntimeService`.
- Do not bypass SDK-owned `tool_call_started / tool_result` events.
