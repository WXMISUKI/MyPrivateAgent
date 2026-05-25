# Design: Worker Ownership Auto-Claim Entrypoint Allowlist

## Contract Shape

`build_worker_ownership_auto_claim_entrypoint_allowlist_contract(...)` returns:

- `contract_version`
- `overall_status`
- `ready`
- `allowed_entrypoints`
- `required_entrypoints`
- `missing_entrypoints`
- `default_auto_claim_enabled`
- `requires_production_gate_ready`
- `next_allowed_action`
- `non_goals`

The default required and allowed entrypoints are:

- `submit_approval.approved`
- `resume_run.continue_loop`

These names describe existing recovery-entry categories, not executable dispatch. A ready allowlist means the policy has named entrypoints; it does not permit auto-claim by itself.

## Gate Integration

`build_worker_ownership_auto_claim_policy_contract(...)` accepts an optional `entrypoint_allowlist_contract`. The policy treats `entrypoint_allowlist_ready` as true when the nested allowlist contract is ready. Production gate evidence exposes:

- allowlist contract version and status
- allowed and missing entrypoints
- default auto-claim enablement
- production gate requirement

The production gate section remains blocked unless the auto-claim policy is fully ready and `auto_claim_enabled_by_default` is explicitly true.

## Safety

This slice is read-only contract hardening. It does not call `claim_run`, does not start background work, and does not change SDK defaults. Runtime smoke and quality gates continue to require `auto_claim_enabled_by_default = false` and blocked production recovery until rollout and ownership gates are complete.
