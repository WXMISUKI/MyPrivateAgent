## ADDED Requirements

### Requirement: SDK register_tool MUST bridge to ToolRuntimeService

`EmbeddedAgentRuntimeSDK.register_tool(...)` MUST register ToolSpec metadata through the configured ToolRuntimeService registry.

#### Scenario: Metadata-only tool registration
- **GIVEN** an EmbeddedAgentRuntimeSDK configured with a ToolRuntimeService
- **WHEN** `register_tool(...)` is called with a valid tool definition
- **THEN** the result status is `registered`
- **AND** the ToolRuntimeService runtime contract includes the registered tool spec.

#### Scenario: Executable handler registration
- **GIVEN** an EmbeddedAgentRuntimeSDK configured with a ToolRuntimeService
- **WHEN** `register_tool(...)` is called with a valid tool definition and handler
- **THEN** the result reports `handler_registered = true`
- **AND** `ToolRuntimeService.execute_tool(...)` can execute the registered tool.

#### Scenario: Invalid tool registration
- **GIVEN** an EmbeddedAgentRuntimeSDK
- **WHEN** `register_tool(...)` is called without a tool name or description
- **THEN** the SDK MUST raise `ValueError`
- **AND** no tool metadata is registered.

### Requirement: SDK contract MUST describe register_tool as preview

The embedded SDK contract MUST mark `register_tool` as `preview` once it is backed by ToolRuntimeService.

#### Scenario: SDK contract exposes tool registration posture
- **WHEN** `EmbeddedAgentRuntimeSDK.build_contract()` is called
- **THEN** method `register_tool` has stability `preview`
- **AND** its required capability remains `runtime.tool_register`.
