## ADDED Requirements
### Requirement: Child Output Merge Must Declare Handoff Readiness
Child output merge behavior MUST expose a read-only handoff readiness contract before child execution is treated as ready for parent merge.

#### Scenario: Handoff strategy is supported
- **WHEN** a child run declares `append_summary` or `role_sections`
- **THEN** the handoff contract MUST report ready
- **AND** it MUST declare artifact envelope, section handoff, replay, and parent metadata expectations

#### Scenario: Handoff strategy is unsupported
- **WHEN** a child run declares an unsupported merge strategy
- **THEN** the handoff contract MUST report blocked
- **AND** parent merge execution MUST NOT be implied
