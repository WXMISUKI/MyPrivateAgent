# child-executor-promotion-gate Specification

## Purpose
Define the child executor promotion gate that decides whether a child executor candidate is ready to move beyond preflight.
## Requirements
### Requirement: Child Executor Promotion Gate Must Expose Final Promotion Decision
The system MUST provide a machine-readable child executor promotion gate contract that states whether the current delegated child execution context is allowed to be promoted beyond the relationship seam.

The gate contract MUST include:

- a gate status
- an allow/deny result
- a failure reason when blocked
- an executor path when allowed
- blockers and a recommended next step

#### Scenario: Gate passes
- **WHEN** the child executor preflight prerequisites are satisfied
- **THEN** the gate contract MUST report a passed status
- **AND** it MUST mark the child executor as allowed for promotion
- **AND** it MUST expose a non-empty executor path

#### Scenario: Gate blocks promotion
- **WHEN** any required prerequisite is missing
- **THEN** the gate contract MUST report a blocked status
- **AND** it MUST mark the child executor as not allowed for promotion
- **AND** it MUST expose a failure reason and blockers

### Requirement: Promotion Gate Must Reuse Backend Truth Sources
The system MUST derive promotion gate results from backend truth sources such as preflight checks, binding readiness, merge semantics, and backend readiness, instead of frontend or caller-side recomputation.

#### Scenario: Runtime profile renders gate
- **WHEN** runtime profile is requested
- **THEN** the backend MUST return the promotion gate contract
- **AND** frontend consumers MUST be able to render the gate result directly
- **AND** they MUST NOT recalculate allow/deny state from raw metadata alone

### Requirement: Promotion Gate Must Preserve Relationship Seam Until Promotion
The system MUST keep `delegate_run(...)` in relationship seam mode until the promotion gate explicitly allows promotion.

#### Scenario: Delegate run remains relationship-only
- **WHEN** a delegated child run exists but the promotion gate is blocked
- **THEN** the system MUST keep the delegated run in relationship seam mode
- **AND** it MUST NOT imply that a real child executor has started

### Requirement: Child Executor Promotion Gate Must Be Quality-Gated

The child executor promotion gate MUST be covered by runtime contract smoke and quality gate summary evidence so consumers can detect missing or malformed promotion gate contracts.

#### Scenario: Promotion gate smoke is healthy

- **WHEN** runtime contract smoke evaluates the current runtime profile
- **THEN** it MUST emit a `child_executor_promotion_gate` contract check
- **AND** the check MUST include gate status, allow/deny result, failure reason, blocker count, and recommended next step
- **AND** the check MUST report healthy only when the gate evidence is machine-readable

#### Scenario: Promotion gate remains relationship-only

- **WHEN** the default gate is blocked
- **THEN** the smoke evidence MUST preserve `allowed = false`
- **AND** it MUST NOT imply that a real child executor has started

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
