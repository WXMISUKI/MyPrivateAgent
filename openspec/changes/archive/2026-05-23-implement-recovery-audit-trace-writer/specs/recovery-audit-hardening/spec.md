# recovery-audit-hardening Specification Delta

## MODIFIED Requirements

### Requirement: Recovery audit MUST correlate trace and operation evidence

Recovery audit MUST correlate operation evidence with trace/audit records without duplicating executable payloads. The first implementation MAY provide an opt-in trace writer without automatically invoking it from SDK recovery execution.

#### Scenario: Recovery operation writes trace evidence

- **WHEN** a recovery operation is recorded
- **THEN** the runtime MAY write a governance trace
- **AND** the trace payload MUST include `operation_id`, `run_id`, `entrypoint`, `operation_status`, `recovery_reason`, and `dedupe_key`
- **AND** it MUST NOT include callable objects, provider clients, handlers, or active stream iterators
- **AND** retry and ownership fields, when present, MUST remain compact summary fields

### Requirement: Recovery audit MUST be idempotent

Recovery audit writing MUST avoid duplicate governance pollution.

#### Scenario: Duplicate operation audit is attempted

- **GIVEN** a trace with the same recovery operation dedupe key already exists
- **WHEN** the audit adapter attempts to write the same operation again
- **THEN** it MUST skip duplicate trace creation
- **AND** it MUST return a machine-readable dedupe result

#### Scenario: Trace service is unavailable

- **WHEN** recovery audit trace writing is requested but the trace service cannot append runtime trace
- **THEN** the writer MUST fail open
- **AND** it MUST return `trace_written = false` with a machine-readable reason
