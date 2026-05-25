# recovery-retry-protocol Specification Delta

## MODIFIED Requirements

### Requirement: Recovery retry MUST be explicit, bounded, and idempotent

The runtime MUST define retry behavior for recovery operations without relying on implicit caller loops. The first implementation MAY expose retry policy and retry evidence without executing automatic retries.

#### Scenario: Retry policy is declared

- **WHEN** a recovery-capable runtime contract is inspected
- **THEN** it MUST expose retry policy fields including `max_attempts`, `backoff_strategy`, `retryable_reasons`, and `terminal_reasons`
- **AND** it MUST state whether retry execution is currently implemented
- **AND** it MUST state whether retry evidence is supported independently from execution

### Requirement: Retry attempts MUST extend recovery operation evidence

Each retry attempt MUST be represented as recovery operation evidence rather than a separate parallel event model.

#### Scenario: Retry attempt is recorded

- **WHEN** a recovery retry attempt starts
- **THEN** the runtime MUST record a recovery operation with `operation_status = attempted`
- **AND** it MUST include `retry.attempt_number`, `retry.max_attempts`, `retry.previous_operation_id`, and `retry.idempotency_key`
- **AND** it MUST preserve the original entrypoint
- **AND** the retry evidence MUST remain compact and non-executable

#### Scenario: Recovery operation has no retry evidence

- **WHEN** a recovery operation is recorded outside a retry attempt
- **THEN** the operation MAY omit the `retry` field
- **AND** existing recovery operation consumers MUST continue to work

### Requirement: Retry MUST only run for retryable failure reasons

The runtime MUST only retry recovery failures that are safe and explicitly classified as retryable.

#### Scenario: Retry reason is classified

- **WHEN** a retry evidence payload is built for a recovery reason
- **THEN** the payload MUST classify whether the reason is retryable
- **AND** terminal reasons MUST produce `retry.status = terminal`
