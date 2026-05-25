## Design

Add `build_worker_ownership_vendor_lock_semantics_contract(...)` to `backend/agent_framework/worker_ownership.py`.

The builder is pure/read-only and returns:

- `contract_version`
- `overall_status`
- `ready`
- `production_lock_allowed`
- `current_posture`
- `policy`
- `missing_sections`
- `next_allowed_action`
- `non_goals`

The default contract is blocked. It records `current_posture = sql_row_lease_fencing` for durable SQL ownership stores, but requires a vendor lock adapter, lock scope, fencing guarantees, failover semantics, TTL/renewal semantics, stale owner cleanup semantics, and explicit production allowment before it can become ready.

`build_worker_ownership_production_gate_contract(...)` accepts `vendor_lock_semantics_contract: dict | None`. The `vendor_lock_semantics` section is ready only when the nested contract is ready and `production_lock_allowed = true`.

`build_worker_ownership_operational_readiness_contract(...)` also carries the vendor lock semantics contract for consumers that inspect operational readiness directly.

Runtime smoke, Quality Gate, and Runtime Contract Gate normalize the nested evidence and require it for `worker_ownership_store_mode_coverage.mode_smoke`.

## Compatibility

- Existing callers remain compatible because the new parameters are optional.
- Existing `vendor_lock_semantics_ready` remains as a compatibility input used to seed the default nested contract.
- No API endpoint, SDK behavior, or database migration changes.

## Non-Goals

- Do not implement vendor-specific distributed lock adapters.
- Do not treat SQL row lease/fencing as vendor lock semantics.
- Do not default-enable worker ownership.
- Do not start background workers or renewal loops.
