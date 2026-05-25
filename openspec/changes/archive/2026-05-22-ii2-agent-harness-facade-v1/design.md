## Design

The facade becomes a thin embedded harness bridge:

1. `AgentHarnessFacade.register_tool(...)`
   - Accepts a `ToolSpec`, a `ToolSpec`-shaped dict, or name/description fields.
   - Optionally accepts a Python callable implementation.
   - Registers metadata into a local ToolSpec registry for facade execution.
   - If a `ToolRuntimeService` is supplied, also registers metadata into its
     underlying tool registry when supported.

2. `AgentHarnessFacade.execute(...)`
   - Existing explicit `tool_executor` still wins.
   - When no explicit executor is provided, the facade builds a default executor
     from the registered facade tool implementations.
   - `tool_policy` can select `tool_name` and `tool_args`; otherwise a single
     registered tool can be selected by default.

3. Action/Observation Trace
   - Tool action metadata is stored inside the normalized tool result
     `execution.action`.
   - Tool observation metadata is stored inside `execution.observation`.
   - The SDK and `ExecutionLoopController` continue to emit existing
     `tool_call_started` and `tool_result` events.

## Contract Vocabulary

- `facade_runtime_posture`: `embedded_harness_v1_candidate`
- `tool_registry_bridge`: describes whether facade has a local registry and/or
  an injected `ToolRuntimeService`.
- `default_tool_executor`: describes whether facade can execute registered
  tools without a caller-supplied executor.
