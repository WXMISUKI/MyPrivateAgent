## Design

### Handoff Contract

The handoff policy is a compact contract that sits between `DurableRecoveryLoader` and a future recovery executor. It answers whether a loaded candidate may be handed off, but it still does not execute recovery.

The policy exposes:

- `contract_version`
- `policy_kind`
- `default_handoff_enabled = false`
- `executes_recovery = false`
- `deserializes_callables = false`
- `allowed_entrypoints`
- `required_evidence`
- `fail_closed_reasons`

### Decision Semantics

The handoff decision remains fail-closed unless all required evidence is present. This slice proves two paths:

- Default path: blocked with `explicit_handoff_required`.
- Explicit path without executor binding: blocked with `recovery_executor_not_bound`.

This keeps policy readiness separate from execution readiness. A future change may bind a recovery executor and move the explicit path forward, but this change must keep `will_execute = false`.

### Production Gate Semantics

`loader_execution_handoff_policy` can become ready because the runtime has a canonical policy contract and fail-closed decision envelope. The overall durable workspace production recovery gate remains blocked by registry binding policy, checkpoint/cursor production gate, worker ownership, recovery audit, and rollout sections.

### Non-Goals

- No cross-process recovery executor.
- No automatic loader execution.
- No callable deserialization.
- No production default recovery enablement.
