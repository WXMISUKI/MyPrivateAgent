# Design

## Contract Shape

Add a pure builder, tentatively:

`build_child_executor_dispatch_retry_scheduler_binding_gate_contract(...)`

Inputs:

- `handoff_contract: Mapping[str, Any] | None`
- `retry_scheduler_contract: Mapping[str, Any] | None`
- `production_scheduler_gate: Mapping[str, Any] | None`
- optional booleans for:
  - `scheduler_binding_requested`
  - `idempotency_dedupe_ready`
  - `audit_timeline_ready`
  - `worker_ownership_ready`
  - `bounded_attempts_ready`
- optional `binding_source`

Output:

- `contract_version`
- `overall_status`
- `scheduler_binding_ready`
- `binding_source`
- `handoff_ready`
- `retryable_result_detected`
- `retry_policy_status`
- `scheduler_contract_ready`
- `production_scheduler_gate_status`
- `production_scheduler_gate_ready`
- `idempotency_dedupe_ready`
- `audit_timeline_ready`
- `worker_ownership_ready`
- `bounded_attempts_ready`
- `will_schedule_retry`
- `missing_sections`
- `blocked_reason`
- `next_allowed_action`
- `non_goals`
- compact nested `evidence`

## Readiness Rules

The binding gate can report ready only when:

- a scheduler binding is explicitly requested
- handoff contract is ready
- handoff reports retryable evidence
- scheduler posture is explicitly ready or bound
- production scheduler gate is ready
- idempotency/dedupe evidence is ready
- audit timeline evidence is ready
- worker ownership evidence is ready
- bounded attempts evidence is ready

`will_schedule_retry` remains false for this slice even when the binding gate reports ready. Ready means "binding decision evidence can be consumed by a future scheduler boundary", not "retry work is scheduled."

## Integration

- Attach the binding gate to `dispatch_retry_scheduler_handoff` as nested evidence.
- Runtime smoke emits a dedicated `child_executor_dispatch_retry_scheduler_binding_gate` check.
- Quality Gate and Runtime Contract Gate normalize the check under:
  `runtime_contract_summary.child_executor_dispatch_retry_scheduler_binding_gate_coverage`
- Snapshot guards stable fields for the new coverage subtree.
- Health trace normalization includes a compact coverage label.

## Safety

The default remains blocked and non-executing. Old reports or missing evidence must fail closed to `binding_smoke = false`. No execution path should call `RecoveryRetryScheduler.schedule(...)`, start a background loop, start a worker, or merge child results.
