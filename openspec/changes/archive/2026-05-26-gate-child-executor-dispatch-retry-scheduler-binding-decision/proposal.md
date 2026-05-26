# Gate Child Executor Dispatch Retry Scheduler Binding Decision

## Summary

Add a side-effect-free binding decision gate between the child executor dispatch retry scheduler handoff contract and any explicit retry scheduler boundary.

The previous handoff contract can prove that retryable dispatch audit evidence is inspectable and that `will_schedule_retry = false`. This change records where a future scheduler binding would come from and why the default remains blocked unless handoff, scheduler posture, production scheduler gate, idempotency/dedupe, audit timeline, worker ownership, and bounded attempt evidence are explicit.

## Motivation

Child executor dispatch now has:

- result handoff evidence
- retry audit posture for success, retryable, terminal, and missing-idempotency paths
- retry scheduler handoff evidence that separates retryable audit posture from scheduling authorization

The remaining gap is that `scheduler_bound = true` is only a builder-level sample. Consumers still need a machine-readable binding decision that explains whether child dispatch retry evidence may be treated as a scheduler-bound candidate.

## Goals

- Expose a `child_executor_dispatch_retry_scheduler_binding_gate` contract.
- Preserve default blocked posture and `will_schedule_retry = false`.
- Prove handoff-ready evidence is still not scheduling authorization.
- Fail closed when handoff, scheduler, production gate, idempotency/dedupe, audit, worker ownership, or bounded-attempt evidence is missing.
- Add runtime smoke, Quality Gate, Runtime Contract Gate, Snapshot, health normalization, docs, and tests coverage.

## Non-Goals

- Do not schedule child executor retry work.
- Do not start a retry scheduler loop.
- Do not start child executor workers or sandbox runtimes.
- Do not enable production automatic retry.
- Do not change SDK default behavior or API endpoints.
