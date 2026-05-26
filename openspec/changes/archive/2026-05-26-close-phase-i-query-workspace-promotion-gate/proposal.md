## Why

Phase I has completed the query workspace promotion discipline needed before resuming deeper channel work. `main_chat` is the canonical workspace baseline, `subagent_lane` has stopped below history/workspace, and `external_adapter` now has only a recent summary pilot.

This change closes Phase I by turning those conclusions into canonical exit and reopen rules, so the next project slice can move to Phase II without re-litigating channel promotion boundaries.

## What Changes

- Record Phase I closure criteria in canonical specs and architecture docs.
- Freeze the current channel promotion state:
  - `main_chat`: `query_workspace` baseline.
  - `subagent_lane`: allowed through `query_detail`; `query_history` and `query_workspace` remain blocked.
  - `external_adapter`: allowed through `recent_summary`; `query_detail`, `query_history`, and `query_workspace` remain blocked.
- Define future reopen rules: any deeper channel implementation must start with a new promotion decision change.
- Update roadmap so the default next phase becomes Phase II runtime-core implementation and delivery-surface slimming, not more channel expansion.
- Non-goals:
  - Do not implement new query contracts.
  - Do not promote `subagent_lane` to history/workspace.
  - Do not promote `external_adapter` to detail/history/workspace.
  - Do not extract a generic recent summary assembler.
  - Do not change backend runtime behavior or frontend UI.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `channel-promotion-gate`: Add Phase I closure and future reopen rules for channel promotion.
- `query-workspace-generalization`: Add the Phase I exit line and block deeper channel work without a separate promotion decision.

## Impact

- OpenSpec:
  - `openspec/specs/channel-promotion-gate/spec.md`
  - `openspec/specs/query-workspace-generalization/spec.md`
- Docs:
  - `docs/roadmap/next_phase_hardening.md`
  - `docs/architecture/runtime_contracts.md`
- Runtime/frontend code:
  - No runtime, API, database, or frontend behavior changes.
