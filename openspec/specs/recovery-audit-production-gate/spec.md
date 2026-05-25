# recovery-audit-production-gate Specification

## Purpose

Define machine-readable production readiness evidence for recovery operation history, audit summaries, and optional trace correlation before durable cross-process recovery can become default behavior.

## Requirements

### Requirement: Recovery audit production readiness MUST be machine-readable

The runtime MUST expose compact recovery audit production readiness before production cross-process recovery can become default behavior.

The contract MUST include:

- contract version
- readiness flag
- operation history support
- audit summary support
- timeline writer availability
- idempotent trace dedupe support
- authorization source flag
- required evidence
- non-goals

#### Scenario: Audit readiness is available

- **WHEN** compact recovery operation history, audit summary, and opt-in trace writer evidence are available
- **THEN** recovery audit readiness reports `ready = true`
- **AND** `authorization_source = false`

#### Scenario: Audit evidence is missing

- **WHEN** operation history or audit summary evidence is missing
- **THEN** recovery audit readiness reports blocked evidence
- **AND** production recovery gate includes `recovery_audit_operation_history` in missing sections

### Requirement: Recovery audit readiness MUST NOT authorize recovery execution

Recovery audit readiness MUST remain governance evidence only.

#### Scenario: Audit is ready but ownership is missing

- **WHEN** recovery audit readiness is ready
- **AND** worker ownership production gate is missing
- **THEN** production recovery remains blocked
- **AND** audit evidence MUST NOT be treated as worker lease validation

### Requirement: Runtime quality gates MUST cover recovery audit readiness

Runtime contract smoke, Quality Gate summary, Runtime Contract Gate, and snapshot guard MUST expose recovery audit operation history coverage.

#### Scenario: Smoke proves audit readiness

- **WHEN** runtime contract smoke runs
- **THEN** it includes recovery audit production readiness evidence
- **AND** quality gates expose `recovery_audit_operation_history_coverage.audit_smoke`
