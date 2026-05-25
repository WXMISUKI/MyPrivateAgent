## MODIFIED Requirements

### Requirement: Degraded runtime contract trace MUST preserve recovery retry evidence coverage

`runtime_contract_gate_degraded` trace payloads MUST include normalized `runtime_contract_summary.recovery_retry_evidence_coverage`.

#### Scenario: Trace payload includes recovery retry coverage

- **WHEN** Runtime Contract Gate is degraded and its summary contains recovery retry evidence coverage
- **THEN** the written trace payload includes `recovery_retry_evidence_coverage`
- **AND** retry status, attempt bounds, retryable flag, terminal flag, recovery reason, and idempotency key presence are preserved in normalized compact form
- **AND** exhausted fail-closed evidence can be covered even when the sampled reason is not retryable
