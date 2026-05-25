# Design

## Boundary

This change defines a production enablement gate for worker ownership. It does not implement a background renewal supervisor, vendor-specific lock adapter, or default recovery-entry auto-claim execution.

## Current State

The runtime already has:

- in-memory worker ownership preview store
- SQLAlchemy durable row lease/fencing adapter
- `WORKER_OWNERSHIP_STORE_MODE` with `memory_only`, `strict_sql`, and `prefer_sql_with_fallback`
- claim, heartbeat, validate, get lease operations
- stale fencing fail-closed behavior
- SDK opt-in recovery ownership validation
- runtime smoke and quality gate coverage for store mode readiness

The remaining production question is whether worker ownership can become default execution authority for recovery or worker dispatch without a caller explicitly supplying ownership evidence.

## Production Gate

The production gate should expose:

- contract version
- overall status
- production default enabled flag
- readiness sections
- missing sections
- next allowed action
- non-goals

Required sections:

- durable ownership store
- vendor lock semantics
- heartbeat renewal supervisor
- migration checklist
- rollout checklist
- recovery entry auto-claim policy
- stale fencing fail-closed validation
- ownership audit evidence
- fail-closed default decision

If any production section is missing, the gate remains blocked and worker ownership remains explicit/opt-in.

## Failure Mode

Missing gate evidence must fail closed. A durable SQL row lease may prove persistence and fencing, but it must not be treated as a vendor-specific distributed lock or as permission to enable default recovery ownership without renewal, rollout, audit, and auto-claim policy evidence.

## Implementation Shape

The first implementation should add a pure contract builder near existing worker ownership readiness code and expose it through the existing worker ownership contract. Runtime smoke and gate summary may then prove the default blocked production posture without changing runtime execution.
