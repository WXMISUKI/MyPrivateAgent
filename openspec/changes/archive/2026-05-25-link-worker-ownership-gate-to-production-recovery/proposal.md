## Why

Durable workspace production recovery now has descriptor lifecycle, registry/checkpoint policy, loader handoff, and recovery audit evidence. The remaining production blocker is worker ownership and rollout, but `persistence_interface.production_recovery_gate` only exposes a generic `worker_ownership_production_gate_missing` section.

Without linking the worker ownership gate evidence into the durable recovery gate, future recovery executor or rollout work must inspect two contract branches and can misread a durable workspace as closer to production recovery than it is.

## What Changes

- Thread `worker_ownership.production_gate` evidence into `persistence_interface.production_recovery_gate`.
- Keep the durable recovery gate blocked unless worker ownership gate is ready and explicitly production-default enabled.
- Expose compact worker ownership blocker evidence from the durable recovery gate section.
- Extend runtime smoke and quality-gate normalization to fail closed when the linked evidence is missing.
- Update runtime contract docs and roadmap state.

## Capabilities

### Modified Capabilities

- `durable-workspace-production-recovery-gate`: Worker ownership section carries nested ownership gate evidence instead of an empty placeholder.
- `embedded-sdk-persistence-interface`: Persistence interface accepts worker ownership production gate evidence from the runtime factory.
- `runtime-worker-ownership-contract`: Clarifies that the worker ownership production gate can be consumed by durable recovery gating without becoming execution authorization.

## Impact

- Affected backend contracts: `persistence_interface.production_recovery_gate`, `worker_ownership.production_gate`, runtime smoke summary, Runtime Contract Gate summary.
- Affected frontend consumers: existing Runtime Surface/Governance consumers only see richer nested evidence; no UI change is required.
- Affected docs/specs: `openspec/specs/*`, `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`.
- Non-goals: no vendor-specific distributed lock, no background renewal supervisor, no default recovery entry auto-claim, no child executor dispatch, no production recovery execution.
