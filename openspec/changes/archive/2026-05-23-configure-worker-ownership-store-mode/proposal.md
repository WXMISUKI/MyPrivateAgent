## Why

The runtime now has both in-memory and SQLAlchemy worker ownership stores, but default construction still has no explicit ownership store mode. The next production-readiness slice is to make ownership store selection configurable and observable without changing the safe default.

收口对象：`worker_ownership_store` 的默认构造策略、配置入口、runtime contract 可观测字段。

非目标：本变更不把 SQL ownership store 设为默认，不新增数据库 vendor 专用锁语义，不实现后台自动 heartbeat，不改变 SDK recovery gate 的 descriptor ownership evidence 前置条件，也不改变无 ownership evidence 的兼容恢复行为。

## What Changes

- Add `WORKER_OWNERSHIP_STORE_MODE` with `memory_only`, `prefer_sql_with_fallback`, and `strict_sql` modes.
- Keep default mode as `memory_only` for backward-compatible local/runtime behavior.
- Add default worker ownership store construction that can return in-memory or SQLAlchemy-backed durable stores based on the configured mode.
- Expose the configured ownership store mode and source in `EmbeddedRuntimeFactory.build_runtime_contract()`.
- Add focused tests for mode selection, strict SQL failure, fallback behavior, and runtime contract visibility.
- Update architecture and roadmap docs to clarify that SQL ownership is opt-in through configuration.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `runtime-worker-ownership-contract`: Add configurable default ownership store selection semantics.

## Impact

- Backend configuration: `backend/config.py`
- Runtime ownership store: `backend/agent_framework/worker_ownership.py`
- Runtime dependency contract: `backend/agent_framework/runtime_dependencies.py`
- Tests: focused backend tests under `tests/agent_framework/`
- Docs truth sources: `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`
- Frontend consumption: no required UI change; existing Runtime Surface contract consumers can observe ownership mode through runtime contract data.
