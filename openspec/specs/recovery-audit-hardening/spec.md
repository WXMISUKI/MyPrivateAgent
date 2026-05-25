# recovery-audit-hardening Specification

## Purpose

Define governance-grade recovery audit summaries and trace correlation for recovery operation evidence.

## Requirements

### Requirement: Recovery audit MUST provide a governance-grade summary

The runtime MUST provide a compact audit summary for recovery operations that can be consumed by Runtime Surface, Governance Timeline, and quality gates. The first implementation MAY provide a read-side summary without writing governance trace records.

#### Scenario: Audit summary is available

- **WHEN** a run has recovery operation history
- **THEN** the Runtime Surface recovery read model MUST expose a recovery audit summary
- **AND** the summary MUST include latest status, latest entrypoint, latest reason, operation counts, retry counts, ownership status, and terminal status
- **AND** the summary MUST be derived from compact recovery operation evidence rather than executable internals
- **AND** production audit readiness MAY use this summary as governance evidence, not as execution authorization

#### Scenario: No operation history exists

- **WHEN** Runtime Surface has no recovery operation history for a run
- **THEN** it MUST still expose an empty recovery audit summary
- **AND** the summary MUST report `operation_count = 0`

### Requirement: Recovery audit MUST correlate trace and operation evidence

Recovery audit MUST correlate operation evidence with trace/audit records without duplicating executable payloads. The first trace writer implementation MAY be opt-in and not automatically invoked from SDK recovery execution.

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

### Requirement: Recovery audit MUST expose failure and retry distribution

Audit summary MUST make repeated failure patterns observable.

#### Scenario: Recovery has multiple failed or blocked attempts

- **WHEN** recovery operation history contains multiple blocked, failed, or retried operations
- **THEN** the audit summary MUST include counts by `operation_status`, `entrypoint`, and `recovery_reason`
- **AND** it MUST identify the latest terminal reason if one exists
- **AND** it MUST include retry status counts when retry evidence exists

### Requirement: Recovery audit summary MUST consume retry evidence

Recovery audit summary MUST expose retry distribution from compact recovery operation evidence without requiring consumers to scan raw history.

#### Scenario: Retry status distribution is summarized

- **WHEN** recovery operation history contains retry evidence
- **THEN** `recovery_audit_summary.retry_status_counts` MUST count retry statuses
- **AND** it MUST expose the latest retry status
- **AND** it MUST expose the latest retry terminal reason when the latest retry evidence is terminal

#### Scenario: SDK-gate retry attempt evidence is summarized

- **WHEN** SDK recovery gates record retry attempt evidence inside recovery operation history
- **THEN** recovery audit summary MUST summarize that evidence exactly like helper-built operation evidence
- **AND** consumers MUST NOT need to scan SDK events or raw metadata to infer retry status

#### Scenario: No retry evidence is present

- **WHEN** recovery operation history contains no retry evidence
- **THEN** `recovery_audit_summary.retry_status_counts` MUST be empty
- **AND** latest retry fields MUST remain empty rather than inferred from operation status alone

### Requirement: Recovery audit MUST remain separated from execution authorization

Recovery audit MUST not grant execution authority.

#### Scenario: Audit summary reports worker ownership

- **WHEN** audit summary includes worker ownership fields
- **THEN** consumers MUST treat them as evidence only
- **AND** they MUST NOT use audit summary as the source of truth for lease validation
- **AND** the summary MUST explicitly identify that it is not an authorization source

#### Scenario: Audit production gate is ready

- **WHEN** recovery audit production readiness reports ready
- **THEN** it proves operation history and audit summary evidence only
- **AND** it MUST NOT authorize recovery execution or worker ownership validation
