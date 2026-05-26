## ADDED Requirements

### Requirement: Query Workspace Generalization MUST Use Promotion Records

The system SHALL use channel promotion records as the gate between high-level query workspace generalization and channel-specific implementation.

#### Scenario: Generalization stays at boundary layer

- **WHEN** Phase I high-level truth sources are stable
- **AND** a channel lacks a promotion record for the desired implementation layer
- **THEN** the team MUST continue with specification, architecture, or readiness-check work
- **AND** it MUST NOT resume channel-specific implementation by default

#### Scenario: Implementation resumes from the shallowest eligible layer

- **WHEN** a promotion record allows channel-specific implementation
- **THEN** the implementation MUST begin at the recorded target layer
- **AND** it MUST preserve explicit non-goals for deeper layers
- **AND** it MUST NOT expand from recent summary into detail, history, or workspace in the same change unless the record explicitly allows each layer
