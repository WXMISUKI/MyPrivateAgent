## ADDED Requirements

### Requirement: Executed child merge fixtures MUST satisfy execution prerequisites
Tests and integration fixtures that expect executed child executor output and merged semantics MUST provide the same explicit executor binding opt-in evidence required by the child executor execution prerequisites contract.

#### Scenario: Fixture expects executed child semantics
- **WHEN** a test fixture binds, executes, and merges an `embedded_sdk_worker` child executor output
- **AND** it asserts executed merged semantics such as `risk_review`
- **THEN** the fixture MUST include explicit executor binding opt-in evidence
- **AND** the execution gate MUST remain fail-closed when that evidence is absent

#### Scenario: Missing opt-in remains blocked
- **WHEN** a child executor payload omits explicit executor binding opt-in evidence
- **THEN** the execution prerequisites MUST continue to block execution
- **AND** Runtime Surface consumers MUST NOT treat the blocked merge as executed child semantics
