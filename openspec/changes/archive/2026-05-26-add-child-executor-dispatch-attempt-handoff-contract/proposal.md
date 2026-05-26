# Proposal: Add Child Executor Dispatch Attempt Handoff Contract

## Summary
Add a machine-readable, side-effect-free child executor dispatch attempt handoff contract that explains when a dispatch attempt envelope can be constructed and why it still does not run by default.

## Motivation
Child executor prerequisites now expose explicit executor binding, bounded context budget, and merge handoff evidence. The next safe step is not enabling workers, but describing the boundary between `child_executor_dispatch_contract`, `ChildExecutorDispatcher`, and sandbox backend attempt envelopes.

This change gives operators and quality gates a precise answer to: can the system build and validate a dispatch attempt handoff envelope, which contracts does it depend on, and why default dispatch remains blocked?

## Scope
- Add a read-only dispatch attempt handoff contract builder.
- Nest the handoff evidence into `child_executor_dispatch_contract`.
- Expose default blocked and opt-in ready envelope validation evidence through runtime smoke, Quality Gate, Runtime Contract Gate, Health normalization, and Snapshot guard.
- Preserve the existing dispatcher opt-in behavior and default disabled posture.
- Update canonical specs and runtime docs.

## Non-Goals
- Do not start a child executor worker.
- Do not enable dispatcher by default.
- Do not execute sandbox worker code.
- Do not add an API endpoint.
- Do not change SDK default recovery or merge execution behavior.
