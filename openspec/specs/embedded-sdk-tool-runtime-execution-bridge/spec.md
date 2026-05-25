# embedded-sdk-tool-runtime-execution-bridge Specification

## Purpose
Ensure Embedded SDK tool execution paths are bridged through ToolRuntimeService and covered by runtime contract evidence.
## Requirements
### Requirement: SDK execute_run MUST use ToolRuntimeService when no explicit executor is provided

`EmbeddedAgentRuntimeSDK.execute_run(...)` MUST be able to execute a registered tool through `ToolRuntimeService` when a tool policy returns an allowed tool decision and no explicit `tool_executor` is supplied.

#### Scenario: SDK executes registered tool through ToolRuntimeService
- **GIVEN** an EmbeddedAgentRuntimeSDK configured with a ToolRuntimeService
- **AND** a registered executable tool
- **WHEN** `execute_run(...)` is called with a tool policy returning `status = allowed`
- **THEN** the run completes
- **AND** `run.tool_history[0].execution.executor = tool_runtime_service`.

### Requirement: SDK direct execution MUST preserve ToolRuntimeService policy coordination

SDK direct execution MUST respect ToolSpec permission levels before invoking a registered handler.

#### Scenario: SDK pauses ask tool before invocation
- **GIVEN** a registered tool with `permission_level = ask`
- **WHEN** `execute_run(...)` receives an allowed tool policy for that tool
- **THEN** the run waits for approval
- **AND** the tool handler is not invoked before approval.

#### Scenario: SDK resumes approved ask tool once
- **GIVEN** a run waiting for an ask tool approval
- **WHEN** the approval is submitted as approved
- **THEN** the tool executes once through ToolRuntimeService
- **AND** the tool history includes `policy_decision.original_status = approval_required`.

#### Scenario: SDK denies deny tool before invocation
- **GIVEN** a registered tool with `permission_level = deny`
- **WHEN** `execute_run(...)` receives an allowed tool policy for that tool
- **THEN** the run fails with `tool_policy_denied`
- **AND** the tool handler is not invoked.
