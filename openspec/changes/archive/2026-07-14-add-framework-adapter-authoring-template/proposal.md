## Why

Runtime Plane Stage 1 has proven the local `simple_agent` / `tool_agent` / `approval_agent` envelope and governance projection shape, but external framework integration still depends on reviewer memory. The next production-enabling step is a reusable adapter authoring template that tells teams how to map mature runtimes such as LangGraph or AgentRun into MyPrivateAgent without turning this project into a new execution platform.

收口对象：`FrameworkAdapterRuntimeService.build_adapter_authoring_checklist(...)` 的只读 checklist/read-model contract。

非目标：不实现 LangGraph、AgentRun 或其他框架执行；不创建 worker、checkpoint、sandbox、scheduler；不改变 `/api/chat`；不写 trace/audit；不注册工具。

## What Changes

- Extend the framework adapter authoring checklist with a machine-readable `authoring_template`.
- Encode recommended adapter file boundaries, required contracts, runtime-plane proof mapping, projection mapping, smoke test checklist, and promotion gate requirements.
- Keep the checklist side-effect-free and conservative: it can guide an adapter author, but it cannot execute, register, promote, or mutate state.
- Update focused tests and docs so future adapter work follows the same template instead of adding ad hoc runtime paths.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `framework-adapter-authoring-checklist`: add an adapter authoring template section to the existing checklist contract.

## Impact

- Backend contract/read model: `backend/services/framework_adapter_runtime_service.py`.
- Tests: `tests/agent_framework/test_framework_adapter_runtime_service.py`.
- Specs/docs: `openspec/specs/framework-adapter-authoring-checklist/spec.md`, `docs/architecture/runtime_plane_integration_strategy.md`, `docs/roadmap/next_phase_hardening.md`, and a focused stage review document.
- Dependencies: none.
- External framework borrowing: borrow LangGraph/AgentRun style adapter boundaries and smoke discipline; do not borrow their execution engine into MyPrivateAgent.
