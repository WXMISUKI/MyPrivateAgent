## Context

The runtime plane has three reference adapter slices and a shared `governance_projection` read model. Today that projection is visible only in adapter return envelopes. For the control plane to become useful to maintainers and future UI/API consumers, Runtime Surface needs a stable read-only contract that explains whether runtime-plane projections are available and what they mean.

## Goals / Non-Goals

**Goals:**

- Add a Runtime Surface profile section for runtime-plane governance projections.
- Keep the builder side-effect-free and independent from adapter execution.
- Support an optional caller-supplied projection for tests and future integration.
- Guard the new contract through snapshot coverage.

**Non-Goals:**

- Do not execute `SimpleAgentAdapter`, `ToolAgentAdapter`, or `ApprovalAgentAdapter`.
- Do not store or replay projections.
- Do not write trace/audit.
- Do not call `ApprovalEngineService`.
- Do not add frontend UI in this slice.

## Decisions

### 1. Add a dedicated builder

The new profile will live in `backend/services/runtime_surface_runtime_plane_builder.py` instead of being assembled inline.

Rationale: Runtime Surface already moved toward concern-specific builders. This avoids growing the top-level assembler and keeps the new contract independently testable.

### 2. Default to no latest projection

If no projection is supplied, the profile reports `latest_projection_available = false` and `reason = projection_source_unavailable`.

Rationale: Runtime Surface must not pretend an execution happened. It should expose readiness and contract shape, not fabricate runtime activity.

### 3. Accept an optional projection source later

The service wrapper will expose `_build_runtime_plane_governance_profile_contract(projection=None)`. The top-level profile uses the default no-projection state for now.

Rationale: this leaves a clean place for future trace-backed or request-scoped projection wiring without adding persistence in this slice.

## Risks / Trade-offs

- [Risk] Consumers may expect live runtime history. -> Mitigation: explicit `latest_projection_available` and boundary flags.
- [Risk] The profile could become another execution path. -> Mitigation: builder accepts dict input only and never imports adapters.
- [Risk] Snapshot guard adds maintenance cost. -> Mitigation: guard only stable compact fields.
