# Add PostgreSQL Vendor Lock Production Gate Wiring Decision

## Summary

Add a read-only decision contract that records whether a ready PostgreSQL vendor lock semantics candidate is explicitly approved to be used as production gate input. This contract does not update the default production gate, enable production lock, or start any worker.

## Motivation

The runtime can now build a coherent PostgreSQL vendor lock semantics candidate from rollout artifact evidence, target decision evidence, a probe, and an opt-in execution seam. The remaining gap before wiring that candidate into `worker_ownership.production_gate.vendor_lock_semantics` is an explicit, machine-readable operational decision. Without this slice, downstream consumers can see a ready candidate but cannot distinguish "ready as evidence" from "approved as production gate input".

## Scope

- Add `build_worker_ownership_postgres_vendor_lock_production_gate_wiring_decision_contract(...)`.
- Expose default blocked and explicitly approved decision evidence in runtime smoke.
- Normalize decision fields into Quality Gate and Runtime Contract Gate summaries.
- Keep default production gate blocked and production default ownership disabled.

## Non-Goals

- Do not pass the candidate into the default production gate automatically.
- Do not execute PostgreSQL advisory lock SQL.
- Do not enable production lock or production default ownership.
- Do not enable recovery auto-claim.
- Do not implement child executor dispatch.
