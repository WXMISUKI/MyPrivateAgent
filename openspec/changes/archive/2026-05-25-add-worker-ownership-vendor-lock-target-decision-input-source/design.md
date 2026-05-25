# Design

## Contract Shape

Add `build_worker_ownership_vendor_lock_target_decision_input_contract(...)` as a read-only builder. It records the provenance of a vendor lock target decision without authorizing production execution.

The contract includes:

- `contract_version`
- `overall_status`
- `input_source_kind`
- `decision_id`
- `approved_by`
- `approved_at`
- `target_backend`
- `lock_adapter_kind`
- `rollout_artifact`
- `config_key`
- `manual_approval_reference`
- `sql_row_lease_is_vendor_lock`
- `missing_sections`
- `next_allowed_action`
- `non_goals`

## Readiness Rules

The input source is ready only when:

- the input source kind is one of `config`, `ops_decision_record`, `rollout_artifact`, or `manual_approval`
- `decision_id`, `approved_by`, `approved_at`, `target_backend`, and `lock_adapter_kind` are present
- the source-specific reference is present:
  - `config` requires `config_key`
  - `ops_decision_record` requires `decision_id`
  - `rollout_artifact` requires `rollout_artifact`
  - `manual_approval` requires `manual_approval_reference`
- SQL row lease is still marked as not being a vendor lock

## Integration

`build_worker_ownership_vendor_lock_target_decision_contract(...)` embeds this input source under `input_source` and treats missing input source evidence as a blocker. The production gate copies a compact form into the `vendor_lock_semantics` section evidence.

Runtime smoke and quality gates require the blocked default input source evidence, preserving fail-closed behavior for old reports that lack the new fields.
