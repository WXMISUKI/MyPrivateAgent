# recovery-retry-protocol Specification

## Purpose

Define explicit, bounded, and idempotent retry behavior for recovery operations.

## Requirements

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

#### Scenario: Recovery retry evidence enters runtime contract smoke

- **WHEN** runtime contract smoke exercises an SDK recovery entrypoint with explicit retry attempt metadata
- **AND** the recovery attempt fails closed
- **THEN** the smoke output MUST include a `recovery_retry_evidence` check
- **AND** the check MUST preserve compact retry fields including contract version, attempt number, max attempts, retry status, terminal flag, retryable flag, recovery reason, and idempotency key presence
- **AND** exhausted fail-closed smoke evidence MUST NOT require `retryable = true`
- **AND** the check MUST NOT execute automatic retry scheduling

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

#### Scenario: Retry reason is classified

- **WHEN** a retry evidence payload is built for a recovery reason
- **THEN** the payload MUST classify whether the reason is retryable
- **AND** terminal reasons MUST produce `retry.status = terminal`

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

### Requirement: Retry protocol MUST separate opt-in execution from production automatic retry

The recovery retry protocol MUST distinguish explicit caller-enabled retry execution from production automatic retry scheduling.

#### Scenario: Explicit retry seam is used

- **WHEN** a caller explicitly invokes retry scheduling with `enabled = true`
- **THEN** the runtime may execute one bounded retry attempt through supported recovery entrypoints
- **AND** this does not imply automatic retry is enabled by default

#### Scenario: Production automatic retry is requested

- **WHEN** retry execution would be initiated by a background scheduler or default runtime behavior
- **THEN** the runtime MUST first evaluate the production scheduler gate
- **AND** it MUST fail closed if the gate is blocked

### Requirement: Retry protocol MUST preserve backoff and terminal decisions

The recovery retry protocol MUST expose enough machine-readable evidence for backoff scheduling and terminal decisions.

#### Scenario: Retry remains pending

- **WHEN** a retryable operation is not yet eligible by backoff time
- **THEN** the scheduler MUST NOT execute it
- **AND** it returns compact pending evidence with next eligible time

#### Scenario: Terminal decision is reached

- **WHEN** retry classifier reports terminal or exhausted status
- **THEN** scheduler MUST NOT execute another attempt
- **AND** terminal status is preserved in recovery operation/read-model evidence
