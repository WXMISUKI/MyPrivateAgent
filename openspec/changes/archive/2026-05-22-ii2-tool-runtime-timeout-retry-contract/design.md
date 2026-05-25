## Design

`ToolRuntimeService.execute_tool(tool_name, args, execution_options=...)`
supports:

- `max_attempts`: integer, minimum 1.
- `timeout_seconds`: positive float. If omitted, uses `ToolSpec.timeout_seconds`
  when present.

Execution behavior:

1. Validate tool existence and required args before attempts.
2. Invoke the registered tool synchronously.
3. Retry only implementation exceptions until `max_attempts` is exhausted.
4. Measure elapsed wall-clock time around each attempt.
5. If a successful attempt exceeds `timeout_seconds`, return `status = timeout`.

Timeout contract:

- This is `post_call_elapsed_check`, not hard cancellation.
- The adapter cannot stop a blocking tool call mid-flight.
- Future worker/sandbox adapters may upgrade this while preserving the envelope.

Retry contract:

- `retry.status = not_needed / recovered / exhausted / skipped`
- `retry.attempt_count`
- `retry.max_attempts`
- `retry.errors`

## Facade

`AgentHarnessFacade` continues to call `ToolRuntimeService.execute_tool(...)`
only through its default executor path. SDK still owns events and run history.
