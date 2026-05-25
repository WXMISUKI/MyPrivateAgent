# runtime-approved-tool-smoke-gate Specification

## Purpose
Ensure approved tool execution behavior is covered by runtime contract smoke checks.
## Requirements
### Requirement: Runtime smoke MUST cover approved runtime-service tool execution

`runtime_contract_smoke.py` MUST include a check that proves facade + ToolRuntimeService `ask` tools resume and execute after SDK approval.

#### Scenario: Smoke check reports approved ask execution

- **WHEN** runtime contract smoke runs
- **THEN** the checks list contains `runtime_approved_tool_execution_bridge`
- **AND** that check reports `approved_tool_call_count = 1`
- **AND** `approved_policy_original_status = approval_required`
- **AND** `approved_policy_override_status = approved`

### Requirement: Runtime smoke MUST prove deny override remains blocked

The approved execution bridge smoke check MUST also prove that `deny` tools cannot be executed with approved override metadata.

#### Scenario: Smoke check reports deny override blocked

- **WHEN** runtime contract smoke runs
- **THEN** `runtime_approved_tool_execution_bridge.deny_override_status` is `policy_denied`
- **AND** `runtime_approved_tool_execution_bridge.deny_tool_call_count` is `0`
