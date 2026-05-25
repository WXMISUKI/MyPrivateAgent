## ADDED Requirements

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
