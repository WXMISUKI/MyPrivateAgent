## Context

The current sequence is:

1. `build_langgraph_controlled_pilot_readiness(...)` decides if smoke may start.
2. `run_langgraph_controlled_pilot_smoke(...)` runs or blocks an explicit smoke.
3. The smoke report contains acceptance evidence, pilot result, snapshot ref, events, and boundaries.

Runtime Surface already knows how to compact a `runtime_plane_governance_projection`, but the smoke report is not yet normalized into that shape.

## Goals / Non-Goals

**Goals:**

- Add `build_langgraph_smoke_governance_projection(...)`.
- Accept a smoke report and produce a side-effect-free projection.
- Preserve the common projection fields: read model, contract version, run id, runtime, adapter id, result status, trace ref, event count, stage counts, approval/tool indicators, and boundaries.
- Add compact `trace_backing` evidence for the smoke-specific facts.

**Non-Goals:**

- No persistence.
- No automatic Runtime Surface injection.
- No Governance Timeline UI.
- No production trace policy.
- No new external runtime call.

## Decisions

1. Keep projection building in `FrameworkAdapterRuntimeService`.

   Rationale: this service owns LangGraph readiness, smoke execution, and existing framework adapter read models.

2. Use the existing `runtime_plane_governance_projection` read model name.

   Rationale: this allows the projection to be consumed by existing compactors while preserving extra LangGraph smoke evidence under an additive `trace_backing` object.

3. Treat blocked smoke as a valid projection source.

   Rationale: blocked evidence is useful governance information and must prove that no external call was attempted.

## Risks / Trade-offs

- [Risk] Extra `trace_backing` fields may be ignored by existing consumers. -> Mitigation: common projection fields remain populated, and later surfaces can opt into the additive section.
- [Risk] Projection could be mistaken for persisted trace. -> Mitigation: boundary flags explicitly say no persistence and no default chat change.

## Migration Plan

1. Add OpenSpec capability.
2. Implement projection builder.
3. Add focused tests for blocked, passed, and failed smoke projection.
4. Update docs and review.
5. Validate and archive.
