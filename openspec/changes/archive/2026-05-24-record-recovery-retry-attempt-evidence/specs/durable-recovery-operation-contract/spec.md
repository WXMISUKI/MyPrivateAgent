## MODIFIED Requirements

### Requirement: Recovery Operation Records Must Be Compact And Non-Executable

Recovery operation records MUST contain audit evidence without copying executable internals, and their contract construction SHOULD live behind a dedicated recovery operation Module rather than inside the SDK orchestration class. When worker ownership or retry evidence is supplied, the operation record MUST preserve compact evidence fields without requiring executable internals.

#### Scenario: Recovery operation includes retry evidence

- **WHEN** a recovery operation record is built with retry evidence
- **THEN** it MUST preserve the compact retry fields
- **AND** supplied retry evidence MUST remain compact and non-executable
- **AND** the operation record MUST preserve its operation identity, entrypoint, and recovery reason

#### Scenario: SDK recovery gate passes retry evidence to operation record

- **WHEN** an SDK recovery gate records a blocked or failed recovery operation for an explicit retry attempt
- **THEN** the operation record MUST include the supplied retry evidence
- **AND** the operation record MUST NOT include callable continuations, executable handlers, provider clients, or active stream iterators

