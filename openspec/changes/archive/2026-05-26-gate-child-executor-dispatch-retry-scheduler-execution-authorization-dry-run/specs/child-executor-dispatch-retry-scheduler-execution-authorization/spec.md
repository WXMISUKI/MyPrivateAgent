# child-executor-dispatch-retry-scheduler-execution-authorization Specification

## ADDED Requirements

### Requirement: Dispatch retry scheduler execution authorization dry-run MUST be machine-readable

The system MUST expose a side-effect-free `child_executor_dispatch_retry_scheduler_execution_authorization` contract that explains whether child executor dispatch retry scheduler binding evidence is sufficient for a future execution authorization review.

The contract MUST include:

- contract version
- overall status
- execution authorization readiness
- binding gate readiness
- explicit authorization request state
- authorization source
- scheduler contract readiness
- production scheduler gate readiness
- durable schedule readiness
- idempotency/dedupe readiness
- audit timeline readiness
- worker ownership readiness
- bounded attempts readiness
- `will_schedule_retry`
- `retry_scheduled`
- missing sections
- blocked reason
- next allowed action
- non-goals

#### Scenario: Default execution authorization is blocked

- **WHEN** retry scheduler binding gate evidence is present
- **AND** no explicit execution authorization request is present
- **THEN** execution authorization MUST report blocked
- **AND** it MUST include `execution_authorization_request` in missing sections
- **AND** it MUST keep `will_schedule_retry = false`
- **AND** it MUST keep `retry_scheduled = false`

#### Scenario: Ready dry-run does not schedule retry

- **WHEN** binding gate evidence is ready
- **AND** scheduler, production gate, durable schedule, idempotency/dedupe, audit timeline, worker ownership, bounded attempts, and explicit authorization evidence are ready
- **THEN** execution authorization MAY report ready
- **AND** it MUST keep `will_schedule_retry = false`
- **AND** it MUST keep `retry_scheduled = false`
- **AND** it MUST explain that scheduling execution remains a non-goal

#### Scenario: Production scheduler gate blocks execution authorization

- **WHEN** binding gate and explicit authorization evidence are ready
- **AND** production scheduler gate evidence is missing or blocked
- **THEN** execution authorization MUST report blocked
- **AND** it MUST include `production_scheduler_gate` in missing sections
- **AND** it MUST keep `will_schedule_retry = false`

#### Scenario: Durable schedule state blocks execution authorization

- **WHEN** binding gate and explicit authorization evidence are ready
- **AND** durable schedule evidence is missing
- **THEN** execution authorization MUST report blocked
- **AND** it MUST include `durable_schedule_state` in missing sections
- **AND** it MUST keep `retry_scheduled = false`

#### Scenario: Audit or idempotency evidence blocks execution authorization

- **WHEN** binding gate and explicit authorization evidence are ready
- **AND** idempotency/dedupe or audit timeline evidence is missing
- **THEN** execution authorization MUST report blocked
- **AND** it MUST include the missing evidence section
- **AND** it MUST keep `will_schedule_retry = false`

#### Scenario: Worker ownership or bounded attempts block execution authorization

- **WHEN** binding gate and explicit authorization evidence are ready
- **AND** worker ownership or bounded attempts evidence is missing
- **THEN** execution authorization MUST report blocked
- **AND** it MUST include the missing evidence section
- **AND** it MUST keep `will_schedule_retry = false`

### Requirement: Dispatch retry scheduler execution authorization coverage MUST enter runtime gates

Runtime smoke, Quality Gate, Runtime Contract Gate, health trace normalization, and Snapshot MUST expose child executor dispatch retry scheduler execution authorization coverage.

#### Scenario: Coverage is complete

- **WHEN** runtime smoke validates default blocked, ready dry-run non-scheduling, production-gate-blocked, missing-durable-schedule, missing-audit/idempotency, and missing-worker/bounded-attempt paths
- **THEN** Quality Gate MUST expose `runtime_contract_summary.child_executor_dispatch_retry_scheduler_execution_authorization_coverage.authorization_smoke = true`
- **AND** Runtime Contract Gate MUST preserve normalized execution authorization evidence
- **AND** Snapshot MUST guard stable coverage fields

#### Scenario: Coverage is missing

- **WHEN** a report omits retry scheduler execution authorization evidence
- **THEN** Quality Gate and Runtime Contract Gate MUST fail closed with `authorization_smoke = false`
- **AND** Snapshot MUST degrade when required summary fields are missing
