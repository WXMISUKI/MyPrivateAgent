## Context

`GovernanceTimelinePanel` has already delegated overview cards, event stream, framework adapter cards, recent snapshot commands, summary actions, and the main chat workspace to child components. The remaining focus summary grid is still a dense block of display markup mixed into the parent template.

The current Phase II direction prefers delivery-surface slimming over more `main_chat` local feature expansion. This change is therefore a small frontend boundary extraction, not a new governance capability.

## Goals / Non-Goals

**Goals:**

- Move the focus summary grid into a child component with props for display values.
- Forward user actions through emits without changing route, filter, query, or clipboard ownership.
- Preserve existing labels, classes, and visible behavior.
- Keep focused Vitest coverage small and disposable-test-file-free.

**Non-Goals:**

- Do not change backend contracts, runtime profile fields, query read models, or governance semantics.
- Do not add new query workspace behavior or promote any non-`main_chat` channel.
- Do not redesign the governance page layout.
- Do not run `npm build` for this low-risk frontend extraction.

## Decisions

1. Extract `GovernanceTimelineFocusSummaryGrid` instead of splitting the event stream.
   - The event stream is already the trunk component and should remain cohesive.
   - The summary grid is display-heavy, has a clear prop/event seam, and does not need direct route ownership.

2. Keep all computed interpretation in the parent.
   - The child receives labels, overview objects, and flags.
   - The parent remains responsible for `activeFilter`, `activeQueryId`, `activeQueryStage`, dedupe state, snapshot focus, and clipboard side effects.

3. Preserve existing CSS class names.
   - This minimizes visual regression risk and keeps existing tests/selectors useful.
   - Component-local styles will carry the summary card layout because scoped parent styles do not apply to child roots.

## Risks / Trade-offs

- [Risk] The prop surface is broad because the extracted block displays many independent parent states.
  -> Mitigation: keep this extraction display-only and avoid moving interpretation logic into the child.
- [Risk] Scoped styles may stop applying after extraction.
  -> Mitigation: move the summary grid/card styles needed by the child into the child component.
- [Risk] Parent integration could lose a clear/copy event.
  -> Mitigation: add a focused child test for event forwarding and keep the existing parent test running.
