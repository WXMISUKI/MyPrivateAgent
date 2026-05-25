## Context

`GovernanceTimelinePanel` is a broad orchestration component. It coordinates plan loading, timeline filtering, snapshot actions, framework-adapter summaries, and the main chat workspace in one place. The behavior is already heavily exercised, so this change should focus on structure rather than semantics.

## Goals / Non-Goals

**Goals:**
- Keep `GovernanceTimelinePanel` as the orchestration entrypoint.
- Move dense UI regions into clearer subcomponent boundaries where that improves maintainability.
- Preserve current governance behavior, filters, and snapshot interactions.
- Keep the refactor covered by focused tests.

**Non-Goals:**
- No governance semantic change.
- No backend contract change.
- No new route model or workspace redesign.
- No redesign of Runtime Surface or query read models.

## Decisions

- Preserve the panel as the top-level coordinator. The user should not lose a single orchestration point for governance timeline state.
- Split by visual and interaction density, not by arbitrary utility boundaries. The first candidates are the main chat workspace and large summary/action clusters.
- Keep event-card and filter behavior intact while extracting surrounding layout/summary scaffolding.

Alternatives considered:
- Leave the panel as-is: rejected because the file is already a maintenance hotspot.
- Split every small helper immediately: rejected because it fragments behavior without reducing meaningful complexity.
- Move everything into one generic “timeline shell”: rejected because it obscures the current domain language and makes the panel harder to reason about.

## Risks / Trade-offs

- [Low] Temporary churn in tests and imports -> Mitigation: keep behavior-focused assertions and move one region at a time.
- [Low] Component boundaries could be too granular -> Mitigation: split only where the panel is visibly dense.
- [Low] Visual regressions on mobile -> Mitigation: preserve the existing layout structure while extracting internals.
