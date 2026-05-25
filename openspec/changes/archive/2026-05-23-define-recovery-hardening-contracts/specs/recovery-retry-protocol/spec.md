# recovery-retry-protocol Specification

## ADDED Requirements

### Requirement: Recovery retry MUST be explicit, bounded, and idempotent

The runtime MUST define retry behavior for recovery operations without relying on implicit caller loops.

#### Scenario: Retry policy is declared

- **WHEN** a recovery-capable runtime contract is inspected
- **THEN** it MUST expose retry policy fields including `max_attempts`, `backoff_strategy`, `retryable_reasons`, and `terminal_reasons`
- **AND** it MUST state whether retry execution is currently implemented

### Requirement: Retry attempts MUST extend recovery operation evidence

Each retry attempt MUST be represented as recovery operation evidence rather than a separate parallel event model.

#### Scenario: Retry attempt is recorded

- **WHEN** a recovery retry attempt starts
- **THEN** the runtime MUST record a recovery operation with `operation_status = attempted`
- **AND** it MUST include `retry.attempt_number`, `retry.max_attempts`, `retry.previous_operation_id`, and `retry.idempotency_key`
- **AND** it MUST preserve the original entrypoint

### Requirement: Retry MUST only run for retryable failure reasons

The runtime MUST only retry recovery failures that are safe and explicitly classified as retryable.

#### Scenario: Retryable transient failure

- **GIVEN** a recovery attempt fails with a retryable reason such as `transient_workspace_unavailable`
- **WHEN** retry attempts remain
- **THEN** the runtime MAY schedule or execute another recovery attempt
- **AND** it MUST use the same idempotency key for the same logical recovery action

#### Scenario: Non-retryable recovery blocker

- **GIVEN** a recovery attempt fails with `missing_registered_binding`, `denied`, `already_resolved`, `stale_worker_fencing_token`, or `worker_ownership_lost`
- **WHEN** retry policy evaluates the result
- **THEN** the runtime MUST NOT retry
- **AND** it MUST mark retry status as `terminal`

### Requirement: Exhausted retries MUST fail closed

Retry exhaustion MUST produce a terminal recovery operation state.

#### Scenario: Retry attempts are exhausted

- **WHEN** the final allowed retry attempt fails
- **THEN** the runtime MUST record `operation_status = failed`
- **AND** it MUST set `retry.status = exhausted`
- **AND** it MUST expose the terminal reason through Runtime Surface recovery read model

### Requirement: Retry MUST respect worker ownership when implemented

Retry execution MUST not bypass worker ownership.

#### Scenario: Retry requires valid ownership

- **GIVEN** worker ownership is implemented
- **WHEN** a retry attempt starts
- **THEN** the runtime MUST validate the active worker lease and fencing token
- **AND** it MUST block the retry if ownership is lost
