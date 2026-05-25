# runtime-contract-trace-recovery-retry-evidence Specification

## Purpose

Ensure degraded Runtime Contract Gate governance traces preserve recovery retry evidence coverage as machine-readable audit metadata.

## Requirements

### Requirement: Degraded runtime contract trace MUST preserve recovery retry evidence coverage

`runtime_contract_gate_degraded` trace payloads MUST include normalized `runtime_contract_summary.recovery_retry_evidence_coverage`.

#### Scenario: Trace payload includes recovery retry coverage

- **WHEN** Runtime Contract Gate is degraded and its summary contains recovery retry evidence coverage
- **THEN** the written trace payload includes `recovery_retry_evidence_coverage`
- **AND** retry status, attempt bounds, retryable flag, terminal flag, recovery reason, and idempotency key presence are preserved in normalized compact form
- **AND** exhausted fail-closed evidence can be covered even when the sampled reason is not retryable

#### Scenario: Missing recovery retry coverage fails closed

- **WHEN** Runtime Contract Gate summary has no object `recovery_retry_evidence_coverage`
- **THEN** the trace payload summary contains `recovery_retry_evidence_coverage.retry_smoke = false`
- **AND** it emits stable empty default evidence

### Requirement: Recovery retry coverage MUST affect degraded trace fingerprint

Runtime Contract Gate degraded fingerprints and dedupe keys MUST change when recovery retry evidence coverage changes.

#### Scenario: Recovery retry coverage change writes a new trace

- **WHEN** two degraded Runtime Contract Gate profiles have the same failed checks but different `recovery_retry_evidence_coverage.retry_smoke`
- **THEN** their fingerprints are different
- **AND** both degraded states can be recorded as distinct governance traces

### Requirement: Degraded runtime contract trace detail MUST expose recovery retry coverage state

The backend trace detail for `runtime_contract_gate_degraded` MUST include a compact recovery retry evidence coverage label.

#### Scenario: Recovery retry evidence is covered

- **WHEN** normalized `recovery_retry_evidence_coverage.retry_smoke = true`
- **THEN** trace detail includes `recovery_retry=covered`

#### Scenario: Recovery retry evidence is missing

- **WHEN** normalized retry coverage is present but not aligned
- **THEN** trace detail includes `recovery_retry=missing`

#### Scenario: Runtime contract summary is absent

- **WHEN** Runtime Contract Gate lacks an object `runtime_contract_summary`
- **THEN** trace detail includes `recovery_retry=unknown`
