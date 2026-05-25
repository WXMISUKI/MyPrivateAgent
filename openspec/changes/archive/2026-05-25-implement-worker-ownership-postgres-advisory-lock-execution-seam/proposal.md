# Change: Implement Worker Ownership PostgreSQL Advisory Lock Execution Seam

## Summary

Add an explicit opt-in PostgreSQL advisory lock execution seam for worker ownership vendor-lock hardening. The seam provides testable one-shot probe/acquire/renew/release operations only when a caller injects an executor. Defaults remain side-effect-free: no database connection, no SQL execution, no background worker, no production ownership enablement, and no recovery auto-claim.

## Motivation

Worker ownership now exposes vendor lock adapter evidence and a PostgreSQL advisory lock probe contract, but the runtime still lacks an executable boundary that can be smoke-tested without wiring production database infrastructure. A narrowly scoped execution seam lets the project validate operation envelopes, owner identity, fencing metadata, and fail-closed behavior before deciding production rollout or database-specific lock semantics.

## Scope

- Add a Python execution seam for PostgreSQL advisory lock operations with explicit executor injection.
- Add a read-only execution seam contract embedded under PostgreSQL vendor lock probe evidence.
- Surface execution seam evidence through `worker_ownership.production_gate.sections[name=vendor_lock_semantics]`.
- Add runtime smoke, quality gate, and runtime contract gate coverage for default blocked and opt-in execution paths.
- Update runtime worker ownership and production gate specifications plus project docs.

## Non-Goals

- No default PostgreSQL connection.
- No production vendor lock enablement.
- No background renewal loop or worker startup.
- No recovery entry auto-claim enablement.
- No change to `WORKER_OWNERSHIP_STORE_MODE` defaults.
- No child executor dispatch changes.
