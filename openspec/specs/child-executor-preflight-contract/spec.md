# child-executor-preflight-contract Specification

## Purpose
Define the child executor preflight contract used to expose binding readiness, blockers, and recommended next steps before promotion.
## Requirements
### Requirement: Child Executor Preflight Must Expose Promotion Readiness
The system MUST provide a machine-readable child executor preflight contract that states whether the current delegated run context is ready to be promoted from a relationship seam to a real child executor.

The contract MUST include:

- a preflight status
- a list of blockers when promotion is not ready
- a recommended next step
- the current binding / merge / backend readiness signals used in the decision

#### Scenario: Promotion is ready
- **WHEN** the SDK can resolve the required continuation bindings, the child merge semantics are complete, and the worker runtime backend is available
- **THEN** the preflight contract MUST report a promotion-ready status
- **AND** it MUST expose an empty blocker list
- **AND** it MUST provide a promotion-oriented next step

#### Scenario: Promotion is blocked
- **WHEN** any required binding, merge semantic, or worker backend prerequisite is missing
- **THEN** the preflight contract MUST report a blocked status
- **AND** it MUST expose the missing prerequisites as blockers
- **AND** it MUST provide a non-promotional next step

### Requirement: Child Executor Preflight Must Remain Side-Effect Free
The system MUST evaluate child executor preflight without creating a child run, mutating persisted run state, or starting a real child executor.

#### Scenario: Preflight is evaluated
- **WHEN** the caller requests a child executor preflight check
- **THEN** the system MUST return a preflight result without creating a new child run
- **AND** it MUST NOT change approval state, continuation state, or merge output state

### Requirement: Child Executor Preflight Must Be Shared Across Backend and Runtime Surface
The system MUST expose the same child executor preflight contract through backend runtime profile and Runtime Surface consumers so the frontend does not need to reconstruct promotion readiness from multiple read models.

#### Scenario: Runtime Surface renders preflight
- **WHEN** runtime profile is requested for a scope with child execution context
- **THEN** the backend MUST include the child executor preflight contract in the returned profile
- **AND** Runtime Surface MUST render that contract directly
- **AND** Runtime Surface MUST NOT recompute promotion readiness from raw metadata or multiple child summary cards

### Requirement: Child Executor Preflight Must Respect Relationship Seam Boundaries
The system MUST keep `delegate_run(...)` as a relationship seam while preflight is being evaluated.

#### Scenario: Delegate run is inspected
- **WHEN** `delegate_run(...)` has been called but the child executor is not yet promoted
- **THEN** the system MUST treat the run as a relationship seam
- **AND** the preflight contract MUST describe why promotion is or is not allowed
- **AND** it MUST NOT imply that a real child executor has already started

### Requirement: Child Executor Preflight Must Use Backend Registry Evidence
Child executor preflight MUST evaluate worker backend readiness through the child executor backend registry rather than treating any non-empty backend string as dispatch ready.

#### Scenario: Backend is known but not dispatch ready
- **WHEN** payload or metadata selects a backend that exists in the registry but is not dispatch ready
- **THEN** preflight MUST report the worker backend requirement as satisfied for backend selection
- **AND** the requirement evidence MUST include the backend registry status and blockers
- **AND** it MUST NOT claim real child executor dispatch is ready

#### Scenario: Backend is unknown
- **WHEN** payload or metadata selects a backend id that is not in the registry
- **THEN** preflight MUST report the worker backend requirement as blocked
- **AND** it MUST expose `unknown_child_executor_backend` as a blocker
