# child-executor-dispatch-retry-scheduler-handoff Specification

## ADDED Requirements

### Requirement: Dispatch retry scheduler handoff MUST be machine-readable

The system MUST expose a side-effect-free `child_executor_dispatch_retry_scheduler_handoff` contract that explains whether child executor dispatch retry audit evidence is eligible to be handed to a retry scheduler.

The contract MUST include:

- contract version
- overall status
- handoff readiness
- retryable result detection
- retry audit policy status
- scheduler binding status
- idempotency evidence readiness
- audit evidence readiness
- production scheduler gate readiness
- `will_schedule_retry`
- missing sections
- blocked reason
- next allowed action
- non-goals

#### Scenario: Retryable audit evidence is not scheduling authorization

- **WHEN** child executor dispatch retry audit policy reports `retry_policy_status = retryable`
- **AND** no retry scheduler binding has been authorized
- **THEN** the handoff contract MUST report blocked
- **AND** it MUST set `retryable_result_detected = true`
- **AND** it MUST set `will_schedule_retry = false`
- **AND** it MUST include a scheduler binding missing section

#### Scenario: Handoff blocks missing idempotency evidence

- **WHEN** retry audit evidence is retryable but idempotency evidence is missing
- **THEN** the handoff contract MUST report blocked
- **AND** it MUST include `idempotency_evidence` in missing sections
- **AND** it MUST keep `will_schedule_retry = false`

#### Scenario: Handoff blocks missing audit evidence

- **WHEN** retry audit evidence is retryable but audit evidence is missing
- **THEN** the handoff contract MUST report blocked
- **AND** it MUST include `audit_evidence` in missing sections
- **AND** it MUST keep `will_schedule_retry = false`

#### Scenario: Terminal retry audit evidence is not scheduler-eligible

- **WHEN** retry audit policy reports `retry_policy_status = terminal`
- **THEN** the handoff contract MUST report blocked
- **AND** it MUST set `retryable_result_detected = false`
- **AND** it MUST keep `will_schedule_retry = false`

### Requirement: Dispatch retry scheduler handoff coverage MUST enter runtime gates

Runtime smoke, Quality Gate, Runtime Contract Gate, and Snapshot MUST expose child executor dispatch retry scheduler handoff coverage.

#### Scenario: Coverage is complete

- **WHEN** runtime smoke validates retryable-without-scheduler, missing-idempotency, missing-audit, and terminal paths
- **THEN** Quality Gate MUST expose `runtime_contract_summary.child_executor_dispatch_retry_scheduler_handoff_coverage.handoff_smoke = true`
- **AND** Runtime Contract Gate MUST preserve normalized retry scheduler handoff evidence
- **AND** Snapshot MUST guard stable coverage fields

#### Scenario: Coverage is missing

- **WHEN** a report omits retry scheduler handoff evidence
- **THEN** Quality Gate and Runtime Contract Gate MUST fail closed with `handoff_smoke = false`
- **AND** Snapshot MUST degrade when required summary fields are missing
