## 1. Shared Governance Interpretation

- [x] 1.1 Consolidate or create the shared governance interpretation layer for route/focus/snapshot semantics
- [x] 1.2 Make `RuntimeSurfacePanel` and `GovernanceTimelinePanel` consume the same interpretation helpers
- [x] 1.3 Keep local rendering and local UI state separate in each panel

## 2. Governance Entry Consistency

- [x] 2.1 Normalize governance entry semantics across summary, detail, drill-down, and snapshot actions
- [x] 2.2 Ensure route-driven focus remains an observation model, not a durable object model
- [x] 2.3 Update governance-related docs to describe the shared interpretation boundary

## 3. Verification and Handoff

- [x] 3.1 Verify governance view unification does not change backend read model contracts
- [x] 3.2 Re-read the affected docs and specs for contradictions
- [x] 3.3 Prepare the change for implementation after spec self-review
