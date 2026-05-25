## MODIFIED Requirements

### Requirement: Governance Overview Run Contract Must Surface Child Merge State

`governance_overview.run` MUST expose the stable parent-facing child merge state so frontend consumers do not need to reconstruct it from separate child merged semantics read models.

The run contract MUST include:

- current run identity fields
- latest trace summary
- `child_merge_intent`
- `child_merge_entities`
- `child_merge_conclusion`
- child merge count fields
- child merge section-source evidence

#### Scenario: Parent overview reads run state from backend contract

- **GIVEN** child merged semantics are available for the current runtime scope
- **WHEN** runtime profile is returned
- **THEN** `governance_overview.run` MUST include the parent-facing merge fields
- **AND** it MUST include child merge section source, section ids, and section counts
- **AND** the frontend MUST be able to render parent overview without reconstructing them from child summary cards

