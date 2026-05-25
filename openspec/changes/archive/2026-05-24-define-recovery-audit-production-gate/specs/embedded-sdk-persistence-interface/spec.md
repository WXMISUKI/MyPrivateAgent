## MODIFIED Requirements

### Requirement: Persistence interface MUST expose production recovery gate evidence

The embedded SDK persistence interface MUST include production recovery gate evidence that distinguishes backend durability from production cross-process recovery readiness.

#### Scenario: Recovery audit operation history is available

- **WHEN** recovery audit production readiness is implemented
- **THEN** the production recovery gate may mark `recovery_audit_operation_history` as ready
- **AND** it MUST remain blocked while registry binding, checkpoint/cursor, ownership, or rollout evidence is missing
