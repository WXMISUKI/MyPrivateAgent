## Why

Phase II 已经把 approval lifecycle、continuation descriptor、registry reattach、workspace backend state contract 和 Runtime Surface recovery gate 收口成机器可读 contract。下一步需要把这些能力推进到 durable runtime recovery v1：系统必须能明确表达 checkpoint、resume cursor 与 durable workspace 的关系，而不是继续把“有 descriptor”误读为“可恢复执行”。

这个 change 解决的是后端 Runtime Core 的恢复边界问题：让 `submit_approval()`、`resume_run()`、`probe_run_recovery()`、`get_run_recovery(...)` 和 quality gate 对“当前能否恢复执行、恢复到哪里、为什么不能恢复”使用同一套 checkpoint/resume 语义。

## 收口对象

- `EmbeddedAgentRuntimeSDK`
- `EmbeddedRunWorkspaceStore`
- `EmbeddedContinuationRegistry`
- `RuntimeSurfaceService.get_run_recovery(...)`
- `runtime_contract_smoke.py`
- `RuntimeContractGateService`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`
- `docs/test_manual.md`

## What Changes

- Introduce a durable checkpoint/resume cursor contract for embedded runtime recovery.
- Define which persisted runtime records can form a checkpoint: run snapshot, event log, approval snapshot, continuation descriptor, artifact ref, child executor output.
- Define a `resume_cursor` shape that points to the next recoverable action without storing Python callables.
- Extend recovery probes and Runtime Surface recovery to report checkpoint readiness and cursor readiness with machine-readable reasons.
- Add runtime smoke and quality gate coverage proving durable checkpoint metadata aligns with approval lifecycle and continuation recovery gates.
- Keep external framework references as vocabulary calibration only: borrow checkpoint/interruption/resume semantics, but keep runtime orchestration inside our harness core.

## 非目标

- Do not migrate Runtime Core to LangGraph or any graph runtime.
- Do not introduce a full distributed scheduler or multi-worker lock manager in this change.
- Do not persist Python callables, active stream iterators, or in-process function bindings.
- Do not build a frontend-first governance view before the backend recovery contract is stable.
- Do not add a database migration unless existing workspace store tables cannot express checkpoint metadata.

## Capabilities

### New Capabilities

- `durable-runtime-checkpoint-resume`: Defines durable checkpoint and resume cursor semantics for embedded runtime recovery.

### Modified Capabilities

- `query-run-read-model`: Recovery read models must expose checkpoint/cursor status without requiring consumers to inspect SDK internals.

## Impact

- Backend runtime: `backend/agent_framework/sdk.py`, `backend/agent_framework/persistence.py`, `backend/agent_framework/continuations.py`, `backend/services/runtime_surface_service.py`.
- Governance and gates: `backend/scripts/runtime_contract_smoke.py`, `backend/scripts/quality_gate_report.py`, `backend/services/runtime_contract_gate_service.py`, `backend/services/runtime_contract_snapshot_service.py`.
- Tests: focused backend tests under `tests/agent_framework/`, especially embedded SDK, workspace store, runtime surface, contract smoke, and contract gate tests.
- Docs: runtime contracts, roadmap, and manual test docs must be updated alongside implementation.
