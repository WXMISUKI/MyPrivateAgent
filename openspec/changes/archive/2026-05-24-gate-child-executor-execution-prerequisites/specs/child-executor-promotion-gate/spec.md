## ADDED Requirements

### Requirement: Promotion Gate Must Surface Execution Prerequisites
The child executor promotion gate MUST expose the child executor execution prerequisites contract as part of its machine-readable evidence.

#### Scenario: Gate blocks while prerequisites are missing
- **WHEN** the promotion gate is evaluated and execution prerequisites are missing
- **THEN** the gate MUST expose `child_executor_execution_prerequisites`
- **AND** the gate MUST remain blocked
- **AND** the gate MUST include prerequisite blockers in its decision evidence

#### Scenario: Runtime profile renders gate prerequisites
- **WHEN** runtime profile is requested
- **THEN** frontend consumers MUST be able to read execution prerequisite evidence from the backend promotion gate contract
- **AND** they MUST NOT need to recalculate execution readiness from preflight metadata
