## ADDED Requirements

### Requirement: Durable loader MUST expose production recovery gate boundary

The durable recovery loader contract MUST identify that candidate loading is not recovery execution and remains gated by the production recovery gate.

#### Scenario: Loader is ready but production gate is blocked

- **WHEN** the loader produces a ready registry-backed candidate
- **AND** production recovery gate is blocked
- **THEN** the loader result remains non-executing evidence
- **AND** default cross-process recovery execution remains disabled

### Requirement: Loader handoff MUST be explicit

The runtime MUST require explicit handoff policy before a loaded candidate can be executed as production cross-process recovery.

#### Scenario: Handoff policy is missing

- **WHEN** a recovery candidate is loaded
- **AND** loader execution handoff policy is missing
- **THEN** DurableRecoveryLoader MUST NOT execute the candidate
- **AND** the production gate includes `loader_execution_handoff_policy` in missing sections
