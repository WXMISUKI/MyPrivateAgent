# tool-runtime-policy-coordination

## ADDED Requirements

### Requirement: Tool runtime execution MUST evaluate permission policy before invocation

`ToolRuntimeService.execute_tool(...)` MUST evaluate a registered tool's permission level before schema validation and before invoking the tool implementation.

#### Scenario: Auto tool is allowed

- **WHEN** a registered tool has permission level `auto`
- **THEN** the execution envelope status is `ok` after successful invocation
- **AND** `execution.policy_decision.status` is `allowed`

#### Scenario: Ask tool requires approval

- **WHEN** a registered tool has permission level `ask`
- **THEN** the execution envelope status is `approval_required`
- **AND** `execution.policy_decision.status` is `approval_required`
- **AND** the tool implementation is not invoked

#### Scenario: High-risk tool requires approval

- **WHEN** a registered tool has permission level `high_risk`
- **THEN** the execution envelope status is `approval_required`
- **AND** `execution.policy_decision.reason_code` is `permission_level_requires_approval`
- **AND** the tool implementation is not invoked

#### Scenario: Denied tool fails closed

- **WHEN** a registered tool has permission level `deny`
- **THEN** the execution envelope status is `policy_denied`
- **AND** `execution.policy_decision.status` is `denied`
- **AND** the tool implementation is not invoked

### Requirement: Tool runtime contract MUST declare policy coordination

`ToolRuntimeService.build_runtime_contract()` MUST declare the policy coordination mode and supported decision statuses for downstream SDK, facade, and governance consumers.

#### Scenario: Runtime contract exposes policy coordination metadata

- **WHEN** runtime contract is built
- **THEN** `execution_adapter.policy_coordination` is `permission_level_gate_v1`
- **AND** `execution_adapter.policy_decision_statuses` contains `allowed`, `approval_required`, and `denied`
