# recovery-retry-scheduler Specification

## Purpose

Define an opt-in automatic recovery retry scheduler that safely advances retryable recovery operations without duplicating retry semantics.

## Requirements

### Requirement: Scheduler MUST honor retry policy and classifier evidence

The scheduler MUST use `recovery_operation_contract.retry_policy` and compact retry evidence to decide whether a recovery operation can be retried.

#### Scenario: Retryable operation

- **WHEN** the previous recovery operation is retryable
- **AND** max attempts are not exhausted
- **THEN** the scheduler may create a bounded next retry attempt
- **AND** the attempt includes idempotency evidence

#### Scenario: Terminal operation

- **WHEN** the previous recovery operation is terminal
- **THEN** the scheduler MUST NOT schedule another retry
- **AND** it records a compact terminal decision

### Requirement: Scheduler MUST be opt-in

Automatic retry execution MUST remain disabled unless an explicit runtime or caller configuration enables it.

Production automatic retry MUST additionally require a ready production scheduler gate before any background or default retry execution can run.

#### Scenario: Default runtime

- **WHEN** no retry scheduler is configured
- **THEN** retry evidence remains available
- **AND** no automatic retry execution occurs

#### Scenario: Explicitly enabled retry

- **WHEN** the scheduler is explicitly enabled for a retryable recovery operation
- **THEN** it MUST execute only the approved recovery entrypoint
- **AND** the resulting recovery operation MUST include compact retry attempt evidence

#### Scenario: Production gate is blocked

- **WHEN** automatic retry is requested but production scheduler gate is blocked
- **THEN** the scheduler MUST remain in explicit opt-in mode
- **AND** no background or default retry execution occurs

### Requirement: Runtime quality gates MUST cover retry scheduler evidence

The runtime contract smoke and quality gate summary MUST expose retry scheduler evidence separately from retry attempt evidence.

#### Scenario: Smoke proves opt-in execution boundary

- **WHEN** runtime contract smoke runs
- **THEN** it MUST include a `recovery_retry_scheduler` check
- **AND** the check MUST prove the default disabled decision and an explicitly enabled retry execution
