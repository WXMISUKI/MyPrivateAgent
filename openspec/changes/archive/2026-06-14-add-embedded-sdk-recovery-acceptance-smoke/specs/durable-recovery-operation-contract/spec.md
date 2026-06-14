## ADDED Requirements

### Requirement: Recovery acceptance MUST preserve non-executable operation evidence

The durable recovery operation contract MUST provide compact operation evidence for acceptance smoke consumers without copying executable runtime internals.

#### Scenario: Acceptance payload includes latest operation summary

- **WHEN** the acceptance smoke completes accepted or blocked recovery scenarios
- **THEN** the payload MUST include compact latest operation evidence when available
- **AND** the evidence MUST include operation status, entrypoint, recovery reason, persistence posture, and workspace evidence
- **AND** the evidence MUST NOT include callable continuations, executable handlers, provider clients, active streams, or raw SDK objects
