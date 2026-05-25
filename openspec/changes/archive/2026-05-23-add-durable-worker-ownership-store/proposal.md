## Why

Worker ownership has already become a first-class runtime dependency, but the default implementation is still in-memory and reports `durable = false`. To move recovery execution toward enterprise production readiness, the next safe slice is to add a durable ownership adapter contract and minimal SQL-backed implementation while preserving the existing descriptor-evidence-driven SDK gate.

收口对象：`runtime-worker-ownership-contract` 的 durable adapter boundary, including lease persistence, monotonic fencing, heartbeat, validation, and compact evidence reporting.

非目标：本变更不把 SQL ownership store 设为全局默认，不实现跨数据库 vendor 的强分布式锁语义，不新增后台自动续租 worker，不改变 SDK recovery 自动 claim / resume 行为，也不把缺少 ownership evidence 的旧恢复路径改成强制 gate。

## What Changes

- Add a durable worker ownership adapter requirement to the existing worker ownership contract.
- Add a SQLAlchemy-backed runtime worker ownership store with the same `claim_run`, `heartbeat`, `validate_ownership`, and `get_lease` surface as the in-memory store.
- Preserve compact non-executable ownership evidence and mark the SQL adapter as `adapter_kind = "sqlalchemy"` and `durable = true`.
- Add focused tests covering cross-store persistence, active lease blocking, expired lease replacement with higher fencing tokens, heartbeat refresh, and stale fencing fail-closed.
- Update runtime architecture and hardening roadmap docs to distinguish the current default in-memory adapter from the new durable adapter option.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `runtime-worker-ownership-contract`: Add durable ownership store requirements and SQL-backed adapter evidence semantics.

## Impact

- Backend contract: `backend/agent_framework/worker_ownership.py`
- Runtime dependency contract: no breaking shape change; durable SQL store remains opt-in through dependency injection.
- Tests: focused backend tests under `tests/agent_framework/`.
- Docs truth sources: `docs/architecture/runtime_contracts.md` and `docs/roadmap/next_phase_hardening.md`.
- Frontend consumption: no direct UI contract change in this slice; runtime contract consumers may observe `worker_ownership.durable = true` only when a SQL store is explicitly injected.
