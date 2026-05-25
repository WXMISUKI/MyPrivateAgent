## Design

`ToolRuntimeService.execute_tool(tool_name, args)` is a narrow adapter:

1. Resolve a registered tool from `tool_registry.get(tool_name)`.
2. Resolve optional `ToolSpec` metadata from `tool_registry.get_tool_spec(...)`.
3. Validate required arguments using the tool's parameter metadata:
   - A parameter is required when its metadata contains `required = true`.
   - A tool may also expose a root-level `required` list.
4. Invoke the tool through `invoke(args)` when available.
5. Return a normalized execution envelope:
   - `status`
   - `tool_name`
   - `args`
   - `result_text`
   - `execution.action`
   - `execution.observation`
   - `execution.tool_spec`
   - `execution.schema_validation`

Facade integration remains conservative:

- Explicit `tool_executor` still wins.
- Local facade handler still wins over ToolRuntimeService for tools registered
  directly through facade.
- If no local handler is available and `tool_runtime_service` is present,
  facade builds a default executor using `ToolRuntimeService.execute_tool(...)`.

## Future Boundaries

Timeout, retry and full JSON Schema validation will be added as explicit
contract fields before becoming executable behavior.
