# gate-tool-runtime-timeout-retry-contract

## Why

`ToolRuntimeService.execute_tool(...)` already exposes synchronous retry metadata and post-call elapsed timeout metadata, but Runtime Contract Gate does not yet summarize this boundary as its own machine-readable coverage.

Without a dedicated gate signal, a regression could silently drop ToolRuntime retry/timeout evidence while the broader SDK ToolRuntime bridge still appears covered.

## What Changes

- Add a runtime contract smoke check for ToolRuntime timeout/retry metadata.
- Normalize the check into `runtime_contract_summary.tool_runtime_timeout_retry_coverage`.
- Guard the coverage through Quality Gate artifact schema, Runtime Contract Gate, and Runtime Contract Snapshot.
- Keep timeout semantics as post-call elapsed metadata only.

## Non-Goals

- Do not implement hard cancellation, sandbox execution, worker execution, or async timeout interruption.
- Do not change `ToolRuntimeService.execute_tool(...)` behavior.
- Do not expand SDK approval/tool bridge semantics.
