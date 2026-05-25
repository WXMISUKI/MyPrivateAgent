## ADDED Requirements

### Requirement: Facade Tool Registration Bridge

The system MUST allow `AgentHarnessFacade` to register `ToolSpec` metadata for
embedded harness execution without becoming a second runtime core.

#### Scenario: Register ToolSpec through facade

- **WHEN** a caller registers a tool through `AgentHarnessFacade.register_tool(...)`
- **THEN** the returned payload MUST include the registered `tool_spec`
- **AND** the facade contract MUST report a local tool registry bridge.

### Requirement: Default Registered Tool Execution

The system MUST allow facade execution to use a registered local tool
implementation when no explicit `tool_executor` is supplied.

#### Scenario: Execute registered tool through facade

- **GIVEN** a run created through `AgentHarnessFacade`
- **AND** a registered tool implementation
- **WHEN** the run is executed with a tool policy selecting that tool
- **THEN** the SDK event stream MUST contain the existing tool start/result events
- **AND** the recorded tool history MUST include action and observation metadata.

### Requirement: SDK-Owned Trace

The system MUST keep tool execution trace inside SDK-owned events and run
metadata.

#### Scenario: Facade execution records action observation metadata

- **WHEN** a registered facade tool is executed
- **THEN** the facade MUST NOT create a separate trace store
- **AND** the tool result execution envelope MUST include `action` and
  `observation` fields.
