# Framework Adapter Authoring Template Review

Stage: Runtime Plane Stage 2/3 bridge
Date: 2026-07-14

## Completed Work

- Added `authoring_template` to the existing framework adapter authoring checklist.
- Mapped Stage 1 proof slices to adapter authoring responsibilities:
  - `simple_agent`: request/event/result envelope and final output normalization.
  - `tool_agent`: controlled read-only tool observation without bypassing ToolRuntime policy.
  - `approval_agent`: high-risk intent becomes approval evidence without handler execution.
- Linked adapter output expectations to `runtime_plane_governance_profile`.
- Added focused tests for ready, blocked, and unknown adapter review paths.

## Scope Confirmation

Stayed within scope:

- Side-effect-free read model only.
- No external framework execution.
- No trace/audit writes from checklist generation.
- No tool registration.
- No default `/api/chat` change.
- No worker, scheduler, checkpoint, sandbox, or provider binding.

Tempting drift avoided:

- Implementing a real LangGraph or AgentRun adapter in the same slice.
- Creating a second adapter template service.
- Promoting `pilot_candidate` to production readiness.
- Adding another local runtime-plane demo instead of preparing mature framework integration.

## Evidence

- OpenSpec change: `add-framework-adapter-authoring-template`
- Contract implementation: `backend/services/framework_adapter_runtime_service.py`
- Focused tests: `tests/agent_framework/test_framework_adapter_runtime_service.py`
- Canonical spec: `openspec/specs/framework-adapter-authoring-checklist/spec.md`

Verification:

- `openspec validate add-framework-adapter-authoring-template`
- `python -m pytest tests/agent_framework/test_framework_adapter_runtime_service.py`

## Next Allowed Action

Choose one controlled pilot proposal:

1. LangGraph adapter controlled pilot for graph/state/checkpoint/human-in-loop semantics.
2. AgentRun adapter controlled pilot for managed runtime/sandbox/deployment/observability semantics.
3. Trace-backed projection source proposal if governance replay evidence is needed before real adapter execution.

Do not continue by extending the local runtime graph engine, checkpoint layer, sandbox, or scheduler unless a new OpenSpec proposal explicitly proves that it is control-plane-owned and not duplicating mature runtime infrastructure.
