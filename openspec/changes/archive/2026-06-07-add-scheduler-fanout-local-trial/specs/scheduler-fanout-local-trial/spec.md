## ADDED Requirements

### Requirement: Scheduler fan-out local trial is available
The system SHALL provide a deterministic local trial that verifies SchedulerService fan-out, child result collection, and parent merge without invoking real child executor backends.

#### Scenario: Fan-out local trial passes
- **GIVEN** a local plan item declares at least two child roles
- **WHEN** the scheduler fan-out local trial runs in success mode
- **THEN** the report decision is `go`
- **AND** it includes a scheduler run id, child run ids, child statuses, merge status, merged output, and recommended next action

#### Scenario: Fan-out local trial reviews partial failure
- **GIVEN** a local plan item declares at least two child roles
- **WHEN** the scheduler fan-out local trial marks one child as failed and merges outputs
- **THEN** the report decision is `review`
- **AND** the merge status is `partial_failed`
- **AND** the failed child reason is visible in the report

#### Scenario: Fan-out local trial is blocked
- **GIVEN** no valid plan item or insufficient child roles are available
- **WHEN** the scheduler fan-out local trial runs
- **THEN** the report decision is `blocked`
- **AND** it includes a machine-readable reason code, blockers, and recovery action

### Requirement: Scheduler fan-out local trial preserves runtime boundaries
The scheduler fan-out local trial SHALL remain a deterministic local diagnostic and SHALL NOT enable production execution behavior.

#### Scenario: Local trial runs
- **WHEN** the scheduler fan-out local trial runs
- **THEN** it does not invoke real child executor backends
- **AND** it does not start workers, invoke sandbox adapters, schedule retries, call a real LLM, call `/api/chat`, or change default runtime behavior

### Requirement: Scheduler fan-out local trial is exposed through CLI
The system SHALL expose the scheduler fan-out local trial through a local CLI command.

#### Scenario: CLI trial runs
- **WHEN** a developer runs `python backend/scripts/scheduler_fanout_local_trial.py`
- **THEN** the CLI prints compact JSON
- **AND** exits with `0` for `go`, `2` for `review`, and `1` for `blocked`
