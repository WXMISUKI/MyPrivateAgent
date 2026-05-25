## Why

Phase II 已经具备 workspace store、continuation descriptor、registry reattach、checkpoint/resume cursor 和 runtime factory 第一刀，但 SDK 调用方仍缺少一个明确的持久化接口 contract：如何选择 durable workspace、如何判断当前 SDK 是否只是 memory preview、以及如何把 persistence posture 暴露给恢复消费方。

现在需要先把接口边界写清，避免后续在 `EmbeddedAgentRuntimeSDK`、`AgentHarnessFacade`、`RuntimeSurfaceService` 和质量门禁里各自解释“持久化已启用”的含义。

## 收口对象

- `EmbeddedAgentRuntimeSDK`
- `AgentHarnessFacade`
- `EmbeddedRuntimeDependencies`
- `EmbeddedRuntimeFactory`
- `EmbeddedRunWorkspaceStore`
- `RuntimeSurfaceService`
- `runtime_contract_smoke.py`
- `quality_gate_report.py`
- `RuntimeContractGateService`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`

## What Changes

- Define a first-class `embedded_sdk_persistence_interface` contract for SDK bootstrap and runtime profile consumption.
- Require SDK/facade construction paths to expose whether persistence is `memory_preview`, `durable_ready`, or `durable_degraded`.
- Define the minimum machine-readable fields needed by recovery consumers: workspace backend kind, durability, fallback status, persistence profile, and recovery posture.
- Require durable-capable SDK paths to continue using `EmbeddedRuntimeDependencies` / `EmbeddedRuntimeFactory` rather than ad hoc workspace construction.
- Add focused contract/smoke coverage so persistence posture cannot silently drift away from recovery probe and runtime factory output.
- Keep existing checkpoint/resume cursor semantics intact; this change clarifies the interface that selects and reports persistence, not a new recovery algorithm.

## 非目标

- Do not introduce a new database schema unless implementation proves the existing workspace store cannot represent the interface.
- Do not implement distributed locks, multi-worker scheduling, or remote execution ownership.
- Do not persist Python callables, stream iterators, provider clients, or arbitrary executable bindings.
- Do not replace checkpoint/resume cursor semantics from the existing durable recovery contract.
- Do not build a new frontend governance panel before the backend contract is stable.
- Do not migrate the runtime to LangGraph or any external harness.

## Capabilities

### New Capabilities

- `embedded-sdk-persistence-interface`: Defines the SDK-facing persistence posture contract, bootstrap requirements, and minimal observable fields for durable embedded runtime use.

### Modified Capabilities

- `durable-workspace-state-contract`: Adds requirements that backend descriptions are consumable by the SDK persistence interface without changing the durable/runtime-only state vocabulary.
- `embedded-sdk-recovery-protocol`: Adds requirements that recovery probes and blocked recovery reasons remain aligned with the selected persistence posture.

## Impact

- Backend runtime: `backend/agent_framework/sdk.py`, `backend/agent_framework/harness.py`, `backend/agent_framework/runtime_dependencies.py`, `backend/agent_framework/persistence.py`.
- Runtime surface and gates: `backend/services/runtime_surface_service.py`, `backend/services/runtime_surface_builders.py`, `backend/scripts/runtime_contract_smoke.py`, `backend/scripts/quality_gate_report.py`, `backend/services/runtime_contract_gate_service.py`, `backend/services/runtime_contract_snapshot_service.py`.
- Tests: focused backend tests under `tests/agent_framework/`, especially embedded SDK, embedded workspace store, runtime factory, runtime surface, contract smoke, and contract gate tests.
- Docs/specs: `docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`, `docs/test_manual.md`, plus the new OpenSpec capability.

## External Reference Policy

- Borrow from LangGraph only the vocabulary distinction between checkpoint storage, resumable cursor, and runtime execution ownership.
- Borrow from OpenHands only the idea that persisted action/observation evidence should be inspectable without re-running execution.
- Do not copy external graph persistence, worker orchestration, product shell, or sandbox model into this slice.
