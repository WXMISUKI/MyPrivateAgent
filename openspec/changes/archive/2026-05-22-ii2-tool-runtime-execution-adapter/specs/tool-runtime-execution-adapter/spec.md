## ADDED Requirements

### Requirement: Tool Runtime Execution Adapter

The system MUST expose a minimal `ToolRuntimeService.execute_tool(...)` adapter
for registered tool execution.

#### Scenario: Execute registered tool

- **GIVEN** a tool registry contains an executable tool
- **WHEN** `ToolRuntimeService.execute_tool(...)` is called with valid args
- **THEN** the result MUST include `status = ok`
- **AND** the result MUST include action and observation metadata.

### Requirement: Fail Closed Argument Validation

The system MUST fail closed when required arguments are missing.

#### Scenario: Missing required argument

- **GIVEN** a registered tool declares a required argument
- **WHEN** `ToolRuntimeService.execute_tool(...)` is called without that argument
- **THEN** the result MUST include `status = validation_failed`
- **AND** the tool implementation MUST NOT be invoked.

### Requirement: Facade ToolRuntimeService Bridge

The system MUST allow `AgentHarnessFacade.execute(...)` to use
`ToolRuntimeService.execute_tool(...)` when no explicit tool executor is
provided.

#### Scenario: Facade executes through ToolRuntimeService

- **GIVEN** a facade has an injected `ToolRuntimeService`
- **AND** a run tool policy selects a registered tool
- **WHEN** `AgentHarnessFacade.execute(...)` runs without an explicit executor
- **THEN** SDK-owned events MUST include the normal tool result event
- **AND** the recorded tool history MUST show `executor = tool_runtime_service`.
