## Design

### Renewal Supervisor Contract

Add `build_worker_ownership_renewal_supervisor_contract(...)` in the worker ownership contract module. The builder is side-effect-free and reports only readiness evidence:

- contract version
- overall status and ready flag
- supervisor enabled-by-default flag
- compact policy fields for heartbeat operation, lease TTL, renew interval, owner identity, and lost-lease fail-closed behavior
- missing sections
- next allowed action
- non-goals

Defaults must report `overall_status = blocked` and `supervisor_enabled_by_default = false`.

### Production Gate Integration

`build_worker_ownership_production_gate_contract(...)` accepts `renewal_supervisor_contract: dict | None = None`. The `heartbeat_renewal_supervisor` section is ready only when:

- heartbeat operation exists on the ownership adapter
- renewal supervisor contract reports `overall_status = ready`
- renewal supervisor contract reports `supervisor_enabled_by_default = true`

The section evidence exposes `renewal_supervisor_status`, `renewal_supervisor_missing_sections`, `supervisor_enabled_by_default`, and `lease_loss_fail_closed`. Existing default behavior remains blocked.

### Quality Gate Semantics

Runtime smoke should assert that strict SQL still reports `sql_row_lease_fencing`, that the renewal supervisor evidence is nested under the production gate, and that the gate remains blocked with `heartbeat_renewal_supervisor` missing.

Quality Gate and Runtime Contract Gate summaries should carry the renewal supervisor evidence in `worker_ownership_store_mode_coverage` and fail closed when old reports lack it.

### Non-Goals

- Do not create a scheduler, thread, worker, timer, or renewal loop.
- Do not mark SQL row lease/fencing as a vendor lock.
- Do not enable recovery entry auto-claim by default.
- Do not change SDK recovery execution behavior.
