## ADDED Requirements

### Requirement: Runtime Core terminology is formally defined
The system MUST define the official Runtime Core terminology for `query`, `run`, `child run`, `scheduler run`, `approval`, `artifact`, `trace`, and `audit` as contract-level concepts, not just display copy.

#### Scenario: Terms are consumed consistently
- **WHEN** a contract, architecture document, or governance view references one of the Runtime Core concepts
- **THEN** it MUST use the same formal meaning for that concept across backend, frontend, and docs

### Requirement: Query and run are distinct concepts
The system MUST treat `query` as the full lifecycle of a user request and `run` as a concrete execution instance within that lifecycle.

#### Scenario: Query vs run distinction
- **WHEN** a contract or view describes a user request lifecycle
- **THEN** `query` MUST NOT be used as a synonym for a single message or single model completion
- **AND** `run` MUST NOT be used as a synonym for the entire lifecycle

### Requirement: Child run naming is unambiguous
The system MUST treat `child_run_id` as the formal Runtime Core identifier for delegated child execution, and MUST treat `child_execution_id` as a compatibility key only.

#### Scenario: Child execution identity
- **WHEN** backend, runtime contract, or front-end display refers to delegated execution identity
- **THEN** `child_run_id` MUST be the primary term
- **AND** `child_execution_id` MAY exist only as a compatibility alias or repository-level key

### Requirement: Scheduler run identity is distinct
The system MUST treat `scheduler run` as the scheduling-layer execution identity for fan-out / fan-in orchestration and MUST NOT use it as a synonym for `query` or `child run`.

#### Scenario: Scheduler run is not query
- **WHEN** a contract describes scheduler orchestration
- **THEN** the term `scheduler run` MUST refer to the scheduling context only
- **AND** it MUST NOT replace `query` or `child run` in lifecycle descriptions

### Requirement: Approval is a first-class governance object
The system MUST define `approval` as a durable, replayable governance decision object that records requester, request, state, processing time, and outcome.

#### Scenario: Approval is durable
- **WHEN** the runtime or governance layer records an approval-related event
- **THEN** the event MUST be representable as a replayable approval object
- **AND** it MUST NOT be reduced to a temporary UI warning or boolean flag

### Requirement: Artifact is a reusable result object
The system MUST define `artifact` as a reusable runtime result object that can be referenced, replayed, or attached to contracts and MUST NOT equate every payload with an artifact.

#### Scenario: Artifact vs payload
- **WHEN** a runtime payload is produced
- **THEN** the payload MUST only be considered an artifact if it is explicitly designed as a referencable result object

### Requirement: Trace and audit remain distinct
The system MUST keep `trace` and `audit` as distinct event flows, where `trace` represents execution evidence and `audit` represents governance record-keeping.

#### Scenario: Trace/audit distinction
- **WHEN** a governance view displays runtime evidence
- **THEN** trace and audit MAY be displayed together
- **BUT** they MUST NOT be treated as identical or complete copies of one another

### Requirement: Durable state is distinguished from runtime state
The system MUST distinguish durable state from runtime state in architecture and contract discussions.

#### Scenario: State classification
- **WHEN** a state survives process restarts or later review
- **THEN** it MUST be treated as durable state
- **WHEN** a state only exists during the current execution window
- **THEN** it MUST be treated as runtime state

### Requirement: Control plane is distinct from execution plane
The system MUST distinguish control plane responsibilities from execution plane responsibilities in runtime contracts and architecture documentation.

#### Scenario: Plane separation
- **WHEN** a concept decides how execution should happen
- **THEN** it MUST be treated as control plane
- **WHEN** a concept performs the actual work
- **THEN** it MUST be treated as execution plane

