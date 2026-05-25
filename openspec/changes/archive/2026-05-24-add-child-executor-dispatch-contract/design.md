# Design

## Contract Shape
Add `build_child_executor_dispatch_contract(...)` in the Embedded SDK contract layer.

The contract should include:

- `contract_version`
- `overall_status`
- `dispatch_ready`
- `will_dispatch`
- `dispatch_mode`
- `backend_id`
- `backend_status`
- `backend_dispatch_ready`
- `gate_allowed`
- `prerequisites_ready`
- `relationship_seam_preserved`
- `blockers`
- `required_contracts`
- `evidence`
- `recommended_next_step`
- `non_goals`

`will_dispatch` must remain `false` in this slice. This contract describes whether the runtime boundary is ready for a future dispatch implementation; it does not perform dispatch.

## Readiness Rules
Dispatch is ready only when all of the following are true:

- promotion gate allows executor handoff
- execution prerequisites are ready
- selected backend is known and dispatch-ready

The default registry keeps `embedded_sdk_worker.dispatch_ready = false`, so default dispatch remains blocked with a `worker_backend_dispatch_ready` blocker.

## Integration Points
- `build_embedded_sdk_contract()` exposes `child_executor_dispatch_contract`.
- Runtime Surface exposes the same contract at:
  - top-level `child_executor_dispatch_contract`
  - `embedded_runtime_boundaries.child_executor_dispatch_contract`
  - `governance_overview.child_executor_dispatch_contract`
- Existing preflight, gate, routing, binding, stub, execution, replay, and merge contracts remain compatible.

## Safety
The dispatch contract is pure assembly. It must not:

- create child runs
- start an executor
- mutate persisted state
- call a worker backend
- validate ownership leases
- change approval or recovery state
