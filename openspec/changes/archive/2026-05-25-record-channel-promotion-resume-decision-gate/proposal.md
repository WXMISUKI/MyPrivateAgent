## Why

Phase H has reached its completion line for `main_chat` query detail, query history, and workspace behavior. Phase I now needs a formal promotion record before any channel resumes implementation, otherwise `subagent_lane` or `external_adapter` work can drift from readiness review into copied `main_chat` workspace behavior.

This change makes the channel promotion decision itself a canonical contract: it records the allowed layer, blockers, explicit non-goals, and next allowed action before implementation resumes.

## What Changes

- Add formal promotion record requirements to `channel-promotion-gate`.
- Record current canonical decisions for `main_chat`, `subagent_lane`, and `external_adapter`.
- Clarify that `external_adapter recent summary` is not the default next implementation until a resume decision explicitly allows it.
- Clarify that `subagent_lane` must not move to history or workspace from its current state without a separate promotion decision.
- Update roadmap and architecture docs so Phase I discussion starts from promotion records, not local UI momentum.
- Non-goals:
  - Do not implement `external_adapter recent summary`.
  - Do not add new runtime read model endpoints.
  - Do not change frontend query workspace behavior.
  - Do not promote any channel to query history or query workspace.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `channel-promotion-gate`: Add the formal implementation resume decision record and canonical current channel decisions.
- `query-workspace-generalization`: Clarify that channel implementation resumes only after a recorded promotion decision.

## Impact

- OpenSpec:
  - `openspec/specs/channel-promotion-gate/spec.md`
  - `openspec/specs/query-workspace-generalization/spec.md`
- Docs:
  - `docs/roadmap/next_phase_hardening.md`
  - `docs/architecture/runtime_contracts.md`
- Runtime/frontend code:
  - No runtime, API, database, or frontend behavior changes.
