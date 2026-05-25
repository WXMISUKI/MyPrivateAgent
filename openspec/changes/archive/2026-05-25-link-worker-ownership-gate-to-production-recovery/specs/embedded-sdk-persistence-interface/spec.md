## MODIFIED Requirements

### Requirement: Persistence interface MUST expose production recovery gate evidence

The embedded SDK persistence interface MUST include production recovery gate evidence that distinguishes backend durability from production cross-process recovery readiness.

#### Scenario: Worker ownership production gate is provided

- **WHEN** the runtime factory builds the embedded persistence interface with worker ownership production gate evidence
- **THEN** `persistence_interface.production_recovery_gate` MUST preserve compact worker ownership gate status and blocker evidence
- **AND** this evidence MUST NOT enable default cross-process recovery while ownership or rollout remains blocked
