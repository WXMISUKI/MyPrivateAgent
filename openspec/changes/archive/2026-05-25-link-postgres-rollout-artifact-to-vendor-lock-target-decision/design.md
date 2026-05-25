# Design: PostgreSQL Target Artifact Binding

## Boundary

The binding consumes an already-loaded artifact/config mapping and optional PostgreSQL rollout consumer evidence. It only assembles contracts. It does not load files, fetch config, connect to PostgreSQL, execute advisory lock SQL, start a worker, or enable production ownership.

## Contract

`build_worker_ownership_postgres_vendor_lock_target_artifact_binding_contract(...)` returns:

- `contract_version`
- `overall_status`
- `ready`
- `source_kind`
- `artifact_id`
- `approved_by`
- `approved_at`
- `target_backend`
- `lock_adapter_kind`
- `lock_scope`
- `fencing_strategy`
- `ttl_renewal_strategy`
- `failover_strategy`
- `stale_owner_cleanup_strategy`
- `rollout_artifact`
- `postgres_rollout_consumer_status`
- `target_decision_input`
- `target_decision`
- `will_enable_production_lock`
- `executes_advisory_lock`
- `sql_row_lease_is_vendor_lock`
- `missing_sections`
- `next_allowed_action`
- `non_goals`

Allowed artifact source kinds are `runtime_config` and `rollout_artifact`. The target must be `postgres` and `postgres_advisory_lock`.

## Readiness

The binding is ready only when:

- artifact source, id, approval, backend, adapter, rollout reference, and target decision fields are present
- PostgreSQL rollout consumer evidence is ready
- nested target decision input is ready
- nested target decision is ready
- SQL row lease is not promoted as vendor lock authority

Even when ready, `will_enable_production_lock` and `executes_advisory_lock` remain `false`.

## Gate Coverage

Runtime smoke and quality gates cover:

- default binding blocked with missing artifact/consumer evidence
- complete artifact can produce ready nested target input and target decision evidence
- binding remains non-executing and does not enable production lock
- production gate remains blocked until all other production sections and explicit enablement are complete
