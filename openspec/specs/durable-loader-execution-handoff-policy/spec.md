# durable-loader-execution-handoff-policy Specification

## Purpose

Define the explicit handoff policy between DurableRecoveryLoader and a future recovery executor without executing recovery by default.

## Requirements

### Requirement: Durable loader handoff policy MUST be machine-readable

The runtime MUST expose a compact handoff policy before a DurableRecoveryLoader candidate can be handed to any recovery executor.

The contract MUST include:

- contract version
- policy kind
- default handoff flag
- allowed entrypoints
- required evidence
- fail-closed reasons
- non-execution guarantees

#### Scenario: Default handoff is blocked

- **WHEN** a loader candidate is ready
- **AND** no explicit handoff request is present
- **THEN** handoff decision reports `status = blocked`
- **AND** `blocked_reason = explicit_handoff_required`
- **AND** `will_execute = false`

#### Scenario: Explicit handoff lacks executor binding

- **WHEN** a loader candidate is ready
- **AND** explicit handoff is requested
- **AND** no recovery executor binding exists
- **THEN** handoff decision reports `status = blocked`
- **AND** `blocked_reason = recovery_executor_not_bound`
- **AND** `will_execute = false`

### Requirement: Handoff policy MUST NOT execute recovery

Handoff policy readiness MUST NOT execute recovery, deserialize callable payloads, or enable default production recovery by itself.

#### Scenario: Policy exists but production recovery remains blocked

- **WHEN** handoff policy evidence is present
- **THEN** DurableRecoveryLoader remains read-only
- **AND** production recovery remains blocked until the other production gate sections are ready

### Requirement: Runtime quality gates MUST cover handoff policy evidence

Runtime contract smoke, Quality Gate summary, Runtime Contract Gate, and snapshot guard MUST expose durable loader handoff coverage.

#### Scenario: Smoke proves blocked default and explicit paths

- **WHEN** runtime contract smoke runs
- **THEN** it includes handoff policy evidence
- **AND** it covers default blocked and explicit-no-executor blocked decisions
