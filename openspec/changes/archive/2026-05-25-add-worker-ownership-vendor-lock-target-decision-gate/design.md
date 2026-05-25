# Design

## Contract Shape

Add `build_worker_ownership_vendor_lock_target_decision_contract(...)` as a read-only builder. The contract records whether an explicit target decision exists before any vendor-specific lock implementation is allowed.

The default contract is blocked and includes:

- `contract_version`
- `overall_status`
- `decision_recorded`
- `target_backend`
- `lock_adapter_kind`
- `lock_scope`
- `fencing_strategy`
- `ttl_renewal_strategy`
- `failover_strategy`
- `stale_owner_cleanup_strategy`
- `sql_row_lease_is_vendor_lock`
- `production_lock_allowed`
- `missing_sections`
- `next_allowed_action`
- `non_goals`

## Readiness Rules

The target decision is ready only when all required decision artifacts are present:

- a decision has been recorded
- a non-SQL-row-lease target backend is named
- lock adapter kind, scope, fencing strategy, TTL/renewal strategy, failover strategy, and stale owner cleanup strategy are named
- SQL row lease is still marked as not being vendor lock semantics
- production lock allowment is explicitly true

Even when this read-only decision is ready, it does not implement the lock adapter. The production gate still depends on the existing vendor lock semantics contract and other production ownership gates.

## Integration

`build_worker_ownership_vendor_lock_semantics_contract(...)` embeds the target decision under `policy.target_decision` and treats a missing/blocked target decision as a vendor lock blocker.

`build_worker_ownership_production_gate_contract(...)` copies compact target decision evidence into the `vendor_lock_semantics` section. Smoke and quality gates consume those fields and fail closed when they are absent.
