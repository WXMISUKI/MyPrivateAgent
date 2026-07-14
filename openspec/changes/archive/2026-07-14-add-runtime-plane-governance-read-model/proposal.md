## Why

Runtime Plane Stage 1 now has three local adapter proofs: `simple_agent`, `tool_agent`, and `approval_agent`. The next most valuable step is to make their normalized envelopes visible as a compact governance read model without changing execution behavior or writing production trace/audit state.

收口对象：runtime-plane envelope -> side-effect-free governance projection.

非目标：do not persist trace/audit, do not add Runtime Surface API wiring, do not change default `/api/chat`, do not submit approvals, do not resume executions, and do not introduce a managed runtime/framework dependency.

## What Changes

- Add a side-effect-free governance projection builder for `ExecutionRequest`, `AgentManifest`, `ExecutionEvent`, and `ExecutionResult`.
- Include the projection in Stage 1 adapter `execute(...)` envelopes under `governance_projection`.
- Keep the projection compact: identity, result status, event/stage counts, approval/tool indicators, trace reference, and explicit read-only boundaries.
- Add focused tests for simple/tool/approval adapter projections.
- Update runtime-plane docs and stage review notes to reflect the read-only governance wiring.

## Capabilities

### New Capabilities

- `runtime-plane-governance-read-model`: Defines the compact, side-effect-free governance projection for runtime-plane adapter envelopes.

### Modified Capabilities

- `runtime-plane-integration-strategy`: Records the post-Stage-1 read-only governance wiring step and its non-goals.

## Impact

Affected code:

- `backend/runtime_plane/governance_bridge.py`
- `backend/runtime_plane/adapters/simple_agent.py`
- `backend/runtime_plane/adapters/tool_agent.py`
- `backend/runtime_plane/adapters/approval_agent.py`
- `backend/tests/runtime_plane/test_governance_projection.py`

Affected docs/specs:

- `openspec/changes/add-runtime-plane-governance-read-model/`
- `docs/architecture/runtime_plane_integration_strategy.md`
- `docs/roadmap/next_phase_hardening.md`
- `docs/roadmap/runtime_plane_governance_read_model_review.md`
