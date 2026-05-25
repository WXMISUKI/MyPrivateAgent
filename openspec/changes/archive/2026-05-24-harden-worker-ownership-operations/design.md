# Design

## Boundary

Worker ownership hardening must keep default local preview behavior usable while making production enablement explicit and auditable.

## Required Capabilities

- Lease heartbeat renewal semantics.
- Stale lease fail-closed validation.
- Optional recovery-entry claim before executing registry-backed continuation.
- Store mode rollout evidence for memory, fallback, strict SQL, and vendor lock posture.
- Migration readiness checklist for `runtime_worker_ownership_leases`.

## Non-Goals

- No implicit distributed lock promise for every SQL vendor.
- No unbounded background renewal thread in the first slice.
- No change to recovery operation compact payload shape except documented optional evidence.
