# Compose Worker Ownership Production Gate Dry-Run

## Summary

Add a read-only worker ownership production gate composition dry-run contract that combines existing production-readiness evidence without enabling production defaults, executing locks, starting background workers, or running recovery auto-claim.

## Motivation

The worker ownership line now exposes PostgreSQL vendor lock probe/execution seam, rollout artifact, target decision, semantics binding, production gate wiring decision, renewal supervisor lifecycle, rollout confirmation, auto-claim enablement, ownership audit, and production default enablement input evidence. These pieces are intentionally safe and side-effect-free, but they are still mostly inspected as individual blockers.

Before any explicit production default enablement seam is introduced, operators and quality gates need a single machine-readable dry-run that answers whether the evidence set would satisfy the production gate if explicit enablement were requested, and why it remains blocked otherwise.

## Scope

- Add a pure builder for production gate composition dry-run evidence.
- Include default blocked and complete ready-evidence paths.
- Prove the dry-run remains non-authorizing: it does not enable production defaults, execute advisory lock SQL, start renewal supervisors, or run recovery auto-claim.
- Surface the dry-run through runtime smoke, Quality Gate, Runtime Contract Gate, and canonical docs/specs.

## Non-Goals

- Do not enable worker ownership production default mode.
- Do not execute PostgreSQL advisory lock SQL.
- Do not start renewal supervisor lifecycle or background workers.
- Do not enable recovery entry auto-claim.
- Do not unblock durable recovery production gate.
- Do not change `WORKER_OWNERSHIP_STORE_MODE` defaults.
- Do not implement child executor dispatch.
