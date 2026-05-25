## 1. Panel Boundary

- [x] 1.1 Extract the densest Governance Timeline regions into clearer subcomponent boundaries without changing behavior.
- [x] 1.2 Keep `GovernanceTimelinePanel` as the orchestration entrypoint for loading, filtering, and route sync.

## 2. Regression Coverage

- [x] 2.1 Refresh focused frontend tests to assert the panel still renders the same governance behavior after the structural split.
- [x] 2.2 Confirm the extracted structure still preserves snapshot commands, workspace, and event-card interactions.

## 3. Documentation and Validation

- [x] 3.1 Update roadmap and runtime contract docs to note the panel slimming boundary.
- [x] 3.2 Validate the new change with OpenSpec and targeted frontend tests.
