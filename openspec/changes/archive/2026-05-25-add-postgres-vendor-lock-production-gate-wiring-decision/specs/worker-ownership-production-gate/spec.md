## ADDED Requirements

### Requirement: Production ownership gates MUST cover PostgreSQL production gate wiring decision evidence

Worker ownership production gate quality coverage MUST prove that PostgreSQL vendor lock production gate wiring decision evidence exists, is fail-closed by default, and does not update the default production gate by itself.

#### Scenario: Runtime smoke covers default wiring decision blocker

- **WHEN** runtime smoke evaluates worker ownership store mode coverage
- **THEN** it MUST include PostgreSQL wiring decision contract version, default status, default missing sections, default non-update, default non-enablement, and default non-execution fields
- **AND** production gate MUST remain blocked

#### Scenario: Runtime smoke covers approved wiring decision

- **WHEN** runtime smoke builds a complete wiring decision from ready semantics binding evidence
- **THEN** it MUST prove the decision can become ready and `wiring_allowed = true`
- **AND** it MUST prove the decision does not update the production gate or enable production lock

#### Scenario: Wiring decision does not bypass durable recovery blocker

- **WHEN** PostgreSQL vendor lock production gate wiring decision evidence is ready
- **THEN** durable recovery production gate MUST remain blocked until worker ownership production gate and rollout enablement are explicitly ready
