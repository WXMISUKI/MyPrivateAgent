## Why

Worker ownership production gating now explains renewal supervisor readiness, but `rollout_checklist` still only reports a generic incomplete rollout blocker. Before ownership can become default authority for recovery or retry, operators need machine-readable rollout evidence without enabling production ownership.

## What Changes

- Add a read-only worker ownership production rollout readiness contract.
- Thread rollout readiness evidence into `worker_ownership.production_gate.sections[name=rollout_checklist]`.
- Keep production ownership blocked unless rollout evidence is ready and explicitly production-confirmed.
- Extend runtime smoke and quality-gate normalization to assert rollout evidence is present and fail-closed by default.
- Update runtime contract docs and roadmap state.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `runtime-worker-ownership-contract`: Worker ownership contract exposes production rollout readiness evidence.
- `worker-ownership-production-gate`: Production gate must explain rollout checklist blockers with machine-readable rollout evidence.

## Impact

- Affected backend contracts: `worker_ownership.production_gate`, `worker_ownership.operational_readiness`, runtime smoke summary, Runtime Contract Gate summary.
- Affected frontend consumers: existing Runtime Surface/Governance consumers may see richer nested evidence; no UI change is required.
- Affected docs/specs: `openspec/specs/runtime-worker-ownership-contract/spec.md`, `openspec/specs/worker-ownership-production-gate/spec.md`, `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`.
- Non-goals: no vendor-specific distributed lock, no background renewal loop, no production ownership enablement, no recovery entry auto-claim, no child executor dispatch.
