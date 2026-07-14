# LangGraph Controlled Pilot Smoke Review

Stage: Framework Adapter controlled pilot execution proof
Date: 2026-07-14

## Completed Work

- Added `run_langgraph_controlled_pilot_smoke(...)` to `FrameworkAdapterRuntimeService`.
- The smoke wrapper now:
  - evaluates `build_langgraph_controlled_pilot_readiness(...)` first
  - returns a blocked smoke report without external calls when readiness is blocked
  - delegates to `execute_external_adapter_run(...)` when readiness is ready
  - summarizes acceptance evidence from pilot status, final output, events, snapshot, query-control recordings, and error payloads
- Added focused tests for blocked, passed, and failed smoke outcomes.

## Scope Confirmation

Stayed within scope:

- Explicit controlled pilot smoke only.
- No default `/api/chat` change.
- No production runtime promotion.
- No new worker, scheduler, checkpoint, sandbox, or provider binding.
- No new execution path beyond the existing external pilot method.
- No AgentRun implementation.

Tempting drift avoided:

- Running external pilot without readiness.
- Treating smoke success as production readiness.
- Writing a new LangGraph execution client instead of reusing the existing adapter transport boundary.
- Promoting smoke evidence directly into production trace policy.

## Evidence

- OpenSpec change: `add-langgraph-controlled-pilot-smoke`
- Contract implementation: `backend/services/framework_adapter_runtime_service.py`
- Focused tests: `tests/agent_framework/test_framework_adapter_runtime_service_external_pilot.py`
- Canonical spec: `openspec/specs/langgraph-controlled-pilot-smoke/spec.md`

Verification:

- `openspec validate add-langgraph-controlled-pilot-smoke`
- `openspec validate langgraph-controlled-pilot-smoke`
- `python -m pytest tests/agent_framework/test_framework_adapter_runtime_service_external_pilot.py`

## Next Allowed Action

Open a trace-backed projection source proposal if the team needs this smoke evidence visible in Runtime Surface or Governance Timeline.

Do not promote LangGraph to default main chat, production runtime, or worker-backed execution in the same slice. Smoke success means the controlled pilot path can run; it does not mean the runtime is production-owned by MyPrivateAgent.
