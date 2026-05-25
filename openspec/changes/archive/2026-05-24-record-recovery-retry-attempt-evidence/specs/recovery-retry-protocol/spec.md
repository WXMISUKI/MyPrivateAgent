## MODIFIED Requirements

### Requirement: Retry attempts MUST extend recovery operation evidence

Each retry attempt MUST be represented as recovery operation evidence rather than a separate parallel event model.

#### Scenario: Retry attempt is recorded

- **WHEN** a recovery retry attempt starts
- **THEN** the runtime MUST record a recovery operation with `operation_status = attempted`
- **AND** it MUST include `retry.attempt_number`, `retry.max_attempts`, `retry.previous_operation_id`, and `retry.idempotency_key`
- **AND** it MUST preserve the original entrypoint
- **AND** the retry evidence MUST remain compact and non-executable

#### Scenario: SDK recovery gate records explicit retry evidence

- **WHEN** an SDK recovery entrypoint is called with explicit retry attempt metadata
- **AND** the recovery attempt is blocked or failed closed
- **THEN** the recorded recovery operation MUST include compact `retry` evidence produced by the retry classifier
- **AND** it MUST preserve the entrypoint and operation identity
- **AND** it MUST NOT create a separate retry event model

#### Scenario: Recovery operation has no retry evidence

- **WHEN** a recovery operation is recorded outside a retry attempt
- **THEN** the operation MAY omit the `retry` field
- **AND** existing recovery operation consumers MUST continue to work

