## Why

`ToolRuntimeService.execute_tool(...)` now provides a minimal execution adapter,
but timeout and retry are only documented as future boundaries. Enterprise
runtime consumers need machine-readable failure semantics before richer
execution backends are introduced.

This change adds a conservative synchronous timeout/retry contract to the tool
runtime adapter without introducing background workers, sandboxing or hard
thread cancellation.

## What Changes

- Add `execution_options` to `ToolRuntimeService.execute_tool(...)`.
- Support `max_attempts` for synchronous retry on tool implementation errors.
- Support `timeout_seconds` as a post-call elapsed-time gate.
- Return machine-readable `retry` and `timeout` metadata inside the execution
  envelope.
- Keep facade execution on the SDK-owned event/history path.

## Non-Goals

- Do not implement hard cancellation of running tool calls.
- Do not introduce async queues, worker pools or sandbox isolation.
- Do not retry validation failures or missing tools.
