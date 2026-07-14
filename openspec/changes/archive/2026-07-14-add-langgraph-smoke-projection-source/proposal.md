## Why

LangGraph controlled pilot smoke can now produce blocked, passed, or failed evidence, but that evidence is still shaped for the smoke caller. The next production-enabling step is to convert smoke evidence into a compact runtime-plane governance projection that can later be consumed by Runtime Surface or Governance Timeline without promoting LangGraph into default execution.

收口对象：LangGraph controlled pilot smoke evidence -> read-only runtime-plane governance projection source。

非目标：不写 trace/audit，不新增前端 UI，不改变 Runtime Surface 默认数据源，不提交审批，不改 `/api/chat`，不做 LangGraph production promotion。

## What Changes

- Add a projection builder for LangGraph controlled pilot smoke reports.
- Emit the existing runtime-plane governance projection field shape where possible.
- Include compact trace-backed evidence: smoke status, acceptance, snapshot reference availability, query-control evidence availability, and external error summary.
- Keep the projection side-effect-free and compatible with future Runtime Surface/Governance Timeline consumption.

## Capabilities

### New Capabilities

- `langgraph-smoke-projection-source`: read-only projection source that converts LangGraph controlled pilot smoke evidence into compact governance projection evidence.

### Modified Capabilities

- None.

## Impact

- Backend contract/read model: `backend/services/framework_adapter_runtime_service.py`.
- Tests: `tests/agent_framework/test_framework_adapter_runtime_service_external_pilot.py`.
- Docs/specs: `openspec/specs/langgraph-smoke-projection-source/spec.md`, `docs/architecture/runtime_plane_integration_strategy.md`, `docs/roadmap/next_phase_hardening.md`, and a focused review document.
- Dependencies: none.
