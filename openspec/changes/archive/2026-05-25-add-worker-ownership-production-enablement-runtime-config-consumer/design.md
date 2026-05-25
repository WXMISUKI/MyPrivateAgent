## Overview

Add `build_worker_ownership_production_enablement_runtime_config_consumer_contract(...)` as a side-effect-free composition helper in the worker ownership contract module.

The consumer accepts a caller-owned config dictionary. It does not read files, fetch remote config, mutate environment variables, start lifecycle processes, execute advisory locks, or claim recovery ownership. Its role is to normalize config evidence into the contracts that already exist:

- `production_default_enablement_input_source`
- `production_gate_composition_dry_run`

## Contract Shape

The consumer returns:

- `contract_version`
- `overall_status`
- `ready`
- `source_kind`
- `config_id`
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
- `enablement_input_source`
- `composition_dry_run`
- `missing_sections`
- `will_enable_production_default`
- `executes_lock`
- `starts_background_worker`
- `runs_recovery_auto_claim`
- `next_allowed_action`
- `non_goals`

## Readiness Rules

The default consumer is `blocked`.

The consumer may report `ready` only when:

- config source kind and config id are present
- approval metadata is present
- target store mode is `strict_sql`
- target backend is `postgres`
- lock adapter kind is `postgres_advisory_lock`
- rollout artifact and all production evidence references are present
- nested enablement input source is ready
- nested composition dry-run is ready

Even when ready, the consumer remains non-executing:

- `will_enable_production_default = false`
- `executes_lock = false`
- `starts_background_worker = false`
- `runs_recovery_auto_claim = false`

## Integration

Runtime smoke will build:

- a default blocked consumer
- a complete ready consumer using ready input contracts from existing worker ownership builders

Quality Gate and Runtime Contract Gate will normalize consumer evidence under `runtime_contract_summary.worker_ownership_store_mode_coverage`.

## Non-Goals

- No API endpoint.
- No runtime environment mutation.
- No default production ownership enablement.
- No PostgreSQL advisory lock SQL execution.
- No background renewal supervisor startup.
- No recovery auto-claim execution.
- No SDK default behavior change.
