# LangGraph Controlled Pilot Readiness Review

Stage: Framework Adapter controlled pilot preparation
Date: 2026-07-14

## Completed Work

- Added `build_langgraph_controlled_pilot_readiness(...)` to `FrameworkAdapterRuntimeService`.
- Composed readiness from:
  - adapter registry
  - LangGraph precheck evidence
  - external pilot enablement
  - authoring template availability
  - Stage 1 proof mapping
  - default chat boundary
- Added focused tests for ready, disabled external pilot, unknown adapter, and registered unsupported adapter paths.

## Scope Confirmation

Stayed within scope:

- Side-effect-free read model only.
- No external LangGraph call.
- No trace/audit writes.
- No approval submission.
- No default `/api/chat` change.
- No AgentRun implementation.
- No worker, scheduler, checkpoint, sandbox, or provider binding.

Tempting drift avoided:

- Running `execute_external_adapter_run(...)` in the readiness gate.
- Treating `can_start_controlled_pilot = true` as production runtime authorization.
- Starting an AgentRun adapter before the existing LangGraph pilot path has been validated.
- Expanding the local runtime plane to mimic LangGraph checkpointing or graph execution.

## Evidence

- OpenSpec change: `add-langgraph-controlled-pilot-readiness`
- Contract implementation: `backend/services/framework_adapter_runtime_service.py`
- Focused tests: `tests/agent_framework/test_framework_adapter_runtime_service.py`
- Canonical spec: `openspec/specs/langgraph-controlled-pilot-readiness/spec.md`

Verification:

- `openspec validate add-langgraph-controlled-pilot-readiness`
- `openspec validate langgraph-controlled-pilot-readiness`
- `python -m pytest tests/agent_framework/test_framework_adapter_runtime_service.py`

## Next Allowed Action

Run an explicit LangGraph controlled pilot smoke only when the readiness gate returns:

- `readiness_status = ready`
- `can_start_controlled_pilot = true`
- `next_allowed_action = run_explicit_controlled_pilot_smoke`

If this smoke needs persistent governance replay, open a separate trace-backed projection source proposal. Do not promote LangGraph to default main chat or production runtime in the same slice.
