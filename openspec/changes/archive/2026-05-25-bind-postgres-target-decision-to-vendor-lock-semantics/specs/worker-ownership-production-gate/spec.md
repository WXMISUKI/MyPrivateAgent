## ADDED Requirements

### Requirement: Production ownership gates MUST cover PostgreSQL vendor lock semantics binding evidence

Worker ownership production gate quality coverage MUST prove that PostgreSQL vendor lock semantics binding evidence exists, is fail-closed by default, and does not update production gate readiness by itself.

#### Scenario: Runtime smoke covers default semantics binding blocker

- **WHEN** runtime smoke evaluates worker ownership store mode coverage
- **THEN** it MUST include PostgreSQL semantics binding contract version, default status, default missing sections, default non-execution, default non-production-gate-update, and default non-enablement fields
- **AND** production gate MUST remain blocked

#### Scenario: Runtime smoke covers ready semantics candidate

- **WHEN** runtime smoke builds a complete PostgreSQL semantics binding from ready target binding and ready opt-in execution seam evidence
- **THEN** it MUST prove nested PostgreSQL probe, adapter, and vendor lock semantics evidence are ready
- **AND** it MUST prove the binding does not execute advisory lock SQL
- **AND** it MUST prove the binding does not enable production lock or update production gate readiness by itself

#### Scenario: Semantics candidate does not bypass durable recovery blocker

- **WHEN** PostgreSQL vendor lock semantics binding evidence is ready
- **THEN** durable recovery production gate MUST remain blocked until worker ownership production gate and rollout enablement are explicitly ready
