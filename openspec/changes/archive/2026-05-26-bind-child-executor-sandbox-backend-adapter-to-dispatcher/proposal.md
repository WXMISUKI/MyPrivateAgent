# Change: Bind Child Executor Sandbox Backend Adapter To Dispatcher

## Summary

Add a side-effect-free, opt-in binding contract between child executor sandbox backend adapter evidence and the child executor dispatcher boundary.

## Motivation

The child executor path now has explicit executor binding, dispatch attempt handoff, sandbox backend adapter readiness, dispatch result handoff, and retry audit policy coverage. The remaining gap before any real sandbox worker backend can be considered is the binding seam between a ready sandbox backend adapter contract and the dispatcher backend adapter map.

Without a dedicated binding contract, consumers can see that a sandbox backend adapter is ready and that the dispatcher exists, but cannot distinguish:

- a ready adapter contract that is not bound to the dispatcher,
- a bound adapter that is missing sandbox guard/audit/idempotency readiness,
- an opt-in test binding that is explicitly ready but still non-production,
- and a blocked default posture that must not start a worker.

## Scope

- Add `child_executor_sandbox_backend_binding` contract evidence.
- Attach binding evidence to `child_executor_dispatch_contract` and dispatcher attempts.
- Add runtime smoke / Quality Gate / Runtime Contract Gate / Snapshot coverage.
- Keep default dispatcher disabled and default worker execution blocked.

## Non-Goals

- Do not start a background worker, queue, process sandbox, or timer.
- Do not enable production child executor dispatch.
- Do not schedule retry execution.
- Do not merge child results into parent state.
- Do not add a new API endpoint.
