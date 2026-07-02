# governance-view-unification Specification

## ADDED Requirements

### Requirement: Runtime Surface governance view MAY render provider ops posture
The Runtime Surface governance view SHALL be able to render provider ops posture as a compact diagnostic card.

#### Scenario: Provider ops renders in Runtime Surface
- **WHEN** the frontend Runtime Surface panel consumes a profile with `provider_ops`
- **THEN** it may render summary counts and compact per-provider posture fields
- **AND** it remains diagnostic-only

#### Scenario: Empty provider ops is visible
- **WHEN** provider ops data is empty or degraded
- **THEN** the Runtime Surface panel shows a stable empty or degraded state
- **AND** it does not silently hide the governance area
