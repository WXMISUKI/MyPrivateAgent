# Bind PostgreSQL Target Decision to Vendor Lock Semantics

## Summary

Add a read-only contract that consumes the PostgreSQL vendor lock target artifact binding from the previous slice and assembles a PostgreSQL vendor lock semantics candidate. The candidate proves that target decision, PostgreSQL probe, adapter capability, and semantics evidence can align, while still not enabling production lock or worker ownership by default.

## Motivation

Worker ownership now has separate evidence for PostgreSQL rollout artifact consumption, target decision input, target decision, advisory lock probe, execution seam, adapter readiness, and vendor lock semantics. The next smallest safe production-hardening step is to bind those pieces into one machine-readable candidate so operators can see whether PostgreSQL advisory lock semantics are coherently ready without treating that as production authorization.

## Scope

- Add `build_worker_ownership_postgres_vendor_lock_semantics_binding_contract(...)`.
- Build nested PostgreSQL probe, adapter, target decision, and vendor lock semantics evidence from the target artifact binding.
- Expose default blocked and complete candidate evidence in runtime smoke, Quality Gate, and Runtime Contract Gate summaries.
- Preserve fail-closed defaults: no SQL execution, no background worker, no production default enablement, no recovery auto-claim.

## Non-Goals

- Do not execute PostgreSQL advisory lock SQL.
- Do not bind a real database connection.
- Do not make `worker_ownership.production_gate.vendor_lock_semantics` ready by default.
- Do not enable production recovery or recovery auto-claim.
- Do not implement child executor dispatch.
