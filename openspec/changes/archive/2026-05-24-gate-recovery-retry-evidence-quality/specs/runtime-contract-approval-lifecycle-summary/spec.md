## MODIFIED Requirements

### Requirement: Runtime contract summary MUST expose recovery retry evidence coverage

The Quality Gate runtime contract summary MUST expose recovery retry evidence coverage as a first-class machine-readable coverage object.

#### Scenario: Recovery retry evidence check is healthy

- **WHEN** runtime contract smoke emits `recovery_retry_evidence` with `ok = true`
- **AND** the check proves compact exhausted retry evidence for an SDK fail-closed recovery operation
- **THEN** the runtime contract summary includes `recovery_retry_evidence_coverage.retry_smoke = true`
- **AND** it preserves retry status, attempt bounds, terminal flag, recovery reason, and idempotency key presence

#### Scenario: Recovery retry evidence check is missing

- **WHEN** a legacy report lacks `recovery_retry_evidence`
- **THEN** the runtime contract summary includes `recovery_retry_evidence_coverage.retry_smoke = false`
- **AND** it emits stable empty default evidence

### Requirement: Runtime contract gates MUST guard recovery retry evidence summary shape

Runtime Contract Gate and artifact schema guards MUST treat recovery retry evidence coverage as part of the stable runtime contract summary.

#### Scenario: Runtime Contract Gate normalizes retry coverage

- **WHEN** a quality gate report already includes `recovery_retry_evidence_coverage`
- **THEN** Runtime Contract Gate normalizes the field into the runtime contract surface
- **AND** malformed or contradictory retry evidence MUST fail closed with `retry_smoke = false`

#### Scenario: Artifact schema summary field is missing

- **WHEN** a runtime contract summary lacks `recovery_retry_evidence_coverage.retry_smoke`
- **THEN** the runtime contract artifact schema reports the summary as degraded
