## Design

### Rollout Readiness Contract

Add `build_worker_ownership_rollout_readiness_contract(...)` in the worker ownership contract module. The builder is side-effect-free and reports only rollout evidence:

- contract version
- overall status and ready flag
- production rollout confirmed flag
- compact checklist fields for strict mode, migration, fallback policy, renewal verification, stale fencing verification, auto-claim decision, audit evidence, and rollback plan
- missing sections
- next allowed action
- non-goals

Defaults must report `overall_status = blocked` and `production_rollout_confirmed = false`.

### Production Gate Integration

`build_worker_ownership_production_gate_contract(...)` accepts `rollout_readiness_contract: dict | None = None`. The `rollout_checklist` section is ready only when the rollout contract reports `overall_status = ready` and `production_rollout_confirmed = true`.

The section evidence exposes `rollout_readiness_status`, `rollout_missing_sections`, `production_rollout_confirmed`, `strict_mode_rollout_confirmed`, `fallback_policy_confirmed`, `migration_ready`, `stale_fencing_verified`, and `rollback_plan_ready`.

### Quality Gate Semantics

Runtime smoke should assert that strict SQL still reports `sql_row_lease_fencing`, that rollout evidence is nested under the production gate, and that the gate remains blocked with `rollout_checklist` missing.

Quality Gate and Runtime Contract Gate summaries should carry rollout readiness evidence in `worker_ownership_store_mode_coverage` and fail closed when old reports lack it.

### Non-Goals

- Do not apply migrations or mutate deployment state.
- Do not enable production ownership.
- Do not start recovery execution, renewal supervision, retry, or child executor dispatch.
