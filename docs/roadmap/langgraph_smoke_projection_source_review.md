# LangGraph Smoke Projection Source Review

Stage: Framework Adapter controlled pilot governance projection
Date: 2026-07-14

## Completed Work

- Added `build_langgraph_smoke_governance_projection(...)` to `FrameworkAdapterRuntimeService`.
- The projection builder converts blocked, passed, and failed smoke reports into `runtime_plane_governance_projection` compatible evidence.
- The projection includes compact `trace_backing` evidence:
  - smoke status
  - acceptance status
  - external call attempted flag
  - snapshot availability
  - query-control recording availability
  - final output availability
  - compact external error summary

## Scope Confirmation

Stayed within scope:

- Read-only projection source only.
- No trace/audit writes.
- No projection persistence.
- No Runtime Surface default source change.
- No Governance Timeline UI.
- No default `/api/chat` change.
- No production runtime promotion.

Tempting drift avoided:

- Persisting smoke projections immediately.
- Treating smoke projection as production trace policy.
- Expanding LangGraph execution semantics inside MyPrivateAgent.
- Building frontend panels before the backend read model stabilized.

## Evidence

- OpenSpec change: `add-langgraph-smoke-projection-source`
- Contract implementation: `backend/services/framework_adapter_runtime_service.py`
- Focused tests: `tests/agent_framework/test_framework_adapter_runtime_service_external_pilot.py`
- Canonical spec: `openspec/specs/langgraph-smoke-projection-source/spec.md`

Verification:

- `openspec validate add-langgraph-smoke-projection-source`
- `openspec validate langgraph-smoke-projection-source`
- `python -m pytest tests/agent_framework/test_framework_adapter_runtime_service_external_pilot.py`

## Next Allowed Action

Let Runtime Surface explicitly consume the LangGraph smoke projection source as a supplied projection and expose compact profile-level visibility.

Do not write production trace, promote LangGraph to default main chat, or make the projection persistent in the same slice.
