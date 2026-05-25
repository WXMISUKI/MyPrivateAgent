# Design: Worker Ownership Rollout Confirmation Decision Record

## Contract

Add `build_worker_ownership_rollout_confirmation_decision_contract(...)`.

The contract is read-only and returns:

- `contract_version`
- `overall_status`
- `production_rollout_confirmed`
- `decision_recorded`
- `decision_id`
- `approved_by`
- `approved_at`
- `target_store_mode`
- `rollback_plan_acknowledged`
- `fallback_policy_acknowledged`
- `renewal_lifecycle_verified`
- `auto_claim_decision_recorded`
- `missing_sections`
- `next_allowed_action`
- `non_goals`

`overall_status` is `ready` only when a decision is recorded, rollout confirmation is true, approver and timestamp are present, target store mode is `strict_sql`, rollback and fallback acknowledgements are true, renewal lifecycle verification is true, and auto-claim decision is recorded.

## Integration

`build_worker_ownership_production_rollout_operationalization_contract(...)` accepts an optional `confirmation_decision_contract`. When omitted, it builds the default blocked decision record.

Operationalization remains blocked when the decision record is blocked. The production gate `rollout_checklist` evidence exposes compact fields:

- `rollout_confirmation_decision_contract_version`
- `rollout_confirmation_decision_status`
- `rollout_decision_recorded`
- `rollout_decision_id`
- `rollout_approved_by`
- `rollout_approved_at`
- `rollout_target_store_mode`
- `rollout_confirmation_missing_sections`
- `rollout_confirmation_production_rollout_confirmed`

## Safety

The decision record is not an authorization shortcut. Worker ownership production default enablement still requires the full production gate and explicit production default enablement strategy. Strict SQL row lease/fencing remains distinct from vendor-specific distributed lock semantics.
