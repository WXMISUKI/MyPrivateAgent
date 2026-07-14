## Why

LangGraph controlled pilot readiness can now say whether the draft adapter is allowed to enter an explicit smoke. The next production-enabling step is to make that smoke a governed contract: readiness first, explicit pilot execution second, compact acceptance evidence last.

收口对象：LangGraph explicit controlled pilot smoke read model and execution wrapper.

非目标：不接入默认 `/api/chat`，不做 production runtime promotion，不新增 worker/checkpoint/sandbox，不实现 LangGraph graph engine，不引入 AgentRun，不改变 existing external pilot transport semantics。

## What Changes

- Add a `run_langgraph_controlled_pilot_smoke(...)` service method.
- The method first evaluates `build_langgraph_controlled_pilot_readiness(...)`.
- If readiness is blocked, return a blocked smoke report without calling the external runtime.
- If readiness is ready, call the existing `execute_external_adapter_run(...)` path and summarize acceptance evidence.
- Record whether the smoke produced status/output/events/snapshot/query-control evidence while keeping default chat and production promotion disabled.

## Capabilities

### New Capabilities

- `langgraph-controlled-pilot-smoke`: explicit LangGraph pilot smoke contract gated by readiness and summarized as acceptance evidence.

### Modified Capabilities

- None.

## Impact

- Backend contract/read model: `backend/services/framework_adapter_runtime_service.py`.
- Tests: `tests/agent_framework/test_framework_adapter_runtime_service_external_pilot.py`.
- Docs/specs: `openspec/specs/langgraph-controlled-pilot-smoke/spec.md`, `docs/architecture/runtime_plane_integration_strategy.md`, `docs/roadmap/next_phase_hardening.md`, and a focused review document.
- Dependencies: none.
- External framework borrowing: use LangGraph only as an external runtime candidate through the existing adapter/transport boundary; do not copy its runtime engine into MyPrivateAgent.
