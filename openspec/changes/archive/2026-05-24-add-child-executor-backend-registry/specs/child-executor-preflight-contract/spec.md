## ADDED Requirements

### Requirement: Child Executor Preflight Must Use Backend Registry Evidence
Child executor preflight MUST evaluate worker backend readiness through the child executor backend registry rather than treating any non-empty backend string as dispatch ready.

#### Scenario: Backend is known but not dispatch ready
- **WHEN** payload or metadata selects a backend that exists in the registry but is not dispatch ready
- **THEN** preflight MUST report the worker backend requirement as blocked
- **AND** the requirement evidence MUST include the backend registry status and blockers
- **AND** it MUST keep the child executor in relationship seam mode

#### Scenario: Backend is unknown
- **WHEN** payload or metadata selects a backend id that is not in the registry
- **THEN** preflight MUST report the worker backend requirement as blocked
- **AND** it MUST expose `unknown_child_executor_backend` as a blocker
