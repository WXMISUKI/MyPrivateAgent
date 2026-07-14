## Why

The framework adapter authoring template now tells teams how to build adapters, but it still does not answer the operational question: "Is LangGraph ready to enter an explicit controlled pilot smoke?" Without a machine-readable readiness gate, teams can confuse draft adapter registration or a passing precheck with production runtime promotion.

收口对象：LangGraph external adapter controlled pilot readiness read model。

非目标：不执行 LangGraph runtime、不调用外部 endpoint、不写 trace/audit、不提交审批、不注册工具、不改变 `/api/chat`、不引入 AgentRun 或其他框架实现。

## What Changes

- Add a side-effect-free controlled pilot readiness contract for `langgraph_draft`.
- Compose existing precheck evidence and authoring template evidence into one readiness gate.
- Require explicit external pilot enablement, package/env readiness, authoring template availability, Stage 1 proof mapping, minimum smoke checklist, and disabled default chat boundary.
- Block unknown adapters and registered non-LangGraph adapters conservatively.
- Update focused tests and docs so the next external runtime step is a controlled pilot smoke, not production execution.

## Capabilities

### New Capabilities

- `langgraph-controlled-pilot-readiness`: machine-readable readiness gate for allowing LangGraph draft adapter to enter an explicit controlled pilot smoke.

### Modified Capabilities

- None.

## Impact

- Backend contract/read model: `backend/services/framework_adapter_runtime_service.py`.
- Tests: `tests/agent_framework/test_framework_adapter_runtime_service.py`.
- Docs/specs: `openspec/specs/langgraph-controlled-pilot-readiness/spec.md`, `docs/architecture/runtime_plane_integration_strategy.md`, `docs/roadmap/next_phase_hardening.md`, and a focused review document.
- Dependencies: none.
- External framework borrowing: borrow LangGraph as a managed execution runtime candidate; do not copy its graph engine, checkpointing, worker, or deployment model into MyPrivateAgent.
