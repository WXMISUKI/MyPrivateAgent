# Design: Child Executor Context Budget Policy Contract

## Contract Shape
The new policy contract is exposed as `child_executor_context_budget_policy` and nested into requirement evidence for `child_context_budget_defined`.

The contract includes:
- `contract_version`
- `overall_status`
- `ready`
- `budget_source`
- `max_turns`
- `timeout_seconds`
- `token_budget`
- `artifact_budget`
- `missing_sections`
- `fail_closed_reason`
- `next_allowed_action`
- `non_goals`

## Readiness Rules
The policy is `ready` only when it can identify a budget source and at least one positive bounded limit:
- `max_turns`
- `timeout_seconds`
- `token_budget`
- `artifact_budget`

Missing source or bounded limit fails closed. Scalar legacy inputs remain supported and are normalized conservatively:
- `metadata.scheduler_policy.max_turns` maps to `max_turns`
- `metadata.scheduler_policy.timeout_seconds` maps to `timeout_seconds`
- an integer `child_context_budget` maps to `max_turns`

## Integration Points
- `build_child_executor_preflight_contract(...)` exposes the policy.
- `build_child_executor_execution_prerequisites_contract(...)` exposes the same policy and uses it for `child_context_budget_defined`.
- `build_child_executor_dispatch_contract(...)` remains blocked unless all prerequisites and dispatch registry evidence are ready.
- Runtime smoke emits both default fail-closed and opt-in bounded policy evidence.
- Quality gate and Runtime Contract Gate normalize this evidence fail-closed.

## Compatibility
The stable requirement name `child_context_budget_defined` is preserved. The change enriches evidence and tightens readiness semantics for malformed or unbounded budget inputs. No endpoint or SDK default behavior changes.
