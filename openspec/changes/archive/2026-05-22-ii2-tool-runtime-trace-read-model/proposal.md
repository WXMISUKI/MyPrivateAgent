## Why

`ToolRuntimeService.execute_tool(...)` now returns machine-readable execution
metadata for schema validation, retry and timeout. That data is useful only if
governance/read-model consumers can see it without parsing raw SDK events.

The current query-control mapper records only source event identity for
`tool_result` events. It should preserve a compact tool runtime observation
summary while still avoiding full event-body duplication.

## What Changes

- Extend `QueryControlEventMapperService.build_record_payload(...)` to include a
  compact `tool_runtime_observation` summary for tool result events.
- Preserve status, tool name, executor, retry, timeout and schema validation
  fields.
- Advertise this read-model field in `QueryControlPlaneService` runtime
  contract.

## Non-Goals

- Do not create a new trace store.
- Do not write raw tool result blobs into query-control payloads.
- Do not change frontend rendering in this change.
