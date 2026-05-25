# Design: Worker Ownership Explicit Auto-Claim Enablement Gate

## Contract Shape

`build_worker_ownership_explicit_auto_claim_enablement_gate_contract(...)` returns:

- `contract_version`
- `overall_status`
- `will_auto_claim`
- `requested_entrypoint`
- `allowed_entrypoints`
- `missing_sections`
- `blocked_reason`
- `next_allowed_action`
- `non_goals`

The gate is ready only when all required inputs are true:

- explicit runtime auto-claim configuration
- production gate ready
- durable ownership
- descriptor evidence fallback
- idempotency evidence
- audit evidence
- lease validation
- rollout auto-claim decision recorded
- requested entrypoint is in the allowlist

## Integration

The auto-claim policy builder accepts an optional `enablement_gate_contract`. When omitted, it builds a default gate that is blocked. Production gate evidence exposes enablement status and blocked reason alongside the existing policy and allowlist evidence.

## Safety

This slice is contract hardening only. It does not call `claim_run`, does not change SDK default behavior, and does not make `worker_ownership_auto_claim_enabled` production-safe by itself.
