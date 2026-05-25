## MODIFIED Requirements

### Requirement: Persistence interface MUST expose production recovery gate evidence

The embedded SDK persistence interface MUST include production recovery gate evidence that distinguishes backend durability from production cross-process recovery readiness.

#### Scenario: Registry/checkpoint policy is available

- **WHEN** registry/checkpoint production policy readiness is implemented
- **THEN** the production recovery gate may mark `registry_binding_resolution` and `checkpoint_resume_cursor_gate` as ready
- **AND** it MUST remain blocked while worker ownership or rollout evidence is missing
