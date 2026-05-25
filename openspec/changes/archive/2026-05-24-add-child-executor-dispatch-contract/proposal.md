# Add Child Executor Dispatch Contract

## Summary
Add a side-effect-free `child_executor_dispatch_contract` that turns the current backend registry and execution prerequisite evidence into an explicit dispatch boundary.

## Problem
Child executor promotion now has three backend-owned signals:

- preflight can identify whether a child run is a promotion candidate
- promotion gate can allow the candidate relationship to move forward
- execution prerequisites can explain why a real executor still cannot start

The missing boundary is the final dispatch-facing contract. Without it, a future call site may treat `child_executor_promotion_gate.allowed = true` as equivalent to "dispatch now", even though the default backend registry still reports `dispatch_ready = false`.

## Goals
- Expose `child_executor_dispatch_contract` as a compact, machine-readable contract.
- Keep default behavior blocked and relationship-only.
- Derive dispatch readiness from promotion gate, execution prerequisites, and backend registry evidence.
- Surface the contract through SDK contract and Runtime Surface/governance read models.
- Add focused tests proving no real worker dispatch is implied.

## Non-Goals
- Do not implement a real child executor.
- Do not allocate workers, queues, processes, leases, or sandbox runtimes.
- Do not change existing child run creation, stub execution, replay, or merge behavior.
- Do not flip default backend `embedded_sdk_worker` to dispatch ready.
