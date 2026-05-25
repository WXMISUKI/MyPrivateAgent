# Change: Link PostgreSQL Rollout Artifact to Vendor Lock Target Decision

## Summary

Add a read-only PostgreSQL vendor lock target artifact binding contract. The binding reuses caller-owned rollout artifact/config evidence to produce nested vendor lock target decision input and target decision contracts, while preserving the existing fail-closed production gate posture.

## Motivation

The PostgreSQL rollout artifact consumer can now normalize rollout evidence into production default enablement input source evidence. The vendor lock target decision path is still interpreted separately. Binding both paths to the same PostgreSQL rollout artifact avoids future drift between "this rollout can request default enablement" and "this rollout selected PostgreSQL advisory lock as the vendor lock target".

## Scope

- Add `build_worker_ownership_postgres_vendor_lock_target_artifact_binding_contract(...)`.
- Normalize PostgreSQL rollout artifact/config fields into nested vendor lock target input and target decision contracts.
- Prove default blocked and complete-artifact paths in runtime smoke, Quality Gate, and Runtime Contract Gate coverage.
- Update canonical specs and docs.

## Non-Goals

- No production default worker ownership enablement.
- No PostgreSQL connection or advisory lock execution.
- No rollout execution or external artifact loading.
- No recovery entry auto-claim enablement.
- No child executor dispatch.
- No API endpoint, migration, or SDK default behavior change.
