## Design

`state_contract` 是 workspace backend 的能力描述，不是实际数据行。

Required shape:

```json
{
  "contract_version": "phase-ii-durable-workspace-state-contract-v1",
  "durable_state_kinds": ["run_snapshot", "event_log", "approval_snapshot", "tool_continuation_descriptor", "loop_continuation_descriptor", "artifact_ref", "child_executor_output"],
  "runtime_only_state_kinds": ["executable_continuation_callable", "python_function_binding", "temporary_stream_cursor", "in_process_event_iterator"]
}
```

Semantics:

- SQLAlchemy store may report `durable = true`, but if `fallback_active = true`, recovery still treats it as not cross-process ready.
- In-memory store reports the same state vocabulary but `durable = false`.
- Consumers should read `state_contract` to understand what the backend is designed to persist, and `durable/fallback_active` to decide whether it is currently safe for cross-process recovery.

Compatibility:

- Existing `describe_backend()` fields remain unchanged.
- Existing recovery checks continue to use `durable` and `fallback_active`.
