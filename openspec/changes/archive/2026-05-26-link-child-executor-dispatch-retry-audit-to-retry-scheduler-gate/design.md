# Design

## Contract Shape

Add a pure builder, tentatively:

`build_child_executor_dispatch_retry_scheduler_handoff_contract(...)`

Inputs:

- `retry_audit_policy: Mapping[str, Any] | None`
- `retry_scheduler_contract: Mapping[str, Any] | None`
- optional `scheduler_bound: bool`
- optional `idempotency_evidence: Mapping[str, Any] | None`
- optional `audit_evidence: Mapping[str, Any] | None`

Output:

- `contract_version`
- `overall_status`
- `retry_scheduler_handoff_ready`
- `retryable_result_detected`
- `retry_policy_status`
- `scheduler_bound`
- `idempotency_evidence_ready`
- `audit_evidence_ready`
- `production_scheduler_gate_ready`
- `will_schedule_retry`
- `missing_sections`
- `blocked_reason`
- `next_allowed_action`
- `non_goals`
- compact nested `evidence`

## Readiness Rules

The handoff can only report ready when:

- retry audit policy is ready
- retry policy status is `retryable`
- idempotency evidence is present
- audit evidence is present
- scheduler binding evidence is present
- production scheduler gate is ready only when a default/production scheduling path is being claimed

This change will keep the default and smoke sample blocked because no scheduler binding is being authorized. It may include an explicit non-scheduling ready-to-inspect sample where retryable evidence is recognized but `will_schedule_retry` remains false.

## Integration

- Attach the handoff contract to `dispatch_result_handoff.dispatch_result_retry_audit_policy` or expose it as a sibling field in the result handoff contract.
- Runtime smoke emits a dedicated `child_executor_dispatch_retry_scheduler_handoff` check.
- Quality Gate and Runtime Contract Gate normalize the check under:
  `runtime_contract_summary.child_executor_dispatch_retry_scheduler_handoff_coverage`
- Snapshot guard adds stable fields for the coverage subtree.

## Safety

`will_schedule_retry` remains false for this slice. The handoff contract is evidence only. Missing fields fail closed and old reports without the check degrade coverage instead of implying scheduling support.
