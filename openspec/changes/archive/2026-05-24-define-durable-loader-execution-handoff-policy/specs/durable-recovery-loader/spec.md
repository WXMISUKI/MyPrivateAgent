## MODIFIED Requirements

### Requirement: Loader handoff MUST be explicit

The runtime MUST require explicit handoff policy before a loaded candidate can be executed as production cross-process recovery.

#### Scenario: Handoff policy is present but executor is missing

- **WHEN** a recovery candidate is loaded
- **AND** loader execution handoff policy is available
- **AND** no recovery executor binding exists
- **THEN** DurableRecoveryLoader MUST NOT execute the candidate
- **AND** the candidate includes handoff policy evidence with `will_execute = false`

#### Scenario: Handoff policy is missing

- **WHEN** a recovery candidate is loaded
- **AND** loader execution handoff policy is missing
- **THEN** DurableRecoveryLoader MUST NOT execute the candidate
- **AND** the production gate includes `loader_execution_handoff_policy` in missing sections
