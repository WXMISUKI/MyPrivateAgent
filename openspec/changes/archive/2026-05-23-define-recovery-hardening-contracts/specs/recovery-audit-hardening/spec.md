# recovery-audit-hardening Specification

## ADDED Requirements

### Requirement: Recovery audit MUST provide a governance-grade summary

The runtime MUST provide a compact audit summary for recovery operations that can be consumed by Runtime Surface, Governance Timeline, and quality gates.

#### Scenario: Audit summary is available

- **WHEN** a run has recovery operation history
- **THEN** the Runtime Surface recovery read model MUST expose a recovery audit summary
- **AND** the summary MUST include latest status, latest entrypoint, latest reason, operation counts, retry counts, ownership status, and terminal status

### Requirement: Recovery audit MUST correlate trace and operation evidence

Recovery audit MUST correlate operation evidence with trace/audit records without duplicating executable payloads.

#### Scenario: Recovery operation writes trace evidence

- **WHEN** a recovery operation is recorded
- **THEN** the runtime MAY write a governance trace
- **AND** the trace payload MUST include `operation_id`, `run_id`, `entrypoint`, `operation_status`, `recovery_reason`, and `dedupe_key`
- **AND** it MUST NOT include callable objects, provider clients, handlers, or active stream iterators

### Requirement: Recovery audit MUST be idempotent

Recovery audit writing MUST avoid duplicate governance pollution.

#### Scenario: Duplicate operation audit is attempted

- **GIVEN** a trace with the same recovery operation dedupe key already exists
- **WHEN** the audit adapter attempts to write the same operation again
- **THEN** it MUST skip duplicate trace creation
- **AND** it MUST return a machine-readable dedupe result

### Requirement: Recovery audit MUST expose failure and retry distribution

Audit summary MUST make repeated failure patterns observable.

#### Scenario: Recovery has multiple failed or blocked attempts

- **WHEN** recovery operation history contains multiple blocked, failed, or retried operations
- **THEN** the audit summary MUST include counts by `operation_status`, `entrypoint`, and `recovery_reason`
- **AND** it MUST identify the latest terminal reason if one exists

### Requirement: Recovery audit MUST remain separated from execution authorization

Recovery audit MUST not grant execution authority.

#### Scenario: Audit summary reports worker ownership

- **WHEN** audit summary includes worker ownership fields
- **THEN** consumers MUST treat them as evidence only
- **AND** they MUST NOT use audit summary as the source of truth for lease validation
