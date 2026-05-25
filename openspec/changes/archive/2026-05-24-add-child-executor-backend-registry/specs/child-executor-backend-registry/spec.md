## ADDED Requirements

### Requirement: Child Executor Backend Registry Must Expose Backend Readiness
The system MUST expose a machine-readable child executor backend registry that lists known worker backend candidates and their readiness for real child executor dispatch.

The registry contract MUST include:

- a contract version
- an overall status
- a list of backend entries
- a lookup map keyed by backend id
- default backend id
- blockers for non-ready backends

Each backend entry MUST include backend id, label, status, dispatch readiness, dispatch mode, supported handoff mode, and blockers.

#### Scenario: Default registry is relationship only
- **WHEN** the default registry is built
- **THEN** it MUST expose at least one known backend candidate
- **AND** every default backend MUST report `dispatch_ready = false`
- **AND** it MUST NOT imply that a real child executor has started

#### Scenario: Backend lookup is unknown
- **WHEN** preflight asks for a backend id that is not present in the registry
- **THEN** the registry lookup MUST return blocked evidence
- **AND** the evidence MUST include an `unknown_child_executor_backend` blocker

### Requirement: Child Executor Backend Registry Must Be Side-Effect Free
The backend registry MUST only describe backend capabilities and MUST NOT create child runs, dispatch work, allocate workers, or mutate persisted state.

#### Scenario: Registry is inspected
- **WHEN** SDK or Runtime Surface reads the backend registry contract
- **THEN** the system MUST return compact capability evidence
- **AND** it MUST NOT start a real executor or worker process
