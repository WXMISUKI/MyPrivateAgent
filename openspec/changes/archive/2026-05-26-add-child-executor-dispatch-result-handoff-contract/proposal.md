## Why

Child executor dispatch now has an opt-in dispatcher and a sandbox attempt handoff contract, but the adapter return path is still only represented as raw dispatcher output. We need a compact, machine-readable result handoff contract so downstream governance can tell whether a backend result is audit-ready without treating it as parent merge completion or default worker execution.

收口对象：child executor backend result handoff / audit evidence after an explicit dispatcher invocation.

非目标：不启动默认 worker，不实现 sandbox runtime，不执行 parent merge，不启用 retry scheduler，不改变 SDK 默认 dispatch behavior。

## What Changes

- Add a side-effect-free `child_executor_dispatch_result_handoff` contract for compact backend result normalization.
- Extend the dispatcher path to attach result handoff evidence to successful or blocked dispatch attempts.
- Add runtime smoke / quality gate / Runtime Contract Gate / snapshot coverage for result handoff evidence.
- Sync runtime contract docs and roadmap with the new post-dispatch boundary.

## Capabilities

### New Capabilities
- `child-executor-dispatch-result-handoff`: Defines compact result handoff and audit evidence for child executor dispatcher backend results.

### Modified Capabilities
- `child-executor-dispatcher`: Dispatcher results must expose result handoff evidence while remaining opt-in and fail-closed.

## Impact

- Affected backend code:
  - `backend/agent_framework/child_executor_dispatcher.py`
  - `backend/agent_framework/__init__.py`
  - runtime smoke / quality gate / runtime contract gate / snapshot services
- Affected tests:
  - `tests/agent_framework/test_child_executor_dispatcher.py`
  - `tests/agent_framework/test_runtime_contract_smoke.py`
  - `tests/agent_framework/test_quality_gate_report.py`
  - `tests/agent_framework/test_runtime_contract_gate_service.py`
  - `tests/agent_framework/test_runtime_contract_snapshot_service.py`
- Affected docs/specs:
  - `docs/architecture/runtime_contracts.md`
  - `docs/roadmap/next_phase_hardening.md`
  - OpenSpec child executor dispatcher and result handoff specs
- No new API endpoint, dependency, database migration, or frontend UI is introduced.
