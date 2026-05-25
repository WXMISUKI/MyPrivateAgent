## ADDED Requirements

### Requirement: Recovery retry evidence MUST be classifiable before execution
The runtime MUST provide a reusable retry evidence classifier so recovery retry state can be audited before automatic retry execution is implemented.

#### Scenario: Terminal reason is classified
- **WHEN** retry evidence is built for `missing_registered_binding`, `denied`, `already_resolved`, `stale_worker_fencing_token`, or `worker_ownership_lost`
- **THEN** the evidence MUST report `retryable = false`
- **AND** it MUST report `terminal = true`
- **AND** it MUST set `retry.status = terminal`

#### Scenario: Retryable reason is classified
- **WHEN** retry evidence is built for a retryable transient reason before attempts are exhausted
- **THEN** the evidence MUST report `retryable = true`
- **AND** it MUST report `terminal = false`
- **AND** it MUST set `retry.status = retryable`

#### Scenario: Retry attempts are exhausted
- **WHEN** retry evidence is built with `attempt_number >= max_attempts` for a retryable reason
- **THEN** the evidence MUST set `retry.status = exhausted`
- **AND** it MUST report `terminal = true`
- **AND** the evidence MUST preserve the idempotency key

