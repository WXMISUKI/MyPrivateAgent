# Design: Production Default Enablement Input Source

## Boundary

The input source contract is descriptive evidence only. It does not enable worker ownership by itself and does not execute rollout, advisory locks, renewal, recovery, or auto-claim.

## Contract

`build_worker_ownership_production_default_enablement_input_source_contract(...)` returns:

- `contract_version`
- `overall_status`
- `input_source_kind`
- `request_id`
- `requested_by`
- `requested_at`
- `target_store_mode`
- `rollout_artifact`
- `vendor_lock_decision_id`
- `renewal_lifecycle_reference`
- `auto_claim_decision_reference`
- `audit_evidence_reference`
- `rollback_plan_reference`
- `fallback_policy_reference`
- `missing_sections`
- `next_allowed_action`
- `non_goals`

Allowed source kinds are `config`, `ops_decision_record`, `rollout_artifact`, and `manual_approval`. The default contract is blocked.

## Strategy Integration

The production enablement strategy accepts an optional `enablement_input_source_contract`. Production default allowment requires:

- all required production sections are ready
- explicit default enablement was requested
- the input source contract is ready

If the boolean is true but the input source is blocked, the strategy remains blocked and explains the missing evidence.

## Gate Integration

The `fail_closed_default_decision` section exposes nested input-source evidence. This lets durable recovery and operators distinguish:

- no default enablement request
- a request without evidence
- a future request with complete rollout-backed evidence

All default paths remain blocked in this slice.
