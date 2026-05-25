## Design

### Auto-Claim Policy Contract

Add `build_worker_ownership_auto_claim_policy_contract(...)` in the worker ownership contract module. The builder is side-effect-free and reports only policy evidence:

- contract version
- overall status and ready flag
- auto-claim enabled-by-default flag
- compact policy fields for explicit configuration, gate readiness requirement, durable store requirement, descriptor evidence fallback, idempotency/audit evidence, entrypoint allowlist, and lease validation requirement
- missing sections
- next allowed action
- non-goals

Defaults must report `overall_status = blocked` and `auto_claim_enabled_by_default = false`.

### Production Gate Integration

`build_worker_ownership_production_gate_contract(...)` accepts `auto_claim_policy_contract: dict | None = None`. The `recovery_entry_auto_claim_policy` section is ready only when the policy contract reports `overall_status = ready` and `auto_claim_enabled_by_default = true`.

The section evidence exposes `auto_claim_policy_status`, `auto_claim_missing_sections`, `auto_claim_enabled_by_default`, `descriptor_evidence_fallback`, `requires_valid_worker_ownership_gate`, `entrypoint_allowlist_ready`, and `audit_evidence_required`.

### Quality Gate Semantics

Runtime smoke should assert that default mode remains `descriptor_evidence_only`, that auto-claim policy evidence is nested under the production gate, and that the gate remains blocked with `recovery_entry_auto_claim_policy` missing.

Quality Gate and Runtime Contract Gate summaries should carry auto-claim policy evidence in `worker_ownership_store_mode_coverage` and fail closed when old reports lack it.

### Non-Goals

- Do not call `claim_run`.
- Do not enable `worker_ownership_auto_claim_enabled` by default.
- Do not change SDK recovery entrypoint execution.
- Do not start recovery, retry, renewal, or child executor work.
