## Why

Worker ownership production gating now blocks durable recovery with machine-readable evidence, but the `heartbeat_renewal_supervisor` section still only states that a background supervisor is missing. Before recovery, retry, or worker dispatch can treat ownership as production authority, operators need a compact contract explaining the renewal policy gap without starting a supervisor.

## What Changes

- Add a read-only worker ownership renewal supervisor readiness contract.
- Thread the renewal supervisor contract into `worker_ownership.production_gate.sections[name=heartbeat_renewal_supervisor]`.
- Keep worker ownership production default disabled unless the renewal supervisor is ready and explicitly production-enabled.
- Extend runtime smoke and quality-gate normalization to assert the nested renewal evidence is present and still blocked by default.
- Update runtime contract docs and roadmap state.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `runtime-worker-ownership-contract`: Worker ownership production gate must expose renewal supervisor readiness evidence and keep default production ownership blocked when the supervisor is missing or not production-enabled.

## Impact

- Affected backend contracts: `worker_ownership.production_gate`, `worker_ownership.operational_readiness`, runtime smoke summary, Runtime Contract Gate summary.
- Affected frontend consumers: existing Runtime Surface/Governance consumers may see richer nested evidence; no UI change is required.
- Affected docs/specs: `openspec/specs/runtime-worker-ownership-contract/spec.md`, `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`.
- Non-goals: no vendor-specific distributed lock, no background renewal loop, no default recovery entry auto-claim, no child executor dispatch, no production recovery execution.
