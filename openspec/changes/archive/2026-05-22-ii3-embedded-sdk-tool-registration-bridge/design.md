# Design

`EmbeddedAgentRuntimeSDK.register_tool(...)` becomes a thin bridge into the existing ToolRuntimeService registry.

The SDK owns no second tool registry. Instead:

1. Normalize caller input into `ToolSpec`.
2. Resolve a tool runtime service from constructor injection or lazy default.
3. Call `tool_runtime_service.tool_registry.register_tool_spec(tool_spec)` when available.
4. If `handler` is supplied, wrap it in the existing `BaseTool` shape and register it with `tool_registry.register(...)`.
5. Return a stable contract:
   - `status`
   - `tool_spec`
   - `tool_registry_bridge`
   - `handler_registered`
   - `runtime_contract`

This keeps SDK registration aligned with facade registration while preserving ToolRuntimeService as the single execution adapter.
