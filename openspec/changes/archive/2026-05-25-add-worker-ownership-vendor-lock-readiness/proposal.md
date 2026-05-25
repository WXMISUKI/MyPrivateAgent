## Why

Worker ownership production gating now explains renewal supervisor, rollout, auto-claim, and audit evidence blockers, but `vendor_lock_semantics` still only reports that SQL row lease/fencing is not a vendor lock. The production gate should expose the exact vendor lock semantics that are missing before default production ownership can be considered.

## What Changes

- Add a read-only vendor lock semantics readiness contract.
- Thread vendor lock evidence into `worker_ownership.production_gate.sections[name=vendor_lock_semantics]`.
- Keep strict SQL row lease/fencing blocked unless vendor-specific lock semantics are explicitly present and production-allowed.
- Extend runtime smoke and quality-gate normalization to assert vendor lock evidence is present and fail-closed by default.
- Update runtime contract docs and roadmap state.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `runtime-worker-ownership-contract`: Worker ownership contract exposes vendor lock semantics readiness evidence.
- `worker-ownership-production-gate`: Production gate must explain vendor lock blockers with machine-readable semantics evidence.

## Impact

- Affected backend contracts: `worker_ownership.production_gate`, `worker_ownership.operational_readiness`, runtime smoke summary, Runtime Contract Gate summary.
- Affected SDK behavior: none; no lock adapter or recovery execution behavior changes.
- Affected docs/specs: `openspec/specs/runtime-worker-ownership-contract/spec.md`, `openspec/specs/worker-ownership-production-gate/spec.md`, `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`.
- Non-goals: no vendor-specific distributed lock implementation, no production default ownership, no background renewal loop, no recovery auto-claim, no child executor dispatch.
