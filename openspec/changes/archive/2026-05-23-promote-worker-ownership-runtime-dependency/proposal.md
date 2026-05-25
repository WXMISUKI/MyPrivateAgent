## Why

SDK recovery gate 已经可以显式消费 `worker_ownership_store`，但该 store 还不是 `EmbeddedRuntimeDependencies` 的一等依赖。结果是默认 runtime factory、Runtime Surface 和垂域 bootstrap 无法从统一 contract 看到 ownership adapter 的真实状态，也无法通过 runtime dependency bundle 传递同一个 ownership store。

本变更收口对象：把 worker ownership store 纳入 embedded runtime dependency seam 和 factory contract。它只提升依赖注入与 contract 可见性，不改变默认 recovery gate 触发条件。

非目标：不实现 SQL lease store、不改变 recovery operation 默认 `worker_ownership.implemented=false`、不自动 claim lease、不让 SDK 在没有 descriptor ownership evidence 时启用 gate。

## What Changes

- `EmbeddedRuntimeDependencies` 增加 `worker_ownership_store`。
- 默认 dependencies 提供 in-memory worker ownership store。
- `EmbeddedRuntimeFactory.create_sdk(...)` 通过 `runtime_dependencies` 把 ownership store 传给 SDK。
- `EmbeddedRuntimeFactory.build_runtime_contract()` 暴露 `worker_ownership` dependency contract。
- 补 focused tests，证明 factory dependency 能传入 SDK，contract 能暴露 ownership adapter 边界。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `runtime-worker-ownership-contract`: worker ownership 从独立 seam 推进为 runtime dependency 可见能力。
- `embedded-sdk-persistence-interface` / runtime factory contract: dependency sources 增加 worker ownership store。

## Impact

- Affected code: `backend/agent_framework/runtime_dependencies.py`、`backend/agent_framework/sdk.py`、`backend/agent_framework/worker_ownership.py`。
- Affected tests: focused SDK runtime dependency tests。
- Affected docs: `docs/architecture/runtime_contracts.md`、`docs/roadmap/next_phase_hardening.md`、`docs/test_manual.md`。
