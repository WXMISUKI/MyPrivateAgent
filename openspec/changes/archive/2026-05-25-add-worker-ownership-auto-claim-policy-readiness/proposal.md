## Why

Worker ownership production gating now explains renewal supervisor and rollout readiness, but `recovery_entry_auto_claim_policy` still only reports a generic missing policy blocker. The SDK already has an explicit opt-in auto-claim path, so the production gate should expose whether auto-claim policy evidence is ready without enabling default claim behavior.

## What Changes

- Add a read-only recovery-entry auto-claim policy readiness contract.
- Thread auto-claim policy evidence into `worker_ownership.production_gate.sections[name=recovery_entry_auto_claim_policy]`.
- Keep default auto-claim disabled unless the policy is ready and explicitly production-default allowed.
- Extend runtime smoke and quality-gate normalization to assert auto-claim policy evidence is present and fail-closed by default.
- Update runtime contract docs and roadmap state.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `runtime-worker-ownership-contract`: Worker ownership contract exposes recovery-entry auto-claim policy readiness evidence.
- `worker-ownership-production-gate`: Production gate must explain auto-claim policy blockers with machine-readable policy evidence.

## Impact

- Affected backend contracts: `worker_ownership.production_gate`, `worker_ownership.operational_readiness`, runtime smoke summary, Runtime Contract Gate summary.
- Affected SDK behavior: none; `worker_ownership_auto_claim_enabled` remains explicit opt-in and disabled by default.
- Affected docs/specs: `openspec/specs/runtime-worker-ownership-contract/spec.md`, `openspec/specs/worker-ownership-production-gate/spec.md`, `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`.
- Non-goals: no default auto-claim, no recovery execution behavior change, no vendor-specific distributed lock, no background renewal loop, no child executor dispatch.
