## ADDED Requirements

### Requirement: Production ownership gates MUST cover PostgreSQL target artifact binding evidence

Worker ownership production gate quality coverage MUST prove that PostgreSQL target artifact binding evidence exists, is fail-closed by default, and does not bypass production lock or default ownership gates.

#### Scenario: Runtime smoke covers default binding blocker

- **WHEN** runtime smoke evaluates worker ownership store mode coverage
- **THEN** it MUST include PostgreSQL target artifact binding contract version, default status, default missing sections, default non-execution, and default non-enablement fields
- **AND** production gate MUST remain blocked

#### Scenario: Runtime smoke covers complete target decision bridge

- **WHEN** runtime smoke builds a complete PostgreSQL target artifact binding from the same rollout artifact family
- **THEN** it MUST prove nested target decision input and target decision evidence are ready
- **AND** it MUST prove the binding does not execute advisory lock SQL
- **AND** it MUST prove the binding does not enable production lock by itself

#### Scenario: Target binding does not bypass production recovery blocker

- **WHEN** PostgreSQL target artifact binding evidence is ready
- **THEN** durable recovery production gate MUST remain blocked until worker ownership production gate and rollout enablement are explicitly ready
