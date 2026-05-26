# child-executor-dispatch-retry-scheduler-binding-gate Specification

## Purpose

Define the read-only gate that turns child executor dispatch retry scheduler handoff evidence into an explicit scheduler binding decision without scheduling retries or enabling production workers.

## Requirements

### Requirement: Dispatch retry scheduler binding gate MUST be machine-readable

The system MUST expose a side-effect-free `child_executor_dispatch_retry_scheduler_binding_gate` contract that explains whether child executor dispatch retry scheduler handoff evidence has an explicit scheduler binding decision.

The contract MUST include:

- contract version
- overall status
- scheduler binding readiness
- binding source
- handoff readiness
- retryable result detection
- retry audit policy status
- scheduler contract readiness
- production scheduler gate status and readiness
- idempotency/dedupe readiness
- audit timeline readiness
- worker ownership readiness
- bounded attempts readiness
- `will_schedule_retry`
- missing sections
- blocked reason
- next allowed action
- non-goals

#### Scenario: Default binding is blocked

- **WHEN** child executor dispatch retry scheduler handoff evidence is present
- **AND** no explicit scheduler binding decision is requested
- **THEN** the binding gate MUST report blocked
- **AND** it MUST include `scheduler_binding_decision` in missing sections
- **AND** it MUST keep `will_schedule_retry = false`

#### Scenario: Handoff-ready evidence is not scheduling authorization

- **WHEN** handoff evidence is ready
- **AND** scheduler binding decision evidence is complete
- **THEN** the binding gate MAY report ready
- **AND** it MUST keep `will_schedule_retry = false`
- **AND** it MUST explain that execution remains a non-goal for this slice

#### Scenario: Binding blocks when production scheduler gate is blocked

- **WHEN** handoff and scheduler binding evidence are ready
- **AND** production scheduler gate evidence is missing or blocked
- **THEN** the binding gate MUST report blocked
- **AND** it MUST include `production_scheduler_gate` in missing sections
- **AND** it MUST keep `will_schedule_retry = false`

#### Scenario: Binding blocks when audit or idempotency evidence is missing

- **WHEN** handoff and scheduler binding evidence are ready
- **AND** idempotency/dedupe or audit timeline evidence is missing
- **THEN** the binding gate MUST report blocked
- **AND** it MUST include the missing evidence section
- **AND** it MUST keep `will_schedule_retry = false`

#### Scenario: Binding blocks when worker ownership or bounded attempts are missing

- **WHEN** handoff and scheduler binding evidence are ready
- **AND** worker ownership or bounded attempts evidence is missing
- **THEN** the binding gate MUST report blocked
- **AND** it MUST include the missing evidence section
- **AND** it MUST keep `will_schedule_retry = false`

### Requirement: Dispatch retry scheduler binding gate coverage MUST enter runtime gates

Runtime smoke, Quality Gate, Runtime Contract Gate, health trace normalization, and Snapshot MUST expose child executor dispatch retry scheduler binding gate coverage.

#### Scenario: Coverage is complete

- **WHEN** runtime smoke validates default blocked, handoff-ready non-scheduling, production-gate-blocked, missing-audit/idempotency, and missing-worker/bounded-attempt paths
- **THEN** Quality Gate MUST expose `runtime_contract_summary.child_executor_dispatch_retry_scheduler_binding_gate_coverage.binding_smoke = true`
- **AND** Runtime Contract Gate MUST preserve normalized binding gate evidence
- **AND** Snapshot MUST guard stable coverage fields

#### Scenario: Coverage is missing

- **WHEN** a report omits retry scheduler binding gate evidence
- **THEN** Quality Gate and Runtime Contract Gate MUST fail closed with `binding_smoke = false`
- **AND** Snapshot MUST degrade when required summary fields are missing
