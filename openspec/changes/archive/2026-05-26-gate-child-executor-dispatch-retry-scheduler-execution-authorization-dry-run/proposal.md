# Proposal: Child Executor Dispatch Retry Scheduler Execution Authorization Dry-Run

## Summary

Add a side-effect-free child executor dispatch retry scheduler execution authorization dry-run contract.

The previous slice introduced `child_executor_dispatch_retry_scheduler_binding_gate`, which can report that retryable dispatch result evidence is ready to be bound to a scheduler decision. This proposal adds the next machine-readable gate: whether the ready binding evidence, production scheduler gate evidence, durable scheduling evidence, idempotency/dedupe, audit timeline, worker ownership, bounded attempts, and explicit authorization request are sufficient for a future retry scheduler execution authorization review.

The dry-run MUST NOT schedule retries, write schedule state, start workers, or enable production retry execution.

## Motivation

The child executor dispatch retry chain now has:

- dispatch result handoff evidence
- retry audit policy evidence
- retry scheduler handoff gate
- retry scheduler binding gate

The remaining ambiguity is that `binding_gate.ready` could be misread as authorization to call the retry scheduler. This change creates a separate dry-run authorization gate so the system can say:

- binding evidence is ready
- execution authorization is or is not ready
- retry scheduling still will not occur in this slice

This keeps the roadmap moving toward retry scheduler integration without crossing into production scheduling semantics.

## Non-Goals

- Do not execute `RecoveryRetryScheduler`.
- Do not create durable retry schedule rows.
- Do not start or enable background workers.
- Do not default-enable production retry scheduling.
- Do not perform parent merge.
- Do not change child executor dispatcher default behavior.

## Impacted Areas

- `backend/agent_framework/child_executor_dispatcher.py`
- `backend/scripts/runtime_contract_smoke.py`
- `backend/scripts/quality_gate_report.py`
- `backend/services/runtime_contract_gate_service.py`
- `backend/routers/health.py`
- `backend/services/runtime_contract_snapshot_service.py`
- `tests/agent_framework/*`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`
