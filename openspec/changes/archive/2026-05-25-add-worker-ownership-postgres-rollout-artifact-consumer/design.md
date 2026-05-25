# Design: PostgreSQL Rollout Artifact Consumer

## Boundary

The consumer accepts an already-loaded mapping from a caller-owned rollout artifact or runtime config source. It validates and normalizes that mapping into contract evidence only. It does not read files, fetch remote config, connect to PostgreSQL, execute advisory lock SQL, or enable production ownership.

## Contract

`build_worker_ownership_postgres_rollout_artifact_consumer_contract(...)` returns:

- `contract_version`
- `overall_status`
- `ready`
- `source_kind`
- `artifact_id`
- `approved_by`
- `approved_at`
- `target_store_mode`
- `target_backend`
- `lock_adapter_kind`
- `rollout_artifact`
- `vendor_lock_decision_id`
- `renewal_lifecycle_reference`
- `auto_claim_decision_reference`
- `audit_evidence_reference`
- `rollback_plan_reference`
- `fallback_policy_reference`
- `postgres_execution_seam_required`
- `postgres_execution_seam_status`
- `enablement_input_source`
- `will_enable_production_default`
- `executes_advisory_lock`
- `missing_sections`
- `next_allowed_action`
- `non_goals`

Allowed source kinds are `runtime_config` and `rollout_artifact`. The only accepted target mode/backend/adapter combination is `strict_sql`, `postgres`, and `postgres_advisory_lock`.

## Enablement Input Source Bridge

When the artifact and PostgreSQL execution seam evidence are ready, the consumer builds a nested `production_default_enablement_input_source` using:

- `input_source_kind = rollout_artifact`
- `request_id = artifact_id`
- `requested_by = approved_by`
- `requested_at = approved_at`
- `target_store_mode = strict_sql`
- rollout, vendor lock, renewal lifecycle, auto-claim, audit, rollback, and fallback references from the artifact

This nested input source can be passed into `build_worker_ownership_production_enablement_strategy_contract(...)`, but it remains descriptive. The consumer always reports `will_enable_production_default = false`.

## Gate Coverage

Runtime smoke and quality gates verify both default and complete-artifact consumer paths:

- default consumer is blocked and non-executing
- complete artifact can produce a ready nested input source
- ready consumer still does not enable production default ownership
- production gate and durable recovery gate remain blocked by worker ownership/rollout evidence
