# Design

## Contract

`build_worker_ownership_postgres_vendor_lock_production_gate_wiring_decision_contract(...)` returns:

- `contract_version`
- `overall_status`
- `ready`
- `decision_recorded`
- `decision_id`
- `approved_by`
- `approved_at`
- `semantics_binding_status`
- `candidate_semantics_status`
- `target_backend`
- `lock_adapter_kind`
- `production_rollout_confirmed`
- `rollback_plan_reference`
- `fallback_policy_reference`
- `wiring_allowed`
- `will_update_production_gate`
- `will_enable_production_lock`
- `executes_advisory_lock`
- `sql_row_lease_is_vendor_lock`
- `semantics_binding`
- `vendor_lock_semantics_candidate`
- `missing_sections`
- `next_allowed_action`
- `non_goals`

## Readiness

The decision is ready only when:

- The source semantics binding is ready.
- The nested vendor lock semantics candidate is ready.
- A decision id, approver, and approval timestamp are present.
- Production rollout confirmation evidence is present.
- Rollback and fallback references are present.
- The target remains `postgres` and `postgres_advisory_lock`.
- SQL row lease/fencing remains explicitly not a vendor lock.

Even when ready:

- `wiring_allowed = true`
- `will_update_production_gate = false`
- `will_enable_production_lock = false`
- `executes_advisory_lock = false`

The decision says the candidate may be wired by a future explicit production gate path; it does not perform that wiring.

## Runtime Coverage

Runtime smoke emits default and ready decision fields. Quality Gate and Runtime Contract Gate normalize those fields into `runtime_contract_summary.worker_ownership_store_mode_coverage`, and old reports fail closed.
