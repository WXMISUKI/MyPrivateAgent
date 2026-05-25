# ii3-embedded-sdk-tool-runtime-execution-bridge

## Why

`EmbeddedAgentRuntimeSDK.register_tool(...)` now registers ToolSpec metadata and optional handlers through `ToolRuntimeService`, but `execute_run(...)` still needs an explicit `tool_executor` callable to execute tools. That means SDK-only integrations can register tools but cannot complete the default action/observation loop without manually rebuilding facade behavior.

This change closes that gap by letting SDK `execute_run(...)` use the configured `ToolRuntimeService` as its default execution adapter when callers provide a tool policy decision but no explicit tool executor.

## What Changes

- Add a ToolRuntimeService-backed default tool executor inside `EmbeddedAgentRuntimeSDK.execute_run(...)`.
- Add policy coordination so SDK direct execution respects `ask / high_risk / deny` ToolSpec permission levels before invocation.
- Preserve SDK-owned events, `tool_history`, approval continuation, and recovery behavior.
- Keep `ToolRuntimeService` as the single tool execution core; SDK only adapts loop policy/executor seams.

## Out of Scope

- External framework adapter execution.
- Worker-level hard timeout or sandbox isolation.
- Frontend governance changes.
