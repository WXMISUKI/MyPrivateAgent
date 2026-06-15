# Design: Governance Timeline Panel Slimming

## Context

`GovernanceTimelinePanel.vue` is 1,208 lines. The Phase II exit gate assessment recommends slimming it to <800 lines. The component already has 8 child components extracted. The remaining bulk is the style section (327 lines).

## Goals

1. Extract the 327-line CSS section to a separate file.
2. Reduce the component from 1,208 to ~880 lines.
3. Maintain identical visual behavior.

## Non-Goals

1. No logic changes.
2. No new features.
3. No child component changes.

## Key Decisions

### Decision 1: Extract to separate CSS file

Extract the CSS to `GovernanceTimelinePanel.css` and import it in the component. This:
- Reduces component size by ~300 lines
- Keeps styles co-located with the component
- Maintains scoped CSS behavior (via module import)

### Decision 2: Keep scoped styles

The CSS uses `scoped` styles. When extracting to a separate file, we'll use CSS modules or a global import with a namespace prefix to maintain isolation.

## Risks

| Risk | Mitigation |
|------|-----------|
| CSS specificity changes | Use same selectors, just move to file |
| Build tool compatibility | Vue supports CSS imports natively |

## Migration

None required. This is a pure refactoring.
