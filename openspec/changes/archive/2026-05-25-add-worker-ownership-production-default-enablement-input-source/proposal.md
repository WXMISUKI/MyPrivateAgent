# Change: Add Worker Ownership Production Default Enablement Input Source

## Summary

Add a read-only production default enablement input source contract for worker ownership. The contract records whether a default-enable request is backed by an explicit rollout artifact, approver, approval time, target store mode, vendor lock decision, renewal lifecycle verification, auto-claim decision, audit evidence, and rollback/fallback references.

## Motivation

Worker ownership now has PostgreSQL advisory lock opt-in execution evidence, rollout evidence, and a production enablement strategy. The remaining safety gap is that `production_default_enabled_requested` is still a plain boolean. Before any future default enablement, the runtime must explain where that request came from and why it is allowed or blocked.

## Scope

- Add a read-only production default enablement input source contract.
- Embed the input source in `build_worker_ownership_production_enablement_strategy_contract(...)`.
- Surface input source evidence through `worker_ownership.production_gate.sections[name=fail_closed_default_decision]`.
- Extend runtime smoke, quality gate, and runtime contract gate coverage.
- Update canonical specs and project docs.

## Non-Goals

- No default production ownership enablement.
- No automatic rollout execution.
- No background worker or supervisor startup.
- No recovery entry auto-claim enablement.
- No database migration or API endpoint.
