## Why

Child executor 已具备 relationship preflight、record-only binding、sandbox backend adapter gate 和 dispatcher contract，但当前 record-only binding 容易被后续消费方误读为真实 executor 授权。下一步需要把真实 child executor 的执行绑定显式 opt-in 化，确保即使其他 prerequisites 看起来 ready，缺少显式执行绑定时仍 fail-closed。

收口对象：`child_executor_execution_prerequisites` 与 `child_executor_dispatch_contract` 中的 explicit executor binding readiness evidence，以及对应 smoke / Quality Gate / Runtime Contract Gate / Snapshot coverage。

## What Changes

- 新增 explicit child executor binding readiness evidence，区分 relationship record-only binding 与 real executor opt-in binding。
- 在 execution prerequisites 中新增 `explicit_executor_binding_opt_in` 要求，缺失时保持 blocked。
- 在 dispatch contract 中暴露 explicit binding status/source/blockers，并阻止缺失 opt-in 的 dispatch readiness。
- 在 child executor execution contract 中要求 explicit opt-in 后才允许 skeleton execution path 执行。
- 新增 runtime smoke、Quality Gate、Runtime Contract Gate 和 Snapshot coverage。
- 非目标：
  - 不默认启动真实 child executor。
  - 不启动 worker、queue、sandbox runtime 或远端 executor。
  - 不实现完整 context budget 或 merge handoff。
  - 不引入数据库迁移或前端展示面。

## Capabilities

### New Capabilities

### Modified Capabilities

- `child-executor-execution-prerequisites`: 新增 explicit executor binding opt-in readiness 要求。
- `child-executor-dispatch-contract`: dispatch readiness 必须读取 explicit binding readiness，缺失时 fail-closed。

## Impact

- 后端 contract / SDK：
  - `backend/agent_framework/sdk.py`
  - `backend/scripts/runtime_contract_smoke.py`
  - `backend/scripts/quality_gate_report.py`
  - `backend/services/runtime_contract_gate_service.py`
  - `backend/services/runtime_contract_snapshot_service.py`
- 测试：
  - `tests/agent_framework/test_embedded_runtime_sdk.py`
  - `tests/agent_framework/test_runtime_contract_smoke.py`
  - `tests/agent_framework/test_quality_gate_report.py`
  - `tests/agent_framework/test_runtime_contract_gate_service.py`
  - `tests/agent_framework/test_runtime_contract_snapshot_service.py`
- 文档真源：
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
  - `openspec/specs/child-executor-execution-prerequisites/spec.md`
  - `openspec/specs/child-executor-dispatch-contract/spec.md`
