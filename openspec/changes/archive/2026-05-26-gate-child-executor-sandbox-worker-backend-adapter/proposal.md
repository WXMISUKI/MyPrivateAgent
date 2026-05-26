## Why

Child executor sandbox worker backend adapter 已有第一刀 contract 和 dispatcher 行为，但它还没有作为独立 runtime contract coverage 进入 smoke、Quality Gate、Runtime Contract Gate 与 Snapshot 守护。下一步需要把 sandbox adapter readiness 从“已有代码路径”收成可持续验证的门禁证据，避免后续真实 child executor binding 绕过 sandbox/resource/audit/idempotency guard。

收口对象：`child_executor_sandbox_backend_coverage` runtime contract summary，以及对应 smoke/gate/snapshot/docs/spec 证据链。

## What Changes

- 新增 runtime smoke check，覆盖 ready sandbox adapter contract、incomplete guard fail-closed、compact attempt envelope、unsafe payload blocked 且不调用 backend。
- 在 Quality Gate 与 Runtime Contract Gate 中新增 `runtime_contract_summary.child_executor_sandbox_backend_coverage`，缺失或证据不一致时 fail-closed。
- 在 Runtime Contract Snapshot 中守护 sandbox backend coverage 的稳定字段，避免 summary shell 存在但 sandbox adapter gate 丢失。
- 同步 runtime contract 文档、roadmap 和 canonical spec。
- 非目标：
  - 不默认启用 child executor。
  - 不启动真实 worker、queue、sandbox runtime 或远端 executor。
  - 不新增数据库迁移、持久化 workspace 或跨进程 child run recovery。
  - 不扩前端展示面，不让 UI 自行重算 sandbox readiness。

## Capabilities

### New Capabilities

### Modified Capabilities

- `child-executor-sandbox-worker-backend`: 新增 sandbox worker backend adapter coverage 必须进入 runtime smoke / Quality Gate / Runtime Contract Gate / Snapshot 的要求。

## Impact

- 后端 contract/gate：
  - `backend/scripts/runtime_contract_smoke.py`
  - `backend/scripts/quality_gate_report.py`
  - `backend/services/runtime_contract_gate_service.py`
  - `backend/services/runtime_contract_snapshot_service.py`
- 后端 contract helpers / tests：
  - `backend/agent_framework/child_executor_sandbox_worker_backend.py`
  - `backend/agent_framework/child_executor_dispatcher.py`
  - `tests/agent_framework/*`
- 文档真源：
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
  - `openspec/specs/child-executor-sandbox-worker-backend/spec.md`
