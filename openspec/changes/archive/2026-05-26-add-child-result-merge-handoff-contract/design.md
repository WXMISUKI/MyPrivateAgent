# Design: Child Result Merge Handoff Contract

## Contract Shape
The new contract is exposed as `child_result_merge_handoff_contract` and nested into the requirement evidence for `child_result_merge_semantics_defined`.

The contract includes:
- `contract_version`
- `overall_status`
- `ready`
- `merge_strategy`
- `merge_source`
- `supported_merge_strategy`
- `intent_policy_ready`
- `artifact_envelope_required`
- `section_handoff_required`
- `parent_metadata_update_supported`
- `replay_compatible`
- `missing_sections`
- `next_allowed_action`
- `non_goals`

## Readiness Rules
The contract is ready only when:
- a merge source is present
- the merge strategy is supported
- intent-aware merge behavior is available
- artifact envelope, section handoff, parent metadata, and replay compatibility are declared by the contract

Supported strategy aliases map to the existing merge surface:
- `append_summary`
- `role_sections`
- `result_merge_policy` objects with `strategy` or `merge_strategy`

Unsupported or empty strategy fails closed and keeps `child_result_merge_semantics_defined` in missing requirements.

## Integration Points
- `build_child_executor_preflight_contract(...)` exposes the handoff contract.
- `build_child_executor_execution_prerequisites_contract(...)` exposes the same handoff evidence.
- Runtime smoke emits default fail-closed and opt-in ready handoff evidence.
- Quality Gate, Runtime Contract Gate, Health normalization, and Snapshot guard carry the evidence forward.

## Compatibility
The stable requirement name remains `child_result_merge_semantics_defined`. Existing supported strategy strings continue to work. This change enriches evidence and tightens malformed or unsupported inputs only.
