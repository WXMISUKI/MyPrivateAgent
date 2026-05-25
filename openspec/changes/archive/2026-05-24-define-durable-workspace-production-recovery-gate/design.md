# Design

## Boundary

This change defines a production gate for default cross-process recovery. It does not execute recovery, deserialize callables, introduce a background loader, or treat `durable_ready` as run-specific recovery authorization.

## Current State

The runtime already has:

- persistence posture: `memory_preview`, `durable_ready`, `durable_degraded`
- durable state contract on workspace backend descriptions
- checkpoint and resume cursor read models
- DurableRecoveryLoader ready/missing/unsafe candidate checks
- registry-backed continuation reattach
- recovery operation evidence and audit summaries
- worker ownership and retry production gates

The missing production decision is whether a runtime may perform cross-process recovery by default without explicit proof that the durable backend, descriptor lifecycle, registry binding, ownership gate, audit, and rollout requirements are complete.

## Production Gate

The production recovery gate should expose:

- contract version
- overall status
- production default enabled flag
- readiness sections
- missing sections
- next allowed action
- non-goals

Required sections:

- durable workspace backend
- durable backend migration/rollout
- descriptor lifecycle governance
- registry binding resolution
- checkpoint/resume cursor readiness
- worker ownership production gate
- recovery audit operation history
- loader execution handoff policy
- fail-closed default decision

If any production section is missing, the gate remains blocked and cross-process recovery remains explicit/conditional.

## Failure Mode

Missing gate evidence must fail closed. `durable_ready` may indicate storage capability, and DurableRecoveryLoader may produce a ready candidate, but neither is enough to enable default production recovery without descriptor lifecycle, ownership, audit, and rollout evidence.

## Implementation Shape

The first implementation should add a pure production gate builder in the persistence/recovery contract layer and expose it through the runtime factory contract. Runtime smoke and quality gate summaries should prove the blocked production posture without changing recovery execution.
