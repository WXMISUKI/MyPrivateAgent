# Design: Child Executor Dispatch Attempt Handoff Contract

## Contract Shape
The new contract is exposed as `child_executor_dispatch_attempt_handoff` and nested under `child_executor_dispatch_contract`.

The contract includes:
- `contract_version`
- `overall_status`
- `ready`
- `dispatch_contract_ready`
- `dispatcher_enabled_by_default`
- `dispatcher_opt_in_required`
- `backend_id`
- `backend_adapter_kind`
- `sandbox_backend_selected`
- `sandbox_attempt_schema_ready`
- `attempt_envelope_supported`
- `attempt_validation_ready`
- `audit_required`
- `idempotency_required`
- `unsafe_payload_guard_ready`
- `will_dispatch`
- `missing_sections`
- `blocked_reason`
- `next_allowed_action`
- `non_goals`

## Readiness Rules
The handoff contract reports ready only when:
- the dispatch contract is ready
- a backend id is selected
- dispatcher remains explicit opt-in
- sandbox backends have a valid attempt envelope schema and unsafe payload guard
- audit and idempotency expectations are present

Ready handoff still sets `will_dispatch = false`; real dispatch remains controlled by `ChildExecutorDispatcher(enabled=True)` and an injected backend adapter.

## Quality Coverage
Runtime smoke must prove:
- default handoff is blocked and does not dispatch
- opt-in sandbox-ready handoff can validate a compact attempt envelope
- unsafe payload keys remain guarded

Quality Gate and Runtime Contract Gate fail closed when the evidence is missing or malformed.

## Compatibility
Existing dispatch contract fields and dispatcher behavior remain compatible. This change only adds evidence and guardrail coverage.
