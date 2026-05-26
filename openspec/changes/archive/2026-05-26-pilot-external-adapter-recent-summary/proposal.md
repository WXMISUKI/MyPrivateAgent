## Why

Phase I now requires a promotion record before resuming channel implementation. `external_adapter` has passed readiness for the shallowest layer, so the next safe slice is a recent summary pilot that validates real Query Control trace evidence without promoting to detail, history, or workspace.

This closes the asymmetry between `subagent_lane` and `external_adapter` at the `recent summary` layer while preserving the channel promotion guardrails.

## What Changes

- Add a dedicated `external_adapter_recent_summary` read model contract.
- Expose it through Runtime Surface and a dedicated runtime-profile endpoint.
- Feed Channel Promotion Gate with real external adapter recent summary readiness instead of static unavailable evidence.
- Update specs and docs to record the resume decision: implementation may resume only for `recent summary`.
- Non-goals:
  - Do not add `external_adapter_query_detail`.
  - Do not add external adapter query history or workspace behavior.
  - Do not extract a generic recent summary assembler.
  - Do not change external adapter execution semantics.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `query-run-read-model`: Add `external_adapter_recent_summary` as the dedicated recent summary pilot for external adapter Query Control traces.
- `channel-promotion-gate`: Record the resume decision that allows only `external_adapter` recent summary implementation and keeps deeper layers blocked.
- `query-workspace-generalization`: Clarify that this implementation resumes from the shallowest eligible layer and does not promote external adapter to detail/history/workspace.

## Impact

- Backend:
  - `backend/services/runtime_surface_service.py`
  - `backend/services/runtime_surface_builders.py`
  - `backend/services/runtime_surface_builders.py` profile assembler output
  - `backend/routers/health.py`
  - `backend/services/runtime_contract_snapshot_service.py` if stable Runtime Profile fields change
- Tests:
  - `tests/agent_framework/test_runtime_surface_service.py`
  - `tests/agent_framework/test_health_router.py`
  - `tests/agent_framework/test_runtime_contract_snapshot_service.py` if snapshot surface changes
- Docs/specs:
  - `openspec/specs/query-run-read-model/spec.md`
  - `openspec/specs/channel-promotion-gate/spec.md`
  - `openspec/specs/query-workspace-generalization/spec.md`
  - `docs/architecture/runtime_contracts.md`
  - `docs/architecture/recent_summary_abstraction_note.md`
  - `docs/roadmap/next_phase_hardening.md`
