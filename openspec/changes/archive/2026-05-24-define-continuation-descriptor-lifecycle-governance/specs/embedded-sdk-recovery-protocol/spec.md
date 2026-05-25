## MODIFIED Requirements

### Requirement: Recovery protocol MUST define descriptor lifecycle evidence

The recovery protocol MUST expose descriptor lifecycle evidence before cross-process recovery can be production-default.

#### Scenario: Descriptor lifecycle is governed

- **WHEN** a descriptor participates in production recovery
- **THEN** lifecycle evidence MUST distinguish created, bound, ready, stale, resolved, and unsafe states
- **AND** unsafe callable-like payloads MUST remain fail-closed
- **AND** lifecycle readiness MUST NOT bypass checkpoint/resume cursor, worker ownership, audit, or loader handoff gates
