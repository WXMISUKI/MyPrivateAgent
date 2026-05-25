## Design

Add `build_worker_ownership_production_enablement_strategy_contract(...)` to `backend/agent_framework/worker_ownership.py`.

The builder is pure/read-only and returns:

- `contract_version`
- `overall_status`
- `ready`
- `production_default_enabled_requested`
- `production_default_allowed`
- `required_sections`
- `blocking_sections`
- `policy`
- `next_allowed_action`
- `non_goals`

The production gate builds all required sections first, then derives the strategy from their readiness plus the explicit `production_default_enabled` input. The `fail_closed_default_decision` section remains blocked until `production_default_allowed = true`.

## Compatibility

- Existing callers remain compatible because `production_default_enabled` remains optional and defaults to false.
- No API endpoint, SDK behavior, worker behavior, or database migration changes.
