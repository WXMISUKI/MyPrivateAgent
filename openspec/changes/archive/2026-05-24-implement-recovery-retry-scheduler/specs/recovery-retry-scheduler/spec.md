# recovery-retry-scheduler Specification

## Purpose

Define an opt-in automatic recovery retry scheduler that safely advances retryable recovery operations without duplicating retry semantics.

## ADDED Requirements

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

#### Scenario: Default runtime

- **WHEN** no retry scheduler is configured
- **THEN** retry evidence remains available
- **AND** no automatic retry execution occurs
