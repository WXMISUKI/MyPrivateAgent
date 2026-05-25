# runtime-approved-tool-execution-bridge

## ADDED Requirements

### Requirement: Approved continuations MUST execute runtime-service ask tools once

When an SDK approval request is approved for a facade runtime-service tool, the resumed continuation MUST execute the underlying tool instead of being blocked again by the same `permission_level_gate_v1`.

#### Scenario: Ask tool executes after approval

- **WHEN** a facade runtime-service tool has permission level `ask`
- **AND** initial execution creates an approval request
- **AND** the approval request is submitted as `approved`
- **THEN** the tool implementation is invoked once
- **AND** the run tool history contains the tool result

### Requirement: Runtime-service approval override MUST not bypass deny

`ToolRuntimeService.execute_tool(...)` MUST allow approved policy override only for decisions that normally require approval.

#### Scenario: Deny tool remains blocked with approval override

- **WHEN** a tool has permission level `deny`
- **AND** execute_tool receives an approved policy override
- **THEN** the execution status remains `policy_denied`
- **AND** the tool implementation is not invoked

### Requirement: Approved override metadata MUST be visible in execution envelope

The execution envelope MUST preserve both the approved override and the original permission-level gate reason.

#### Scenario: Approved execution records policy override

- **WHEN** an `ask` tool executes with an approved policy override
- **THEN** `execution.policy_decision.status` is `allowed`
- **AND** `execution.policy_decision.override.status` is `approved`
- **AND** `execution.policy_decision.original_status` is `approval_required`
