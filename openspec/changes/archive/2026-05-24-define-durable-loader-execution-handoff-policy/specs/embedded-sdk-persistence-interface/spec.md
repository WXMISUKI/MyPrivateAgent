## MODIFIED Requirements

### Requirement: Persistence interface MUST expose production recovery gate evidence

The embedded SDK persistence interface MUST include production recovery gate evidence that distinguishes backend durability from production cross-process recovery readiness.

#### Scenario: Handoff policy is available

- **WHEN** durable loader execution handoff policy is implemented
- **THEN** the production recovery gate may mark `loader_execution_handoff_policy` as ready
- **AND** it MUST remain blocked while registry binding, checkpoint/cursor, ownership, audit, or rollout evidence is missing
