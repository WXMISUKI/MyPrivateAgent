# facade-tool-runtime-policy-bridge Specification

## Purpose
Define how facade-level tool execution coordinates with ToolRuntime policy decisions for allowed, approval-required, and denied tools.
## Requirements
### Requirement: Facade MUST honor ToolRuntimeService policy before execution

`AgentHarnessFacade.execute(...)` MUST map `ToolRuntimeService` permission-level policy decisions into execution-loop tool policy decisions before invoking the runtime-service tool executor.

#### Scenario: Runtime-service ask tool pauses through SDK approval lifecycle

- **WHEN** facade execute receives an `allowed` tool policy for a registry tool whose runtime ToolSpec permission level is `ask`
- **THEN** the run stops in `waiting_approval`
- **AND** an approval request is returned
- **AND** the runtime-service tool implementation is not invoked

#### Scenario: Runtime-service deny tool fails closed before execution

- **WHEN** facade execute receives an `allowed` tool policy for a registry tool whose runtime ToolSpec permission level is `deny`
- **THEN** the run state is `failed`
- **AND** the run stop reason is `tool_policy_denied`
- **AND** the runtime-service tool implementation is not invoked

### Requirement: ToolRuntimeService MUST expose a side-effect-free policy probe

`ToolRuntimeService` MUST expose a public policy probe that returns `permission_level_gate_v1` decisions without invoking the tool.

#### Scenario: Policy probe does not invoke tools

- **WHEN** a caller probes policy for a registered `ask` tool
- **THEN** the returned decision status is `approval_required`
- **AND** the tool implementation is not invoked
