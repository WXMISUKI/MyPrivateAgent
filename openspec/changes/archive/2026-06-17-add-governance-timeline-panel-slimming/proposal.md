# Proposal: Governance Timeline Panel Slimming

## Background

`GovernanceTimelinePanel.vue` is 1,208 lines. The Phase II exit gate assessment recommends slimming it to <800 lines. The component already has 8 child components extracted. The remaining bulk is:
- Style section: 327 lines of CSS
- Computed properties: 275 lines
- Functions/watchers: 210 lines

## Purpose

Extract the 327-line CSS section to a separate file, reducing the component from 1,208 to ~880 lines.

## Scope

- NEW: `frontend-vue/src/components/GovernanceTimelinePanel.css` — extracted styles
- MODIFIED: `GovernanceTimelinePanel.vue` — import CSS, remove inline styles

## Non-Goals

- No logic changes
- No new features
- No child component changes

## Capabilities Affected

- MODIFIED: `governance-timeline-panel-slimming`
