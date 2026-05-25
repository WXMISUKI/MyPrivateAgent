## ADDED Requirements

### Requirement: Production ownership gates MUST cover PostgreSQL rollout artifact consumer evidence

Worker ownership production gate quality coverage MUST prove that PostgreSQL rollout artifact consumer evidence exists, is fail-closed by default, and does not bypass production default enablement gates.

#### Scenario: Runtime smoke covers default consumer blocker

- **WHEN** runtime smoke evaluates worker ownership store mode coverage
- **THEN** it MUST include PostgreSQL rollout artifact consumer contract version, default status, default missing sections, default non-execution, and default non-enablement fields
- **AND** the production gate MUST remain blocked

#### Scenario: Runtime smoke covers complete artifact bridge

- **WHEN** runtime smoke builds a complete PostgreSQL rollout artifact consumer with a ready opt-in execution seam contract
- **THEN** it MUST prove the consumer can produce ready nested input source evidence
- **AND** it MUST prove that the consumer still reports `will_enable_production_default = false`
- **AND** production default worker ownership MUST remain disabled

#### Scenario: SQL row lease is not promoted by artifact consumer

- **WHEN** strict SQL row lease/fencing is present
- **THEN** PostgreSQL rollout artifact consumer evidence MUST NOT mark SQL row lease/fencing as vendor lock authority
- **AND** production gate and durable recovery gate MUST remain blocked until explicit production enablement and rollout decisions are complete
