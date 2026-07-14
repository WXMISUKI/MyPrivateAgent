## MODIFIED Requirements

### Requirement: Runtime integrations must use normalized execution envelopes
The system MUST normalize external runtime requests, events, results, interruptions, and errors into a stable execution envelope before those signals reach governance or front-end consumers.

#### Scenario: External framework emits native events
- **WHEN** a runtime integration produces framework-native events or errors
- **THEN** the integration MUST map them into the local execution envelope
- **AND** the governance surface MUST consume the normalized contract rather than the framework-native payload

#### Scenario: Approval interrupt is emitted by runtime
- **WHEN** an external runtime interrupts execution for approval
- **THEN** the event MUST be represented as a normalized approval interrupt in the local contract
- **AND** the approval decision MUST remain replayable

#### Scenario: Runtime Surface exposes projection readiness
- **WHEN** Runtime Surface exposes runtime-plane governance visibility
- **THEN** it MUST consume the normalized projection contract rather than adapter-native state
- **AND** it MUST remain read-only until a later change explicitly adds trace persistence or approval submission
