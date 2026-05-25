# Design

## Contract

`build_worker_ownership_postgres_vendor_lock_semantics_binding_contract(...)` returns a side-effect-free object with:

- `contract_version`
- `overall_status`
- `ready`
- `target_binding_status`
- `target_binding_contract_version`
- `postgres_execution_seam_status`
- `postgres_probe_status`
- `vendor_lock_adapter_status`
- `vendor_lock_semantics_status`
- `target_decision_status`
- `target_backend`
- `lock_adapter_kind`
- `lock_scope`
- `fencing_strategy`
- `ttl_renewal_strategy`
- `failover_strategy`
- `stale_owner_cleanup_strategy`
- `postgres_probe`
- `vendor_lock_adapter`
- `vendor_lock_semantics`
- `will_enable_production_lock`
- `will_update_production_gate`
- `executes_advisory_lock`
- `sql_row_lease_is_vendor_lock`
- `missing_sections`
- `next_allowed_action`
- `non_goals`

## Readiness

The binding is `ready` only when:

- PostgreSQL target artifact binding is ready.
- Target decision is ready.
- PostgreSQL execution seam evidence is ready.
- PostgreSQL probe evidence is ready and non-executing.
- Vendor lock adapter contract is ready.
- Vendor lock semantics contract is ready as a candidate.
- SQL row lease/fencing remains explicitly not a vendor lock.

Even when the binding is ready:

- `will_enable_production_lock = false`
- `will_update_production_gate = false`
- `executes_advisory_lock = false`

The nested vendor lock semantics candidate may report `production_lock_allowed = true` as descriptive readiness evidence, but this contract does not pass it into the default production gate.

## Runtime Coverage

Runtime smoke emits:

- default binding blocker fields
- ready candidate fields
- nested semantics/adapter/probe status fields
- non-execution and non-enablement fields

Quality Gate and Runtime Contract Gate normalize these fields into `runtime_contract_summary.worker_ownership_store_mode_coverage`.
