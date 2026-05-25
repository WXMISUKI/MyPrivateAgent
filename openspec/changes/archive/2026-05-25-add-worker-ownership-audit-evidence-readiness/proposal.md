## Why

Worker ownership production gating now explains renewal supervisor, rollout readiness, and recovery-entry auto-claim policy blockers, but `ownership_audit_evidence` still reports a generic boolean blocker. The gate should expose whether audit evidence is compact, operation-linked, idempotent, and explicitly non-authoritative without enabling ownership or recovery execution.

## What Changes

- Add a read-only worker ownership audit evidence readiness contract.
- Thread audit evidence into `worker_ownership.production_gate.sections[name=ownership_audit_evidence]`.
- Keep production ownership blocked unless audit evidence is ready and remains a non-authorization source.
- Extend runtime smoke and quality-gate normalization to assert audit evidence is present and fail-closed by default.
- Update runtime contract docs and roadmap state.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `runtime-worker-ownership-contract`: Worker ownership contract exposes ownership audit evidence readiness.
- `worker-ownership-production-gate`: Production gate must explain audit evidence blockers with machine-readable evidence.

## Impact

- Affected backend contracts: `worker_ownership.production_gate`, `worker_ownership.operational_readiness`, runtime smoke summary, Runtime Contract Gate summary.
- Affected SDK behavior: none; no audit writer or recovery execution behavior changes.
- Affected docs/specs: `openspec/specs/runtime-worker-ownership-contract/spec.md`, `openspec/specs/worker-ownership-production-gate/spec.md`, `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`.
- Non-goals: no audit writer side effects, no audit-as-authorization, no default worker ownership, no vendor-specific distributed lock, no background renewal loop, no child executor dispatch.
