## MODIFIED Requirements

### Requirement: Retry attempts MUST extend recovery operation evidence

Each retry attempt MUST be represented as recovery operation evidence rather than a separate parallel event model.

#### Scenario: Recovery retry evidence enters runtime contract smoke

- **WHEN** runtime contract smoke exercises an SDK recovery entrypoint with explicit retry attempt metadata
- **AND** the recovery attempt fails closed
- **THEN** the smoke output MUST include a `recovery_retry_evidence` check
- **AND** the check MUST preserve compact retry fields including contract version, attempt number, max attempts, retry status, terminal flag, retryable flag, recovery reason, and idempotency key presence
- **AND** exhausted fail-closed smoke evidence MUST NOT require `retryable = true`
- **AND** the check MUST NOT execute automatic retry scheduling
