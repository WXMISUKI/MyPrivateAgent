## Why

Durable workspace production recovery is still blocked by `registry_binding_resolution` and `checkpoint_resume_cursor_gate` even though the runtime already has registry-backed reattach, durable loader evidence, and checkpoint/resume cursor smoke coverage.

Without a production policy contract for these two sections, future recovery executor or rollout work could confuse "a sample smoke path is covered" with "production recovery has a machine-readable policy gate".

## What Changes

- Add a compact `production-recovery-registry-checkpoint-policy` capability.
- Expose registry binding resolution and checkpoint/resume cursor production policy evidence from the embedded persistence production recovery gate.
- Mark `registry_binding_resolution` and `checkpoint_resume_cursor_gate` ready only when side-effect-free policy evidence is present.
- Extend runtime smoke, Quality Gate, Runtime Contract Gate, and Snapshot with `production_recovery_registry_checkpoint_policy_coverage.policy_smoke`.
- Keep production recovery blocked while worker ownership and rollout sections are missing.

## Capabilities

### New Capabilities

- `production-recovery-registry-checkpoint-policy`: Defines production readiness evidence for registry binding resolution and checkpoint/resume cursor gate policy.

### Modified Capabilities

- `durable-workspace-production-recovery-gate`: Allows registry/checkpoint policy sections to become ready independently from worker ownership and rollout.
- `embedded-sdk-persistence-interface`: Persistence posture exposes the updated production recovery gate evidence.
- `embedded-sdk-recovery-protocol`: Clarifies that checkpoint/cursor policy remains a gate and not execution authorization.

## Impact

- Affected backend contracts: `persistence_interface.production_recovery_gate`, runtime contract smoke summary, Runtime Contract Gate, Snapshot.
- Affected docs/specs: `openspec/specs/*`, `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`.
- Non-goals: no default cross-process recovery execution, no executor binding, no callable deserialization, no worker lease validation.
