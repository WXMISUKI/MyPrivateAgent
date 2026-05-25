## Why

Worker ownership now has a vendor lock adapter seam, but it still cannot describe a concrete backend family. The next safe step is a PostgreSQL advisory lock probe contract that records the expected semantics for a future implementation without acquiring locks, opening database connections, or granting production default ownership.

## What Changes

- Add a read-only PostgreSQL advisory lock probe contract for worker ownership.
- Allow the vendor lock adapter contract to embed backend probe evidence.
- Surface compact PostgreSQL probe evidence through `worker_ownership.production_gate.sections[name=vendor_lock_semantics].evidence`.
- Extend runtime smoke, Quality Gate, and Runtime Contract Gate summaries so missing concrete backend readiness is machine-readable.
- Keep production default ownership blocked: no real lock acquisition, no background worker, no default recovery auto-claim, and no `WORKER_OWNERSHIP_STORE_MODE` default change.

## Capabilities

### New Capabilities

### Modified Capabilities

- `runtime-worker-ownership-contract`: expose PostgreSQL advisory lock probe evidence inside the vendor lock adapter seam.
- `worker-ownership-production-gate`: surface PostgreSQL probe blockers as part of the vendor lock section.

## Impact

- Affected backend contract: `backend/agent_framework/worker_ownership.py`.
- Affected gate/report paths: `backend/scripts/runtime_contract_smoke.py`, `backend/scripts/quality_gate_report.py`, and `backend/services/runtime_contract_gate_service.py`.
- Affected tests: focused worker ownership, runtime smoke, quality gate, and runtime contract gate tests.
- Affected docs/specs: `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`, and worker ownership OpenSpec specs.

收口对象：PostgreSQL advisory lock backend probe contract evidence.

非目标：不连接 PostgreSQL，不执行 `pg_try_advisory_lock` / unlock，不实现真实 distributed lock adapter，不启用 production default ownership，不启用 recovery auto-claim，不启动后台续租或 worker。
