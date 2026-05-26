# Design: Child Executor Dispatch Retry Scheduler Execution Authorization Dry-Run

## Contract Shape

Add a pure builder:

`build_child_executor_dispatch_retry_scheduler_execution_authorization_contract(...)`

Inputs:

- `retry_scheduler_binding_gate`
- `retry_scheduler_contract`
- `production_scheduler_gate`
- `explicit_authorization_requested`
- `authorization_source`
- `durable_schedule_ready`
- `idempotency_dedupe_ready`
- `audit_timeline_ready`
- `worker_ownership_ready`
- `bounded_attempts_ready`

Output:

- `contract_version`
- `overall_status`
- `execution_authorization_ready`
- `binding_gate_ready`
- `explicit_authorization_requested`
- `authorization_source`
- `production_scheduler_gate_ready`
- `durable_schedule_ready`
- `idempotency_dedupe_ready`
- `audit_timeline_ready`
- `worker_ownership_ready`
- `bounded_attempts_ready`
- `will_schedule_retry`
- `retry_scheduled`
- `missing_sections`
- `blocked_reason`
- `next_allowed_action`
- `non_goals`
- compact nested evidence for binding, scheduler, production gate, and required execution evidence

## Readiness Rules

The dry-run reports `ready` only when all are true:

- binding gate exists and is ready
- explicit execution authorization request is present
- authorization source is present
- retry scheduler contract is ready
- production scheduler gate is ready
- durable schedule evidence is ready
- idempotency/dedupe evidence is ready
- audit timeline evidence is ready
- worker ownership evidence is ready
- bounded attempts evidence is ready

Regardless of readiness:

- `will_schedule_retry = false`
- `retry_scheduled = false`

## Fail-Closed Behavior

Missing or malformed evidence is converted into machine-readable `missing_sections`. The contract must remain side-effect-free and must never infer production authorization from binding gate readiness alone.

## Integration

The contract will be attached under retry scheduler binding gate evidence as:

`retry_scheduler_binding_gate.retry_scheduler_execution_authorization`

Runtime smoke, Quality Gate summary, Runtime Contract Gate, health trace normalization, and Snapshot will expose:

`runtime_contract_summary.child_executor_dispatch_retry_scheduler_execution_authorization_coverage`

## Verification

Focused tests will cover:

- default blocked when explicit authorization is absent
- ready dry-run but non-scheduling
- blocked production scheduler gate
- blocked missing durable schedule
- blocked missing audit/idempotency
- blocked missing worker ownership/bounded attempts
- fail-closed summary normalization
- snapshot stable field protection
