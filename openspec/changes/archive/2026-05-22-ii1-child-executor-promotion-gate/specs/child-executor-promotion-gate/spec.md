## ADDED Requirements

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
