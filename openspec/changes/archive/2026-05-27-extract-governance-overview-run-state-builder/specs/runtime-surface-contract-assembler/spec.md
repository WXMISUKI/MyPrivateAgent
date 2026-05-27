## ADDED Requirements

### Requirement: Governance overview run-state assembly MUST be decomposable before full overview extraction
The system MUST allow the `governance_overview.run` section to be extracted into a dedicated builder without requiring the full governance overview contract to move at the same time.

#### Scenario: Run section is extracted independently
- **WHEN** maintainers refactor Runtime Surface governance overview assembly
- **THEN** they MAY extract `governance_overview.run` as an independent concern-specific builder
- **AND** the full governance overview shell MUST preserve existing recovery, child executor, approval, audit, and main chat sections
