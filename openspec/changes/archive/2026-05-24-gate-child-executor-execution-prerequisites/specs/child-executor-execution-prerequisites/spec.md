## ADDED Requirements

### Requirement: Child Executor Execution Prerequisites Must Be Machine-Readable
The system MUST expose a machine-readable `child_executor_execution_prerequisites` contract that states whether a delegated child run has all prerequisites needed before a real child executor can be started.

The contract MUST include:

- a contract version
- an overall status
- a boolean readiness result
- a list of requirement entries
- a list of missing requirements
- a recommended next step

Each requirement entry MUST include a stable requirement name, a status, compact evidence, and a blocker when the requirement is not ready.

#### Scenario: Prerequisites are blocked
- **WHEN** one or more required child executor execution prerequisites are missing
- **THEN** the contract MUST report a blocked status
- **AND** it MUST set readiness to false
- **AND** it MUST expose the missing requirement names and blockers
- **AND** it MUST NOT imply that a real child executor has started

#### Scenario: Prerequisites are ready
- **WHEN** executor binding, context budget, merge contract, worker backend, recovery boundary, and promotion gate prerequisites are all ready
- **THEN** the contract MUST report a ready status
- **AND** it MUST set readiness to true
- **AND** it MUST expose an empty missing requirement list

### Requirement: Child Executor Execution Prerequisites Must Be Side-Effect Free
The system MUST evaluate child executor execution prerequisites without creating child runs, starting executors, mutating persisted run state, or changing approval/recovery state.

#### Scenario: Prerequisites are evaluated
- **WHEN** a caller requests child executor execution prerequisites
- **THEN** the system MUST return prerequisite evidence
- **AND** it MUST NOT create or execute a child executor
- **AND** it MUST keep the delegated run in relationship seam mode unless a separate future executor implementation explicitly starts execution

### Requirement: Child Executor Execution Prerequisites Must Be Quality-Gated
The runtime contract smoke and quality gate summary MUST expose coverage evidence for the child executor execution prerequisites contract.

#### Scenario: Prerequisite smoke is healthy
- **WHEN** runtime contract smoke evaluates the runtime profile
- **THEN** it MUST emit child executor execution prerequisite evidence
- **AND** the quality gate summary MUST expose `child_executor_execution_prerequisites_coverage`
- **AND** missing or malformed prerequisite evidence MUST fail closed as uncovered
