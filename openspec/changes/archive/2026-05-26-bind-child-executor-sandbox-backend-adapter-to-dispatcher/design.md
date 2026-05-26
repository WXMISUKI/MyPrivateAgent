# Design

## Contract Shape

Introduce a pure builder:

`build_child_executor_sandbox_backend_binding_contract(...)`

Inputs:

- `backend_id`
- `backend_registry_entry`
- `adapter_contract`
- `dispatcher_backend_adapters`
- `explicit_binding`

Output:

- `contract_version`
- `overall_status`
- `ready`
- `backend_id`
- `adapter_contract_status`
- `adapter_contract_ready`
- `binding_status`
- `dispatcher_binding_ready`
- `attempt_envelope_supported`
- `audit_idempotency_ready`
- `missing_sections`
- `next_allowed_action`
- `non_goals`

The builder is side-effect-free. It inspects only supplied evidence and never calls an adapter.

## Readiness Rules

The binding is ready only when:

- explicit binding is present,
- backend id is present,
- registry entry describes a sandbox worker backend,
- adapter contract is ready,
- sandbox guard, audit, and idempotency evidence are ready,
- an adapter is callable in the dispatcher adapter map,
- and the compact attempt envelope can be validated.

Default status remains blocked. A ready binding does not authorize production dispatch; it only means the dispatcher has a callable backend adapter for an already-ready sandbox adapter contract.

## Integration

- `build_child_executor_dispatch_contract(...)` includes nested `child_executor_sandbox_backend_binding`.
- `ChildExecutorDispatcher.dispatch(...)` includes binding evidence in dispatch attempts when a binding contract is provided in the dispatch contract.
- Runtime smoke validates default blocked, ready opt-in binding, and missing callable binding.
- Quality Gate and Runtime Contract Gate expose `runtime_contract_summary.child_executor_sandbox_backend_binding_coverage`.
- Snapshot guards stable coverage fields.
- Health degraded traces normalize the coverage and include a compact label.

## Safety

The change does not execute backend adapters inside the binding builder. Existing dispatcher execution remains opt-in through `ChildExecutorDispatcher(enabled=True, backend_adapters=...)`, and default behavior remains blocked.
